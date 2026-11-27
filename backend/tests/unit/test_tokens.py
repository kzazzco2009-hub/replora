"""P5.2 access tokens (S-24): a pinned algorithm, a short life, and nothing else accepted."""

from datetime import UTC, datetime, timedelta
from uuid import uuid7

import jwt
import pytest

from app.auth.tokens import ACCESS_TTL, access_token, digest, new_secret, read_access

KEY = "k" * 43
NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)
USER, SESSION = uuid7(), uuid7()


def test_an_access_token_names_its_user_and_session_for_15_minutes():
    assert timedelta(minutes=15) == ACCESS_TTL
    token = access_token(USER, SESSION, NOW, KEY)
    assert read_access(token, KEY, NOW + ACCESS_TTL - timedelta(seconds=1)) == (USER, SESSION)
    assert read_access(token, KEY, NOW + ACCESS_TTL) is None


def test_a_token_signed_with_another_key_is_refused():
    assert read_access(access_token(USER, SESSION, NOW, "x" * 43), KEY, NOW) is None


@pytest.mark.filterwarnings("ignore::jwt.warnings.InsecureKeyLengthWarning")
@pytest.mark.parametrize("algorithm", ["HS512", "none"])
def test_any_other_algorithm_is_refused(algorithm):
    claims = {"sub": str(USER), "sid": str(SESSION), "exp": int((NOW + ACCESS_TTL).timestamp())}
    token = jwt.encode(claims, None if algorithm == "none" else KEY, algorithm=algorithm)
    assert read_access(token, KEY, NOW) is None


@pytest.mark.parametrize("token", ["", "garbage", "a.b.c"])
def test_a_malformed_token_is_refused(token):
    assert read_access(token, KEY, NOW) is None


def test_a_token_missing_a_claim_is_refused():
    claims = {"sub": str(USER), "exp": int((NOW + ACCESS_TTL).timestamp())}
    assert read_access(jwt.encode(claims, KEY, algorithm="HS256"), KEY, NOW) is None


def test_secrets_are_random_and_stored_only_as_their_sha256():
    first, second = new_secret(), new_secret()
    assert first != second and len(first) >= 43
    assert len(digest(first)) == 64 and digest(first) != first
