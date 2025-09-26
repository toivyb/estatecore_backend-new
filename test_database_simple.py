#!/usr/bin/env python3
"""
Database connectivity and persistence test for Render database
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import app components
from app import create_app, db

def test_database_connection():
    """Test basic database connection"""
    print("Testing database connection...")
    
    try:
        app = create_app()
        with app.app_context():
            # Test basic database connection
            result = db.session.execute(db.text("SELECT 1 as test")).fetchone()
            if result and result[0] == 1:
                print("SUCCESS: Database connection established!")
                return True
            else:
                print("FAILED: Database connection test failed")
                return False
    except Exception as e:
        print(f"FAILED: Database connection error: {str(e)}")
        return False

def test_properties_crud():
    """Test Properties CRUD operations with actual database"""
    print("\nTesting Properties CRUD operations...")
    
    try:
        app = create_app()
        with app.app_context():
            # Test CREATE - Insert a test property
            test_property_data = {
                'organization_id': 1,
                'name': 'Database Test Property',
                'street_address': '123 Test Street',
                'city': 'Test City',
                'state': 'TS',
                'zip_code': '12345',
                'type': 'APARTMENT',
                'description': 'Test property for database verification',
                'units': 5,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_deleted': False
            }
            
            # Insert property
            result = db.session.execute(db.text("""
                INSERT INTO properties (
                    organization_id, name, street_address, city, state, zip_code, 
                    property_type, description, total_units, is_active, 
                    created_at, updated_at, is_deleted
                ) VALUES (
                    :organization_id, :name, :street_address, :city, :state, :zip_code,
                    :type, :description, :units, :is_active, 
                    :created_at, :updated_at, :is_deleted
                ) RETURNING id
            """), test_property_data)
            
            property_id = result.fetchone()[0]
            db.session.commit()
            print(f"SUCCESS: Property created with ID: {property_id}")
            
            # Test READ - Fetch the property back
            result = db.session.execute(db.text("""
                SELECT id, name, street_address, property_type, total_units 
                FROM properties 
                WHERE id = :property_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'property_id': property_id}).fetchone()
            
            if result:
                print(f"SUCCESS: Property retrieved: {result[1]} at {result[2]} ({result[4]} units)")
            else:
                print("FAILED: Failed to retrieve created property")
                return False
            
            # Test UPDATE - Modify the property
            db.session.execute(db.text("""
                UPDATE properties 
                SET name = :new_name, updated_at = :updated_at
                WHERE id = :property_id
            """), {
                'property_id': property_id,
                'new_name': 'Updated Database Test Property',
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            print("SUCCESS: Property updated successfully")
            
            # Verify update
            result = db.session.execute(db.text("""
                SELECT name FROM properties WHERE id = :property_id
            """), {'property_id': property_id}).fetchone()
            
            if result and result[0] == 'Updated Database Test Property':
                print("SUCCESS: Property update verified in database")
            else:
                print("FAILED: Property update not reflected in database")
                return False
            
            # Test DELETE - Remove the test property
            db.session.execute(db.text("""
                UPDATE properties 
                SET is_deleted = true, updated_at = :updated_at
                WHERE id = :property_id
            """), {
                'property_id': property_id,
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            print("SUCCESS: Property soft-deleted successfully")
            
            # Verify deletion (should not appear in active queries)
            result = db.session.execute(db.text("""
                SELECT id FROM properties 
                WHERE id = :property_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'property_id': property_id}).fetchone()
            
            if not result:
                print("SUCCESS: Property deletion verified - not visible in active queries")
            else:
                print("FAILED: Property still visible after deletion")
                return False
                
            print("SUCCESS: Properties CRUD operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"FAILED: Properties CRUD test failed: {str(e)}")
        db.session.rollback()
        return False

def show_database_statistics():
    """Show current database statistics"""
    print("\nDatabase Statistics:")
    
    try:
        app = create_app()
        with app.app_context():
            # Count active records
            tables = ['properties', 'users', 'tenants']
            
            for table in tables:
                try:
                    result = db.session.execute(db.text(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE is_deleted = false OR is_deleted IS NULL
                    """)).fetchone()
                    
                    active_count = result[0] if result else 0
                    print(f"  {table.capitalize()}: {active_count} active records")
                    
                except Exception as e:
                    print(f"  {table.capitalize()}: Error counting records - {str(e)}")
            
    except Exception as e:
        print(f"FAILED: Failed to get database statistics: {str(e)}")

def test_actual_api_endpoints():
    """Test actual API endpoints to verify they work with database"""
    print("\nTesting actual API endpoints...")
    
    try:
        app = create_app()
        with app.test_client() as client:
            # Test Properties GET endpoint
            response = client.get('/api/properties')
            if response.status_code == 200:
                properties = response.get_json()
                print(f"SUCCESS: GET /api/properties returned {len(properties)} properties")
            else:
                print(f"FAILED: GET /api/properties returned status {response.status_code}")
                return False
            
            # Test Users GET endpoint  
            response = client.get('/api/users')
            if response.status_code == 200:
                users = response.get_json()
                print(f"SUCCESS: GET /api/users returned {len(users)} users")
            else:
                print(f"FAILED: GET /api/users returned status {response.status_code}")
                return False
                
            # Test Tenants GET endpoint
            response = client.get('/api/tenants')
            if response.status_code == 200:
                tenants = response.get_json()
                print(f"SUCCESS: GET /api/tenants returned {len(tenants)} tenants")
            else:
                print(f"FAILED: GET /api/tenants returned status {response.status_code}")
                return False
            
            print("SUCCESS: All API endpoints responding correctly!")
            return True
            
    except Exception as e:
        print(f"FAILED: API endpoint test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("EstateCore Render Database Verification Test")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("\nFAILED: Database connection failed. Please check your Render database configuration.")
        return False
    
    # Show current database stats
    show_database_statistics()
    
    # Test CRUD operations
    tests_passed = 0
    total_tests = 2
    
    if test_properties_crud():
        tests_passed += 1
        
    if test_actual_api_endpoints():
        tests_passed += 1
    
    # Final results
    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: ALL TESTS PASSED! Your Render database is working perfectly!")
        print("- Data persistence verified")
        print("- CRUD operations working correctly")
        print("- API endpoints responding properly")
        print("- Database connectivity confirmed")
        return True
    else:
        print("WARNING: Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    main()