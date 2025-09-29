from flask import Blueprint, request, jsonify
from estatecore_backend.models import db, User, Tenant, Property
from datetime import datetime

tenants_bp = Blueprint('tenants', __name__)

@tenants_bp.route('', methods=['GET'])
def get_tenants():
    try:
        # Get all tenants with their user and property information
        tenants = db.session.query(Tenant).join(User).all()
        result = []
        
        for tenant in tenants:
            tenant_data = {
                'id': tenant.id,
                'user_id': tenant.user_id,
                'property_id': tenant.property_id,
                'unit_id': tenant.unit_id,
                'lease_start': tenant.lease_start.isoformat() if tenant.lease_start else None,
                'lease_end': tenant.lease_end.isoformat() if tenant.lease_end else None,
                'rent_amount': float(tenant.rent_amount) if tenant.rent_amount else 0,
                'deposit': float(tenant.deposit) if tenant.deposit else 0,
                'status': tenant.status,
                'lease_document_name': tenant.lease_document_name,
                'user': {
                    'id': tenant.user.id,
                    'username': tenant.user.username,
                    'email': tenant.user.email,
                    'role': tenant.user.role
                } if tenant.user else None,
                'property': {
                    'id': tenant.property.id,
                    'name': tenant.property.name,
                    'address': tenant.property.address
                } if tenant.property else None
            }
            result.append(tenant_data)
            
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching tenants: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenants_bp.route('', methods=['POST'])
def create_tenant():
    try:
        data = request.json
        
        # Create new tenant record
        tenant = Tenant(
            user_id=data.get('user_id'),
            property_id=data.get('property_id'),
            unit_id=data.get('unit_id'),
            lease_start=datetime.fromisoformat(data.get('lease_start').replace('Z', '+00:00')) if data.get('lease_start') else None,
            lease_end=datetime.fromisoformat(data.get('lease_end').replace('Z', '+00:00')) if data.get('lease_end') else None,
            rent_amount=data.get('rent_amount'),
            deposit=data.get('deposit', 0),
            status=data.get('status', 'active'),
            lease_document_name=data.get('lease_document_name'),
            lease_document_path=data.get('lease_document_path'),
            lease_parsed_data=data.get('lease_parsed_data')
        )
        
        db.session.add(tenant)
        db.session.commit()
        
        return jsonify({'message': 'Tenant created successfully', 'id': tenant.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating tenant: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenants_bp.route('/<int:tenant_id>', methods=['PUT'])
def update_tenant(tenant_id):
    try:
        tenant = Tenant.query.get_or_404(tenant_id)
        data = request.json
        
        # Update tenant fields
        if 'lease_start' in data and data['lease_start']:
            tenant.lease_start = datetime.fromisoformat(data['lease_start'].replace('Z', '+00:00'))
        if 'lease_end' in data and data['lease_end']:
            tenant.lease_end = datetime.fromisoformat(data['lease_end'].replace('Z', '+00:00'))
        if 'rent_amount' in data:
            tenant.rent_amount = data['rent_amount']
        if 'deposit' in data:
            tenant.deposit = data['deposit']
        if 'status' in data:
            tenant.status = data['status']
            
        # Update user information if provided
        if 'user' in data and tenant.user:
            user_data = data['user']
            if 'username' in user_data:
                tenant.user.username = user_data['username']
            if 'email' in user_data:
                tenant.user.email = user_data['email']
        
        db.session.commit()
        return jsonify({'message': 'Tenant updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating tenant: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenants_bp.route('/<int:tenant_id>', methods=['DELETE'])
def delete_tenant(tenant_id):
    try:
        tenant = Tenant.query.get_or_404(tenant_id)
        db.session.delete(tenant)
        db.session.commit()
        return jsonify({'message': 'Tenant deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting tenant: {str(e)}")
        return jsonify({'error': str(e)}), 500