import os


def _database_url():
    value = os.environ.get("DATABASE_URL", "sqlite:///estatecore.db")
    if value.startswith("postgres://"):
        value = value.replace("postgres://", "postgresql://", 1)
    return value


class Config:
    ENVIRONMENT = os.environ.get("ESTATECORE_ENV", "development")
    SECRET_KEY = os.environ.get("SECRET_KEY", "development-only-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    ]
