"""
FastAPI router for Docket module.
Scoped under /matters/{matter_id}/docket and /notifications.
Enforces multi-tenancy, viewer read-only restrictions, and user isolation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.core.auth import (
    get_current_user,
    require_matter_access,
    require_matter_write,
)
from app.core.database import get_db
from app.core.models import MatterMember
from app.core.schemas import CurrentUser
from app.docket import service
from app.docket.ics import generate_ics_calendar
from app.docket.models import Event, Notification
from app.docket.schemas import (
    AgendaResponse,
    AttachedDocumentResponse,
    CancelRequest,
    DocumentReviewUpdateRequest,
    EventChangeResponse,
    EventCreate,
    EventDetailResponse,
    EventHistoryResponse,
    EventListResponse,
    EventResponse,
    EventUpdate,
    NotificationListResponse,
    NotificationResponse,
    PostponeRequest,
    ReminderActionRequest,
    ReminderCreate,
    ReminderResponse,
    RescheduleRequest,
    RescheduleResponse,
    VerifyDeadlineRequest,
)

docket_router = APIRouter(prefix="/matters/{matter_id}/docket", tags=["Docket"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ==========================================
# Events Endpoints
# ==========================================


@docket_router.get("/events", response_model=EventListResponse)
def get_events(
    matter_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kind: Optional[str] = Query(None, pattern="^(hearing|deadline)$"),
    status_filter: Optional[str] = Query(None, alias="status"),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
) -> EventListResponse:
    """List events for a matter."""
    items, total = service.list_events(
        db=db,
        matter_id=matter_id,
        limit=limit,
        offset=offset,
        kind=kind,
        status_filter=status_filter,
        from_date=from_date,
        to_date=to_date,
    )
    return EventListResponse(
        items=[EventResponse.model_validate(e) for e in items],
        total=total,
    )


@docket_router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    matter_id: str,
    data: EventCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> EventResponse:
    """Create a new hearing or deadline event. Viewers receive 403 Forbidden."""
    event, warning = service.create_event(
        db=db,
        matter_id=matter_id,
        data=data,
        creator_id=current_user.id,
    )
    resp = EventResponse.model_validate(event)
    resp.warning = warning
    return resp


@docket_router.get("/events/{event_id}", response_model=EventDetailResponse)
def get_event(
    matter_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
) -> EventDetailResponse:
    """Get event details including attachments, reminders, and history."""
    event = service.get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found for this matter.",
        )
    return EventDetailResponse.model_validate(event)


@docket_router.patch("/events/{event_id}", response_model=EventResponse)
def update_event(
    matter_id: str,
    event_id: str,
    data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> EventResponse:
    """Update event metadata (non-date fields)."""
    event = service.update_event(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        data=data,
        actor_id=current_user.id,
    )
    return EventResponse.model_validate(event)


@docket_router.delete("/events/{event_id}")
def delete_event(
    matter_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> Dict[str, str]:
    """Delete an event."""
    service.delete_event(db, matter_id, event_id, actor_id=current_user.id)
    return {"status": "deleted", "id": event_id}


# ==========================================
# Lifecycle: Reschedule, Postpone, Cancel, Verify
# ==========================================


@docket_router.post("/events/{event_id}/reschedule", response_model=RescheduleResponse)
def reschedule_event(
    matter_id: str,
    event_id: str,
    data: RescheduleRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> RescheduleResponse:
    """Reschedule an event date. Computes and reports fixed reminder conflicts."""
    event, res_status, conflicts = service.reschedule_event(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        data=data,
        actor_id=current_user.id,
    )
    return RescheduleResponse(
        status=res_status,
        event=EventResponse.model_validate(event),
        conflicts=conflicts,
    )


@docket_router.post("/events/{event_id}/postpone", response_model=EventResponse)
def postpone_event(
    matter_id: str,
    event_id: str,
    data: PostponeRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> EventResponse:
    """Postpone an event. Pauses reminders."""
    event = service.postpone_event(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        reason=data.reason,
        actor_id=current_user.id,
        tentative_date=data.tentative_date,
    )
    return EventResponse.model_validate(event)


@docket_router.post("/events/{event_id}/cancel", response_model=EventResponse)
def cancel_event(
    matter_id: str,
    event_id: str,
    data: CancelRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> EventResponse:
    """Cancel an event and cancel all active reminders."""
    event = service.cancel_event(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        reason=data.reason,
        actor_id=current_user.id,
    )
    return EventResponse.model_validate(event)


@docket_router.post("/events/{event_id}/verify", response_model=EventResponse)
def verify_deadline(
    matter_id: str,
    event_id: str,
    data: Optional[VerifyDeadlineRequest] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> EventResponse:
    """Verify a deadline, stamping verified_by and verified_at."""
    notes = data.notes if data else None
    event = service.verify_deadline(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        actor_id=current_user.id,
        notes=notes,
    )
    return EventResponse.model_validate(event)


# ==========================================
# Attached Documents Endpoints
# ==========================================


@docket_router.post(
    "/events/{event_id}/documents",
    response_model=AttachedDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    matter_id: str,
    event_id: str,
    display_name: str = Form(...),
    external_document_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> AttachedDocumentResponse:
    """Attach a document file or link to an event."""
    doc = service.attach_document(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        file=file,
        display_name=display_name,
        actor_id=current_user.id,
        external_document_id=external_document_id,
    )
    return AttachedDocumentResponse.model_validate(doc)


@docket_router.patch(
    "/events/{event_id}/documents/{doc_id}",
    response_model=AttachedDocumentResponse,
)
def update_document_review(
    matter_id: str,
    event_id: str,
    doc_id: str,
    data: DocumentReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> AttachedDocumentResponse:
    """Update document review status."""
    doc = service.update_document_review_status(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        doc_id=doc_id,
        review_status=data.review_status,
        actor_id=current_user.id,
    )
    return AttachedDocumentResponse.model_validate(doc)


@docket_router.get("/events/{event_id}/documents/{doc_id}/download")
def download_document(
    matter_id: str,
    event_id: str,
    doc_id: str,
    version: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
):
    """Download an attached document version. Matter-scoped."""
    file_path, display_name, content_type = service.get_document_version_file(
        db=db,
        matter_id=matter_id,
        doc_id=doc_id,
        version_number=version,
    )
    return FileResponse(
        path=file_path,
        filename=display_name,
        media_type=content_type,
    )


@docket_router.delete("/events/{event_id}/documents/{doc_id}")
def delete_document(
    matter_id: str,
    event_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> Dict[str, str]:
    """Delete an attached document."""
    service.delete_document(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        doc_id=doc_id,
        actor_id=current_user.id,
    )
    return {"status": "deleted", "id": doc_id}


# ==========================================
# Reminders Endpoints
# ==========================================


@docket_router.get(
    "/events/{event_id}/reminders", response_model=List[ReminderResponse]
)
def get_reminders(
    matter_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
) -> List[ReminderResponse]:
    """List reminders for an event."""
    event = service.get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )
    return [ReminderResponse.model_validate(r) for r in event.reminders]


@docket_router.post(
    "/events/{event_id}/reminders",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    matter_id: str,
    event_id: str,
    data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> ReminderResponse:
    """Create a reminder for an event or attached document."""
    rem = service.create_reminder(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        data=data,
        creator_id=current_user.id,
    )
    return ReminderResponse.model_validate(rem)


@docket_router.patch(
    "/events/{event_id}/reminders/{reminder_id}",
    response_model=ReminderResponse,
)
def handle_reminder_action(
    matter_id: str,
    event_id: str,
    reminder_id: str,
    data: ReminderActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> ReminderResponse:
    """Acknowledge, snooze, or mark done."""
    rem = service.update_reminder_action(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        reminder_id=reminder_id,
        action=data,
        actor_id=current_user.id,
    )
    return ReminderResponse.model_validate(rem)


@docket_router.delete("/events/{event_id}/reminders/{reminder_id}")
def delete_reminder(
    matter_id: str,
    event_id: str,
    reminder_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_write),
) -> Dict[str, str]:
    """Delete a reminder."""
    service.delete_reminder(
        db=db,
        matter_id=matter_id,
        event_id=event_id,
        reminder_id=reminder_id,
        actor_id=current_user.id,
    )
    return {"status": "deleted", "id": reminder_id}


# ==========================================
# Agenda, History & .ics Export
# ==========================================


@docket_router.get("/agenda", response_model=AgendaResponse)
def get_agenda(
    matter_id: str,
    from_date: datetime = Query(..., alias="from"),
    to_date: datetime = Query(..., alias="to"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    member: MatterMember = Depends(require_matter_access),
) -> AgendaResponse:
    """Get sorted chronological stream of events and reminders."""
    if from_date.tzinfo is None:
        from_date = from_date.replace(tzinfo=timezone.utc)
    if to_date.tzinfo is None:
        to_date = to_date.replace(tzinfo=timezone.utc)

    agenda_data = service.get_agenda(
        db=db,
        matter_id=matter_id,
        from_date=from_date,
        to_date=to_date,
        current_user_id=current_user.id,
    )
    return AgendaResponse(
        items=agenda_data["items"],
        events=[EventResponse.model_validate(e) for e in agenda_data["events"]],
        due_reminders=[
            ReminderResponse.model_validate(r) for r in agenda_data["due_reminders"]
        ],
        missed_reminders=[
            ReminderResponse.model_validate(r) for r in agenda_data["missed_reminders"]
        ],
    )


@docket_router.get("/events/{event_id}/history", response_model=EventHistoryResponse)
def get_event_history(
    matter_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
) -> EventHistoryResponse:
    """Retrieve event date/status changes and audit trail."""
    event = service.get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    logs = list(
        db.scalars(
            select(AuditLog)
            .where(
                AuditLog.matter_id == matter_id,
                AuditLog.target_id == event_id,
            )
            .order_by(AuditLog.created_at.desc())
        ).all()
    )

    return EventHistoryResponse(
        event_id=event.id,
        changes=[EventChangeResponse.model_validate(c) for c in event.changes],
        audit_trail=[
            {
                "actor": log.actor,
                "action": log.action,
                "created_at": log.created_at,
                "reason": log.reason,
            }
            for log in logs
        ],
    )


@docket_router.get("/events/{event_id}/export.ics")
def export_event_ics(
    matter_id: str,
    event_id: str,
    redact: bool = Query(False),
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
):
    """Export single event as RFC 5545 .ics."""
    event = service.get_event(db, matter_id, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    ics_content = generate_ics_calendar(event, redact=redact)
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="event-{event.id}.ics"'},
    )


@docket_router.get("/export.ics")
def export_matter_ics(
    matter_id: str,
    redact: bool = Query(False),
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
):
    """Export all upcoming matter events as RFC 5545 .ics."""
    now = datetime.now(timezone.utc)
    events = list(
        db.scalars(
            select(Event)
            .where(Event.matter_id == matter_id, Event.starts_at >= now)
            .order_by(Event.starts_at.asc())
        ).all()
    )

    ics_content = generate_ics_calendar(
        events, redact=redact, calendar_name=f"Matter {matter_id} Docket"
    )
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": (
                f'attachment; filename="matter-{matter_id}-docket.ics"'
            )
        },
    )


# ==========================================
# In-App Notifications (Calling User Scoped)
# ==========================================


@notifications_router.get("", response_model=NotificationListResponse)
def get_user_notifications(
    matter_id: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> NotificationListResponse:
    """Returns only the calling user's notifications. Scoped to current_user.id."""
    query = select(Notification).where(Notification.user_id == current_user.id)
    count_query = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id
    )

    if matter_id:
        query = query.where(Notification.matter_id == matter_id)
        count_query = count_query.where(Notification.matter_id == matter_id)

    if unread_only:
        query = query.where(Notification.is_read.is_(False))
        count_query = count_query.where(Notification.is_read.is_(False))

    query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

    total = db.scalar(count_query) or 0
    items = list(db.scalars(query).all())

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
    )


@notifications_router.post(
    "/{notification_id}/read", response_model=NotificationResponse
)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> NotificationResponse:
    """Marks a notification as read. Verifies user ownership."""
    notif = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notif)
    return NotificationResponse.model_validate(notif)


@notifications_router.post("/read-all")
def mark_all_notifications_read(
    matter_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Marks all notifications as read for current user."""
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    if matter_id:
        stmt = stmt.where(Notification.matter_id == matter_id)

    res = db.execute(stmt)
    db.commit()
    count = getattr(res, "rowcount", 0)
    return {"updated_count": int(count) if count is not None else 0}
