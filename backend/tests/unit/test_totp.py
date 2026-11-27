"""P5.11 TOTP (RFC 6238) and the secret's encryption at rest (S-28)."""

import base64
from datetime import UTC, datetime

import pytest

from app.auth.totp import code_at, decrypt, encrypt, new_secret, step_of, uri, verify

RFC_SECRET = base64.b32encode(b"12345678901234567890").decode()


RFC_VECTORS = [(59, "287082"), (1111111109, "081804"), (1234567890, "005924"),
               (2000000000, "279037")]  # fmt: skip
"""RFC 6238 appendix B, SHA-1, the last 6 of 8 digits."""


@pytest.mark.parametrize(("seconds", "code"), RFC_VECTORS)
def test_codes_match_the_rfc_6238_sha1_vectors(seconds, code):
    assert code_at(RFC_SECRET, seconds // 30) == code


def at(seconds: int) -> datetime:
    return datetime.fromtimestamp(seconds, UTC)


def test_a_code_is_accepted_one_step_either_side_and_returns_its_step():
    now = at(1234567890)
    step = step_of(now)
    for drift in (-1, 0, 1):
        assert verify(RFC_SECRET, code_at(RFC_SECRET, step + drift), now, None) == step + drift
    assert verify(RFC_SECRET, code_at(RFC_SECRET, step + 2), now, None) is None


def test_a_code_cannot_be_replayed():
    now = at(1234567890)
    code = code_at(RFC_SECRET, step_of(now))
    used = verify(RFC_SECRET, code, now, None)
    assert verify(RFC_SECRET, code, now, used) is None


def test_secrets_are_random_base32_and_encrypted_at_rest():
    secret = new_secret()
    assert len(base64.b32decode(secret)) == 20 and secret != new_secret()
    key = "x" * 43
    stored = encrypt(secret, key)
    assert secret.encode() not in stored
    assert decrypt(stored, key) == secret


def test_the_provisioning_uri_names_the_issuer_and_account():
    link = uri("ABC", "salma@example.com")
    assert link.startswith("otpauth://totp/Replora:salma%40example.com?secret=ABC")
    assert "issuer=Replora" in link and "period=30" in link and "digits=6" in link
