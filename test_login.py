#!/usr/bin/env python3
"""
Simple test script to verify login functionality
"""
import os
import requests

# Set up environment
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'dev-secret-key-for-testing-only'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'

def test_login():
    # Test the login endpoint
    login_data = {
        "email": "admin@example.com", 
        "password": "SecureAdmin123!"
    }
    
    try:
        # Test login
        response = requests.post(
            "http://localhost:5000/api/login", 
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login Response Status: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Login successful! Token received: {token[:20]}...")
            
            # Test authenticated endpoint
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get("http://localhost:5000/api/me", headers=headers)
            print(f"Me Response Status: {me_response.status_code}")
            print(f"Me Response: {me_response.text}")
            
            if me_response.status_code == 200:
                print("✅ Authentication working correctly!")
            else:
                print("❌ Authentication failed")
        else:
            print("❌ Login failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not running on localhost:5000")
        print("Please start the backend server first")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_dev_endpoints():
    """Test development endpoints"""
    try:
        # Test dev credentials endpoint
        response = requests.get("http://localhost:5000/api/dev/credentials")
        print(f"\nDev Credentials Response: {response.status_code}")
        if response.status_code == 200:
            print(f"Credentials: {response.json()}")
        
        # Test health endpoint
        response = requests.get("http://localhost:5000/api/health")
        print(f"Health Response: {response.status_code}")
        if response.status_code == 200:
            print(f"Health: {response.json()}")
            
    except Exception as e:
        print(f"Dev endpoints error: {e}")

if __name__ == "__main__":
    print("🔧 Testing EstateCore Login...")
    print("=" * 50)
    test_dev_endpoints()
    print("\n" + "=" * 50)
    test_login()