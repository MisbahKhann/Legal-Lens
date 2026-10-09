"""
Pydantic data models for Step 10: Local LLM Fallback & Ambiguous Extraction Resolution.
Provides structured containers for targeted LLM input context and structured LLM responses.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class AmbiguityType(str, Enum):
    """Categorization of legal extraction ambiguities requiring LLM fallback."""

    ENTITY_TYPE = "ENTITY_TYPE"
    ENTITY_IDENTITY = "ENTITY_IDENTITY"
    RELATIONSHIP_TYPE = "RELATIONSHIP_TYPE"
    TEMPORAL_INTERPRETATION = "TEMPORAL_INTERPRETATION"
    CONFLICTING_EXTRACTION = "CONFLICTING_EXTRACTION"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"


class LLMDecision(str, Enum):
    """LLM resolution decision outcome."""

    RESOLVED = "RESOLVED"
    UNCERTAIN = "UNCERTAIN"
    REJECTED = "REJECTED"


class LLMFallbackRequest(BaseModel):
    """
    Narrow context payload provided to the LLM fallback service.
    Contains strictly the text and candidate options required to resolve an ambiguity.
    """

    request_id: str = Field(
        default_factory=lambda: f"req_llm_{uuid4().hex[:12]}",
        description="Unique identifier for the LLM fallback request.",
    )
    case_id: str = Field(..., description="Unique case identifier.")
    source_document_id: str = Field(..., description="Source document identifier.")
    source_page: Optional[int] = Field(
        default=1, description="1-indexed source document page number."
    )
    source_text: str = Field(
        ..., description="Verbatim text snippet/sentence containing ambiguity."
    )
    char_span: Optional[Tuple[int, int]] = Field(
        default=None, description="Character offsets within source text/document."
    )

    ambiguity_type: AmbiguityType = Field(
        ..., description="Type of ambiguity needing resolution."
    )

    # Candidate options for resolution
    candidate_entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of candidate entity dicts under consideration.",
    )
    candidate_relationships: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of candidate relationship dicts under consideration.",
    )
    candidate_dates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of candidate temporal expressions or events.",
    )

    # Ontology boundaries
    allowed_entity_types: List[str] = Field(
        default_factory=list,
        description="Restricted subset of allowed Step 1 EntityType strings.",
    )
    allowed_relationship_types: List[str] = Field(
        default_factory=list,
        description="Restricted subset of allowed Step 1 RelationshipType strings.",
    )

    original_extraction_method: str = Field(
        default="DETERMINISTIC_RULE",
        description="Extraction method of original candidate (e.g., DETERMINISTIC_RULE, GLINER_RELEX).",
    )
    provenance_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context metadata to attach to audit history.",
    )


class LLMFallbackResponse(BaseModel):
    """
    Structured resolution response returned by local LLM and validated against ontology.
    """

    response_id: str = Field(
        default_factory=lambda: f"res_llm_{uuid4().hex[:12]}",
        description="Unique identifier for the response.",
    )
    request_id: Optional[str] = Field(
        default=None, description="Associated fallback request ID."
    )
    decision: LLMDecision = Field(
        ..., description="Resolution decision (RESOLVED, UNCERTAIN, REJECTED)."
    )

    selected_entity_type: Optional[str] = Field(
        default=None, description="Selected entity type string if resolving entity."
    )
    selected_entity_name: Optional[str] = Field(
        default=None, description="Selected canonical entity name if resolving entity."
    )

    selected_relationship_type: Optional[str] = Field(
        default=None,
        description="Selected relationship type string if resolving relation.",
    )
    source_entity_name: Optional[str] = Field(
        default=None, description="Source entity name for selected relationship."
    )
    target_entity_name: Optional[str] = Field(
        default=None, description="Target entity name for selected relationship."
    )

    selected_temporal_interpretation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Temporal resolution details if resolving dates/events.",
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="LLM prediction confidence score (0.0 to 1.0).",
    )
    reasoning: str = Field(
        default="", description="Brief evidence/rationale summary provided by LLM."
    )
    needs_human_review: bool = Field(
        default=False,
        description="Flag indicating whether item requires escalation to Step 9 human review.",
    )

    # Provider & Audit Metadata
    llm_provider: str = Field(
        default="ollama", description="LLM provider name (e.g. ollama)."
    )
    llm_model: str = Field(
        default="qwen2.5:1.5b", description="LLM model identifier used."
    )
    raw_response: Optional[str] = Field(
        default=None, description="Raw text JSON payload returned by LLM."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of resolution generation.",
    )

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))
