"""
Matter and MatterMember ORM models.
"""

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UTCDateTime


class Matter(Base):
    """Legal Matter entity for multi-tenancy and data isolation."""

    __tablename__ = "matters"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'closed', 'archived')",
            name="ck_matter_status",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    case_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

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

    members: Mapped[List["MatterMember"]] = relationship(
        "MatterMember",
        back_populates="matter",
        cascade="all, delete-orphan",
    )


class MatterMember(Base):
    """Membership mapping defining user access and role within a matter."""

    __tablename__ = "matter_members"
    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'attorney', 'paralegal', 'viewer')",
            name="ck_matter_member_role",
        ),
        UniqueConstraint("matter_id", "user_id", name="uq_matter_member"),
        Index("ix_matter_member_matter_user", "matter_id", "user_id"),
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
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="attorney")

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    matter: Mapped["Matter"] = relationship("Matter", back_populates="members")
