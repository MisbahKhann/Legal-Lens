"""
Exporter for Human-in-the-Loop Graph Editor UI configuration (React / ReactFlow / Cytoscape).
"""

from typing import Dict, Any, Optional
from app.schema.registry import SchemaRegistry
from app.schema.entity_types import EntityType, EntityCategory, ENTITY_METADATA
from app.schema.relationship_types import RelationshipType, RELATIONSHIP_METADATA


CATEGORY_UI_CONFIG = {
    EntityCategory.PARTY_LEGAL_ACTOR: {"color": "#1E3A8A", "bg_color": "#DBEAFE", "icon": "user-check"},
    EntityCategory.LEGAL_SOURCE_NORMATIVE: {"color": "#9A3412", "bg_color": "#FFEDD5", "icon": "book-open"},
    EntityCategory.CASE_MATTER: {"color": "#15803D", "bg_color": "#DCFCE7", "icon": "scale"},
    EntityCategory.DOCUMENTARY_EVIDENCE: {"color": "#B45309", "bg_color": "#FEF3C7", "icon": "file-text"},
    EntityCategory.TEMPORAL_EVENT: {"color": "#6B21A8", "bg_color": "#F3E8FF", "icon": "calendar"},
}


def export_graph_editor_schema(registry: Optional[SchemaRegistry] = None) -> Dict[str, Any]:
    """
    Generates UI Schema definition used by front-end interactive Knowledge Graph editors
    to enforce validation during manual node creation, edge creation, and editing.
    """
    reg = registry or SchemaRegistry()
    full_ontology = reg.export_full_ontology_spec()

    node_types_ui = {}
    for e_name, meta in full_ontology["entity_types"].items():
        cat_enum = EntityCategory(meta["category"])
        ui_theme = CATEGORY_UI_CONFIG.get(cat_enum, {"color": "#374151", "bg_color": "#F3F4F6", "icon": "circle"})
        node_types_ui[e_name] = {
            "label": e_name.replace("_", " ").title(),
            "category": meta["category"],
            "description": meta["description"],
            "theme": ui_theme,
            "form_fields": [
                {"name": "name", "label": "Entity Name", "type": "string", "required": True},
                *[{ "name": p, "label": p.replace("_", " ").title(), "type": "string", "required": False } for p in meta["properties"]]
            ]
        }

    # Build matrix of allowed relationships per source node type for UI dropdown filtering
    source_to_valid_targets: Dict[str, Dict[str, list]] = {}
    for triplet in reg.get_all_allowed_triplets():
        src = triplet["source_type"]
        rel = triplet["relationship_type"]
        tgt = triplet["target_type"]

        if src not in source_to_valid_targets:
            source_to_valid_targets[src] = {}
        if rel not in source_to_valid_targets[src]:
            source_to_valid_targets[src][rel] = []
        if tgt not in source_to_valid_targets[src][rel]:
            source_to_valid_targets[src][rel].append(tgt)

    return {
        "version": "1.0.0",
        "node_types": node_types_ui,
        "relationship_types": full_ontology["relationship_types"],
        "ui_matrix": source_to_valid_targets,
        "provenance_fields": [
            {"name": "case_id", "type": "string", "required": True},
            {"name": "source_document_id", "type": "string", "required": True},
            {"name": "source_page", "type": "number", "required": False},
            {"name": "source_text", "type": "textarea", "required": False},
            {"name": "confidence", "type": "number", "min": 0.0, "max": 1.0, "required": True},
            {"name": "extraction_method", "type": "select", "options": ["GLINER_RELEX", "DETERMINISTIC_RULE", "MANUAL_HUMAN", "LLM_EXTRACTION"], "required": True}
        ],
        "temporal_fields": [
            {"name": "event_date", "type": "datetime", "required": False},
            {"name": "start_date", "type": "datetime", "required": False},
            {"name": "end_date", "type": "datetime", "required": False},
            {"name": "deadline", "type": "datetime", "required": False},
            {"name": "status", "type": "select", "options": ["PENDING", "COMPLETED", "UPCOMING", "OVERDUE", "CANCELLED", "ONGOING"], "required": False}
        ]
    }
