#!/usr/bin/env python3
"""
Simple minimal Flask app for testing
"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def home():
        return jsonify({
            'message': 'EstateCore API is running',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/dashboard')
    def api_dashboard():
        return jsonify({
            'total_properties': 15,
            'available_properties': 3,
            'total_users': 42,
            'total_revenue': 125000.50,
            'pending_revenue': 8500.25
        })
    
    @app.route('/dashboard')
    def dashboard():
        return jsonify({
            'total_properties': 15,
            'available_properties': 3,
            'total_users': 42,
            'total_revenue': 125000.50,
            'pending_revenue': 8500.25
        })
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        # Simple test login
        if email == 'admin@estatecore.com' and password == 'admin':
            return jsonify({
                'token': 'test-token-123',
                'user': {
                    'id': 1,
                    'email': email,
                    'username': 'Admin User',
                    'role': 'admin'
                }
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    # Add common endpoints that frontend might call
    @app.route('/api/properties')
    def properties():
        return jsonify([
            {'id': 1, 'name': 'Test Property 1', 'address': '123 Main St'},
            {'id': 2, 'name': 'Test Property 2', 'address': '456 Oak Ave'}
        ])
    
    @app.route('/api/tenants')
    def tenants():
        return jsonify([
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ])
    
    @app.route('/api/maintenance')
    def maintenance():
        return jsonify([
            {'id': 1, 'description': 'Fix leaky faucet', 'status': 'pending'},
            {'id': 2, 'description': 'Replace light bulb', 'status': 'completed'}
        ])
    
    @app.route('/api/ai/lease-expiration-check')
    def lease_expiration_check():
        return jsonify({
            'success': True,
            'total_count': 3,
            'high_priority_count': 1,
            'expiring_leases': [
                {
                    'tenant_name': 'Sarah Johnson',
                    'property_name': 'Sunset Apartments',
                    'unit_number': '2A',
                    'lease_end_date': '2025-10-15',
                    'days_until_expiry': 26,
                    'priority': 'high'
                },
                {
                    'tenant_name': 'Mike Chen',
                    'property_name': 'Oak Ridge Complex',
                    'unit_number': '1B',
                    'lease_end_date': '2025-11-30',
                    'days_until_expiry': 72,
                    'priority': 'medium'
                },
                {
                    'tenant_name': 'Emily Davis',
                    'property_name': 'Maple Street Units',
                    'unit_number': '3C',
                    'lease_end_date': '2025-12-31',
                    'days_until_expiry': 103,
                    'priority': 'low'
                }
            ]
        })
    
    @app.route('/api/lpr/events')
    def lpr_events():
        return jsonify([
            {
                'id': 1,
                'plate_number': 'ABC123',
                'confidence': 0.95,
                'camera_id': 'cam_001',
                'created_at': '2025-01-19T10:30:00Z',
                'location': 'Main Entrance',
                'status': 'allowed'
            },
            {
                'id': 2,
                'plate_number': 'XYZ789',
                'confidence': 0.88,
                'camera_id': 'cam_002', 
                'created_at': '2025-01-19T09:15:00Z',
                'location': 'Parking Garage',
                'status': 'denied'
            },
            {
                'id': 3,
                'plate_number': 'DEF456',
                'confidence': 0.92,
                'camera_id': 'cam_001',
                'created_at': '2025-01-18T16:45:00Z',
                'location': 'Main Entrance',
                'status': 'allowed'
            }
        ])
    
    @app.route('/api/lpr/blacklist')
    def lpr_blacklist():
        return jsonify([
            {
                'id': 1,
                'plate_number': 'BAN001',
                'reason': 'Unauthorized vehicle',
                'added_by': 'admin',
                'created_at': '2025-01-15T14:20:00Z'
            },
            {
                'id': 2,
                'plate_number': 'XYZ789',
                'reason': 'Trespassing incident',
                'added_by': 'security',
                'created_at': '2025-01-16T08:30:00Z'
            }
        ])
    
    # Add more common endpoints that pages might need
    @app.route('/api/users')
    def users():
        return jsonify([
            {
                'id': 1,
                'email': 'admin@estatecore.com',
                'username': 'Admin User',
                'role': 'admin',
                'is_active': True,
                'first_name': 'Admin',
                'last_name': 'User',
                'created_at': '2025-01-01T00:00:00Z'
            },
            {
                'id': 2,
                'email': 'demo@estatecore.com',
                'username': 'Demo User',
                'role': 'manager',
                'is_active': True,
                'first_name': 'Demo',
                'last_name': 'User',
                'created_at': '2025-01-02T00:00:00Z'
            }
        ])
    
    @app.route('/api/financial/dashboard')
    def financial_dashboard():
        return jsonify({
            'success': True,
            'data': {
                'overview_metrics': {
                    'total_revenue': 125000.50,
                    'net_income': 89000.25,
                    'profit_margin': 71.2,
                    'cash_flow': 45000.75,
                    'occupancy_rate': 95.5
                },
                'quick_stats': {
                    'properties_count': 15,
                    'units_count': 120,
                    'tenants_count': 114,
                    'maintenance_requests': 3
                },
                'alerts': [
                    {
                        'type': 'warning',
                        'severity': 'medium',
                        'title': 'High Vacancy Rate',
                        'message': 'Unit 2A has been vacant for 45 days'
                    }
                ]
            }
        })
    
    @app.route('/api/lease/dashboard')
    def lease_dashboard():
        return jsonify({
            'success': True,
            'data': {
                'total_active_leases': 114,
                'occupancy_rate': 95.0,
                'expiring_soon': 8,
                'renewal_rate': 87.5,
                'lease_violations': {
                    'open': 2,
                    'resolved': 15
                }
            }
        })
    
    @app.route('/api/maintenance/scheduling')
    def maintenance_scheduling():
        return jsonify({
            'success': True,
            'scheduled_requests': [
                {
                    'id': 1,
                    'title': 'HVAC Maintenance',
                    'property': 'Building A',
                    'unit': '2A',
                    'scheduled_date': '2025-01-25',
                    'priority': 'medium',
                    'status': 'scheduled'
                }
            ]
        })
    
    @app.route('/api/tenant-screening')
    def tenant_screening():
        return jsonify({
            'success': True,
            'applications': [
                {
                    'id': 1,
                    'applicant_name': 'John Smith',
                    'property': 'Sunset Apartments',
                    'unit': '3B',
                    'status': 'pending',
                    'score': 750,
                    'submitted_date': '2025-01-18'
                }
            ]
        })
    
    @app.route('/api/bulk-operations')
    def bulk_operations():
        return jsonify({
            'success': True,
            'operations': [
                {
                    'id': 1,
                    'type': 'rent_increase',
                    'status': 'completed',
                    'affected_units': 25,
                    'created_date': '2025-01-15'
                }
            ]
        })
    
    @app.route('/api/access-logs')
    def access_logs():
        return jsonify([
            {
                'id': 1,
                'user': 'John Doe',
                'door': 'Main Entrance',
                'time': '2025-01-19T10:30:00Z',
                'action': 'entry',
                'status': 'success'
            },
            {
                'id': 2,
                'user': 'Jane Smith',
                'door': 'Parking Garage',
                'time': '2025-01-19T09:15:00Z',
                'action': 'exit',
                'status': 'success'
            }
        ])
    
    @app.route('/api/access-logs/simulate', methods=['POST'])
    def simulate_access():
        return jsonify({'success': True, 'message': 'Access log simulated'})
    
    @app.route('/api/messages')
    def messages():
        return jsonify([
            {
                'id': 1,
                'from': 'Property Manager',
                'to': 'John Doe',
                'subject': 'Rent Reminder',
                'message': 'Your rent is due on the 1st',
                'timestamp': '2025-01-19T10:00:00Z',
                'read': False
            }
        ])
    
    @app.route('/api/documents')
    def documents():
        return jsonify([
            {
                'id': 1,
                'name': 'Lease Agreement.pdf',
                'type': 'lease',
                'size': '2.5 MB',
                'uploaded_date': '2025-01-15',
                'tenant': 'John Doe'
            }
        ])
    
    @app.route('/api/reports')
    def reports():
        return jsonify([
            {
                'id': 1,
                'name': 'Monthly Revenue Report',
                'type': 'financial',
                'generated_date': '2025-01-01',
                'status': 'completed'
            }
        ])
    
    @app.route('/api/performance/metrics')
    def performance_metrics():
        return jsonify({
            'success': True,
            'metrics': {
                'response_time': 250,
                'uptime': 99.9,
                'memory_usage': 45.2,
                'cpu_usage': 23.1
            }
        })
    
    @app.route('/api/testing/results')
    def testing_results():
        return jsonify({
            'success': True,
            'test_suites': [
                {
                    'name': 'API Tests',
                    'status': 'passed',
                    'tests_run': 45,
                    'passed': 43,
                    'failed': 2
                }
            ]
        })
    
    # Catch-all for other API endpoints
    @app.route('/api/<path:path>')
    def api_catchall(path):
        return jsonify({
            'message': f'Endpoint /api/{path} not implemented in simple app',
            'status': 'placeholder'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("Starting EstateCore Simple App...")
    app.run(host='localhost', port=5179, debug=True)