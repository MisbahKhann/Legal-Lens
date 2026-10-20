"""
Pydantic schemas for core models (Matter, MatterMember, CurrentUser).
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CurrentUser(BaseModel):
    """Authenticated user context (role is scoped per-matter, not global)."""

    id: str
    email: Optional[str] = None


class MatterMemberBase(BaseModel):
    user_id: str
    role: str = "attorney"


class MatterMemberCreate(MatterMemberBase):
    pass


class MatterMemberResponse(MatterMemberBase):
    id: str
    matter_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatterBase(BaseModel):
    name: str = Field(..., max_length=255)
    case_number: str = Field(..., max_length=100)
    client_name: str = Field(..., max_length=255)
    status: str = "active"


class MatterCreate(MatterBase):
    pass


class MatterUpdate(BaseModel):
    name: Optional[str] = None
    case_number: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None


class MatterResponse(MatterBase):
    id: str
    created_at: datetime
    updated_at: datetime
    members: Optional[List[MatterMemberResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class MatterListResponse(BaseModel):
    items: List[MatterResponse]
    total: int
