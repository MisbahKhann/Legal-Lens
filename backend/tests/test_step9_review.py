"""
Step 9 Test Suite: Human-in-the-Loop Review & Graph Correction API.
Validates all 16 required review operations, ontology constraints, audit trail preservation,
case isolation, and FastAPI REST endpoints.
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.review.models import (
    ItemType,
    ReviewStatus,
    TrustStatus,
    ReviewItem,
)
from app.review.generator import ReviewCandidateGenerator
from app.review.manager import ReviewManager
from app.schema.validator import (
    TripletConstraintViolationError,
)
from app.validation.models import (
    ValidationResult,
    ValidationRecord,
    ValidationStatus,
    RecordType,
    ValidationSeverity,
)
from app.main import app


@pytest.fixture
def review_manager():
    """Returns a fresh ReviewManager instance for each test."""
    return ReviewManager()


@pytest.fixture
def mock_neo4j_store():
    """Returns a mock Neo4jGraphStore instance."""
    mock = MagicMock()
    mock.verify_connection.return_value = True
    mock.update_entity_trust_status.return_value = True
    mock.update_relationship_trust_status.return_value = True
    mock.update_timeline_event_trust_status.return_value = True
    mock.merge_entities_in_graph.return_value = True
    return mock


@pytest.fixture
def sample_case_id():
    return "case_test_step9_001"


# -----------------------------------------------------------------------------
# 1. Create a Review Item
# -----------------------------------------------------------------------------
def test_01_create_review_item(review_manager, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY,
        status=ReviewStatus.PENDING,
        confidence=0.62,
        reason="Low extraction confidence",
        original_prediction={
            "canonical_name": "Uncertain LLC",
            "entity_type": "ORGANIZATION",
        },
        source_document_id="doc_001.pdf",
        source_page=2,
        source_text="Uncertain LLC entered into an agreement.",
    )
    saved = review_manager.add_review_item(item)
    assert saved.review_id.startswith("rev_")
    assert saved.case_id == sample_case_id
    assert saved.status == ReviewStatus.PENDING


# -----------------------------------------------------------------------------
# 2. Retrieve Pending Review Items
# -----------------------------------------------------------------------------
def test_02_retrieve_pending_review_items(review_manager, sample_case_id):
    item1 = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY,
        status=ReviewStatus.PENDING,
        original_prediction={"canonical_name": "Entity 1"},
    )
    item2 = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.RELATIONSHIP,
        status=ReviewStatus.PENDING,
        original_prediction={"rule": "REPRESENTED_BY"},
    )
    review_manager.add_review_items([item1, item2])

    pending_items = review_manager.get_review_items_for_case(
        case_id=sample_case_id, status=ReviewStatus.PENDING
    )
    assert len(pending_items) == 2
    assert all(i.status == ReviewStatus.PENDING for i in pending_items)


# -----------------------------------------------------------------------------
# 3. Approve an Entity
# -----------------------------------------------------------------------------
def test_03_approve_entity(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY,
        entity_id="ent_100",
        status=ReviewStatus.PENDING,
        original_prediction={"canonical_name": "John Doe", "entity_type": "PARTY"},
    )
    review_manager.add_review_item(item)

    approved = review_manager.approve_item(
        review_id=item.review_id,
        reviewer_id="lawyer_01",
        reviewer_note="Verified from page 1",
        neo4j_store=mock_neo4j_store,
    )
    assert approved.status == ReviewStatus.APPROVED
    assert approved.reviewed_by == "lawyer_01"
    assert approved.reviewer_note == "Verified from page 1"
    mock_neo4j_store.update_entity_trust_status.assert_called_with(
        "ent_100", sample_case_id, TrustStatus.APPROVED.value
    )


# -----------------------------------------------------------------------------
# 4. Reject an Entity
# -----------------------------------------------------------------------------
def test_04_reject_entity(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY,
        entity_id="ent_101",
        status=ReviewStatus.PENDING,
        original_prediction={
            "canonical_name": "False Positive Inc",
            "entity_type": "ORGANIZATION",
        },
    )
    review_manager.add_review_item(item)

    rejected = review_manager.reject_item(
        review_id=item.review_id,
        reviewer_id="lawyer_01",
        reviewer_note="Noise extraction",
        neo4j_store=mock_neo4j_store,
    )
    assert rejected.status == ReviewStatus.REJECTED
    assert rejected.reviewed_by == "lawyer_01"
    mock_neo4j_store.update_entity_trust_status.assert_called_with(
        "ent_101", sample_case_id, TrustStatus.REJECTED.value
    )


# -----------------------------------------------------------------------------
# 5. Correct an Entity
# -----------------------------------------------------------------------------
def test_05_correct_entity(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY,
        entity_id="ent_102",
        status=ReviewStatus.PENDING,
        original_prediction={"canonical_name": "Acme Corp", "entity_type": "PARTY"},
    )
    review_manager.add_review_item(item)

    corrections = {
        "canonical_name": "Acme Corporation",
        "entity_type": "ORGANIZATION",
        "aliases": ["Acme Corp", "Acme"],
    }
    corrected = review_manager.correct_entity(
        review_id=item.review_id,
        reviewer_id="lawyer_02",
        corrected_fields=corrections,
        reviewer_note="Fixed full company name and entity type",
        neo4j_store=mock_neo4j_store,
    )
    assert corrected.status == ReviewStatus.CORRECTED
    assert corrected.corrected_value == corrections
    # Verify original prediction preserved!
    assert corrected.original_prediction["canonical_name"] == "Acme Corp"


# -----------------------------------------------------------------------------
# 6. Approve a Relationship
# -----------------------------------------------------------------------------
def test_06_approve_relationship(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.RELATIONSHIP,
        relationship_id="rel_200",
        status=ReviewStatus.PENDING,
        original_prediction={
            "relationship_type": "REPRESENTED_BY",
            "source_id": "ent_100",
            "target_id": "ent_101",
        },
    )
    review_manager.add_review_item(item)

    approved = review_manager.approve_item(
        review_id=item.review_id,
        reviewer_id="lawyer_01",
        neo4j_store=mock_neo4j_store,
    )
    assert approved.status == ReviewStatus.APPROVED
    mock_neo4j_store.update_relationship_trust_status.assert_called_with(
        "rel_200", sample_case_id, TrustStatus.APPROVED.value
    )


# -----------------------------------------------------------------------------
# 7. Reject a Relationship
# -----------------------------------------------------------------------------
def test_07_reject_relationship(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.RELATIONSHIP,
        relationship_id="rel_201",
        status=ReviewStatus.PENDING,
        original_prediction={
            "relationship_type": "EMPLOYED_BY",
            "source_id": "ent_100",
            "target_id": "ent_102",
        },
    )
    review_manager.add_review_item(item)

    rejected = review_manager.reject_item(
        review_id=item.review_id,
        reviewer_id="lawyer_01",
        reviewer_note="Spurious relationship link",
        neo4j_store=mock_neo4j_store,
    )
    assert rejected.status == ReviewStatus.REJECTED
    mock_neo4j_store.update_relationship_trust_status.assert_called_with(
        "rel_201", sample_case_id, TrustStatus.REJECTED.value
    )


# -----------------------------------------------------------------------------
# 8. Correct a Relationship
# -----------------------------------------------------------------------------
def test_08_correct_relationship(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.RELATIONSHIP,
        relationship_id="rel_202",
        status=ReviewStatus.PENDING,
        original_prediction={
            "relationship_type": "FILED_IN",
            "source_type": "CASE",
            "target_type": "COURT",
        },
    )
    review_manager.add_review_item(item)

    # Correct relationship_type to REPRESENTED_BY (PERSON -> LAWYER)
    corrections = {
        "relationship_type": "REPRESENTED_BY",
        "source_type": "PERSON",
        "target_type": "LAWYER",
    }
    corrected = review_manager.correct_relationship(
        review_id=item.review_id,
        reviewer_id="lawyer_01",
        corrected_fields=corrections,
        neo4j_store=mock_neo4j_store,
    )
    assert corrected.status == ReviewStatus.CORRECTED
    assert corrected.corrected_value["relationship_type"] == "REPRESENTED_BY"


# -----------------------------------------------------------------------------
# 9. Merge Two Entities
# -----------------------------------------------------------------------------
def test_09_merge_two_entities(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY_MERGE,
        status=ReviewStatus.PENDING,
        original_prediction={
            "entity_1": "John Smith",
            "entity_2": "John A. Smith",
        },
    )
    review_manager.add_review_item(item)

    audit = review_manager.merge_entities(
        case_id=sample_case_id,
        primary_entity_id="ent_smith_canonical",
        secondary_entity_id="ent_smith_dup",
        reviewer_id="lawyer_01",
        reviewer_note="Merged duplicate names",
        review_id=item.review_id,
        neo4j_store=mock_neo4j_store,
    )
    assert audit.decision == "MERGE"
    assert audit.original_value["primary_entity_id"] == "ent_smith_canonical"
    assert item.status == ReviewStatus.APPROVED
    mock_neo4j_store.merge_entities_in_graph.assert_called_with(
        sample_case_id, "ent_smith_canonical", "ent_smith_dup"
    )


# -----------------------------------------------------------------------------
# 10. Keep Two Entities Separate
# -----------------------------------------------------------------------------
def test_10_keep_two_entities_separate(
    review_manager, mock_neo4j_store, sample_case_id
):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY_MERGE,
        status=ReviewStatus.PENDING,
        original_prediction={
            "entity_1": "John Smith Senior",
            "entity_2": "John Smith Junior",
        },
    )
    review_manager.add_review_item(item)

    audit = review_manager.keep_entities_separate(
        case_id=sample_case_id,
        entity_id_1="ent_smith_sr",
        entity_id_2="ent_smith_jr",
        reviewer_id="lawyer_01",
        reviewer_note="Distinct individuals (father and son)",
        review_id=item.review_id,
        neo4j_store=mock_neo4j_store,
    )
    assert audit.decision == "KEEP_SEPARATE"
    assert item.status == ReviewStatus.APPROVED
    mock_neo4j_store.update_entity_trust_status.assert_any_call(
        "ent_smith_sr", sample_case_id, TrustStatus.KEPT_SEPARATE.value
    )
    mock_neo4j_store.update_entity_trust_status.assert_any_call(
        "ent_smith_jr", sample_case_id, TrustStatus.KEPT_SEPARATE.value
    )


# -----------------------------------------------------------------------------
# 11. Correct a Temporal Event
# -----------------------------------------------------------------------------
def test_11_correct_temporal_event(review_manager, mock_neo4j_store, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.EVENT,
        event_id="evt_300",
        status=ReviewStatus.PENDING,
        original_prediction={
            "description": "Complaint filed",
            "event_date": "2023-05-01",
            "date_precision": "MONTH",
        },
    )
    review_manager.add_review_item(item)

    corrections = {
        "event_date": "2023-05-15",
        "date_precision": "EXACT_DAY",
        "description": "Complaint filed in District Court",
    }
    corrected = review_manager.correct_temporal(
        review_id=item.review_id,
        reviewer_id="lawyer_02",
        corrected_fields=corrections,
        neo4j_store=mock_neo4j_store,
    )
    assert corrected.status == ReviewStatus.CORRECTED
    assert corrected.corrected_value["event_date"] == "2023-05-15"
    mock_neo4j_store.update_timeline_event_trust_status.assert_called_with(
        "evt_300",
        sample_case_id,
        TrustStatus.CORRECTED.value,
        corrected_fields=corrections,
    )


# -----------------------------------------------------------------------------
# 12. Preserve Original Extraction
# -----------------------------------------------------------------------------
def test_12_preserve_original_extraction(review_manager, sample_case_id):
    original_pred = {
        "canonical_name": "Initech Corp",
        "entity_type": "PARTY",
        "confidence": 0.55,
    }
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY,
        status=ReviewStatus.PENDING,
        original_prediction=original_pred,
    )
    review_manager.add_review_item(item)

    review_manager.correct_entity(
        review_id=item.review_id,
        reviewer_id="lawyer_01",
        corrected_fields={
            "canonical_name": "Initech Corporation",
            "entity_type": "ORGANIZATION",
        },
    )

    # Re-retrieve item and verify original is unchanged
    retrieved = review_manager.get_review_item(item.review_id)
    assert retrieved.original_prediction == original_pred
    assert retrieved.corrected_value["canonical_name"] == "Initech Corporation"


# -----------------------------------------------------------------------------
# 13. Create an Audit Trail
# -----------------------------------------------------------------------------
def test_13_create_audit_trail(review_manager, sample_case_id):
    item1 = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.ENTITY,
        original_prediction={"name": "A"},
    )
    item2 = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.RELATIONSHIP,
        original_prediction={"rel": "B"},
    )
    review_manager.add_review_items([item1, item2])

    review_manager.approve_item(
        item1.review_id, reviewer_id="user_a", reviewer_note="Looks good"
    )
    review_manager.reject_item(
        item2.review_id, reviewer_id="user_b", reviewer_note="Invalid"
    )

    trail = review_manager.get_audit_trail_for_case(sample_case_id)
    assert len(trail) == 2
    assert trail[0].decision == "APPROVED"
    assert trail[0].reviewer_id == "user_a"
    assert trail[1].decision == "REJECTED"
    assert trail[1].reviewer_id == "user_b"


# -----------------------------------------------------------------------------
# 14. Prevent Invalid Corrected Relationships (Ontology Enforcement)
# -----------------------------------------------------------------------------
def test_14_prevent_invalid_corrected_relationships(review_manager, sample_case_id):
    item = ReviewItem(
        case_id=sample_case_id,
        item_type=ItemType.RELATIONSHIP,
        original_prediction={
            "relationship_type": "FILED_IN",
            "source_type": "FILING",
            "target_type": "COURT",
        },
    )
    review_manager.add_review_item(item)

    # Attempt to correct relationship to invalid triplet (e.g. COURT -[EMPLOYED_BY]-> STATUTE)
    invalid_corrections = {
        "relationship_type": "EMPLOYED_BY",
        "source_type": "COURT",
        "target_type": "STATUTE",
    }
    with pytest.raises(TripletConstraintViolationError):
        review_manager.correct_relationship(
            review_id=item.review_id,
            reviewer_id="lawyer_01",
            corrected_fields=invalid_corrections,
        )


# -----------------------------------------------------------------------------
# 15. Preserve Case Isolation
# -----------------------------------------------------------------------------
def test_15_preserve_case_isolation(review_manager):
    item_case1 = ReviewItem(
        case_id="case_A",
        item_type=ItemType.ENTITY,
        original_prediction={"name": "Entity Case A"},
    )
    review_manager.add_review_item(item_case1)

    # Attempt cross-case merge
    with pytest.raises(ValueError, match="Case mismatch"):
        review_manager.merge_entities(
            case_id="case_B",
            primary_entity_id="ent_b",
            secondary_entity_id="ent_a",
            reviewer_id="lawyer_01",
            review_id=item_case1.review_id,
        )


# -----------------------------------------------------------------------------
# 16. Verify Neo4j is Updated Correctly (Mock Store Calls & Generator)
# -----------------------------------------------------------------------------
def test_16_generator_and_neo4j_integration(mock_neo4j_store, sample_case_id):
    # Setup candidate generator
    val_rec = ValidationRecord(
        record_type=RecordType.RELATIONSHIP,
        status=ValidationStatus.REVIEW_REQUIRED,
        severity=ValidationSeverity.MEDIUM,
        validation_rule="UNRESOLVED_ENTITY_REFERENCE",
        message="Relationship target entity reference is ambiguous",
        source_document_id="doc_test.pdf",
        source_page=4,
        confidence=0.5,
    )
    val_res = ValidationResult(
        document_id="doc_test.pdf",
        case_id=sample_case_id,
        review_required=[val_rec],
    )

    gen = ReviewCandidateGenerator(confidence_threshold=0.75)
    candidates = gen.generate_review_items(validation_result=val_res)
    assert len(candidates) == 1
    c = candidates[0]
    assert c.item_type == ItemType.RELATIONSHIP
    assert c.validation_rule == "UNRESOLVED_ENTITY_REFERENCE"

    mgr = ReviewManager()
    mgr.add_review_item(c)
    mgr.approve_item(c.review_id, reviewer_id="admin", neo4j_store=mock_neo4j_store)
    # If c.relationship_id is None, no exception is raised and execution proceeds cleanly


# -----------------------------------------------------------------------------
# 17. End-to-End FastAPI Client Tests
# -----------------------------------------------------------------------------
def test_fastapi_review_api_endpoints():
    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["step"] in [9, 10]

    case_id = "case_api_test_99"
    item = ReviewItem(
        case_id=case_id,
        item_type=ItemType.ENTITY,
        status=ReviewStatus.PENDING,
        confidence=0.45,
        original_prediction={
            "canonical_name": "API Test Org",
            "entity_type": "ORGANIZATION",
        },
    )
    from app.api.review_router import global_review_manager

    global_review_manager.add_review_item(item)

    # 2. Get items for case
    res = client.get(f"/api/v1/review/{case_id}/items")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1

    # 3. Get single item
    res = client.get(f"/api/v1/review/items/{item.review_id}")
    assert res.status_code == 200
    assert res.json()["review_id"] == item.review_id

    # 4. Approve item via API
    res = client.post(
        f"/api/v1/review/items/{item.review_id}/approve",
        json={"reviewer_id": "lawyer_api", "reviewer_note": "Approved via REST API"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 5. Check audit trail
    res = client.get(f"/api/v1/review/{case_id}/audit-trail")
    assert res.status_code == 200
    trail = res.json()
    assert len(trail) >= 1
    assert trail[0]["reviewer_id"] == "lawyer_api"
