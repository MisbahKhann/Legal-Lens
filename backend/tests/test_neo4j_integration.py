"""
Real Neo4j Integration Test for Step 8 Knowledge Graph Storage.
Attempts connection to an active local/remote Neo4j instance.
If Neo4j is offline, skips gracefully and outputs setup instructions.
"""

import pytest
import logging
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.resolution.models import CanonicalEntity, ResolvedRelation
from app.validation.models import ValidationResult
from app.temporal.models import (
    CaseTimeline,
    TimelineEvent,
    DatePrecision,
    TemporalStatus,
)
from app.storage.neo4j_store import Neo4jGraphStore
from app.storage.neo4j_pipeline import Neo4jStoragePipeline

logger = logging.getLogger(__name__)


def check_neo4j_online() -> bool:
    """Helper to check if Neo4j is reachable before running integration tests."""
    store = Neo4jGraphStore()
    try:
        driver = store.connect()
        driver.verify_connectivity()
        store.close()
        return True
    except Exception as e:
        logger.info("Neo4j connectivity check failed: %s", str(e))
        return False


@pytest.mark.skipif(
    not check_neo4j_online(),
    reason="Live Neo4j instance is not reachable. (To test against a real database: docker run -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password neo4j:latest)",
)
def test_real_neo4j_integration_end_to_end():
    """Real integration test against live Neo4j database."""
    case_id = "case_integration_test_001"
    doc_id = "doc_integration_001"

    store = Neo4jGraphStore()
    pipeline = Neo4jStoragePipeline(store=store)

    # Clean previous test state
    store.clear_case_graph(case_id)

    # 1. Construct test validation result
    ent1 = CanonicalEntity(
        canonical_id="ent_integ_001",
        entity_type=EntityType.PERSON,
        canonical_name="Alice Smith",
        aliases=["A. Smith"],
        document_id=doc_id,
        case_id=case_id,
    )
    ent2 = CanonicalEntity(
        canonical_id="ent_integ_002",
        entity_type=EntityType.ORGANIZATION,
        canonical_name="Lex Corp",
        aliases=[],
        document_id=doc_id,
        case_id=case_id,
    )
    rel1 = ResolvedRelation(
        relation_id="rel_integ_001",
        relation_type=RelationshipType.REPRESENTED_BY,
        source_entity_id="ent_integ_001",
        target_entity_id="ent_integ_002",
        document_id=doc_id,
        case_id=case_id,
        is_valid=True,
    )
    val_result = ValidationResult(
        document_id=doc_id,
        case_id=case_id,
        validated_entities=[ent1, ent2],
        validated_relationships=[rel1],
    )

    # 2. Construct test timeline
    ev1 = TimelineEvent(
        event_id="evt_integ_001",
        canonical_entity_id="ent_integ_001",
        event_type=EntityType.EVENT,
        description="Filing of lawsuit",
        event_date="2023-05-10",
        date_precision=DatePrecision.EXACT_DAY,
        temporal_status=TemporalStatus.RESOLVED,
        source_document_id=doc_id,
        source_page=1,
        source_text="Lawsuit filed May 10, 2023.",
        provenance={"case_id": case_id, "source_document_id": doc_id, "source_page": 1},
    )
    timeline = CaseTimeline(
        document_id=doc_id,
        case_id=case_id,
        events=[ev1],
    )

    # 3. Import Case Graph
    summary = pipeline.import_case_graph(val_result, timeline)
    assert summary["status"] == "SUCCESS"
    assert summary["entities_imported"] == 2
    assert summary["relationships_imported"] == 1
    assert summary["timeline_events_imported"] == 1

    # 4. Retrieve imported graph & verify
    graph = store.get_complete_case_graph(case_id)
    assert len(graph["entities"]) == 2
    assert len(graph["relationships"]) == 1
    assert len(graph["timeline_events"]) == 1

    # 5. Test Idempotency (Import again, ensure count remains identical)
    summary2 = pipeline.import_case_graph(val_result, timeline)
    graph2 = store.get_complete_case_graph(case_id)
    assert len(graph2["entities"]) == 2
    assert len(graph2["relationships"]) == 1
    assert len(graph2["timeline_events"]) == 1

    # 6. Test Case Isolation
    graph_other = store.get_complete_case_graph("case_non_existent_999")
    assert len(graph_other["entities"]) == 0
    assert len(graph_other["relationships"]) == 0

    # Clean up test state
    store.clear_case_graph(case_id)
    store.close()
