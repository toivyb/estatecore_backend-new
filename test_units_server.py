#!/usr/bin/env python3
"""
Minimal server to test units endpoints
"""
import sys
sys.path.insert(0, '.')

from app import app

if __name__ == '__main__':
    print("=== STARTING UNITS TEST SERVER ===")
    
    # Verify units routes exist
    units_routes = [rule for rule in app.url_map.iter_rules() if 'units' in rule.rule]
    print(f"Units routes found: {len(units_routes)}")
    for rule in units_routes:
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    # Test with test client first
    print("\n=== TESTING WITH TEST CLIENT ===")
    with app.test_client() as client:
        response = client.get('/api/units?property_id=1')
        print(f"Test client GET /api/units: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Units returned: {len(data)}")
        
    print("\n=== STARTING HTTP SERVER ON PORT 5002 ===")
    print("Test with: curl http://localhost:5002/api/units?property_id=1")
    print("Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)