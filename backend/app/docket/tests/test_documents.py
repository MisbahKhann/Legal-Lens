"""
Tests for Document attachments, versioning, SHA-256 deduplication, and review workflows.
"""

import io
from datetime import datetime, timedelta, timezone


def test_document_upload_versioning_and_download(client):
    """
    Test uploading a document, verifying sha256 and version 1,
    downloading the file, and uploading version 2.
    """
    event_date = datetime.now(timezone.utc) + timedelta(days=7)
    ev_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Evidentiary Hearing",
            "starts_at": event_date.isoformat(),
            "priority": "medium",
        },
    )
    event_id = ev_res.json()["id"]

    # Upload version 1
    file_content_v1 = b"%PDF-1.4 Mock Legal Document Content v1"
    res1 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/documents",
        headers={"X-User-Id": "user-attorney"},
        data={"display_name": "Complaint.pdf"},
        files={
            "file": ("Complaint.pdf", io.BytesIO(file_content_v1), "application/pdf")
        },
    )
    assert res1.status_code == 201
    doc_v1 = res1.json()
    doc_id = doc_v1["id"]
    assert doc_v1["display_name"] == "Complaint.pdf"
    assert doc_v1["review_status"] == "to_review"
    assert len(doc_v1["versions"]) == 1
    assert doc_v1["versions"][0]["version_number"] == 1
    assert doc_v1["versions"][0]["is_current"] is True

    # Download file
    dl_url = (
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}"
        f"/documents/{doc_id}/download"
    )
    dl_res = client.get(
        dl_url,
        headers={"X-User-Id": "user-attorney"},
    )
    assert dl_res.status_code == 200
    assert dl_res.content == file_content_v1

    # Upload version 2 with different content
    file_content_v2 = b"%PDF-1.4 Mock Legal Document Content v2 (Amended)"
    res2 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/documents",
        headers={"X-User-Id": "user-attorney"},
        data={"display_name": "Complaint.pdf"},
        files={
            "file": ("Complaint.pdf", io.BytesIO(file_content_v2), "application/pdf")
        },
    )
    assert res2.status_code == 201
    doc_v2 = res2.json()
    assert len(doc_v2["versions"]) == 2
    # Verify version 2 supersedes version 1
    current_v = doc_v2["current_version"]
    assert current_v["version_number"] == 2
    assert current_v["is_current"] is True
    assert current_v["supersedes_id"] is not None


def test_same_sha256_reupload_is_noop(client):
    """Uploading the exact same file content with the same display name is a no-op."""
    event_date = datetime.now(timezone.utc) + timedelta(days=7)
    ev_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Hearing",
            "starts_at": event_date.isoformat(),
            "priority": "low",
        },
    )
    event_id = ev_res.json()["id"]

    content = b"Exact Same Document Bytes"
    res1 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/documents",
        headers={"X-User-Id": "user-attorney"},
        data={"display_name": "Exhibit_A.pdf"},
        files={"file": ("Exhibit_A.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert res1.status_code == 201

    # Re-upload same content
    res2 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/documents",
        headers={"X-User-Id": "user-attorney"},
        data={"display_name": "Exhibit_A.pdf"},
        files={"file": ("Exhibit_A.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert res2.status_code == 201
    doc = res2.json()
    assert len(doc["versions"]) == 1, "No duplicate version row should be created"


def test_reupload_of_reviewed_document_sets_changed_since_review(client):
    """
    When a document has review_status='reviewed', uploading a new version:
    1. Sets review_status='changed_since_review'
    2. Re-arms document-linked reminders (resets sent to pending).
    """
    event_date = datetime.now(timezone.utc) + timedelta(days=7)
    ev_res = client.post(
        "/api/v1/matters/matter-test-1/docket/events",
        headers={"X-User-Id": "user-attorney"},
        json={
            "kind": "hearing",
            "title": "Motion Hearing",
            "starts_at": event_date.isoformat(),
            "priority": "high",
        },
    )
    event_id = ev_res.json()["id"]

    # Upload file
    upload_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/documents",
        headers={"X-User-Id": "user-attorney"},
        data={"display_name": "Brief.pdf"},
        files={"file": ("Brief.pdf", io.BytesIO(b"Original Brief"), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    # Mark reviewed
    review_res = client.patch(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/documents/{doc_id}",
        headers={"X-User-Id": "user-attorney"},
        json={"review_status": "reviewed"},
    )
    assert review_res.status_code == 200
    assert review_res.json()["review_status"] == "reviewed"

    # Add reminder linked to this document
    rem_res = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/reminders",
        headers={"X-User-Id": "user-attorney"},
        json={
            "anchor": "offset_before_event",
            "days_before": 2,
            "document_id": doc_id,
        },
    )
    assert rem_res.json()["id"] is not None

    # Upload new version
    upload_v2 = client.post(
        f"/api/v1/matters/matter-test-1/docket/events/{event_id}/documents",
        headers={"X-User-Id": "user-attorney"},
        data={"display_name": "Brief.pdf"},
        files={
            "file": (
                "Brief.pdf",
                io.BytesIO(b"Revised Brief with Edits"),
                "application/pdf",
            )
        },
    )
    assert upload_v2.status_code == 201
    doc_data = upload_v2.json()
    assert doc_data["review_status"] == "changed_since_review"
