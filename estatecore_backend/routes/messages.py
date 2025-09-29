from flask import Blueprint, request, jsonify
from estatecore_backend.models import db, Message, User
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('', methods=['GET'])
def get_messages():
    """Get messages for a user (inbox)"""
    try:
        user_id = request.args.get('user_id', type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        message_type = request.args.get('type')
        limit = request.args.get('limit', 50, type=int)
        
        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400
            
        query = Message.query.filter_by(recipient_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
            
        if message_type:
            query = query.filter_by(message_type=message_type)
            
        messages = query.order_by(Message.created_at.desc()).limit(limit).all()
        
        result = []
        for msg in messages:
            message_data = {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'sender_name': msg.sender.username if msg.sender else 'System',
                'subject': msg.subject,
                'content': msg.content,
                'message_type': msg.message_type,
                'is_read': msg.is_read,
                'is_system': msg.is_system,
                'priority': msg.priority,
                'created_at': msg.created_at.isoformat(),
                'read_at': msg.read_at.isoformat() if msg.read_at else None
            }
            result.append(message_data)
            
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('', methods=['POST'])
def send_message():
    """Send a new message"""
    try:
        data = request.json
        
        message = Message(
            sender_id=data.get('sender_id'),
            recipient_id=data.get('recipient_id'),
            subject=data.get('subject'),
            content=data.get('content'),
            message_type=data.get('message_type', 'general'),
            priority=data.get('priority', 'normal'),
            is_system=data.get('is_system', False)
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent successfully',
            'id': message.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/<int:message_id>/read', methods=['PUT'])
def mark_as_read(message_id):
    """Mark a message as read"""
    try:
        message = Message.query.get_or_404(message_id)
        
        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.utcnow()
            db.session.commit()
            
        return jsonify({'message': 'Message marked as read'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error marking message as read: {str(e)}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message"""
    try:
        message = Message.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'message': 'Message deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/unread-count', methods=['GET'])
def get_unread_count():
    """Get count of unread messages for a user"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400
            
        count = Message.query.filter_by(
            recipient_id=user_id,
            is_read=False
        ).count()
        
        return jsonify({'unread_count': count})
        
    except Exception as e:
        print(f"Error getting unread count: {str(e)}")
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/broadcast', methods=['POST'])
def broadcast_message():
    """Send a message to multiple users (admin only)"""
    try:
        data = request.json
        sender_id = data.get('sender_id')
        recipient_ids = data.get('recipient_ids', [])
        subject = data.get('subject')
        content = data.get('content')
        message_type = data.get('message_type', 'general')
        priority = data.get('priority', 'normal')
        
        if not all([sender_id, recipient_ids, subject, content]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Verify sender has admin privileges
        sender = User.query.get(sender_id)
        if not sender or sender.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Unauthorized - admin access required'}), 403
            
        messages_created = 0
        for recipient_id in recipient_ids:
            message = Message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                subject=subject,
                content=content,
                message_type=message_type,
                priority=priority
            )
            db.session.add(message)
            messages_created += 1
            
        db.session.commit()
        
        return jsonify({
            'message': f'Broadcast sent to {messages_created} recipients',
            'recipients': messages_created
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error broadcasting message: {str(e)}")
        return jsonify({'error': str(e)}), 500