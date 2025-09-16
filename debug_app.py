#!/usr/bin/env python3
"""Debug version of app.py to test basic functionality"""
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()

def create_debug_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = 'debug_secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///debug.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Simple health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'EstateCore Debug'})
    
    @app.route('/')
    def root():
        return jsonify({'message': 'EstateCore Debug API', 'status': 'running'})
    
    # Simple properties endpoint
    @app.route('/api/properties', methods=['GET'])
    def get_properties():
        return jsonify([])
    
    return app

if __name__ == '__main__':
    app = create_debug_app()
    print("Starting debug server...")
    app.run(host='0.0.0.0', port=5001, debug=True)