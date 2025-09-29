from flask import Blueprint, request, jsonify
from estatecore_backend.models import db, Unit

units_bp = Blueprint('units', __name__)

@units_bp.route('', methods=['GET'])
def get_units():
    try:
        property_id = request.args.get('property_id')
        
        if property_id:
            units = Unit.query.filter_by(property_id=property_id).all()
        else:
            units = Unit.query.all()
            
        result = []
        for unit in units:
            unit_data = {
                'id': unit.id,
                'property_id': unit.property_id,
                'unit_number': unit.unit_number,
                'bedrooms': unit.bedrooms,
                'bathrooms': unit.bathrooms,
                'rent': float(unit.rent) if unit.rent else 0,
                'square_feet': unit.square_feet,
                'is_available': unit.is_available,
                'created_at': unit.created_at.isoformat() if unit.created_at else None
            }
            result.append(unit_data)
            
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching units: {str(e)}")
        return jsonify({'error': str(e)}), 500

@units_bp.route('', methods=['POST'])
def create_unit():
    try:
        data = request.json
        
        unit = Unit(
            property_id=data.get('property_id'),
            unit_number=data.get('unit_number'),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            rent=data.get('rent'),
            square_feet=data.get('square_feet'),
            is_available=data.get('is_available', True)
        )
        
        db.session.add(unit)
        db.session.commit()
        
        return jsonify({'message': 'Unit created successfully', 'id': unit.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating unit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@units_bp.route('/<int:unit_id>', methods=['PUT'])
def update_unit(unit_id):
    try:
        unit = Unit.query.get_or_404(unit_id)
        data = request.json
        
        unit.unit_number = data.get('unit_number', unit.unit_number)
        unit.bedrooms = data.get('bedrooms', unit.bedrooms)
        unit.bathrooms = data.get('bathrooms', unit.bathrooms)
        unit.rent = data.get('rent', unit.rent)
        unit.square_feet = data.get('square_feet', unit.square_feet)
        unit.is_available = data.get('is_available', unit.is_available)
        
        db.session.commit()
        return jsonify({'message': 'Unit updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating unit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@units_bp.route('/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    try:
        unit = Unit.query.get_or_404(unit_id)
        db.session.delete(unit)
        db.session.commit()
        return jsonify({'message': 'Unit deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting unit: {str(e)}")
        return jsonify({'error': str(e)}), 500