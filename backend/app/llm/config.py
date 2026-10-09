"""
Configuration management for Local LLM Provider integration (Step 10).
Loads environment variables for Ollama provider, model selection, timeouts, and decision thresholds.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """
    LLM Fallback configuration container.
    """

    provider: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama").lower(),
        description="Active LLM provider backend (default: 'ollama').",
    )
    ollama_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        ).rstrip("/"),
        description="Base HTTP URL for Ollama server API.",
    )
    ollama_model: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
        description="Local Ollama model identifier to invoke.",
    )
    timeout: float = Field(
        default_factory=lambda: float(os.getenv("LLM_TIMEOUT", "30.0")),
        ge=1.0,
        description="HTTP request timeout in seconds.",
    )
    high_confidence_threshold: float = Field(
        default_factory=lambda: float(
            os.getenv("LLM_HIGH_CONFIDENCE_THRESHOLD", "0.85")
        ),
        ge=0.0,
        le=1.0,
        description="Threshold above which LLM result is accepted directly.",
    )
    low_confidence_threshold: float = Field(
        default_factory=lambda: float(
            os.getenv("LLM_LOW_CONFIDENCE_THRESHOLD", "0.50")
        ),
        ge=0.0,
        le=1.0,
        description="Threshold below which LLM result is rejected.",
    )

    def validate_config(self) -> None:
        """Validates that configuration parameters are valid."""
        if not self.provider:
            raise ValueError("LLM provider cannot be empty.")
        if self.provider != "ollama":
            raise ValueError(
                f"Unsupported LLM provider '{self.provider}'. Currently supported: 'ollama'."
            )
        if not self.ollama_model or not self.ollama_model.strip():
            raise ValueError(
                "OLLAMA_MODEL configuration is missing or empty. Expected default 'qwen2.5:1.5b'."
            )
        if self.high_confidence_threshold <= self.low_confidence_threshold:
            raise ValueError(
                f"High confidence threshold ({self.high_confidence_threshold}) must be strictly greater than low threshold ({self.low_confidence_threshold})."
            )


def get_llm_config() -> LLMConfig:
    """Factory helper to obtain a validated LLMConfig instance from environment."""
    config = LLMConfig()
    config.validate_config()
    return config
