"""
Audit service providing record_event and query functions.
Strictly append-only: No update or delete operations are defined.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit.models import AuditLog


def record_event(
    db: Session,
    matter_id: str,
    actor: str,
    action: str,
    target_type: str,
    target_id: str,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    confidence: Optional[float] = None,
) -> AuditLog:
    """
    Append an audit log entry in the caller's active database transaction.
    DOES NOT COMMIT ITSELF: Caller is responsible for transaction commit/rollback.
    """
    entry = AuditLog(
        id=str(uuid.uuid4()),
        matter_id=matter_id,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_state=before,
        after_state=after,
        reason=reason,
        confidence=confidence,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.flush()
    return entry


def list_matter_audit_logs(
    db: Session,
    matter_id: str,
    limit: int = 50,
    offset: int = 0,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
) -> Tuple[List[AuditLog], int]:
    """Retrieve paginated audit logs scoped strictly to the specified matter."""
    query = select(AuditLog).where(AuditLog.matter_id == matter_id)
    count_query = select(func.count(AuditLog.id)).where(AuditLog.matter_id == matter_id)

    if target_type:
        query = query.where(AuditLog.target_type == target_type)
        count_query = count_query.where(AuditLog.target_type == target_type)

    if target_id:
        query = query.where(AuditLog.target_id == target_id)
        count_query = count_query.where(AuditLog.target_id == target_id)

    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)

    total = db.scalar(count_query) or 0
    items = list(db.scalars(query).all())
    return items, total
