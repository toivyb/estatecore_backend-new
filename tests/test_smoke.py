from datetime import date
import pytest
from estatecore_app import create_app
from estatecore_app.extensions import db
from estatecore_app.models import AccessCredential, Company, Lease, Payment, Property, User

@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "JWT_SECRET_KEY": "test-secret-that-is-at-least-32-bytes", "LPR_INTEGRATION_KEY": "lpr-test-key"})
    with app.app_context():
        db.create_all()
        company = Company(name="Demo Company"); db.session.add(company); db.session.flush()
        prop = Property(company_id=company.id, name="Demo Unit 1", address="1 Demo Way"); db.session.add(prop); db.session.flush()
        admin = User(email="admin@example.com", name="Demo Admin", role="company_admin", company_id=company.id); admin.set_password("safe-admin-password")
        tenant = User(email="tenant@example.com", name="Demo Tenant", role="tenant", company_id=company.id); tenant.set_password("safe-demo-password")
        db.session.add_all([admin, tenant]); db.session.flush()
        lease = Lease(tenant_id=tenant.id, company_id=company.id, property_id=prop.id, property_name=prop.name, monthly_rent=1200, status="active"); db.session.add(lease); db.session.flush()
        db.session.add(Payment(lease_id=lease.id, company_id=company.id, amount=1200, status="paid", due_date=date.today(), idempotency_key="initial-rent"))
        db.session.add(AccessCredential(tenant_id=tenant.id, company_id=company.id, property_id=prop.id, plate="ABC123", active=True))
        db.session.commit()
    yield app

def login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.get_json()["access_token"]}

def test_health_and_tenant_portal(app):
    client = app.test_client()
    assert client.get("/api/health").get_json() == {"status": "ok"}
    portal = client.get("/api/tenant/me", headers=login(client, "tenant@example.com", "safe-demo-password"))
    assert portal.status_code == 200
    assert portal.get_json()["lease"]["status"] == "active"

def test_maintenance_workflow(app):
    client = app.test_client()
    created = client.post("/api/maintenance", headers=login(client, "tenant@example.com", "safe-demo-password"), json={"description": "Leaking faucet", "priority": "urgent"})
    assert created.status_code == 201
    updated = client.patch("/api/admin/maintenance/" + str(created.get_json()["id"]), headers=login(client, "admin@example.com", "safe-admin-password"), json={"status": "assigned", "assigned_to": "Demo Plumbing"})
    assert updated.get_json()["status"] == "assigned"

def test_bills_and_idempotent_rent_charge(app):
    client = app.test_client(); headers = login(client, "admin@example.com", "safe-admin-password")
    assert client.post("/api/admin/bills", headers=headers, json={"vendor": "Water Utility", "category": "utilities", "amount": 88.25, "due_date": date.today().isoformat()}).status_code == 201
    lease_id = client.get("/api/admin/leases", headers=headers).get_json()[0]["id"]
    payload = {"due_date": date.today().isoformat(), "idempotency_key": "august-rent"}
    first = client.post(f"/api/admin/leases/{lease_id}/charges", headers=headers, json=payload)
    second = client.post(f"/api/admin/leases/{lease_id}/charges", headers=headers, json=payload)
    assert first.status_code == 201 and second.status_code == 200
    assert first.get_json()["id"] == second.get_json()["id"]

def test_lpr_requires_key_and_is_idempotent(app):
    client = app.test_client()
    assert client.post("/api/access/check", json={"plate": "ABC123", "event_id": "evt-1"}).status_code == 401
    headers = {"X-Integration-Key": "lpr-test-key"}
    first = client.post("/api/access/check", headers=headers, json={"plate": "ABC123", "event_id": "evt-1"})
    second = client.post("/api/access/check", headers=headers, json={"plate": "ABC123", "event_id": "evt-1"})
    assert first.status_code == 200
    assert second.get_json()["duplicate"] is True
