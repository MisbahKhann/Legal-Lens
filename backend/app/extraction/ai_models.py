"""
Data models for Step 4: AI-based Entity & Relationship Extraction using GLiNER-Relex.
Provides standardized containers for candidate entities, candidate relationships, AI results,
and combined extraction results (Step 3 + Step 4).
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from uuid import uuid4
from pydantic import BaseModel, Field

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import ExtractionMethod
from app.extraction.models import DeterministicExtractionResult, ExtractedCandidateEntity


class CandidateEntity(BaseModel):
    """
    Standardized Candidate Entity extracted via AI model (GLiNER-Relex).
    Preserves document ID, page number, char offsets, source text, confidence,
    and exact extraction method.
    """
    entity_id: str = Field(
        default_factory=lambda: f"ai_ent_{uuid4().hex[:12]}",
        description="Unique identifier for the AI candidate entity."
    )
    entity_type: EntityType = Field(..., description="Step 1 controlled EntityType enum value.")
    text: str = Field(..., description="Raw extracted text for entity.")
    normalized_value: Any = Field(default="", description="Normalized value representation.")
    document_id: str = Field(..., description="Source legal document ID.")
    case_id: Optional[str] = Field(default=None, description="Associated case identifier if known.")
    page_number: int = Field(..., ge=1, description="1-indexed page number where entity was extracted.")
    section_id: Optional[str] = Field(default=None, description="Section ID if available.")
    chunk_id: Optional[str] = Field(default=None, description="Chunk ID from document chunker.")
    source_text: str = Field(..., description="Verbatim text context/snippet containing the entity.")
    start_offset: int = Field(..., ge=0, description="Character start offset in source_text or chunk.")
    end_offset: int = Field(..., ge=0, description="Character end offset in source_text or chunk.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model prediction confidence score (0.0 to 1.0)."
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.GLINER_RELEX,
        description="Extraction methodology used ('gliner_relex')."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional model or extraction metadata."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of extraction."
    )


class CandidateRelation(BaseModel):
    """
    Standardized Candidate Relationship extracted via AI model (GLiNER-Relex).
    Links a source CandidateEntity to a target CandidateEntity and preserves full provenance
    and validation status against Step 1 ontology constraints.
    """
    relation_id: str = Field(
        default_factory=lambda: f"ai_rel_{uuid4().hex[:12]}",
        description="Unique identifier for the AI candidate relationship."
    )
    relation_type: RelationshipType = Field(..., description="Step 1 controlled RelationshipType enum value.")
    source_entity: CandidateEntity = Field(..., description="Source candidate entity.")
    target_entity: CandidateEntity = Field(..., description="Target candidate entity.")
    document_id: str = Field(..., description="Source legal document ID.")
    case_id: Optional[str] = Field(default=None, description="Associated case identifier.")
    page_number: int = Field(..., ge=1, description="1-indexed page number where relationship was extracted.")
    source_text: str = Field(..., description="Verbatim text snippet/sentence containing the relationship.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of relationship extraction."
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.GLINER_RELEX,
        description="Extraction methodology used ('gliner_relex')."
    )
    is_valid: bool = Field(
        default=True,
        description="Whether this relationship satisfies Step 1 triplet constraints."
    )
    validation_error: Optional[str] = Field(
        default=None,
        description="Details of constraint violation if invalid."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional extraction metadata."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of extraction."
    )


class AIExtractionResult(BaseModel):
    """
    Container summarizing all AI candidate entities and relationships extracted from a LegalDocument.
    """
    document_id: str = Field(..., description="Source document identifier.")
    case_id: Optional[str] = Field(default=None, description="Associated case identifier.")
    model_name: str = Field(default="knowledgator/gliner-multitask-large-v0.5", description="Model name used for extraction.")
    entities: List[CandidateEntity] = Field(default_factory=list, description="Extracted candidate entities.")
    relations: List[CandidateRelation] = Field(default_factory=list, description="Extracted candidate relations.")
    rejected_relations: List[CandidateRelation] = Field(
        default_factory=list,
        description="Relationships rejected due to schema constraint violations."
    )
    summary_counts: Dict[str, int] = Field(default_factory=dict, description="Summary counts of entities and relations.")
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution timestamp."
    )


class CombinedExtractionResult(BaseModel):
    """
    Unified result structure combining Step 3 deterministic extractions and Step 4 AI extractions.
    Ensures clear separation of extraction sources without overwriting either.
    """
    document_id: str = Field(..., description="Source legal document ID.")
    case_id: Optional[str] = Field(default=None, description="Associated case identifier.")
    deterministic_result: DeterministicExtractionResult = Field(..., description="Step 3 extractions.")
    ai_result: AIExtractionResult = Field(..., description="Step 4 GLiNER-Relex extractions.")
    total_deterministic_entities: int = Field(default=0)
    total_ai_entities: int = Field(default=0)
    total_ai_relations: int = Field(default=0)
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of combined pipeline execution."
    )
