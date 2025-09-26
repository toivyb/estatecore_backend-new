#!/usr/bin/env python3
"""
Energy Management API Routes for EstateCore Phase 5C
REST API endpoints for smart energy management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.energy_management_service import get_energy_management_service

# Create blueprint
energy_bp = Blueprint('energy_management', __name__, url_prefix='/api/energy')

@energy_bp.route('/readings', methods=['POST'])
def add_energy_reading():
    """Add a new energy reading"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['property_id', 'energy_type', 'consumption', 'cost']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Parse timestamp if provided
        timestamp = None
        if 'timestamp' in data:
            try:
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid timestamp format. Use ISO format: YYYY-MM-DDTHH:MM:SS'
                }), 400
        
        # Get service and add reading
        service = get_energy_management_service()
        result = service.add_energy_reading(
            property_id=int(data['property_id']),
            energy_type=data['energy_type'],
            consumption=float(data['consumption']),
            cost=float(data['cost']),
            timestamp=timestamp,
            unit_id=data.get('unit_id'),
            temperature=data.get('temperature'),
            occupancy=data.get('occupancy'),
            equipment_id=data.get('equipment_id'),
            metadata=data.get('metadata')
        )
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to add energy reading: {str(e)}'
        }), 500

@energy_bp.route('/forecast/<int:property_id>/<energy_type>')
def get_energy_forecast(property_id, energy_type):
    """Get energy consumption forecast"""
    try:
        # Get optional parameters
        days = request.args.get('days', 7, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        # Get service and generate forecast
        service = get_energy_management_service()
        result = service.get_energy_forecast(
            property_id=property_id,
            energy_type=energy_type,
            days=days
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate forecast: {str(e)}'
        }), 500

@energy_bp.route('/recommendations/<int:property_id>')
def get_optimization_recommendations(property_id):
    """Get AI-powered optimization recommendations"""
    try:
        service = get_energy_management_service()
        result = service.get_optimization_recommendations(property_id)
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get recommendations: {str(e)}'
        }), 500

@energy_bp.route('/analytics/<int:property_id>')
def get_energy_analytics(property_id):
    """Get comprehensive energy analytics"""
    try:
        # Get optional parameters
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        service = get_energy_management_service()
        result = service.get_energy_analytics(property_id, days)
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get analytics: {str(e)}'
        }), 500

@energy_bp.route('/alerts')
def get_energy_alerts():
    """Get energy management alerts"""
    try:
        # Get optional parameters
        property_id = request.args.get('property_id', type=int)
        status = request.args.get('status', 'active')
        severity = request.args.get('severity')
        
        service = get_energy_management_service()
        result = service.get_energy_alerts(
            property_id=property_id,
            status=status,
            severity=severity
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get alerts: {str(e)}'
        }), 500

@energy_bp.route('/dashboard/<int:property_id>')
def get_energy_dashboard(property_id):
    """Get comprehensive energy dashboard data"""
    try:
        service = get_energy_management_service()
        result = service.get_energy_dashboard_data(property_id)
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get dashboard data: {str(e)}'
        }), 500

@energy_bp.route('/simulate/<int:property_id>', methods=['POST'])
def simulate_energy_data(property_id):
    """Simulate energy data for demonstration purposes"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        if days < 1 or days > 90:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 90'
            }), 400
        
        service = get_energy_management_service()
        result = service.simulate_energy_data(property_id, days)
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to simulate data: {str(e)}'
        }), 500

@energy_bp.route('/types')
def get_energy_types():
    """Get available energy types"""
    try:
        energy_types = [
            {
                'value': 'electricity',
                'label': 'Electricity',
                'unit': 'kWh',
                'description': 'Electrical energy consumption'
            },
            {
                'value': 'gas',
                'label': 'Natural Gas',
                'unit': 'therms',
                'description': 'Natural gas consumption'
            },
            {
                'value': 'water',
                'label': 'Water',
                'unit': 'gallons',
                'description': 'Water consumption'
            },
            {
                'value': 'hvac',
                'label': 'HVAC',
                'unit': 'kWh',
                'description': 'Heating, ventilation, and air conditioning'
            },
            {
                'value': 'lighting',
                'label': 'Lighting',
                'unit': 'kWh',
                'description': 'Lighting systems energy consumption'
            },
            {
                'value': 'solar',
                'label': 'Solar',
                'unit': 'kWh',
                'description': 'Solar energy generation'
            }
        ]
        
        return jsonify({
            'success': True,
            'energy_types': energy_types
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get energy types: {str(e)}'
        }), 500

@energy_bp.route('/optimization-strategies')
def get_optimization_strategies():
    """Get available optimization strategies"""
    try:
        strategies = [
            {
                'value': 'cost_reduction',
                'label': 'Cost Reduction',
                'description': 'Focus on reducing energy costs'
            },
            {
                'value': 'sustainability',
                'label': 'Sustainability',
                'description': 'Focus on environmental impact reduction'
            },
            {
                'value': 'efficiency',
                'label': 'Efficiency',
                'description': 'Focus on improving energy efficiency'
            },
            {
                'value': 'peak_shaving',
                'label': 'Peak Shaving',
                'description': 'Reduce peak demand charges'
            },
            {
                'value': 'demand_response',
                'label': 'Demand Response',
                'description': 'Participate in utility demand response programs'
            }
        ]
        
        return jsonify({
            'success': True,
            'strategies': strategies
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get optimization strategies: {str(e)}'
        }), 500

@energy_bp.route('/comparison/<int:property_id>')
def get_energy_comparison(property_id):
    """Get energy comparison with benchmarks"""
    try:
        service = get_energy_management_service()
        analytics = service.get_energy_analytics(property_id, days=30)
        
        if not analytics['success']:
            return jsonify(analytics), 400
        
        # Generate comparison with industry benchmarks
        property_analytics = analytics['analytics']
        total_consumption = property_analytics.get('total_consumption', 0)
        total_cost = property_analytics.get('total_cost', 0)
        
        # Simple benchmark comparison (would use real data in production)
        benchmarks = {
            'industry_average_consumption': total_consumption * 1.2,  # Property is 20% better
            'industry_average_cost': total_cost * 1.15,  # Property is 15% better
            'top_quartile_consumption': total_consumption * 0.8,  # Top quartile is 20% better
            'top_quartile_cost': total_cost * 0.85,  # Top quartile is 15% better
        }
        
        # Calculate performance scores
        consumption_score = min(100, (benchmarks['industry_average_consumption'] / total_consumption) * 75) if total_consumption > 0 else 0
        cost_score = min(100, (benchmarks['industry_average_cost'] / total_cost) * 75) if total_cost > 0 else 0
        
        comparison = {
            'property_performance': {
                'consumption_score': round(consumption_score, 1),
                'cost_score': round(cost_score, 1),
                'overall_score': round((consumption_score + cost_score) / 2, 1)
            },
            'benchmarks': benchmarks,
            'insights': []
        }
        
        # Add insights
        if consumption_score >= 80:
            comparison['insights'].append('🌟 Excellent energy consumption performance')
        elif consumption_score >= 60:
            comparison['insights'].append('⚡ Good energy consumption with improvement opportunities')
        else:
            comparison['insights'].append('⚠️ Energy consumption above industry average')
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'property_analytics': property_analytics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get comparison: {str(e)}'
        }), 500

@energy_bp.route('/health')
def health_check():
    """Health check endpoint for energy management service"""
    try:
        service = get_energy_management_service()
        
        # Check if models are trained
        models_trained = service.engine.is_trained
        
        # Check data availability
        data_count = len(service.engine.energy_readings)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'models_trained': models_trained,
            'data_points': data_count,
            'service_version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Error handlers
@energy_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested energy management endpoint does not exist'
    }), 404

@energy_bp.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint'
    }), 405

@energy_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred in the energy management service'
    }), 500