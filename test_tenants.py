#!/usr/bin/env python3
"""Test tenants endpoint specifically"""
from app import create_app, db, Tenant

def test_tenants():
    """Test tenants query specifically"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Testing tenants query...")
            tenants = Tenant.query.all()
            print(f"Found {len(tenants)} tenants in database")
            
            # Test the API endpoint
            with app.test_client() as client:
                print("Testing /api/tenants endpoint...")
                response = client.get('/api/tenants')
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json
                    print(f"API returned {len(data)} tenants")
                    if data:
                        print("Sample tenant data:")
                        print(data[0])
                else:
                    print(f"Error response: {response.data}")
            
            return True
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    test_tenants()