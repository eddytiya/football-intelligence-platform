"""create cached historical top scorer rows"""

from alembic import op
import sqlalchemy as sa

revision = "d1a80c1f9c02"
down_revision = "90086b5fadb6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "player_season_scorers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("competition_id", sa.Integer(), sa.ForeignKey("competitions.id"), nullable=False),
        sa.Column("season_year", sa.Integer(), nullable=False),
        sa.Column("player_api_id", sa.Integer(), nullable=False),
        sa.Column("player_name", sa.String(), nullable=False),
        sa.Column("team_name", sa.String()),
        sa.Column("team_crest", sa.String()),
        sa.Column("goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("appearances", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("competition_id", "season_year", "player_api_id", name="uq_scorer_competition_season_player"),
    )
    op.create_index("ix_player_season_scorers_competition", "player_season_scorers", ["competition_id"])
    op.create_index("ix_player_season_scorers_season", "player_season_scorers", ["season_year"])


def downgrade():
    op.drop_index("ix_player_season_scorers_season", table_name="player_season_scorers")
    op.drop_index("ix_player_season_scorers_competition", table_name="player_season_scorers")
    op.drop_table("player_season_scorers")
