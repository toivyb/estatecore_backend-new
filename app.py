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
current_user_id = 0  # System Admin (super_admin) - can see all properties

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
    total_revenue = sum(
        float(t['rent_amount']) for t in user_tenants 
        if t.get('rent_amount') and isinstance(t['rent_amount'], (int, float, str)) and str(t['rent_amount']).replace('.', '').isdigit()
    )
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
    environment = 'Production' if os.environ.get('RENDER') else 'Development'
    return jsonify({
        'message': f'EstateCore API v6.0 - {environment} Ready', 
        'status': 'running',
        'database': 'Connected',
        'environment': environment
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
            'data': metrics,  # Frontend expects 'data' not 'metrics'
            'metrics': metrics,  # Keep both for compatibility
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
        
        # If user is authenticated and not super_admin, return their company info
        user = get_current_user()
        if user and user.role != 'super_admin' and user.company_id:
            user_company = next((c for c in companies_data if c['id'] == user.company_id), None)
            if user_company:
                return jsonify({
                    'success': True,
                    'company': user_company,  # Single company for frontend
                    'companies': companies_data  # Full list for compatibility
                })
        
        return jsonify({
            'success': True,
            'companies': companies_data,
            'company': companies_data[0] if companies_data else None  # Default to first company
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies', methods=['POST'])
def create_company():
    """Create a new company"""
    try:
        print(f"=== Company Creation Request ===")
        print(f"Method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Raw data: {request.get_data()}")
        
        data = request.get_json()
        print(f"Parsed JSON data: {data}")
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('billing_email'):
            error_msg = 'Name and billing email are required'
            print(f"Validation error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Set defaults for optional fields
        data.setdefault('subscription_plan', 'trial')
        data.setdefault('status', 'active')
        data.setdefault('auto_billing', True)
        data.setdefault('payment_method', 'card')
        
        # Add timestamp
        data['created_at'] = datetime.now().isoformat()
        print(f"Final data to create: {data}")
        
        # Create company in database
        print("Calling DatabaseManager.create_company...")
        company_id = DatabaseManager.create_company(data)
        print(f"Company created with ID: {company_id}")
        
        response = {
            'success': True,
            'message': f'Company "{data["name"]}" created successfully',
            'company_id': company_id
        }
        print(f"Success response: {response}")
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"ERROR creating company: {error_msg}")
        print(f"Full traceback: {error_trace}")
        print(f"Request data: {data if 'data' in locals() else 'No data received'}")
        
        return jsonify({
            'success': False, 
            'error': error_msg,
            'details': 'Check server logs for full error trace'
        }), 500

@app.route('/api/companies/<int:company_id>', methods=['PUT', 'DELETE'])
def handle_company(company_id):
    """Handle company update and delete operations"""
    if request.method == 'PUT':
        # Update company information
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
    
    elif request.method == 'DELETE':
        # Delete company and all associated data
        try:
            # Get company first to check if it exists
            company = DatabaseManager.get_company_by_id(company_id)
            if not company:
                return jsonify({'success': False, 'error': 'Company not found'}), 404
            
            company_name = company['name']
            
            # Get all users associated with this company
            users = DatabaseManager.get_users()
            company_users = [user for user in users if user['company_id'] == company_id]
            
            # Get all properties associated with this company
            properties = DatabaseManager.get_properties_by_company(company_id)
            
            # Delete all tenants from company properties
            for prop in properties:
                tenants = DatabaseManager.get_tenants_by_property(prop['id'])
                for tenant in tenants:
                    DatabaseManager.delete_tenant(tenant['id'])
            
            # Delete all properties
            for prop in properties:
                DatabaseManager.delete_property(prop['id'])
            
            # Delete all users (this will handle property access cleanup)
            for user in company_users:
                DatabaseManager.delete_user(user['id'])
            
            # Finally delete the company
            success = DatabaseManager.delete_company(company_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Company "{company_name}" and all associated data deleted successfully',
                    'deleted_users': len(company_users),
                    'deleted_properties': len(properties)
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to delete company'}), 500
                
        except Exception as e:
            print(f"Error deleting company {company_id}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/trial', methods=['POST'])
def extend_trial(company_id):
    """Extend company trial period"""
    try:
        data = request.get_json() or {}
        
        # Get company
        company = DatabaseManager.get_company_by_id(company_id)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        # Calculate new trial end date (default 30 days from now)
        from datetime import datetime, timedelta
        days_to_extend = data.get('days', 30)
        new_trial_end = (datetime.now() + timedelta(days=days_to_extend)).isoformat()
        
        # Update company trial
        update_data = {
            'name': company['name'],
            'subscription_plan': 'trial',  # Set to trial
            'billing_email': company['billing_email'],
            'status': 'active',
            'trial_ends_at': new_trial_end,
            'custom_domain': company.get('custom_domain'),
            'logo_url': company.get('logo_url'),
            'phone': company.get('phone'),
            'address': company.get('address'),
            'payment_method': company.get('payment_method', 'card'),
            'auto_billing': company.get('auto_billing', True),
            'mrr_override': company.get('mrr_override')
        }
        
        success = DatabaseManager.update_company(company_id, update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Trial extended for {days_to_extend} days',
                'trial_ends_at': new_trial_end
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to extend trial'}), 500
            
    except Exception as e:
        print(f"Error extending trial for company {company_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/suspend', methods=['POST'])
def suspend_company(company_id):
    """Suspend a company and deactivate all users"""
    try:
        # Get company
        company = DatabaseManager.get_company_by_id(company_id)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        # Update company status to suspended
        update_data = dict(company)
        update_data['status'] = 'suspended'
        
        success = DatabaseManager.update_company(company_id, update_data)
        
        if success:
            # Deactivate all company users
            users = DatabaseManager.get_users()
            for user in users:
                if user['company_id'] == company_id and user['status'] == 'active':
                    user_update = dict(user)
                    user_update['status'] = 'suspended'
                    DatabaseManager.update_user(user['id'], user_update)
            
            return jsonify({
                'success': True,
                'message': f'Company "{company["name"]}" suspended and all users deactivated'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to suspend company'}), 500
            
    except Exception as e:
        print(f"Error suspending company {company_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/activate', methods=['POST'])
def activate_company(company_id):
    """Activate a suspended company and reactivate all users"""
    try:
        # Get company
        company = DatabaseManager.get_company_by_id(company_id)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        # Update company status to active
        update_data = dict(company)
        update_data['status'] = 'active'
        
        success = DatabaseManager.update_company(company_id, update_data)
        
        if success:
            # Reactivate all company users
            users = DatabaseManager.get_users()
            for user in users:
                if user['company_id'] == company_id and user['status'] == 'suspended':
                    user_update = dict(user)
                    user_update['status'] = 'active'
                    DatabaseManager.update_user(user['id'], user_update)
            
            return jsonify({
                'success': True,
                'message': f'Company "{company["name"]}" activated and all users reactivated'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to activate company'}), 500
            
    except Exception as e:
        print(f"Error activating company {company_id}: {str(e)}")
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
        
        # Frontend expects either array directly (success) or error object
        # For compatibility with frontend validation logic  
        if properties_data and len(properties_data) > 0:
            return jsonify(properties_data)  # Return array directly for successful responses
        else:
            return jsonify({
                'success': True,
                'properties': properties_data,
                'message': 'No properties found'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/properties', methods=['POST'])
def create_property():
    """Create a new property"""
    try:
        data = request.get_json()
        print(f"Property creation request data: {data}")  # Debug logging
        
        # Validate required fields
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Property name is required'}), 400
            
        if not data.get('address'):
            return jsonify({'success': False, 'error': 'Property address is required'}), 400
            
        if not data.get('company_id'):
            return jsonify({'success': False, 'error': 'Company ID is required'}), 400
        
        # Verify company exists
        company = DatabaseManager.get_company_by_id(data['company_id'])
        if not company:
            return jsonify({'success': False, 'error': 'Invalid company ID'}), 400
        
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

@app.route('/api/properties/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    """Delete a property"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Check if property exists
        property_data = DatabaseManager.get_property_by_id(property_id)
        if not property_data:
            return jsonify({'success': False, 'error': 'Property not found'}), 404
        
        # Check if user has access to this property
        if user.role != 'super_admin' and property_data['company_id'] != user.company_id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # Check if property has tenants
        tenants = DatabaseManager.get_tenants_by_property(property_id)
        if tenants:
            return jsonify({
                'success': False, 
                'error': f'Cannot delete property with {len(tenants)} active tenants. Please remove tenants first.'
            }), 400
        
        # Delete the property (note: we need to add delete method to DatabaseManager)
        query = "DELETE FROM properties WHERE id = ?"
        DatabaseManager.execute_query(query, (property_id,))
        
        return jsonify({
            'success': True,
            'message': f'Property "{property_data["name"]}" deleted successfully'
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
        
        # Frontend expects either array directly (success) or error object
        # For compatibility with frontend validation logic
        if tenants_data and len(tenants_data) > 0:
            return jsonify(tenants_data)  # Return array directly for successful responses
        else:
            return jsonify({
                'success': True,
                'tenants': tenants_data,
                'message': 'No tenants found'
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

@app.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    """Reset user password and generate new OTP"""
    try:
        # Check if user exists
        user_data = DatabaseManager.get_user_by_id(user_id)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Generate new OTP
        import secrets
        import string
        otp = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # Update user with new OTP and reset password
        update_data = dict(user_data)
        update_data['otp'] = otp
        update_data['is_first_login'] = True
        update_data['password_hash'] = None  # Clear password to force reset
        
        success = DatabaseManager.update_user(user_id, update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Password reset for {user_data["name"]}. New OTP: {otp}',
                'otp': otp  # In production, send via email instead
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to reset password'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/set-password', methods=['POST'])
def set_user_password(user_id):
    """Administratively set a user's password"""
    try:
        data = request.get_json()
        
        if not data or not data.get('password'):
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        password = data['password']
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        user_data = DatabaseManager.get_user_by_id(user_id)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Hash the new password
        password_hash = hash_password(password)
        
        # Update user with new password
        update_data = dict(user_data)
        update_data['password_hash'] = password_hash
        update_data['is_first_login'] = False  # Mark as not first login since password is set
        update_data['otp'] = None  # Clear OTP
        
        success = DatabaseManager.update_user(user_id, update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Password set successfully for {user_data["name"]}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to set password'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Demo endpoint for switching users (development only)
@app.route('/api/demo/switch-user/<int:user_id>', methods=['POST'])
def switch_user(user_id):
    """Switch current user for demo purposes (development only)"""
    global current_user_id
    try:
        # Check if user exists
        user_data = DatabaseManager.get_user_by_id(user_id)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Switch to the user
        current_user_id = user_id
        
        return jsonify({
            'success': True,
            'message': f'Switched to user: {user_data["name"]}',
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

# Authentication and user routes
@app.route('/api/auth/user', methods=['GET'])
def get_current_user_info():
    """Get current authenticated user info"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Get company information
        company_data = None
        if user.company_id:
            company_data = DatabaseManager.get_company_by_id(user.company_id)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'company_id': user.company_id,
                'company_name': company_data['name'] if company_data else 'No Company',
                'status': user.status
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Company analytics routes
@app.route('/api/companies/analytics', methods=['GET'])
def get_companies_analytics():
    """Get platform-wide company analytics"""
    try:
        companies_data = DatabaseManager.get_companies()
        
        total_companies = len(companies_data)
        active_companies = len([c for c in companies_data if c['status'] == 'active'])
        
        # Calculate total MRR and units
        total_mrr = 0
        total_units = 0
        plan_distribution = {'trial': 0, 'basic': 0, 'premium': 0, 'enterprise': 0}
        
        for company in companies_data:
            company_obj = Company(company)
            total_mrr += company_obj.monthly_fee
            
            properties = DatabaseManager.get_properties_by_company(company['id'])
            company_units = sum(p['units'] for p in properties)
            total_units += company_units
            
            plan = company['subscription_plan']
            if plan in plan_distribution:
                plan_distribution[plan] += 1
        
        # Calculate growth metrics (mock data for demo)
        growth_data = [
            {'month': 'Jan', 'companies': 1, 'mrr': 150},
            {'month': 'Feb', 'companies': 2, 'mrr': 450},
            {'month': 'Mar', 'companies': 3, 'mrr': 750},
            {'month': 'Apr', 'companies': 4, 'mrr': total_mrr}
        ]
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_companies': total_companies,
                'active_companies': active_companies,
                'total_mrr': total_mrr,
                'total_units': total_units,
                'plan_distribution': plan_distribution,
                'growth_data': growth_data,
                'avg_units_per_company': round(total_units / max(total_companies, 1), 1),
                'avg_mrr_per_company': round(total_mrr / max(active_companies, 1), 2)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/metrics', methods=['GET'])
def get_company_metrics(company_id):
    """Get detailed metrics for a specific company (alias for analytics)"""
    return get_company_analytics(company_id)

@app.route('/api/companies/<int:company_id>/analytics', methods=['GET'])
def get_company_analytics(company_id):
    """Get analytics for a specific company"""
    try:
        company = DatabaseManager.get_company_by_id(company_id)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        properties = DatabaseManager.get_properties_by_company(company_id)
        
        total_properties = len(properties)
        total_units = sum(p['units'] for p in properties)
        occupied_units = sum(p['occupied_units'] for p in properties)
        
        # Get tenants for revenue calculation
        total_revenue = 0
        total_tenants = 0
        for prop in properties:
            tenants = DatabaseManager.get_tenants_by_property(prop['id'])
            total_tenants += len(tenants)
            total_revenue += sum(t['rent_amount'] for t in tenants if t['rent_amount'])
        
        occupancy_rate = round((occupied_units / max(total_units, 1)) * 100, 1)
        
        company_obj = Company(company)
        monthly_fee = company_obj.monthly_fee
        
        return jsonify({
            'success': True,
            'analytics': {
                'company_id': company_id,
                'company_name': company['name'],
                'total_properties': total_properties,
                'total_units': total_units,
                'occupied_units': occupied_units,
                'total_tenants': total_tenants,
                'total_revenue': total_revenue,
                'monthly_fee': monthly_fee,
                'occupancy_rate': occupancy_rate,
                'subscription_plan': company['subscription_plan'],
                'status': company['status']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# AI lease expiration check endpoint
@app.route('/api/ai/lease-expiration-check', methods=['GET'])
def ai_lease_expiration_check():
    """AI-powered lease expiration analysis and recommendations"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Get lease expiration data using existing function
        lease_data = calculate_lease_expirations(user)
        expiring_leases = lease_data['expiring_leases']
        
        # AI analysis and recommendations
        ai_recommendations = []
        critical_actions = []
        
        for lease in expiring_leases:
            days_until_expiry = lease['days_until_expiry']
            tenant_name = lease['tenant_name']
            property_name = lease['property_name']
            
            if days_until_expiry <= 30:
                # Critical: Immediate action needed
                recommendation = {
                    'type': 'critical',
                    'tenant': tenant_name,
                    'property': property_name,
                    'days_remaining': days_until_expiry,
                    'action': f"URGENT: Contact {tenant_name} immediately for lease renewal discussion",
                    'priority': 'high',
                    'suggested_actions': [
                        'Schedule face-to-face meeting within 3 days',
                        'Prepare lease renewal terms and pricing',
                        'Research current market rates for comparison',
                        'Have backup marketing plan ready if tenant leaves'
                    ]
                }
                critical_actions.append(f"Contact {tenant_name} - {days_until_expiry} days remaining")
            elif days_until_expiry <= 60:
                # Medium priority: Start planning
                recommendation = {
                    'type': 'medium',
                    'tenant': tenant_name,
                    'property': property_name,
                    'days_remaining': days_until_expiry,
                    'action': f"Begin lease renewal process with {tenant_name}",
                    'priority': 'medium',
                    'suggested_actions': [
                        'Send initial lease renewal notice',
                        'Review tenant payment history and satisfaction',
                        'Prepare competitive lease terms',
                        'Schedule property inspection if needed'
                    ]
                }
            else:
                # Low priority: Early planning
                recommendation = {
                    'type': 'low',
                    'tenant': tenant_name,
                    'property': property_name,
                    'days_remaining': days_until_expiry,
                    'action': f"Monitor and prepare for {tenant_name} lease renewal",
                    'priority': 'low',
                    'suggested_actions': [
                        'Review tenant satisfaction and history',
                        'Plan any necessary property improvements',
                        'Research market trends for renewal pricing',
                        'Begin early renewal discussions if tenant is excellent'
                    ]
                }
            
            ai_recommendations.append(recommendation)
        
        # Generate AI insights
        total_expiring = len(expiring_leases)
        revenue_at_risk = sum(
            tenant.get('rent_amount', 0) for tenant in expiring_leases 
            if isinstance(tenant.get('rent_amount'), (int, float))
        )
        
        ai_insights = {
            'revenue_at_risk': revenue_at_risk,
            'critical_renewals': len([r for r in ai_recommendations if r['type'] == 'critical']),
            'success_probability': max(70 - (total_expiring * 5), 30),  # Simple AI model
            'recommended_strategy': (
                'Focus on high-value tenants first. Consider offering incentives for early renewals.'
                if total_expiring > 5 else
                'Standard renewal process should be sufficient.'
            )
        }
        
        ai_analysis_data = {
            'total_expiring_leases': total_expiring,
            'critical_actions_needed': len(critical_actions),
            'ai_recommendations': ai_recommendations,
            'critical_actions': critical_actions,
            'insights': ai_insights,
            'analysis_timestamp': datetime.now().isoformat(),
            'confidence_score': 0.85
        }
        
        return jsonify({
            'success': True,
            'data': ai_analysis_data,  # Frontend expects 'data'
            'ai_analysis': ai_analysis_data  # Keep both for compatibility
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# AI maintenance prediction endpoint
@app.route('/api/maintenance/predict', methods=['POST'])
def predict_maintenance():
    """AI-powered maintenance prediction"""
    try:
        data = request.get_json()
        property_id = data.get('property_id')
        
        if not property_id:
            return jsonify({'success': False, 'error': 'Property ID is required'}), 400
        
        # Mock AI maintenance prediction
        predictions = [
            {
                'type': 'HVAC System',
                'risk_level': 'medium',
                'predicted_failure_date': '2025-11-15',
                'confidence': 0.78,
                'estimated_cost': 850,
                'recommended_action': 'Schedule preventive maintenance within 30 days'
            },
            {
                'type': 'Plumbing',
                'risk_level': 'low',
                'predicted_failure_date': '2026-03-20',
                'confidence': 0.65,
                'estimated_cost': 420,
                'recommended_action': 'Monitor for 6 months'
            }
        ]
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'analysis_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# AI damage assessment endpoint
@app.route('/api/ai/assess-damage', methods=['POST'])
def assess_damage():
    """AI-powered damage assessment"""
    try:
        data = request.get_json()
        
        # Mock AI damage assessment
        assessment = {
            'damage_type': data.get('damage_type', 'unknown'),
            'severity': 'moderate',
            'estimated_repair_cost': 1250,
            'urgency': 'medium',
            'recommended_contractor_type': 'general_contractor',
            'estimated_completion_time': '3-5 days',
            'ai_confidence': 0.82,
            'assessment_notes': 'Based on description and property history, this appears to be standard wear and repair needs.'
        }
        
        return jsonify({
            'success': True,
            'assessment': assessment,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check for Render
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# Test DELETE endpoint
@app.route('/api/test-delete/<int:test_id>', methods=['DELETE'])
def test_delete(test_id):
    return jsonify({'success': True, 'message': f'DELETE test successful for ID {test_id}'})

# Debug endpoint to get ALL properties without access control
@app.route('/api/properties/all', methods=['GET'])
def get_all_properties():
    """Get ALL properties without access control - for debugging"""
    try:
        properties = DatabaseManager.get_properties()
        
        # Add additional information to each property
        for prop in properties:
            # Get tenant count
            tenants = DatabaseManager.get_tenants_by_property(prop['id'])
            prop['tenant_count'] = len(tenants)
            
            # Get company name
            company = DatabaseManager.get_company_by_id(prop['company_id'])
            prop['company_name'] = company['name'] if company else 'Unknown'
            
            # Get property manager name
            if prop.get('property_manager_id'):
                manager = DatabaseManager.get_user_by_id(prop['property_manager_id'])
                prop['property_manager_name'] = manager['name'] if manager else 'Unknown'
            else:
                prop['property_manager_name'] = 'Unassigned'
        
        return jsonify(properties)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =================== UNITS ENDPOINTS ===================

@app.route('/api/units', methods=['GET'])
def get_units():
    """Get units for a specific property"""
    try:
        property_id = request.args.get('property_id')
        
        if not property_id:
            return jsonify({'success': False, 'error': 'property_id is required'}), 400
        
        # Get units from database
        units = DatabaseManager.get_units_by_property(int(property_id))
        
        return jsonify(units)
    except Exception as e:
        print(f"Error getting units: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/units', methods=['POST'])
def create_unit():
    """Create a new unit"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['property_id', 'unit_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Create unit data
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
        
        # Save to database
        unit_id = DatabaseManager.create_unit(unit_data)
        
        if unit_id:
            return jsonify({
                'success': True,
                'message': 'Unit created successfully',
                'unit_id': unit_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create unit'}), 500
            
    except Exception as e:
        print(f"Error creating unit: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/units/<int:unit_id>', methods=['PUT'])
def update_unit(unit_id):
    """Update an existing unit"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Add updated timestamp
        data['updated_at'] = datetime.now().isoformat()
        
        # Update unit in database
        success = DatabaseManager.update_unit(unit_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Unit updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update unit'}), 500
            
    except Exception as e:
        print(f"Error updating unit: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/units/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    """Delete a unit"""
    try:
        # Check if unit exists
        unit = DatabaseManager.get_unit_by_id(unit_id)
        if not unit:
            return jsonify({'success': False, 'error': 'Unit not found'}), 404
        
        # Delete unit from database
        success = DatabaseManager.delete_unit(unit_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Unit deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete unit'}), 500
            
    except Exception as e:
        print(f"Error deleting unit: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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