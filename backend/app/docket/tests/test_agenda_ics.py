"""
Tests for Daily Agenda stream and RFC 5545 .ics Export.
Verifies chronological ordering, due/missed reminders separation, stable UID,
sequence increments, cancelled status, and redaction.
"""

from datetime import datetime, timedelta, timezone
from icalendar import Calendar


def test_agenda_chronological_ordering(client):
    """
    Test that agenda returns events and reminders sorted chronologically
    within range.
    """
    now = datetime.now(timezone.utc)
    day1 = now + timedelta(days=1)
    day2 = now + timedelta(days=2)
    day3 = now + timedelta(days=3)

    # Create event on Day 2
    res_ev2 = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Day 2 Status Conference",
            "starts_at": day2.isoformat(),
            "timezone": "America/New_York",
            "court_name": "SDNY Room 301",
        },
    )
    assert res_ev2.status_code == 201
    ev2_id = res_ev2.json()["id"]

    # Create event on Day 3
    res_ev3 = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "deadline",
            "title": "Day 3 Filing Deadline",
            "starts_at": day3.isoformat(),
            "timezone": "America/New_York",
            "deadline_type": "Filing",
        },
    )
    assert res_ev3.status_code == 201

    # Create fixed reminder on Day 1 for ev2
    res_rem1 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev2_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "fixed_datetime",
            "fire_at": day1.isoformat(),
            "repeat_rule": "none",
        },
    )
    assert res_rem1.status_code == 201

    # Request agenda for Day 0 to Day 4
    from_date = (now - timedelta(hours=1)).isoformat()
    to_date = (now + timedelta(days=4)).isoformat()
    res_agenda = client.get(
        "/api/v1/matters/matter-test-1/docket/agenda",
        headers={"X-User-Id": "user-attorney"},
        params={"from": from_date, "to": to_date},
    )
    assert res_agenda.status_code == 200
    data = res_agenda.json()

    assert len(data["items"]) >= 3
    # Check timestamps are in ascending chronological order
    timestamps = [item["timestamp"] for item in data["items"]]
    assert timestamps == sorted(timestamps)

    # Verify kinds in items
    kinds = [item["item_type"] for item in data["items"]]
    assert "reminder" in kinds
    assert "event" in kinds


def test_agenda_due_and_missed_reminders_separation(client, db_session):
    """Test that agenda separates pending reminders from missed reminders."""
    now = datetime.now(timezone.utc)
    ev_time = now + timedelta(days=5)

    res_ev = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Motion Hearing",
            "starts_at": ev_time.isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res_ev.status_code == 201
    ev_id = res_ev.json()["id"]

    # Create pending reminder
    res_p = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "fixed_datetime",
            "fire_at": (now + timedelta(days=1)).isoformat(),
        },
    )
    assert res_p.status_code == 201

    # Create reminder and manually set state to 'missed'
    from app.docket.models import Reminder

    missed_rem = Reminder(
        matter_id="matter-test-1",
        event_id=ev_id,
        user_id="user-attorney",
        anchor="fixed_datetime",
        fire_at=now - timedelta(hours=2),
        state="missed",
        created_by="user-attorney",
    )
    db_session.add(missed_rem)
    db_session.commit()

    from_date = (now - timedelta(days=1)).isoformat()
    to_date = (now + timedelta(days=3)).isoformat()
    res_agenda = client.get(
        "/api/v1/matters/matter-test-1/docket/agenda",
        headers={"X-User-Id": "user-attorney"},
        params={"from": from_date, "to": to_date},
    )
    assert res_agenda.status_code == 200
    data = res_agenda.json()

    assert any(r["id"] == missed_rem.id for r in data["missed_reminders"])
    assert any(r["state"] == "pending" for r in data["due_reminders"])


def test_event_ics_export_and_redaction(client):
    """Test RFC 5545 .ics generation with stable UID, sequence, and redaction option."""
    starts_at = datetime.now(timezone.utc) + timedelta(days=7)
    res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Emergency TRO Hearing",
            "starts_at": starts_at.isoformat(),
            "timezone": "America/New_York",
            "court_name": "U.S. District Court, EDNY",
            "courtroom": "4B",
            "judge": "Hon. Raymond Dearie",
            "notes": "Highly confidential settlement discussion",
        },
    )
    assert res.status_code == 201
    ev_id = res.json()["id"]

    # 1. Unredacted .ics export
    res_ics = client.get(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/export.ics",
        headers={"X-User-Id": "user-attorney"},
    )
    assert res_ics.status_code == 200
    assert res_ics.headers["content-type"].startswith("text/calendar")
    ics_text = res_ics.text

    # Parse with icalendar
    cal = Calendar.from_ical(ics_text)
    event_comp = [c for c in cal.walk() if c.name == "VEVENT"][0]

    assert str(event_comp.get("uid")) == f"docket-event-{ev_id}@legallens.internal"
    assert int(event_comp.get("sequence")) == 0
    assert str(event_comp.get("status")) == "CONFIRMED"
    assert "Hon. Raymond Dearie" in str(event_comp.get("description"))
    assert "Highly confidential" in str(event_comp.get("description"))
    assert "EDNY" in str(event_comp.get("location"))

    # 2. Reschedule to increment sequence
    new_date = starts_at + timedelta(days=3)
    res_resched = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/reschedule",
        headers={"X-User-Id": "user-attorney"},
        json={
            "new_starts_at": new_date.isoformat(),
            "reason": "Judge unavailable on original date",
        },
    )
    assert res_resched.status_code == 200

    # 3. Redacted .ics export
    res_redacted = client.get(
        f"/api/v1/matters/matter-test-1/docket/events/{ev_id}/export.ics?redact=true",
        headers={"X-User-Id": "user-attorney"},
    )
    assert res_redacted.status_code == 200
    redacted_cal = Calendar.from_ical(res_redacted.text)
    redacted_event = [c for c in redacted_cal.walk() if c.name == "VEVENT"][0]

    assert int(redacted_event.get("sequence")) == 1  # Sequence incremented
    assert "Hon. Raymond Dearie" not in str(redacted_event.get("description"))
    assert "Highly confidential" not in str(redacted_event.get("description"))
    assert "Redacted Court Location" in str(redacted_event.get("location"))


def test_matter_wide_ics_export_with_cancelled_status(client):
    """
    Test exporting all upcoming events for a matter, verifying CANCELLED status
    on cancelled events.
    """
    now = datetime.now(timezone.utc)
    # Event 1: scheduled
    res1 = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Active Hearing",
            "starts_at": (now + timedelta(days=10)).isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res1.status_code == 201

    # Event 2: cancelled
    res2 = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Cancelled Pretrial Conference",
            "starts_at": (now + timedelta(days=12)).isoformat(),
            "timezone": "America/New_York",
        },
    )
    assert res2.status_code == 201
    ev2_id = res2.json()["id"]

    res_cancel = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{ev2_id}/cancel",
        headers={"X-User-Id": "user-attorney"},
        json={"reason": "Case settled in mediation"},
    )
    assert res_cancel.status_code == 200

    # Export matter .ics
    res_all_ics = client.get(
        "/api/v1/matters/matter-test-1/docket/export.ics",
        headers={"X-User-Id": "user-attorney"},
    )
    assert res_all_ics.status_code == 200
    cal = Calendar.from_ical(res_all_ics.text)
    events = [c for c in cal.walk() if c.name == "VEVENT"]
    assert len(events) >= 2

    statuses = {str(e.get("uid")): str(e.get("status")) for e in events}
    assert statuses[f"docket-event-{ev2_id}@legallens.internal"] == "CANCELLED"
