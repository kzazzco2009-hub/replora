"""CSRF protection (P5.3, S-25): a double-submit token and an Origin check.

Every POST, PUT, PATCH and DELETE under `/api/v1` needs the `X-CSRF-Token` header to equal the
readable `replora_csrf` cookie, login and register included (login CSRF). A request that carries
an `Origin` header must come from an allowed origin. A failure is 403 `CSRF_FAILED`. The check is
a router dependency that reads only the `Request`, so it adds nothing to the OpenAPI contract.
"""

import hmac

from fastapi import Request, Response

from app.api.problem import ProblemError
from app.auth.sessions import REFRESH_TTL
from app.auth.tokens import new_secret

CSRF_COOKIE = "replora_csrf"
CSRF_HEADER = "x-csrf-token"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def csrf_failed() -> ProblemError:
    return ProblemError(403, "CSRF_FAILED", "CSRF check failed")


def protect(request: Request) -> None:
    if request.method not in UNSAFE_METHODS:
        return
    origin = request.headers.get("origin")
    if origin is not None and origin not in request.app.state.settings.allowed_origins:
        raise csrf_failed()
    cookie, header = request.cookies.get(CSRF_COOKIE), request.headers.get(CSRF_HEADER)
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise csrf_failed()


def issue_csrf(request: Request, response: Response) -> None:
    """Set a fresh token. Called by `GET /auth/csrf`, and after login and logout."""
    secure = request.app.state.settings.app_env == "production"
    response.set_cookie(CSRF_COOKIE, new_secret(), max_age=int(REFRESH_TTL.total_seconds()),
                        path="/", httponly=False, secure=secure, samesite="lax")  # fmt: skip
