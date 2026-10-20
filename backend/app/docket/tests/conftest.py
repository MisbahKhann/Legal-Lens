"""
Pytest fixtures for Docket test suite.
Configures isolated in-memory SQLite, FastAPI test client, and seeded test matters.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.audit.router import router as audit_router
from app.core.database import Base, get_db
from app.core.models import Matter, MatterMember
from app.core.router import router as core_router
from app.docket.router import docket_router, notifications_router

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False
)


@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated database session with full schema and DDL triggers."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        # Seed standard primary matter
        m1 = Matter(
            id="matter-test-1",
            name="Primary Litigation Matter",
            case_number="CV-2026-100",
            client_name="Acme Corp",
            status="active",
        )
        mem1 = MatterMember(
            id="mem-1",
            matter_id="matter-test-1",
            user_id="user-attorney",
            role="attorney",
        )
        mem2 = MatterMember(
            id="mem-2",
            matter_id="matter-test-1",
            user_id="user-owner",
            role="owner",
        )
        mem3 = MatterMember(
            id="mem-3",
            matter_id="matter-test-1",
            user_id="user-viewer",
            role="viewer",
        )

        # Seed secondary matter for isolation tests
        m2 = Matter(
            id="matter-test-2",
            name="Isolated Matter",
            case_number="CV-2026-200",
            client_name="Other Client",
            status="active",
        )
        mem4 = MatterMember(
            id="mem-4",
            matter_id="matter-test-2",
            user_id="user-other",
            role="attorney",
        )

        session.add_all([m1, mem1, mem2, mem3, m2, mem4])
        session.commit()

        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient with dependency overrides."""
    test_app = FastAPI()
    test_app.include_router(core_router, prefix="/api/v1")
    test_app.include_router(audit_router, prefix="/api/v1")
    test_app.include_router(docket_router, prefix="/api/v1")
    test_app.include_router(notifications_router, prefix="/api/v1")

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()
