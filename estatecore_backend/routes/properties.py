from flask import Blueprint, request, jsonify
from estatecore_backend.models import db, Property

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('', methods=['GET'])
def get_properties():
    try:
        properties = Property.query.all()  # Get all properties, not just available ones
        result = []
        for prop in properties:
            result.append({
                'id': prop.id,
                'name': prop.name if hasattr(prop, 'name') else prop.address,
                'address': prop.address,
                'type': prop.type,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'rent': float(prop.rent) if prop.rent else 0,
                'units': prop.units if hasattr(prop, 'units') else 1,
                'description': prop.description,
                'is_available': prop.is_available,
                'created_at': prop.created_at.isoformat() if prop.created_at else None
            })
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching properties: {str(e)}")
        return jsonify({'error': str(e)}), 500

@properties_bp.route('', methods=['POST'])
def create_property():
    try:
        data = request.json
        print(f"Received property data: {data}")  # Debug log
        
        # Default owner_id to 1 if not provided (assuming super admin has ID 1)
        owner_id = data.get('owner_id', 1)
        
        # Convert empty strings to None for numeric fields
        def safe_int(value):
            if value == '' or value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        def safe_float(value):
            if value == '' or value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        property = Property(
            name=data.get('name', '') or 'Unnamed Property',
            address=data.get('address', '') or 'No Address',
            type=data.get('type', '') or 'other',
            bedrooms=safe_int(data.get('bedrooms')),
            bathrooms=safe_float(data.get('bathrooms')),
            rent=safe_float(data.get('rent')) or 0,
            units=safe_int(data.get('units')) or 1,
            description=data.get('description', ''),
            owner_id=owner_id
        )
        
        db.session.add(property)
        db.session.commit()
        
        return jsonify({
            'message': 'Property created successfully', 
            'id': property.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating property: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/<int:property_id>', methods=['GET'])
def get_property(property_id):
    try:
        property = Property.query.get_or_404(property_id)
        return jsonify({
            'id': property.id,
            'name': property.name if hasattr(property, 'name') else property.address,
            'address': property.address,
            'type': property.type,
            'bedrooms': property.bedrooms,
            'bathrooms': property.bathrooms,
            'rent': float(property.rent) if property.rent else 0,
            'units': property.units if hasattr(property, 'units') else 1,
            'description': property.description,
            'is_available': property.is_available,
            'created_at': property.created_at.isoformat() if property.created_at else None
        })
    except Exception as e:
        print(f"Error fetching property: {str(e)}")
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/<int:property_id>', methods=['PUT'])
def update_property(property_id):
    try:
        property = Property.query.get_or_404(property_id)
        data = request.json
        
        # Update fields if provided
        if 'name' in data:
            property.name = data['name']
        if 'address' in data:
            property.address = data['address']
        if 'type' in data:
            property.type = data['type']
        if 'bedrooms' in data:
            property.bedrooms = data['bedrooms']
        if 'bathrooms' in data:
            property.bathrooms = data['bathrooms']
        if 'rent' in data:
            property.rent = data['rent']
        if 'units' in data:
            property.units = data['units']
        if 'description' in data:
            property.description = data['description']
        if 'is_available' in data:
            property.is_available = data['is_available']
            
        db.session.commit()
        
        return jsonify({'message': 'Property updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating property: {str(e)}")
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    try:
        property = Property.query.get_or_404(property_id)
        
        # Check for related records that might prevent deletion
        from estatecore_backend.models import Tenant, Unit
        
        # Check for active tenants
        active_tenants = Tenant.query.filter_by(property_id=property_id, status='active').count()
        if active_tenants > 0:
            return jsonify({
                'error': f'Cannot delete property with {active_tenants} active tenant(s). Please terminate or move tenants first.'
            }), 400
        
        # Delete related records first to avoid foreign key constraints
        try:
            # Delete all units for this property
            Unit.query.filter_by(property_id=property_id).delete()
            
            # Delete inactive tenants
            Tenant.query.filter_by(property_id=property_id).delete()
            
            # Now delete the property
            db.session.delete(property)
            db.session.commit()
            
            return jsonify({'message': 'Property and related records deleted successfully'})
            
        except Exception as delete_error:
            db.session.rollback()
            # If cascading delete fails, provide helpful error message
            error_str = str(delete_error)
            if 'foreign key constraint' in error_str.lower():
                return jsonify({
                    'error': 'Cannot delete property due to related records. Please remove all tenants, units, and payments first.'
                }), 400
            else:
                return jsonify({'error': f'Delete failed: {error_str}'}), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting property: {str(e)}")
        return jsonify({'error': f'Failed to delete property: {str(e)}'}), 500