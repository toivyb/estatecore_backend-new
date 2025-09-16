#!/usr/bin/env python3
"""Test properties endpoint specifically"""
from app import create_app, db, Property

def test_properties():
    """Test properties query specifically"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Testing properties query...")
            properties = Property.query.all()
            print(f"Found {len(properties)} properties in database")
            
            # Test the API endpoint
            with app.test_client() as client:
                print("Testing /api/properties endpoint...")
                response = client.get('/api/properties')
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json
                    print(f"API returned {len(data)} properties")
                    if data:
                        print("Sample property data:")
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
    test_properties()