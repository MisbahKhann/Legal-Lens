"""
Authentication and matter access control dependencies.
Role is resolved strictly from matter_members for the scoped matter.
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.models import Matter, MatterMember
from app.core.schemas import CurrentUser


def verify_auth_environment() -> None:
    """Startup check refusing header authentication in production environment."""
    if settings.ENV.lower() == "production":
        raise RuntimeError(
            "Development header-based authentication is strictly prohibited in "
            "production mode."
        )


def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> CurrentUser:
    """
    Header-based dev auth dependency.
    Role headers (e.g. X-User-Role) are completely ignored; roles are evaluated
    strictly per-matter via matter_members.
    """
    if settings.ENV.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Header-based authentication is disabled in production.",
        )

    user_id = x_user_id.strip() if x_user_id and x_user_id.strip() else "user-dev-1"
    return CurrentUser(id=user_id)


def require_matter_access(
    matter_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> MatterMember:
    """
    Verifies that the matter exists and current user is a member.
    Returns MatterMember with the resolved user role.
    """
    matter = db.scalar(select(Matter).where(Matter.id == matter_id))
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter '{matter_id}' not found.",
        )

    member = db.scalar(
        select(MatterMember).where(
            MatterMember.matter_id == matter_id,
            MatterMember.user_id == current_user.id,
        )
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User '{current_user.id}' is not a member of matter '{matter_id}'.",
        )

    return member


def require_matter_write(
    member: MatterMember = Depends(require_matter_access),
) -> MatterMember:
    """
    Enforces write permissions.
    Viewers have read-only access and are rejected with 403 Forbidden.
    """
    if member.role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers have read-only access to this matter.",
        )
    return member


def require_audit_access(
    member: MatterMember = Depends(require_matter_access),
) -> MatterMember:
    """
    Enforces audit trail access permissions.
    Only matter owners and attorneys may view the audit trail.
    """
    if member.role not in ("owner", "attorney"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit trail access requires owner or attorney role.",
        )
    return member
