"""
Script to generate declarative schema artifact files in docs/schema/ directory.
"""

import json
from pathlib import Path
from app.schema.registry import SchemaRegistry
from app.schema.exporters import (
    export_gliner_config,
    export_neo4j_schema,
    export_graph_editor_schema,
    export_deterministic_rules_schema,
)


def generate_all_schema_artifacts(output_dir: str = None) -> None:
    """Generates JSON and Cypher schema artifacts in the designated documentation directory."""
    if output_dir is None:
        # Default to repo root docs/schema
        output_dir = Path(__file__).resolve().parents[3] / "docs" / "schema"
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    reg = SchemaRegistry()

    # 1. Declarative Ontology Specification JSON
    ontology_spec = reg.export_full_ontology_spec()
    with open(out_path / "ontology.json", "w", encoding="utf-8") as f:
        json.dump(ontology_spec, f, indent=2)

    # 2. GLiNER-Relex Config JSON
    gliner_config = export_gliner_config(reg)
    with open(out_path / "gliner_schema.json", "w", encoding="utf-8") as f:
        json.dump(gliner_config, f, indent=2)

    # 3. Neo4j Cypher DDL Script
    neo4j_cypher = export_neo4j_schema(reg)
    with open(out_path / "neo4j_schema.cypher", "w", encoding="utf-8") as f:
        f.write(neo4j_cypher)

    # 4. Graph Editor UI Schema JSON
    editor_schema = export_graph_editor_schema(reg)
    with open(out_path / "graph_editor_schema.json", "w", encoding="utf-8") as f:
        json.dump(editor_schema, f, indent=2)

    # 5. Deterministic Rules Schema JSON
    rules_schema = export_deterministic_rules_schema(reg)
    with open(out_path / "deterministic_rules_schema.json", "w", encoding="utf-8") as f:
        json.dump(rules_schema, f, indent=2)

    print(f"Successfully generated all schema artifacts in '{output_dir}'.")


if __name__ == "__main__":
    generate_all_schema_artifacts()
