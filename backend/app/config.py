"""Application settings, read from environment variables (and the repo-root `.env` locally)."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration. Secrets are `SecretStr`, so they never appear in logs or reprs."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    openrouter_api_key: SecretStr | None = None
