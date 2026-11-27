"""Passwords (P5.1, S-20): argon2id hashes and the NIST 800-63B policy.

The policy is length (12 to 256 characters, in the request models) plus a check against an offline
list of breached passwords. There are no composition rules, so long passphrases in any script,
Arabic included, are welcome. Text is NFKC-normalized before hashing, so the same passphrase typed
on different keyboards verifies.
"""

import unicodedata
from functools import cache
from pathlib import Path

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

HASHER = PasswordHash((Argon2Hasher(),))
"""argon2id with pwdlib's recommended parameters. Older hashes are upgraded at login."""


def _normal(password: str) -> str:
    return unicodedata.normalize("NFKC", password)


def hash_password(password: str) -> str:
    return HASHER.hash(_normal(password))


def verify_password(password: str, stored: str) -> tuple[bool, str | None]:
    """Whether it matches, and a new hash to store when the parameters have changed."""
    return HASHER.verify_and_update(_normal(password), stored)


@cache
def _breached() -> frozenset[str]:
    path = Path(__file__).with_name("breached_passwords.txt")
    lines = path.read_text(encoding="utf-8").splitlines()
    return frozenset(line for line in lines if line and not line.startswith("#"))


BREACHED = _breached()


def is_breached(password: str) -> bool:
    return _normal(password).strip().lower() in BREACHED
