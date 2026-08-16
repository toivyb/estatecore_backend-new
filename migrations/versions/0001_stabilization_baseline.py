"""EstateCore stabilization baseline."""

from alembic import op
import sqlalchemy as sa

revision = "0001_stabilization"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("user", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("role", sa.String(32), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_user_email", "user", ["email"])
    op.create_table("lease", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False), sa.Column("property_name", sa.String(255), nullable=False), sa.Column("monthly_rent", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(32), nullable=False))
    op.create_index("ix_lease_tenant_id", "lease", ["tenant_id"])
    op.create_table("payment", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("lease_id", sa.Integer(), sa.ForeignKey("lease.id"), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("due_date", sa.Date(), nullable=False), sa.Column("paid_at", sa.DateTime(timezone=True)))
    op.create_index("ix_payment_lease_id", "payment", ["lease_id"])
    op.create_table("maintenance_request", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("priority", sa.String(16), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_maintenance_request_tenant_id", "maintenance_request", ["tenant_id"])
    op.create_table("access_credential", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False), sa.Column("plate", sa.String(32), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.UniqueConstraint("plate"))
    op.create_index("ix_access_credential_tenant_id", "access_credential", ["tenant_id"])
    op.create_index("ix_access_credential_plate", "access_credential", ["plate"])
    op.create_table("access_event", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("plate", sa.String(32), nullable=False), sa.Column("result", sa.String(16), nullable=False), sa.Column("reason", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_access_event_plate", "access_event", ["plate"])


def downgrade():
    op.drop_table("access_event")
    op.drop_table("access_credential")
    op.drop_table("maintenance_request")
    op.drop_table("payment")
    op.drop_table("lease")
    op.drop_table("user")
