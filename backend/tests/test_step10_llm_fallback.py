"""
Focused Step 10 Test Suite: Local LLM Fallback & Ambiguous Extraction Resolution.
Tests configuration loading, provider error handling, ontology validation, confidence thresholds,
provenance preservation, Step 6 validation integration, and Step 9 human review escalation using mocked LLM responses.

STRICT INSTRUCTION: NO REAL OLLAMA INFERENCE IS EXECUTED IN THESE TESTS.
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch

from app.llm.config import LLMConfig, get_llm_config
from app.llm.models import (
    LLMFallbackRequest,
    LLMFallbackResponse,
    LLMDecision,
    AmbiguityType,
)
from app.llm.provider import LLMProvider, OllamaProvider
from app.llm.service import LLMFallbackService
from app.review.manager import ReviewManager
from app.review.models import ItemType, ReviewStatus
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType


# ---------------------------------------------------------------------------
# Test 1: Ollama Configuration Loading
# ---------------------------------------------------------------------------
def test_ollama_config_loading(monkeypatch):
    """Test reading configuration values from environment variables and defaults."""
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    monkeypatch.setenv("LLM_HIGH_CONFIDENCE_THRESHOLD", "0.85")

    config = get_llm_config()
    assert config.provider == "ollama"
    assert config.ollama_base_url == "http://localhost:11434"
    assert config.ollama_model == "qwen2.5:1.5b"
    assert config.high_confidence_threshold == 0.85

    # Test default model fallback when OLLAMA_MODEL is unset
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    config_default = get_llm_config()
    assert config_default.ollama_model == "qwen2.5:1.5b"


# ---------------------------------------------------------------------------
# Test 2: Successful Local LLM Response (Mocked)
# ---------------------------------------------------------------------------
def test_successful_llm_response_mocked():
    """Test parsing a valid structured JSON response from local LLM provider."""
    mock_llm_json = json.dumps(
        {
            "decision": "RESOLVED",
            "selected_entity_type": "PLAINTIFF",
            "selected_entity_name": "Acme Corporation",
            "confidence": 0.92,
            "reasoning": "Text explicitly identifies Acme Corporation as the plaintiff filing the complaint.",
            "needs_human_review": False,
        }
    )

    request = LLMFallbackRequest(
        case_id="case_101",
        source_document_id="doc_complaint.pdf",
        source_page=1,
        source_text="Acme Corporation filed a complaint against Beta LLC in District Court.",
        ambiguity_type=AmbiguityType.ENTITY_TYPE,
        allowed_entity_types=["PLAINTIFF", "DEFENDANT", "CORPORATION"],
        candidate_entities=[{"text": "Acme Corporation", "type": "PARTY"}],
    )

    provider = OllamaProvider()
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(
            {"response": mock_llm_json}
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = provider.generate_resolution(request)
        assert res.decision == LLMDecision.RESOLVED
        assert res.selected_entity_type == "PLAINTIFF"
        assert res.selected_entity_name == "Acme Corporation"
        assert res.confidence == 0.92
        assert res.needs_human_review is False


# ---------------------------------------------------------------------------
# Test 3: Ollama Unavailable (Connection Error Handling)
# ---------------------------------------------------------------------------
def test_ollama_unavailable_graceful_fallback():
    """Test graceful fallback response when Ollama HTTP server is unreachable."""
    request = LLMFallbackRequest(
        case_id="case_102",
        source_document_id="doc_test.pdf",
        source_text="Unresolved ambiguity context snippet.",
        ambiguity_type=AmbiguityType.UNRESOLVED_REFERENCE,
    )

    provider = OllamaProvider()
    with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
        res = provider.generate_resolution(request)
        assert res.decision == LLMDecision.UNCERTAIN
        assert res.confidence == 0.0
        assert res.needs_human_review is True
        assert (
            "unavailable" in res.reasoning.lower() or "error" in res.reasoning.lower()
        )


# ---------------------------------------------------------------------------
# Test 4: Malformed LLM Response Handling
# ---------------------------------------------------------------------------
def test_malformed_llm_response_handling():
    """Test handling of invalid JSON text returned by LLM model."""
    request = LLMFallbackRequest(
        case_id="case_103",
        source_document_id="doc_test.pdf",
        source_text="Ambiguous text.",
        ambiguity_type=AmbiguityType.ENTITY_TYPE,
    )

    provider = OllamaProvider()
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(
            {"response": "Not valid JSON output..."}
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = provider.generate_resolution(request)
        assert res.decision == LLMDecision.UNCERTAIN
        assert res.needs_human_review is True
        assert "malformed" in res.reasoning.lower() or "json" in res.reasoning.lower()


# ---------------------------------------------------------------------------
# Test 5: Invalid Ontology Returned by LLM (Rejected & Escalated)
# ---------------------------------------------------------------------------
def test_invalid_ontology_returned_by_llm():
    """Test that arbitrary AI-invented entity types are rejected by SchemaValidator."""
    mock_invalid_json = json.dumps(
        {
            "decision": "RESOLVED",
            "selected_entity_type": "INVALID_FAKETYPE_99",  # Not in Step 1 EntityType
            "selected_entity_name": "John Doe",
            "confidence": 0.95,
            "reasoning": "Assigned fake type.",
            "needs_human_review": False,
        }
    )

    request = LLMFallbackRequest(
        case_id="case_104",
        source_document_id="doc_test.pdf",
        source_text="John Doe appeared.",
        ambiguity_type=AmbiguityType.ENTITY_TYPE,
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.RESOLVED,
        selected_entity_type="INVALID_FAKETYPE_99",
        selected_entity_name="John Doe",
        confidence=0.95,
        reasoning="Assigned fake type.",
        needs_human_review=False,
    )

    review_mgr = ReviewManager()
    service = LLMFallbackService(provider=mock_provider, review_manager=review_mgr)

    res = service.resolve_ambiguity(request)
    assert res.decision == LLMDecision.REJECTED
    assert res.confidence == 0.0
    assert res.needs_human_review is True
    assert "validation rejected" in res.reasoning.lower()

    # Verify item was escalated to Step 9 review manager
    items = review_mgr.get_review_items_for_case("case_104")
    assert len(items) == 1
    assert items[0].status == ReviewStatus.PENDING


# ---------------------------------------------------------------------------
# Test 6: High-Confidence LLM Result Decision Flow
# ---------------------------------------------------------------------------
def test_high_confidence_llm_result():
    """Test that valid high-confidence LLM output passes without requiring human review."""
    request = LLMFallbackRequest(
        case_id="case_105",
        source_document_id="doc_test.pdf",
        source_text="The Supreme Court of Pakistan issued an order.",
        ambiguity_type=AmbiguityType.ENTITY_TYPE,
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.RESOLVED,
        selected_entity_type="COURT",
        selected_entity_name="Supreme Court of Pakistan",
        confidence=0.95,
        reasoning="Text specifies Pakistan Supreme Court.",
        needs_human_review=False,
    )

    review_mgr = ReviewManager()
    service = LLMFallbackService(provider=mock_provider, review_manager=review_mgr)

    res = service.resolve_ambiguity(request)
    assert res.decision == LLMDecision.RESOLVED
    assert res.confidence == 0.95
    assert res.needs_human_review is False


# ---------------------------------------------------------------------------
# Test 7: Uncertain LLM Result -> Human Review Escalation
# ---------------------------------------------------------------------------
def test_uncertain_llm_result_escalation():
    """Test that medium or uncertain LLM confidence triggers Step 9 human review creation."""
    request = LLMFallbackRequest(
        case_id="case_106",
        source_document_id="doc_test.pdf",
        source_text="The party might be a guarantor or a witness.",
        ambiguity_type=AmbiguityType.ENTITY_TYPE,
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.RESOLVED,
        selected_entity_type="WITNESS",
        selected_entity_name="John Smith",
        confidence=0.60,  # Below high threshold 0.85
        reasoning="Ambiguous context, weak indicator.",
        needs_human_review=True,
    )

    review_mgr = ReviewManager()
    service = LLMFallbackService(provider=mock_provider, review_manager=review_mgr)

    res = service.resolve_ambiguity(request)
    assert res.needs_human_review is True

    review_items = review_mgr.get_review_items_for_case("case_106")
    assert len(review_items) == 1
    item = review_items[0]
    assert item.status == ReviewStatus.PENDING
    assert item.case_id == "case_106"
    assert item.confidence == 0.60


# ---------------------------------------------------------------------------
# Test 8: Provenance Preservation
# ---------------------------------------------------------------------------
def test_provenance_preservation():
    """Test that LLM-assisted predictions preserve complete provenance metadata."""
    request = LLMFallbackRequest(
        case_id="case_107",
        source_document_id="doc_license_agreement.pdf",
        source_page=4,
        source_text="ABC Ltd granted an exclusive license to XYZ Inc.",
        char_span=(10, 50),
        ambiguity_type=AmbiguityType.RELATIONSHIP_TYPE,
        original_extraction_method="GLINER_RELEX",
        candidate_relationships=[
            {
                "source": "ABC Ltd",
                "source_type": "PARTY",
                "relation": "GRANTED_LICENSE",
                "target": "XYZ Inc",
                "target_type": "PARTY",
            }
        ],
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.UNCERTAIN,
        confidence=0.40,
        reasoning="Relationship ambiguity requires human verification.",
        needs_human_review=True,
    )

    review_mgr = ReviewManager()
    service = LLMFallbackService(provider=mock_provider, review_manager=review_mgr)

    service.resolve_ambiguity(request)
    review_items = review_mgr.get_review_items_for_case("case_107")
    assert len(review_items) == 1
    item = review_items[0]

    # Check provenance details
    details = item.provenance_details
    assert details.get("llm_assisted") is True
    assert details.get("llm_provider") == "ollama"
    assert details.get("llm_model") == "qwen2.5:1.5b"
    assert "original_candidates" in details
    assert item.source_document_id == "doc_license_agreement.pdf"
    assert item.source_page == 4
    assert item.source_span == (10, 50)


# ---------------------------------------------------------------------------
# Test 9: Original Extraction Preservation (Never Overwritten)
# ---------------------------------------------------------------------------
def test_original_extraction_preservation():
    """Test that original candidate extraction payload is stored untouched in review item."""
    orig_candidates = [{"text": "Original Rule Candidate", "type": "UNKNOWN"}]
    request = LLMFallbackRequest(
        case_id="case_108",
        source_document_id="doc_orig.pdf",
        source_text="Original text snippet.",
        ambiguity_type=AmbiguityType.CONFLICTING_EXTRACTION,
        original_extraction_method="DETERMINISTIC_RULE",
        candidate_entities=orig_candidates,
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.UNCERTAIN,
        confidence=0.30,
        reasoning="Low confidence.",
        needs_human_review=True,
    )

    review_mgr = ReviewManager()
    service = LLMFallbackService(provider=mock_provider, review_manager=review_mgr)

    service.resolve_ambiguity(request)
    item = review_mgr.get_review_items_for_case("case_108")[0]
    orig_pred = item.original_prediction

    assert orig_pred.get("original_extraction_method") == "DETERMINISTIC_RULE"
    assert orig_pred.get("candidate_entities") == orig_candidates


# ---------------------------------------------------------------------------
# Test 10: Step 6 Schema Validation Integration
# ---------------------------------------------------------------------------
def test_step6_schema_validation_integration():
    """Test integration of SchemaValidator for relationship triplet constraints."""
    # Attempting to assign invalid triplet: (COURT) -[OWNS]-> (STATUTE)
    request = LLMFallbackRequest(
        case_id="case_109",
        source_document_id="doc_test.pdf",
        source_text="High Court PKR owns Section 4.",
        ambiguity_type=AmbiguityType.RELATIONSHIP_TYPE,
        candidate_relationships=[{"source_type": "COURT", "target_type": "STATUTE"}],
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.RESOLVED,
        selected_relationship_type="OWNS",  # OWNS is not allowed for COURT -> STATUTE
        confidence=0.90,
        reasoning="Model suggested OWNS.",
        needs_human_review=False,
    )

    review_mgr = ReviewManager()
    service = LLMFallbackService(provider=mock_provider, review_manager=review_mgr)

    res = service.resolve_ambiguity(request)
    # Triplet constraint violation should cause rejection
    assert res.decision == LLMDecision.REJECTED
    assert res.needs_human_review is True
    assert (
        "triplet validation failed" in res.reasoning.lower()
        or "validation rejected" in res.reasoning.lower()
    )


# ---------------------------------------------------------------------------
# Test 11: Step 9 Review Manager Integration
# ---------------------------------------------------------------------------
def test_step9_review_manager_integration():
    """Test full integration with Step 9 review lifecycle."""
    request = LLMFallbackRequest(
        case_id="case_110",
        source_document_id="doc_contract.pdf",
        source_text="Seller agrees to deliver goods by October 15, 2026.",
        ambiguity_type=AmbiguityType.TEMPORAL_INTERPRETATION,
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.UNCERTAIN,
        confidence=0.50,
        reasoning="Relative timeline reference unresolved.",
        needs_human_review=True,
    )

    review_mgr = ReviewManager()
    service = LLMFallbackService(provider=mock_provider, review_manager=review_mgr)

    service.resolve_ambiguity(request)

    # Check that Step 9 review manager stored the review item correctly
    pending_items = review_mgr.get_review_items_for_case(
        "case_110", status=ReviewStatus.PENDING
    )
    assert len(pending_items) == 1
    assert pending_items[0].item_type == ItemType.TEMPORAL

    # Lawyers can approve or correct using Step 9 manager
    approved_item = review_mgr.approve_item(
        pending_items[0].review_id, reviewer_id="lawyer_01"
    )
    assert approved_item.status == ReviewStatus.APPROVED
    assert approved_item.reviewed_by == "lawyer_01"


# ---------------------------------------------------------------------------
# Test 12: No Direct Unvalidated Neo4j Insertion
# ---------------------------------------------------------------------------
def test_no_direct_unvalidated_neo4j_insertion():
    """Test that unvalidated or low-confidence LLM predictions never write to Neo4j."""
    mock_neo4j_store = MagicMock()
    mock_neo4j_store.verify_connection.return_value = True

    request = LLMFallbackRequest(
        case_id="case_111",
        source_document_id="doc_test.pdf",
        source_text="Unvalidated entity assertion.",
        ambiguity_type=AmbiguityType.ENTITY_TYPE,
    )

    mock_provider = MagicMock(spec=LLMProvider)
    # LLM returns invalid entity type
    mock_provider.generate_resolution.return_value = LLMFallbackResponse(
        request_id=request.request_id,
        decision=LLMDecision.RESOLVED,
        selected_entity_type="INVALID_TYPE",
        selected_entity_name="Test Node",
        confidence=0.99,
        reasoning="Invalid type suggestion.",
        needs_human_review=False,
    )

    service = LLMFallbackService(
        provider=mock_provider,
        review_manager=ReviewManager(),
        neo4j_store=mock_neo4j_store,
    )

    service.resolve_ambiguity(request)

    # Ensure upsert_entities was NEVER called on Neo4j store for invalid output
    mock_neo4j_store.upsert_entities.assert_not_called()
