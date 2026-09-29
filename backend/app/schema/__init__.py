"""
Legal Knowledge Graph Schema and Ontology Package.

Provides controlled, extensible entity types, relationship types, provenance structures,
temporal models, strict triplet validation, and multi-target schema exporters.
"""

from app.schema.entity_types import EntityType, EntityCategory, ENTITY_METADATA
from app.schema.relationship_types import RelationshipType, RELATIONSHIP_METADATA
from app.schema.provenance import Provenance, ExtractionMethod
from app.schema.temporal import TemporalProperties, EventStatus
from app.schema.constraints import RELATIONSHIP_CONSTRAINTS
from app.schema.models import LegalNode, LegalRelationship, Triplet
from app.schema.validator import SchemaValidator, SchemaValidationError, TripletConstraintViolationError
from app.schema.registry import SchemaRegistry

__all__ = [
    "EntityType",
    "EntityCategory",
    "ENTITY_METADATA",
    "RelationshipType",
    "RELATIONSHIP_METADATA",
    "Provenance",
    "ExtractionMethod",
    "TemporalProperties",
    "EventStatus",
    "RELATIONSHIP_CONSTRAINTS",
    "LegalNode",
    "LegalRelationship",
    "Triplet",
    "SchemaValidator",
    "SchemaValidationError",
    "TripletConstraintViolationError",
    "SchemaRegistry",
]
