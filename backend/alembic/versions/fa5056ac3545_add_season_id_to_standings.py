"""add season_id to standings

Revision ID: fa5056ac3545
Revises: 8d83ebb554e1
Create Date: 2026-07-21 17:51:54.359996
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fa5056ac3545"
down_revision: Union[str, Sequence[str], None] = "8d83ebb554e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "standings",
        sa.Column(
            "season_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_standings_season_id",
        "standings",
        "seasons",
        ["season_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_standings_season_id",
        "standings",
        type_="foreignkey",
    )

    op.drop_column(
        "standings",
        "season_id",
    )