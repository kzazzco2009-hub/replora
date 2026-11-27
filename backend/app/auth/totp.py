"""TOTP for MFA (P5.11, S-28): RFC 6238 with SHA-1, 6 digits, 30-second steps.

A code is accepted one step either side of now, and never for a step already used, so a code
seen over someone's shoulder can't be replayed. The secret is stored encrypted (Fernet) under an
app-level key from the environment.
"""

import base64
import hashlib
import hmac
import secrets
import struct
from datetime import datetime
from urllib.parse import quote

from cryptography.fernet import Fernet

STEP_SECONDS = 30
DIGITS = 6
ISSUER = "Replora"


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode()


def step_of(now: datetime) -> int:
    return int(now.timestamp()) // STEP_SECONDS


def code_at(secret: str, step: int) -> str:
    digest = hmac.new(base64.b32decode(secret), struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % 10**DIGITS).zfill(DIGITS)


def verify(secret: str, code: str, now: datetime, last_step: int | None) -> int | None:
    """The step the code belongs to, or None (wrong, too far off, or already used)."""
    current = step_of(now)
    for step in (current - 1, current, current + 1):
        if (last_step is None or step > last_step) and hmac.compare_digest(
            code_at(secret, step), code
        ):
            return step
    return None


def uri(secret: str, email: str) -> str:
    label = quote(f"{ISSUER}:{email}", safe=":")
    return (f"otpauth://totp/{label}?secret={secret}&issuer={ISSUER}"
            f"&digits={DIGITS}&period={STEP_SECONDS}")  # fmt: skip


def _fernet(key: str) -> Fernet:
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))


def encrypt(secret: str, key: str) -> bytes:
    return _fernet(key).encrypt(secret.encode())


def decrypt(stored: bytes, key: str) -> str:
    return _fernet(key).decrypt(stored).decode()
