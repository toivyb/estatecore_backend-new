from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from .extensions import db
from .models import AccessCredential, AccessEvent, Lease, MaintenanceRequest, Payment, User

api = Blueprint("api", __name__)


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
    return jsonify(access_token=create_access_token(identity=str(user.id)))


@api.get("/tenant/me")
@jwt_required()
def tenant_me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify(error="user not found"), 404
    lease = Lease.query.filter_by(tenant_id=user.id, status="active").first()
    payments = []
    if lease:
        payments = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.due_date.desc()).all()
    return jsonify(
        user={"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        lease=None if not lease else {
            "id": lease.id,
            "property": lease.property_name,
            "monthly_rent": float(lease.monthly_rent),
            "status": lease.status,
        },
        payments=[{
            "id": item.id,
            "amount": float(item.amount),
            "status": item.status,
            "due_date": item.due_date.isoformat(),
        } for item in payments],
    )


@api.route("/maintenance", methods=["GET", "POST"])
@jwt_required()
def maintenance():
    tenant_id = int(get_jwt_identity())
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        description = payload.get("description", "").strip()
        if not description:
            return jsonify(error="description is required"), 400
        item = MaintenanceRequest(
            tenant_id=tenant_id,
            description=description,
            priority=payload.get("priority", "normal"),
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(id=item.id, status=item.status), 201
    items = MaintenanceRequest.query.filter_by(tenant_id=tenant_id).order_by(
        MaintenanceRequest.created_at.desc()
    ).all()
    return jsonify([{
        "id": item.id,
        "description": item.description,
        "priority": item.priority,
        "status": item.status,
    } for item in items])


@api.post("/access/check")
def access_check():
    payload = request.get_json(silent=True) or {}
    plate = payload.get("plate", "").strip().upper()
    credential = AccessCredential.query.filter_by(plate=plate, active=True).first() if plate else None
    lease = None
    if credential:
        lease = Lease.query.filter_by(tenant_id=credential.tenant_id, status="active").first()
    current_payment = None
    if lease:
        current_payment = Payment.query.filter(
            Payment.lease_id == lease.id,
            Payment.due_date <= date.today(),
        ).order_by(Payment.due_date.desc()).first()
    granted = bool(credential and lease and current_payment and current_payment.status == "paid")
    reason = "current rent paid" if granted else "no active credential, lease, or paid rent"
    db.session.add(AccessEvent(plate=plate or "UNKNOWN", result="granted" if granted else "denied", reason=reason))
    db.session.commit()
    return jsonify(access="granted" if granted else "denied", reason=reason), 200 if granted else 403
