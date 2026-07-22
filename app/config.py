"""Centralized, env-driven configuration. No insecure defaults for secrets."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8765
    app_secret_key: str = Field(..., min_length=32)

    database_url: str = "postgresql+psycopg://payroll:payroll@localhost:5432/payroll_panel"

    session_cookie_name: str = "payroll_session"
    session_ttl_hours: int = 168
    access_token_ttl_hours: int = 24

    upload_dir: Path = BASE_DIR / "uploads"
    data_dir: Path = BASE_DIR / "data"

    google_application_credentials: str | None = None
    drive_parent_folder_id: str | None = None
    drive_folder_name: str = "صورت-کارگری-پنل-بهزادیان"

    cors_origins: str = ""

    @field_validator("app_secret_key")
    @classmethod
    def _no_placeholder_secret(cls, v: str) -> str:
        if v.strip().lower() in {"", "change-me", "change-me-generate-a-random-64-char-hex-string"}:
            raise ValueError("APP_SECRET_KEY must be set to a real random secret, not the placeholder")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
