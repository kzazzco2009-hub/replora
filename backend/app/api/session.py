"""Session cookies and the signed-in caller (P5.2, S-24).

Everything is read from the `Request`, so no cookie appears as an OpenAPI parameter and the
contract stays as frozen. Both cookies are HttpOnly, SameSite=Lax, on `/`, and Secure in
production.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fastapi import Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.api.problem import ProblemError
from app.auth.sessions import REFRESH_TTL
from app.auth.tokens import ACCESS_TTL, access_token, read_access
from app.db import models as m

ACCESS_COOKIE = "replora_access"
REFRESH_COOKIE = "replora_refresh"


def database(request: Request) -> sessionmaker[Session]:
    return request.app.state.sessions


def now(request: Request) -> datetime:
    return request.app.state.clock()


def unauthenticated() -> ProblemError:
    return ProblemError(401, "UNAUTHENTICATED", "Unauthorized")


def set_session_cookies(
    request: Request, response: Response, row: m.Session, refresh_token: str
) -> None:
    access = access_token(row.user_id, row.id, now(request), request.app.state.jwt_key)
    secure = request.app.state.settings.app_env == "production"
    for name, value, ttl in ((ACCESS_COOKIE, access, ACCESS_TTL),
                             (REFRESH_COOKIE, refresh_token, REFRESH_TTL)):  # fmt: skip
        response.set_cookie(name, value, max_age=int(ttl.total_seconds()), path="/",
                            httponly=True, secure=secure, samesite="lax")  # fmt: skip


def clear_session_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(name, path="/", httponly=True, samesite="lax")


@dataclass(frozen=True)
class Caller:
    user: m.User
    session_id: UUID


def caller(request: Request) -> Caller:
    """The signed-in user, from a valid access token of a live session; otherwise 401."""
    token = request.cookies.get(ACCESS_COOKIE, "")
    ids = read_access(token, request.app.state.jwt_key, now(request))
    if ids is None:
        raise unauthenticated()
    user_id, session_id = ids
    with database(request)() as session:
        user = session.get(m.User, user_id)
        row = session.get(m.Session, session_id)
    live = row is not None and row.revoked_at is None and row.user_id == user_id
    if user is None or user.deleted_at is not None or not live:
        raise unauthenticated()
    return Caller(user, session_id)
