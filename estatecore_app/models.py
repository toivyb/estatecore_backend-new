from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="tenant")
    password_hash = db.Column(db.String(255), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), index=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Lease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    property_name = db.Column(db.String(255), nullable=False)
    monthly_rent = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="active")
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False, index=True)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey("lease.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending")
    due_date = db.Column(db.Date, nullable=False)
    paid_at = db.Column(db.DateTime(timezone=True))
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    idempotency_key = db.Column(db.String(128), unique=True, nullable=False)
    processor_transaction_id = db.Column(db.String(255), unique=True)


class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(16), nullable=False, default="normal")
    status = db.Column(db.String(32), nullable=False, default="open")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False, index=True)
    assigned_to = db.Column(db.String(255))


class AccessCredential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    plate = db.Column(db.String(32), unique=True, nullable=False, index=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False, index=True)


class AccessEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(32), nullable=False, index=True)
    result = db.Column(db.String(16), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False, index=True)
    event_key = db.Column(db.String(128), unique=True, nullable=False)


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)


class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(500), nullable=False)


class CompanyBill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), index=True)
    vendor = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="unpaid")
    reference = db.Column(db.String(255))
