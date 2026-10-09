"""
Data models and Enums for Step 9: Human-in-the-Loop Review & Graph Correction API.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Category of legal information item requiring human review."""

    ENTITY = "ENTITY"
    RELATIONSHIP = "RELATIONSHIP"
    EVENT = "EVENT"
    ENTITY_MERGE = "ENTITY_MERGE"
    ENTITY_SPLIT = "ENTITY_SPLIT"
    TEMPORAL = "TEMPORAL"


class ReviewStatus(str, Enum):
    """Lifecycle status of a human review item."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"


class TrustStatus(str, Enum):
    """Graph assertion trust classification distinguishing system AI extractions from reviewed data."""

    EXTRACTED = "EXTRACTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"
    MERGED = "MERGED"
    KEPT_SEPARATE = "KEPT_SEPARATE"


class ReviewItem(BaseModel):
    """
    Structured candidate item flagged for human review.
    Exposes complete provenance and source context to allow lawyer inspection.
    """

    review_id: str = Field(
        default_factory=lambda: f"rev_{uuid4().hex[:12]}",
        description="Unique identifier for the review item.",
    )
    case_id: str = Field(..., description="Unique case identifier.")
    item_type: ItemType = Field(..., description="Category of candidate item.")
    status: ReviewStatus = Field(
        default=ReviewStatus.PENDING, description="Current review status."
    )

    entity_id: Optional[str] = Field(
        default=None, description="Target canonical entity ID if applicable."
    )
    relationship_id: Optional[str] = Field(
        default=None, description="Target relationship ID if applicable."
    )
    event_id: Optional[str] = Field(
        default=None, description="Target timeline event ID if applicable."
    )

    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Extraction confidence score."
    )
    reason: Optional[str] = Field(
        default=None, description="Explanation why item required review."
    )
    validation_rule: Optional[str] = Field(
        default=None, description="Violated validation rule if applicable."
    )

    original_prediction: Dict[str, Any] = Field(
        ..., description="Complete original AI/system prediction payload."
    )
    corrected_value: Optional[Dict[str, Any]] = Field(
        default=None, description="Human corrected fields payload."
    )

    # Source Provenance & Context
    source_document_id: Optional[str] = Field(
        default=None, description="Source document identifier."
    )
    source_page: Optional[int] = Field(
        default=None, description="Source document page number."
    )
    source_text: Optional[str] = Field(
        default=None, description="Verbatim source sentence or snippet."
    )
    source_span: Optional[Tuple[int, int]] = Field(
        default=None, description="Character offsets within document."
    )
    extraction_method: Optional[str] = Field(
        default=None, description="Model/Extraction method (e.g. GLINER_RELEX, RULE)."
    )
    provenance_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Rich source coordinates and entity/relationship context.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when review candidate was created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when review item was last updated.",
    )
    reviewed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when human review occurred."
    )
    reviewed_by: Optional[str] = Field(
        default=None, description="Identifier of the human reviewer."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Notes/justification provided by human reviewer."
    )


class AuditRecord(BaseModel):
    """
    Immutable audit log entry recording every human decision.
    """

    audit_id: str = Field(
        default_factory=lambda: f"aud_{uuid4().hex[:12]}",
        description="Unique identifier for audit log entry.",
    )
    review_id: str = Field(..., description="Associated review item ID.")
    case_id: str = Field(..., description="Associated case ID.")
    reviewer_id: str = Field(..., description="Identifier of the reviewer.")
    decision: str = Field(
        ...,
        description="Review action (e.g., APPROVED, REJECTED, CORRECTED, MERGED, KEPT_SEPARATE).",
    )
    original_value: Dict[str, Any] = Field(
        ..., description="Original extracted prediction value."
    )
    corrected_value: Optional[Dict[str, Any]] = Field(
        default=None, description="Human corrected value if applicable."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Reviewer note or rationale."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution timestamp.",
    )


# DTO Schemas for API Requests/Responses


class ApproveRequest(BaseModel):
    reviewer_id: str = Field(
        ..., min_length=1, description="ID of lawyer/user performing review."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Optional note for decision."
    )


class RejectRequest(BaseModel):
    reviewer_id: str = Field(
        ..., min_length=1, description="ID of lawyer/user performing review."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Optional reason for rejection."
    )


class CorrectEntityRequest(BaseModel):
    reviewer_id: str = Field(
        ..., min_length=1, description="ID of lawyer/user performing review."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Optional review note."
    )
    entity_type: Optional[str] = Field(
        default=None, description="Corrected entity type."
    )
    canonical_name: Optional[str] = Field(
        default=None, description="Corrected canonical name."
    )
    normalized_name: Optional[str] = Field(
        default=None, description="Corrected normalized name."
    )
    aliases: Optional[List[str]] = Field(
        default=None, description="Corrected aliases list."
    )


class CorrectRelationshipRequest(BaseModel):
    reviewer_id: str = Field(
        ..., min_length=1, description="ID of lawyer/user performing review."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Optional review note."
    )
    relationship_type: Optional[str] = Field(
        default=None, description="Corrected relationship type."
    )
    source_id: Optional[str] = Field(
        default=None, description="Corrected source entity ID."
    )
    target_id: Optional[str] = Field(
        default=None, description="Corrected target entity ID."
    )


class CorrectTemporalRequest(BaseModel):
    reviewer_id: str = Field(
        ..., min_length=1, description="ID of lawyer/user performing review."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Optional review note."
    )
    event_date: Optional[str] = Field(
        default=None, description="Corrected event ISO date string."
    )
    start_date: Optional[str] = Field(
        default=None, description="Corrected start ISO date string."
    )
    end_date: Optional[str] = Field(
        default=None, description="Corrected end ISO date string."
    )
    date_precision: Optional[str] = Field(
        default=None, description="Corrected date precision."
    )
    event_type: Optional[str] = Field(
        default=None, description="Corrected event entity type."
    )
    description: Optional[str] = Field(
        default=None, description="Corrected event description."
    )


class MergeEntitiesRequest(BaseModel):
    reviewer_id: str = Field(
        ..., min_length=1, description="ID of lawyer/user performing review."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Optional review note."
    )
    primary_entity_id: str = Field(
        ..., description="Canonical entity ID to keep as primary."
    )
    secondary_entity_id: str = Field(
        ..., description="Canonical entity ID to merge into primary."
    )
    case_id: str = Field(..., description="Case identifier.")


class KeepSeparateRequest(BaseModel):
    reviewer_id: str = Field(
        ..., min_length=1, description="ID of lawyer/user performing review."
    )
    reviewer_note: Optional[str] = Field(
        default=None, description="Optional review note."
    )
    entity_id_1: str = Field(..., description="First entity ID.")
    entity_id_2: str = Field(..., description="Second entity ID.")
    case_id: str = Field(..., description="Case identifier.")
