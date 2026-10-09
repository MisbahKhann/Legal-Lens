"""
FastAPI Router for Step 10: Local LLM Fallback & Ambiguous Extraction Resolution.
Provides REST endpoints for triggering narrow LLM resolution and checking provider status.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.llm.config import LLMConfig, get_llm_config
from app.llm.models import LLMFallbackRequest, LLMFallbackResponse
from app.llm.provider import OllamaProvider
from app.llm.service import LLMFallbackService
from app.api.review_router import get_manager
from app.review.manager import ReviewManager

router = APIRouter(prefix="/api/v1/llm", tags=["LLM Fallback Resolution"])

# Module-level service instance helper
_service_instance: LLMFallbackService = None


def get_llm_service(
    review_mgr: ReviewManager = Depends(get_manager),
) -> LLMFallbackService:
    """Dependency provider for LLMFallbackService."""
    config = get_llm_config()
    provider = OllamaProvider(config=config)
    return LLMFallbackService(
        provider=provider, config=config, review_manager=review_mgr
    )


@router.get("/status")
def get_llm_status() -> Dict[str, Any]:
    """
    Returns the status of the local LLM provider configuration and reachability.
    Does NOT invoke model inference or tokens.
    """
    config = get_llm_config()
    provider = OllamaProvider(config=config)
    is_reachable = provider.is_available()

    return {
        "status": "ONLINE" if is_reachable else "UNREACHABLE",
        "provider": config.provider,
        "ollama_base_url": config.ollama_base_url,
        "configured_model": config.ollama_model,
        "is_model_available": is_reachable,
        "high_confidence_threshold": config.high_confidence_threshold,
        "low_confidence_threshold": config.low_confidence_threshold,
    }


@router.post("/fallback", response_model=LLMFallbackResponse)
def trigger_llm_fallback(
    request: LLMFallbackRequest,
    service: LLMFallbackService = Depends(get_llm_service),
) -> LLMFallbackResponse:
    """
    Triggers targeted local LLM fallback for an ambiguous extraction.
    Validates output against Step 1 ontology and escalates to Step 9 review if uncertain.
    """
    try:
        return service.resolve_ambiguity(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM Fallback resolution failed: {str(e)}",
        )
