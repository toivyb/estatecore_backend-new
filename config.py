import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")

    # Database URI from environment variable
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable must be set")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

