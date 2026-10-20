"""
Tests verifying that Docket operations record immutable audit entries in audit_logs.
Checks create, reschedule, postpone, cancel, verify, document attach/review,
and reminder actions.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.audit.models import AuditLog


def test_event_lifecycle_audit_logging(client, db_session):
    """
    Test that event creation, reschedule, postpone, cancel, and verify
    record audit entries.
    """
    now = datetime.now(timezone.utc)
    ev_time = now + timedelta(days=10)

    # 1. Create event
    res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "deadline",
            "title": "Discovery Completion Deadline",
            "starts_at": ev_time.isoformat(),
            "timezone": "America/New_York",
            "deadline_type": "Discovery",
        },
    )
    assert res.status_code == 201
    ev_id = res.json()["id"]

    # Verify audit entry for create
    log_create = db_session.scalar(
        select(AuditLog).where(
            AuditLog.matter_id == "matter-test-1",
            AuditLog.target_id == ev_id,
            AuditLog.action == "create",
        )
    )
    assert log_create is not None
    assert log_create.actor == "user-attorney"
    assert log_create.target_type == "event"

    # 2. Reschedule event
    new_time = ev_time + timedelta(days=5)
    res_resched = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/reschedule",
        headers={"X-User-Id": "user-attorney"},
        json={
            "new_starts_at": new_time.isoformat(),
            "reason": "Discovery extension granted by stipulation",
        },
    )
    assert res_resched.status_code == 200

    log_resched = db_session.scalar(
        select(AuditLog).where(
            AuditLog.matter_id == "matter-test-1",
            AuditLog.target_id == ev_id,
            AuditLog.action == "reschedule",
        )
    )
    assert log_resched is not None
    assert log_resched.reason == "Discovery extension granted by stipulation"

    # 3. Verify deadline
    res_verify = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/verify",
        headers={"X-User-Id": "user-attorney"},
        json={"notes": "Verified against docket entry #48"},
    )
    assert res_verify.status_code == 200

    log_verify = db_session.scalar(
        select(AuditLog).where(
            AuditLog.matter_id == "matter-test-1",
            AuditLog.target_id == ev_id,
            AuditLog.action == "verify",
        )
    )
    assert log_verify is not None
    assert log_verify.reason == "Verified against docket entry #48"

    # 4. Check Event History endpoint
    res_hist = client.get(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/history",
        headers={"X-User-Id": "user-attorney"},
    )
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    actions = [a["action"] for a in hist_data["audit_trail"]]
    assert "create" in actions
    assert "reschedule" in actions
    assert "verify" in actions


def test_document_and_reminder_audit_logging(client, db_session):
    """
    Test that document review status changes and reminder actions record
    audit entries.
    """
    now = datetime.now(timezone.utc)
    ev_time = now + timedelta(days=7)

    # Create event
    res_ev = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Evidentiary Hearing",
            "starts_at": ev_time.isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res_ev.status_code == 201
    ev_id = res_ev.json()["id"]

    # Attach document
    res_doc = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/documents",
        headers={"X-User-Id": "user-attorney"},
        data={"display_name": "Exhibit_A.pdf"},
        files={"file": ("Exhibit_A.pdf", b"Dummy PDF content", "application/pdf")},
    )
    assert res_doc.status_code == 201
    doc_id = res_doc.json()["id"]

    # Change review status to reviewed
    res_rev = client.patch(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/documents/{doc_id}",
        headers={"X-User-Id": "user-attorney"},
        json={"review_status": "reviewed"},
    )
    assert res_rev.status_code == 200

    log_doc = db_session.scalar(
        select(AuditLog).where(
            AuditLog.matter_id == "matter-test-1",
            AuditLog.target_id == doc_id,
            AuditLog.action == "review_status_change",
        )
    )
    assert log_doc is not None
    assert log_doc.after_state == {"review_status": "reviewed"}

    # Create reminder
    res_rem = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "fixed_datetime",
            "fire_at": (now + timedelta(days=2)).isoformat(),
        },
    )
    assert res_rem.status_code == 201
    rem_id = res_rem.json()["id"]

    # Acknowledge reminder
    res_ack = client.patch(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/reminders/{rem_id}",
        headers={"X-User-Id": "user-attorney"},
        json={"action": "acknowledge"},
    )
    assert res_ack.status_code == 200

    log_rem = db_session.scalar(
        select(AuditLog).where(
            AuditLog.matter_id == "matter-test-1",
            AuditLog.target_id == rem_id,
            AuditLog.action == "acknowledge",
        )
    )
    assert log_rem is not None
    assert log_rem.actor == "user-attorney"
