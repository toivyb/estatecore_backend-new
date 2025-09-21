#!/usr/bin/env python3
"""
WSGI entry point for EstateCore production deployment
"""
import os
from simple_app import create_app

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# Create application instance
application = create_app()
app = application

if __name__ == "__main__":
    # For development/testing
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
