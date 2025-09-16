#!/usr/bin/env python3
"""
Test app.py with local sqlite database
"""
import os
import tempfile
from app import create_app, db

def test_local_app():
    """Test app with local database"""
    
    # Create a temporary database file
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Override environment variables for local testing
    os.environ['DATABASE_URL'] = f'sqlite:///{temp_db.name}'
    os.environ['CORS_ORIGINS'] = 'http://localhost:3000'
    
    try:
        print("Creating app with local database...")
        app = create_app()
        
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")
            
            # Test the properties endpoint
            with app.test_client() as client:
                print("Testing /health endpoint...")
                response = client.get('/health')
                print(f"Health status: {response.status_code}")
                if response.status_code == 200:
                    print(f"Health response: {response.json}")
                
                print("Testing /api/properties endpoint...")
                response = client.get('/api/properties')
                print(f"Properties status: {response.status_code}")
                if response.status_code == 200:
                    print(f"Properties response: {response.json}")
                else:
                    print(f"Properties error: {response.data}")
                
                print("Testing property creation...")
                test_property = {
                    'name': 'Test Property',
                    'address': '123 Test St',
                    'type': 'house',
                    'units': 1,
                    'description': 'A test property'
                }
                response = client.post('/api/properties', json=test_property)
                print(f"Create property status: {response.status_code}")
                if response.status_code == 201:
                    print(f"Create property response: {response.json}")
                else:
                    print(f"Create property error: {response.data}")
                
        print("Local app test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing local app: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_db.name)
        except:
            pass

if __name__ == "__main__":
    success = test_local_app()
    if success:
        print("Local app works correctly!")
    else:
        print("Local app test failed!")