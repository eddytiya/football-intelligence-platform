"""add competition mappings table

Revision ID: 3f3ba33a5c7b
Revises: 613a3a104186
Create Date: 2026-07-21 14:35:27.653612
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f3ba33a5c7b"
down_revision: Union[str, Sequence[str], None] = "613a3a104186"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "competition_mappings",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "competition_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "provider_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["competition_id"],
            ["competitions.id"],
            name="fk_competition_mappings_competition_id",
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "provider",
            "provider_id",
            name="uq_competition_provider",
        ),
    )

    op.create_index(
        op.f("ix_competition_mappings_id"),
        "competition_mappings",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_competition_mappings_id"),
        table_name="competition_mappings",
    )

    op.drop_table("competition_mappings")