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
    return app
