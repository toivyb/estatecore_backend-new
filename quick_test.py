#!/usr/bin/env python3
"""Quick test of updated models"""
from app import create_app

def quick_test():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Test tenants endpoint
            response = client.get('/api/tenants')
            print(f"Tenants: {response.status_code}")
            
            # Test properties endpoint  
            response = client.get('/api/properties')
            print(f"Properties: {response.status_code}")
            
            # Test users endpoint
            response = client.get('/api/users')
            print(f"Users: {response.status_code}")

if __name__ == "__main__":
    quick_test()