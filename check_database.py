#!/usr/bin/env python3
"""
Database inspection script to check current schema
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from estatecore_backend import create_app, db

def check_database():
    """Check database schema"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking database schema...")
            
            # Get database engine
            engine = db.engine
            
            # Check if tables exist
            tables = engine.table_names()
            print(f"📋 Existing tables: {tables}")
            
            # Try to create a simple property to test
            if 'properties' in tables:
                print("🏠 Properties table exists, testing creation...")
                from estatecore_backend.models import Property
                
                # Check Property model
                inspector = db.inspect(engine)
                columns = inspector.get_columns('properties')
                print(f"📋 Properties columns: {[col['name'] for col in columns]}")
                
                # Try to create a test property
                test_property = Property(
                    name='Test Property',
                    address='123 Test St',
                    type='house',
                    rent=1000,
                    owner_id=1
                )
                
                db.session.add(test_property)
                db.session.commit()
                print("✅ Test property created successfully!")
                
                # Clean up test property
                db.session.delete(test_property)
                db.session.commit()
                print("🧹 Test property cleaned up")
                
            else:
                print("❌ Properties table doesn't exist!")
                print("🔧 Run 'python update_database.py' to create tables")
                
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            import traceback
            traceback.print_exc()
            print("\n🔧 Try running 'python update_database.py' to fix database issues")

if __name__ == "__main__":
    check_database()