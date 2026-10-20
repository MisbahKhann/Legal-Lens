"""
API v1 Router Aggregator and Application Lifespan.
Combines core, audit, and docket routers into a single mountable router.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import APIRouter, FastAPI

from app.audit.router import router as audit_router
from app.core.config import settings
from app.core.router import router as core_router
from app.docket.router import docket_router, notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Validates auth environment and initializes background scheduler.
    """
    from app.core.auth import verify_auth_environment

    verify_auth_environment()

    stop_func = None

    if settings.SCHEDULER_ENABLED:
        try:
            from app.docket.scheduler import (
                start_scheduler,
                stop_scheduler,
            )

            scheduler = start_scheduler()
            stop_func = stop_scheduler
        except ImportError:
            scheduler = None
    yield
    if scheduler and stop_func:
        try:
            stop_func()
        except Exception:
            pass


api_v1_router = APIRouter()

# Mount core matters router
api_v1_router.include_router(core_router)

# Mount audit router
api_v1_router.include_router(audit_router)

# Mount docket routers
api_v1_router.include_router(docket_router)
api_v1_router.include_router(notifications_router)
