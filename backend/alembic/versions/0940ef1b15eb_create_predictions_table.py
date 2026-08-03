"""create predictions table

Revision ID: 0940ef1b15eb
Revises: fa5056ac3545
Create Date: 2026-07-25 16:04:05.060546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0940ef1b15eb'
down_revision: Union[str, Sequence[str], None] = 'fa5056ac3545'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('prediction', sa.String(length=30), nullable=False),
        sa.Column('home_probability', sa.Float(), nullable=False),
        sa.Column('draw_probability', sa.Float(), nullable=False),
        sa.Column('away_probability', sa.Float(), nullable=False),
        sa.Column(
            'predicted_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['match_id'],
            ['matches.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(
        op.f('ix_predictions_id'),
        'predictions',
        ['id'],
        unique=False,
    )

    op.create_index(
        op.f('ix_predictions_match_id'),
        'predictions',
        ['match_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_predictions_match_id'),
        table_name='predictions',
    )

    op.drop_index(
        op.f('ix_predictions_id'),
        table_name='predictions',
    )

    op.drop_table('predictions')