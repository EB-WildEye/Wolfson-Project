"""Centralized config via pydantic-settings."""

from pathlib import Path
from typing import Literal
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All config loaded from .env — no hardcoded secrets."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "ingestion" / "data"
    LANCEDB_PATH: Path = BASE_DIR / "lancedb_data"

    ENV: Literal["dev", "prod"] = "dev"

    GEMINI_API_KEY: SecretStr
    GEMINI_MODEL: str = "gemini-3.1-pro-preview"
    FALLBACK_MODEL: str = "gemini-2.5-pro"
    EMBED_MODEL: str = "gemini-embedding-001"

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "gali"

    LANCEDB_TABLE: str = "documents"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200

    API_PORT: int = 8001

    # CORS — override in .env for production, e.g. ALLOWED_ORIGINS='["https://gali.hospital.com"]'
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8501",   # Streamlit UI
        "http://localhost:3000",   # React dev (if used)
        "http://127.0.0.1:8501",
    ]


settings = Settings()

