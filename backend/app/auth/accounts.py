"""Accounts (P5.2): registration with a personal workspace (P5.5), and credential checks.

Both answer the same way, at the same cost, whether or not the email exists (S-26). Register
always hashes and login always verifies, against a dummy hash when there is no such user.
"""

from functools import cache

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import new_secret
from app.db import models as m


@cache
def _dummy_hash() -> str:
    return hash_password(new_secret())


def normal_email(email: str) -> str:
    return email.strip().lower()


def find_user(session: Session, email: str) -> m.User | None:
    query = select(m.User).where(func.lower(m.User.email) == normal_email(email))
    return session.scalars(query).one_or_none()


def register(
    session: Session, email: str, password: str, display_name: str, locale: str
) -> tuple[m.User, bool]:
    """The user and whether it is new. A new user owns a new personal workspace."""
    hashed = hash_password(password)
    existing = find_user(session, email)
    if existing is not None:
        return existing, False
    user = m.User(email=normal_email(email), password_hash=hashed, display_name=display_name,
                  locale=locale)  # fmt: skip
    session.add(user)
    session.flush()
    space = m.Workspace(name=display_name, owner_id=user.id, personal=True)
    session.add(space)
    session.flush()
    session.add(m.Membership(workspace_id=space.id, user_id=user.id, role="owner"))
    return user, True


def authenticate(session: Session, email: str, password: str) -> m.User | None:
    """The user when the password is right; the stored hash is upgraded if it is old (S-20)."""
    user = find_user(session, email)
    live = user is not None and user.deleted_at is None
    valid, updated = verify_password(password, user.password_hash if live else _dummy_hash())
    if not (live and valid):
        return None
    if updated is not None:
        user.password_hash = updated
    return user
