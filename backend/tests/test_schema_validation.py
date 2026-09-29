"""
Comprehensive Unit Tests for Legal Case Knowledge Graph Schema Validation.
"""

from datetime import datetime, timezone, timedelta
import pytest

from app.schema.entity_types import EntityType, get_entity_hierarchy
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import Provenance, ExtractionMethod
from app.schema.temporal import TemporalProperties, EventStatus
from app.schema.models import LegalNode, LegalRelationship, Triplet
from app.schema.validator import (
    SchemaValidator,
    InvalidEntityTypeError,
    InvalidRelationshipTypeError,
    TripletConstraintViolationError,
    ProvenanceValidationError,
    TemporalValidationError,
)
from app.schema.registry import SchemaRegistry
from app.schema.exporters import (
    export_gliner_config,
    export_neo4j_schema,
    export_graph_editor_schema,
    export_deterministic_rules_schema,
)


class TestEntityTypeAndHierarchy:
    def test_all_25_entity_types_exist(self):
        expected_types = {
            "CASE", "PERSON", "LAWYER", "JUDGE", "WITNESS",
            "ORGANIZATION", "COMPANY", "LAW_FIRM", "GOVERNMENT_AGENCY", "COURT",
            "STATUTE", "REGULATION", "LEGAL_CONCEPT", "LEGAL_ISSUE", "CLAIM",
            "DOCUMENT", "CONTRACT", "EVIDENCE", "EXHIBIT", "FILING",
            "TESTIMONY", "EVENT", "DATE", "DEADLINE", "HEARING"
        }
        actual_types = {e.value for e in EntityType}
        assert actual_types == expected_types

    def test_valid_entity_type_validation(self):
        assert SchemaValidator.validate_entity_type("LAWYER") == EntityType.LAWYER

    def test_invalid_entity_type_rejection(self):
        with pytest.raises(InvalidEntityTypeError) as exc_info:
            SchemaValidator.validate_entity_type("UNKNOWN_AI_ENTITY")
        assert "Invalid entity type 'UNKNOWN_AI_ENTITY'" in str(exc_info.value)

    def test_entity_hierarchy(self):
        lawyer_hierarchy = get_entity_hierarchy(EntityType.LAWYER)
        assert lawyer_hierarchy == [EntityType.LAWYER, EntityType.PERSON]

        contract_hierarchy = get_entity_hierarchy(EntityType.CONTRACT)
        assert contract_hierarchy == [EntityType.CONTRACT, EntityType.DOCUMENT]


class TestRelationshipTypes:
    def test_all_24_relationship_types_exist(self):
        expected_rels = {
            "PLAINTIFF_IN", "DEFENDANT_IN", "REPRESENTED_BY", "DECIDED_BY", "FILED_IN",
            "CITES", "APPLIES", "INTERPRETS", "OVERRULES", "FOLLOWS",
            "DISTINGUISHES", "SUPPORTED_BY", "CONTRADICTED_BY", "EVIDENCED_BY", "MENTIONED_IN",
            "WORKS_FOR", "EMPLOYED_BY", "OWNS", "REPRESENTS", "OCCURRED_ON",
            "OCCURRED_IN", "BEFORE", "AFTER", "HAS_DEADLINE"
        }
        actual_rels = {r.value for r in RelationshipType}
        assert actual_rels == expected_rels

    def test_invalid_relationship_type_rejection(self):
        with pytest.raises(InvalidRelationshipTypeError):
            SchemaValidator.validate_relationship_type("INVALID_RELATION_NAME")


class TestTripletConstraints:
    def test_valid_triplets_pass(self):
        assert SchemaValidator.validate_triplet(
            EntityType.PERSON, RelationshipType.PLAINTIFF_IN, EntityType.CASE
        )
        assert SchemaValidator.validate_triplet(
            EntityType.LAWYER, RelationshipType.REPRESENTS, EntityType.COMPANY
        )
        assert SchemaValidator.validate_triplet(
            EntityType.CASE, RelationshipType.DECIDED_BY, EntityType.JUDGE
        )
        assert SchemaValidator.validate_triplet(
            EntityType.EVENT, RelationshipType.OCCURRED_ON, EntityType.DATE
        )

    def test_subtype_inheritance_in_triplets(self):
        # LAWYER is a subtype of PERSON, so LAWYER can be PLAINTIFF_IN CASE
        assert SchemaValidator.validate_triplet(
            EntityType.LAWYER, RelationshipType.PLAINTIFF_IN, EntityType.CASE, allow_subtype_inheritance=True
        )

    def test_invalid_triplet_rejection(self):
        with pytest.raises(TripletConstraintViolationError) as exc_info:
            SchemaValidator.validate_triplet(
                EntityType.JUDGE, RelationshipType.PLAINTIFF_IN, EntityType.STATUTE
            )
        assert "Invalid relationship triplet" in str(exc_info.value)

    def test_prevent_arbitrary_ai_inventions(self):
        with pytest.raises(InvalidRelationshipTypeError):
            SchemaValidator.validate_relationship_type("LIKES_ATTORNEY")


class TestProvenanceValidation:
    def test_valid_provenance(self):
        prov = Provenance(
            case_id="case-123",
            source_document_id="doc-456",
            source_page=12,
            source_text="John Doe filed a complaint.",
            char_span=(10, 35),
            confidence=0.98,
            extraction_method=ExtractionMethod.GLINER_RELEX,
            created_by="gliner_agent"
        )
        SchemaValidator.validate_provenance(prov)
        assert prov.confidence == 0.98

    def test_invalid_confidence_out_of_bounds(self):
        with pytest.raises(ValueError):
            Provenance(
                case_id="case-1",
                source_document_id="doc-1",
                confidence=1.5
            )

    def test_invalid_char_span_start_greater_than_end(self):
        with pytest.raises(ValueError):
            Provenance(
                case_id="case-1",
                source_document_id="doc-1",
                char_span=(50, 20)
            )

    def test_empty_case_id_rejection(self):
        prov = Provenance(
            case_id="",
            source_document_id="doc-1"
        )
        with pytest.raises(ProvenanceValidationError):
            SchemaValidator.validate_provenance(prov)


class TestTemporalValidation:
    def test_valid_temporal_dates(self):
        now = datetime.now(timezone.utc)
        later = now + timedelta(days=5)
        temp = TemporalProperties(
            start_date=now,
            end_date=later,
            status=EventStatus.UPCOMING
        )
        SchemaValidator.validate_temporal(temp)

    def test_start_date_after_end_date_rejection(self):
        now = datetime.now(timezone.utc)
        earlier = now - timedelta(days=5)
        with pytest.raises(ValueError):
            TemporalProperties(
                start_date=now,
                end_date=earlier
            )

    def test_overdue_deadline_check(self):
        past_deadline = datetime.now(timezone.utc) - timedelta(days=2)
        temp = TemporalProperties(
            deadline=past_deadline,
            status=EventStatus.PENDING
        )
        assert temp.check_is_overdue() is True


class TestLegalNodeAndRelationshipModels:
    def test_node_creation_and_validation(self):
        node = LegalNode(
            name="Judge Smith",
            entity_type=EntityType.JUDGE,
            properties={"court_chamber": "Chamber 402"},
            provenance=Provenance(
                case_id="case-999",
                source_document_id="doc-888",
                extraction_method=ExtractionMethod.MANUAL_HUMAN
            )
        )
        SchemaValidator.validate_node(node)
        assert node.entity_type == EntityType.JUDGE

    def test_relationship_creation_and_validation(self):
        rel = LegalRelationship(
            source_id="lawyer-1",
            source_type=EntityType.LAWYER,
            relationship_type=RelationshipType.REPRESENTS,
            target_id="person-1",
            target_type=EntityType.PERSON,
            provenance=Provenance(
                case_id="case-999",
                source_document_id="doc-888"
            )
        )
        SchemaValidator.validate_relationship(rel)
        assert rel.triplet.source_type == EntityType.LAWYER


class TestSchemaRegistryAndExporters:
    def test_registry_summary(self):
        registry = SchemaRegistry()
        spec = registry.export_full_ontology_spec()
        assert spec["total_entity_types"] == 25
        assert spec["total_relationship_types"] == 24
        assert len(spec["relationship_types"]) == 24

    def test_gliner_exporter(self):
        config = export_gliner_config()
        assert len(config["entity_labels"]) == 25
        assert len(config["relation_labels"]) == 24
        assert len(config["allowed_pairs"]) > 0

    def test_neo4j_exporter(self):
        cypher = export_neo4j_schema()
        assert "CREATE CONSTRAINT constraint_case_id_unique" in cypher
        assert "CREATE INDEX index_person_name" in cypher

    def test_editor_exporter(self):
        schema = export_graph_editor_schema()
        assert "CASE" in schema["node_types"]
        assert len(schema["provenance_fields"]) == 6

    def test_rules_exporter(self):
        rules = export_deterministic_rules_schema()
        assert len(rules["relationship_rules"]) == 24
