"""
NotificationChannel interface and implementations.
Provides in-app database persistence and stub email delivery channel.
"""

import abc
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.docket.models import Notification

logger = logging.getLogger(__name__)


class NotificationChannel(abc.ABC):
    """Abstract notification delivery channel."""

    @abc.abstractmethod
    def send(
        self,
        db: Session,
        matter_id: str,
        user_id: str,
        event_id: str,
        title: str,
        message: str,
        notification_type: str,
        reminder_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """Dispatch notification across this channel."""
        pass


class InAppNotificationChannel(NotificationChannel):
    """Persists in-app notifications into the database."""

    def send(
        self,
        db: Session,
        matter_id: str,
        user_id: str,
        event_id: str,
        title: str,
        message: str,
        notification_type: str,
        reminder_id: Optional[str] = None,
    ) -> Notification:
        notification = Notification(
            id=str(uuid.uuid4()),
            matter_id=matter_id,
            user_id=user_id,
            event_id=event_id,
            reminder_id=reminder_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(notification)
        db.flush()
        return notification


class StubEmailNotificationChannel(NotificationChannel):
    """Simulates email delivery for testing and local dev."""

    def send(
        self,
        db: Session,
        matter_id: str,
        user_id: str,
        event_id: str,
        title: str,
        message: str,
        notification_type: str,
        reminder_id: Optional[str] = None,
    ) -> None:
        logger.info(
            "[STUB EMAIL] To: %s | Title: %s | Type: %s | Event: %s",
            user_id,
            title,
            notification_type,
            event_id,
        )
        return None
