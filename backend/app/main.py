"""FastAPI application factory."""

from datetime import UTC, datetime
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api import problem, v1
from app.auth.tokens import new_secret
from app.config import Settings
from app.db.engine import make_engine, make_sessions
from app.observability import RequestIdMiddleware, configure_logging


def operation_id(route: APIRoute) -> str:
    """Short, stable OpenAPI operationId (`auth_login`); it names the generated client function."""
    return f"{route.tags[0]}_{route.name}"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the Replora API. Interactive docs and the live OpenAPI are off in production."""
    settings = settings or Settings()
    docs = settings.app_env != "production"
    app = FastAPI(
        title="Replora API",
        version=version("replora-backend"),
        debug=settings.debug,
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
        generate_unique_id_function=operation_id,
    )
    app.state.settings = settings
    app.state.sessions = make_sessions(make_engine(settings.database_url))
    app.state.jwt_key = (
        settings.jwt_secret.get_secret_value() if settings.jwt_secret else new_secret()
    )
    app.state.clock = lambda: datetime.now(UTC)
    app.include_router(v1.router)
    problem.install(app)
    app.add_middleware(RequestIdMiddleware)
    configure_logging()
    return app
