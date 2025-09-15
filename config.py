import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_change_in_production")

    # Database URI from environment variable - handle Render's postgres:// URLs
    database_url = os.environ.get("DATABASE_URL", "postgresql://estatecore_user:StrongPassword123@localhost:5432/estatecore_dev")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    
    # Production settings
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = ENV == "development"

