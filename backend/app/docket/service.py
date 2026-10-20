"""
Comprehensive service layer for Docket module.
Handles events, reschedule conflict resolution, document versioning,
reminders, agenda, and atomic reminder occurrence firing.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.core.config import settings
from app.docket.channels import InAppNotificationChannel
from app.docket.engine import (
    calculate_offset_fire_time,
    compute_due_reminders,
    compute_next_occurrence,
)
from app.docket.models import (
    AttachedDocument,
    DocumentVersion,
    Event,
    EventChange,
    Reminder,
    ReminderOccurrence,
)
from app.docket.schemas import (
    ConflictDecision,
    EventCreate,
    EventUpdate,
    ReminderActionRequest,
    ReminderConflict,
    ReminderCreate,
    RescheduleRequest,
)

# ==========================================
# Event Operations
# ==========================================


def create_event(
    db: Session,
    matter_id: str,
    data: EventCreate,
    creator_id: str,
) -> Tuple[Event, Optional[str]]:
    """Create a new docket event. Validates dates and checks for past date warning."""
    now = datetime.now(timezone.utc)
    warning = None
    if data.starts_at < now:
        warning = (
            "Event start date is in the past. Reminders can only be scheduled "
            "for future occurrences."
        )

    event_id = str(uuid.uuid4())
    event = Event(
        id=event_id,
        matter_id=matter_id,
        kind=data.kind,
        title=data.title,
        starts_at=data.starts_at,
        timezone=data.timezone,
        status="scheduled",
        priority=data.priority,
        notes=data.notes,
        # Hearing fields
        hearing_type=data.hearing_type,
        court_name=data.court_name,
        courtroom=data.courtroom,
        judge=data.judge,
        case_number=data.case_number,
        mode=data.mode,
        virtual_link=data.virtual_link,
        # Deadline fields
        deadline_type=data.deadline_type,
        source_description=data.source_description,
        source_document_id=data.source_document_id,
        entered_by=creator_id,
        verified_by=None,
        verified_at=None,
        adjustment_reason=data.adjustment_reason,
        sequence=0,
    )
    db.add(event)

    record_event(
        db=db,
        matter_id=matter_id,
        actor=creator_id,
        action="create",
        target_type="event",
        target_id=event_id,
        after={
            "title": data.title,
            "kind": data.kind,
            "starts_at": data.starts_at.isoformat(),
        },
    )
    db.commit()
    db.refresh(event)
    return event, warning


def get_event(
    db: Session,
    matter_id: str,
    event_id: str,
) -> Optional[Event]:
    """Retrieve event scoped to a specific matter."""
    return db.scalar(
        select(Event).where(Event.id == event_id, Event.matter_id == matter_id)
    )


def list_events(
    db: Session,
    matter_id: str,
    limit: int = 50,
    offset: int = 0,
    kind: Optional[str] = None,
    status_filter: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> Tuple[List[Event], int]:
    """Retrieve paginated events scoped to a matter with optional filters."""
    query = select(Event).where(Event.matter_id == matter_id)
    count_query = select(func.count(Event.id)).where(Event.matter_id == matter_id)

    if kind:
        query = query.where(Event.kind == kind)
        count_query = count_query.where(Event.kind == kind)
    if status_filter:
        query = query.where(Event.status == status_filter)
        count_query = count_query.where(Event.status == status_filter)
    if from_date:
        query = query.where(Event.starts_at >= from_date)
        count_query = count_query.where(Event.starts_at >= from_date)
    if to_date:
        query = query.where(Event.starts_at <= to_date)
        count_query = count_query.where(Event.starts_at <= to_date)

    query = query.order_by(Event.starts_at.asc()).offset(offset).limit(limit)

    total = db.scalar(count_query) or 0
    items = list(db.scalars(query).all())
    return items, total


def update_event(
    db: Session,
    matter_id: str,
    event_id: str,
    data: EventUpdate,
    actor_id: str,
) -> Event:
    """Update event non-date metadata. Date updates must use reschedule_event."""
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )

    before = {"title": event.title, "priority": event.priority}
    update_data = data.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(event, field, val)

    event.updated_at = datetime.now(timezone.utc)
    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="update",
        target_type="event",
        target_id=event.id,
        before=before,
        after=update_data,
    )
    db.commit()
    db.refresh(event)
    return event


def delete_event(
    db: Session,
    matter_id: str,
    event_id: str,
    actor_id: str,
) -> None:
    """Delete an event and its cascading associations."""
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )

    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="delete",
        target_type="event",
        target_id=event.id,
        before={"title": event.title, "kind": event.kind},
    )
    db.delete(event)
    db.commit()


# ==========================================
# Reschedule, Postpone, Cancel & Verify
# ==========================================


def reschedule_event(
    db: Session,
    matter_id: str,
    event_id: str,
    data: RescheduleRequest,
    actor_id: str,
) -> Tuple[Event, str, List[ReminderConflict]]:
    """
    Reschedules an event.
    - Shifts offset reminders automatically; re-arms already-sent offset reminders.
    - Flags fixed datetime reminders as conflicts unless explicit decision provided.
    - Clears verified_by/verified_at for deadlines.
    - Increments sequence for iCalendar tracking.
    """
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )

    now = datetime.now(timezone.utc)
    new_starts_at = data.new_starts_at
    if new_starts_at.tzinfo is None:
        new_starts_at = new_starts_at.replace(tzinfo=timezone.utc)

    court_tz = data.new_timezone or event.timezone
    resolutions = data.conflict_resolutions or {}

    # Inspect all non-cancelled, non-done reminders
    active_reminders = list(
        db.scalars(
            select(Reminder).where(
                Reminder.event_id == event.id,
                Reminder.state.notin_(["cancelled", "done"]),
            )
        ).all()
    )

    conflicts: List[ReminderConflict] = []

    for rem in active_reminders:
        if rem.anchor == "offset_before_event":
            # Compute new firing time
            days_before = rem.days_before if rem.days_before is not None else 1
            projected_fire = calculate_offset_fire_time(
                event_starts_at_utc=new_starts_at,
                court_timezone=court_tz,
                days_before=days_before,
                time_of_day_str=rem.time_of_day,
            )
            if projected_fire < now:
                conflicts.append(
                    ReminderConflict(
                        reminder_id=rem.id,
                        anchor=rem.anchor,
                        current_fire_at=rem.fire_at,
                        projected_fire_at=projected_fire,
                        issue="PROJECTED_FIRE_IN_PAST",
                        suggested_action="cancel",
                    )
                )
        elif rem.anchor == "fixed_datetime":
            # Fixed reminders must not silently move
            if rem.id not in resolutions:
                issue = (
                    "SCHEDULED_AFTER_EVENT"
                    if rem.fire_at and rem.fire_at > new_starts_at
                    else "FIXED_DATE_CONFIRMATION_REQUIRED"
                )
                conflicts.append(
                    ReminderConflict(
                        reminder_id=rem.id,
                        anchor=rem.anchor,
                        current_fire_at=rem.fire_at,
                        projected_fire_at=rem.fire_at,
                        issue=issue,
                        suggested_action="keep",
                    )
                )

    # If unresolved conflicts exist, do not apply changes yet
    unresolved = [c for c in conflicts if c.reminder_id not in resolutions]
    if unresolved:
        return event, "conflicts_detected", conflicts

    # Apply reschedule
    old_starts_at = event.starts_at
    old_status = event.status

    event.starts_at = new_starts_at
    event.timezone = court_tz
    event.status = "rescheduled"
    event.adjustment_reason = data.reason
    event.sequence += 1

    # Date change clears deadline verification
    if event.kind == "deadline":
        event.verified_by = None
        event.verified_at = None

    # Record EventChange
    change = EventChange(
        id=str(uuid.uuid4()),
        event_id=event.id,
        matter_id=matter_id,
        change_type="reschedule",
        old_starts_at=old_starts_at,
        new_starts_at=new_starts_at,
        old_status=old_status,
        new_status="rescheduled",
        reason=data.reason,
        actor=actor_id,
        created_at=now,
    )
    db.add(change)

    # Record Audit log
    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="reschedule",
        target_type="event",
        target_id=event.id,
        before={"starts_at": old_starts_at.isoformat(), "status": old_status},
        after={"starts_at": new_starts_at.isoformat(), "status": "rescheduled"},
        reason=data.reason,
    )

    # Apply reminder adjustments
    for rem in active_reminders:
        if rem.id in resolutions:
            decision: ConflictDecision = resolutions[rem.id]
            if decision.action == "keep":
                pass
            elif decision.action == "cancel":
                rem.state = "cancelled"
            elif decision.action == "shift":
                days = decision.days_before if decision.days_before is not None else 1
                rem.days_before = days
                rem.time_of_day = decision.time_of_day or "09:00:00"
                rem.anchor = "offset_before_event"
                rem.fire_at = calculate_offset_fire_time(
                    event_starts_at_utc=new_starts_at,
                    court_timezone=court_tz,
                    days_before=days,
                    time_of_day_str=rem.time_of_day,
                )
                rem.state = "pending"
        else:
            if rem.anchor == "offset_before_event":
                days = rem.days_before if rem.days_before is not None else 1
                rem.fire_at = calculate_offset_fire_time(
                    event_starts_at_utc=new_starts_at,
                    court_timezone=court_tz,
                    days_before=days,
                    time_of_day_str=rem.time_of_day,
                )
                # Re-arm already-sent offset reminders for the new date
                if rem.state in ("sent", "missed"):
                    rem.state = "pending"

    # Send in-app notification of event reschedule
    InAppNotificationChannel().send(
        db=db,
        matter_id=matter_id,
        user_id=actor_id,
        event_id=event.id,
        title=f"Event Rescheduled: {event.title}",
        message=f"Rescheduled to {new_starts_at.isoformat()}. Reason: {data.reason}",
        notification_type="event_rescheduled",
    )

    db.commit()
    db.refresh(event)
    return event, "completed", []


def postpone_event(
    db: Session,
    matter_id: str,
    event_id: str,
    reason: str,
    actor_id: str,
    tentative_date: Optional[datetime] = None,
) -> Event:
    """Postpone an event. Pauses reminders until rescheduled."""
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )

    now = datetime.now(timezone.utc)
    old_status = event.status
    event.status = "postponed"
    if tentative_date:
        event.starts_at = tentative_date

    change = EventChange(
        id=str(uuid.uuid4()),
        event_id=event.id,
        matter_id=matter_id,
        change_type="postpone",
        old_status=old_status,
        new_status="postponed",
        reason=reason,
        actor=actor_id,
        created_at=now,
    )
    db.add(change)

    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="postpone",
        target_type="event",
        target_id=event.id,
        before={"status": old_status},
        after={"status": "postponed"},
        reason=reason,
    )

    InAppNotificationChannel().send(
        db=db,
        matter_id=matter_id,
        user_id=actor_id,
        event_id=event.id,
        title=f"Event Postponed: {event.title}",
        message=f"Postponed. Reason: {reason}",
        notification_type="event_postponed",
    )

    db.commit()
    db.refresh(event)
    return event


def cancel_event(
    db: Session,
    matter_id: str,
    event_id: str,
    reason: str,
    actor_id: str,
) -> Event:
    """Cancels an event and cancels all associated active reminders."""
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )

    now = datetime.now(timezone.utc)
    old_status = event.status
    event.status = "cancelled"
    event.sequence += 1

    # Cancel all active reminders
    for rem in event.reminders:
        if rem.state not in ("done", "cancelled"):
            rem.state = "cancelled"

    change = EventChange(
        id=str(uuid.uuid4()),
        event_id=event.id,
        matter_id=matter_id,
        change_type="cancel",
        old_status=old_status,
        new_status="cancelled",
        reason=reason,
        actor=actor_id,
        created_at=now,
    )
    db.add(change)

    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="cancel",
        target_type="event",
        target_id=event.id,
        before={"status": old_status},
        after={"status": "cancelled"},
        reason=reason,
    )

    InAppNotificationChannel().send(
        db=db,
        matter_id=matter_id,
        user_id=actor_id,
        event_id=event.id,
        title=f"Event Cancelled: {event.title}",
        message=f"Cancelled. Reason: {reason}",
        notification_type="event_cancelled",
    )

    db.commit()
    db.refresh(event)
    return event


def verify_deadline(
    db: Session,
    matter_id: str,
    event_id: str,
    actor_id: str,
    notes: Optional[str] = None,
) -> Event:
    """Verifies a deadline, stamping verified_by and verified_at."""
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )
    if event.kind != "deadline":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only deadline events can be verified.",
        )

    now = datetime.now(timezone.utc)
    event.verified_by = actor_id
    event.verified_at = now

    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="verify",
        target_type="event",
        target_id=event.id,
        after={"verified_by": actor_id, "verified_at": now.isoformat()},
        reason=notes,
    )
    db.commit()
    db.refresh(event)
    return event


# ==========================================
# Attached Documents & Versioning
# ==========================================


def attach_document(
    db: Session,
    matter_id: str,
    event_id: str,
    file: Optional[UploadFile],
    display_name: str,
    actor_id: str,
    external_document_id: Optional[str] = None,
) -> AttachedDocument:
    """
    Attaches a document with version tracking.
    - Stored under uploads/{matter_id}/
    - SHA-256 calculation
    - Same-sha256 re-upload is a no-op
    - Preserves prior versions in docket_document_versions
    - Re-upload of reviewed file triggers changed_since_review and re-arms reminders
    """
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )

    # Validate file payload if provided
    file_bytes = b""
    content_type = "application/octet-stream"
    if file:
        content_type = file.content_type or "application/octet-stream"
        if (
            settings.ALLOWED_CONTENT_TYPES
            and content_type not in settings.ALLOWED_CONTENT_TYPES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content type '{content_type}' is not permitted.",
            )

        file_bytes = file.file.read()
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "File exceeds maximum upload size of "
                    f"{settings.MAX_UPLOAD_SIZE_BYTES} bytes."
                ),
            )

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # Find existing logical document with matching display_name on this event
    logical_doc = db.scalar(
        select(AttachedDocument).where(
            AttachedDocument.event_id == event.id,
            AttachedDocument.matter_id == matter_id,
            AttachedDocument.display_name == display_name,
        )
    )

    now = datetime.now(timezone.utc)

    # Prepare storage directory
    matter_upload_dir = os.path.join(settings.UPLOAD_DIR, matter_id)
    os.makedirs(matter_upload_dir, exist_ok=True)
    stored_filename = f"{sha256_hash}_{uuid.uuid4().hex[:8]}.bin"
    file_path = os.path.join(matter_upload_dir, stored_filename).replace("\\", "/")

    if logical_doc:
        # Check if identical SHA already exists
        for v in logical_doc.versions:
            if v.sha256 == sha256_hash:
                # Same-sha256 re-upload is a no-op
                return logical_doc

        # Write new version file to disk
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Mark prior versions as not current
        for v in logical_doc.versions:
            v.is_current = False

        prev_version = logical_doc.current_version
        prev_version_num = (
            max([v.version_number for v in logical_doc.versions])
            if logical_doc.versions
            else 1
        )
        new_version_num = prev_version_num + 1

        new_version = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=logical_doc.id,
            matter_id=matter_id,
            version_number=new_version_num,
            file_path=file_path,
            file_size_bytes=len(file_bytes),
            content_type=content_type,
            sha256=sha256_hash,
            is_current=True,
            supersedes_id=prev_version.id if prev_version else None,
            external_document_id=external_document_id,
            uploaded_by=actor_id,
            uploaded_at=now,
        )
        db.add(new_version)

        # If previous version was reviewed, set changed_since_review
        # and re-arm reminders
        if logical_doc.review_status == "reviewed":
            logical_doc.review_status = "changed_since_review"
            for rem in logical_doc.reminders:
                if rem.state in ("sent", "missed"):
                    rem.state = "pending"

        logical_doc.updated_at = now
        record_event(
            db=db,
            matter_id=matter_id,
            actor=actor_id,
            action="document_upload",
            target_type="document",
            target_id=logical_doc.id,
            after={
                "version": new_version_num,
                "review_status": logical_doc.review_status,
            },
        )
        db.commit()
        db.refresh(logical_doc)
        return logical_doc

    # First version of new document
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    doc_id = str(uuid.uuid4())
    logical_doc = AttachedDocument(
        id=doc_id,
        event_id=event.id,
        matter_id=matter_id,
        display_name=display_name,
        review_status="to_review",
        created_at=now,
        updated_at=now,
    )
    db.add(logical_doc)

    initial_version = DocumentVersion(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        matter_id=matter_id,
        version_number=1,
        file_path=file_path,
        file_size_bytes=len(file_bytes),
        content_type=content_type,
        sha256=sha256_hash,
        is_current=True,
        supersedes_id=None,
        external_document_id=external_document_id,
        uploaded_by=actor_id,
        uploaded_at=now,
    )
    db.add(initial_version)

    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="document_upload",
        target_type="document",
        target_id=doc_id,
        after={"display_name": display_name, "version": 1},
    )
    db.commit()
    db.refresh(logical_doc)
    return logical_doc


def update_document_review_status(
    db: Session,
    matter_id: str,
    event_id: str,
    doc_id: str,
    review_status: str,
    actor_id: str,
) -> AttachedDocument:
    """Updates document review status and writes audit log."""
    doc = db.scalar(
        select(AttachedDocument).where(
            AttachedDocument.id == doc_id,
            AttachedDocument.event_id == event_id,
            AttachedDocument.matter_id == matter_id,
        )
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found for this event and matter.",
        )

    before = {"review_status": doc.review_status}
    doc.review_status = review_status
    if review_status == "reviewed":
        doc.reviewed_at = datetime.now(timezone.utc)
        doc.reviewed_by = actor_id

    doc.updated_at = datetime.now(timezone.utc)
    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="review_status_change",
        target_type="document",
        target_id=doc.id,
        before=before,
        after={"review_status": review_status},
    )
    db.commit()
    db.refresh(doc)
    return doc


def get_document_version_file(
    db: Session,
    matter_id: str,
    doc_id: str,
    version_number: Optional[int] = None,
) -> Tuple[str, str, str]:
    """Retrieves file path, display name, and content type for download."""
    doc = db.scalar(
        select(AttachedDocument).where(
            AttachedDocument.id == doc_id,
            AttachedDocument.matter_id == matter_id,
        )
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found for this matter.",
        )

    target_ver: Optional[DocumentVersion] = None
    if version_number:
        for v in doc.versions:
            if v.version_number == version_number:
                target_ver = v
                break
    else:
        target_ver = doc.current_version

    if not target_ver or not os.path.exists(target_ver.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file version not found on disk.",
        )

    return target_ver.file_path, doc.display_name, target_ver.content_type


def delete_document(
    db: Session,
    matter_id: str,
    event_id: str,
    doc_id: str,
    actor_id: str,
) -> None:
    """Removes an attached document."""
    doc = db.scalar(
        select(AttachedDocument).where(
            AttachedDocument.id == doc_id,
            AttachedDocument.event_id == event_id,
            AttachedDocument.matter_id == matter_id,
        )
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="document_delete",
        target_type="document",
        target_id=doc.id,
        before={"display_name": doc.display_name},
    )
    db.delete(doc)
    db.commit()


# ==========================================
# Reminders
# ==========================================


def create_reminder(
    db: Session,
    matter_id: str,
    event_id: str,
    data: ReminderCreate,
    creator_id: str,
) -> Reminder:
    """
    Creates a reminder for an event or attached document.
    Calculates fire_at in court timezone.
    Validates fire_at is not in the past.
    """
    event = get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )

    # Cross-matter check for document_id
    if data.document_id:
        doc = db.scalar(
            select(AttachedDocument).where(
                AttachedDocument.id == data.document_id,
                AttachedDocument.event_id == event.id,
                AttachedDocument.matter_id == matter_id,
            )
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document does not belong to this event and matter.",
            )

    now = datetime.now(timezone.utc)
    fire_at: Optional[datetime] = None

    if data.anchor == "offset_before_event":
        days = data.days_before if data.days_before is not None else 1
        fire_at = calculate_offset_fire_time(
            event_starts_at_utc=event.starts_at,
            court_timezone=event.timezone,
            days_before=days,
            time_of_day_str=data.time_of_day,
        )
    else:
        if not data.fire_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fire_at is required for fixed_datetime reminders.",
            )
        fire_at = data.fire_at
        if fire_at.tzinfo is None:
            fire_at = fire_at.replace(tzinfo=timezone.utc)

    # Reminders are never created in the past
    if fire_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminders cannot be scheduled in the past.",
        )

    rem_id = str(uuid.uuid4())
    reminder = Reminder(
        id=rem_id,
        event_id=event.id,
        matter_id=matter_id,
        document_id=data.document_id,
        user_id=creator_id,
        created_by=creator_id,
        anchor=data.anchor,
        days_before=data.days_before,
        time_of_day=data.time_of_day,
        fire_at=fire_at,
        repeat_rule=data.repeat_rule,
        state="pending",
    )
    db.add(reminder)

    record_event(
        db=db,
        matter_id=matter_id,
        actor=creator_id,
        action="reminder_create",
        target_type="reminder",
        target_id=rem_id,
        after={
            "anchor": data.anchor,
            "fire_at": fire_at.isoformat(),
            "repeat_rule": data.repeat_rule,
        },
    )
    db.commit()
    db.refresh(reminder)
    return reminder


def update_reminder_action(
    db: Session,
    matter_id: str,
    event_id: str,
    reminder_id: str,
    action: ReminderActionRequest,
    actor_id: str,
) -> Reminder:
    """Handles user reminder actions: snooze, acknowledge, done."""
    rem = db.scalar(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.event_id == event_id,
            Reminder.matter_id == matter_id,
        )
    )
    if not rem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found for this event and matter.",
        )

    now = datetime.now(timezone.utc)
    before_state = rem.state

    if action.action == "snooze":
        if not action.snooze_until:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="snooze_until is required when snoozing a reminder.",
            )
        snooze_time = action.snooze_until
        if snooze_time.tzinfo is None:
            snooze_time = snooze_time.replace(tzinfo=timezone.utc)
        if snooze_time <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="snooze_until must be in the future.",
            )
        rem.state = "snoozed"
        rem.snoozed_until = snooze_time
    elif action.action == "acknowledge":
        rem.state = "acknowledged"
    elif action.action == "done":
        rem.state = "done"

    rem.updated_at = now
    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action=action.action,
        target_type="reminder",
        target_id=rem.id,
        before={"state": before_state},
        after={"state": rem.state},
    )
    db.commit()
    db.refresh(rem)
    return rem


def delete_reminder(
    db: Session,
    matter_id: str,
    event_id: str,
    reminder_id: str,
    actor_id: str,
) -> None:
    """Deletes a reminder."""
    rem = db.scalar(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.event_id == event_id,
            Reminder.matter_id == matter_id,
        )
    )
    if not rem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found.",
        )

    record_event(
        db=db,
        matter_id=matter_id,
        actor=actor_id,
        action="reminder_delete",
        target_type="reminder",
        target_id=rem.id,
    )
    db.delete(rem)
    db.commit()


# ==========================================
# Idempotent Occurrence Firing & Scheduler
# ==========================================


def process_due_reminders(db: Session, now: datetime) -> int:
    """
    Evaluates due reminders and executes firing with atomic claim idempotency.
    Guaranteed safe across multiple scheduler triggers or server restarts.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # Load candidate reminders
    candidates = list(
        db.scalars(
            select(Reminder).where(Reminder.state.in_(["pending", "snoozed", "sent"]))
        ).all()
    )
    if not candidates:
        return 0

    event_ids = {r.event_id for r in candidates}
    events = list(db.scalars(select(Event).where(Event.id.in_(event_ids))).all())
    event_map = {e.id: e for e in events}

    doc_ids = {r.document_id for r in candidates if r.document_id}
    docs = (
        list(
            db.scalars(
                select(AttachedDocument).where(AttachedDocument.id.in_(doc_ids))
            ).all()
        )
        if doc_ids
        else []
    )
    doc_map = {d.id: d for d in docs}

    actions = compute_due_reminders(candidates, event_map, doc_map, now)
    fired_count = 0
    channel = InAppNotificationChannel()

    for act in actions:
        rem = act.reminder
        event = event_map[rem.event_id]

        # 1. Atomic claim via unique constraint on (reminder_id, occurrence_time)
        occurrence = ReminderOccurrence(
            id=str(uuid.uuid4()),
            reminder_id=rem.id,
            occurrence_time=act.occurrence_time,
            fired_at=now,
            status=(
                "late_missed" if act.action_type == "fire_late_missed" else "fired"
            ),
        )
        db.add(occurrence)
        try:
            db.flush()
        except IntegrityError:
            # Already claimed and fired by another worker or previous cycle
            db.rollback()
            continue

        # 2. Update reminder status
        rem.last_fired_at = now
        rem.state = act.new_state
        if rem.state == "snoozed":
            rem.snoozed_until = None

        # 3. Handle repeating rules
        if rem.repeat_rule != "none":
            next_fire = compute_next_occurrence(
                current_fire_at=act.occurrence_time,
                repeat_rule=rem.repeat_rule,
                event_starts_at=event.starts_at,
            )
            if next_fire:
                rem.fire_at = next_fire
                rem.state = "pending"

        # 4. Dispatch notification to the reminder's owner/recipient
        channel.send(
            db=db,
            matter_id=rem.matter_id,
            user_id=rem.user_id,
            event_id=rem.event_id,
            reminder_id=rem.id,
            title=(
                f"LATE REMINDER: {event.title}"
                if act.action_type == "fire_late_missed"
                else f"Reminder: {event.title}"
            ),
            message=(
                f"Deadline/hearing alert for {event.title} at "
                f"{event.starts_at.isoformat()}."
            ),
            notification_type=act.notification_type,
        )

        fired_count += 1
        db.commit()

    return fired_count


# ==========================================
# Agenda & History
# ==========================================


def get_agenda(
    db: Session,
    matter_id: str,
    from_date: datetime,
    to_date: datetime,
    current_user_id: str,
) -> Dict[str, Any]:
    """Compiles chronological agenda of events, due reminders, and missed reminders."""
    events = list(
        db.scalars(
            select(Event)
            .where(
                Event.matter_id == matter_id,
                Event.starts_at >= from_date,
                Event.starts_at <= to_date,
            )
            .order_by(Event.starts_at.asc())
        ).all()
    )

    reminders = list(
        db.scalars(
            select(Reminder).where(
                Reminder.matter_id == matter_id,
                Reminder.user_id == current_user_id,
            )
        ).all()
    )

    due_reminders = [
        r
        for r in reminders
        if r.state in ("pending", "snoozed")
        and r.fire_at
        and from_date <= r.fire_at <= to_date
    ]
    missed_reminders = [r for r in reminders if r.state == "missed"]

    items: List[Dict[str, Any]] = []
    for ev in events:
        items.append(
            {
                "item_type": "event",
                "timestamp": ev.starts_at,
                "event": ev,
                "reminder": None,
                "is_missed": False,
            }
        )
    for rem in due_reminders:
        items.append(
            {
                "item_type": "reminder",
                "timestamp": rem.fire_at,
                "event": rem.event,
                "reminder": rem,
                "is_missed": False,
            }
        )
    for rem in missed_reminders:
        items.append(
            {
                "item_type": "reminder",
                "timestamp": rem.fire_at,
                "event": rem.event,
                "reminder": rem,
                "is_missed": True,
            }
        )

    # Sort chronological
    items.sort(key=lambda x: x["timestamp"])

    return {
        "items": items,
        "events": events,
        "due_reminders": due_reminders,
        "missed_reminders": missed_reminders,
    }
