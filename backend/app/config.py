"""Centralized app settings, loaded once from the repo-root .env."""
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_FILE)


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.environ.get("LLM_PROVIDER", "groq")
    llm_model: str = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
    groq_api_key: str = os.environ.get("GROQ_API_KEY", "")
    google_api_key: str = os.environ.get("GOOGLE_API_KEY", "")

    database_url: str = os.environ.get("DATABASE_URL", "")
    # Writable connection for app metadata (conversation history) — separate
    # from the read-only agent connection above.
    app_database_url: str = os.environ.get("APP_DATABASE_URL", "")

    sql_statement_timeout_ms: int = int(os.environ.get("SQL_STATEMENT_TIMEOUT_MS", "10000"))
    max_self_correct_retries: int = int(os.environ.get("MAX_SELF_CORRECT_RETRIES", "3"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
