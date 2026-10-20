"""
Tests for Event creation, deadline verification, and past-date warnings.
"""

from datetime import datetime, timedelta, timezone


def test_create_hearing_event(client):
    """Test creating a court hearing event with hearing-specific metadata."""
    future_date = datetime.now(timezone.utc) + timedelta(days=14)
    payload = {
        "kind": "hearing",
        "title": "Preliminary Injunction Hearing",
        "starts_at": future_date.isoformat(),
        "timezone": "America/New_York",
        "priority": "high",
        "notes": "Bring physical exhibits",
        "hearing_type": "Injunction",
        "court_name": "U.S. District Court, SDNY",
        "courtroom": "5A",
        "judge": "Hon. Sarah Vance",
        "case_number": "1:26-cv-00999",
        "mode": "in_person",
        "virtual_link": None,
    }

    res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["kind"] == "hearing"
    assert data["title"] == "Preliminary Injunction Hearing"
    assert data["court_name"] == "U.S. District Court, SDNY"
    assert data["judge"] == "Hon. Sarah Vance"
    assert data["warning"] is None
    assert data["sequence"] == 0


def test_create_deadline_event_and_server_entered_by(client):
    """Test creating a legal deadline with server-assigned entered_by."""
    future_date = datetime.now(timezone.utc) + timedelta(days=30)
    payload = {
        "kind": "deadline",
        "title": "Motion for Summary Judgment Filing Deadline",
        "starts_at": future_date.isoformat(),
        "timezone": "America/New_York",
        "priority": "urgent",
        "notes": "FRCP Rule 56 deadline",
        "deadline_type": "Statutory",
        "source_description": "Court Scheduling Order, ECF No. 42",
        "source_document_id": "doc-kg-order-42",
    }

    res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["kind"] == "deadline"
    assert data["entered_by"] == "user-attorney"
    assert data["verified_by"] is None
    assert data["verified_at"] is None


def test_past_date_warning(client):
    """Creating an event with starts_at in the past returns a warning."""
    past_date = datetime.now(timezone.utc) - timedelta(days=2)
    payload = {
        "kind": "hearing",
        "title": "Past Initial Conference",
        "starts_at": past_date.isoformat(),
        "timezone": "America/New_York",
        "priority": "medium",
    }

    res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["warning"] is not None
    assert "in the past" in data["warning"]


def test_verify_deadline_endpoint(client):
    """Test verifying a deadline stamps verified_by and verified_at."""
    future_date = datetime.now(timezone.utc) + timedelta(days=10)
    create_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "deadline",
            "title": "Expert Witness Disclosure",
            "starts_at": future_date.isoformat(),
            "priority": "high",
        },
    )
    event_id = create_res.json()["id"]

    verify_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/verify",
        headers={"X-User-Id": "user-owner"},
        json={"notes": "Confirmed against local rule 26.2"},
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["verified_by"] == "user-owner"
    assert data["verified_at"] is not None


def test_verify_hearing_rejected_with_400(client):
    """Verifying a hearing event is rejected (only deadlines can be verified)."""
    future_date = datetime.now(timezone.utc) + timedelta(days=5)
    create_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Oral Argument",
            "starts_at": future_date.isoformat(),
            "priority": "high",
        },
    )
    event_id = create_res.json()["id"]

    verify_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/verify",
        headers={"X-User-Id": "user-attorney"},
    )
    assert verify_res.status_code == 400
    assert "Only deadline events can be verified" in verify_res.json()["detail"]
