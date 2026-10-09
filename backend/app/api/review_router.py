"""
FastAPI APIRouter for Step 9: Human-in-the-Loop Review & Graph Correction.
Provides endpoints for retrieving review items, approving, rejecting, correcting,
merging entities, keeping entities separate, and viewing audit trails.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.review.models import (
    ItemType,
    ReviewStatus,
    ReviewItem,
    AuditRecord,
    ApproveRequest,
    RejectRequest,
    MergeEntitiesRequest,
    KeepSeparateRequest,
)
from app.review.manager import ReviewManager
from app.schema.validator import SchemaValidationError
from app.storage.neo4j_store import Neo4jGraphStore

# Global singleton review manager instance for the app backend
global_review_manager = ReviewManager()
global_neo4j_store = Neo4jGraphStore()

router = APIRouter(prefix="/api/v1/review", tags=["human-review"])


def get_manager() -> ReviewManager:
    return global_review_manager


def get_neo4j_store() -> Neo4jGraphStore:
    return global_neo4j_store


@router.get("/{case_id}/items", response_model=List[ReviewItem])
def get_case_review_items(
    case_id: str = Path(..., description="Case identifier"),
    status: Optional[ReviewStatus] = Query(None, description="Filter by ReviewStatus"),
    item_type: Optional[ItemType] = Query(None, description="Filter by ItemType"),
    manager: ReviewManager = Depends(get_manager),
):
    """
    Retrieves candidate review items for a specific case.
    Exposes complete provenance and source text context for human review.
    """
    return manager.get_review_items_for_case(
        case_id=case_id, status=status, item_type=item_type
    )


@router.get("/items/{review_id}", response_model=ReviewItem)
def get_review_item(
    review_id: str = Path(..., description="Unique review item ID"),
    manager: ReviewManager = Depends(get_manager),
):
    """
    Retrieves detailed source context and prediction for a single review item.
    """
    item = manager.get_review_item(review_id)
    if not item:
        raise HTTPException(
            status_code=404, detail=f"Review item '{review_id}' not found."
        )
    return item


@router.get("/{case_id}/audit-trail", response_model=List[AuditRecord])
def get_case_audit_trail(
    case_id: str = Path(..., description="Case identifier"),
    manager: ReviewManager = Depends(get_manager),
):
    """
    Retrieves immutable audit trail history of human review decisions for a case.
    """
    return manager.get_audit_trail_for_case(case_id=case_id)


@router.post("/items/{review_id}/approve", response_model=ReviewItem)
def approve_review_item(
    review_id: str = Path(..., description="Unique review item ID"),
    req: ApproveRequest = ...,
    manager: ReviewManager = Depends(get_manager),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
):
    """
    Approves a candidate item as trusted knowledge without modifications.
    """
    try:
        return manager.approve_item(
            review_id=review_id,
            reviewer_id=req.reviewer_id,
            reviewer_note=req.reviewer_note,
            neo4j_store=store,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/{review_id}/reject", response_model=ReviewItem)
def reject_review_item(
    review_id: str = Path(..., description="Unique review item ID"),
    req: RejectRequest = ...,
    manager: ReviewManager = Depends(get_manager),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
):
    """
    Rejects a candidate extraction, preventing it from becoming trusted graph knowledge.
    """
    try:
        return manager.reject_item(
            review_id=review_id,
            reviewer_id=req.reviewer_id,
            reviewer_note=req.reviewer_note,
            neo4j_store=store,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/{review_id}/correct", response_model=ReviewItem)
def correct_review_item(
    review_id: str = Path(..., description="Unique review item ID"),
    corrections: Dict[str, Any] = ...,
    reviewer_id: str = Query(..., description="Reviewer user ID"),
    reviewer_note: Optional[str] = Query(None, description="Optional reviewer note"),
    manager: ReviewManager = Depends(get_manager),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
):
    """
    Applies human corrections to an item while preserving original prediction.
    Strictly validates corrections against Step 1 ontology constraints.
    """
    item = manager.get_review_item(review_id)
    if not item:
        raise HTTPException(
            status_code=404, detail=f"Review item '{review_id}' not found."
        )

    try:
        if item.item_type == ItemType.ENTITY:
            return manager.correct_entity(
                review_id=review_id,
                reviewer_id=reviewer_id,
                corrected_fields=corrections,
                reviewer_note=reviewer_note,
                neo4j_store=store,
            )
        elif item.item_type == ItemType.RELATIONSHIP:
            return manager.correct_relationship(
                review_id=review_id,
                reviewer_id=reviewer_id,
                corrected_fields=corrections,
                reviewer_note=reviewer_note,
                neo4j_store=store,
            )
        elif item.item_type in [ItemType.EVENT, ItemType.TEMPORAL]:
            return manager.correct_temporal(
                review_id=review_id,
                reviewer_id=reviewer_id,
                corrected_fields=corrections,
                reviewer_note=reviewer_note,
                neo4j_store=store,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Item type '{item.item_type}' does not support generic correction.",
            )
    except SchemaValidationError as e:
        raise HTTPException(
            status_code=400, detail=f"Ontology validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge", response_model=AuditRecord)
def merge_entities_endpoint(
    req: MergeEntitiesRequest,
    review_id: Optional[str] = Query(None, description="Optional review item ID"),
    manager: ReviewManager = Depends(get_manager),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
):
    """
    Merges two canonical entities, preserving provenance evidence and updating relationships.
    Enforces case isolation.
    """
    try:
        return manager.merge_entities(
            case_id=req.case_id,
            primary_entity_id=req.primary_entity_id,
            secondary_entity_id=req.secondary_entity_id,
            reviewer_id=req.reviewer_id,
            reviewer_note=req.reviewer_note,
            review_id=review_id,
            neo4j_store=store,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keep-separate", response_model=AuditRecord)
def keep_separate_endpoint(
    req: KeepSeparateRequest,
    review_id: Optional[str] = Query(None, description="Optional review item ID"),
    manager: ReviewManager = Depends(get_manager),
    store: Neo4jGraphStore = Depends(get_neo4j_store),
):
    """
    Explicitly retains two ambiguous entities as separate canonical entities.
    """
    try:
        return manager.keep_entities_separate(
            case_id=req.case_id,
            entity_id_1=req.entity_id_1,
            entity_id_2=req.entity_id_2,
            reviewer_id=req.reviewer_id,
            reviewer_note=req.reviewer_note,
            review_id=review_id,
            neo4j_store=store,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
