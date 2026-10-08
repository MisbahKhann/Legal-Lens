"""
Models for Step 6 Validation and Consistency Checking.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import uuid4

from app.resolution.models import CanonicalEntity, ResolvedRelation


class ValidationStatus(str, Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INVALID = "INVALID"


class ValidationSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecordType(str, Enum):
    ENTITY = "ENTITY"
    RELATIONSHIP = "RELATIONSHIP"


class ValidationRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: f"val_{uuid4().hex[:12]}")
    record_type: RecordType
    status: ValidationStatus
    severity: ValidationSeverity
    validation_rule: str
    message: str
    entity_id: Optional[str] = None
    relationship_id: Optional[str] = None
    supporting_evidence: Any = None
    source_document_id: Optional[str] = None
    source_page: Optional[int] = None
    source_text: Optional[str] = None
    confidence: Optional[float] = None


class ValidationResult(BaseModel):
    document_id: str
    case_id: Optional[str] = None

    validated_entities: List[CanonicalEntity] = Field(default_factory=list)
    validated_relationships: List[ResolvedRelation] = Field(default_factory=list)

    warnings: List[ValidationRecord] = Field(default_factory=list)
    review_required: List[ValidationRecord] = Field(default_factory=list)

    invalid_entities: List[CanonicalEntity] = Field(default_factory=list)
    invalid_relationships: List[ResolvedRelation] = Field(default_factory=list)

    validation_summary: Dict[str, int] = Field(default_factory=dict)

    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
