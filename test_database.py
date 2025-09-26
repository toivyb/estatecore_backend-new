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
    print("🔍 Testing database connection...")
    
    try:
        app = create_app()
        with app.app_context():
            # Test basic database connection
            result = db.session.execute(db.text("SELECT 1 as test")).fetchone()
            if result and result[0] == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection test failed")
                return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False

def test_properties_crud():
    """Test Properties CRUD operations with actual database"""
    print("\n🏢 Testing Properties CRUD operations...")
    
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
            print(f"✅ Property created with ID: {property_id}")
            
            # Test READ - Fetch the property back
            result = db.session.execute(db.text("""
                SELECT id, name, street_address, property_type, total_units 
                FROM properties 
                WHERE id = :property_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'property_id': property_id}).fetchone()
            
            if result:
                print(f"✅ Property retrieved: {result[1]} at {result[2]} ({result[4]} units)")
            else:
                print("❌ Failed to retrieve created property")
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
            print("✅ Property updated successfully")
            
            # Verify update
            result = db.session.execute(db.text("""
                SELECT name FROM properties WHERE id = :property_id
            """), {'property_id': property_id}).fetchone()
            
            if result and result[0] == 'Updated Database Test Property':
                print("✅ Property update verified in database")
            else:
                print("❌ Property update not reflected in database")
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
            print("✅ Property soft-deleted successfully")
            
            # Verify deletion (should not appear in active queries)
            result = db.session.execute(db.text("""
                SELECT id FROM properties 
                WHERE id = :property_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'property_id': property_id}).fetchone()
            
            if not result:
                print("✅ Property deletion verified - not visible in active queries")
            else:
                print("❌ Property still visible after deletion")
                return False
                
            print("✅ Properties CRUD operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Properties CRUD test failed: {str(e)}")
        db.session.rollback()
        return False

def test_users_crud():
    """Test Users CRUD operations with actual database"""
    print("\n👥 Testing Users CRUD operations...")
    
    try:
        app = create_app()
        with app.app_context():
            # Test CREATE - Insert a test user
            import hashlib
            password_hash = hashlib.sha256('testpassword123'.encode()).hexdigest()
            
            test_user_data = {
                'organization_id': 1,
                'email': 'database.test@example.com',
                'password_hash': password_hash,
                'first_name': 'Database',
                'last_name': 'Test',
                'phone': '+1234567890',
                'role': 'tenant',
                'is_active': True,
                'is_verified': True,
                'login_attempts': 0,
                'email_notifications_enabled': True,
                'sms_notifications_enabled': False,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_deleted': False,
                'is_temporary_password': False,
                'password_change_required': False,
                'two_factor_enabled': False,
                'login_notification_enabled': True,
                'suspicious_activity_alerts': True,
                'property_management_access': False,
                'lpr_management_access': False
            }
            
            # Insert user
            result = db.session.execute(db.text("""
                INSERT INTO users (
                    organization_id, email, password_hash, first_name, last_name, 
                    phone, role, is_active, is_verified, login_attempts,
                    email_notifications_enabled, sms_notifications_enabled,
                    created_at, updated_at, is_deleted, is_temporary_password,
                    password_change_required, two_factor_enabled,
                    login_notification_enabled, suspicious_activity_alerts,
                    property_management_access, lpr_management_access
                ) VALUES (
                    :organization_id, :email, :password_hash, :first_name, :last_name,
                    :phone, :role, :is_active, :is_verified, :login_attempts,
                    :email_notifications_enabled, :sms_notifications_enabled,
                    :created_at, :updated_at, :is_deleted, :is_temporary_password,
                    :password_change_required, :two_factor_enabled,
                    :login_notification_enabled, :suspicious_activity_alerts,
                    :property_management_access, :lpr_management_access
                ) RETURNING id
            """), test_user_data)
            
            user_id = result.fetchone()[0]
            db.session.commit()
            print(f"✅ User created with ID: {user_id}")
            
            # Test READ - Fetch the user back
            result = db.session.execute(db.text("""
                SELECT id, email, first_name, last_name, role, is_active
                FROM users 
                WHERE id = :user_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'user_id': user_id}).fetchone()
            
            if result:
                print(f"✅ User retrieved: {result[2]} {result[3]} ({result[1]}, role: {result[4]})")
            else:
                print("❌ Failed to retrieve created user")
                return False
            
            # Test UPDATE - Modify the user
            db.session.execute(db.text("""
                UPDATE users 
                SET first_name = :new_name, updated_at = :updated_at
                WHERE id = :user_id
            """), {
                'user_id': user_id,
                'new_name': 'UpdatedDatabase',
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            print("✅ User updated successfully")
            
            # Verify update
            result = db.session.execute(db.text("""
                SELECT first_name FROM users WHERE id = :user_id
            """), {'user_id': user_id}).fetchone()
            
            if result and result[0] == 'UpdatedDatabase':
                print("✅ User update verified in database")
            else:
                print("❌ User update not reflected in database")
                return False
            
            # Test DELETE - Remove the test user
            db.session.execute(db.text("""
                UPDATE users 
                SET is_deleted = true, updated_at = :updated_at
                WHERE id = :user_id
            """), {
                'user_id': user_id,
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            print("✅ User soft-deleted successfully")
            
            # Verify deletion
            result = db.session.execute(db.text("""
                SELECT id FROM users 
                WHERE id = :user_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'user_id': user_id}).fetchone()
            
            if not result:
                print("✅ User deletion verified - not visible in active queries")
            else:
                print("❌ User still visible after deletion")
                return False
                
            print("✅ Users CRUD operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Users CRUD test failed: {str(e)}")
        db.session.rollback()
        return False

def test_tenants_crud():
    """Test Tenants CRUD operations with actual database"""
    print("\n🏠 Testing Tenants CRUD operations...")
    
    try:
        app = create_app()
        with app.app_context():
            # Test CREATE - Insert a test tenant
            test_tenant_data = {
                'organization_id': 1,
                'first_name': 'Tenant',
                'last_name': 'Database',
                'email': 'tenant.test@example.com',
                'phone': '+1987654321',
                'monthly_income': 5000.00,
                'is_active': True,
                'move_in_date': datetime.now().date(),
                'move_out_date': None,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_deleted': False
            }
            
            # Insert tenant
            result = db.session.execute(db.text("""
                INSERT INTO tenants (
                    organization_id, first_name, last_name, email, phone,
                    monthly_income, is_active, move_in_date, move_out_date,
                    created_at, updated_at, is_deleted
                ) VALUES (
                    :organization_id, :first_name, :last_name, :email, :phone,
                    :monthly_income, :is_active, :move_in_date, :move_out_date,
                    :created_at, :updated_at, :is_deleted
                ) RETURNING id
            """), test_tenant_data)
            
            tenant_id = result.fetchone()[0]
            db.session.commit()
            print(f"✅ Tenant created with ID: {tenant_id}")
            
            # Test READ - Fetch the tenant back
            result = db.session.execute(db.text("""
                SELECT id, first_name, last_name, email, monthly_income, is_active
                FROM tenants 
                WHERE id = :tenant_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'tenant_id': tenant_id}).fetchone()
            
            if result:
                print(f"✅ Tenant retrieved: {result[1]} {result[2]} ({result[3]}, income: ${result[4]})")
            else:
                print("❌ Failed to retrieve created tenant")
                return False
            
            # Test UPDATE - Modify the tenant
            db.session.execute(db.text("""
                UPDATE tenants 
                SET monthly_income = :new_income, updated_at = :updated_at
                WHERE id = :tenant_id
            """), {
                'tenant_id': tenant_id,
                'new_income': 5500.00,
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            print("✅ Tenant updated successfully")
            
            # Verify update
            result = db.session.execute(db.text("""
                SELECT monthly_income FROM tenants WHERE id = :tenant_id
            """), {'tenant_id': tenant_id}).fetchone()
            
            if result and result[0] == 5500.00:
                print("✅ Tenant update verified in database")
            else:
                print("❌ Tenant update not reflected in database")
                return False
            
            # Test DELETE - Remove the test tenant
            db.session.execute(db.text("""
                UPDATE tenants 
                SET is_deleted = true, updated_at = :updated_at
                WHERE id = :tenant_id
            """), {
                'tenant_id': tenant_id,
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            print("✅ Tenant soft-deleted successfully")
            
            # Verify deletion
            result = db.session.execute(db.text("""
                SELECT id FROM tenants 
                WHERE id = :tenant_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {'tenant_id': tenant_id}).fetchone()
            
            if not result:
                print("✅ Tenant deletion verified - not visible in active queries")
            else:
                print("❌ Tenant still visible after deletion")
                return False
                
            print("✅ Tenants CRUD operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Tenants CRUD test failed: {str(e)}")
        db.session.rollback()
        return False

def show_database_statistics():
    """Show current database statistics"""
    print("\n📊 Database Statistics:")
    
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
        print(f"❌ Failed to get database statistics: {str(e)}")

def main():
    """Main test function"""
    print("🚀 EstateCore Render Database Verification Test")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database connection failed. Please check your Render database configuration.")
        return False
    
    # Show current database stats
    show_database_statistics()
    
    # Test CRUD operations
    tests_passed = 0
    total_tests = 3
    
    if test_properties_crud():
        tests_passed += 1
        
    if test_users_crud():
        tests_passed += 1
        
    if test_tenants_crud():
        tests_passed += 1
    
    # Final results
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Your Render database is working perfectly!")
        print("✅ Data persistence verified across all core entities")
        print("✅ CRUD operations working correctly")
        print("✅ Database connectivity confirmed")
        return True
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    main()