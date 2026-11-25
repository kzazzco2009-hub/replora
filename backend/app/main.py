"""FastAPI application factory."""

from importlib.metadata import version

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api import problem, v1
from app.config import Settings
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
    app.include_router(v1.router)
    problem.install(app)
    app.add_middleware(RequestIdMiddleware)
    configure_logging()
    return app
