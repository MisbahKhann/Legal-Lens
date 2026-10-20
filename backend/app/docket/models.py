"""
SQLAlchemy models for Docket module.
Hearings, Deadlines, EventChanges, AttachedDocuments, Reminders,
Occurrences, and Notifications.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UTCDateTime


class Event(Base):
    """Docket Event representing a court hearing or legal deadline."""

    __tablename__ = "docket_events"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('hearing', 'deadline')",
            name="ck_event_kind",
        ),
        CheckConstraint(
            "status IN ('scheduled', 'rescheduled', 'postponed', "
            "'cancelled', 'completed')",
            name="ck_event_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="ck_event_priority",
        ),
        CheckConstraint(
            "mode IS NULL OR mode IN ('in_person', 'virtual', 'hybrid')",
            name="ck_event_hearing_mode",
        ),
        Index("ix_docket_events_matter_starts", "matter_id", "starts_at"),
        Index("ix_docket_events_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    matter_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="America/New_York"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hearing-specific fields
    hearing_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    court_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    courtroom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    judge: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    case_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    virtual_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Deadline-specific fields
    deadline_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_document_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    entered_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    adjustment_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # iCalendar sequence counter
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    changes: Mapped[List["EventChange"]] = relationship(
        "EventChange",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="desc(EventChange.created_at)",
    )
    documents: Mapped[List["AttachedDocument"]] = relationship(
        "AttachedDocument",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[List["Reminder"]] = relationship(
        "Reminder",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventChange(Base):
    """History record of every date, time, or status modification to an event."""

    __tablename__ = "docket_event_changes"
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('reschedule', 'postpone', 'cancel', 'edit')",
            name="ck_change_type",
        ),
        Index("ix_docket_event_changes_matter", "matter_id", "event_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("docket_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_starts_at: Mapped[Optional[datetime]] = mapped_column(
        UTCDateTime, nullable=True
    )
    new_starts_at: Mapped[Optional[datetime]] = mapped_column(
        UTCDateTime, nullable=True
    )
    old_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    event: Mapped["Event"] = relationship("Event", back_populates="changes")


class AttachedDocument(Base):
    """
    Logical Document attached to an event with review workflow tracking.
    Review status and reminders attach to this logical document.
    Prior file versions are preserved in docket_document_versions.
    """

    __tablename__ = "docket_attached_documents"
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('to_review', 'reviewed', 'changed_since_review')",
            name="ck_doc_review_status",
        ),
        Index("ix_docket_docs_matter_event", "matter_id", "event_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("docket_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="to_review"
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    event: Mapped["Event"] = relationship("Event", back_populates="documents")
    versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number",
    )
    reminders: Mapped[List["Reminder"]] = relationship(
        "Reminder", back_populates="document"
    )

    @property
    def current_version(self) -> Optional["DocumentVersion"]:
        for v in self.versions:
            if v.is_current:
                return v
        return self.versions[-1] if self.versions else None


class DocumentVersion(Base):
    """
    Physical version of an attached document.
    Prior versions are preserved; supersedes_id links the version chain.
    """

    __tablename__ = "docket_document_versions"
    __table_args__ = (
        Index("ix_docket_doc_versions_doc", "document_id"),
        Index("ix_docket_doc_versions_sha", "document_id", "sha256"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("docket_attached_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="application/octet-stream"
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supersedes_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("docket_document_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_document_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    uploaded_by: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    document: Mapped["AttachedDocument"] = relationship(
        "AttachedDocument", back_populates="versions"
    )


class Reminder(Base):
    """Notification trigger configuration for an event or attached document."""

    __tablename__ = "docket_reminders"
    __table_args__ = (
        CheckConstraint(
            "anchor IN ('offset_before_event', 'fixed_datetime')",
            name="ck_reminder_anchor",
        ),
        CheckConstraint(
            "repeat_rule IN ('none', 'daily_until_reviewed', 'daily_until_event')",
            name="ck_reminder_repeat_rule",
        ),
        CheckConstraint(
            "state IN ('pending', 'sent', 'acknowledged', 'snoozed', "
            "'done', 'missed', 'cancelled')",
            name="ck_reminder_state",
        ),
        Index("ix_docket_reminders_matter", "matter_id"),
        Index("ix_docket_reminders_state", "state"),
        Index("ix_docket_reminders_state_fire_at", "state", "fire_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("docket_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("docket_attached_documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    anchor: Mapped[str] = mapped_column(String(30), nullable=False)
    days_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_of_day: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    fire_at: Mapped[Optional[datetime]] = mapped_column(
        UTCDateTime, nullable=True, index=True
    )
    repeat_rule: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(
        UTCDateTime, nullable=True
    )
    last_fired_at: Mapped[Optional[datetime]] = mapped_column(
        UTCDateTime, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    event: Mapped["Event"] = relationship("Event", back_populates="reminders")
    document: Mapped[Optional["AttachedDocument"]] = relationship(
        "AttachedDocument", back_populates="reminders"
    )
    occurrences: Mapped[List["ReminderOccurrence"]] = relationship(
        "ReminderOccurrence",
        back_populates="reminder",
        cascade="all, delete-orphan",
    )


class ReminderOccurrence(Base):
    """
    Atomic tracking record for reminder executions.
    Guarantees idempotency via unique constraint on (reminder_id, occurrence_time).
    """

    __tablename__ = "docket_reminder_occurrences"
    __table_args__ = (
        UniqueConstraint(
            "reminder_id", "occurrence_time", name="uq_reminder_occurrence"
        ),
        CheckConstraint(
            "status IN ('fired', 'late_missed')",
            name="ck_occurrence_status",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    reminder_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("docket_reminders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    occurrence_time: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    fired_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="fired")

    reminder: Mapped["Reminder"] = relationship(
        "Reminder", back_populates="occurrences"
    )


class Notification(Base):
    """In-app alert for hearing changes and reminder dispatches."""

    __tablename__ = "docket_notifications"
    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('reminder_fired', 'reminder_late', "
            "'event_rescheduled', 'event_postponed', 'event_cancelled', "
            "'document_changed')",
            name="ck_notification_type",
        ),
        Index("ix_docket_notifications_user_read", "user_id", "is_read"),
        Index("ix_docket_notifications_matter", "matter_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    matter_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("docket_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reminder_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("docket_reminders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
