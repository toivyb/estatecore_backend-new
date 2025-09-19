#!/usr/bin/env python3
"""
Enhanced User Management Database Setup
Creates tables and updates schema for property/LPR management system
"""

import os
import sys
from datetime import datetime

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///estatecore.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def create_enhanced_tables():
    """Create enhanced user management tables"""
    
    with app.app_context():
        try:
            print("Creating Enhanced User Management Tables...")
            
            # 1. Create LPR Companies table
            print("Creating LPR Companies table...")
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS lpr_companies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    description TEXT,
                    contact_email VARCHAR(120),
                    contact_phone VARCHAR(20),
                    address VARCHAR(300),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    max_alerts_per_day INTEGER DEFAULT 100,
                    max_cameras INTEGER DEFAULT 10,
                    subscription_type VARCHAR(20) DEFAULT 'basic'
                )
            """))
            
            # 2. Add new columns to users table (check if they exist first)
            print("Enhancing Users table...")
            
            # Check existing columns
            existing_columns = db.session.execute(db.text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND table_schema = CURRENT_SCHEMA()
            """)).fetchall()
            
            existing_column_names = [row[0] for row in existing_columns]
            
            # Add LPR company reference
            if 'lpr_company_id' not in existing_column_names:
                print("  Adding lpr_company_id column...")
                db.session.execute(db.text("""
                    ALTER TABLE users ADD COLUMN lpr_company_id INTEGER REFERENCES lpr_companies(id)
                """))
            
            # Add LPR permissions
            if 'lpr_permissions' not in existing_column_names:
                print("  Adding lpr_permissions column...")
                db.session.execute(db.text("""
                    ALTER TABLE users ADD COLUMN lpr_permissions VARCHAR(20)
                """))
            
            # Add access control flags
            if 'property_management_access' not in existing_column_names:
                print("  Adding property_management_access column...")
                db.session.execute(db.text("""
                    ALTER TABLE users ADD COLUMN property_management_access BOOLEAN DEFAULT false
                """))
            
            if 'lpr_management_access' not in existing_column_names:
                print("  Adding lpr_management_access column...")
                db.session.execute(db.text("""
                    ALTER TABLE users ADD COLUMN lpr_management_access BOOLEAN DEFAULT false
                """))
            
            # Expand role column if needed
            print("  Expanding role column length...")
            db.session.execute(db.text("""
                ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(30)
            """))
            
            # 3. Add company_id to LPR events table
            print("Enhancing LPR Events table...")
            lpr_events_columns = db.session.execute(db.text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'lpr_events' AND table_schema = CURRENT_SCHEMA()
            """)).fetchall()
            
            lpr_events_column_names = [row[0] for row in lpr_events_columns]
            
            if 'company_id' not in lpr_events_column_names:
                print("  Adding company_id to lpr_events...")
                db.session.execute(db.text("""
                    ALTER TABLE lpr_events ADD COLUMN company_id INTEGER REFERENCES lpr_companies(id)
                """))
            
            # 4. Add notes field to invites table for extended data
            print("Enhancing Invites table...")
            invites_columns = db.session.execute(db.text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'invites' AND table_schema = CURRENT_SCHEMA()
            """)).fetchall()
            
            invites_column_names = [row[0] for row in invites_columns]
            
            if 'notes' not in invites_column_names:
                print("  Adding notes field to invites...")
                db.session.execute(db.text("""
                    ALTER TABLE invites ADD COLUMN notes TEXT
                """))
            
            # 5. Insert sample LPR companies
            print("Creating sample LPR companies...")
            
            # Check if companies already exist
            existing_companies = db.session.execute(db.text("""
                SELECT COUNT(*) FROM lpr_companies
            """)).scalar()
            
            if existing_companies == 0:
                sample_companies = [
                    {
                        'name': 'SecureView Security',
                        'description': 'Professional security services with LPR monitoring',
                        'contact_email': 'admin@secureview.com',
                        'contact_phone': '555-0101',
                        'subscription_type': 'premium'
                    },
                    {
                        'name': 'ParkSafe Solutions',
                        'description': 'Parking management and access control systems',
                        'contact_email': 'support@parksafe.com',
                        'contact_phone': '555-0102',
                        'subscription_type': 'enterprise'
                    },
                    {
                        'name': 'Metro Property Management',
                        'description': 'Comprehensive property management with security integration',
                        'contact_email': 'tech@metroprop.com',
                        'contact_phone': '555-0103',
                        'subscription_type': 'basic'
                    },
                    {
                        'name': 'Guardian Fleet Services',
                        'description': 'Fleet tracking and vehicle monitoring solutions',
                        'contact_email': 'ops@guardianfleet.com',
                        'contact_phone': '555-0104',
                        'subscription_type': 'premium'
                    }
                ]
                
                for company in sample_companies:
                    db.session.execute(db.text("""
                        INSERT INTO lpr_companies (name, description, contact_email, contact_phone, subscription_type, created_at)
                        VALUES (:name, :description, :contact_email, :contact_phone, :subscription_type, :created_at)
                    """), {
                        **company,
                        'created_at': datetime.utcnow()
                    })
                
                print(f"  Created {len(sample_companies)} sample companies")
            else:
                print(f"  Found {existing_companies} existing companies")
            
            # 6. Create indexes for performance
            print("Creating performance indexes...")
            
            try:
                db.session.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_users_lpr_company ON users(lpr_company_id)
                """))
                
                db.session.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_users_lpr_access ON users(lpr_management_access)
                """))
                
                db.session.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_users_property_access ON users(property_management_access)
                """))
                
                db.session.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_lpr_events_company ON lpr_events(company_id)
                """))
                
                print("  Created performance indexes")
                
            except Exception as e:
                print(f"  Index creation warning: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            
            print("Enhanced User Management setup completed successfully!")
            
            # 7. Display summary
            print("\nSummary:")
            companies_count = db.session.execute(db.text("SELECT COUNT(*) FROM lpr_companies")).scalar()
            users_count = db.session.execute(db.text("SELECT COUNT(*) FROM users")).scalar()
            
            print(f"  - LPR Companies: {companies_count}")
            print(f"  - Total Users: {users_count}")
            
            # Show role distribution
            role_stats = db.session.execute(db.text("""
                SELECT role, COUNT(*) as count
                FROM users
                GROUP BY role
                ORDER BY count DESC
            """)).fetchall()
            
            print("  - User Roles:")
            for role, count in role_stats:
                print(f"    {role}: {count}")
            
            print("\nNext Steps:")
            print("  1. Test the enhanced invitation system")
            print("  2. Create users with LPR management access")
            print("  3. Configure company-specific LPR data")
            print("  4. Set up role-based access control in frontend")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating enhanced tables: {str(e)}")
            return False

if __name__ == "__main__":
    print("Enhanced User Management Database Setup")
    print("=" * 50)
    
    success = create_enhanced_tables()
    
    if success:
        print("\nSetup completed successfully!")
        print("You can now use the enhanced user management features.")
    else:
        print("\nSetup failed. Check the error messages above.")
        sys.exit(1)