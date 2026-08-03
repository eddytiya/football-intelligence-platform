"""make team api_id nullable

Revision ID: 9284cd69502a
Revises: 05ed94384c3a
Create Date: 2026-07-29 16:48:45.966786

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9284cd69502a"
down_revision: Union[str, Sequence[str], None] = "05ed94384c3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "teams",
        "api_id",
        existing_type=sa.INTEGER(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "teams",
        "api_id",
        existing_type=sa.INTEGER(),
        nullable=False,
    )