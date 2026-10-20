"""
Pydantic schemas for Docket module.
Hearings, deadlines, reschedule conflicts, documents, reminders, agenda,
and notifications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

# ==========================================
# Event Schemas
# ==========================================


class EventCreate(BaseModel):
    """Event creation payload. entered_by is determined server-side from auth."""

    kind: str = Field(..., pattern="^(hearing|deadline)$")
    title: str = Field(..., min_length=1, max_length=255)
    starts_at: datetime
    timezone: str = Field(default="America/New_York", max_length=64)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    notes: Optional[str] = None

    # Hearing fields
    hearing_type: Optional[str] = Field(None, max_length=100)
    court_name: Optional[str] = Field(None, max_length=255)
    courtroom: Optional[str] = Field(None, max_length=100)
    judge: Optional[str] = Field(None, max_length=100)
    case_number: Optional[str] = Field(None, max_length=100)
    mode: Optional[str] = Field(None, pattern="^(in_person|virtual|hybrid)$")
    virtual_link: Optional[str] = Field(None, max_length=512)

    # Deadline fields
    deadline_type: Optional[str] = Field(None, max_length=100)
    source_description: Optional[str] = None
    source_document_id: Optional[str] = Field(None, max_length=100)
    verified_by: Optional[str] = Field(None, max_length=100)
    adjustment_reason: Optional[str] = None


class EventUpdate(BaseModel):
    """Metadata updates (non-date fields). Date changes must use /reschedule."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    notes: Optional[str] = None

    # Hearing fields
    hearing_type: Optional[str] = None
    court_name: Optional[str] = None
    courtroom: Optional[str] = None
    judge: Optional[str] = None
    case_number: Optional[str] = None
    mode: Optional[str] = None
    virtual_link: Optional[str] = None

    # Deadline fields
    deadline_type: Optional[str] = None
    source_description: Optional[str] = None
    source_document_id: Optional[str] = None
    adjustment_reason: Optional[str] = None


class EventResponse(BaseModel):
    id: str
    matter_id: str
    kind: str
    title: str
    starts_at: datetime
    timezone: str
    status: str
    priority: str
    notes: Optional[str] = None

    # Hearing fields
    hearing_type: Optional[str] = None
    court_name: Optional[str] = None
    courtroom: Optional[str] = None
    judge: Optional[str] = None
    case_number: Optional[str] = None
    mode: Optional[str] = None
    virtual_link: Optional[str] = None

    # Deadline fields
    deadline_type: Optional[str] = None
    source_description: Optional[str] = None
    source_document_id: Optional[str] = None
    entered_by: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    adjustment_reason: Optional[str] = None

    sequence: int
    created_at: datetime
    updated_at: datetime
    warning: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int


class EventChangeResponse(BaseModel):
    id: str
    event_id: str
    matter_id: str
    change_type: str
    old_starts_at: Optional[datetime] = None
    new_starts_at: Optional[datetime] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    reason: str
    actor: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Document Schemas
# ==========================================


class DocumentVersionResponse(BaseModel):
    id: str
    document_id: str
    matter_id: str
    version_number: int
    file_path: str
    file_size_bytes: int
    content_type: str
    sha256: str
    is_current: bool
    supersedes_id: Optional[str] = None
    external_document_id: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttachedDocumentResponse(BaseModel):
    id: str
    event_id: str
    matter_id: str
    display_name: str
    review_status: str
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    current_version: Optional[DocumentVersionResponse] = None
    versions: List[DocumentVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentReviewUpdateRequest(BaseModel):
    review_status: str = Field(..., pattern="^(to_review|reviewed)$")


# ==========================================
# Reminder Schemas
# ==========================================


class ReminderCreate(BaseModel):
    anchor: str = Field(..., pattern="^(offset_before_event|fixed_datetime)$")
    days_before: Optional[int] = Field(None, ge=0)
    time_of_day: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    fire_at: Optional[datetime] = None
    repeat_rule: str = Field(
        default="none",
        pattern="^(none|daily_until_reviewed|daily_until_event)$",
    )
    document_id: Optional[str] = None


class ReminderActionRequest(BaseModel):
    action: str = Field(..., pattern="^(snooze|acknowledge|done)$")
    snooze_until: Optional[datetime] = None


class ReminderResponse(BaseModel):
    id: str
    event_id: str
    matter_id: str
    document_id: Optional[str] = None
    user_id: str
    created_by: str
    anchor: str
    days_before: Optional[int] = None
    time_of_day: Optional[str] = None
    fire_at: Optional[datetime] = None
    repeat_rule: str
    state: str
    snoozed_until: Optional[datetime] = None
    last_fired_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Reschedule & Conflicts Schemas
# ==========================================


class ConflictDecision(BaseModel):
    action: str = Field(..., pattern="^(keep|shift|cancel)$")
    days_before: Optional[int] = None
    time_of_day: Optional[str] = None


class ReminderConflict(BaseModel):
    reminder_id: str
    anchor: str
    current_fire_at: Optional[datetime] = None
    projected_fire_at: Optional[datetime] = None
    issue: str
    suggested_action: str


class RescheduleRequest(BaseModel):
    new_starts_at: datetime
    new_timezone: Optional[str] = None
    reason: str = Field(..., min_length=1)
    conflict_resolutions: Optional[Dict[str, ConflictDecision]] = None


class RescheduleResponse(BaseModel):
    status: str  # 'completed' | 'conflicts_detected'
    event: EventResponse
    conflicts: List[ReminderConflict] = []


class PostponeRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    tentative_date: Optional[datetime] = None


class CancelRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class VerifyDeadlineRequest(BaseModel):
    notes: Optional[str] = None


# ==========================================
# Event Detail & History
# ==========================================


class EventDetailResponse(EventResponse):
    documents: List[AttachedDocumentResponse] = []
    reminders: List[ReminderResponse] = []
    changes: List[EventChangeResponse] = []


class EventHistoryResponse(BaseModel):
    event_id: str
    changes: List[EventChangeResponse]
    audit_trail: List[Dict[str, Any]]


# ==========================================
# Agenda & Notification Schemas
# ==========================================


class AgendaItem(BaseModel):
    item_type: str  # 'event' | 'reminder'
    timestamp: datetime
    event: Optional[EventResponse] = None
    reminder: Optional[ReminderResponse] = None
    is_missed: bool = False


class AgendaResponse(BaseModel):
    items: List[AgendaItem]
    events: List[EventResponse]
    due_reminders: List[ReminderResponse]
    missed_reminders: List[ReminderResponse]


class NotificationResponse(BaseModel):
    id: str
    matter_id: str
    user_id: str
    event_id: str
    reminder_id: Optional[str] = None
    title: str
    message: str
    notification_type: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
