#!/usr/bin/env python3
"""
Test the complete property creation flow
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_property_creation():
    print("Testing property creation flow...")
    
    # 1. Get current properties count
    response = requests.get(f"{BASE_URL}/api/properties")
    if response.status_code == 200:
        properties_before = response.json()
        print(f"Properties before creation: {len(properties_before)}")
    else:
        print(f"Failed to get properties: {response.status_code}")
        return
    
    # 2. Create a new property
    property_data = {
        "name": "Flow Test Property",
        "address": "456 Flow Test St",
        "company_id": 1,
        "units": 2,
        "type": "condo"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/properties",
        headers={"Content-Type": "application/json"},
        json=property_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Property creation result: {result}")
        property_id = result.get('property_id')
        
        # 3. Get properties again to verify
        response = requests.get(f"{BASE_URL}/api/properties")
        if response.status_code == 200:
            properties_after = response.json()
            print(f"Properties after creation: {len(properties_after)}")
            
            # Check if new property exists
            new_property = None
            for prop in properties_after:
                if prop['id'] == property_id:
                    new_property = prop
                    break
            
            if new_property:
                print(f"SUCCESS: Property found: {new_property['name']} (ID: {new_property['id']})")
            else:
                print(f"ERROR: Property with ID {property_id} not found in list")
                print(f"Available IDs: {[p['id'] for p in properties_after]}")
        else:
            print(f"Failed to get properties after creation: {response.status_code}")
    else:
        print(f"Failed to create property: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_property_creation()