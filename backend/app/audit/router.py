"""
Audit router for matter audit logs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.audit import service
from app.audit.schemas import AuditLogListResponse, AuditLogResponse
from app.core.auth import require_audit_access
from app.core.database import get_db
from app.core.models import MatterMember

router = APIRouter(prefix="/matters/{matter_id}/audit", tags=["Audit"])


@router.get("", response_model=AuditLogListResponse)
def get_matter_audit_logs(
    matter_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    target_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_audit_access),
) -> AuditLogListResponse:
    """Retrieve audit trail logs for a specific matter. Scoped to matter members."""
    items, total = service.list_matter_audit_logs(
        db=db,
        matter_id=matter_id,
        limit=limit,
        offset=offset,
        target_type=target_type,
        target_id=target_id,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in items],
        total=total,
    )
