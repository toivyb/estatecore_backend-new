#!/usr/bin/env python3
"""
Inspect database schema to understand existing structure
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def inspect_database():
    """Inspect the database schema"""
    
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            print("Inspecting database schema...")
            
            # Get database engine and inspector
            engine = db.engine
            inspector = db.inspect(engine)
            
            # Get all table names
            tables = inspector.get_table_names()
            print(f"\nFound {len(tables)} tables:")
            for table in sorted(tables):
                print(f"  - {table}")
            
            # Check specific tables we care about
            important_tables = ['users', 'properties', 'tenants', 'units', 'invites', 'messages']
            
            for table_name in important_tables:
                if table_name in tables:
                    print(f"\n=== {table_name.upper()} TABLE ===")
                    columns = inspector.get_columns(table_name)
                    for col in columns:
                        col_type = str(col['type'])
                        nullable = "NULL" if col['nullable'] else "NOT NULL"
                        default = f" DEFAULT {col['default']}" if col.get('default') else ""
                        print(f"  {col['name']:<25} {col_type:<20} {nullable}{default}")
                else:
                    print(f"\n=== {table_name.upper()} TABLE === NOT FOUND")
            
            return True
                
    except Exception as e:
        print(f"Error inspecting database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    inspect_database()