"""
Service layer for Matter management and memberships.
"""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.models import Matter, MatterMember
from app.core.schemas import MatterCreate, MatterUpdate


def create_matter(
    db: Session,
    data: MatterCreate,
    creator_id: str,
) -> Matter:
    """Create a new matter and automatically assign the creator as owner."""
    matter_id = str(uuid.uuid4())
    matter = Matter(
        id=matter_id,
        name=data.name,
        case_number=data.case_number,
        client_name=data.client_name,
        status=data.status,
    )
    db.add(matter)

    # Automatically add creator as owner
    owner_member = MatterMember(
        id=str(uuid.uuid4()),
        matter_id=matter_id,
        user_id=creator_id,
        role="owner",
    )
    db.add(owner_member)
    db.commit()
    db.refresh(matter)
    return matter


def get_matter(db: Session, matter_id: str) -> Optional[Matter]:
    """Retrieve a single matter by id."""
    return db.scalar(select(Matter).where(Matter.id == matter_id))


def list_user_matters(
    db: Session,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Matter], int]:
    """List matters that the specified user has access to with pagination."""
    query = (
        select(Matter)
        .join(MatterMember, Matter.id == MatterMember.matter_id)
        .where(MatterMember.user_id == user_id)
        .order_by(Matter.created_at.desc())
    )
    total = (
        db.scalar(
            select(func.count(Matter.id))
            .join(MatterMember, Matter.id == MatterMember.matter_id)
            .where(MatterMember.user_id == user_id)
        )
        or 0
    )

    items = list(db.scalars(query.offset(offset).limit(limit)).all())
    return items, total


def update_matter(
    db: Session,
    matter_id: str,
    data: MatterUpdate,
) -> Optional[Matter]:
    """Update matter metadata."""
    matter = get_matter(db, matter_id)
    if not matter:
        return None

    if data.name is not None:
        matter.name = data.name
    if data.case_number is not None:
        matter.case_number = data.case_number
    if data.client_name is not None:
        matter.client_name = data.client_name
    if data.status is not None:
        matter.status = data.status

    db.commit()
    db.refresh(matter)
    return matter


def add_matter_member(
    db: Session,
    matter_id: str,
    user_id: str,
    role: str = "attorney",
) -> MatterMember:
    """Add or update a matter member."""
    existing = db.scalar(
        select(MatterMember).where(
            MatterMember.matter_id == matter_id,
            MatterMember.user_id == user_id,
        )
    )
    if existing:
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    member = MatterMember(
        id=str(uuid.uuid4()),
        matter_id=matter_id,
        user_id=user_id,
        role=role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
