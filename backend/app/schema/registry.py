"""
SchemaRegistry providing controlled access to entity/relationship specifications and controlled extensibility.
"""

from typing import Dict, Set, List, Any, Optional
from app.schema.entity_types import EntityType, ENTITY_METADATA, EntityCategory
from app.schema.relationship_types import RelationshipType, RELATIONSHIP_METADATA
from app.schema.constraints import RELATIONSHIP_CONSTRAINTS
from app.schema.models import Triplet


class SchemaRegistry:
    """
    Central registry for Knowledge Graph ontology specs.
    Provides lookup utilities and controlled extension capabilities.
    """

    def __init__(self):
        self._entity_types = dict(ENTITY_METADATA)
        self._relationship_types = dict(RELATIONSHIP_METADATA)
        self._constraints = dict(RELATIONSHIP_CONSTRAINTS)

    def list_entity_types(self) -> List[str]:
        """Returns list of active entity type names."""
        return [e.value for e in self._entity_types.keys()]

    def list_relationship_types(self) -> List[str]:
        """Returns list of active relationship type names."""
        return [r.value for r in self._relationship_types.keys()]

    def get_entity_metadata(self, entity_type: EntityType) -> Dict[str, Any]:
        """Returns metadata dictionary for an entity type."""
        return self._entity_types.get(entity_type, {})

    def get_relationship_metadata(self, rel_type: RelationshipType) -> Dict[str, Any]:
        """Returns metadata dictionary for a relationship type."""
        return self._relationship_types.get(rel_type, {})

    def get_allowed_sources(self, rel_type: RelationshipType) -> List[str]:
        """Returns list of allowed source entity type names for a relationship."""
        constraint = self._constraints.get(rel_type, {})
        sources = constraint.get("sources", set())
        return sorted([s.value for s in sources])

    def get_allowed_targets(self, rel_type: RelationshipType) -> List[str]:
        """Returns list of allowed target entity type names for a relationship."""
        constraint = self._constraints.get(rel_type, {})
        targets = constraint.get("targets", set())
        return sorted([t.value for t in targets])

    def get_all_allowed_triplets(self) -> List[Dict[str, str]]:
        """
        Generates list of all valid (source, relation, target) combinations
        for extraction model configuration and validation rules.
        """
        triplets = []
        for rel_type, constraint in self._constraints.items():
            for source in constraint["sources"]:
                for target in constraint["targets"]:
                    triplets.append({
                        "source_type": source.value,
                        "relationship_type": rel_type.value,
                        "target_type": target.value
                    })
        return triplets

    def export_full_ontology_spec(self) -> Dict[str, Any]:
        """Returns comprehensive declarative dictionary of full ontology."""
        return {
            "version": "1.0.0",
            "title": "US Legal Case Knowledge Graph Schema Spec",
            "entity_types": {
                e.value: {
                    "description": meta.get("description"),
                    "category": meta.get("category").value if isinstance(meta.get("category"), EntityCategory) else meta.get("category"),
                    "parent_type": meta.get("parent_type").value if meta.get("parent_type") else None,
                    "properties": meta.get("properties", [])
                }
                for e, meta in self._entity_types.items()
            },
            "relationship_types": {
                r.value: {
                    "description": meta.get("description"),
                    "is_directed": meta.get("is_directed", True),
                    "inverse": meta.get("inverse").value if meta.get("inverse") else None,
                    "allowed_sources": self.get_allowed_sources(r),
                    "allowed_targets": self.get_allowed_targets(r)
                }
                for r, meta in self._relationship_types.items()
            },
            "total_entity_types": len(self._entity_types),
            "total_relationship_types": len(self._relationship_types),
            "total_allowed_triplet_rules": len(self.get_all_allowed_triplets())
        }
