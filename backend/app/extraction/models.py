"""
Data models for Step 3: Deterministic Candidate Entity Extractions.
Stores candidate extractions before fusion with downstream AI models (Step 4).
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from uuid import uuid4
from pydantic import BaseModel, Field

from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod


class ExtractedCandidateEntity(BaseModel):
    """
    Standardized container for candidate entities extracted via deterministic/rule-based methods.
    Preserves exact provenance (document ID, page number, char span, raw source text),
    extraction confidence, and normalized values.
    """
    entity_id: str = Field(
        default_factory=lambda: f"cand_{uuid4().hex[:12]}",
        description="Unique identifier for the extracted candidate entity."
    )
    document_id: str = Field(..., description="Source legal document ID.")
    case_id: Optional[str] = Field(default=None, description="Associated case identifier if known.")
    page_number: int = Field(..., ge=1, description="1-indexed page number where extracted.")
    source_text: str = Field(..., description="Verbatim text context/snippet containing the extracted entity.")
    char_span: Optional[Tuple[int, int]] = Field(
        default=None,
        description="[start, end] character offset in page text or source block text."
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.DETERMINISTIC_RULE,
        description="Extraction methodology used."
    )
    rule_name: str = Field(
        default="rule_generic",
        description="Specific pattern or rule name that triggered this extraction."
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Rule certainty / confidence score."
    )
    entity_type: EntityType = Field(..., description="Step 1 ontology EntityType enum value.")
    category: str = Field(
        ...,
        description="Extraction category identifier (e.g. case_citation, statutory_citation, date, docket_number, section_reference, exhibit, filing_type, court_name)."
    )
    original_value: str = Field(..., description="Original raw text expression matched by the rule.")
    normalized_value: Any = Field(..., description="Normalized machine-readable representation.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Category-specific attributes (e.g., volume, reporter, title, section)."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of extraction."
    )


class DeterministicExtractionResult(BaseModel):
    """
    Container summarizing all candidate extractions produced from a LegalDocument.
    """
    document_id: str = Field(..., description="Source document identifier.")
    case_id: Optional[str] = Field(default=None, description="Associated case identifier.")
    candidates: List[ExtractedCandidateEntity] = Field(
        default_factory=list,
        description="Complete list of deterministic candidate extractions."
    )
    summary_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Counts of extracted candidates grouped by category."
    )
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Pipeline execution timestamp."
    )

    def get_by_category(self, category: str) -> List[ExtractedCandidateEntity]:
        """Filter candidates by category string."""
        return [c for c in self.candidates if c.category == category]

    def get_by_entity_type(self, entity_type: EntityType) -> List[ExtractedCandidateEntity]:
        """Filter candidates by ontology EntityType."""
        return [c for c in self.candidates if c.entity_type == entity_type]
