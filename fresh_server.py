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
     origins=["*"], 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-User-Email'],
     supports_credentials=True)

# Additional manual CORS handling
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Email')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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

@app.route('/test')
def test():
    return jsonify({'message': 'test endpoint working'})

@app.route('/api/auth/user', methods=['GET'])
def get_auth_user():
    # Return mock user data for now
    return jsonify({
        'id': 1,
        'email': 'admin@example.com',
        'name': 'Admin User',
        'role': 'admin'
    })

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    # Return mock dashboard data
    return jsonify({
        'totalProperties': 9,
        'totalTenants': 45,
        'totalRevenue': 125000,
        'occupancyRate': 0.85
    })

# Handle preflight requests for all API routes
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_preflight(path):
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Email')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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

@app.route('/api/tenants', methods=['POST'])
def create_tenant():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create tenant as a user with role 'tenant'
        user_data = {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'role': 'tenant',
            'company_id': data.get('company_id', 1),
            'status': 'active',
            'is_first_login': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        user_id = DatabaseManager.create_user(user_data)
        return jsonify({
            'success': True,
            'message': 'Tenant created successfully',
            'tenant_id': user_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tenants/<int:tenant_id>', methods=['DELETE'])
def delete_tenant(tenant_id):
    try:
        # Delete tenant (which is a user with role 'tenant')
        success = DatabaseManager.delete_user(tenant_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Tenant deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete tenant'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tenants/<int:tenant_id>', methods=['PUT'])
def update_tenant(tenant_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add updated timestamp
        data['updated_at'] = datetime.now().isoformat()
        
        # Update tenant (user) in database
        success = DatabaseManager.update_user(tenant_id, data)
        if success:
            return jsonify({
                'success': True,
                'message': 'Tenant updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update tenant'}), 500
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
    print("   POST /api/tenants")
    print("   PUT  /api/tenants/{id}")
    print("   DELETE /api/tenants/{id}")
    print("   GET  /api/units?property_id=1")
    print("   POST /api/units")
    print("   POST /api/ai/process-lease")
    
    app.run(host='0.0.0.0', port=5004, debug=False)