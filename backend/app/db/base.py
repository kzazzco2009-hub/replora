"""The declarative base: UUIDv7 primary keys and UTC timestamps on every table (P4.2)."""

from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy import JSON, DateTime, MetaData, TypeDecorator, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMES = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}
"""Indexes and unique constraints are named by hand, as `plan.md` §6 lists them."""


class UtcDateTime(TypeDecorator[datetime]):
    """A timestamp stored and returned in UTC. A naive datetime is refused, never guessed."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


JsonDocument = JSON().with_variant(JSONB(), "postgresql")


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMES)
    type_annotation_map = {datetime: UtcDateTime, UUID: Uuid}


class IdMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)


class CreatedMixin:
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
