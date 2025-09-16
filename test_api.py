#!/usr/bin/env python3
"""
API test script to verify backend functionality
"""
import requests
import json

def test_api():
    """Test the EstateCore API endpoints"""
    base_url = "https://estatecore-backend-sujs.onrender.com/api"
    
    print("🔗 Testing EstateCore API...")
    
    # Test 1: Check if API is responding
    try:
        print("\n📍 Testing API connectivity...")
        response = requests.get(f"{base_url}/properties", timeout=10)
        print(f"✅ API Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Found {len(data)} properties")
        elif response.status_code == 500:
            print("❌ 500 Internal Server Error - Database/Schema issue")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print("No error details available")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ API request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - is the server running?")
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
    
    # Test 2: Try to create a simple property
    print("\n🏠 Testing property creation...")
    test_property = {
        "name": "Test Property",
        "address": "123 Test Street",
        "type": "house",
        "rent": 1200,
        "bedrooms": 3,
        "bathrooms": 2,
        "units": 1,
        "description": "Test property created by API test"
    }
    
    try:
        response = requests.post(
            f"{base_url}/properties",
            json=test_property,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📤 Create Response: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Property created with ID: {data.get('id')}")
        else:
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data}")
            except:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"❌ Create test failed: {str(e)}")
    
    print("\n🔧 If you see errors, try:")
    print("1. Check if the backend server is running")
    print("2. Run 'python update_database.py' to fix database schema")
    print("3. Check the server logs for detailed error messages")

if __name__ == "__main__":
    test_api()