"""change external_id to string

Revision ID: e7fd3e799e2e
Revises: 9284cd69502a
Create Date: 2026-07-29 23:46:34.434489

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7fd3e799e2e"
down_revision: Union[str, Sequence[str], None] = "9284cd69502a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "external_ids",
        "external_id",
        existing_type=sa.INTEGER(),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using="external_id::varchar",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "external_ids",
        "external_id",
        existing_type=sa.String(length=255),
        type_=sa.INTEGER(),
        existing_nullable=False,
        postgresql_using="external_id::integer",
    )