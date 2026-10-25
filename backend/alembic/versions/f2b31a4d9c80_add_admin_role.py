"""Add administrator roles to existing account tables."""
from alembic import op
import sqlalchemy as sa

revision = "f2b31a4d9c80"
down_revision = "d1a80c1f9c02"
branch_labels = None
depends_on = None


def upgrade():
    # Accounts were previously created at application startup, so a fresh
    # database may not have this table yet.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("users"):
        if "is_admin" not in {column["name"] for column in inspector.get_columns("users")}:
            op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("users"):
        if "is_admin" in {column["name"] for column in inspector.get_columns("users")}:
            op.drop_column("users", "is_admin")
