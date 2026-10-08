"""
Strict Schema Validator for Legal Knowledge Graph Nodes, Relationships, and Triplets.
Enforces entity/relationship controlled vocabularies and source/target constraint matrix.
"""

from typing import List, Optional, Tuple, Dict, Set
from app.schema.entity_types import EntityType, ENTITY_METADATA, get_entity_hierarchy
from app.schema.relationship_types import RelationshipType, RELATIONSHIP_METADATA
from app.schema.constraints import RELATIONSHIP_CONSTRAINTS
from app.schema.models import LegalNode, LegalRelationship, Triplet
from app.schema.provenance import Provenance
from app.schema.temporal import TemporalProperties


class SchemaValidationError(Exception):
    """Base exception for all schema validation failures."""

    pass


class InvalidEntityTypeError(SchemaValidationError):
    """Raised when an unrecognized entity type string is supplied."""

    pass


class InvalidRelationshipTypeError(SchemaValidationError):
    """Raised when an unrecognized relationship type string is supplied."""

    pass


class TripletConstraintViolationError(SchemaValidationError):
    """Raised when a relationship violates allowed (source_type, rel_type, target_type) constraints."""

    pass


class ProvenanceValidationError(SchemaValidationError):
    """Raised when provenance metadata is incomplete or invalid."""

    pass


class TemporalValidationError(SchemaValidationError):
    """Raised when temporal metadata contains logical contradictions."""

    pass


class SchemaValidator:
    """
    Authoritative validation engine for the Knowledge Graph.
    Ensures zero arbitrary AI-invented entity or relationship types,
    and enforces strict triplet domain/range constraints.
    """

    @classmethod
    def validate_entity_type(cls, entity_type: str) -> EntityType:
        """Validates that entity_type string belongs to controlled EntityType enum."""
        try:
            return EntityType(entity_type)
        except ValueError:
            valid_types = [e.value for e in EntityType]
            raise InvalidEntityTypeError(
                f"Invalid entity type '{entity_type}'. "
                f"Must be one of controlled EntityTypes: {valid_types}"
            )

    @classmethod
    def validate_relationship_type(cls, rel_type: str) -> RelationshipType:
        """Validates that rel_type string belongs to controlled RelationshipType enum."""
        try:
            return RelationshipType(rel_type)
        except ValueError:
            valid_types = [r.value for r in RelationshipType]
            raise InvalidRelationshipTypeError(
                f"Invalid relationship type '{rel_type}'. "
                f"Must be one of controlled RelationshipTypes: {valid_types}"
            )

    @classmethod
    def validate_triplet(
        cls,
        source_type: EntityType,
        relationship_type: RelationshipType,
        target_type: EntityType,
        allow_subtype_inheritance: bool = True,
    ) -> bool:
        """
        Validates if (source_type, relationship_type, target_type) is permitted.

        Args:
            source_type: Source entity type enum
            relationship_type: Relationship type enum
            target_type: Target entity type enum
            allow_subtype_inheritance: If True, supertypes in hierarchy are checked.

        Returns:
            True if valid.

        Raises:
            TripletConstraintViolationError if invalid.
        """
        if relationship_type not in RELATIONSHIP_CONSTRAINTS:
            raise InvalidRelationshipTypeError(
                f"No constraint entry found for relationship type '{relationship_type.value}'."
            )

        constraint = RELATIONSHIP_CONSTRAINTS[relationship_type]
        allowed_sources: Set[EntityType] = constraint["sources"]
        allowed_targets: Set[EntityType] = constraint["targets"]

        # Check source type validity
        source_valid = source_type in allowed_sources
        if not source_valid and allow_subtype_inheritance:
            source_hierarchy = get_entity_hierarchy(source_type)
            source_valid = any(st in allowed_sources for st in source_hierarchy)

        # Check target type validity
        target_valid = target_type in allowed_targets
        if not target_valid and allow_subtype_inheritance:
            target_hierarchy = get_entity_hierarchy(target_type)
            target_valid = any(tt in allowed_targets for tt in target_hierarchy)

        if not source_valid or not target_valid:
            allowed_src_str = ", ".join(sorted([s.value for s in allowed_sources]))
            allowed_tgt_str = ", ".join(sorted([t.value for t in allowed_targets]))
            raise TripletConstraintViolationError(
                f"Invalid relationship triplet: ({source_type.value}) -[{relationship_type.value}]-> ({target_type.value}). "
                f"Relationship '{relationship_type.value}' allows sources: [{allowed_src_str}] "
                f"and targets: [{allowed_tgt_str}]."
            )

        return True

    @classmethod
    def validate_node(cls, node: LegalNode) -> None:
        """Validates a LegalNode instance including entity type, provenance, and temporal properties."""
        cls.validate_entity_type(node.entity_type.value)
        cls.validate_provenance(node.provenance)
        if node.temporal:
            cls.validate_temporal(node.temporal)

    @classmethod
    def validate_relationship(
        cls, relationship: LegalRelationship, allow_subtype_inheritance: bool = True
    ) -> None:
        """Validates a LegalRelationship instance including triplet constraints, provenance, and temporal properties."""
        cls.validate_entity_type(relationship.source_type.value)
        cls.validate_relationship_type(relationship.relationship_type.value)
        cls.validate_entity_type(relationship.target_type.value)

        cls.validate_triplet(
            source_type=relationship.source_type,
            relationship_type=relationship.relationship_type,
            target_type=relationship.target_type,
            allow_subtype_inheritance=allow_subtype_inheritance,
        )

        cls.validate_provenance(relationship.provenance)
        if relationship.temporal:
            cls.validate_temporal(relationship.temporal)

    @classmethod
    def validate_provenance(cls, provenance: Provenance) -> None:
        """Validates provenance fields."""
        if not provenance.case_id or not provenance.case_id.strip():
            raise ProvenanceValidationError("Provenance case_id cannot be empty.")
        if (
            not provenance.source_document_id
            or not provenance.source_document_id.strip()
        ):
            raise ProvenanceValidationError(
                "Provenance source_document_id cannot be empty."
            )
        if not (0.0 <= provenance.confidence <= 1.0):
            raise ProvenanceValidationError(
                f"Confidence score {provenance.confidence} out of range [0.0, 1.0]."
            )

    @classmethod
    def validate_temporal(cls, temporal: TemporalProperties) -> None:
        """Validates temporal dates consistency."""
        if temporal.start_date and temporal.end_date:
            if temporal.start_date > temporal.end_date:
                raise TemporalValidationError(
                    f"start_date ({temporal.start_date}) cannot be after end_date ({temporal.end_date})."
                )
