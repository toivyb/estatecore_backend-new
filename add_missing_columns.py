#!/usr/bin/env python3
"""
Add missing columns to existing tables
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_missing_columns():
    """Add missing columns to existing tables"""
    
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            print("Adding missing columns to database...")
            
            # Get database engine and inspector
            engine = db.engine
            inspector = db.inspect(engine)
            
            # Check properties table columns
            if 'properties' in inspector.get_table_names():
                columns = inspector.get_columns('properties')
                column_names = [col['name'] for col in columns]
                print(f"Properties table columns: {column_names}")
                
                # Add missing columns using raw SQL
                missing_columns = []
                
                if 'address' not in column_names:
                    missing_columns.append('address')
                    try:
                        db.engine.execute('ALTER TABLE properties ADD COLUMN address VARCHAR(200)')
                        print("Added 'address' column to properties table")
                    except Exception as e:
                        print(f"Error adding address column: {e}")
                        
                if 'name' not in column_names:
                    missing_columns.append('name')
                    try:
                        db.engine.execute('ALTER TABLE properties ADD COLUMN name VARCHAR(100)')
                        print("Added 'name' column to properties table")
                    except Exception as e:
                        print(f"Error adding name column: {e}")
                        
                if 'units' not in column_names:
                    missing_columns.append('units')
                    try:
                        db.engine.execute('ALTER TABLE properties ADD COLUMN units INTEGER DEFAULT 1')
                        print("Added 'units' column to properties table")
                    except Exception as e:
                        print(f"Error adding units column: {e}")
                        
                if 'description' not in column_names:
                    missing_columns.append('description')
                    try:
                        db.engine.execute('ALTER TABLE properties ADD COLUMN description TEXT')
                        print("Added 'description' column to properties table")
                    except Exception as e:
                        print(f"Error adding description column: {e}")
                        
                if 'is_available' not in column_names:
                    missing_columns.append('is_available')
                    try:
                        db.engine.execute('ALTER TABLE properties ADD COLUMN is_available BOOLEAN DEFAULT TRUE')
                        print("Added 'is_available' column to properties table")
                    except Exception as e:
                        print(f"Error adding is_available column: {e}")
                        
                if 'created_at' not in column_names:
                    missing_columns.append('created_at')
                    try:
                        db.engine.execute('ALTER TABLE properties ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                        print("Added 'created_at' column to properties table")
                    except Exception as e:
                        print(f"Error adding created_at column: {e}")
                        
                if 'owner_id' not in column_names:
                    missing_columns.append('owner_id')
                    try:
                        db.engine.execute('ALTER TABLE properties ADD COLUMN owner_id INTEGER')
                        print("Added 'owner_id' column to properties table")
                    except Exception as e:
                        print(f"Error adding owner_id column: {e}")
                
                if missing_columns:
                    print(f"Added missing columns to properties: {missing_columns}")
                else:
                    print("All required columns already exist in properties table")
                
                # Try to test the query now
                try:
                    from app import Property
                    properties = Property.query.all()
                    print(f"Database test successful - found {len(properties)} properties")
                    print("Migration completed successfully!")
                    return True
                except Exception as e:
                    print(f"Still having issues querying properties: {e}")
                    return False
            else:
                print("Properties table not found - need to create it")
                try:
                    db.create_all()
                    print("Created all missing tables")
                    return True
                except Exception as e:
                    print(f"Error creating tables: {e}")
                    return False
                
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_missing_columns()
    if success:
        print("Ready to test!")
        exit(0)
    else:
        print("Migration failed!")
        exit(1)