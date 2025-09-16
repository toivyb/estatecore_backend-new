import os
import sys
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid

# Initialize extensions
db = SQLAlchemy()

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='tenant')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Float)
    rent = db.Column(db.Float, nullable=False)
    units = db.Column(db.Integer, default=1)
    occupancy = db.Column(db.String(10))
    description = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    lease_start = db.Column(db.DateTime)
    lease_end = db.Column(db.DateTime)
    rent_amount = db.Column(db.Float, nullable=False)
    deposit = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))

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
    resolved_at = db.Column(db.DateTime)

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    visitor_name = db.Column(db.String(100))
    access_time = db.Column(db.DateTime, default=datetime.utcnow)
    access_type = db.Column(db.String(50))
    granted = db.Column(db.Boolean, default=True)

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
        return jsonify({'status': 'healthy', 'service': 'EstateCore Backend'})
    
    @app.route('/')
    def root():
        return jsonify({'message': 'EstateCore API', 'status': 'running'})
    
    # Properties API
    @app.route('/api/properties', methods=['GET'])
    def get_properties():
        properties = Property.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'address': p.address,
            'type': p.type,
            'bedrooms': p.bedrooms,
            'bathrooms': p.bathrooms,
            'rent': p.rent,
            'units': p.units,
            'occupancy': p.occupancy,
            'is_available': p.is_available
        } for p in properties])
    
    @app.route('/api/properties', methods=['POST'])
    def create_property():
        data = request.get_json()
        property = Property(
            name=data['name'],
            address=data['address'],
            type=data['type'],
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            rent=data['rent'],
            units=data.get('units', 1),
            description=data.get('description'),
            owner_id=1  # Default owner
        )
        db.session.add(property)
        db.session.commit()
        return jsonify({'message': 'Property created', 'id': property.id}), 201
    
    # Users API
    @app.route('/api/users', methods=['GET'])
    def get_users():
        users = User.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': u.id,
            'email': u.email,
            'username': u.username,
            'role': u.role,
            'created_at': u.created_at.isoformat()
        } for u in users])
    
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
    
    # Tenants API
    @app.route('/api/tenants', methods=['GET'])
    def get_tenants():
        tenants = db.session.query(Tenant, User, Property).join(User).join(Property).all()
        return jsonify([{
            'id': t.id,
            'user': {'id': u.id, 'email': u.email, 'username': u.username},
            'property': {'id': p.id, 'name': p.name, 'address': p.address},
            'lease_start': t.lease_start.isoformat() if t.lease_start else None,
            'lease_end': t.lease_end.isoformat() if t.lease_end else None,
            'rent_amount': t.rent_amount,
            'status': t.status
        } for t, u, p in tenants])
    
    # Payments API
    @app.route('/api/payments', methods=['GET'])
    def get_payments():
        payments = db.session.query(Payment, Tenant, User, Property).join(Tenant).join(User).join(Property).all()
        return jsonify([{
            'id': pay.id,
            'amount': pay.amount,
            'payment_date': pay.payment_date.isoformat(),
            'due_date': pay.due_date.isoformat(),
            'status': pay.status,
            'tenant': u.username,
            'property': p.name
        } for pay, t, u, p in payments])
    
    # Maintenance API
    @app.route('/api/maintenance', methods=['GET'])
    def get_maintenance():
        requests = db.session.query(MaintenanceRequest, Property).join(Property).all()
        return jsonify([{
            'id': m.id,
            'title': m.title,
            'description': m.description,
            'priority': m.priority,
            'status': m.status,
            'property': p.name,
            'created_at': m.created_at.isoformat()
        } for m, p in requests])
    
    @app.route('/api/maintenance', methods=['POST'])
    def create_maintenance():
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
        total_properties = Property.query.count()
        available_properties = Property.query.filter_by(is_available=True).count()
        total_users = User.query.filter_by(is_active=True).count()
        total_payments = Payment.query.count()
        
        completed_payments = Payment.query.filter_by(status='completed').all()
        total_revenue = sum(p.amount for p in completed_payments)
        
        pending_payments = Payment.query.filter_by(status='pending').all()
        pending_revenue = sum(p.amount for p in pending_payments)
        
        return jsonify({
            'total_properties': total_properties,
            'available_properties': available_properties,
            'occupied_properties': total_properties - available_properties,
            'total_users': total_users,
            'total_payments': total_payments,
            'total_revenue': total_revenue,
            'pending_revenue': pending_revenue,
            'recent_properties': []
        })
    
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
    
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database error: {e}")
    
    return app

# Create the app instance for gunicorn
app = create_app()

# For direct execution
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)