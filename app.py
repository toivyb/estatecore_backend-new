import os
import sys
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

# Initialize extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Import and register blueprints
    from estatecore_backend.routes.auth import auth_bp
    from estatecore_backend.routes.properties import properties_bp
    from estatecore_backend.routes.users import users_bp
    from estatecore_backend.routes.payments import payments_bp
    from estatecore_backend.routes.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(properties_bp, url_prefix='/api/properties')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    
    # Health check route
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'EstateCore Backend'})
    
    @app.route('/')
    def root():
        return jsonify({'message': 'EstateCore API', 'status': 'running'})
    
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database error: {e}")
    
    return app

# For direct execution
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)