#!/usr/bin/env python3
"""Simple test of key endpoints"""
from app import create_app

def simple_test():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Test key endpoints
            endpoints = [
                ('/health', 'Health check'),
                ('/api/properties', 'Properties'),
                ('/api/tenants', 'Tenants'),
                ('/api/users', 'Users'),
            ]
            
            all_good = True
            for endpoint, name in endpoints:
                response = client.get(endpoint)
                status = "OK" if response.status_code < 400 else "FAIL"
                print(f"{name}: {response.status_code} - {status}")
                if response.status_code >= 400:
                    all_good = False
            
            if all_good:
                print("ALL TESTS PASSED - READY TO DEPLOY!")
            else:
                print("Some tests failed")
            
            return all_good

if __name__ == "__main__":
    simple_test()