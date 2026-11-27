"""Signed, expiring tokens for storage URLs (P6.1, S-34, S-36).

A token is base64url(JSON claims + expiry) and an HMAC-SHA256 over it. Each one is for one
operation (`put` or `get`) on one key, so it can't be reused for anything else.
"""

import base64
import hashlib
import hmac
import json
from datetime import datetime
from typing import Any


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _mac(body: str, key: str) -> str:
    return _b64(hmac.new(key.encode(), body.encode(), hashlib.sha256).digest())


def sign(claims: dict[str, Any], key: str, expires_at: datetime) -> str:
    body = _b64(json.dumps({**claims, "exp": int(expires_at.timestamp())}).encode())
    return f"{body}.{_mac(body, key)}"


def verify(token: str, key: str, now: datetime, op: str) -> dict[str, Any] | None:
    """The claims of a genuine, unexpired token for `op`; None for anything else."""
    body, _, mac = token.partition(".")
    if not mac or not hmac.compare_digest(mac, _mac(body, key)):
        return None
    claims = json.loads(_unb64(body))
    if claims.pop("exp") <= now.timestamp() or claims.get("op") != op:
        return None
    return claims
