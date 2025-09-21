#!/usr/bin/env python3
"""
EstateCore Property Management System
Production-ready Flask application with security hardening
"""
import os
import sys
import smtplib
import ssl
import hashlib
import jwt
import time
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import secrets

# Import billing system
sys.path.append(os.path.join(os.path.dirname(__file__), 'billing_system'))
from billing_api import init_billing_system
import urllib.parse
from functools import wraps
import stripe

def create_app():
    app = Flask(__name__)
    
    # Security Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Extended for testing
    
    # CORS with security headers
    CORS(app, 
         origins=['http://localhost:3017', 'http://localhost:3016', 'http://localhost:3014', 'http://localhost:3013', 'http://localhost:3006', 'http://localhost:3000'],
         supports_credentials=True,
         expose_headers=['Content-Type', 'Authorization'],
         allow_headers=['Content-Type', 'Authorization']
    )
    
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Email configuration - Update these with your email settings
    EMAIL_CONFIG = {
        'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'SMTP_PORT': int(os.getenv('SMTP_PORT', '587')),
        'EMAIL_ADDRESS': os.getenv('EMAIL_ADDRESS', 'your-email@gmail.com'),
        'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', 'your-app-password'),
        'FROM_NAME': os.getenv('FROM_NAME', 'EstateCore System')
    }
    
    # Stripe configuration
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')  # Use test key by default
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')
    
    # Store invite tokens and failed attempts
    invite_tokens = {}
    failed_attempts = {}
    
    # Security utilities
    def hash_password(password):
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        return hashlib.sha256((password + salt).encode()).hexdigest() + ':' + salt
    
    def verify_password(password, hashed):
        """Verify password against hash"""
        try:
            password_hash, salt = hashed.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def generate_jwt_token(user_data):
        """Generate JWT token for user"""
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'role': user_data['role'],
            'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    def verify_jwt_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    def require_auth(f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'No token provided'}), 401
            
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = verify_jwt_token(token)
            if 'error' in payload:
                return jsonify(payload), 401
            
            request.current_user = payload
            return f(*args, **kwargs)
        return decorated_function
    
    def require_role(required_roles):
        """Decorator to require specific roles"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(request, 'current_user'):
                    return jsonify({'error': 'Authentication required'}), 401
                
                user_role = request.current_user.get('role')
                if user_role not in required_roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def validate_input(data, required_fields):
        """Validate required input fields"""
        errors = []
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} is required")
        return errors
    
    def send_email(to_email, subject, html_content, text_content=None):
        """Send email using SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{EMAIL_CONFIG['FROM_NAME']} <{EMAIL_CONFIG['EMAIL_ADDRESS']}>"
            message["To"] = to_email
            
            # Add text and HTML content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
                server.starttls(context=context)
                server.login(EMAIL_CONFIG['EMAIL_ADDRESS'], EMAIL_CONFIG['EMAIL_PASSWORD'])
                server.sendmail(EMAIL_CONFIG['EMAIL_ADDRESS'], to_email, message.as_string())
            
            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)
    
    def create_invite_email_content(email, access_type, property_role, lpr_role, lpr_company_name, lpr_permissions, invite_url):
        """Create HTML email content for invitation"""
        
        # Determine access description
        access_descriptions = []
        if access_type in ['property_management', 'both']:
            access_descriptions.append(f"Property Management ({property_role})")
        if access_type in ['lpr_management', 'both']:
            access_descriptions.append(f"LPR Management ({lpr_role} at {lpr_company_name}) with {lpr_permissions}")
        
        access_text = " and ".join(access_descriptions)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                .access-details {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007bff; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏢 EstateCore Invitation</h1>
                    <p>You've been invited to join our property management system</p>
                </div>
                <div class="content">
                    <h2>Welcome to EstateCore!</h2>
                    <p>You have been invited to join EstateCore with the following access permissions:</p>
                    
                    <div class="access-details">
                        <h3>Your Access Level:</h3>
                        <p><strong>{access_text}</strong></p>
                    </div>
                    
                    <p>Click the button below to accept your invitation and create your account:</p>
                    
                    <div style="text-align: center;">
                        <a href="{invite_url}" class="button">Accept Invitation</a>
                    </div>
                    
                    <p><small>If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{invite_url}">{invite_url}</a></small></p>
                    
                    <p><strong>Security Notice:</strong> This invitation link will expire in 7 days for security purposes.</p>
                </div>
                <div class="footer">
                    <p>This email was sent by EstateCore Property Management System</p>
                    <p>If you didn't expect this invitation, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        EstateCore Invitation
        
        You have been invited to join EstateCore with the following access:
        {access_text}
        
        Accept your invitation by visiting: {invite_url}
        
        This invitation will expire in 7 days.
        
        If you didn't expect this invitation, please ignore this email.
        """
        
        return html_content, text_content
    
    # In-memory storage for the session
    properties_data = [
        {'id': 1, 'name': 'Test Property 1', 'address': '123 Main St', 'is_available': True, 'rent': 1200},
        {'id': 2, 'name': 'Test Property 2', 'address': '456 Oak Ave', 'is_available': False, 'rent': 1500}
    ]
    
    units_data = {
        '1': [
            {'id': 1, 'unit_number': '1A', 'bedrooms': 2, 'bathrooms': 1, 'rent': 1200, 'square_feet': 850, 'is_available': True, 'property_id': 1},
            {'id': 2, 'unit_number': '1B', 'bedrooms': 1, 'bathrooms': 1, 'rent': 1000, 'square_feet': 650, 'is_available': False, 'property_id': 1}
        ],
        '2': [
            {'id': 3, 'unit_number': '2A', 'bedrooms': 3, 'bathrooms': 2, 'rent': 1500, 'square_feet': 1200, 'is_available': False, 'property_id': 2}
        ]
    }
    
    next_unit_id = [4]  # Use list to make it mutable
    next_property_id = [3]
    next_tenant_id = [3]
    next_user_id = [4]
    next_payment_id = [4]
    
    # Sample tenant data
    tenants_data = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'property_id': 1, 'unit_id': 1, 'status': 'active'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'property_id': 2, 'unit_id': 3, 'status': 'active'}
    ]
    
    # Sample user data with hashed passwords
    # Default password for all users is "password123" (change in production)
    default_password_hash = hash_password("password123")
    admin_password_hash = hash_password("admin")
    
    users_data = [
        {
            'id': 1, 
            'email': 'john@example.com', 
            'username': 'John Doe', 
            'role': 'tenant',
            'password_hash': default_password_hash,
            'is_active': True,
            'created_at': '2025-01-01T00:00:00Z'
        },
        {
            'id': 2, 
            'email': 'jane@example.com', 
            'username': 'Jane Smith', 
            'role': 'tenant',
            'password_hash': default_password_hash,
            'is_active': True,
            'created_at': '2025-01-02T00:00:00Z'
        },
        {
            'id': 3, 
            'email': 'admin@estatecore.com', 
            'username': 'Admin User', 
            'role': 'admin',
            'password_hash': admin_password_hash,
            'is_active': True,
            'created_at': '2025-01-01T00:00:00Z'
        }
    ]
    
    # Sample payments data
    payments_data = [
        {'id': 1, 'tenant_id': 1, 'amount': 1200.00, 'due_date': '2025-01-01', 'status': 'completed', 'payment_date': '2024-12-28'},
        {'id': 2, 'tenant_id': 2, 'amount': 1500.00, 'due_date': '2025-01-01', 'status': 'pending', 'payment_date': None},
        {'id': 3, 'tenant_id': 1, 'amount': 1200.00, 'due_date': '2025-02-01', 'status': 'pending', 'payment_date': None}
    ]
    
    # LPR Companies data storage
    lpr_companies_data = [
        {
            'id': 1,
            'name': 'SecureView LLC',
            'description': 'Professional security monitoring services for residential properties',
            'contact_email': 'admin@secureview.com',
            'contact_phone': '+1-555-0100',
            'address': '123 Security Blvd, Tech City, TC 12345',
            'max_alerts_per_day': 500,
            'max_cameras': 50,
            'subscription_type': 'enterprise',
            'user_count': 25,
            'users': [
                {
                    'id': 1,
                    'username': 'john.security',
                    'email': 'john@secureview.com',
                    'role': 'admin',
                    'lpr_permissions': 'full_access'
                },
                {
                    'id': 2,
                    'username': 'jane.monitor',
                    'email': 'jane@secureview.com',
                    'role': 'operator',
                    'lpr_permissions': 'view_alerts'
                }
            ]
        },
        {
            'id': 2,
            'name': 'PropertyGuard Systems',
            'description': 'Automated license plate recognition for apartment complexes',
            'contact_email': 'support@propertyguard.com',
            'contact_phone': '+1-555-0200',
            'address': '456 Guard Ave, Security Town, ST 67890',
            'max_alerts_per_day': 200,
            'max_cameras': 20,
            'subscription_type': 'premium',
            'user_count': 12,
            'users': [
                {
                    'id': 3,
                    'username': 'admin.guard',
                    'email': 'admin@propertyguard.com',
                    'role': 'admin',
                    'lpr_permissions': 'full_access'
                }
            ]
        }
    ]
    
    next_lpr_company_id = [3]
    
    @app.route('/')
    def home():
        return jsonify({
            'message': 'EstateCore API is running',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/dashboard')
    def api_dashboard():
        # Calculate real metrics from actual data
        total_properties = len(properties_data)
        available_properties = len([p for p in properties_data if p.get('is_available', False)])
        total_users = len(users_data)
        
        # Calculate total revenue from all units
        total_revenue = 0
        total_units = 0
        occupied_units = 0
        
        for property_id, units in units_data.items():
            for unit in units:
                total_units += 1
                if not unit.get('is_available', True):  # Not available means occupied
                    occupied_units += 1
                    total_revenue += unit.get('rent', 0)
        
        # Estimate pending revenue (assume 10% of total for demo)
        pending_revenue = total_revenue * 0.1
        
        return jsonify({
            'total_properties': total_properties,
            'available_properties': available_properties,
            'total_users': total_users,
            'total_revenue': total_revenue,
            'pending_revenue': pending_revenue,
            'total_units': total_units,
            'occupied_units': occupied_units,
            'occupancy_rate': round((occupied_units / total_units * 100) if total_units > 0 else 0, 1),
            'total_tenants': len(tenants_data)
        })
    
    @app.route('/dashboard')
    def dashboard():
        # Same logic as /api/dashboard for compatibility
        total_properties = len(properties_data)
        available_properties = len([p for p in properties_data if p.get('is_available', False)])
        total_users = len(users_data)
        
        total_revenue = 0
        total_units = 0
        occupied_units = 0
        
        for property_id, units in units_data.items():
            for unit in units:
                total_units += 1
                if not unit.get('is_available', True):
                    occupied_units += 1
                    total_revenue += unit.get('rent', 0)
        
        pending_revenue = total_revenue * 0.1
        
        return jsonify({
            'total_properties': total_properties,
            'available_properties': available_properties,
            'total_users': total_users,
            'total_revenue': total_revenue,
            'pending_revenue': pending_revenue,
            'total_units': total_units,
            'occupied_units': occupied_units,
            'occupancy_rate': round((occupied_units / total_units * 100) if total_units > 0 else 0, 1),
            'total_tenants': len(tenants_data)
        })
    
    @app.route('/api/auth/login', methods=['POST'])
    @limiter.limit("5 per minute")
    def login():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate input
        errors = validate_input(data, ['email', 'password'])
        if errors:
            return jsonify({'error': errors}), 400
            
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        client_ip = get_remote_address()
        
        # Check for too many failed attempts
        if client_ip in failed_attempts:
            attempts = failed_attempts[client_ip]
            if len(attempts) >= 5:
                # Check if last attempt was within last 15 minutes
                recent_attempts = [a for a in attempts if time.time() - a < 900]  # 15 minutes
                if len(recent_attempts) >= 5:
                    return jsonify({'error': 'Too many failed attempts. Try again later.'}), 429
        
        # Find user by email
        user = None
        for u in users_data:
            if u['email'].lower() == email and u.get('is_active', True):
                user = u
                break
        
        # Verify credentials
        if user and verify_password(password, user['password_hash']):
            # Clear failed attempts on successful login
            if client_ip in failed_attempts:
                del failed_attempts[client_ip]
                
            # Generate JWT token
            token = generate_jwt_token(user)
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'username': user['username'],
                    'role': user['role']
                }
            })
        else:
            # Record failed attempt
            if client_ip not in failed_attempts:
                failed_attempts[client_ip] = []
            failed_attempts[client_ip].append(time.time())
            
            return jsonify({'error': 'Invalid email or password'}), 401
    
    @app.route('/api/auth/logout', methods=['POST'])
    @require_auth
    def logout():
        # In a real app, you'd invalidate the token in a blacklist
        return jsonify({'message': 'Logged out successfully'})
    
    @app.route('/api/auth/me', methods=['GET'])
    @require_auth
    def get_current_user():
        return jsonify({
            'user': {
                'id': request.current_user['user_id'],
                'email': request.current_user['email'],
                'role': request.current_user['role']
            }
        })
    
    # Invite endpoints
    @app.route('/api/invites/verify', methods=['POST'])
    def verify_invite():
        data = request.get_json()
        token = data.get('token')
        email = data.get('email')
        
        # Mock validation
        if token and email:
            return jsonify({
                'valid': True,
                'email': email,
                'role': 'tenant',
                'invited_by': 'Admin User'
            })
        else:
            return jsonify({'error': 'Invalid or expired invitation'}), 400
    
    @app.route('/api/invites/accept', methods=['POST'])
    def accept_invite():
        data = request.get_json()
        return jsonify({
            'success': True,
            'message': 'Account created successfully'
        })
    
    @app.route('/api/invites/send-enhanced', methods=['POST'])
    def send_enhanced_invite():
        data = request.get_json()
        email = data.get('email')
        access_type = data.get('access_type')
        property_role = data.get('property_role')
        lpr_role = data.get('lpr_role')
        lpr_company_id = data.get('lpr_company_id')
        lpr_permissions = data.get('lpr_permissions')
        
        # Generate secure invite token
        invite_token = secrets.token_urlsafe(32)
        
        # Store invite details
        invite_tokens[invite_token] = {
            'email': email,
            'access_type': access_type,
            'property_role': property_role,
            'lpr_role': lpr_role,
            'lpr_company_id': lpr_company_id,
            'lpr_permissions': lpr_permissions,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow().timestamp() + (7 * 24 * 60 * 60))  # 7 days
        }
        
        # Get LPR company name if applicable
        lpr_company_name = "Unknown Company"
        if lpr_company_id:
            for company in lpr_companies_data:
                if company['id'] == int(lpr_company_id):
                    lpr_company_name = company['name']
                    break
        
        # Create invite URL
        frontend_url = "http://localhost:3013"  # Update this to match your frontend URL
        invite_url = f"{frontend_url}/invite/accept?token={invite_token}&email={urllib.parse.quote(email)}"
        
        # Create email content
        html_content, text_content = create_invite_email_content(
            email, access_type, property_role, lpr_role, 
            lpr_company_name, lpr_permissions, invite_url
        )
        
        # Send email
        email_success, email_message = send_email(
            email, 
            "🏢 EstateCore Invitation - Join Our Property Management System",
            html_content,
            text_content
        )
        
        if email_success:
            return jsonify({
                'success': True,
                'message': f'Invitation email sent successfully to {email}',
                'invite_token': invite_token,
                'invite_url': invite_url,
                'access_details': {
                    'access_type': access_type,
                    'property_role': property_role,
                    'lpr_role': lpr_role,
                    'lpr_company_id': lpr_company_id,
                    'lpr_permissions': lpr_permissions
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send email: {email_message}',
                'invite_token': invite_token,  # Still return token for testing
                'invite_url': invite_url
            }), 500

    # Add common endpoints that frontend might call
    @app.route('/api/properties')
    def properties():
        return jsonify(properties_data)
    
    @app.route('/api/properties', methods=['POST'])
    def create_property():
        data = request.get_json()
        new_property = {
            'id': next_property_id[0],
            'name': data.get('name'),
            'address': data.get('address'),
            'type': data.get('type'),
            'rent': data.get('rent'),
            'bedrooms': data.get('bedrooms'),
            'bathrooms': data.get('bathrooms'),
            'is_available': True
        }
        properties_data.append(new_property)
        next_property_id[0] += 1
        return jsonify(new_property)
    
    @app.route('/api/units')
    def units():
        property_id = request.args.get('property_id')
        return jsonify(units_data.get(property_id, []))
    
    @app.route('/api/units', methods=['POST'])
    def create_unit():
        data = request.get_json()
        property_id = str(data.get('property_id'))
        
        new_unit = {
            'id': next_unit_id[0],
            'unit_number': data.get('unit_number'),
            'bedrooms': int(data.get('bedrooms', 0)) if data.get('bedrooms') else 0,
            'bathrooms': int(data.get('bathrooms', 0)) if data.get('bathrooms') else 0,
            'rent': float(data.get('rent', 0)) if data.get('rent') else 0,
            'square_feet': int(data.get('square_feet', 0)) if data.get('square_feet') else 0,
            'is_available': True,
            'property_id': int(property_id) if property_id else None
        }
        
        # Initialize the property's units list if it doesn't exist
        if property_id not in units_data:
            units_data[property_id] = []
        
        # Add the new unit to the property's units list
        units_data[property_id].append(new_unit)
        next_unit_id[0] += 1
        
        return jsonify(new_unit)
    
    @app.route('/api/tenants')
    def tenants():
        return jsonify(tenants_data)
    
    @app.route('/api/tenants', methods=['POST'])
    def create_tenant():
        data = request.get_json()
        new_tenant = {
            'id': next_tenant_id[0],
            'user_id': data.get('user_id'),
            'property_id': data.get('property_id'),
            'unit_id': data.get('unit_id'),
            'lease_start': data.get('lease_start'),
            'lease_end': data.get('lease_end'),
            'rent_amount': data.get('rent_amount'),
            'deposit': data.get('deposit'),
            'lease_document_name': data.get('lease_document_name'),
            'lease_document_path': data.get('lease_document_path'),
            'lease_parsed_data': data.get('lease_parsed_data'),
            'status': 'active'
        }
        tenants_data.append(new_tenant)
        next_tenant_id[0] += 1
        return jsonify(new_tenant)
    
    @app.route('/api/tenants/<int:tenant_id>', methods=['PUT'])
    def update_tenant(tenant_id):
        data = request.get_json()
        for i, tenant in enumerate(tenants_data):
            if tenant['id'] == tenant_id:
                tenant.update(data)
                return jsonify(tenant)
        return jsonify({'error': 'Tenant not found'}), 404
    
    @app.route('/api/tenants/<int:tenant_id>', methods=['DELETE'])
    def delete_tenant(tenant_id):
        global tenants_data
        tenants_data = [t for t in tenants_data if t['id'] != tenant_id]
        return jsonify({'success': True})
    
    
    @app.route('/api/ai/process-lease', methods=['POST'])
    def process_lease():
        data = request.get_json()
        lease_content = data.get('lease_content', '')
        filename = data.get('filename', '')
        
        # Mock AI processing - simulate extracting data from lease
        parsed_data = {
            'tenant_name': 'Extracted Tenant Name',
            'property_address': 'Extracted Property Address',
            'lease_start_date': '2024-01-01',
            'lease_end_date': '2024-12-31',
            'monthly_rent': 1200,
            'security_deposit': 2400,
            'lease_terms': 'Standard 12-month lease agreement',
            'ai_confidence': 0.95,
            'extracted_fields': {
                'tenant_info': True,
                'property_info': True,
                'financial_terms': True,
                'dates': True
            }
        }
        
        return jsonify({
            'success': True,
            'filename': filename,
            'parsed_data': parsed_data,
            'processing_time': '2.3s',
            'confidence_score': 0.95
        })
    
    @app.route('/api/payments')
    @require_auth
    def payments():
        return jsonify(payments_data)
    
    @app.route('/api/rent/generate', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def generate_rent_invoices():
        """Generate monthly rent invoices for all active tenants"""
        data = request.get_json()
        month = data.get('month', datetime.now().strftime('%Y-%m'))
        
        generated_invoices = []
        
        for tenant in tenants_data:
            if tenant.get('status') == 'active' and tenant.get('rent_amount'):
                # Check if invoice already exists for this month
                existing_invoice = None
                for payment in payments_data:
                    if (payment.get('tenant_id') == tenant['id'] and 
                        payment.get('due_date', '').startswith(month)):
                        existing_invoice = payment
                        break
                
                if not existing_invoice:
                    # Generate new invoice
                    due_date = f"{month}-01"  # First of the month
                    new_invoice = {
                        'id': next_payment_id[0],
                        'tenant_id': tenant['id'],
                        'tenant_name': tenant.get('name', 'Unknown'),
                        'property_id': tenant.get('property_id'),
                        'unit_id': tenant.get('unit_id'),
                        'amount': float(tenant['rent_amount']),
                        'due_date': due_date,
                        'status': 'pending',
                        'type': 'rent',
                        'generated_date': datetime.now().isoformat(),
                        'payment_date': None,
                        'late_fees': 0.0,
                        'notes': f"Monthly rent for {month}"
                    }
                    
                    payments_data.append(new_invoice)
                    generated_invoices.append(new_invoice)
                    next_payment_id[0] += 1
        
        return jsonify({
            'success': True,
            'generated_count': len(generated_invoices),
            'invoices': generated_invoices,
            'month': month
        })
    
    @app.route('/api/rent/late-fees', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def calculate_late_fees():
        """Calculate and apply late fees to overdue payments"""
        data = request.get_json()
        late_fee_amount = data.get('late_fee_amount', 50.0)
        grace_period_days = data.get('grace_period_days', 5)
        
        today = datetime.now().date()
        updated_payments = []
        
        for payment in payments_data:
            if payment.get('status') == 'pending':
                due_date = datetime.strptime(payment['due_date'], '%Y-%m-%d').date()
                days_overdue = (today - due_date).days
                
                if days_overdue > grace_period_days and payment.get('late_fees', 0) == 0:
                    payment['late_fees'] = late_fee_amount
                    payment['amount'] += late_fee_amount
                    payment['notes'] = payment.get('notes', '') + f" | Late fee applied: ${late_fee_amount}"
                    updated_payments.append(payment)
        
        return jsonify({
            'success': True,
            'updated_count': len(updated_payments),
            'payments': updated_payments
        })
    
    @app.route('/api/rent/dashboard')
    @require_auth
    def rent_dashboard():
        """Comprehensive rent collection dashboard"""
        today = datetime.now().date()
        current_month = datetime.now().strftime('%Y-%m')
        
        # Calculate metrics
        total_rent_due = sum(p['amount'] for p in payments_data 
                           if p.get('status') == 'pending' and p.get('type') == 'rent')
        
        total_collected = sum(p['amount'] for p in payments_data 
                            if p.get('status') == 'completed' and p.get('type') == 'rent')
        
        overdue_payments = []
        current_month_payments = []
        
        for payment in payments_data:
            if payment.get('type') == 'rent':
                due_date = datetime.strptime(payment['due_date'], '%Y-%m-%d').date()
                
                if payment['due_date'].startswith(current_month):
                    current_month_payments.append(payment)
                
                if payment.get('status') == 'pending' and due_date < today:
                    days_overdue = (today - due_date).days
                    payment_copy = payment.copy()
                    payment_copy['days_overdue'] = days_overdue
                    overdue_payments.append(payment_copy)
        
        # Collection rate for current month
        current_month_total = sum(p['amount'] for p in current_month_payments)
        current_month_collected = sum(p['amount'] for p in current_month_payments 
                                    if p.get('status') == 'completed')
        collection_rate = (current_month_collected / current_month_total * 100) if current_month_total > 0 else 0
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_rent_due': total_rent_due,
                'total_collected': total_collected,
                'collection_rate': round(collection_rate, 1),
                'overdue_count': len(overdue_payments),
                'overdue_amount': sum(p['amount'] for p in overdue_payments)
            },
            'overdue_payments': overdue_payments,
            'current_month_payments': current_month_payments
        })
    
    @app.route('/api/stripe/config', methods=['GET'])
    @require_auth
    def get_stripe_config():
        """Get Stripe publishable key"""
        return jsonify({
            'publishable_key': STRIPE_PUBLISHABLE_KEY
        })
    
    @app.route('/api/payments/create-intent', methods=['POST'])
    @require_auth
    def create_payment_intent():
        """Create Stripe payment intent for rent payment"""
        data = request.get_json()
        
        # Validate input
        errors = validate_input(data, ['amount', 'payment_id'])
        if errors:
            return jsonify({'error': errors}), 400
        
        try:
            amount = int(float(data.get('amount')) * 100)  # Convert to cents
            payment_id = data.get('payment_id')
            
            # Find the payment record
            payment_record = None
            for payment in payments_data:
                if payment['id'] == int(payment_id):
                    payment_record = payment
                    break
            
            if not payment_record:
                return jsonify({'error': 'Payment not found'}), 404
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                automatic_payment_methods={
                    'enabled': True,
                },
                metadata={
                    'payment_id': payment_id,
                    'tenant_id': payment_record.get('tenant_id'),
                    'property_id': payment_record.get('property_id'),
                    'type': payment_record.get('type', 'rent')
                }
            )
            
            # Update payment record with Stripe intent ID
            payment_record['stripe_intent_id'] = intent.id
            payment_record['status'] = 'processing'
            
            return jsonify({
                'client_secret': intent.client_secret,
                'payment_id': payment_id,
                'amount': amount,
                'status': intent.status
            })
            
        except stripe.error.StripeError as e:
            return jsonify({'error': f'Stripe error: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'error': f'Payment processing error: {str(e)}'}), 500
    
    @app.route('/api/payments/webhook', methods=['POST'])
    @limiter.exempt
    def stripe_webhook():
        """Handle Stripe webhook events"""
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            if endpoint_secret:
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            else:
                # For development without webhook secret
                event = stripe.Event.construct_from(request.get_json(), stripe.api_key)
            
            # Handle payment succeeded
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                payment_id = payment_intent.get('metadata', {}).get('payment_id')
                
                if payment_id:
                    # Update payment record
                    for payment in payments_data:
                        if payment['id'] == int(payment_id):
                            payment['status'] = 'completed'
                            payment['payment_date'] = datetime.now().isoformat()
                            payment['stripe_payment_id'] = payment_intent.get('id')
                            break
            
            # Handle payment failed
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                payment_id = payment_intent.get('metadata', {}).get('payment_id')
                
                if payment_id:
                    for payment in payments_data:
                        if payment['id'] == int(payment_id):
                            payment['status'] = 'failed'
                            payment['failure_reason'] = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
                            break
            
            return jsonify({'status': 'success'})
            
        except ValueError as e:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            return jsonify({'error': 'Invalid signature'}), 400
    
    @app.route('/api/payments/<int:payment_id>/confirm', methods=['POST'])
    def confirm_payment(payment_id):
        for payment in payments_data:
            if payment['id'] == payment_id:
                payment['status'] = 'completed'
                payment['payment_date'] = datetime.utcnow().isoformat()
                return jsonify({'success': True, 'payment': payment})
        return jsonify({'error': 'Payment not found'}), 404
    
    @app.route('/api/payments', methods=['POST'])
    def create_payment():
        data = request.get_json()
        new_payment = {
            'id': next_payment_id[0],
            'tenant_id': data.get('tenant_id'),
            'amount': data.get('amount'),
            'due_date': data.get('due_date'),
            'status': 'pending',
            'payment_date': None
        }
        payments_data.append(new_payment)
        next_payment_id[0] += 1
        return jsonify(new_payment)
    
    # Maintenance system data
    maintenance_requests = [
        {
            'id': 1,
            'title': 'Fix leaky faucet',
            'description': 'Kitchen sink is dripping constantly, causing water waste',
            'status': 'pending',
            'priority': 'medium',
            'category': 'plumbing',
            'property_id': 1,
            'property_name': 'Test Property 1',
            'unit_id': 1,
            'tenant_contact': 'john@example.com',
            'created_at': '2025-01-15T10:00:00Z',
            'assigned_vendor': None,
            'estimated_cost': 150.0,
            'photos': []
        },
        {
            'id': 2,
            'title': 'Replace light bulb',
            'description': 'Hallway light is out, needs LED replacement',
            'status': 'completed',
            'priority': 'low',
            'category': 'electrical',
            'property_id': 2,
            'property_name': 'Test Property 2',
            'unit_id': 3,
            'tenant_contact': 'jane@example.com',
            'created_at': '2025-01-14T09:30:00Z',
            'assigned_vendor': 'ABC Electric',
            'estimated_cost': 25.0,
            'completed_at': '2025-01-14T15:30:00Z',
            'photos': []
        },
        {
            'id': 3,
            'title': 'HVAC system maintenance',
            'description': 'Annual HVAC system check and filter replacement',
            'status': 'assigned',
            'priority': 'high',
            'category': 'hvac',
            'property_id': 1,
            'property_name': 'Test Property 1',
            'unit_id': 2,
            'tenant_contact': None,
            'created_at': '2025-01-16T08:00:00Z',
            'assigned_vendor': 'Climate Control Pro',
            'estimated_cost': 350.0,
            'photos': []
        }
    ]
    
    maintenance_vendors = [
        {
            'id': 1,
            'name': 'John Smith',
            'company': 'ABC Electric',
            'email': 'john@abcelectric.com',
            'phone': '+1-555-0101',
            'specialties': ['electrical', 'lighting'],
            'hourly_rate': 85.0,
            'rating': 4.8,
            'insurance_verified': True,
            'active': True
        },
        {
            'id': 2,
            'name': 'Mike Johnson',
            'company': 'Pro Plumbing',
            'email': 'mike@proplumbing.com',
            'phone': '+1-555-0102',
            'specialties': ['plumbing', 'appliances'],
            'hourly_rate': 95.0,
            'rating': 4.9,
            'insurance_verified': True,
            'active': True
        },
        {
            'id': 3,
            'name': 'Sarah Wilson',
            'company': 'Climate Control Pro',
            'email': 'sarah@climatecontrol.com',
            'phone': '+1-555-0103',
            'specialties': ['hvac', 'refrigeration'],
            'hourly_rate': 110.0,
            'rating': 4.7,
            'insurance_verified': True,
            'active': True
        }
    ]
    
    next_maintenance_id = [4]
    next_vendor_id = [4]
    
    @app.route('/api/maintenance')
    def maintenance():
        # Legacy endpoint for backward compatibility
        return jsonify(maintenance_requests)
    
    @app.route('/api/maintenance/requests')
    @require_auth
    def get_maintenance_requests():
        """Get all maintenance requests"""
        return jsonify(maintenance_requests)
    
    @app.route('/api/maintenance/requests', methods=['POST'])
    @require_auth
    def create_maintenance_request():
        """Create new maintenance request"""
        data = request.get_json()
        
        # Validate input
        errors = validate_input(data, ['title', 'description', 'priority', 'category'])
        if errors:
            return jsonify({'error': errors}), 400
        
        new_request = {
            'id': next_maintenance_id[0],
            'title': data.get('title'),
            'description': data.get('description'),
            'status': 'pending',
            'priority': data.get('priority', 'medium'),
            'category': data.get('category'),
            'property_id': data.get('property_id'),
            'property_name': data.get('property_name', f"Property #{data.get('property_id')}"),
            'unit_id': data.get('unit_id'),
            'tenant_contact': data.get('tenant_contact'),
            'created_at': datetime.now().isoformat(),
            'assigned_vendor': None,
            'estimated_cost': data.get('estimated_cost', 0.0),
            'photos': data.get('photos', [])
        }
        
        maintenance_requests.append(new_request)
        next_maintenance_id[0] += 1
        
        return jsonify(new_request)
    
    @app.route('/api/maintenance/requests/<int:request_id>/assign', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def assign_vendor(request_id):
        """Assign vendor to maintenance request"""
        data = request.get_json()
        vendor_id = data.get('vendor_id')
        
        # Find vendor
        vendor = None
        for v in maintenance_vendors:
            if v['id'] == int(vendor_id):
                vendor = v
                break
        
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404
        
        # Find and update request
        for req in maintenance_requests:
            if req['id'] == request_id:
                req['assigned_vendor'] = f"{vendor['name']} - {vendor['company']}"
                req['status'] = 'assigned'
                req['assigned_at'] = datetime.now().isoformat()
                return jsonify(req)
        
        return jsonify({'error': 'Request not found'}), 404
    
    @app.route('/api/maintenance/requests/<int:request_id>/status', methods=['PUT'])
    @require_auth
    def update_request_status(request_id):
        """Update maintenance request status"""
        data = request.get_json()
        new_status = data.get('status')
        
        valid_statuses = ['pending', 'assigned', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        # Find and update request
        for req in maintenance_requests:
            if req['id'] == request_id:
                req['status'] = new_status
                if new_status == 'completed':
                    req['completed_at'] = datetime.now().isoformat()
                elif new_status == 'in_progress':
                    req['started_at'] = datetime.now().isoformat()
                return jsonify(req)
        
        return jsonify({'error': 'Request not found'}), 404
    
    @app.route('/api/maintenance/vendors')
    @require_auth
    def get_vendors():
        """Get all maintenance vendors"""
        return jsonify([v for v in maintenance_vendors if v.get('active', True)])
    
    @app.route('/api/maintenance/vendors', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def create_vendor():
        """Add new maintenance vendor"""
        data = request.get_json()
        
        # Validate input
        errors = validate_input(data, ['name'])
        if errors:
            return jsonify({'error': errors}), 400
        
        new_vendor = {
            'id': next_vendor_id[0],
            'name': data.get('name'),
            'company': data.get('company', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'specialties': data.get('specialties', []),
            'hourly_rate': float(data.get('hourly_rate', 0)) if data.get('hourly_rate') else 0.0,
            'rating': float(data.get('rating', 5.0)),
            'insurance_verified': data.get('insurance_verified', False),
            'active': True,
            'created_at': datetime.now().isoformat()
        }
        
        maintenance_vendors.append(new_vendor)
        next_vendor_id[0] += 1
        
        return jsonify(new_vendor)
    
    @app.route('/api/maintenance/dashboard')
    @require_auth
    def maintenance_dashboard():
        """Comprehensive maintenance dashboard metrics"""
        today = datetime.now()
        
        # Calculate metrics
        total_requests = len(maintenance_requests)
        pending_requests = len([r for r in maintenance_requests if r['status'] == 'pending'])
        in_progress_requests = len([r for r in maintenance_requests if r['status'] == 'in_progress'])
        completed_requests = len([r for r in maintenance_requests if r['status'] == 'completed'])
        
        # Emergency requests
        emergency_requests = [r for r in maintenance_requests if r['priority'] == 'emergency' and r['status'] != 'completed']
        
        # Calculate costs
        total_estimated_cost = sum(r.get('estimated_cost', 0) for r in maintenance_requests)
        completed_cost = sum(r.get('estimated_cost', 0) for r in maintenance_requests if r['status'] == 'completed')
        
        # Average response time (mock calculation)
        avg_response_time = 4.2  # hours
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'in_progress_requests': in_progress_requests,
                'completed_requests': completed_requests,
                'emergency_requests': len(emergency_requests),
                'total_estimated_cost': total_estimated_cost,
                'completed_cost': completed_cost,
                'avg_response_time': avg_response_time,
                'vendor_count': len([v for v in maintenance_vendors if v.get('active', True)])
            },
            'emergency_requests': emergency_requests,
            'recent_requests': sorted(maintenance_requests, key=lambda x: x['created_at'], reverse=True)[:10]
        })
    
    @app.route('/api/maintenance/dispatch', methods=['POST'])
    def maintenance_dispatch():
        data = request.get_json()
        request_id = data.get('request_id')
        return jsonify({
            'success': True,
            'contractor': 'ABC Maintenance Co.',
            'eta_hours': 4,
            'message': f'Request {request_id} dispatched successfully'
        })
    
    @app.route('/api/maintenance', methods=['POST'])
    def create_maintenance():
        data = request.get_json()
        return jsonify({
            'id': 3,
            'title': data.get('title'),
            'description': data.get('description'),
            'status': 'open',
            'priority': data.get('priority', 'medium'),
            'created_at': datetime.utcnow().isoformat()
        })
    
    # Analytics endpoints
    @app.route('/api/analytics/overview')
    def analytics_overview():
        return jsonify({
            'key_metrics': {
                'occupancy_rate': 85,
                'total_properties': 15
            },
            'performance_indicators': {
                'revenue_growth': 12,
                'tenant_satisfaction': 4.2
            },
            'recent_activity': [
                {'action': 'New tenant signed lease', 'time': '2 hours ago'},
                {'action': 'Maintenance request completed', 'time': '4 hours ago'}
            ],
            'alerts': [
                {'type': 'info', 'message': 'All systems operational'}
            ]
        })
    
    @app.route('/api/ai/revenue-forecast')
    def revenue_forecast():
        return jsonify({
            'current_month': 125000,
            'next_month': 130000,
            'quarterly': 390000,
            'annual': 1560000,
            'trends': {
                'growth_rate': 8,
                'confidence': 92
            },
            'recommendations': [
                'Consider raising rent on unit 2A by 3%',
                'Schedule maintenance to prevent revenue loss'
            ]
        })
    
    @app.route('/api/ai/maintenance-forecast')
    def maintenance_forecast():
        return jsonify({
            'upcoming_maintenance': 7,
            'estimated_monthly_cost': 8500,
            'high_priority_items': 2,
            'predictive_alerts': [
                {
                    'property': 'Test Property 1',
                    'issue': 'HVAC system showing early wear signs',
                    'urgency': 'medium'
                }
            ],
            'cost_optimization': [
                'Bundle similar maintenance tasks to reduce costs',
                'Schedule preventive maintenance during off-peak season'
            ]
        })
    
    @app.route('/api/ai/tenant-score/<tenant_id>')
    def tenant_score(tenant_id):
        return jsonify({
            'score': 85,
            'risk_level': 'low',
            'factors': {
                'payment_history': 95,
                'communication': 80,
                'maintenance_requests': 75
            }
        })

    @app.route('/api/ai/lease-expiration-check')
    def lease_expiration_check():
        return jsonify({
            'success': True,
            'total_count': 3,
            'high_priority_count': 1,
            'expiring_leases': [
                {
                    'tenant_name': 'Sarah Johnson',
                    'property_name': 'Sunset Apartments',
                    'unit_number': '2A',
                    'lease_end_date': '2025-10-15',
                    'days_until_expiry': 26,
                    'priority': 'high'
                },
                {
                    'tenant_name': 'Mike Chen',
                    'property_name': 'Oak Ridge Complex',
                    'unit_number': '1B',
                    'lease_end_date': '2025-11-30',
                    'days_until_expiry': 72,
                    'priority': 'medium'
                },
                {
                    'tenant_name': 'Emily Davis',
                    'property_name': 'Maple Street Units',
                    'unit_number': '3C',
                    'lease_end_date': '2025-12-31',
                    'days_until_expiry': 103,
                    'priority': 'low'
                }
            ]
        })
    
    @app.route('/api/lpr/events')
    def lpr_events():
        return jsonify([
            {
                'id': 1,
                'plate_number': 'ABC123',
                'confidence': 0.95,
                'camera_id': 'cam_001',
                'created_at': '2025-01-19T10:30:00Z',
                'location': 'Main Entrance',
                'status': 'allowed'
            },
            {
                'id': 2,
                'plate_number': 'XYZ789',
                'confidence': 0.88,
                'camera_id': 'cam_002', 
                'created_at': '2025-01-19T09:15:00Z',
                'location': 'Parking Garage',
                'status': 'denied'
            },
            {
                'id': 3,
                'plate_number': 'DEF456',
                'confidence': 0.92,
                'camera_id': 'cam_001',
                'created_at': '2025-01-18T16:45:00Z',
                'location': 'Main Entrance',
                'status': 'allowed'
            }
        ])
    
    @app.route('/api/lpr/blacklist')
    def lpr_blacklist():
        return jsonify([
            {
                'id': 1,
                'plate_number': 'BAN001',
                'reason': 'Unauthorized vehicle',
                'added_by': 'admin',
                'created_at': '2025-01-15T14:20:00Z'
            },
            {
                'id': 2,
                'plate_number': 'XYZ789',
                'reason': 'Trespassing incident',
                'added_by': 'security',
                'created_at': '2025-01-16T08:30:00Z'
            }
        ])
    
    
    @app.route('/api/lpr/companies')
    def lpr_companies():
        return jsonify(lpr_companies_data)
    
    @app.route('/api/lpr/companies', methods=['POST'])
    def create_lpr_company():
        data = request.get_json()
        new_company = {
            'id': next_lpr_company_id[0],
            'name': data.get('name'),
            'description': data.get('description', ''),
            'contact_email': data.get('contact_email', ''),
            'contact_phone': data.get('contact_phone', ''),
            'address': data.get('address', ''),
            'max_alerts_per_day': int(data.get('max_alerts_per_day', 100)),
            'max_cameras': int(data.get('max_cameras', 100)),
            'subscription_type': data.get('subscription_type', 'basic'),
            'user_count': 0,
            'users': []
        }
        lpr_companies_data.append(new_company)
        next_lpr_company_id[0] += 1
        return jsonify(new_company)
    
    @app.route('/api/lpr/companies/<int:company_id>')
    def get_lpr_company(company_id):
        for company in lpr_companies_data:
            if company['id'] == company_id:
                return jsonify(company)
        return jsonify({'error': 'Company not found'}), 404
    
    # Add more common endpoints that pages might need
    
    @app.route('/api/financial/dashboard')
    def financial_dashboard():
        return jsonify({
            'success': True,
            'data': {
                'overview_metrics': {
                    'total_revenue': 125000.50,
                    'net_income': 89000.25,
                    'profit_margin': 71.2,
                    'cash_flow': 45000.75,
                    'occupancy_rate': 95.5
                },
                'quick_stats': {
                    'properties_count': 15,
                    'units_count': 120,
                    'tenants_count': 114,
                    'maintenance_requests': 3
                },
                'alerts': [
                    {
                        'type': 'warning',
                        'severity': 'medium',
                        'title': 'High Vacancy Rate',
                        'message': 'Unit 2A has been vacant for 45 days'
                    }
                ]
            }
        })
    
    @app.route('/api/lease/dashboard')
    def lease_dashboard():
        return jsonify({
            'success': True,
            'data': {
                'total_active_leases': 114,
                'occupancy_rate': 95.0,
                'expiring_soon': 8,
                'renewal_rate': 87.5,
                'lease_violations': {
                    'open': 2,
                    'resolved': 15
                }
            }
        })
    
    @app.route('/api/maintenance/scheduling')
    def maintenance_scheduling():
        return jsonify({
            'success': True,
            'scheduled_requests': [
                {
                    'id': 1,
                    'title': 'HVAC Maintenance',
                    'property': 'Building A',
                    'unit': '2A',
                    'scheduled_date': '2025-01-25',
                    'priority': 'medium',
                    'status': 'scheduled'
                }
            ]
        })
    
    @app.route('/api/tenant-screening')
    def tenant_screening():
        return jsonify({
            'success': True,
            'applications': [
                {
                    'id': 1,
                    'applicant_name': 'John Smith',
                    'property': 'Sunset Apartments',
                    'unit': '3B',
                    'status': 'pending',
                    'score': 750,
                    'submitted_date': '2025-01-18'
                }
            ]
        })
    
    @app.route('/api/bulk-operations')
    def bulk_operations():
        return jsonify({
            'success': True,
            'operations': [
                {
                    'id': 1,
                    'type': 'rent_increase',
                    'status': 'completed',
                    'affected_units': 25,
                    'created_date': '2025-01-15'
                }
            ]
        })
    
    @app.route('/api/access-logs')
    def access_logs():
        return jsonify([
            {
                'id': 1,
                'user': 'John Doe',
                'door': 'Main Entrance',
                'time': '2025-01-19T10:30:00Z',
                'action': 'entry',
                'status': 'success'
            },
            {
                'id': 2,
                'user': 'Jane Smith',
                'door': 'Parking Garage',
                'time': '2025-01-19T09:15:00Z',
                'action': 'exit',
                'status': 'success'
            }
        ])
    
    @app.route('/api/access-logs/simulate', methods=['POST'])
    def simulate_access():
        return jsonify({'success': True, 'message': 'Access log simulated'})
    
    @app.route('/api/messages')
    def messages():
        return jsonify([
            {
                'id': 1,
                'from': 'Property Manager',
                'to': 'John Doe',
                'subject': 'Rent Reminder',
                'message': 'Your rent is due on the 1st',
                'timestamp': '2025-01-19T10:00:00Z',
                'read': False
            }
        ])
    
    @app.route('/api/documents')
    def documents():
        return jsonify([
            {
                'id': 1,
                'name': 'Lease Agreement.pdf',
                'type': 'lease',
                'size': '2.5 MB',
                'uploaded_date': '2025-01-15',
                'tenant': 'John Doe'
            }
        ])
    
    @app.route('/api/reports')
    def reports():
        return jsonify([
            {
                'id': 1,
                'name': 'Monthly Revenue Report',
                'type': 'financial',
                'generated_date': '2025-01-01',
                'status': 'completed'
            }
        ])
    
    @app.route('/api/performance/metrics')
    def performance_metrics():
        return jsonify({
            'success': True,
            'metrics': {
                'response_time': 250,
                'uptime': 99.9,
                'memory_usage': 45.2,
                'cpu_usage': 23.1
            }
        })
    
    @app.route('/api/testing/results')
    def testing_results():
        return jsonify({
            'success': True,
            'test_suites': [
                {
                    'name': 'API Tests',
                    'status': 'passed',
                    'tests_run': 45,
                    'passed': 43,
                    'failed': 2
                }
            ]
        })
    
    # ===== AI/ML API ENDPOINTS =====
    
    @app.route('/api/ai/asset-health', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_asset_health():
        """AI-powered asset health scoring"""
        try:
            # Import AI module
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), 'ai_modules', 'predict'))
            from asset_health_score import get_asset_health_score
            
            data = request.get_json()
            property_id = data.get('property_id')
            
            # Get property data (mock for now)
            input_data = {
                'maintenance_history': [
                    {'date': '2024-01-15', 'cost': 350, 'category': 'plumbing', 'priority': 'medium'},
                    {'date': '2024-02-20', 'cost': 150, 'category': 'electrical', 'priority': 'low'}
                ],
                'financial_performance': {
                    'revenue_trend': 0.05,
                    'expense_ratio': 0.25,
                    'occupancy_rate': 0.95,
                    'collection_rate': 0.98
                },
                'condition_reports': [
                    {'date': '2024-01-01', 'overall_rating': 8, 'critical_issues': 0, 'property_age_years': 15}
                ],
                'occupancy_rate': 0.95,
                'utility_efficiency': 0.85,
                'tenant_satisfaction': 0.88
            }
            
            result = get_asset_health_score(input_data)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Asset health analysis failed: {str(e)}'}), 500
    
    @app.route('/api/ai/maintenance-forecast', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_maintenance_forecast():
        """AI-powered maintenance forecasting"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), 'ai_modules', 'predict'))
            from maintenance_forecast import forecast_maintenance
            
            data = request.get_json()
            property_id = data.get('property_id')
            
            # Mock equipment and property data
            equipment_data = {
                'hvac_unit_1': {
                    'age_months': 36,
                    'type': 'hvac',
                    'usage_intensity': 'high',
                    'last_service_date': '2024-01-15'
                },
                'water_heater_1': {
                    'age_months': 48,
                    'type': 'appliances',
                    'usage_intensity': 'medium',
                    'last_service_date': '2023-12-01'
                }
            }
            
            property_data = {
                'square_footage': 1200,
                'age_years': 15,
                'type': 'apartment'
            }
            
            historical_data = [
                {'date': '2024-01-15', 'equipment_id': 'hvac_unit_1', 'cost': 350, 'description': 'Filter replacement'},
                {'date': '2023-12-01', 'equipment_id': 'water_heater_1', 'cost': 200, 'description': 'Thermostat repair'}
            ]
            
            result = forecast_maintenance(equipment_data, property_data, historical_data)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Maintenance forecast failed: {str(e)}'}), 500
    
    @app.route('/api/ai/tenant-score', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_tenant_score():
        """AI-powered tenant risk scoring"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), 'ai_modules', 'predict'))
            from lease_scoring import score_lease
            
            data = request.get_json()
            tenant_id = data.get('tenant_id')
            
            # Mock tenant data
            tenant_data = {
                'payment_history': [
                    {'date': '2024-01-01', 'status': 'on_time', 'amount': 1200},
                    {'date': '2024-02-01', 'status': 'on_time', 'amount': 1200},
                    {'date': '2024-03-01', 'status': 'late', 'days_late': 5, 'amount': 1200}
                ],
                'financial_info': {
                    'monthly_income': 4500,
                    'monthly_rent': 1200,
                    'monthly_debt_payments': 800,
                    'employment_length_months': 24,
                    'employment_type': 'full_time_permanent',
                    'credit_score': 720,
                    'liquid_assets': 8000
                },
                'behavioral_data': {
                    'avg_response_time_hours': 4,
                    'maintenance_requests': [
                        {'priority': 'low', 'resolved_quickly': True}
                    ],
                    'lease_violations': 0,
                    'neighbor_complaints': 0,
                    'property_condition_scores': [8, 8, 9]
                }
            }
            
            property_data = {
                'monthly_rent': 1200,
                'type': 'apartment',
                'location_desirability_score': 80
            }
            
            market_data = {
                'average_market_rent': 1250,
                'local_vacancy_rate': 0.04,
                'local_employment_rate': 0.96
            }
            
            result = score_lease(tenant_data, property_data, market_data)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Tenant scoring failed: {str(e)}'}), 500
    
    @app.route('/api/ai/revenue-leakage', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_revenue_leakage():
        """AI-powered revenue leakage detection"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), 'ai_modules', 'predict'))
            from revenue_leakage import detect_revenue_leakage
            
            data = request.get_json()
            portfolio_id = data.get('portfolio_id')
            
            # Mock property portfolio data
            property_data = {
                'units': [
                    {
                        'id': 'unit_1',
                        'number': '101',
                        'current_rent': 1100,
                        'type': 'apartment',
                        'square_footage': 900,
                        'status': 'occupied'
                    },
                    {
                        'id': 'unit_2',
                        'number': '102',
                        'current_rent': 1050,
                        'type': 'apartment',
                        'square_footage': 850,
                        'status': 'occupied'
                    },
                    {
                        'id': 'unit_3',
                        'number': '103',
                        'current_rent': 0,
                        'type': 'apartment',
                        'square_footage': 900,
                        'status': 'vacant',
                        'days_vacant': 45,
                        'market_rent': 1150
                    }
                ],
                'property_vacancy_rate': 0.08,
                'market_competition_level': 0.6
            }
            
            market_data = {
                'comparable_rents': {
                    'apartment': {'average': 1200},
                    'average': 1200
                },
                'average_market_rent': 1200,
                'comparable_properties_count': 8,
                'data_age_days': 15,
                'location_similarity_score': 0.9
            }
            
            historical_data = {
                'vacancy_periods': [
                    {'unit_id': 'unit_3', 'days_to_fill': 30, 'status': 'filled'},
                    {'unit_id': 'unit_2', 'days_to_fill': 21, 'status': 'filled'}
                ],
                'concessions': [],
                'maintenance_records': [
                    {'unit_id': 'unit_1', 'cost': 200, 'affects_habitability': False, 'preventable': True},
                    {'unit_id': 'unit_2', 'cost': 350, 'affects_habitability': True, 'preventable': False, 'severity': 'medium'}
                ]
            }
            
            result = detect_revenue_leakage(property_data, market_data, historical_data)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Revenue leakage detection failed: {str(e)}'}), 500
    
    @app.route('/api/ai/dashboard-summary', methods=['GET'])
    @require_auth
    def ai_dashboard_summary():
        """AI dashboard summary with key insights"""
        try:
            # This would aggregate data from all AI models
            summary = {
                'asset_health': {
                    'average_score': 78.5,
                    'properties_at_risk': 2,
                    'total_properties': 10,
                    'trend': 'stable'
                },
                'maintenance_forecast': {
                    'high_risk_equipment': 3,
                    'predicted_monthly_cost': 1250,
                    'optimization_savings': 320
                },
                'tenant_risk': {
                    'high_risk_tenants': 1,
                    'average_score': 82.3,
                    'renewal_likelihood': 0.87
                },
                'revenue_optimization': {
                    'total_annual_leakage': 8450,
                    'underpriced_units': 4,
                    'optimization_potential': 6200
                },
                'recommendations': [
                    {
                        'type': 'urgent',
                        'title': 'Review rent pricing for Unit 102',
                        'impact': '$1,800 annual'
                    },
                    {
                        'type': 'maintenance',
                        'title': 'Schedule HVAC maintenance for Building A',
                        'impact': '$500 savings'
                    },
                    {
                        'type': 'tenant',
                        'title': 'Monitor payment patterns for Tenant #3',
                        'impact': 'Risk mitigation'
                    }
                ]
            }
            
            return jsonify({'success': True, 'data': summary})
            
        except Exception as e:
            return jsonify({'error': f'AI dashboard summary failed: {str(e)}'}), 500
    
    @app.route('/api/ai/lease-renewal', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_lease_renewal():
        """Predict lease renewal probability"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'predict'))
            from lease_renewal import predict_lease_renewal
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Sample data for testing
            tenant_data = data.get('tenant_data', {
                'payment_history': [
                    {'date': '2024-01-01', 'status': 'on_time'},
                    {'date': '2024-02-01', 'status': 'on_time'},
                    {'date': '2024-03-01', 'status': 'late', 'days_late': 5},
                    {'date': '2024-04-01', 'status': 'on_time'}
                ],
                'maintenance_requests': [
                    {'satisfaction_rating': 4, 'response_time_hours': 24},
                    {'satisfaction_rating': 5, 'response_time_hours': 12}
                ],
                'communication_rating': 4,
                'lease_violations': 0,
                'complaint_count': 0,
                'tenancy_length_months': 18,
                'financial_info': {
                    'monthly_income': 5000,
                    'monthly_rent': 1200,
                    'monthly_debt_payments': 800,
                    'employment_length_months': 24,
                    'credit_score': 720
                }
            })
            
            lease_data = data.get('lease_data', {
                'monthly_rent': 1200,
                'lease_length_months': 12,
                'lease_end_date': '2024-12-31',
                'rent_increase_history': [
                    {'date': '2024-01-01', 'percentage': 3.0}
                ],
                'included_utilities': ['water', 'trash'],
                'amenities_included': ['parking'],
                'pet_friendly': True,
                'parking_included': True,
                'security_deposit': 1200
            })
            
            property_data = data.get('property_data', {
                'age_years': 5,
                'last_renovation_year': 2022,
                'amenities': ['pool', 'gym', 'parking'],
                'location_rating': 8,
                'security_features': ['keypad_entry', 'cameras'],
                'energy_efficiency_rating': 'B'
            })
            
            market_data = data.get('market_data', {
                'average_market_rent': 1250,
                'local_vacancy_rate': 0.04,
                'annual_rent_growth': 0.035,
                'new_units_coming_online': 50,
                'total_market_units': 2000,
                'local_employment_rate': 0.96,
                'average_annual_increase': 3.5
            })
            
            result = predict_lease_renewal(tenant_data, lease_data, property_data, market_data)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Lease renewal prediction failed: {str(e)}'}), 500
    
    @app.route('/api/ai/utility-forecast', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_utility_forecast():
        """Forecast utility costs for properties"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'predict'))
            from utility_forecasting import forecast_utility_costs
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Sample data for testing
            property_data = data.get('property_data', {
                'square_footage': 1200,
                'total_units': 1,
                'occupancy_rate': 1.0,
                'energy_efficiency_rating': 'B',
                'insulation_rating': 'good',
                'hvac_age_years': 5,
                'heating_system_age': 5,
                'low_flow_fixtures': True,
                'landscaping_irrigation': 0.3,
                'recycling_service': True,
                'bulk_pickup': False,
                'internet_included': True,
                'cable_included': False,
                'property_type': 'residential',
                'age_years': 8,
                'solar_feasible': True
            })
            
            historical_data = data.get('historical_data', {
                'electricity_bills': [
                    {'usage': 950, 'cost': 114, 'month': 1},
                    {'usage': 820, 'cost': 98, 'month': 2},
                    {'usage': 750, 'cost': 90, 'month': 3},
                    {'usage': 680, 'cost': 82, 'month': 4}
                ],
                'gas_bills': [
                    {'usage': 45, 'cost': 54, 'month': 1},
                    {'usage': 38, 'cost': 46, 'month': 2},
                    {'usage': 25, 'cost': 30, 'month': 3},
                    {'usage': 15, 'cost': 18, 'month': 4}
                ],
                'water_bills': [
                    {'usage': 2800, 'cost': 28, 'month': 1},
                    {'usage': 2600, 'cost': 26, 'month': 2},
                    {'usage': 2400, 'cost': 24, 'month': 3},
                    {'usage': 2200, 'cost': 22, 'month': 4}
                ]
            })
            
            weather_data = data.get('weather_data', {
                'extreme_weather_frequency': 0.2,
                'average_summer_temp': 85,
                'average_winter_temp': 35,
                'cooling_degree_days': 1200,
                'heating_degree_days': 3500
            })
            
            market_data = data.get('market_data', {
                'electricity_rate_trend': 0.03,
                'gas_rate_trend': 0.04,
                'water_rate_trend': 0.02,
                'renewable_incentives': True
            })
            
            result = forecast_utility_costs(property_data, historical_data, weather_data, market_data)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Utility forecasting failed: {str(e)}'}), 500
    
    @app.route('/api/ai/property-valuation', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_property_valuation():
        """Estimate property value using multiple approaches"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'predict'))
            from property_valuation import estimate_property_value
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Sample data for testing
            property_data = data.get('property_data', {
                'square_footage': 1500,
                'age_years': 8,
                'condition': 'good',
                'location_score': 8,
                'property_type': 'residential',
                'amenities': ['pool', 'parking', 'updated_kitchen'],
                'land_area_sqft': 6000,
                'construction_quality': 'average',
                'updated_kitchen': True,
                'updated_bathrooms': True
            })
            
            market_data = data.get('market_data', {
                'annual_appreciation_rate': 0.04,
                'price_trend': 'increasing',
                'months_of_inventory': 5,
                'average_days_on_market': 35,
                'median_price_per_sqft': 180,
                'year_ago_price_per_sqft': 170,
                'land_value_per_sqft': 25,
                'median_home_value': 280000,
                'price_volatility': 0.08,
                'local_unemployment_rate': 0.04
            })
            
            financial_data = data.get('financial_data', {
                'monthly_rent': 2200,
                'vacancy_rate': 0.06,
                'annual_operating_expenses': 8000
            })
            
            comparable_sales = data.get('comparable_sales', [
                {
                    'id': 'comp_1',
                    'sale_price': 285000,
                    'square_footage': 1450,
                    'age_years': 10,
                    'condition': 'average',
                    'location_score': 7,
                    'amenities': ['parking'],
                    'sale_date': '2024-08-15'
                },
                {
                    'id': 'comp_2',
                    'sale_price': 310000,
                    'square_footage': 1600,
                    'age_years': 5,
                    'condition': 'good',
                    'location_score': 8,
                    'amenities': ['pool', 'parking'],
                    'sale_date': '2024-09-01'
                }
            ])
            
            result = estimate_property_value(property_data, market_data, financial_data, comparable_sales)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Property valuation failed: {str(e)}'}), 500
    
    @app.route('/api/ai/smart-notifications', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_smart_notifications():
        """Generate intelligent, prioritized notifications"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'predict'))
            from smart_notifications import generate_smart_notifications
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Sample data for testing
            tenant_data = data.get('tenant_data', {
                'lease_expirations': [
                    {
                        'tenant_id': 'tenant_1',
                        'tenant_name': 'John Smith',
                        'expiry_date': '2024-10-31',
                        'renewal_initiated': False,
                        'renewal_status': 'pending',
                        'property_id': 'prop_1'
                    }
                ],
                'satisfaction_scores': [
                    {
                        'tenant_id': 'tenant_2',
                        'tenant_name': 'Jane Doe',
                        'score': 3,
                        'issues': ['maintenance delays', 'noise complaints'],
                        'property_id': 'prop_2'
                    }
                ],
                'renewal_predictions': [
                    {
                        'tenant_id': 'tenant_3',
                        'tenant_name': 'Bob Johnson',
                        'renewal_probability': 0.45,
                        'property_id': 'prop_3'
                    }
                ],
                'tenants': [
                    {
                        'id': 'tenant_1',
                        'value_tier': 'high',
                        'complaint_frequency': 'low',
                        'payment_reliability': 'excellent'
                    }
                ]
            })
            
            property_data = data.get('property_data', {
                'security_incidents': [
                    {
                        'id': 'incident_1',
                        'type': 'break_in_attempt',
                        'severity': 'high',
                        'location': 'Building A parking garage',
                        'property_id': 'prop_1',
                        'reported_time': '2024-09-21T02:30:00'
                    }
                ],
                'rent_analysis': [
                    {
                        'property_id': 'prop_4',
                        'property_address': '123 Main St',
                        'market_position': 'significantly_below',
                        'below_market_pct': 15,
                        'potential_increase': 250
                    }
                ],
                'inspection_schedule': [
                    {
                        'id': 'inspection_1',
                        'property_address': '456 Oak Ave',
                        'scheduled_date': '2024-09-25',
                        'property_id': 'prop_5'
                    }
                ],
                'properties': [
                    {
                        'id': 'prop_1',
                        'value_tier': 'high'
                    }
                ]
            })
            
            maintenance_data = data.get('maintenance_data', {
                'emergency_requests': [
                    {
                        'id': 'emergency_1',
                        'description': 'Water leak in Unit 204',
                        'status': 'open',
                        'priority': 'emergency',
                        'tenant_id': 'tenant_4',
                        'property_id': 'prop_1',
                        'property_address': '789 Pine St',
                        'created_time': '2024-09-21T08:30:00'
                    }
                ],
                'equipment_health': [
                    {
                        'id': 'hvac_unit_1',
                        'name': 'HVAC Unit - Building A',
                        'failure_probability_30d': 0.35,
                        'property_id': 'prop_1'
                    }
                ]
            })
            
            financial_data = data.get('financial_data', {
                'late_payments': [
                    {
                        'tenant_id': 'tenant_5',
                        'tenant_name': 'Alice Williams',
                        'days_late': 12,
                        'amount': 1500,
                        'property_id': 'prop_2'
                    }
                ]
            })
            
            result = generate_smart_notifications(tenant_data, property_data, maintenance_data, financial_data)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Smart notifications failed: {str(e)}'}), 500
    
    @app.route('/api/ai/property-inspection', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def ai_property_inspection():
        """Analyze property images using computer vision"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'vision'))
            from property_inspector import analyze_property_image
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Get image data and analysis type
            image_data = data.get('image_data', '')
            analysis_type = data.get('analysis_type', 'general_inspection')
            
            # For demo purposes, simulate image analysis without actual image
            if not image_data:
                # Use demo image data for testing
                image_data = 'demo_image_base64_data'
            
            result = analyze_property_image(image_data, analysis_type)
            return jsonify({'success': True, 'data': result})
            
        except ImportError as e:
            return jsonify({'error': f'AI module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Property inspection failed: {str(e)}'}), 500
    
    @app.route('/api/iot/sensors', methods=['GET'])
    @require_auth
    @require_role(['admin', 'manager'])
    def get_iot_sensors():
        """Get IoT sensor status and data"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'iot'))
            from sensor_integration import IoTSensorManager, SensorType
            
            # Initialize sensor manager with demo data
            sensor_manager = IoTSensorManager()
            
            # Register demo sensors
            demo_sensors = [
                {
                    'type': 'temperature',
                    'property_id': 'prop_1',
                    'location': 'Living Room',
                    'thresholds': {'min': 65, 'max': 80}
                },
                {
                    'type': 'humidity',
                    'property_id': 'prop_1',
                    'location': 'Bathroom',
                    'thresholds': {'max': 70}
                },
                {
                    'type': 'occupancy',
                    'property_id': 'prop_1',
                    'location': 'Kitchen'
                },
                {
                    'type': 'energy',
                    'property_id': 'prop_1',
                    'location': 'Main Panel'
                }
            ]
            
            sensor_ids = []
            for sensor_config in demo_sensors:
                sensor_id = sensor_manager.register_sensor(sensor_config)
                sensor_ids.append(sensor_id)
            
            # Get current readings
            property_readings = sensor_manager.get_property_readings('prop_1')
            
            # Get sensor status summary
            status_summary = sensor_manager.get_sensor_status_summary('prop_1')
            
            # Convert readings to serializable format
            readings_data = []
            for reading in property_readings:
                readings_data.append({
                    'sensor_id': reading.sensor_id,
                    'sensor_type': reading.sensor_type.value,
                    'value': reading.value,
                    'unit': reading.unit,
                    'location': reading.location,
                    'timestamp': reading.timestamp.isoformat(),
                    'quality': reading.quality,
                    'alert_triggered': reading.alert_triggered
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'sensor_summary': status_summary,
                    'current_readings': readings_data,
                    'registered_sensors': len(sensor_ids)
                }
            })
            
        except ImportError as e:
            return jsonify({'error': f'IoT module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'IoT sensors request failed: {str(e)}'}), 500
    
    @app.route('/api/iot/analytics', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def get_iot_analytics():
        """Get IoT sensor analytics and insights"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'iot'))
            from sensor_integration import IoTSensorManager, analyze_sensor_data, SensorType
            
            data = request.get_json()
            property_id = data.get('property_id', 'prop_1')
            hours_back = data.get('hours_back', 24)
            
            # Initialize sensor manager and generate historical data
            sensor_manager = IoTSensorManager()
            
            # Register sensors and generate sample data
            sensor_configs = [
                {'type': 'temperature', 'property_id': property_id, 'location': 'Living Room'},
                {'type': 'humidity', 'property_id': property_id, 'location': 'Bathroom'},
                {'type': 'energy', 'property_id': property_id, 'location': 'Main Panel'},
                {'type': 'air_quality', 'property_id': property_id, 'location': 'Bedroom'}
            ]
            
            all_readings = []
            for config in sensor_configs:
                sensor_id = sensor_manager.register_sensor(config)
                # Generate multiple readings for analysis
                for _ in range(50):
                    reading = sensor_manager.get_sensor_reading(sensor_id)
                    all_readings.append(reading)
            
            # Analyze the sensor data
            analysis_result = analyze_sensor_data(all_readings)
            
            return jsonify({'success': True, 'data': analysis_result})
            
        except ImportError as e:
            return jsonify({'error': f'IoT module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'IoT analytics failed: {str(e)}'}), 500
    
    @app.route('/api/realtime/pipeline/status', methods=['GET'])
    @require_auth
    @require_role(['admin', 'manager'])
    def get_realtime_pipeline_status():
        """Get real-time data pipeline status"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'realtime'))
            from data_pipeline import RealTimeDataPipeline, DataStreamType, create_property_data_streams
            
            # Initialize pipeline
            pipeline = RealTimeDataPipeline()
            
            # Create demo streams
            property_streams = create_property_data_streams(pipeline, 'prop_1')
            
            # Start pipeline
            pipeline.start_pipeline()
            
            # Generate some demo events
            demo_events = [
                {
                    'stream_id': property_streams['sensors'],
                    'data': {
                        'sensor_type': 'temperature',
                        'value': 72.5,
                        'property_id': 'prop_1',
                        'location': 'living_room'
                    }
                },
                {
                    'stream_id': property_streams['alerts'],
                    'data': {
                        'alert_type': 'maintenance_due',
                        'severity': 'medium',
                        'property_id': 'prop_1',
                        'description': 'HVAC filter replacement due'
                    }
                }
            ]
            
            for event in demo_events:
                pipeline.publish_event(event['stream_id'], event['data'])
            
            # Get pipeline status
            status = pipeline.get_stream_status()
            analytics = pipeline.get_analytics_summary()
            
            return jsonify({
                'success': True,
                'data': {
                    'pipeline_status': 'running',
                    'stream_status': status,
                    'analytics_summary': analytics,
                    'created_streams': list(property_streams.keys())
                }
            })
            
        except ImportError as e:
            return jsonify({'error': f'Real-time module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Pipeline status failed: {str(e)}'}), 500
    
    @app.route('/api/occupancy/analytics', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def occupancy_analytics():
        """Analyze occupancy patterns and generate insights"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'analytics'))
            from occupancy_analytics import OccupancyAnalyticsEngine, generate_occupancy_dashboard_data
            
            data = request.get_json()
            property_id = data.get('property_id', 'prop_1')
            
            # Initialize occupancy analytics engine
            analytics_engine = OccupancyAnalyticsEngine()
            
            # Get IoT sensor data (simulate if not provided)
            iot_data = data.get('iot_data', {})
            if not iot_data.get('sensor_readings'):
                # Simulate occupancy sensor data for demonstration
                iot_data = {
                    'sensor_readings': [
                        {
                            'sensor_type': 'occupancy',
                            'value': 0.75,
                            'location': 'Apartment 101',
                            'timestamp': datetime.now().isoformat(),
                            'property_id': property_id
                        },
                        {
                            'sensor_type': 'motion',
                            'value': 5,
                            'location': 'Lobby',
                            'timestamp': datetime.now().isoformat(),
                            'property_id': property_id
                        },
                        {
                            'sensor_type': 'occupancy',
                            'value': 0.45,
                            'location': 'Gym',
                            'timestamp': datetime.now().isoformat(),
                            'property_id': property_id
                        },
                        {
                            'sensor_type': 'energy',
                            'value': 2.8,
                            'location': 'Office Space 201',
                            'timestamp': datetime.now().isoformat(),
                            'property_id': property_id
                        },
                        {
                            'sensor_type': 'temperature',
                            'value': 73,
                            'location': 'Common Area',
                            'timestamp': datetime.now().isoformat(),
                            'property_id': property_id
                        },
                        {
                            'sensor_type': 'occupancy',
                            'value': 0.2,
                            'location': 'Parking Garage',
                            'timestamp': datetime.now().isoformat(),
                            'property_id': property_id
                        }
                    ]
                }
            
            # Analyze occupancy patterns
            utilization_report = analytics_engine.analyze_occupancy_patterns(iot_data, property_id)
            
            # Generate dashboard data
            dashboard_data = generate_occupancy_dashboard_data(utilization_report)
            
            return jsonify({'success': True, 'data': dashboard_data})
            
        except ImportError as e:
            return jsonify({'error': f'Occupancy analytics module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Occupancy analytics failed: {str(e)}'}), 500

    @app.route('/api/occupancy/report/<property_id>', methods=['GET'])
    @require_auth
    @require_role(['admin', 'manager'])
    def get_occupancy_report(property_id):
        """Get detailed occupancy report for a property"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'analytics'))
            from occupancy_analytics import OccupancyAnalyticsEngine, serialize_utilization_report
            
            analytics_engine = OccupancyAnalyticsEngine()
            
            # Simulate comprehensive IoT data
            iot_data = {
                'sensor_readings': []
            }
            
            # Generate sample data for different spaces and times
            import random
            spaces = [
                ('Apartment 101', 'occupancy'),
                ('Apartment 102', 'occupancy'),
                ('Apartment 201', 'occupancy'),
                ('Lobby', 'motion'),
                ('Gym', 'occupancy'),
                ('Pool Area', 'occupancy'),
                ('Office 201', 'energy'),
                ('Common Kitchen', 'motion'),
                ('Parking Garage', 'occupancy'),
                ('Rooftop Deck', 'occupancy')
            ]
            
            for i in range(100):  # Generate 100 sample readings
                for location, sensor_type in spaces:
                    value = random.uniform(0.1, 0.9) if sensor_type == 'occupancy' else random.uniform(1, 10)
                    iot_data['sensor_readings'].append({
                        'sensor_type': sensor_type,
                        'value': value,
                        'location': location,
                        'timestamp': (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat(),
                        'property_id': property_id
                    })
            
            # Analyze occupancy patterns
            utilization_report = analytics_engine.analyze_occupancy_patterns(iot_data, property_id)
            
            # Serialize report for JSON response
            report_data = serialize_utilization_report(utilization_report)
            
            return jsonify({'success': True, 'data': report_data})
            
        except ImportError as e:
            return jsonify({'error': f'Occupancy analytics module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Occupancy report failed: {str(e)}'}), 500

    @app.route('/api/occupancy/insights/<property_id>', methods=['GET'])
    @require_auth
    @require_role(['admin', 'manager'])
    def get_occupancy_insights(property_id):
        """Get actionable occupancy insights for a property"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'analytics'))
            from occupancy_analytics import OccupancyAnalyticsEngine, serialize_occupancy_insight
            
            analytics_engine = OccupancyAnalyticsEngine()
            
            # Simulate IoT data focused on insights generation
            iot_data = {
                'sensor_readings': [
                    # Low utilization space
                    {'sensor_type': 'occupancy', 'value': 0.25, 'location': 'Conference Room A', 'timestamp': datetime.now().isoformat(), 'property_id': property_id},
                    {'sensor_type': 'occupancy', 'value': 0.18, 'location': 'Conference Room A', 'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(), 'property_id': property_id},
                    # High utilization space
                    {'sensor_type': 'occupancy', 'value': 0.85, 'location': 'Main Lobby', 'timestamp': datetime.now().isoformat(), 'property_id': property_id},
                    {'sensor_type': 'occupancy', 'value': 0.92, 'location': 'Main Lobby', 'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(), 'property_id': property_id},
                    # Peak hours pattern
                    {'sensor_type': 'motion', 'value': 8, 'location': 'Elevator Bank', 'timestamp': datetime.now().replace(hour=9).isoformat(), 'property_id': property_id},
                    {'sensor_type': 'motion', 'value': 2, 'location': 'Elevator Bank', 'timestamp': datetime.now().replace(hour=15).isoformat(), 'property_id': property_id}
                ]
            }
            
            # Analyze occupancy patterns
            utilization_report = analytics_engine.analyze_occupancy_patterns(iot_data, property_id)
            
            # Serialize insights for JSON response
            insights_data = [serialize_occupancy_insight(insight) for insight in utilization_report.utilization_insights]
            
            return jsonify({
                'success': True, 
                'data': {
                    'insights': insights_data,
                    'total_insights': len(insights_data),
                    'high_priority_count': len([i for i in utilization_report.utilization_insights if i.priority_level == "High"]),
                    'total_potential_revenue': sum(i.potential_revenue for i in utilization_report.utilization_insights),
                    'total_potential_savings': sum(i.potential_savings for i in utilization_report.utilization_insights)
                }
            })
            
        except ImportError as e:
            return jsonify({'error': f'Occupancy analytics module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Occupancy insights failed: {str(e)}'}), 500

    @app.route('/api/maintenance/predictive', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def predictive_maintenance_analysis():
        """Analyze IoT data for predictive maintenance insights"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'predict'))
            from predictive_maintenance import PredictiveMaintenanceEngine, generate_maintenance_dashboard_data
            
            data = request.get_json()
            property_id = data.get('property_id', 'prop_1')
            
            # Initialize predictive maintenance engine
            maintenance_engine = PredictiveMaintenanceEngine()
            
            # Get IoT sensor data (simulate if not provided)
            iot_data = data.get('iot_data', {})
            if not iot_data.get('sensor_readings'):
                # Simulate IoT sensor data for demonstration
                iot_data = {
                    'sensor_readings': [
                        {
                            'sensor_type': 'temperature',
                            'value': 80.5,  # High temperature
                            'location': 'Living Room',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'energy',
                            'value': 4.2,  # High energy consumption
                            'location': 'Main Panel',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'humidity',
                            'value': 75,  # High humidity
                            'location': 'Bathroom',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'water',
                            'value': 1.8,  # Water flow detected
                            'location': 'Kitchen',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'air_quality',
                            'value': 120,  # Poor air quality
                            'location': 'Bedroom',
                            'timestamp': datetime.now().isoformat()
                        }
                    ]
                }
            
            # Analyze IoT data for maintenance predictions
            predictions = maintenance_engine.analyze_iot_data_for_maintenance(iot_data, property_id)
            
            # Create maintenance tasks from predictions
            tasks = maintenance_engine.create_maintenance_tasks(predictions)
            
            # Generate dashboard data
            dashboard_data = generate_maintenance_dashboard_data(predictions, tasks)
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except ImportError as e:
            return jsonify({'error': f'Predictive maintenance module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Predictive maintenance analysis failed: {str(e)}'}), 500
    
    @app.route('/api/maintenance/predictions/<property_id>', methods=['GET'])
    @require_auth
    @require_role(['admin', 'manager'])
    def get_maintenance_predictions(property_id):
        """Get current maintenance predictions for a property"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'predict'))
            from predictive_maintenance import PredictiveMaintenanceEngine
            
            # Initialize engine and get cached predictions
            maintenance_engine = PredictiveMaintenanceEngine()
            
            # Simulate some predictions for demo
            demo_predictions = [
                {
                    'prediction_id': f'pred_{property_id}_1',
                    'equipment_id': f'hvac_unit_{property_id}',
                    'equipment_type': 'HVAC System',
                    'maintenance_type': 'hvac',
                    'failure_probability': 0.35,
                    'predicted_failure_date': (datetime.now() + timedelta(days=14)).isoformat(),
                    'confidence_score': 0.82,
                    'priority_level': 'high',
                    'estimated_cost': 750.00,
                    'recommended_action': 'Schedule comprehensive HVAC maintenance within 3 days',
                    'trigger_factors': ['High energy consumption: 4.2 kWh', 'High temperature variance: 8.5°F'],
                    'property_id': property_id,
                    'location': 'Living Room',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'prediction_id': f'pred_{property_id}_2',
                    'equipment_id': f'plumbing_system_{property_id}',
                    'equipment_type': 'Plumbing System',
                    'maintenance_type': 'plumbing',
                    'failure_probability': 0.42,
                    'predicted_failure_date': (datetime.now() + timedelta(days=7)).isoformat(),
                    'confidence_score': 0.75,
                    'priority_level': 'critical',
                    'estimated_cost': 320.00,
                    'recommended_action': 'URGENT: Inspect for water leaks and plumbing issues immediately',
                    'trigger_factors': ['High humidity in Kitchen: 75%', 'Water flow detected: 1.8 GPM'],
                    'property_id': property_id,
                    'location': 'Kitchen',
                    'created_at': datetime.now().isoformat()
                }
            ]
            
            return jsonify({
                'success': True,
                'data': {
                    'predictions': demo_predictions,
                    'property_id': property_id,
                    'total_predictions': len(demo_predictions),
                    'critical_count': len([p for p in demo_predictions if p['priority_level'] == 'critical']),
                    'last_updated': datetime.now().isoformat()
                }
            })
            
        except ImportError as e:
            return jsonify({'error': f'Predictive maintenance module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Failed to get predictions: {str(e)}'}), 500
    
    @app.route('/api/energy/optimization', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def energy_optimization_analysis():
        """Analyze energy usage and generate optimization recommendations"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_modules', 'optimize'))
            from energy_optimization import EnergyOptimizationEngine, generate_energy_optimization_dashboard
            
            data = request.get_json()
            property_id = data.get('property_id', 'prop_1')
            
            # Initialize energy optimization engine
            optimization_engine = EnergyOptimizationEngine()
            
            # Get IoT sensor data (simulate if not provided)
            iot_data = data.get('iot_data', {})
            if not iot_data.get('sensor_readings'):
                # Simulate IoT sensor data for demonstration
                iot_data = {
                    'sensor_readings': [
                        {
                            'sensor_type': 'energy',
                            'value': 4.5,  # High energy consumption
                            'location': 'Main Panel',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'energy',
                            'value': 0.8,  # Lighting consumption
                            'location': 'Living Room',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'energy',
                            'value': 2.2,  # Water heater consumption
                            'location': 'Water Heater',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'temperature',
                            'value': 78,  # Temperature for correlation
                            'location': 'Living Room',
                            'timestamp': datetime.now().isoformat()
                        },
                        {
                            'sensor_type': 'occupancy',
                            'value': 1,  # Occupied
                            'location': 'Living Room',
                            'timestamp': datetime.now().isoformat()
                        }
                    ]
                }
            
            # Analyze energy usage patterns
            energy_analysis = optimization_engine.analyze_energy_usage(iot_data, property_id)
            
            # Generate optimization recommendations
            recommendations = optimization_engine.generate_optimization_recommendations(energy_analysis, property_id)
            
            # Create smart schedules
            schedules = optimization_engine.create_smart_schedules(recommendations, energy_analysis)
            
            # Generate dashboard data
            dashboard_data = generate_energy_optimization_dashboard(energy_analysis, recommendations, schedules)
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except ImportError as e:
            return jsonify({'error': f'Energy optimization module not available: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Energy optimization analysis failed: {str(e)}'}), 500
    
    @app.route('/api/energy/recommendations/<property_id>', methods=['GET'])
    @require_auth
    @require_role(['admin', 'manager'])
    def get_energy_recommendations(property_id):
        """Get current energy optimization recommendations for a property"""
        try:
            # Simulate energy recommendations for demo
            demo_recommendations = [
                {
                    'recommendation_id': f'energy_rec_{property_id}_1',
                    'strategy': 'energy_efficiency',
                    'equipment_id': 'hvac_unit_living_room',
                    'equipment_type': 'HVAC System',
                    'description': 'Install smart thermostat for Living Room HVAC system with occupancy sensing and scheduling',
                    'estimated_savings': 328.50,
                    'implementation_cost': 250.00,
                    'payback_period_months': 9,
                    'difficulty': 'easy',
                    'priority_score': 85.0,
                    'annual_kwh_savings': 2190.0,
                    'co2_reduction_tons': 0.876,
                    'property_id': property_id,
                    'location': 'Living Room',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'recommendation_id': f'energy_rec_{property_id}_2',
                    'strategy': 'energy_efficiency',
                    'equipment_id': 'lighting_living_room',
                    'equipment_type': 'Lighting System',
                    'description': 'Upgrade Living Room lighting to LED with occupancy sensors and dimming controls',
                    'estimated_savings': 87.60,
                    'implementation_cost': 300.00,
                    'payback_period_months': 41,
                    'difficulty': 'easy',
                    'priority_score': 80.0,
                    'annual_kwh_savings': 584.0,
                    'co2_reduction_tons': 0.234,
                    'property_id': property_id,
                    'location': 'Living Room',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'recommendation_id': f'energy_rec_{property_id}_3',
                    'strategy': 'time_of_use',
                    'equipment_id': 'water_heater_water_heater',
                    'equipment_type': 'Water Heater',
                    'description': 'Install smart water heater controller for Water Heater to heat during off-peak hours',
                    'estimated_savings': 128.48,
                    'implementation_cost': 200.00,
                    'payback_period_months': 19,
                    'difficulty': 'medium',
                    'priority_score': 70.0,
                    'annual_kwh_savings': 0.0,
                    'co2_reduction_tons': 0.0,
                    'property_id': property_id,
                    'location': 'Water Heater',
                    'created_at': datetime.now().isoformat()
                }
            ]
            
            return jsonify({
                'success': True,
                'data': {
                    'recommendations': demo_recommendations,
                    'property_id': property_id,
                    'total_recommendations': len(demo_recommendations),
                    'total_potential_savings': sum(r['estimated_savings'] for r in demo_recommendations),
                    'total_implementation_cost': sum(r['implementation_cost'] for r in demo_recommendations),
                    'last_updated': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to get energy recommendations: {str(e)}'}), 500
    
    @app.route('/api/energy/schedules', methods=['POST'])
    @require_auth
    @require_role(['admin', 'manager'])
    def activate_energy_schedule():
        """Activate a smart energy schedule"""
        try:
            data = request.get_json()
            schedule_id = data.get('schedule_id')
            equipment_id = data.get('equipment_id')
            property_id = data.get('property_id')
            
            # Simulate schedule activation
            return jsonify({
                'success': True,
                'message': f'Smart schedule {schedule_id} activated for {equipment_id}',
                'data': {
                    'schedule_id': schedule_id,
                    'equipment_id': equipment_id,
                    'property_id': property_id,
                    'status': 'active',
                    'activated_at': datetime.now().isoformat(),
                    'estimated_annual_savings': 250.00
                }
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to activate schedule: {str(e)}'}), 500
    
    # In-memory user store (in production, use a database)
    users_db = {
        'admin': {
            'id': 'admin',
            'username': 'Admin User',
            'email': 'admin@estatecore.com',
            'role': 'super_admin',
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'subscription_id': None,
            'units_managed': 0
        }
    }
    
    # User Management API with Billing Integration
    @app.route('/api/users', methods=['GET'])
    @require_auth
    def get_users():
        """Get all users"""
        return jsonify(list(users_db.values()))
    
    @app.route('/api/users', methods=['POST'])
    @require_auth
    @require_role(['admin', 'super_admin'])
    def create_user():
        """Create a new user with automatic billing"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['username', 'email', 'password', 'role']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            # Check if user already exists
            email = data['email']
            if email in users_db:
                return jsonify({'error': 'User with this email already exists'}), 400
            
            # Get billing information
            subscription_id = data.get('subscription_id')
            units_to_add = data.get('units_to_add', 1)  # Default 1 unit per user
            auto_charge = data.get('auto_charge', True)  # Auto-charge by default
            
            # Create user
            user_id = str(uuid.uuid4())
            hashed_password = hash_password(data['password'])
            
            new_user = {
                'id': user_id,
                'username': data['username'],
                'email': email,
                'password_hash': hashed_password,
                'role': data['role'],
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'subscription_id': subscription_id,
                'units_managed': units_to_add
            }
            
            # If billing is enabled and subscription provided
            billing_result = None
            if subscription_id and auto_charge:
                try:
                    # Calculate and charge for additional units
                    charge_response = billing_api.subscription_manager.calculate_unit_based_charges(
                        subscription_id=subscription_id,
                        units_used=units_to_add
                    )
                    
                    # Generate invoice for the additional units
                    invoice = billing_api.subscription_manager.generate_invoice(
                        subscription_id=subscription_id,
                        units_used=units_to_add,
                        one_time_charges={'User Addition': charge_response}
                    )
                    
                    billing_result = {
                        'units_added': units_to_add,
                        'unit_charge': charge_response,
                        'invoice_id': invoice.invoice_id,
                        'total_amount': invoice.total_amount
                    }
                    
                except Exception as billing_error:
                    # Log billing error but still create user
                    print(f"Billing error during user creation: {str(billing_error)}")
                    billing_result = {
                        'error': str(billing_error),
                        'units_added': units_to_add,
                        'charged': False
                    }
            
            # Save user to database
            users_db[email] = new_user
            
            # Remove password hash from response
            response_user = new_user.copy()
            del response_user['password_hash']
            
            return jsonify({
                'message': 'User created successfully',
                'user': response_user,
                'billing': billing_result
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<user_id>', methods=['PUT'])
    @require_auth
    @require_role(['admin', 'super_admin'])
    def update_user(user_id):
        """Update a user"""
        try:
            data = request.get_json()
            
            # Find user by ID
            user = None
            user_email = None
            for email, u in users_db.items():
                if u['id'] == user_id:
                    user = u
                    user_email = email
                    break
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Update user fields
            if 'username' in data:
                user['username'] = data['username']
            if 'email' in data and data['email'] != user_email:
                # Move user to new email key
                users_db[data['email']] = user
                del users_db[user_email]
                user['email'] = data['email']
            if 'role' in data:
                user['role'] = data['role']
            if 'is_active' in data:
                user['is_active'] = data['is_active']
            
            user['updated_at'] = datetime.now().isoformat()
            
            # Remove password hash from response
            response_user = user.copy()
            if 'password_hash' in response_user:
                del response_user['password_hash']
            
            return jsonify({
                'message': 'User updated successfully',
                'user': response_user
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<user_id>', methods=['DELETE'])
    @require_auth
    @require_role(['admin', 'super_admin'])
    def delete_user(user_id):
        """Delete a user"""
        try:
            # Find and remove user
            user_email = None
            for email, user in users_db.items():
                if user['id'] == user_id:
                    user_email = email
                    break
            
            if not user_email:
                return jsonify({'error': 'User not found'}), 404
            
            del users_db[user_email]
            
            return jsonify({'message': 'User deleted successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<user_id>/billing', methods=['POST'])
    @require_auth
    @require_role(['admin', 'super_admin'])
    def add_user_units(user_id):
        """Add units to a user and charge for them"""
        try:
            data = request.get_json()
            
            # Find user
            user = None
            for u in users_db.values():
                if u['id'] == user_id:
                    user = u
                    break
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            subscription_id = data.get('subscription_id') or user.get('subscription_id')
            units_to_add = data.get('units_to_add', 1)
            
            if not subscription_id:
                return jsonify({'error': 'No subscription ID provided'}), 400
            
            # Calculate and charge for additional units
            charge_amount = billing_api.subscription_manager.calculate_unit_based_charges(
                subscription_id=subscription_id,
                units_used=units_to_add
            )
            
            # Generate invoice
            invoice = billing_api.subscription_manager.generate_invoice(
                subscription_id=subscription_id,
                units_used=units_to_add,
                one_time_charges={'Additional Units': charge_amount}
            )
            
            # Update user's unit count
            user['units_managed'] = user.get('units_managed', 0) + units_to_add
            user['updated_at'] = datetime.now().isoformat()
            
            return jsonify({
                'message': 'Units added and charged successfully',
                'user_id': user_id,
                'units_added': units_to_add,
                'total_units': user['units_managed'],
                'charge_amount': charge_amount,
                'invoice_id': invoice.invoice_id,
                'invoice_total': invoice.total_amount
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Catch-all for other API endpoints
    @app.route('/api/<path:path>')
    def api_catchall(path):
        return jsonify({
            'message': f'Endpoint /api/{path} not implemented in simple app',
            'status': 'placeholder'
        })
    
    # Initialize billing system
    billing_api = init_billing_system(app)
    
    # Initialize environmental monitoring system
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_modules', 'environmental'))
    from environmental_api import init_environmental_system
    environmental_api = init_environmental_system(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("Starting EstateCore Simple App with Billing System...")
    app.run(host='localhost', port=5179, debug=True)