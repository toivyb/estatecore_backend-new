#!/usr/bin/env python3
"""
Emergency fix for dashboard endpoints - minimal working version
This can be deployed as a quick patch
"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from datetime import datetime

def create_emergency_app():
    app = Flask(__name__)
    
    # CORS Configuration
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS(app, origins=cors_origins, supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy', 
            'service': 'EstateCore Backend Emergency', 
            'version': 'emergency-1.0',
            'note': 'Minimal dashboard functionality while deployment completes'
        })
    
    @app.route('/dashboard', methods=['GET'])
    def get_dashboard():
        # Return mock data that matches expected structure
        return jsonify({
            'total_properties': 0,
            'available_properties': 0,
            'occupied_properties': 0,
            'total_users': 3,
            'total_payments': 0,
            'total_revenue': 0,
            'pending_revenue': 0,
            'recent_properties': []
        })
    
    @app.route('/api/ai/lease-expiration-check', methods=['GET'])
    def get_lease_expiration_check():
        return jsonify({
            'expiring_soon': [],
            'expired': [],
            'alerts': ['System is being updated - lease tracking will be available shortly']
        })
    
    # Basic existing endpoints with mock data
    @app.route('/api/properties', methods=['GET'])
    def get_properties():
        return jsonify([])
    
    @app.route('/api/tenants', methods=['GET'])
    def get_tenants():
        return jsonify([])
    
    @app.route('/api/users', methods=['GET'])
    def get_users():
        return jsonify([])
    
    return app

if __name__ == '__main__':
    app = create_emergency_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)