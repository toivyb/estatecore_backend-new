#!/usr/bin/env python3
"""
EstateCore Flask API with SQLite Database Integration
Multi-tenant SaaS property management platform
"""

import os
import random
import secrets
import string
import hashlib
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from database_connection import DatabaseManager, Company, User, hash_password

# Create Flask app
app = Flask(__name__)
CORS(app, origins=['*'],  # Allow all origins for production
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])

# Global current user for authentication simulation
current_user_id = 1  # Default to a valid user

def get_current_user():
    """Get current authenticated user from database"""
    user_data = DatabaseManager.get_user_by_id(current_user_id)
    if user_data:
        return User(user_data)
    return None

def filter_data_by_user_access(user, data_type="dashboard"):
    """Filter data based on user's access level"""
    if user.role == 'super_admin':
        # Super admin sees all data
        properties = DatabaseManager.get_properties()
        tenants = DatabaseManager.get_tenants()
    elif user.role == 'company_admin':
        # Company admin sees all company data
        properties = DatabaseManager.get_properties_by_company(user.company_id)
        tenants = []
        for prop in properties:
            tenants.extend(DatabaseManager.get_tenants_by_property(prop['id']))
    else:
        # Property managers see only their assigned properties
        # For now, show company properties (implement property-specific access later)
        properties = DatabaseManager.get_properties_by_company(user.company_id)
        tenants = []
        for prop in properties:
            tenants.extend(DatabaseManager.get_tenants_by_property(prop['id']))
    
    return {
        'properties': properties,
        'tenants': tenants,
        'property_ids': [p['id'] for p in properties]
    }

def calculate_dashboard_metrics(user=None):
    """Calculate real-time dashboard metrics from database"""
    if user is None:
        user = get_current_user()
    
    # Get data filtered by user's access level
    user_data = filter_data_by_user_access(user)
    user_properties = user_data['properties']
    user_tenants = user_data['tenants']
    
    total_properties = len(user_properties)
    total_units = sum(p['units'] for p in user_properties)
    occupied_units = sum(p['occupied_units'] for p in user_properties)
    available_properties = len([p for p in user_properties if p['occupied_units'] < p['units']])
    total_tenants = len(user_tenants)
    
    # Calculate revenue from user's accessible tenants only
    total_revenue = sum(t['rent_amount'] for t in user_tenants if t['rent_amount'])
    pending_revenue = total_revenue * 0.05  # Assume 5% pending
    
    occupancy_rate = round((occupied_units / total_units) * 100, 1) if total_units > 0 else 0
    
    # Get company info
    company_data = DatabaseManager.get_company_by_id(user.company_id) if user.company_id else None
    company_name = company_data['name'] if company_data else "Unknown Company"
    
    return {
        'total_properties': total_properties,
        'available_properties': available_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'total_tenants': total_tenants,
        'total_users': total_tenants,
        'total_revenue': int(total_revenue),
        'pending_revenue': int(pending_revenue),
        'occupancy_rate': occupancy_rate,
        'company_name': company_name,
        'user_role': user.role,
        'accessible_property_count': len(user_properties)
    }

def calculate_lease_expirations(user=None):
    """Calculate lease expirations from database"""
    if user is None:
        user = get_current_user()
    
    current_date = datetime.now()
    expiring_leases = []
    
    # Get only tenants that the user can access
    user_data = filter_data_by_user_access(user)
    user_tenants = user_data['tenants']
    user_properties = user_data['properties']
    
    for tenant in user_tenants:
        if not tenant['lease_end_date']:
            continue
            
        lease_end = datetime.strptime(tenant['lease_end_date'], "%Y-%m-%d")
        days_until_expiry = (lease_end - current_date).days
        
        if days_until_expiry <= 90:  # Leases expiring within 90 days
            property_name = next((p['name'] for p in user_properties if p['id'] == tenant['property_id']), "Unknown Property")
            
            if days_until_expiry <= 30:
                priority = "high"
            elif days_until_expiry <= 60:
                priority = "medium"
            else:
                priority = "low"
            
            expiring_leases.append({
                'tenant_name': tenant['name'],
                'property_name': property_name,
                'unit_number': tenant['unit_number'],
                'lease_end_date': tenant['lease_end_date'],
                'days_until_expiry': days_until_expiry,
                'priority': priority
            })
    
    high_priority_count = len([lease for lease in expiring_leases if lease['priority'] == 'high'])
    
    return {
        'total_count': len(expiring_leases),
        'high_priority_count': high_priority_count,
        'expiring_leases': sorted(expiring_leases, key=lambda x: x['days_until_expiry'])
    }

# API Routes

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@app.route('/')
def home():
    return jsonify({
        'message': 'EstateCore API v6.0 - Production Ready', 
        'status': 'running',
        'database': 'Connected',
        'environment': 'Production'
    })

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard data with real metrics from database"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        metrics = calculate_dashboard_metrics(user)
        lease_data = calculate_lease_expirations(user)
        
        # Get recent activities from database
        recent_properties = DatabaseManager.get_properties()[-5:]  # Last 5 properties
        recent_tenants = DatabaseManager.get_tenants()[-5:]  # Last 5 tenants
        
        activities = []
        for prop in recent_properties:
            activities.append({
                'type': 'property_added',
                'message': f"New property '{prop['name']}' added",
                'timestamp': prop.get('created_at', datetime.now().isoformat())
            })
        
        for tenant in recent_tenants:
            activities.append({
                'type': 'tenant_added', 
                'message': f"New tenant '{tenant['name']}' added",
                'timestamp': tenant.get('created_at', datetime.now().isoformat())
            })
        
        # Sort activities by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'lease_expirations': lease_data,
            'recent_activities': activities[:10]  # Last 10 activities
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Get all companies"""
    try:
        companies_data = DatabaseManager.get_companies()
        
        # Add calculated metrics to each company
        for company in companies_data:
            company_obj = Company(company)
            company['monthly_fee'] = company_obj.monthly_fee
            
            # Get property count
            properties = DatabaseManager.get_properties_by_company(company['id'])
            company['property_count'] = len(properties)
            company['total_units'] = sum(p['units'] for p in properties)
        
        return jsonify({
            'success': True,
            'companies': companies_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies', methods=['POST'])
def create_company():
    """Create a new company"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('billing_email'):
            return jsonify({'success': False, 'error': 'Name and billing email are required'}), 400
        
        # Add timestamp
        data['created_at'] = datetime.now().isoformat()
        
        company_id = DatabaseManager.create_company(data)
        
        return jsonify({
            'success': True,
            'message': f'Company "{data["name"]}" created successfully',
            'company_id': company_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>', methods=['PUT'])
def update_company(company_id):
    """Update company information"""
    try:
        data = request.get_json()
        
        # Check if company exists
        existing_company = DatabaseManager.get_company_by_id(company_id)
        if not existing_company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        # Update company
        success = DatabaseManager.update_company(company_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Company updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update company'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        users_data = DatabaseManager.get_users()
        
        # Add company information to each user
        for user in users_data:
            if user['company_id']:
                company = DatabaseManager.get_company_by_id(user['company_id'])
                user['company_name'] = company['name'] if company else 'Unknown'
            else:
                user['company_name'] = 'No Company'
            
            # Remove sensitive data
            user.pop('password_hash', None)
            user.pop('otp', None)
        
        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('email') or not data.get('role'):
            return jsonify({'success': False, 'error': 'Name, email, and role are required'}), 400
        
        # Check if email already exists
        existing_user = DatabaseManager.get_user_by_email(data['email'])
        if existing_user:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Generate OTP or handle password setup
        if data.get('use_otp', True):
            # Generate OTP
            otp = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            data['otp'] = otp
            data['is_first_login'] = True
            setup_method = 'otp'
        else:
            # Email link method or temporary password
            data['otp'] = None
            data['is_first_login'] = True
            if data.get('temp_password'):
                data['password_hash'] = hash_password(data['temp_password'])
            setup_method = 'email_link'
        
        # Create user
        user_id = DatabaseManager.create_user(data)
        
        response_data = {
            'success': True,
            'message': f'User "{data["name"]}" created successfully',
            'user_id': user_id,
            'setup_method': setup_method
        }
        
        if setup_method == 'otp':
            response_data['otp'] = data['otp']
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user"""
    try:
        user_data = DatabaseManager.get_user_by_id(user_id)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Add company information
        if user_data['company_id']:
            company = DatabaseManager.get_company_by_id(user_data['company_id'])
            user_data['company_name'] = company['name'] if company else 'Unknown'
        else:
            user_data['company_name'] = 'No Company'
        
        # Remove sensitive data
        user_data.pop('password_hash', None)
        user_data.pop('otp', None)
        
        return jsonify({
            'success': True,
            'user': user_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        # Check if user exists
        existing_user = DatabaseManager.get_user_by_id(user_id)
        if not existing_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Prevent deleting super admin
        if existing_user['role'] == 'super_admin':
            return jsonify({'success': False, 'error': 'Cannot delete super admin user'}), 403
        
        # Handle foreign key references before deleting user
        try:
            # Remove user as property manager (set to NULL)
            query = "UPDATE properties SET property_manager_id = NULL WHERE property_manager_id = ?"
            DatabaseManager.execute_query(query, (user_id,))
            
            # Remove user property access records
            query = "DELETE FROM user_property_access WHERE user_id = ?"
            DatabaseManager.execute_query(query, (user_id,))
            
            # Delete user from database
            query = "DELETE FROM users WHERE id = ?"
            rows_affected = DatabaseManager.execute_query(query, (user_id,))
        except Exception as db_error:
            raise Exception(f"Database error during user deletion: {str(db_error)}")
        
        if rows_affected > 0:
            return jsonify({
                'success': True,
                'message': f'User "{existing_user["name"]}" deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User could not be deleted'
            }), 500
        
    except Exception as e:
        print(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user"""
    try:
        data = request.get_json()
        
        # Check if user exists
        existing_user = DatabaseManager.get_user_by_id(user_id)
        if not existing_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update user
        success = DatabaseManager.update_user(user_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'User updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update user'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/properties', methods=['GET'])
def get_properties():
    """Get properties based on user access"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        user_data = filter_data_by_user_access(user)
        properties_data = user_data['properties']
        
        # Add additional information to each property
        for prop in properties_data:
            # Get tenant count
            tenants = DatabaseManager.get_tenants_by_property(prop['id'])
            prop['tenant_count'] = len(tenants)
            
            # Get company name
            company = DatabaseManager.get_company_by_id(prop['company_id'])
            prop['company_name'] = company['name'] if company else 'Unknown'
            
            # Get property manager name
            if prop['property_manager_id']:
                manager = DatabaseManager.get_user_by_id(prop['property_manager_id'])
                prop['property_manager_name'] = manager['name'] if manager else 'Unassigned'
            else:
                prop['property_manager_name'] = 'Unassigned'
        
        return jsonify({
            'success': True,
            'properties': properties_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/properties', methods=['POST'])
def create_property():
    """Create a new property"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('address') or not data.get('company_id'):
            return jsonify({'success': False, 'error': 'Name, address, and company are required'}), 400
        
        # Create property
        property_id = DatabaseManager.create_property(data)
        
        # Update company billing based on new units
        company = DatabaseManager.get_company_by_id(data['company_id'])
        if company:
            company_obj = Company(company)
            new_monthly_fee = company_obj.monthly_fee
            
            return jsonify({
                'success': True,
                'message': f'Property "{data["name"]}" created successfully',
                'property_id': property_id,
                'billing_message': f'Company billing updated: ${new_monthly_fee:.2f}/month'
            })
        
        return jsonify({
            'success': True,
            'message': f'Property "{data["name"]}" created successfully',
            'property_id': property_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenants', methods=['GET'])
def get_tenants():
    """Get tenants based on user access"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        user_data = filter_data_by_user_access(user)
        tenants_data = user_data['tenants']
        properties_data = user_data['properties']
        
        # Add property information to each tenant
        for tenant in tenants_data:
            property_info = next((p for p in properties_data if p['id'] == tenant['property_id']), None)
            if property_info:
                tenant['property_name'] = property_info['name']
                tenant['property_address'] = property_info['address']
            else:
                tenant['property_name'] = 'Unknown Property'
                tenant['property_address'] = 'Unknown Address'
        
        return jsonify({
            'success': True,
            'tenants': tenants_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payments', methods=['GET'])
def get_payments():
    """Get payment history"""
    try:
        payments_data = DatabaseManager.get_payments()
        
        return jsonify({
            'success': True,
            'payments': payments_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/maintenance', methods=['GET'])
def get_maintenance():
    """Get maintenance requests"""
    try:
        maintenance_data = DatabaseManager.get_maintenance_requests()
        
        return jsonify({
            'success': True,
            'maintenance_requests': maintenance_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Authentication routes (simplified for development)
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple login for development"""
    global current_user_id
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        password = data.get('password')
        
        # Find user by email
        user_data = DatabaseManager.get_user_by_email(email)
        if not user_data:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        user = User(user_data)
        
        # Check OTP if provided
        if otp:
            if user.otp == otp:
                if user.is_first_login:
                    # User needs to set password
                    return jsonify({
                        'success': True,
                        'requires_password_change': True,
                        'temporary_token': 'temp_token_' + str(user.id),
                        'user_id': user.id
                    })
                else:
                    # Normal login
                    current_user_id = user.id
                    return jsonify({
                        'success': True,
                        'user': {
                            'id': user.id,
                            'name': user.name,
                            'email': user.email,
                            'role': user.role,
                            'company_id': user.company_id
                        }
                    })
            else:
                return jsonify({'success': False, 'error': 'Invalid OTP'}), 401
        
        # Check password if provided
        if password:
            password_hash = hash_password(password)
            if user.password_hash == password_hash:
                current_user_id = user.id
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                        'role': user.role,
                        'company_id': user.company_id
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Invalid password'}), 401
        
        return jsonify({'success': False, 'error': 'Email and password/OTP required'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/set-password', methods=['POST'])
def set_password():
    """Set password after OTP verification"""
    global current_user_id
    try:
        data = request.get_json()
        email = data.get('email')
        new_password = data.get('new_password')
        temporary_token = data.get('temporary_token')
        
        if not all([email, new_password, temporary_token]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Find user
        user_data = DatabaseManager.get_user_by_email(email)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update password
        password_hash = hash_password(new_password)
        update_data = {
            'name': user_data['name'],
            'email': user_data['email'],
            'company_id': user_data['company_id'],
            'role': user_data['role'],
            'password_hash': password_hash,
            'otp': None,  # Clear OTP
            'is_first_login': False,
            'phone': user_data['phone'],
            'status': user_data['status']
        }
        
        DatabaseManager.update_user(user_data['id'], update_data)
        
        # Set current user
        current_user_id = user_data['id']
        
        return jsonify({
            'success': True,
            'message': 'Password set successfully',
            'user': {
                'id': user_data['id'],
                'name': user_data['name'],
                'email': user_data['email'],
                'role': user_data['role'],
                'company_id': user_data['company_id']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists('estatecore.db'):
        print("Initializing database...")
        os.system('python database_setup.py')
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get('PORT', 5001))
    
    print("Starting EstateCore Production Server...")
    print(f"Environment: {'Production' if os.environ.get('RENDER') else 'Development'}")
    print(f"Port: {port}")
    print("API Endpoints:")
    print("  Dashboard: /api/dashboard")
    print("  Companies: /api/companies")
    print("  Properties: /api/properties")
    print("  Users: /api/users")
    print("  Health: /health")
    
    app.run(debug=False, host='0.0.0.0', port=port)