"""
Relationship Triplet Constraint rules for US Legal Knowledge Graph.
Defines valid (source_type, relationship_type, target_type) rules.
"""

from typing import Dict, Set, Any
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType

# Map of relationship type to allowed source and target entity types
RELATIONSHIP_CONSTRAINTS: Dict[RelationshipType, Dict[str, Set[EntityType]]] = {
    RelationshipType.PLAINTIFF_IN: {
        "sources": {
            EntityType.PERSON,
            EntityType.LAWYER,
            EntityType.ORGANIZATION,
            EntityType.COMPANY,
            EntityType.LAW_FIRM,
            EntityType.GOVERNMENT_AGENCY,
        },
        "targets": {EntityType.CASE},
    },
    RelationshipType.DEFENDANT_IN: {
        "sources": {
            EntityType.PERSON,
            EntityType.LAWYER,
            EntityType.ORGANIZATION,
            EntityType.COMPANY,
            EntityType.LAW_FIRM,
            EntityType.GOVERNMENT_AGENCY,
        },
        "targets": {EntityType.CASE},
    },
    RelationshipType.REPRESENTED_BY: {
        "sources": {
            EntityType.PERSON,
            EntityType.ORGANIZATION,
            EntityType.COMPANY,
            EntityType.GOVERNMENT_AGENCY,
            EntityType.CASE,
        },
        "targets": {
            EntityType.LAWYER,
            EntityType.LAW_FIRM,
        },
    },
    RelationshipType.DECIDED_BY: {
        "sources": {
            EntityType.CASE,
            EntityType.LEGAL_ISSUE,
            EntityType.CLAIM,
            EntityType.HEARING,
            EntityType.FILING,
        },
        "targets": {
            EntityType.JUDGE,
            EntityType.COURT,
        },
    },
    RelationshipType.FILED_IN: {
        "sources": {
            EntityType.CASE,
            EntityType.FILING,
            EntityType.DOCUMENT,
            EntityType.CONTRACT,
            EntityType.EVIDENCE,
            EntityType.EXHIBIT,
        },
        "targets": {
            EntityType.COURT,
            EntityType.CASE,
        },
    },
    RelationshipType.CITES: {
        "sources": {
            EntityType.CASE,
            EntityType.DOCUMENT,
            EntityType.CONTRACT,
            EntityType.FILING,
            EntityType.TESTIMONY,
            EntityType.STATUTE,
            EntityType.REGULATION,
        },
        "targets": {
            EntityType.CASE,
            EntityType.STATUTE,
            EntityType.REGULATION,
            EntityType.DOCUMENT,
            EntityType.CONTRACT,
        },
    },
    RelationshipType.APPLIES: {
        "sources": {
            EntityType.CASE,
            EntityType.JUDGE,
            EntityType.COURT,
            EntityType.FILING,
            EntityType.DOCUMENT,
        },
        "targets": {
            EntityType.STATUTE,
            EntityType.REGULATION,
            EntityType.LEGAL_CONCEPT,
            EntityType.LEGAL_ISSUE,
        },
    },
    RelationshipType.INTERPRETS: {
        "sources": {
            EntityType.CASE,
            EntityType.JUDGE,
            EntityType.COURT,
            EntityType.DOCUMENT,
            EntityType.FILING,
        },
        "targets": {
            EntityType.STATUTE,
            EntityType.REGULATION,
            EntityType.CONTRACT,
            EntityType.LEGAL_CONCEPT,
        },
    },
    RelationshipType.OVERRULES: {
        "sources": {
            EntityType.CASE,
            EntityType.COURT,
        },
        "targets": {
            EntityType.CASE,
        },
    },
    RelationshipType.FOLLOWS: {
        "sources": {
            EntityType.CASE,
            EntityType.COURT,
        },
        "targets": {
            EntityType.CASE,
        },
    },
    RelationshipType.DISTINGUISHES: {
        "sources": {
            EntityType.CASE,
            EntityType.COURT,
            EntityType.FILING,
        },
        "targets": {
            EntityType.CASE,
        },
    },
    RelationshipType.SUPPORTED_BY: {
        "sources": {
            EntityType.CLAIM,
            EntityType.LEGAL_ISSUE,
            EntityType.FILING,
            EntityType.TESTIMONY,
            EntityType.CASE,
        },
        "targets": {
            EntityType.EVIDENCE,
            EntityType.EXHIBIT,
            EntityType.TESTIMONY,
            EntityType.DOCUMENT,
            EntityType.STATUTE,
            EntityType.REGULATION,
            EntityType.CONTRACT,
        },
    },
    RelationshipType.CONTRADICTED_BY: {
        "sources": {
            EntityType.CLAIM,
            EntityType.LEGAL_ISSUE,
            EntityType.TESTIMONY,
            EntityType.EVIDENCE,
            EntityType.FILING,
        },
        "targets": {
            EntityType.EVIDENCE,
            EntityType.EXHIBIT,
            EntityType.TESTIMONY,
            EntityType.DOCUMENT,
        },
    },
    RelationshipType.EVIDENCED_BY: {
        "sources": {
            EntityType.CLAIM,
            EntityType.LEGAL_ISSUE,
            EntityType.EVENT,
            EntityType.HEARING,
            EntityType.CASE,
        },
        "targets": {
            EntityType.EVIDENCE,
            EntityType.EXHIBIT,
            EntityType.DOCUMENT,
            EntityType.TESTIMONY,
            EntityType.CONTRACT,
        },
    },
    RelationshipType.MENTIONED_IN: {
        "sources": set(EntityType),  # Any entity type can be mentioned in a document
        "targets": {
            EntityType.DOCUMENT,
            EntityType.FILING,
            EntityType.CONTRACT,
            EntityType.TESTIMONY,
            EntityType.EXHIBIT,
            EntityType.CASE,
        },
    },
    RelationshipType.WORKS_FOR: {
        "sources": {
            EntityType.PERSON,
            EntityType.LAWYER,
            EntityType.WITNESS,
        },
        "targets": {
            EntityType.ORGANIZATION,
            EntityType.COMPANY,
            EntityType.LAW_FIRM,
            EntityType.GOVERNMENT_AGENCY,
            EntityType.COURT,
        },
    },
    RelationshipType.EMPLOYED_BY: {
        "sources": {
            EntityType.PERSON,
            EntityType.LAWYER,
            EntityType.WITNESS,
        },
        "targets": {
            EntityType.ORGANIZATION,
            EntityType.COMPANY,
            EntityType.LAW_FIRM,
            EntityType.GOVERNMENT_AGENCY,
            EntityType.COURT,
        },
    },
    RelationshipType.OWNS: {
        "sources": {
            EntityType.PERSON,
            EntityType.ORGANIZATION,
            EntityType.COMPANY,
            EntityType.LAW_FIRM,
            EntityType.GOVERNMENT_AGENCY,
        },
        "targets": {
            EntityType.COMPANY,
            EntityType.ORGANIZATION,
            EntityType.EVIDENCE,
            EntityType.EXHIBIT,
            EntityType.DOCUMENT,
            EntityType.CONTRACT,
        },
    },
    RelationshipType.REPRESENTS: {
        "sources": {
            EntityType.LAWYER,
            EntityType.LAW_FIRM,
        },
        "targets": {
            EntityType.PERSON,
            EntityType.ORGANIZATION,
            EntityType.COMPANY,
            EntityType.GOVERNMENT_AGENCY,
            EntityType.CASE,
        },
    },
    RelationshipType.OCCURRED_ON: {
        "sources": {
            EntityType.EVENT,
            EntityType.HEARING,
            EntityType.FILING,
            EntityType.DOCUMENT,
            EntityType.CONTRACT,
            EntityType.CASE,
        },
        "targets": {
            EntityType.DATE,
        },
    },
    RelationshipType.OCCURRED_IN: {
        "sources": {
            EntityType.EVENT,
            EntityType.HEARING,
            EntityType.TESTIMONY,
            EntityType.DOCUMENT,
        },
        "targets": {
            EntityType.CASE,
            EntityType.COURT,
        },
    },
    RelationshipType.BEFORE: {
        "sources": {
            EntityType.EVENT,
            EntityType.HEARING,
            EntityType.DATE,
            EntityType.DEADLINE,
            EntityType.FILING,
        },
        "targets": {
            EntityType.EVENT,
            EntityType.HEARING,
            EntityType.DATE,
            EntityType.DEADLINE,
            EntityType.FILING,
        },
    },
    RelationshipType.AFTER: {
        "sources": {
            EntityType.EVENT,
            EntityType.HEARING,
            EntityType.DATE,
            EntityType.DEADLINE,
            EntityType.FILING,
        },
        "targets": {
            EntityType.EVENT,
            EntityType.HEARING,
            EntityType.DATE,
            EntityType.DEADLINE,
            EntityType.FILING,
        },
    },
    RelationshipType.HAS_DEADLINE: {
        "sources": {
            EntityType.CASE,
            EntityType.FILING,
            EntityType.HEARING,
            EntityType.EVENT,
            EntityType.LEGAL_ISSUE,
            EntityType.CLAIM,
        },
        "targets": {
            EntityType.DEADLINE,
            EntityType.DATE,
        },
    },
}
