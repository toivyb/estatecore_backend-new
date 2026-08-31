import os

from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt, migrate


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if app.config.get("ENVIRONMENT") == "production":
        missing = [
            name
            for name in ("SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL")
            if not os.environ.get(name)
        ]
        if missing:
            raise RuntimeError("Missing production settings: " + ", ".join(missing))

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    from .routes import api
    app.register_blueprint(api, url_prefix="/api")

    @app.cli.command("seed-demo")
    def seed_demo():
        from datetime import date
        import click
        from .models import AccessCredential, Company, Lease, Payment, Property, User
        admin_email = os.environ.get("ESTATECORE_ADMIN_EMAIL", "toivybraun@gmail.com").strip().lower()
        admin_password = os.environ.get("ESTATECORE_ADMIN_PASSWORD")
        if not admin_password:
            raise click.ClickException("ESTATECORE_ADMIN_PASSWORD must be set before seeding")
        company = Company.query.filter_by(name="EstateCore Demo").first()
        if not company:
            company = Company(name="EstateCore Demo")
            db.session.add(company); db.session.flush()
        prop = Property.query.filter_by(company_id=company.id, name="Demo Building").first()
        if not prop:
            prop = Property(company_id=company.id, name="Demo Building", address="123 Demo Street")
            db.session.add(prop); db.session.flush()
        users = {}
        for email, name, role, password in (
            (admin_email, "Toivy Braun", "super_admin", admin_password),
            ("tenant@demo.estatecore.local", "Demo Tenant", "tenant", "DemoTenant-ChangeMe-2026"),
        ):
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(email=email, name=name, role=role, company_id=company.id)
                db.session.add(user); db.session.flush()
            user.name = name
            user.role = role
            user.company_id = company.id
            user.set_password(password)
            users[role] = user
        lease = Lease.query.filter_by(tenant_id=users["tenant"].id, status="active").first()
        if not lease:
            lease = Lease(tenant_id=users["tenant"].id, company_id=company.id, property_id=prop.id, property_name=prop.name, monthly_rent=1200, status="active")
            db.session.add(lease); db.session.flush()
        if not Payment.query.filter_by(idempotency_key="demo-current-rent").first():
            db.session.add(Payment(lease_id=lease.id, company_id=company.id, amount=1200, due_date=date.today(), status="paid", idempotency_key="demo-current-rent"))
        if not AccessCredential.query.filter_by(plate="DEMO123").first():
            db.session.add(AccessCredential(tenant_id=users["tenant"].id, company_id=company.id, property_id=prop.id, plate="DEMO123", active=True))
        db.session.commit()
        print(f"Demo data ready. System admin: {admin_email}")
    return app
