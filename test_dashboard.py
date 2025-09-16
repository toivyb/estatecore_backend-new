#!/usr/bin/env python3
"""Test dashboard endpoints"""
from app import create_app

def test_dashboard():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Test dashboard endpoints
            endpoints = [
                ('/dashboard', 'Dashboard'),
                ('/api/ai/lease-expiration-check', 'Lease Expiration Check'),
            ]
            
            all_good = True
            for endpoint, name in endpoints:
                response = client.get(endpoint)
                status = "OK" if response.status_code < 400 else "FAIL"
                print(f"{name}: {response.status_code} - {status}")
                if response.status_code >= 400:
                    all_good = False
                    print(f"  Error: {response.data}")
                else:
                    print(f"  Response: {response.json}")
            
            if all_good:
                print("ALL DASHBOARD ENDPOINTS WORKING!")
            else:
                print("Some dashboard endpoints failed")
            
            return all_good

if __name__ == "__main__":
    test_dashboard()