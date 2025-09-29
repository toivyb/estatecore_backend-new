"""
Enhanced Maintenance Request API Endpoints
Comprehensive maintenance system with photo uploads, workflow management, and notifications
"""

from flask import Blueprint, request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import mimetypes
from pathlib import Path

# Import models (assuming they're defined in models module)
from ..models import MaintenanceRequest, MaintenancePhoto, MaintenanceComment, User, Property

maintenance_bp = Blueprint('maintenance', __name__)
db = SQLAlchemy()

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_FILES_PER_REQUEST = 10

# Maintenance categories
MAINTENANCE_CATEGORIES = [
    'plumbing', 'electrical', 'hvac', 'appliances', 'flooring',
    'painting', 'roofing', 'doors_windows', 'landscaping', 'pest_control',
    'security', 'cleaning', 'other'
]

# Priority levels with escalation rules
PRIORITY_LEVELS = {
    'low': {'escalation_hours': 168, 'auto_assign': False},  # 7 days
    'medium': {'escalation_hours': 72, 'auto_assign': True},  # 3 days
    'high': {'escalation_hours': 24, 'auto_assign': True},   # 1 day
    'emergency': {'escalation_hours': 2, 'auto_assign': True}  # 2 hours
}

# Status workflow
STATUS_WORKFLOW = {
    'pending': ['assigned', 'cancelled'],
    'assigned': ['in_progress', 'pending', 'cancelled'],
    'in_progress': ['on_hold', 'completed', 'cancelled'],
    'on_hold': ['in_progress', 'cancelled'],
    'completed': ['reopened'],
    'cancelled': ['pending'],
    'reopened': ['assigned', 'in_progress']
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Get file size"""
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Seek back to beginning
    return size

def save_uploaded_file(file, request_id):
    """Save uploaded file and return file info"""
    if not file or not allowed_file(file.filename):
        return None
    
    # Check file size
    if get_file_size(file) > MAX_FILE_SIZE:
        return None
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    # Create upload directory structure
    upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads')) / 'maintenance' / str(request_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = upload_dir / unique_filename
    file.save(str(file_path))
    
    return {
        'filename': unique_filename,
        'original_filename': filename,
        'file_path': str(file_path),
        'file_size': get_file_size(file),
        'mime_type': mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    }

@maintenance_bp.route('/api/maintenance/requests', methods=['POST'])
def create_maintenance_request():
    """Create a new maintenance request with optional photo uploads"""
    try:
        # Handle multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            files = request.files.getlist('photos')
        else:
            data = request.get_json()
            files = []
        
        # Validate required fields
        required_fields = ['title', 'description', 'category', 'priority', 'property_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate category and priority
        if data['category'] not in MAINTENANCE_CATEGORIES:
            return jsonify({'error': 'Invalid category'}), 400
        
        if data['priority'] not in PRIORITY_LEVELS:
            return jsonify({'error': 'Invalid priority level'}), 400
        
        # Create maintenance request
        maintenance_request = MaintenanceRequest(
            id=str(uuid.uuid4()),
            title=data['title'],
            description=data['description'],
            category=data['category'],
            priority=data['priority'],
            status='pending',
            property_id=int(data['property_id']),
            tenant_id=data.get('tenant_id'),  # Can be None for manager-created requests
            requested_by=data.get('user_id'),  # Current user
            unit_number=data.get('unit_number'),
            location_details=data.get('location_details'),
            preferred_contact_method=data.get('preferred_contact_method', 'email'),
            access_instructions=data.get('access_instructions'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(maintenance_request)
        db.session.flush()  # To get the ID
        
        # Handle photo uploads
        photo_urls = []
        if files and len(files) <= MAX_FILES_PER_REQUEST:
            for file in files:
                if file and file.filename:
                    file_info = save_uploaded_file(file, maintenance_request.id)
                    if file_info:
                        photo = MaintenancePhoto(
                            id=str(uuid.uuid4()),
                            maintenance_request_id=maintenance_request.id,
                            filename=file_info['filename'],
                            original_filename=file_info['original_filename'],
                            file_path=file_info['file_path'],
                            file_size=file_info['file_size'],
                            mime_type=file_info['mime_type'],
                            uploaded_by=data.get('user_id'),
                            uploaded_at=datetime.utcnow()
                        )
                        db.session.add(photo)
                        photo_urls.append(f"/api/maintenance/photos/{photo.id}")
        
        # Auto-assign if priority requires it
        if PRIORITY_LEVELS[data['priority']]['auto_assign']:
            # Logic to auto-assign to available maintenance staff
            # This would integrate with your staff management system
            pass
        
        db.session.commit()
        
        # Create notification for property managers
        # This would integrate with your notification system
        
        return jsonify({
            'message': 'Maintenance request created successfully',
            'request_id': maintenance_request.id,
            'status': maintenance_request.status,
            'priority': maintenance_request.priority,
            'photo_urls': photo_urls
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating maintenance request: {str(e)}")
        return jsonify({'error': 'Failed to create maintenance request'}), 500

@maintenance_bp.route('/api/maintenance/requests', methods=['GET'])
def get_maintenance_requests():
    """Get maintenance requests with filtering and pagination"""
    try:
        # Query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status = request.args.get('status')
        priority = request.args.get('priority')
        category = request.args.get('category')
        property_id = request.args.get('property_id')
        tenant_id = request.args.get('tenant_id')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        
        # Build query
        query = MaintenanceRequest.query
        
        # Apply filters
        if status:
            query = query.filter(MaintenanceRequest.status == status)
        if priority:
            query = query.filter(MaintenanceRequest.priority == priority)
        if category:
            query = query.filter(MaintenanceRequest.category == category)
        if property_id:
            query = query.filter(MaintenanceRequest.property_id == int(property_id))
        if tenant_id:
            query = query.filter(MaintenanceRequest.tenant_id == int(tenant_id))
        if assigned_to:
            query = query.filter(MaintenanceRequest.assigned_to_id == int(assigned_to))
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    MaintenanceRequest.title.ilike(search_term),
                    MaintenanceRequest.description.ilike(search_term)
                )
            )
        
        # Order by priority and creation date
        priority_order = db.case(
            (MaintenanceRequest.priority == 'emergency', 1),
            (MaintenanceRequest.priority == 'high', 2),
            (MaintenanceRequest.priority == 'medium', 3),
            (MaintenanceRequest.priority == 'low', 4),
            else_=5
        )
        query = query.order_by(priority_order, MaintenanceRequest.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        requests = []
        for req in pagination.items:
            # Get photos
            photos = MaintenancePhoto.query.filter_by(
                maintenance_request_id=req.id
            ).all()
            
            # Get latest comment
            latest_comment = MaintenanceComment.query.filter_by(
                maintenance_request_id=req.id
            ).order_by(MaintenanceComment.created_at.desc()).first()
            
            requests.append({
                'id': req.id,
                'title': req.title,
                'description': req.description,
                'category': req.category,
                'priority': req.priority,
                'status': req.status,
                'property_id': req.property_id,
                'tenant_id': req.tenant_id,
                'assigned_to_id': req.assigned_to_id,
                'unit_number': req.unit_number,
                'location_details': req.location_details,
                'estimated_cost': req.estimated_cost,
                'actual_cost': req.actual_cost,
                'created_at': req.created_at.isoformat() if req.created_at else None,
                'updated_at': req.updated_at.isoformat() if req.updated_at else None,
                'completed_at': req.completed_at.isoformat() if req.completed_at else None,
                'due_date': req.due_date.isoformat() if req.due_date else None,
                'photos': [
                    {
                        'id': photo.id,
                        'url': f"/api/maintenance/photos/{photo.id}",
                        'original_filename': photo.original_filename,
                        'uploaded_at': photo.uploaded_at.isoformat()
                    } for photo in photos
                ],
                'latest_comment': {
                    'text': latest_comment.comment_text,
                    'created_at': latest_comment.created_at.isoformat(),
                    'author_id': latest_comment.user_id
                } if latest_comment else None,
                'days_open': (datetime.utcnow() - req.created_at).days if req.created_at else 0
            })
        
        return jsonify({
            'requests': requests,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching maintenance requests: {str(e)}")
        return jsonify({'error': 'Failed to fetch maintenance requests'}), 500

@maintenance_bp.route('/api/maintenance/requests/<request_id>', methods=['GET'])
def get_maintenance_request(request_id):
    """Get a specific maintenance request with full details"""
    try:
        maintenance_request = MaintenanceRequest.query.filter_by(id=request_id).first()
        if not maintenance_request:
            return jsonify({'error': 'Maintenance request not found'}), 404
        
        # Get photos
        photos = MaintenancePhoto.query.filter_by(
            maintenance_request_id=request_id
        ).order_by(MaintenancePhoto.uploaded_at.desc()).all()
        
        # Get comments/timeline
        comments = MaintenanceComment.query.filter_by(
            maintenance_request_id=request_id
        ).order_by(MaintenanceComment.created_at.asc()).all()
        
        # Get property and tenant info
        property_info = Property.query.filter_by(id=maintenance_request.property_id).first()
        tenant_info = User.query.filter_by(id=maintenance_request.tenant_id).first() if maintenance_request.tenant_id else None
        assigned_to_info = User.query.filter_by(id=maintenance_request.assigned_to_id).first() if maintenance_request.assigned_to_id else None
        
        return jsonify({
            'id': maintenance_request.id,
            'title': maintenance_request.title,
            'description': maintenance_request.description,
            'category': maintenance_request.category,
            'priority': maintenance_request.priority,
            'status': maintenance_request.status,
            'property': {
                'id': property_info.id,
                'name': property_info.name,
                'address': property_info.address
            } if property_info else None,
            'tenant': {
                'id': tenant_info.id,
                'name': f"{tenant_info.first_name} {tenant_info.last_name}",
                'email': tenant_info.email
            } if tenant_info else None,
            'assigned_to': {
                'id': assigned_to_info.id,
                'name': f"{assigned_to_info.first_name} {assigned_to_info.last_name}",
                'email': assigned_to_info.email
            } if assigned_to_info else None,
            'unit_number': maintenance_request.unit_number,
            'location_details': maintenance_request.location_details,
            'estimated_cost': maintenance_request.estimated_cost,
            'actual_cost': maintenance_request.actual_cost,
            'preferred_contact_method': maintenance_request.preferred_contact_method,
            'access_instructions': maintenance_request.access_instructions,
            'created_at': maintenance_request.created_at.isoformat() if maintenance_request.created_at else None,
            'updated_at': maintenance_request.updated_at.isoformat() if maintenance_request.updated_at else None,
            'completed_at': maintenance_request.completed_at.isoformat() if maintenance_request.completed_at else None,
            'due_date': maintenance_request.due_date.isoformat() if maintenance_request.due_date else None,
            'photos': [
                {
                    'id': photo.id,
                    'url': f"/api/maintenance/photos/{photo.id}",
                    'thumbnail_url': f"/api/maintenance/photos/{photo.id}?size=thumbnail",
                    'original_filename': photo.original_filename,
                    'file_size': photo.file_size,
                    'uploaded_at': photo.uploaded_at.isoformat(),
                    'uploaded_by': photo.uploaded_by
                } for photo in photos
            ],
            'timeline': [
                {
                    'id': comment.id,
                    'type': comment.comment_type,
                    'text': comment.comment_text,
                    'author_id': comment.user_id,
                    'created_at': comment.created_at.isoformat(),
                    'is_internal': comment.is_internal
                } for comment in comments
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching maintenance request {request_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch maintenance request'}), 500

@maintenance_bp.route('/api/maintenance/requests/<request_id>/status', methods=['PATCH'])
def update_maintenance_status(request_id):
    """Update maintenance request status with workflow validation"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        comment = data.get('comment', '')
        user_id = data.get('user_id')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        maintenance_request = MaintenanceRequest.query.filter_by(id=request_id).first()
        if not maintenance_request:
            return jsonify({'error': 'Maintenance request not found'}), 404
        
        # Validate status transition
        current_status = maintenance_request.status
        if new_status not in STATUS_WORKFLOW.get(current_status, []):
            return jsonify({'error': f'Cannot transition from {current_status} to {new_status}'}), 400
        
        # Update status
        old_status = maintenance_request.status
        maintenance_request.status = new_status
        maintenance_request.updated_at = datetime.utcnow()
        
        # Set completion date if completed
        if new_status == 'completed':
            maintenance_request.completed_at = datetime.utcnow()
        
        # Add status change comment
        if comment or old_status != new_status:
            status_comment = MaintenanceComment(
                id=str(uuid.uuid4()),
                maintenance_request_id=request_id,
                user_id=user_id,
                comment_text=comment or f"Status changed from {old_status} to {new_status}",
                comment_type='status_change',
                created_at=datetime.utcnow()
            )
            db.session.add(status_comment)
        
        db.session.commit()
        
        # Send notifications
        # This would integrate with your notification system
        
        return jsonify({
            'message': 'Status updated successfully',
            'old_status': old_status,
            'new_status': new_status,
            'updated_at': maintenance_request.updated_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating maintenance request status: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500

@maintenance_bp.route('/api/maintenance/requests/<request_id>/assign', methods=['PATCH'])
def assign_maintenance_request(request_id):
    """Assign maintenance request to staff member"""
    try:
        data = request.get_json()
        assigned_to_id = data.get('assigned_to_id')
        comment = data.get('comment', '')
        user_id = data.get('user_id')
        
        maintenance_request = MaintenanceRequest.query.filter_by(id=request_id).first()
        if not maintenance_request:
            return jsonify({'error': 'Maintenance request not found'}), 404
        
        # Validate assignee exists and has appropriate role
        assignee = User.query.filter_by(id=assigned_to_id).first()
        if not assignee:
            return jsonify({'error': 'Assignee not found'}), 404
        
        old_assignee_id = maintenance_request.assigned_to_id
        maintenance_request.assigned_to_id = assigned_to_id
        maintenance_request.updated_at = datetime.utcnow()
        
        # Update status to assigned if it was pending
        if maintenance_request.status == 'pending':
            maintenance_request.status = 'assigned'
        
        # Add assignment comment
        assignment_comment = MaintenanceComment(
            id=str(uuid.uuid4()),
            maintenance_request_id=request_id,
            user_id=user_id,
            comment_text=comment or f"Assigned to {assignee.first_name} {assignee.last_name}",
            comment_type='assignment',
            created_at=datetime.utcnow()
        )
        db.session.add(assignment_comment)
        
        db.session.commit()
        
        # Send notification to assignee
        # This would integrate with your notification system
        
        return jsonify({
            'message': 'Assignment updated successfully',
            'assigned_to': {
                'id': assignee.id,
                'name': f"{assignee.first_name} {assignee.last_name}",
                'email': assignee.email
            },
            'status': maintenance_request.status
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning maintenance request: {str(e)}")
        return jsonify({'error': 'Failed to assign request'}), 500

@maintenance_bp.route('/api/maintenance/requests/<request_id>/comments', methods=['POST'])
def add_maintenance_comment(request_id):
    """Add a comment to maintenance request"""
    try:
        data = request.get_json()
        comment_text = data.get('comment')
        user_id = data.get('user_id')
        is_internal = data.get('is_internal', False)
        
        if not comment_text:
            return jsonify({'error': 'Comment text is required'}), 400
        
        maintenance_request = MaintenanceRequest.query.filter_by(id=request_id).first()
        if not maintenance_request:
            return jsonify({'error': 'Maintenance request not found'}), 404
        
        comment = MaintenanceComment(
            id=str(uuid.uuid4()),
            maintenance_request_id=request_id,
            user_id=user_id,
            comment_text=comment_text,
            comment_type='comment',
            is_internal=is_internal,
            created_at=datetime.utcnow()
        )
        
        db.session.add(comment)
        maintenance_request.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Get user info for response
        user = User.query.filter_by(id=user_id).first()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'text': comment.comment_text,
                'author': f"{user.first_name} {user.last_name}" if user else "Unknown",
                'created_at': comment.created_at.isoformat(),
                'is_internal': comment.is_internal
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding comment: {str(e)}")
        return jsonify({'error': 'Failed to add comment'}), 500

@maintenance_bp.route('/api/maintenance/requests/<request_id>/photos', methods=['POST'])
def upload_maintenance_photos(request_id):
    """Upload additional photos to existing maintenance request"""
    try:
        maintenance_request = MaintenanceRequest.query.filter_by(id=request_id).first()
        if not maintenance_request:
            return jsonify({'error': 'Maintenance request not found'}), 404
        
        files = request.files.getlist('photos')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        if len(files) > MAX_FILES_PER_REQUEST:
            return jsonify({'error': f'Maximum {MAX_FILES_PER_REQUEST} files allowed'}), 400
        
        uploaded_photos = []
        user_id = request.form.get('user_id')
        
        for file in files:
            if file and file.filename:
                file_info = save_uploaded_file(file, request_id)
                if file_info:
                    photo = MaintenancePhoto(
                        id=str(uuid.uuid4()),
                        maintenance_request_id=request_id,
                        filename=file_info['filename'],
                        original_filename=file_info['original_filename'],
                        file_path=file_info['file_path'],
                        file_size=file_info['file_size'],
                        mime_type=file_info['mime_type'],
                        uploaded_by=user_id,
                        uploaded_at=datetime.utcnow()
                    )
                    db.session.add(photo)
                    uploaded_photos.append({
                        'id': photo.id,
                        'url': f"/api/maintenance/photos/{photo.id}",
                        'original_filename': photo.original_filename
                    })
        
        if uploaded_photos:
            # Add photo upload comment
            photo_comment = MaintenanceComment(
                id=str(uuid.uuid4()),
                maintenance_request_id=request_id,
                user_id=user_id,
                comment_text=f"Added {len(uploaded_photos)} photo(s)",
                comment_type='photo_upload',
                created_at=datetime.utcnow()
            )
            db.session.add(photo_comment)
            
            maintenance_request.updated_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'message': f'{len(uploaded_photos)} photos uploaded successfully',
            'photos': uploaded_photos
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading photos: {str(e)}")
        return jsonify({'error': 'Failed to upload photos'}), 500

@maintenance_bp.route('/api/maintenance/photos/<photo_id>', methods=['GET'])
def get_maintenance_photo(photo_id):
    """Serve maintenance request photos"""
    try:
        photo = MaintenancePhoto.query.filter_by(id=photo_id).first()
        if not photo:
            return jsonify({'error': 'Photo not found'}), 404
        
        # Check if file exists
        file_path = Path(photo.file_path)
        if not file_path.exists():
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Get size parameter for thumbnails
        size = request.args.get('size', 'full')
        
        if size == 'thumbnail':
            # In a real implementation, you'd generate or serve a thumbnail
            # For now, serve the full image
            pass
        
        # Serve the file
        from flask import send_file
        return send_file(
            file_path,
            mimetype=photo.mime_type,
            as_attachment=False,
            download_name=photo.original_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Error serving photo {photo_id}: {str(e)}")
        return jsonify({'error': 'Failed to serve photo'}), 500

@maintenance_bp.route('/api/maintenance/categories', methods=['GET'])
def get_maintenance_categories():
    """Get available maintenance categories"""
    return jsonify({
        'categories': MAINTENANCE_CATEGORIES
    })

@maintenance_bp.route('/api/maintenance/priorities', methods=['GET'])
def get_maintenance_priorities():
    """Get available priority levels"""
    return jsonify({
        'priorities': list(PRIORITY_LEVELS.keys())
    })

@maintenance_bp.route('/api/maintenance/dashboard', methods=['GET'])
def get_maintenance_dashboard():
    """Get maintenance dashboard statistics"""
    try:
        # Get various statistics
        total_requests = MaintenanceRequest.query.count()
        pending_requests = MaintenanceRequest.query.filter_by(status='pending').count()
        in_progress_requests = MaintenanceRequest.query.filter_by(status='in_progress').count()
        completed_today = MaintenanceRequest.query.filter(
            MaintenanceRequest.completed_at >= datetime.utcnow().date()
        ).count()
        
        # High priority requests
        high_priority = MaintenanceRequest.query.filter(
            MaintenanceRequest.priority.in_(['high', 'emergency']),
            MaintenanceRequest.status.in_(['pending', 'assigned', 'in_progress'])
        ).count()
        
        # Overdue requests (no due date handling in basic schema, using creation date + priority)
        overdue_requests = []
        for priority, config in PRIORITY_LEVELS.items():
            cutoff_time = datetime.utcnow() - timedelta(hours=config['escalation_hours'])
            overdue = MaintenanceRequest.query.filter(
                MaintenanceRequest.priority == priority,
                MaintenanceRequest.status.in_(['pending', 'assigned']),
                MaintenanceRequest.created_at <= cutoff_time
            ).count()
            if overdue > 0:
                overdue_requests.append({
                    'priority': priority,
                    'count': overdue,
                    'escalation_hours': config['escalation_hours']
                })
        
        # Recent requests
        recent_requests = MaintenanceRequest.query.order_by(
            MaintenanceRequest.created_at.desc()
        ).limit(5).all()
        
        recent_list = []
        for req in recent_requests:
            recent_list.append({
                'id': req.id,
                'title': req.title,
                'priority': req.priority,
                'status': req.status,
                'created_at': req.created_at.isoformat() if req.created_at else None
            })
        
        return jsonify({
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'in_progress_requests': in_progress_requests,
            'completed_today': completed_today,
            'high_priority_requests': high_priority,
            'overdue_requests': overdue_requests,
            'recent_requests': recent_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching maintenance dashboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500