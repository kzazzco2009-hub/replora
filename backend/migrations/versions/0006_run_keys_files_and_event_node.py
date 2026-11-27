"""run approve key, file ids and pinned definition; event node id

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-27 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    with op.batch_alter_table("runs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("approve_key", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("file_ids", JSON, nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("definition", JSON, nullable=True))
    with op.batch_alter_table("run_events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("node_id", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("run_events", schema=None) as batch_op:
        batch_op.drop_column("node_id")
    with op.batch_alter_table("runs", schema=None) as batch_op:
        batch_op.drop_column("definition")
        batch_op.drop_column("file_ids")
        batch_op.drop_column("approve_key")
