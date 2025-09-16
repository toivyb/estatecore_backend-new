#!/usr/bin/env python3
"""Simple API test script"""
import requests
import json

def test_simple():
    """Test the EstateCore API endpoints"""
    base_url = "http://localhost:5000"
    
    print("Testing EstateCore API...")
    
    # Test 1: Health check
    try:
        print("\nTesting health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health Response: {response.status_code}")
        if response.status_code == 200:
            print(f"Health Data: {response.json()}")
        else:
            print(f"Health Error: {response.text}")
    except Exception as e:
        print(f"Health test failed: {str(e)}")
    
    # Test 2: Properties endpoint
    try:
        print("\nTesting properties endpoint...")
        response = requests.get(f"{base_url}/api/properties", timeout=5)
        print(f"Properties Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} properties")
        else:
            print(f"Properties Error: {response.text[:500]}")
    except Exception as e:
        print(f"Properties test failed: {str(e)}")

if __name__ == "__main__":
    test_simple()