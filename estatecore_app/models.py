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


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey("lease.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending")
    due_date = db.Column(db.Date, nullable=False)
    paid_at = db.Column(db.DateTime(timezone=True))


class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(16), nullable=False, default="normal")
    status = db.Column(db.String(32), nullable=False, default="open")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class AccessCredential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    plate = db.Column(db.String(32), unique=True, nullable=False, index=True)
    active = db.Column(db.Boolean, nullable=False, default=True)


class AccessEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(32), nullable=False, index=True)
    result = db.Column(db.String(16), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
