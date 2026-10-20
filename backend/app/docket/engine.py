"""
Pure deterministic calculation engine for Docket reminders and timing.
Operates without side effects; accepts explicit `now` parameter for unit testing.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from app.docket.models import AttachedDocument, Event, Reminder


@dataclass
class DueReminderAction:
    """Action recommendation resulting from pure reminder evaluation."""

    reminder: Reminder
    action_type: str  # 'fire_normal' | 'fire_late_missed'
    occurrence_time: datetime
    notification_type: str  # 'reminder_fired' | 'reminder_late'
    new_state: str  # 'sent' | 'missed'


def parse_time_of_day(time_str: Optional[str]) -> time:
    """Parses HH:MM or HH:MM:SS string into a datetime.time object."""
    if not time_str:
        return time(9, 0, 0)  # Default morning 9:00 AM

    parts = [int(p) for p in time_str.strip().split(":")]
    if len(parts) == 2:
        return time(parts[0], parts[1], 0)
    elif len(parts) >= 3:
        return time(parts[0], parts[1], parts[2])
    return time(9, 0, 0)


def calculate_offset_fire_time(
    event_starts_at_utc: datetime,
    court_timezone: str,
    days_before: int,
    time_of_day_str: Optional[str] = None,
) -> datetime:
    """
    Computes UTC firing datetime in the court's timezone.
    Guarantees accurate DST transitions by calculating on court local calendar.
    """
    try:
        tz = ZoneInfo(court_timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    # Ensure event starts_at is UTC aware
    if event_starts_at_utc.tzinfo is None:
        event_starts_at_utc = event_starts_at_utc.replace(tzinfo=timezone.utc)

    local_event_dt = event_starts_at_utc.astimezone(tz)
    local_target_date = local_event_dt.date() - timedelta(days=days_before)
    target_time = parse_time_of_day(time_of_day_str)

    # Combine in local court timezone
    local_fire_dt = datetime.combine(local_target_date, target_time, tzinfo=tz)
    # Convert back to UTC for database storage and comparisons
    return local_fire_dt.astimezone(timezone.utc)


def compute_next_occurrence(
    current_fire_at: datetime,
    repeat_rule: str,
    event_starts_at: datetime,
) -> Optional[datetime]:
    """
    Computes next recurrence fire time.
    Daily rules add 24 hours. Returns None if repeat rule is 'none'
    or event has arrived.
    """
    if repeat_rule == "none":
        return None

    next_fire = current_fire_at + timedelta(days=1)
    if repeat_rule == "daily_until_event" and next_fire >= event_starts_at:
        return None

    return next_fire


def compute_due_reminders(
    reminders: List[Reminder],
    event_map: Dict[str, Event],
    doc_map: Dict[str, AttachedDocument],
    now: datetime,
    grace_period_hours: int = 2,
) -> List[DueReminderAction]:
    """
    Pure evaluation of which reminders are due at timestamp `now`.
    Enforces rules:
    - Postponed/cancelled events pause/stop reminders.
    - Document reminders stop if document is reviewed; resume if changed_since_review.
    - Reminders whose time has passed are never auto-marked done.
    - Overdue beyond grace period fires a late notification and marks missed.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    due_actions: List[DueReminderAction] = []

    for rem in reminders:
        # Ignore already completed, acknowledged, done, or cancelled reminders
        if rem.state in ("done", "cancelled", "acknowledged"):
            continue

        event = event_map.get(rem.event_id)
        if not event:
            continue

        # Postponed events pause reminders; cancelled/completed events stop them
        if event.status in ("postponed", "cancelled", "completed"):
            continue

        # Check attached document review status if scoped to a document
        if rem.document_id:
            doc = doc_map.get(rem.document_id)
            if doc and doc.review_status == "reviewed":
                # Reviewed documents do NOT fire reminders
                continue

        # Determine target firing time
        target_time = rem.snoozed_until if rem.state == "snoozed" else rem.fire_at
        if not target_time:
            continue

        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        # Evaluate if due
        if target_time <= now:
            delay = now - target_time
            if delay > timedelta(hours=grace_period_hours):
                # Beyond grace period: late firing and state becomes missed
                due_actions.append(
                    DueReminderAction(
                        reminder=rem,
                        action_type="fire_late_missed",
                        occurrence_time=target_time,
                        notification_type="reminder_late",
                        new_state="missed",
                    )
                )
            else:
                # Normal firing
                due_actions.append(
                    DueReminderAction(
                        reminder=rem,
                        action_type="fire_normal",
                        occurrence_time=target_time,
                        notification_type="reminder_fired",
                        new_state="sent",
                    )
                )

    return due_actions
