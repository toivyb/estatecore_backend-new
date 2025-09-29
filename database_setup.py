#!/usr/bin/env python3
"""
Database setup and migration script for EstateCore
Supports SQLite for development and PostgreSQL for production
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
import hashlib
import secrets
import string

DATABASE_PATH = "estatecore.db"

def create_database_schema():
    """Create all database tables with proper relationships"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            subscription_plan TEXT NOT NULL DEFAULT 'basic',
            billing_email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            trial_ends_at TEXT,
            custom_domain TEXT,
            logo_url TEXT,
            phone TEXT,
            address TEXT,
            payment_method TEXT DEFAULT 'card',
            auto_billing BOOLEAN DEFAULT 1,
            mrr_override REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company_id INTEGER,
            role TEXT NOT NULL,
            password_hash TEXT,
            otp TEXT,
            is_first_login BOOLEAN DEFAULT 1,
            last_login TEXT,
            status TEXT DEFAULT 'active',
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
    """)
    
    # User property access table (many-to-many relationship)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_property_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE,
            UNIQUE(user_id, property_id)
        );
    """)
    
    # Properties table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            units INTEGER DEFAULT 1,
            occupied_units INTEGER DEFAULT 0,
            rent_amount REAL,
            company_id INTEGER NOT NULL,
            property_manager_id INTEGER,
            type TEXT DEFAULT 'apartment',
            bedrooms INTEGER,
            bathrooms REAL,
            description TEXT,
            is_available BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            FOREIGN KEY (property_manager_id) REFERENCES users (id)
        );
    """)
    
    # Units table (for multi-unit properties)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            unit_number TEXT NOT NULL,
            bedrooms INTEGER,
            bathrooms REAL,
            rent REAL,
            square_feet INTEGER,
            is_available BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE,
            UNIQUE(property_id, unit_number)
        );
    """)
    
    # Tenants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            property_id INTEGER NOT NULL,
            unit_id INTEGER,
            unit_number TEXT,
            lease_start_date TEXT,
            lease_end_date TEXT,
            rent_amount REAL,
            security_deposit REAL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id),
            FOREIGN KEY (unit_id) REFERENCES units (id)
        );
    """)
    
    # Payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_type TEXT NOT NULL,
            payment_method TEXT DEFAULT 'credit_card',
            status TEXT DEFAULT 'pending',
            payment_date TEXT,
            due_date TEXT,
            description TEXT,
            receipt_number TEXT,
            stripe_payment_id TEXT,
            processing_fee REAL DEFAULT 0,
            net_amount REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id),
            FOREIGN KEY (property_id) REFERENCES properties (id)
        );
    """)
    
    # Maintenance requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            unit_id INTEGER,
            tenant_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            assigned_to INTEGER,
            estimated_cost REAL,
            actual_cost REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY (property_id) REFERENCES properties (id),
            FOREIGN KEY (unit_id) REFERENCES units (id),
            FOREIGN KEY (tenant_id) REFERENCES tenants (id),
            FOREIGN KEY (assigned_to) REFERENCES users (id)
        );
    """)
    
    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            uploaded_by INTEGER,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        );
    """)
    
    # System settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_company ON properties(company_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenants_property ON tenants(property_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_tenant ON payments(tenant_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_property ON payments(property_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_property ON maintenance_requests(property_id);")
    
    conn.commit()
    conn.close()
    
    print("Database schema created successfully!")

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_sample_data():
    """Insert sample data for development and testing"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Insert sample companies
    companies_data = [
        (1, 'Premier Property Management', 'premium', 'billing@premier-pm.com', '2024-01-15', 'active'),
        (2, 'GreenVille Estates', 'premium', 'admin@greenville-estates.com', '2024-03-20', 'active'),
        (3, 'Urban Living Co', 'basic', 'finance@urbanliving.co', '2024-06-10', 'active'),
        (4, 'Sunset Properties LLC', 'basic', 'accounts@sunsetproperties.com', '2024-08-05', 'active')
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO companies (id, name, subscription_plan, billing_email, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, companies_data)
    
    # Insert sample users with hashed passwords
    default_password_hash = hash_password('password123')
    users_data = [
        (0, 'System Admin', 'admin@estatecore.com', None, 'super_admin', default_password_hash, None, 0),
        (1, 'John Smith', 'john@premier-pm.com', 1, 'company_admin', default_password_hash, None, 0),
        (2, 'Sarah Davis', 'sarah@premier-pm.com', 1, 'property_admin', default_password_hash, None, 0),
        (3, 'Mike Johnson', 'mike@premier-pm.com', 1, 'property_manager', default_password_hash, None, 0),
        (4, 'Emily Rodriguez', 'emily@greenville-estates.com', 2, 'company_admin', default_password_hash, None, 0),
        (5, 'David Chen', 'david@greenville-estates.com', 2, 'property_admin', default_password_hash, None, 0),
        (6, 'Lisa Anderson', 'lisa@urbanliving.co', 3, 'company_admin', default_password_hash, None, 0),
        (7, 'James Wilson', 'james@urbanliving.co', 3, 'property_manager', default_password_hash, None, 0),
        (8, 'Maria Garcia', 'maria@sunsetproperties.com', 4, 'company_admin', default_password_hash, None, 0)
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO users (id, name, email, company_id, role, password_hash, otp, is_first_login)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)
    
    # Insert sample properties
    properties_data = [
        (1, 'Sunset Apartments', '123 Sunset Blvd', 24, 22, 2500, 1, 3, 'apartment'),
        (2, 'Downtown Lofts', '456 Main St', 48, 45, 3200, 1, 3, 'apartment'),
        (3, 'Green Valley Homes', '789 Oak Ave', 15, 12, 2800, 2, 5, 'house'),
        (4, 'Riverside Complex', '321 River Rd', 32, 28, 2200, 2, 5, 'apartment'),
        (5, 'City Center Plaza', '654 Urban Way', 60, 55, 2600, 3, 7, 'apartment'),
        (6, 'Hillside Residences', '987 Hill St', 20, 18, 3000, 4, None, 'townhouse'),
        (7, 'Lakefront Condos', '147 Lake Dr', 36, 32, 2900, 4, None, 'condo')
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO properties (id, name, address, units, occupied_units, rent_amount, company_id, property_manager_id, type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, properties_data)
    
    # Insert sample tenants
    today = datetime.now()
    lease_end_dates = [
        (today + timedelta(days=90)).strftime("%Y-%m-%d"),
        (today + timedelta(days=180)).strftime("%Y-%m-%d"),
        (today + timedelta(days=270)).strftime("%Y-%m-%d"),
        (today + timedelta(days=365)).strftime("%Y-%m-%d")
    ]
    
    tenants_data = [
        (1, 'Alice Johnson', 'alice.johnson@email.com', '555-0101', 1, None, '1A', lease_end_dates[0], 1200),
        (2, 'Bob Williams', 'bob.williams@email.com', '555-0102', 1, None, '2B', lease_end_dates[1], 1300),
        (3, 'Carol Brown', 'carol.brown@email.com', '555-0103', 2, None, '3C', lease_end_dates[2], 1500),
        (4, 'David Jones', 'david.jones@email.com', '555-0104', 3, None, '101', lease_end_dates[0], 2200),
        (5, 'Eva Davis', 'eva.davis@email.com', '555-0105', 4, None, '4A', lease_end_dates[3], 1800),
        (6, 'Frank Miller', 'frank.miller@email.com', '555-0106', 5, None, '5B', lease_end_dates[1], 2000),
        (7, 'Grace Wilson', 'grace.wilson@email.com', '555-0107', 6, None, '6C', lease_end_dates[2], 2500),
        (8, 'Henry Taylor', 'henry.taylor@email.com', '555-0108', 7, None, '7A', lease_end_dates[0], 2300),
        (9, 'Ivy Anderson', 'ivy.anderson@email.com', '555-0109', 1, None, '8B', lease_end_dates[3], 1400),
        (10, 'Jack Thomas', 'jack.thomas@email.com', '555-0110', 2, None, '9C', lease_end_dates[1], 1600)
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO tenants (id, name, email, phone, property_id, unit_id, unit_number, lease_end_date, rent_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tenants_data)
    
    # Insert user property access relationships
    property_access_data = [
        (2, 1), (2, 2),  # Sarah has access to properties 1 and 2
        (3, 1),          # Mike has access to property 1
        (5, 3), (5, 4),  # David has access to properties 3 and 4
        (7, 5)           # James has access to property 5
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO user_property_access (user_id, property_id)
        VALUES (?, ?)
    """, property_access_data)
    
    # Insert some sample units for apartment properties
    units_data = [
        (1, '1A', 1, 1.0, 1200, 750),
        (1, '1B', 1, 1.0, 1250, 800),
        (1, '2A', 2, 2.0, 1500, 950),
        (1, '2B', 2, 2.0, 1550, 1000),
        (2, '101', 1, 1.5, 1800, 850),
        (2, '102', 2, 2.0, 2200, 1100),
        (2, '201', 1, 1.5, 1750, 825),
        (4, '1A', 1, 1.0, 1400, 700),
        (4, '2A', 2, 1.5, 1800, 900),
        (5, '301', 1, 1.0, 1600, 600)
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO units (property_id, unit_number, bedrooms, bathrooms, rent, square_feet)
        VALUES (?, ?, ?, ?, ?, ?)
    """, units_data)
    
    # Insert system settings
    settings_data = [
        ('app_name', 'EstateCore', 'Application name'),
        ('app_version', '6.0', 'Application version'),
        ('database_version', '1.0', 'Database schema version'),
        ('default_currency', 'USD', 'Default currency for the system'),
        ('stripe_publishable_key', 'pk_test_...', 'Stripe publishable key'),
        ('email_from_address', 'noreply@estatecore.com', 'Default from email address'),
        ('company_logo_url', '/assets/logo.png', 'Default company logo'),
        ('max_file_upload_size', '10485760', 'Maximum file upload size in bytes (10MB)')
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO system_settings (key, value, description)
        VALUES (?, ?, ?)
    """, settings_data)
    
    conn.commit()
    conn.close()
    
    print("Sample data inserted successfully!")
    print(f"Database location: {os.path.abspath(DATABASE_PATH)}")
    print("Default password for all users: password123")

def reset_database():
    """Drop all tables and recreate the database"""
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print("Existing database deleted")
    
    create_database_schema()
    seed_sample_data()

def backup_database(backup_path=None):
    """Create a backup of the current database"""
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"estatecore_backup_{timestamp}.db"
    
    if os.path.exists(DATABASE_PATH):
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    else:
        print("No database found to backup")
        return None

def get_database_info():
    """Get information about the current database"""
    if not os.path.exists(DATABASE_PATH):
        print("Database does not exist")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    print(f"Database: {os.path.abspath(DATABASE_PATH)}")
    print(f"Size: {os.path.getsize(DATABASE_PATH):,} bytes")
    print(f"Tables: {len(tables)}")
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} records")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            create_database_schema()
        elif command == "seed":
            seed_sample_data()
        elif command == "reset":
            reset_database()
        elif command == "backup":
            backup_path = sys.argv[2] if len(sys.argv) > 2 else None
            backup_database(backup_path)
        elif command == "info":
            get_database_info()
        else:
            print("Usage: python database_setup.py [create|seed|reset|backup|info]")
    else:
        print("Setting up EstateCore database...")
        reset_database()
        get_database_info()