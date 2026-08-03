"""create sync_logs table

Revision ID: 90086b5fadb6
Revises: e7fd3e799e2e
Create Date: 2026-07-30 00:00:22.698477

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "90086b5fadb6"
down_revision: Union[str, Sequence[str], None] = "e7fd3e799e2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("resource", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("last_sync", sa.DateTime(), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_sync_logs_provider",
        "sync_logs",
        ["provider"],
    )

    op.create_index(
        "ix_sync_logs_resource",
        "sync_logs",
        ["resource"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_sync_logs_resource",
        table_name="sync_logs",
    )

    op.drop_index(
        "ix_sync_logs_provider",
        table_name="sync_logs",
    )

    op.drop_table("sync_logs")