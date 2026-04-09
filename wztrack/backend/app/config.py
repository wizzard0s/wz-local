from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://wztrack:wztrack@localhost:5432/wztrack"
    db_schema: str = "wztrack"

    # JWT RS256 — values may use literal \n for newlines (as stored in .env)
    jwt_private_key: str = ""
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"

    @property
    def jwt_private_key_pem(self) -> str:
        return self.jwt_private_key.replace("\\\\n", "\n")

    @property
    def jwt_public_key_pem(self) -> str:
        return self.jwt_public_key.replace("\\\\n", "\n")
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:80"]

    # File uploads
    upload_dir: str = "/uploads"
    max_issue_attachment_bytes: int = 10 * 1024 * 1024   # 10 MB
    max_evidence_attachment_bytes: int = 20 * 1024 * 1024  # 20 MB

    # Seed admin account (first startup only)
    admin_email: str = "admin@wztrack.local"
    admin_password: str = "changeme"
    admin_display_name: str = "Administrator"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
