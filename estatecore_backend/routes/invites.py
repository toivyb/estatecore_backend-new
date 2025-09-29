from flask import Blueprint, request, jsonify, current_app
from estatecore_backend.models import db, User, Invite, LPRCompany
from utils.simple_email import send_invite_email, send_enhanced_invite_email, generate_invite_token
from datetime import datetime, timedelta

invites_bp = Blueprint('invites', __name__)

@invites_bp.route('/send', methods=['POST'])
def send_invite():
    """Send an invitation email to a new user"""
    try:
        data = request.json
        email = data.get('email')
        role = data.get('role', 'tenant')
        invited_by_id = data.get('invited_by_id')
        
        # Validate inputs
        if not email or not invited_by_id:
            return jsonify({'error': 'Email and invited_by_id are required'}), 400
            
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
            
        # Check if there's already a pending invite
        pending_invite = Invite.query.filter_by(
            email=email, 
            is_used=False
        ).filter(Invite.expires_at > datetime.utcnow()).first()
        
        if pending_invite:
            return jsonify({'error': 'A pending invitation already exists for this email'}), 400
            
        # Get the user who is sending the invite
        invited_by = User.query.get(invited_by_id)
        if not invited_by:
            return jsonify({'error': 'Inviting user not found'}), 404
            
        # Generate invite token and expiry
        token = generate_invite_token()
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create invite record
        invite = Invite(
            email=email,
            role=role,
            token=token,
            invited_by_id=invited_by_id,
            expires_at=expires_at
        )
        
        db.session.add(invite)
        db.session.commit()
        
        # Send invitation email
        email_sent = send_invite_email(
            email=email,
            role=role,
            invited_by=invited_by.username,
            token=token
        )
        
        if email_sent:
            return jsonify({
                'message': f'Invitation sent successfully to {email}',
                'invite_id': invite.id,
                'expires_at': expires_at.isoformat()
            }), 201
        else:
            # If email failed, still keep the invite record but notify
            return jsonify({
                'message': f'Invite created but email delivery failed. Invite token: {token}',
                'invite_id': invite.id,
                'token': token,
                'expires_at': expires_at.isoformat()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        print(f"Error sending invite: {str(e)}")
        return jsonify({'error': str(e)}), 500

@invites_bp.route('/verify', methods=['POST'])
def verify_invite():
    """Verify an invitation token"""
    try:
        data = request.json
        token = data.get('token')
        email = data.get('email')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
            
        # Find the invite
        invite = Invite.query.filter_by(token=token, is_used=False).first()
        
        if not invite:
            return jsonify({'error': 'Invalid or expired invitation'}), 400
            
        if invite.expires_at < datetime.utcnow():
            return jsonify({'error': 'Invitation has expired'}), 400
            
        if email and invite.email != email:
            return jsonify({'error': 'Email does not match invitation'}), 400
            
        return jsonify({
            'valid': True,
            'email': invite.email,
            'role': invite.role,
            'invited_by': invite.invited_by.username,
            'expires_at': invite.expires_at.isoformat()
        })
        
    except Exception as e:
        print(f"Error verifying invite: {str(e)}")
        return jsonify({'error': str(e)}), 500

@invites_bp.route('/accept', methods=['POST'])
def accept_invite():
    """Accept an invitation and create user account"""
    try:
        data = request.json
        token = data.get('token')
        username = data.get('username')
        password = data.get('password')
        
        if not all([token, username, password]):
            return jsonify({'error': 'Token, username, and password are required'}), 400
            
        # Find and validate invite
        invite = Invite.query.filter_by(token=token, is_used=False).first()
        
        if not invite:
            return jsonify({'error': 'Invalid invitation'}), 400
            
        if invite.expires_at < datetime.utcnow():
            return jsonify({'error': 'Invitation has expired'}), 400
            
        # Check if user already exists
        existing_user = User.query.filter_by(email=invite.email).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
            
        # Parse extended invite data
        import json
        extended_data = {}
        if hasattr(invite, 'notes') and invite.notes:
            try:
                extended_data = json.loads(invite.notes)
            except:
                extended_data = {}
        
        # Create new user with enhanced fields
        user = User(
            username=username,
            email=invite.email,
            role=invite.role,
            property_management_access=extended_data.get('property_management_access', False),
            lpr_management_access=extended_data.get('lpr_management_access', False),
            lpr_company_id=extended_data.get('lpr_company_id'),
            lpr_permissions=extended_data.get('lpr_permissions')
        )
        user.set_password(password)
        
        # Mark invite as used
        invite.is_used = True
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Account created successfully',
            'user_id': user.id,
            'email': user.email,
            'role': user.role
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error accepting invite: {str(e)}")
        return jsonify({'error': str(e)}), 500

@invites_bp.route('', methods=['GET'])
def get_pending_invites():
    """Get all pending invitations"""
    try:
        invites = Invite.query.filter_by(is_used=False).filter(
            Invite.expires_at > datetime.utcnow()
        ).all()
        
        result = []
        for invite in invites:
            result.append({
                'id': invite.id,
                'email': invite.email,
                'role': invite.role,
                'invited_by': invite.invited_by.username,
                'created_at': invite.created_at.isoformat(),
                'expires_at': invite.expires_at.isoformat()
            })
            
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching invites: {str(e)}")
        return jsonify({'error': str(e)}), 500

@invites_bp.route('/<int:invite_id>', methods=['DELETE'])
def cancel_invite(invite_id):
    """Cancel a pending invitation"""
    try:
        invite = Invite.query.get_or_404(invite_id)
        
        if invite.is_used:
            return jsonify({'error': 'Invitation has already been used'}), 400
            
        db.session.delete(invite)
        db.session.commit()
        
        return jsonify({'message': 'Invitation cancelled successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling invite: {str(e)}")
        return jsonify({'error': str(e)}), 500

@invites_bp.route('/send-enhanced', methods=['POST'])
def send_enhanced_invite():
    """Send an enhanced invitation with property/LPR management options"""
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
        invited_by_id = data.get('invited_by_id', 1)  # Default to super admin
        
        # Validate inputs
        if not email or not access_type:
            return jsonify({'error': 'Email and access type are required'}), 400
            
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
            
        # Validate LPR company if LPR access is requested
        if lpr_management_access and lpr_company_id:
            company = LPRCompany.query.get(lpr_company_id)
            if not company or not company.is_active:
                return jsonify({'error': 'Invalid or inactive LPR company'}), 400
                
        # Check if there's already a pending invite
        pending_invite = Invite.query.filter_by(
            email=email, 
            is_used=False
        ).filter(Invite.expires_at > datetime.utcnow()).first()
        
        if pending_invite:
            return jsonify({'error': 'A pending invitation already exists for this email'}), 400
            
        # Determine primary role for invite
        if property_role and lpr_role:
            # Both access - use property role as primary
            primary_role = property_role
        elif property_role:
            primary_role = property_role
        elif lpr_role:
            primary_role = lpr_role
        else:
            primary_role = 'user'
            
        # Generate invite token and expiry
        token = generate_invite_token()
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create enhanced invite record with JSON data for extended fields
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
        
        invite = Invite(
            email=email,
            role=primary_role,
            token=token,
            invited_by_id=invited_by_id,
            expires_at=expires_at
        )
        
        # Store extended data in notes field temporarily (we'll add a proper field later)
        invite.notes = json.dumps(extended_data)
        
        db.session.add(invite)
        db.session.commit()
        
        # Get inviting user and company name for email
        invited_by = User.query.get(invited_by_id)
        company_name = "No specific company"
        if lpr_company_id:
            company = LPRCompany.query.get(lpr_company_id)
            if company:
                company_name = company.name
        
        # Send enhanced invitation email
        email_sent = send_enhanced_invite_email(
            email=email,
            access_type=access_type,
            property_role=property_role,
            lpr_role=lpr_role,
            company_name=company_name,
            invited_by=invited_by.username if invited_by else "System Admin",
            token=token
        )
        
        if email_sent:
            return jsonify({
                'message': f'Enhanced invitation sent successfully to {email}',
                'invite_id': invite.id,
                'access_type': access_type,
                'expires_at': expires_at.isoformat()
            }), 201
        else:
            return jsonify({
                'message': f'Invite created but email delivery failed. Invite token: {token}',
                'invite_id': invite.id,
                'token': token,
                'expires_at': expires_at.isoformat()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        print(f"Error sending enhanced invite: {str(e)}")
        return jsonify({'error': str(e)}), 500

