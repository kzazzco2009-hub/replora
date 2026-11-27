"""draft file ids

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-27 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("drafts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "file_ids",
                sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
                nullable=False,
                server_default="[]",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("drafts", schema=None) as batch_op:
        batch_op.drop_column("file_ids")
