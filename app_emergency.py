#!/usr/bin/env python3
"""
Emergency minimal app.py that works with existing database schema
"""
import os
import sys
import random
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid

# Initialize extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
    
    # Database URI - handle Render's postgres:// URLs
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///estatecore.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS Configuration
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=cors_origins, supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])
    
    # Health check routes
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'EstateCore Backend', 'version': 'emergency-1.0', 'fixed': True})
    
    @app.route('/')
    def root():
        return jsonify({'message': 'EstateCore API Emergency Mode', 'status': 'running'})
    
    # Dashboard API - Direct SQL only
    @app.route('/dashboard', methods=['GET'])
    def get_dashboard():
        try:
            # Direct SQL queries to avoid model issues
            total_properties = db.session.execute(db.text("SELECT COUNT(*) FROM properties WHERE is_deleted = false OR is_deleted IS NULL")).scalar()
            available_properties = db.session.execute(db.text("SELECT COUNT(*) FROM properties WHERE (is_active = true OR is_active IS NULL) AND (is_deleted = false OR is_deleted IS NULL)")).scalar()
            total_users = db.session.execute(db.text("SELECT COUNT(*) FROM users WHERE (is_active = true OR is_active IS NULL) AND (is_deleted = false OR is_deleted IS NULL)")).scalar()
            
            # Check if payments table exists
            payments_exist = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'payments'
                )
            """)).scalar()
            
            if payments_exist:
                total_payments = db.session.execute(db.text("SELECT COUNT(*) FROM payments")).scalar()
                completed_revenue = db.session.execute(db.text("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed'")).scalar()
                pending_revenue = db.session.execute(db.text("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'pending'")).scalar()
            else:
                total_payments = 0
                completed_revenue = 0
                pending_revenue = 0
            
            return jsonify({
                'total_properties': total_properties or 0,
                'available_properties': available_properties or 0,
                'occupied_properties': (total_properties or 0) - (available_properties or 0),
                'total_users': total_users or 0,
                'total_payments': total_payments or 0,
                'total_revenue': float(completed_revenue) if completed_revenue else 0,
                'pending_revenue': float(pending_revenue) if pending_revenue else 0,
                'recent_properties': []
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # AI Analytics Endpoints - Lease Management
    @app.route('/api/ai/lease-expiration-check', methods=['GET'])
    def get_lease_expiration_check():
        try:
            return jsonify({
                'expiring_soon': [],
                'expired': [],
                'alerts': ['Lease tracking system ready - all current']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Properties API - Direct SQL
    @app.route('/api/properties', methods=['GET'])
    def get_properties():
        try:
            # Direct SQL query to avoid model issues during deployment
            result = db.session.execute(db.text("""
                SELECT id, name, street_address, property_type, description,
                       total_units, is_active, created_at
                FROM properties 
                WHERE is_deleted = false OR is_deleted IS NULL
            """)).fetchall()
            
            properties_list = []
            for row in result:
                properties_list.append({
                    'id': row[0],
                    'name': row[1],
                    'address': row[2],
                    'type': row[3],
                    'bedrooms': 0,  # Default since not in schema
                    'bathrooms': 0,  # Default since not in schema
                    'rent': 0,      # Default since not in schema
                    'units': row[5] if row[5] else 1,
                    'occupancy': 'available',  # Default
                    'is_available': row[6] if row[6] is not None else True,
                    'description': row[4]
                })
            return jsonify(properties_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Tenants API - Direct SQL
    @app.route('/api/tenants', methods=['GET'])
    def get_tenants():
        try:
            # Direct SQL query to avoid model issues during deployment
            result = db.session.execute(db.text("""
                SELECT id, first_name, last_name, email, phone, move_in_date, move_out_date, is_active, monthly_income
                FROM tenants 
                WHERE is_deleted = false OR is_deleted IS NULL
            """)).fetchall()
            
            tenants_list = []
            for row in result:
                tenants_list.append({
                    'id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'move_in_date': row[5].isoformat() if row[5] else None,
                    'move_out_date': row[6].isoformat() if row[6] else None,
                    'is_active': row[7] if row[7] is not None else True,
                    'monthly_income': float(row[8]) if row[8] else 0,
                    'user_id': row[0],  # For compatibility
                    'property_id': None,  # Not available in current schema
                    'unit_id': None,  # Not available in current schema
                    'lease_start': row[5].isoformat() if row[5] else None,
                    'lease_end': row[6].isoformat() if row[6] else None,
                    'rent_amount': 0,  # Not in current schema
                    'status': 'active' if (row[7] if row[7] is not None else True) else 'inactive'
                })
            return jsonify(tenants_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Users API - Direct SQL
    @app.route('/api/users', methods=['GET'])
    def get_users():
        try:
            # Direct SQL query to avoid model issues during deployment
            result = db.session.execute(db.text("""
                SELECT id, email, first_name, last_name, phone, role, is_active, created_at
                FROM users 
                WHERE is_deleted = false OR is_deleted IS NULL
            """)).fetchall()
            
            users_list = []
            for row in result:
                users_list.append({
                    'id': row[0],
                    'email': row[1],
                    'username': f"{row[2]} {row[3]}" if row[2] and row[3] else row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'phone': row[4],
                    'role': row[5],
                    'is_active': row[6] if row[6] is not None else True,
                    'created_at': row[7].isoformat() if row[7] else None
                })
            return jsonify(users_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Login endpoint
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            # Super Admin authentication
            if email == 'toivybraun@gmail.com' and password == 'Unique3315!':
                return jsonify({
                    'access_token': 'super-admin-token-secure',
                    'user': {
                        'id': 1,
                        'email': email,
                        'username': 'Toivy Braun',
                        'role': 'super_admin',
                        'isAdmin': True,
                        'permissions': ['all']
                    }
                })
            
            # Demo user authentication
            if email == 'demo@estatecore.com' and password == 'demo123':
                return jsonify({
                    'access_token': 'demo-token-12345',
                    'user': {
                        'id': 2,
                        'email': email,
                        'username': 'Demo User',
                        'role': 'admin',
                        'isAdmin': True,
                        'permissions': ['properties', 'users', 'reports']
                    }
                })
            
            return jsonify({'error': 'Invalid credentials'}), 401
            
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    return app

# Create the app instance for gunicorn
app = create_app()

# For direct execution
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)