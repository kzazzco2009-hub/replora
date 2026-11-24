"""FastAPI application factory."""

from fastapi import FastAPI

from app.api import v1
from app.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the Replora API. Interactive docs and the live OpenAPI are off in production."""
    settings = settings or Settings()
    docs = settings.app_env != "production"
    app = FastAPI(
        title="Replora API",
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.include_router(v1.router)
    return app
