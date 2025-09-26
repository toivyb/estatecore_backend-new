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
from dotenv import load_dotenv
from email_service import EmailService, create_email_service
from sms_service import SMSService, create_sms_service
from database_service import get_database_service
from file_storage_service import FileStorageService, create_file_storage_service
from permissions_service import (
    get_permission_service, require_permission, require_role, 
    Permission, Role, load_user_permissions, get_user_role_info, has_permission
)
from rent_collection_service import get_rent_collection_service, PaymentMethod, PaymentStatus
from lease_management_service import get_lease_management_service, LeaseStatus, RenewalStatus, LeaseType
from financial_reporting_service import get_financial_reporting_service, ReportType, ReportPeriod
from security_service import get_security_service, SecurityEventType, ThreatLevel, require_valid_session, require_api_key, rate_limited
from maintenance_scheduling_service import get_maintenance_service, MaintenanceType, MaintenanceStatus, Priority
from tenant_screening_service import get_tenant_screening_service, ApplicationStatus, ScreeningType, DecisionStatus
from bulk_operations_service import get_bulk_operations_service, OperationType, OperationStatus, EntityType
from performance_service import get_performance_service, cached, monitored
from rate_limiting_service import get_rate_limiting_service, rate_limit, RateLimitConfig, RateLimitAlgorithm, RateLimitScope

# Import billing system
sys.path.append(os.path.join(os.path.dirname(__file__), 'billing_system'))
from billing_api import init_billing_system
from enhanced_lpr_service import get_enhanced_lpr_service, LPRCamera, VehicleRecord, CameraType, LPRProvider, VehicleStatus

# Load environment variables
load_dotenv()

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
    
    # CORS Configuration - Allow all origins for development
    # cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    # print(f"CORS Origins: {cors_origins}")  # Debug print
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins="*", supports_credentials=False, allow_headers=['Content-Type', 'Authorization'])
    
    # Initialize rate limiting service
    rate_limiting_service = get_rate_limiting_service()
    
    # Configure rate limits for different endpoints
    rate_limiting_service.configure_endpoint('/api/auth/login', RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        algorithm=RateLimitAlgorithm.FIXED_WINDOW,
        scope=RateLimitScope.PER_IP
    ))
    
    rate_limiting_service.configure_endpoint('/api/bulk-operations/import', RateLimitConfig(
        requests_per_minute=2,
        requests_per_hour=20,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        scope=RateLimitScope.PER_USER
    ))
    
    rate_limiting_service.configure_endpoint('/api/files/upload', RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        scope=RateLimitScope.PER_USER
    ))
    
    # Add manual CORS headers as fallback
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'false'
        return response

    # Register Yardi Integration Blueprint
    try:
        from yardi_integration.yardi_routes import yardi_bp
        app.register_blueprint(yardi_bp)
        print("Yardi Integration routes registered successfully")
    except ImportError as e:
        print(f"Yardi Integration not available: {e}")
    except Exception as e:
        print(f"Failed to register Yardi Integration routes: {e}")

    # Register Compliance API Blueprint
    try:
        from routes.compliance_api import compliance_bp
        app.register_blueprint(compliance_bp)
        print("Compliance API routes registered successfully")
        
        # Initialize compliance system
        from services.compliance_service import get_compliance_orchestrator
        compliance_orchestrator = get_compliance_orchestrator()
        print("Compliance system initialized")
    except ImportError as e:
        print(f"Compliance API not available: {e}")
    
    # Initialize SaaS Billing System
    try:
        billing_api = init_billing_system(app)
        print("SaaS Billing System initialized successfully")
        
        # Store billing API reference for use in endpoints
        app.billing_api = billing_api
    except ImportError as e:
        print(f"Billing System not available: {e}")
    except Exception as e:
        print(f"Failed to initialize Billing System: {e}")
    
    # Initialize Energy Management Service Directly
    try:
        # Add paths for energy management
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_modules'))
        sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))
        
        from services.energy_management_service import get_energy_management_service
        energy_service = get_energy_management_service()
        print("Energy Management service initialized successfully")
        
        # Store service reference for use in endpoints
        app.energy_service = energy_service
    except ImportError as e:
        print(f"Energy Management service not available: {e}")
    except Exception as e:
        print(f"Failed to initialize Energy Management service: {e}")

    # Authentication and Permission Middleware
    @app.before_request
    def load_user_context():
        """Load user context for permission checking"""
        from flask import g
        
        # Skip auth for public endpoints
        public_endpoints = ['/health', '/', '/api/test-cors', '/api/auth/login', '/api/auth/register']
        if request.endpoint in public_endpoints or request.path in public_endpoints:
            return
        
        # Skip auth for OPTIONS requests
        if request.method == 'OPTIONS':
            return
            
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # In production, validate JWT token here
            # For now, we'll use a simple user ID extraction
            try:
                # Mock token parsing - in production use proper JWT validation
                if token == 'admin_token':
                    g.user_id = 1
                    g.user_role = 'super_admin'
                elif token == 'manager_token':
                    g.user_id = 2
                    g.user_role = 'property_manager'
                elif token == 'tenant_token':
                    g.user_id = 3
                    g.user_role = 'tenant'
                else:
                    # Try to parse as simple user_id for development
                    g.user_id = int(token) if token.isdigit() else None
                    g.user_role = 'property_manager'  # Default for development
                
                # Load user permissions if user is authenticated
                if hasattr(g, 'user_id') and g.user_id:
                    load_user_permissions(
                        user_id=g.user_id,
                        role_name=g.user_role,
                        property_access=[1, 2, 3] if g.user_role != 'tenant' else [1],
                        tenant_access=[g.user_id] if g.user_role == 'tenant' else []
                    )
                    
            except (ValueError, AttributeError):
                g.user_id = None
                g.user_role = None
        else:
            g.user_id = None
            g.user_role = None

    # Add explicit OPTIONS handlers for common routes
    @app.route('/api/lpr/companies', methods=['OPTIONS'])
    def options_lpr_companies():
        return '', 200

    @app.route('/api/invites/send-enhanced', methods=['OPTIONS']) 
    def options_invites():
        return '', 200

    @app.route('/api/test-cors', methods=['GET'])
    def test_cors():
        response = jsonify({'message': 'CORS test successful', 'timestamp': datetime.utcnow().isoformat()})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        return response
    
    # Health check routes
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'EstateCore Backend', 'version': 'emergency-2.0', 'fixed': True, 'deployed': datetime.utcnow().isoformat()})
    
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
                    WHERE table_name = 'payments' AND (table_schema = 'public' OR table_schema IS NULL)
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
            
            response_data = {
                'total_properties': total_properties or 0,
                'available_properties': available_properties or 0,
                'occupied_properties': (total_properties or 0) - (available_properties or 0),
                'total_users': total_users or 0,
                'total_payments': total_payments or 0,
                'total_revenue': float(completed_revenue) if completed_revenue else 0,
                'pending_revenue': float(pending_revenue) if pending_revenue else 0,
                'recent_properties': []
            }
            
            return jsonify(response_data)
        except Exception as e:
            print(f"Dashboard error: {str(e)}")
            # Return a safe fallback response
            return jsonify({
                'total_properties': 0,
                'available_properties': 0,
                'occupied_properties': 0,
                'total_users': 0,
                'total_payments': 0,
                'total_revenue': 0,
                'pending_revenue': 0,
                'recent_properties': [],
                'error': 'Dashboard temporarily unavailable'
            })
    
    # AI Analytics Endpoints - Lease Management
    @app.route('/api/ai/lease-expiration-check', methods=['GET'])
    def get_lease_expiration_check():
        try:
            # Check if leases table exists and get lease data
            leases_exist = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'leases' AND (table_schema = 'public' OR table_schema IS NULL)
                )
            """)).scalar()
            
            expiring_soon = []
            expired = []
            alerts = ['Lease tracking system ready']
            
            if leases_exist:
                # Get leases expiring in next 30 days
                expiring_leases = db.session.execute(db.text("""
                    SELECT id, tenant_id, start_date, end_date 
                    FROM leases 
                    WHERE end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
                    AND (is_active = true OR is_active IS NULL)
                """)).fetchall()
                
                for lease in expiring_leases:
                    expiring_soon.append({
                        'lease_id': lease[0],
                        'tenant_id': lease[1],
                        'end_date': lease[3].isoformat() if lease[3] else None
                    })
                
                # Get expired leases
                expired_leases = db.session.execute(db.text("""
                    SELECT id, tenant_id, start_date, end_date 
                    FROM leases 
                    WHERE end_date < CURRENT_DATE
                    AND (is_active = true OR is_active IS NULL)
                """)).fetchall()
                
                for lease in expired_leases:
                    expired.append({
                        'lease_id': lease[0],
                        'tenant_id': lease[1],
                        'end_date': lease[3].isoformat() if lease[3] else None
                    })
                
                if expiring_soon:
                    alerts.append(f'{len(expiring_soon)} leases expiring within 30 days')
                if expired:
                    alerts.append(f'{len(expired)} leases have expired')
            
            return jsonify({
                'expiring_soon': expiring_soon,
                'expired': expired,
                'alerts': alerts
            })
        except Exception as e:
            print(f"Lease expiration check error: {str(e)}")
            return jsonify({
                'expiring_soon': [],
                'expired': [],
                'alerts': ['Lease tracking temporarily unavailable'],
                'error': 'Service temporarily unavailable'
            })
    
    @app.route('/api/ai/process-lease', methods=['POST'])
    def process_lease():
        """Process lease document with AI (mock implementation)"""
        try:
            data = request.json
            
            # Mock AI processing - in a real implementation, this would use OCR and NLP
            # to extract lease information from the document
            
            lease_content = data.get('lease_content', '')
            filename = data.get('filename', 'unknown.pdf')
            tenant_id = data.get('tenant_id')
            
            # Mock extracted data - in real implementation, this would be parsed from the document
            parsed_data = {
                'tenant_name': 'Extracted from document',
                'property_address': 'Extracted address',
                'lease_start_date': '2024-01-01',
                'lease_end_date': '2024-12-31',
                'monthly_rent': 1200.00,
                'security_deposit': 1200.00,
                'pet_policy': 'No pets allowed',
                'lease_terms': 'Standard 12-month lease',
                'extracted_text': f'Processed content from {filename}',
                'confidence_score': 0.95
            }
            
            # Store processing result if tenant_id provided
            if tenant_id:
                # In a real implementation, you might store this in a lease_documents table
                print(f"Processed lease for tenant {tenant_id}: {parsed_data}")
            
            return jsonify({
                'success': True,
                'parsed_data': parsed_data,
                'message': 'Lease document processed successfully',
                'filename': filename
            })
            
        except Exception as e:
            print(f"Lease processing error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to process lease document',
                'parsed_data': None
            }), 500
    
    # Properties API - Direct SQL
    @app.route('/api/properties', methods=['GET', 'POST'])
    def handle_properties():
        if request.method == 'GET':
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
        
        elif request.method == 'POST':
            try:
                data = request.json
                
                # Validate required fields
                required_fields = ['name', 'address', 'type']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                # Parse address to get city, state, zip if possible
                address_parts = data['address'].split(',')
                street_address = address_parts[0].strip() if address_parts else data['address']
                city = address_parts[1].strip() if len(address_parts) > 1 else 'Unknown'
                state = address_parts[2].strip() if len(address_parts) > 2 else 'Unknown'
                zip_code = '00000'  # Default zip code
                
                # Insert new property with all required fields
                result = db.session.execute(db.text("""
                    INSERT INTO properties (
                        organization_id, name, street_address, city, state, zip_code, 
                        property_type, description, total_units, is_active, 
                        created_at, updated_at, is_deleted
                    ) VALUES (
                        :organization_id, :name, :street_address, :city, :state, :zip_code,
                        :type, :description, :units, :is_active, 
                        :created_at, :updated_at, :is_deleted
                    ) RETURNING id
                """), {
                    'organization_id': 1,  # Default organization ID
                    'name': data['name'],
                    'street_address': street_address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                    'type': data['type'].upper(),
                    'description': data.get('description', ''),
                    'units': int(data.get('units', 1)),
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'is_deleted': False
                })
                
                property_id = result.fetchone()[0]
                db.session.commit()
                
                return jsonify({
                    'message': 'Property created successfully',
                    'id': property_id,
                    'name': data['name']
                }), 201
                
            except Exception as e:
                db.session.rollback()
                print(f"Property creation error: {str(e)}")
                return jsonify({'error': 'Failed to create property'}), 500

    @app.route('/api/properties/<int:property_id>', methods=['PUT'])
    def update_property(property_id):
        """Update an existing property"""
        try:
            data = request.json
            
            # Update property
            db.session.execute(db.text("""
                UPDATE properties 
                SET name = :name, street_address = :address, property_type = :type,
                    description = :description, total_units = :units
                WHERE id = :property_id AND (is_deleted = false OR is_deleted IS NULL)
            """), {
                'property_id': property_id,
                'name': data['name'],
                'address': data['address'],
                'type': data['type'],
                'description': data.get('description', ''),
                'units': int(data.get('units', 1))
            })
            
            db.session.commit()
            
            return jsonify({
                'message': 'Property updated successfully',
                'id': property_id
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Property update error: {str(e)}")
            return jsonify({'error': 'Failed to update property'}), 500

    @app.route('/api/properties/<int:property_id>', methods=['DELETE'])
    def delete_property(property_id):
        """Delete a property (soft delete)"""
        try:
            # Soft delete by setting is_deleted flag
            db.session.execute(db.text("""
                UPDATE properties 
                SET is_deleted = true 
                WHERE id = :property_id
            """), {'property_id': property_id})
            
            db.session.commit()
            
            return jsonify({
                'message': 'Property deleted successfully',
                'id': property_id
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Property deletion error: {str(e)}")
            return jsonify({'error': 'Failed to delete property'}), 500
    
    # Units API - Direct SQL
    @app.route('/api/units', methods=['GET', 'POST'])
    def handle_units():
        if request.method == 'GET':
            try:
                property_id = request.args.get('property_id')
                if property_id:
                    # Get units for specific property
                    result = db.session.execute(db.text("""
                        SELECT id, property_id, unit_number, floor_number, bedrooms, bathrooms, 
                               sqft, base_rent, security_deposit, status, is_occupied, available_date
                        FROM units 
                        WHERE property_id = :property_id AND (is_deleted = false OR is_deleted IS NULL)
                        ORDER BY unit_number
                    """), {'property_id': property_id}).fetchall()
                else:
                    # Get all units
                    result = db.session.execute(db.text("""
                        SELECT id, property_id, unit_number, floor_number, bedrooms, bathrooms, 
                               sqft, base_rent, security_deposit, status, is_occupied, available_date
                        FROM units 
                        WHERE is_deleted = false OR is_deleted IS NULL
                        ORDER BY property_id, unit_number
                    """)).fetchall()
                
                units_list = []
                for row in result:
                    units_list.append({
                        'id': row[0],
                        'property_id': row[1],
                        'unit_number': row[2],
                        'floor_number': row[3],
                        'bedrooms': row[4] or 0,
                        'bathrooms': row[5] or 0,
                        'square_feet': row[6],
                        'rent': float(row[7]) if row[7] else 0,
                        'security_deposit': float(row[8]) if row[8] else 0,
                        'status': row[9] or 'available',
                        'is_available': not row[10] if row[10] is not None else True,
                        'available_date': row[11].isoformat() if row[11] else None
                    })
                return jsonify(units_list)
            except Exception as e:
                print(f"Units GET error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.json
                
                # Validate required fields
                required_fields = ['property_id', 'unit_number', 'rent']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                # Insert new unit
                result = db.session.execute(db.text("""
                    INSERT INTO units (
                        property_id, unit_number, floor_number, bedrooms, bathrooms, 
                        sqft, base_rent, security_deposit, status, is_occupied,
                        created_at, updated_at, is_deleted
                    ) VALUES (
                        :property_id, :unit_number, :floor_number, :bedrooms, :bathrooms,
                        :sqft, :base_rent, :security_deposit, :status, :is_occupied,
                        :created_at, :updated_at, :is_deleted
                    ) RETURNING id
                """), {
                    'property_id': int(data['property_id']),
                    'unit_number': data['unit_number'],
                    'floor_number': data.get('floor_number'),
                    'bedrooms': int(data.get('bedrooms', 0)),
                    'bathrooms': float(data.get('bathrooms', 0)),
                    'sqft': int(data.get('square_feet', 0)) if data.get('square_feet') else None,
                    'base_rent': float(data['rent']),
                    'security_deposit': float(data.get('security_deposit', 0)),
                    'status': 'VACANT',  # Default status
                    'is_occupied': False,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'is_deleted': False
                })
                
                unit_id = result.fetchone()[0]
                db.session.commit()
                
                return jsonify({
                    'message': 'Unit created successfully',
                    'id': unit_id,
                    'unit_number': data['unit_number']
                }), 201
                
            except Exception as e:
                db.session.rollback()
                print(f"Unit creation error: {str(e)}")
                return jsonify({'error': 'Failed to create unit'}), 500
    
    @app.route('/api/units/<int:unit_id>', methods=['PUT', 'DELETE'])
    def handle_unit(unit_id):
        if request.method == 'PUT':
            try:
                data = request.json
                
                # Update unit
                db.session.execute(db.text("""
                    UPDATE units 
                    SET unit_number = :unit_number, floor_number = :floor_number, 
                        bedrooms = :bedrooms, bathrooms = :bathrooms, sqft = :sqft,
                        base_rent = :base_rent, security_deposit = :security_deposit,
                        updated_at = :updated_at
                    WHERE id = :unit_id AND (is_deleted = false OR is_deleted IS NULL)
                """), {
                    'unit_id': unit_id,
                    'unit_number': data.get('unit_number'),
                    'floor_number': data.get('floor_number'),
                    'bedrooms': int(data.get('bedrooms', 0)),
                    'bathrooms': float(data.get('bathrooms', 0)),
                    'sqft': int(data.get('square_feet', 0)) if data.get('square_feet') else None,
                    'base_rent': float(data.get('rent', 0)),
                    'security_deposit': float(data.get('security_deposit', 0)),
                    'updated_at': datetime.utcnow()
                })
                
                db.session.commit()
                return jsonify({'message': 'Unit updated successfully'})
                
            except Exception as e:
                db.session.rollback()
                print(f"Unit update error: {str(e)}")
                return jsonify({'error': 'Failed to update unit'}), 500
        
        elif request.method == 'DELETE':
            try:
                # Soft delete unit
                db.session.execute(db.text("""
                    UPDATE units 
                    SET is_deleted = true, deleted_at = :deleted_at, updated_at = :updated_at
                    WHERE id = :unit_id
                """), {
                    'unit_id': unit_id,
                    'deleted_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                
                db.session.commit()
                return jsonify({'message': 'Unit deleted successfully'})
                
            except Exception as e:
                db.session.rollback()
                print(f"Unit deletion error: {str(e)}")
                return jsonify({'error': 'Failed to delete unit'}), 500
    
    # Tenants API - Direct SQL
    @app.route('/api/tenants', methods=['GET', 'POST'])
    def handle_tenants():
        if request.method == 'GET':
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
        
        elif request.method == 'POST':
            try:
                data = request.json
                
                # Validate required fields
                required_fields = ['user_id', 'property_id', 'unit_id', 'lease_start', 'lease_end', 'rent_amount']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                # Get user info from user_id
                user_info = db.session.execute(db.text("""
                    SELECT first_name, last_name, email, phone 
                    FROM users WHERE id = :user_id
                """), {'user_id': data['user_id']}).fetchone()
                
                if not user_info:
                    return jsonify({'error': 'User not found'}), 404
                
                # Insert new tenant
                result = db.session.execute(db.text("""
                    INSERT INTO tenants (
                        organization_id, first_name, last_name, email, phone,
                        monthly_income, is_active, move_in_date, move_out_date,
                        created_at, updated_at, is_deleted
                    ) VALUES (
                        :organization_id, :first_name, :last_name, :email, :phone,
                        :monthly_income, :is_active, :move_in_date, :move_out_date,
                        :created_at, :updated_at, :is_deleted
                    ) RETURNING id
                """), {
                    'organization_id': 1,  # Default organization
                    'first_name': user_info[0],
                    'last_name': user_info[1],
                    'email': user_info[2],
                    'phone': user_info[3] or '',
                    'monthly_income': data.get('monthly_income', 0),
                    'is_active': True,
                    'move_in_date': datetime.strptime(data['lease_start'], '%Y-%m-%d').date(),
                    'move_out_date': datetime.strptime(data['lease_end'], '%Y-%m-%d').date() if data.get('lease_end') else None,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'is_deleted': False
                })
                
                tenant_id = result.fetchone()[0]
                db.session.commit()
                
                return jsonify({
                    'message': 'Tenant created successfully',
                    'id': tenant_id,
                    'user_id': data['user_id']
                }), 201
                
            except Exception as e:
                db.session.rollback()
                print(f"Tenant creation error: {str(e)}")
                return jsonify({'error': 'Failed to create tenant'}), 500
    
    @app.route('/api/tenants/<int:tenant_id>', methods=['PUT', 'DELETE'])
    def handle_tenant(tenant_id):
        if request.method == 'PUT':
            try:
                data = request.json
                
                # Update tenant
                db.session.execute(db.text("""
                    UPDATE tenants 
                    SET first_name = :first_name, last_name = :last_name, 
                        email = :email, phone = :phone, monthly_income = :monthly_income,
                        move_in_date = :move_in_date, move_out_date = :move_out_date,
                        is_active = :is_active, updated_at = :updated_at
                    WHERE id = :tenant_id AND (is_deleted = false OR is_deleted IS NULL)
                """), {
                    'tenant_id': tenant_id,
                    'first_name': data.get('first_name', ''),
                    'last_name': data.get('last_name', ''),
                    'email': data.get('email', ''),
                    'phone': data.get('phone', ''),
                    'monthly_income': data.get('monthly_income', 0),
                    'move_in_date': datetime.strptime(data['lease_start'], '%Y-%m-%d').date() if data.get('lease_start') else None,
                    'move_out_date': datetime.strptime(data['lease_end'], '%Y-%m-%d').date() if data.get('lease_end') else None,
                    'is_active': data.get('status') == 'active',
                    'updated_at': datetime.utcnow()
                })
                
                db.session.commit()
                return jsonify({'message': 'Tenant updated successfully'})
                
            except Exception as e:
                db.session.rollback()
                print(f"Tenant update error: {str(e)}")
                return jsonify({'error': 'Failed to update tenant'}), 500
        
        elif request.method == 'DELETE':
            try:
                # Soft delete tenant
                db.session.execute(db.text("""
                    UPDATE tenants 
                    SET is_deleted = true, deleted_at = :deleted_at, updated_at = :updated_at
                    WHERE id = :tenant_id
                """), {
                    'tenant_id': tenant_id,
                    'deleted_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                
                db.session.commit()
                return jsonify({'message': 'Tenant deleted successfully'})
                
            except Exception as e:
                db.session.rollback()
                print(f"Tenant deletion error: {str(e)}")
                return jsonify({'error': 'Failed to delete tenant'}), 500
    
    # Users API - Direct SQL
    @app.route('/api/users', methods=['GET', 'POST'])
    def handle_users():
        if request.method == 'GET':
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
        
        elif request.method == 'POST':
            try:
                data = request.json
                
                # Validate required fields
                required_fields = ['email', 'username', 'password']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                # Split username into first and last name
                username_parts = data['username'].split(' ', 1)
                first_name = username_parts[0]
                last_name = username_parts[1] if len(username_parts) > 1 else ''
                
                # Hash password (simple hash for now)
                import hashlib
                password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
                
                # Insert new user
                result = db.session.execute(db.text("""
                    INSERT INTO users (
                        organization_id, email, password_hash, first_name, last_name, 
                        phone, role, is_active, is_verified, login_attempts,
                        email_notifications_enabled, sms_notifications_enabled,
                        created_at, updated_at, is_deleted, is_temporary_password,
                        password_change_required, two_factor_enabled,
                        login_notification_enabled, suspicious_activity_alerts,
                        property_management_access, lpr_management_access
                    ) VALUES (
                        :organization_id, :email, :password_hash, :first_name, :last_name,
                        :phone, :role, :is_active, :is_verified, :login_attempts,
                        :email_notifications_enabled, :sms_notifications_enabled,
                        :created_at, :updated_at, :is_deleted, :is_temporary_password,
                        :password_change_required, :two_factor_enabled,
                        :login_notification_enabled, :suspicious_activity_alerts,
                        :property_management_access, :lpr_management_access
                    ) RETURNING id
                """), {
                    'organization_id': 1,  # Default organization
                    'email': data['email'],
                    'password_hash': password_hash,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': data.get('phone', ''),
                    'role': data.get('role', 'tenant'),
                    'is_active': True,
                    'is_verified': True,
                    'login_attempts': 0,
                    'email_notifications_enabled': True,
                    'sms_notifications_enabled': False,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'is_deleted': False,
                    'is_temporary_password': True,
                    'password_change_required': True,
                    'two_factor_enabled': False,
                    'login_notification_enabled': True,
                    'suspicious_activity_alerts': True,
                    'property_management_access': data.get('role') == 'admin',
                    'lpr_management_access': False
                })
                
                user_id = result.fetchone()[0]
                db.session.commit()
                
                # Initialize response
                response_data = {
                    'message': 'User created successfully',
                    'id': user_id,
                    'email': data['email']
                }
                
                # SaaS Billing Integration
                try:
                    if hasattr(app, 'billing_api') and data.get('subscription_id') and data.get('auto_charge'):
                        from billing_system.subscription_manager import SubscriptionTier, BillingCycle
                        
                        # Get billing parameters from request
                        subscription_id = data.get('subscription_id')
                        units_to_add = int(data.get('units_to_add', 1))
                        
                        # Create subscription if it doesn't exist
                        if subscription_id == 'new':
                            # Create new subscription
                            subscription = app.billing_api.subscription_manager.create_subscription(
                                customer_id=str(user_id),
                                company_name=data.get('username', data['email']),
                                tier=SubscriptionTier.PROFESSIONAL,
                                billing_cycle=BillingCycle.MONTHLY,
                                trial_days=14
                            )
                            subscription_id = subscription.subscription_id
                        
                        # Generate invoice for units
                        invoice = app.billing_api.subscription_manager.generate_invoice(
                            subscription_id=subscription_id,
                            units_used=units_to_add,
                            tax_rate=0.0,
                            discount_amount=0.0,
                            one_time_charges={}
                        )
                        
                        # Process payment if auto_charge is enabled
                        if data.get('auto_charge'):
                            # In a real implementation, you'd process the payment here
                            # For now, we'll just return the billing information
                            pass
                        
                        # Add billing information to response
                        response_data['billing'] = {
                            'subscription_id': subscription_id,
                            'units_added': units_to_add,
                            'unit_price': 2.50,
                            'total_amount': units_to_add * 2.50,
                            'invoice_id': invoice.invoice_id,
                            'invoice_number': invoice.invoice_number
                        }
                        
                except Exception as billing_error:
                    print(f"Billing integration error: {str(billing_error)}")
                    response_data['billing'] = {'error': str(billing_error)}
                
                return jsonify(response_data), 201
                
            except Exception as e:
                db.session.rollback()
                print(f"User creation error: {str(e)}")
                return jsonify({'error': 'Failed to create user'}), 500
    
    @app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
    def handle_user(user_id):
        if request.method == 'PUT':
            try:
                data = request.json
                
                # Split username into first and last name if provided
                if data.get('username'):
                    username_parts = data['username'].split(' ', 1)
                    first_name = username_parts[0]
                    last_name = username_parts[1] if len(username_parts) > 1 else ''
                else:
                    first_name = data.get('first_name', '')
                    last_name = data.get('last_name', '')
                
                # Update user
                db.session.execute(db.text("""
                    UPDATE users 
                    SET first_name = :first_name, last_name = :last_name, 
                        email = :email, phone = :phone, role = :role,
                        is_active = :is_active, updated_at = :updated_at
                    WHERE id = :user_id AND (is_deleted = false OR is_deleted IS NULL)
                """), {
                    'user_id': user_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': data.get('email', ''),
                    'phone': data.get('phone', ''),
                    'role': data.get('role', 'tenant'),
                    'is_active': data.get('is_active', True),
                    'updated_at': datetime.utcnow()
                })
                
                db.session.commit()
                return jsonify({'message': 'User updated successfully'})
                
            except Exception as e:
                db.session.rollback()
                print(f"User update error: {str(e)}")
                return jsonify({'error': 'Failed to update user'}), 500
        
        elif request.method == 'DELETE':
            try:
                # Soft delete user
                db.session.execute(db.text("""
                    UPDATE users 
                    SET is_deleted = true, deleted_at = :deleted_at, updated_at = :updated_at
                    WHERE id = :user_id
                """), {
                    'user_id': user_id,
                    'deleted_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                
                db.session.commit()
                return jsonify({'message': 'User deleted successfully'})
                
            except Exception as e:
                db.session.rollback()
                print(f"User deletion error: {str(e)}")
                return jsonify({'error': 'Failed to delete user'}), 500
    
    # Maintenance API - Direct SQL
    @app.route('/api/maintenance', methods=['GET', 'POST'])
    def handle_maintenance():
        if request.method == 'GET':
            try:
                # Direct SQL query for maintenance requests
                result = db.session.execute(db.text("""
                    SELECT id, property_id, tenant_id, title, description, priority, status, created_at
                    FROM maintenance_requests 
                    ORDER BY created_at DESC
                    LIMIT 50
                """)).fetchall()
                
                maintenance_list = []
                for row in result:
                    maintenance_list.append({
                        'id': row[0],
                        'property_id': row[1],
                        'tenant_id': row[2],
                        'title': row[3],
                        'description': row[4],
                        'priority': row[5],
                        'status': row[6],
                        'created_at': row[7].isoformat() if row[7] else None
                    })
                return jsonify(maintenance_list)
            except Exception as e:
                # If table doesn't exist, return empty list
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                
                # Validate required fields - property_id and title are required
                if not data.get('property_id'):
                    return jsonify({'error': 'property_id is required'}), 400
                if not data.get('title'):
                    return jsonify({'error': 'title is required'}), 400
                
                # Mock maintenance request creation (table may not exist)
                return jsonify({
                    'message': 'Maintenance request created successfully',
                    'id': 1,  # Mock ID
                    'title': data['title']
                }), 201
                
            except Exception as e:
                print(f"Maintenance creation error: {str(e)}")
                return jsonify({'error': 'Failed to create maintenance request'}), 500
    
    @app.route('/api/maintenance/<int:maintenance_id>', methods=['PUT', 'DELETE'])
    def handle_maintenance_item(maintenance_id):
        if request.method == 'PUT':
            try:
                data = request.json
                # Mock maintenance update
                return jsonify({'message': 'Maintenance request updated successfully'})
            except Exception as e:
                return jsonify({'error': 'Failed to update maintenance request'}), 500
        
        elif request.method == 'DELETE':
            try:
                # Mock maintenance deletion
                return jsonify({'message': 'Maintenance request deleted successfully'})
            except Exception as e:
                return jsonify({'error': 'Failed to delete maintenance request'}), 500
    
    @app.route('/api/documents', methods=['GET', 'POST'])
    def handle_documents():
        if request.method == 'GET':
            try:
                # Mock documents list
                documents = [
                    {
                        'id': 1,
                        'name': 'Sample Lease Agreement.pdf',
                        'type': 'lease',
                        'property_id': 1,
                        'uploaded_date': datetime.utcnow().isoformat(),
                        'file_size': '2.3 MB'
                    },
                    {
                        'id': 2,
                        'name': 'Property Insurance.pdf',
                        'type': 'insurance',
                        'property_id': 1,
                        'uploaded_date': datetime.utcnow().isoformat(),
                        'file_size': '1.8 MB'
                    }
                ]
                return jsonify(documents)
            except Exception as e:
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                # Mock document upload
                return jsonify({
                    'message': 'Document uploaded successfully',
                    'id': 3,
                    'name': data.get('name', 'unknown.pdf')
                }), 201
            except Exception as e:
                return jsonify({'error': 'Failed to upload document'}), 500
    
    # Rent and Payment Endpoints
    @app.route('/api/rent/metrics', methods=['GET'])
    def get_rent_metrics():
        try:
            month = request.args.get('month', datetime.now().strftime('%Y-%m'))
            
            # Mock rent metrics data
            metrics = {
                'total_rent': 15000.00,
                'collected': 12000.00,
                'pending': 3000.00,
                'net': 12000.00,
                'month': month,
                'properties': [
                    {'id': 1, 'name': 'Property 1', 'rent': 5000, 'collected': 4000},
                    {'id': 2, 'name': 'Property 2', 'rent': 10000, 'collected': 8000}
                ]
            }
            return jsonify(metrics)
        except Exception as e:
            return jsonify({'error': 'Failed to fetch rent metrics'}), 500
    
    @app.route('/api/payments', methods=['GET', 'POST'])
    def handle_payments():
        if request.method == 'GET':
            try:
                # Mock payments data
                payments = [
                    {
                        'id': 1,
                        'tenant_id': 1,
                        'amount': 1200.00,
                        'status': 'completed',
                        'payment_date': datetime.utcnow().isoformat(),
                        'payment_method': 'credit_card'
                    },
                    {
                        'id': 2,
                        'tenant_id': 2,
                        'amount': 1500.00,
                        'status': 'pending',
                        'payment_date': datetime.utcnow().isoformat(),
                        'payment_method': 'bank_transfer'
                    }
                ]
                return jsonify(payments)
            except Exception as e:
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                # Mock payment creation
                return jsonify({
                    'message': 'Payment created successfully',
                    'id': 3,
                    'amount': data.get('amount', 0)
                }), 201
            except Exception as e:
                return jsonify({'error': 'Failed to create payment'}), 500
    
    @app.route('/api/payments/create-intent', methods=['POST'])
    def create_payment_intent():
        try:
            import stripe
            data = request.json
            amount = data.get('amount', 0)
            
            # Get Stripe secret key from environment
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_stripe_secret_key_here')
            
            # Check if we have a real Stripe key or use mock
            if stripe.api_key == 'sk_test_your_stripe_secret_key_here':
                # Mock Stripe payment intent creation for development
                payment_intent = {
                    'id': f'pi_mock_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                    'client_secret': f'pi_mock_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_secret',
                    'amount': int(amount * 100),  # Stripe uses cents
                    'currency': 'usd',
                    'status': 'requires_payment_method'
                }
            else:
                # Real Stripe payment intent creation
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Stripe uses cents
                    currency='usd',
                    metadata={
                        'tenant_id': data.get('tenant_id'),
                        'property_id': data.get('property_id')
                    }
                )
                payment_intent = {
                    'id': payment_intent.id,
                    'client_secret': payment_intent.client_secret,
                    'amount': payment_intent.amount,
                    'currency': payment_intent.currency,
                    'status': payment_intent.status
                }
            
            return jsonify(payment_intent)
        except Exception as e:
            print(f"Payment intent error: {str(e)}")
            return jsonify({'error': 'Failed to create payment intent'}), 500
    
    @app.route('/api/payments/<payment_id>/confirm', methods=['POST'])
    def confirm_payment(payment_id):
        try:
            # Mock payment confirmation
            return jsonify({
                'id': payment_id,
                'status': 'succeeded',
                'message': 'Payment confirmed successfully'
            })
        except Exception as e:
            return jsonify({'error': 'Failed to confirm payment'}), 500
    
    # LPR System Endpoints
    @app.route('/api/lpr/events', methods=['POST', 'GET'])
    def lpr_events():
        try:
            if request.method == 'POST':
                # Log new LPR event
                data = request.get_json()
                
                # Insert event into database
                db.session.execute(db.text("""
                    INSERT INTO lpr_events (plate, confidence, camera_id, image_path, timestamp, is_blacklisted, created_at)
                    VALUES (:plate, :confidence, :camera_id, :image_path, :timestamp, :is_blacklisted, NOW())
                """), {
                    'plate': data.get('plate'),
                    'confidence': data.get('confidence'),
                    'camera_id': data.get('camera_id'),
                    'image_path': data.get('image_path'),
                    'timestamp': data.get('timestamp'),
                    'is_blacklisted': data.get('is_blacklisted', False)
                })
                db.session.commit()
                
                return jsonify({'status': 'success', 'message': 'Event logged'}), 201
                
            else:
                # Get LPR events
                limit = request.args.get('limit', 50, type=int)
                events = db.session.execute(db.text("""
                    SELECT plate, confidence, camera_id, timestamp, is_blacklisted, created_at
                    FROM lpr_events 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """), {'limit': limit}).fetchall()
                
                return jsonify([{
                    'plate': row[0],
                    'confidence': row[1],
                    'camera_id': row[2],
                    'timestamp': row[3],
                    'is_blacklisted': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                } for row in events])
                
        except Exception as e:
            print(f"LPR events error: {str(e)}")
            if request.method == 'POST':
                return jsonify({'error': 'Failed to log event'}), 500
            else:
                return jsonify([])
    
    @app.route('/api/lpr/blacklist', methods=['GET', 'POST', 'DELETE'])
    def lpr_blacklist():
        try:
            if request.method == 'POST':
                # Add plate to blacklist
                data = request.get_json()
                plate = data.get('plate', '').upper().strip()
                reason = data.get('reason', '')
                
                if not plate:
                    return jsonify({'error': 'Plate number required'}), 400
                
                # Check if already exists
                existing = db.session.execute(db.text("""
                    SELECT id FROM lpr_blacklist WHERE plate = :plate
                """), {'plate': plate}).fetchone()
                
                if existing:
                    return jsonify({'error': 'Plate already blacklisted'}), 409
                
                # Add to blacklist
                db.session.execute(db.text("""
                    INSERT INTO lpr_blacklist (plate, reason, created_at)
                    VALUES (:plate, :reason, NOW())
                """), {'plate': plate, 'reason': reason})
                db.session.commit()
                
                return jsonify({'status': 'success', 'message': 'Plate added to blacklist'}), 201
                
            elif request.method == 'DELETE':
                # Remove plate from blacklist
                plate = request.args.get('plate', '').upper().strip()
                
                if not plate:
                    return jsonify({'error': 'Plate number required'}), 400
                
                result = db.session.execute(db.text("""
                    DELETE FROM lpr_blacklist WHERE plate = :plate
                """), {'plate': plate})
                db.session.commit()
                
                if result.rowcount > 0:
                    return jsonify({'status': 'success', 'message': 'Plate removed from blacklist'})
                else:
                    return jsonify({'error': 'Plate not found in blacklist'}), 404
                    
            else:
                # Get blacklist
                blacklist = db.session.execute(db.text("""
                    SELECT plate, reason, created_at FROM lpr_blacklist ORDER BY created_at DESC
                """)).fetchall()
                
                return jsonify([{
                    'plate': row[0],
                    'reason': row[1],
                    'created_at': row[2].isoformat() if row[2] else None
                } for row in blacklist])
                
        except Exception as e:
            print(f"Blacklist error: {str(e)}")
            return jsonify({'error': 'Database operation failed'}), 500
    
    @app.route('/api/lpr/blacklist/check', methods=['GET'])
    def check_blacklist():
        try:
            plate = request.args.get('plate', '').upper().strip()
            
            if not plate:
                return jsonify({'error': 'Plate number required'}), 400
            
            result = db.session.execute(db.text("""
                SELECT id, reason FROM lpr_blacklist WHERE plate = :plate
            """), {'plate': plate}).fetchone()
            
            is_blacklisted = result is not None
            reason = result[1] if result else None
            
            return jsonify({
                'plate': plate,
                'is_blacklisted': is_blacklisted,
                'reason': reason
            })
            
        except Exception as e:
            print(f"Blacklist check error: {str(e)}")
            return jsonify({'error': 'Check failed'}), 500
    
    @app.route('/api/lpr/recognize', methods=['POST'])
    def lpr_recognize():
        """Standalone LPR endpoint for client integration"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No image selected'}), 400
            
            # Save uploaded file temporarily
            import tempfile
            import uuid
            
            temp_dir = tempfile.gettempdir()
            filename = f"lpr_temp_{uuid.uuid4().hex}.jpg"
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            
            try:
                # Recognize plate
                from lpr_recognizer import recognize_plate
                api_key = os.environ.get("OPENALPR_API_KEY", "")
                plate, confidence = recognize_plate(temp_path, api_key)
                
                result = {
                    'success': plate is not None,
                    'plate': plate,
                    'confidence': confidence,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Check blacklist if plate found
                if plate:
                    blacklist_result = db.session.execute(db.text("""
                        SELECT reason FROM lpr_blacklist WHERE plate = :plate
                    """), {'plate': plate.upper()}).fetchone()
                    
                    result['is_blacklisted'] = blacklist_result is not None
                    result['blacklist_reason'] = blacklist_result[0] if blacklist_result else None
                
                return jsonify(result)
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            print(f"LPR recognize error: {str(e)}")
            return jsonify({'error': 'Recognition failed'}), 500
    
    @app.route('/api/lpr/ai-recognize', methods=['POST'])
    def ai_recognize_plate():
        """Advanced AI recognition with multiple OCR backends"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No image selected'}), 400
            
            # Save uploaded file temporarily
            import tempfile
            import uuid
            from ai_plate_recognition import AIPlateRecognizer
            
            temp_dir = tempfile.gettempdir()
            filename = f"ai_lpr_temp_{uuid.uuid4().hex}.jpg"
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            
            try:
                # Use AI recognizer
                recognizer = AIPlateRecognizer()
                results = recognizer.recognize_plate(temp_path)
                
                response_data = {
                    'success': len(results) > 0,
                    'timestamp': datetime.utcnow().isoformat(),
                    'results': []
                }
                
                for result in results:
                    plate_data = {
                        'plate': result.plate,
                        'confidence': result.confidence,
                        'source': result.source,
                        'bbox': result.bbox
                    }
                    
                    # Check blacklist for each result
                    blacklist_result = db.session.execute(db.text("""
                        SELECT reason FROM lpr_blacklist WHERE plate = :plate
                    """), {'plate': result.plate.upper()}).fetchone()
                    
                    plate_data['is_blacklisted'] = blacklist_result is not None
                    plate_data['blacklist_reason'] = blacklist_result[0] if blacklist_result else None
                    
                    response_data['results'].append(plate_data)
                
                return jsonify(response_data)
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            print(f"AI LPR recognize error: {str(e)}")
            return jsonify({'error': 'AI recognition failed'}), 500
    
    @app.route('/api/lpr/search', methods=['GET'])
    def search_plates():
        """Intelligent plate search with fuzzy matching"""
        try:
            query = request.args.get('q', '').strip()
            min_similarity = float(request.args.get('min_similarity', '0.5'))
            limit = int(request.args.get('limit', '10'))
            
            if not query:
                return jsonify({'error': 'Query parameter required'}), 400
            
            from ai_plate_recognition import FuzzyPlateSearch
            
            # Initialize fuzzy search
            fuzzy_search = FuzzyPlateSearch()
            
            # Search database
            results = fuzzy_search.smart_search_database(
                query, db, min_similarity, limit
            )
            
            # Get additional details for each result
            detailed_results = []
            for result in results:
                # Get latest event for this plate
                latest_event = db.session.execute(db.text("""
                    SELECT camera_id, created_at, is_blacklisted
                    FROM lpr_events 
                    WHERE plate = :plate 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """), {'plate': result.plate}).fetchone()
                
                # Check if blacklisted
                blacklist_info = db.session.execute(db.text("""
                    SELECT reason, created_at FROM lpr_blacklist WHERE plate = :plate
                """), {'plate': result.plate}).fetchone()
                
                detailed_result = {
                    'plate': result.plate,
                    'similarity': result.similarity,
                    'match_type': result.match_type,
                    'original_query': result.original_query,
                    'is_blacklisted': blacklist_info is not None,
                    'blacklist_reason': blacklist_info[0] if blacklist_info else None,
                    'blacklist_date': blacklist_info[1].isoformat() if blacklist_info and blacklist_info[1] else None,
                    'last_seen': latest_event[1].isoformat() if latest_event and latest_event[1] else None,
                    'last_camera': latest_event[0] if latest_event else None
                }
                
                detailed_results.append(detailed_result)
            
            return jsonify({
                'query': query,
                'results': detailed_results,
                'total_found': len(detailed_results)
            })
            
        except Exception as e:
            print(f"Plate search error: {str(e)}")
            return jsonify({'error': 'Search failed'}), 500
    
    @app.route('/api/lpr/companies', methods=['GET'])
    def get_lpr_companies():
        """Get all active LPR companies"""
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return response
            
        try:
            result = db.session.execute(db.text("""
                SELECT 
                    id, name, description, contact_email, contact_phone, 
                    address, max_alerts_per_day, max_cameras, 
                    subscription_type, created_at
                FROM lpr_companies 
                WHERE is_active = true
                ORDER BY name
            """)).fetchall()
            
            companies = []
            for row in result:
                # Count users for each company
                user_count = db.session.execute(db.text("""
                    SELECT COUNT(*) FROM users 
                    WHERE lpr_company_id = :company_id AND is_active = true
                """), {'company_id': row[0]}).scalar()
                
                companies.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'contact_email': row[3],
                    'contact_phone': row[4],
                    'address': row[5],
                    'max_alerts_per_day': row[6],
                    'max_cameras': row[7],
                    'subscription_type': row[8],
                    'created_at': row[9].isoformat() if row[9] else None,
                    'user_count': user_count or 0
                })
            
            response = jsonify(companies)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return response
            
        except Exception as e:
            print(f"Companies fetch error: {str(e)}")
            return jsonify({'error': 'Failed to fetch companies'}), 500
    
    @app.route('/api/lpr/companies', methods=['POST'])
    def create_lpr_company():
        """Create a new LPR company"""
        try:
            data = request.json
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'Company name is required'}), 400
            
            # Check if company name already exists
            existing = db.session.execute(db.text("""
                SELECT id FROM lpr_companies WHERE name = :name
            """), {'name': data['name']}).fetchone()
            
            if existing:
                return jsonify({'error': 'Company name already exists'}), 400
            
            # Insert new company
            db.session.execute(db.text("""
                INSERT INTO lpr_companies (
                    name, description, contact_email, contact_phone, address,
                    max_alerts_per_day, max_cameras, subscription_type, created_at
                ) VALUES (
                    :name, :description, :contact_email, :contact_phone, :address,
                    :max_alerts_per_day, :max_cameras, :subscription_type, :created_at
                )
            """), {
                'name': data['name'],
                'description': data.get('description', ''),
                'contact_email': data.get('contact_email', ''),
                'contact_phone': data.get('contact_phone', ''),
                'address': data.get('address', ''),
                'max_alerts_per_day': data.get('max_alerts_per_day', 100),
                'max_cameras': data.get('max_cameras', 10),
                'subscription_type': data.get('subscription_type', 'basic'),
                'created_at': datetime.utcnow()
            })
            
            db.session.commit()
            
            response = jsonify({
                'message': 'Company created successfully',
                'name': data['name']
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return response, 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Company creation error: {str(e)}")
            return jsonify({'error': 'Failed to create company'}), 500
    
    @app.route('/api/lpr/companies/<int:company_id>', methods=['GET'])
    def get_lpr_company_details(company_id):
        """Get specific company details with users"""
        try:
            # Get company info
            company = db.session.execute(db.text("""
                SELECT id, name, description, contact_email, contact_phone, address,
                       max_alerts_per_day, max_cameras, subscription_type, created_at
                FROM lpr_companies 
                WHERE id = :company_id AND is_active = true
            """), {'company_id': company_id}).fetchone()
            
            if not company:
                return jsonify({'error': 'Company not found'}), 404
            
            # Get company users
            users = db.session.execute(db.text("""
                SELECT id, username, email, role, lpr_permissions, created_at
                FROM users 
                WHERE lpr_company_id = :company_id AND is_active = true
                ORDER BY username
            """), {'company_id': company_id}).fetchall()
            
            user_list = []
            for user in users:
                user_list.append({
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'lpr_permissions': user[4],
                    'created_at': user[5].isoformat() if user[5] else None
                })
            
            result = {
                'id': company[0],
                'name': company[1],
                'description': company[2],
                'contact_email': company[3],
                'contact_phone': company[4],
                'address': company[5],
                'max_alerts_per_day': company[6],
                'max_cameras': company[7],
                'subscription_type': company[8],
                'created_at': company[9].isoformat() if company[9] else None,
                'users': user_list,
                'user_count': len(user_list)
            }
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Company details error: {str(e)}")
            return jsonify({'error': 'Failed to fetch company details'}), 500
    
    @app.route('/api/invites/send', methods=['POST'])
    def send_simple_invite():
        """Simple invitation endpoint"""
        try:
            data = request.json
            email = data.get('email')
            role = data.get('role', 'tenant')
            
            if not email:
                return jsonify({'error': 'Email is required'}), 400
            
            # Mock invitation sending - in real implementation, this would send actual emails
            print(f"Sending invitation to {email} with role {role}")
            
            return jsonify({
                'message': 'Invitation sent successfully',
                'email': email,
                'role': role
            })
            
        except Exception as e:
            print(f"Simple invite error: {str(e)}")
            return jsonify({'error': 'Failed to send invitation'}), 500
    
    @app.route('/api/invites/send-enhanced', methods=['POST'])
    def send_enhanced_invite():
        """Enhanced invitation endpoint for property/LPR management"""
        try:
            data = request.json
            email = data.get('email')
            access_type = data.get('access_type')
            property_management_access = data.get('property_management_access', False)
            lpr_management_access = data.get('lpr_management_access', False)
            property_role = data.get('property_role')
            lpr_role = data.get('lpr_role')
            lpr_company_id = data.get('lpr_company_id')
            lpr_permissions = data.get('lpr_permissions')
            
            # Validate inputs
            if not email or not access_type:
                return jsonify({'error': 'Email and access type are required'}), 400
            
            # Check if user already exists
            existing_user = db.session.execute(db.text("""
                SELECT id FROM users WHERE email = :email
            """), {'email': email}).fetchone()
            
            if existing_user:
                return jsonify({'error': 'User with this email already exists'}), 400
            
            # Validate LPR company if needed
            if lpr_management_access and lpr_company_id:
                company_check = db.session.execute(db.text("""
                    SELECT id FROM lpr_companies WHERE id = :company_id AND is_active = true
                """), {'company_id': lpr_company_id}).fetchone()
                
                if not company_check:
                    return jsonify({'error': 'Invalid or inactive LPR company'}), 400
            
            # Check for existing pending invite
            pending_invite = db.session.execute(db.text("""
                SELECT id FROM invites 
                WHERE email = :email AND is_used = false AND expires_at > NOW()
            """), {'email': email}).fetchone()
            
            if pending_invite:
                return jsonify({'error': 'A pending invitation already exists for this email'}), 400
            
            # Generate invite token
            import uuid
            token = uuid.uuid4().hex
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            # Determine primary role
            primary_role = property_role or lpr_role or 'user'
            
            # Create invite with extended data in notes field
            import json
            extended_data = {
                'access_type': access_type,
                'property_management_access': property_management_access,
                'lpr_management_access': lpr_management_access,
                'property_role': property_role,
                'lpr_role': lpr_role,
                'lpr_company_id': lpr_company_id,
                'lpr_permissions': lpr_permissions
            }
            
            db.session.execute(db.text("""
                INSERT INTO invites (email, role, token, invited_by_id, expires_at, notes, created_at)
                VALUES (:email, :role, :token, :invited_by_id, :expires_at, :notes, :created_at)
            """), {
                'email': email,
                'role': primary_role,
                'token': token,
                'invited_by_id': 1,  # Default to super admin
                'expires_at': expires_at,
                'notes': json.dumps(extended_data),
                'created_at': datetime.utcnow()
            })
            
            db.session.commit()
            
            # Send enhanced invitation email
            try:
                from utils.simple_email import send_enhanced_invite_email
                company_name = "No specific company"
                if lpr_company_id:
                    company_result = db.session.execute(db.text("""
                        SELECT name FROM lpr_companies WHERE id = :company_id
                    """), {'company_id': lpr_company_id}).fetchone()
                    if company_result:
                        company_name = company_result[0]
                
                email_sent = send_enhanced_invite_email(
                    email=email,
                    access_type=access_type,
                    property_role=property_role,
                    lpr_role=lpr_role,
                    company_name=company_name,
                    invited_by="System Admin",
                    token=token
                )
                
                if email_sent:
                    message = f'Enhanced invitation sent successfully to {email}'
                else:
                    message = f'Invitation created for {email}, but email delivery failed. Please share the token manually.'
                    
            except Exception as e:
                print(f"Email sending error: {str(e)}")
                message = f'Invitation created for {email}, but email delivery failed.'
            
            return jsonify({
                'message': message,
                'access_type': access_type,
                'token': token,  # For testing/manual sharing
                'expires_at': expires_at.isoformat()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Enhanced invite error: {str(e)}")
            return jsonify({'error': 'Failed to send invitation'}), 500
    
    @app.route('/api/lpr/suggest', methods=['GET'])
    def suggest_plates():
        """Auto-suggest plates based on partial input"""
        try:
            query = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', '5'))
            
            if len(query) < 2:
                return jsonify({'suggestions': []})
            
            from ai_plate_recognition import FuzzyPlateSearch
            
            # Get plates that start with or contain the query
            plates = db.session.execute(db.text("""
                SELECT DISTINCT plate FROM (
                    SELECT plate FROM lpr_events WHERE plate ILIKE :query1 OR plate ILIKE :query2
                    UNION
                    SELECT plate FROM lpr_blacklist WHERE plate ILIKE :query1 OR plate ILIKE :query2
                ) AS matches
                ORDER BY plate
                LIMIT :limit
            """), {
                'query1': f"{query.upper()}%",  # Starts with
                'query2': f"%{query.upper()}%",  # Contains
                'limit': limit
            }).fetchall()
            
            suggestions = [row[0] for row in plates]
            
            return jsonify({
                'query': query,
                'suggestions': suggestions
            })
            
        except Exception as e:
            print(f"Plate suggest error: {str(e)}")
            return jsonify({'suggestions': []})
    
    @app.route('/api/lpr/analyze-image', methods=['POST'])
    def analyze_image():
        """Analyze image and return all plate candidates with confidence scores"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No image selected'}), 400
            
            # Save uploaded file temporarily
            import tempfile
            import uuid
            from ai_plate_recognition import AIPlateRecognizer
            
            temp_dir = tempfile.gettempdir()
            filename = f"analyze_temp_{uuid.uuid4().hex}.jpg"
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            
            try:
                # Use AI recognizer to get all candidates
                recognizer = AIPlateRecognizer()
                results = recognizer.recognize_plate(temp_path)
                
                # Also get preprocessed images info
                processed_images = recognizer.preprocess_image(temp_path)
                
                analysis_result = {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'image_analysis': {
                        'preprocessed_versions': len(processed_images),
                        'total_candidates': len(results)
                    },
                    'candidates': []
                }
                
                for i, result in enumerate(results):
                    candidate = {
                        'rank': i + 1,
                        'plate': result.plate,
                        'confidence': result.confidence,
                        'source': result.source,
                        'bbox': result.bbox,
                        'is_valid_format': recognizer._is_potential_plate(result.plate)
                    }
                    
                    # Check if this plate exists in our database
                    db_check = db.session.execute(db.text("""
                        SELECT 
                            (SELECT COUNT(*) FROM lpr_events WHERE plate = :plate) as event_count,
                            (SELECT reason FROM lpr_blacklist WHERE plate = :plate) as blacklist_reason
                    """), {'plate': result.plate}).fetchone()
                    
                    candidate['database_matches'] = {
                        'event_count': db_check[0] if db_check else 0,
                        'is_blacklisted': db_check[1] is not None if db_check else False,
                        'blacklist_reason': db_check[1] if db_check else None
                    }
                    
                    analysis_result['candidates'].append(candidate)
                
                return jsonify(analysis_result)
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            print(f"Image analysis error: {str(e)}")
            return jsonify({'error': 'Image analysis failed'}), 500
    
    @app.route('/api/notifications/send', methods=['POST'])
    def send_notification():
        """Send notifications for blacklisted plates"""
        try:
            data = request.get_json()
            
            # Log notification
            print(f"[NOTIFICATION] {data.get('type', 'alert')}: {data}")
            
            # Here you could integrate with:
            # - Email services
            # - SMS services  
            # - Slack/Discord webhooks
            # - Push notifications
            # - Mobile apps
            
            # For now, just acknowledge
            return jsonify({'status': 'success', 'message': 'Notification sent'})
            
        except Exception as e:
            print(f"Notification error: {str(e)}")
            return jsonify({'error': 'Failed to send notification'}), 500

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
    
    # Analytics API
    @app.route('/api/analytics', methods=['GET'])
    def get_analytics():
        try:
            days = request.args.get('days', '30')
            
            # Mock analytics data - in production this would query real data
            analytics_data = {
                'overview': {
                    'total_revenue': 127500,
                    'occupancy_rate': 94.2,
                    'avg_rent': 1850,
                    'maintenance_cost': 8450,
                    'revenue_growth': 15.2,
                    'occupancy_growth': 2.1,
                    'rent_growth': 5.8,
                    'maintenance_savings': -12.5
                },
                'financial': {
                    'monthly_revenue': [85000, 92000, 88000, 105000, 98000, 127500],
                    'expenses': [25000, 28000, 24000, 32000, 29000, 35000],
                    'net_income': [60000, 64000, 64000, 73000, 69000, 92500]
                },
                'operations': {
                    'maintenance_requests': {
                        'open': 15,
                        'in_progress': 8,
                        'completed': 45,
                        'cancelled': 2
                    },
                    'avg_response_time': 2.3,
                    'work_orders_completed': 142,
                    'tenant_satisfaction': 4.7
                },
                'tenant_analytics': {
                    'avg_lease_length': 18,
                    'turnover_rate': 12,
                    'avg_security_deposit': 1200,
                    'total_tenants': 124,
                    'new_tenants_this_month': 8,
                    'lease_renewals': 15
                },
                'occupancy': {
                    'occupied': 85,
                    'vacant': 12,
                    'maintenance': 3
                },
                'rent_collection': {
                    'collected': [12000, 19000, 15000, 25000, 22000, 30000],
                    'due': [15000, 20000, 18000, 27000, 25000, 32000]
                },
                'predictive_insights': [
                    {
                        'type': 'revenue_forecast',
                        'message': 'Based on current trends, expect 8% revenue growth next quarter',
                        'confidence': 0.85
                    },
                    {
                        'type': 'maintenance_alert',
                        'message': 'Unit 204 may require HVAC maintenance within 30 days',
                        'confidence': 0.72
                    },
                    {
                        'type': 'optimization',
                        'message': 'Consider raising rent by 3% based on market analysis',
                        'confidence': 0.91
                    }
                ],
                'real_time_activity': [
                    {
                        'type': 'payment',
                        'message': 'Rent payment received from Unit 305 - $1,850',
                        'timestamp': datetime.utcnow().isoformat(),
                        'priority': 'low'
                    },
                    {
                        'type': 'maintenance',
                        'message': 'New maintenance request - Unit 102 Plumbing',
                        'timestamp': (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                        'priority': 'medium'
                    },
                    {
                        'type': 'lease',
                        'message': 'Lease renewal signed - Unit 204',
                        'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                        'priority': 'low'
                    }
                ]
            }
            
            return jsonify(analytics_data)
            
        except Exception as e:
            print(f"Analytics error: {str(e)}")
            return jsonify({'error': 'Failed to fetch analytics'}), 500

    # Notifications API
    @app.route('/api/notifications', methods=['GET', 'POST'])
    def handle_notifications():
        if request.method == 'GET':
            try:
                # Mock notifications data
                mock_notifications = [
                    {
                        'id': 1,
                        'title': 'Rent Payment Received',
                        'message': 'Rent payment of $1,850 received from Unit 305',
                        'type': 'payment',
                        'priority': 'low',
                        'timestamp': datetime.utcnow().isoformat(),
                        'read': False
                    },
                    {
                        'id': 2,
                        'title': 'Maintenance Alert',
                        'message': 'HVAC system requires urgent attention in Unit 204',
                        'type': 'maintenance',
                        'priority': 'high',
                        'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                        'read': False
                    },
                    {
                        'id': 3,
                        'title': 'Security Alert',
                        'message': 'Blacklisted vehicle ABC-123 detected at Property A',
                        'type': 'security',
                        'priority': 'high',
                        'timestamp': (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                        'read': True
                    },
                    {
                        'id': 4,
                        'title': 'Lease Renewal',
                        'message': 'Lease renewal due for Unit 102 next month',
                        'type': 'lease',
                        'priority': 'medium',
                        'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                        'read': True
                    }
                ]
                return jsonify(mock_notifications)
            except Exception as e:
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                # Create new notification
                new_notification = {
                    'id': random.randint(1000, 9999),
                    'title': data.get('title', 'New Notification'),
                    'message': data.get('message', ''),
                    'type': data.get('type', 'system'),
                    'priority': data.get('priority', 'medium'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'read': False
                }
                return jsonify(new_notification), 201
            except Exception as e:
                return jsonify({'error': 'Failed to create notification'}), 500

    @app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
    def mark_notification_read(notification_id):
        try:
            # Mock mark as read
            return jsonify({'message': 'Notification marked as read'})
        except Exception as e:
            return jsonify({'error': 'Failed to mark notification as read'}), 500

    @app.route('/api/notifications/mark-all-read', methods=['POST'])
    def mark_all_notifications_read():
        try:
            # Mock mark all as read
            return jsonify({'message': 'All notifications marked as read'})
        except Exception as e:
            return jsonify({'error': 'Failed to mark notifications as read'}), 500

    @app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
    def delete_notification(notification_id):
        try:
            # Mock delete notification
            return jsonify({'message': 'Notification deleted'})
        except Exception as e:
            return jsonify({'error': 'Failed to delete notification'}), 500

    # Search API
    @app.route('/api/search', methods=['POST'])
    def search():
        try:
            data = request.json
            query = data.get('query', '')
            filters = data.get('filters', {})
            entity_type = data.get('entityType', 'all')
            
            # Mock search results - in production this would search the database
            mock_results = []
            
            if 'property' in query.lower() or entity_type == 'properties':
                mock_results.extend([
                    {
                        'id': 1,
                        'type': 'property',
                        'title': 'Sunset Apartments',
                        'subtitle': '123 Main St, Anytown, ST 12345',
                        'description': '50-unit apartment complex',
                        'match_score': 0.95
                    },
                    {
                        'id': 2,
                        'type': 'property',
                        'title': 'Ocean View Condos',
                        'subtitle': '456 Beach Ave, Coastal City, ST 54321',
                        'description': '25-unit luxury condominiums',
                        'match_score': 0.87
                    }
                ])
            
            if 'tenant' in query.lower() or entity_type == 'tenants':
                mock_results.extend([
                    {
                        'id': 1,
                        'type': 'tenant',
                        'title': 'John Smith',
                        'subtitle': 'Unit 305, Sunset Apartments',
                        'description': 'Lease expires 12/2024',
                        'match_score': 0.92
                    }
                ])
            
            if 'maintenance' in query.lower() or entity_type == 'maintenance':
                mock_results.extend([
                    {
                        'id': 1,
                        'type': 'maintenance',
                        'title': 'HVAC Repair Request',
                        'subtitle': 'Unit 204 - High Priority',
                        'description': 'AC unit not cooling properly',
                        'match_score': 0.89
                    }
                ])
            
            # Sort by match score
            mock_results.sort(key=lambda x: x['match_score'], reverse=True)
            
            return jsonify({
                'results': mock_results,
                'total': len(mock_results),
                'query': query,
                'filters': filters
            })
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return jsonify({'error': 'Search failed'}), 500

    @app.route('/api/search/suggestions', methods=['GET'])
    def search_suggestions():
        try:
            query = request.args.get('q', '')
            entity_type = request.args.get('type', 'all')
            
            # Mock suggestions based on query
            suggestions = []
            
            if 'prop' in query.lower():
                suggestions.extend([
                    {'text': 'Properties by location', 'type': 'property', 'icon': '🏢'},
                    {'text': 'Property management', 'type': 'property', 'icon': '🏢'},
                    {'text': 'Property maintenance', 'type': 'property', 'icon': '🏢'}
                ])
            
            if 'ten' in query.lower():
                suggestions.extend([
                    {'text': 'Tenant screening', 'type': 'tenant', 'icon': '👤'},
                    {'text': 'Tenant communications', 'type': 'tenant', 'icon': '👤'},
                    {'text': 'Tenant payments', 'type': 'tenant', 'icon': '👤'}
                ])
            
            if 'main' in query.lower():
                suggestions.extend([
                    {'text': 'Maintenance requests', 'type': 'maintenance', 'icon': '🔧'},
                    {'text': 'Maintenance scheduling', 'type': 'maintenance', 'icon': '🔧'},
                    {'text': 'Maintenance history', 'type': 'maintenance', 'icon': '🔧'}
                ])
            
            # Generic suggestions if no specific matches
            if not suggestions:
                suggestions = [
                    {'text': f'{query} in properties', 'type': 'property', 'icon': '🏢'},
                    {'text': f'{query} in tenants', 'type': 'tenant', 'icon': '👤'},
                    {'text': f'{query} in maintenance', 'type': 'maintenance', 'icon': '🔧'}
                ]
            
            return jsonify(suggestions[:5])  # Limit to 5 suggestions
            
        except Exception as e:
            return jsonify([])

    @app.route('/api/search/saved', methods=['GET'])
    def get_saved_searches():
        try:
            # Mock saved searches
            saved_searches = [
                {
                    'id': 1,
                    'name': 'High Priority Maintenance',
                    'query': 'maintenance',
                    'filters': {'priority': 'high', 'status': 'open'},
                    'entityType': 'maintenance'
                },
                {
                    'id': 2,
                    'name': 'Vacant Properties',
                    'query': 'vacant',
                    'filters': {'status': 'vacant'},
                    'entityType': 'properties'
                }
            ]
            return jsonify(saved_searches)
        except Exception as e:
            return jsonify([])

    @app.route('/api/search/save', methods=['POST'])
    def save_search():
        try:
            data = request.json
            # Mock save search
            saved_search = {
                'id': random.randint(1000, 9999),
                'name': data.get('name'),
                'query': data.get('query'),
                'filters': data.get('filters', {}),
                'entityType': data.get('entityType', 'all'),
                'created_at': datetime.utcnow().isoformat()
            }
            return jsonify(saved_search), 201
        except Exception as e:
            return jsonify({'error': 'Failed to save search'}), 500

    # Enhanced Documents API
    @app.route('/api/documents/enhanced', methods=['GET', 'POST'])
    def handle_enhanced_documents():
        if request.method == 'GET':
            try:
                folder_id = request.args.get('folder')
                # Enhanced mock documents with more metadata
                documents = [
                    {
                        'id': 1,
                        'name': 'Lease Agreement - Unit 305.pdf',
                        'type': 'pdf',
                        'category': 'lease',
                        'description': 'Standard lease agreement for Unit 305',
                        'size': 2457600,  # bytes
                        'property_id': 1,
                        'unit_id': 305,
                        'tenant_id': 1,
                        'folder_id': folder_id,
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'uploaded_by': 'Property Manager',
                        'file_path': '/documents/lease_305.pdf',
                        'is_public': False,
                        'tags': ['lease', 'legal', 'unit-305'],
                        'version': 1,
                        'checksum': 'abc123def456'
                    },
                    {
                        'id': 2,
                        'name': 'Property Insurance Certificate.pdf',
                        'type': 'pdf',
                        'category': 'insurance',
                        'description': 'Annual property insurance certificate',
                        'size': 1887436,
                        'property_id': 1,
                        'uploaded_at': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                        'uploaded_by': 'Admin',
                        'file_path': '/documents/insurance_2024.pdf',
                        'is_public': False,
                        'tags': ['insurance', 'legal', 'annual'],
                        'version': 1,
                        'checksum': 'def456ghi789'
                    },
                    {
                        'id': 3,
                        'name': 'Maintenance Invoice - March 2024.xlsx',
                        'type': 'xlsx',
                        'category': 'financial',
                        'description': 'March 2024 maintenance expenses',
                        'size': 45678,
                        'property_id': 1,
                        'uploaded_at': (datetime.utcnow() - timedelta(days=10)).isoformat(),
                        'uploaded_by': 'Accountant',
                        'file_path': '/documents/maintenance_march_2024.xlsx',
                        'is_public': False,
                        'tags': ['financial', 'maintenance', 'march-2024'],
                        'version': 2,
                        'checksum': 'ghi789jkl012'
                    },
                    {
                        'id': 4,
                        'name': 'Property Photos - Main Building.zip',
                        'type': 'zip',
                        'category': 'media',
                        'description': 'Updated photos of main building exterior and common areas',
                        'size': 15728640,
                        'property_id': 1,
                        'uploaded_at': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                        'uploaded_by': 'Marketing Team',
                        'file_path': '/documents/property_photos_main.zip',
                        'is_public': True,
                        'tags': ['photos', 'marketing', 'exterior'],
                        'version': 1,
                        'checksum': 'jkl012mno345'
                    }
                ]
                return jsonify(documents)
            except Exception as e:
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                # Mock document creation with enhanced metadata
                new_document = {
                    'id': random.randint(1000, 9999),
                    'name': data.get('name', 'Untitled Document'),
                    'type': data.get('type', 'unknown'),
                    'category': data.get('category', 'general'),
                    'description': data.get('description', ''),
                    'size': data.get('size', 0),
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'uploaded_by': 'Current User',
                    'version': 1
                }
                return jsonify(new_document), 201
            except Exception as e:
                return jsonify({'error': 'Failed to upload document'}), 500

    @app.route('/api/documents/upload', methods=['POST'])
    def upload_documents():
        try:
            # Mock file upload handling
            folder_id = request.form.get('folder_id')
            
            # In a real implementation, you would:
            # 1. Save files to storage (local, S3, etc.)
            # 2. Extract metadata (file size, type, etc.)
            # 3. Generate thumbnails for images
            # 4. Scan for viruses
            # 5. Save metadata to database
            
            uploaded_files = []
            file_count = len(request.files.getlist('files'))
            
            for i in range(file_count):
                uploaded_files.append({
                    'id': random.randint(1000, 9999),
                    'name': f'uploaded_file_{i+1}.pdf',
                    'size': random.randint(100000, 5000000),
                    'type': 'pdf',
                    'uploaded_at': datetime.utcnow().isoformat()
                })
            
            return jsonify({
                'message': f'{len(uploaded_files)} files uploaded successfully',
                'files': uploaded_files
            }), 201
            
        except Exception as e:
            return jsonify({'error': 'Upload failed'}), 500

    @app.route('/api/documents/folders', methods=['GET', 'POST'])
    def handle_folders():
        if request.method == 'GET':
            try:
                # Mock folder structure
                folders = [
                    {
                        'id': 1,
                        'name': 'Lease Agreements',
                        'parent_id': None,
                        'document_count': 15,
                        'created_at': datetime.utcnow().isoformat()
                    },
                    {
                        'id': 2,
                        'name': 'Insurance Documents',
                        'parent_id': None,
                        'document_count': 8,
                        'created_at': datetime.utcnow().isoformat()
                    },
                    {
                        'id': 3,
                        'name': 'Financial Records',
                        'parent_id': None,
                        'document_count': 25,
                        'created_at': datetime.utcnow().isoformat()
                    },
                    {
                        'id': 4,
                        'name': 'Property Photos',
                        'parent_id': None,
                        'document_count': 45,
                        'created_at': datetime.utcnow().isoformat()
                    }
                ]
                return jsonify(folders)
            except Exception as e:
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                new_folder = {
                    'id': random.randint(1000, 9999),
                    'name': data.get('name'),
                    'parent_id': data.get('parent_id'),
                    'document_count': 0,
                    'created_at': datetime.utcnow().isoformat()
                }
                return jsonify(new_folder), 201
            except Exception as e:
                return jsonify({'error': 'Failed to create folder'}), 500

    @app.route('/api/documents/<int:document_id>', methods=['GET', 'DELETE'])
    def handle_document(document_id):
        if request.method == 'GET':
            try:
                # Mock document details
                document = {
                    'id': document_id,
                    'name': 'Sample Document.pdf',
                    'type': 'pdf',
                    'size': 1234567,
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'metadata': {
                        'pages': 15,
                        'author': 'Property Manager',
                        'created_date': datetime.utcnow().isoformat()
                    }
                }
                return jsonify(document)
            except Exception as e:
                return jsonify({'error': 'Document not found'}), 404
        
        elif request.method == 'DELETE':
            try:
                # Mock document deletion
                return jsonify({'message': 'Document deleted successfully'})
            except Exception as e:
                return jsonify({'error': 'Failed to delete document'}), 500

    @app.route('/api/documents/<int:document_id>/download', methods=['GET'])
    def download_document(document_id):
        try:
            # Mock file download - in reality, this would stream the actual file
            return jsonify({
                'download_url': f'/files/document_{document_id}.pdf',
                'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
            })
        except Exception as e:
            return jsonify({'error': 'Download failed'}), 500

    @app.route('/api/documents/<int:document_id>/share', methods=['POST'])
    def share_document(document_id):
        try:
            data = request.json
            expires_in = data.get('expires_in', 24 * 60 * 60)  # 24 hours default
            
            # Generate secure share token
            share_token = f"share_{document_id}_{random.randint(100000, 999999)}"
            
            share_info = {
                'share_url': f'https://estatecore.com/shared/{share_token}',
                'token': share_token,
                'expires_at': (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
                'permissions': data.get('permissions', ['view']),
                'document_id': document_id
            }
            
            return jsonify(share_info), 201
        except Exception as e:
            return jsonify({'error': 'Failed to create share link'}), 500

    @app.route('/api/documents/bulk/<action>', methods=['POST'])
    def bulk_document_action(action):
        try:
            data = request.json
            document_ids = data.get('document_ids', [])
            
            if not document_ids:
                return jsonify({'error': 'No documents specified'}), 400
            
            if action == 'delete':
                # Mock bulk delete
                return jsonify({
                    'message': f'{len(document_ids)} documents deleted successfully',
                    'deleted_ids': document_ids
                })
            elif action == 'download':
                # Mock bulk download - create zip file
                zip_token = f"bulk_{random.randint(100000, 999999)}"
                return jsonify({
                    'message': f'Preparing download for {len(document_ids)} documents',
                    'download_url': f'/downloads/{zip_token}.zip',
                    'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
                })
            else:
                return jsonify({'error': f'Unknown action: {action}'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Bulk {action} failed'}), 500

    # Email API
    @app.route('/api/email/send-invitation', methods=['POST'])
    def send_email_invitation():
        try:
            data = request.json
            email_service = create_email_service()
            
            success = email_service.send_user_invitation(
                email=data.get('email'),
                name=data.get('name'),
                role=data.get('role'),
                temporary_password=data.get('temporary_password'),
                organization_name=data.get('organization_name', 'EstateCore'),
                login_url=data.get('login_url', 'https://app.estatecore.com')
            )
            
            if success:
                return jsonify({'message': 'Invitation sent successfully'}), 200
            else:
                return jsonify({'error': 'Failed to send invitation'}), 500
                
        except Exception as e:
            print(f"Email invitation error: {str(e)}")
            return jsonify({'error': 'Failed to send invitation'}), 500

    @app.route('/api/email/send-maintenance-notification', methods=['POST'])
    def send_maintenance_notification():
        try:
            data = request.json
            email_service = create_email_service()
            
            success = email_service.send_maintenance_notification(
                to_emails=data.get('to_emails', []),
                notification_type=data.get('notification_type', 'Request'),
                title=data.get('title'),
                description=data.get('description'),
                property_name=data.get('property_name'),
                unit_number=data.get('unit_number'),
                priority=data.get('priority', 'Medium'),
                status=data.get('status', 'Open'),
                recipient_name=data.get('recipient_name', 'Tenant')
            )
            
            if success:
                return jsonify({'message': 'Notification sent successfully'}), 200
            else:
                return jsonify({'error': 'Failed to send notification'}), 500
                
        except Exception as e:
            print(f"Maintenance notification error: {str(e)}")
            return jsonify({'error': 'Failed to send notification'}), 500

    @app.route('/api/email/send-payment-receipt', methods=['POST'])
    def send_payment_receipt():
        try:
            data = request.json
            email_service = create_email_service()
            
            success = email_service.send_payment_receipt(
                email=data.get('email'),
                recipient_name=data.get('recipient_name'),
                amount=float(data.get('amount', 0)),
                property_name=data.get('property_name'),
                unit_number=data.get('unit_number'),
                payment_method=data.get('payment_method', 'Credit Card'),
                transaction_id=data.get('transaction_id'),
                payment_date=data.get('payment_date'),
                receipt_url=data.get('receipt_url')
            )
            
            if success:
                return jsonify({'message': 'Receipt sent successfully'}), 200
            else:
                return jsonify({'error': 'Failed to send receipt'}), 500
                
        except Exception as e:
            print(f"Payment receipt error: {str(e)}")
            return jsonify({'error': 'Failed to send receipt'}), 500

    @app.route('/api/email/test-configuration', methods=['POST'])
    def test_email_configuration():
        try:
            email_service = create_email_service()
            success = email_service.test_configuration()
            
            if success:
                return jsonify({'message': 'Email configuration is working'}), 200
            else:
                return jsonify({'error': 'Email configuration test failed'}), 500
                
        except Exception as e:
            print(f"Email test error: {str(e)}")
            return jsonify({'error': 'Email test failed'}), 500

    @app.route('/api/email/bulk-send', methods=['POST'])
    def bulk_send_emails():
        try:
            data = request.json
            email_service = create_email_service()
            
            recipients = data.get('recipients', [])
            template_name = data.get('template_name')
            subject = data.get('subject')
            common_context = data.get('common_context', {})
            individual_contexts = data.get('individual_contexts', [])
            
            results = email_service.send_bulk_notification(
                recipients=recipients,
                subject=subject,
                template_name=template_name,
                common_context=common_context,
                individual_contexts=individual_contexts
            )
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            return jsonify({
                'message': f'Sent {success_count}/{total_count} emails successfully',
                'results': results
            }), 200
            
        except Exception as e:
            print(f"Bulk email error: {str(e)}")
            return jsonify({'error': 'Bulk email send failed'}), 500

    # Enhanced User Creation with Email Integration
    @app.route('/api/users/invite', methods=['POST'])
    def invite_user():
        try:
            data = request.json
            
            # Generate temporary password
            temp_password = f"temp{random.randint(100000, 999999)}"
            
            # Create user in database (mock for now)
            new_user = {
                'id': random.randint(1000, 9999),
                'email': data.get('email'),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'role': data.get('role', 'tenant'),
                'is_active': True,
                'temporary_password': temp_password,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Send invitation email
            email_service = create_email_service()
            email_success = email_service.send_user_invitation(
                email=data.get('email'),
                name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                role=data.get('role', 'tenant'),
                temporary_password=temp_password,
                organization_name=data.get('organization_name', 'EstateCore')
            )
            
            return jsonify({
                'message': 'User invited successfully',
                'user': new_user,
                'email_sent': email_success
            }), 201
            
        except Exception as e:
            print(f"User invitation error: {str(e)}")
            return jsonify({'error': 'Failed to invite user'}), 500

    # SMS API
    @app.route('/api/sms/send', methods=['POST'])
    def send_sms():
        try:
            data = request.json
            sms_service = create_sms_service()
            
            result = sms_service.send_sms(
                to_number=data.get('phone_number'),
                message=data.get('message'),
                media_urls=data.get('media_urls', [])
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            print(f"SMS send error: {str(e)}")
            return jsonify({'error': 'Failed to send SMS'}), 500

    @app.route('/api/sms/send-bulk', methods=['POST'])
    def send_bulk_sms():
        try:
            data = request.json
            sms_service = create_sms_service()
            
            result = sms_service.send_bulk_sms(
                recipients=data.get('recipients', []),
                message_template=data.get('message_template'),
                personalization_data=data.get('personalization_data', [])
            )
            
            return jsonify(result), 200
            
        except Exception as e:
            print(f"Bulk SMS error: {str(e)}")
            return jsonify({'error': 'Failed to send bulk SMS'}), 500

    @app.route('/api/sms/send-maintenance-alert', methods=['POST'])
    def send_maintenance_sms():
        try:
            data = request.json
            sms_service = create_sms_service()
            
            result = sms_service.send_maintenance_alert(
                phone_number=data.get('phone_number'),
                tenant_name=data.get('tenant_name'),
                property_name=data.get('property_name'),
                unit_number=data.get('unit_number'),
                maintenance_type=data.get('maintenance_type'),
                urgency=data.get('urgency', 'normal')
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            print(f"Maintenance SMS error: {str(e)}")
            return jsonify({'error': 'Failed to send maintenance alert'}), 500

    @app.route('/api/sms/send-rent-reminder', methods=['POST'])
    def send_rent_reminder_sms():
        try:
            data = request.json
            sms_service = create_sms_service()
            
            result = sms_service.send_rent_reminder(
                phone_number=data.get('phone_number'),
                tenant_name=data.get('tenant_name'),
                amount_due=float(data.get('amount_due', 0)),
                due_date=data.get('due_date'),
                property_name=data.get('property_name'),
                unit_number=data.get('unit_number')
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            print(f"Rent reminder SMS error: {str(e)}")
            return jsonify({'error': 'Failed to send rent reminder'}), 500

    @app.route('/api/sms/send-emergency-alert', methods=['POST'])
    def send_emergency_alert_sms():
        try:
            data = request.json
            sms_service = create_sms_service()
            
            result = sms_service.send_emergency_alert(
                emergency_contacts=data.get('emergency_contacts', []),
                alert_message=data.get('alert_message'),
                property_name=data.get('property_name')
            )
            
            return jsonify(result), 200
            
        except Exception as e:
            print(f"Emergency alert SMS error: {str(e)}")
            return jsonify({'error': 'Failed to send emergency alert'}), 500

    @app.route('/api/sms/send-security-alert', methods=['POST'])
    def send_security_alert_sms():
        try:
            data = request.json
            sms_service = create_sms_service()
            
            result = sms_service.send_security_alert(
                security_contacts=data.get('security_contacts', []),
                alert_type=data.get('alert_type'),
                location=data.get('location'),
                description=data.get('description'),
                timestamp=data.get('timestamp')
            )
            
            return jsonify(result), 200
            
        except Exception as e:
            print(f"Security alert SMS error: {str(e)}")
            return jsonify({'error': 'Failed to send security alert'}), 500

    @app.route('/api/sms/send-payment-confirmation', methods=['POST'])
    def send_payment_confirmation_sms():
        try:
            data = request.json
            sms_service = create_sms_service()
            
            result = sms_service.send_payment_confirmation(
                phone_number=data.get('phone_number'),
                tenant_name=data.get('tenant_name'),
                amount=float(data.get('amount', 0)),
                transaction_id=data.get('transaction_id'),
                property_name=data.get('property_name'),
                unit_number=data.get('unit_number')
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            print(f"Payment confirmation SMS error: {str(e)}")
            return jsonify({'error': 'Failed to send payment confirmation'}), 500

    @app.route('/api/sms/status/<message_sid>', methods=['GET'])
    def get_sms_status(message_sid):
        try:
            sms_service = create_sms_service()
            result = sms_service.get_message_status(message_sid)
            
            return jsonify(result), 200
            
        except Exception as e:
            print(f"SMS status error: {str(e)}")
            return jsonify({'error': 'Failed to get SMS status'}), 500

    @app.route('/api/sms/test-configuration', methods=['POST'])
    def test_sms_configuration():
        try:
            data = request.json
            phone_number = data.get('phone_number')
            
            if not phone_number:
                return jsonify({'error': 'Phone number is required for testing'}), 400
            
            sms_service = create_sms_service()
            result = sms_service.send_sms(
                phone_number,
                f"EstateCore SMS test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            if result['success']:
                return jsonify({'message': 'SMS configuration test successful', 'result': result}), 200
            else:
                return jsonify({'error': 'SMS configuration test failed', 'result': result}), 500
                
        except Exception as e:
            print(f"SMS test error: {str(e)}")
            return jsonify({'error': 'SMS test failed'}), 500

    # Real Database Integration - Users API
    @app.route('/api/users/db', methods=['GET', 'POST'])
    def handle_users_db():
        if request.method == 'GET':
            try:
                db_service = get_database_service()
                users = db_service.get_users()
                
                # Format users for frontend
                for user in users:
                    user['username'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('email', '')
                
                return jsonify(users)
            except Exception as e:
                print(f"Users fetch error: {str(e)}")
                # Fallback to mock data
                return jsonify([
                    {
                        'id': 1,
                        'username': 'Admin User',
                        'email': 'admin@estatecore.com',
                        'role': 'admin',
                        'is_active': True,
                        'created_at': datetime.utcnow().isoformat()
                    }
                ])
        
        elif request.method == 'POST':
            try:
                data = request.json
                db_service = get_database_service()
                
                # Prepare user data
                user_data = {
                    'email': data.get('email'),
                    'first_name': data.get('first_name', ''),
                    'last_name': data.get('last_name', ''),
                    'phone': data.get('phone', ''),
                    'role': data.get('role', 'tenant')
                }
                
                # Split username if provided
                if data.get('username') and not user_data['first_name']:
                    username_parts = data['username'].split(' ', 1)
                    user_data['first_name'] = username_parts[0]
                    user_data['last_name'] = username_parts[1] if len(username_parts) > 1 else ''
                
                user = db_service.create_user(user_data)
                return jsonify({'message': 'User created successfully', 'user': user}), 201
                
            except Exception as e:
                print(f"User creation error: {str(e)}")
                return jsonify({'error': 'Failed to create user'}), 500

    @app.route('/api/users/db/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
    def handle_user_db_detail(user_id):
        db_service = get_database_service()
        
        if request.method == 'GET':
            try:
                user = db_service.get_user_by_id(user_id)
                if user:
                    return jsonify(user)
                else:
                    return jsonify({'error': 'User not found'}), 404
            except Exception as e:
                return jsonify({'error': 'Failed to fetch user'}), 500
        
        elif request.method == 'PUT':
            try:
                data = request.json
                success = db_service.update_user(user_id, data)
                if success:
                    return jsonify({'message': 'User updated successfully'})
                else:
                    return jsonify({'error': 'User not found'}), 404
            except Exception as e:
                return jsonify({'error': 'Failed to update user'}), 500
        
        elif request.method == 'DELETE':
            try:
                success = db_service.delete_user(user_id)
                if success:
                    return jsonify({'message': 'User deleted successfully'})
                else:
                    return jsonify({'error': 'User not found'}), 404
            except Exception as e:
                return jsonify({'error': 'Failed to delete user'}), 500

    # Real Database Integration - Properties API
    @app.route('/api/properties', methods=['GET', 'POST'])
    def handle_properties_db():
        if request.method == 'GET':
            try:
                db_service = get_database_service()
                properties = db_service.get_properties()
                return jsonify(properties)
            except Exception as e:
                print(f"Properties fetch error: {str(e)}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                db_service = get_database_service()
                
                property_data = {
                    'name': data.get('name'),
                    'address': data.get('address'),
                    'city': data.get('city'),
                    'state': data.get('state'),
                    'zip_code': data.get('zip_code'),
                    'property_type': data.get('property_type', 'APARTMENT'),
                    'total_units': data.get('total_units', 0),
                    'year_built': data.get('year_built'),
                    'square_footage': data.get('square_footage'),
                    'description': data.get('description', ''),
                    'amenities': data.get('amenities', [])
                }
                
                property_obj = db_service.create_property(property_data)
                return jsonify({'message': 'Property created successfully', 'property': property_obj}), 201
                
            except Exception as e:
                print(f"Property creation error: {str(e)}")
                return jsonify({'error': 'Failed to create property'}), 500

    @app.route('/api/properties/<int:property_id>', methods=['PUT'])
    def update_property_db(property_id):
        """Update a property using database service"""
        try:
            data = request.json
            db_service = get_database_service()
            
            property_data = {
                'name': data.get('name'),
                'address': data.get('address'),
                'city': data.get('city'),
                'state': data.get('state'),
                'zip_code': data.get('zip_code'),
                'property_type': data.get('property_type'),
                'total_units': data.get('total_units'),
                'year_built': data.get('year_built'),
                'square_footage': data.get('square_footage'),
                'description': data.get('description'),
                'amenities': data.get('amenities', [])
            }
            
            # Remove None values to avoid overwriting existing data with None
            property_data = {k: v for k, v in property_data.items() if v is not None}
            
            updated_property = db_service.update_property(property_id, property_data)
            return jsonify({'message': 'Property updated successfully', 'property': updated_property})
            
        except Exception as e:
            print(f"Property update error: {str(e)}")
            return jsonify({'error': 'Failed to update property'}), 500

    @app.route('/api/properties/<int:property_id>', methods=['DELETE'])
    def delete_property_db(property_id):
        """Delete a property using database service"""
        try:
            db_service = get_database_service()
            
            # Check if property exists and get its details
            try:
                property_details = db_service.get_property_by_id(property_id)
                if not property_details:
                    return jsonify({'error': 'Property not found'}), 404
            except Exception:
                return jsonify({'error': 'Property not found'}), 404
            
            # Delete the property (this might be a soft delete depending on the service implementation)
            result = db_service.delete_property(property_id)
            
            if result:
                return jsonify({'message': 'Property deleted successfully', 'id': property_id})
            else:
                return jsonify({'error': 'Failed to delete property'}), 500
            
        except Exception as e:
            print(f"Property deletion error: {str(e)}")
            return jsonify({'error': 'Failed to delete property'}), 500

    # Real Database Integration - Tenants API  
    @app.route('/api/tenants', methods=['GET', 'POST'])
    def handle_tenants_db():
        if request.method == 'GET':
            try:
                db_service = get_database_service()
                property_id = request.args.get('property_id')
                tenants = db_service.get_tenants(property_id=int(property_id) if property_id else None)
                return jsonify(tenants)
            except Exception as e:
                print(f"Tenants fetch error: {str(e)}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                db_service = get_database_service()
                
                tenant_data = {
                    'user_id': data.get('user_id'),
                    'property_id': data.get('property_id'),
                    'unit_number': data.get('unit_number'),
                    'lease_start_date': data.get('lease_start_date'),
                    'lease_end_date': data.get('lease_end_date'),
                    'rent_amount': data.get('rent_amount', 0),
                    'security_deposit': data.get('security_deposit', 0),
                    'status': data.get('status', 'active'),
                    'move_in_date': data.get('move_in_date'),
                    'emergency_contact_name': data.get('emergency_contact_name', ''),
                    'emergency_contact_phone': data.get('emergency_contact_phone', '')
                }
                
                tenant = db_service.create_tenant(tenant_data)
                return jsonify({'message': 'Tenant created successfully', 'tenant': tenant}), 201
                
            except Exception as e:
                print(f"Tenant creation error: {str(e)}")
                return jsonify({'error': 'Failed to create tenant'}), 500

    # Real Database Integration - Maintenance API
    @app.route('/api/maintenance', methods=['GET', 'POST'])
    def handle_maintenance_db():
        if request.method == 'GET':
            try:
                db_service = get_database_service()
                property_id = request.args.get('property_id')
                status = request.args.get('status')
                
                requests = db_service.get_maintenance_requests(
                    property_id=int(property_id) if property_id else None,
                    status=status
                )
                return jsonify(requests)
            except Exception as e:
                print(f"Maintenance fetch error: {str(e)}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                db_service = get_database_service()
                
                # Validate required fields
                if not data.get('property_id'):
                    return jsonify({'error': 'property_id is required'}), 400
                if not data.get('title'):
                    return jsonify({'error': 'title is required'}), 400
                
                request_data = {
                    'property_id': data.get('property_id'),
                    'tenant_id': data.get('tenant_id'),
                    'unit_number': data.get('unit_number'),
                    'title': data.get('title'),
                    'description': data.get('description', ''),
                    'priority': data.get('priority', 'medium'),
                    'status': data.get('status', 'open'),
                    'category': data.get('category', 'general')
                }
                
                maintenance_request = db_service.create_maintenance_request(request_data)
                
                # Send notification if configured
                try:
                    email_service = create_email_service()
                    email_service.send_maintenance_notification(
                        to_emails=['maintenance@estatecore.com'],
                        notification_type='Request',
                        title=data.get('title'),
                        description=data.get('description', ''),
                        property_name=f"Property {data.get('property_id')}",
                        unit_number=data.get('unit_number', 'N/A'),
                        priority=data.get('priority', 'medium')
                    )
                except Exception as e:
                    print(f"Notification send error: {e}")
                
                return jsonify({'message': 'Maintenance request created successfully', 'request': maintenance_request}), 201
                
            except Exception as e:
                print(f"Maintenance creation error: {str(e)}")
                return jsonify({'error': 'Failed to create maintenance request'}), 500

    # Real Database Integration - Payments API
    @app.route('/api/payments', methods=['GET', 'POST'])
    def handle_payments_db():
        if request.method == 'GET':
            try:
                db_service = get_database_service()
                tenant_id = request.args.get('tenant_id')
                property_id = request.args.get('property_id')
                
                payments = db_service.get_payments(
                    tenant_id=int(tenant_id) if tenant_id else None,
                    property_id=int(property_id) if property_id else None
                )
                return jsonify(payments)
            except Exception as e:
                print(f"Payments fetch error: {str(e)}")
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                db_service = get_database_service()
                
                payment_data = {
                    'tenant_id': data.get('tenant_id'),
                    'property_id': data.get('property_id'),
                    'amount': data.get('amount'),
                    'payment_type': data.get('payment_type', 'rent'),
                    'payment_method': data.get('payment_method', 'online'),
                    'payment_date': data.get('payment_date'),
                    'due_date': data.get('due_date'),
                    'status': data.get('status', 'completed'),
                    'transaction_id': data.get('transaction_id'),
                    'stripe_payment_intent_id': data.get('stripe_payment_intent_id'),
                    'description': data.get('description', '')
                }
                
                payment = db_service.create_payment(payment_data)
                
                # Send confirmation if configured
                try:
                    if data.get('send_confirmation') and data.get('tenant_email'):
                        email_service = create_email_service()
                        email_service.send_payment_receipt(
                            email=data.get('tenant_email'),
                            recipient_name=data.get('tenant_name', 'Tenant'),
                            amount=float(data.get('amount', 0)),
                            property_name=f"Property {data.get('property_id')}",
                            unit_number=data.get('unit_number'),
                            transaction_id=data.get('transaction_id')
                        )
                except Exception as e:
                    print(f"Payment confirmation error: {e}")
                
                return jsonify({'message': 'Payment recorded successfully', 'payment': payment}), 201
                
            except Exception as e:
                print(f"Payment creation error: {str(e)}")
                return jsonify({'error': 'Failed to record payment'}), 500

    # Real Database Integration - Analytics API
    @app.route('/api/analytics/database', methods=['GET'])
    def get_database_analytics():
        try:
            db_service = get_database_service()
            days = int(request.args.get('days', 30))
            
            analytics_data = db_service.get_analytics_data(days)
            return jsonify(analytics_data)
            
        except Exception as e:
            print(f"Database analytics error: {str(e)}")
            return jsonify({'error': 'Failed to fetch analytics'}), 500

    # Messages API
    @app.route('/api/messages', methods=['GET', 'POST'])
    def handle_messages():
        if request.method == 'GET':
            try:
                user_id = request.args.get('user_id')
                # Mock messages data
                mock_messages = [
                    {
                        'id': 1,
                        'from': 'Property Manager',
                        'to': 'tenant@example.com',
                        'subject': 'Rent Reminder',
                        'message': 'This is a friendly reminder that your rent payment is due on the 1st of each month.',
                        'timestamp': datetime.utcnow().isoformat(),
                        'status': 'read'
                    },
                    {
                        'id': 2,
                        'from': 'Maintenance Team',
                        'to': 'tenant@example.com',
                        'subject': 'Maintenance Request Update',
                        'message': 'Your maintenance request has been completed. Please let us know if you need anything else.',
                        'timestamp': datetime.utcnow().isoformat(),
                        'status': 'unread'
                    }
                ]
                return jsonify(mock_messages)
            except Exception as e:
                return jsonify([])
        
        elif request.method == 'POST':
            try:
                data = request.json
                # Mock message creation
                return jsonify({
                    'message': 'Message sent successfully',
                    'id': 1
                }), 201
            except Exception as e:
                return jsonify({'error': 'Failed to send message'}), 500

    # File Upload and Document Management API
    @app.route('/api/files/upload', methods=['POST'])
    def upload_file():
        """Handle single file upload"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Get additional metadata from form data
            metadata = {
                'property_id': request.form.get('property_id'),
                'tenant_id': request.form.get('tenant_id'),
                'category': request.form.get('category', 'general'),
                'description': request.form.get('description', ''),
                'uploaded_by': request.form.get('uploaded_by')
            }
            
            # Save file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            # Upload using file storage service
            file_service = create_file_storage_service()
            result = file_service.upload_file(temp_path, file.filename, metadata)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if result['success']:
                # Store file info in database
                file_data = result['file']
                try:
                    db.session.execute(db.text("""
                        INSERT INTO documents (name, file_path, file_size, file_type, category,
                                             description, property_id, tenant_id, uploaded_by,
                                             checksum, created_at, updated_at)
                        VALUES (:name, :file_path, :file_size, :file_type, :category,
                                :description, :property_id, :tenant_id, :uploaded_by,
                                :checksum, :created_at, :updated_at)
                    """), {
                        'name': file_data['original_filename'],
                        'file_path': file_data['relative_path'],
                        'file_size': file_data['file_size'],
                        'file_type': file_data['mime_type'],
                        'category': file_data['category'],
                        'description': metadata.get('description', ''),
                        'property_id': metadata.get('property_id'),
                        'tenant_id': metadata.get('tenant_id'),
                        'uploaded_by': metadata.get('uploaded_by'),
                        'checksum': file_data['file_hash'],
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    })
                    db.session.commit()
                except Exception as db_error:
                    print(f"Database error storing file info: {db_error}")
                    # Continue even if DB storage fails
                
                return jsonify({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'file': file_data
                })
            else:
                return jsonify({'error': result['error']}), 400
                
        except Exception as e:
            print(f"File upload error: {e}")
            return jsonify({'error': 'File upload failed'}), 500
    
    @app.route('/api/files/upload-multiple', methods=['POST'])
    def upload_multiple_files():
        """Handle multiple file upload"""
        try:
            if 'files' not in request.files:
                return jsonify({'error': 'No files provided'}), 400
            
            files = request.files.getlist('files')
            if not files or all(file.filename == '' for file in files):
                return jsonify({'error': 'No files selected'}), 400
            
            # Get shared metadata
            shared_metadata = {
                'property_id': request.form.get('property_id'),
                'tenant_id': request.form.get('tenant_id'),
                'category': request.form.get('category', 'general'),
                'uploaded_by': request.form.get('uploaded_by')
            }
            
            file_service = create_file_storage_service()
            upload_results = []
            
            for file in files:
                if file.filename:
                    try:
                        # Save file temporarily
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                            file.save(temp_file.name)
                            temp_path = temp_file.name
                        
                        # Upload using file storage service
                        result = file_service.upload_file(temp_path, file.filename, shared_metadata)
                        
                        # Clean up temp file
                        os.unlink(temp_path)
                        
                        if result['success']:
                            # Store file info in database
                            file_data = result['file']
                            try:
                                db.session.execute(db.text("""
                                    INSERT INTO documents (name, file_path, file_size, file_type, category,
                                                         description, property_id, tenant_id, uploaded_by,
                                                         checksum, created_at, updated_at)
                                    VALUES (:name, :file_path, :file_size, :file_type, :category,
                                            :description, :property_id, :tenant_id, :uploaded_by,
                                            :checksum, :created_at, :updated_at)
                                """), {
                                    'name': file_data['original_filename'],
                                    'file_path': file_data['relative_path'],
                                    'file_size': file_data['file_size'],
                                    'file_type': file_data['mime_type'],
                                    'category': file_data['category'],
                                    'description': shared_metadata.get('description', ''),
                                    'property_id': shared_metadata.get('property_id'),
                                    'tenant_id': shared_metadata.get('tenant_id'),
                                    'uploaded_by': shared_metadata.get('uploaded_by'),
                                    'checksum': file_data['file_hash'],
                                    'created_at': datetime.utcnow(),
                                    'updated_at': datetime.utcnow()
                                })
                                db.session.commit()
                            except Exception as db_error:
                                print(f"Database error storing file info: {db_error}")
                        
                        upload_results.append({
                            'filename': file.filename,
                            'success': result['success'],
                            'result': result
                        })
                        
                    except Exception as file_error:
                        upload_results.append({
                            'filename': file.filename,
                            'success': False,
                            'error': str(file_error)
                        })
            
            successful_uploads = sum(1 for r in upload_results if r['success'])
            
            return jsonify({
                'message': f'{successful_uploads}/{len(upload_results)} files uploaded successfully',
                'results': upload_results
            })
                
        except Exception as e:
            print(f"Multiple file upload error: {e}")
            return jsonify({'error': 'Multiple file upload failed'}), 500
    
    @app.route('/api/files/documents', methods=['GET'])
    def get_documents():
        """Get list of uploaded documents"""
        try:
            property_id = request.args.get('property_id')
            tenant_id = request.args.get('tenant_id')
            category = request.args.get('category')
            
            # Build query
            query = """
                SELECT d.*, p.name as property_name, 
                       CONCAT(u.first_name, ' ', u.last_name) as uploaded_by_name
                FROM documents d
                LEFT JOIN properties p ON d.property_id = p.id
                LEFT JOIN users u ON d.uploaded_by = u.id
                WHERE 1=1
            """
            params = {}
            
            if property_id:
                query += " AND d.property_id = :property_id"
                params['property_id'] = property_id
            
            if tenant_id:
                query += " AND d.tenant_id = :tenant_id"
                params['tenant_id'] = tenant_id
            
            if category:
                query += " AND d.category = :category"
                params['category'] = category
            
            query += " ORDER BY d.created_at DESC"
            
            result = db.session.execute(db.text(query), params).fetchall()
            
            documents = []
            file_service = create_file_storage_service()
            
            for row in result:
                doc_data = {
                    'id': row[0],
                    'name': row[1],
                    'file_path': row[2],
                    'file_size': row[3],
                    'file_type': row[4],
                    'category': row[5],
                    'description': row[6],
                    'property_id': row[7],
                    'tenant_id': row[8],
                    'folder_id': row[9],
                    'uploaded_by': row[10],
                    'is_public': row[11],
                    'tags': row[12],
                    'version': row[13],
                    'checksum': row[14],
                    'created_at': row[15].isoformat() if row[15] else None,
                    'updated_at': row[16].isoformat() if row[16] else None,
                    'property_name': row[17] if len(row) > 17 else None,
                    'uploaded_by_name': row[18] if len(row) > 18 else None,
                    'download_url': file_service.get_file_url(row[2]) if row[2] else None
                }
                documents.append(doc_data)
            
            return jsonify(documents)
            
        except Exception as e:
            print(f"Get documents error: {e}")
            return jsonify([])
    
    @app.route('/api/files/documents/<int:doc_id>', methods=['DELETE'])
    def delete_document(doc_id):
        """Delete a document"""
        try:
            # Get document info first
            result = db.session.execute(db.text("""
                SELECT file_path FROM documents WHERE id = :doc_id
            """), {'doc_id': doc_id}).fetchone()
            
            if not result:
                return jsonify({'error': 'Document not found'}), 404
            
            file_path = result[0]
            
            # Delete from file system
            file_service = create_file_storage_service()
            full_path = os.path.join(file_service.config.storage_path, file_path)
            file_service.delete_file(full_path)
            
            # Delete from database
            db.session.execute(db.text("""
                DELETE FROM documents WHERE id = :doc_id
            """), {'doc_id': doc_id})
            db.session.commit()
            
            return jsonify({'message': 'Document deleted successfully'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Delete document error: {e}")
            return jsonify({'error': 'Failed to delete document'}), 500
    
    @app.route('/api/files/storage-stats', methods=['GET'])
    def get_storage_stats():
        """Get file storage statistics"""
        try:
            file_service = create_file_storage_service()
            stats = file_service.get_storage_stats()
            
            # Add database statistics
            try:
                doc_count = db.session.execute(db.text("""
                    SELECT COUNT(*) FROM documents
                """)).scalar()
                stats['database_records'] = doc_count or 0
            except:
                stats['database_records'] = 0
            
            return jsonify(stats)
            
        except Exception as e:
            print(f"Storage stats error: {e}")
            return jsonify({'error': 'Failed to get storage statistics'}), 500
    
    @app.route('/api/files/create-archive', methods=['POST'])
    def create_download_archive():
        """Create downloadable archive of multiple files"""
        try:
            data = request.json
            document_ids = data.get('document_ids', [])
            
            if not document_ids:
                return jsonify({'error': 'No documents selected'}), 400
            
            # Get file paths from database
            placeholders = ','.join([':id' + str(i) for i in range(len(document_ids))])
            params = {f'id{i}': doc_id for i, doc_id in enumerate(document_ids)}
            
            result = db.session.execute(db.text(f"""
                SELECT file_path, name FROM documents 
                WHERE id IN ({placeholders})
            """), params).fetchall()
            
            if not result:
                return jsonify({'error': 'No valid documents found'}), 404
            
            # Build full file paths
            file_service = create_file_storage_service()
            file_paths = []
            for row in result:
                full_path = os.path.join(file_service.config.storage_path, row[0])
                if os.path.exists(full_path):
                    file_paths.append(full_path)
            
            if not file_paths:
                return jsonify({'error': 'No files found on disk'}), 404
            
            # Create archive
            archive_result = file_service.create_download_archive(file_paths)
            
            if archive_result['success']:
                return jsonify({
                    'success': True,
                    'archive_name': archive_result['archive_name'],
                    'download_url': archive_result['download_url'],
                    'files_count': archive_result['files_count'],
                    'archive_size': archive_result['archive_size']
                })
            else:
                return jsonify({'error': archive_result['error']}), 500
                
        except Exception as e:
            print(f"Create archive error: {e}")
            return jsonify({'error': 'Failed to create archive'}), 500
    
    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        """Serve uploaded files"""
        try:
            file_service = create_file_storage_service()
            file_path = os.path.join(file_service.config.storage_path, filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404
            
            # Security check - ensure file is within upload directory
            if not os.path.abspath(file_path).startswith(os.path.abspath(file_service.config.storage_path)):
                return jsonify({'error': 'Access denied'}), 403
            
            from flask import send_file
            return send_file(file_path)
            
        except Exception as e:
            print(f"File serve error: {e}")
            return jsonify({'error': 'Failed to serve file'}), 500

    # Role and Permission Management API
    @app.route('/api/auth/login/simple', methods=['POST'])
    def simple_login():
        """Simple login endpoint for testing"""
        try:
            data = request.json
            email = data.get('email', '')
            password = data.get('password', '')
            
            # Mock authentication - in production use proper password hashing
            mock_users = {
                'admin@estatecore.com': {'id': 1, 'role': 'super_admin', 'token': 'admin_token'},
                'manager@estatecore.com': {'id': 2, 'role': 'property_manager', 'token': 'manager_token'},
                'tenant@estatecore.com': {'id': 3, 'role': 'tenant', 'token': 'tenant_token'}
            }
            
            user = mock_users.get(email)
            if user and password == 'password':  # Mock password check
                # Load user permissions
                load_user_permissions(
                    user_id=user['id'],
                    role_name=user['role'],
                    property_access=[1, 2, 3] if user['role'] != 'tenant' else [1],
                    tenant_access=[user['id']] if user['role'] == 'tenant' else []
                )
                
                return jsonify({
                    'success': True,
                    'token': user['token'],
                    'user': {
                        'id': user['id'],
                        'email': email,
                        'role': user['role']
                    }
                })
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
                
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    @app.route('/api/auth/me', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_current_user():
        """Get current user information with permissions"""
        try:
            from flask import g
            user_id = g.user_id
            
            # Get user role info
            role_info = get_user_role_info(user_id)
            
            # Get user details from database
            result = db.session.execute(db.text("""
                SELECT id, email, first_name, last_name, role, is_active, created_at
                FROM users WHERE id = :user_id
            """), {'user_id': user_id}).fetchone()
            
            if result:
                user_data = {
                    'id': result[0],
                    'email': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'role': result[4],
                    'is_active': result[5],
                    'created_at': result[6].isoformat() if result[6] else None,
                    'permissions': role_info.get('permissions', []),
                    'property_access': role_info.get('property_access', []),
                    'tenant_access': role_info.get('tenant_access', [])
                }
                return jsonify(user_data)
            else:
                return jsonify({'error': 'User not found'}), 404
                
        except Exception as e:
            print(f"Get current user error: {e}")
            return jsonify({'error': 'Failed to get user information'}), 500
    
    @app.route('/api/permissions/roles', methods=['GET'])
    @require_permission(Permission.MANAGE_ROLES)
    def get_all_roles():
        """Get all available roles and their permissions"""
        try:
            permission_service = get_permission_service()
            roles_data = []
            
            for role, role_def in permission_service.get_all_roles().items():
                roles_data.append({
                    'id': role.value,
                    'name': role_def.name,
                    'display_name': role_def.display_name,
                    'description': role_def.description,
                    'permissions': [perm.value for perm in role_def.permissions],
                    'is_system_role': role_def.is_system_role,
                    'created_at': role_def.created_at.isoformat()
                })
            
            return jsonify(roles_data)
            
        except Exception as e:
            print(f"Get roles error: {e}")
            return jsonify({'error': 'Failed to get roles'}), 500
    
    @app.route('/api/permissions/permissions', methods=['GET'])
    @require_permission(Permission.MANAGE_ROLES)
    def get_all_permissions():
        """Get all available permissions"""
        try:
            permissions_data = []
            
            for permission in Permission:
                # Group permissions by category
                category = permission.value.split('_')[0] if '_' in permission.value else 'general'
                permissions_data.append({
                    'id': permission.value,
                    'name': permission.value,
                    'display_name': permission.value.replace('_', ' ').title(),
                    'category': category,
                    'description': f"Permission to {permission.value.replace('_', ' ')}"
                })
            
            # Group by category
            grouped_permissions = {}
            for perm in permissions_data:
                category = perm['category']
                if category not in grouped_permissions:
                    grouped_permissions[category] = []
                grouped_permissions[category].append(perm)
            
            return jsonify(grouped_permissions)
            
        except Exception as e:
            print(f"Get permissions error: {e}")
            return jsonify({'error': 'Failed to get permissions'}), 500
    
    @app.route('/api/users/<int:user_id>/role', methods=['PUT'])
    @require_permission(Permission.MANAGE_ROLES)
    def update_user_role(user_id):
        """Update user's role and permissions"""
        try:
            data = request.json
            new_role = data.get('role')
            property_access = data.get('property_access', [])
            tenant_access = data.get('tenant_access', [])
            additional_permissions = data.get('additional_permissions', [])
            
            if not new_role:
                return jsonify({'error': 'Role is required'}), 400
            
            try:
                role_enum = Role(new_role)
            except ValueError:
                return jsonify({'error': 'Invalid role'}), 400
            
            # Update user role in database
            db.session.execute(db.text("""
                UPDATE users 
                SET role = :role, updated_at = :updated_at
                WHERE id = :user_id
            """), {
                'user_id': user_id,
                'role': new_role,
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
            
            # Update user permissions in cache if user is currently logged in
            permission_service = get_permission_service()
            if user_id in permission_service.user_contexts:
                try:
                    additional_perms = [Permission(perm) for perm in additional_permissions]
                except ValueError:
                    additional_perms = []
                
                load_user_permissions(
                    user_id=user_id,
                    role_name=new_role,
                    property_access=property_access,
                    tenant_access=tenant_access,
                    additional_permissions=additional_permissions
                )
            
            return jsonify({
                'message': 'User role updated successfully',
                'user_id': user_id,
                'role': new_role
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Update user role error: {e}")
            return jsonify({'error': 'Failed to update user role'}), 500
    
    @app.route('/api/permissions/check', methods=['POST'])
    def check_permissions():
        """Check if current user has specific permissions"""
        try:
            from flask import g
            user_id = g.user_id
            
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            data = request.json
            permissions_to_check = data.get('permissions', [])
            resource_type = data.get('resource_type')
            resource_id = data.get('resource_id')
            
            permission_service = get_permission_service()
            results = {}
            
            for perm_name in permissions_to_check:
                try:
                    permission = Permission(perm_name)
                    has_perm = permission_service.has_permission(
                        user_id, permission, resource_id, resource_type
                    )
                    results[perm_name] = has_perm
                except ValueError:
                    results[perm_name] = False
            
            return jsonify(results)
            
        except Exception as e:
            print(f"Check permissions error: {e}")
            return jsonify({'error': 'Failed to check permissions'}), 500
    
    @app.route('/api/users/<int:user_id>/permissions', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_user_permissions(user_id):
        """Get user's permissions and access rights"""
        try:
            from flask import g
            current_user_id = g.user_id
            
            permission_service = get_permission_service()
            
            # Check if current user can access target user
            if not permission_service.can_access_user(current_user_id, user_id):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Get user role info
            role_info = get_user_role_info(user_id)
            
            if not role_info:
                return jsonify({'error': 'User permissions not found'}), 404
            
            # Get accessible properties and tenants
            accessible_properties = permission_service.get_accessible_properties(user_id)
            
            return jsonify({
                'user_id': user_id,
                'role': role_info.get('role'),
                'display_name': role_info.get('display_name'),
                'permissions': role_info.get('permissions', []),
                'property_access': role_info.get('property_access', []),
                'tenant_access': role_info.get('tenant_access', []),
                'accessible_properties': accessible_properties
            })
            
        except Exception as e:
            print(f"Get user permissions error: {e}")
            return jsonify({'error': 'Failed to get user permissions'}), 500

    # Rent Collection and Payment Processing API
    @app.route('/api/rent/invoices/generate_legacy', methods=['POST'])
    @require_permission(Permission.CREATE_PAYMENT)
    def generate_rent_invoices_legacy():
        """Generate monthly rent invoices"""
        try:
            data = request.json or {}
            target_month = data.get('target_month')
            
            rent_service = get_rent_collection_service()
            
            if target_month:
                from datetime import datetime
                target_date = datetime.strptime(target_month, '%Y-%m-%d').date()
                result = rent_service.generate_monthly_invoices(target_date)
            else:
                result = rent_service.generate_monthly_invoices()
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f"Generated {result['invoices_generated']} invoices",
                    'data': result
                })
            else:
                return jsonify({'error': result.get('error', 'Invoice generation failed')}), 500
                
        except Exception as e:
            print(f"Invoice generation error: {e}")
            return jsonify({'error': 'Failed to generate invoices'}), 500
    
    @app.route('/api/rent/dashboard', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_rent_collection_dashboard():
        """Get rent collection dashboard data"""
        try:
            rent_service = get_rent_collection_service()
            dashboard_data = rent_service.get_collection_dashboard_data()
            
            return jsonify(dashboard_data)
            
        except Exception as e:
            print(f"Rent dashboard error: {e}")
            return jsonify({'error': 'Failed to get dashboard data'}), 500
    
    @app.route('/api/rent/invoices', methods=['GET'])
    @require_permission(Permission.READ_PAYMENT)
    def get_rent_invoices():
        """Get rent invoices with filtering"""
        try:
            # Get query parameters
            tenant_id = request.args.get('tenant_id', type=int)
            property_id = request.args.get('property_id', type=int)
            status = request.args.get('status')
            month = request.args.get('month')
            limit = request.args.get('limit', default=50, type=int)
            
            # Build query
            query = """
                SELECT ri.*, t.unit_number, prop.name as property_name,
                       u.first_name, u.last_name, u.email as tenant_email
                FROM rent_invoices ri
                LEFT JOIN tenants t ON ri.tenant_id = t.id
                LEFT JOIN properties prop ON ri.property_id = prop.id
                LEFT JOIN users u ON t.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if tenant_id:
                query += " AND ri.tenant_id = ?"
                params.append(tenant_id)
            
            if property_id:
                query += " AND ri.property_id = ?"
                params.append(property_id)
            
            if status:
                query += " AND ri.status = ?"
                params.append(status)
            
            if month:
                query += " AND strftime('%Y-%m', ri.due_date) = ?"
                params.append(month)
            
            query += " ORDER BY ri.due_date DESC LIMIT ?"
            params.append(limit)
            
            # Execute query (fallback to mock data if no database)
            try:
                result = db.session.execute(db.text(query), params).fetchall()
                
                invoices = []
                for row in result:
                    invoice_data = {
                        'id': row[0],
                        'tenant_id': row[1],
                        'property_id': row[2],
                        'unit_number': row[3],
                        'amount_due': float(row[4]),
                        'due_date': row[5],
                        'late_fee': float(row[6]) if row[6] else 0,
                        'total_amount': float(row[7]),
                        'amount_paid': float(row[8]) if row[8] else 0,
                        'status': row[9],
                        'payment_status': row[10],
                        'description': row[11],
                        'created_at': row[12],
                        'property_name': row[16] if len(row) > 16 else None,
                        'tenant_name': f"{row[17]} {row[18]}" if len(row) > 18 and row[17] and row[18] else None,
                        'tenant_email': row[19] if len(row) > 19 else None
                    }
                    invoices.append(invoice_data)
                
                return jsonify(invoices)
                
            except Exception:
                # Return mock data if database query fails
                mock_invoices = [
                    {
                        'id': 'INV-202412-0001-abc123',
                        'tenant_id': 1,
                        'property_id': 1,
                        'unit_number': '101',
                        'amount_due': 1500.00,
                        'due_date': '2024-12-01',
                        'late_fee': 0.00,
                        'total_amount': 1500.00,
                        'amount_paid': 0.00,
                        'status': 'current',
                        'payment_status': 'pending',
                        'description': 'Rent for December 2024 - Unit 101',
                        'created_at': '2024-11-25T00:00:00',
                        'property_name': 'Sunset Apartments',
                        'tenant_name': 'John Doe',
                        'tenant_email': 'john.doe@example.com'
                    },
                    {
                        'id': 'INV-202412-0002-def456',
                        'tenant_id': 2,
                        'property_id': 1,
                        'unit_number': '102',
                        'amount_due': 1600.00,
                        'due_date': '2024-12-01',
                        'late_fee': 0.00,
                        'total_amount': 1600.00,
                        'amount_paid': 1600.00,
                        'status': 'paid',
                        'payment_status': 'completed',
                        'description': 'Rent for December 2024 - Unit 102',
                        'created_at': '2024-11-25T00:00:00',
                        'property_name': 'Sunset Apartments',
                        'tenant_name': 'Jane Smith',
                        'tenant_email': 'jane.smith@example.com'
                    }
                ]
                return jsonify(mock_invoices)
            
        except Exception as e:
            print(f"Get rent invoices error: {e}")
            return jsonify({'error': 'Failed to get rent invoices'}), 500
    
    @app.route('/api/rent/invoices/<invoice_id>/pay', methods=['POST'])
    @require_permission(Permission.CREATE_PAYMENT)
    def process_rent_payment(invoice_id):
        """Process rent payment"""
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['amount', 'payment_method']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Process payment
            rent_service = get_rent_collection_service()
            result = rent_service.process_payment(invoice_id, data)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Payment processed successfully',
                    'transaction_id': result.get('transaction_id'),
                    'amount_paid': result.get('amount_paid')
                })
            else:
                return jsonify({'error': result.get('error', 'Payment processing failed')}), 400
                
        except Exception as e:
            print(f"Payment processing error: {e}")
            return jsonify({'error': 'Failed to process payment'}), 500
    
    @app.route('/api/rent/reminders/send', methods=['POST'])
    @require_permission(Permission.SEND_NOTIFICATIONS)
    def send_rent_reminders():
        """Send rent payment reminders"""
        try:
            data = request.json or {}
            reminder_type = data.get('type', 'all')
            
            rent_service = get_rent_collection_service()
            result = rent_service.send_rent_reminders(reminder_type)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f"Sent {result['reminders_sent']} reminders",
                    'data': result
                })
            else:
                return jsonify({'error': result.get('error', 'Failed to send reminders')}), 500
                
        except Exception as e:
            print(f"Rent reminders error: {e}")
            return jsonify({'error': 'Failed to send reminders'}), 500
    
    @app.route('/api/rent/payments', methods=['GET'])
    @require_permission(Permission.READ_PAYMENT)
    def get_rent_payments():
        """Get rent payment history"""
        try:
            # Get query parameters
            tenant_id = request.args.get('tenant_id', type=int)
            property_id = request.args.get('property_id', type=int)
            status = request.args.get('status')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            limit = request.args.get('limit', default=50, type=int)
            
            # Build query for payment transactions
            query = """
                SELECT pt.*, ri.unit_number, prop.name as property_name,
                       u.first_name, u.last_name, u.email as tenant_email
                FROM payment_transactions pt
                LEFT JOIN rent_invoices ri ON pt.invoice_id = ri.id
                LEFT JOIN tenants t ON ri.tenant_id = t.id
                LEFT JOIN properties prop ON ri.property_id = prop.id
                LEFT JOIN users u ON t.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if tenant_id:
                query += " AND pt.tenant_id = ?"
                params.append(tenant_id)
            
            if status:
                query += " AND pt.status = ?"
                params.append(status)
            
            if start_date:
                query += " AND DATE(pt.created_at) >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(pt.created_at) <= ?"
                params.append(end_date)
            
            query += " ORDER BY pt.created_at DESC LIMIT ?"
            params.append(limit)
            
            # Execute query (fallback to mock data)
            try:
                result = db.session.execute(db.text(query), params).fetchall()
                
                payments = []
                for row in result:
                    payment_data = {
                        'id': row[0],
                        'invoice_id': row[1],
                        'tenant_id': row[2],
                        'amount': float(row[3]),
                        'payment_method': row[4],
                        'status': row[5],
                        'transaction_id': row[6],
                        'created_at': row[7],
                        'processed_at': row[8],
                        'description': row[9],
                        'unit_number': row[10] if len(row) > 10 else None,
                        'property_name': row[11] if len(row) > 11 else None,
                        'tenant_name': f"{row[12]} {row[13]}" if len(row) > 13 and row[12] and row[13] else None,
                        'tenant_email': row[14] if len(row) > 14 else None
                    }
                    payments.append(payment_data)
                
                return jsonify(payments)
                
            except Exception:
                # Return mock data
                mock_payments = [
                    {
                        'id': 'TXN-123456789',
                        'invoice_id': 'INV-202412-0002-def456',
                        'tenant_id': 2,
                        'amount': 1600.00,
                        'payment_method': 'credit_card',
                        'status': 'completed',
                        'transaction_id': 'stripe_txn_abc123',
                        'created_at': '2024-11-28T10:30:00',
                        'processed_at': '2024-11-28T10:30:15',
                        'description': 'Rent payment for invoice INV-202412-0002-def456',
                        'unit_number': '102',
                        'property_name': 'Sunset Apartments',
                        'tenant_name': 'Jane Smith',
                        'tenant_email': 'jane.smith@example.com'
                    }
                ]
                return jsonify(mock_payments)
            
        except Exception as e:
            print(f"Get rent payments error: {e}")
            return jsonify({'error': 'Failed to get rent payments'}), 500
    
    @app.route('/api/rent/late-fees/calculate', methods=['POST'])
    @require_permission(Permission.UPDATE_PAYMENT)
    def calculate_late_fees():
        """Calculate and apply late fees"""
        try:
            data = request.json or {}
            tenant_id = data.get('tenant_id')
            invoice_ids = data.get('invoice_ids', [])
            
            if not tenant_id and not invoice_ids:
                return jsonify({'error': 'Either tenant_id or invoice_ids must be provided'}), 400
            
            # Mock late fee calculation
            late_fees_applied = []
            total_late_fees = 0.0
            
            if tenant_id:
                # Calculate late fees for all overdue invoices for tenant
                late_fee = 50.0  # Mock calculation
                late_fees_applied.append({
                    'tenant_id': tenant_id,
                    'late_fee': late_fee,
                    'reason': 'Overdue rent payment'
                })
                total_late_fees += late_fee
            
            for invoice_id in invoice_ids:
                # Calculate late fee for specific invoice
                late_fee = 25.0  # Mock calculation
                late_fees_applied.append({
                    'invoice_id': invoice_id,
                    'late_fee': late_fee,
                    'reason': 'Invoice overdue'
                })
                total_late_fees += late_fee
            
            return jsonify({
                'success': True,
                'late_fees_applied': late_fees_applied,
                'total_late_fees': total_late_fees,
                'applied_count': len(late_fees_applied)
            })
            
        except Exception as e:
            print(f"Late fee calculation error: {e}")
            return jsonify({'error': 'Failed to calculate late fees'}), 500

    @app.route('/api/test-post', methods=['POST'])
    def test_post():
        return jsonify({'message': 'POST works!', 'received': request.json})
    
    # ===========================================
    # LEASE MANAGEMENT API ENDPOINTS
    # ===========================================
    
    @app.route('/api/lease/dashboard', methods=['GET'])
    @require_permission(Permission.READ_LEASE)
    def get_lease_dashboard():
        """Get lease management dashboard data"""
        try:
            lease_service = get_lease_management_service()
            dashboard_data = lease_service.get_lease_dashboard_data()
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            print(f"Lease dashboard error: {e}")
            return jsonify({'error': 'Failed to get lease dashboard data'}), 500
    
    @app.route('/api/lease/renewals/process', methods=['POST'])
    @require_permission(Permission.MANAGE_LEASE)
    def process_lease_renewals():
        """Process lease renewals for expiring leases"""
        try:
            lease_service = get_lease_management_service()
            result = lease_service.process_lease_renewals()
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': f"Processed {result.get('processed_renewals', 0)} lease renewals",
                    'data': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to process renewals')
                }), 500
                
        except Exception as e:
            print(f"Lease renewal processing error: {e}")
            return jsonify({'error': 'Failed to process lease renewals'}), 500
    
    @app.route('/api/lease/renewals/create', methods=['POST'])
    @require_permission(Permission.CREATE_LEASE)
    def create_lease_renewal():
        """Create a lease renewal"""
        try:
            data = request.json
            
            if not data.get('lease_id'):
                return jsonify({'error': 'lease_id is required'}), 400
            
            if not data.get('renewal_terms'):
                return jsonify({'error': 'renewal_terms is required'}), 400
            
            lease_service = get_lease_management_service()
            result = lease_service.create_lease_renewal(
                lease_id=data['lease_id'],
                renewal_terms=data['renewal_terms']
            )
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': result.get('message', 'Lease renewal created successfully'),
                    'new_lease_id': result.get('new_lease_id')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to create lease renewal')
                }), 400
                
        except Exception as e:
            print(f"Lease renewal creation error: {e}")
            return jsonify({'error': 'Failed to create lease renewal'}), 500
    
    @app.route('/api/lease/violations', methods=['POST'])
    @require_permission(Permission.CREATE_LEASE)
    def track_lease_violation():
        """Track a lease violation"""
        try:
            data = request.json
            
            required_fields = ['lease_id', 'type', 'description']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            lease_service = get_lease_management_service()
            result = lease_service.track_lease_violation(
                lease_id=data['lease_id'],
                violation_data={
                    'type': data['type'],
                    'description': data['description'],
                    'severity': data.get('severity', 'medium')
                }
            )
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': result.get('message', 'Lease violation recorded'),
                    'violation_id': result.get('violation_id')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to record violation')
                }), 400
                
        except Exception as e:
            print(f"Lease violation tracking error: {e}")
            return jsonify({'error': 'Failed to track lease violation'}), 500
    
    @app.route('/api/lease/expiring', methods=['GET'])
    @require_permission(Permission.READ_LEASE)
    def get_expiring_leases():
        """Get leases expiring within specified timeframe"""
        try:
            days = request.args.get('days', 60, type=int)
            lease_service = get_lease_management_service()
            
            # Get dashboard data which includes upcoming expirations
            dashboard_data = lease_service.get_lease_dashboard_data()
            upcoming_expirations = dashboard_data.get('upcoming_expirations', [])
            
            return jsonify({
                'success': True,
                'expiring_leases': upcoming_expirations,
                'count': len(upcoming_expirations),
                'timeframe_days': days
            })
            
        except Exception as e:
            print(f"Get expiring leases error: {e}")
            return jsonify({'error': 'Failed to get expiring leases'}), 500
    
    @app.route('/api/lease/renewal-status/<lease_id>', methods=['PUT'])
    @require_permission(Permission.MANAGE_LEASE)
    def update_lease_renewal_status():
        """Update lease renewal status"""
        try:
            data = request.json
            lease_id = request.view_args['lease_id']
            
            if not data.get('status'):
                return jsonify({'error': 'status is required'}), 400
            
            # Validate status
            try:
                status = RenewalStatus(data['status'])
            except ValueError:
                return jsonify({'error': 'Invalid renewal status'}), 400
            
            lease_service = get_lease_management_service()
            lease_service._update_lease_renewal_status(lease_id, status)
            
            return jsonify({
                'success': True,
                'message': f'Lease renewal status updated to {status.value}',
                'lease_id': lease_id,
                'new_status': status.value
            })
            
        except Exception as e:
            print(f"Update lease renewal status error: {e}")
            return jsonify({'error': 'Failed to update lease renewal status'}), 500
    
    @app.route('/api/lease/analytics', methods=['GET'])
    @require_permission(Permission.READ_LEASE)
    def get_lease_analytics():
        """Get lease analytics and metrics"""
        try:
            lease_service = get_lease_management_service()
            dashboard_data = lease_service.get_lease_dashboard_data()
            
            analytics = {
                'occupancy_metrics': {
                    'occupancy_rate': dashboard_data.get('occupancy_rate', 0),
                    'total_active_leases': dashboard_data.get('total_active_leases', 0),
                    'total_expired_leases': dashboard_data.get('expired_leases', 0)
                },
                'renewal_metrics': {
                    'renewal_rate': dashboard_data.get('renewal_rate', 0),
                    'renewal_pipeline': dashboard_data.get('renewal_pipeline', {}),
                    'average_lease_term': dashboard_data.get('average_lease_term', 0)
                },
                'violation_metrics': {
                    'total_violations': dashboard_data.get('lease_violations', {}),
                    'violations_by_severity': dashboard_data.get('lease_violations', {}).get('by_severity', {})
                },
                'status_breakdown': dashboard_data.get('lease_status_breakdown', {}),
                'recent_activity': {
                    'recent_renewals': dashboard_data.get('recent_renewals', []),
                    'expiring_soon': dashboard_data.get('expiring_soon', 0)
                }
            }
            
            return jsonify({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            print(f"Lease analytics error: {e}")
            return jsonify({'error': 'Failed to get lease analytics'}), 500
    
    @app.route('/api/lease/renewal-notices/send', methods=['POST'])
    @require_permission(Permission.MANAGE_LEASE)
    def send_renewal_notices():
        """Send renewal notices to tenants with expiring leases"""
        try:
            data = request.json or {}
            notice_type = data.get('notice_type', 'initial')  # initial, reminder
            lease_ids = data.get('lease_ids', [])  # specific leases, or empty for all eligible
            
            lease_service = get_lease_management_service()
            
            # If specific lease IDs provided, process only those
            if lease_ids:
                sent_count = 0
                failed_count = 0
                results = []
                
                for lease_id in lease_ids:
                    try:
                        # Mock lease data for the specific lease
                        lease = {
                            'id': lease_id,
                            'tenant_email': 'tenant@example.com',
                            'tenant_name': 'John Doe',
                            'property_name': 'Sample Property',
                            'unit_number': '101',
                            'end_date': '2024-12-31'
                        }
                        
                        result = lease_service._send_renewal_notice(lease, notice_type)
                        results.append({
                            'lease_id': lease_id,
                            'success': result.get('success', False),
                            'notice_type': notice_type
                        })
                        
                        if result.get('success'):
                            sent_count += 1
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        failed_count += 1
                        results.append({
                            'lease_id': lease_id,
                            'success': False,
                            'error': str(e)
                        })
                
                return jsonify({
                    'success': True,
                    'message': f'Sent {sent_count} renewal notices, {failed_count} failed',
                    'notices_sent': sent_count,
                    'notices_failed': failed_count,
                    'results': results
                })
            else:
                # Process all eligible leases
                result = lease_service.process_lease_renewals()
                
                return jsonify({
                    'success': True,
                    'message': f"Sent renewal notices to {result.get('notifications_sent', 0)} tenants",
                    'data': result
                })
                
        except Exception as e:
            print(f"Send renewal notices error: {e}")
            return jsonify({'error': 'Failed to send renewal notices'}), 500
    
    @app.route('/api/lease/market-rates', methods=['GET'])
    @require_permission(Permission.READ_LEASE)
    def get_market_rates():
        """Get market rate analysis for lease renewals"""
        try:
            property_id = request.args.get('property_id', type=int)
            unit_type = request.args.get('unit_type')
            
            lease_service = get_lease_management_service()
            
            # Mock market rate calculation
            mock_lease = {
                'property_id': property_id or 1,
                'rent_amount': 1500.0,
                'unit_type': unit_type or 'standard'
            }
            
            market_adjustment = lease_service._calculate_market_rate_adjustment(mock_lease)
            
            return jsonify({
                'success': True,
                'market_analysis': market_adjustment,
                'property_id': property_id,
                'unit_type': unit_type
            })
            
        except Exception as e:
            print(f"Market rates error: {e}")
            return jsonify({'error': 'Failed to get market rates'}), 500
    
    # ===========================================
    # RENT COLLECTION API ENDPOINTS
    # ===========================================
    
    @app.route('/api/rent/dashboard', methods=['GET'])
    @require_permission(Permission.READ_PAYMENT)
    def get_rent_dashboard():
        """Get rent collection dashboard data"""
        try:
            rent_service = get_rent_collection_service()
            dashboard_data = rent_service.get_collection_dashboard_data()
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            print(f"Rent dashboard error: {e}")
            return jsonify({'error': 'Failed to get rent dashboard data'}), 500
    
    @app.route('/api/rent/invoices/generate', methods=['POST'])
    @require_permission(Permission.CREATE_PAYMENT)
    def generate_rent_invoices():
        """Generate monthly rent invoices"""
        try:
            data = request.json or {}
            target_month = data.get('target_month')
            
            if target_month:
                from datetime import datetime
                target_month = datetime.strptime(target_month, '%Y-%m-%d').date()
            
            rent_service = get_rent_collection_service()
            result = rent_service.generate_monthly_invoices(target_month)
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': f"Generated {result.get('invoices_generated', 0)} invoices",
                    'data': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to generate invoices')
                }), 500
                
        except Exception as e:
            print(f"Invoice generation error: {e}")
            return jsonify({'error': 'Failed to generate invoices'}), 500
    
    @app.route('/api/rent/invoices/mock', methods=['GET'])
    @require_permission(Permission.READ_PAYMENT)
    def get_rent_invoices_mock():
        """Get mock rent invoices with optional filtering"""
        try:
            # Get query parameters
            status = request.args.get('status')
            month = request.args.get('month')
            tenant_id = request.args.get('tenant_id', type=int)
            limit = request.args.get('limit', 50, type=int)
            
            # Mock invoice data for now
            from datetime import datetime, timedelta
            import uuid
            
            mock_invoices = []
            for i in range(min(limit, 10)):
                invoice_id = f"INV-{datetime.now().strftime('%Y%m')}-{i+1:04d}-{uuid.uuid4().hex[:8]}"
                mock_invoices.append({
                    'id': invoice_id,
                    'tenant_id': i + 1,
                    'tenant_name': f'Tenant {i + 1}',
                    'tenant_email': f'tenant{i+1}@example.com',
                    'property_id': 1,
                    'property_name': 'Sample Property',
                    'unit_number': f'{101 + i}',
                    'amount_due': 1500.0 + (i * 100),
                    'late_fee': 0.0 if i < 7 else 50.0,
                    'total_amount': 1500.0 + (i * 100) + (0.0 if i < 7 else 50.0),
                    'due_date': (datetime.now() + timedelta(days=(5 - i))).strftime('%Y-%m-%d'),
                    'status': 'current' if i < 7 else 'late',
                    'payment_status': 'pending' if i < 5 else 'completed',
                    'description': f'Rent for {datetime.now().strftime("%B %Y")} - Unit {101 + i}',
                    'created_at': datetime.now().isoformat()
                })
            
            # Apply filters
            filtered_invoices = mock_invoices
            if status and status != 'all':
                filtered_invoices = [inv for inv in filtered_invoices if inv['status'] == status]
            
            return jsonify(filtered_invoices)
            
        except Exception as e:
            print(f"Get invoices error: {e}")
            return jsonify({'error': 'Failed to get invoices'}), 500
    
    @app.route('/api/rent/invoices/<invoice_id>/pay/mock', methods=['POST'])
    @require_permission(Permission.CREATE_PAYMENT)
    def process_rent_payment_mock(invoice_id):
        """Process a rent payment (mock implementation)"""
        try:
            data = request.json
            
            if not data.get('amount'):
                return jsonify({'error': 'amount is required'}), 400
            
            rent_service = get_rent_collection_service()
            result = rent_service.process_payment(invoice_id, data)
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Payment processed successfully',
                    'transaction_id': result.get('transaction_id'),
                    'amount_paid': result.get('amount_paid')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Payment processing failed')
                }), 400
                
        except Exception as e:
            print(f"Payment processing error: {e}")
            return jsonify({'error': 'Failed to process payment'}), 500
    
    @app.route('/api/rent/reminders/send/bulk', methods=['POST'])
    @require_permission(Permission.CREATE_PAYMENT)
    def send_rent_reminders_bulk():
        """Send rent payment reminders (bulk operation)"""
        try:
            data = request.json or {}
            reminder_type = data.get('type', 'all')
            
            rent_service = get_rent_collection_service()
            result = rent_service.send_rent_reminders(reminder_type)
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': f"Sent {result.get('reminders_sent', 0)} reminders",
                    'data': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to send reminders')
                }), 500
                
        except Exception as e:
            print(f"Send reminders error: {e}")
            return jsonify({'error': 'Failed to send reminders'}), 500
    
    @app.route('/api/rent/payments', methods=['GET'])
    @require_permission(Permission.READ_PAYMENT)
    def get_recent_payments():
        """Get recent rent payments"""
        try:
            limit = request.args.get('limit', 20, type=int)
            
            # Mock payment data
            from datetime import datetime, timedelta
            import uuid
            
            mock_payments = []
            for i in range(min(limit, 10)):
                mock_payments.append({
                    'id': f'TXN-{uuid.uuid4().hex[:12]}',
                    'tenant_id': i + 1,
                    'tenant_name': f'Tenant {i + 1}',
                    'property_id': 1,
                    'property_name': 'Sample Property',
                    'unit_number': f'{101 + i}',
                    'amount': 1500.0 + (i * 50),
                    'payment_method': 'credit_card' if i % 2 == 0 else 'bank_transfer',
                    'status': 'completed',
                    'transaction_id': f'stripe_txn_{uuid.uuid4().hex[:16]}',
                    'created_at': (datetime.now() - timedelta(days=i)).isoformat(),
                    'processed_at': (datetime.now() - timedelta(days=i)).isoformat()
                })
            
            return jsonify(mock_payments)
            
        except Exception as e:
            print(f"Get payments error: {e}")
            return jsonify({'error': 'Failed to get payments'}), 500
    
    # ===========================================
    # FINANCIAL REPORTING API ENDPOINTS
    # ===========================================
    
    @app.route('/api/financial/dashboard', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_financial_dashboard():
        """Get financial dashboard overview data"""
        try:
            financial_service = get_financial_reporting_service()
            dashboard_data = financial_service.get_dashboard_data()
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            print(f"Financial dashboard error: {e}")
            return jsonify({'error': 'Failed to get financial dashboard data'}), 500
    
    @app.route('/api/financial/reports/generate', methods=['POST'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def generate_financial_report():
        """Generate a financial report"""
        try:
            data = request.json or {}
            
            # Validate required fields
            report_type_str = data.get('report_type')
            if not report_type_str:
                return jsonify({'error': 'report_type is required'}), 400
            
            try:
                report_type = ReportType(report_type_str)
            except ValueError:
                return jsonify({'error': 'Invalid report type'}), 400
            
            period_str = data.get('period', 'monthly')
            try:
                period = ReportPeriod(period_str)
            except ValueError:
                return jsonify({'error': 'Invalid period'}), 400
            
            # Parse dates if provided
            start_date = None
            end_date = None
            if data.get('start_date'):
                from datetime import datetime
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            if data.get('end_date'):
                from datetime import datetime
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=report_type,
                period=period,
                start_date=start_date,
                end_date=end_date
            )
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': f"Generated {report_type.value} report successfully",
                    'report': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to generate report')
                }), 500
                
        except Exception as e:
            print(f"Financial report generation error: {e}")
            return jsonify({'error': 'Failed to generate financial report'}), 500
    
    @app.route('/api/financial/reports/<report_type>', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_financial_report(report_type):
        """Get a specific type of financial report"""
        try:
            # Validate report type
            try:
                report_type_enum = ReportType(report_type)
            except ValueError:
                return jsonify({'error': 'Invalid report type'}), 400
            
            # Get query parameters
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            try:
                period_enum = ReportPeriod(period)
            except ValueError:
                return jsonify({'error': 'Invalid period'}), 400
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=report_type_enum,
                period=period_enum,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Get financial report error: {e}")
            return jsonify({'error': 'Failed to get financial report'}), 500
    
    @app.route('/api/financial/income-statement', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_income_statement():
        """Get income statement report"""
        try:
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=ReportType.INCOME_STATEMENT,
                period=ReportPeriod(period) if period in [p.value for p in ReportPeriod] else ReportPeriod.MONTHLY,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Income statement error: {e}")
            return jsonify({'error': 'Failed to get income statement'}), 500
    
    @app.route('/api/financial/cash-flow', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_cash_flow():
        """Get cash flow statement"""
        try:
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=ReportType.CASH_FLOW,
                period=ReportPeriod(period) if period in [p.value for p in ReportPeriod] else ReportPeriod.MONTHLY,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Cash flow error: {e}")
            return jsonify({'error': 'Failed to get cash flow statement'}), 500
    
    @app.route('/api/financial/rent-roll', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_rent_roll():
        """Get rent roll report"""
        try:
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=ReportType.RENT_ROLL,
                period=ReportPeriod(period) if period in [p.value for p in ReportPeriod] else ReportPeriod.MONTHLY,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Rent roll error: {e}")
            return jsonify({'error': 'Failed to get rent roll'}), 500
    
    @app.route('/api/financial/vacancy-analysis', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_vacancy_analysis():
        """Get vacancy analysis report"""
        try:
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=ReportType.VACANCY_REPORT,
                period=ReportPeriod(period) if period in [p.value for p in ReportPeriod] else ReportPeriod.MONTHLY,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Vacancy analysis error: {e}")
            return jsonify({'error': 'Failed to get vacancy analysis'}), 500
    
    @app.route('/api/financial/expense-summary', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_expense_summary():
        """Get expense summary report"""
        try:
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=ReportType.EXPENSE_SUMMARY,
                period=ReportPeriod(period) if period in [p.value for p in ReportPeriod] else ReportPeriod.MONTHLY,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Expense summary error: {e}")
            return jsonify({'error': 'Failed to get expense summary'}), 500
    
    @app.route('/api/financial/profit-loss', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_profit_loss():
        """Get profit and loss statement"""
        try:
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=ReportType.PROFIT_LOSS,
                period=ReportPeriod(period) if period in [p.value for p in ReportPeriod] else ReportPeriod.MONTHLY,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Profit loss error: {e}")
            return jsonify({'error': 'Failed to get profit and loss statement'}), 500
    
    @app.route('/api/financial/kpi-metrics', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_kpi_metrics():
        """Get key performance indicators"""
        try:
            period = request.args.get('period', 'monthly')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                from datetime import datetime
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            financial_service = get_financial_reporting_service()
            
            # Get KPI metrics from dashboard or generate specifically
            dashboard_data = financial_service.get_dashboard_data()
            kpi_metrics = dashboard_data.get('kpi_metrics', {})
            
            return jsonify({
                'success': True,
                'kpi_metrics': kpi_metrics,
                'period': f"{start_date_obj or 'current'} to {end_date_obj or 'current'}"
            })
            
        except Exception as e:
            print(f"KPI metrics error: {e}")
            return jsonify({'error': 'Failed to get KPI metrics'}), 500
    
    @app.route('/api/financial/charts-data', methods=['GET'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def get_financial_charts_data():
        """Get chart data for financial visualizations"""
        try:
            report_type = request.args.get('report_type', 'comprehensive')
            period = request.args.get('period', 'monthly')
            
            financial_service = get_financial_reporting_service()
            
            # Generate comprehensive report to get charts data
            result = financial_service.generate_financial_report(
                report_type=ReportType.PROFIT_LOSS,  # Use P&L as it has comprehensive data
                period=ReportPeriod(period) if period in [p.value for p in ReportPeriod] else ReportPeriod.MONTHLY
            )
            
            charts_data = result.get('charts_data', [])
            
            return jsonify({
                'success': True,
                'charts_data': charts_data,
                'report_type': report_type,
                'period': period
            })
            
        except Exception as e:
            print(f"Charts data error: {e}")
            return jsonify({'error': 'Failed to get charts data'}), 500
    
    @app.route('/api/financial/export/<report_type>', methods=['POST'])
    @require_permission(Permission.VIEW_FINANCIAL_REPORTS)
    def export_financial_report(report_type):
        """Export financial report to PDF/Excel"""
        try:
            data = request.json or {}
            export_format = data.get('format', 'pdf')  # pdf, excel, csv
            
            if export_format not in ['pdf', 'excel', 'csv']:
                return jsonify({'error': 'Invalid export format'}), 400
            
            # Validate report type
            try:
                report_type_enum = ReportType(report_type)
            except ValueError:
                return jsonify({'error': 'Invalid report type'}), 400
            
            # Generate the report
            financial_service = get_financial_reporting_service()
            result = financial_service.generate_financial_report(
                report_type=report_type_enum,
                period=ReportPeriod.MONTHLY
            )
            
            if not result.get('success'):
                return jsonify({'error': 'Failed to generate report for export'}), 500
            
            # Mock export process (would integrate with actual export service)
            export_url = f"/exports/{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
            
            return jsonify({
                'success': True,
                'message': f'Report exported to {export_format.upper()} successfully',
                'export_url': export_url,
                'download_link': export_url,
                'file_size': '2.5 MB',  # Mock
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
            })
            
        except Exception as e:
            print(f"Export financial report error: {e}")
            return jsonify({'error': 'Failed to export financial report'}), 500
    
    # ===========================================
    # SECURITY & MONITORING API ENDPOINTS
    # ===========================================
    
    @app.route('/api/security/dashboard', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_security_dashboard():
        """Get security dashboard data"""
        try:
            security_service = get_security_service()
            dashboard_data = security_service.get_security_dashboard_data()
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            print(f"Security dashboard error: {e}")
            return jsonify({'error': 'Failed to get security dashboard data'}), 500
    
    @app.route('/api/security/sessions', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_active_sessions():
        """Get active user sessions"""
        try:
            security_service = get_security_service()
            
            # Get all active sessions
            active_sessions = []
            for session in security_service.sessions.values():
                if session.status.value == 'active':
                    active_sessions.append({
                        'id': session.id,
                        'user_id': session.user_id,
                        'ip_address': session.ip_address,
                        'user_agent': session.user_agent,
                        'created_at': session.created_at.isoformat(),
                        'last_accessed': session.last_accessed.isoformat(),
                        'expires_at': session.expires_at.isoformat(),
                        'status': session.status.value
                    })
            
            return jsonify({
                'success': True,
                'sessions': active_sessions,
                'total_count': len(active_sessions)
            })
            
        except Exception as e:
            print(f"Get sessions error: {e}")
            return jsonify({'error': 'Failed to get active sessions'}), 500
    
    @app.route('/api/security/sessions/<session_id>/revoke', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def revoke_session(session_id):
        """Revoke a user session"""
        try:
            current_user = request.get('current_user', {})
            user_id = current_user.get('id')
            
            security_service = get_security_service()
            success = security_service.revoke_session(session_id, user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Session revoked successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Session not found or already revoked'
                }), 404
                
        except Exception as e:
            print(f"Session revocation error: {e}")
            return jsonify({'error': 'Failed to revoke session'}), 500
    
    @app.route('/api/security/api-keys', methods=['GET', 'POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def handle_api_keys():
        """Get or create API keys"""
        if request.method == 'GET':
            try:
                security_service = get_security_service()
                
                # Get all API keys (excluding sensitive data)
                api_keys = []
                for key in security_service.api_keys.values():
                    api_keys.append({
                        'id': key.id,
                        'user_id': key.user_id,
                        'name': key.name,
                        'permissions': key.permissions,
                        'created_at': key.created_at.isoformat(),
                        'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                        'last_used': key.last_used.isoformat() if key.last_used else None,
                        'is_active': key.is_active,
                        'rate_limit': key.rate_limit,
                        'usage_count': key.usage_count
                    })
                
                return jsonify({
                    'success': True,
                    'api_keys': api_keys,
                    'total_count': len(api_keys)
                })
                
            except Exception as e:
                print(f"Get API keys error: {e}")
                return jsonify({'error': 'Failed to get API keys'}), 500
        
        elif request.method == 'POST':
            try:
                data = request.json or {}
                current_user = request.get('current_user', {})
                user_id = current_user.get('id', 1)  # Default for demo
                
                # Validate required fields
                name = data.get('name')
                if not name:
                    return jsonify({'error': 'API key name is required'}), 400
                
                permissions = data.get('permissions', [])
                rate_limit = data.get('rate_limit', 1000)
                expires_at = None
                
                if data.get('expires_at'):
                    from datetime import datetime
                    expires_at = datetime.fromisoformat(data['expires_at'])
                
                security_service = get_security_service()
                result = security_service.create_api_key(
                    user_id=user_id,
                    name=name,
                    permissions=permissions,
                    expires_at=expires_at,
                    rate_limit=rate_limit
                )
                
                if result.get('success'):
                    return jsonify({
                        'success': True,
                        'message': 'API key created successfully',
                        'api_key': result['api_key'],  # Only shown once
                        'key_id': result['key_id'],
                        'permissions': result['permissions'],
                        'rate_limit': result['rate_limit']
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': result.get('error', 'Failed to create API key')
                    }), 500
                    
            except Exception as e:
                print(f"API key creation error: {e}")
                return jsonify({'error': 'Failed to create API key'}), 500
    
    @app.route('/api/security/api-keys/<key_id>/revoke', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def revoke_api_key(key_id):
        """Revoke an API key"""
        try:
            security_service = get_security_service()
            
            # Find and revoke API key
            api_key = security_service.api_keys.get(key_id)
            if api_key:
                api_key.is_active = False
                
                # Log security event
                current_user = request.get('current_user', {})
                security_service.log_security_event(
                    event_type=SecurityEventType.API_KEY_REVOKED,
                    user_id=current_user.get('id'),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    threat_level=ThreatLevel.LOW,
                    details={'api_key_id': key_id, 'name': api_key.name}
                )
                
                return jsonify({
                    'success': True,
                    'message': 'API key revoked successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'API key not found'
                }), 404
                
        except Exception as e:
            print(f"API key revocation error: {e}")
            return jsonify({'error': 'Failed to revoke API key'}), 500
    
    @app.route('/api/security/events', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_security_events():
        """Get security events with filtering"""
        try:
            security_service = get_security_service()
            
            # Get query parameters
            limit = request.args.get('limit', 50, type=int)
            event_type = request.args.get('event_type')
            threat_level = request.args.get('threat_level')
            user_id = request.args.get('user_id', type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Filter events
            events = security_service.security_events.copy()
            
            if event_type:
                events = [e for e in events if e.event_type.value == event_type]
            
            if threat_level:
                events = [e for e in events if e.threat_level.value == threat_level]
            
            if user_id:
                events = [e for e in events if e.user_id == user_id]
            
            if start_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date)
                events = [e for e in events if e.timestamp >= start_dt]
            
            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date)
                events = [e for e in events if e.timestamp <= end_dt]
            
            # Sort by timestamp (newest first) and limit
            events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            # Convert to response format
            event_data = []
            for event in events:
                event_data.append({
                    'id': event.id,
                    'event_type': event.event_type.value,
                    'user_id': event.user_id,
                    'ip_address': event.ip_address,
                    'user_agent': event.user_agent,
                    'timestamp': event.timestamp.isoformat(),
                    'threat_level': event.threat_level.value,
                    'endpoint': event.endpoint,
                    'success': event.success,
                    'details': event.details,
                    'session_id': event.session_id
                })
            
            return jsonify({
                'success': True,
                'events': event_data,
                'total_count': len(event_data),
                'filters_applied': {
                    'event_type': event_type,
                    'threat_level': threat_level,
                    'user_id': user_id,
                    'date_range': f"{start_date} to {end_date}" if start_date or end_date else None
                }
            })
            
        except Exception as e:
            print(f"Get security events error: {e}")
            return jsonify({'error': 'Failed to get security events'}), 500
    
    @app.route('/api/security/alerts', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_security_alerts():
        """Get security alerts"""
        try:
            security_service = get_security_service()
            
            # Get query parameters
            limit = request.args.get('limit', 20, type=int)
            severity = request.args.get('severity')
            resolved = request.args.get('resolved')
            
            # Filter alerts
            alerts = security_service.security_alerts.copy()
            
            if severity:
                alerts = [a for a in alerts if a.severity.value == severity]
            
            if resolved is not None:
                resolved_bool = resolved.lower() == 'true'
                alerts = [a for a in alerts if a.resolved == resolved_bool]
            
            # Sort by timestamp (newest first) and limit
            alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            # Convert to response format
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    'id': alert.id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity.value,
                    'user_id': alert.user_id,
                    'ip_address': alert.ip_address,
                    'description': alert.description,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'metadata': alert.metadata
                })
            
            return jsonify({
                'success': True,
                'alerts': alert_data,
                'total_count': len(alert_data),
                'filters_applied': {
                    'severity': severity,
                    'resolved': resolved
                }
            })
            
        except Exception as e:
            print(f"Get security alerts error: {e}")
            return jsonify({'error': 'Failed to get security alerts'}), 500
    
    @app.route('/api/security/alerts/<alert_id>/resolve', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def resolve_security_alert(alert_id):
        """Resolve a security alert"""
        try:
            security_service = get_security_service()
            
            # Find and resolve alert
            alert = None
            for a in security_service.security_alerts:
                if a.id == alert_id:
                    alert = a
                    break
            
            if alert:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                
                return jsonify({
                    'success': True,
                    'message': 'Security alert resolved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Security alert not found'
                }), 404
                
        except Exception as e:
            print(f"Resolve security alert error: {e}")
            return jsonify({'error': 'Failed to resolve security alert'}), 500
    
    @app.route('/api/security/rate-limits', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_rate_limit_status():
        """Get current rate limit status"""
        try:
            security_service = get_security_service()
            
            # Get rate limit data
            rate_limit_data = []
            for key, data in security_service.rate_limits.items():
                rate_limit_data.append({
                    'key': key,
                    'current_requests': len(data['requests']),
                    'blocked_until': data['blocked_until'],
                    'is_blocked': data['blocked_until'] and time.time() < data['blocked_until']
                })
            
            # Get rate limit rules
            rules_data = []
            for rule in security_service.rate_limit_rules:
                rules_data.append({
                    'endpoint': rule.endpoint,
                    'max_requests': rule.max_requests,
                    'time_window': rule.time_window,
                    'per_user': rule.per_user,
                    'per_ip': rule.per_ip
                })
            
            return jsonify({
                'success': True,
                'current_limits': rate_limit_data,
                'rules': rules_data
            })
            
        except Exception as e:
            print(f"Get rate limits error: {e}")
            return jsonify({'error': 'Failed to get rate limit status'}), 500
    
    @app.route('/api/security/test-alert', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def test_security_alert():
        """Test security alert generation (for testing purposes)"""
        try:
            data = request.json or {}
            alert_type = data.get('type', 'test_alert')
            severity = data.get('severity', 'medium')
            
            security_service = get_security_service()
            current_user = request.get('current_user', {})
            
            # Log test security event
            event_id = security_service.log_security_event(
                event_type=SecurityEventType.SECURITY_ALERT,
                user_id=current_user.get('id'),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                threat_level=ThreatLevel(severity),
                details={
                    'test_alert': True,
                    'alert_type': alert_type,
                    'description': f'Test security alert: {alert_type}'
                },
                endpoint='/api/security/test-alert'
            )
            
            return jsonify({
                'success': True,
                'message': 'Test security alert generated',
                'event_id': event_id
            })
            
        except Exception as e:
            print(f"Test security alert error: {e}")
            return jsonify({'error': 'Failed to generate test alert'}), 500
    
    @app.route('/api/security/auth/enhanced-login', methods=['POST'])
    @rate_limited
    def enhanced_login():
        """Enhanced login with security monitoring"""
        try:
            data = request.json or {}
            email = data.get('email')
            password = data.get('password')
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            if not email or not password:
                return jsonify({'error': 'Email and password are required'}), 400
            
            security_service = get_security_service()
            
            # Here you would validate credentials against your user database
            # For demo, we'll simulate a successful login
            user_id = 1  # Mock user ID
            permissions = ['read_property', 'write_property', 'read_financial']  # Mock permissions
            
            # Create secure session
            session_result = security_service.create_session(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                permissions=permissions
            )
            
            if session_result.get('success'):
                # Log successful login
                security_service.log_security_event(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    threat_level=ThreatLevel.LOW,
                    details={'email': email},
                    endpoint='/api/security/auth/enhanced-login'
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'token': session_result['token'],
                    'expires_at': session_result['expires_at'],
                    'permissions': session_result['permissions']
                })
            else:
                # Log failed login
                security_service.log_security_event(
                    event_type=SecurityEventType.LOGIN_FAILURE,
                    user_id=None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    threat_level=ThreatLevel.MEDIUM,
                    details={'email': email, 'error': session_result.get('error')},
                    endpoint='/api/security/auth/enhanced-login',
                    success=False
                )
                
                return jsonify({
                    'success': False,
                    'error': 'Login failed'
                }), 401
                
        except Exception as e:
            print(f"Enhanced login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    # ===== MAINTENANCE SCHEDULING ENDPOINTS =====
    
    @app.route('/api/maintenance-scheduling/dashboard', methods=['GET'])
    @require_permission(Permission.READ_MAINTENANCE)
    def get_maintenance_dashboard():
        """Get maintenance scheduling dashboard data"""
        try:
            maintenance_service = get_maintenance_service()
            dashboard_data = maintenance_service.get_maintenance_dashboard_data()
            
            if dashboard_data.get('success'):
                return jsonify(dashboard_data)
            else:
                return jsonify({'error': dashboard_data.get('error', 'Failed to get dashboard data')}), 500
                
        except Exception as e:
            print(f"Maintenance dashboard error: {e}")
            return jsonify({'error': 'Failed to get maintenance dashboard data'}), 500
    
    @app.route('/api/maintenance-scheduling/items', methods=['GET', 'POST'])
    @require_permission(Permission.READ_MAINTENANCE)
    def handle_maintenance_items():
        """Handle maintenance items"""
        maintenance_service = get_maintenance_service()
        
        if request.method == 'GET':
            try:
                # Return all maintenance items
                items = []
                for item in maintenance_service.maintenance_items.values():
                    items.append(maintenance_service._serialize_maintenance_item(item))
                
                return jsonify({
                    'success': True,
                    'items': items
                })
                
            except Exception as e:
                print(f"Get maintenance items error: {e}")
                return jsonify({'error': 'Failed to get maintenance items'}), 500
        
        elif request.method == 'POST':
            try:
                if not has_permission(Permission.CREATE_MAINTENANCE):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json or {}
                property_id = data.get('property_id')
                name = data.get('name')
                category = data.get('category')
                
                if not all([property_id, name, category]):
                    return jsonify({'error': 'property_id, name, and category are required'}), 400
                
                result = maintenance_service.create_maintenance_item(
                    property_id=property_id,
                    name=name,
                    category=category,
                    model=data.get('model'),
                    serial_number=data.get('serial_number'),
                    installation_date=datetime.fromisoformat(data['installation_date']) if data.get('installation_date') else None,
                    warranty_expires=datetime.fromisoformat(data['warranty_expires']) if data.get('warranty_expires') else None,
                    service_interval_days=data.get('service_interval_days', 90)
                )
                
                if result.get('success'):
                    return jsonify(result), 201
                else:
                    return jsonify({'error': result.get('error', 'Failed to create maintenance item')}), 500
                    
            except Exception as e:
                print(f"Create maintenance item error: {e}")
                return jsonify({'error': 'Failed to create maintenance item'}), 500
    
    @app.route('/api/maintenance-scheduling/requests', methods=['GET', 'POST'])
    @require_permission(Permission.READ_MAINTENANCE)
    def handle_maintenance_requests():
        """Handle maintenance requests"""
        maintenance_service = get_maintenance_service()
        
        if request.method == 'GET':
            try:
                # Get filter parameters
                status_filter = request.args.get('status')
                priority_filter = request.args.get('priority')
                property_id = request.args.get('property_id')
                
                requests = []
                for req in maintenance_service.maintenance_requests.values():
                    # Apply filters
                    if status_filter and req.status.value != status_filter:
                        continue
                    if priority_filter and req.priority.value != priority_filter:
                        continue
                    if property_id and req.property_id != int(property_id):
                        continue
                    
                    requests.append(maintenance_service._serialize_maintenance_request(req))
                
                # Sort by created_at descending
                requests.sort(key=lambda x: x['created_at'], reverse=True)
                
                return jsonify({
                    'success': True,
                    'requests': requests
                })
                
            except Exception as e:
                print(f"Get maintenance requests error: {e}")
                return jsonify({'error': 'Failed to get maintenance requests'}), 500
        
        elif request.method == 'POST':
            try:
                if not has_permission(Permission.CREATE_MAINTENANCE):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json or {}
                
                # Get current user from session
                current_user = load_user_permissions()
                requested_by = current_user.get('user_id', 1)
                
                required_fields = ['property_id', 'title', 'description', 'maintenance_type', 'priority']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                result = maintenance_service.create_maintenance_request(
                    property_id=data['property_id'],
                    title=data['title'],
                    description=data['description'],
                    maintenance_type=MaintenanceType(data['maintenance_type']),
                    priority=Priority(data['priority']),
                    requested_by=requested_by,
                    item_id=data.get('item_id'),
                    estimated_hours=data.get('estimated_hours'),
                    estimated_cost=data.get('estimated_cost'),
                    tenant_access_required=data.get('tenant_access_required', False)
                )
                
                if result.get('success'):
                    return jsonify(result), 201
                else:
                    return jsonify({'error': result.get('error', 'Failed to create maintenance request')}), 500
                    
            except Exception as e:
                print(f"Create maintenance request error: {e}")
                return jsonify({'error': 'Failed to create maintenance request'}), 500
    
    @app.route('/api/maintenance-scheduling/requests/<request_id>', methods=['GET', 'PUT', 'DELETE'])
    @require_permission(Permission.READ_MAINTENANCE)
    def handle_maintenance_request(request_id):
        """Handle individual maintenance request"""
        maintenance_service = get_maintenance_service()
        
        if request.method == 'GET':
            try:
                if request_id not in maintenance_service.maintenance_requests:
                    return jsonify({'error': 'Maintenance request not found'}), 404
                
                req = maintenance_service.maintenance_requests[request_id]
                return jsonify({
                    'success': True,
                    'request': maintenance_service._serialize_maintenance_request(req)
                })
                
            except Exception as e:
                print(f"Get maintenance request error: {e}")
                return jsonify({'error': 'Failed to get maintenance request'}), 500
        
        elif request.method == 'PUT':
            try:
                if not has_permission(Permission.CREATE_MAINTENANCE):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json or {}
                
                if 'status' in data:
                    # Update status
                    result = maintenance_service.update_maintenance_status(
                        request_id=request_id,
                        status=MaintenanceStatus(data['status']),
                        notes=data.get('notes', ''),
                        actual_hours=data.get('actual_hours'),
                        actual_cost=data.get('actual_cost')
                    )
                    
                    if result.get('success'):
                        return jsonify(result)
                    else:
                        return jsonify({'error': result.get('error', 'Failed to update status')}), 500
                
                # Other updates can be added here
                return jsonify({'error': 'No valid update data provided'}), 400
                
            except Exception as e:
                print(f"Update maintenance request error: {e}")
                return jsonify({'error': 'Failed to update maintenance request'}), 500
        
        elif request.method == 'DELETE':
            try:
                if not has_permission(Permission.DELETE_MAINTENANCE):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                if request_id in maintenance_service.maintenance_requests:
                    del maintenance_service.maintenance_requests[request_id]
                    return jsonify({'success': True, 'message': 'Maintenance request deleted'})
                else:
                    return jsonify({'error': 'Maintenance request not found'}), 404
                    
            except Exception as e:
                print(f"Delete maintenance request error: {e}")
                return jsonify({'error': 'Failed to delete maintenance request'}), 500
    
    @app.route('/api/maintenance-scheduling/schedule', methods=['POST'])
    @require_permission(Permission.CREATE_MAINTENANCE)
    def schedule_maintenance():
        """Schedule a maintenance request"""
        try:
            data = request.json or {}
            request_id = data.get('request_id')
            scheduled_date = data.get('scheduled_date')
            vendor_id = data.get('vendor_id')
            
            if not request_id or not scheduled_date:
                return jsonify({'error': 'request_id and scheduled_date are required'}), 400
            
            maintenance_service = get_maintenance_service()
            
            # Parse scheduled date
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
            
            result = maintenance_service.schedule_maintenance_request(
                request_id=request_id,
                scheduled_date=scheduled_datetime,
                vendor_id=vendor_id
            )
            
            if result.get('success'):
                return jsonify(result)
            else:
                return jsonify({'error': result.get('error', 'Failed to schedule maintenance')}), 500
                
        except Exception as e:
            print(f"Schedule maintenance error: {e}")
            return jsonify({'error': 'Failed to schedule maintenance'}), 500
    
    @app.route('/api/maintenance-scheduling/vendors', methods=['GET', 'POST'])
    @require_permission(Permission.READ_MAINTENANCE)
    def handle_vendors():
        """Handle maintenance vendors"""
        maintenance_service = get_maintenance_service()
        
        if request.method == 'GET':
            try:
                vendors = []
                for vendor in maintenance_service.vendors.values():
                    vendors.append(maintenance_service._serialize_vendor(vendor))
                
                return jsonify({
                    'success': True,
                    'vendors': vendors
                })
                
            except Exception as e:
                print(f"Get vendors error: {e}")
                return jsonify({'error': 'Failed to get vendors'}), 500
        
        elif request.method == 'POST':
            try:
                if not has_permission(Permission.CREATE_MAINTENANCE):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json or {}
                required_fields = ['name', 'contact_person', 'email', 'phone', 'address', 'specialties']
                
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                vendor_id = str(uuid.uuid4())
                vendor = {
                    'id': vendor_id,
                    'name': data['name'],
                    'contact_person': data['contact_person'],
                    'email': data['email'],
                    'phone': data['phone'],
                    'address': data['address'],
                    'specialties': data['specialties'],
                    'hourly_rate': data.get('hourly_rate', 0.0),
                    'rating': data.get('rating', 0.0),
                    'created_at': datetime.utcnow()
                }
                
                # This would normally save to database
                return jsonify({
                    'success': True,
                    'vendor_id': vendor_id,
                    'vendor': vendor
                }), 201
                
            except Exception as e:
                print(f"Create vendor error: {e}")
                return jsonify({'error': 'Failed to create vendor'}), 500
    
    @app.route('/api/maintenance-scheduling/scheduled', methods=['GET'])
    @require_permission(Permission.READ_MAINTENANCE)
    def get_scheduled_maintenance():
        """Get scheduled maintenance for date range"""
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            maintenance_service = get_maintenance_service()
            
            # Parse dates if provided
            start_datetime = None
            end_datetime = None
            
            if start_date:
                try:
                    start_datetime = datetime.fromisoformat(start_date)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format'}), 400
            
            if end_date:
                try:
                    end_datetime = datetime.fromisoformat(end_date)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format'}), 400
            
            result = maintenance_service.get_scheduled_maintenance(start_datetime, end_datetime)
            
            if result.get('success'):
                return jsonify(result)
            else:
                return jsonify({'error': result.get('error', 'Failed to get scheduled maintenance')}), 500
                
        except Exception as e:
            print(f"Get scheduled maintenance error: {e}")
            return jsonify({'error': 'Failed to get scheduled maintenance'}), 500
    
    @app.route('/api/maintenance-scheduling/preventive/generate', methods=['POST'])
    @require_permission(Permission.CREATE_MAINTENANCE)
    def generate_preventive_maintenance():
        """Generate preventive maintenance requests"""
        try:
            maintenance_service = get_maintenance_service()
            result = maintenance_service.generate_preventive_maintenance_requests()
            
            if result.get('success'):
                return jsonify(result)
            else:
                return jsonify({'error': result.get('error', 'Failed to generate preventive maintenance')}), 500
                
        except Exception as e:
            print(f"Generate preventive maintenance error: {e}")
            return jsonify({'error': 'Failed to generate preventive maintenance'}), 500
    
    # ===== TENANT SCREENING ENDPOINTS =====
    
    @app.route('/api/tenant-screening/dashboard', methods=['GET'])
    @require_permission(Permission.READ_TENANT)
    def get_tenant_screening_dashboard():
        """Get tenant screening dashboard data"""
        try:
            screening_service = get_tenant_screening_service()
            dashboard_data = screening_service.get_screening_dashboard_data()
            
            if dashboard_data.get('success'):
                return jsonify(dashboard_data)
            else:
                return jsonify({'error': dashboard_data.get('error', 'Failed to get dashboard data')}), 500
                
        except Exception as e:
            print(f"Tenant screening dashboard error: {e}")
            return jsonify({'error': 'Failed to get tenant screening dashboard data'}), 500
    
    @app.route('/api/tenant-screening/applications', methods=['GET', 'POST'])
    @require_permission(Permission.READ_TENANT)
    def handle_tenant_applications():
        """Handle tenant applications"""
        screening_service = get_tenant_screening_service()
        
        if request.method == 'GET':
            try:
                # Get filter parameters
                status_filter = request.args.get('status')
                property_id = request.args.get('property_id')
                
                applications = []
                for app in screening_service.applications.values():
                    # Apply filters
                    if status_filter and app.status.value != status_filter:
                        continue
                    if property_id and app.property_id != int(property_id):
                        continue
                    
                    # Serialize application data
                    app_data = {
                        'id': app.id,
                        'property_id': app.property_id,
                        'unit_id': app.unit_id,
                        'submitted_at': app.submitted_at.isoformat(),
                        'status': app.status.value,
                        'applicant_name': f"{app.personal_info.get('first_name', '')} {app.personal_info.get('last_name', '')}",
                        'email': app.personal_info.get('email', ''),
                        'phone': app.personal_info.get('phone', ''),
                        'annual_income': app.employment_info.get('annual_income'),
                        'employer': app.employment_info.get('employer', ''),
                        'is_complete': app.is_complete,
                        'application_fee_paid': app.application_fee_paid,
                        'screening_results': app.screening_results,
                        'decision_notes': app.decision_notes
                    }
                    applications.append(app_data)
                
                # Sort by submitted_at descending
                applications.sort(key=lambda x: x['submitted_at'], reverse=True)
                
                return jsonify({
                    'success': True,
                    'applications': applications
                })
                
            except Exception as e:
                print(f"Get tenant applications error: {e}")
                return jsonify({'error': 'Failed to get tenant applications'}), 500
        
        elif request.method == 'POST':
            try:
                data = request.json or {}
                
                required_fields = ['property_id', 'personal_info', 'employment_info']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                # Validate personal info
                personal_info = data['personal_info']
                required_personal = ['first_name', 'last_name', 'email', 'phone', 'ssn', 'date_of_birth']
                for field in required_personal:
                    if not personal_info.get(field):
                        return jsonify({'error': f'personal_info.{field} is required'}), 400
                
                # Validate employment info
                employment_info = data['employment_info']
                required_employment = ['employer', 'annual_income', 'employment_start_date']
                for field in required_employment:
                    if not employment_info.get(field):
                        return jsonify({'error': f'employment_info.{field} is required'}), 400
                
                result = screening_service.submit_application(
                    property_id=data['property_id'],
                    personal_info=personal_info,
                    employment_info=employment_info,
                    unit_id=data.get('unit_id'),
                    rental_history=data.get('rental_history', []),
                    references=data.get('references', []),
                    emergency_contacts=data.get('emergency_contacts', []),
                    lease_terms=data.get('lease_terms', {}),
                    application_fee_paid=data.get('application_fee_paid', False)
                )
                
                if result.get('success'):
                    return jsonify(result), 201
                else:
                    return jsonify({'error': result.get('error', 'Failed to submit application')}), 500
                    
            except Exception as e:
                print(f"Submit tenant application error: {e}")
                return jsonify({'error': 'Failed to submit tenant application'}), 500
    
    @app.route('/api/tenant-screening/applications/<application_id>', methods=['GET', 'PUT', 'DELETE'])
    @require_permission(Permission.READ_TENANT)
    def handle_tenant_application(application_id):
        """Handle individual tenant application"""
        screening_service = get_tenant_screening_service()
        
        if request.method == 'GET':
            try:
                if application_id not in screening_service.applications:
                    return jsonify({'error': 'Application not found'}), 404
                
                app = screening_service.applications[application_id]
                
                # Get associated screening checks
                app_checks = [check for check in screening_service.screening_checks.values() 
                             if check.application_id == application_id]
                
                # Get reference checks
                ref_checks = [check for check in screening_service.reference_checks.values() 
                             if check.application_id == application_id]
                
                app_data = {
                    'id': app.id,
                    'property_id': app.property_id,
                    'unit_id': app.unit_id,
                    'submitted_at': app.submitted_at.isoformat(),
                    'status': app.status.value,
                    'personal_info': app.personal_info,
                    'employment_info': app.employment_info,
                    'rental_history': app.rental_history,
                    'references': app.references,
                    'emergency_contacts': app.emergency_contacts,
                    'documents': app.documents,
                    'screening_results': app.screening_results,
                    'decision_notes': app.decision_notes,
                    'lease_terms': app.lease_terms,
                    'application_fee_paid': app.application_fee_paid,
                    'security_deposit_paid': app.security_deposit_paid,
                    'is_complete': app.is_complete,
                    'screening_checks': [
                        {
                            'id': check.id,
                            'check_type': check.check_type.value,
                            'status': check.status.value,
                            'score': check.score,
                            'completed_at': check.completed_at.isoformat() if check.completed_at else None,
                            'notes': check.notes,
                            'cost': check.cost
                        } for check in app_checks
                    ],
                    'reference_checks': [
                        {
                            'id': check.id,
                            'reference_type': check.reference_type,
                            'contact_name': check.contact_name,
                            'verification_status': check.verification_status,
                            'recommendation_score': check.recommendation_score,
                            'notes': check.notes
                        } for check in ref_checks
                    ]
                }
                
                return jsonify({
                    'success': True,
                    'application': app_data
                })
                
            except Exception as e:
                print(f"Get tenant application error: {e}")
                return jsonify({'error': 'Failed to get tenant application'}), 500
        
        elif request.method == 'PUT':
            try:
                if not has_permission(Permission.READ_TENANT):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json or {}
                
                if 'decision' in data:
                    # Application decision
                    decision_status = ApplicationStatus(data['decision'])
                    notes = data.get('notes', '')
                    conditions = data.get('conditions', [])
                    
                    result = screening_service.approve_application(
                        application_id=application_id,
                        decision=decision_status,
                        notes=notes,
                        conditions=conditions
                    )
                    
                    if result.get('success'):
                        return jsonify(result)
                    else:
                        return jsonify({'error': result.get('error', 'Failed to update application')}), 500
                
                # Other updates can be added here
                return jsonify({'error': 'No valid update data provided'}), 400
                
            except Exception as e:
                print(f"Update tenant application error: {e}")
                return jsonify({'error': 'Failed to update tenant application'}), 500
        
        elif request.method == 'DELETE':
            try:
                if not has_permission(Permission.READ_TENANT):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                if application_id in screening_service.applications:
                    # Mark as withdrawn instead of deleting
                    app = screening_service.applications[application_id]
                    app.status = ApplicationStatus.WITHDRAWN
                    return jsonify({'success': True, 'message': 'Application withdrawn'})
                else:
                    return jsonify({'error': 'Application not found'}), 404
                    
            except Exception as e:
                print(f"Delete tenant application error: {e}")
                return jsonify({'error': 'Failed to withdraw application'}), 500
    
    @app.route('/api/tenant-screening/applications/<application_id>/score', methods=['GET', 'POST'])
    @require_permission(Permission.READ_TENANT)
    def handle_application_score(application_id):
        """Handle application scoring"""
        screening_service = get_tenant_screening_service()
        
        if request.method == 'GET':
            try:
                result = screening_service.calculate_overall_score(application_id)
                
                if result.get('success'):
                    return jsonify(result)
                else:
                    return jsonify({'error': result.get('error', 'Failed to calculate score')}), 500
                    
            except Exception as e:
                print(f"Get application score error: {e}")
                return jsonify({'error': 'Failed to get application score'}), 500
        
        elif request.method == 'POST':
            try:
                if not has_permission(Permission.READ_TENANT):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Recalculate score (useful after manual updates to screening results)
                result = screening_service.calculate_overall_score(application_id)
                
                if result.get('success'):
                    return jsonify(result)
                else:
                    return jsonify({'error': result.get('error', 'Failed to recalculate score')}), 500
                    
            except Exception as e:
                print(f"Recalculate application score error: {e}")
                return jsonify({'error': 'Failed to recalculate application score'}), 500
    
    @app.route('/api/tenant-screening/criteria', methods=['GET', 'PUT'])
    @require_permission(Permission.READ_TENANT)
    def handle_screening_criteria():
        """Handle screening criteria configuration"""
        screening_service = get_tenant_screening_service()
        
        if request.method == 'GET':
            try:
                criteria = screening_service.screening_criteria
                scoring_model = screening_service.scoring_model
                
                return jsonify({
                    'success': True,
                    'criteria': {
                        'min_credit_score': criteria.min_credit_score,
                        'max_debt_to_income_ratio': criteria.max_debt_to_income_ratio,
                        'min_income_multiplier': criteria.min_income_multiplier,
                        'require_employment_verification': criteria.require_employment_verification,
                        'require_rental_history': criteria.require_rental_history,
                        'max_evictions_allowed': criteria.max_evictions_allowed,
                        'max_criminal_convictions': criteria.max_criminal_convictions,
                        'require_references': criteria.require_references,
                        'background_check_years': criteria.background_check_years,
                        'credit_check_required': criteria.credit_check_required
                    },
                    'scoring_model': {
                        'credit_score_weight': scoring_model.credit_score_weight,
                        'income_weight': scoring_model.income_weight,
                        'rental_history_weight': scoring_model.rental_history_weight,
                        'employment_weight': scoring_model.employment_weight,
                        'references_weight': scoring_model.references_weight,
                        'max_score': scoring_model.max_score
                    }
                })
                
            except Exception as e:
                print(f"Get screening criteria error: {e}")
                return jsonify({'error': 'Failed to get screening criteria'}), 500
        
        elif request.method == 'PUT':
            try:
                if not has_permission(Permission.MANAGE_ROLES):
                    return jsonify({'error': 'Admin permissions required'}), 403
                
                data = request.json or {}
                
                # Update screening criteria
                if 'criteria' in data:
                    criteria_data = data['criteria']
                    criteria = screening_service.screening_criteria
                    
                    if 'min_credit_score' in criteria_data:
                        criteria.min_credit_score = criteria_data['min_credit_score']
                    if 'max_debt_to_income_ratio' in criteria_data:
                        criteria.max_debt_to_income_ratio = criteria_data['max_debt_to_income_ratio']
                    if 'min_income_multiplier' in criteria_data:
                        criteria.min_income_multiplier = criteria_data['min_income_multiplier']
                    if 'require_employment_verification' in criteria_data:
                        criteria.require_employment_verification = criteria_data['require_employment_verification']
                    if 'require_rental_history' in criteria_data:
                        criteria.require_rental_history = criteria_data['require_rental_history']
                    if 'max_evictions_allowed' in criteria_data:
                        criteria.max_evictions_allowed = criteria_data['max_evictions_allowed']
                    if 'max_criminal_convictions' in criteria_data:
                        criteria.max_criminal_convictions = criteria_data['max_criminal_convictions']
                    if 'require_references' in criteria_data:
                        criteria.require_references = criteria_data['require_references']
                
                # Update scoring model
                if 'scoring_model' in data:
                    model_data = data['scoring_model']
                    scoring_model = screening_service.scoring_model
                    
                    if 'credit_score_weight' in model_data:
                        scoring_model.credit_score_weight = model_data['credit_score_weight']
                    if 'income_weight' in model_data:
                        scoring_model.income_weight = model_data['income_weight']
                    if 'rental_history_weight' in model_data:
                        scoring_model.rental_history_weight = model_data['rental_history_weight']
                    if 'employment_weight' in model_data:
                        scoring_model.employment_weight = model_data['employment_weight']
                    if 'references_weight' in model_data:
                        scoring_model.references_weight = model_data['references_weight']
                
                return jsonify({
                    'success': True,
                    'message': 'Screening criteria updated successfully'
                })
                
            except Exception as e:
                print(f"Update screening criteria error: {e}")
                return jsonify({'error': 'Failed to update screening criteria'}), 500
    
    @app.route('/api/tenant-screening/checks', methods=['GET'])
    @require_permission(Permission.READ_TENANT)
    def get_screening_checks():
        """Get screening checks for applications"""
        try:
            screening_service = get_tenant_screening_service()
            application_id = request.args.get('application_id')
            check_type = request.args.get('check_type')
            
            checks = []
            for check in screening_service.screening_checks.values():
                # Apply filters
                if application_id and check.application_id != application_id:
                    continue
                if check_type and check.check_type.value != check_type:
                    continue
                
                check_data = {
                    'id': check.id,
                    'application_id': check.application_id,
                    'check_type': check.check_type.value,
                    'status': check.status.value,
                    'score': check.score,
                    'provider': check.provider,
                    'completed_at': check.completed_at.isoformat() if check.completed_at else None,
                    'notes': check.notes,
                    'cost': check.cost,
                    'details': check.details
                }
                checks.append(check_data)
            
            # Sort by completion date descending
            checks.sort(key=lambda x: x['completed_at'] or '0000-00-00', reverse=True)
            
            return jsonify({
                'success': True,
                'checks': checks
            })
            
        except Exception as e:
            print(f"Get screening checks error: {e}")
            return jsonify({'error': 'Failed to get screening checks'}), 500
    
    @app.route('/api/tenant-screening/reports/summary', methods=['GET'])
    @require_permission(Permission.READ_TENANT)
    def get_screening_summary_report():
        """Get tenant screening summary report"""
        try:
            screening_service = get_tenant_screening_service()
            
            # Get date range parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates
            start_datetime = None
            end_datetime = None
            
            if start_date:
                try:
                    start_datetime = datetime.fromisoformat(start_date)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format'}), 400
            
            if end_date:
                try:
                    end_datetime = datetime.fromisoformat(end_date)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format'}), 400
            
            # Filter applications by date range
            applications = screening_service.applications.values()
            
            if start_datetime:
                applications = [app for app in applications if app.submitted_at >= start_datetime]
            
            if end_datetime:
                applications = [app for app in applications if app.submitted_at <= end_datetime]
            
            # Calculate metrics
            total_applications = len(applications)
            status_breakdown = {}
            
            for status in ApplicationStatus:
                count = len([app for app in applications if app.status == status])
                status_breakdown[status.value] = count
            
            # Calculate approval rates
            approved_count = status_breakdown.get('approved', 0)
            conditional_count = status_breakdown.get('conditionally_approved', 0)
            rejected_count = status_breakdown.get('rejected', 0)
            total_decided = approved_count + conditional_count + rejected_count
            
            approval_rate = (approved_count / total_decided * 100) if total_decided > 0 else 0
            conditional_rate = (conditional_count / total_decided * 100) if total_decided > 0 else 0
            rejection_rate = (rejected_count / total_decided * 100) if total_decided > 0 else 0
            
            # Calculate average scores
            completed_apps = [app for app in applications 
                            if 'overall_score' in app.screening_results]
            
            avg_score = 0
            if completed_apps:
                total_score = sum(app.screening_results['overall_score']['overall_score'] 
                                for app in completed_apps)
                avg_score = total_score / len(completed_apps)
            
            # Calculate revenue
            all_checks = [check for check in screening_service.screening_checks.values()
                         if any(app.id == check.application_id for app in applications)]
            total_screening_revenue = sum(check.cost for check in all_checks if check.completed_at)
            
            return jsonify({
                'success': True,
                'report': {
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'summary': {
                        'total_applications': total_applications,
                        'total_decided': total_decided,
                        'pending_review': total_applications - total_decided,
                        'average_score': round(avg_score, 1),
                        'total_screening_revenue': total_screening_revenue
                    },
                    'status_breakdown': status_breakdown,
                    'approval_metrics': {
                        'approval_rate': round(approval_rate, 1),
                        'conditional_rate': round(conditional_rate, 1),
                        'rejection_rate': round(rejection_rate, 1)
                    },
                    'applications': [
                        {
                            'id': app.id,
                            'applicant_name': f"{app.personal_info.get('first_name', '')} {app.personal_info.get('last_name', '')}",
                            'property_id': app.property_id,
                            'submitted_at': app.submitted_at.isoformat(),
                            'status': app.status.value,
                            'overall_score': app.screening_results.get('overall_score', {}).get('overall_score', 0)
                        }
                        for app in sorted(applications, key=lambda x: x.submitted_at, reverse=True)
                    ]
                }
            })
            
        except Exception as e:
            print(f"Get screening summary report error: {e}")
            return jsonify({'error': 'Failed to get screening summary report'}), 500
    
    # ===== BULK OPERATIONS ENDPOINTS =====
    
    @app.route('/api/bulk-operations/operations', methods=['GET', 'POST'])
    @require_permission(Permission.READ_USER)
    def handle_bulk_operations():
        """Handle bulk operations"""
        bulk_service = get_bulk_operations_service()
        
        if request.method == 'GET':
            try:
                user_id = request.args.get('user_id')
                limit = int(request.args.get('limit', 50))
                
                operations = bulk_service.get_operations_summary(
                    user_id=int(user_id) if user_id else None,
                    limit=limit
                )
                
                return jsonify({
                    'success': True,
                    'operations': operations
                })
                
            except Exception as e:
                print(f"Get bulk operations error: {e}")
                return jsonify({'error': 'Failed to get bulk operations'}), 500
        
        elif request.method == 'POST':
            try:
                if not has_permission(Permission.MANAGE_ROLES):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json or {}
                
                required_fields = ['operation_type', 'entity_type']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
                
                # Get current user
                current_user = load_user_permissions()
                created_by = current_user.get('user_id', 1)
                
                operation_id = bulk_service.create_bulk_operation(
                    operation_type=OperationType(data['operation_type']),
                    entity_type=EntityType(data['entity_type']),
                    created_by=created_by,
                    parameters=data.get('parameters', {})
                )
                
                return jsonify({
                    'success': True,
                    'operation_id': operation_id
                }), 201
                
            except Exception as e:
                print(f"Create bulk operation error: {e}")
                return jsonify({'error': 'Failed to create bulk operation'}), 500
    
    @app.route('/api/bulk-operations/operations/<operation_id>', methods=['GET', 'DELETE'])
    @require_permission(Permission.READ_USER)
    def handle_bulk_operation(operation_id):
        """Handle individual bulk operation"""
        bulk_service = get_bulk_operations_service()
        
        if request.method == 'GET':
            try:
                operation = bulk_service.get_operation_status(operation_id)
                if not operation:
                    return jsonify({'error': 'Operation not found'}), 404
                
                operation_data = {
                    'id': operation.id,
                    'operation_type': operation.operation_type.value,
                    'entity_type': operation.entity_type.value,
                    'status': operation.status.value,
                    'created_at': operation.created_at.isoformat(),
                    'started_at': operation.started_at.isoformat() if operation.started_at else None,
                    'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
                    'created_by': operation.created_by,
                    'total_records': operation.total_records,
                    'processed_records': operation.processed_records,
                    'successful_records': operation.successful_records,
                    'failed_records': operation.failed_records,
                    'progress_percentage': operation.progress_percentage,
                    'parameters': operation.parameters,
                    'results': operation.results,
                    'error_details': operation.error_details,
                    'estimated_completion': operation.estimated_completion.isoformat() if operation.estimated_completion else None
                }
                
                return jsonify({
                    'success': True,
                    'operation': operation_data
                })
                
            except Exception as e:
                print(f"Get bulk operation error: {e}")
                return jsonify({'error': 'Failed to get bulk operation'}), 500
        
        elif request.method == 'DELETE':
            try:
                if not has_permission(Permission.MANAGE_ROLES):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                success = bulk_service.cancel_operation(operation_id)
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Operation cancelled successfully'
                    })
                else:
                    return jsonify({'error': 'Failed to cancel operation or operation not found'}), 404
                    
            except Exception as e:
                print(f"Cancel bulk operation error: {e}")
                return jsonify({'error': 'Failed to cancel bulk operation'}), 500
    
    @app.route('/api/bulk-operations/import', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def bulk_import():
        """Handle bulk import operations"""
        try:
            # Get file data from request
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Get operation parameters
            operation_type = request.form.get('operation_type', 'import')
            entity_type = request.form.get('entity_type')
            file_type = request.form.get('file_type', 'csv')
            
            if not entity_type:
                return jsonify({'error': 'entity_type is required'}), 400
            
            # Get current user
            current_user = load_user_permissions()
            created_by = current_user.get('user_id', 1)
            
            # Create bulk operation
            bulk_service = get_bulk_operations_service()
            operation_id = bulk_service.create_bulk_operation(
                operation_type=OperationType(operation_type),
                entity_type=EntityType(entity_type),
                created_by=created_by,
                parameters={'file_type': file_type, 'filename': file.filename}
            )
            
            # Read file data
            file_data = file.read().decode('utf-8')
            
            # Process import
            result = bulk_service.process_bulk_import(operation_id, file_data, file_type)
            
            return jsonify({
                'success': result.success,
                'operation_id': operation_id,
                'total_processed': result.total_processed,
                'successful_count': result.successful_count,
                'failed_count': result.failed_count,
                'execution_time_seconds': result.execution_time_seconds,
                'errors': result.errors[:10]  # Limit errors in response
            })
            
        except Exception as e:
            print(f"Bulk import error: {e}")
            return jsonify({'error': 'Failed to process bulk import'}), 500
    
    @app.route('/api/bulk-operations/update', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def bulk_update():
        """Handle bulk update operations"""
        try:
            data = request.json or {}
            
            required_fields = ['entity_type', 'record_ids', 'update_data']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            # Get current user
            current_user = load_user_permissions()
            created_by = current_user.get('user_id', 1)
            
            # Create bulk operation
            bulk_service = get_bulk_operations_service()
            operation_id = bulk_service.create_bulk_operation(
                operation_type=OperationType.UPDATE,
                entity_type=EntityType(data['entity_type']),
                created_by=created_by,
                parameters={'update_fields': list(data['update_data'].keys())}
            )
            
            # Process update
            result = bulk_service.process_bulk_update(
                operation_id=operation_id,
                record_ids=data['record_ids'],
                update_data=data['update_data']
            )
            
            return jsonify({
                'success': result.success,
                'operation_id': operation_id,
                'total_processed': result.total_processed,
                'successful_count': result.successful_count,
                'failed_count': result.failed_count,
                'execution_time_seconds': result.execution_time_seconds,
                'errors': result.errors[:10]
            })
            
        except Exception as e:
            print(f"Bulk update error: {e}")
            return jsonify({'error': 'Failed to process bulk update'}), 500
    
    @app.route('/api/bulk-operations/export', methods=['POST'])
    @require_permission(Permission.READ_USER)
    def bulk_export():
        """Handle bulk export operations"""
        try:
            data = request.json or {}
            
            required_fields = ['entity_type']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            # Get current user
            current_user = load_user_permissions()
            created_by = current_user.get('user_id', 1)
            
            # Create bulk operation
            bulk_service = get_bulk_operations_service()
            operation_id = bulk_service.create_bulk_operation(
                operation_type=OperationType.EXPORT,
                entity_type=EntityType(data['entity_type']),
                created_by=created_by,
                parameters={
                    'format': data.get('format', 'csv'),
                    'filters': data.get('filters', {})
                }
            )
            
            # Process export
            result = bulk_service.process_bulk_export(
                operation_id=operation_id,
                filters=data.get('filters', {}),
                format=data.get('format', 'csv')
            )
            
            return jsonify({
                'success': result.success,
                'operation_id': operation_id,
                'total_processed': result.total_processed,
                'execution_time_seconds': result.execution_time_seconds,
                'output_file_path': result.output_file_path
            })
            
        except Exception as e:
            print(f"Bulk export error: {e}")
            return jsonify({'error': 'Failed to process bulk export'}), 500
    
    @app.route('/api/bulk-operations/validate', methods=['POST'])
    @require_permission(Permission.READ_USER)
    def validate_bulk_data():
        """Validate bulk data before processing"""
        try:
            # Get file data from request
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            entity_type = request.form.get('entity_type')
            file_type = request.form.get('file_type', 'csv')
            
            if not entity_type:
                return jsonify({'error': 'entity_type is required'}), 400
            
            # Read and parse file data
            file_data = file.read().decode('utf-8')
            bulk_service = get_bulk_operations_service()
            
            if file_type.lower() == 'csv':
                data = bulk_service._parse_csv_data(file_data)
            elif file_type.lower() == 'json':
                data = json.loads(file_data)
            else:
                return jsonify({'error': f'Unsupported file type: {file_type}'}), 400
            
            # Validate data
            validation_result = bulk_service.validate_bulk_data(EntityType(entity_type), data)
            
            return jsonify({
                'success': True,
                'is_valid': validation_result.is_valid,
                'total_records': len(data),
                'valid_records': len(validation_result.valid_records),
                'invalid_records': len(validation_result.invalid_records),
                'errors': validation_result.errors[:20],  # Limit errors
                'warnings': validation_result.warnings[:20]  # Limit warnings
            })
            
        except Exception as e:
            print(f"Bulk validation error: {e}")
            return jsonify({'error': 'Failed to validate bulk data'}), 500
    
    @app.route('/api/bulk-operations/templates/<entity_type>', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_bulk_template(entity_type):
        """Get CSV template for bulk operations"""
        try:
            templates = {
                'properties': [
                    'property_name', 'address', 'property_type', 'rent_amount', 
                    'bedrooms', 'bathrooms', 'square_feet', 'status'
                ],
                'tenants': [
                    'first_name', 'last_name', 'email', 'phone', 'property_id',
                    'lease_start', 'lease_end', 'monthly_rent', 'security_deposit'
                ],
                'maintenance_requests': [
                    'property_id', 'title', 'description', 'priority', 'maintenance_type',
                    'estimated_cost', 'tenant_access_required'
                ],
                'users': [
                    'username', 'email', 'first_name', 'last_name', 'role', 'is_active'
                ]
            }
            
            if entity_type not in templates:
                return jsonify({'error': 'Invalid entity type'}), 400
            
            # Generate CSV template
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(templates[entity_type])
            
            csv_content = output.getvalue()
            output.close()
            
            response = app.response_class(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={entity_type}_template.csv'}
            )
            
            return response
            
        except Exception as e:
            print(f"Get bulk template error: {e}")
            return jsonify({'error': 'Failed to get bulk template'}), 500

    # Performance Optimization API Endpoints
    @app.route('/api/performance/summary', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_performance_summary():
        """Get comprehensive performance summary"""
        try:
            performance_service = get_performance_service()
            summary = performance_service.get_performance_summary()
            return jsonify(summary)
        except Exception as e:
            print(f"Performance summary error: {e}")
            return jsonify({'error': 'Failed to get performance summary'}), 500
    
    @app.route('/api/performance/recommendations', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_performance_recommendations():
        """Get performance optimization recommendations"""
        try:
            performance_service = get_performance_service()
            recommendations = performance_service.generate_optimization_recommendations()
            return jsonify({'recommendations': recommendations})
        except Exception as e:
            print(f"Performance recommendations error: {e}")
            return jsonify({'error': 'Failed to get recommendations'}), 500
    
    @app.route('/api/performance/settings', methods=['GET', 'PUT'])
    @require_permission(Permission.MANAGE_ROLES)
    def manage_performance_settings():
        """Get or update performance settings"""
        try:
            performance_service = get_performance_service()
            
            if request.method == 'GET':
                return jsonify(performance_service.settings)
            
            elif request.method == 'PUT':
                new_settings = request.json
                result = performance_service.optimize_settings(new_settings)
                return jsonify(result)
                
        except Exception as e:
            print(f"Performance settings error: {e}")
            return jsonify({'error': 'Failed to manage performance settings'}), 500
    
    @app.route('/api/performance/cache/clear', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def clear_performance_cache():
        """Clear all performance caches"""
        try:
            performance_service = get_performance_service()
            result = performance_service.clear_caches()
            return jsonify(result)
        except Exception as e:
            print(f"Clear cache error: {e}")
            return jsonify({'error': 'Failed to clear cache'}), 500
    
    @app.route('/api/performance/metrics/<endpoint_name>', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_endpoint_metrics(endpoint_name):
        """Get performance metrics for specific endpoint"""
        try:
            hours = request.args.get('hours', 24, type=int)
            performance_service = get_performance_service()
            stats = performance_service.monitor.get_endpoint_stats(endpoint_name, hours)
            return jsonify(stats)
        except Exception as e:
            print(f"Endpoint metrics error: {e}")
            return jsonify({'error': 'Failed to get endpoint metrics'}), 500
    
    @app.route('/api/performance/slow-endpoints', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_slow_endpoints():
        """Get slow performing endpoints"""
        try:
            threshold_ms = request.args.get('threshold_ms', 1000, type=float)
            hours = request.args.get('hours', 24, type=int)
            performance_service = get_performance_service()
            slow_endpoints = performance_service.monitor.get_slow_endpoints(threshold_ms, hours)
            return jsonify({'slow_endpoints': slow_endpoints})
        except Exception as e:
            print(f"Slow endpoints error: {e}")
            return jsonify({'error': 'Failed to get slow endpoints'}), 500
    
    @app.route('/api/performance/slow-queries', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_slow_queries():
        """Get slow performing database queries"""
        try:
            threshold_ms = request.args.get('threshold_ms', 500, type=float)
            performance_service = get_performance_service()
            slow_queries = performance_service.db_optimizer.get_slow_queries(threshold_ms)
            return jsonify({'slow_queries': slow_queries})
        except Exception as e:
            print(f"Slow queries error: {e}")
            return jsonify({'error': 'Failed to get slow queries'}), 500

    # Testing Framework API Endpoints
    @app.route('/api/testing/run', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def run_tests():
        """Run test suite"""
        try:
            import subprocess
            import threading
            
            data = request.json or {}
            test_suite = data.get('suite', 'all')
            
            # Mock test execution for demo purposes
            # In production, this would run actual pytest commands
            result = {
                'success': True,
                'test_run_id': 'test_run_' + str(int(time.time())),
                'status': 'running',
                'message': f'Started {test_suite} test suite'
            }
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Run tests error: {e}")
            return jsonify({'error': 'Failed to run tests'}), 500
    
    @app.route('/api/testing/results', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_test_results():
        """Get latest test results"""
        try:
            # Mock test results - in production, read from test output files
            results = {
                'summary': {
                    'total_tests': 127,
                    'passed': 119,
                    'failed': 8,
                    'skipped': 0,
                    'success_rate': 93.7,
                    'execution_time': '2m 45s',
                    'last_run': datetime.utcnow().isoformat()
                },
                'categories': {
                    'unit': {'total': 45, 'passed': 42, 'failed': 3, 'status': 'warning'},
                    'integration': {'total': 20, 'passed': 18, 'failed': 2, 'status': 'warning'},
                    'performance': {'total': 15, 'passed': 15, 'failed': 0, 'status': 'success'},
                    'security': {'total': 12, 'passed': 11, 'failed': 1, 'status': 'warning'},
                    'api': {'total': 35, 'passed': 33, 'failed': 2, 'status': 'warning'}
                },
                'recent_failures': [
                    {
                        'test_name': 'test_payment_processing_with_invalid_card',
                        'category': 'unit',
                        'error': 'AssertionError: Expected payment to fail with invalid card',
                        'file': 'test_rent_collection.py:145',
                        'duration': '0.12s'
                    },
                    {
                        'test_name': 'test_bulk_import_large_dataset',
                        'category': 'performance',
                        'error': 'Timeout: Test exceeded 30s execution time',
                        'file': 'test_bulk_operations.py:89',
                        'duration': '30.01s'
                    }
                ]
            }
            
            return jsonify(results)
            
        except Exception as e:
            print(f"Get test results error: {e}")
            return jsonify({'error': 'Failed to get test results'}), 500
    
    @app.route('/api/testing/history', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_test_history():
        """Get test execution history"""
        try:
            limit = request.args.get('limit', 50, type=int)
            
            # Mock test history
            history = [
                {
                    'id': 1,
                    'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    'total': 127,
                    'passed': 119,
                    'failed': 8,
                    'success_rate': 93.7,
                    'duration': '2m 45s',
                    'branch': 'main',
                    'commit': 'abc123f',
                    'triggered_by': 'CI/CD Pipeline'
                },
                {
                    'id': 2,
                    'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    'total': 125,
                    'passed': 123,
                    'failed': 2,
                    'success_rate': 98.4,
                    'duration': '2m 32s',
                    'branch': 'main',
                    'commit': 'def456a',
                    'triggered_by': 'Manual Run'
                }
            ]
            
            return jsonify({'history': history[:limit]})
            
        except Exception as e:
            print(f"Get test history error: {e}")
            return jsonify({'error': 'Failed to get test history'}), 500
    
    @app.route('/api/testing/coverage', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_test_coverage():
        """Get code coverage report"""
        try:
            # Mock coverage data - in production, read from coverage reports
            coverage = {
                'overall': {
                    'lines_covered': 92.1,
                    'functions_covered': 84.3,
                    'branches_covered': 79.8,
                    'overall_coverage': 87.5
                },
                'files': [
                    {'file': 'database_service.py', 'coverage': 95.2, 'lines': '245/258'},
                    {'file': 'permissions_service.py', 'coverage': 91.8, 'lines': '189/206'},
                    {'file': 'rent_collection_service.py', 'coverage': 88.4, 'lines': '298/337'},
                    {'file': 'security_service.py', 'coverage': 92.6, 'lines': '267/288'},
                    {'file': 'maintenance_service.py', 'coverage': 83.1, 'lines': '224/269'},
                    {'file': 'financial_reporting.py', 'coverage': 89.7, 'lines': '178/198'}
                ],
                'uncovered_lines': [
                    {'file': 'rent_collection_service.py', 'lines': [145, 167, 234, 289]},
                    {'file': 'maintenance_service.py', 'lines': [89, 156, 203, 245, 267]}
                ]
            }
            
            return jsonify(coverage)
            
        except Exception as e:
            print(f"Get test coverage error: {e}")
            return jsonify({'error': 'Failed to get test coverage'}), 500
    
    @app.route('/api/testing/logs/<test_run_id>', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_test_logs(test_run_id):
        """Get logs for specific test run"""
        try:
            # Mock test logs - in production, read from log files
            logs = [
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'info',
                    'message': f'Starting test run {test_run_id}...'
                },
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'info',
                    'message': 'Setting up test environment...'
                },
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'success',
                    'message': 'Database connection established'
                }
            ]
            
            return jsonify({'logs': logs})
            
        except Exception as e:
            print(f"Get test logs error: {e}")
            return jsonify({'error': 'Failed to get test logs'}), 500

    # Rate Limiting Middleware and API Endpoints
    @app.before_request
    def check_rate_limits():
        """Check rate limits for incoming requests"""
        from flask import request, jsonify, g
        
        # Skip rate limiting for certain endpoints
        if request.endpoint in ['static', 'health'] or request.path.startswith('/static/'):
            return
        
        # Skip OPTIONS requests
        if request.method == 'OPTIONS':
            return
        
        try:
            rate_limiting_service = get_rate_limiting_service()
            
            # Get client identifier
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Get user ID if available
            user_id = getattr(g, 'user_id', None)
            
            # Check rate limit
            result = rate_limiting_service.check_rate_limit(
                identifier=client_ip,
                endpoint=request.path,
                user_id=user_id
            )
            
            if not result['allowed']:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Reason: {result["reason"]}',
                    'retry_after': result.get('retry_after'),
                    'remaining': result.get('remaining', 0)
                })
                response.status_code = 429
                response.headers['X-RateLimit-Remaining'] = str(result.get('remaining', 0))
                if result.get('retry_after'):
                    response.headers['Retry-After'] = str(int(result['retry_after']))
                return response
                
        except Exception as e:
            # Log error but don't block requests if rate limiting fails
            print(f"Rate limiting error: {e}")
    
    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to responses"""
        try:
            from flask import request, g
            
            # Skip for static files and certain endpoints
            if request.endpoint in ['static'] or request.path.startswith('/static/'):
                return response
            
            rate_limiting_service = get_rate_limiting_service()
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            user_id = getattr(g, 'user_id', None)
            
            # Get current rate limit status
            status = rate_limiting_service.get_rate_limit_status(
                identifier=client_ip,
                endpoint=request.path,
                user_id=user_id
            )
            
            if 'status' in status and status['status'] != 'no_data':
                if 'current_requests' in status['status']:
                    remaining = status['status'].get('max_requests', 0) - status['status'].get('current_requests', 0)
                    response.headers['X-RateLimit-Remaining'] = str(max(0, remaining))
                
                if 'reset_time' in status['status'] and status['status']['reset_time']:
                    response.headers['X-RateLimit-Reset'] = str(int(status['status']['reset_time']))
                    
        except Exception as e:
            # Don't let header addition break responses
            pass
        
        return response
    
    @app.route('/api/rate-limiting/status', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_rate_limiting_status():
        """Get rate limiting status and statistics"""
        try:
            rate_limiting_service = get_rate_limiting_service()
            stats = rate_limiting_service.get_statistics()
            return jsonify(stats)
        except Exception as e:
            print(f"Rate limiting status error: {e}")
            return jsonify({'error': 'Failed to get rate limiting status'}), 500
    
    @app.route('/api/rate-limiting/reset', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def reset_rate_limits():
        """Reset rate limits for specific identifier/endpoint"""
        try:
            data = request.json
            identifier = data.get('identifier')
            endpoint = data.get('endpoint')
            user_id = data.get('user_id')
            
            if not identifier or not endpoint:
                return jsonify({'error': 'identifier and endpoint are required'}), 400
            
            rate_limiting_service = get_rate_limiting_service()
            result = rate_limiting_service.reset_rate_limit(
                identifier=identifier,
                endpoint=endpoint,
                user_id=user_id
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Reset rate limits error: {e}")
            return jsonify({'error': 'Failed to reset rate limits'}), 500
    
    @app.route('/api/rate-limiting/configure', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def configure_rate_limiting():
        """Configure rate limiting for specific endpoint"""
        try:
            data = request.json
            endpoint = data.get('endpoint')
            
            if not endpoint:
                return jsonify({'error': 'endpoint is required'}), 400
            
            config = RateLimitConfig(
                requests_per_minute=data.get('requests_per_minute', 60),
                requests_per_hour=data.get('requests_per_hour', 1000),
                algorithm=RateLimitAlgorithm(data.get('algorithm', 'sliding_window')),
                scope=RateLimitScope(data.get('scope', 'per_ip')),
                burst_allowance=data.get('burst_allowance', 10),
                whitelist=data.get('whitelist', []),
                blacklist=data.get('blacklist', [])
            )
            
            rate_limiting_service = get_rate_limiting_service()
            rate_limiting_service.configure_endpoint(endpoint, config)
            
            return jsonify({
                'success': True,
                'message': f'Rate limiting configured for {endpoint}',
                'config': {
                    'requests_per_minute': config.requests_per_minute,
                    'algorithm': config.algorithm.value,
                    'scope': config.scope.value
                }
            })
            
        except Exception as e:
            print(f"Configure rate limiting error: {e}")
            return jsonify({'error': 'Failed to configure rate limiting'}), 500
    
    @app.route('/api/rate-limiting/cleanup', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def cleanup_rate_limiters():
        """Clean up expired rate limiters"""
        try:
            rate_limiting_service = get_rate_limiting_service()
            rate_limiting_service.cleanup_expired_limiters()
            
            return jsonify({
                'success': True,
                'message': 'Rate limiter cleanup completed'
            })
            
        except Exception as e:
            print(f"Cleanup rate limiters error: {e}")
            return jsonify({'error': 'Failed to cleanup rate limiters'}), 500

    # Enhanced LPR API Endpoints
    @app.route('/api/lpr/cameras', methods=['GET', 'POST'])
    @require_permission(Permission.READ_USER)
    def handle_lpr_cameras():
        """Get or add LPR cameras"""
        try:
            lpr_service = get_enhanced_lpr_service()
            
            if request.method == 'GET':
                cameras = []
                for camera_id, camera in lpr_service.cameras.items():
                    cameras.append({
                        'id': camera.id,
                        'name': camera.name,
                        'location': camera.location,
                        'camera_type': camera.camera_type.value,
                        'rtsp_url': camera.rtsp_url,
                        'property_id': camera.property_id,
                        'provider': camera.provider.value,
                        'confidence_threshold': camera.confidence_threshold,
                        'is_active': camera.is_active,
                        'last_detection': camera.last_detection.isoformat() if camera.last_detection else None,
                        'total_detections': camera.total_detections,
                        'settings': camera.settings
                    })
                
                return jsonify({'cameras': cameras})
            
            elif request.method == 'POST':
                if not has_permission(Permission.MANAGE_ROLES):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json
                camera = LPRCamera(
                    id=data.get('id', f"cam_{int(time.time())}"),
                    name=data['name'],
                    location=data['location'],
                    camera_type=CameraType(data['camera_type']),
                    rtsp_url=data['rtsp_url'],
                    property_id=data['property_id'],
                    provider=LPRProvider(data.get('provider', 'mock')),
                    confidence_threshold=data.get('confidence_threshold', 0.8),
                    is_active=data.get('is_active', True),
                    settings=data.get('settings', {})
                )
                
                success = lpr_service.add_camera(camera)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Camera added successfully',
                        'camera_id': camera.id
                    })
                else:
                    return jsonify({'error': 'Failed to add camera'}), 500
                    
        except Exception as e:
            print(f"LPR cameras error: {e}")
            return jsonify({'error': 'Failed to handle LPR cameras'}), 500
    
    @app.route('/api/lpr/cameras/<camera_id>', methods=['PUT', 'DELETE'])
    @require_permission(Permission.MANAGE_ROLES)
    def handle_lpr_camera(camera_id):
        """Update or delete LPR camera"""
        try:
            lpr_service = get_enhanced_lpr_service()
            
            if camera_id not in lpr_service.cameras:
                return jsonify({'error': 'Camera not found'}), 404
            
            if request.method == 'PUT':
                data = request.json
                camera = lpr_service.cameras[camera_id]
                
                # Update camera properties
                camera.name = data.get('name', camera.name)
                camera.location = data.get('location', camera.location)
                camera.rtsp_url = data.get('rtsp_url', camera.rtsp_url)
                camera.confidence_threshold = data.get('confidence_threshold', camera.confidence_threshold)
                camera.is_active = data.get('is_active', camera.is_active)
                camera.settings = data.get('settings', camera.settings)
                
                return jsonify({
                    'success': True,
                    'message': 'Camera updated successfully'
                })
            
            elif request.method == 'DELETE':
                del lpr_service.cameras[camera_id]
                
                return jsonify({
                    'success': True,
                    'message': 'Camera deleted successfully'
                })
                
        except Exception as e:
            print(f"LPR camera error: {e}")
            return jsonify({'error': 'Failed to handle LPR camera'}), 500
    
    @app.route('/api/lpr/cameras/<camera_id>/start', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def start_lpr_camera(camera_id):
        """Start LPR camera monitoring"""
        try:
            lpr_service = get_enhanced_lpr_service()
            success = lpr_service.start_camera_monitoring(camera_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Camera {camera_id} monitoring started'
                })
            else:
                return jsonify({'error': 'Failed to start camera monitoring'}), 500
                
        except Exception as e:
            print(f"Start LPR camera error: {e}")
            return jsonify({'error': 'Failed to start camera monitoring'}), 500
    
    @app.route('/api/lpr/cameras/start-all', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def start_all_lpr_cameras():
        """Start all LPR camera monitoring"""
        try:
            lpr_service = get_enhanced_lpr_service()
            results = lpr_service.start_all_cameras()
            
            return jsonify({
                'success': True,
                'message': 'All cameras started',
                'results': results
            })
            
        except Exception as e:
            print(f"Start all LPR cameras error: {e}")
            return jsonify({'error': 'Failed to start all cameras'}), 500
    
    @app.route('/api/lpr/cameras/stop-all', methods=['POST'])
    @require_permission(Permission.MANAGE_ROLES)
    def stop_all_lpr_cameras():
        """Stop all LPR camera monitoring"""
        try:
            lpr_service = get_enhanced_lpr_service()
            lpr_service.stop_all_cameras()
            
            return jsonify({
                'success': True,
                'message': 'All cameras stopped'
            })
            
        except Exception as e:
            print(f"Stop all LPR cameras error: {e}")
            return jsonify({'error': 'Failed to stop all cameras'}), 500
    
    @app.route('/api/lpr/vehicles', methods=['GET', 'POST'])
    @require_permission(Permission.READ_USER)
    def handle_lpr_vehicles():
        """Get or add vehicle records"""
        try:
            lpr_service = get_enhanced_lpr_service()
            
            if request.method == 'GET':
                vehicles = []
                for plate, vehicle in lpr_service.vehicle_records.items():
                    vehicles.append({
                        'license_plate': vehicle.license_plate,
                        'owner_name': vehicle.owner_name,
                        'tenant_id': vehicle.tenant_id,
                        'property_id': vehicle.property_id,
                        'status': vehicle.status.value,
                        'valid_from': vehicle.valid_from.isoformat(),
                        'valid_until': vehicle.valid_until.isoformat() if vehicle.valid_until else None,
                        'notes': vehicle.notes,
                        'created_at': vehicle.created_at.isoformat(),
                        'updated_at': vehicle.updated_at.isoformat()
                    })
                
                return jsonify({'vehicles': vehicles})
            
            elif request.method == 'POST':
                if not has_permission(Permission.MANAGE_ROLES):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.json
                
                valid_until = None
                if data.get('valid_until'):
                    valid_until = datetime.fromisoformat(data['valid_until'].replace('Z', '+00:00'))
                
                vehicle = VehicleRecord(
                    license_plate=data['license_plate'].upper(),
                    owner_name=data.get('owner_name'),
                    tenant_id=data.get('tenant_id'),
                    property_id=data['property_id'],
                    status=VehicleStatus(data['status']),
                    valid_from=datetime.fromisoformat(data['valid_from'].replace('Z', '+00:00')),
                    valid_until=valid_until,
                    notes=data.get('notes', '')
                )
                
                success = lpr_service.add_vehicle_record(vehicle)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Vehicle record added successfully'
                    })
                else:
                    return jsonify({'error': 'Failed to add vehicle record'}), 500
                    
        except Exception as e:
            print(f"LPR vehicles error: {e}")
            return jsonify({'error': 'Failed to handle LPR vehicles'}), 500
    
    @app.route('/api/lpr/detections', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_lpr_detections():
        """Get LPR detections with filters"""
        try:
            lpr_service = get_enhanced_lpr_service()
            
            # Get query parameters
            hours = request.args.get('hours', 24, type=int)
            property_id = request.args.get('property_id', type=int)
            license_plate = request.args.get('license_plate')
            camera_id = request.args.get('camera_id')
            
            if license_plate or camera_id:
                # Use search function for specific filters
                start_date = datetime.utcnow() - timedelta(hours=hours)
                detections = lpr_service.search_detections(
                    license_plate=license_plate,
                    camera_id=camera_id,
                    start_date=start_date
                )
            else:
                # Use recent detections
                detections = lpr_service.get_recent_detections(hours=hours, property_id=property_id)
            
            return jsonify({'detections': detections})
            
        except Exception as e:
            print(f"Get LPR detections error: {e}")
            return jsonify({'error': 'Failed to get LPR detections'}), 500
    
    @app.route('/api/lpr/statistics', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_lpr_statistics():
        """Get LPR system statistics"""
        try:
            lpr_service = get_enhanced_lpr_service()
            stats = lpr_service.get_statistics()
            
            return jsonify(stats)
            
        except Exception as e:
            print(f"Get LPR statistics error: {e}")
            return jsonify({'error': 'Failed to get LPR statistics'}), 500
    
    @app.route('/api/lpr/alerts', methods=['GET'])
    @require_permission(Permission.READ_USER)
    def get_lpr_alerts():
        """Get recent LPR security alerts"""
        try:
            lpr_service = get_enhanced_lpr_service()
            
            # Get detections that triggered alerts
            hours = request.args.get('hours', 24, type=int)
            detections = lpr_service.get_recent_detections(hours=hours)
            
            alerts = []
            for detection in detections:
                if detection['access_action'] in ['deny', 'alert']:
                    alerts.append({
                        'id': detection['id'],
                        'license_plate': detection['license_plate'],
                        'camera_id': detection['camera_id'],
                        'timestamp': detection['timestamp'],
                        'vehicle_status': detection['vehicle_status'],
                        'access_action': detection['access_action'],
                        'property_id': detection['property_id'],
                        'confidence': detection['confidence'],
                        'metadata': detection['metadata']
                    })
            
            return jsonify({'alerts': alerts})
            
        except Exception as e:
            print(f"Get LPR alerts error: {e}")
            return jsonify({'error': 'Failed to get LPR alerts'}), 500

    # Energy Management API Routes
    @app.route('/api/energy/readings', methods=['POST'])
    def add_energy_reading():
        """Add a new energy reading"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['property_id', 'energy_type', 'consumption', 'cost']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # Parse timestamp if provided
            timestamp = None
            if 'timestamp' in data:
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid timestamp format. Use ISO format: YYYY-MM-DDTHH:MM:SS'
                    }), 400
            
            # Add reading using service
            result = app.energy_service.add_energy_reading(
                property_id=int(data['property_id']),
                energy_type=data['energy_type'],
                consumption=float(data['consumption']),
                cost=float(data['cost']),
                timestamp=timestamp,
                unit_id=data.get('unit_id'),
                temperature=data.get('temperature'),
                occupancy=data.get('occupancy'),
                equipment_id=data.get('equipment_id'),
                metadata=data.get('metadata')
            )
            
            status_code = 201 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to add energy reading: {str(e)}'
            }), 500

    @app.route('/api/energy/forecast/<int:property_id>/<energy_type>')
    def get_energy_forecast(property_id, energy_type):
        """Get energy consumption forecast"""
        try:
            # Get optional parameters
            days = request.args.get('days', 7, type=int)
            
            if days < 1 or days > 365:
                return jsonify({
                    'success': False,
                    'error': 'Days parameter must be between 1 and 365'
                }), 400
            
            # Generate forecast using service
            result = app.energy_service.get_energy_forecast(
                property_id=property_id,
                energy_type=energy_type,
                days=days
            )
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to generate forecast: {str(e)}'
            }), 500

    @app.route('/api/energy/recommendations/<int:property_id>')
    def get_optimization_recommendations(property_id):
        """Get AI-powered optimization recommendations"""
        try:
            result = app.energy_service.get_optimization_recommendations(property_id)
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get recommendations: {str(e)}'
            }), 500

    @app.route('/api/energy/analytics/<int:property_id>')
    def get_energy_analytics(property_id):
        """Get comprehensive energy analytics"""
        try:
            # Get optional parameters
            days = request.args.get('days', 30, type=int)
            
            if days < 1 or days > 365:
                return jsonify({
                    'success': False,
                    'error': 'Days parameter must be between 1 and 365'
                }), 400
            
            result = app.energy_service.get_energy_analytics(property_id, days)
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get analytics: {str(e)}'
            }), 500

    @app.route('/api/energy/alerts')
    def get_energy_alerts():
        """Get energy management alerts"""
        try:
            # Get optional parameters
            property_id = request.args.get('property_id', type=int)
            status = request.args.get('status', 'active')
            severity = request.args.get('severity')
            
            result = app.energy_service.get_energy_alerts(
                property_id=property_id,
                status=status,
                severity=severity
            )
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get alerts: {str(e)}'
            }), 500

    @app.route('/api/energy/dashboard/<int:property_id>')
    def get_energy_dashboard(property_id):
        """Get comprehensive energy dashboard data"""
        try:
            result = app.energy_service.get_energy_dashboard_data(property_id)
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get dashboard data: {str(e)}'
            }), 500

    @app.route('/api/energy/simulate/<int:property_id>', methods=['POST'])
    def simulate_energy_data(property_id):
        """Simulate energy data for demonstration purposes"""
        try:
            data = request.get_json() or {}
            days = data.get('days', 7)
            
            if days < 1 or days > 90:
                return jsonify({
                    'success': False,
                    'error': 'Days parameter must be between 1 and 90'
                }), 400
            
            result = app.energy_service.simulate_energy_data(property_id, days)
            
            status_code = 200 if result['success'] else 400
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to simulate data: {str(e)}'
            }), 500

    @app.route('/api/energy/types')
    def get_energy_types():
        """Get available energy types"""
        try:
            energy_types = [
                {
                    'value': 'electricity',
                    'label': 'Electricity',
                    'unit': 'kWh',
                    'description': 'Electrical energy consumption'
                },
                {
                    'value': 'gas',
                    'label': 'Natural Gas',
                    'unit': 'therms',
                    'description': 'Natural gas consumption'
                },
                {
                    'value': 'water',
                    'label': 'Water',
                    'unit': 'gallons',
                    'description': 'Water consumption'
                },
                {
                    'value': 'hvac',
                    'label': 'HVAC',
                    'unit': 'kWh',
                    'description': 'Heating, ventilation, and air conditioning'
                },
                {
                    'value': 'lighting',
                    'label': 'Lighting',
                    'unit': 'kWh',
                    'description': 'Lighting systems energy consumption'
                },
                {
                    'value': 'solar',
                    'label': 'Solar',
                    'unit': 'kWh',
                    'description': 'Solar energy generation'
                }
            ]
            
            return jsonify({
                'success': True,
                'energy_types': energy_types
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get energy types: {str(e)}'
            }), 500

    @app.route('/api/energy/health')
    def energy_health_check():
        """Health check endpoint for energy management service"""
        try:
            # Check data availability
            data_count = len(app.energy_service.engine.energy_readings)
            
            return jsonify({
                'success': True,
                'status': 'healthy',
                'models_trained': True,  # Simplified engine is always ready
                'data_points': data_count,
                'service_version': '1.0.0',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    # Computer Vision API Routes
    @app.route('/api/ai/analyze-property', methods=['POST'])
    def analyze_property_image():
        """Analyze property image for condition assessment"""
        try:
            if 'image' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No image provided'
                }), 400
            
            image_file = request.files['image']
            property_id = request.form.get('property_id', 1)
            metadata = json.loads(request.form.get('metadata', '{}'))
            
            # Save image temporarily
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"property_analysis_{uuid.uuid4().hex}.jpg")
            image_file.save(temp_path)
            
            try:
                # Import and use property analyzer
                from ai_services.computer_vision.property_analyzer import get_property_analyzer
                analyzer = get_property_analyzer()
                
                # Analyze the property image
                analysis_result = analyzer.analyze_property_image(temp_path, int(property_id), metadata)
                
                # Convert result to JSON
                result_data = {
                    'success': True,
                    'analysis': {
                        'property_id': analysis_result.property_id,
                        'overall_condition': analysis_result.property_analysis.overall_condition.value,
                        'condition_score': analysis_result.property_analysis.condition_score,
                        'confidence_score': analysis_result.confidence_score,
                        'features_detected': analysis_result.property_analysis.features_detected,
                        'room_analysis': analysis_result.property_analysis.room_analysis,
                        'recommendations': analysis_result.recommendations,
                        'timestamp': analysis_result.analysis_timestamp.isoformat()
                    }
                }
                
                return jsonify(result_data)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Property analysis failed: {str(e)}'
            }), 500
    
    @app.route('/api/ai/assess-damage', methods=['POST'])
    def assess_property_damage():
        """Assess property damage from uploaded image"""
        try:
            if 'image' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No image provided'
                }), 400
            
            image_file = request.files['image']
            property_id = request.form.get('property_id', 1)
            metadata = json.loads(request.form.get('metadata', '{}'))
            
            # Save image temporarily
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"damage_assessment_{uuid.uuid4().hex}.jpg")
            image_file.save(temp_path)
            
            try:
                # Import and use damage detector
                from ai_services.computer_vision.damage_detector import get_damage_detector
                detector = get_damage_detector()
                
                # Assess damage
                damage_result = detector.detect_damage(temp_path, int(property_id), metadata)
                
                # Convert result to JSON
                result_data = {
                    'success': True,
                    'damage_assessment': {
                        'property_id': damage_result.property_id,
                        'overall_damage_score': damage_result.overall_damage_score,
                        'urgency_level': damage_result.urgency_level.value,
                        'damage_types': [d.value for d in damage_result.damage_types],
                        'affected_areas': damage_result.affected_areas,
                        'estimated_total_cost': damage_result.estimated_total_cost,
                        'repair_recommendations': damage_result.repair_recommendations,
                        'confidence_score': damage_result.confidence_score,
                        'timestamp': damage_result.assessment_timestamp.isoformat()
                    }
                }
                
                return jsonify(result_data)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Damage assessment failed: {str(e)}'
            }), 500
    
    @app.route('/api/ai/enhance-image', methods=['POST'])
    def enhance_property_image():
        """Enhance image quality for better analysis"""
        try:
            if 'image' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No image provided'
                }), 400
            
            image_file = request.files['image']
            enhancement_type = request.form.get('enhancement_type', 'auto')
            
            # Save image temporarily
            import tempfile
            temp_dir = tempfile.gettempdir()
            input_path = os.path.join(temp_dir, f"input_{uuid.uuid4().hex}.jpg")
            output_path = os.path.join(temp_dir, f"enhanced_{uuid.uuid4().hex}.jpg")
            image_file.save(input_path)
            
            try:
                # Import and use image processor
                from ai_services.computer_vision.image_processor import get_image_processor
                processor = get_image_processor()
                
                # Enhance the image
                enhanced_result = processor.enhance_image(input_path, output_path, enhancement_type)
                
                # Read enhanced image as base64
                import base64
                with open(output_path, 'rb') as f:
                    enhanced_image_data = base64.b64encode(f.read()).decode()
                
                result_data = {
                    'success': True,
                    'enhancement': {
                        'original_quality_score': enhanced_result.original_quality_score,
                        'enhanced_quality_score': enhanced_result.enhanced_quality_score,
                        'improvement_score': enhanced_result.enhancement_score,
                        'enhancements_applied': enhanced_result.enhancements_applied,
                        'enhanced_image': f"data:image/jpeg;base64,{enhanced_image_data}",
                        'processing_time_ms': enhanced_result.processing_time_ms,
                        'timestamp': enhanced_result.enhancement_timestamp.isoformat()
                    }
                }
                
                return jsonify(result_data)
                
            finally:
                # Clean up temporary files
                for path in [input_path, output_path]:
                    if os.path.exists(path):
                        os.unlink(path)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Image enhancement failed: {str(e)}'
            }), 500

    # Live Camera Analysis API Routes
    @app.route('/api/camera/available', methods=['GET'])
    def get_available_cameras():
        """Get list of available cameras"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer
            analyzer = get_live_camera_analyzer()
            cameras = analyzer.get_available_cameras()
            
            return jsonify({
                'success': True,
                'cameras': cameras,
                'total_found': len(cameras)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get available cameras: {str(e)}'
            }), 500

    @app.route('/api/camera/add', methods=['POST'])
    def add_camera():
        """Add a new camera to live analysis system"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer, CameraType, StreamQuality
            
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['camera_id', 'source', 'property_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            analyzer = get_live_camera_analyzer()
            
            # Create camera configuration
            camera_type = CameraType(data.get('camera_type', 'usb_camera'))
            quality = StreamQuality(data.get('quality', 'medium'))
            
            camera_config = analyzer.create_camera_config(
                camera_id=data['camera_id'],
                source=data['source'],
                camera_type=camera_type,
                quality=quality
            )
            
            # Add camera
            success = analyzer.add_camera(camera_config, int(data['property_id']))
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Camera {data["camera_id"]} added successfully',
                    'camera_config': {
                        'camera_id': camera_config.camera_id,
                        'resolution': camera_config.resolution,
                        'fps': camera_config.fps
                    }
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add camera'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to add camera: {str(e)}'
            }), 500

    @app.route('/api/camera/<camera_id>/start', methods=['POST'])
    def start_camera_analysis(camera_id):
        """Start live analysis for a camera"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer, AnalysisMode
            
            data = request.get_json() or {}
            analysis_mode = AnalysisMode(data.get('analysis_mode', 'interval'))
            
            analyzer = get_live_camera_analyzer()
            success = analyzer.start_live_analysis(camera_id, analysis_mode)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Live analysis started for camera {camera_id}',
                    'analysis_mode': analysis_mode.value
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to start live analysis'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to start camera analysis: {str(e)}'
            }), 500

    @app.route('/api/camera/<camera_id>/stop', methods=['POST'])
    def stop_camera_analysis(camera_id):
        """Stop live analysis for a camera"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer
            
            analyzer = get_live_camera_analyzer()
            success = analyzer.stop_camera_analysis(camera_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Live analysis stopped for camera {camera_id}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to stop live analysis'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to stop camera analysis: {str(e)}'
            }), 500

    @app.route('/api/camera/<camera_id>/capture', methods=['POST'])
    def capture_analysis_frame(camera_id):
        """Manually capture and analyze a frame"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer
            
            data = request.get_json() or {}
            property_id = int(data.get('property_id', 1))
            description = data.get('description', 'Manual capture')
            
            analyzer = get_live_camera_analyzer()
            analysis_result = analyzer.capture_analysis_frame(camera_id, property_id, description)
            
            if analysis_result:
                # Convert analysis result to JSON-serializable format
                result_data = {
                    'frame_id': analysis_result.frame_id,
                    'timestamp': analysis_result.timestamp.isoformat(),
                    'camera_id': analysis_result.camera_id,
                    'property_id': analysis_result.property_id,
                    'frame_size': analysis_result.frame_size,
                    'image_quality_score': analysis_result.image_quality_score,
                    'focus_score': analysis_result.focus_score,
                    'lighting_score': analysis_result.lighting_score,
                    'motion_detected': analysis_result.motion_detected,
                    'objects_count': len(analysis_result.objects_detected),
                    'analysis_time': analysis_result.analysis_time,
                    'confidence_score': analysis_result.confidence_score
                }
                
                # Add property analysis summary if available
                if analysis_result.property_analysis:
                    result_data['property_condition'] = analysis_result.property_analysis.overall_condition.value
                    result_data['features_detected'] = len(analysis_result.property_analysis.features_detected)
                
                # Add damage assessment summary if available
                if analysis_result.damage_assessment:
                    result_data['damage_score'] = analysis_result.damage_assessment.overall_damage_score
                    result_data['urgency_level'] = analysis_result.damage_assessment.urgency_level.value
                    result_data['estimated_repair_cost'] = analysis_result.damage_assessment.estimated_total_cost
                
                return jsonify({
                    'success': True,
                    'message': 'Frame captured and analyzed successfully',
                    'analysis': result_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to capture and analyze frame'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to capture frame: {str(e)}'
            }), 500

    @app.route('/api/camera/<camera_id>/status', methods=['GET'])
    def get_camera_status(camera_id):
        """Get current status and statistics for a camera"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer
            
            analyzer = get_live_camera_analyzer()
            stream_data = analyzer.get_live_stream_data(camera_id)
            
            if stream_data:
                # Remove the actual frame data for API response (too large)
                if 'current_frame' in stream_data:
                    stream_data['has_current_frame'] = stream_data['current_frame'] is not None
                    del stream_data['current_frame']
                
                # Simplify last analysis data
                if stream_data.get('last_analysis'):
                    last_analysis = stream_data['last_analysis']
                    stream_data['last_analysis_summary'] = {
                        'timestamp': last_analysis.timestamp.isoformat(),
                        'confidence_score': last_analysis.confidence_score,
                        'image_quality_score': last_analysis.image_quality_score,
                        'motion_detected': last_analysis.motion_detected,
                        'objects_count': len(last_analysis.objects_detected),
                        'analysis_time': last_analysis.analysis_time
                    }
                    del stream_data['last_analysis']
                
                return jsonify({
                    'success': True,
                    'stream_data': stream_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Camera not found'
                }), 404
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get camera status: {str(e)}'
            }), 500

    @app.route('/api/camera/<camera_id>/remove', methods=['DELETE'])
    def remove_camera(camera_id):
        """Remove a camera from the system"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer
            
            analyzer = get_live_camera_analyzer()
            success = analyzer.remove_camera(camera_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Camera {camera_id} removed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to remove camera'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to remove camera: {str(e)}'
            }), 500

    @app.route('/api/camera/analysis/batch', methods=['POST'])
    def batch_analyze_properties():
        """Analyze multiple property images from cameras"""
        try:
            from ai_services.computer_vision.live_camera_analyzer import get_live_camera_analyzer
            
            data = request.get_json()
            camera_ids = data.get('camera_ids', [])
            property_id = int(data.get('property_id', 1))
            
            if not camera_ids:
                return jsonify({
                    'success': False,
                    'error': 'No camera IDs provided'
                }), 400
            
            analyzer = get_live_camera_analyzer()
            results = []
            
            for camera_id in camera_ids:
                try:
                    analysis_result = analyzer.capture_analysis_frame(camera_id, property_id, 'Batch analysis')
                    if analysis_result:
                        results.append({
                            'camera_id': camera_id,
                            'success': True,
                            'analysis_summary': {
                                'confidence_score': analysis_result.confidence_score,
                                'image_quality_score': analysis_result.image_quality_score,
                                'objects_detected': len(analysis_result.objects_detected),
                                'motion_detected': analysis_result.motion_detected
                            }
                        })
                    else:
                        results.append({
                            'camera_id': camera_id,
                            'success': False,
                            'error': 'Analysis failed'
                        })
                except Exception as e:
                    results.append({
                        'camera_id': camera_id,
                        'success': False,
                        'error': str(e)
                    })
            
            successful_analyses = len([r for r in results if r['success']])
            
            return jsonify({
                'success': True,
                'message': f'Batch analysis completed: {successful_analyses}/{len(camera_ids)} successful',
                'results': results,
                'summary': {
                    'total_cameras': len(camera_ids),
                    'successful_analyses': successful_analyses,
                    'failed_analyses': len(camera_ids) - successful_analyses
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Batch analysis failed: {str(e)}'
            }), 500

    # ===== NLP DOCUMENT PROCESSING ENDPOINTS =====
    
    @app.route('/api/document/process', methods=['POST'])
    def process_document():
        """Process document text with NLP analysis"""
        try:
            from ai_services.nlp.document_processor import get_document_processor
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            document_text = data.get('text', '')
            document_id = data.get('document_id')
            
            if not document_text or len(document_text.strip()) < 10:
                return jsonify({
                    'success': False,
                    'error': 'Document text is too short or empty'
                }), 400
            
            processor = get_document_processor()
            analysis = processor.process_document(document_text, document_id)
            
            # Convert analysis to JSON-serializable format
            analysis_dict = {
                'document_id': analysis.document_id,
                'document_type': analysis.document_type.value,
                'confidence': analysis.confidence.value,
                'processing_time': analysis.processing_time,
                'text_length': analysis.text_length,
                'language': analysis.language,
                
                # Extracted information
                'entities': [
                    {
                        'text': e.text,
                        'type': e.entity_type,
                        'confidence': e.confidence,
                        'normalized_value': e.normalized_value
                    } for e in analysis.entities
                ],
                'dates': [
                    {
                        'text': d.text,
                        'parsed_date': d.parsed_date.isoformat(),
                        'date_type': d.date_type,
                        'confidence': d.confidence
                    } for d in analysis.dates
                ],
                'amounts': [
                    {
                        'text': a.text,
                        'amount': a.amount,
                        'currency': a.currency,
                        'amount_type': a.amount_type,
                        'confidence': a.confidence
                    } for a in analysis.amounts
                ],
                'clauses': [
                    {
                        'clause_type': c.clause_type,
                        'importance': c.importance,
                        'risk_level': c.risk_level,
                        'summary': c.summary
                    } for c in analysis.clauses
                ],
                
                # Analysis scores
                'sentiment_score': analysis.sentiment_score,
                'readability_score': analysis.readability_score,
                'complexity_score': analysis.complexity_score,
                'legal_risk_score': analysis.legal_risk_score,
                
                # Summary information
                'key_terms': analysis.key_terms,
                'summary': analysis.summary,
                'recommendations': analysis.recommendations,
                'warnings': analysis.warnings,
                'processed_at': analysis.processed_at.isoformat()
            }
            
            return jsonify({
                'success': True,
                'analysis': analysis_dict
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Document processing failed: {str(e)}'
            }), 500

    @app.route('/api/document/analyze-lease', methods=['POST'])
    def analyze_lease_document():
        """Specialized lease agreement analysis"""
        try:
            from ai_services.nlp.document_processor import get_document_processor
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            document_text = data.get('text', '')
            property_id = data.get('property_id')
            tenant_id = data.get('tenant_id')
            
            if not document_text:
                return jsonify({
                    'success': False,
                    'error': 'Document text is required'
                }), 400
            
            processor = get_document_processor()
            analysis = processor.process_document(document_text, f"lease_{property_id}_{tenant_id}")
            
            # Extract lease-specific information
            lease_info = {
                'tenant_name': analysis.key_terms.get('tenant', 'Not specified'),
                'landlord_name': analysis.key_terms.get('landlord', 'Not specified'),
                'property_address': analysis.key_terms.get('property_address', 'Not specified'),
                'monthly_rent': analysis.key_terms.get('monthly_rent', 0),
                'security_deposit': analysis.key_terms.get('security_deposit', 0),
                'lease_start_date': analysis.key_terms.get('lease_start_date', 'Not specified'),
                'lease_end_date': analysis.key_terms.get('lease_end_date', 'Not specified'),
                'lease_term_months': analysis.key_terms.get('lease_term_months', 0),
                
                'analysis_summary': {
                    'document_type': analysis.document_type.value,
                    'confidence': analysis.confidence.value,
                    'legal_risk_score': analysis.legal_risk_score,
                    'sentiment_score': analysis.sentiment_score,
                    'readability_score': analysis.readability_score,
                    'high_risk_clauses': len([c for c in analysis.clauses if c.risk_level == 'high']),
                    'total_clauses': len(analysis.clauses)
                },
                
                'recommendations': analysis.recommendations,
                'warnings': analysis.warnings,
                'summary': analysis.summary
            }
            
            return jsonify({
                'success': True,
                'lease_analysis': lease_info
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Lease analysis failed: {str(e)}'
            }), 500

    @app.route('/api/document/extract-entities', methods=['POST'])
    def extract_document_entities():
        """Extract named entities from document text"""
        try:
            from ai_services.nlp.document_processor import get_document_processor
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            document_text = data.get('text', '')
            
            if not document_text:
                return jsonify({
                    'success': False,
                    'error': 'Document text is required'
                }), 400
            
            processor = get_document_processor()
            
            # Quick entity extraction without full document processing
            if processor.spacy_available:
                entities = processor._extract_entities_spacy(document_text)
            else:
                entities = processor._extract_entities_rules(document_text)
            
            dates = processor._extract_dates(document_text)
            amounts = processor._extract_amounts(document_text)
            
            entities_data = [
                {
                    'text': e.text,
                    'type': e.entity_type,
                    'confidence': e.confidence,
                    'normalized_value': e.normalized_value,
                    'context': e.context
                } for e in entities
            ]
            
            dates_data = [
                {
                    'text': d.text,
                    'parsed_date': d.parsed_date.isoformat(),
                    'date_type': d.date_type,
                    'confidence': d.confidence
                } for d in dates
            ]
            
            amounts_data = [
                {
                    'text': a.text,
                    'amount': a.amount,
                    'currency': a.currency,
                    'amount_type': a.amount_type,
                    'confidence': a.confidence
                } for a in amounts
            ]
            
            return jsonify({
                'success': True,
                'extraction_results': {
                    'entities': entities_data,
                    'dates': dates_data,
                    'amounts': amounts_data,
                    'summary': {
                        'total_entities': len(entities_data),
                        'total_dates': len(dates_data),
                        'total_amounts': len(amounts_data),
                        'total_amount_value': sum(a['amount'] for a in amounts_data)
                    }
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Entity extraction failed: {str(e)}'
            }), 500

    @app.route('/api/document/assess-risk', methods=['POST'])
    def assess_document_risk():
        """Assess legal and compliance risks in document"""
        try:
            from ai_services.nlp.document_processor import get_document_processor
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            document_text = data.get('text', '')
            document_type = data.get('document_type', 'unknown')
            
            if not document_text:
                return jsonify({
                    'success': False,
                    'error': 'Document text is required'
                }), 400
            
            processor = get_document_processor()
            
            # Identify document type if not provided
            from ai_services.nlp.document_processor import DocumentType
            if document_type == 'unknown':
                doc_type, _ = processor._identify_document_type(document_text)
            else:
                doc_type = DocumentType(document_type)
            
            # Extract clauses for risk assessment
            clauses = processor._extract_clauses(document_text, doc_type)
            legal_risk_score = processor._assess_legal_risk(clauses, document_text)
            
            # Analyze sentiment and complexity
            sentiment_score = processor._analyze_sentiment(document_text)
            complexity_score = processor._calculate_complexity(document_text)
            
            risk_assessment = {
                'document_type': doc_type.value,
                'legal_risk_score': legal_risk_score,
                'sentiment_score': sentiment_score,
                'complexity_score': complexity_score,
                
                'risk_breakdown': {
                    'high_risk_clauses': len([c for c in clauses if c.risk_level == 'high']),
                    'medium_risk_clauses': len([c for c in clauses if c.risk_level == 'medium']),
                    'critical_clauses': len([c for c in clauses if c.importance == 'critical']),
                    'total_clauses': len(clauses)
                },
                
                'risk_level': (
                    'HIGH' if legal_risk_score > 70 else
                    'MEDIUM' if legal_risk_score > 40 else
                    'LOW'
                ),
                
                'clauses': [
                    {
                        'type': c.clause_type,
                        'importance': c.importance,
                        'risk_level': c.risk_level,
                        'summary': c.summary
                    } for c in clauses if c.risk_level in ['high', 'critical'] or c.importance == 'critical'
                ],
                
                'recommendations': processor._generate_recommendations(doc_type, clauses, legal_risk_score),
                'warnings': processor._generate_warnings(clauses, legal_risk_score, [])
            }
            
            return jsonify({
                'success': True,
                'risk_assessment': risk_assessment
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Risk assessment failed: {str(e)}'
            }), 500

    @app.route('/api/document/batch-process', methods=['POST'])
    def batch_process_documents():
        """Process multiple documents in batch"""
        try:
            from ai_services.nlp.document_processor import get_document_processor
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            documents = data.get('documents', [])
            
            if not documents:
                return jsonify({
                    'success': False,
                    'error': 'No documents provided'
                }), 400
            
            if len(documents) > 10:  # Limit batch size
                return jsonify({
                    'success': False,
                    'error': 'Maximum 10 documents per batch'
                }), 400
            
            processor = get_document_processor()
            results = []
            
            for i, doc_data in enumerate(documents):
                try:
                    text = doc_data.get('text', '')
                    doc_id = doc_data.get('document_id', f'batch_doc_{i}')
                    
                    if len(text.strip()) < 10:
                        results.append({
                            'document_id': doc_id,
                            'success': False,
                            'error': 'Document text too short'
                        })
                        continue
                    
                    analysis = processor.process_document(text, doc_id)
                    
                    # Create summary result for batch processing
                    results.append({
                        'document_id': doc_id,
                        'success': True,
                        'summary': {
                            'document_type': analysis.document_type.value,
                            'confidence': analysis.confidence.value,
                            'processing_time': analysis.processing_time,
                            'entities_found': len(analysis.entities),
                            'dates_found': len(analysis.dates),
                            'amounts_found': len(analysis.amounts),
                            'legal_risk_score': analysis.legal_risk_score,
                            'high_risk_clauses': len([c for c in analysis.clauses if c.risk_level == 'high']),
                            'key_terms': analysis.key_terms,
                            'warnings_count': len(analysis.warnings)
                        }
                    })
                    
                except Exception as e:
                    results.append({
                        'document_id': doc_data.get('document_id', f'batch_doc_{i}'),
                        'success': False,
                        'error': str(e)
                    })
            
            successful_analyses = len([r for r in results if r['success']])
            
            return jsonify({
                'success': True,
                'message': f'Batch processing completed: {successful_analyses}/{len(documents)} successful',
                'results': results,
                'summary': {
                    'total_documents': len(documents),
                    'successful_analyses': successful_analyses,
                    'failed_analyses': len(documents) - successful_analyses,
                    'average_risk_score': sum(
                        r['summary']['legal_risk_score'] 
                        for r in results 
                        if r['success']
                    ) / max(successful_analyses, 1)
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Batch processing failed: {str(e)}'
            }), 500

    # ===== PREDICTIVE MAINTENANCE AI ENDPOINTS =====
    
    @app.route('/api/maintenance/predict', methods=['POST'])
    def predict_maintenance():
        """Predict maintenance needs for a property"""
        try:
            from ai_services.predictive_analytics.maintenance_predictor import get_predictive_maintenance_ai
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            property_id = data.get('property_id')
            prediction_days = data.get('prediction_days', 90)
            
            if not property_id:
                return jsonify({
                    'success': False,
                    'error': 'Property ID is required'
                }), 400
            
            predictor = get_predictive_maintenance_ai()
            predictions = predictor.predict_maintenance_needs(int(property_id), prediction_days)
            
            # Convert predictions to JSON-serializable format
            predictions_data = []
            for prediction in predictions:
                predictions_data.append({
                    'property_id': prediction.property_id,
                    'equipment_id': prediction.equipment_id,
                    'maintenance_type': prediction.maintenance_type.value,
                    'predicted_date': prediction.predicted_date.isoformat(),
                    'confidence': prediction.confidence.value,
                    'confidence_score': prediction.confidence_score,
                    'risk_factors': prediction.risk_factors,
                    'estimated_cost_range': prediction.estimated_cost,
                    'estimated_duration_hours': prediction.estimated_duration,
                    'priority': prediction.recommended_priority.value,
                    'reason': prediction.reason,
                    'preventive_actions': prediction.preventive_actions,
                    'warning_signs': prediction.warning_signs,
                    'cost_impact_if_delayed': prediction.cost_impact_if_delayed,
                    'optimal_window_start': prediction.optimal_scheduling_window[0].isoformat(),
                    'optimal_window_end': prediction.optimal_scheduling_window[1].isoformat(),
                    'model_version': prediction.model_version,
                    'prediction_timestamp': prediction.prediction_timestamp.isoformat()
                })
            
            return jsonify({
                'success': True,
                'predictions': predictions_data,
                'summary': {
                    'total_predictions': len(predictions_data),
                    'critical_items': len([p for p in predictions_data if p['priority'] == 'critical']),
                    'high_priority_items': len([p for p in predictions_data if p['priority'] == 'high']),
                    'total_estimated_cost': sum(
                        (p['estimated_cost_range'][0] + p['estimated_cost_range'][1]) / 2 
                        for p in predictions_data
                    ),
                    'next_maintenance_date': min(p['predicted_date'] for p in predictions_data) if predictions_data else None
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Maintenance prediction failed: {str(e)}'
            }), 500

    @app.route('/api/maintenance/optimize-costs', methods=['POST'])
    def optimize_maintenance_costs():
        """Optimize maintenance costs and scheduling"""
        try:
            from ai_services.predictive_analytics.maintenance_predictor import get_predictive_maintenance_ai
            from ai_services.predictive_analytics.cost_optimizer import get_cost_optimizer, OptimizationStrategy
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            property_id = data.get('property_id')
            strategy = data.get('strategy', 'cost_minimization')
            prediction_days = data.get('prediction_days', 90)
            
            if not property_id:
                return jsonify({
                    'success': False,
                    'error': 'Property ID is required'
                }), 400
            
            # Get predictions first
            predictor = get_predictive_maintenance_ai()
            predictions = predictor.predict_maintenance_needs(int(property_id), prediction_days)
            
            if not predictions:
                return jsonify({
                    'success': True,
                    'message': 'No maintenance predictions found for optimization',
                    'optimization_result': None
                })
            
            # Optimize costs
            optimizer = get_cost_optimizer()
            optimization_strategy = OptimizationStrategy(strategy)
            
            result = optimizer.optimize_maintenance_costs(
                predictions, int(property_id), optimization_strategy
            )
            
            # Convert result to JSON-serializable format
            optimization_data = {
                'property_id': result.property_id,
                'optimization_strategy': result.optimization_strategy.value,
                'original_total_cost': result.original_total_cost,
                'optimized_total_cost': result.optimized_total_cost,
                'cost_savings': result.cost_savings,
                'savings_percentage': result.savings_percentage,
                'optimized_schedule': result.optimized_schedule,
                'contractor_assignments': result.contractor_assignments,
                'tenant_disruption_hours': result.tenant_disruption_hours,
                'total_project_duration_days': result.total_project_duration_days,
                'risk_mitigation_actions': result.risk_mitigation_actions,
                'contractor_utilization': result.contractor_utilization,
                'equipment_sharing_opportunities': result.equipment_sharing_opportunities,
                'bulk_purchase_savings': result.bulk_purchase_savings,
                'recommendations': result.recommendations,
                'alternative_strategies': result.alternative_strategies,
                'optimization_timestamp': result.optimization_timestamp.isoformat()
            }
            
            return jsonify({
                'success': True,
                'optimization_result': optimization_data,
                'summary': {
                    'total_savings': result.cost_savings,
                    'savings_percentage': result.savings_percentage,
                    'project_duration_days': result.total_project_duration_days,
                    'scheduled_items': len(result.optimized_schedule),
                    'contractors_involved': len(result.contractor_assignments)
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Cost optimization failed: {str(e)}'
            }), 500

    @app.route('/api/maintenance/insights/<int:property_id>', methods=['GET'])
    def get_maintenance_insights(property_id):
        """Get comprehensive maintenance insights for a property"""
        try:
            from ai_services.predictive_analytics.maintenance_predictor import get_predictive_maintenance_ai
            
            predictor = get_predictive_maintenance_ai()
            insights = predictor.get_maintenance_insights(property_id)
            
            return jsonify({
                'success': True,
                'insights': insights
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get maintenance insights: {str(e)}'
            }), 500

    @app.route('/api/maintenance/cost-analysis', methods=['POST'])
    def get_cost_analysis():
        """Get detailed cost analysis report"""
        try:
            from ai_services.predictive_analytics.maintenance_predictor import get_predictive_maintenance_ai
            from ai_services.predictive_analytics.cost_optimizer import get_cost_optimizer
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            property_id = data.get('property_id')
            prediction_days = data.get('prediction_days', 90)
            
            if not property_id:
                return jsonify({
                    'success': False,
                    'error': 'Property ID is required'
                }), 400
            
            # Get predictions
            predictor = get_predictive_maintenance_ai()
            predictions = predictor.predict_maintenance_needs(int(property_id), prediction_days)
            
            # Generate cost analysis report
            optimizer = get_cost_optimizer()
            report = optimizer.get_cost_analysis_report(int(property_id), predictions)
            
            return jsonify({
                'success': True,
                'cost_analysis_report': report
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Cost analysis failed: {str(e)}'
            }), 500

    @app.route('/api/maintenance/equipment', methods=['POST'])
    def add_equipment_data():
        """Add equipment data for predictive analysis"""
        try:
            from ai_services.predictive_analytics.maintenance_predictor import (
                get_predictive_maintenance_ai, EquipmentData, MaintenanceType
            )
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            required_fields = ['equipment_id', 'property_id', 'equipment_type', 'brand', 'installation_date']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # Parse installation date
            from datetime import datetime
            installation_date = datetime.fromisoformat(data['installation_date'].replace('Z', '+00:00'))
            
            # Parse warranty expiry if provided
            warranty_expiry = None
            if data.get('warranty_expiry'):
                warranty_expiry = datetime.fromisoformat(data['warranty_expiry'].replace('Z', '+00:00'))
            
            # Create equipment data object
            equipment = EquipmentData(
                equipment_id=data['equipment_id'],
                property_id=int(data['property_id']),
                equipment_type=MaintenanceType(data['equipment_type']),
                brand=data['brand'],
                model=data.get('model', ''),
                installation_date=installation_date,
                warranty_expiry=warranty_expiry,
                last_service_date=None,  # Can be updated later
                service_intervals=[],    # Can be updated later
                operating_hours=data.get('operating_hours', 0),
                energy_consumption=data.get('energy_consumption', 0.0),
                performance_metrics=data.get('performance_metrics', {}),
                sensor_readings=data.get('sensor_readings', {}),
                maintenance_history=data.get('maintenance_history', []),
                replacement_cost=data.get('replacement_cost', 0.0)
            )
            
            # Add to predictor
            predictor = get_predictive_maintenance_ai()
            success = predictor.add_equipment_data(equipment)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Equipment {equipment.equipment_id} added successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add equipment data'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to add equipment data: {str(e)}'
            }), 500

    @app.route('/api/maintenance/record', methods=['POST'])
    def add_maintenance_record():
        """Add historical maintenance record for model training"""
        try:
            from ai_services.predictive_analytics.maintenance_predictor import (
                get_predictive_maintenance_ai, MaintenanceRecord, MaintenanceType, MaintenancePriority
            )
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            required_fields = ['record_id', 'property_id', 'maintenance_type', 'completion_date', 'cost']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # Parse completion date
            from datetime import datetime
            completion_date = datetime.fromisoformat(data['completion_date'].replace('Z', '+00:00'))
            
            # Create maintenance record
            record = MaintenanceRecord(
                record_id=data['record_id'],
                property_id=int(data['property_id']),
                maintenance_type=MaintenanceType(data['maintenance_type']),
                description=data.get('description', ''),
                cost=float(data['cost']),
                completion_date=completion_date,
                duration_hours=data.get('duration_hours', 4),
                priority=MaintenancePriority(data.get('priority', 'medium')),
                contractor=data.get('contractor', ''),
                parts_replaced=data.get('parts_replaced', []),
                issue_severity=data.get('issue_severity', 5),
                customer_satisfaction=data.get('customer_satisfaction', 3),
                weather_conditions=data.get('weather_conditions', ''),
                equipment_age_years=data.get('equipment_age_years', 0.0),
                last_maintenance_days=data.get('last_maintenance_days', 365),
                property_age_years=data.get('property_age_years', 0),
                tenant_reported=data.get('tenant_reported', False)
            )
            
            # Add to predictor
            predictor = get_predictive_maintenance_ai()
            success = predictor.add_maintenance_record(record)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Maintenance record {record.record_id} added successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add maintenance record'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to add maintenance record: {str(e)}'
            }), 500

    @app.route('/api/maintenance/batch-optimize', methods=['POST'])
    def batch_optimize_properties():
        """Optimize maintenance schedules for multiple properties"""
        try:
            from ai_services.predictive_analytics.maintenance_predictor import get_predictive_maintenance_ai
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            property_ids = data.get('property_ids', [])
            optimization_period_days = data.get('optimization_period_days', 365)
            
            if not property_ids:
                return jsonify({
                    'success': False,
                    'error': 'Property IDs are required'
                }), 400
            
            # Convert to integers
            property_ids = [int(pid) for pid in property_ids]
            
            # Optimize schedules
            predictor = get_predictive_maintenance_ai()
            recommendations = predictor.optimize_maintenance_schedule(
                property_ids, optimization_period_days
            )
            
            # Convert recommendations to JSON format
            recommendations_data = []
            for rec in recommendations:
                recommendations_data.append({
                    'property_id': rec.property_id,
                    'optimization_period': [
                        rec.optimization_period[0].isoformat(),
                        rec.optimization_period[1].isoformat()
                    ],
                    'total_predicted_cost': rec.total_predicted_cost,
                    'recommendations': rec.recommendations,
                    'cost_savings_potential': rec.cost_savings_potential,
                    'efficiency_improvements': rec.efficiency_improvements,
                    'resource_requirements': rec.resource_requirements
                })
            
            total_savings = sum(r['cost_savings_potential'] for r in recommendations_data)
            total_cost = sum(r['total_predicted_cost'] for r in recommendations_data)
            
            return jsonify({
                'success': True,
                'batch_optimization': {
                    'property_count': len(property_ids),
                    'total_predicted_cost': total_cost,
                    'total_savings_potential': total_savings,
                    'average_savings_percentage': (total_savings / total_cost * 100) if total_cost > 0 else 0,
                    'recommendations': recommendations_data
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Batch optimization failed: {str(e)}'
            }), 500

    return app

# Create the app instance for gunicorn
app = create_app()

# For direct execution
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)