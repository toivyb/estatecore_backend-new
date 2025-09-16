#!/usr/bin/env python3
"""
Verify that all endpoints work correctly before deployment
"""
from app import create_app, db

def verify_all_endpoints():
    """Test all major endpoints"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=== DEPLOYMENT VERIFICATION ===")
            
            # Test database connection
            properties = db.session.execute(db.text("SELECT COUNT(*) FROM properties")).scalar()
            tenants = db.session.execute(db.text("SELECT COUNT(*) FROM tenants")).scalar()
            users = db.session.execute(db.text("SELECT COUNT(*) FROM users")).scalar()
            
            print(f"Database connection: OK")
            print(f"Properties count: {properties}")
            print(f"Tenants count: {tenants}")
            print(f"Users count: {users}")
            
            # Test all API endpoints
            with app.test_client() as client:
                endpoints_to_test = [
                    '/health',
                    '/api/properties',
                    '/api/tenants',
                    '/api/users',
                    '/api/units',
                    '/api/payments',
                    '/api/maintenance',
                    '/api/invites',
                    '/api/messages?user_id=1',
                    '/api/analytics/overview',
                    '/api/ai/lease-expiration-check'
                ]
                
                results = {}
                for endpoint in endpoints_to_test:
                    try:
                        response = client.get(endpoint)
                        results[endpoint] = {
                            'status': response.status_code,
                            'success': response.status_code < 400
                        }
                        status_emoji = "✅" if response.status_code < 400 else "❌"
                        print(f"{status_emoji} {endpoint}: {response.status_code}")
                    except Exception as e:
                        results[endpoint] = {
                            'status': 'ERROR',
                            'success': False,
                            'error': str(e)
                        }
                        print(f"❌ {endpoint}: ERROR - {str(e)}")
                
                # Summary
                successful = sum(1 for r in results.values() if r['success'])
                total = len(results)
                
                print(f"\n=== SUMMARY ===")
                print(f"Successful endpoints: {successful}/{total}")
                print(f"Success rate: {successful/total*100:.1f}%")
                
                if successful == total:
                    print("🎉 ALL ENDPOINTS WORKING - READY FOR DEPLOYMENT!")
                    return True
                else:
                    print("⚠️  Some endpoints have issues - review before deployment")
                    return False
            
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = verify_all_endpoints()
    exit(0 if success else 1)