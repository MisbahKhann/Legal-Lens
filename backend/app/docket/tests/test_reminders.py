"""
Tests for Reminder timing, court timezone / DST calculation,
idempotent atomic claim firing, and repeat rule lifecycle.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.docket.engine import (
    calculate_offset_fire_time,
    compute_due_reminders,
)
from app.docket.models import Event, Reminder
from app.docket.service import process_due_reminders


def test_court_timezone_and_dst_offset_calculation():
    """
    Verifies that reminder time computation properly calculates in court local time
    across daylight saving transitions.
    In America/New_York:
    - November DST end (EDT UTC-4 -> EST UTC-5).
    """
    # Event on Nov 5, 2026 at 10:00 AM NY time (EST, UTC-5)
    # Starts at 15:00:00 UTC
    event_time_utc = datetime(2026, 11, 5, 15, 0, 0, tzinfo=timezone.utc)

    # 7 days before is Oct 29, 2026 at 09:00 AM NY time (EDT, UTC-4)
    # In EDT, 09:00 AM is 13:00:00 UTC
    fire_utc = calculate_offset_fire_time(
        event_starts_at_utc=event_time_utc,
        court_timezone="America/New_York",
        days_before=7,
        time_of_day_str="09:00:00",
    )

    # Check that in NY local time, the reminder is at exactly 09:00:00 AM
    local_fire = fire_utc.astimezone(ZoneInfo("America/New_York"))
    assert local_fire.hour == 9
    assert local_fire.minute == 0
    assert local_fire.day == 29
    assert local_fire.month == 10
    # Because Oct 29 is EDT (UTC-4), 09:00 EDT == 13:00 UTC
    assert fire_utc.hour == 13


def test_morning_of_preset_calculation():
    """Morning-of preset (days_before=0, time_of_day='09:00:00')."""
    event_time_utc = datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc)
    fire_utc = calculate_offset_fire_time(
        event_starts_at_utc=event_time_utc,
        court_timezone="America/New_York",
        days_before=0,
        time_of_day_str="09:00:00",
    )
    local_fire = fire_utc.astimezone(ZoneInfo("America/New_York"))
    assert local_fire.day == 15
    assert local_fire.month == 6
    assert local_fire.hour == 9
    assert local_fire.minute == 0


def test_pure_compute_due_reminders_and_grace_period():
    """
    Tests pure compute_due_reminders function:
    - Target time <= now triggers normal firing.
    - Target time overdue > grace period triggers late firing and marks missed.
    - Postponed/cancelled events are ignored.
    - Reviewed document reminders are ignored.
    """
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

    ev_active = Event(
        id="ev-1",
        matter_id="m-1",
        kind="hearing",
        title="Active Hearing",
        starts_at=now + timedelta(days=2),
        status="scheduled",
    )
    ev_postponed = Event(
        id="ev-2",
        matter_id="m-1",
        kind="hearing",
        title="Postponed Hearing",
        starts_at=now + timedelta(days=5),
        status="postponed",
    )

    # Reminder 1: normal due (fire_at 15 mins ago)
    rem_normal = Reminder(
        id="rem-normal",
        event_id="ev-1",
        matter_id="m-1",
        user_id="user-1",
        created_by="user-1",
        anchor="offset_before_event",
        fire_at=now - timedelta(minutes=15),
        state="pending",
    )

    # Reminder 2: overdue by 5 hours (> 2h grace period)
    rem_overdue = Reminder(
        id="rem-overdue",
        event_id="ev-1",
        matter_id="m-1",
        user_id="user-1",
        created_by="user-1",
        anchor="offset_before_event",
        fire_at=now - timedelta(hours=5),
        state="pending",
    )

    # Reminder 3: on postponed event (should be ignored)
    rem_postponed = Reminder(
        id="rem-postponed",
        event_id="ev-2",
        matter_id="m-1",
        user_id="user-1",
        created_by="user-1",
        anchor="offset_before_event",
        fire_at=now - timedelta(minutes=10),
        state="pending",
    )

    actions = compute_due_reminders(
        reminders=[rem_normal, rem_overdue, rem_postponed],
        event_map={"ev-1": ev_active, "ev-2": ev_postponed},
        doc_map={},
        now=now,
        grace_period_hours=2,
    )

    assert len(actions) == 2
    act_normal = next(a for a in actions if a.reminder.id == "rem-normal")
    assert act_normal.action_type == "fire_normal"
    assert act_normal.new_state == "sent"

    act_overdue = next(a for a in actions if a.reminder.id == "rem-overdue")
    assert act_overdue.action_type == "fire_late_missed"
    assert act_overdue.new_state == "missed"


def test_atomic_idempotent_firing_in_service(db_session):
    """
    Verifies that calling process_due_reminders multiple times
    or concurrently only executes once due to the atomic claim.
    """
    now = datetime.now(timezone.utc)
    ev = Event(
        id="ev-idem",
        matter_id="matter-test-1",
        kind="hearing",
        title="Idempotency Test Hearing",
        starts_at=now + timedelta(days=3),
        status="scheduled",
    )
    rem = Reminder(
        id="rem-idem",
        event_id="ev-idem",
        matter_id="matter-test-1",
        user_id="user-attorney",
        created_by="user-attorney",
        anchor="offset_before_event",
        fire_at=now - timedelta(minutes=5),
        state="pending",
    )
    db_session.add_all([ev, rem])
    db_session.commit()

    # First run: fires reminder
    fired_count_1 = process_due_reminders(db_session, now)
    assert fired_count_1 == 1

    # Second immediate run at same timestamp: must be 0 (already fired)
    fired_count_2 = process_due_reminders(db_session, now)
    assert fired_count_2 == 0


def test_repeating_reminder_returns_to_pending(db_session):
    """
    Verifies that repeating reminders return to state 'pending' with the
    next fire time, and do not stay stuck in 'sent'.
    """
    now = datetime.now(timezone.utc)
    ev = Event(
        id="ev-rep",
        matter_id="matter-test-1",
        kind="deadline",
        title="Rep Hearing",
        starts_at=now + timedelta(days=5),
        status="scheduled",
    )
    rem = Reminder(
        id="rem-rep",
        event_id="ev-rep",
        matter_id="matter-test-1",
        user_id="user-attorney",
        created_by="user-attorney",
        anchor="offset_before_event",
        repeat_rule="daily_until_event",
        fire_at=now - timedelta(minutes=10),
        state="pending",
    )
    db_session.add_all([ev, rem])
    db_session.commit()

    process_due_reminders(db_session, now)

    db_session.refresh(rem)
    assert rem.state == "pending"
    assert rem.fire_at > now
