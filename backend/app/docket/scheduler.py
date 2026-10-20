"""
APScheduler background runner for Docket reminder dispatching.
Executes once every 60 seconds with idempotency guarantees.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.background import (  # type: ignore[import-untyped]
    BackgroundScheduler,
)

from app.core.config import settings
from app.core.database import SessionLocal
from app.docket.service import process_due_reminders

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def run_scheduler_tick() -> None:
    """Invoked every minute by background scheduler."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        count = process_due_reminders(db, now)
        if count > 0:
            logger.info("Scheduler processed %d due reminders.", count)
    except Exception as exc:
        logger.error("Error in scheduler tick: %s", exc, exc_info=True)
    finally:
        db.close()


def start_scheduler() -> Optional[BackgroundScheduler]:
    """Starts the background scheduler if enabled."""
    global _scheduler
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled via SCHEDULER_ENABLED=False.")
        return None

    if _scheduler is None or not _scheduler.running:
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            run_scheduler_tick,
            "interval",
            minutes=1,
            id="docket_reminder_tick",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info("Docket background scheduler started.")
    return _scheduler


def stop_scheduler() -> None:
    """Stops the background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Docket background scheduler stopped.")
        _scheduler = None
