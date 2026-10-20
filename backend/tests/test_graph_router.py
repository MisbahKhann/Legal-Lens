"""
Unit tests for LegalLens Knowledge Graph Router (Step 8+ UI Backend).
Tests case listing, complete graph retrieval, entity CRUD with ontology validation,
relationship CRUD with triplet validation, self-loop prevention, user notes persistence,
graph preferences persistence, and neighborhood expansion.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.review_router import get_neo4j_store
from app.storage.neo4j_store import Neo4jGraphStore


@pytest.fixture
def client():
    """Provides a TestClient with a mock Neo4j store."""
    mock_store = MagicMock(spec=Neo4jGraphStore)
    mock_store.verify_connection.return_value = (
        False  # Test offline cache resilience first
    )

    app.dependency_overrides[get_neo4j_store] = lambda: mock_store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_cases(client):
    """Test GET /api/v1/graph/cases returns case summaries."""
    response = client.get("/api/v1/graph/cases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_empty_or_new_case_graph(client):
    """Test GET /api/v1/graph/{case_id} returns valid structured graph for new case."""
    case_id = "test_unit_case_001"
    response = client.get(f"/api/v1/graph/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert "entities" in data
    assert "relationships" in data
    assert "timeline_events" in data
    assert "summary" in data


def test_entity_creation_valid(client):
    """Test POST /api/v1/graph/{case_id}/entities with valid EntityType."""
    case_id = "test_unit_case_001"
    payload = {
        "canonical_name": "Justice Ruth Bader",
        "entity_type": "JUDGE",
        "aliases": ["RBG", "Justice Ginsburg"],
        "source_text": "Presided over the landmark oral argument.",
    }
    response = client.post(f"/api/v1/graph/{case_id}/entities", json=payload)
    assert response.status_code == 200
    ent = response.json()
    assert ent["canonical_name"] == "Justice Ruth Bader"
    assert ent["entity_type"] == "JUDGE"
    assert ent["case_id"] == case_id
    assert "id" in ent
    assert "RBG" in ent["aliases"]


def test_entity_creation_invalid_type(client):
    """Test POST /api/v1/graph/{case_id}/entities fails on invalid entity type."""
    case_id = "test_unit_case_001"
    payload = {
        "canonical_name": "Invalid Entity",
        "entity_type": "TOTALLY_FAKE_TYPE",
    }
    response = client.post(f"/api/v1/graph/{case_id}/entities", json=payload)
    assert response.status_code == 400
    err = response.json()
    assert "Invalid entity type" in err["detail"]


def test_entity_update(client):
    """Test PUT /api/v1/graph/{case_id}/entities/{entity_id} updates entity name."""
    case_id = "test_unit_case_001"
    create_res = client.post(
        f"/api/v1/graph/{case_id}/entities",
        json={"canonical_name": "Initial Name", "entity_type": "PERSON"},
    )
    ent_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/v1/graph/{case_id}/entities/{ent_id}",
        json={"canonical_name": "Updated Name", "aliases": ["Alias 1"]},
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["status"] == "UPDATED"
    assert data["updates"]["canonical_name"] == "Updated Name"


def test_relationship_creation_and_triplet_validation(client):
    """Test relationship creation between source and target entities with triplet validation."""
    case_id = "test_unit_case_rel_001"
    # Create lawyer
    lawyer_res = client.post(
        f"/api/v1/graph/{case_id}/entities",
        json={"canonical_name": "Alice Counsel", "entity_type": "LAWYER"},
    )
    lawyer_id = lawyer_res.json()["id"]

    # Create company
    company_res = client.post(
        f"/api/v1/graph/{case_id}/entities",
        json={"canonical_name": "Acme Industries", "entity_type": "COMPANY"},
    )
    company_id = company_res.json()["id"]

    # Valid triplet: (LAWYER) -[REPRESENTS]-> (COMPANY)
    valid_rel = {
        "source_id": lawyer_id,
        "target_id": company_id,
        "relationship_type": "REPRESENTS",
        "source_text": "Retained as defense counsel on record.",
    }
    rel_res = client.post(f"/api/v1/graph/{case_id}/relationships", json=valid_rel)
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    assert rel_data["relationship_type"] == "REPRESENTS"
    assert rel_data["source_id"] == lawyer_id
    assert rel_data["target_id"] == company_id

    # Self-link rejection
    self_rel = {
        "source_id": lawyer_id,
        "target_id": lawyer_id,
        "relationship_type": "REPRESENTS",
    }
    self_res = client.post(f"/api/v1/graph/{case_id}/relationships", json=self_rel)
    assert self_res.status_code == 400
    assert "self-linking" in self_res.json()["detail"].lower()

    # Invalid triplet: (COMPANY) -[REPRESENTS]-> (LAWYER) is invalid for REPRESENTS
    invalid_rel = {
        "source_id": company_id,
        "target_id": lawyer_id,
        "relationship_type": "REPRESENTS",
    }
    inv_res = client.post(f"/api/v1/graph/{case_id}/relationships", json=invalid_rel)
    assert inv_res.status_code == 400
    assert "Invalid relationship triplet" in inv_res.json()["detail"]


def test_notes_persistence(client):
    """Test saving and retrieving user notes for an entity."""
    case_id = "test_unit_case_notes"
    ent_res = client.post(
        f"/api/v1/graph/{case_id}/entities",
        json={"canonical_name": "Key Witness", "entity_type": "WITNESS"},
    )
    ent_id = ent_res.json()["id"]

    # Save note
    save_res = client.put(
        f"/api/v1/graph/{case_id}/entities/{ent_id}/notes",
        json={"notes": "Credible testimony regarding transaction timing on Exhibit 4."},
    )
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "SAVED"

    # Get note
    get_res = client.get(f"/api/v1/graph/{case_id}/entities/{ent_id}/notes")
    assert get_res.status_code == 200
    assert "Exhibit 4" in get_res.json()["notes"]


def test_preferences_persistence(client):
    """Test saving and retrieving graph view preferences."""
    case_id = "test_unit_case_prefs"
    payload = {
        "custom_colors": {"ent_1": "#6B1F28", "ent_2": "#C9A24B"},
        "preferred_layout": "breadthfirst",
    }
    save_res = client.put(f"/api/v1/graph/{case_id}/preferences", json=payload)
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "SAVED"

    get_res = client.get(f"/api/v1/graph/{case_id}/preferences")
    assert get_res.status_code == 200
    prefs = get_res.json()
    assert prefs["preferred_layout"] == "breadthfirst"
    assert prefs["custom_colors"]["ent_1"] == "#6B1F28"


def test_entity_deletion_with_edge_detachment(client):
    """Test DELETE entity detaches relationships and removes node."""
    case_id = "test_unit_case_del"
    e1 = client.post(
        f"/api/v1/graph/{case_id}/entities",
        json={"canonical_name": "E1", "entity_type": "PERSON"},
    ).json()["id"]
    e2 = client.post(
        f"/api/v1/graph/{case_id}/entities",
        json={"canonical_name": "E2", "entity_type": "ORGANIZATION"},
    ).json()["id"]
    rel = client.post(
        f"/api/v1/graph/{case_id}/relationships",
        json={"source_id": e1, "target_id": e2, "relationship_type": "WORKS_FOR"},
    ).json()

    del_res = client.delete(f"/api/v1/graph/{case_id}/entities/{e1}")
    assert del_res.status_code == 200
    data = del_res.json()
    assert data["status"] == "DELETED"
    assert data["relationships_detached"] >= 1

    # Verify graph no longer contains e1
    g = client.get(f"/api/v1/graph/{case_id}").json()
    assert not any(ent["id"] == e1 for ent in g["entities"])
    assert not any(r["id"] == rel["id"] for r in g["relationships"])
