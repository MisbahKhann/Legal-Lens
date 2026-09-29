"""
Relationship Type definitions for US Legal Knowledge Graph.
"""

from enum import Enum
from typing import Dict, Any, Optional


class RelationshipType(str, Enum):
    """
    Controlled vocabulary of relationship/edge types for US Legal Case KG.
    AI extraction models MUST restrict relationship classifications to this enum.
    """
    PLAINTIFF_IN = "PLAINTIFF_IN"
    DEFENDANT_IN = "DEFENDANT_IN"
    REPRESENTED_BY = "REPRESENTED_BY"
    DECIDED_BY = "DECIDED_BY"
    FILED_IN = "FILED_IN"
    CITES = "CITES"
    APPLIES = "APPLIES"
    INTERPRETS = "INTERPRETS"
    OVERRULES = "OVERRULES"
    FOLLOWS = "FOLLOWS"
    DISTINGUISHES = "DISTINGUISHES"
    SUPPORTED_BY = "SUPPORTED_BY"
    CONTRADICTED_BY = "CONTRADICTED_BY"
    EVIDENCED_BY = "EVIDENCED_BY"
    MENTIONED_IN = "MENTIONED_IN"
    WORKS_FOR = "WORKS_FOR"
    EMPLOYED_BY = "EMPLOYED_BY"
    OWNS = "OWNS"
    REPRESENTS = "REPRESENTS"
    OCCURRED_ON = "OCCURRED_ON"
    OCCURRED_IN = "OCCURRED_IN"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    HAS_DEADLINE = "HAS_DEADLINE"


RELATIONSHIP_METADATA: Dict[RelationshipType, Dict[str, Any]] = {
    RelationshipType.PLAINTIFF_IN: {
        "description": "Indicates that an entity is a plaintiff initiating legal action in a case.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.DEFENDANT_IN: {
        "description": "Indicates that an entity is a defendant accused or sued in a case.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.REPRESENTED_BY: {
        "description": "Indicates legal representation by an attorney or law firm.",
        "inverse": RelationshipType.REPRESENTS,
        "is_directed": True
    },
    RelationshipType.DECIDED_BY: {
        "description": "Indicates judicial decision or resolution of a case, issue, or claim by a judge or court.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.FILED_IN: {
        "description": "Indicates submission of a filing or document to a specific court or case file.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.CITES: {
        "description": "Indicates legal reference or citation of an authority, statute, case, or document.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.APPLIES: {
        "description": "Indicates judicial application of a statute, regulation, or legal doctrine.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.INTERPRETS: {
        "description": "Indicates legal interpretation or construction of a statute, contract clause, or doctrine.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.OVERRULES: {
        "description": "Indicates higher court precedent setting aside or invalidating prior case authority.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.FOLLOWS: {
        "description": "Indicates judicial adherence to binding or persuasive precedent.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.DISTINGUISHES: {
        "description": "Indicates distinguishing facts or legal context of current matter from precedent.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.SUPPORTED_BY: {
        "description": "Indicates that a claim, issue, or testimony is supported by evidence, testimony, or statutory authority.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.CONTRADICTED_BY: {
        "description": "Indicates that a claim, assertion, or testimony is contradicted by opposing evidence or testimony.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.EVIDENCED_BY: {
        "description": "Indicates factual proof of an event or claim via specific exhibit or documentary evidence.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.MENTIONED_IN: {
        "description": "Indicates explicit textual mention of an entity inside a document, filing, or testimony.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.WORKS_FOR: {
        "description": "Indicates employment or organizational affiliation.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.EMPLOYED_BY: {
        "description": "Indicates formal employment relationship connecting individual to entity.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.OWNS: {
        "description": "Indicates legal ownership, title, or controlling interest.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.REPRESENTS: {
        "description": "Indicates attorney or law firm representation of a party or matter.",
        "inverse": RelationshipType.REPRESENTED_BY,
        "is_directed": True
    },
    RelationshipType.OCCURRED_ON: {
        "description": "Associates an event, hearing, or filing with a specific calendar date entity.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.OCCURRED_IN: {
        "description": "Associates an event, hearing, or document with a case or court proceeding context.",
        "inverse": None,
        "is_directed": True
    },
    RelationshipType.BEFORE: {
        "description": "Temporal ordering indicating source event/date occurred prior to target event/date.",
        "inverse": RelationshipType.AFTER,
        "is_directed": True
    },
    RelationshipType.AFTER: {
        "description": "Temporal ordering indicating source event/date occurred after target event/date.",
        "inverse": RelationshipType.BEFORE,
        "is_directed": True
    },
    RelationshipType.HAS_DEADLINE: {
        "description": "Associates a procedural filing, case, or task with a specific deadline entity or date.",
        "inverse": None,
        "is_directed": True
    }
}
