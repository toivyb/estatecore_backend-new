"""access event administrative overrides

Revision ID: 0003_access_overrides
Revises: 0002_demo_workflows
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_access_overrides"
down_revision = "0002_demo_workflows"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("access_event") as batch:
        batch.add_column(sa.Column("overridden_by", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("override_note", sa.String(length=500), nullable=True))
        batch.create_index("ix_access_event_overridden_by", ["overridden_by"])
        batch.create_foreign_key("fk_access_event_overridden_by_user", "user", ["overridden_by"], ["id"])

def downgrade():
    with op.batch_alter_table("access_event") as batch:
        batch.drop_constraint("fk_access_event_overridden_by_user", type_="foreignkey")
        batch.drop_index("ix_access_event_overridden_by")
        batch.drop_column("override_note")
        batch.drop_column("overridden_by")
