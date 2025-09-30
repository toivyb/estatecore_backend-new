#!/usr/bin/env python3
"""
Test the set-password endpoint
"""
import requests
import json

def test_set_password():
    url = "http://localhost:5001/api/users/9/set-password"
    data = {"password": "newpassword123"}
    
    print("Testing set-password endpoint...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Set password endpoint is working!")
        elif response.status_code == 404:
            print("❌ Endpoint not found - Flask server needs restart")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_set_password()