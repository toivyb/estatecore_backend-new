from flask import Blueprint, jsonify
from estatecore_backend import db
from estatecore_backend.models import Property, Payment, User

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    try:
        # Get basic counts
        total_properties = Property.query.count()
        available_properties = Property.query.filter_by(is_available=True).count()
        total_users = User.query.filter_by(is_active=True).count()
        total_payments = Payment.query.count()
        
        # Calculate total revenue
        completed_payments = Payment.query.filter_by(status='completed').all()
        total_revenue = sum(payment.amount for payment in completed_payments)
        
        # Calculate pending payments
        pending_payments = Payment.query.filter_by(status='pending').all()
        pending_revenue = sum(payment.amount for payment in pending_payments)
        
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard-metrics', methods=['GET'])
def get_dashboard_metrics():
    try:
        # Calculate rent collected
        completed_payments = Payment.query.filter_by(status='completed').all()
        rent_collected = sum(payment.amount for payment in completed_payments)
        
        # Calculate outstanding rent
        pending_payments = Payment.query.filter_by(status='pending').all()
        outstanding_rent = sum(payment.amount for payment in pending_payments)
        
        # Mock data for now - in a real app this would come from actual data
        open_maintenance = 5
        
        return jsonify({
            'rent_collected': rent_collected,
            'outstanding_rent': outstanding_rent,
            'open_maintenance': open_maintenance,
            'total_properties': Property.query.count(),
            'occupied_units': Property.query.filter_by(is_available=False).count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500