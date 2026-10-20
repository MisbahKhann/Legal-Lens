"""
Tests for event rescheduling, conflict resolution, postpone, and cancel flows.
"""

from datetime import datetime, timedelta, timezone


def test_reschedule_shifts_offset_reminders_and_clears_verification(client):
    """
    On reschedule:
    - offset_before_event reminders shift automatically to the new date.
    - Verified deadlines clear verified_by and verified_at.
    """
    base_date = datetime.now(timezone.utc) + timedelta(days=10)
    create_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "deadline",
            "title": "Discovery Cutoff",
            "starts_at": base_date.isoformat(),
            "priority": "high",
        },
    )
    event_id = create_res.json()["id"]

    # Verify deadline
    client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/verify",
        headers={"X-User-Id": "user-attorney"},
    )

    # Add 3 days before offset reminder
    rem_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "offset_before_event",
            "days_before": 3,
            "time_of_day": "09:00:00",
        },
    )
    assert rem_res.status_code == 201
    rem_id = rem_res.json()["id"]
    old_fire_at = rem_res.json()["fire_at"]

    # Reschedule event to 20 days out
    new_date = datetime.now(timezone.utc) + timedelta(days=20)
    resched_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/reschedule",
        headers={"X-User-Id": "user-attorney"},
        json={
            "new_starts_at": new_date.isoformat(),
            "reason": "Joint stipulation extending discovery",
        },
    )
    assert resched_res.status_code == 200
    res_data = resched_res.json()
    assert res_data["status"] == "completed"
    assert res_data["event"]["status"] == "rescheduled"
    assert res_data["event"]["verified_by"] is None
    assert res_data["event"]["verified_at"] is None
    assert res_data["event"]["sequence"] == 1

    # Check reminder shifted
    detail_res = client.get(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}",
        headers={"X-User-Id": "user-attorney"},
    )
    reminders = detail_res.json()["reminders"]
    rem = next(r for r in reminders if r["id"] == rem_id)
    assert rem["fire_at"] != old_fire_at


def test_reschedule_reports_fixed_datetime_conflicts_and_resolves(client):
    """
    Fixed datetime reminders are NOT silently moved; reported as conflicts.
    Client resolves them with conflict_resolutions.
    """
    event_date = datetime.now(timezone.utc) + timedelta(days=10)
    create_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Status Conference",
            "starts_at": event_date.isoformat(),
            "priority": "medium",
        },
    )
    event_id = create_res.json()["id"]

    # Fixed reminder 5 days out
    fixed_fire = datetime.now(timezone.utc) + timedelta(days=5)
    rem_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "fixed_datetime",
            "fire_at": fixed_fire.isoformat(),
        },
    )
    rem_id = rem_res.json()["id"]

    # Reschedule earlier to 3 days out (fixed reminder is now AFTER event)
    new_date = datetime.now(timezone.utc) + timedelta(days=3)
    attempt1 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/reschedule",
        headers={"X-User-Id": "user-attorney"},
        json={
            "new_starts_at": new_date.isoformat(),
            "reason": "Court moved conference forward",
        },
    )
    assert attempt1.status_code == 200
    data1 = attempt1.json()
    assert data1["status"] == "conflicts_detected"
    assert len(data1["conflicts"]) == 1
    assert data1["conflicts"][0]["reminder_id"] == rem_id

    # Resolve conflict by shifting reminder
    attempt2 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/reschedule",
        headers={"X-User-Id": "user-attorney"},
        json={
            "new_starts_at": new_date.isoformat(),
            "reason": "Court moved conference forward",
            "conflict_resolutions": {
                rem_id: {
                    "action": "shift",
                    "days_before": 1,
                    "time_of_day": "09:00:00",
                }
            },
        },
    )
    assert attempt2.status_code == 200
    data2 = attempt2.json()
    assert data2["status"] == "completed"


def test_postpone_and_cancel_event(client):
    """
    Postponing sets status=postponed.
    Cancelling sets status=cancelled and cancels all active reminders.
    """
    event_date = datetime.now(timezone.utc) + timedelta(days=10)
    create_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Evidentiary Hearing",
            "starts_at": event_date.isoformat(),
            "priority": "high",
        },
    )
    event_id = create_res.json()["id"]

    # Add reminder
    rem_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "offset_before_event",
            "days_before": 2,
        },
    )
    rem_id = rem_res.json()["id"]

    # Postpone
    postpone_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/postpone",
        headers={"X-User-Id": "user-attorney"},
        json={"reason": "Judge unavailable"},
    )
    assert postpone_res.status_code == 200
    assert postpone_res.json()["status"] == "postponed"

    # Cancel
    cancel_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/cancel",
        headers={"X-User-Id": "user-attorney"},
        json={"reason": "Case settled"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Check reminder state is 'cancelled'
    detail = client.get(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}",
        headers={"X-User-Id": "user-attorney"},
    ).json()
    rem = next(r for r in detail["reminders"] if r["id"] == rem_id)
    assert rem["state"] == "cancelled"
