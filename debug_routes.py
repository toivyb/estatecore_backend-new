#!/usr/bin/env python3
"""
Debug Flask routes to identify units endpoint issue
"""
from app import app

print("=== DEBUGGING FLASK ROUTES ===")
print("All registered routes:")

for rule in app.url_map.iter_rules():
    methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {methods:20} {rule.rule:30} -> {rule.endpoint}")

print("\n=== UNITS SPECIFIC ROUTES ===")
units_routes = [rule for rule in app.url_map.iter_rules() if 'units' in rule.rule]
for rule in units_routes:
    methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {methods:20} {rule.rule:30} -> {rule.endpoint}")

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")
print(f"Units routes: {len(units_routes)}")

# Test the route matching
print("\n=== TESTING ROUTE MATCHING ===")
with app.test_request_context('/api/units?property_id=1', method='GET'):
    try:
        endpoint, values = app.url_map.bind('localhost').match('/api/units')
        print(f"Route match successful: endpoint={endpoint}, values={values}")
    except Exception as e:
        print(f"Route match failed: {e}")

# Test specific units function exists
print("\n=== TESTING FUNCTION AVAILABILITY ===")
try:
    from app import get_units, create_unit, update_unit, delete_unit
    print("✓ All units functions imported successfully")
    print(f"  get_units: {get_units}")
    print(f"  create_unit: {create_unit}")
    print(f"  update_unit: {update_unit}")
    print(f"  delete_unit: {delete_unit}")
except ImportError as e:
    print(f"✗ Function import failed: {e}")

print("\n=== TESTING WITH TEST CLIENT ===")
with app.test_client() as client:
    response = client.get('/api/units?property_id=1')
    print(f"Test client response: {response.status_code}")
    if response.status_code == 200:
        print("✓ Test client works - issue is with HTTP server")
    else:
        print(f"✗ Test client also fails: {response.get_data(as_text=True)}")