"""
Unit tests for Step 8 Neo4j Knowledge Graph Storage using mock drivers.
Verifies connection config, entity/relationship/temporal event MERGE operations,
case isolation, idempotency, invalid record filtering, and graph retrieval queries.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.resolution.models import CanonicalEntity, ResolvedRelation
from app.validation.models import (
    ValidationResult,
    ValidationRecord,
    ValidationStatus,
    ValidationSeverity,
    RecordType,
)
from app.temporal.models import (
    CaseTimeline,
    TimelineEvent,
    TemporalRelationship,
    DatePrecision,
    TemporalStatus,
)
from app.storage.neo4j_store import Neo4jGraphStore
from app.storage.neo4j_pipeline import Neo4jStoragePipeline


@pytest.fixture
def mock_store():
    """Provides a Neo4jGraphStore instance with a mocked driver & session."""
    store = Neo4jGraphStore(
        uri="bolt://localhost:7687",
        username="test_user",
        password="test_password",
        database="neo4j",
    )
    store._driver = MagicMock()
    mock_session = MagicMock()
    store._driver.session.return_value.__enter__.return_value = mock_session
    mock_result = MagicMock()
    mock_session.run.return_value = mock_result
    mock_result.consume.return_value.counters.nodes_deleted = 5
    return store, mock_session


@pytest.fixture
def sample_validation_result():
    """Constructs a representative ValidationResult with valid and invalid records."""
    case_id = "case_test_001"
    doc_id = "doc_test_001"

    ent1 = CanonicalEntity(
        canonical_id="ent_001",
        entity_type=EntityType.PERSON,
        canonical_name="John Doe",
        aliases=["J. Doe"],
        document_id=doc_id,
        case_id=case_id,
    )
    ent2 = CanonicalEntity(
        canonical_id="ent_002",
        entity_type=EntityType.ORGANIZATION,
        canonical_name="Acme Corp",
        aliases=[],
        document_id=doc_id,
        case_id=case_id,
    )
    invalid_ent = CanonicalEntity(
        canonical_id="ent_invalid_99",
        entity_type=EntityType.COURT,
        canonical_name="Invalid Court",
        aliases=[],
        document_id=doc_id,
        case_id=case_id,
    )

    rel1 = ResolvedRelation(
        relation_id="rel_001",
        relation_type=RelationshipType.WORKS_FOR,
        source_entity_id="ent_001",
        target_entity_id="ent_002",
        document_id=doc_id,
        case_id=case_id,
        is_valid=True,
    )
    invalid_rel = ResolvedRelation(
        relation_id="rel_invalid_99",
        relation_type=RelationshipType.PLAINTIFF_IN,
        source_entity_id="ent_001",
        target_entity_id="ent_002",
        document_id=doc_id,
        case_id=case_id,
        is_valid=False,
    )

    review_record = ValidationRecord(
        record_type=RecordType.RELATIONSHIP,
        status=ValidationStatus.REVIEW_REQUIRED,
        severity=ValidationSeverity.MEDIUM,
        validation_rule="UNTRUSTED_TYPE",
        message="Review needed",
        relationship_id="rel_review_99",
    )

    return ValidationResult(
        document_id=doc_id,
        case_id=case_id,
        validated_entities=[ent1, ent2],
        invalid_entities=[invalid_ent],
        validated_relationships=[rel1],
        invalid_relationships=[invalid_rel],
        review_required=[review_record],
    )


@pytest.fixture
def sample_case_timeline():
    """Constructs a representative CaseTimeline output from Step 7."""
    case_id = "case_test_001"
    doc_id = "doc_test_001"

    ev1 = TimelineEvent(
        event_id="evt_001",
        canonical_entity_id="ent_001",
        event_type=EntityType.EVENT,
        description="Filing of Complaint",
        event_date="2023-01-15",
        date_precision=DatePrecision.EXACT_DAY,
        temporal_status=TemporalStatus.RESOLVED,
        source_document_id=doc_id,
        source_page=1,
        source_text="Complaint filed on Jan 15, 2023.",
        provenance={"case_id": case_id, "source_document_id": doc_id, "source_page": 1},
    )

    ev2 = TimelineEvent(
        event_id="evt_002",
        event_type=EntityType.EVENT,
        description="Court Hearing",
        event_date="2023-02-20",
        date_precision=DatePrecision.EXACT_DAY,
        temporal_status=TemporalStatus.RESOLVED,
        source_document_id=doc_id,
        source_page=3,
        source_text="Hearing scheduled Feb 20, 2023.",
        provenance={"case_id": case_id, "source_document_id": doc_id, "source_page": 3},
    )

    temp_rel = TemporalRelationship(
        relationship_id="trel_001",
        source_event_id="evt_001",
        relationship_type=RelationshipType.BEFORE,
        target_event_id="evt_002",
        provenance={"case_id": case_id, "source_document_id": doc_id, "source_page": 1},
    )

    return CaseTimeline(
        document_id=doc_id,
        case_id=case_id,
        events=[ev1, ev2],
        temporal_relationships=[temp_rel],
    )


# ==============================================================================
# TESTS
# ==============================================================================


def test_neo4j_connection_config(monkeypatch):
    """Test that Neo4jGraphStore respects environment variables."""
    monkeypatch.setenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "custom_user")
    monkeypatch.setenv("NEO4J_PASSWORD", "custom_pass")
    monkeypatch.setenv("NEO4J_DATABASE", "custom_db")

    store = Neo4jGraphStore()
    assert store.uri == "bolt://127.0.0.1:7687"
    assert store.username == "custom_user"
    assert store.password == "custom_pass"
    assert store.database == "custom_db"


def test_upsert_entities_cypher_structure(mock_store):
    """Test entity node upsert Cypher query and parameter passing."""
    store, mock_session = mock_store
    entities = [
        {
            "id": "ent_001",
            "canonical_name": "John Doe",
            "normalized_name": "john doe",
            "entity_type": "PERSON",
            "aliases": ["J. Doe"],
            "document_id": "doc_1",
            "source_document_id": "doc_1",
            "source_page": 1,
            "source_text": "John Doe",
            "confidence": 1.0,
            "extraction_method": "GLINER_RELEX",
            "created_at": "2026-10-08T00:00:00Z",
            "updated_at": "2026-10-08T00:00:00Z",
        }
    ]

    count = store.upsert_entities(entities, case_id="case_123")
    assert count == 1
    assert mock_session.run.called
    cypher_arg = mock_session.run.call_args[0][0]
    assert "MERGE (n:LegalEntity {id: ent.id, case_id: $case_id})" in cypher_arg
    assert mock_session.run.call_args[1]["case_id"] == "case_123"


def test_upsert_relationships_cypher_structure(mock_store):
    """Test relationship edge upsert Cypher query and case scoping."""
    store, mock_session = mock_store
    relationships = [
        {
            "id": "rel_001",
            "relationship_type": "WORKS_FOR",
            "source_id": "ent_001",
            "target_id": "ent_002",
            "document_id": "doc_1",
            "source_document_id": "doc_1",
            "source_page": 1,
            "source_text": "works at",
            "confidence": 0.95,
            "extraction_method": "GLINER_RELEX",
            "created_at": "2026-10-08T00:00:00Z",
        }
    ]

    count = store.upsert_relationships(relationships, case_id="case_123")
    assert count == 1
    cypher_arg = mock_session.run.call_args[0][0]
    assert (
        "MERGE (s)-[r:`WORKS_FOR` {id: rel.id, case_id: $case_id}]->(t)" in cypher_arg
    )


def test_pipeline_import_and_filtering(
    mock_store, sample_validation_result, sample_case_timeline
):
    """Test that Step 8 pipeline filters INVALID & REVIEW_REQUIRED records and imports valid elements."""
    store, mock_session = mock_store
    pipeline = Neo4jStoragePipeline(store=store)

    summary = pipeline.import_case_graph(
        validation_result=sample_validation_result,
        case_timeline=sample_case_timeline,
    )

    assert summary["status"] == "SUCCESS"
    assert summary["case_id"] == "case_test_001"
    assert summary["entities_imported"] == 2
    assert summary["relationships_imported"] == 1
    assert summary["timeline_events_imported"] == 2
    assert summary["temporal_relationships_imported"] == 1
    assert summary["invalid_entities_filtered"] == 1
    assert (
        summary["invalid_relationships_filtered"] == 2
    )  # 1 invalid + 1 review_required


def test_case_isolation_queries(mock_store):
    """Verify that retrieval queries filter by case_id strictly."""
    store, mock_session = mock_store

    mock_session.run.return_value = []
    store.get_case_entities("case_ABC")
    query_run = mock_session.run.call_args_list[-1]
    assert "WHERE" in query_run[0][0] or "{case_id: $case_id}" in query_run[0][0]
    assert query_run[1]["case_id"] == "case_ABC"

    store.get_case_relationships("case_ABC")
    query_run = mock_session.run.call_args_list[-1]
    assert "{case_id: $case_id}" in query_run[0][0]
    assert query_run[1]["case_id"] == "case_ABC"


def test_idempotent_reimport(
    mock_store, sample_validation_result, sample_case_timeline
):
    """Verify that re-importing the exact same case pipeline output produces identical summary counts."""
    store, mock_session = mock_store
    pipeline = Neo4jStoragePipeline(store=store)

    res1 = pipeline.import_case_graph(sample_validation_result, sample_case_timeline)
    res2 = pipeline.import_case_graph(sample_validation_result, sample_case_timeline)

    assert res1["entities_imported"] == res2["entities_imported"]
    assert res1["relationships_imported"] == res2["relationships_imported"]
    assert res1["timeline_events_imported"] == res2["timeline_events_imported"]


def test_get_complete_case_graph(mock_store):
    """Test get_complete_case_graph helper output structure."""
    store, mock_session = mock_store

    with patch.object(
        store, "get_case_entities", return_value=[{"id": "ent_1"}]
    ), patch.object(
        store, "get_case_relationships", return_value=[{"id": "rel_1"}]
    ), patch.object(
        store, "get_case_timeline_events", return_value=[{"id": "evt_1"}]
    ):

        graph = store.get_complete_case_graph("case_xyz")
        assert graph["case_id"] == "case_xyz"
        assert graph["summary"]["entity_count"] == 1
        assert graph["summary"]["relationship_count"] == 1
        assert graph["summary"]["timeline_event_count"] == 1
        assert len(graph["entities"]) == 1
        assert len(graph["relationships"]) == 1
        assert len(graph["timeline_events"]) == 1
