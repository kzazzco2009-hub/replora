"""P5.1 password hashing (T5.1) and the NIST 800-63B policy (T5.2)."""

import pytest
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.auth.passwords import BREACHED, hash_password, is_breached, verify_password

ARABIC = "كلمة سر طويلة جدا للاختبار"


def test_hashes_are_argon2id_and_salted():
    first, second = hash_password("correct horse battery"), hash_password("correct horse battery")
    assert first.startswith("$argon2id$")
    assert first != second


def test_the_right_password_verifies_and_a_wrong_one_does_not():
    stored = hash_password(ARABIC)
    assert verify_password(ARABIC, stored) == (True, None)
    assert verify_password(ARABIC + "x", stored) == (False, None)


def test_unicode_is_normalized_before_hashing():
    composed, decomposed = "café passphrase", "café passphrase"
    assert verify_password(decomposed, hash_password(composed))[0]


def test_an_old_parameter_set_is_rehashed_on_login():
    old = PasswordHash((Argon2Hasher(time_cost=1, memory_cost=8192),)).hash("long passphrase ok")
    valid, updated = verify_password("long passphrase ok", old)
    assert valid
    assert updated is not None and updated != old and updated.startswith("$argon2id$")


def test_the_breached_list_holds_only_long_lowercase_entries():
    assert len(BREACHED) > 1000
    assert all(len(entry) >= 12 and entry == entry.lower() for entry in BREACHED)


@pytest.mark.parametrize("password", ["1234567890qwerty", "1234567890QWERTY", " 000000000000 "])
def test_a_breached_password_is_refused_ignoring_case_and_spaces(password):
    assert is_breached(password)


@pytest.mark.parametrize("password", ["correct horse battery staple", ARABIC, "a" * 12 + "!b"])
def test_long_passphrases_are_accepted_with_no_composition_rules(password):
    assert not is_breached(password)


@pytest.mark.parametrize(
    ("password", "code"),
    [("short", "STRING_TOO_SHORT"), ("1234567890qwerty", "PASSWORD_BREACHED")],
)
def test_registration_refuses_a_weak_password_with_a_field_code(client, password, code):
    body = {"email": "s@example.com", "password": password, "display_name": "S", "locale": "ar"}
    response = client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 422
    errors = response.json()["errors"]
    assert [(e["code"], e["path"]) for e in errors] == [(code, "body.password")]


def test_the_user_never_carries_a_password_field(schemas):
    for name in ("User", "Me"):
        assert not {"password", "password_hash"} & set(schemas[name]["properties"])
