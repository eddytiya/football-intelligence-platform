"""replace competition mappings with external ids

Revision ID: 8d83ebb554e1
Revises: 3f3ba33a5c7b
Create Date: 2026-07-21 14:46:47.386963
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8d83ebb554e1"
down_revision: Union[str, Sequence[str], None] = "3f3ba33a5c7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Replace competition_mappings with generic external_ids.
    """

    op.create_table(
        "external_ids",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "entity_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "external_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "entity_type",
            "provider",
            "external_id",
            name="uq_external_entity",
        ),
    )

    op.create_index(
        "ix_external_lookup",
        "external_ids",
        [
            "entity_type",
            "provider",
            "external_id",
        ],
    )

    op.create_index(
        "ix_internal_lookup",
        "external_ids",
        [
            "entity_type",
            "entity_id",
        ],
    )

    op.drop_table("competition_mappings")


def downgrade() -> None:
    """
    Restore competition_mappings.
    """

    op.create_table(
        "competition_mappings",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
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

        sa.UniqueConstraint(
            "provider",
            "provider_id",
            name="uq_competition_provider",
        ),
    )

    op.drop_index("ix_internal_lookup", table_name="external_ids")
    op.drop_index("ix_external_lookup", table_name="external_ids")

    op.drop_table("external_ids")