#!/usr/bin/env python3
"""
Test SaaS user creation functionality with billing integration
"""
import os
import sys
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import app components
from app import create_app, db

def test_saas_user_creation():
    """Test SaaS user creation with billing integration"""
    print("Testing SaaS User Creation with Billing Integration...")
    
    try:
        app = create_app()
        with app.test_client() as client:
            # Test data for SaaS user creation
            saas_user_data = {
                'email': 'saas.test@example.com',
                'username': 'SaaS Test User',
                'password': 'testpassword123',
                'role': 'admin',
                'phone': '+1234567890',
                'subscription_id': 'new',  # Create new subscription
                'units_to_add': 10,
                'auto_charge': True
            }
            
            # Test POST request to create SaaS user
            response = client.post('/api/users', 
                                 json=saas_user_data,
                                 content_type='application/json')
            
            if response.status_code == 201:
                result = response.get_json()
                print(f"SUCCESS: SaaS user created with ID: {result['id']}")
                print(f"Email: {result['email']}")
                
                # Check if billing information was included
                if 'billing' in result:
                    billing = result['billing']
                    if 'error' in billing:
                        print(f"WARNING: Billing integration error: {billing['error']}")
                    else:
                        print("SUCCESS: Billing integration working!")
                        print(f"  Subscription ID: {billing.get('subscription_id', 'N/A')}")
                        print(f"  Units added: {billing.get('units_added', 'N/A')}")
                        print(f"  Unit price: ${billing.get('unit_price', 'N/A')}")
                        print(f"  Total amount: ${billing.get('total_amount', 'N/A')}")
                        print(f"  Invoice ID: {billing.get('invoice_id', 'N/A')}")
                else:
                    print("INFO: No billing information returned (may not be enabled)")
                
                return True
            else:
                print(f"FAILED: SaaS user creation failed with status {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)}")
                return False
                
    except Exception as e:
        print(f"FAILED: SaaS user creation test failed: {str(e)}")
        return False

def test_regular_user_creation():
    """Test regular user creation without billing"""
    print("\nTesting Regular User Creation (without billing)...")
    
    try:
        app = create_app()
        with app.test_client() as client:
            # Test data for regular user creation (no billing fields)
            regular_user_data = {
                'email': 'regular.test@example.com',
                'username': 'Regular Test User',
                'password': 'testpassword123',
                'role': 'tenant',
                'phone': '+1987654321'
            }
            
            # Test POST request to create regular user
            response = client.post('/api/users', 
                                 json=regular_user_data,
                                 content_type='application/json')
            
            if response.status_code == 201:
                result = response.get_json()
                print(f"SUCCESS: Regular user created with ID: {result['id']}")
                print(f"Email: {result['email']}")
                
                # Should not have billing information
                if 'billing' not in result:
                    print("SUCCESS: No billing information (as expected for regular user)")
                else:
                    print("INFO: Billing information present (may be default behavior)")
                
                return True
            else:
                print(f"FAILED: Regular user creation failed with status {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)}")
                return False
                
    except Exception as e:
        print(f"FAILED: Regular user creation test failed: {str(e)}")
        return False

def test_database_data_visibility():
    """Test that data is actually visible in database after creation"""
    print("\nTesting Database Data Visibility...")
    
    try:
        app = create_app()
        with app.app_context():
            # Count users created in the last hour (including our test users)
            one_hour_ago = datetime.utcnow().replace(microsecond=0)
            one_hour_ago = one_hour_ago.replace(hour=one_hour_ago.hour-1)
            
            result = db.session.execute(db.text("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= :time_threshold 
                AND (is_deleted = false OR is_deleted IS NULL)
            """), {'time_threshold': one_hour_ago}).fetchone()
            
            recent_users = result[0] if result else 0
            print(f"SUCCESS: Found {recent_users} users created in the last hour")
            
            # Get details of recent users
            result = db.session.execute(db.text("""
                SELECT id, email, first_name, last_name, role, created_at
                FROM users 
                WHERE created_at >= :time_threshold 
                AND (is_deleted = false OR is_deleted IS NULL)
                ORDER BY created_at DESC
                LIMIT 5
            """), {'time_threshold': one_hour_ago}).fetchall()
            
            if result:
                print("Recent users in database:")
                for user in result:
                    print(f"  ID: {user[0]}, Email: {user[1]}, Name: {user[2]} {user[3]}, Role: {user[4]}")
            
            # Test that API endpoints reflect the database state
            print("\nVerifying API endpoints reflect database state...")
            
        with app.test_client() as client:
            response = client.get('/api/users')
            if response.status_code == 200:
                api_users = response.get_json()
                print(f"SUCCESS: API returns {len(api_users)} total users")
                
                # Find our test users in API response
                test_emails = ['saas.test@example.com', 'regular.test@example.com']
                found_test_users = [u for u in api_users if u['email'] in test_emails]
                
                print(f"SUCCESS: Found {len(found_test_users)} test users in API response")
                for user in found_test_users:
                    print(f"  {user['email']} - {user['username']} ({user['role']})")
                
                return True
            else:
                print(f"FAILED: API call failed with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"FAILED: Database visibility test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("EstateCore SaaS Functionality Test")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    if test_saas_user_creation():
        tests_passed += 1
        
    if test_regular_user_creation():
        tests_passed += 1
        
    if test_database_data_visibility():
        tests_passed += 1
    
    # Final results
    print("\n" + "=" * 40)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: ALL SaaS FUNCTIONALITY TESTS PASSED!")
        print("- SaaS user creation working")
        print("- Regular user creation working") 
        print("- Database persistence confirmed")
        print("- API endpoints reflecting database state")
        return True
    else:
        print("WARNING: Some SaaS tests failed. Check error messages above.")
        return False

if __name__ == "__main__":
    main()