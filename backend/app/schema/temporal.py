"""
Temporal data models and status enums for event and time tracking.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class EventStatus(str, Enum):
    """Execution or compliance status for legal events, deadlines, and hearings."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    UPCOMING = "UPCOMING"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    ONGOING = "ONGOING"


class TemporalProperties(BaseModel):
    """
    Temporal tracking model for nodes (EVENT, HEARING, DEADLINE, DATE) or relationships.
    """
    event_date: Optional[datetime] = Field(
        default=None,
        description="Exact date and time of the event occurrence."
    )
    start_date: Optional[datetime] = Field(
        default=None,
        description="Start date/time for multi-day events, hearings, or period constraints."
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="End date/time for multi-day events, hearings, or period constraints."
    )
    deadline: Optional[datetime] = Field(
        default=None,
        description="Mandatory due date/time associated with a filing or procedural step."
    )
    status: Optional[EventStatus] = Field(
        default=EventStatus.PENDING,
        description="Current status of the temporal event or deadline."
    )

    @model_validator(mode="after")
    def validate_date_coherence(self) -> "TemporalProperties":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError(
                    f"start_date ({self.start_date.isoformat()}) cannot be later than end_date ({self.end_date.isoformat()})"
                )
        return self

    def check_is_overdue(self, reference_time: Optional[datetime] = None) -> bool:
        """Determines if a deadline is overdue relative to reference_time (default now UTC)."""
        if self.deadline is None or self.status == EventStatus.COMPLETED:
            return False
        ref = reference_time or datetime.now(timezone.utc)
        return ref > self.deadline
