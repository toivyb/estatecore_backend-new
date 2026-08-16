from datetime import date

import pytest

from estatecore_app import create_app
from estatecore_app.extensions import db
from estatecore_app.models import AccessCredential, Lease, Payment, User


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "JWT_SECRET_KEY": "test-secret-that-is-at-least-32-bytes",
    })
    with app.app_context():
        db.create_all()
        user = User(email="tenant@example.com", name="Demo Tenant", role="tenant")
        user.set_password("safe-demo-password")
        db.session.add(user)
        db.session.flush()
        lease = Lease(tenant_id=user.id, property_name="Demo Unit 1", monthly_rent=1200, status="active")
        db.session.add(lease)
        db.session.flush()
        db.session.add(Payment(lease_id=lease.id, amount=1200, status="paid", due_date=date.today()))
        db.session.add(AccessCredential(tenant_id=user.id, plate="ABC123", active=True))
        db.session.commit()
    yield app


def test_health(app):
    assert app.test_client().get("/api/health").get_json() == {"status": "ok"}


def test_login_and_tenant_portal(app):
    client = app.test_client()
    response = client.post("/api/auth/login", json={
        "email": "tenant@example.com",
        "password": "safe-demo-password",
    })
    assert response.status_code == 200
    token = response.get_json()["access_token"]
    portal = client.get("/api/tenant/me", headers={"Authorization": f"Bearer {token}"})
    assert portal.status_code == 200
    assert portal.get_json()["lease"]["status"] == "active"


def test_access_requires_current_paid_lease(app):
    client = app.test_client()
    assert client.post("/api/access/check", json={"plate": "ABC123"}).status_code == 200
    assert client.post("/api/access/check", json={"plate": "UNKNOWN"}).status_code == 403
