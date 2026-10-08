"""
Models for Step 5 Entity Resolution and Deduplication.
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.extraction.ai_models import CandidateEntity, CandidateRelation


class CanonicalEntity(BaseModel):
    """
    A canonical, resolved entity resulting from merging one or more CandidateEntities.
    Handles exact and normalized duplicates.
    """
    canonical_id: str = Field(
        default_factory=lambda: f"ent_{uuid4().hex[:12]}",
        description="Unique identifier for the resolved entity."
    )
    entity_type: EntityType = Field(..., description="Entity type.")
    canonical_name: str = Field(..., description="Canonical text representation.")
    aliases: List[str] = Field(default_factory=list, description="Other variations of the name observed.")
    
    # Provenance tracking
    mentions: List[CandidateEntity] = Field(default_factory=list, description="Original CandidateEntity mentions.")
    
    document_id: str = Field(..., description="Source document ID.")
    case_id: Optional[str] = Field(default=None, description="Case ID.")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of resolution."
    )


class ResolvedRelation(BaseModel):
    """
    A resolved relationship mapping between CanonicalEntities rather than CandidateEntities.
    """
    relation_id: str = Field(
        default_factory=lambda: f"rel_{uuid4().hex[:12]}",
        description="Unique identifier for the resolved relationship."
    )
    relation_type: RelationshipType = Field(..., description="Type of relationship.")
    source_entity_id: str = Field(..., description="Canonical ID of the source entity.")
    target_entity_id: str = Field(..., description="Canonical ID of the target entity.")
    
    # Provenance
    mentions: List[CandidateRelation] = Field(default_factory=list, description="Original CandidateRelation mentions supporting this relation.")
    
    document_id: str = Field(..., description="Source document ID.")
    case_id: Optional[str] = Field(default=None, description="Case ID.")
    
    is_valid: bool = Field(default=True, description="Whether this relationship is valid.")
    validation_error: Optional[str] = Field(default=None, description="Error if invalid.")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of resolution."
    )


class ResolutionResult(BaseModel):
    """
    Container summarizing Step 5 resolution.
    """
    document_id: str = Field(..., description="Source document identifier.")
    case_id: Optional[str] = Field(default=None, description="Associated case identifier.")
    canonical_entities: List[CanonicalEntity] = Field(default_factory=list, description="Resolved canonical entities.")
    resolved_relations: List[ResolvedRelation] = Field(default_factory=list, description="Resolved relationships.")
    unresolved_entities: List[CandidateEntity] = Field(default_factory=list, description="Entities that could not be resolved or were ambiguous.")
    summary_counts: Dict[str, int] = Field(default_factory=dict, description="Summary statistics.")
    resolved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution timestamp."
    )
