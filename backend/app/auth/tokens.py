"""Access tokens and secrets (P5.2, S-24).

The access token is a JWT, HS256 only: the algorithm is pinned, so `none` or any other one is
refused. It lives 15 minutes and names the user and the session. Refresh tokens, reset, verify and
invite tokens are random secrets that the database keeps only as their SHA-256.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID

import jwt

ALGORITHM = "HS256"
ACCESS_TTL = timedelta(minutes=15)


def access_token(user_id: UUID, session_id: UUID, now: datetime, key: str) -> str:
    claims = {"sub": str(user_id), "sid": str(session_id), "iat": int(now.timestamp()),
              "exp": int((now + ACCESS_TTL).timestamp())}  # fmt: skip
    return jwt.encode(claims, key, algorithm=ALGORITHM)


def read_access(token: str, key: str, now: datetime) -> tuple[UUID, UUID] | None:
    """`(user_id, session_id)` of a valid, unexpired token; None for anything else."""
    try:
        # Time is checked here against `now`, not by PyJWT against the wall clock.
        options = {"require": ["exp", "sub", "sid"], "verify_exp": False, "verify_iat": False}
        claims = jwt.decode(token, key, algorithms=[ALGORITHM], options=options)
        if claims["exp"] <= now.timestamp():
            return None
        return UUID(claims["sub"]), UUID(claims["sid"])
    except jwt.PyJWTError, ValueError:
        return None


def new_secret() -> str:
    """256 random bits, URL-safe."""
    return secrets.token_urlsafe(32)


def digest(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()
