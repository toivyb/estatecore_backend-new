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
    assigned_contractor = db.Column(db.String(100))
    estimated_completion = db.Column(db.DateTime)
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='unread')
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
    
    @app.route('/api/properties/<int:property_id>', methods=['PUT'])
    def update_property(property_id):
        try:
            property = Property.query.get_or_404(property_id)
            data = request.get_json()
            
            property.name = data.get('name', property.name)
            property.address = data.get('address', property.address)
            property.type = data.get('type', property.type)
            property.bedrooms = data.get('bedrooms', property.bedrooms)
            property.bathrooms = data.get('bathrooms', property.bathrooms)
            property.rent = data.get('rent', property.rent)
            property.units = data.get('units', property.units)
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
        users = User.query.all()  # Get all users including inactive
        return jsonify([{
            'id': u.id,
            'email': u.email,
            'username': u.username,
            'role': u.role,
            'is_active': u.is_active,
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
    
    # Tenants API
    @app.route('/api/tenants', methods=['GET'])
    def get_tenants():
        try:
            tenants = Tenant.query.all()
            result = []
            for tenant in tenants:
                user = User.query.get(tenant.user_id) if tenant.user_id else None
                property = Property.query.get(tenant.property_id) if tenant.property_id else None
                
                result.append({
                    'id': tenant.id,
                    'user': {'id': user.id, 'email': user.email, 'username': user.username} if user else None,
                    'property': {'id': property.id, 'name': property.name, 'address': property.address} if property else None,
                    'lease_start': tenant.lease_start.isoformat() if tenant.lease_start else None,
                    'lease_end': tenant.lease_end.isoformat() if tenant.lease_end else None,
                    'rent_amount': tenant.rent_amount,
                    'deposit': tenant.deposit,
                    'status': tenant.status
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/tenants', methods=['POST'])
    def create_tenant():
        try:
            data = request.get_json()
            tenant = Tenant(
                user_id=data['user_id'],
                property_id=data['property_id'],
                lease_start=datetime.strptime(data['lease_start'], '%Y-%m-%d') if data.get('lease_start') else None,
                lease_end=datetime.strptime(data['lease_end'], '%Y-%m-%d') if data.get('lease_end') else None,
                rent_amount=data.get('rent_amount'),
                deposit=data.get('deposit'),
                status='active'
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
            
            if data.get('lease_start'):
                tenant.lease_start = datetime.strptime(data['lease_start'], '%Y-%m-%d')
            if data.get('lease_end'):
                tenant.lease_end = datetime.strptime(data['lease_end'], '%Y-%m-%d')
            
            tenant.rent_amount = data.get('rent_amount', tenant.rent_amount)
            tenant.deposit = data.get('deposit', tenant.deposit)
            tenant.status = data.get('status', tenant.status)
            
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