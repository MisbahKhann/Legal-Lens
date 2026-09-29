"""
Entity Type definitions and ontology taxonomy for US Legal Knowledge Graph.
"""

from enum import Enum
from typing import Dict, Any, Optional, List


class EntityCategory(str, Enum):
    """Broad functional categories for Knowledge Graph entities."""
    PARTY_LEGAL_ACTOR = "PARTY_LEGAL_ACTOR"
    LEGAL_SOURCE_NORMATIVE = "LEGAL_SOURCE_NORMATIVE"
    CASE_MATTER = "CASE_MATTER"
    DOCUMENTARY_EVIDENCE = "DOCUMENTARY_EVIDENCE"
    TEMPORAL_EVENT = "TEMPORAL_EVENT"


class EntityType(str, Enum):
    """
    Controlled vocabulary of entity/node types for US Legal Case KG.
    AI extraction models MUST restrict entity classifications to this enum.
    """
    CASE = "CASE"
    PERSON = "PERSON"
    LAWYER = "LAWYER"
    JUDGE = "JUDGE"
    WITNESS = "WITNESS"
    ORGANIZATION = "ORGANIZATION"
    COMPANY = "COMPANY"
    LAW_FIRM = "LAW_FIRM"
    GOVERNMENT_AGENCY = "GOVERNMENT_AGENCY"
    COURT = "COURT"
    STATUTE = "STATUTE"
    REGULATION = "REGULATION"
    LEGAL_CONCEPT = "LEGAL_CONCEPT"
    LEGAL_ISSUE = "LEGAL_ISSUE"
    CLAIM = "CLAIM"
    DOCUMENT = "DOCUMENT"
    CONTRACT = "CONTRACT"
    EVIDENCE = "EVIDENCE"
    EXHIBIT = "EXHIBIT"
    FILING = "FILING"
    TESTIMONY = "TESTIMONY"
    EVENT = "EVENT"
    DATE = "DATE"
    DEADLINE = "DEADLINE"
    HEARING = "HEARING"


# Metadata registry describing each entity type, category, parent type, and properties
ENTITY_METADATA: Dict[EntityType, Dict[str, Any]] = {
    EntityType.CASE: {
        "description": "A judicial proceeding, litigation matter, or lawsuit identified by case title/docket number.",
        "category": EntityCategory.CASE_MATTER,
        "parent_type": None,
        "properties": ["docket_number", "citation", "jurisdiction", "court_name", "status"]
    },
    EntityType.PERSON: {
        "description": "An individual human being relevant to the legal proceeding.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": None,
        "properties": ["full_name", "first_name", "last_name", "role", "alias"]
    },
    EntityType.LAWYER: {
        "description": "An attorney or legal practitioner representing a party or appearing in court.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": EntityType.PERSON,
        "properties": ["bar_number", "firm_affiliation", "specialty"]
    },
    EntityType.JUDGE: {
        "description": "A judicial officer who presides over court proceedings and rulings.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": EntityType.PERSON,
        "properties": ["title", "court_chamber", "appointment_type"]
    },
    EntityType.WITNESS: {
        "description": "An individual who gives testimony or provides sworn statements under oath.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": EntityType.PERSON,
        "properties": ["witness_type", "expertise_area", "subpoena_status"]
    },
    EntityType.ORGANIZATION: {
        "description": "A generic legal or corporate entity, institution, or collective body.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": None,
        "properties": ["org_name", "org_type", "state_of_incorporation"]
    },
    EntityType.COMPANY: {
        "description": "A commercial business organization, corporation, LLC, or partnership.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": EntityType.ORGANIZATION,
        "properties": ["ticker_symbol", "industry", "ein"]
    },
    EntityType.LAW_FIRM: {
        "description": "A legal practice entity comprising one or more attorneys offering legal services.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": EntityType.ORGANIZATION,
        "properties": ["firm_name", "office_locations", "website"]
    },
    EntityType.GOVERNMENT_AGENCY: {
        "description": "A public administrative or executive agency, board, or municipal entity.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": EntityType.ORGANIZATION,
        "properties": ["agency_level", "jurisdiction", "regulatory_scope"]
    },
    EntityType.COURT: {
        "description": "A judicial tribunal established to hear and adjudicate legal disputes.",
        "category": EntityCategory.PARTY_LEGAL_ACTOR,
        "parent_type": None,
        "properties": ["court_name", "court_level", "district_circuit", "jurisdiction"]
    },
    EntityType.STATUTE: {
        "description": "A formal written enactment of a legislative body (e.g., U.S. Code, state statutes).",
        "category": EntityCategory.LEGAL_SOURCE_NORMATIVE,
        "parent_type": None,
        "properties": ["statute_citation", "code_section", "title", "enacting_body"]
    },
    EntityType.REGULATION: {
        "description": "A rule or administrative order promulgated by a regulatory agency (e.g., CFR).",
        "category": EntityCategory.LEGAL_SOURCE_NORMATIVE,
        "parent_type": None,
        "properties": ["cfr_citation", "issuing_agency", "effective_date"]
    },
    EntityType.LEGAL_CONCEPT: {
        "description": "An established legal principle, doctrine, test, or standard (e.g., Strict Liability, Res Judicata).",
        "category": EntityCategory.LEGAL_SOURCE_NORMATIVE,
        "parent_type": None,
        "properties": ["concept_name", "domain", "defining_case"]
    },
    EntityType.LEGAL_ISSUE: {
        "description": "A specific legal question or disputed matter of law raised in a case.",
        "category": EntityCategory.CASE_MATTER,
        "parent_type": None,
        "properties": ["issue_description", "area_of_law", "disposition"]
    },
    EntityType.CLAIM: {
        "description": "A cause of action or legal demand asserted by a party against another.",
        "category": EntityCategory.CASE_MATTER,
        "parent_type": None,
        "properties": ["claim_type", "remedy_sought", "count_number", "status"]
    },
    EntityType.DOCUMENT: {
        "description": "A general textual or record item relevant to the legal proceedings.",
        "category": EntityCategory.DOCUMENTARY_EVIDENCE,
        "parent_type": None,
        "properties": ["title", "document_type", "bates_number", "date_created"]
    },
    EntityType.CONTRACT: {
        "description": "A legally binding agreement or instrument between two or more parties.",
        "category": EntityCategory.DOCUMENTARY_EVIDENCE,
        "parent_type": EntityType.DOCUMENT,
        "properties": ["contract_title", "effective_date", "termination_date", "governing_law"]
    },
    EntityType.EVIDENCE: {
        "description": "Any item, record, or physical item offered to prove or disprove a fact.",
        "category": EntityCategory.DOCUMENTARY_EVIDENCE,
        "parent_type": None,
        "properties": ["evidence_id", "description", "admissibility_status"]
    },
    EntityType.EXHIBIT: {
        "description": "A document or item formally marked and produced as evidence in court.",
        "category": EntityCategory.DOCUMENTARY_EVIDENCE,
        "parent_type": EntityType.EVIDENCE,
        "properties": ["exhibit_label", "offering_party", "admission_date"]
    },
    EntityType.FILING: {
        "description": "A formal written document submitted to the court (e.g., Motion, Brief, Complaint, Answer).",
        "category": EntityCategory.DOCUMENTARY_EVIDENCE,
        "parent_type": EntityType.DOCUMENT,
        "properties": ["filing_type", "docket_entry_number", "filing_date", "submitting_party"]
    },
    EntityType.TESTIMONY: {
        "description": "Oral or written statement given under oath during deposition, hearing, or trial.",
        "category": EntityCategory.DOCUMENTARY_EVIDENCE,
        "parent_type": EntityType.EVIDENCE,
        "properties": ["deponent_name", "testimony_date", "transcript_volume"]
    },
    EntityType.EVENT: {
        "description": "A factual occurrence, incident, transaction, or legal occurrence relevant to the narrative.",
        "category": EntityCategory.TEMPORAL_EVENT,
        "parent_type": None,
        "properties": ["event_name", "description", "location"]
    },
    EntityType.DATE: {
        "description": "A specific calendar date or time instance referenced in the record.",
        "category": EntityCategory.TEMPORAL_EVENT,
        "parent_type": None,
        "properties": ["date_value", "iso_format", "granularity"]
    },
    EntityType.DEADLINE: {
        "description": "A fixed procedural or statutory date/time by which an action must be completed.",
        "category": EntityCategory.TEMPORAL_EVENT,
        "parent_type": None,
        "properties": ["deadline_name", "due_date", "governing_rule", "status"]
    },
    EntityType.HEARING: {
        "description": "A formal judicial proceeding before a court or tribunal (e.g., Oral Argument, Trial, Motion Hearing).",
        "category": EntityCategory.TEMPORAL_EVENT,
        "parent_type": EntityType.EVENT,
        "properties": ["hearing_type", "presiding_judge", "courtroom"]
    }
}


def get_entity_hierarchy(entity_type: EntityType) -> List[EntityType]:
    """Returns entity type itself plus all supertypes in ascending order."""
    hierarchy = [entity_type]
    curr = entity_type
    while True:
        parent = ENTITY_METADATA[curr].get("parent_type")
        if not parent:
            break
        hierarchy.append(parent)
        curr = parent
    return hierarchy
