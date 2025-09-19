#!/usr/bin/env python3
"""Debug script to check route registration"""

from app import create_app

# Create app instance
app = create_app()

# Print all registered routes
print("Registered routes:")
for rule in app.url_map.iter_rules():
    methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
    print(f"  {rule.endpoint}: {rule.rule} [{methods}]")

# Check specifically for properties routes
properties_routes = [rule for rule in app.url_map.iter_rules() if 'properties' in rule.rule]
print(f"\nProperties routes found: {len(properties_routes)}")
for route in properties_routes:
    methods = ', '.join(route.methods - {'HEAD', 'OPTIONS'})
    print(f"  {route.rule} [{methods}]")