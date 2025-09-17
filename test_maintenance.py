#!/usr/bin/env python3
"""Test maintenance endpoint"""
from app import create_app

def test_maintenance():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            response = client.get('/api/maintenance')
            print(f"Maintenance: {response.status_code} - {'OK' if response.status_code < 400 else 'FAIL'}")
            if response.status_code < 400:
                print(f"  Response: {response.json}")
            else:
                print(f"  Error: {response.data}")

if __name__ == "__main__":
    test_maintenance()