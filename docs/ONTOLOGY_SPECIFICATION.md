# US Legal Case Knowledge Graph: Authoritative Schema & Ontology Specification

> **Version:** 1.0.0  
> **Status:** Authoritative (Step 1 Complete)  
> **Scope:** Knowledge Graph Schema, Entity & Relationship Controlled Vocabularies, Provenance & Temporal Models, Triplet Constraint Matrices, and Downstream Exporters.

---

## 1. Overview & Architectural Purpose

This document establishes the **authoritative, controlled ontology** for the US Legal Case Knowledge Graph system (**LegalLens**). 

The Knowledge Graph is structured to represent individual legal cases as dedicated, queryable subgraphs. To guarantee legal auditability, zero hallucinations, and high precision across downstream NLP, database, and UI editor components, **arbitrary AI-generated entity or relationship types are strictly prohibited**. All extracted triplets must conform to the controlled vocabulary and constraint matrices defined herein.

---

## 2. Entity / Node Types (25 Types)

The ontology categorizes legal entities into 5 functional super-categories:

1. `PARTY_LEGAL_ACTOR`: Human actors, judges, lawyers, witnesses, and organizations.
2. `LEGAL_SOURCE_NORMATIVE`: Statutes, regulations, and legal doctrines.
3. `CASE_MATTER`: Litigated cases, claims, and disputed legal issues.
4. `DOCUMENTARY_EVIDENCE`: Documents, contracts, filings, testimonies, and exhibits.
5. `TEMPORAL_EVENT`: Events, dates, deadlines, and judicial hearings.

### Entity Catalog

| Entity Type | Category | Parent Type | Description | Key Properties |
| :--- | :--- | :--- | :--- | :--- |
| `CASE` | `CASE_MATTER` | — | Judicial proceeding or litigation matter identified by title/docket. | `docket_number`, `citation`, `jurisdiction`, `court_name`, `status` |
| `PERSON` | `PARTY_LEGAL_ACTOR` | — | Individual human being relevant to the legal proceeding. | `full_name`, `first_name`, `last_name`, `role`, `alias` |
| `LAWYER` | `PARTY_LEGAL_ACTOR` | `PERSON` | Attorney or legal counsel representing a party or appearing in court. | `bar_number`, `firm_affiliation`, `specialty` |
| `JUDGE` | `PARTY_LEGAL_ACTOR` | `PERSON` | Judicial officer presiding over court proceedings and rulings. | `title`, `court_chamber`, `appointment_type` |
| `WITNESS` | `PARTY_LEGAL_ACTOR` | `PERSON` | Individual giving testimony or sworn statements under oath. | `witness_type`, `expertise_area`, `subpoena_status` |
| `ORGANIZATION` | `PARTY_LEGAL_ACTOR` | — | Generic legal or corporate entity, institution, or collective body. | `org_name`, `org_type`, `state_of_incorporation` |
| `COMPANY` | `PARTY_LEGAL_ACTOR` | `ORGANIZATION` | Commercial business entity, corporation, LLC, or partnership. | `ticker_symbol`, `industry`, `ein` |
| `LAW_FIRM` | `PARTY_LEGAL_ACTOR` | `ORGANIZATION` | Legal practice entity offering professional legal services. | `firm_name`, `office_locations`, `website` |
| `GOVERNMENT_AGENCY` | `PARTY_LEGAL_ACTOR` | `ORGANIZATION` | Public administrative, executive, or regulatory agency. | `agency_level`, `jurisdiction`, `regulatory_scope` |
| `COURT` | `PARTY_LEGAL_ACTOR` | — | Judicial tribunal established to hear and adjudicate disputes. | `court_name`, `court_level`, `district_circuit`, `jurisdiction` |
| `STATUTE` | `LEGAL_SOURCE_NORMATIVE` | — | Formal written enactment of a legislative body (e.g., U.S. Code). | `statute_citation`, `code_section`, `title`, `enacting_body` |
| `REGULATION` | `LEGAL_SOURCE_NORMATIVE` | — | Administrative rule or order promulgated by an agency (e.g., CFR). | `cfr_citation`, `issuing_agency`, `effective_date` |
| `LEGAL_CONCEPT` | `LEGAL_SOURCE_NORMATIVE` | — | Established legal principle, doctrine, or standard (e.g., Strict Liability). | `concept_name`, `domain`, `defining_case` |
| `LEGAL_ISSUE` | `CASE_MATTER` | — | Specific legal question or disputed matter of law raised in a case. | `issue_description`, `area_of_law`, `disposition` |
| `CLAIM` | `CASE_MATTER` | — | Cause of action or legal demand asserted by a party. | `claim_type`, `remedy_sought`, `count_number`, `status` |
| `DOCUMENT` | `DOCUMENTARY_EVIDENCE` | — | General textual or record item relevant to proceedings. | `title`, `document_type`, `bates_number`, `date_created` |
| `CONTRACT` | `DOCUMENTARY_EVIDENCE` | `DOCUMENT` | Legally binding agreement or instrument between parties. | `contract_title`, `effective_date`, `termination_date`, `governing_law` |
| `EVIDENCE` | `DOCUMENTARY_EVIDENCE` | — | Item or record offered to prove or disprove a factual matter. | `evidence_id`, `description`, `admissibility_status` |
| `EXHIBIT` | `DOCUMENTARY_EVIDENCE` | `EVIDENCE` | Document or item formally marked and produced as evidence. | `exhibit_label`, `offering_party`, `admission_date` |
| `FILING` | `DOCUMENTARY_EVIDENCE` | `DOCUMENT` | Written document submitted to court (Motion, Brief, Complaint). | `filing_type`, `docket_entry_number`, `filing_date`, `submitting_party` |
| `TESTIMONY` | `DOCUMENTARY_EVIDENCE` | `EVIDENCE` | Sworn statement given during deposition, hearing, or trial. | `deponent_name`, `testimony_date`, `transcript_volume` |
| `EVENT` | `TEMPORAL_EVENT` | — | Factual occurrence, transaction, or incident relevant to narrative. | `event_name`, `description`, `location` |
| `DATE` | `TEMPORAL_EVENT` | — | Specific calendar date or time instance referenced in record. | `date_value`, `iso_format`, `granularity` |
| `DEADLINE` | `TEMPORAL_EVENT` | — | Fixed procedural or statutory date by which action must occur. | `deadline_name`, `due_date`, `governing_rule`, `status` |
| `HEARING` | `TEMPORAL_EVENT` | `EVENT` | Formal judicial proceeding before a judge (Trial, Oral Argument). | `hearing_type`, `presiding_judge`, `courtroom` |

---

## 3. Relationship Types & Triplet Constraints (24 Types)

For every relationship type, valid **Source Entity Types** and **Target Entity Types** are strictly defined. The validation engine rejects any edge where `(Source, Edge, Target)` is not in this matrix.

### Triplet Constraint Matrix

| Relationship Type | Directed | Inverse | Valid Source Entity Types | Valid Target Entity Types |
| :--- | :---: | :--- | :--- | :--- |
| `PLAINTIFF_IN` | Yes | — | `PERSON`, `LAWYER`, `ORGANIZATION`, `COMPANY`, `LAW_FIRM`, `GOVERNMENT_AGENCY` | `CASE` |
| `DEFENDANT_IN` | Yes | — | `PERSON`, `LAWYER`, `ORGANIZATION`, `COMPANY`, `LAW_FIRM`, `GOVERNMENT_AGENCY` | `CASE` |
| `REPRESENTED_BY` | Yes | `REPRESENTS` | `PERSON`, `ORGANIZATION`, `COMPANY`, `GOVERNMENT_AGENCY`, `CASE` | `LAWYER`, `LAW_FIRM` |
| `DECIDED_BY` | Yes | — | `CASE`, `LEGAL_ISSUE`, `CLAIM`, `HEARING`, `FILING` | `JUDGE`, `COURT` |
| `FILED_IN` | Yes | — | `CASE`, `FILING`, `DOCUMENT`, `CONTRACT`, `EVIDENCE`, `EXHIBIT` | `COURT`, `CASE` |
| `CITES` | Yes | — | `CASE`, `DOCUMENT`, `CONTRACT`, `FILING`, `TESTIMONY`, `STATUTE`, `REGULATION` | `CASE`, `STATUTE`, `REGULATION`, `DOCUMENT`, `CONTRACT` |
| `APPLIES` | Yes | — | `CASE`, `JUDGE`, `COURT`, `FILING`, `DOCUMENT` | `STATUTE`, `REGULATION`, `LEGAL_CONCEPT`, `LEGAL_ISSUE` |
| `INTERPRETS` | Yes | — | `CASE`, `JUDGE`, `COURT`, `DOCUMENT`, `FILING` | `STATUTE`, `REGULATION`, `CONTRACT`, `LEGAL_CONCEPT` |
| `OVERRULES` | Yes | — | `CASE`, `COURT` | `CASE` |
| `FOLLOWS` | Yes | — | `CASE`, `COURT` | `CASE` |
| `DISTINGUISHES` | Yes | — | `CASE`, `COURT`, `FILING` | `CASE` |
| `SUPPORTED_BY` | Yes | — | `CLAIM`, `LEGAL_ISSUE`, `FILING`, `TESTIMONY`, `CASE` | `EVIDENCE`, `EXHIBIT`, `TESTIMONY`, `DOCUMENT`, `STATUTE`, `REGULATION`, `CONTRACT` |
| `CONTRADICTED_BY` | Yes | — | `CLAIM`, `LEGAL_ISSUE`, `TESTIMONY`, `EVIDENCE`, `FILING` | `EVIDENCE`, `EXHIBIT`, `TESTIMONY`, `DOCUMENT` |
| `EVIDENCED_BY` | Yes | — | `CLAIM`, `LEGAL_ISSUE`, `EVENT`, `HEARING`, `CASE` | `EVIDENCE`, `EXHIBIT`, `DOCUMENT`, `TESTIMONY`, `CONTRACT` |
| `MENTIONED_IN` | Yes | — | *ANY ENTITY TYPE* | `DOCUMENT`, `FILING`, `CONTRACT`, `TESTIMONY`, `EXHIBIT`, `CASE` |
| `WORKS_FOR` | Yes | — | `PERSON`, `LAWYER`, `WITNESS` | `ORGANIZATION`, `COMPANY`, `LAW_FIRM`, `GOVERNMENT_AGENCY`, `COURT` |
| `EMPLOYED_BY` | Yes | — | `PERSON`, `LAWYER`, `WITNESS` | `ORGANIZATION`, `COMPANY`, `LAW_FIRM`, `GOVERNMENT_AGENCY`, `COURT` |
| `OWNS` | Yes | — | `PERSON`, `ORGANIZATION`, `COMPANY`, `LAW_FIRM`, `GOVERNMENT_AGENCY` | `COMPANY`, `ORGANIZATION`, `EVIDENCE`, `EXHIBIT`, `DOCUMENT`, `CONTRACT` |
| `REPRESENTS` | Yes | `REPRESENTED_BY` | `LAWYER`, `LAW_FIRM` | `PERSON`, `ORGANIZATION`, `COMPANY`, `GOVERNMENT_AGENCY`, `CASE` |
| `OCCURRED_ON` | Yes | — | `EVENT`, `HEARING`, `FILING`, `DOCUMENT`, `CONTRACT`, `CASE` | `DATE` |
| `OCCURRED_IN` | Yes | — | `EVENT`, `HEARING`, `TESTIMONY`, `DOCUMENT` | `CASE`, `COURT` |
| `BEFORE` | Yes | `AFTER` | `EVENT`, `HEARING`, `DATE`, `DEADLINE`, `FILING` | `EVENT`, `HEARING`, `DATE`, `DEADLINE`, `FILING` |
| `AFTER` | Yes | `BEFORE` | `EVENT`, `HEARING`, `DATE`, `DEADLINE`, `FILING` | `EVENT`, `HEARING`, `DATE`, `DEADLINE`, `FILING` |
| `HAS_DEADLINE` | Yes | — | `CASE`, `FILING`, `HEARING`, `EVENT`, `LEGAL_ISSUE`, `CLAIM` | `DEADLINE`, `DATE` |

---

## 4. Provenance Data Model

Every single node and relationship edge in the Knowledge Graph **MUST** carry a `Provenance` block. This guarantees 100% legal auditability back to exact pages and quotes in source court filings.

```python
class Provenance(BaseModel):
    case_id: str                      # Mandatory UUID / identifier of the case KG
    source_document_id: str           # Mandatory source document ID or filename
    source_page: Optional[int]        # 1-indexed page number (>= 1)
    source_text: Optional[str]        # Verbatim raw text quote extracted
    char_span: Optional[Tuple[int, int]] # Character offsets [start, end]
    confidence: float                 # Extraction confidence score (0.0 to 1.0)
    extraction_method: ExtractionMethod # Enum: GLINER_RELEX, DETERMINISTIC_RULE, MANUAL_HUMAN, LLM_EXTRACTION
    created_by: str                   # User ID, lawyer name, or agent process name
    created_at: datetime              # ISO 8601 UTC timestamp
    updated_at: datetime              # ISO 8601 UTC timestamp
```

---

## 5. Temporal Properties Data Model

Temporal tracking is supported on relevant nodes (`EVENT`, `HEARING`, `DEADLINE`, `DATE`) and relationship edges.

```python
class TemporalProperties(BaseModel):
    event_date: Optional[datetime]    # Exact event timestamp
    start_date: Optional[datetime]    # Start timestamp for periods (start_date <= end_date)
    end_date: Optional[datetime]      # End timestamp for periods
    deadline: Optional[datetime]      # Due date timestamp
    status: Optional[EventStatus]     # Enum: PENDING, COMPLETED, UPCOMING, OVERDUE, CANCELLED, ONGOING
```

---

## 6. Downstream System Exporters

The ontology is exported into system-ready schema representations in `docs/schema/`:

1. **GLiNER-Relex Extraction Config** (`docs/schema/gliner_schema.json`):  
   Provides label lists (`entity_labels`, `relation_labels`) and `allowed_pairs` matrix for joint entity-relation extraction.
2. **Deterministic Legal Extraction Rules** (`docs/schema/deterministic_rules_schema.json`):  
   Provides pattern matching templates and valid triplet constraints for rule-based regex/NLP engines.
3. **Neo4j Cypher DDL Script** (`docs/schema/neo4j_schema.cypher`):  
   Includes `CREATE CONSTRAINT` unique identifier statements, property existence rules, and lookup indexes.
4. **Human-in-the-Loop Graph Editor UI Schema** (`docs/schema/graph_editor_schema.json`):  
   Form field definitions, category UI themes (colors/icons), and client-side edge validation matrices for React/Cytoscape.

---

## 7. Code Architecture & Verification

The schema implementation is modularized in `backend/app/schema/`:

- `entity_types.py`: `EntityType` enum, metadata, and hierarchy resolver.
- `relationship_types.py`: `RelationshipType` enum and directionality metadata.
- `provenance.py`: Pydantic `Provenance` model with confidence & page validators.
- `temporal.py`: Pydantic `TemporalProperties` model with date coherence validators.
- `constraints.py`: Exhaustive `RELATIONSHIP_CONSTRAINTS` dictionary.
- `models.py`: `LegalNode`, `LegalRelationship`, and `Triplet` models.
- `validator.py`: `SchemaValidator` engine enforcing strict triplet rules.
- `registry.py`: `SchemaRegistry` for controlled lookup and extension.
- `exporters/`: Multi-target format exporters.

### Verification Status

The schema is verified by 24 comprehensive unit tests in `backend/tests/test_schema_validation.py`:

```bash
pytest backend/tests/test_schema_validation.py
# Result: 24 passed in 0.22s
```
