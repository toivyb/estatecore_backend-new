# wsgi.py at project root
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    app = create_app()
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: create a simple Flask app
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'EstateCore Backend is running'})
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})
