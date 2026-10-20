"""
Configuration management for LegalLens platform.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform application settings."""

    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./legallens.db"
    UPLOAD_DIR: str = "./uploads"
    SCHEDULER_ENABLED: bool = True
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_CONTENT_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/rtf",
        "image/png",
        "image/jpeg",
    ]
    DEFAULT_TIMEZONE: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
