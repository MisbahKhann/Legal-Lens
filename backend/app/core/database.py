"""
Database engine, session management, and custom UTC datetime decorator.
"""

from datetime import datetime, timezone
from typing import Generator, Optional, Any

from sqlalchemy import DateTime, TypeDecorator, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class UTCDateTime(TypeDecorator):
    """
    Ensures datetimes are stored as naive UTC in DB and returned as UTC-aware.
    Protects against SQLite dropping timezone metadata while maintaining
    Postgres compatibility.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: Optional[datetime], dialect: Any
    ) -> Optional[datetime]:
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
            return value.replace(tzinfo=None)
        return value

    def process_result_value(
        self, value: Optional[datetime], dialect: Any
    ) -> Optional[datetime]:
        if value is not None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.x models."""

    pass


# Connect arguments: SQLite requires check_same_thread=False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """Enforce foreign key constraints on SQLite connections."""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
