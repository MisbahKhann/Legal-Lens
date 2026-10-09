"""
LLM Provider abstraction and Ollama local model integration for Step 10.
Includes robust error handling for Ollama connectivity, model availability, timeouts, and malformed responses.
"""

from abc import ABC, abstractmethod
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from app.llm.config import LLMConfig, get_llm_config
from app.llm.models import (
    LLMFallbackRequest,
    LLMFallbackResponse,
    LLMDecision,
)
from app.llm.prompts import SYSTEM_PROMPT, build_fallback_prompt

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    pass


class LLMProvider(ABC):
    """Abstract interface for local LLM fallback providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the LLM provider service and model are reachable."""
        pass

    @abstractmethod
    def generate_resolution(self, request: LLMFallbackRequest) -> LLMFallbackResponse:
        """Generates a structured LLMFallbackResponse for an ambiguity request."""
        pass


class OllamaProvider(LLMProvider):
    """
    Ollama implementation of LLMProvider.
    Communicates via Ollama HTTP API (/api/generate or /api/tags).
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or get_llm_config()

    def is_available(self) -> bool:
        """
        Verifies if Ollama server is running and the configured model is installed.
        Returns True if reachable and model exists, False otherwise.
        """
        try:
            url = f"{self.config.ollama_base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Check if requested model or model:latest exists
                    target_model = self.config.ollama_model
                    target_base = target_model.split(":")[0]
                    found = any(
                        target_model in m or m.startswith(target_base) for m in models
                    )
                    if not found:
                        logger.warning(
                            "Ollama reachable but model '%s' not found in %s",
                            target_model,
                            models,
                        )
                    return found
        except Exception as e:
            logger.warning("Ollama availability check failed: %s", str(e))
            return False
        return False

    def generate_resolution(self, request: LLMFallbackRequest) -> LLMFallbackResponse:
        """
        Sends formatted prompt to Ollama /api/generate endpoint with JSON response format.
        Handles errors gracefully by returning a fallback LLMFallbackResponse.
        """
        prompt = build_fallback_prompt(request)
        payload = {
            "model": self.config.ollama_model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0},
        }

        url = f"{self.config.ollama_base_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(payload).encode("utf-8")

        try:
            req = urllib.request.Request(
                url, data=req_data, headers=headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                if resp.status != 200:
                    return self._build_error_response(
                        request,
                        f"Ollama returned HTTP {resp.status}",
                    )

                response_bytes = resp.read()
                if not response_bytes or not response_bytes.strip():
                    return self._build_error_response(
                        request, "Empty response received from Ollama."
                    )

                resp_json = json.loads(response_bytes.decode("utf-8"))
                raw_text = resp_json.get("response", "")

                return self._parse_llm_json_response(request, raw_text)

        except urllib.error.URLError as e:
            logger.error("Ollama connection error: %s", str(e))
            return self._build_error_response(
                request, f"Ollama service unavailable: {str(e.reason)}"
            )
        except TimeoutError as e:
            logger.error("Ollama request timed out: %s", str(e))
            return self._build_error_response(
                request, f"Ollama request timed out after {self.config.timeout}s"
            )
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Ollama API envelope: %s", str(e))
            return self._build_error_response(
                request, f"Malformed Ollama response structure: {str(e)}"
            )
        except Exception as e:
            logger.error("Unexpected error in OllamaProvider: %s", str(e))
            return self._build_error_response(
                request, f"Ollama provider execution failure: {str(e)}"
            )

    def _parse_llm_json_response(
        self, request: LLMFallbackRequest, raw_text: str
    ) -> LLMFallbackResponse:
        """Parses raw JSON generated by LLM into LLMFallbackResponse."""
        if not raw_text or not raw_text.strip():
            return self._build_error_response(
                request, "Ollama generated empty text response.", raw_text=raw_text
            )

        try:
            parsed = json.loads(raw_text)

            decision_str = str(parsed.get("decision", "UNCERTAIN")).upper()
            try:
                decision = LLMDecision(decision_str)
            except ValueError:
                decision = LLMDecision.UNCERTAIN

            conf = float(parsed.get("confidence", 0.0))
            needs_review = bool(
                parsed.get("needs_human_review", decision != LLMDecision.RESOLVED)
            )

            return LLMFallbackResponse(
                request_id=request.request_id,
                decision=decision,
                selected_entity_type=parsed.get("selected_entity_type"),
                selected_entity_name=parsed.get("selected_entity_name"),
                selected_relationship_type=parsed.get("selected_relationship_type"),
                source_entity_name=parsed.get("source_entity_name"),
                target_entity_name=parsed.get("target_entity_name"),
                selected_temporal_interpretation=parsed.get(
                    "selected_temporal_interpretation"
                ),
                confidence=conf,
                reasoning=str(parsed.get("reasoning", "")),
                needs_human_review=needs_review,
                llm_provider=self.config.provider,
                llm_model=self.config.ollama_model,
                raw_response=raw_text,
            )
        except json.JSONDecodeError as e:
            logger.warning("Malformed JSON in LLM text response: %s", str(e))
            return self._build_error_response(
                request,
                f"Malformed JSON in LLM text output: {str(e)}",
                raw_text=raw_text,
            )

    def _build_error_response(
        self,
        request: LLMFallbackRequest,
        error_msg: str,
        raw_text: Optional[str] = None,
    ) -> LLMFallbackResponse:
        """Helper creating a standard error/fallback response requiring human review."""
        return LLMFallbackResponse(
            request_id=request.request_id,
            decision=LLMDecision.UNCERTAIN,
            confidence=0.0,
            reasoning=f"LLM Provider Fallback Error: {error_msg}",
            needs_human_review=True,
            llm_provider=self.config.provider,
            llm_model=self.config.ollama_model,
            raw_response=raw_text,
        )
