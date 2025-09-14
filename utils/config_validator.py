"""
Configuration validation utilities for EstateCore
"""
import os
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass

def validate_environment():
    """
    Validate environment configuration for EstateCore
    Raises ConfigValidationError if validation fails
    """
    errors = []
    warnings = []
    
    # Required variables
    required_vars = {
        'SECRET_KEY': {
            'min_length': 16,
            'description': 'Flask secret key for session security'
        },
        'DATABASE_URL': {
            'validator': _validate_database_url,
            'description': 'PostgreSQL database connection URL'
        }
    }
    
    # Check required variables
    for var_name, config in required_vars.items():
        value = os.environ.get(var_name)
        
        if not value:
            errors.append(f"{var_name} is required - {config['description']}")
            continue
            
        # Check minimum length
        if 'min_length' in config and len(value) < config['min_length']:
            errors.append(f"{var_name} must be at least {config['min_length']} characters")
            
        # Custom validator
        if 'validator' in config:
            try:
                config['validator'](value)
            except ValueError as e:
                errors.append(f"{var_name}: {str(e)}")
    
    # Optional variables with warnings
    optional_vars = {
        'JWT_SECRET_KEY': 'JWT authentication (will use SECRET_KEY if not set)',
        'CORS_ORIGINS': 'Cross-origin request handling',
        'FLASK_ENV': 'Flask environment mode (defaults to production)',
        'OPENALPR_API_KEY': 'License plate recognition functionality'
    }
    
    for var_name, description in optional_vars.items():
        if not os.environ.get(var_name):
            warnings.append(f"{var_name} not set - {description}")
    
    # Log results
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        logger.error(error_msg)
        raise ConfigValidationError(error_msg)
    
    if warnings:
        warning_msg = "Configuration warnings:\n" + "\n".join(f"  - {warn}" for warn in warnings)
        logger.warning(warning_msg)
    
    logger.info("Configuration validation passed")

def _validate_database_url(url):
    """Validate PostgreSQL database URL format"""
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in ['postgresql', 'postgres']:
            raise ValueError("Database URL must use postgresql:// or postgres:// scheme")
            
        if not parsed.hostname:
            raise ValueError("Database URL must include hostname")
            
        if not parsed.username:
            raise ValueError("Database URL must include username")
            
        if not parsed.password:
            raise ValueError("Database URL must include password")
            
        if not parsed.path or len(parsed.path.strip('/')) == 0:
            raise ValueError("Database URL must include database name")
            
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid database URL format: {str(e)}")

def get_config_summary():
    """Get a summary of current configuration (without sensitive values)"""
    config_info = {
        'SECRET_KEY': '✅ Set' if os.environ.get('SECRET_KEY') else '❌ Missing',
        'DATABASE_URL': '✅ Set' if os.environ.get('DATABASE_URL') else '❌ Missing',
        'JWT_SECRET_KEY': '✅ Set' if os.environ.get('JWT_SECRET_KEY') else '⚠️ Using SECRET_KEY',
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'production'),
        'CORS_ORIGINS': '✅ Set' if os.environ.get('CORS_ORIGINS') else '⚠️ Using defaults'
    }
    
    return config_info