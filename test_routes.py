#!/usr/bin/env python3
"""Test script to check Flask route registration"""

# Import the app from app.py
from app import app

def list_routes():
    """List all registered routes in the Flask app"""
    print("Registered Flask Routes:")
    print("-" * 50)
    
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        print(f"{rule.rule:40} {methods}")
    
    print("-" * 50)
    print(f"Total routes: {len(list(app.url_map.iter_rules()))}")

if __name__ == '__main__':
    list_routes()