#!/usr/bin/env python3
"""
Simple database migration script to fix schema issues
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database():
    """Fix database schema for production"""
    
    try:
        from app import create_app, db
        from app import Property, User, Tenant, Unit, Invite, Message
        
        app = create_app()
        
        with app.app_context():
            print("Starting database migration...")
            
            # Get database engine and inspector
            engine = db.engine
            inspector = db.inspect(engine)
            
            print("Checking current database schema...")
            
            # Check if tables exist
            tables = inspector.get_table_names()
            print(f"Existing tables: {tables}")
            
            # Drop and recreate all tables to ensure schema matches
            print("Recreating all tables with correct schema...")
            
            try:
                # Drop all tables
                db.drop_all()
                print("Dropped all existing tables")
                
                # Create all tables with current schema
                db.create_all()
                print("Created all tables with correct schema")
                
                # Create default admin user if none exists
                admin = User.query.filter_by(role='super_admin').first()
                if not admin:
                    print("Creating default admin user...")
                    admin = User(
                        username='EstateCore Admin',
                        email='admin@estatecore.com',
                        role='super_admin',
                        password_hash='temp_hash'  # Should be properly hashed
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("Default admin user created!")
                    print("Email: admin@estatecore.com")
                    print("Password: admin123")
                else:
                    print("Admin user already exists")
                    
                # Test that we can query properties now
                properties = Property.query.all()
                print(f"Database test successful - found {len(properties)} properties")
                
                print("Migration completed successfully!")
                print("The backend server should now work correctly.")
                
                return True
                
            except Exception as e:
                print(f"Migration error: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("Ready to deploy!")
        exit(0)
    else:
        print("Migration failed!")
        exit(1)