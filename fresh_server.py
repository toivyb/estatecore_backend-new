#!/usr/bin/env python3
"""
Fresh Flask server with all endpoints for EstateCore frontend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database_connection import DatabaseManager
from datetime import datetime

# Create a brand new Flask app
app = Flask(__name__)

# Enable CORS for all routes and methods
CORS(app, 
     origins=['http://localhost:3021', 'http://localhost:3020', 'http://localhost:3019'], 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])

@app.route('/')
def home():
    return jsonify({
        'message': 'EstateCore Fresh Server - All Endpoints',
        'status': 'running',
        'version': '1.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'server': 'fresh'})

# =================== PROPERTIES ===================
@app.route('/api/properties', methods=['GET'])
def get_properties():
    try:
        properties = DatabaseManager.get_properties()
        return jsonify(properties)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =================== COMPANIES ===================
@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        companies = DatabaseManager.get_companies()
        return jsonify(companies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =================== USERS/TENANTS ===================
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = DatabaseManager.get_users()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_data = {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'role': data.get('role', 'tenant'),
            'company_id': data.get('company_id', 1),
            'status': 'active',
            'is_first_login': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        user_id = DatabaseManager.create_user(user_data)
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': user_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tenants', methods=['GET'])
def get_tenants():
    try:
        tenants = DatabaseManager.get_tenants()
        return jsonify(tenants)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =================== AI ENDPOINTS ===================
@app.route('/api/ai/process-lease', methods=['POST'])
def process_lease():
    try:
        return jsonify({
            'success': True,
            'message': 'Lease processed successfully',
            'data': {
                'tenant_name': 'AI Extracted Name',
                'lease_start': '2025-01-01',
                'lease_end': '2025-12-31',
                'rent_amount': 1500
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =================== UNITS ===================
@app.route('/api/units', methods=['GET'])
def get_units():
    try:
        property_id = request.args.get('property_id')
        if not property_id:
            return jsonify({'error': 'property_id required'}), 400
        
        units = DatabaseManager.get_units_by_property(int(property_id))
        return jsonify(units)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/units', methods=['POST'])
def create_unit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        unit_data = {
            'property_id': data['property_id'],
            'unit_number': data['unit_number'],
            'bedrooms': data.get('bedrooms', 1),
            'bathrooms': data.get('bathrooms', 1),
            'square_feet': data.get('square_feet', 0),
            'rent': data.get('rent', 0),
            'status': data.get('status', 'vacant'),
            'description': data.get('description', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        unit_id = DatabaseManager.create_unit(unit_data)
        return jsonify({
            'success': True,
            'message': 'Unit created successfully',
            'unit_id': unit_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=== ESTATECORE FRESH SERVER ===")
    print("URL: http://localhost:5004")
    print("Endpoints:")
    print("   GET  /health")
    print("   GET  /api/properties")
    print("   GET  /api/companies") 
    print("   GET  /api/users")
    print("   POST /api/users")
    print("   GET  /api/tenants")
    print("   GET  /api/units?property_id=1")
    print("   POST /api/units")
    print("   POST /api/ai/process-lease")
    
    app.run(host='0.0.0.0', port=5004, debug=False)