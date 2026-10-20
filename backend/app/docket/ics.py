"""
iCalendar RFC 5545 generation utility.
Supports stable UIDs, SEQUENCE tracking, CANCELLED status, and redaction.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Union
from icalendar import Calendar, Event as IcsEvent

from app.docket.models import Event


def generate_ics_calendar(
    events: Union[Event, List[Event]],
    redact: bool = False,
    calendar_name: str = "LegalLens Docket",
) -> str:
    """Generates an RFC 5545 compliant .ics calendar string."""
    cal = Calendar()
    cal.add("prodid", "-//LegalLens//Docket Reminder System//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", calendar_name)

    if isinstance(events, Event):
        event_list = [events]
    else:
        event_list = events

    now = datetime.now(timezone.utc)

    for ev in event_list:
        ics_ev = IcsEvent()
        # Stable UID
        ics_ev.add("uid", f"docket-event-{ev.id}@legallens.internal")
        ics_ev.add("sequence", ev.sequence)
        ics_ev.add("dtstamp", now)

        # Starts at
        starts_at = ev.starts_at
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        ics_ev.add("dtstart", starts_at)

        # End at (assume 1 hour default if not specified)
        ics_ev.add("dtend", starts_at + timedelta(hours=1))

        # Status
        if ev.status == "cancelled":
            ics_ev.add("status", "CANCELLED")
        elif ev.status in ("scheduled", "rescheduled"):
            ics_ev.add("status", "CONFIRMED")
        else:
            ics_ev.add("status", "TENTATIVE")

        # Summary / Title
        ics_ev.add("summary", f"[{ev.kind.upper()}] {ev.title}")

        # Description and Location
        description_parts = [
            f"Matter: {ev.matter_id}",
            f"Type: {ev.kind}",
            f"Status: {ev.status}",
        ]

        location = None
        if ev.kind == "hearing":
            if not redact:
                if ev.court_name:
                    location = ev.court_name
                    if ev.courtroom:
                        location += f", Room {ev.courtroom}"
                if ev.judge:
                    description_parts.append(f"Judge: {ev.judge}")
                if ev.mode:
                    description_parts.append(f"Mode: {ev.mode}")
                if ev.virtual_link:
                    description_parts.append(f"Virtual Link: {ev.virtual_link}")
            else:
                location = "Redacted Court Location"
                description_parts.append("Location details redacted.")

        if ev.notes and not redact:
            description_parts.append(f"Notes: {ev.notes}")

        if location:
            ics_ev.add("location", location)

        ics_ev.add("description", "\n".join(description_parts))
        cal.add_component(ics_ev)

    return cal.to_ical().decode("utf-8")
