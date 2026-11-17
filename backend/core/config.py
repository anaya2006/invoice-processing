# backend/core/config.py
"""Application configuration using pydantic-settings.
All settings are loaded from environment variables or a .env file.
"""
from typing import ClassVar

import os
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core settings
    BACKEND_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent  # backend/ (core/config.py sits one level down)
    DATABASE_URL: str = f"sqlite:///{(BACKEND_DIR / 'ana.db').as_posix()}"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10
    ALLOWED_ORIGINS: list[str] = ["*"]
    DEMO_MODE: bool = True
    JWT_SECRET: str = "change-me-secret"
    JWT_EXPIRE_HOURS: int = 8
    # Tesseract configuration
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    TESSDATA_PREFIX: str | None = None
    # OCR settings
    OCR_MAX_PAGES: int = 5
    OCR_DPI: int = 300
    OCR_MIN_WORD_CONF: int = 60
    # Image quality thresholds
    BLUR_THRESHOLD: float = 100.0
    MIN_PAGE_PIXELS: int = 1000 * 1000
    # Business thresholds
    TOTAL_TOLERANCE_PCT: float = 0.01
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.80
    ALLOWED_TAX_RATES: list[int] = [0, 5, 12, 18, 28]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
