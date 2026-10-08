"""
Exporter for GLiNER-Relex model entity and relation extraction configuration.
"""

from typing import Dict, Any, Optional
from app.schema.registry import SchemaRegistry


def export_gliner_config(registry: Optional[SchemaRegistry] = None) -> Dict[str, Any]:
    """
    Generates JSON-serializable configuration formatted specifically for GLiNER / GLiNER-Relex
    joint entity & relation extraction pipeline.
    """
    reg = registry or SchemaRegistry()
    entity_labels = reg.list_entity_types()
    relation_labels = reg.list_relationship_types()

    allowed_pairs = []
    for triplet in reg.get_all_allowed_triplets():
        allowed_pairs.append(
            {
                "relation": triplet["relationship_type"],
                "head": triplet["source_type"],
                "tail": triplet["target_type"],
            }
        )

    return {
        "model_type": "gliner_relex_legal_v1",
        "entity_labels": entity_labels,
        "relation_labels": relation_labels,
        "allowed_pairs": allowed_pairs,
        "num_entity_types": len(entity_labels),
        "num_relation_types": len(relation_labels),
        "num_valid_pairs": len(allowed_pairs),
        "threshold_config": {"entity_threshold": 0.50, "relation_threshold": 0.55},
    }
