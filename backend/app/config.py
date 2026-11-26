"""Application settings, read from environment variables (and the repo-root `.env` locally)."""

from datetime import timedelta
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

PRODUCTION_SECRETS = ("openrouter_api_key",)
"""S-02: production refuses to start without these. Each phase adds the secrets it needs."""


class Settings(BaseSettings):
    """Runtime configuration. Secrets are `SecretStr`, so they never appear in logs or reprs."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_ignore_empty=True,
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    openrouter_api_key: SecretStr | None = None
    database_url: str = f"sqlite:///{(REPO_ROOT / '.data' / 'replora.db').as_posix()}"
    """P4.1: SQLite under `.data/` locally; the Supabase pooler URL in production (Phase 18)."""
    approval_ttl_hours: Annotated[int, Field(ge=1)] = 24
    """P3.6: a run awaiting approval for longer than this expires."""

    @property
    def approval_ttl(self) -> timedelta:
        return timedelta(hours=self.approval_ttl_hours)

    @model_validator(mode="after")
    def _production_is_safe(self) -> Self:
        """S-02: in production, every required secret is set and debug is off."""
        if self.app_env != "production":
            return self
        missing = [name for name in PRODUCTION_SECRETS if getattr(self, name) is None]
        if missing:
            raise ValueError(f"production needs: {', '.join(missing)}")
        if self.debug:
            raise ValueError("debug must be off in production")
        return self
