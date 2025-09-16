#!/usr/bin/env python3
"""
Database update script to ensure all tables and columns exist
Run this to fix database schema issues
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from estatecore_backend import create_app, db

def update_database():
    """Update database schema"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Updating database schema...")
            
            # Drop and recreate all tables to ensure clean schema
            print("📋 Recreating database tables...")
            db.drop_all()
            db.create_all()
            
            print("✅ Database schema updated successfully!")
            
            # Create a default admin user if none exists
            from estatecore_backend.models import User
            admin = User.query.filter_by(email='admin@estatecore.com').first()
            
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
                
            print("\n🎉 Database is ready to use!")
            
        except Exception as e:
            print(f"❌ Error updating database: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    update_database()