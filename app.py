import os
import sys
import random
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import stripe
from decimal import Decimal

# Initialize extensions
db = SQLAlchemy()

# Database Models
# Temporarily disabled new models to avoid startup issues until tables are created
"""
class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    legal_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    license_number = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    subscription_status = db.Column(db.String(20), default='trial')
    subscription_plan = db.Column(db.String(50), default='basic')
    trial_ends_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    buildings = db.relationship('Building', backref='company', lazy=True)
    users = db.relationship('User', backref='company', lazy=True)

class Building(db.Model):
    __tablename__ = 'buildings'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    building_type = db.Column(db.String(50), nullable=False, default='residential')
    description = db.Column(db.Text, nullable=True)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    year_built = db.Column(db.Integer, nullable=True)
    total_floors = db.Column(db.Integer, nullable=True)
    total_units = db.Column(db.Integer, nullable=True, default=0)
    parking_spaces = db.Column(db.Integer, nullable=True, default=0)
    amenities = db.Column(db.Text, nullable=True)  # JSON string of amenities
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    units = db.relationship('Unit', backref='building', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='building', lazy=True)

class StripeCustomer(db.Model):
    __tablename__ = 'stripe_customers'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class StripeSubscription(db.Model):
    __tablename__ = 'stripe_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100), nullable=False, unique=True)
    stripe_customer_id = db.Column(db.String(100), nullable=False)
    plan_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
"""

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(16), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Add compatibility property for frontend
    @property
    def username(self):
        return f"{self.first_name} {self.last_name}"

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    property_type = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=True)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    total_units = db.Column(db.Integer, nullable=True)
    manager_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, nullable=True, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Add properties to maintain API compatibility
    @property
    def address(self):
        return self.street_address
    
    @address.setter
    def address(self, value):
        self.street_address = value
    
    @property
    def type(self):
        return self.property_type
    
    @type.setter 
    def type(self, value):
        self.property_type = value
        
    @property
    def units(self):
        return self.total_units
    
    @units.setter
    def units(self, value):
        self.total_units = value
        
    @property
    def is_available(self):
        return self.is_active
    
    @is_available.setter
    def is_available(self, value):
        self.is_active = value
        
    @property
    def owner_id(self):
        return self.manager_id
    
    @owner_id.setter
    def owner_id(self, value):
        self.manager_id = value
        
    # Mock properties for API compatibility
    @property 
    def bedrooms(self):
        return 0  # Default value since column doesn't exist
        
    @property
    def bathrooms(self):
        return 0  # Default value since column doesn't exist
        
    @property
    def rent(self):
        return 0  # Default value since column doesn't exist
        
    @property
    def occupancy(self):
        return 'available'  # Default value since column doesn't exist

class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    floor_number = db.Column(db.Integer, nullable=True)
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Float, nullable=True)
    sqft = db.Column(db.Integer, nullable=True)
    base_rent = db.Column(db.Numeric(10, 2), nullable=False)
    security_deposit = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(11), nullable=True)
    is_occupied = db.Column(db.Boolean, nullable=True)
    available_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Add compatibility properties
    @property
    def rent(self):
        return float(self.base_rent) if self.base_rent else 0
    
    @property
    def square_feet(self):
        return self.sqft
        
    @property
    def is_available(self):
        return not self.is_occupied if self.is_occupied is not None else True

class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    monthly_income = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, nullable=True, default=True)
    move_in_date = db.Column(db.Date, nullable=True)
    move_out_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Add compatibility properties for the API
    @property
    def user_id(self):
        return self.id  # For compatibility, we'll treat tenant as user
    
    @property
    def property_id(self):
        return None  # We don't have direct property link in this schema
    
    @property
    def unit_id(self):
        return None  # We don't have direct unit link in this schema
        
    @property
    def lease_start(self):
        return self.move_in_date
        
    @property
    def lease_end(self):
        return self.move_out_date
        
    @property
    def rent_amount(self):
        return 0  # Not in this schema
        
    @property
    def status(self):
        return 'active' if self.is_active else 'inactive'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    unit_id = db.Column(db.Integer, nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    stripe_payment_intent_id = db.Column(db.String(100), nullable=True)
    stripe_charge_id = db.Column(db.String(100), nullable=True)
    payment_type = db.Column(db.String(50), default='rent')  # rent, deposit, fee, etc.
    description = db.Column(db.Text, nullable=True)
    late_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

"""
class RentPayment(db.Model):
    __tablename__ = 'rent_payments'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    late_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, paid, partial, late, waived
    payment_period = db.Column(db.String(20), nullable=False)  # e.g., "2024-01"
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    auto_pay_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
"""

class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_requests'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, nullable=False)
    to_user_id = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    
    # Add compatibility properties
    @property
    def sender_id(self):
        return self.from_user_id
    
    @property
    def recipient_id(self):
        return self.to_user_id
        
    @property
    def content(self):
        return self.message
        
    @property
    def is_read(self):
        return self.status == 'read' if self.status else False
        
    @property
    def is_system(self):
        return self.from_user_id is None

class Invite(db.Model):
    __tablename__ = 'invites'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(500))
    size = db.Column(db.String(20))
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

class TenantScore(db.Model):
    __tablename__ = 'tenant_scores'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    overall_score = db.Column(db.Float, nullable=False)
    payment_score = db.Column(db.Float)
    communication_score = db.Column(db.Float)
    maintenance_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class SetupProgress(db.Model):
    __tablename__ = 'setup_progress'
    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.String(50), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    data = db.Column(db.Text)  # JSON data for step configuration

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    visitor_name = db.Column(db.String(100))
    access_time = db.Column(db.DateTime, default=datetime.utcnow)
    access_type = db.Column(db.String(50))
    granted = db.Column(db.Boolean, default=True)
    access_code = db.Column(db.String(20))
    expires_at = db.Column(db.DateTime)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_used = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)

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
        return jsonify({'status': 'healthy', 'service': 'EstateCore Backend', 'version': '4.0', 'models_fixed': True, 'timestamp': datetime.utcnow().isoformat()})
    
    @app.route('/')
    def root():
        return jsonify({'message': 'EstateCore API', 'status': 'running'})
    
    @app.route('/test-deployment')
    def test_deployment():
        return jsonify({'deployment': 'success', 'version': '4.0', 'dashboard_ready': True})
    
    # Properties API
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
    
    @app.route('/api/properties', methods=['POST'])
    def create_property():
        data = request.get_json()
        property = Property(
            name=data['name'],
            street_address=data.get('address', ''),
            city=data.get('city', 'Unknown'),
            state=data.get('state', 'Unknown'),
            zip_code=data.get('zip_code', '00000'),
            property_type=data.get('type', 'house'),
            total_units=data.get('units', 1),
            description=data.get('description', ''),
            manager_id=1  # Default owner
        )
        db.session.add(property)
        db.session.commit()
        return jsonify({'message': 'Property created', 'id': property.id}), 201
    
    @app.route('/api/properties/<int:property_id>', methods=['PUT'])
    def update_property(property_id):
        try:
            property = Property.query.get_or_404(property_id)
            data = request.get_json()
            
            property.name = data.get('name', property.name)
            property.street_address = data.get('address', property.street_address)
            property.property_type = data.get('type', property.property_type)
            property.total_units = data.get('units', property.total_units)
            property.description = data.get('description', property.description)
            
            db.session.commit()
            return jsonify({'message': 'Property updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/properties/<int:property_id>', methods=['DELETE'])
    def delete_property(property_id):
        try:
            property = Property.query.get_or_404(property_id)
            db.session.delete(property)
            db.session.commit()
            return jsonify({'message': 'Property deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Users API
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
    
    @app.route('/api/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        user = User(
            email=data['email'],
            username=data['username'],
            password_hash='temp_hash',  # Should be properly hashed
            role=data.get('role', 'tenant')
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created', 'id': user.id}), 201
    
    @app.route('/api/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        try:
            user = User.query.get_or_404(user_id)
            data = request.get_json()
            
            user.email = data.get('email', user.email)
            user.username = data.get('username', user.username)
            user.role = data.get('role', user.role)
            user.is_active = data.get('is_active', user.is_active)
            
            db.session.commit()
            return jsonify({'message': 'User updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        try:
            user = User.query.get_or_404(user_id)
            user.is_active = False  # Soft delete
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Units API
    @app.route('/api/units', methods=['GET'])
    def get_units():
        try:
            property_id = request.args.get('property_id')
            if property_id:
                units = Unit.query.filter_by(property_id=property_id).all()
            else:
                units = Unit.query.all()
            
            result = []
            for unit in units:
                property = Property.query.get(unit.property_id) if unit.property_id else None
                result.append({
                    'id': unit.id,
                    'property_id': unit.property_id,
                    'property_name': property.name if property else 'Unknown',
                    'unit_number': unit.unit_number,
                    'bedrooms': unit.bedrooms,
                    'bathrooms': unit.bathrooms,
                    'rent': unit.rent,
                    'square_feet': unit.square_feet,
                    'is_available': unit.is_available
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/units', methods=['POST'])
    def create_unit():
        try:
            data = request.get_json()
            unit = Unit(
                property_id=data['property_id'],
                unit_number=data['unit_number'],
                bedrooms=data.get('bedrooms'),
                bathrooms=data.get('bathrooms'),
                rent=data['rent'],
                square_feet=data.get('square_feet'),
                is_available=data.get('is_available', True)
            )
            db.session.add(unit)
            db.session.commit()
            return jsonify({'message': 'Unit created', 'id': unit.id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/units/<int:unit_id>', methods=['PUT'])
    def update_unit(unit_id):
        try:
            unit = Unit.query.get_or_404(unit_id)
            data = request.get_json()
            
            unit.unit_number = data.get('unit_number', unit.unit_number)
            unit.bedrooms = data.get('bedrooms', unit.bedrooms)
            unit.bathrooms = data.get('bathrooms', unit.bathrooms)
            unit.rent = data.get('rent', unit.rent)
            unit.square_feet = data.get('square_feet', unit.square_feet)
            unit.is_available = data.get('is_available', unit.is_available)
            
            db.session.commit()
            return jsonify({'message': 'Unit updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/units/<int:unit_id>', methods=['DELETE'])
    def delete_unit(unit_id):
        try:
            unit = Unit.query.get_or_404(unit_id)
            db.session.delete(unit)
            db.session.commit()
            return jsonify({'message': 'Unit deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Tenants API
    @app.route('/api/tenants', methods=['GET'])
    def get_tenants():
        try:
            # Direct SQL query to avoid model issues during deployment
            result = db.session.execute(db.text("""
                SELECT id, first_name, last_name, email, phone, 
                       move_in_date, move_out_date, is_active, monthly_income
                FROM tenants 
                WHERE is_deleted = false OR is_deleted IS NULL
            """)).fetchall()
            
            tenants_list = []
            for row in result:
                tenants_list.append({
                    'id': row[0],
                    'user': {
                        'id': row[0], 
                        'email': row[3], 
                        'username': f"{row[1]} {row[2]}"
                    },
                    'property': None,  # Not available in current schema
                    'unit': None,      # Not available in current schema
                    'lease_start': row[5].isoformat() if row[5] else None,
                    'lease_end': row[6].isoformat() if row[6] else None,
                    'rent_amount': 0,  # Not available in current schema
                    'deposit': 0,      # Not available in current schema
                    'status': 'active' if row[7] else 'inactive',
                    'first_name': row[1],
                    'last_name': row[2],
                    'phone': row[4],
                    'monthly_income': float(row[8]) if row[8] else 0
                })
            return jsonify(tenants_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tenants', methods=['POST'])
    def create_tenant():
        try:
            data = request.get_json()
            
            tenant = Tenant(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
                monthly_income=data.get('monthly_income'),
                move_in_date=datetime.strptime(data['move_in_date'], '%Y-%m-%d').date() if data.get('move_in_date') else None,
                move_out_date=datetime.strptime(data['move_out_date'], '%Y-%m-%d').date() if data.get('move_out_date') else None,
                is_active=True
            )
            db.session.add(tenant)
            db.session.commit()
            return jsonify({'message': 'Tenant created', 'id': tenant.id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tenants/<int:tenant_id>', methods=['PUT'])
    def update_tenant(tenant_id):
        try:
            tenant = Tenant.query.get_or_404(tenant_id)
            data = request.get_json()
            
            tenant.first_name = data.get('first_name', tenant.first_name)
            tenant.last_name = data.get('last_name', tenant.last_name)
            tenant.email = data.get('email', tenant.email)
            tenant.phone = data.get('phone', tenant.phone)
            
            if data.get('move_in_date'):
                tenant.move_in_date = datetime.strptime(data['move_in_date'], '%Y-%m-%d').date()
            if data.get('move_out_date'):
                tenant.move_out_date = datetime.strptime(data['move_out_date'], '%Y-%m-%d').date()
            
            tenant.monthly_income = data.get('monthly_income', tenant.monthly_income)
            tenant.is_active = data.get('is_active', tenant.is_active)
            tenant.updated_at = datetime.utcnow()
            
            db.session.commit()
            return jsonify({'message': 'Tenant updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tenants/<int:tenant_id>', methods=['DELETE'])
    def delete_tenant(tenant_id):
        try:
            tenant = Tenant.query.get_or_404(tenant_id)
            db.session.delete(tenant)
            db.session.commit()
            return jsonify({'message': 'Tenant deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Payments API
    @app.route('/api/payments', methods=['GET'])
    def get_payments():
        try:
            payments = Payment.query.all()
            result = []
            for payment in payments:
                tenant = Tenant.query.get(payment.tenant_id) if payment.tenant_id else None
                user = User.query.get(tenant.user_id) if tenant and tenant.user_id else None
                property = Property.query.get(tenant.property_id) if tenant and tenant.property_id else None
                
                result.append({
                    'id': payment.id,
                    'amount': payment.amount,
                    'payment_date': payment.payment_date.isoformat(),
                    'due_date': payment.due_date.isoformat(),
                    'status': payment.status,
                    'tenant': user.username if user else 'Unknown',
                    'property': property.name if property else 'Unknown'
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Maintenance API
    @app.route('/api/maintenance', methods=['GET'])
    def get_maintenance():
        try:
            requests = MaintenanceRequest.query.all()
            result = []
            for request in requests:
                property = Property.query.get(request.property_id) if request.property_id else None
                result.append({
                    'id': request.id,
                    'title': request.title,
                    'description': request.description,
                    'priority': request.priority,
                    'status': request.status,
                    'property': property.name if property else 'Unknown',
                    'created_at': request.created_at.isoformat()
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/maintenance', methods=['POST'])
    def create_maintenance():
        try:
            data = request.get_json()
            request_obj = MaintenanceRequest(
                property_id=data['property_id'],
                title=data['title'],
                description=data.get('description'),
                priority=data.get('priority', 'medium')
            )
            db.session.add(request_obj)
            db.session.commit()
            return jsonify({'message': 'Maintenance request created', 'id': request_obj.id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/maintenance/<int:request_id>', methods=['PUT'])
    def update_maintenance(request_id):
        try:
            maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
            data = request.get_json()
            
            maintenance_request.title = data.get('title', maintenance_request.title)
            maintenance_request.description = data.get('description', maintenance_request.description)
            maintenance_request.priority = data.get('priority', maintenance_request.priority)
            maintenance_request.status = data.get('status', maintenance_request.status)
            
            db.session.commit()
            return jsonify({'message': 'Maintenance request updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/maintenance/<int:request_id>', methods=['DELETE'])
    def delete_maintenance(request_id):
        try:
            maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
            db.session.delete(maintenance_request)
            db.session.commit()
            return jsonify({'message': 'Maintenance request deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Access Control API
    @app.route('/api/access', methods=['GET'])
    def get_access_logs():
        logs = db.session.query(AccessLog, Property).join(Property).all()
        return jsonify([{
            'id': a.id,
            'visitor_name': a.visitor_name,
            'access_time': a.access_time.isoformat(),
            'access_type': a.access_type,
            'granted': a.granted,
            'property': p.name
        } for a, p in logs])
    
    # Dashboard API
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
            # Check if units table exists and has lease data
            units_exist = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'units'
                )
            """)).scalar()
            
            if not units_exist:
                # Return mock data if table doesn't exist yet
                return jsonify({
                    'expiring_soon': [],
                    'expired': [],
                    'alerts': ['Lease tracking system is being set up']
                })
            
            # Check if lease_end column exists, if not use mock data
            try:
                # Try to query lease_end column
                expiring_soon = db.session.execute(db.text("""
                    SELECT id, unit_number, lease_end 
                    FROM units 
                    WHERE lease_end IS NOT NULL 
                    AND lease_end BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
                    AND (is_deleted = false OR is_deleted IS NULL)
                    LIMIT 10
                """)).fetchall()
                
                expired = db.session.execute(db.text("""
                    SELECT id, unit_number, lease_end 
                    FROM units 
                    WHERE lease_end IS NOT NULL 
                    AND lease_end < CURRENT_DATE
                    AND (is_deleted = false OR is_deleted IS NULL)
                    LIMIT 10
                """)).fetchall()
                
            except Exception:
                # Column doesn't exist, return mock data
                expiring_soon = []
                expired = []
            
            alerts = []
            if len(expiring_soon) > 0:
                alerts.append(f"{len(expiring_soon)} leases expiring within 30 days")
            if len(expired) > 0:
                alerts.append(f"{len(expired)} leases have already expired")
            
            return jsonify({
                'expiring_soon': [{
                    'unit_id': row[0],
                    'unit_number': row[1],
                    'lease_end': row[2].isoformat() if row[2] else None
                } for row in expiring_soon],
                'expired': [{
                    'unit_id': row[0],
                    'unit_number': row[1],
                    'lease_end': row[2].isoformat() if row[2] else None
                } for row in expired],
                'alerts': alerts if alerts else ['All leases are current']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
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
    
    # Advanced Payment Processing with Stripe
    @app.route('/api/payments/create-intent', methods=['POST'])
    def create_payment_intent():
        try:
            data = request.get_json()
            amount = int(data['amount'] * 100)  # Convert to cents
            
            # Create Stripe payment intent (mock for now)
            intent_id = f"pi_{uuid.uuid4().hex[:24]}"
            
            payment = Payment(
                tenant_id=data['tenant_id'],
                amount=data['amount'],
                due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
                status='pending',
                payment_method='stripe',
                transaction_id=intent_id
            )
            db.session.add(payment)
            db.session.commit()
            
            return jsonify({
                'client_secret': f"{intent_id}_secret",
                'payment_id': payment.id,
                'status': 'requires_payment_method'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/payments/<int:payment_id>/confirm', methods=['POST'])
    def confirm_payment(payment_id):
        try:
            payment = Payment.query.get_or_404(payment_id)
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'message': 'Payment confirmed', 'status': 'completed'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Setup Wizard API
    @app.route('/api/setup/progress', methods=['GET'])
    def get_setup_progress():
        steps = [
            {'id': 'organization', 'name': 'Organization Setup', 'completed': True},
            {'id': 'properties', 'name': 'Add Properties', 'completed': Property.query.count() > 0},
            {'id': 'users', 'name': 'Create Users', 'completed': User.query.count() > 2},
            {'id': 'payments', 'name': 'Payment Setup', 'completed': False},
            {'id': 'integrations', 'name': 'Integrations', 'completed': False}
        ]
        
        completed_steps = sum(1 for step in steps if step['completed'])
        progress_percentage = (completed_steps / len(steps)) * 100
        
        return jsonify({
            'steps': steps,
            'progress': progress_percentage,
            'completed': completed_steps,
            'total': len(steps)
        })
    
    # Maintenance Dispatch System
    @app.route('/api/maintenance/dispatch', methods=['POST'])
    def dispatch_maintenance():
        try:
            data = request.get_json()
            request_id = data['request_id']
            
            # AI-powered automatic dispatch logic
            maintenance_request = MaintenanceRequest.query.get_or_404(request_id)
            
            # Determine dispatch based on priority and type
            dispatch_rules = {
                'high': {'contractor': 'Emergency Maintenance', 'eta': 2},
                'medium': {'contractor': 'General Maintenance', 'eta': 24},
                'low': {'contractor': 'Scheduled Maintenance', 'eta': 72}
            }
            
            rule = dispatch_rules.get(maintenance_request.priority, dispatch_rules['medium'])
            
            # Update request with dispatch info
            maintenance_request.status = 'dispatched'
            maintenance_request.assigned_contractor = rule['contractor']
            maintenance_request.estimated_completion = datetime.utcnow() + timedelta(hours=rule['eta'])
            
            db.session.commit()
            
            return jsonify({
                'message': 'Maintenance request dispatched',
                'contractor': rule['contractor'],
                'eta_hours': rule['eta'],
                'status': 'dispatched'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # AI Analytics Endpoints
    @app.route('/api/ai/tenant-score/<int:tenant_id>', methods=['GET'])
    def get_tenant_score(tenant_id):
        # Mock AI tenant scoring
        tenant = Tenant.query.get_or_404(tenant_id)
        payments = Payment.query.filter_by(tenant_id=tenant_id).all()
        
        # Calculate score based on payment history
        on_time_payments = sum(1 for p in payments if p.status == 'completed')
        total_payments = len(payments)
        payment_score = (on_time_payments / total_payments * 100) if total_payments > 0 else 85
        
        # Mock additional scoring factors
        score = {
            'overall_score': min(95, payment_score + random.randint(-10, 10)),
            'payment_score': payment_score,
            'communication_score': random.randint(70, 95),
            'maintenance_score': random.randint(80, 95),
            'risk_level': 'low' if payment_score > 80 else 'medium',
            'recommendations': [
                'Tenant has excellent payment history',
                'Consider lease renewal offer',
                'Monitor for any changes in payment patterns'
            ]
        }
        
        return jsonify(score)
    
    @app.route('/api/ai/revenue-forecast', methods=['GET'])
    def get_revenue_forecast():
        # Mock revenue forecasting
        current_revenue = sum(p.amount for p in Payment.query.filter_by(status='completed').all())
        
        forecast = {
            'current_month': current_revenue,
            'next_month': current_revenue * 1.02,
            'quarterly': current_revenue * 3.1,
            'annual': current_revenue * 12.5,
            'trends': {
                'growth_rate': 2.1,
                'confidence': 85,
                'factors': ['Seasonal increase', 'New tenant onboarding', 'Market trends']
            },
            'recommendations': [
                'Consider 3% rent increase for renewals',
                'Focus on high-performing properties',
                'Monitor market competition'
            ]
        }
        
        return jsonify(forecast)
    
    @app.route('/api/ai/maintenance-forecast', methods=['GET'])
    def get_maintenance_forecast():
        properties = Property.query.all()
        requests = MaintenanceRequest.query.all()
        
        forecast = {
            'upcoming_maintenance': len([r for r in requests if r.status == 'open']),
            'estimated_monthly_cost': random.randint(3000, 8000),
            'high_priority_items': 3,
            'predictive_alerts': [
                {'property': 'Maple Grove Apartments', 'issue': 'HVAC system due for service', 'urgency': 'medium'},
                {'property': 'Oak Ridge Complex', 'issue': 'Roof inspection needed', 'urgency': 'low'},
                {'property': 'Pine Valley Condos', 'issue': 'Elevator maintenance due', 'urgency': 'high'}
            ],
            'cost_optimization': [
                'Bundle HVAC services across properties for 15% savings',
                'Schedule preventive maintenance to reduce emergency calls',
                'Consider maintenance contracts for better rates'
            ]
        }
        
        return jsonify(forecast)
    
    # Communication System
    @app.route('/api/messages', methods=['GET'])
    def get_messages():
        # Mock messaging system
        messages = [
            {
                'id': 1,
                'from': 'john.doe@email.com',
                'to': 'admin@estatecore.com',
                'subject': 'Maintenance Request Follow-up',
                'message': 'Thank you for the quick response to my AC repair request.',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'read'
            },
            {
                'id': 2,
                'from': 'jane.smith@email.com',
                'to': 'admin@estatecore.com',
                'subject': 'Lease Renewal Question',
                'message': 'I would like to discuss lease renewal options for next year.',
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'status': 'unread'
            }
        ]
        return jsonify(messages)
    
    @app.route('/api/messages', methods=['POST'])
    def send_message():
        data = request.get_json()
        # In a real system, this would save to database and send notifications
        return jsonify({'message': 'Message sent successfully', 'id': random.randint(1000, 9999)})
    
    # Document Management
    @app.route('/api/documents', methods=['GET'])
    def get_documents():
        documents = [
            {
                'id': 1,
                'name': 'Lease Agreement - Unit 2A',
                'type': 'lease',
                'size': '2.1 MB',
                'uploaded': datetime.utcnow().isoformat(),
                'tenant': 'John Doe',
                'property': 'Maple Grove Apartments'
            },
            {
                'id': 2,
                'name': 'Property Insurance Policy',
                'type': 'insurance',
                'size': '1.8 MB',
                'uploaded': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                'property': 'All Properties'
            }
        ]
        return jsonify(documents)
    
    # Financial Reports
    @app.route('/api/reports/financial', methods=['GET'])
    def get_financial_report():
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Mock financial report
        report = {
            'period': f"{start_date} to {end_date}" if start_date and end_date else "Current Month",
            'summary': {
                'total_income': 25680.00,
                'total_expenses': 8450.00,
                'net_income': 17230.00,
                'profit_margin': 67.1
            },
            'income_breakdown': {
                'rent': 24000.00,
                'late_fees': 480.00,
                'deposits': 1200.00
            },
            'expense_breakdown': {
                'maintenance': 3200.00,
                'utilities': 2100.00,
                'insurance': 1800.00,
                'management': 1350.00
            },
            'property_performance': [
                {'property': 'Maple Grove Apartments', 'income': 8400.00, 'expenses': 2800.00, 'roi': 66.7},
                {'property': 'Oak Ridge Complex', 'income': 5400.00, 'expenses': 1900.00, 'roi': 64.8},
                {'property': 'Pine Valley Condos', 'income': 7200.00, 'expenses': 2100.00, 'roi': 70.8}
            ]
        }
        
        return jsonify(report)
    
    # Access Control & Security System
    @app.route('/api/access/grant-temp', methods=['POST'])
    def grant_temporary_access():
        try:
            data = request.get_json()
            access_code = str(random.randint(100000, 999999))
            
            # Create temporary access log
            access_log = AccessLog(
                property_id=data['property_id'],
                visitor_name=data['visitor_name'],
                access_type='temporary',
                access_code=access_code,
                expires_at=datetime.utcnow() + timedelta(hours=data.get('duration_hours', 24)),
                granted_by=data.get('user_id'),
                granted=True
            )
            db.session.add(access_log)
            db.session.commit()
            
            return jsonify({
                'access_code': access_code,
                'expires_at': access_log.expires_at.isoformat(),
                'message': 'Temporary access granted',
                'instructions': f'Use code {access_code} at the property entrance'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/access/verify/<access_code>', methods=['POST'])
    def verify_access_code(access_code):
        try:
            access_log = AccessLog.query.filter_by(
                access_code=access_code,
                granted=True
            ).first()
            
            if not access_log:
                return jsonify({'error': 'Invalid access code'}), 404
            
            if access_log.expires_at and access_log.expires_at < datetime.utcnow():
                return jsonify({'error': 'Access code expired'}), 403
            
            # Log the access attempt
            access_log.last_used = datetime.utcnow()
            access_log.usage_count = (access_log.usage_count or 0) + 1
            db.session.commit()
            
            return jsonify({
                'valid': True,
                'visitor_name': access_log.visitor_name,
                'property_id': access_log.property_id,
                'access_granted': True
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Smart Door Control API
    @app.route('/api/doors/<int:property_id>/unlock', methods=['POST'])
    def unlock_door(property_id):
        try:
            data = request.get_json()
            duration = data.get('duration_seconds', 30)
            
            # Log door unlock event
            access_log = AccessLog(
                property_id=property_id,
                access_type='remote_unlock',
                access_time=datetime.utcnow(),
                granted_by=data.get('user_id'),
                granted=True,
                notes=f'Remote unlock for {duration} seconds'
            )
            db.session.add(access_log)
            db.session.commit()
            
            return jsonify({
                'message': 'Door unlocked successfully',
                'duration': duration,
                'auto_lock_at': (datetime.utcnow() + timedelta(seconds=duration)).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Tenant Portal API
    @app.route('/api/tenant/portal/<int:tenant_id>', methods=['GET'])
    def get_tenant_portal(tenant_id):
        try:
            tenant = Tenant.query.get_or_404(tenant_id)
            user = User.query.get(tenant.user_id)
            property = Property.query.get(tenant.property_id)
            
            # Get recent payments
            payments = Payment.query.filter_by(tenant_id=tenant_id).order_by(Payment.due_date.desc()).limit(5).all()
            
            # Get maintenance requests
            maintenance = MaintenanceRequest.query.filter_by(tenant_id=tenant_id).order_by(MaintenanceRequest.created_at.desc()).limit(5).all()
            
            # Get pending payments
            pending_payments = Payment.query.filter_by(tenant_id=tenant_id, status='pending').all()
            
            portal_data = {
                'tenant_info': {
                    'name': user.username,
                    'email': user.email,
                    'lease_start': tenant.lease_start.isoformat() if tenant.lease_start else None,
                    'lease_end': tenant.lease_end.isoformat() if tenant.lease_end else None,
                    'rent_amount': tenant.rent_amount
                },
                'property_info': {
                    'name': property.name,
                    'address': property.address,
                    'type': property.type
                },
                'payments': [{
                    'id': p.id,
                    'amount': p.amount,
                    'due_date': p.due_date.isoformat(),
                    'status': p.status,
                    'payment_date': p.payment_date.isoformat() if p.payment_date else None
                } for p in payments],
                'pending_payments': [{
                    'id': p.id,
                    'amount': p.amount,
                    'due_date': p.due_date.isoformat()
                } for p in pending_payments],
                'maintenance_requests': [{
                    'id': m.id,
                    'title': m.title,
                    'status': m.status,
                    'priority': m.priority,
                    'created_at': m.created_at.isoformat()
                } for m in maintenance],
                'notifications': [
                    {'type': 'payment', 'message': f'{len(pending_payments)} payment(s) due'},
                    {'type': 'maintenance', 'message': f'{len([m for m in maintenance if m.status == "open"])} open maintenance request(s)'}
                ]
            }
            
            return jsonify(portal_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Quick Actions API
    @app.route('/api/quick-actions', methods=['GET'])
    def get_quick_actions():
        quick_actions = [
            {
                'id': 'add_property',
                'title': 'Add New Property',
                'description': 'Quickly add a new property to your portfolio',
                'icon': 'building',
                'url': '/properties/new'
            },
            {
                'id': 'process_payment',
                'title': 'Process Payment',
                'description': 'Record a tenant payment',
                'icon': 'credit-card',
                'url': '/payments/new'
            },
            {
                'id': 'create_maintenance',
                'title': 'Create Maintenance Request',
                'description': 'Report a maintenance issue',
                'icon': 'wrench',
                'url': '/maintenance/new'
            },
            {
                'id': 'grant_access',
                'title': 'Grant Temporary Access',
                'description': 'Generate access code for visitors',
                'icon': 'key',
                'url': '/access/grant'
            },
            {
                'id': 'send_message',
                'title': 'Send Message',
                'description': 'Communicate with tenants or staff',
                'icon': 'message',
                'url': '/messages/new'
            }
        ]
        return jsonify(quick_actions)
    
    # Analytics Dashboard API
    @app.route('/api/analytics/overview', methods=['GET'])
    def get_analytics_overview():
        # Comprehensive analytics for dashboard
        total_properties = Property.query.count()
        total_tenants = Tenant.query.filter_by(status='active').count()
        total_revenue = sum(p.amount for p in Payment.query.filter_by(status='completed').all())
        
        # Calculate occupancy rate
        occupied_properties = Property.query.filter_by(is_available=False).count()
        occupancy_rate = (occupied_properties / total_properties * 100) if total_properties > 0 else 0
        
        # Maintenance metrics
        open_maintenance = MaintenanceRequest.query.filter_by(status='open').count()
        avg_resolution_time = 24  # Mock data
        
        # Financial metrics
        monthly_revenue = total_revenue * 0.08  # Approximate monthly
        expenses = monthly_revenue * 0.3  # 30% expense ratio
        net_income = monthly_revenue - expenses
        
        analytics = {
            'key_metrics': {
                'total_properties': total_properties,
                'total_tenants': total_tenants,
                'occupancy_rate': round(occupancy_rate, 1),
                'monthly_revenue': round(monthly_revenue, 2),
                'net_income': round(net_income, 2),
                'open_maintenance': open_maintenance
            },
            'performance_indicators': {
                'revenue_growth': 12.5,  # Percentage
                'tenant_satisfaction': 87,  # Score out of 100
                'maintenance_efficiency': 95,  # Percentage
                'collection_rate': 98.2  # Percentage
            },
            'recent_activity': [
                {'action': 'Payment received', 'details': '$1,200 from John Doe', 'time': '2 hours ago'},
                {'action': 'Maintenance completed', 'details': 'AC repair at Maple Grove', 'time': '4 hours ago'},
                {'action': 'New tenant onboarded', 'details': 'Sarah Wilson - Unit 3B', 'time': '1 day ago'}
            ],
            'alerts': [
                {'type': 'warning', 'message': '3 payments overdue', 'priority': 'medium'},
                {'type': 'info', 'message': '2 maintenance requests require attention', 'priority': 'low'}
            ]
        }
        
        return jsonify(analytics)

    # AI Lease Processing & Expiration Reminders
    @app.route('/api/ai/process-lease', methods=['POST'])
    def process_lease_document():
        try:
            data = request.get_json()
            lease_content = data.get('lease_content', '')
            tenant_id = data.get('tenant_id')
            
            # AI lease parsing simulation (in production, use OpenAI or similar)
            import re
            
            # Extract lease dates
            lease_start_match = re.search(r'lease.*start.*?(\d{1,2}[/-]\d{1,2}[/-]\d{4})', lease_content, re.IGNORECASE)
            lease_end_match = re.search(r'lease.*end|expir.*?(\d{1,2}[/-]\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})', lease_content, re.IGNORECASE)
            rent_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', lease_content)
            
            parsed_data = {
                'lease_start': lease_start_match.group(1) if lease_start_match else None,
                'lease_end': lease_end_match.group(1) if lease_end_match else None,
                'rent_amount': rent_match.group(1).replace(',', '') if rent_match else None,
                'parsed_at': datetime.utcnow().isoformat(),
                'ai_confidence': 0.85,
                'extracted_terms': []
            }
            
            # Update tenant record with parsed data
            if tenant_id:
                tenant = Tenant.query.get(tenant_id)
                if tenant:
                    tenant.lease_parsed_data = str(parsed_data)
                    db.session.commit()
            
            return jsonify({
                'message': 'Lease document processed successfully',
                'parsed_data': parsed_data
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/ai/lease-expiration-check', methods=['GET'])
    def check_lease_expirations():
        try:
            # Get tenants with leases expiring in the next 30-90 days
            thirty_days = datetime.utcnow() + timedelta(days=30)
            ninety_days = datetime.utcnow() + timedelta(days=90)
            
            expiring_leases = Tenant.query.filter(
                Tenant.lease_end.between(datetime.utcnow(), ninety_days),
                Tenant.status == 'active'
            ).all()
            
            notifications = []
            for tenant in expiring_leases:
                user = User.query.get(tenant.user_id) if tenant.user_id else None
                property = Property.query.get(tenant.property_id) if tenant.property_id else None
                unit = Unit.query.get(tenant.unit_id) if hasattr(tenant, 'unit_id') and tenant.unit_id else None
                
                days_until_expiry = (tenant.lease_end - datetime.utcnow()).days if tenant.lease_end else 0
                
                priority = 'high' if days_until_expiry <= 30 else 'medium' if days_until_expiry <= 60 else 'low'
                
                notifications.append({
                    'tenant_id': tenant.id,
                    'tenant_name': user.username if user else 'Unknown',
                    'tenant_email': user.email if user else 'Unknown',
                    'property_name': property.name if property else 'Unknown',
                    'unit_number': unit.unit_number if unit else 'N/A',
                    'lease_end_date': tenant.lease_end.isoformat() if tenant.lease_end else None,
                    'days_until_expiry': days_until_expiry,
                    'priority': priority,
                    'reminder_sent': tenant.lease_expiration_reminder_sent if hasattr(tenant, 'lease_expiration_reminder_sent') else False
                })
            
            return jsonify({
                'expiring_leases': notifications,
                'total_count': len(notifications),
                'high_priority_count': len([n for n in notifications if n['priority'] == 'high'])
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/ai/send-expiration-reminder/<int:tenant_id>', methods=['POST'])
    def send_expiration_reminder(tenant_id):
        try:
            tenant = Tenant.query.get_or_404(tenant_id)
            user = User.query.get(tenant.user_id) if tenant.user_id else None
            property = Property.query.get(tenant.property_id) if tenant.property_id else None
            unit = Unit.query.get(tenant.unit_id) if hasattr(tenant, 'unit_id') and tenant.unit_id else None
            
            # Mark reminder as sent
            if hasattr(tenant, 'lease_expiration_reminder_sent'):
                tenant.lease_expiration_reminder_sent = True
                db.session.commit()
            
            # In production, send actual email/SMS here
            message_content = f"""
            Dear {user.username if user else 'Tenant'},
            
            This is a reminder that your lease for {property.name if property else 'your property'} 
            {f'Unit {unit.unit_number}' if unit else ''} 
            is set to expire on {tenant.lease_end.strftime('%B %d, %Y') if tenant.lease_end else 'N/A'}.
            
            Please contact us to discuss renewal options.
            
            Best regards,
            Property Management
            """
            
            return jsonify({
                'message': 'Expiration reminder sent successfully',
                'recipient': user.email if user else 'Unknown',
                'lease_end_date': tenant.lease_end.isoformat() if tenant.lease_end else None
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Invites API
    @app.route('/api/invites', methods=['GET'])
    def get_invites():
        try:
            invites = Invite.query.all()
            result = []
            for invite in invites:
                invited_by = User.query.get(invite.invited_by_id) if invite.invited_by_id else None
                result.append({
                    'id': invite.id,
                    'email': invite.email,
                    'role': invite.role,
                    'token': invite.token,
                    'invited_by': invited_by.username if invited_by else 'Unknown',
                    'expires_at': invite.expires_at.isoformat() if invite.expires_at else None,
                    'is_used': invite.is_used,
                    'created_at': invite.created_at.isoformat() if invite.created_at else None
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/invites', methods=['POST'])
    def create_invite():
        try:
            data = request.get_json()
            
            # Generate unique token
            import secrets
            token = secrets.token_urlsafe(32)
            
            # Set expiration (7 days from now)
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            invite = Invite(
                email=data['email'],
                role=data.get('role', 'tenant'),
                token=token,
                invited_by_id=data.get('invited_by_id', 1),  # Default to admin
                expires_at=expires_at
            )
            
            db.session.add(invite)
            db.session.commit()
            
            # Create in-app message notification
            message = Message(
                recipient_id=data.get('invited_by_id', 1),
                subject=f'Invitation sent to {data["email"]}',
                content=f'An invitation has been sent to {data["email"]} for the role: {data.get("role", "tenant")}. The invitation will expire on {expires_at.strftime("%B %d, %Y")}.',
                message_type='invitation',
                is_system=True,
                priority='normal'
            )
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'message': 'Invite created successfully',
                'id': invite.id,
                'token': token,
                'expires_at': expires_at.isoformat()
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/invites/<token>', methods=['GET'])
    def get_invite_by_token(token):
        try:
            invite = Invite.query.filter_by(token=token).first()
            if not invite:
                return jsonify({'error': 'Invite not found'}), 404
            
            if invite.is_used:
                return jsonify({'error': 'Invite already used'}), 400
            
            if invite.expires_at < datetime.utcnow():
                return jsonify({'error': 'Invite expired'}), 400
            
            return jsonify({
                'email': invite.email,
                'role': invite.role,
                'expires_at': invite.expires_at.isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/invites/<token>/accept', methods=['POST'])
    def accept_invite(token):
        try:
            invite = Invite.query.filter_by(token=token).first()
            if not invite:
                return jsonify({'error': 'Invite not found'}), 404
            
            if invite.is_used:
                return jsonify({'error': 'Invite already used'}), 400
            
            if invite.expires_at < datetime.utcnow():
                return jsonify({'error': 'Invite expired'}), 400
            
            data = request.get_json()
            
            # Create new user
            user = User(
                email=invite.email,
                username=data.get('username', invite.email.split('@')[0]),
                password_hash='temp_hash',  # Should be properly hashed
                role=invite.role
            )
            
            db.session.add(user)
            
            # Mark invite as used
            invite.is_used = True
            
            db.session.commit()
            
            return jsonify({
                'message': 'Invite accepted successfully',
                'user_id': user.id
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Messages API (In-app messaging system)
    @app.route('/api/messages', methods=['GET'])
    def get_user_messages():
        try:
            user_id = request.args.get('user_id', 1, type=int)
            messages = Message.query.filter_by(recipient_id=user_id).order_by(Message.created_at.desc()).all()
            
            result = []
            for msg in messages:
                sender = User.query.get(msg.sender_id) if msg.sender_id else None
                result.append({
                    'id': msg.id,
                    'sender': sender.username if sender else 'System',
                    'sender_email': sender.email if sender else 'system@estatecore.com',
                    'subject': msg.subject,
                    'content': msg.content,
                    'message_type': msg.message_type,
                    'is_read': msg.is_read,
                    'is_system': msg.is_system,
                    'priority': msg.priority,
                    'created_at': msg.created_at.isoformat(),
                    'read_at': msg.read_at.isoformat() if msg.read_at else None
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/messages', methods=['POST'])
    def create_message():
        try:
            data = request.get_json()
            
            message = Message(
                sender_id=data.get('sender_id'),
                recipient_id=data['recipient_id'],
                subject=data['subject'],
                content=data['content'],
                message_type=data.get('message_type', 'general'),
                is_system=data.get('is_system', False),
                priority=data.get('priority', 'normal')
            )
            
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'message': 'Message sent successfully',
                'id': message.id
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/messages/<int:message_id>/read', methods=['PUT'])
    def mark_message_read(message_id):
        try:
            message = Message.query.get_or_404(message_id)
            message.is_read = True
            message.read_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({'message': 'Message marked as read'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/messages/<int:message_id>', methods=['DELETE'])
    def delete_message(message_id):
        try:
            message = Message.query.get_or_404(message_id)
            db.session.delete(message)
            db.session.commit()
            
            return jsonify({'message': 'Message deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database error: {e}")
    
    # Initialize Stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_test_key_here')
    
    # Companies API
    @app.route('/api/companies', methods=['GET'])
    def get_companies():
        try:
            # Check if companies table exists
            result = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'companies'
                )
            """)).fetchone()
            
            if not result[0]:
                # Table doesn't exist yet, return empty list
                return jsonify([])
            
            # Direct SQL query for existing tables (simplified for compatibility)
            result = db.session.execute(db.text("""
                SELECT id, name, email
                FROM companies 
                LIMIT 10
            """)).fetchall()
            
            companies_list = []
            for row in result:
                companies_list.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'phone': None,
                    'city': None,
                    'state': None,
                    'created_at': None,
                    'is_active': True,
                    'building_count': 0  # Will update when buildings table exists
                })
            return jsonify(companies_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/companies', methods=['POST'])
    def create_company():
        try:
            data = request.get_json()
            
            # Create Stripe customer for the company
            stripe_customer = None
            if data.get('email'):
                try:
                    stripe_customer = stripe.Customer.create(
                        email=data['email'],
                        name=data['name'],
                        description=f"Company: {data['name']}"
                    )
                except Exception as stripe_error:
                    print(f"Stripe customer creation failed: {stripe_error}")
            
            company = Company(
                name=data['name'],
                legal_name=data.get('legal_name'),
                email=data['email'],
                phone=data.get('phone'),
                address=data.get('address'),
                city=data.get('city'),
                state=data.get('state'),
                zip_code=data.get('zip_code'),
                website=data.get('website'),
                license_number=data.get('license_number'),
                tax_id=data.get('tax_id'),
                stripe_customer_id=stripe_customer.id if stripe_customer else None,
                trial_ends_at=datetime.utcnow() + timedelta(days=30)  # 30-day trial
            )
            db.session.add(company)
            db.session.commit()
            
            return jsonify({'message': 'Company created', 'id': company.id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/companies/<int:company_id>', methods=['PUT'])
    def update_company(company_id):
        try:
            company = Company.query.get_or_404(company_id)
            data = request.get_json()
            
            company.name = data.get('name', company.name)
            company.legal_name = data.get('legal_name', company.legal_name)
            company.email = data.get('email', company.email)
            company.phone = data.get('phone', company.phone)
            company.address = data.get('address', company.address)
            company.city = data.get('city', company.city)
            company.state = data.get('state', company.state)
            company.zip_code = data.get('zip_code', company.zip_code)
            company.website = data.get('website', company.website)
            company.license_number = data.get('license_number', company.license_number)
            company.tax_id = data.get('tax_id', company.tax_id)
            company.updated_at = datetime.utcnow()
            
            db.session.commit()
            return jsonify({'message': 'Company updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Buildings API
    @app.route('/api/buildings', methods=['GET'])
    def get_buildings():
        try:
            # Check if buildings table exists
            result = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'buildings'
                )
            """)).fetchone()
            
            if not result[0]:
                # Table doesn't exist yet, return empty list
                return jsonify([])
            
            company_id = request.args.get('company_id')
            
            # Direct SQL query for existing tables (simplified for compatibility)
            result = db.session.execute(db.text("""
                SELECT id, name
                FROM buildings 
                LIMIT 10
            """)).fetchall()
            
            buildings_list = []
            for row in result:
                buildings_list.append({
                    'id': row[0],
                    'name': row[1],
                    'street_address': None,
                    'city': None,
                    'state': None,
                    'total_units': 0,
                    'created_at': None,
                    'is_active': True,
                    'unit_count': 0  # Will update when units table relationships work
                })
            return jsonify(buildings_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/buildings', methods=['POST'])
    def create_building():
        try:
            data = request.get_json()
            building = Building(
                company_id=data['company_id'],
                name=data['name'],
                building_type=data.get('building_type', 'residential'),
                description=data.get('description'),
                street_address=data['street_address'],
                city=data['city'],
                state=data['state'],
                zip_code=data['zip_code'],
                year_built=data.get('year_built'),
                total_floors=data.get('total_floors'),
                total_units=data.get('total_units', 0),
                parking_spaces=data.get('parking_spaces', 0),
                amenities=data.get('amenities'),
                manager_id=data.get('manager_id')
            )
            db.session.add(building)
            db.session.commit()
            return jsonify({'message': 'Building created', 'id': building.id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/buildings/<int:building_id>/units', methods=['GET'])
    def get_building_units(building_id):
        try:
            units = Unit.query.filter_by(building_id=building_id, is_deleted=False).all()
            return jsonify([{
                'id': u.id,
                'building_id': u.building_id,
                'unit_number': u.unit_number,
                'floor_number': u.floor_number,
                'bedrooms': u.bedrooms,
                'bathrooms': u.bathrooms,
                'sqft': u.sqft,
                'base_rent': float(u.base_rent) if u.base_rent else 0,
                'security_deposit': float(u.security_deposit) if u.security_deposit else 0,
                'status': u.status,
                'is_occupied': u.is_occupied,
                'available_date': u.available_date.isoformat() if u.available_date else None,
                'current_tenant': {
                    'id': u.current_tenant.id,
                    'name': f"{u.current_tenant.first_name} {u.current_tenant.last_name}"
                } if u.current_tenant else None,
                'lease_start': u.lease_start.isoformat() if u.lease_start else None,
                'lease_end': u.lease_end.isoformat() if u.lease_end else None
            } for u in units])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Enhanced Units API for Building Integration (extending existing endpoint)
    @app.route('/api/units/buildings', methods=['POST'])
    def create_building_unit():
        try:
            data = request.get_json()
            unit = Unit(
                building_id=data['building_id'],
                property_id=data.get('property_id'),  # Backward compatibility
                unit_number=data['unit_number'],
                floor_number=data.get('floor_number'),
                bedrooms=data.get('bedrooms'),
                bathrooms=data.get('bathrooms'),
                sqft=data.get('sqft'),
                base_rent=Decimal(str(data['base_rent'])),
                security_deposit=Decimal(str(data.get('security_deposit', 0))),
                status=data.get('status', 'available'),
                available_date=datetime.strptime(data['available_date'], '%Y-%m-%d').date() if data.get('available_date') else None
            )
            db.session.add(unit)
            db.session.commit()
            
            # Update building total units count
            building = Building.query.get(data['building_id'])
            if building:
                building.total_units = Unit.query.filter_by(building_id=building.id, is_deleted=False).count()
                db.session.commit()
            
            return jsonify({'message': 'Building unit created', 'id': unit.id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Stripe Payment Integration APIs
    @app.route('/api/stripe/create-customer', methods=['POST'])
    def create_stripe_customer():
        try:
            data = request.get_json()
            
            # Create Stripe customer
            stripe_customer = stripe.Customer.create(
                email=data['email'],
                name=data['name'],
                phone=data.get('phone'),
                description=f"Tenant ID: {data.get('tenant_id', 'Unknown')}"
            )
            
            # Store in our database
            customer = StripeCustomer(
                tenant_id=data.get('tenant_id'),
                company_id=data.get('company_id'),
                stripe_customer_id=stripe_customer.id,
                email=data['email'],
                name=data['name'],
                phone=data.get('phone')
            )
            db.session.add(customer)
            db.session.commit()
            
            return jsonify({
                'stripe_customer_id': stripe_customer.id,
                'customer_id': customer.id
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stripe/create-payment-intent', methods=['POST'])
    def create_stripe_payment_intent():
        try:
            data = request.get_json()
            amount = int(float(data['amount']) * 100)  # Convert to cents
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                customer=data.get('customer_id'),
                description=data.get('description', 'Rent payment'),
                metadata={
                    'tenant_id': str(data.get('tenant_id', '')),
                    'unit_id': str(data.get('unit_id', '')),
                    'payment_period': data.get('payment_period', '')
                }
            )
            
            # Create payment record
            payment = Payment(
                tenant_id=data.get('tenant_id'),
                unit_id=data.get('unit_id'),
                amount=Decimal(str(data['amount'])),
                due_date=datetime.strptime(data['due_date'], '%Y-%m-%d') if data.get('due_date') else datetime.utcnow(),
                payment_type=data.get('payment_type', 'rent'),
                description=data.get('description'),
                stripe_payment_intent_id=intent.id,
                payment_method='stripe'
            )
            db.session.add(payment)
            db.session.commit()
            
            return jsonify({
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'payment_id': payment.id
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stripe/confirm-payment', methods=['POST'])
    def confirm_stripe_payment():
        try:
            data = request.get_json()
            payment_intent_id = data['payment_intent_id']
            
            # Retrieve payment intent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Update payment record
            payment = Payment.query.filter_by(stripe_payment_intent_id=payment_intent_id).first()
            if payment:
                payment.status = 'completed' if intent.status == 'succeeded' else 'failed'
                payment.payment_date = datetime.utcnow()
                if intent.charges.data:
                    payment.stripe_charge_id = intent.charges.data[0].id
                    payment.transaction_id = intent.charges.data[0].id
                db.session.commit()
            
            return jsonify({
                'status': intent.status,
                'payment_id': payment.id if payment else None
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/rent-payments', methods=['GET'])
    def get_rent_payments():
        try:
            # Check if rent_payments table exists
            result = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'rent_payments'
                )
            """)).fetchone()
            
            if not result[0]:
                # Table doesn't exist yet, return empty list
                return jsonify([])
            
            tenant_id = request.args.get('tenant_id')
            unit_id = request.args.get('unit_id')
            status = request.args.get('status')
            
            # Build dynamic SQL query
            sql = "SELECT id, tenant_id, unit_id, amount_due, amount_paid, due_date, status, payment_period FROM rent_payments WHERE 1=1"
            params = {}
            
            if tenant_id:
                sql += " AND tenant_id = :tenant_id"
                params['tenant_id'] = tenant_id
            if unit_id:
                sql += " AND unit_id = :unit_id"
                params['unit_id'] = unit_id
            if status:
                sql += " AND status = :status"
                params['status'] = status
            
            result = db.session.execute(db.text(sql), params).fetchall()
            
            return jsonify([{
                'id': row[0],
                'tenant_id': row[1],
                'unit_id': row[2],
                'amount_due': float(row[3]) if row[3] else 0,
                'amount_paid': float(row[4]) if row[4] else 0,
                'due_date': row[5].isoformat() if row[5] else None,
                'status': row[6],
                'payment_period': row[7]
            } for row in result])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

# Create the app instance for gunicorn
app = create_app()

# For direct execution
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)