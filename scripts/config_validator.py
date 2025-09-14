"""
Environment Variable Validation Utility
Ensures all required environment variables are properly set
"""
import os
import sys
from urllib.parse import urlparse

def validate_required_env_vars():
    """Validate that all required environment variables are set"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    invalid_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        elif var == 'SECRET_KEY' and len(value) < 16:
            invalid_vars.append(f"{var} (must be at least 16 characters)")
        elif var == 'DATABASE_URL' and not validate_database_url(value):
            invalid_vars.append(f"{var} (invalid database URL format)")
    
    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nTIP: Copy .env.example to .env and fill in the values")
        return False
    
    if invalid_vars:
        print("ERROR: Invalid environment variable values:")
        for var in invalid_vars:
            print(f"  - {var}")
        return False
    
    print("SUCCESS: All required environment variables are properly configured")
    return True

def validate_database_url(url):
    """Validate database URL format"""
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ['postgresql', 'postgres'] and
            parsed.hostname and
            parsed.username and
            parsed.password and
            parsed.path and len(parsed.path) > 1
        )
    except Exception:
        return False

def validate_optional_vars():
    """Validate optional environment variables and provide warnings"""
    optional_vars = {
        'JWT_SECRET_KEY': 'JWT tokens will use SECRET_KEY',
        'CORS_ORIGINS': 'CORS will default to localhost origins',
        'FLASK_ENV': 'Will default to production mode',
    }
    
    warnings = []
    
    for var, message in optional_vars.items():
        if not os.environ.get(var):
            warnings.append(f"{var}: {message}")
    
    if warnings:
        print("\nWARNING: Optional environment variables not set:")
        for warning in warnings:
            print(f"  - {warning}")

if __name__ == "__main__":
    print("Validating EstateCore Environment Configuration...")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("SUCCESS: .env file loaded")
    except ImportError:
        print("WARNING: python-dotenv not installed, using system environment variables only")
    except Exception as e:
        print(f"WARNING: Could not load .env file: {e}")
    
    print()
    
    if validate_required_env_vars():
        validate_optional_vars()
        print("\nSUCCESS: Configuration validation successful!")
        sys.exit(0)
    else:
        print("\nERROR: Configuration validation failed!")
        sys.exit(1)