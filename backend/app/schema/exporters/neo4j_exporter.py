"""
Exporter for Neo4j Database Cypher DDL schema constraints, indexes, and relationship definitions.
"""

from typing import List, Optional
from app.schema.registry import SchemaRegistry
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType


def export_neo4j_schema(registry: Optional[SchemaRegistry] = None) -> str:
    """
    Generates Cypher DDL script containing node uniqueness constraints,
    property existence constraints, index definitions, and schema metadata comments for Neo4j.
    """
    reg = registry or SchemaRegistry()
    cypher_lines: List[str] = []

    cypher_lines.append(
        "// ============================================================================="
    )
    cypher_lines.append("// US LEGAL CASE KNOWLEDGE GRAPH - NEO4J SCHEMA DEFINITION")
    cypher_lines.append("// Auto-generated from authoritative Schema Registry")
    cypher_lines.append(
        "// =============================================================================\n"
    )

    cypher_lines.append(
        "// -----------------------------------------------------------------------------"
    )
    cypher_lines.append("// 1. NODE UNIQUENESS & IDENTIFIER CONSTRAINTS")
    cypher_lines.append(
        "// -----------------------------------------------------------------------------"
    )

    for entity_name in reg.list_entity_types():
        cypher_lines.append(
            f"CREATE CONSTRAINT constraint_{entity_name.lower()}_id_unique IF NOT EXISTS "
            f"FOR (n:`{entity_name}`) REQUIRE n.id IS UNIQUE;"
        )

    cypher_lines.append(
        "\n// -----------------------------------------------------------------------------"
    )
    cypher_lines.append("// 2. PROPERTY INDEXES FOR PERFORMANCE")
    cypher_lines.append(
        "// -----------------------------------------------------------------------------"
    )

    for entity_name in reg.list_entity_types():
        cypher_lines.append(
            f"CREATE INDEX index_{entity_name.lower()}_case_id IF NOT EXISTS "
            f"FOR (n:`{entity_name}`) ON (n.case_id);"
        )
        cypher_lines.append(
            f"CREATE INDEX index_{entity_name.lower()}_name IF NOT EXISTS "
            f"FOR (n:`{entity_name}`) ON (n.name);"
        )

    cypher_lines.append(
        "\n// -----------------------------------------------------------------------------"
    )
    cypher_lines.append("// 3. PROVENANCE PROPERTY EXISTENCE CONSTRAINTS")
    cypher_lines.append(
        "// -----------------------------------------------------------------------------"
    )

    for entity_name in reg.list_entity_types():
        cypher_lines.append(
            f"CREATE CONSTRAINT constraint_{entity_name.lower()}_provenance_case IF NOT EXISTS "
            f"FOR (n:`{entity_name}`) REQUIRE n.case_id IS NOT NULL;"
        )

    cypher_lines.append(
        "\n// -----------------------------------------------------------------------------"
    )
    cypher_lines.append("// 4. AUTHORITATIVE RELATIONSHIP TRIPLET MATRICES")
    cypher_lines.append(
        "// -----------------------------------------------------------------------------"
    )

    for rel_name in reg.list_relationship_types():
        rel_enum = RelationshipType(rel_name)
        sources = reg.get_allowed_sources(rel_enum)
        targets = reg.get_allowed_targets(rel_enum)
        cypher_lines.append(
            f"// Relationship: [{rel_name}] | Sources: {', '.join(sources)} | Targets: {', '.join(targets)}"
        )

    return "\n".join(cypher_lines)
