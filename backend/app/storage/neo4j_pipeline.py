"""
Step 8 Storage Pipeline: Neo4j Knowledge Graph Import.
Converts Step 6 ValidationResult and Step 7 CaseTimeline into Neo4j graph elements.
Enforces case isolation, provenance preservation, invalid record exclusion, and idempotency.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.validation.models import ValidationResult

from app.temporal.models import CaseTimeline
from app.storage.neo4j_store import Neo4jGraphStore

logger = logging.getLogger(__name__)


class Neo4jStoragePipeline:
    """
    Step 8 Knowledge Graph Storage Pipeline.
    """

    def __init__(self, store: Optional[Neo4jGraphStore] = None):
        self.store = store or Neo4jGraphStore()

    def import_case_graph(
        self,
        validation_result: ValidationResult,
        case_timeline: CaseTimeline,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes Step 8 import of validated entities, relationships, and temporal timeline events.

        Args:
            validation_result: Step 6 validation pipeline output.
            case_timeline: Step 7 temporal pipeline output.
            case_id: Optional explicit case ID override. If not specified, uses pipeline case_id.

        Returns:
            Dict containing import status and summary counts.
        """
        resolved_case_id = (
            case_id
            or validation_result.case_id
            or case_timeline.case_id
            or f"case_{validation_result.document_id}"
        )

        logger.info("Beginning Step 8 Neo4j import for case_id: %s", resolved_case_id)

        # 1. Setup Neo4j Schema (indexes & constraints)
        try:
            self.store.setup_schema()
        except Exception as e:
            logger.warning("Schema setup note: %s", str(e))

        # 2. Extract & Format Validated Entities (Filter out any invalid entities)
        invalid_entity_ids = {
            e.canonical_id for e in validation_result.invalid_entities
        }
        valid_entities = [
            e
            for e in validation_result.validated_entities
            if e.canonical_id not in invalid_entity_ids
        ]

        entity_dicts: List[Dict[str, Any]] = []
        for ent in valid_entities:
            # Extract mention provenance details if present
            first_mention = ent.mentions[0] if ent.mentions else None
            source_page = (
                getattr(first_mention, "source_page", None) if first_mention else 1
            )
            source_text = (
                getattr(first_mention, "source_text", ent.canonical_name)
                if first_mention
                else ent.canonical_name
            )
            confidence = (
                getattr(first_mention, "confidence", 1.0) if first_mention else 1.0
            )
            extraction_method = (
                getattr(first_mention, "extraction_method", "GLINER_RELEX")
                if first_mention
                else "GLINER_RELEX"
            )
            if hasattr(extraction_method, "value"):
                extraction_method = extraction_method.value

            entity_type_str = (
                ent.entity_type.value
                if hasattr(ent.entity_type, "value")
                else str(ent.entity_type)
            )

            created_at_str = (
                ent.created_at.isoformat()
                if isinstance(ent.created_at, datetime)
                else str(ent.created_at)
            )

            entity_dicts.append(
                {
                    "id": ent.canonical_id,
                    "canonical_name": ent.canonical_name,
                    "normalized_name": ent.canonical_name.lower().strip(),
                    "entity_type": entity_type_str,
                    "aliases": list(ent.aliases),
                    "document_id": ent.document_id,
                    "source_document_id": ent.document_id,
                    "source_page": source_page or 1,
                    "source_text": source_text,
                    "confidence": float(confidence),
                    "extraction_method": str(extraction_method),
                    "created_at": created_at_str,
                    "updated_at": created_at_str,
                }
            )

        # 3. Extract & Format Validated Relationships (Exclude INVALID & REVIEW_REQUIRED)
        invalid_rel_ids = {
            r.relation_id for r in validation_result.invalid_relationships
        }
        review_required_rel_ids = {
            rec.relationship_id
            for rec in validation_result.review_required
            if rec.relationship_id
        }

        valid_relationships = [
            rel
            for rel in validation_result.validated_relationships
            if rel.is_valid
            and rel.relation_id not in invalid_rel_ids
            and rel.relation_id not in review_required_rel_ids
        ]

        rel_dicts: List[Dict[str, Any]] = []
        for rel in valid_relationships:
            first_mention = rel.mentions[0] if rel.mentions else None
            source_page = (
                getattr(first_mention, "source_page", None) if first_mention else 1
            )
            source_text = (
                getattr(first_mention, "source_text", "") if first_mention else ""
            )
            confidence = (
                getattr(first_mention, "confidence", 1.0) if first_mention else 1.0
            )
            extraction_method = (
                getattr(first_mention, "extraction_method", "GLINER_RELEX")
                if first_mention
                else "GLINER_RELEX"
            )
            if hasattr(extraction_method, "value"):
                extraction_method = extraction_method.value

            rel_type_str = (
                rel.relation_type.value
                if hasattr(rel.relation_type, "value")
                else str(rel.relation_type)
            )

            created_at_str = (
                rel.created_at.isoformat()
                if isinstance(rel.created_at, datetime)
                else str(rel.created_at)
            )

            rel_dicts.append(
                {
                    "id": rel.relation_id,
                    "relationship_type": rel_type_str,
                    "source_id": rel.source_entity_id,
                    "target_id": rel.target_entity_id,
                    "document_id": rel.document_id,
                    "source_document_id": rel.document_id,
                    "source_page": source_page or 1,
                    "source_text": source_text,
                    "confidence": float(confidence),
                    "extraction_method": str(extraction_method),
                    "created_at": created_at_str,
                }
            )

        # 4. Extract & Format Timeline Events (Step 7)
        event_dicts: List[Dict[str, Any]] = []
        for ev in case_timeline.events:
            ev_type_str = (
                ev.event_type.value
                if hasattr(ev.event_type, "value")
                else str(ev.event_type)
            )
            precision_str = (
                ev.date_precision.value
                if hasattr(ev.date_precision, "value")
                else str(ev.date_precision)
            )
            status_str = (
                ev.temporal_status.value
                if hasattr(ev.temporal_status, "value")
                else str(ev.temporal_status)
            )
            method_str = (
                ev.extraction_method.value
                if hasattr(ev.extraction_method, "value")
                else str(ev.extraction_method)
            )

            event_dicts.append(
                {
                    "id": ev.event_id,
                    "description": ev.description,
                    "event_type": ev_type_str,
                    "event_date": ev.event_date,
                    "start_date": ev.start_date,
                    "end_date": ev.end_date,
                    "date_precision": precision_str,
                    "temporal_status": status_str,
                    "confidence": float(ev.confidence),
                    "derived_from": ev.derived_from,
                    "source_document_id": ev.source_document_id,
                    "source_page": ev.source_page or 1,
                    "source_text": ev.source_text or "",
                    "extraction_method": method_str,
                    "canonical_entity_id": ev.canonical_entity_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        # 5. Extract & Format Temporal Relationships
        temp_rel_dicts: List[Dict[str, Any]] = []
        for tr in case_timeline.temporal_relationships:
            rel_type_str = (
                tr.relationship_type.value
                if hasattr(tr.relationship_type, "value")
                else str(tr.relationship_type)
            )
            prov = tr.provenance
            temp_rel_dicts.append(
                {
                    "id": tr.relationship_id,
                    "source_id": tr.source_event_id,
                    "relationship_type": rel_type_str,
                    "target_id": tr.target_event_id,
                    "source_document_id": (
                        prov.source_document_id
                        if prov
                        else validation_result.document_id
                    ),
                    "source_page": prov.source_page if prov else 1,
                    "source_text": prov.source_text if prov else "",
                    "confidence": prov.confidence if prov else 1.0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        # 6. Execute Neo4j Upserts
        imported_entities = self.store.upsert_entities(
            entity_dicts, case_id=resolved_case_id
        )
        imported_relationships = self.store.upsert_relationships(
            rel_dicts, case_id=resolved_case_id
        )
        imported_events = self.store.upsert_timeline_events(
            event_dicts, case_id=resolved_case_id
        )
        imported_temp_rels = self.store.upsert_temporal_relationships(
            temp_rel_dicts, case_id=resolved_case_id
        )

        summary = {
            "status": "SUCCESS",
            "case_id": resolved_case_id,
            "entities_imported": imported_entities,
            "relationships_imported": imported_relationships,
            "timeline_events_imported": imported_events,
            "temporal_relationships_imported": imported_temp_rels,
            "invalid_entities_filtered": len(validation_result.invalid_entities),
            "invalid_relationships_filtered": len(
                validation_result.invalid_relationships
            )
            + len(review_required_rel_ids),
        }

        logger.info("Step 8 Neo4j Import Summary: %s", summary)
        return summary
