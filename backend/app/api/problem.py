"""RFC 9457 problem+json errors: the model, the exception, its handler and the OpenAPI wiring."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.models import ApiModel

PROBLEM_MEDIA_TYPE = "application/problem+json"


class ProblemItem(ApiModel):
    """One field-level issue inside a problem."""

    path: str
    code: str
    params: dict[str, Any] = {}


class Problem(ApiModel):
    """Error body. Clients translate `code`, never `detail` (docs/api_contract.md §1)."""

    type: str = "about:blank"
    title: str
    status: int
    code: str
    detail: str | None = None
    correlation_id: str | None = None
    errors: list[ProblemItem] | None = None


class ProblemError(Exception):
    """Raise to answer with a problem+json response."""

    def __init__(self, status: int, code: str, title: str) -> None:
        super().__init__(code)
        self.problem = Problem(status=status, code=code, title=title)


def not_implemented() -> ProblemError:
    """The answer of a contract stub that has no implementation yet."""
    return ProblemError(501, "NOT_IMPLEMENTED", "Not implemented")


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    "4XX": {"model": Problem, "description": "Client error"},
    501: {"model": Problem, "description": "Not implemented yet (contract stub)"},
}


def install(app: FastAPI) -> None:
    """Register the problem handler and document error bodies as problem+json."""

    async def handle(_: Request, error: ProblemError) -> JSONResponse:
        body = error.problem.model_dump(exclude_none=True)
        return JSONResponse(body, status_code=error.problem.status, media_type=PROBLEM_MEDIA_TYPE)

    app.add_exception_handler(ProblemError, handle)
    build_openapi = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            app.openapi_schema = use_problem_media_type(build_openapi())
        return app.openapi_schema

    app.openapi = openapi


def use_problem_media_type(document: dict[str, Any]) -> dict[str, Any]:
    """Move error-response schemas from `application/json` to `application/problem+json`.

    FastAPI documents every response model under the route's media type; errors are problem+json.
    """
    for operations in document.get("paths", {}).values():
        for operation in operations.values():
            for status, response in operation.get("responses", {}).items():
                content = response.get("content", {})
                if str(status)[0] in "45" and "application/json" in content:
                    response["content"] = {PROBLEM_MEDIA_TYPE: content["application/json"]}
    return document
