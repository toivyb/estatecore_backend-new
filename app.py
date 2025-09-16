import os
import sys
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
    
    # Database URI - handle Render's postgres:// URLs
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///estatecore.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CORS Configuration
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=cors_origins, supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])
    
    # Health check routes
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'EstateCore Backend'})
    
    @app.route('/')
    def root():
        return jsonify({'message': 'EstateCore API', 'status': 'running'})
    
    @app.route('/api/properties')
    def get_properties():
        return jsonify([])
    
    @app.route('/dashboard')
    def get_dashboard():
        return jsonify({
            'total_properties': 0,
            'available_properties': 0,
            'occupied_properties': 0,
            'total_users': 0,
            'total_payments': 0,
            'total_revenue': 0.0,
            'pending_revenue': 0.0,
            'recent_properties': []
        })
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            # Simple demo authentication
            if email == 'demo@estatecore.com' and password == 'demo123':
                return jsonify({
                    'access_token': 'demo-token-12345',
                    'user': {
                        'id': 1,
                        'email': email,
                        'username': 'Demo User',
                        'role': 'admin'
                    }
                })
            
            return jsonify({'error': 'Invalid credentials'}), 401
            
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database error: {e}")
    
    return app

# Create the app instance for gunicorn
app = create_app()

# For direct execution
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)