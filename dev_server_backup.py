#!/usr/bin/env python3
"""
Simplified Flask app for dashboard development
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

# Create Flask app
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:4173', 'http://localhost:3006'])

# Import services for real data
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Using real calculated data instead of importing complex services
print("Using calculated real data from property/tenant models")

# Multi-tenant SaaS data models
class Company:
    def __init__(self, id, name, subscription_plan, billing_email, created_at, status='active', 
                 trial_ends_at=None, custom_domain=None, logo_url=None, phone=None, 
                 address=None, payment_method=None, auto_billing=True, mrr_override=None):
        self.id = id
        self.name = name
        self.subscription_plan = subscription_plan  # trial, basic, premium, enterprise
        self.billing_email = billing_email
        self.created_at = created_at
        self.status = status  # trial, active, suspended, cancelled, past_due
        self.trial_ends_at = trial_ends_at
        self.custom_domain = custom_domain
        self.logo_url = logo_url
        self.phone = phone
        self.address = address
        self.payment_method = payment_method  # card, bank_transfer, invoice
        self.auto_billing = auto_billing
        self.mrr_override = mrr_override  # Manual override for custom pricing
        
        # Initialize new attributes for existing companies
        if not hasattr(self, 'trial_ends_at'):
            self.trial_ends_at = None
        if not hasattr(self, 'custom_domain'):
            self.custom_domain = None
        if not hasattr(self, 'logo_url'):
            self.logo_url = None
        if not hasattr(self, 'phone'):
            self.phone = None
        if not hasattr(self, 'address'):
            self.address = None
        if not hasattr(self, 'payment_method'):
            self.payment_method = 'card'
        if not hasattr(self, 'auto_billing'):
            self.auto_billing = True
        if not hasattr(self, 'mrr_override'):
            self.mrr_override = None
    
    def calculate_monthly_fee(self, total_units=0):
        """Calculate monthly fee based on units and plan"""
        if self.mrr_override:
            return self.mrr_override
            
        unit_prices = {
            'trial': 0.0,
            'basic': 2.0, 
            'premium': 2.5,
            'enterprise': 3.0
        }
        unit_price = unit_prices.get(self.subscription_plan, 2.0)
        return total_units * unit_price
    
    @property
    def monthly_fee(self):
        # Calculate based on company's total units
        company_properties = [p for p in properties if p.company_id == self.id]
        total_units = sum(p.units for p in company_properties)
        return self.calculate_monthly_fee(total_units)
    
    @property 
    def is_trial_expired(self):
        """Check if trial period has expired"""
        if not self.trial_ends_at:
            return False
        from datetime import datetime
        trial_end = datetime.fromisoformat(self.trial_ends_at.replace('Z', '+00:00'))
        return datetime.utcnow() < trial_end
    
    @property
    def days_until_trial_expires(self):
        """Get days remaining in trial"""
        if not self.trial_ends_at:
            return None
        from datetime import datetime
        trial_end = datetime.fromisoformat(self.trial_ends_at.replace('Z', '+00:00'))
        delta = trial_end - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def annual_revenue(self):
        """Calculate annual recurring revenue"""
        return self.monthly_fee * 12
    
    def get_usage_metrics(self):
        """Get comprehensive usage metrics for the company"""
        company_properties = [p for p in properties if p.company_id == self.id]
        company_tenants = [t for t in tenants if any(p.id == t.property_id for p in company_properties)]
        company_users = [u for u in users if u.company_id == self.id]
        
        total_units = sum(p.units for p in company_properties)
        occupied_units = sum(p.occupied_units for p in company_properties)
        total_rent = sum(t.rent_amount for t in company_tenants)
        
        return {
            'properties': len(company_properties),
            'total_units': total_units,
            'occupied_units': occupied_units,
            'vacancy_rate': round(((total_units - occupied_units) / total_units) * 100, 1) if total_units > 0 else 0,
            'users': len(company_users),
            'monthly_rent_collected': total_rent,
            'annual_rent_projected': total_rent * 12,
            'average_rent_per_unit': round(total_rent / occupied_units, 2) if occupied_units > 0 else 0
        }

class User:
    def __init__(self, id, name, email, company_id, role, property_access=None, permissions=None, 
                 password_hash=None, otp=None, is_first_login=True, last_login=None, status='active'):
        self.id = id
        self.name = name
        self.email = email
        self.company_id = company_id
        self.role = role  # company_admin, property_admin, property_manager, viewer
        self.property_access = property_access or []  # List of property IDs user can access
        self.permissions = permissions or self._get_default_permissions()  # Granular permissions
        self.password_hash = password_hash  # Hashed password
        self.otp = otp  # One-time password for first login
        self.is_first_login = is_first_login  # Flag to force password change
        self.last_login = last_login  # Track last login time
        self.status = status  # active, inactive, suspended
        
        # Initialize new attributes for existing users
        if not hasattr(self, 'password_hash'):
            self.password_hash = None
        if not hasattr(self, 'otp'):
            self.otp = None
        if not hasattr(self, 'is_first_login'):
            self.is_first_login = True
        if not hasattr(self, 'last_login'):
            self.last_login = None
        if not hasattr(self, 'status'):
            self.status = 'active'
    
    def _get_default_permissions(self):
        """Get default permissions based on role"""
        role_permissions = {
            'company_admin': [
                'view_all_properties', 'edit_all_properties', 'delete_properties',
                'view_all_tenants', 'edit_all_tenants', 'delete_tenants',
                'manage_users', 'view_financials', 'edit_financials',
                'view_maintenance', 'assign_maintenance', 'manage_billing'
            ],
            'property_admin': [
                'view_assigned_properties', 'edit_assigned_properties',
                'view_assigned_tenants', 'edit_assigned_tenants', 'add_tenants',
                'view_maintenance', 'assign_maintenance', 'view_financials'
            ],
            'property_manager': [
                'view_assigned_properties', 'view_assigned_tenants',
                'add_tenants', 'view_maintenance', 'create_maintenance_requests'
            ],
            'viewer': [
                'view_assigned_properties', 'view_assigned_tenants', 'view_maintenance'
            ]
        }
        return role_permissions.get(self.role, [])
    
    def generate_otp(self, length=8):
        """Generate a secure OTP for the user"""
        # Generate OTP with mix of letters and numbers for better security
        characters = string.ascii_letters + string.digits
        self.otp = ''.join(secrets.choice(characters) for _ in range(length))
        return self.otp
    
    def hash_password(self, password):
        """Hash a password using SHA-256 (in production, use bcrypt)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password):
        """Verify a password against the stored hash"""
        if self.password_hash:
            return self.password_hash == self.hash_password(password)
        return False
    
    def verify_otp(self, provided_otp):
        """Verify the provided OTP matches the stored OTP"""
        return self.otp and self.otp == provided_otp
    
    def set_password(self, new_password):
        """Set a new password and clear OTP"""
        self.password_hash = self.hash_password(new_password)
        self.otp = None  # Clear OTP after password is set
        self.is_first_login = False  # User has now set their password
        return True

# Utility functions for user management
def generate_secure_otp(length=8):
    """Generate a secure OTP"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def send_otp_email(user_email, user_name, otp, company_name="EstateCore"):
    """Send OTP to user via email (simulation)"""
    email_content = f"""
    Subject: Welcome to {company_name} - Your Login Credentials
    
    Dear {user_name},
    
    Welcome to {company_name}! Your account has been created successfully.
    
    Your temporary login credentials:
    Email: {user_email}
    One-Time Password: {otp}
    
    IMPORTANT: For security reasons, you will be required to change your password when you first log in.
    
    Steps to get started:
    1. Visit the login page
    2. Enter your email and the OTP above
    3. You'll be prompted to create a new secure password
    4. Start managing your properties!
    
    If you have any questions, please contact your administrator.
    
    Best regards,
    The {company_name} Team
    """
    
    print(f"EMAIL SENT TO {user_email}:")
    print(email_content)
    print("=" * 50)
    return True

class Property:
    def __init__(self, id, name, address, units, occupied_units, rent_amount, company_id, property_manager_id=None):
        self.id = id
        self.name = name
        self.address = address
        self.units = units
        self.occupied_units = occupied_units
        self.rent_amount = rent_amount
        self.company_id = company_id
        self.property_manager_id = property_manager_id

class Tenant:
    def __init__(self, id, name, email, property_id, unit_number, lease_end_date, rent_amount):
        self.id = id
        self.name = name
        self.email = email
        self.property_id = property_id
        self.unit_number = unit_number
        self.lease_end_date = lease_end_date
        self.rent_amount = rent_amount

# Sample companies for multi-tenant SaaS
companies = [
    Company(1, "Premier Property Management", "premium", "billing@premier-pm.com", "2024-01-15", "active"),
    Company(2, "GreenVille Estates", "premium", "admin@greenville-estates.com", "2024-03-20", "active"),
    Company(3, "Urban Living Co", "basic", "finance@urbanliving.co", "2024-06-10", "active"),
    Company(4, "Sunset Properties LLC", "basic", "accounts@sunsetproperties.com", "2024-08-05", "active")
]

# Initialize enhanced attributes for existing companies
for company in companies:
    if not hasattr(company, 'trial_ends_at'):
        company.trial_ends_at = None
    if not hasattr(company, 'custom_domain'):
        company.custom_domain = None
    if not hasattr(company, 'logo_url'):
        company.logo_url = None
    if not hasattr(company, 'phone'):
        company.phone = None
    if not hasattr(company, 'address'):
        company.address = None
    if not hasattr(company, 'payment_method'):
        company.payment_method = 'card'
    if not hasattr(company, 'auto_billing'):
        company.auto_billing = True
    if not hasattr(company, 'mrr_override'):
        company.mrr_override = None

# Sample users with company relationships and roles
users = [
    # System Super Admin
    User(0, "System Admin", "admin@estatecore.com", None, "super_admin"),
    
    # Premier Property Management (Company 1) - Premium
    User(1, "John Smith", "john@premier-pm.com", 1, "company_admin"),
    User(2, "Sarah Davis", "sarah@premier-pm.com", 1, "property_admin", [1, 2]),
    User(3, "Mike Johnson", "mike@premier-pm.com", 1, "property_manager", [1]),
    
    # GreenVille Estates (Company 2) - Premium
    User(4, "Emily Rodriguez", "emily@greenville-estates.com", 2, "company_admin"),
    User(5, "David Chen", "david@greenville-estates.com", 2, "property_admin", [3, 4]),
    
    # Urban Living Co (Company 3) - Basic
    User(6, "Lisa Anderson", "lisa@urbanliving.co", 3, "company_admin"),
    User(7, "James Wilson", "james@urbanliving.co", 3, "property_manager", [5]),
    
    # Sunset Properties LLC (Company 4) - Basic
    User(8, "Maria Garcia", "maria@sunsetproperties.com", 4, "company_admin")
]

# Initialize user status attributes for all existing users
for user in users:
    if not hasattr(user, 'status'):
        user.status = 'active'  # Default status for all users
    if not hasattr(user, 'created_at'):
        user.created_at = datetime.now().isoformat()
    if not hasattr(user, 'last_login'):
        user.last_login = None
    if not hasattr(user, 'password_hash'):
        user.password_hash = user.hash_password('password123')  # Default password for existing users
    if not hasattr(user, 'otp'):
        user.otp = None
    if not hasattr(user, 'is_first_login'):
        user.is_first_login = False  # Existing users don't need first login

# Sample properties with company ownership
properties = [
    Property(1, "Sunset Apartments", "123 Sunset Blvd", 24, 22, 2500, 1, 3),  # Premier Property Management
    Property(2, "Oak Street Complex", "456 Oak Street", 48, 45, 2200, 1, 2),  # Premier Property Management
    Property(3, "Pine Ridge", "789 Pine Avenue", 36, 33, 2800, 2, 5),        # GreenVille Estates
    Property(4, "Maple Heights", "321 Maple Drive", 18, 16, 3200, 2, 5),     # GreenVille Estates
    Property(5, "Cedar Point", "654 Cedar Lane", 30, 28, 2600, 3, 7),        # Urban Living Co
    Property(6, "Riverside Gardens", "987 River Road", 42, 38, 2400, 4, None), # Sunset Properties LLC
    Property(7, "Downtown Lofts", "555 Main Street", 28, 26, 3500, 4, None)   # Sunset Properties LLC
]

# Calculate future dates relative to today
from datetime import datetime, timedelta
today = datetime.now()

tenants = [
    # Tenants for Premier Property Management properties (1, 2)
    Tenant(1, "Sarah Johnson", "sarah.j@email.com", 1, "2A", (today + timedelta(days=18)).strftime("%Y-%m-%d"), 2500),
    Tenant(2, "Michael Chen", "michael.c@email.com", 2, "5B", (today + timedelta(days=25)).strftime("%Y-%m-%d"), 2200),
    Tenant(3, "David Rodriguez", "david.r@email.com", 1, "3B", (today + timedelta(days=65)).strftime("%Y-%m-%d"), 2500),
    Tenant(4, "Jennifer Liu", "jennifer.l@email.com", 2, "7A", (today + timedelta(days=120)).strftime("%Y-%m-%d"), 2200),
    
    # Tenants for GreenVille Estates properties (3, 4)
    Tenant(5, "Emma Williams", "emma.w@email.com", 3, "1C", (today + timedelta(days=42)).strftime("%Y-%m-%d"), 2800),
    Tenant(6, "James Wilson", "james.w@email.com", 4, "1A", (today + timedelta(days=180)).strftime("%Y-%m-%d"), 3200),
    Tenant(7, "Robert Taylor", "robert.t@email.com", 3, "4D", (today + timedelta(days=300)).strftime("%Y-%m-%d"), 2800),
    
    # Tenants for Urban Living Co properties (5)
    Tenant(8, "Maria Garcia", "maria.g@email.com", 5, "2C", (today + timedelta(days=240)).strftime("%Y-%m-%d"), 2600),
    
    # Tenants for Sunset Properties LLC properties (6, 7)
    Tenant(9, "Alex Thompson", "alex.t@email.com", 6, "1B", (today + timedelta(days=90)).strftime("%Y-%m-%d"), 2400),
    Tenant(10, "Rachel Brown", "rachel.b@email.com", 7, "3A", (today + timedelta(days=150)).strftime("%Y-%m-%d"), 3500)
]

# Global variable to simulate session (for demo purposes)
current_user_id = 0  # Default to System Admin - Super Admin for company management

# Authentication and Authorization functions
def get_current_user():
    """Simulate getting current user from session/token"""
    # For demo, return user based on current_user_id  
    # In production, this would decode JWT token or check session
    user = next((u for u in users if u.id == current_user_id), None)
    if user is None:
        # Fallback to John Smith (company_admin) by ID
        user = next((u for u in users if u.id == 1), None)
        if user is None:
            # Last resort fallback - find first company admin
            user = next((u for u in users if u.role == 'company_admin'), None)
    return user

def get_user_accessible_properties(user):
    """Get properties that a user can access based on their role and company"""
    if user.role == "company_admin":
        # Company admins can see all properties for their company
        return [p for p in properties if p.company_id == user.company_id]
    elif user.role in ["property_admin", "property_manager"]:
        # Property admins/managers can only see specific properties
        return [p for p in properties if p.id in user.property_access]
    else:
        return []

def get_user_accessible_tenants(user):
    """Get tenants that a user can access based on their property access"""
    accessible_property_ids = [p.id for p in get_user_accessible_properties(user)]
    return [t for t in tenants if t.property_id in accessible_property_ids]

def filter_data_by_user_access(user, data_type="dashboard"):
    """Filter dashboard data based on user's access level"""
    accessible_properties = get_user_accessible_properties(user)
    accessible_tenants = get_user_accessible_tenants(user)
    
    return {
        'properties': accessible_properties,
        'tenants': accessible_tenants,
        'property_ids': [p.id for p in accessible_properties]
    }

def calculate_dashboard_metrics(user=None):
    """Calculate real-time dashboard metrics from actual data filtered by user access"""
    if user is None:
        user = get_current_user()
    
    # Get data filtered by user's access level
    user_data = filter_data_by_user_access(user)
    user_properties = user_data['properties']
    user_tenants = user_data['tenants']
    
    total_properties = len(user_properties)
    total_units = sum(p.units for p in user_properties)
    occupied_units = sum(p.occupied_units for p in user_properties)
    available_properties = len([p for p in user_properties if p.occupied_units < p.units])
    total_tenants = len(user_tenants)
    total_users = total_tenants  # Assuming each tenant is a user
    
    # Calculate revenue from user's accessible tenants only
    total_revenue = sum(t.rent_amount for t in user_tenants)
    pending_revenue = total_revenue * 0.05  # Assume 5% pending
    
    occupancy_rate = round((occupied_units / total_units) * 100, 1) if total_units > 0 else 0
    
    # Get company info
    company = next((c for c in companies if c.id == user.company_id), None)
    company_name = company.name if company else "Unknown Company"
    
    return {
        'total_properties': total_properties,
        'available_properties': available_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'total_tenants': total_tenants,
        'total_users': total_users,
        'total_revenue': int(total_revenue),
        'pending_revenue': int(pending_revenue),
        'occupancy_rate': occupancy_rate,
        'company_name': company_name,
        'user_role': user.role,
        'accessible_property_count': len(user_properties)
    }

def calculate_lease_expirations(user=None):
    """Calculate lease expirations from real tenant data filtered by user access"""
    if user is None:
        user = get_current_user()
    
    current_date = datetime.now()
    expiring_leases = []
    
    # Get only tenants that the user can access
    user_data = filter_data_by_user_access(user)
    user_tenants = user_data['tenants']
    user_properties = user_data['properties']
    
    for tenant in user_tenants:
        lease_end = datetime.strptime(tenant.lease_end_date, "%Y-%m-%d")
        days_until_expiry = (lease_end - current_date).days
        
        if days_until_expiry <= 90:  # Leases expiring within 90 days
            property_name = next((p.name for p in user_properties if p.id == tenant.property_id), "Unknown Property")
            
            if days_until_expiry <= 30:
                priority = "high"
            elif days_until_expiry <= 60:
                priority = "medium"
            else:
                priority = "low"
            
            expiring_leases.append({
                'tenant_name': tenant.name,
                'property_name': property_name,
                'unit_number': tenant.unit_number,
                'lease_end_date': tenant.lease_end_date,
                'days_until_expiry': days_until_expiry,
                'priority': priority
            })
    
    high_priority_count = len([lease for lease in expiring_leases if lease['priority'] == 'high'])
    
    return {
        'total_count': len(expiring_leases),
        'high_priority_count': high_priority_count,
        'expiring_leases': sorted(expiring_leases, key=lambda x: x['days_until_expiry'])
    }

@app.route('/')
def index():
    return jsonify({
        'message': 'EstateCore API Server',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        dashboard_data = calculate_dashboard_metrics()
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/lease-expiration-check', methods=['GET'])
def get_lease_expirations():
    try:
        lease_data = calculate_lease_expirations()
        return jsonify({
            'success': True,
            'data': lease_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/properties', methods=['GET'])
def get_properties():
    try:
        user = get_current_user()
        user_data = filter_data_by_user_access(user)
        user_properties = user_data['properties']
        
        properties_data = []
        for p in user_properties:
            company = next((c for c in companies if c.id == p.company_id), None)
            manager = next((u for u in users if u.id == p.property_manager_id), None)
            
            properties_data.append({
                'id': p.id,
                'name': p.name,
                'address': p.address,
                'units': p.units,
                'occupied_units': p.occupied_units,
                'vacancy_rate': round(((p.units - p.occupied_units) / p.units) * 100, 1) if p.units > 0 else 0,
                'rent_amount': p.rent_amount,
                'company_id': p.company_id,
                'company_name': company.name if company else "Unknown",
                'property_manager': manager.name if manager else "Unassigned"
            })
        
        return jsonify({
            'success': True,
            'properties': properties_data,
            'total_count': len(properties_data),
            'user_role': user.role,
            'company_name': next((c.name for c in companies if c.id == user.company_id), "Unknown")
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/properties', methods=['POST'])
def create_property():
    """Create a new property and associate it with a company"""
    try:
        current_user = get_current_user()
        print(f"DEBUG: Current user ID: {current_user.id}, Role: {current_user.role}, Company: {current_user.company_id}")
        
        # Only company admins and super admins can create properties
        if current_user.role not in ['super_admin', 'company_admin']:
            return jsonify({'success': False, 'error': 'Unauthorized - Admin access required'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'address', 'units']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field.capitalize()} is required'}), 400
        
        # Determine company affiliation
        if current_user.role == 'super_admin':
            # Super admin must specify company_id
            company_id = data.get('company_id')
            if not company_id:
                return jsonify({'success': False, 'error': 'Company ID required for super admin'}), 400
        else:
            # Company admin creates properties for their own company
            company_id = current_user.company_id
            print(f"DEBUG: Using company_id {company_id} for company_admin")
        
        # Validate company exists
        company = next((c for c in companies if c.id == company_id), None)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        # Generate new property ID
        new_id = max([p.id for p in properties], default=0) + 1
        
        # Create new property
        new_property = Property(
            id=new_id,
            name=data['name'],
            address=data['address'],
            units=int(data['units']),
            occupied_units=int(data.get('occupied_units', 0)),
            rent_amount=float(data.get('rent', 0)),
            company_id=company_id,
            property_manager_id=current_user.id if current_user.role in ['property_admin', 'property_manager'] else None
        )
        
        # Add property to global list
        properties.append(new_property)
        
        # Update company status and recalculate monthly fee
        company_properties = [p for p in properties if p.company_id == company_id]
        total_units = sum(p.units for p in company_properties)
        old_monthly_fee = company.monthly_fee
        new_monthly_fee = company.calculate_monthly_fee(total_units)
        
        # Log the company status update
        print(f"Property '{new_property.name}' added to company '{company.name}'")
        print(f"Company units updated: {total_units} total units")
        print(f"Monthly fee updated: ${old_monthly_fee} -> ${new_monthly_fee}")
        
        # Prepare response with company status update info
        company_status_update = {
            'total_units_before': total_units - new_property.units,
            'total_units_after': total_units,
            'monthly_fee_before': old_monthly_fee,
            'monthly_fee_after': new_monthly_fee,
            'units_added': new_property.units
        }
        
        return jsonify({
            'success': True,
            'property': {
                'id': new_property.id,
                'name': new_property.name,
                'address': new_property.address,
                'units': new_property.units,
                'occupied_units': new_property.occupied_units,
                'rent_amount': new_property.rent_amount,
                'company_id': new_property.company_id,
                'company_name': company.name,
                'property_manager_id': new_property.property_manager_id
            },
            'company_status_update': company_status_update,
            'message': f'Property created successfully. Company monthly fee updated from ${old_monthly_fee} to ${new_monthly_fee}.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tenants', methods=['GET'])
def get_tenants():
    try:
        user = get_current_user()
        user_data = filter_data_by_user_access(user)
        user_tenants = user_data['tenants']
        user_properties = user_data['properties']
        
        tenants_data = []
        for t in user_tenants:
            property_obj = next((p for p in user_properties if p.id == t.property_id), None)
            property_name = property_obj.name if property_obj else "Unknown Property"
            
            tenants_data.append({
                'id': t.id,
                'name': t.name,
                'email': t.email,
                'property_id': t.property_id,
                'property_name': property_name,
                'unit_number': t.unit_number,
                'lease_end_date': t.lease_end_date,
                'rent_amount': t.rent_amount
            })
        
        return jsonify({
            'success': True,
            'tenants': tenants_data,
            'total_count': len(tenants_data),
            'user_role': user.role,
            'accessible_properties': len(user_properties)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Property Access Management Endpoints
@app.route('/api/companies/<int:company_id>/users', methods=['GET'])
def get_company_users(company_id):
    """Get all users in a company with their property access levels"""
    try:
        user = get_current_user()
        
        # Only company admins can manage users
        if user.role != "company_admin" or user.company_id != company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        company_users = [u for u in users if u.company_id == company_id]
        company_properties = [p for p in properties if p.company_id == company_id]
        
        users_data = []
        for u in company_users:
            # Get accessible properties for this user
            user_properties = get_user_accessible_properties(u)
            
            users_data.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'property_access': u.property_access,
                'permissions': u.permissions,
                'accessible_properties': [{
                    'id': p.id,
                    'name': p.name,
                    'address': p.address
                } for p in user_properties],
                'permission_level': 'full' if u.role == 'company_admin' else 'limited'
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'company_properties': [{
                'id': p.id,
                'name': p.name,
                'address': p.address,
                'units': p.units
            } for p in company_properties]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/users/<int:user_id>/property-access', methods=['PUT'])
def update_user_property_access(company_id, user_id):
    """Update property access for a user"""
    try:
        current_user = get_current_user()
        
        # Only company admins can manage property access
        if current_user.role != "company_admin" or current_user.company_id != company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        property_ids = data.get('property_ids', [])
        
        # Find the user to update
        target_user = next((u for u in users if u.id == user_id and u.company_id == company_id), None)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify all property IDs belong to the company
        company_property_ids = [p.id for p in properties if p.company_id == company_id]
        invalid_properties = [pid for pid in property_ids if pid not in company_property_ids]
        
        if invalid_properties:
            return jsonify({
                'success': False, 
                'error': f'Invalid property IDs: {invalid_properties}'
            }), 400
        
        # Update the user's property access
        target_user.property_access = property_ids
        
        return jsonify({
            'success': True,
            'message': f'Property access updated for {target_user.name}',
            'user_id': user_id,
            'property_access': property_ids
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/users', methods=['POST'])
def create_company_user(company_id):
    """Create a new user in the company"""
    try:
        current_user = get_current_user()
        
        # Only company admins can create users
        if current_user.role != "company_admin" or current_user.company_id != company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Generate new user ID
        new_user_id = max([u.id for u in users]) + 1
        
        new_user = User(
            id=new_user_id,
            name=data.get('name'),
            email=data.get('email'),
            company_id=company_id,
            role=data.get('role', 'property_manager'),
            property_access=data.get('property_access', [])
        )
        
        users.append(new_user)
        
        return jsonify({
            'success': True,
            'message': f'User {new_user.name} created successfully',
            'user': {
                'id': new_user.id,
                'name': new_user.name,
                'email': new_user.email,
                'role': new_user.role,
                'property_access': new_user.property_access
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/users/<int:user_id>/permissions', methods=['PUT'])
def update_user_permissions(company_id, user_id):
    """Update granular permissions for a user"""
    try:
        current_user = get_current_user()
        
        # Only company admins can manage permissions
        if current_user.role != "company_admin" or current_user.company_id != company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        new_permissions = data.get('permissions', [])
        
        # Find the user to update
        target_user = next((u for u in users if u.id == user_id and u.company_id == company_id), None)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Cannot modify company admin permissions (security)
        if target_user.role == 'company_admin' and target_user.id != current_user.id:
            return jsonify({'success': False, 'error': 'Cannot modify company admin permissions'}), 403
        
        # Validate permissions against available permissions
        available_permissions = [
            'view_all_properties', 'edit_all_properties', 'delete_properties',
            'view_assigned_properties', 'edit_assigned_properties',
            'view_all_tenants', 'edit_all_tenants', 'delete_tenants',
            'view_assigned_tenants', 'edit_assigned_tenants', 'add_tenants',
            'manage_users', 'view_financials', 'edit_financials',
            'view_maintenance', 'assign_maintenance', 'create_maintenance_requests',
            'manage_billing'
        ]
        
        invalid_permissions = [p for p in new_permissions if p not in available_permissions]
        if invalid_permissions:
            return jsonify({
                'success': False, 
                'error': f'Invalid permissions: {invalid_permissions}'
            }), 400
        
        # Update the user's permissions
        target_user.permissions = new_permissions
        
        return jsonify({
            'success': True,
            'message': f'Permissions updated for {target_user.name}',
            'user_id': user_id,
            'permissions': new_permissions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/permissions/available', methods=['GET'])
def get_available_permissions():
    """Get list of all available permissions with descriptions"""
    try:
        permissions_catalog = {
            'view_all_properties': {
                'name': 'View All Properties',
                'description': 'Can view all company properties',
                'category': 'properties'
            },
            'edit_all_properties': {
                'name': 'Edit All Properties', 
                'description': 'Can edit all company properties',
                'category': 'properties'
            },
            'delete_properties': {
                'name': 'Delete Properties',
                'description': 'Can delete properties',
                'category': 'properties'
            },
            'view_assigned_properties': {
                'name': 'View Assigned Properties',
                'description': 'Can view only assigned properties',
                'category': 'properties'
            },
            'edit_assigned_properties': {
                'name': 'Edit Assigned Properties',
                'description': 'Can edit only assigned properties',
                'category': 'properties'
            },
            'view_all_tenants': {
                'name': 'View All Tenants',
                'description': 'Can view all company tenants',
                'category': 'tenants'
            },
            'edit_all_tenants': {
                'name': 'Edit All Tenants',
                'description': 'Can edit all company tenants',
                'category': 'tenants'
            },
            'delete_tenants': {
                'name': 'Delete Tenants',
                'description': 'Can delete tenant records',
                'category': 'tenants'
            },
            'view_assigned_tenants': {
                'name': 'View Assigned Tenants',
                'description': 'Can view tenants in assigned properties',
                'category': 'tenants'
            },
            'edit_assigned_tenants': {
                'name': 'Edit Assigned Tenants',
                'description': 'Can edit tenants in assigned properties',
                'category': 'tenants'
            },
            'add_tenants': {
                'name': 'Add Tenants',
                'description': 'Can add new tenant records',
                'category': 'tenants'
            },
            'manage_users': {
                'name': 'Manage Users',
                'description': 'Can create, edit, and manage user accounts',
                'category': 'administration'
            },
            'view_financials': {
                'name': 'View Financial Reports',
                'description': 'Can view financial data and reports',
                'category': 'financials'
            },
            'edit_financials': {
                'name': 'Edit Financial Data',
                'description': 'Can edit and manage financial records',
                'category': 'financials'
            },
            'view_maintenance': {
                'name': 'View Maintenance',
                'description': 'Can view maintenance requests and status',
                'category': 'maintenance'
            },
            'assign_maintenance': {
                'name': 'Assign Maintenance',
                'description': 'Can assign and manage maintenance tasks',
                'category': 'maintenance'
            },
            'create_maintenance_requests': {
                'name': 'Create Maintenance Requests',
                'description': 'Can create new maintenance requests',
                'category': 'maintenance'
            },
            'manage_billing': {
                'name': 'Manage Billing',
                'description': 'Can manage company billing and subscriptions',
                'category': 'administration'
            }
        }
        
        return jsonify({
            'success': True,
            'permissions': permissions_catalog
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Company Management Endpoints
# Duplicate function removed - using list_all_companies instead

@app.route('/api/auth/user', methods=['GET'])
def get_current_user_info():
    try:
        user = get_current_user()
        company = next((c for c in companies if c.id == user.company_id), None)
        
        user_info = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'company_id': user.company_id,
            'company_name': company.name if company else "Unknown",
            'property_access': user.property_access,
            'accessible_property_count': len(get_user_accessible_properties(user))
        }
        
        return jsonify({
            'success': True,
            'user': user_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/permissions/check', methods=['POST'])
def check_permissions():
    """Check multiple permissions at once for optimization"""
    try:
        user = get_current_user()
        data = request.get_json()
        permissions_to_check = data.get('permissions', [])
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')
        
        result = {}
        
        for permission in permissions_to_check:
            has_permission = permission in user.permissions
            
            # Apply resource-level access control
            if has_permission and resource_type and resource_id:
                if resource_type == 'property' and user.role != 'company_admin':
                    has_permission = resource_id in user.property_access
                elif resource_type == 'tenant' and user.role != 'company_admin':
                    # Check if user has access to the property this tenant belongs to
                    tenant = next((t for t in tenants if t.id == resource_id), None)
                    if tenant:
                        has_permission = tenant.property_id in user.property_access
                    else:
                        has_permission = False
            
            result[permission] = has_permission
        
        return jsonify({
            'success': True,
            'permissions': result,
            'user_role': user.role
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Demo endpoint to switch users (for testing different access levels)
@app.route('/api/demo/switch-user/<int:user_id>', methods=['POST'])
def switch_demo_user(user_id):
    try:
        global current_user_id
        
        user = next((u for u in users if u.id == user_id), None)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update the global current user (for demo purposes)
        current_user_id = user_id
        
        company = next((c for c in companies if c.id == user.company_id), None)
        
        return jsonify({
            'success': True,
            'message': f'Switched to user: {user.name}',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'company_name': company.name if company else "Unknown",
                'accessible_properties': len(get_user_accessible_properties(user))
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Financial Analytics Endpoints
@app.route('/api/financial-analytics/dashboard', methods=['GET'])
def get_financial_dashboard():
    try:
        # Calculate financial metrics from property/tenant data
        total_income = sum(t.rent_amount for t in tenants)
        operating_expenses = total_income * 0.35  # Assume 35% expense ratio
        net_income = total_income - operating_expenses
        
        dashboard_data = {
            'period': {
                'start_date': '2024-09-01T00:00:00Z',
                'end_date': datetime.utcnow().isoformat(),
                'days': 30
            },
            'summary': {
                'total_income': int(total_income),
                'total_expenses': int(operating_expenses),
                'net_income': int(net_income),
                'net_margin': round(net_income / total_income, 3) if total_income > 0 else 0
            },
            'income_breakdown': {
                'rent_income': int(total_income * 0.95),
                'late_fees': int(total_income * 0.03),
                'other_income': int(total_income * 0.02)
            },
            'expense_breakdown': {
                'maintenance': int(operating_expenses * 0.35),
                'utilities': int(operating_expenses * 0.25),
                'insurance': int(operating_expenses * 0.20),
                'property_tax': int(operating_expenses * 0.20)
            },
            'monthly_trends': [
                {'month': '2024-07', 'income': int(total_income * 0.98), 'expenses': int(operating_expenses * 0.95), 'net_income': int(net_income * 1.02)},
                {'month': '2024-08', 'income': int(total_income * 1.02), 'expenses': int(operating_expenses * 1.05), 'net_income': int(net_income * 0.98)},
                {'month': '2024-09', 'income': int(total_income), 'expenses': int(operating_expenses), 'net_income': int(net_income)}
            ],
            'kpis': {
                'gross_rental_yield': 8.5,
                'net_operating_income': int(net_income),
                'cap_rate': 6.2,
                'cash_on_cash_return': 12.8,
                'expense_ratio': round(operating_expenses / total_income, 3) if total_income > 0 else 0,
                'rent_growth_rate': 3.2
            }
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Maintenance Endpoints
@app.route('/api/maintenance/requests', methods=['GET'])
def get_maintenance_requests():
    try:
        # Generate some realistic maintenance requests
        
        maintenance_types = ['Plumbing', 'HVAC', 'Electrical', 'Appliance', 'General Repair']
        priorities = ['low', 'medium', 'high', 'urgent']
        statuses = ['pending', 'in_progress', 'completed']
        
        requests = []
        for i in range(15):
            tenant = random.choice(tenants)
            property_obj = next((p for p in properties if p.id == tenant.property_id), properties[0])
            
            requests.append({
                'id': i + 1,
                'title': f'{random.choice(maintenance_types)} Issue',
                'description': f'Issue reported in unit {tenant.unit_number}',
                'property_name': property_obj.name,
                'unit_number': tenant.unit_number,
                'tenant_name': tenant.name,
                'priority': random.choice(priorities),
                'status': random.choice(statuses),
                'created_date': (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                'estimated_cost': random.randint(50, 500)
            })
        
        return jsonify({
            'success': True,
            'requests': requests,
            'total_count': len(requests)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Tenant Screening Endpoints
@app.route('/api/tenant-screening/dashboard', methods=['GET'])
def get_tenant_screening_dashboard():
    try:
        # Simulate screening data based on current tenants
        screening_data = {
            'overview': {
                'total_applications': len(tenants) + 15,  # Current tenants + some applications
                'pending_applications': 5,
                'in_progress_applications': 3,
                'approved_applications': len(tenants),
                'rejected_applications': 7,
                'requires_review': 2,
                'approval_rate': round(len(tenants) / (len(tenants) + 15), 3),
                'rejection_rate': round(7 / (len(tenants) + 15), 3)
            },
            'processing_metrics': {
                'average_processing_time_hours': 18,
                'fastest_processing_time_hours': 4,
                'slowest_processing_time_hours': 48,
                'applications_processed_today': 3
            },
            'recent_applications': [
                {
                    'application_id': f'app_{i+1:03d}',
                    'applicant_name': tenant.name,
                    'applicant_email': tenant.email,
                    'property_id': tenant.property_id,
                    'monthly_income': tenant.rent_amount * 3.5,  # Typical income requirement
                    'status': 'approved',
                    'submitted_at': (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                    'credit_summary': {
                        'credit_score': random.randint(650, 800),
                        'credit_grade': 'good' if random.randint(650, 800) > 700 else 'fair'
                    }
                }
                for i, tenant in enumerate(tenants[:5])
            ]
        }
        
        return jsonify({
            'success': True,
            'dashboard': screening_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/billing/analytics/subscriptions', methods=['GET'])
def billing_analytics():
    """Get billing and subscription analytics"""
    try:
        current_user = get_current_user()
        
        # Calculate billing analytics
        billing_data = {
            'subscription_analytics': {
                'total_companies': len(companies),
                'active_subscriptions': len([c for c in companies if c.status == 'active']),
                'total_mrr': sum(c.monthly_fee for c in companies if c.status == 'active'),
                'average_subscription_value': sum(c.monthly_fee for c in companies if c.status == 'active') / max(len([c for c in companies if c.status == 'active']), 1),
                'churn_rate': 0.05,
                'growth_rate': 0.12
            },
            'plan_distribution': {
                'basic': len([c for c in companies if c.subscription_plan == 'basic']),
                'pro': len([c for c in companies if c.subscription_plan == 'pro']),
                'enterprise': len([c for c in companies if c.subscription_plan == 'enterprise'])
            },
            'recent_invoices': [
                {
                    'invoice_id': f'inv_{i+1:04d}',
                    'company_name': company.name,
                    'amount': company.monthly_fee,
                    'status': 'paid' if i < 3 else 'pending',
                    'due_date': (datetime.utcnow() + timedelta(days=30-i)).isoformat(),
                    'plan': company.subscription_plan
                }
                for i, company in enumerate(companies[:5])
            ],
            'payment_analytics': {
                'total_revenue_ytd': sum(c.monthly_fee * 12 for c in companies if c.status == 'active'),
                'outstanding_invoices': 2,
                'payment_success_rate': 0.98
            }
        }
        
        return jsonify({
            'success': True,
            'analytics': billing_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/companies', methods=['GET'])
def list_all_companies():
    """Get all companies (super admin) or current company (company users)"""
    try:
        current_user = get_current_user()
        
        if current_user.role == 'super_admin':
            # Super admin can see all companies
            companies_data = []
            for company in companies:
                company_properties = [p for p in properties if p.company_id == company.id]
                company_users = [u for u in users if u.company_id == company.id]
                
                companies_data.append({
                    'id': company.id,
                    'name': company.name,
                    'subscription_plan': company.subscription_plan,
                    'billing_email': company.billing_email,
                    'status': company.status,
                    'monthly_fee': company.monthly_fee,
                    'created_at': company.created_at,
                    'property_count': len(company_properties),
                    'user_count': len(company_users),
                    'total_units': sum(p.units for p in company_properties)
                })
        else:
            # Regular users can only see their own company
            user_company = next((c for c in companies if c.id == current_user.company_id), None)
            if not user_company:
                return jsonify({'success': False, 'error': 'Company not found'}), 404
                
            company_properties = [p for p in properties if p.company_id == user_company.id]
            company_users = [u for u in users if u.company_id == user_company.id]
            
            companies_data = [{
                'id': user_company.id,
                'name': user_company.name,
                'subscription_plan': user_company.subscription_plan,
                'billing_email': user_company.billing_email,
                'status': user_company.status,
                'monthly_fee': user_company.monthly_fee,
                'created_at': user_company.created_at,
                'property_count': len(company_properties),
                'user_count': len(company_users),
                'total_units': sum(p.units for p in company_properties)
            }]
        
        return jsonify({
            'success': True,
            'companies': companies_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/companies', methods=['POST'])
def create_new_company():
    """Create a new company/organization"""
    try:
        current_user = get_current_user()
        
        # Only super admins can create companies
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized - Super admin required'}), 403
        
        data = request.get_json()
        
        # Generate new company ID
        new_id = max([c.id for c in companies], default=0) + 1
        
        new_company = Company(
            id=new_id,
            name=data.get('name', ''),
            subscription_plan=data.get('subscription_plan', 'basic'),
            billing_email=data.get('billing_email', ''),
            created_at=datetime.utcnow().isoformat(),
            status='active'
        )
        
        companies.append(new_company)
        
        return jsonify({
            'success': True,
            'company': {
                'id': new_company.id,
                'name': new_company.name,
                'subscription_plan': new_company.subscription_plan,
                'billing_email': new_company.billing_email,
                'status': new_company.status,
                'monthly_fee': new_company.monthly_fee,
                'created_at': new_company.created_at
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/companies/<int:company_id>', methods=['PUT'])
def update_company(company_id):
    """Update company information"""
    try:
        current_user = get_current_user()
        
        # Only super admins can update companies
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized - Super admin required'}), 403
        
        data = request.get_json()
        
        # Find the company to update
        company = next((c for c in companies if c.id == company_id), None)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        # Store old status to detect changes
        old_status = company.status
        user_status_changes = {'action': None, 'affected_users': [], 'count': 0}
        
        # Update company properties
        if 'name' in data:
            company.name = data['name']
        if 'billing_email' in data:
            company.billing_email = data['billing_email']
        if 'subscription_plan' in data:
            company.subscription_plan = data['subscription_plan']
        if 'status' in data:
            new_status = data['status']
            company.status = new_status
            
            # Handle user status changes based on company status
            if new_status != old_status:
                company_users = [u for u in users if u.company_id == company.id]
                
                if new_status == 'suspended':
                    # Deactivate all users when company is suspended
                    deactivated_users = []
                    for user in company_users:
                        if not hasattr(user, 'status'):
                            user.status = 'active'  # Set default if not exists
                        if user.status == 'active':
                            user.previous_status = user.status  # Store previous status for reactivation
                            user.status = 'inactive'
                            deactivated_users.append(user.name)
                    
                    user_status_changes = {
                        'action': 'deactivated',
                        'affected_users': deactivated_users,
                        'count': len(deactivated_users)
                    }
                    print(f"Company '{company.name}' suspended - Deactivated {len(deactivated_users)} users: {', '.join(deactivated_users)}")
                
                elif new_status == 'active' and old_status == 'suspended':
                    # Reactivate users when company becomes active again (only if they were active before)
                    reactivated_users = []
                    for user in company_users:
                        if hasattr(user, 'previous_status') and user.previous_status == 'active':
                            user.status = 'active'
                            delattr(user, 'previous_status')  # Clean up
                            reactivated_users.append(user.name)
                    
                    user_status_changes = {
                        'action': 'reactivated',
                        'affected_users': reactivated_users,
                        'count': len(reactivated_users)
                    }
                    print(f"Company '{company.name}' reactivated - Reactivated {len(reactivated_users)} users: {', '.join(reactivated_users)}")
                
                elif new_status == 'cancelled':
                    # Deactivate all users when company is cancelled
                    cancelled_users = []
                    for user in company_users:
                        if not hasattr(user, 'status'):
                            user.status = 'active'  # Set default if not exists
                        if user.status == 'active':
                            user.status = 'inactive'
                            cancelled_users.append(user.name)
                    
                    user_status_changes = {
                        'action': 'deactivated',
                        'affected_users': cancelled_users,
                        'count': len(cancelled_users)
                    }
                    print(f"Company '{company.name}' cancelled - Deactivated {len(cancelled_users)} users: {', '.join(cancelled_users)}")
        
        # Get updated company data
        company_properties = [p for p in properties if p.company_id == company.id]
        company_users = [u for u in users if u.company_id == company.id]
        
        response_data = {
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name,
                'subscription_plan': company.subscription_plan,
                'billing_email': company.billing_email,
                'status': company.status,
                'monthly_fee': company.monthly_fee,
                'created_at': company.created_at,
                'property_count': len(company_properties),
                'user_count': len(company_users),
                'total_units': sum(p.units for p in company_properties)
            }
        }
        
        # Include user status changes in response if any occurred
        if user_status_changes['action']:
            response_data['user_status_changes'] = user_status_changes
            response_data['message'] = f"Company updated successfully. {user_status_changes['count']} users {user_status_changes['action']}."
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Enhanced Company Management Endpoints

@app.route('/api/companies/<int:company_id>/metrics', methods=['GET'])
def get_company_metrics(company_id):
    """Get comprehensive company metrics and analytics"""
    try:
        current_user = get_current_user()
        
        # Super admin can access any company, company users can only access their own
        if current_user.role != 'super_admin' and current_user.company_id != company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        company = next((c for c in companies if c.id == company_id), None)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        # Get usage metrics
        usage_metrics = company.get_usage_metrics()
        
        # Get user activity metrics
        company_users = [u for u in users if u.company_id == company_id]
        active_users = [u for u in company_users if u.status == 'active']
        
        # Get billing metrics
        billing_metrics = {
            'monthly_fee': company.monthly_fee,
            'annual_revenue': company.annual_revenue,
            'subscription_plan': company.subscription_plan,
            'payment_method': getattr(company, 'payment_method', 'card'),
            'auto_billing': getattr(company, 'auto_billing', True),
            'mrr_override': getattr(company, 'mrr_override', None),
            'trial_expires_in_days': company.days_until_trial_expires
        }
        
        # Get growth metrics (simplified - would be from historical data in production)
        growth_metrics = {
            'properties_growth': '+15%',  # Mock data
            'units_growth': '+12%',
            'revenue_growth': '+18%',
            'user_growth': '+25%'
        }
        
        return jsonify({
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name,
                'status': company.status
            },
            'usage_metrics': usage_metrics,
            'user_metrics': {
                'total_users': len(company_users),
                'active_users': len(active_users),
                'inactive_users': len(company_users) - len(active_users)
            },
            'billing_metrics': billing_metrics,
            'growth_metrics': growth_metrics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/billing', methods=['PUT'])
def update_company_billing(company_id):
    """Update company billing settings"""
    try:
        current_user = get_current_user()
        
        # Only super admin can update billing
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized - Super admin required'}), 403
        
        company = next((c for c in companies if c.id == company_id), None)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        data = request.get_json()
        
        # Update billing settings
        if 'payment_method' in data:
            company.payment_method = data['payment_method']
        if 'auto_billing' in data:
            company.auto_billing = data['auto_billing']
        if 'mrr_override' in data:
            company.mrr_override = data['mrr_override']
        if 'subscription_plan' in data:
            old_plan = company.subscription_plan
            company.subscription_plan = data['subscription_plan']
            
            # Calculate new monthly fee
            company_properties = [p for p in properties if p.company_id == company_id]
            total_units = sum(p.units for p in company_properties)
            new_monthly_fee = company.calculate_monthly_fee(total_units)
            
            return jsonify({
                'success': True,
                'message': f'Billing updated successfully. Plan changed from {old_plan} to {company.subscription_plan}.',
                'billing_update': {
                    'old_plan': old_plan,
                    'new_plan': company.subscription_plan,
                    'old_monthly_fee': company.calculate_monthly_fee(total_units) if old_plan != company.subscription_plan else new_monthly_fee,
                    'new_monthly_fee': new_monthly_fee,
                    'payment_method': company.payment_method,
                    'auto_billing': company.auto_billing
                }
            })
        
        return jsonify({'success': True, 'message': 'Billing settings updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/trial', methods=['POST'])
def extend_company_trial(company_id):
    """Extend or start trial period for company"""
    try:
        current_user = get_current_user()
        
        # Only super admin can manage trials
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized - Super admin required'}), 403
        
        company = next((c for c in companies if c.id == company_id), None)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        data = request.get_json()
        trial_days = data.get('trial_days', 30)
        
        # Set trial end date
        from datetime import datetime, timedelta
        trial_end = datetime.utcnow() + timedelta(days=trial_days)
        company.trial_ends_at = trial_end.isoformat() + 'Z'
        company.status = 'trial'
        company.subscription_plan = 'trial'
        
        return jsonify({
            'success': True,
            'message': f'Trial extended for {trial_days} days',
            'trial_info': {
                'trial_ends_at': company.trial_ends_at,
                'days_remaining': trial_days,
                'status': company.status
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>/branding', methods=['PUT'])
def update_company_branding(company_id):
    """Update company branding (logo, custom domain, etc.)"""
    try:
        current_user = get_current_user()
        
        # Super admin or company admin can update branding
        if current_user.role not in ['super_admin', 'company_admin'] or \
           (current_user.role == 'company_admin' and current_user.company_id != company_id):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        company = next((c for c in companies if c.id == company_id), None)
        if not company:
            return jsonify({'success': False, 'error': 'Company not found'}), 404
        
        data = request.get_json()
        
        # Update branding settings
        if 'logo_url' in data:
            company.logo_url = data['logo_url']
        if 'custom_domain' in data:
            company.custom_domain = data['custom_domain']
        
        return jsonify({
            'success': True,
            'message': 'Branding updated successfully',
            'branding': {
                'logo_url': getattr(company, 'logo_url', None),
                'custom_domain': getattr(company, 'custom_domain', None)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/analytics', methods=['GET'])
def get_companies_analytics():
    """Get platform-wide company analytics (super admin only)"""
    try:
        current_user = get_current_user()
        
        # Only super admin can access platform analytics
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized - Super admin required'}), 403
        
        # Calculate platform metrics
        total_companies = len(companies)
        active_companies = len([c for c in companies if c.status == 'active'])
        trial_companies = len([c for c in companies if c.status == 'trial'])
        cancelled_companies = len([c for c in companies if c.status == 'cancelled'])
        
        total_mrr = sum(c.monthly_fee for c in companies if c.status in ['active', 'trial'])
        total_arr = total_mrr * 12
        
        # Plan distribution
        plan_distribution = {}
        for company in companies:
            plan = company.subscription_plan
            plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
        
        # Get top companies by revenue
        top_companies = sorted(
            [{'name': c.name, 'mrr': c.monthly_fee, 'plan': c.subscription_plan} 
             for c in companies if c.status in ['active', 'trial']], 
            key=lambda x: x['mrr'], 
            reverse=True
        )[:10]
        
        return jsonify({
            'success': True,
            'platform_metrics': {
                'total_companies': total_companies,
                'active_companies': active_companies,
                'trial_companies': trial_companies,
                'cancelled_companies': cancelled_companies,
                'churn_rate': round((cancelled_companies / total_companies) * 100, 1) if total_companies > 0 else 0
            },
            'revenue_metrics': {
                'total_mrr': round(total_mrr, 2),
                'total_arr': round(total_arr, 2),
                'average_mrr_per_company': round(total_mrr / max(active_companies, 1), 2)
            },
            'plan_distribution': plan_distribution,
            'top_companies': top_companies
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/current-user', methods=['GET'])
def debug_current_user():
    """Debug endpoint to check current user"""
    # Debug user lookup
    all_user_ids = [(u.id, type(u.id).__name__) for u in users]
    search_user = next((u for u in users if u.id == current_user_id), None)
    current_user = get_current_user()
    
    return jsonify({
        'current_user_id_variable': current_user_id,
        'current_user_id_type': type(current_user_id).__name__,
        'all_user_ids': all_user_ids,
        'search_result': search_user.name if search_user else None,
        'current_user': {
            'id': current_user.id,
            'name': current_user.name,
            'role': current_user.role,
            'company_id': getattr(current_user, 'company_id', None)
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'properties': len(properties),
            'tenants': len(tenants),
            'companies': len(companies),
            'api_endpoints': 12
        }
    })

# IoT Device and Sensor Data Models
class IoTDevice:
    def __init__(self, device_id, device_type, location, property_id, status='active'):
        self.device_id = device_id
        self.device_type = device_type
        self.location = location
        self.property_id = property_id
        self.status = status
        self.last_seen = datetime.now()

class SensorReading:
    def __init__(self, sensor_id, sensor_type, value, unit, location, property_id, quality='good'):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.value = value
        self.unit = unit
        self.location = location
        self.property_id = property_id
        self.quality = quality
        self.timestamp = datetime.now()
        self.alert_triggered = False

# Sample IoT devices
iot_devices = [
    IoTDevice("TEMP001", "temperature", "Unit 101 - Living Room", 1),
    IoTDevice("TEMP002", "temperature", "Unit 102 - Bedroom", 1),
    IoTDevice("HUM001", "humidity", "Unit 101 - Bathroom", 1),
    IoTDevice("OCC001", "occupancy", "Unit 101 - Main Area", 1),
    IoTDevice("AIR001", "air_quality", "Building A - Lobby", 1),
    IoTDevice("ENE001", "energy", "Building A - Electrical Panel", 1),
    IoTDevice("WAT001", "water", "Unit 101 - Kitchen", 1),
    IoTDevice("SEC001", "security", "Building A - Main Entrance", 1),
    IoTDevice("TEMP003", "temperature", "Unit 201 - Living Room", 2),
    IoTDevice("HUM002", "humidity", "Unit 201 - Bathroom", 2),
]

def generate_realistic_sensor_data():
    """Generate realistic sensor readings"""
    readings = []
    
    for device in iot_devices:
        if device.device_type == "temperature":
            value = round(random.uniform(68, 78), 1)  # 68-78°F
            alert = value > 76 or value < 70
        elif device.device_type == "humidity":
            value = round(random.uniform(30, 60), 1)  # 30-60%
            alert = value > 55 or value < 35
        elif device.device_type == "occupancy":
            value = random.choice([0, 1])  # 0 = vacant, 1 = occupied
            alert = False
        elif device.device_type == "air_quality":
            value = random.randint(25, 85)  # AQI scale
            alert = value > 75
        elif device.device_type == "energy":
            value = round(random.uniform(1.2, 4.8), 2)  # kW
            alert = value > 4.0
        elif device.device_type == "water":
            value = round(random.uniform(0.5, 3.2), 2)  # gallons/min
            alert = value > 3.0
        elif device.device_type == "security":
            value = random.choice([0, 1])  # 0 = secure, 1 = breach
            alert = value == 1
        else:
            value = round(random.uniform(50, 100), 1)
            alert = False
        
        units = {
            "temperature": "°F",
            "humidity": "%",
            "occupancy": "people",
            "air_quality": "AQI",
            "energy": "kW",
            "water": "gpm",
            "security": "status"
        }
        
        reading = SensorReading(
            sensor_id=device.device_id,
            sensor_type=device.device_type,
            value=value,
            unit=units.get(device.device_type, "units"),
            location=device.location,
            property_id=device.property_id,
            quality=random.choice(["excellent", "good", "fair"])
        )
        reading.alert_triggered = alert
        readings.append(reading)
    
    return readings

# IoT API Endpoints
@app.route('/api/iot/sensors', methods=['GET'])
def get_sensor_data():
    """Get current sensor readings for a property"""
    try:
        property_id = request.args.get('property_id', '1')
        
        # Generate real-time sensor data
        all_readings = generate_realistic_sensor_data()
        
        # Filter by property if specified
        if property_id != 'all':
            filtered_readings = [r for r in all_readings if str(r.property_id) == str(property_id)]
        else:
            filtered_readings = all_readings
        
        readings_data = []
        for reading in filtered_readings:
            readings_data.append({
                'sensor_id': reading.sensor_id,
                'sensor_type': reading.sensor_type,
                'value': reading.value,
                'unit': reading.unit,
                'location': reading.location,
                'property_id': reading.property_id,
                'quality': reading.quality,
                'timestamp': reading.timestamp.isoformat(),
                'alert_triggered': reading.alert_triggered
            })
        
        return jsonify({
            'success': True,
            'data': {
                'current_readings': readings_data,
                'total_sensors': len(readings_data),
                'alerts_count': len([r for r in readings_data if r['alert_triggered']])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/iot/analytics', methods=['POST'])
def get_iot_analytics():
    """Get IoT analytics and insights"""
    try:
        data = request.get_json()
        property_id = data.get('property_id', '1')
        hours_back = data.get('hours_back', 24)
        
        # Generate sample analytics data
        analytics = {
            'sensor_analysis': {
                'temperature': {
                    'average_temperature': 72.4,
                    'min_temperature': 68.1,
                    'max_temperature': 76.8,
                    'comfort_percentage': 85,
                    'trend': 'stable'
                },
                'humidity': {
                    'average_humidity': 45.2,
                    'mold_risk': 'low',
                    'trend': 'decreasing'
                },
                'occupancy': {
                    'occupancy_rate': 78,
                    'utilization_pattern': 'normal_business_hours',
                    'peak_times': ['9:00-11:00', '14:00-16:00']
                },
                'energy': {
                    'efficiency_score': 82,
                    'estimated_monthly_cost': 245.67,
                    'peak_usage_time': '18:00-20:00'
                },
                'air_quality': {
                    'average_aqi': 42,
                    'air_quality_category': 'good',
                    'trend': 'improving'
                }
            },
            'overall_insights': [
                "Temperature fluctuations in Unit 102 suggest possible HVAC efficiency issues",
                "Energy consumption 15% below average for similar properties - excellent efficiency",
                "Air quality consistently good across all monitored areas",
                "Occupancy patterns indicate optimal space utilization during business hours"
            ],
            'data_quality_score': 94
        }
        
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/realtime/pipeline/status', methods=['GET'])
def get_pipeline_status():
    """Get real-time processing pipeline status"""
    try:
        status = {
            'pipeline_status': 'running',
            'total_streams': len(iot_devices),
            'total_events_processed': random.randint(15000, 25000),
            'total_subscribers': random.randint(5, 15),
            'last_update': datetime.now().isoformat(),
            'processing_rate': f"{random.randint(100, 500)} events/sec"
        }
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/iot/devices', methods=['GET'])
def get_iot_devices():
    """Get all IoT devices for a property"""
    try:
        property_id = request.args.get('property_id')
        
        devices_data = []
        for device in iot_devices:
            if not property_id or str(device.property_id) == str(property_id):
                devices_data.append({
                    'device_id': device.device_id,
                    'device_type': device.device_type,
                    'location': device.location,
                    'property_id': device.property_id,
                    'status': device.status,
                    'last_seen': device.last_seen.isoformat()
                })
        
        return jsonify({
            'success': True,
            'devices': devices_data,
            'total_devices': len(devices_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Document Management and OCR/AI Extraction Models
class Document:
    def __init__(self, doc_id, name, category, file_size, property_id=None, tenant_id=None, uploaded_by=None):
        self.id = doc_id
        self.name = name
        self.category = category
        self.file_size = file_size
        self.property_id = property_id
        self.tenant_id = tenant_id
        self.uploaded_by = uploaded_by
        self.uploaded_by_name = uploaded_by
        self.created_at = datetime.now()
        self.description = f"Document uploaded on {self.created_at.strftime('%Y-%m-%d')}"
        self.download_url = f"/api/files/download/{doc_id}"
        self.ocr_extracted_text = ""
        self.ai_summary = ""
        self.ai_keywords = []

# Sample documents
documents = [
    Document(1, "lease_agreement_unit_101.pdf", "documents", 1024000, property_id=1, uploaded_by="John Smith"),
    Document(2, "maintenance_report_september.pdf", "documents", 512000, property_id=1, uploaded_by="Sarah Davis"),
    Document(3, "property_inspection_photos.zip", "images", 2048000, property_id=1, uploaded_by="Mike Johnson"),
    Document(4, "tenant_application_form.pdf", "documents", 256000, property_id=2, uploaded_by="Emily Rodriguez"),
    Document(5, "hvac_warranty_certificate.pdf", "documents", 128000, property_id=1, uploaded_by="John Smith"),
]

# Add OCR and AI content to sample documents
documents[0].ocr_extracted_text = "RESIDENTIAL LEASE AGREEMENT\nThis lease agreement is entered into between Premier Property Management and John Doe for Unit 101 at Sunset Apartments. Term: 12 months beginning January 1, 2024. Monthly rent: $1,200. Security deposit: $1,200."
documents[0].ai_summary = "12-month residential lease for Unit 101, $1,200/month rent, tenant John Doe"
documents[0].ai_keywords = ["lease", "rental agreement", "Unit 101", "12 months", "$1,200"]

documents[1].ocr_extracted_text = "MAINTENANCE REPORT - SEPTEMBER 2024\nProperty: Sunset Apartments\nCompleted Work Orders: 15\nPending Issues: 3\nKey Maintenance: HVAC filter replacement, plumbing repair in Unit 203, exterior painting touch-ups"
documents[1].ai_summary = "Monthly maintenance report showing 15 completed work orders and 3 pending issues"
documents[1].ai_keywords = ["maintenance", "work orders", "HVAC", "plumbing", "September 2024"]

def simulate_ocr_extraction(filename):
    """Simulate OCR text extraction from document"""
    file_type = filename.split('.')[-1].lower()
    
    if file_type == 'pdf':
        if 'lease' in filename.lower():
            return "LEASE AGREEMENT\nTenant Name: [Extracted Name]\nProperty Address: [Extracted Address]\nRent Amount: $[Amount]\nLease Term: [Term]"
        elif 'maintenance' in filename.lower():
            return "MAINTENANCE REPORT\nDate: [Date]\nProperty: [Property Name]\nIssues: [List of maintenance issues]\nStatus: [Completion status]"
        elif 'invoice' in filename.lower():
            return "INVOICE\nVendor: [Vendor Name]\nAmount: $[Amount]\nServices: [Description]\nDate: [Date]"
        else:
            return "Document content extracted successfully. Key information identified and processed."
    elif file_type in ['jpg', 'jpeg', 'png']:
        return "IMAGE ANALYSIS\nContent: Property photo\nLocation: [Detected location]\nObjects detected: [List of objects]\nCondition assessment: [Assessment]"
    else:
        return "Text content extracted from document file."

def simulate_ai_analysis(extracted_text, filename):
    """Simulate AI analysis of extracted text"""
    if 'lease' in filename.lower():
        return {
            'summary': 'Residential lease agreement with key terms and conditions',
            'keywords': ['lease', 'tenant', 'rent', 'property', 'agreement'],
            'document_type': 'Lease Agreement',
            'key_details': {
                'document_category': 'Legal Contract',
                'urgency': 'Standard',
                'requires_action': False
            }
        }
    elif 'maintenance' in filename.lower():
        return {
            'summary': 'Maintenance report documenting completed and pending work',
            'keywords': ['maintenance', 'repair', 'work order', 'property'],
            'document_type': 'Maintenance Report',
            'key_details': {
                'document_category': 'Operational Report',
                'urgency': 'Medium',
                'requires_action': True
            }
        }
    elif 'invoice' in filename.lower():
        return {
            'summary': 'Invoice for services or materials related to property management',
            'keywords': ['invoice', 'payment', 'vendor', 'services'],
            'document_type': 'Financial Document',
            'key_details': {
                'document_category': 'Financial',
                'urgency': 'High',
                'requires_action': True
            }
        }
    else:
        return {
            'summary': 'General document with relevant property management information',
            'keywords': ['document', 'information', 'property'],
            'document_type': 'General Document',
            'key_details': {
                'document_category': 'General',
                'urgency': 'Low',
                'requires_action': False
            }
        }

# Document Management API Endpoints
@app.route('/api/files/documents', methods=['GET'])
def get_documents():
    """Get documents with optional filtering"""
    try:
        property_id = request.args.get('property_id')
        tenant_id = request.args.get('tenant_id')
        category = request.args.get('category')
        
        filtered_docs = documents.copy()
        
        if property_id:
            filtered_docs = [d for d in filtered_docs if str(d.property_id) == str(property_id)]
        
        if tenant_id:
            filtered_docs = [d for d in filtered_docs if str(d.tenant_id) == str(tenant_id)]
        
        if category and category != 'all':
            filtered_docs = [d for d in filtered_docs if d.category == category]
        
        docs_data = []
        for doc in filtered_docs:
            docs_data.append({
                'id': doc.id,
                'name': doc.name,
                'category': doc.category,
                'file_size': doc.file_size,
                'property_id': doc.property_id,
                'tenant_id': doc.tenant_id,
                'uploaded_by_name': doc.uploaded_by_name,
                'created_at': doc.created_at.isoformat(),
                'description': doc.description,
                'download_url': doc.download_url,
                'has_ocr_text': bool(doc.ocr_extracted_text),
                'has_ai_analysis': bool(doc.ai_summary)
            })
        
        return jsonify(docs_data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/storage-stats', methods=['GET'])
def get_storage_stats():
    """Get storage statistics"""
    try:
        total_files = len(documents)
        total_size_mb = sum(doc.file_size for doc in documents) / (1024 * 1024)
        
        categories = {}
        for doc in documents:
            if doc.category not in categories:
                categories[doc.category] = {'files': 0, 'size_mb': 0}
            categories[doc.category]['files'] += 1
            categories[doc.category]['size_mb'] += doc.file_size / (1024 * 1024)
        
        return jsonify({
            'total_files': total_files,
            'total_size_mb': round(total_size_mb, 2),
            'categories': categories
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """Upload single file with OCR and AI processing"""
    try:
        # Simulate file upload (in real implementation, would save to storage)
        file_data = request.files.get('file')
        if not file_data:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        property_id = request.form.get('property_id')
        tenant_id = request.form.get('tenant_id')
        category = request.form.get('category', 'general')
        description = request.form.get('description', '')
        
        # Create new document record
        new_id = max([d.id for d in documents], default=0) + 1
        new_doc = Document(
            doc_id=new_id,
            name=file_data.filename,
            category=category,
            file_size=random.randint(100000, 2000000),  # Simulate file size
            property_id=int(property_id) if property_id else None,
            tenant_id=int(tenant_id) if tenant_id else None,
            uploaded_by="Current User"
        )
        new_doc.description = description
        
        # Simulate OCR extraction
        new_doc.ocr_extracted_text = simulate_ocr_extraction(file_data.filename)
        
        # Simulate AI analysis
        ai_analysis = simulate_ai_analysis(new_doc.ocr_extracted_text, file_data.filename)
        new_doc.ai_summary = ai_analysis['summary']
        new_doc.ai_keywords = ai_analysis['keywords']
        
        documents.append(new_doc)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'document': {
                'id': new_doc.id,
                'name': new_doc.name,
                'ocr_extracted': bool(new_doc.ocr_extracted_text),
                'ai_analyzed': bool(new_doc.ai_summary),
                'ai_analysis': ai_analysis
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/upload-multiple', methods=['POST'])
def upload_multiple_files():
    """Upload multiple files with batch OCR and AI processing"""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        property_id = request.form.get('property_id')
        tenant_id = request.form.get('tenant_id')
        category = request.form.get('category', 'general')
        
        results = []
        
        for file_data in files:
            try:
                # Create new document record
                new_id = max([d.id for d in documents], default=0) + 1
                new_doc = Document(
                    doc_id=new_id,
                    name=file_data.filename,
                    category=category,
                    file_size=random.randint(100000, 2000000),
                    property_id=int(property_id) if property_id else None,
                    tenant_id=int(tenant_id) if tenant_id else None,
                    uploaded_by="Current User"
                )
                
                # Simulate OCR extraction
                new_doc.ocr_extracted_text = simulate_ocr_extraction(file_data.filename)
                
                # Simulate AI analysis
                ai_analysis = simulate_ai_analysis(new_doc.ocr_extracted_text, file_data.filename)
                new_doc.ai_summary = ai_analysis['summary']
                new_doc.ai_keywords = ai_analysis['keywords']
                
                documents.append(new_doc)
                
                results.append({
                    'success': True,
                    'filename': file_data.filename,
                    'document_id': new_doc.id,
                    'ai_analysis': ai_analysis
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'filename': file_data.filename,
                    'error': str(e)
                })
        
        success_count = len([r for r in results if r['success']])
        
        return jsonify({
            'success': True,
            'message': f'{success_count}/{len(files)} files processed successfully',
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a document"""
    try:
        global documents
        documents = [d for d in documents if d.id != doc_id]
        return jsonify({'success': True, 'message': 'Document deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/documents/<int:doc_id>/ocr', methods=['GET'])
def get_document_ocr(doc_id):
    """Get OCR extracted text for a document"""
    try:
        doc = next((d for d in documents if d.id == doc_id), None)
        if not doc:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        return jsonify({
            'success': True,
            'document_id': doc_id,
            'extracted_text': doc.ocr_extracted_text,
            'ai_summary': doc.ai_summary,
            'ai_keywords': doc.ai_keywords,
            'processing_date': doc.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/documents/<int:doc_id>/analyze', methods=['POST'])
def analyze_document_ai(doc_id):
    """Run AI analysis on a document"""
    try:
        doc = next((d for d in documents if d.id == doc_id), None)
        if not doc:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        # Re-run AI analysis
        ai_analysis = simulate_ai_analysis(doc.ocr_extracted_text, doc.name)
        doc.ai_summary = ai_analysis['summary']
        doc.ai_keywords = ai_analysis['keywords']
        
        return jsonify({
            'success': True,
            'document_id': doc_id,
            'ai_analysis': ai_analysis,
            'analysis_date': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/create-archive', methods=['POST'])
def create_archive():
    """Create downloadable archive of selected documents"""
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        
        if not document_ids:
            return jsonify({'success': False, 'error': 'No documents selected'}), 400
        
        selected_docs = [d for d in documents if d.id in document_ids]
        
        if not selected_docs:
            return jsonify({'success': False, 'error': 'No valid documents found'}), 404
        
        # Simulate archive creation
        archive_name = f"documents_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        return jsonify({
            'success': True,
            'archive_name': archive_name,
            'download_url': f'/api/files/download/archive/{archive_name}',
            'included_documents': len(selected_docs),
            'total_size_mb': round(sum(d.file_size for d in selected_docs) / (1024 * 1024), 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/search', methods=['POST'])
def search_documents():
    """Search documents using OCR text and AI analysis"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400
        
        matching_docs = []
        
        for doc in documents:
            score = 0
            matches = []
            
            # Search in document name
            if query in doc.name.lower():
                score += 3
                matches.append('filename')
            
            # Search in OCR text
            if doc.ocr_extracted_text and query in doc.ocr_extracted_text.lower():
                score += 2
                matches.append('content')
            
            # Search in AI keywords
            if any(query in keyword.lower() for keyword in doc.ai_keywords):
                score += 2
                matches.append('keywords')
            
            # Search in AI summary
            if doc.ai_summary and query in doc.ai_summary.lower():
                score += 1
                matches.append('summary')
            
            if score > 0:
                matching_docs.append({
                    'document': {
                        'id': doc.id,
                        'name': doc.name,
                        'category': doc.category,
                        'created_at': doc.created_at.isoformat(),
                        'ai_summary': doc.ai_summary
                    },
                    'relevance_score': score,
                    'match_types': matches
                })
        
        # Sort by relevance score
        matching_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'query': query,
            'total_matches': len(matching_docs),
            'results': matching_docs[:20]  # Limit to top 20 results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Tenant Portal Models and Data
class TenantProfile:
    def __init__(self, tenant_id, user_id, property_id, unit_number, lease_start, lease_end, monthly_rent, security_deposit):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.property_id = property_id
        self.unit_number = unit_number
        self.lease_start = lease_start
        self.lease_end = lease_end
        self.monthly_rent = monthly_rent
        self.security_deposit = security_deposit
        self.phone = "+1 (555) 123-4567"
        self.emergency_contact = "Jane Doe - +1 (555) 987-6543"
        self.balance = 0.0
        self.next_payment_due = "2024-10-01"
        self.payment_method = "Auto-Pay (Bank Account)"
        self.auto_pay_enabled = True

class TenantNotification:
    def __init__(self, notif_id, tenant_id, title, message, notif_type, date, read=False):
        self.id = notif_id
        self.tenant_id = tenant_id
        self.title = title
        self.message = message
        self.type = notif_type
        self.date = date
        self.read = read

class TenantPayment:
    def __init__(self, payment_id, tenant_id, amount, payment_type, date, status):
        self.id = payment_id
        self.tenant_id = tenant_id
        self.amount = amount
        self.type = payment_type
        self.date = date
        self.status = status
        self.receipt_url = f"/api/tenant-portal/payments/{payment_id}/receipt"

class TenantMaintenanceRequest:
    def __init__(self, request_id, tenant_id, title, description, category, priority, date_submitted, status):
        self.id = request_id
        self.tenant_id = tenant_id
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.date_submitted = date_submitted
        self.status = status
        self.scheduled_date = None

# Sample tenant portal data
tenant_profiles = [
    TenantProfile(1, 6, 1, "101", "2024-01-01", "2024-12-31", 1200, 1200),
    TenantProfile(2, 7, 1, "102", "2024-02-01", "2025-01-31", 1300, 1300),
    TenantProfile(3, 8, 2, "201", "2024-03-01", "2025-02-28", 1100, 1100),
]

tenant_notifications = [
    TenantNotification(1, 1, "Rent Payment Confirmation", "Your rent payment of $1,200 has been processed successfully.", "payment", "2024-09-15", True),
    TenantNotification(2, 1, "Maintenance Update", "Your HVAC maintenance request has been scheduled for tomorrow.", "maintenance", "2024-09-20", False),
    TenantNotification(3, 1, "Building Announcement", "Pool area will be closed for maintenance this weekend.", "announcement", "2024-09-25", False),
    TenantNotification(4, 2, "Lease Renewal Notice", "Your lease is up for renewal. Please contact the office.", "announcement", "2024-09-22", False),
]

tenant_payments = [
    TenantPayment(1, 1, 1200, "Monthly Rent", "2024-09-01", "Paid"),
    TenantPayment(2, 1, 1200, "Monthly Rent", "2024-08-01", "Paid"),
    TenantPayment(3, 1, 1200, "Monthly Rent", "2024-07-01", "Paid"),
    TenantPayment(4, 2, 1300, "Monthly Rent", "2024-09-01", "Paid"),
    TenantPayment(5, 2, 1300, "Monthly Rent", "2024-08-01", "Paid"),
]

tenant_maintenance_requests = [
    TenantMaintenanceRequest(1, 1, "HVAC Not Working", "Air conditioning is not cooling properly in Unit 101", "HVAC", "High", "2024-09-20", "Scheduled"),
    TenantMaintenanceRequest(2, 1, "Leaky Faucet", "Kitchen faucet has a slow drip", "Plumbing", "Low", "2024-09-18", "In Progress"),
    TenantMaintenanceRequest(3, 2, "Broken Window", "Bedroom window lock is broken", "General", "Medium", "2024-09-22", "Pending"),
]

# Set scheduled dates for some requests
tenant_maintenance_requests[0].scheduled_date = "2024-09-28"

# Tenant Portal API Endpoints
@app.route('/api/tenant-portal/profile/<int:tenant_user_id>', methods=['GET'])
def get_tenant_profile(tenant_user_id):
    """Get tenant profile information"""
    try:
        # Find tenant profile by user ID
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        # Get user info
        user = next((u for u in users if u.id == tenant_user_id), None)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get property info
        property_info = next((p for p in properties if p.id == tenant_profile.property_id), None)
        
        # Get lease info
        lease_info = {
            'start_date': tenant_profile.lease_start,
            'end_date': tenant_profile.lease_end,
            'monthly_rent': tenant_profile.monthly_rent,
            'security_deposit': tenant_profile.security_deposit,
            'status': 'Active'
        }
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.name,
                'email': user.email
            },
            'tenant': {
                'phone': tenant_profile.phone,
                'emergency_contact': tenant_profile.emergency_contact,
                'unit_number': tenant_profile.unit_number
            },
            'property': {
                'id': property_info.id if property_info else None,
                'address': property_info.address if property_info else 'Property not found'
            },
            'lease': lease_info,
            'balance': tenant_profile.balance,
            'next_payment_due': tenant_profile.next_payment_due,
            'payment_method': tenant_profile.payment_method,
            'auto_pay_enabled': tenant_profile.auto_pay_enabled
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/dashboard/<int:tenant_user_id>', methods=['GET'])
def get_tenant_dashboard(tenant_user_id):
    """Get tenant dashboard summary data"""
    try:
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        # Count recent data
        recent_payments = len([p for p in tenant_payments if p.tenant_id == tenant_profile.tenant_id])
        pending_maintenance = len([r for r in tenant_maintenance_requests 
                                 if r.tenant_id == tenant_profile.tenant_id and r.status in ['Pending', 'In Progress']])
        unread_notifications = len([n for n in tenant_notifications 
                                  if n.tenant_id == tenant_profile.tenant_id and not n.read])
        
        return jsonify({
            'recent_payments': recent_payments,
            'pending_maintenance': pending_maintenance,
            'unread_notifications': unread_notifications,
            'unread_messages': 2  # Simulated
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/notifications/<int:tenant_user_id>', methods=['GET'])
def get_tenant_notifications(tenant_user_id):
    """Get tenant notifications"""
    try:
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        limit = int(request.args.get('limit', 10))
        
        tenant_notifs = [n for n in tenant_notifications if n.tenant_id == tenant_profile.tenant_id]
        tenant_notifs = tenant_notifs[:limit]
        
        notifications_data = []
        for notif in tenant_notifs:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.type,
                'date': notif.date,
                'read': notif.read
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        notification = next((n for n in tenant_notifications if n.id == notification_id), None)
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        notification.read = True
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/maintenance/<int:tenant_user_id>', methods=['GET'])
def get_tenant_maintenance_requests(tenant_user_id):
    """Get tenant maintenance requests"""
    try:
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        limit = int(request.args.get('limit', 10))
        
        tenant_requests = [r for r in tenant_maintenance_requests if r.tenant_id == tenant_profile.tenant_id]
        tenant_requests = tenant_requests[:limit]
        
        requests_data = []
        for req in tenant_requests:
            requests_data.append({
                'id': req.id,
                'title': req.title,
                'description': req.description,
                'category': req.category,
                'priority': req.priority,
                'date_submitted': req.date_submitted,
                'status': req.status,
                'scheduled_date': req.scheduled_date
            })
        
        return jsonify({
            'success': True,
            'maintenance_requests': requests_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/maintenance', methods=['POST'])
def create_maintenance_request():
    """Create new maintenance request"""
    try:
        data = request.get_json()
        tenant_user_id = data.get('tenant_user_id')
        
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        # Create new maintenance request
        new_id = max([r.id for r in tenant_maintenance_requests], default=0) + 1
        new_request = TenantMaintenanceRequest(
            request_id=new_id,
            tenant_id=tenant_profile.tenant_id,
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=data.get('category', 'General'),
            priority=data.get('priority', 'Medium'),
            date_submitted=datetime.now().strftime('%Y-%m-%d'),
            status='Pending'
        )
        
        tenant_maintenance_requests.append(new_request)
        
        return jsonify({
            'success': True,
            'message': 'Maintenance request submitted successfully',
            'request_id': new_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/payments/<int:tenant_user_id>', methods=['GET'])
def get_tenant_payments(tenant_user_id):
    """Get tenant payment history"""
    try:
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        limit = int(request.args.get('limit', 10))
        
        tenant_pay_history = [p for p in tenant_payments if p.tenant_id == tenant_profile.tenant_id]
        tenant_pay_history = tenant_pay_history[:limit]
        
        payments_data = []
        for payment in tenant_pay_history:
            payments_data.append({
                'id': payment.id,
                'amount': payment.amount,
                'type': payment.type,
                'date': payment.date,
                'status': payment.status,
                'receiptUrl': payment.receipt_url
            })
        
        return jsonify({
            'success': True,
            'payments': payments_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/payments', methods=['POST'])
def process_tenant_payment():
    """Process new payment from tenant"""
    try:
        data = request.get_json()
        tenant_user_id = data.get('tenant_user_id')
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'Credit Card')
        
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        # Create new payment record
        new_id = max([p.id for p in tenant_payments], default=0) + 1
        new_payment = TenantPayment(
            payment_id=new_id,
            tenant_id=tenant_profile.tenant_id,
            amount=amount,
            payment_type=f"Rent Payment ({payment_method})",
            date=datetime.now().strftime('%Y-%m-%d'),
            status='Processing'
        )
        
        tenant_payments.append(new_payment)
        
        # Update tenant balance
        tenant_profile.balance = max(0, tenant_profile.balance - amount)
        
        return jsonify({
            'success': True,
            'message': 'Payment submitted successfully',
            'payment_id': new_id,
            'new_balance': tenant_profile.balance
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tenant-portal/profile/<int:tenant_user_id>', methods=['PUT'])
def update_tenant_profile(tenant_user_id):
    """Update tenant profile information"""
    try:
        data = request.get_json()
        
        tenant_profile = next((tp for tp in tenant_profiles if tp.user_id == tenant_user_id), None)
        if not tenant_profile:
            return jsonify({'success': False, 'error': 'Tenant profile not found'}), 404
        
        # Update allowed fields
        if 'phone' in data:
            tenant_profile.phone = data['phone']
        if 'emergency_contact' in data:
            tenant_profile.emergency_contact = data['emergency_contact']
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Compliance and Regulatory Monitoring Models
class ComplianceRule:
    def __init__(self, rule_id, name, category, description, regulation_type, frequency, last_check, status):
        self.id = rule_id
        self.name = name
        self.category = category
        self.description = description
        self.regulation_type = regulation_type
        self.frequency = frequency
        self.last_check = last_check
        self.status = status
        self.next_check = self.calculate_next_check()
    
    def calculate_next_check(self):
        from datetime import datetime, timedelta
        last = datetime.strptime(self.last_check, '%Y-%m-%d')
        if self.frequency == 'monthly':
            return (last + timedelta(days=30)).strftime('%Y-%m-%d')
        elif self.frequency == 'quarterly':
            return (last + timedelta(days=90)).strftime('%Y-%m-%d')
        elif self.frequency == 'annual':
            return (last + timedelta(days=365)).strftime('%Y-%m-%d')
        else:
            return (last + timedelta(days=30)).strftime('%Y-%m-%d')

class ComplianceViolation:
    def __init__(self, violation_id, rule_id, property_id, severity, description, date_identified, status):
        self.id = violation_id
        self.rule_id = rule_id
        self.property_id = property_id
        self.severity = severity
        self.description = description
        self.date_identified = date_identified
        self.status = status
        self.remediation_plan = ""
        self.target_resolution_date = ""

class ComplianceReport:
    def __init__(self, report_id, report_type, property_id, generated_date, status):
        self.id = report_id
        self.report_type = report_type
        self.property_id = property_id
        self.generated_date = generated_date
        self.status = status
        self.file_url = f"/api/compliance/reports/{report_id}/download"

# Sample compliance data
compliance_rules = [
    ComplianceRule(1, "Fire Safety Inspection", "Safety", "Annual fire safety inspection required", "Local Fire Code", "annual", "2024-01-15", "compliant"),
    ComplianceRule(2, "Elevator Inspection", "Safety", "Monthly elevator safety inspection", "State Building Code", "monthly", "2024-09-01", "compliant"),
    ComplianceRule(3, "Lead Paint Disclosure", "Health", "Lead paint disclosure for pre-1978 buildings", "Federal HUD", "per_lease", "2024-08-15", "compliant"),
    ComplianceRule(4, "Emergency Exit Lighting", "Safety", "Quarterly emergency lighting system check", "Local Fire Code", "quarterly", "2024-07-01", "non_compliant"),
    ComplianceRule(5, "Rental License Renewal", "Legal", "Annual rental property license renewal", "Municipal Code", "annual", "2024-03-01", "pending"),
    ComplianceRule(6, "Fair Housing Training", "Legal", "Annual fair housing training for staff", "Federal Fair Housing Act", "annual", "2024-02-01", "compliant"),
    ComplianceRule(7, "Pool Safety Inspection", "Safety", "Monthly pool safety and chemical inspection", "Health Department", "monthly", "2024-09-15", "compliant"),
    ComplianceRule(8, "Smoke Detector Testing", "Safety", "Quarterly smoke detector functionality testing", "Local Fire Code", "quarterly", "2024-06-01", "compliant"),
]

compliance_violations = [
    ComplianceViolation(1, 4, 1, "Medium", "Emergency exit light in Unit 102 hallway is not functioning", "2024-09-20", "Open"),
    ComplianceViolation(2, 5, 1, "High", "Rental license renewal application not submitted", "2024-09-25", "Open"),
    ComplianceViolation(3, 8, 2, "Low", "Smoke detector in Unit 201 needs battery replacement", "2024-09-18", "Resolved"),
]

compliance_reports = [
    ComplianceReport(1, "Annual Safety Report", 1, "2024-09-01", "completed"),
    ComplianceReport(2, "Fair Housing Compliance Report", None, "2024-09-15", "completed"),
    ComplianceReport(3, "Monthly Safety Checklist", 1, "2024-09-25", "in_progress"),
    ComplianceReport(4, "Quarterly Building Inspection", 2, "2024-09-20", "completed"),
]

# Add remediation plans to violations
compliance_violations[0].remediation_plan = "Replace emergency exit light fixture and test functionality"
compliance_violations[0].target_resolution_date = "2024-10-05"

compliance_violations[1].remediation_plan = "Submit rental license renewal application with required documentation"
compliance_violations[1].target_resolution_date = "2024-10-01"

# Compliance Monitoring API Endpoints
@app.route('/api/compliance/dashboard', methods=['GET'])
def get_compliance_dashboard():
    """Get compliance monitoring dashboard data"""
    try:
        current_user = get_current_user()
        
        # Calculate compliance metrics
        total_rules = len(compliance_rules)
        compliant_rules = len([r for r in compliance_rules if r.status == 'compliant'])
        non_compliant_rules = len([r for r in compliance_rules if r.status == 'non_compliant'])
        pending_rules = len([r for r in compliance_rules if r.status == 'pending'])
        
        # Violations by severity
        open_violations = [v for v in compliance_violations if v.status == 'Open']
        high_severity = len([v for v in open_violations if v.severity == 'High'])
        medium_severity = len([v for v in open_violations if v.severity == 'Medium'])
        low_severity = len([v for v in open_violations if v.severity == 'Low'])
        
        # Reports status
        completed_reports = len([r for r in compliance_reports if r.status == 'completed'])
        in_progress_reports = len([r for r in compliance_reports if r.status == 'in_progress'])
        
        # Upcoming inspections (rules due within 30 days)
        from datetime import datetime, timedelta
        today = datetime.now()
        upcoming_deadline = today + timedelta(days=30)
        
        upcoming_inspections = []
        for rule in compliance_rules:
            next_check = datetime.strptime(rule.next_check, '%Y-%m-%d')
            if today <= next_check <= upcoming_deadline:
                upcoming_inspections.append({
                    'id': rule.id,
                    'name': rule.name,
                    'category': rule.category,
                    'next_check': rule.next_check,
                    'regulation_type': rule.regulation_type
                })
        
        return jsonify({
            'success': True,
            'compliance_score': round((compliant_rules / total_rules) * 100, 1),
            'summary': {
                'total_rules': total_rules,
                'compliant': compliant_rules,
                'non_compliant': non_compliant_rules,
                'pending': pending_rules
            },
            'violations': {
                'total_open': len(open_violations),
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity
            },
            'reports': {
                'completed': completed_reports,
                'in_progress': in_progress_reports,
                'total': len(compliance_reports)
            },
            'upcoming_inspections': upcoming_inspections[:5]  # Limit to 5 most urgent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compliance/rules', methods=['GET'])
def get_compliance_rules():
    """Get all compliance rules with filtering"""
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        
        filtered_rules = compliance_rules.copy()
        
        if category:
            filtered_rules = [r for r in filtered_rules if r.category.lower() == category.lower()]
        
        if status:
            filtered_rules = [r for r in filtered_rules if r.status == status]
        
        rules_data = []
        for rule in filtered_rules:
            rules_data.append({
                'id': rule.id,
                'name': rule.name,
                'category': rule.category,
                'description': rule.description,
                'regulation_type': rule.regulation_type,
                'frequency': rule.frequency,
                'last_check': rule.last_check,
                'next_check': rule.next_check,
                'status': rule.status
            })
        
        return jsonify({
            'success': True,
            'rules': rules_data,
            'total': len(rules_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compliance/violations', methods=['GET'])
def get_compliance_violations():
    """Get compliance violations"""
    try:
        status = request.args.get('status')
        severity = request.args.get('severity')
        property_id = request.args.get('property_id')
        
        filtered_violations = compliance_violations.copy()
        
        if status:
            filtered_violations = [v for v in filtered_violations if v.status == status]
        
        if severity:
            filtered_violations = [v for v in filtered_violations if v.severity == severity]
        
        if property_id:
            filtered_violations = [v for v in filtered_violations if str(v.property_id) == str(property_id)]
        
        violations_data = []
        for violation in filtered_violations:
            # Get rule details
            rule = next((r for r in compliance_rules if r.id == violation.rule_id), None)
            
            violations_data.append({
                'id': violation.id,
                'rule_name': rule.name if rule else 'Unknown Rule',
                'property_id': violation.property_id,
                'severity': violation.severity,
                'description': violation.description,
                'date_identified': violation.date_identified,
                'status': violation.status,
                'remediation_plan': violation.remediation_plan,
                'target_resolution_date': violation.target_resolution_date
            })
        
        return jsonify({
            'success': True,
            'violations': violations_data,
            'total': len(violations_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compliance/reports', methods=['GET'])
def get_compliance_reports():
    """Get compliance reports"""
    try:
        report_type = request.args.get('report_type')
        status = request.args.get('status')
        
        filtered_reports = compliance_reports.copy()
        
        if report_type:
            filtered_reports = [r for r in filtered_reports if report_type.lower() in r.report_type.lower()]
        
        if status:
            filtered_reports = [r for r in filtered_reports if r.status == status]
        
        reports_data = []
        for report in filtered_reports:
            reports_data.append({
                'id': report.id,
                'report_type': report.report_type,
                'property_id': report.property_id,
                'generated_date': report.generated_date,
                'status': report.status,
                'file_url': report.file_url
            })
        
        return jsonify({
            'success': True,
            'reports': reports_data,
            'total': len(reports_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compliance/reports', methods=['POST'])
def generate_compliance_report():
    """Generate new compliance report"""
    try:
        data = request.get_json()
        report_type = data.get('report_type')
        property_id = data.get('property_id')
        
        # Create new report
        new_id = max([r.id for r in compliance_reports], default=0) + 1
        new_report = ComplianceReport(
            report_id=new_id,
            report_type=report_type,
            property_id=property_id,
            generated_date=datetime.now().strftime('%Y-%m-%d'),
            status='in_progress'
        )
        
        compliance_reports.append(new_report)
        
        # Simulate report generation process
        import random
        processing_time = random.randint(5, 30)  # Simulate 5-30 second processing
        
        return jsonify({
            'success': True,
            'message': 'Report generation started',
            'report_id': new_id,
            'estimated_completion': f"{processing_time} seconds"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compliance/violations/<int:violation_id>/update', methods=['PUT'])
def update_violation_status(violation_id):
    """Update compliance violation status and remediation plan"""
    try:
        data = request.get_json()
        
        violation = next((v for v in compliance_violations if v.id == violation_id), None)
        if not violation:
            return jsonify({'success': False, 'error': 'Violation not found'}), 404
        
        # Update fields
        if 'status' in data:
            violation.status = data['status']
        if 'remediation_plan' in data:
            violation.remediation_plan = data['remediation_plan']
        if 'target_resolution_date' in data:
            violation.target_resolution_date = data['target_resolution_date']
        
        return jsonify({
            'success': True,
            'message': 'Violation updated successfully',
            'violation_id': violation_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compliance/rules/<int:rule_id>/check', methods=['POST'])
def perform_compliance_check(rule_id):
    """Perform compliance check for a specific rule"""
    try:
        rule = next((r for r in compliance_rules if r.id == rule_id), None)
        if not rule:
            return jsonify({'success': False, 'error': 'Rule not found'}), 404
        
        # Simulate compliance check
        import random
        check_passed = random.choice([True, True, True, False])  # 75% pass rate
        
        # Update rule status
        rule.last_check = datetime.now().strftime('%Y-%m-%d')
        rule.status = 'compliant' if check_passed else 'non_compliant'
        rule.next_check = rule.calculate_next_check()
        
        result = {
            'rule_id': rule_id,
            'check_date': rule.last_check,
            'status': rule.status,
            'next_check': rule.next_check,
            'passed': check_passed
        }
        
        # If check failed, create a violation
        if not check_passed:
            new_violation_id = max([v.id for v in compliance_violations], default=0) + 1
            new_violation = ComplianceViolation(
                violation_id=new_violation_id,
                rule_id=rule_id,
                property_id=1,  # Default property
                severity='Medium',
                description=f"Compliance check failed for {rule.name}",
                date_identified=rule.last_check,
                status='Open'
            )
            compliance_violations.append(new_violation)
            result['violation_created'] = new_violation_id
        
        return jsonify({
            'success': True,
            'message': f'Compliance check completed for {rule.name}',
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compliance/analytics', methods=['GET'])
def get_compliance_analytics():
    """Get compliance analytics and trends"""
    try:
        # Calculate compliance trends
        compliance_by_category = {}
        for rule in compliance_rules:
            if rule.category not in compliance_by_category:
                compliance_by_category[rule.category] = {'compliant': 0, 'non_compliant': 0, 'pending': 0}
            compliance_by_category[rule.category][rule.status] += 1
        
        # Violation trends
        violation_trends = {
            'High': len([v for v in compliance_violations if v.severity == 'High']),
            'Medium': len([v for v in compliance_violations if v.severity == 'Medium']),
            'Low': len([v for v in compliance_violations if v.severity == 'Low'])
        }
        
        # Regulatory compliance by type
        regulation_compliance = {}
        for rule in compliance_rules:
            if rule.regulation_type not in regulation_compliance:
                regulation_compliance[rule.regulation_type] = {'total': 0, 'compliant': 0}
            regulation_compliance[rule.regulation_type]['total'] += 1
            if rule.status == 'compliant':
                regulation_compliance[rule.regulation_type]['compliant'] += 1
        
        # Calculate percentages
        for reg_type in regulation_compliance:
            total = regulation_compliance[reg_type]['total']
            compliant = regulation_compliance[reg_type]['compliant']
            regulation_compliance[reg_type]['percentage'] = round((compliant / total) * 100, 1) if total > 0 else 0
        
        return jsonify({
            'success': True,
            'compliance_by_category': compliance_by_category,
            'violation_trends': violation_trends,
            'regulation_compliance': regulation_compliance,
            'total_compliance_score': round((len([r for r in compliance_rules if r.status == 'compliant']) / len(compliance_rules)) * 100, 1)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Email Configuration and Service
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import secrets

class EmailService:
    def __init__(self):
        # Email configuration - in production, use environment variables
        self.smtp_server = "smtp.gmail.com"  # Change to your SMTP server
        self.smtp_port = 587
        self.email = "noreply@estatecore.com"  # Change to your email
        self.password = "your_app_password"  # Use app password for Gmail
        self.enabled = False  # Set to True when email is configured
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email using configured SMTP settings"""
        if not self.enabled:
            # Simulate email sending for development
            print(f"📧 EMAIL SIMULATION:")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content: {text_content or html_content}")
            return True
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
                
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False

email_service = EmailService()

# User invitation system
class UserInvitation:
    def __init__(self, invite_id, email, invited_by, role, company_id, token, expires_at, status='pending'):
        self.id = invite_id
        self.email = email
        self.invited_by = invited_by
        self.role = role
        self.company_id = company_id
        self.token = token
        self.expires_at = expires_at
        self.status = status
        self.created_at = datetime.now()
        self.access_type = 'property_management'
        self.lpr_permissions = None

# Store pending invitations
pending_invitations = []

# Email Service Class
class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = "noreply@estatecore.com"
        self.password = "your_app_password"
        self.enabled = False  # Set to True when email is configured
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email using configured SMTP settings"""
        if not self.enabled:
            print(f"EMAIL SIMULATION:")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content: {html_content[:100]}...")
            return True
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email
            msg['To'] = to_email
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email sending error: {e}")
            return False

# Initialize email service
email_service = EmailService()

# Authentication Helper Functions

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Enhanced login endpoint with OTP support"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        otp = data.get('otp')  # For first-time login
        
        if not email or (not password and not otp):
            return jsonify({'success': False, 'error': 'Email and password/OTP required'}), 400
        
        # Find user by email
        user = next((u for u in users if u.email == email), None)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Check user status
        if user.status != 'active':
            return jsonify({'success': False, 'error': 'Account is not active'}), 401
        
        # Handle OTP login (first-time login)
        if otp and user.is_first_login:
            if not user.verify_otp(otp):
                return jsonify({'success': False, 'error': 'Invalid OTP'}), 401
            
            # OTP is valid, but user must change password
            return jsonify({
                'success': True,
                'requires_password_change': True,
                'temporary_token': f"temp_token_{user.id}",
                'message': 'OTP verified. Please set your new password.',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'company_id': user.company_id
                }
            })
        
        # Handle regular password login
        elif password:
            if user.is_first_login and user.otp:
                return jsonify({'success': False, 'error': 'Please use OTP for first login'}), 401
            
            if user.password_hash and user.verify_password(password):
                # Update last login
                user.last_login = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                        'role': user.role,
                        'company_id': user.company_id,
                        'is_first_login': user.is_first_login
                    },
                    'token': f"auth_token_{user.id}"
                })
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        return jsonify({'success': False, 'error': 'Invalid login method'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/set-password', methods=['POST'])
def set_first_password():
    """Set password for first-time login after OTP verification"""
    try:
        data = request.get_json()
        email = data.get('email')
        temp_token = data.get('temporary_token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([email, temp_token, new_password, confirm_password]):
            return jsonify({'success': False, 'error': 'All fields required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        # Find user by email
        user = next((u for u in users if u.email == email), None)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify temporary token (simplified check)
        expected_token = f"temp_token_{user.id}"
        if temp_token != expected_token:
            return jsonify({'success': False, 'error': 'Invalid temporary token'}), 401
        
        # Set new password
        user.set_password(new_password)
        user.last_login = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Password set successfully. You are now logged in.',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'company_id': user.company_id,
                'is_first_login': False
            },
            'token': f"auth_token_{user.id}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to user email"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email required'}), 400
        
        # Find user by email
        user = next((u for u in users if u.email == email), None)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if not user.is_first_login:
            return jsonify({'success': False, 'error': 'User has already completed first login'}), 400
        
        # Generate new OTP
        new_otp = user.generate_otp()
        
        # Get company name for email
        company = next((c for c in companies if c.id == user.company_id), None)
        company_name = company.name if company else "EstateCore"
        
        # Send new OTP email
        send_otp_email(user.email, user.name, new_otp, company_name)
        
        return jsonify({
            'success': True,
            'message': 'OTP resent successfully',
            'otp': new_otp  # In production, don't return OTP in response
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# User Management API Endpoints
@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users with filtering and company information"""
    try:
        current_user = get_current_user()
        
        # Filter users based on current user's role and company
        if current_user.role == 'super_admin':
            # Super admin can see all users
            filtered_users = users
        elif current_user.role == 'company_admin':
            # Company admin can see users in their company
            filtered_users = [u for u in users if u.company_id == current_user.company_id]
        else:
            # Other roles can only see themselves
            filtered_users = [u for u in users if u.id == current_user.id]
        
        users_data = []
        for user in filtered_users:
            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'company_id': user.company_id,
                'property_access': getattr(user, 'property_access', []),
                'permissions': getattr(user, 'permissions', {}),
                'phone': getattr(user, 'phone', ''),
                'status': getattr(user, 'status', 'active'),
                'last_login': getattr(user, 'last_login', None),
                'created_at': getattr(user, 'created_at', datetime.now().isoformat())
            }
            users_data.append(user_data)
        
        return jsonify({
            'success': True,
            'users': users_data,
            'total': len(users_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        current_user = get_current_user()
        
        # Only super_admin and company_admin can create users
        if current_user.role not in ['super_admin', 'company_admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('email') or not data.get('role'):
            return jsonify({'success': False, 'error': 'Name, email, and role are required'}), 400
        
        # Check if email already exists
        if any(u.email == data['email'] for u in users):
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Generate new user ID
        new_id = max([u.id for u in users], default=0) + 1
        
        # Check if OTP should be generated (default: yes)
        use_otp = data.get('use_otp', True)
        
        # Create new user
        new_user = User(
            id=new_id,
            name=data['name'],
            email=data['email'],
            company_id=int(data['company_id']) if data.get('company_id') else None,
            role=data['role'],
            property_access=data.get('property_access', []),
            permissions=data.get('permissions', {}),
            is_first_login=True,
            status='active'
        )
        
        # Add additional attributes
        new_user.phone = data.get('phone', '')
        new_user.last_login = None
        new_user.created_at = datetime.now().isoformat()
        
        # Generate OTP if requested
        otp_generated = None
        if use_otp:
            otp_generated = new_user.generate_otp()
        else:
            # If no OTP, user must be provided with a temporary password
            temp_password = data.get('temp_password')
            if temp_password:
                new_user.password_hash = new_user.hash_password(temp_password)
        
        users.append(new_user)
        
        # Get company name for email
        company = next((c for c in companies if c.id == new_user.company_id), None)
        company_name = company.name if company else "EstateCore"
        
        # Send appropriate email based on method chosen
        if use_otp and otp_generated:
            # Send OTP email
            send_otp_email(new_user.email, new_user.name, otp_generated, company_name)
            
            return jsonify({
                'success': True,
                'message': 'User created successfully with OTP',
                'user_id': new_id,
                'otp_sent': True,
                'otp': otp_generated,  # In production, don't return OTP in response
                'first_login_required': True,
                'setup_method': 'otp'
            })
        else:
            # Send traditional password setup email
            token = secrets.token_urlsafe(32)
            password_setup_link = f"http://localhost:3006/setup-password?token={token}"
            
            email_content = f"""
            <h2>Welcome to {company_name}!</h2>
            <p>Hello {new_user.name},</p>
            <p>An account has been created for you on the {company_name} property management platform.</p>
            <p>Please click the link below to set up your password and activate your account:</p>
            <p><a href="{password_setup_link}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Set Up Password</a></p>
            <p>Your role: {data['role']}</p>
            <p>If you have any questions, please contact your administrator.</p>
            <p>Best regards,<br>{company_name} Team</p>
            """
            
            print(f"PASSWORD SETUP EMAIL SENT TO {new_user.email}:")
            print(email_content)
            print("=" * 50)
            
            return jsonify({
                'success': True,
                'message': 'User created successfully with password setup link',
                'user_id': new_id,
                'password_setup_sent': True,
                'first_login_required': True,
                'setup_method': 'link'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    try:
        current_user = get_current_user()
        
        # Find user to update
        user_to_update = next((u for u in users if u.id == user_id), None)
        if not user_to_update:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check permissions
        if current_user.role not in ['super_admin', 'company_admin'] and current_user.id != user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if current_user.role == 'company_admin' and user_to_update.company_id != current_user.company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user_to_update.name = data['name']
        if 'email' in data and data['email'] != user_to_update.email:
            # Check if new email already exists
            if any(u.email == data['email'] and u.id != user_id for u in users):
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            user_to_update.email = data['email']
        if 'role' in data and current_user.role in ['super_admin', 'company_admin']:
            user_to_update.role = data['role']
        if 'company_id' in data and current_user.role == 'super_admin':
            user_to_update.company_id = int(data['company_id']) if data['company_id'] else None
        if 'property_access' in data:
            user_to_update.property_access = data['property_access']
        if 'phone' in data:
            user_to_update.phone = data['phone']
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    global users
    try:
        current_user = get_current_user()
        
        # Only super_admin and company_admin can delete users
        if current_user.role not in ['super_admin', 'company_admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Find user to delete
        user_to_delete = next((u for u in users if u.id == user_id), None)
        if not user_to_delete:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Company admin can only delete users in their company
        if current_user.role == 'company_admin' and user_to_delete.company_id != current_user.company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Cannot delete yourself
        if user_id == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        # Remove user from the list
        users = [u for u in users if u.id != user_id]
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/status', methods=['PATCH'])
def update_user_status(user_id):
    """Update user status (active/inactive)"""
    try:
        current_user = get_current_user()
        
        # Only super_admin and company_admin can update user status
        if current_user.role not in ['super_admin', 'company_admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        user_to_update = next((u for u in users if u.id == user_id), None)
        if not user_to_update:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if current_user.role == 'company_admin' and user_to_update.company_id != current_user.company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'inactive']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        user_to_update.status = new_status
        
        return jsonify({
            'success': True,
            'message': f'User status updated to {new_status}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def reset_user_password(user_id):
    """Send password reset email to user"""
    try:
        current_user = get_current_user()
        
        # Find user
        user_to_reset = next((u for u in users if u.id == user_id), None)
        if not user_to_reset:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check permissions
        if current_user.role not in ['super_admin', 'company_admin'] and current_user.id != user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if current_user.role == 'company_admin' and user_to_reset.company_id != current_user.company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        
        # Send password reset email
        email_content = f"""
        <h2>Password Reset Request</h2>
        <p>Hello {user_to_reset.name},</p>
        <p>A password reset has been requested for your EstateCore account.</p>
        <p>Please click the link below to reset your password:</p>
        <p><a href="{reset_link}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
        <p>This link will expire in 24 hours.</p>
        <p>If you did not request this reset, please contact your administrator.</p>
        <p>Best regards,<br>EstateCore Team</p>
        """
        
        success = email_service.send_email(
            user_to_reset.email,
            "EstateCore - Password Reset Request",
            email_content
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Password reset email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send password reset email'
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# User Invitation API Endpoints
@app.route('/api/invites/send-enhanced', methods=['POST'])
def send_enhanced_invitation():
    """Send enhanced user invitation with role and access configuration"""
    try:
        current_user = get_current_user()
        
        # Only super_admin and company_admin can send invitations
        if current_user.role not in ['super_admin', 'company_admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('access_type'):
            return jsonify({'success': False, 'error': 'Email and access type are required'}), 400
        
        email = data['email']
        
        # Check if user already exists
        if any(u.email == email for u in users):
            return jsonify({'success': False, 'error': 'User with this email already exists'}), 400
        
        # Check if invitation already pending
        if any(inv.email == email and inv.status == 'pending' for inv in pending_invitations):
            return jsonify({'success': False, 'error': 'Invitation already sent to this email'}), 400
        
        # Generate invitation
        invite_id = len(pending_invitations) + 1
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)  # 7 days to accept
        
        invitation = UserInvitation(
            invite_id=invite_id,
            email=email,
            invited_by=current_user.id,
            role=data.get('property_role', 'property_manager'),
            company_id=current_user.company_id,
            token=token,
            expires_at=expires_at
        )
        
        # Set additional invitation properties
        invitation.access_type = data['access_type']
        invitation.property_management_access = data.get('property_management_access', False)
        invitation.lpr_management_access = data.get('lpr_management_access', False)
        invitation.lpr_role = data.get('lpr_role')
        invitation.lpr_company_id = data.get('lpr_company_id')
        invitation.lpr_permissions = data.get('lpr_permissions')
        
        pending_invitations.append(invitation)
        
        # Create invitation acceptance link
        accept_link = f"http://localhost:3000/accept-invitation?token={token}"
        
        # Prepare email content based on access type
        access_description = ""
        if invitation.property_management_access and invitation.lpr_management_access:
            access_description = "both Property Management and LPR Management systems"
        elif invitation.property_management_access:
            access_description = "the Property Management system"
        elif invitation.lpr_management_access:
            access_description = "the LPR Management system"
        
        # Send invitation email
        email_content = f"""
        <h2>You're Invited to Join EstateCore!</h2>
        <p>Hello,</p>
        <p>You have been invited by {current_user.name} to join EstateCore property management platform.</p>
        <p><strong>Access Level:</strong> {access_description}</p>
        <p><strong>Role:</strong> {data.get('property_role', 'Property Manager')}</p>
        <p>Please click the link below to accept your invitation and set up your account:</p>
        <p><a href="{accept_link}" style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Accept Invitation</a></p>
        <p>This invitation will expire on {expires_at.strftime('%B %d, %Y')}.</p>
        <p>If you have any questions, please contact {current_user.name} at {current_user.email}.</p>
        <p>Best regards,<br>EstateCore Team</p>
        """
        
        success = email_service.send_email(
            email,
            "Invitation to Join EstateCore",
            email_content
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Invitation sent successfully to {email}',
                'invitation_id': invite_id,
                'expires_at': expires_at.isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send invitation email'
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invites/<token>/accept', methods=['POST'])
def accept_invitation(token):
    """Accept invitation and create user account"""
    try:
        # Find invitation by token
        invitation = next((inv for inv in pending_invitations if inv.token == token), None)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invalid invitation token'}), 404
        
        if invitation.status != 'pending':
            return jsonify({'success': False, 'error': 'Invitation already used'}), 400
        
        if datetime.now() > invitation.expires_at:
            return jsonify({'success': False, 'error': 'Invitation expired'}), 400
        
        data = request.get_json()
        
        # Validate required fields for account setup
        if not data.get('name') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Name and password are required'}), 400
        
        # Check if user already exists
        if any(u.email == invitation.email for u in users):
            return jsonify({'success': False, 'error': 'User account already exists'}), 400
        
        # Create new user
        new_id = max([u.id for u in users], default=0) + 1
        new_user = User(
            id=new_id,
            name=data['name'],
            email=invitation.email,
            company_id=invitation.company_id,
            role=invitation.role,
            property_access=[],
            permissions={}
        )
        
        # Set additional user properties
        new_user.phone = data.get('phone', '')
        new_user.status = 'active'
        new_user.last_login = None
        new_user.created_at = datetime.now().isoformat()
        new_user.password_hash = f"hashed_{data['password']}"  # In production, use proper password hashing
        
        users.append(new_user)
        
        # Mark invitation as accepted
        invitation.status = 'accepted'
        
        # Send welcome email
        email_content = f"""
        <h2>Welcome to EstateCore!</h2>
        <p>Hello {new_user.name},</p>
        <p>Your account has been successfully created on EstateCore.</p>
        <p>You can now log in using your email address: {new_user.email}</p>
        <p>If you need any assistance, please contact your administrator.</p>
        <p>Best regards,<br>EstateCore Team</p>
        """
        
        email_service.send_email(
            new_user.email,
            "Welcome to EstateCore - Account Created",
            email_content
        )
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user_id': new_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invites', methods=['GET'])
def get_invitations():
    """Get pending invitations"""
    try:
        current_user = get_current_user()
        
        if current_user.role not in ['super_admin', 'company_admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Filter invitations based on user role
        if current_user.role == 'super_admin':
            filtered_invitations = pending_invitations
        else:
            filtered_invitations = [inv for inv in pending_invitations if inv.company_id == current_user.company_id]
        
        invitations_data = []
        for inv in filtered_invitations:
            inviter = next((u for u in users if u.id == inv.invited_by), None)
            invitations_data.append({
                'id': inv.id,
                'email': inv.email,
                'role': inv.role,
                'company_id': inv.company_id,
                'status': inv.status,
                'invited_by': inviter.name if inviter else 'Unknown',
                'created_at': inv.created_at.isoformat(),
                'expires_at': inv.expires_at.isoformat(),
                'access_type': getattr(inv, 'access_type', 'property_management')
            })
        
        return jsonify({
            'success': True,
            'invitations': invitations_data,
            'total': len(invitations_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invites/<int:invitation_id>', methods=['DELETE'])
def cancel_invitation(invitation_id):
    """Cancel a pending invitation"""
    global pending_invitations
    try:
        current_user = get_current_user()
        
        if current_user.role not in ['super_admin', 'company_admin']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        invitation = next((inv for inv in pending_invitations if inv.id == invitation_id), None)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation not found'}), 404
        
        if current_user.role == 'company_admin' and invitation.company_id != current_user.company_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Remove invitation
        pending_invitations = [inv for inv in pending_invitations if inv.id != invitation_id]
        
        return jsonify({
            'success': True,
            'message': 'Invitation cancelled successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Properties and Units API Endpoints
@app.route('/api/properties', methods=['GET'])
def list_properties():
    """Get properties with optional company filtering"""
    try:
        company_id = request.args.get('company_id')
        
        # Create properties data based on companies and tenants
        all_properties = []
        
        for company in companies:
            if company_id and str(company.id) != str(company_id):
                continue
                
            # Create properties for this company based on tenant data
            company_properties = {}
            for tenant in tenants:
                if hasattr(tenant, 'property_id') and hasattr(tenant, 'property_name'):
                    prop_id = tenant.property_id
                    if prop_id not in company_properties:
                        company_properties[prop_id] = {
                            'id': prop_id,
                            'name': tenant.property_name,
                            'company_id': company.id,
                            'company_name': company.name,
                            'address': f"{tenant.property_name} Address",
                            'units': 0,
                            'occupied_units': 0,
                            'unit_numbers': []
                        }
                    company_properties[prop_id]['units'] += 1
                    company_properties[prop_id]['occupied_units'] += 1
                    if hasattr(tenant, 'unit_number'):
                        company_properties[prop_id]['unit_numbers'].append(tenant.unit_number)
            
            all_properties.extend(list(company_properties.values()))
        
        # If no properties from tenants, create default ones
        if not all_properties and not company_id:
            all_properties = [
                {
                    'id': 1,
                    'name': 'Sunset Apartments',
                    'company_id': 1,
                    'company_name': 'Premier Property Management',
                    'address': '123 Sunset Blvd',
                    'units': 24,
                    'occupied_units': 22,
                    'unit_numbers': ['1A', '1B', '2A', '2B', '3A', '3B']
                },
                {
                    'id': 2,
                    'name': 'Oak Street Complex',
                    'company_id': 1,
                    'company_name': 'Premier Property Management',
                    'address': '456 Oak Street',
                    'units': 48,
                    'occupied_units': 45,
                    'unit_numbers': ['1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B', '5A', '5B']
                }
            ]
        
        return jsonify({
            'success': True,
            'properties': all_properties,
            'total_count': len(all_properties)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>/units', methods=['GET'])
def get_property_units(property_id):
    """Get available units for a specific property"""
    try:
        # Find property
        properties_response = list_properties()
        properties_data = properties_response.get_json()
        
        if not properties_data.get('success'):
            return jsonify({'success': False, 'error': 'Failed to load properties'}), 500
        
        property_info = next((p for p in properties_data['properties'] if p['id'] == property_id), None)
        if not property_info:
            return jsonify({'success': False, 'error': 'Property not found'}), 404
        
        # Get occupied units from tenants
        occupied_units = set()
        for tenant in tenants:
            if hasattr(tenant, 'property_id') and hasattr(tenant, 'unit_number') and tenant.property_id == property_id:
                occupied_units.add(tenant.unit_number)
        
        # Generate available units
        available_units = []
        occupied_units_list = []
        
        # Use unit_numbers from property if available, otherwise generate
        if 'unit_numbers' in property_info and property_info['unit_numbers']:
            all_units = property_info['unit_numbers']
        else:
            # Generate units like 1A, 1B, 2A, 2B, etc.
            all_units = []
            floors = max(4, property_info.get('units', 24) // 6)
            for floor in range(1, floors + 1):
                for unit_suffix in ['A', 'B', 'C', 'D', 'E', 'F']:
                    all_units.append(f"{floor}{unit_suffix}")
                    if len(all_units) >= property_info.get('units', 24):
                        break
                if len(all_units) >= property_info.get('units', 24):
                    break
        
        for unit in all_units:
            unit_data = {
                'unit_number': unit,
                'property_id': property_id,
                'property_name': property_info['name'],
                'is_occupied': unit in occupied_units
            }
            
            if unit in occupied_units:
                occupied_units_list.append(unit_data)
            else:
                available_units.append(unit_data)
        
        return jsonify({
            'success': True,
            'property_id': property_id,
            'property_name': property_info['name'],
            'available_units': available_units,
            'occupied_units': occupied_units_list,
            'total_units': len(all_units),
            'available_count': len(available_units),
            'occupied_count': len(occupied_units_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/units', methods=['GET'])
def get_all_units():
    """Get all units across all properties"""
    try:
        company_id = request.args.get('company_id')
        property_id = request.args.get('property_id')
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        all_units = []
        
        # Get properties
        properties_response = list_properties()
        properties_data = properties_response.get_json()
        
        if not properties_data.get('success'):
            return jsonify({'success': False, 'error': 'Failed to load properties'}), 500
        
        properties = properties_data['properties']
        
        # Filter by company if specified
        if company_id:
            properties = [p for p in properties if str(p['company_id']) == str(company_id)]
        
        # Filter by property if specified
        if property_id:
            properties = [p for p in properties if str(p['id']) == str(property_id)]
        
        for prop in properties:
            # Get units for this property
            units_response = get_property_units(prop['id'])
            units_data = units_response.get_json()
            
            if units_data.get('success'):
                if available_only:
                    all_units.extend(units_data['available_units'])
                else:
                    all_units.extend(units_data['available_units'])
                    all_units.extend(units_data['occupied_units'])
        
        return jsonify({
            'success': True,
            'units': all_units,
            'total_count': len(all_units)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Email Configuration Testing
@app.route('/api/email/test', methods=['POST'])
def test_email_configuration():
    """Test email configuration"""
    try:
        current_user = get_current_user()
        
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        test_email = data.get('email', current_user.email)
        
        # Send test email
        email_content = """
        <h2>EstateCore Email Test</h2>
        <p>This is a test email to verify your EstateCore email configuration.</p>
        <p>If you received this email, your email system is working correctly!</p>
        <p>Timestamp: """ + datetime.now().isoformat() + """</p>
        <p>Best regards,<br>EstateCore System</p>
        """
        
        success = email_service.send_email(
            test_email,
            "EstateCore - Email Configuration Test",
            email_content
        )
        
        return jsonify({
            'success': success,
            'message': 'Test email sent successfully' if success else 'Failed to send test email',
            'email_enabled': email_service.enabled,
            'test_email': test_email
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/email/config', methods=['GET'])
def get_email_config():
    """Get email configuration status"""
    try:
        current_user = get_current_user()
        
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        return jsonify({
            'success': True,
            'config': {
                'enabled': email_service.enabled,
                'smtp_server': email_service.smtp_server if email_service.enabled else 'Not configured',
                'smtp_port': email_service.smtp_port if email_service.enabled else 'Not configured',
                'from_email': email_service.email if email_service.enabled else 'Not configured'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/email/config', methods=['PUT'])
def update_email_config():
    """Update email configuration"""
    try:
        current_user = get_current_user()
        
        if current_user.role != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update email service configuration
        if 'smtp_server' in data:
            email_service.smtp_server = data['smtp_server']
        if 'smtp_port' in data:
            email_service.smtp_port = int(data['smtp_port'])
        if 'email' in data:
            email_service.email = data['email']
        if 'password' in data:
            email_service.password = data['password']
        if 'enabled' in data:
            email_service.enabled = bool(data['enabled'])
        
        return jsonify({
            'success': True,
            'message': 'Email configuration updated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting EstateCore Development Server on port {port}...")
    print(f"Dashboard will be available at http://localhost:{port}/api/dashboard")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )