#!/usr/bin/env python3
"""Test new company/building/payment endpoints"""
from app import create_app

def test_new_endpoints():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Test new endpoints
            endpoints = [
                ('/api/companies', 'Companies'),
                ('/api/buildings', 'Buildings'),
                ('/api/rent-payments', 'Rent Payments'),
            ]
            
            all_good = True
            for endpoint, name in endpoints:
                response = client.get(endpoint)
                status = "OK" if response.status_code < 400 else "FAIL"
                print(f"{name}: {response.status_code} - {status}")
                if response.status_code >= 400:
                    all_good = False
                    print(f"  Error: {response.data}")
            
            if all_good:
                print("ALL NEW ENDPOINTS WORKING!")
            else:
                print("Some new endpoints failed")
            
            return all_good

if __name__ == "__main__":
    test_new_endpoints()