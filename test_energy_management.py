#!/usr/bin/env python3
"""
Test Smart Energy Management System
"""
import sys
import os
from datetime import datetime

# Import app components
from app import create_app

def test_energy_management_api():
    """Test Energy Management API endpoints"""
    print("Testing Smart Energy Management System")
    print("=" * 40)
    
    try:
        app = create_app()
        with app.test_client() as client:
            property_id = 1
            
            # Test 1: Health Check
            print("1. Testing health check endpoint...")
            response = client.get('/api/energy/health')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   Service Status: {data.get('status')}")
                print(f"   Models Trained: {data.get('models_trained')}")
                print(f"   Data Points: {data.get('data_points')}")
            
            # Test 2: Get Energy Types
            print("\n2. Testing energy types endpoint...")
            response = client.get('/api/energy/types')
            if response.status_code == 200:
                data = response.get_json()
                types = data.get('energy_types', [])
                print(f"   Available energy types: {len(types)}")
                for energy_type in types[:3]:
                    print(f"   - {energy_type['label']}: {energy_type['unit']}")
            
            # Test 3: Simulate Energy Data
            print("\n3. Simulating energy data...")
            response = client.post(f'/api/energy/simulate/{property_id}', json={'days': 10})
            if response.status_code == 200:
                data = response.get_json()
                print(f"   Success: {data.get('success')}")
                print(f"   Readings added: {data.get('readings_added')}")
                print(f"   Alerts generated: {data.get('total_alerts_generated')}")
            else:
                print(f"   Failed: {response.status_code}")
                print(f"   Error: {response.get_json()}")
            
            # Test 4: Get Dashboard Data
            print("\n4. Testing dashboard endpoint...")
            response = client.get(f'/api/energy/dashboard/{property_id}')
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    dashboard = data.get('dashboard', {})
                    analytics = dashboard.get('analytics', {})
                    print(f"   Total consumption: {analytics.get('total_consumption', 'N/A')}")
                    print(f"   Total cost: ${analytics.get('total_cost', 'N/A')}")
                    print(f"   Efficiency score: {analytics.get('efficiency_score', 'N/A')}%")
                else:
                    print(f"   Error: {data.get('error')}")
            
            # Test 5: Get Forecast
            print("\n5. Testing forecast endpoint...")
            response = client.get(f'/api/energy/forecast/{property_id}/electricity?days=7')
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    forecast = data.get('forecast', {})
                    summary = data.get('summary', {})
                    print(f"   7-day forecast generated")
                    print(f"   Total predicted consumption: {summary.get('total_predicted_consumption', 'N/A')} kWh")
                    print(f"   Total predicted cost: ${summary.get('total_predicted_cost', 'N/A')}")
                else:
                    print(f"   Error: {data.get('error')}")
            
            # Test 6: Get Recommendations
            print("\n6. Testing recommendations endpoint...")
            response = client.get(f'/api/energy/recommendations/{property_id}')
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    recommendations = data.get('recommendations', [])
                    summary = data.get('summary', {})
                    print(f"   Recommendations generated: {len(recommendations)}")
                    print(f"   Total potential monthly savings: ${summary.get('total_potential_monthly_savings', 'N/A')}")
                    if recommendations:
                        top_rec = recommendations[0]
                        print(f"   Top recommendation: {top_rec.get('title')}")
                        print(f"   Potential savings: ${top_rec.get('potential_savings')}/month")
                else:
                    print(f"   Error: {data.get('error')}")
            
            # Test 7: Get Alerts
            print("\n7. Testing alerts endpoint...")
            response = client.get(f'/api/energy/alerts?property_id={property_id}')
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    alerts = data.get('alerts', [])
                    summary = data.get('summary', {})
                    print(f"   Active alerts: {len(alerts)}")
                    print(f"   Critical alerts: {summary.get('critical_count', 0)}")
                    print(f"   High priority alerts: {summary.get('high_count', 0)}")
                    if alerts:
                        alert = alerts[0]
                        print(f"   Latest alert: {alert.get('title')} ({alert.get('severity')})")
                else:
                    print(f"   Error: {data.get('error')}")
            
            # Test 8: Add Energy Reading
            print("\n8. Testing add energy reading endpoint...")
            reading_data = {
                'property_id': property_id,
                'energy_type': 'electricity',
                'consumption': 450.5,
                'cost': 54.06,
                'temperature': 72.5,
                'occupancy': True
            }
            response = client.post('/api/energy/readings', json=reading_data)
            if response.status_code == 201:
                data = response.get_json()
                print(f"   Success: {data.get('success')}")
                print(f"   Alerts triggered: {data.get('alerts_triggered')}")
            else:
                print(f"   Failed: {response.status_code}")
            
            print("\n" + "=" * 40)
            print("[SUCCESS] Energy Management System Test Complete!")
            return True
            
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_energy_management_api()