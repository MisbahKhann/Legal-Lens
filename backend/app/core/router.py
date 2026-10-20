"""
FastAPI router for core matter operations.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import (
    get_current_user,
    require_matter_access,
    require_matter_write,
)
from app.core.database import get_db
from app.core.models import MatterMember
from app.core.schemas import (
    CurrentUser,
    MatterCreate,
    MatterListResponse,
    MatterMemberCreate,
    MatterMemberResponse,
    MatterResponse,
)
from app.core import service

router = APIRouter(prefix="/matters", tags=["Matters"])


@router.get("", response_model=MatterListResponse)
def list_matters(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> MatterListResponse:
    """List matters accessible by the current user."""
    items, total = service.list_user_matters(
        db, user_id=current_user.id, limit=limit, offset=offset
    )
    return MatterListResponse(
        items=[MatterResponse.model_validate(m) for m in items],
        total=total,
    )


@router.post("", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
def create_matter(
    data: MatterCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> MatterResponse:
    """Create a new legal matter."""
    matter = service.create_matter(db, data, creator_id=current_user.id)
    return MatterResponse.model_validate(matter)


@router.get("/{matter_id}", response_model=MatterResponse)
def get_matter(
    matter_id: str,
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_access),
) -> MatterResponse:
    """Get single matter details. Requires membership."""
    matter = service.get_matter(db, matter_id)
    return MatterResponse.model_validate(matter)


@router.post(
    "/{matter_id}/members",
    response_model=MatterMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    matter_id: str,
    data: MatterMemberCreate,
    db: Session = Depends(get_db),
    member: MatterMember = Depends(require_matter_write),
) -> MatterMemberResponse:
    """Add a user as a member to this matter. Requires membership."""
    created_member = service.add_matter_member(
        db, matter_id=matter_id, user_id=data.user_id, role=data.role
    )
    return MatterMemberResponse.model_validate(created_member)
