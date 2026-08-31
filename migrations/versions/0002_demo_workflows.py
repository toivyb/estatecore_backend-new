"""Company-scoped demo workflows."""
from alembic import op
import sqlalchemy as sa

revision = "0002_demo_workflows"
down_revision = "0001_stabilization"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("company", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(255), nullable=False, unique=True))
    op.create_table("property", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("address", sa.String(500), nullable=False))
    op.create_index("ix_property_company_id", "property", ["company_id"])
    op.add_column("user", sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.id")))
    op.create_index("ix_user_company_id", "user", ["company_id"])
    for table in ("lease", "payment", "maintenance_request", "access_credential", "access_event"):
        op.add_column(table, sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=True))
        op.create_index(f"ix_{table}_company_id", table, ["company_id"])
    for table in ("lease", "maintenance_request", "access_credential", "access_event"):
        op.add_column(table, sa.Column("property_id", sa.Integer(), sa.ForeignKey("property.id"), nullable=True))
        op.create_index(f"ix_{table}_property_id", table, ["property_id"])
    op.add_column("payment", sa.Column("idempotency_key", sa.String(128)))
    op.add_column("payment", sa.Column("processor_transaction_id", sa.String(255)))
    op.create_unique_constraint("uq_payment_idempotency_key", "payment", ["idempotency_key"])
    op.create_unique_constraint("uq_payment_processor_transaction_id", "payment", ["processor_transaction_id"])
    op.add_column("maintenance_request", sa.Column("assigned_to", sa.String(255)))
    op.add_column("access_event", sa.Column("event_key", sa.String(128)))
    op.create_unique_constraint("uq_access_event_event_key", "access_event", ["event_key"])
    op.create_table("company_bill", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False), sa.Column("property_id", sa.Integer(), sa.ForeignKey("property.id")), sa.Column("vendor", sa.String(255), nullable=False), sa.Column("category", sa.String(64), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("due_date", sa.Date(), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("reference", sa.String(255)))
    op.create_index("ix_company_bill_company_id", "company_bill", ["company_id"])
    op.create_index("ix_company_bill_property_id", "company_bill", ["property_id"])

def downgrade():
    op.drop_table("company_bill")
    op.drop_constraint("uq_access_event_event_key", "access_event", type_="unique")
    op.drop_column("access_event", "event_key")
    op.drop_column("maintenance_request", "assigned_to")
    op.drop_constraint("uq_payment_processor_transaction_id", "payment", type_="unique")
    op.drop_constraint("uq_payment_idempotency_key", "payment", type_="unique")
    op.drop_column("payment", "processor_transaction_id"); op.drop_column("payment", "idempotency_key")
    for table in ("access_event", "access_credential", "maintenance_request", "lease"):
        op.drop_column(table, "property_id")
    for table in ("access_event", "access_credential", "maintenance_request", "payment", "lease"):
        op.drop_column(table, "company_id")
    op.drop_column("user", "company_id")
    op.drop_table("property"); op.drop_table("company")
