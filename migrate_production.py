#!/usr/bin/env python3
"""
Production database migration script for Render deployment
This script handles the database schema updates needed for the new features
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def migrate_database():
    """Run database migrations for production"""
    
    try:
        from estatecore_backend import create_app, db
        from estatecore_backend.models import User, Property, Tenant, Unit, Invite, Message
        
        app = create_app()
        
        with app.app_context():
            print("🚀 Starting production database migration...")
            
            # Get database engine
            engine = db.engine
            inspector = db.inspect(engine)
            
            print("📋 Checking current database schema...")
            
            # Check if tables exist
            tables = inspector.get_tables()
            table_names = [t['name'] for t in tables]
            print(f"Existing tables: {table_names}")
            
            # Create missing tables
            print("🔧 Creating/updating database tables...")
            
            try:
                # This will create missing tables and columns
                db.create_all()
                print("✅ Database tables created/updated")
                
                # Check if we need to add missing columns to existing tables
                if 'properties' in table_names:
                    columns = inspector.get_columns('properties')
                    column_names = [col['name'] for col in columns]
                    
                    # Add missing columns using raw SQL if needed
                    missing_columns = []
                    
                    if 'name' not in column_names:
                        missing_columns.append('name')
                        db.engine.execute('ALTER TABLE properties ADD COLUMN name VARCHAR(200)')
                        
                    if 'units' not in column_names:
                        missing_columns.append('units')
                        db.engine.execute('ALTER TABLE properties ADD COLUMN units INTEGER DEFAULT 1')
                        
                    if missing_columns:
                        print(f"✅ Added missing columns to properties: {missing_columns}")
                
                print("✅ Database migration completed successfully!")
                
                # Create default admin user if none exists
                admin = User.query.filter_by(role='super_admin').first()
                if not admin:
                    print("👤 Creating default admin user...")
                    admin = User(
                        username='EstateCore Admin',
                        email='admin@estatecore.com',
                        role='super_admin'
                    )
                    admin.set_password('admin123')
                    db.session.add(admin)
                    db.session.commit()
                    print("✅ Default admin user created!")
                    print("📧 Email: admin@estatecore.com")
                    print("🔑 Password: admin123")
                else:
                    print("👤 Admin user already exists")
                    
                print("\n🎉 Migration completed successfully!")
                print("The backend server should now work correctly.")
                
                return True
                
            except Exception as e:
                print(f"❌ Migration error: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🚀 Ready to deploy!")
        exit(0)
    else:
        print("\n❌ Migration failed!")
        exit(1)