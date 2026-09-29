"""
Exporter for Deterministic Legal Extraction Rules schema configuration.
"""

from typing import Dict, Any, Optional
from app.schema.registry import SchemaRegistry
from app.schema.relationship_types import RelationshipType


def export_deterministic_rules_schema(registry: Optional[SchemaRegistry] = None) -> Dict[str, Any]:
    """
    Generates rule engine configuration defining strict pattern matching constraints
    for rule-based entity and relationship extractors.
    """
    reg = registry or SchemaRegistry()

    rules_config = []
    for rel_type_str in reg.list_relationship_types():
        rel_enum = RelationshipType(rel_type_str)
        rel_meta = reg.get_relationship_metadata(rel_enum)
        allowed_triplets = [
            t for t in reg.get_all_allowed_triplets()
            if t["relationship_type"] == rel_type_str
        ]

        rules_config.append({
            "relationship_type": rel_type_str,
            "description": rel_meta.get("description"),
            "valid_triplets": allowed_triplets,
            "patterns": [
                {
                    "pattern_id": f"rule_{rel_type_str.lower()}_01",
                    "regex_template": None,
                    "dependency_parse_template": None,
                    "confidence_default": 0.95
                }
            ]
        })

    return {
        "version": "1.0.0",
        "engine": "deterministic_legal_rule_extractor",
        "relationship_rules": rules_config,
        "total_rules": len(rules_config)
    }
