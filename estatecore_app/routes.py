from datetime import date, datetime, timezone
from functools import wraps
from uuid import uuid4
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from .extensions import db
from .models import AccessCredential, AccessEvent, CompanyBill, Lease, MaintenanceRequest, Payment, Property, User

api = Blueprint("api", __name__)
ADMIN_ROLES = {"admin", "company_admin", "super_admin"}

def current_user():
    return db.session.get(User, int(get_jwt_identity()))

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user.role not in ADMIN_ROLES:
            return jsonify(error="admin access required"), 403
        return fn(user, *args, **kwargs)
    return wrapped

@api.get("/health")
def health():
    db.session.execute(db.text("SELECT 1"))
    return jsonify(status="ok")

@api.post("/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=payload.get("email", "").strip().lower()).first()
    if not user or not user.check_password(payload.get("password", "")):
        return jsonify(error="invalid credentials"), 401
    return jsonify(access_token=create_access_token(identity=str(user.id)), user={"name": user.name, "role": user.role})

@api.get("/tenant/me")
@jwt_required()
def tenant_me():
    user = current_user()
    if not user:
        return jsonify(error="user not found"), 404
    lease = Lease.query.filter_by(tenant_id=user.id, status="active").first()
    payments = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.due_date.desc()).all() if lease else []
    maintenance = MaintenanceRequest.query.filter_by(tenant_id=user.id).order_by(MaintenanceRequest.created_at.desc()).all()
    return jsonify(
        user={"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        lease=None if not lease else {"id": lease.id, "property": lease.property_name, "monthly_rent": float(lease.monthly_rent), "status": lease.status},
        payments=[{"id": p.id, "amount": float(p.amount), "status": p.status, "due_date": p.due_date.isoformat()} for p in payments],
        maintenance=[{"id": m.id, "description": m.description, "priority": m.priority, "status": m.status} for m in maintenance],
    )

@api.route("/maintenance", methods=["GET", "POST"])
@jwt_required()
def maintenance():
    user = current_user()
    if not user:
        return jsonify(error="user not found"), 404
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        description = payload.get("description", "").strip()
        lease = Lease.query.filter_by(tenant_id=user.id, status="active").first()
        if not description or not lease:
            return jsonify(error="description and active lease are required"), 400
        item = MaintenanceRequest(tenant_id=user.id, company_id=lease.company_id, property_id=lease.property_id, description=description, priority=payload.get("priority", "normal"))
        db.session.add(item); db.session.commit()
        return jsonify(id=item.id, status=item.status), 201
    items = MaintenanceRequest.query.filter_by(tenant_id=user.id).order_by(MaintenanceRequest.created_at.desc()).all()
    return jsonify([{"id": m.id, "description": m.description, "priority": m.priority, "status": m.status} for m in items])

@api.route("/admin/leases", methods=["GET", "POST"])
@admin_required
def admin_leases(admin):
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        tenant = db.session.get(User, payload.get("tenant_id"))
        prop = db.session.get(Property, payload.get("property_id"))
        if not tenant or not prop or tenant.company_id != admin.company_id or prop.company_id != admin.company_id:
            return jsonify(error="tenant or property not found in company"), 404
        item = Lease(tenant_id=tenant.id, company_id=admin.company_id, property_id=prop.id, property_name=prop.name, monthly_rent=payload.get("monthly_rent"), status="active")
        db.session.add(item); db.session.commit()
        return jsonify(id=item.id), 201
    items = Lease.query.filter_by(company_id=admin.company_id).all()
    users = {u.id: u for u in User.query.filter_by(company_id=admin.company_id).all()}
    return jsonify([{"id": x.id, "tenant_id": x.tenant_id, "tenant": users.get(x.tenant_id).name if users.get(x.tenant_id) else "Unknown", "property": x.property_name, "property_id": x.property_id, "rent": float(x.monthly_rent), "status": x.status} for x in items])

@api.get("/admin/setup")
@admin_required
def admin_setup(admin):
    tenants = User.query.filter_by(company_id=admin.company_id, role="tenant").order_by(User.name).all()
    properties = Property.query.filter_by(company_id=admin.company_id).order_by(Property.name).all()
    return jsonify(
        tenants=[{"id": x.id, "name": x.name, "email": x.email} for x in tenants],
        properties=[{"id": x.id, "name": x.name, "address": x.address} for x in properties],
    )

@api.get("/admin/payments")
@admin_required
def admin_payments(admin):
    items = Payment.query.filter_by(company_id=admin.company_id).order_by(Payment.due_date.desc()).all()
    leases = {x.id: x for x in Lease.query.filter_by(company_id=admin.company_id).all()}
    users = {x.id: x for x in User.query.filter_by(company_id=admin.company_id).all()}
    result = []
    for item in items:
        lease = leases.get(item.lease_id)
        tenant = users.get(lease.tenant_id) if lease else None
        result.append({"id": item.id, "lease_id": item.lease_id, "tenant": tenant.name if tenant else "Unknown", "property": lease.property_name if lease else "Unknown", "amount": float(item.amount), "due_date": item.due_date.isoformat(), "status": item.status})
    return jsonify(result)

@api.post("/admin/leases/<int:lease_id>/charges")
@admin_required
def create_charge(admin, lease_id):
    payload = request.get_json(silent=True) or {}
    lease = Lease.query.filter_by(id=lease_id, company_id=admin.company_id).first()
    key = payload.get("idempotency_key", "").strip()
    if not lease or not key or not payload.get("due_date"):
        return jsonify(error="lease, due_date and idempotency_key are required"), 400
    existing = Payment.query.filter_by(idempotency_key=key).first()
    if existing:
        return jsonify(id=existing.id, status=existing.status), 200
    item = Payment(lease_id=lease.id, company_id=admin.company_id, amount=payload.get("amount", lease.monthly_rent), due_date=date.fromisoformat(payload["due_date"]), status="pending", idempotency_key=key)
    db.session.add(item); db.session.commit()
    return jsonify(id=item.id, status=item.status), 201

@api.patch("/admin/payments/<int:payment_id>")
@admin_required
def update_payment(admin, payment_id):
    item = Payment.query.filter_by(id=payment_id, company_id=admin.company_id).first()
    if not item:
        return jsonify(error="payment not found"), 404
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in {"pending", "paid", "unpaid", "failed"}:
        return jsonify(error="invalid payment status"), 400
    item.status = status
    item.paid_at = datetime.now(timezone.utc) if status == "paid" else None
    item.processor_transaction_id = payload.get("processor_transaction_id")
    db.session.commit()
    return jsonify(id=item.id, status=item.status)

@api.get("/admin/maintenance")
@admin_required
def admin_maintenance(admin):
    items = MaintenanceRequest.query.filter_by(company_id=admin.company_id).order_by(MaintenanceRequest.created_at.desc()).all()
    users = {u.id: u for u in User.query.filter_by(company_id=admin.company_id).all()}
    return jsonify([{"id": m.id, "tenant": users.get(m.tenant_id).name if users.get(m.tenant_id) else "Unknown", "description": m.description, "priority": m.priority, "status": m.status, "assigned_to": m.assigned_to} for m in items])

@api.patch("/admin/maintenance/<int:item_id>")
@admin_required
def update_maintenance(admin, item_id):
    item = MaintenanceRequest.query.filter_by(id=item_id, company_id=admin.company_id).first()
    if not item:
        return jsonify(error="maintenance request not found"), 404
    payload = request.get_json(silent=True) or {}
    if payload.get("status") not in {"open", "assigned", "completed"}:
        return jsonify(error="invalid maintenance status"), 400
    item.status = payload["status"]; item.assigned_to = payload.get("assigned_to")
    db.session.commit()
    return jsonify(id=item.id, status=item.status)

@api.route("/admin/bills", methods=["GET", "POST"])
@admin_required
def company_bills(admin):
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        try:
            item = CompanyBill(company_id=admin.company_id, property_id=payload.get("property_id"), vendor=payload["vendor"].strip(), category=payload["category"].strip(), amount=payload["amount"], due_date=date.fromisoformat(payload["due_date"]), status=payload.get("status", "unpaid"), reference=payload.get("reference"))
        except (KeyError, ValueError, AttributeError):
            return jsonify(error="vendor, category, amount and due_date are required"), 400
        db.session.add(item); db.session.commit()
        return jsonify(id=item.id, status=item.status), 201
    items = CompanyBill.query.filter_by(company_id=admin.company_id).order_by(CompanyBill.due_date.desc()).all()
    return jsonify([{"id": b.id, "vendor": b.vendor, "category": b.category, "amount": float(b.amount), "due_date": b.due_date.isoformat(), "status": b.status} for b in items])

@api.patch("/admin/bills/<int:item_id>")
@admin_required
def update_bill(admin, item_id):
    item = CompanyBill.query.filter_by(id=item_id, company_id=admin.company_id).first()
    if not item:
        return jsonify(error="bill not found"), 404
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"unpaid", "paid", "overdue"}:
        return jsonify(error="invalid bill status"), 400
    item.status = status
    db.session.commit()
    return jsonify(id=item.id, status=item.status)

@api.get("/admin/access/events")
@admin_required
def access_events(admin):
    items = AccessEvent.query.filter_by(company_id=admin.company_id).order_by(AccessEvent.created_at.desc()).limit(100).all()
    return jsonify([{"id": x.id, "plate": x.plate, "result": x.result, "reason": x.reason, "created_at": x.created_at.isoformat(), "override_note": x.override_note} for x in items])

@api.patch("/admin/access/events/<int:event_id>/override")
@admin_required
def override_access_event(admin, event_id):
    item = AccessEvent.query.filter_by(id=event_id, company_id=admin.company_id).first()
    payload = request.get_json(silent=True) or {}
    result = payload.get("result")
    note = payload.get("note", "").strip()
    if not item:
        return jsonify(error="access event not found"), 404
    if result not in {"granted", "denied"} or not note:
        return jsonify(error="result and override note are required"), 400
    item.result = result
    item.reason = "manual administrative override"
    item.overridden_by = admin.id
    item.override_note = note
    db.session.commit()
    return jsonify(id=item.id, result=item.result, override_note=item.override_note)

@api.post("/access/check")
def access_check():
    expected_key = current_app.config.get("LPR_INTEGRATION_KEY")
    if expected_key and request.headers.get("X-Integration-Key") != expected_key:
        return jsonify(error="invalid integration key"), 401
    payload = request.get_json(silent=True) or {}
    plate = payload.get("plate", "").strip().upper()
    event_key = payload.get("event_id", "").strip() or str(uuid4())
    existing = AccessEvent.query.filter_by(event_key=event_key).first()
    if existing:
        return jsonify(access=existing.result, reason=existing.reason, duplicate=True), 200 if existing.result == "granted" else 403
    credential = AccessCredential.query.filter_by(plate=plate, active=True).first() if plate else None
    lease = Lease.query.filter_by(tenant_id=credential.tenant_id, property_id=credential.property_id, status="active").first() if credential else None
    current_payment = Payment.query.filter(Payment.lease_id == lease.id, Payment.due_date <= date.today()).order_by(Payment.due_date.desc()).first() if lease else None
    granted = bool(credential and lease and current_payment and current_payment.status == "paid")
    reason = "current rent paid" if granted else "no active credential, lease, or paid rent"
    if credential:
        db.session.add(AccessEvent(plate=plate, result="granted" if granted else "denied", reason=reason, company_id=credential.company_id, property_id=credential.property_id, event_key=event_key))
        db.session.commit()
    return jsonify(access="granted" if granted else "denied", reason=reason), 200 if granted else 403
