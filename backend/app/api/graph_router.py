"""
FastAPI Router for LegalLens Knowledge Graph Workspace.
Provides endpoints for case listing, document upload & graph extraction,
graph retrieval, progressive neighborhood expansion, entity/relationship mutations,
server-side user notes, and graph presentation preferences.
Strictly enforces case isolation, ontology schema constraints, and auditability.
"""

import os
import json
import uuid
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
    Path as FPath,
    Query,
    Depends,
    BackgroundTasks,
)
from pydantic import BaseModel, Field

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.validator import (
    SchemaValidator,
    InvalidEntityTypeError,
    InvalidRelationshipTypeError,
    TripletConstraintViolationError,
)
from app.storage.neo4j_store import Neo4jGraphStore
from app.api.review_router import get_neo4j_store, get_manager, ReviewManager
from app.review.models import ReviewItem, ItemType, ReviewStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["knowledge-graph"])

BASE_STORAGE_DIR = (
    Path("backend/storage") if Path("backend/storage").exists() else Path("storage")
)
GRAPHS_DIR = BASE_STORAGE_DIR / "graphs"
NOTES_DIR = BASE_STORAGE_DIR / "notes"
PREFS_DIR = BASE_STORAGE_DIR / "preferences"

GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)
PREFS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# In-process job status store (survives server restarts via JSON on disk).
# Key: job_id (str), Value: job record dict.
# ---------------------------------------------------------------------------
JOBS_DIR = BASE_STORAGE_DIR / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)
_jobs_lock = threading.Lock()


def _write_job(job: Dict[str, Any]) -> None:
    """Persist job record to disk (thread-safe)."""
    with _jobs_lock:
        job_file = JOBS_DIR / f"{job['job_id']}.json"
        with open(job_file, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2)


def _read_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Read a job record from disk."""
    job_file = JOBS_DIR / f"{job_id}.json"
    if not job_file.is_file():
        return None
    try:
        with open(job_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# =============================================================================
# Request / Response DTO Models
# =============================================================================


class CaseSummary(BaseModel):
    case_id: str
    title: str
    entity_count: int
    relationship_count: int
    timeline_event_count: int
    document_count: int
    updated_at: str


class CreateEntityRequest(BaseModel):
    canonical_name: str = Field(
        ..., min_length=1, description="Entity primary display name"
    )
    entity_type: str = Field(..., description="Controlled EntityType enum string")
    aliases: Optional[List[str]] = Field(
        default_factory=list, description="Alternative names / aliases"
    )
    source_text: Optional[str] = Field(
        default=None, description="Optional supporting quote or excerpt"
    )
    description: Optional[str] = Field(
        default=None, description="Optional descriptive note"
    )


class UpdateEntityRequest(BaseModel):
    canonical_name: Optional[str] = Field(default=None, min_length=1)
    entity_type: Optional[str] = Field(default=None)
    aliases: Optional[List[str]] = Field(default=None)


class CreateRelationshipRequest(BaseModel):
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(
        ..., description="Controlled RelationshipType enum string"
    )
    source_text: Optional[str] = Field(
        default=None, description="Optional evidentiary text citation"
    )
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)


class SaveNotesRequest(BaseModel):
    notes: str = Field(..., description="User-authored note content")


class SavePreferencesRequest(BaseModel):
    custom_colors: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Map of node_id -> hex color string"
    )
    preferred_layout: Optional[str] = Field(
        default="cose", description="Layout mode (cose, breadthfirst, etc.)"
    )


# =============================================================================
# Helper Utilities for Storage Cache & Case Isolation
# =============================================================================


def _load_cached_graph(case_id: str) -> Optional[Dict[str, Any]]:
    """Loads graph JSON from persistent storage if available."""
    target_file = GRAPHS_DIR / f"{case_id}.json"
    if target_file.is_file():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load cached graph for case %s: %s", case_id, e)
    return None


def _save_cached_graph(case_id: str, data: Dict[str, Any]) -> None:
    """Persists graph JSON to storage cache."""
    target_file = GRAPHS_DIR / f"{case_id}.json"
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning("Failed to cache graph for case %s: %s", case_id, e)


def _load_notes(case_id: str, entity_id: str) -> str:
    note_file = NOTES_DIR / case_id / f"{entity_id}.txt"
    if note_file.is_file():
        try:
            return note_file.read_text(encoding="utf-8")
        except Exception:
            pass
    return ""


def _save_notes(case_id: str, entity_id: str, notes: str) -> None:
    case_notes_dir = NOTES_DIR / case_id
    case_notes_dir.mkdir(parents=True, exist_ok=True)
    note_file = case_notes_dir / f"{entity_id}.txt"
    note_file.write_text(notes, encoding="utf-8")


def _load_preferences(case_id: str) -> Dict[str, Any]:
    pref_file = PREFS_DIR / f"{case_id}.json"
    if pref_file.is_file():
        try:
            with open(pref_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"custom_colors": {}, "preferred_layout": "cose"}


def _save_preferences(case_id: str, prefs: Dict[str, Any]) -> None:
    pref_file = PREFS_DIR / f"{case_id}.json"
    with open(pref_file, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/cases", response_model=List[CaseSummary])
def list_cases(
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> List[CaseSummary]:
    """
    Lists all accessible legal cases with their entity, relationship, and document counts.
    Queries live Neo4j database when available and aggregates with storage archives.
    """
    cases_dict: Dict[str, Dict[str, Any]] = {}
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Inspect live Neo4j database if connected
    if store.verify_connection():
        try:
            driver = store.connect()
            query = """
            MATCH (n:LegalEntity)
            WHERE n.case_id IS NOT NULL AND n.case_id <> ''
            RETURN n.case_id AS case_id, count(n) AS entity_count
            """
            with driver.session(database=store.database) as session:
                res = session.run(query)
                for rec in res:
                    cid = rec["case_id"]
                    cases_dict[cid] = {
                        "case_id": cid,
                        "title": cid.replace("_", " ").title(),
                        "entity_count": rec["entity_count"],
                        "relationship_count": 0,
                        "timeline_event_count": 0,
                        "document_count": 1,
                        "updated_at": now_iso,
                    }

            # Count relationships per case
            rel_query = """
            MATCH ()-[r]->()
            WHERE r.case_id IS NOT NULL AND r.case_id <> ''
            RETURN r.case_id AS case_id, count(r) AS rel_count
            """
            with driver.session(database=store.database) as session:
                res = session.run(rel_query)
                for rec in res:
                    cid = rec["case_id"]
                    if cid in cases_dict:
                        cases_dict[cid]["relationship_count"] = rec["rel_count"]

            # Count timeline events per case
            evt_query = """
            MATCH (e:TimelineEvent)
            WHERE e.case_id IS NOT NULL AND e.case_id <> ''
            RETURN e.case_id AS case_id, count(e) AS evt_count
            """
            with driver.session(database=store.database) as session:
                res = session.run(evt_query)
                for rec in res:
                    cid = rec["case_id"]
                    if cid in cases_dict:
                        cases_dict[cid]["timeline_event_count"] = rec["evt_count"]
        except Exception as e:
            logger.warning("Error querying Neo4j for cases list: %s", e)

    # 2. Inspect storage cached graphs
    for f in GRAPHS_DIR.glob("*.json"):
        cid = f.stem
        if cid not in cases_dict:
            try:
                with open(f, "r", encoding="utf-8") as gf:
                    data = json.load(gf)
                    summary = data.get("summary", {})
                    cases_dict[cid] = {
                        "case_id": cid,
                        "title": data.get("title", cid.replace("_", " ").title()),
                        "entity_count": summary.get(
                            "entity_count", len(data.get("entities", []))
                        ),
                        "relationship_count": summary.get(
                            "relationship_count", len(data.get("relationships", []))
                        ),
                        "timeline_event_count": summary.get(
                            "timeline_event_count", len(data.get("timeline_events", []))
                        ),
                        "document_count": 1,
                        "updated_at": now_iso,
                    }
            except Exception:
                pass

    # 3. Inspect parsed storage documents
    parsed_dir = BASE_STORAGE_DIR / "parsed"
    if parsed_dir.is_dir():
        for doc_file in parsed_dir.glob("*.json"):
            try:
                with open(doc_file, "r", encoding="utf-8") as df:
                    doc_data = json.load(df)
                    cid = doc_data.get("case_id")
                    if cid and cid not in cases_dict:
                        filename = doc_data.get("filename", "Legal Document")
                        cases_dict[cid] = {
                            "case_id": cid,
                            "title": doc_data.get("document_metadata", {}).get("title")
                            or filename,
                            "entity_count": 0,
                            "relationship_count": 0,
                            "timeline_event_count": 0,
                            "document_count": 1,
                            "updated_at": doc_data.get("processing_metadata", {}).get(
                                "completed_at", now_iso
                            ),
                        }
            except Exception:
                pass

    return [
        CaseSummary(**v)
        for v in sorted(cases_dict.values(), key=lambda x: x["case_id"])
    ]


@router.post("/upload")
async def upload_and_process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_id: str = Form(
        ..., description="Target case identifier to scope the document and graph"
    ),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
    review_mgr: ReviewManager = Depends(get_manager),
) -> Dict[str, Any]:
    """
    Accepts a legal document upload and immediately returns a job_id.
    Processing runs in a background thread — poll GET /api/v1/graph/jobs/{job_id}
    for status (PENDING → PROCESSING → SUCCESS | PARTIAL | FAILED).
    """
    case_id = case_id.strip()
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id cannot be empty.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    MAX_SIZE = 150 * 1024 * 1024
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({len(contents)} bytes) exceeds the 150MB limit.",
        )

    filename = file.filename or "uploaded_document.pdf"
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    job: Dict[str, Any] = {
        "job_id": job_id,
        "case_id": case_id,
        "filename": filename,
        "status": "PENDING",
        "stage": "Queued",
        "created_at": now_iso,
        "updated_at": now_iso,
        "metrics": {},
        "error": None,
    }
    _write_job(job)

    background_tasks.add_task(
        _run_extraction_pipeline,
        job_id=job_id,
        case_id=case_id,
        filename=filename,
        contents=contents,
        store=store,
        review_mgr=review_mgr,
    )

    return {
        "job_id": job_id,
        "status": "PENDING",
        "case_id": case_id,
        "filename": filename,
        "message": "Processing started in background. Poll /api/v1/graph/jobs/{job_id} for status.",
    }


def _run_extraction_pipeline(
    job_id: str,
    case_id: str,
    filename: str,
    contents: bytes,
    store: Neo4jGraphStore,
    review_mgr: ReviewManager,
) -> None:
    """Background thread: runs the full extraction pipeline and writes final job status."""

    def _update(
        stage: str, status: str = "PROCESSING", error: str = None, metrics: dict = None
    ):
        job = _read_job(job_id) or {}
        job.update(
            {
                "status": status,
                "stage": stage,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        if error is not None:
            job["error"] = error
        if metrics is not None:
            job["metrics"] = metrics
        _write_job(job)

    try:
        from app.ingestion.pipeline import DocumentIngestionPipeline
        from app.extraction.ai_pipeline import AIExtractionPipeline
        from app.resolution.pipeline import EntityResolutionPipeline
        from app.validation.pipeline import ValidationPipeline
        from app.temporal.pipeline import TemporalPipeline
        from app.storage.neo4j_pipeline import Neo4jStoragePipeline

        pipeline_start = time.monotonic()
        stage_timings: Dict[str, float] = {}

        # Step 2 — Ingestion
        _update("Ingesting document")
        t0 = time.monotonic()
        try:
            ingestion = DocumentIngestionPipeline(
                base_storage_dir=str(BASE_STORAGE_DIR)
            )
            legal_doc = ingestion.process_document(
                source=contents,
                filename=filename,
                case_id=case_id,
            )
        except Exception as e:
            logger.error("Step 2 Ingestion failed for job %s: %s", job_id, e)
            _update(
                "Ingestion failed",
                status="FAILED",
                error=f"Document ingestion error: {e}",
            )
            return
        stage_timings["ingestion_secs"] = round(time.monotonic() - t0, 2)
        logger.info(
            "Job %s — ingestion complete in %.1fs (%d pages).",
            job_id,
            stage_timings["ingestion_secs"],
            len(getattr(legal_doc, "pages", [])),
        )

        # Steps 3 & 4 — Extraction (GLiNER model — reuses singleton, fast after first load)
        page_count = len(getattr(legal_doc, "pages", []))
        _update(
            f"Extracting entities from {page_count} page(s) "
            f"(GLiNER model — reuses cached instance)"
        )
        t0 = time.monotonic()
        try:
            # AIExtractionPipeline uses the process-wide GLiNER singleton via get_extractor().
            ai_pipeline = AIExtractionPipeline()
            combined_result = ai_pipeline.run_pipeline(legal_doc)
        except Exception as e:
            logger.error("Extraction failed for job %s: %s", job_id, e)
            _update(
                "Extraction failed",
                status="FAILED",
                error=f"Entity extraction error: {e}",
            )
            return
        stage_timings["extraction_secs"] = round(time.monotonic() - t0, 2)
        logger.info(
            "Job %s — extraction complete in %.1fs (%d entities, %d relations).",
            job_id,
            stage_timings["extraction_secs"],
            len(combined_result.ai_result.entities),
            len(combined_result.ai_result.relations),
        )

        # Step 5 — Resolution
        _update("Resolving and deduplicating entities")
        t0 = time.monotonic()
        resolution_pipeline = EntityResolutionPipeline()
        all_entities = (
            combined_result.deterministic_result.candidates
            + combined_result.ai_result.entities
        )
        all_relations = combined_result.ai_result.relations
        resolution_result = resolution_pipeline.resolve(
            document_id=legal_doc.document_id,
            case_id=legal_doc.case_id,
            entities=all_entities,
            relations=all_relations,
        )
        stage_timings["resolution_secs"] = round(time.monotonic() - t0, 2)

        # Step 6 — Validation
        _update("Validating against ontology")
        t0 = time.monotonic()
        validation_pipeline = ValidationPipeline()
        validation_result = validation_pipeline.validate(resolution_result)
        stage_timings["validation_secs"] = round(time.monotonic() - t0, 2)

        for rec in validation_result.review_required:
            item = ReviewItem(
                case_id=case_id,
                item_type=(
                    ItemType.RELATIONSHIP if rec.relationship_id else ItemType.ENTITY
                ),
                status=ReviewStatus.PENDING,
                entity_id=rec.entity_id,
                relationship_id=rec.relationship_id,
                confidence=0.5,
                reason=rec.message or "Flagged by Step 6 validation rule",
                validation_rule=rec.validation_rule,
                original_prediction={
                    "rule": rec.validation_rule,
                    "message": rec.message,
                    "record_type": str(rec.record_type.value),
                },
                source_document_id=legal_doc.document_id,
            )
            review_mgr.add_review_item(item)

        # Step 7 — Temporal
        _update("Extracting timeline events")
        t0 = time.monotonic()
        temporal_pipeline = TemporalPipeline()
        case_timeline = temporal_pipeline.process_timeline(
            document=legal_doc,
            resolution_result=resolution_result,
            validation_result=validation_result,
        )
        stage_timings["temporal_secs"] = round(time.monotonic() - t0, 2)

        # Step 8 — Build serialisable graph
        _update("Persisting graph")
        t0 = time.monotonic()
        entities_data = []
        for ent in validation_result.validated_entities:
            first_m = ent.mentions[0] if getattr(ent, "mentions", None) else None
            spage = getattr(first_m, "source_page", 1) or 1
            stext = (
                getattr(first_m, "source_text", ent.canonical_name)
                or ent.canonical_name
            )
            conf = getattr(first_m, "confidence", 1.0) or 1.0
            emeth = (
                getattr(first_m, "extraction_method", "GLINER_RELEX") or "GLINER_RELEX"
            )
            if hasattr(emeth, "value"):
                emeth = emeth.value
            etype = (
                ent.entity_type.value
                if hasattr(ent.entity_type, "value")
                else str(ent.entity_type)
            )
            c_at = (
                ent.created_at.isoformat()
                if hasattr(ent.created_at, "isoformat")
                else str(ent.created_at)
            )
            entities_data.append(
                {
                    "id": ent.canonical_id,
                    "canonical_name": ent.canonical_name,
                    "normalized_name": getattr(
                        ent, "normalized_name", ent.canonical_name.lower().strip()
                    ),
                    "entity_type": etype,
                    "aliases": list(getattr(ent, "aliases", [])),
                    "document_id": ent.document_id,
                    "source_document_id": getattr(
                        ent, "source_document_id", ent.document_id
                    )
                    or legal_doc.document_id,
                    "source_page": spage,
                    "source_text": stext,
                    "confidence": float(conf),
                    "extraction_method": str(emeth),
                    "created_at": c_at,
                    "updated_at": c_at,
                }
            )

        entity_name_map: dict = {
            ent.canonical_id: ent.canonical_name
            for ent in validation_result.validated_entities
        }

        relationships_data = []
        for rel in validation_result.validated_relationships:
            first_m = rel.mentions[0] if getattr(rel, "mentions", None) else None
            spage = getattr(first_m, "source_page", 1) or 1
            stext = getattr(first_m, "source_text", "") or ""
            conf = getattr(first_m, "confidence", 1.0) or 1.0
            emeth = (
                getattr(first_m, "extraction_method", "GLINER_RELEX") or "GLINER_RELEX"
            )
            if hasattr(emeth, "value"):
                emeth = emeth.value
            rtype = (
                rel.relation_type.value
                if hasattr(rel.relation_type, "value")
                else str(rel.relation_type)
            )
            c_at = (
                rel.created_at.isoformat()
                if hasattr(rel.created_at, "isoformat")
                else str(rel.created_at)
            )
            src_name = entity_name_map.get(rel.source_entity_id, rel.source_entity_id)
            tgt_name = entity_name_map.get(rel.target_entity_id, rel.target_entity_id)
            relationships_data.append(
                {
                    "id": rel.relation_id,
                    "relationship_type": rtype,
                    "source_id": rel.source_entity_id,
                    "source_name": src_name,
                    "target_id": rel.target_entity_id,
                    "target_name": tgt_name,
                    "document_id": rel.document_id,
                    "source_document_id": getattr(
                        rel, "source_document_id", rel.document_id
                    )
                    or legal_doc.document_id,
                    "source_page": spage,
                    "source_text": stext,
                    "confidence": float(conf),
                    "extraction_method": str(emeth),
                    "created_at": c_at,
                }
            )

        events_data = [
            {
                "id": ev.event_id,
                "description": ev.description,
                "event_type": (
                    ev.event_type.value
                    if hasattr(ev.event_type, "value")
                    else str(ev.event_type)
                ),
                "event_date": ev.event_date,
                "start_date": ev.start_date,
                "end_date": ev.end_date,
                "date_precision": (
                    ev.date_precision.value
                    if hasattr(ev.date_precision, "value")
                    else str(ev.date_precision)
                ),
                "temporal_status": (
                    ev.temporal_status.value
                    if hasattr(ev.temporal_status, "value")
                    else str(ev.temporal_status)
                ),
                "confidence": ev.confidence,
                "source_document_id": ev.source_document_id or legal_doc.document_id,
                "source_page": ev.source_page or 1,
                "source_text": ev.source_text,
                "canonical_entity_id": ev.canonical_entity_id,
                "associated_entity_id": ev.canonical_entity_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            for ev in case_timeline.events
        ]

        cached_graph = {
            "case_id": case_id,
            "title": filename,
            "summary": {
                "entity_count": len(entities_data),
                "relationship_count": len(relationships_data),
                "timeline_event_count": len(events_data),
            },
            "entities": entities_data,
            "relationships": relationships_data,
            "timeline_events": events_data,
        }
        _save_cached_graph(case_id, cached_graph)

        neo4j_synced = False
        if store.verify_connection():
            try:
                pipeline = Neo4jStoragePipeline(store=store)
                pipeline.import_case_graph(
                    validation_result=validation_result,
                    case_timeline=case_timeline,
                    case_id=case_id,
                )
                neo4j_synced = True
            except Exception as e:
                logger.warning("Neo4j import warning for job %s: %s", job_id, e)
        stage_timings["persist_secs"] = round(time.monotonic() - t0, 2)

        metrics = {
            "entities_extracted": len(entities_data),
            "relationships_extracted": len(relationships_data),
            "timeline_events_extracted": len(events_data),
            "review_items_flagged": len(validation_result.review_required),
            "neo4j_synced": neo4j_synced,
            "stage_timings_secs": stage_timings,
            "total_pipeline_secs": round(time.monotonic() - pipeline_start, 2),
        }
        final_status = "PARTIAL" if len(entities_data) == 0 else "SUCCESS"
        final_stage = (
            "Complete — no entities extracted (check OCR/text quality)"
            if len(entities_data) == 0
            else f"Complete — {len(entities_data)} entities, {len(relationships_data)} relationships"
        )
        _update(final_stage, status=final_status, metrics=metrics)
        logger.info("Job %s finished: %s", job_id, final_stage)

    except Exception as e:
        logger.exception("Unexpected error in extraction job %s", job_id)
        _update("Unexpected pipeline error", status="FAILED", error=str(e))


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str = FPath(...)) -> Dict[str, Any]:
    """Poll the status of a background extraction job."""
    job = _read_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job


@router.get("/{case_id}")
def get_case_graph(
    case_id: str = FPath(..., description="Unique case identifier"),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Retrieves the complete Case Knowledge Graph (entities, relationships, events, and metrics).
    Enforces strict case isolation.
    Overlays persistent user notes and visual preferences.
    """
    case_id = case_id.strip()
    graph_data: Optional[Dict[str, Any]] = None

    # Try live Neo4j if available
    if store.verify_connection():
        try:
            raw_graph = store.get_complete_case_graph(case_id)
            if raw_graph and (raw_graph["entities"] or raw_graph["relationships"]):
                graph_data = raw_graph
        except Exception as e:
            logger.warning("Neo4j retrieval error for case %s: %s", case_id, e)

    # Fallback to persistent storage cache if Neo4j is offline or empty for this case
    if not graph_data:
        graph_data = _load_cached_graph(case_id)

    if not graph_data:
        # Return empty structured graph
        graph_data = {
            "case_id": case_id,
            "summary": {
                "entity_count": 0,
                "relationship_count": 0,
                "timeline_event_count": 0,
            },
            "entities": [],
            "relationships": [],
            "timeline_events": [],
        }

    # Overlay user notes & preferences
    prefs = _load_preferences(case_id)
    custom_colors = prefs.get("custom_colors", {})
    for ent in graph_data.get("entities", []):
        eid = ent.get("id")
        if eid:
            ent["user_notes"] = _load_notes(case_id, eid)
            if eid in custom_colors:
                ent["custom_color"] = custom_colors[eid]

    graph_data["preferences"] = prefs
    return graph_data


@router.get("/{case_id}/neighbors/{node_id}")
def get_node_neighbors(
    case_id: str = FPath(..., description="Case identifier"),
    node_id: str = FPath(..., description="Target entity ID to expand"),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Progressively expands a selected entity by retrieving its 1-hop connected neighbors
    and connecting edges. Enforces strict case isolation.
    """
    case_id = case_id.strip()
    node_id = node_id.strip()

    # Query live Neo4j
    if store.verify_connection():
        try:
            driver = store.connect()
            query = """
            MATCH (s:LegalEntity {id: $node_id, case_id: $case_id})-[r]-(t:LegalEntity {case_id: $case_id})
            RETURN properties(t) AS neighbor, properties(r) AS rel, type(r) AS rel_type,
                   startNode(r).id AS source_id, endNode(r).id AS target_id
            """
            with driver.session(database=store.database) as session:
                result = session.run(query, node_id=node_id, case_id=case_id)
                neighbors = []
                relationships = []
                seen_nodes = set()
                for rec in result:
                    n_props = rec["neighbor"]
                    if n_props["id"] not in seen_nodes:
                        seen_nodes.add(n_props["id"])
                        neighbors.append(dict(n_props))
                    r_props = dict(rec["rel"])
                    r_props["relationship_type"] = rec["rel_type"]
                    r_props["source_id"] = rec["source_id"]
                    r_props["target_id"] = rec["target_id"]
                    relationships.append(r_props)
                return {
                    "case_id": case_id,
                    "target_node_id": node_id,
                    "neighbors": neighbors,
                    "relationships": relationships,
                }
        except Exception as e:
            logger.warning("Neo4j neighbor query note: %s", e)

    # Fallback to cached graph filtering
    full_graph = _load_cached_graph(case_id) or {"entities": [], "relationships": []}
    rel_matches = [
        r
        for r in full_graph.get("relationships", [])
        if r.get("source_id") == node_id or r.get("target_id") == node_id
    ]
    neighbor_ids = {
        r["target_id"] if r["source_id"] == node_id else r["source_id"]
        for r in rel_matches
    }
    neighbor_nodes = [
        e for e in full_graph.get("entities", []) if e.get("id") in neighbor_ids
    ]
    return {
        "case_id": case_id,
        "target_node_id": node_id,
        "neighbors": neighbor_nodes,
        "relationships": rel_matches,
    }


@router.post("/{case_id}/entities")
def create_entity(
    case_id: str = FPath(..., description="Case identifier"),
    req: CreateEntityRequest = ...,
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Creates a new canonical legal entity node in the case graph.
    Strictly validates entity_type against ontology constraints.
    """
    case_id = case_id.strip()
    try:
        validated_type = SchemaValidator.validate_entity_type(req.entity_type)
    except InvalidEntityTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    entity_id = f"ent_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    new_entity = {
        "id": entity_id,
        "case_id": case_id,
        "canonical_name": req.canonical_name.strip(),
        "normalized_name": req.canonical_name.strip().lower(),
        "entity_type": validated_type.value,
        "aliases": req.aliases or [],
        "source_text": req.source_text or req.description or "User created entity",
        "confidence": 1.0,
        "trust_status": "APPROVED",
        "extraction_method": "MANUAL_HUMAN",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    # 1. Update live Neo4j if available
    if store.verify_connection():
        try:
            store.upsert_entities([new_entity], case_id=case_id)
        except Exception as e:
            logger.error("Failed to persist entity in Neo4j: %s", e)
            raise HTTPException(
                status_code=500, detail=f"Database write failed: {str(e)}"
            )

    # 2. Update storage cache
    graph = _load_cached_graph(case_id) or {
        "case_id": case_id,
        "summary": {
            "entity_count": 0,
            "relationship_count": 0,
            "timeline_event_count": 0,
        },
        "entities": [],
        "relationships": [],
        "timeline_events": [],
    }
    graph["entities"].append(new_entity)
    graph["summary"]["entity_count"] = len(graph["entities"])
    _save_cached_graph(case_id, graph)

    return new_entity


@router.put("/{case_id}/entities/{entity_id}")
def update_entity(
    case_id: str = FPath(..., description="Case identifier"),
    entity_id: str = FPath(..., description="Target entity ID to update"),
    req: UpdateEntityRequest = ...,
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Updates properties of an existing canonical entity node.
    Enforces case isolation and ontology validation.
    """
    case_id = case_id.strip()
    entity_id = entity_id.strip()

    updates: Dict[str, Any] = {}
    if req.canonical_name:
        updates["canonical_name"] = req.canonical_name.strip()
        updates["normalized_name"] = req.canonical_name.strip().lower()
    if req.aliases is not None:
        updates["aliases"] = req.aliases
    if req.entity_type:
        try:
            validated_type = SchemaValidator.validate_entity_type(req.entity_type)
            updates["entity_type"] = validated_type.value
        except InvalidEntityTypeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    now_iso = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now_iso

    # Update Neo4j if online
    if store.verify_connection():
        driver = store.connect()
        set_clauses = ["n.updated_at = $updated_at"]
        params: Dict[str, Any] = {
            "entity_id": entity_id,
            "case_id": case_id,
            "updated_at": now_iso,
        }

        if "canonical_name" in updates:
            set_clauses.append("n.canonical_name = $cname, n.normalized_name = $nname")
            params["cname"] = updates["canonical_name"]
            params["nname"] = updates["normalized_name"]
        if "entity_type" in updates:
            set_clauses.append("n.entity_type = $etype")
            params["etype"] = updates["entity_type"]
        if "aliases" in updates:
            set_clauses.append("n.aliases = $aliases")
            params["aliases"] = updates["aliases"]

        query = f"""
        MATCH (n:LegalEntity {{id: $entity_id, case_id: $case_id}})
        SET {', '.join(set_clauses)}
        RETURN properties(n) AS entity
        """
        with driver.session(database=store.database) as session:
            res = session.run(query, **params)
            record = res.single()
            if not record:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entity '{entity_id}' not found in case '{case_id}'.",
                )

    # Update cache
    graph = _load_cached_graph(case_id)
    if graph:
        found = False
        for ent in graph.get("entities", []):
            if ent.get("id") == entity_id:
                ent.update(updates)
                found = True
                break
        if found:
            _save_cached_graph(case_id, graph)

    return {
        "status": "UPDATED",
        "entity_id": entity_id,
        "case_id": case_id,
        "updates": updates,
    }


@router.delete("/{case_id}/entities/{entity_id}")
def delete_entity(
    case_id: str = FPath(..., description="Case identifier"),
    entity_id: str = FPath(..., description="Target entity ID to delete"),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Deletes an entity node from the case graph and detaches connected relationships.
    Enforces case scoping and reports the count of removed relationships.
    """
    case_id = case_id.strip()
    entity_id = entity_id.strip()
    detached_count = 0

    if store.verify_connection():
        driver = store.connect()
        # Count connected edges first to report to user
        count_query = """
        MATCH (n:LegalEntity {id: $entity_id, case_id: $case_id})-[r]-()
        RETURN count(r) AS rel_count
        """
        del_query = """
        MATCH (n:LegalEntity {id: $entity_id, case_id: $case_id})
        DETACH DELETE n
        """
        with driver.session(database=store.database) as session:
            res = session.run(count_query, entity_id=entity_id, case_id=case_id)
            rec = res.single()
            if rec:
                detached_count = rec["rel_count"]
            session.run(del_query, entity_id=entity_id, case_id=case_id)

    # Update cache
    graph = _load_cached_graph(case_id)
    if graph:
        initial_ents = len(graph.get("entities", []))
        graph["entities"] = [
            e for e in graph.get("entities", []) if e.get("id") != entity_id
        ]
        if not detached_count:
            # calculate from cache
            detached_count = len(
                [
                    r
                    for r in graph.get("relationships", [])
                    if r.get("source_id") == entity_id
                    or r.get("target_id") == entity_id
                ]
            )
        graph["relationships"] = [
            r
            for r in graph.get("relationships", [])
            if r.get("source_id") != entity_id and r.get("target_id") != entity_id
        ]
        graph["summary"]["entity_count"] = len(graph["entities"])
        graph["summary"]["relationship_count"] = len(graph["relationships"])
        _save_cached_graph(case_id, graph)

    return {
        "status": "DELETED",
        "entity_id": entity_id,
        "case_id": case_id,
        "relationships_detached": detached_count,
    }


@router.post("/{case_id}/relationships")
def create_relationship(
    case_id: str = FPath(..., description="Case identifier"),
    req: CreateRelationshipRequest = ...,
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Creates a new validated relationship edge between two entities in the same case.
    Strictly verifies that:
      1. Source and target belong to the same case.
      2. No self-loop edges.
      3. Triplet satisfies Step 1 ontology constraints via SchemaValidator.validate_triplet.
    """
    case_id = case_id.strip()
    if req.source_id == req.target_id:
        raise HTTPException(
            status_code=400, detail="Accidental self-linking is not permitted."
        )

    # 1. Determine entity types for source and target
    source_type_str: Optional[str] = None
    target_type_str: Optional[str] = None
    source_name = req.source_id
    target_name = req.target_id

    # Check live Neo4j
    if store.verify_connection():
        driver = store.connect()
        query = """
        MATCH (n:LegalEntity {case_id: $case_id})
        WHERE n.id IN [$src_id, $tgt_id]
        RETURN n.id AS id, n.entity_type AS entity_type, n.canonical_name AS canonical_name
        """
        with driver.session(database=store.database) as session:
            res = session.run(
                query, case_id=case_id, src_id=req.source_id, tgt_id=req.target_id
            )
            for rec in res:
                if rec["id"] == req.source_id:
                    source_type_str = rec["entity_type"]
                    source_name = rec["canonical_name"]
                elif rec["id"] == req.target_id:
                    target_type_str = rec["entity_type"]
                    target_name = rec["canonical_name"]

    # Fallback to cache lookup if needed
    if not source_type_str or not target_type_str:
        graph = _load_cached_graph(case_id) or {"entities": []}
        for e in graph.get("entities", []):
            if e.get("id") == req.source_id:
                source_type_str = e.get("entity_type")
                source_name = e.get("canonical_name", req.source_id)
            elif e.get("id") == req.target_id:
                target_type_str = e.get("entity_type")
                target_name = e.get("canonical_name", req.target_id)

    if not source_type_str or not target_type_str:
        raise HTTPException(
            status_code=400,
            detail=f"Both entities must exist in case '{case_id}'. (Found source: {bool(source_type_str)}, target: {bool(target_type_str)})",
        )

    # 2. Strict Triplet Ontology Validation
    try:
        rel_type_enum = SchemaValidator.validate_relationship_type(
            req.relationship_type
        )
        src_type_enum = SchemaValidator.validate_entity_type(source_type_str)
        tgt_type_enum = SchemaValidator.validate_entity_type(target_type_str)
        SchemaValidator.validate_triplet(
            src_type_enum, rel_type_enum, tgt_type_enum, allow_subtype_inheritance=True
        )
    except (
        InvalidRelationshipTypeError,
        InvalidEntityTypeError,
        TripletConstraintViolationError,
    ) as ex:
        raise HTTPException(status_code=400, detail=str(ex))

    rel_id = f"rel_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    new_rel = {
        "id": rel_id,
        "relationship_type": rel_type_enum.value,
        "source_id": req.source_id,
        "source_name": source_name,
        "target_id": req.target_id,
        "target_name": target_name,
        "confidence": req.confidence or 1.0,
        "source_text": req.source_text or "User created relationship",
        "trust_status": "APPROVED",
        "extraction_method": "MANUAL_HUMAN",
        "created_at": now_iso,
    }

    # Persist into Neo4j
    if store.verify_connection():
        try:
            store.upsert_relationships([new_rel], case_id=case_id)
        except Exception as e:
            logger.error("Failed to upsert relationship into Neo4j: %s", e)
            raise HTTPException(
                status_code=500, detail=f"Database write failed: {str(e)}"
            )

    # Update cache
    graph = _load_cached_graph(case_id)
    if graph:
        graph.setdefault("relationships", []).append(new_rel)
        graph["summary"]["relationship_count"] = len(graph["relationships"])
        _save_cached_graph(case_id, graph)

    return new_rel


@router.delete("/{case_id}/relationships/{relationship_id}")
def delete_relationship(
    case_id: str = FPath(..., description="Case identifier"),
    relationship_id: str = FPath(..., description="Target relationship ID to delete"),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Deletes a relationship edge scoped to the case.
    """
    case_id = case_id.strip()
    relationship_id = relationship_id.strip()

    if store.verify_connection():
        driver = store.connect()
        query = """
        MATCH ()-[r {id: $rel_id, case_id: $case_id}]->()
        DELETE r
        """
        with driver.session(database=store.database) as session:
            session.run(query, rel_id=relationship_id, case_id=case_id)

    # Update cache
    graph = _load_cached_graph(case_id)
    if graph:
        graph["relationships"] = [
            r for r in graph.get("relationships", []) if r.get("id") != relationship_id
        ]
        graph["summary"]["relationship_count"] = len(graph["relationships"])
        _save_cached_graph(case_id, graph)

    return {"status": "DELETED", "relationship_id": relationship_id, "case_id": case_id}


@router.get("/{case_id}/entities/{entity_id}/notes")
def get_entity_notes(
    case_id: str = FPath(..., description="Case identifier"),
    entity_id: str = FPath(..., description="Target entity ID"),
) -> Dict[str, Any]:
    """Retrieves user notes for a specific entity in a case."""
    notes = _load_notes(case_id.strip(), entity_id.strip())
    return {"case_id": case_id, "entity_id": entity_id, "notes": notes}


@router.put("/{case_id}/entities/{entity_id}/notes")
def save_entity_notes(
    case_id: str = FPath(..., description="Case identifier"),
    entity_id: str = FPath(..., description="Target entity ID"),
    req: SaveNotesRequest = ...,
    store: Neo4jGraphStore = Depends(get_neo4j_store),
) -> Dict[str, Any]:
    """
    Saves user notes for an entity server-side.
    Preserves extracted entity descriptions intact.
    """
    case_id = case_id.strip()
    entity_id = entity_id.strip()
    _save_notes(case_id, entity_id, req.notes)

    # Sync to Neo4j node property if available
    if store.verify_connection():
        try:
            driver = store.connect()
            query = """
            MATCH (n:LegalEntity {id: $entity_id, case_id: $case_id})
            SET n.user_notes = $notes, n.notes_updated_at = $updated_at
            RETURN n.id AS id
            """
            with driver.session(database=store.database) as session:
                session.run(
                    query,
                    entity_id=entity_id,
                    case_id=case_id,
                    notes=req.notes,
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
        except Exception as e:
            logger.warning("Note Neo4j sync note: %s", e)

    return {
        "status": "SAVED",
        "case_id": case_id,
        "entity_id": entity_id,
        "notes": req.notes,
    }


@router.get("/{case_id}/preferences")
def get_graph_preferences(
    case_id: str = FPath(..., description="Case identifier"),
) -> Dict[str, Any]:
    """Retrieves presentation preferences (custom node colors, preferred layout)."""
    return _load_preferences(case_id.strip())


@router.put("/{case_id}/preferences")
def save_graph_preferences(
    case_id: str = FPath(..., description="Case identifier"),
    req: SavePreferencesRequest = ...,
) -> Dict[str, Any]:
    """Saves presentation preferences (custom node colors, preferred layout) server-side."""
    case_id = case_id.strip()
    existing = _load_preferences(case_id)
    if req.custom_colors is not None:
        existing["custom_colors"] = req.custom_colors
    if req.preferred_layout:
        existing["preferred_layout"] = req.preferred_layout
    _save_preferences(case_id, existing)
    return {"status": "SAVED", "case_id": case_id, "preferences": existing}
