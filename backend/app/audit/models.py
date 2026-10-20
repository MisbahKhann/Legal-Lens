"""
AuditLog ORM model.
Strictly append-only: updates and deletes are prohibited.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Float, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UTCDateTime


class AuditLog(Base):
    """
    Append-only audit trail logging all lifecycle events, status changes,
    and administrative actions across matters.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_matter_target", "matter_id", "target_type", "target_id"),
        Index("ix_audit_logs_created_at", "created_at"),
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
    actor: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


from sqlalchemy import event, text  # noqa: E402


@event.listens_for(AuditLog.__table__, "after_create")
def create_audit_log_triggers(target, connection, **kw) -> None:
    """Create triggers preventing UPDATE and DELETE on audit_logs."""
    if connection.dialect.name == "sqlite":
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS trg_prevent_audit_logs_update "
                "BEFORE UPDATE ON audit_logs BEGIN "
                "SELECT RAISE(FAIL, 'Updates prohibited on append-only audit_logs'); "
                "END;"
            )
        )
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS trg_prevent_audit_logs_delete "
                "BEFORE DELETE ON audit_logs BEGIN "
                "SELECT RAISE(FAIL, 'Deletions prohibited on append-only audit_logs'); "
                "END;"
            )
        )
