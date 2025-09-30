#!/usr/bin/env python3
"""
Test script for DELETE endpoint
"""
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['*'], methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

@app.route('/api/companies/<int:company_id>', methods=['DELETE'])
def delete_company(company_id):
    return jsonify({
        'success': True,
        'message': f'DELETE test successful for company {company_id}'
    })

@app.route('/api/test')
def test():
    return jsonify({'status': 'Test server running'})

if __name__ == '__main__':
    print("Starting test server on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=False)