"""RFC 9457 problem+json errors: the model, the exception, the handlers and the OpenAPI wiring."""

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.models import ApiModel

PROBLEM_MEDIA_TYPE = "application/problem+json"

# Pydantic error type → our stable 422 `code`. Explicit, so a library upgrade cannot rename a code.
VALIDATION_CODES = {
    name: name.upper()
    for name in (
        "missing",
        "extra_forbidden",
        "json_invalid",
        "model_attributes_type",
        "string_type",
        "string_too_short",
        "string_too_long",
        "string_pattern_mismatch",
        "literal_error",
        "uuid_parsing",
        "value_error",
    )
}


class ProblemItem(ApiModel):
    """One field-level issue. `code` is stable and translated by the client."""

    path: str
    code: str
    params: dict[str, Any] = {}


class ProblemDetails(ApiModel):
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
        self.problem = ProblemDetails(status=status, code=code, title=title)


def not_implemented() -> ProblemError:
    """The answer of a contract stub that has no implementation yet."""
    return ProblemError(501, "NOT_IMPLEMENTED", "Not implemented")


def _documented(description: str) -> dict[str, Any]:
    return {"model": ProblemDetails, "description": description}


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: _documented("Not signed in, or the session expired"),
    403: _documented("CSRF check failed, or not allowed in this workspace"),
    409: _documented("Conflict with the current state"),
    422: _documented("Validation failed (`code: VALIDATION_FAILED`, details in `errors`)"),
    429: _documented("Too many requests (see `Retry-After`)"),
    501: _documented("Not implemented yet (contract stub)"),
}
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: _documented("Not found, or not yours"),
}


def install(app: FastAPI) -> None:
    """Register the problem handlers and document error bodies as problem+json."""
    app.add_exception_handler(ProblemError, _handle_problem)
    app.add_exception_handler(RequestValidationError, _handle_validation)
    app.add_exception_handler(HTTPException, _handle_http)
    app.add_exception_handler(Exception, _handle_unexpected)
    build_openapi = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            app.openapi_schema = use_problem_media_type(build_openapi())
        return app.openapi_schema

    app.openapi = openapi


async def _handle_problem(_: Request, error: ProblemError) -> JSONResponse:
    return _problem_response(error.problem)


async def _handle_validation(_: Request, error: RequestValidationError) -> JSONResponse:
    """422 as problem+json. The rejected input is never echoed back (it may be a password)."""
    items = [
        ProblemItem(
            path=".".join(str(part) for part in issue["loc"]),
            code=validation_code(issue["type"]),
            params={key: _plain(value) for key, value in issue.get("ctx", {}).items()},
        )
        for issue in error.errors()
    ]
    problem = ProblemDetails(
        status=422, code="VALIDATION_FAILED", title="Validation failed", errors=items
    )
    return _problem_response(problem)


async def _handle_http(_: Request, error: HTTPException) -> JSONResponse:
    """Routing 404/405 and any HTTPException. `detail` is not sent: clients translate `code`."""
    return _problem_response(_status_problem(error.status_code), error.headers)


async def _handle_unexpected(_: Request, __: Exception) -> JSONResponse:
    """An unhandled error. Nothing about it is sent; the server still logs the traceback."""
    return _problem_response(_status_problem(500, code="INTERNAL_ERROR"))


def validation_code(error_type: str) -> str:
    """The stable 422 `code` for a Pydantic error type; `INVALID` for one we have not listed."""
    return VALIDATION_CODES.get(error_type, "INVALID")


def _status_problem(status: int, code: str | None = None) -> ProblemDetails:
    http_status = HTTPStatus(status)
    return ProblemDetails(status=status, code=code or http_status.name, title=http_status.phrase)


def _problem_response(
    problem: ProblemDetails, headers: dict[str, str] | None = None
) -> JSONResponse:
    body = problem.model_dump(exclude_none=True)
    return JSONResponse(
        body, status_code=problem.status, headers=headers, media_type=PROBLEM_MEDIA_TYPE
    )


def _plain(value: Any) -> Any:
    """Keep JSON scalars; render anything else (for example an exception) as text."""
    return value if isinstance(value, str | int | float | bool | None) else str(value)


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
