#!/usr/bin/env python3
"""
Start Flask server with all latest endpoints
"""
import os
import sys

# Change to the correct directory
os.chdir(r'C:\Users\toivy\estatecore_project')

# Import the updated app
from app import app

if __name__ == '__main__':
    print("Starting EstateCore Server with ALL endpoints...")
    print("Available endpoints:")
    
    # List all routes
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/static'):
            methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"  {methods:12} {rule.rule}")
    
    print(f"\nServer starting on http://localhost:5002")
    print("Key endpoints:")
    print("  - User Management: /api/users")
    print("  - Set Password: /api/users/{id}/set-password")
    print("  - Switch User: /api/demo/switch-user/{id}")
    print("  - Health Check: /health")
    
    # Start server on port 5002 to avoid conflicts
    app.run(host='0.0.0.0', port=5002, debug=False)