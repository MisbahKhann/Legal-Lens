"""
Tests for multi-tenant matter isolation, role-based write protection,
cross-matter resource rejection, and user notification scoping.
"""

from datetime import datetime, timedelta, timezone
from app.docket.models import Notification


def test_non_member_access_forbidden(client):
    """Test that users not in matter_members receive 403 Forbidden."""
    # user-other is a member of matter-test-2, but NOT matter-test-1
    res = client.get(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-other"},
    )
    assert res.status_code == 403
    assert "not a member" in res.json()["detail"]


def test_viewer_role_read_only_enforcement(client):
    """
    Test that members with 'viewer' role can read but cannot mutate docket
    resources.
    """
    # 1. Reading events is permitted
    res_get = client.get(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-viewer"},
    )
    assert res_get.status_code == 200

    # 2. Creating an event is forbidden (403)
    future_date = datetime.now(timezone.utc) + timedelta(days=7)
    res_post = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-viewer"},
        json={
            "kind": "hearing",
            "title": "Viewer Attempted Hearing",
            "starts_at": future_date.isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res_post.status_code == 403
    assert "read-only access" in res_post.json()["detail"]


def test_viewer_mutation_endpoints_blocked(client):
    """Test that viewer cannot reschedule, postpone, cancel, or attach documents."""
    # First, attorney creates an event
    future_date = datetime.now(timezone.utc) + timedelta(days=10)
    res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Case Management Conference",
            "starts_at": future_date.isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res.status_code == 201
    ev_id = res.json()["id"]

    # Viewer attempts reschedule -> 403
    res_resched = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/reschedule",
        headers={"X-User-Id": "user-viewer"},
        json={
            "new_starts_at": (future_date + timedelta(days=1)).isoformat(),
            "reason": "Viewer unauthorized attempt",
        },
    )
    assert res_resched.status_code == 403

    # Viewer attempts postpone -> 403
    res_postpone = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/postpone",
        headers={"X-User-Id": "user-viewer"},
        json={"reason": "Unauthorized postpone"},
    )
    assert res_postpone.status_code == 403

    # Viewer attempts cancel -> 403
    res_cancel = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/cancel",
        headers={"X-User-Id": "user-viewer"},
        json={"reason": "Unauthorized cancel"},
    )
    assert res_cancel.status_code == 403

    # Viewer attempts create reminder -> 403
    res_rem = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/reminders",
        headers={"X-User-Id": "user-viewer"},
        json={
            "anchor": "fixed_datetime",
            "fire_at": (future_date - timedelta(days=1)).isoformat(),
        },
    )
    assert res_rem.status_code == 403


def test_cross_matter_resource_linking_rejected(client):
    """
    Test that linking or operating on resources across different matters
    is rejected.
    """
    # 1. Create event in matter 1 by user-attorney
    res1 = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Matter 1 Hearing",
            "starts_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res1.status_code == 201
    assert res1.json()["id"] is not None

    # 2. Create event in matter 2 by user-other
    res2 = client.post(
        "/api/v1/matters/matter-test-2/docket/events",
        headers={"X-User-Id": "user-other"},
        json={
            "kind": "hearing",
            "title": "Matter 2 Hearing",
            "starts_at": (datetime.now(timezone.utc) + timedelta(days=6)).isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res2.status_code == 201
    ev2_id = res2.json()["id"]

    # 3. Attempt to access matter 2's event through matter 1 endpoint -> 404
    res_cross = client.get(
        f"/api/v1/matters/matter-test-1/docket/events/{ev2_id}",
        headers={"X-User-Id": "user-attorney"},
    )
    assert res_cross.status_code == 404

    # 4. Attempt to create a reminder for matter 2's event through matter 1 -> 404
    res_rem_cross = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev2_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "fixed_datetime",
            "fire_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert res_rem_cross.status_code == 404


def test_user_notification_isolation(client, db_session):
    """
    Test that user only receives their own notifications and cannot mark
    other users' notifications as read.
    """
    # First create an event to satisfy foreign key
    future_date = datetime.now(timezone.utc) + timedelta(days=5)
    res_ev = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Hearing for Notifications",
            "starts_at": future_date.isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res_ev.status_code == 201
    ev_id = res_ev.json()["id"]

    # Seed a notification for user-attorney and one for user-owner
    n1 = Notification(
        matter_id="matter-test-1",
        user_id="user-attorney",
        event_id=ev_id,
        title="Attorney Notice",
        message="Notice for attorney only",
        notification_type="reminder_fired",
    )
    n2 = Notification(
        matter_id="matter-test-1",
        user_id="user-owner",
        event_id=ev_id,
        title="Owner Notice",
        message="Notice for owner only",
        notification_type="reminder_fired",
    )
    db_session.add_all([n1, n2])
    db_session.commit()

    # User-attorney checks their notifications
    res = client.get("/api/v1/notifications", headers={"X-User-Id": "user-attorney"})
    assert res.status_code == 200
    data = res.json()
    item_ids = [n["id"] for n in data["items"]]
    assert n1.id in item_ids
    assert n2.id not in item_ids  # Cannot see owner's notification

    # User-attorney attempts to mark user-owner's notification as read -> 404
    res_mark = client.post(
        f"/api/v1/notifications/{n2.id}/read",
        headers={"X-User-Id": "user-attorney"},
    )
    assert res_mark.status_code == 404
