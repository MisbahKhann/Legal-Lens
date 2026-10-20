"""
Unit and integration tests for Matter multi-tenancy and access isolation.
Verifies that users can never read, query, or mutate matters they are not members of.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.models import MatterMember
from app.core.router import router as core_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(core_router, prefix="/api/v1")

# In-memory SQLite for test isolation
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
    """Provides a clean in-memory database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient with database session dependency overridden."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_matter_creation_and_ownership(client, db_session):
    """Test creating a matter assigns creator as owner."""
    response = client.post(
        "/api/v1/matters",
        headers={"X-User-Id": "attorney-1"},
        json={
            "name": "Doe v. State",
            "case_number": "CV-2026-0001",
            "client_name": "John Doe",
            "status": "active",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Doe v. State"
    matter_id = data["id"]

    # Verify membership table
    member = (
        db_session.query(MatterMember)
        .filter_by(matter_id=matter_id, user_id="attorney-1")
        .first()
    )
    assert member is not None
    assert member.role == "owner"


def test_matter_isolation_list(client, db_session):
    """Test that list endpoint only returns matters user is a member of."""
    # Create Matter 1 for User A
    res1 = client.post(
        "/api/v1/matters",
        headers={"X-User-Id": "user-a"},
        json={
            "name": "Matter Alpha",
            "case_number": "A-1",
            "client_name": "Client A",
            "status": "active",
        },
    )
    assert res1.status_code == 201
    matter_a_id = res1.json()["id"]

    # Create Matter 2 for User B
    res2 = client.post(
        "/api/v1/matters",
        headers={"X-User-Id": "user-b"},
        json={
            "name": "Matter Beta",
            "case_number": "B-1",
            "client_name": "Client B",
            "status": "active",
        },
    )
    assert res2.status_code == 201
    matter_b_id = res2.json()["id"]

    # User A queries matters
    list_a = client.get("/api/v1/matters", headers={"X-User-Id": "user-a"})
    assert list_a.status_code == 200
    items_a = list_a.json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["id"] == matter_a_id

    # User B queries matters
    list_b = client.get("/api/v1/matters", headers={"X-User-Id": "user-b"})
    assert list_b.status_code == 200
    items_b = list_b.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["id"] == matter_b_id

    # User C (no matters) queries
    list_c = client.get("/api/v1/matters", headers={"X-User-Id": "user-c"})
    assert list_c.status_code == 200
    assert len(list_c.json()["items"]) == 0


def test_matter_access_control_403_for_non_members(client):
    """Test non-members receive 403 Forbidden when requesting matter details."""
    # Create matter as user-a
    create_res = client.post(
        "/api/v1/matters",
        headers={"X-User-Id": "user-a"},
        json={
            "name": "Confidential Matter",
            "case_number": "CONF-99",
            "client_name": "Secret Client",
            "status": "active",
        },
    )
    matter_id = create_res.json()["id"]

    # user-a can access
    res_a = client.get(f"/api/v1/matters/{matter_id}", headers={"X-User-Id": "user-a"})
    assert res_a.status_code == 200

    # user-intruder receives 403 Forbidden
    res_intruder = client.get(
        f"/api/v1/matters/{matter_id}", headers={"X-User-Id": "user-intruder"}
    )
    assert res_intruder.status_code == 403
    assert "not a member" in res_intruder.json()["detail"]


def test_matter_not_found_404(client):
    """Test non-existent matter returns 404 Not Found."""
    res = client.get("/api/v1/matters/non-existent-id", headers={"X-User-Id": "user-a"})
    assert res.status_code == 404


def test_role_enforcement_and_ignored_role_header(client, db_session):
    """
    Verifies:
    1. X-User-Role header is completely ignored; role comes strictly from
       matter_members.
    2. Viewers cannot add members or perform mutations (403 Forbidden).
    """
    from app.core.models import Matter, MatterMember

    matter = Matter(
        id="matter-role-test",
        name="Role Test Matter",
        case_number="R-1",
        client_name="Client R",
        status="active",
    )
    viewer_member = MatterMember(
        id="mem-viewer",
        matter_id="matter-role-test",
        user_id="user-viewer",
        role="viewer",
    )
    db_session.add_all([matter, viewer_member])
    db_session.commit()

    # User attempts to spoof role as 'owner' via X-User-Role header
    res_spoof = client.post(
        "/api/v1/matters/matter-role-test/members",
        headers={"X-User-Id": "user-viewer", "X-User-Role": "owner"},
        json={"user_id": "user-new", "role": "attorney"},
    )
    assert res_spoof.status_code == 403
    assert "Viewers have read-only access" in res_spoof.json()["detail"]


def test_production_env_refuses_header_auth():
    """Startup check raises RuntimeError when ENV is production."""
    from app.core.config import settings
    from app.core.auth import verify_auth_environment

    old_env = settings.ENV
    try:
        settings.ENV = "production"
        with pytest.raises(RuntimeError) as exc_info:
            verify_auth_environment()
        assert "Development header-based authentication is strictly prohibited" in str(
            exc_info.value
        )
    finally:
        settings.ENV = old_env
