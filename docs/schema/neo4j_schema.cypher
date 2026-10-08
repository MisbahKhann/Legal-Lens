// =============================================================================
// US LEGAL CASE KNOWLEDGE GRAPH - NEO4J SCHEMA DEFINITION
// Auto-generated from authoritative Schema Registry
// =============================================================================

// -----------------------------------------------------------------------------
// 1. NODE UNIQUENESS & IDENTIFIER CONSTRAINTS
// -----------------------------------------------------------------------------
CREATE CONSTRAINT constraint_case_id_unique IF NOT EXISTS FOR (n:`CASE`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_person_id_unique IF NOT EXISTS FOR (n:`PERSON`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_lawyer_id_unique IF NOT EXISTS FOR (n:`LAWYER`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_judge_id_unique IF NOT EXISTS FOR (n:`JUDGE`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_witness_id_unique IF NOT EXISTS FOR (n:`WITNESS`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_organization_id_unique IF NOT EXISTS FOR (n:`ORGANIZATION`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_company_id_unique IF NOT EXISTS FOR (n:`COMPANY`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_law_firm_id_unique IF NOT EXISTS FOR (n:`LAW_FIRM`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_government_agency_id_unique IF NOT EXISTS FOR (n:`GOVERNMENT_AGENCY`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_court_id_unique IF NOT EXISTS FOR (n:`COURT`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_statute_id_unique IF NOT EXISTS FOR (n:`STATUTE`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_regulation_id_unique IF NOT EXISTS FOR (n:`REGULATION`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_legal_concept_id_unique IF NOT EXISTS FOR (n:`LEGAL_CONCEPT`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_legal_issue_id_unique IF NOT EXISTS FOR (n:`LEGAL_ISSUE`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_claim_id_unique IF NOT EXISTS FOR (n:`CLAIM`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_document_id_unique IF NOT EXISTS FOR (n:`DOCUMENT`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_contract_id_unique IF NOT EXISTS FOR (n:`CONTRACT`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_evidence_id_unique IF NOT EXISTS FOR (n:`EVIDENCE`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_exhibit_id_unique IF NOT EXISTS FOR (n:`EXHIBIT`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_filing_id_unique IF NOT EXISTS FOR (n:`FILING`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_testimony_id_unique IF NOT EXISTS FOR (n:`TESTIMONY`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_event_id_unique IF NOT EXISTS FOR (n:`EVENT`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_date_id_unique IF NOT EXISTS FOR (n:`DATE`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_deadline_id_unique IF NOT EXISTS FOR (n:`DEADLINE`) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_hearing_id_unique IF NOT EXISTS FOR (n:`HEARING`) REQUIRE n.id IS UNIQUE;

// -----------------------------------------------------------------------------
// 2. PROPERTY INDEXES FOR PERFORMANCE
// -----------------------------------------------------------------------------
CREATE INDEX index_case_case_id IF NOT EXISTS FOR (n:`CASE`) ON (n.case_id);
CREATE INDEX index_case_name IF NOT EXISTS FOR (n:`CASE`) ON (n.name);
CREATE INDEX index_person_case_id IF NOT EXISTS FOR (n:`PERSON`) ON (n.case_id);
CREATE INDEX index_person_name IF NOT EXISTS FOR (n:`PERSON`) ON (n.name);
CREATE INDEX index_lawyer_case_id IF NOT EXISTS FOR (n:`LAWYER`) ON (n.case_id);
CREATE INDEX index_lawyer_name IF NOT EXISTS FOR (n:`LAWYER`) ON (n.name);
CREATE INDEX index_judge_case_id IF NOT EXISTS FOR (n:`JUDGE`) ON (n.case_id);
CREATE INDEX index_judge_name IF NOT EXISTS FOR (n:`JUDGE`) ON (n.name);
CREATE INDEX index_witness_case_id IF NOT EXISTS FOR (n:`WITNESS`) ON (n.case_id);
CREATE INDEX index_witness_name IF NOT EXISTS FOR (n:`WITNESS`) ON (n.name);
CREATE INDEX index_organization_case_id IF NOT EXISTS FOR (n:`ORGANIZATION`) ON (n.case_id);
CREATE INDEX index_organization_name IF NOT EXISTS FOR (n:`ORGANIZATION`) ON (n.name);
CREATE INDEX index_company_case_id IF NOT EXISTS FOR (n:`COMPANY`) ON (n.case_id);
CREATE INDEX index_company_name IF NOT EXISTS FOR (n:`COMPANY`) ON (n.name);
CREATE INDEX index_law_firm_case_id IF NOT EXISTS FOR (n:`LAW_FIRM`) ON (n.case_id);
CREATE INDEX index_law_firm_name IF NOT EXISTS FOR (n:`LAW_FIRM`) ON (n.name);
CREATE INDEX index_government_agency_case_id IF NOT EXISTS FOR (n:`GOVERNMENT_AGENCY`) ON (n.case_id);
CREATE INDEX index_government_agency_name IF NOT EXISTS FOR (n:`GOVERNMENT_AGENCY`) ON (n.name);
CREATE INDEX index_court_case_id IF NOT EXISTS FOR (n:`COURT`) ON (n.case_id);
CREATE INDEX index_court_name IF NOT EXISTS FOR (n:`COURT`) ON (n.name);
CREATE INDEX index_statute_case_id IF NOT EXISTS FOR (n:`STATUTE`) ON (n.case_id);
CREATE INDEX index_statute_name IF NOT EXISTS FOR (n:`STATUTE`) ON (n.name);
CREATE INDEX index_regulation_case_id IF NOT EXISTS FOR (n:`REGULATION`) ON (n.case_id);
CREATE INDEX index_regulation_name IF NOT EXISTS FOR (n:`REGULATION`) ON (n.name);
CREATE INDEX index_legal_concept_case_id IF NOT EXISTS FOR (n:`LEGAL_CONCEPT`) ON (n.case_id);
CREATE INDEX index_legal_concept_name IF NOT EXISTS FOR (n:`LEGAL_CONCEPT`) ON (n.name);
CREATE INDEX index_legal_issue_case_id IF NOT EXISTS FOR (n:`LEGAL_ISSUE`) ON (n.case_id);
CREATE INDEX index_legal_issue_name IF NOT EXISTS FOR (n:`LEGAL_ISSUE`) ON (n.name);
CREATE INDEX index_claim_case_id IF NOT EXISTS FOR (n:`CLAIM`) ON (n.case_id);
CREATE INDEX index_claim_name IF NOT EXISTS FOR (n:`CLAIM`) ON (n.name);
CREATE INDEX index_document_case_id IF NOT EXISTS FOR (n:`DOCUMENT`) ON (n.case_id);
CREATE INDEX index_document_name IF NOT EXISTS FOR (n:`DOCUMENT`) ON (n.name);
CREATE INDEX index_contract_case_id IF NOT EXISTS FOR (n:`CONTRACT`) ON (n.case_id);
CREATE INDEX index_contract_name IF NOT EXISTS FOR (n:`CONTRACT`) ON (n.name);
CREATE INDEX index_evidence_case_id IF NOT EXISTS FOR (n:`EVIDENCE`) ON (n.case_id);
CREATE INDEX index_evidence_name IF NOT EXISTS FOR (n:`EVIDENCE`) ON (n.name);
CREATE INDEX index_exhibit_case_id IF NOT EXISTS FOR (n:`EXHIBIT`) ON (n.case_id);
CREATE INDEX index_exhibit_name IF NOT EXISTS FOR (n:`EXHIBIT`) ON (n.name);
CREATE INDEX index_filing_case_id IF NOT EXISTS FOR (n:`FILING`) ON (n.case_id);
CREATE INDEX index_filing_name IF NOT EXISTS FOR (n:`FILING`) ON (n.name);
CREATE INDEX index_testimony_case_id IF NOT EXISTS FOR (n:`TESTIMONY`) ON (n.case_id);
CREATE INDEX index_testimony_name IF NOT EXISTS FOR (n:`TESTIMONY`) ON (n.name);
CREATE INDEX index_event_case_id IF NOT EXISTS FOR (n:`EVENT`) ON (n.case_id);
CREATE INDEX index_event_name IF NOT EXISTS FOR (n:`EVENT`) ON (n.name);
CREATE INDEX index_date_case_id IF NOT EXISTS FOR (n:`DATE`) ON (n.case_id);
CREATE INDEX index_date_name IF NOT EXISTS FOR (n:`DATE`) ON (n.name);
CREATE INDEX index_deadline_case_id IF NOT EXISTS FOR (n:`DEADLINE`) ON (n.case_id);
CREATE INDEX index_deadline_name IF NOT EXISTS FOR (n:`DEADLINE`) ON (n.name);
CREATE INDEX index_hearing_case_id IF NOT EXISTS FOR (n:`HEARING`) ON (n.case_id);
CREATE INDEX index_hearing_name IF NOT EXISTS FOR (n:`HEARING`) ON (n.name);

// -----------------------------------------------------------------------------
// 3. PROVENANCE PROPERTY EXISTENCE CONSTRAINTS
// -----------------------------------------------------------------------------
CREATE CONSTRAINT constraint_case_provenance_case IF NOT EXISTS FOR (n:`CASE`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_person_provenance_case IF NOT EXISTS FOR (n:`PERSON`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_lawyer_provenance_case IF NOT EXISTS FOR (n:`LAWYER`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_judge_provenance_case IF NOT EXISTS FOR (n:`JUDGE`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_witness_provenance_case IF NOT EXISTS FOR (n:`WITNESS`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_organization_provenance_case IF NOT EXISTS FOR (n:`ORGANIZATION`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_company_provenance_case IF NOT EXISTS FOR (n:`COMPANY`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_law_firm_provenance_case IF NOT EXISTS FOR (n:`LAW_FIRM`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_government_agency_provenance_case IF NOT EXISTS FOR (n:`GOVERNMENT_AGENCY`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_court_provenance_case IF NOT EXISTS FOR (n:`COURT`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_statute_provenance_case IF NOT EXISTS FOR (n:`STATUTE`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_regulation_provenance_case IF NOT EXISTS FOR (n:`REGULATION`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_legal_concept_provenance_case IF NOT EXISTS FOR (n:`LEGAL_CONCEPT`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_legal_issue_provenance_case IF NOT EXISTS FOR (n:`LEGAL_ISSUE`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_claim_provenance_case IF NOT EXISTS FOR (n:`CLAIM`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_document_provenance_case IF NOT EXISTS FOR (n:`DOCUMENT`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_contract_provenance_case IF NOT EXISTS FOR (n:`CONTRACT`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_evidence_provenance_case IF NOT EXISTS FOR (n:`EVIDENCE`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_exhibit_provenance_case IF NOT EXISTS FOR (n:`EXHIBIT`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_filing_provenance_case IF NOT EXISTS FOR (n:`FILING`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_testimony_provenance_case IF NOT EXISTS FOR (n:`TESTIMONY`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_event_provenance_case IF NOT EXISTS FOR (n:`EVENT`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_date_provenance_case IF NOT EXISTS FOR (n:`DATE`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_deadline_provenance_case IF NOT EXISTS FOR (n:`DEADLINE`) REQUIRE n.case_id IS NOT NULL;
CREATE CONSTRAINT constraint_hearing_provenance_case IF NOT EXISTS FOR (n:`HEARING`) REQUIRE n.case_id IS NOT NULL;

// -----------------------------------------------------------------------------
// 4. AUTHORITATIVE RELATIONSHIP TRIPLET MATRICES
// -----------------------------------------------------------------------------
// Relationship: [PLAINTIFF_IN] | Sources: COMPANY, GOVERNMENT_AGENCY, LAWYER, LAW_FIRM, ORGANIZATION, PERSON | Targets: CASE
// Relationship: [DEFENDANT_IN] | Sources: COMPANY, GOVERNMENT_AGENCY, LAWYER, LAW_FIRM, ORGANIZATION, PERSON | Targets: CASE
// Relationship: [REPRESENTED_BY] | Sources: CASE, COMPANY, GOVERNMENT_AGENCY, ORGANIZATION, PERSON | Targets: LAWYER, LAW_FIRM
// Relationship: [DECIDED_BY] | Sources: CASE, CLAIM, FILING, HEARING, LEGAL_ISSUE | Targets: COURT, JUDGE
// Relationship: [FILED_IN] | Sources: CASE, CONTRACT, DOCUMENT, EVIDENCE, EXHIBIT, FILING | Targets: CASE, COURT
// Relationship: [CITES] | Sources: CASE, CONTRACT, DOCUMENT, FILING, REGULATION, STATUTE, TESTIMONY | Targets: CASE, CONTRACT, DOCUMENT, REGULATION, STATUTE
// Relationship: [APPLIES] | Sources: CASE, COURT, DOCUMENT, FILING, JUDGE | Targets: LEGAL_CONCEPT, LEGAL_ISSUE, REGULATION, STATUTE
// Relationship: [INTERPRETS] | Sources: CASE, COURT, DOCUMENT, FILING, JUDGE | Targets: CONTRACT, LEGAL_CONCEPT, REGULATION, STATUTE
// Relationship: [OVERRULES] | Sources: CASE, COURT | Targets: CASE
// Relationship: [FOLLOWS] | Sources: CASE, COURT | Targets: CASE
// Relationship: [DISTINGUISHES] | Sources: CASE, COURT, FILING | Targets: CASE
// Relationship: [SUPPORTED_BY] | Sources: CASE, CLAIM, FILING, LEGAL_ISSUE, TESTIMONY | Targets: CONTRACT, DOCUMENT, EVIDENCE, EXHIBIT, REGULATION, STATUTE, TESTIMONY
// Relationship: [CONTRADICTED_BY] | Sources: CLAIM, EVIDENCE, FILING, LEGAL_ISSUE, TESTIMONY | Targets: DOCUMENT, EVIDENCE, EXHIBIT, TESTIMONY
// Relationship: [EVIDENCED_BY] | Sources: CASE, CLAIM, EVENT, HEARING, LEGAL_ISSUE | Targets: CONTRACT, DOCUMENT, EVIDENCE, EXHIBIT, TESTIMONY
// Relationship: [MENTIONED_IN] | Sources: CASE, CLAIM, COMPANY, CONTRACT, COURT, DATE, DEADLINE, DOCUMENT, EVENT, EVIDENCE, EXHIBIT, FILING, GOVERNMENT_AGENCY, HEARING, JUDGE, LAWYER, LAW_FIRM, LEGAL_CONCEPT, LEGAL_ISSUE, ORGANIZATION, PERSON, REGULATION, STATUTE, TESTIMONY, WITNESS | Targets: CASE, CONTRACT, DOCUMENT, EXHIBIT, FILING, TESTIMONY
// Relationship: [WORKS_FOR] | Sources: LAWYER, PERSON, WITNESS | Targets: COMPANY, COURT, GOVERNMENT_AGENCY, LAW_FIRM, ORGANIZATION
// Relationship: [EMPLOYED_BY] | Sources: LAWYER, PERSON, WITNESS | Targets: COMPANY, COURT, GOVERNMENT_AGENCY, LAW_FIRM, ORGANIZATION
// Relationship: [OWNS] | Sources: COMPANY, GOVERNMENT_AGENCY, LAW_FIRM, ORGANIZATION, PERSON | Targets: COMPANY, CONTRACT, DOCUMENT, EVIDENCE, EXHIBIT, ORGANIZATION
// Relationship: [REPRESENTS] | Sources: LAWYER, LAW_FIRM | Targets: CASE, COMPANY, GOVERNMENT_AGENCY, ORGANIZATION, PERSON
// Relationship: [OCCURRED_ON] | Sources: CASE, CONTRACT, DOCUMENT, EVENT, FILING, HEARING | Targets: DATE
// Relationship: [OCCURRED_IN] | Sources: DOCUMENT, EVENT, HEARING, TESTIMONY | Targets: CASE, COURT
// Relationship: [BEFORE] | Sources: DATE, DEADLINE, EVENT, FILING, HEARING | Targets: DATE, DEADLINE, EVENT, FILING, HEARING
// Relationship: [AFTER] | Sources: DATE, DEADLINE, EVENT, FILING, HEARING | Targets: DATE, DEADLINE, EVENT, FILING, HEARING
// Relationship: [HAS_DEADLINE] | Sources: CASE, CLAIM, EVENT, FILING, HEARING, LEGAL_ISSUE | Targets: DATE, DEADLINE