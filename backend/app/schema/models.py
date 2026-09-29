"""
Core Pydantic graph entity (Node) and edge (Relationship) data models.
"""

from typing import Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import Provenance
from app.schema.temporal import TemporalProperties


class Triplet(BaseModel):
    """Declarative triplet tuple (Source Entity Type, Relationship Type, Target Entity Type)."""
    source_type: EntityType
    relationship_type: RelationshipType
    target_type: EntityType

    def __str__(self) -> str:
        return f"({self.source_type.value}) -[{self.relationship_type.value}]-> ({self.target_type.value})"


class LegalNode(BaseModel):
    """
    Knowledge Graph Node representing a Legal Entity.
    """
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the node."
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Canonical name or textual label of the entity."
    )
    entity_type: EntityType = Field(
        ...,
        description="Controlled entity type enum."
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-specific properties (e.g. docket_number, bar_number)."
    )
    provenance: Provenance = Field(
        ...,
        description="Mandatory extraction lineage and source provenance record."
    )
    temporal: Optional[TemporalProperties] = Field(
        default=None,
        description="Optional temporal properties if entity has time/deadline metadata."
    )


class LegalRelationship(BaseModel):
    """
    Knowledge Graph Edge representing a directed relationship between two Legal Nodes.
    """
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the relationship edge."
    )
    source_id: str = Field(
        ...,
        description="Unique node ID of the source entity."
    )
    source_type: EntityType = Field(
        ...,
        description="Entity type of the source node."
    )
    relationship_type: RelationshipType = Field(
        ...,
        description="Controlled relationship type enum."
    )
    target_id: str = Field(
        ...,
        description="Unique node ID of the target entity."
    )
    target_type: EntityType = Field(
        ...,
        description="Entity type of the target node."
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional relationship attributes."
    )
    provenance: Provenance = Field(
        ...,
        description="Mandatory extraction lineage and source provenance record."
    )
    temporal: Optional[TemporalProperties] = Field(
        default=None,
        description="Optional temporal properties (e.g., effective dates of relationship)."
    )

    @property
    def triplet(self) -> Triplet:
        """Returns the abstract Triplet definition for constraint checking."""
        return Triplet(
            source_type=self.source_type,
            relationship_type=self.relationship_type,
            target_type=self.target_type
        )
