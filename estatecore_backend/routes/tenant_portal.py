from flask import Blueprint, request, jsonify
from estatecore_backend.models import db, User, Tenant, Property, Payment, MaintenanceRequest, Notification, Message
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash

tenant_portal_bp = Blueprint('tenant_portal', __name__)

@tenant_portal_bp.route('/auth/validate', methods=['POST'])
def validate_tenant_auth():
    """Validate tenant authentication credentials"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user and verify they are a tenant
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is a tenant
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get tenant information
        tenant = Tenant.query.filter_by(user_id=user.id).first()
        if not tenant:
            return jsonify({'error': 'Tenant profile not found'}), 404
        
        return jsonify({
            'message': 'Authentication successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'tenant': {
                'id': tenant.id,
                'property_id': tenant.property_id,
                'unit_id': tenant.unit_id,
                'status': tenant.status
            }
        }), 200
        
    except Exception as e:
        print(f"Error validating tenant auth: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_tenant_profile(user_id):
    """Retrieve tenant profile data"""
    try:
        # Get user information
        user = User.query.get_or_404(user_id)
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get tenant information
        tenant = Tenant.query.filter_by(user_id=user_id).first()
        if not tenant:
            return jsonify({'error': 'Tenant profile not found'}), 404
        
        # Get property information
        property_info = None
        if tenant.property:
            property_info = {
                'id': tenant.property.id,
                'name': tenant.property.name,
                'address': tenant.property.address,
                'type': tenant.property.type
            }
        
        profile_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat() if user.created_at else None
            },
            'tenant': {
                'id': tenant.id,
                'lease_start': tenant.lease_start.isoformat() if tenant.lease_start else None,
                'lease_end': tenant.lease_end.isoformat() if tenant.lease_end else None,
                'rent_amount': float(tenant.rent_amount) if tenant.rent_amount else 0,
                'deposit': float(tenant.deposit) if tenant.deposit else 0,
                'status': tenant.status,
                'unit_id': tenant.unit_id
            },
            'property': property_info
        }
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"Error fetching tenant profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/payments/<int:user_id>', methods=['GET'])
def get_tenant_payment_history(user_id):
    """Retrieve tenant payment history"""
    try:
        # Verify user is a tenant
        user = User.query.get_or_404(user_id)
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get payment history
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        status_filter = request.args.get('status')
        
        query = Payment.query.filter_by(tenant_id=user_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        payments = query.order_by(Payment.payment_date.desc()).offset(offset).limit(limit).all()
        
        payment_data = []
        for payment in payments:
            payment_info = {
                'id': payment.id,
                'amount': float(payment.amount),
                'status': payment.status,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'stripe_payment_id': payment.stripe_payment_id,
                'property_id': payment.property_id
            }
            payment_data.append(payment_info)
        
        # Get total count for pagination
        total_count = Payment.query.filter_by(tenant_id=user_id).count()
        
        return jsonify({
            'payments': payment_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"Error fetching payment history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/maintenance/<int:user_id>', methods=['GET'])
def get_tenant_maintenance_requests(user_id):
    """Retrieve tenant maintenance requests"""
    try:
        # Verify user is a tenant
        user = User.query.get_or_404(user_id)
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get maintenance requests
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        status_filter = request.args.get('status')
        
        query = MaintenanceRequest.query.filter_by(tenant_id=user_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        requests = query.order_by(MaintenanceRequest.created_at.desc()).offset(offset).limit(limit).all()
        
        request_data = []
        for req in requests:
            request_info = {
                'id': req.id,
                'title': req.title,
                'description': req.description,
                'category': req.category,
                'priority': req.priority,
                'status': req.status,
                'notes': req.notes,
                'created_at': req.created_at.isoformat() if req.created_at else None,
                'updated_at': req.updated_at.isoformat() if req.updated_at else None,
                'completed_at': req.completed_at.isoformat() if req.completed_at else None,
                'assigned_to': req.assigned_to.username if req.assigned_to else None
            }
            request_data.append(request_info)
        
        # Get total count for pagination
        total_count = MaintenanceRequest.query.filter_by(tenant_id=user_id).count()
        
        return jsonify({
            'maintenance_requests': request_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"Error fetching maintenance requests: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/maintenance/<int:user_id>', methods=['POST'])
def create_tenant_maintenance_request(user_id):
    """Create a new maintenance request"""
    try:
        # Verify user is a tenant
        user = User.query.get_or_404(user_id)
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get tenant info for property_id
        tenant = Tenant.query.filter_by(user_id=user_id).first()
        if not tenant:
            return jsonify({'error': 'Tenant profile not found'}), 404
        
        data = request.json
        
        # Create maintenance request
        maintenance_request = MaintenanceRequest(
            tenant_id=user_id,
            property_id=tenant.property_id,
            unit_id=tenant.unit_id,
            title=data.get('title'),
            description=data.get('description'),
            category=data.get('category'),
            priority=data.get('priority', 'medium')
        )
        
        db.session.add(maintenance_request)
        db.session.commit()
        
        # Create notification for property manager
        # Find property managers/admins for this property
        admins = User.query.filter(User.role.in_(['admin', 'manager'])).all()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                title=f"New Maintenance Request: {data.get('title')}",
                message=f"Tenant {user.username} has submitted a new maintenance request for {tenant.property.name}",
                type='maintenance',
                priority=data.get('priority', 'medium'),
                action_required=True,
                action_url=f'/maintenance/{maintenance_request.id}'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Maintenance request created successfully',
            'id': maintenance_request.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating maintenance request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/notifications/<int:user_id>', methods=['GET'])
def get_tenant_notifications(user_id):
    """Retrieve tenant notifications"""
    try:
        # Verify user is a tenant
        user = User.query.get_or_404(user_id)
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get notifications
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notification_type = request.args.get('type')
        
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        if notification_type:
            query = query.filter_by(type=notification_type)
        
        # Filter out expired notifications
        query = query.filter(
            (Notification.expires_at.is_(None)) | 
            (Notification.expires_at > datetime.utcnow())
        )
        
        notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
        
        notification_data = []
        for notif in notifications:
            notification_info = {
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.type,
                'priority': notif.priority,
                'is_read': notif.is_read,
                'action_required': notif.action_required,
                'action_url': notif.action_url,
                'created_at': notif.created_at.isoformat() if notif.created_at else None,
                'read_at': notif.read_at.isoformat() if notif.read_at else None,
                'expires_at': notif.expires_at.isoformat() if notif.expires_at else None
            }
            notification_data.append(notification_info)
        
        # Get unread count
        unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).filter(
            (Notification.expires_at.is_(None)) | 
            (Notification.expires_at > datetime.utcnow())
        ).count()
        
        return jsonify({
            'notifications': notification_data,
            'unread_count': unread_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notification as read: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/lease/<int:user_id>', methods=['GET'])
def get_tenant_lease_info(user_id):
    """Retrieve tenant lease information"""
    try:
        # Verify user is a tenant
        user = User.query.get_or_404(user_id)
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get tenant information
        tenant = Tenant.query.filter_by(user_id=user_id).first()
        if not tenant:
            return jsonify({'error': 'Tenant profile not found'}), 404
        
        # Calculate lease status
        lease_status = 'active'
        days_until_expiry = None
        
        if tenant.lease_end:
            today = datetime.now().date()
            lease_end = tenant.lease_end
            
            if lease_end < today:
                lease_status = 'expired'
            else:
                days_until_expiry = (lease_end - today).days
                if days_until_expiry <= 30:
                    lease_status = 'expiring_soon'
        
        lease_data = {
            'tenant_id': tenant.id,
            'lease_start': tenant.lease_start.isoformat() if tenant.lease_start else None,
            'lease_end': tenant.lease_end.isoformat() if tenant.lease_end else None,
            'rent_amount': float(tenant.rent_amount) if tenant.rent_amount else 0,
            'deposit': float(tenant.deposit) if tenant.deposit else 0,
            'status': tenant.status,
            'lease_status': lease_status,
            'days_until_expiry': days_until_expiry,
            'lease_document_name': tenant.lease_document_name,
            'property': {
                'id': tenant.property.id,
                'name': tenant.property.name,
                'address': tenant.property.address,
                'type': tenant.property.type
            } if tenant.property else None,
            'unit_id': tenant.unit_id
        }
        
        return jsonify(lease_data), 200
        
    except Exception as e:
        print(f"Error fetching lease information: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_portal_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def get_tenant_dashboard_summary(user_id):
    """Get tenant dashboard summary with key metrics"""
    try:
        # Verify user is a tenant
        user = User.query.get_or_404(user_id)
        if user.role != 'tenant':
            return jsonify({'error': 'Access denied - tenant access only'}), 403
        
        # Get tenant information
        tenant = Tenant.query.filter_by(user_id=user_id).first()
        if not tenant:
            return jsonify({'error': 'Tenant profile not found'}), 404
        
        # Get recent payments (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        recent_payments = Payment.query.filter(
            Payment.tenant_id == user_id,
            Payment.payment_date >= six_months_ago
        ).order_by(Payment.payment_date.desc()).limit(6).all()
        
        # Get pending maintenance requests
        pending_maintenance = MaintenanceRequest.query.filter(
            MaintenanceRequest.tenant_id == user_id,
            MaintenanceRequest.status.in_(['submitted', 'in_progress'])
        ).count()
        
        # Get unread notifications
        unread_notifications = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).filter(
            (Notification.expires_at.is_(None)) | 
            (Notification.expires_at > datetime.utcnow())
        ).count()
        
        # Get unread messages
        unread_messages = Message.query.filter_by(
            recipient_id=user_id,
            is_read=False
        ).count()
        
        # Calculate lease status
        lease_status = 'active'
        days_until_expiry = None
        
        if tenant.lease_end:
            today = datetime.now().date()
            lease_end = tenant.lease_end
            
            if lease_end < today:
                lease_status = 'expired'
            else:
                days_until_expiry = (lease_end - today).days
                if days_until_expiry <= 30:
                    lease_status = 'expiring_soon'
        
        # Format recent payments
        payment_history = []
        for payment in recent_payments:
            payment_history.append({
                'id': payment.id,
                'amount': float(payment.amount),
                'status': payment.status,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None
            })
        
        dashboard_data = {
            'tenant_info': {
                'name': user.username,
                'email': user.email,
                'property_name': tenant.property.name if tenant.property else None,
                'unit_id': tenant.unit_id,
                'rent_amount': float(tenant.rent_amount) if tenant.rent_amount else 0
            },
            'lease_info': {
                'status': lease_status,
                'days_until_expiry': days_until_expiry,
                'lease_end': tenant.lease_end.isoformat() if tenant.lease_end else None
            },
            'counts': {
                'unread_notifications': unread_notifications,
                'unread_messages': unread_messages,
                'pending_maintenance': pending_maintenance
            },
            'recent_payments': payment_history
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        print(f"Error fetching dashboard summary: {str(e)}")
        return jsonify({'error': str(e)}), 500