"""
Provenance data models for tracking extraction lineage, confidence, and auditability.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Tuple, List, Union
from pydantic import BaseModel, Field, field_validator


class ExtractionMethod(str, Enum):
    """Supported entity and relationship extraction methodologies."""

    GLINER_RELEX = "GLINER_RELEX"
    DETERMINISTIC_RULE = "DETERMINISTIC_RULE"
    MANUAL_HUMAN = "MANUAL_HUMAN"
    LLM_EXTRACTION = "LLM_EXTRACTION"
    HYBRID = "HYBRID"


class Provenance(BaseModel):
    """
    Mandatory metadata structure attached to every Node and Relationship
    to ensure 100% legal auditability and traceability to original source documents.
    """

    case_id: str = Field(
        ..., description="Unique identifier of the case knowledge graph."
    )
    source_document_id: str = Field(
        ..., description="ID or file path of the source legal document."
    )
    source_page: Optional[int] = Field(
        default=None,
        ge=1,
        description="1-indexed page number in the source document where entity/relationship appears.",
    )
    source_text: Optional[str] = Field(
        default=None,
        description="Verbatim text snippet or quote extracted from source document.",
    )
    char_span: Optional[Tuple[int, int]] = Field(
        default=None,
        description="Character start and end offsets [start, end] in the source document text.",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction (0.0 to 1.0). Manual entries default to 1.0.",
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.MANUAL_HUMAN,
        description="Methodology used to extract or create this entity/relationship.",
    )
    created_by: str = Field(
        default="system",
        description="User ID, attorney name, or agent system component that created this record.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of creation.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of last update.",
    )

    @field_validator("char_span")
    @classmethod
    def validate_char_span(
        cls, span: Optional[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        if span is not None:
            start, end = span
            if start < 0 or end < 0:
                raise ValueError(
                    "Span character indices must be non-negative integers."
                )
            if start >= end:
                raise ValueError(
                    f"Span start offset ({start}) must be strictly less than end offset ({end})."
                )
        return span

    def update_timestamp(self) -> None:
        """Helper to update timestamp on modification."""
        self.updated_at = datetime.now(timezone.utc)
