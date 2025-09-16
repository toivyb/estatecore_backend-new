#!/usr/bin/env python3
"""Test database connectivity with app.py"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    print("Testing app.py imports...")
    from app import create_app, db, Property
    print("Successfully imported from app.py")
    
    print("Creating app...")
    app = create_app()
    print("App created successfully")
    
    with app.app_context():
        print("Testing database connection...")
        try:
            # Test database connection
            db.create_all()
            print("Database tables created/verified")
            
            # Test query
            properties = Property.query.all()
            print(f"Found {len(properties)} properties in database")
            
            print("All tests passed! App.py is working correctly.")
            
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            import traceback
            traceback.print_exc()
            
except ImportError as import_error:
    print(f"Import error: {str(import_error)}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"App creation error: {str(e)}")
    import traceback
    traceback.print_exc()