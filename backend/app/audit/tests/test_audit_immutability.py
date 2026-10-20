"""
Tests for Audit Log Immutability and Transaction Semantics.
Verifies append-only enforcement via DB triggers and non-committing
record_event behavior.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.audit.models import AuditLog
from app.audit.router import router as audit_router
from app.audit.service import record_event
from app.core.database import Base, get_db
from app.core.models import Matter, MatterMember
from app.core.router import router as core_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(core_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")

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
    """Clean isolated DB session with audit triggers enabled."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with dependency overrides."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_record_event_caller_transaction_semantics(db_session):
    """
    Verifies that record_event does NOT commit itself.
    If the caller's transaction rolls back, the audit log must be rolled back too.
    """
    matter = Matter(
        id="matter-txn-test",
        name="Txn Test Matter",
        case_number="TXN-1",
        client_name="Client Txn",
        status="active",
    )
    db_session.add(matter)
    db_session.commit()

    # Step 1: record event in uncommitted transaction, then roll back
    record_event(
        db=db_session,
        matter_id="matter-txn-test",
        actor="attorney-1",
        action="test_action",
        target_type="event",
        target_id="event-1",
        reason="will rollback",
    )
    db_session.rollback()

    logs = db_session.query(AuditLog).filter_by(matter_id="matter-txn-test").all()
    assert len(logs) == 0, "Audit log should have been rolled back"

    # Step 2: record event and commit
    record_event(
        db=db_session,
        matter_id="matter-txn-test",
        actor="attorney-1",
        action="test_action",
        target_type="event",
        target_id="event-1",
        reason="will commit",
    )
    db_session.commit()

    logs_after = db_session.query(AuditLog).filter_by(matter_id="matter-txn-test").all()
    assert len(logs_after) == 1
    assert logs_after[0].reason == "will commit"


def test_audit_logs_trigger_blocks_update(db_session):
    """Verifies that DB trigger prohibits UPDATE on audit_logs."""
    matter = Matter(
        id="matter-trg-test",
        name="Trigger Test Matter",
        case_number="TRG-1",
        client_name="Client Trigger",
        status="active",
    )
    db_session.add(matter)
    db_session.commit()

    entry = record_event(
        db=db_session,
        matter_id="matter-trg-test",
        actor="attorney-1",
        action="create",
        target_type="event",
        target_id="event-target-1",
    )
    db_session.commit()

    # Attempt direct SQL UPDATE on the audit entry
    with pytest.raises(DBAPIError) as exc_info:
        db_session.execute(
            text(
                f"UPDATE audit_logs SET actor = 'tampered_user' WHERE id = '{entry.id}'"
            )
        )
        db_session.commit()

    assert "Updates prohibited on append-only audit_logs" in str(exc_info.value)
    db_session.rollback()


def test_audit_logs_trigger_blocks_delete(db_session):
    """Verifies that DB trigger prohibits DELETE on audit_logs."""
    matter = Matter(
        id="matter-del-test",
        name="Delete Test Matter",
        case_number="DEL-1",
        client_name="Client Del",
        status="active",
    )
    db_session.add(matter)
    db_session.commit()

    entry = record_event(
        db=db_session,
        matter_id="matter-del-test",
        actor="attorney-1",
        action="create",
        target_type="event",
        target_id="event-target-2",
    )
    db_session.commit()

    # Attempt direct SQL DELETE on the audit entry
    with pytest.raises(DBAPIError) as exc_info:
        db_session.execute(text(f"DELETE FROM audit_logs WHERE id = '{entry.id}'"))
        db_session.commit()

    assert "Deletions prohibited on append-only audit_logs" in str(exc_info.value)
    db_session.rollback()


def test_audit_api_endpoint_isolation_and_pagination(client, db_session):
    """Tests audit log API endpoint enforces matter membership and pagination."""
    # Create Matter 1 with member user-1
    matter1 = Matter(
        id="matter-aud-1",
        name="Matter 1",
        case_number="M-1",
        client_name="C-1",
        status="active",
    )
    member1 = MatterMember(
        id="mem-1", matter_id="matter-aud-1", user_id="user-1", role="owner"
    )
    db_session.add_all([matter1, member1])
    db_session.commit()

    # Record 3 events for Matter 1
    for i in range(3):
        record_event(
            db=db_session,
            matter_id="matter-aud-1",
            actor="user-1",
            action=f"action_{i}",
            target_type="event",
            target_id=f"target-{i}",
        )
    db_session.commit()

    # User 1 requests audit logs (page 1, limit 2)
    res_page1 = client.get(
        "/api/v1/matters/matter-aud-1/audit?limit=2&offset=0",
        headers={"X-User-Id": "user-1"},
    )
    assert res_page1.status_code == 200
    data1 = res_page1.json()
    assert data1["total"] == 3
    assert len(data1["items"]) == 2

    # User 1 requests page 2
    res_page2 = client.get(
        "/api/v1/matters/matter-aud-1/audit?limit=2&offset=2",
        headers={"X-User-Id": "user-1"},
    )
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert len(data2["items"]) == 1

    # Unauthorized User (non-member) gets 403 Forbidden
    res_unauth = client.get(
        "/api/v1/matters/matter-aud-1/audit",
        headers={"X-User-Id": "user-unauthorized"},
    )
    assert res_unauth.status_code == 403

    # Add paralegal member
    paralegal = MatterMember(
        id="mem-para", matter_id="matter-aud-1", user_id="user-para", role="paralegal"
    )
    db_session.add(paralegal)
    db_session.commit()

    # Paralegal gets 403 Forbidden on audit listing (owner/attorney only)
    res_para = client.get(
        "/api/v1/matters/matter-aud-1/audit",
        headers={"X-User-Id": "user-para"},
    )
    assert res_para.status_code == 403
    assert "Audit trail access requires owner or attorney" in res_para.json()["detail"]
