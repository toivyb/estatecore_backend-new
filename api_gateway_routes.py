"""
API Gateway Routes Integration for EstateCore
Flask routes that integrate the API Gateway with existing EstateCore services
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, Response, g, current_app
from functools import wraps

# Import API Gateway services
from api_gateway_service import (
    get_api_gateway_service, APIVersion, HTTPMethod, AuthenticationType,
    APIEndpoint, APIRequest, RequestTransformer, ResponseTransformer
)
from api_key_management_service import get_api_key_service, APIKeyType, APIKeyPermissions
from oauth_authentication_service import get_oauth_service, GrantType, SecuritySchemeType
from api_monitoring_service import get_monitoring_service, RequestMetrics
from api_documentation_service import get_documentation_service
from enterprise_features_service import get_enterprise_service

# Import existing EstateCore services
from permissions_service import get_permission_service, Permission, Role
from security_service import get_security_service, SecurityEventType, ThreatLevel
from rate_limiting_service import get_rate_limiting_service, RateLimitConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIGatewayMiddleware:
    """API Gateway middleware for Flask"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.gateway_service = get_api_gateway_service()
        self.key_service = get_api_key_service()
        self.oauth_service = get_oauth_service()
        self.monitoring_service = get_monitoring_service()
        self.enterprise_service = get_enterprise_service()
        
        # Register middleware
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Initialize default endpoints
        self._register_default_endpoints()
    
    def _register_default_endpoints(self):
        """Register default API endpoints with the gateway"""
        
        # Authentication endpoints
        auth_endpoints = [
            APIEndpoint(
                path="/api/v1/auth/login",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/auth/login",
                authentication=AuthenticationType.NONE,
                rate_limit=10,
                circuit_breaker_enabled=True,
                documentation={
                    "summary": "User login",
                    "description": "Authenticate user and return access token",
                    "tags": ["Authentication"]
                }
            ),
            APIEndpoint(
                path="/api/v1/auth/logout",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/auth/logout",
                authentication=AuthenticationType.JWT_TOKEN,
                documentation={
                    "summary": "User logout",
                    "description": "Invalidate user session",
                    "tags": ["Authentication"]
                }
            )
        ]
        
        # Properties endpoints
        properties_endpoints = [
            APIEndpoint(
                path="/api/v1/properties",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/properties",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["properties:read"],
                rate_limit=100,
                enable_caching=True,
                cache_ttl=300,
                documentation={
                    "summary": "List properties",
                    "description": "Retrieve a paginated list of properties",
                    "tags": ["Properties"]
                }
            ),
            APIEndpoint(
                path="/api/v1/properties",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/properties",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["properties:write"],
                rate_limit=50,
                documentation={
                    "summary": "Create property",
                    "description": "Create a new property",
                    "tags": ["Properties"]
                }
            ),
            APIEndpoint(
                path="/api/v1/properties/{property_id}",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/properties/{property_id}",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["properties:read"],
                enable_caching=True,
                documentation={
                    "summary": "Get property",
                    "description": "Retrieve a specific property by ID",
                    "tags": ["Properties"]
                }
            )
        ]
        
        # Tenants endpoints
        tenants_endpoints = [
            APIEndpoint(
                path="/api/v1/tenants",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/tenants",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["tenants:read"],
                rate_limit=100,
                enable_caching=True,
                documentation={
                    "summary": "List tenants",
                    "description": "Retrieve a paginated list of tenants",
                    "tags": ["Tenants"]
                }
            ),
            APIEndpoint(
                path="/api/v1/tenants",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/tenants",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["tenants:write"],
                rate_limit=50,
                documentation={
                    "summary": "Create tenant",
                    "description": "Create a new tenant",
                    "tags": ["Tenants"]
                }
            )
        ]
        
        # Payments endpoints
        payments_endpoints = [
            APIEndpoint(
                path="/api/v1/payments",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/payments",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["payments:read"],
                rate_limit=100,
                documentation={
                    "summary": "List payments",
                    "description": "Retrieve payment history",
                    "tags": ["Payments"]
                }
            ),
            APIEndpoint(
                path="/api/v1/payments",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/payments",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["payments:write"],
                rate_limit=25,
                documentation={
                    "summary": "Process payment",
                    "description": "Process a new payment",
                    "tags": ["Payments"]
                }
            )
        ]
        
        # Maintenance endpoints
        maintenance_endpoints = [
            APIEndpoint(
                path="/api/v1/maintenance",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/maintenance",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["maintenance:read"],
                rate_limit=100,
                documentation={
                    "summary": "List maintenance requests",
                    "description": "Retrieve maintenance request history",
                    "tags": ["Maintenance"]
                }
            ),
            APIEndpoint(
                path="/api/v1/maintenance",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/maintenance",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["maintenance:write"],
                rate_limit=50,
                documentation={
                    "summary": "Create maintenance request",
                    "description": "Create a new maintenance request",
                    "tags": ["Maintenance"]
                }
            )
        ]
        
        # Analytics endpoints
        analytics_endpoints = [
            APIEndpoint(
                path="/api/v1/analytics/dashboard",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/analytics/dashboard",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["analytics:read"],
                rate_limit=50,
                enable_caching=True,
                cache_ttl=600,
                documentation={
                    "summary": "Get dashboard analytics",
                    "description": "Retrieve dashboard analytics data",
                    "tags": ["Analytics"]
                }
            )
        ]
        
        # Register all endpoints
        all_endpoints = (
            auth_endpoints + properties_endpoints + tenants_endpoints + 
            payments_endpoints + maintenance_endpoints + analytics_endpoints
        )
        
        for endpoint in all_endpoints:
            self.gateway_service.register_endpoint(endpoint)
            logger.info(f"Registered endpoint: {endpoint.method.value} {endpoint.path}")
    
    def before_request(self):
        """Process request through API Gateway before handling"""
        # Skip gateway processing for certain paths
        skip_paths = [
            '/health',
            '/metrics',
            '/docs',
            '/static',
            '/favicon.ico'
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return
        
        # Check if this is an API endpoint
        if not request.path.startswith('/api/'):
            return
        
        # Store original request start time
        g.request_start_time = datetime.utcnow()
        
        # Extract tenant information
        tenant_id = self._extract_tenant_id()
        if tenant_id:
            g.tenant_id = tenant_id
            
            # Validate tenant
            is_valid, error_msg = self.enterprise_service.validate_tenant_request(
                tenant_id, self._get_request_type()
            )
            if not is_valid:
                return self._create_error_response(403, error_msg)
        
        # Process through gateway if it's a versioned API endpoint
        if self._is_gateway_endpoint():
            try:
                gateway_response = self.gateway_service.process_request(request)
                if gateway_response:
                    return gateway_response
            except Exception as e:
                logger.error(f"Gateway processing failed: {str(e)}")
                # Continue with normal processing as fallback
    
    def after_request(self, response: Response) -> Response:
        """Process response after handling"""
        # Skip for non-API endpoints
        if not request.path.startswith('/api/'):
            return response
        
        # Record metrics
        if hasattr(g, 'request_start_time'):
            processing_time = (datetime.utcnow() - g.request_start_time).total_seconds()
            
            # Create request metrics
            metrics = RequestMetrics(
                request_id=getattr(g, 'request_id', str(id(request))),
                timestamp=g.request_start_time,
                client_id=getattr(g, 'client_id', None),
                endpoint=request.path,
                method=request.method,
                version=getattr(g, 'api_version', 'v1'),
                response_status=response.status_code,
                response_time=processing_time,
                request_size=len(request.get_data()) if request.get_data() else 0,
                response_size=len(response.get_data()) if response.get_data() else 0,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                cache_hit=getattr(g, 'cache_hit', False),
                rate_limited=getattr(g, 'rate_limited', False)
            )
            
            self.monitoring_service.record_request(metrics)
            
            # Trigger webhooks for significant events
            if hasattr(g, 'tenant_id'):
                self._trigger_webhooks(g.tenant_id, metrics)
        
        # Add gateway headers
        response.headers['X-API-Gateway'] = 'EstateCore-Gateway-1.0'
        response.headers['X-Request-ID'] = getattr(g, 'request_id', str(id(request)))
        
        if hasattr(g, 'processing_time'):
            response.headers['X-Response-Time'] = f"{g.processing_time:.3f}s"
        
        return response
    
    def _extract_tenant_id(self) -> Optional[str]:
        """Extract tenant ID from request"""
        # Try custom domain first
        host = request.headers.get('Host', '')
        tenant = self.enterprise_service.tenant_manager.get_tenant_by_domain(host)
        if tenant:
            return tenant.tenant_id
        
        # Try header
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            return tenant_id
        
        # Try API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            is_valid, api_key_obj, _ = self.key_service.verify_api_key(api_key)
            if is_valid and api_key_obj:
                # Get tenant from client
                for client in self.gateway_service.clients.values():
                    if api_key in client.api_keys:
                        return self.enterprise_service.tenant_manager.get_tenant(
                            client.organization_id
                        )
        
        return None
    
    def _get_request_type(self) -> str:
        """Determine request type for tenant validation"""
        if 'webhook' in request.path.lower():
            return 'webhook'
        elif 'custom' in request.path.lower():
            return 'custom_endpoint'
        else:
            return 'api'
    
    def _is_gateway_endpoint(self) -> bool:
        """Check if endpoint should be processed by gateway"""
        # Check if endpoint is registered with gateway
        for endpoint_key, endpoint in self.gateway_service.endpoints.items():
            if endpoint.path in request.path and endpoint.method.value == request.method:
                return True
        return False
    
    def _trigger_webhooks(self, tenant_id: str, metrics: RequestMetrics):
        """Trigger webhooks for significant events"""
        webhook_events = []
        
        # API errors
        if metrics.response_status >= 400:
            webhook_events.append({
                'event': 'api.error',
                'data': {
                    'endpoint': metrics.endpoint,
                    'method': metrics.method,
                    'status_code': metrics.response_status,
                    'response_time': metrics.response_time,
                    'client_id': metrics.client_id,
                    'timestamp': metrics.timestamp.isoformat()
                }
            })
        
        # High response times
        if metrics.response_time > 2.0:
            webhook_events.append({
                'event': 'api.slow_response',
                'data': {
                    'endpoint': metrics.endpoint,
                    'response_time': metrics.response_time,
                    'threshold': 2.0,
                    'timestamp': metrics.timestamp.isoformat()
                }
            })
        
        # Rate limiting
        if metrics.rate_limited:
            webhook_events.append({
                'event': 'api.rate_limited',
                'data': {
                    'endpoint': metrics.endpoint,
                    'client_id': metrics.client_id,
                    'timestamp': metrics.timestamp.isoformat()
                }
            })
        
        # Trigger webhooks
        for event in webhook_events:
            self.enterprise_service.webhook_manager.trigger_webhook(
                tenant_id, event['event'], event['data']
            )
    
    def _create_error_response(self, status_code: int, message: str) -> Response:
        """Create standardized error response"""
        error_response = {
            'error': {
                'code': status_code,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        return jsonify(error_response), status_code

def create_api_gateway_routes(app: Flask):
    """Create API Gateway management routes"""
    
    gateway_service = get_api_gateway_service()
    key_service = get_api_key_service()
    oauth_service = get_oauth_service()
    monitoring_service = get_monitoring_service()
    documentation_service = get_documentation_service()
    enterprise_service = get_enterprise_service()
    
    # API Gateway management endpoints
    @app.route('/api/gateway/status', methods=['GET'])
    def gateway_status():
        """Get API Gateway status"""
        try:
            status = {
                'status': 'healthy',
                'version': '1.0.0',
                'timestamp': datetime.utcnow().isoformat(),
                'endpoints_registered': len(gateway_service.endpoints),
                'clients_registered': len(gateway_service.clients),
                'features': {
                    'authentication': True,
                    'rate_limiting': True,
                    'monitoring': True,
                    'caching': True,
                    'webhooks': True,
                    'multi_tenant': True
                }
            }
            return jsonify(status)
        except Exception as e:
            logger.error(f"Gateway status check failed: {str(e)}")
            return jsonify({'error': 'Status check failed'}), 500
    
    # API Key management endpoints
    @app.route('/api/gateway/keys', methods=['POST'])
    def create_api_key():
        """Create new API key"""
        try:
            data = request.get_json()
            
            # Create permissions
            permissions = APIKeyPermissions(
                endpoints=data.get('endpoints', []),
                methods=data.get('methods', ['GET', 'POST', 'PUT', 'DELETE']),
                rate_limits=data.get('rate_limits', {}),
                ip_whitelist=data.get('ip_whitelist', []),
                time_restrictions=data.get('time_restrictions', {}),
                data_access_level=data.get('data_access_level', 'standard')
            )
            
            # Create API key
            api_key, key_obj = key_service.create_api_key(
                client_id=data['client_id'],
                organization_id=data['organization_id'],
                name=data['name'],
                description=data.get('description', ''),
                key_type=APIKeyType(data.get('key_type', 'full_access')),
                permissions=permissions,
                expires_in_days=data.get('expires_in_days')
            )
            
            return jsonify({
                'api_key': api_key,
                'key_id': key_obj.key_id,
                'created_at': key_obj.created_at.isoformat(),
                'expires_at': key_obj.expires_at.isoformat() if key_obj.expires_at else None
            })
            
        except Exception as e:
            logger.error(f"API key creation failed: {str(e)}")
            return jsonify({'error': 'Failed to create API key'}), 500
    
    @app.route('/api/gateway/keys/<key_id>', methods=['DELETE'])
    def revoke_api_key(key_id):
        """Revoke API key"""
        try:
            success = key_service.revoke_api_key(key_id, "Revoked via API")
            if success:
                return jsonify({'message': 'API key revoked successfully'})
            else:
                return jsonify({'error': 'API key not found'}), 404
        except Exception as e:
            logger.error(f"API key revocation failed: {str(e)}")
            return jsonify({'error': 'Failed to revoke API key'}), 500
    
    # OAuth endpoints
    @app.route('/api/gateway/oauth/authorize', methods=['GET'])
    def oauth_authorize():
        """OAuth authorization endpoint"""
        try:
            client_id = request.args.get('client_id')
            redirect_uri = request.args.get('redirect_uri')
            scopes = request.args.get('scope', '').split()
            state = request.args.get('state')
            code_challenge = request.args.get('code_challenge')
            code_challenge_method = request.args.get('code_challenge_method')
            
            success, auth_url, error = oauth_service.create_authorization_url(
                client_id, redirect_uri, scopes, state, code_challenge, code_challenge_method
            )
            
            if success:
                return jsonify({'authorization_url': auth_url})
            else:
                return jsonify({'error': error}), 400
                
        except Exception as e:
            logger.error(f"OAuth authorization failed: {str(e)}")
            return jsonify({'error': 'Authorization failed'}), 500
    
    @app.route('/api/gateway/oauth/token', methods=['POST'])
    def oauth_token():
        """OAuth token endpoint"""
        try:
            data = request.get_json() or {}
            grant_type = data.get('grant_type')
            
            if grant_type == 'authorization_code':
                success, response, error = oauth_service.exchange_code_for_token(
                    data.get('code'),
                    data.get('client_id'),
                    data.get('client_secret'),
                    data.get('redirect_uri'),
                    data.get('code_verifier')
                )
            elif grant_type == 'client_credentials':
                success, response, error = oauth_service.client_credentials_grant(
                    data.get('client_id'),
                    data.get('client_secret'),
                    data.get('scope', '').split()
                )
            elif grant_type == 'refresh_token':
                success, response, error = oauth_service.refresh_access_token(
                    data.get('refresh_token'),
                    data.get('client_id'),
                    data.get('client_secret')
                )
            else:
                return jsonify({'error': 'Unsupported grant type'}), 400
            
            if success:
                return jsonify(response)
            else:
                return jsonify({'error': error}), 400
                
        except Exception as e:
            logger.error(f"OAuth token exchange failed: {str(e)}")
            return jsonify({'error': 'Token exchange failed'}), 500
    
    # Monitoring endpoints
    @app.route('/api/gateway/metrics', methods=['GET'])
    def get_metrics():
        """Get API Gateway metrics"""
        try:
            time_window = int(request.args.get('time_window', 3600))
            endpoint = request.args.get('endpoint')
            client_id = request.args.get('client_id')
            
            metrics = monitoring_service.get_performance_metrics(
                time_window=time_window,
                endpoint=endpoint,
                client_id=client_id
            )
            
            return jsonify({
                'metrics': metrics.__dict__,
                'time_window': time_window,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Metrics retrieval failed: {str(e)}")
            return jsonify({'error': 'Failed to retrieve metrics'}), 500
    
    @app.route('/api/gateway/analytics/dashboard', methods=['GET'])
    def get_analytics_dashboard():
        """Get comprehensive analytics dashboard"""
        try:
            dashboard_data = monitoring_service.get_dashboard_data()
            return jsonify(dashboard_data)
        except Exception as e:
            logger.error(f"Dashboard data retrieval failed: {str(e)}")
            return jsonify({'error': 'Failed to retrieve dashboard data'}), 500
    
    # Documentation endpoints
    @app.route('/api/gateway/docs/openapi.json', methods=['GET'])
    def get_openapi_spec():
        """Get OpenAPI specification"""
        try:
            spec = documentation_service.generate_documentation()
            return jsonify(spec)
        except Exception as e:
            logger.error(f"OpenAPI spec generation failed: {str(e)}")
            return jsonify({'error': 'Failed to generate documentation'}), 500
    
    @app.route('/api/gateway/docs', methods=['GET'])
    def get_api_explorer():
        """Get interactive API explorer"""
        try:
            explorer_html = documentation_service.generate_api_explorer()
            return Response(explorer_html, mimetype='text/html')
        except Exception as e:
            logger.error(f"API explorer generation failed: {str(e)}")
            return jsonify({'error': 'Failed to generate API explorer'}), 500
    
    @app.route('/api/gateway/docs/sdk/<language>', methods=['GET'])
    def get_sdk(language):
        """Generate SDK for specified language"""
        try:
            sdk_files = documentation_service.generate_sdk(language)
            return jsonify({
                'language': language,
                'files': sdk_files,
                'generated_at': datetime.utcnow().isoformat()
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"SDK generation failed: {str(e)}")
            return jsonify({'error': 'Failed to generate SDK'}), 500
    
    # Enterprise features endpoints
    @app.route('/api/gateway/tenants', methods=['POST'])
    def create_tenant():
        """Create new tenant"""
        try:
            data = request.get_json()
            
            from enterprise_features_service import TenantTier
            tenant = enterprise_service.tenant_manager.create_tenant(
                organization_id=data['organization_id'],
                tenant_name=data['tenant_name'],
                tier=TenantTier(data.get('tier', 'basic')),
                custom_domain=data.get('custom_domain')
            )
            
            return jsonify({
                'tenant_id': tenant.tenant_id,
                'tenant_name': tenant.tenant_name,
                'tier': tenant.tier.value,
                'created_at': tenant.created_at.isoformat(),
                'api_limits': tenant.api_limits,
                'enabled_features': tenant.enabled_features
            })
            
        except Exception as e:
            logger.error(f"Tenant creation failed: {str(e)}")
            return jsonify({'error': 'Failed to create tenant'}), 500
    
    @app.route('/api/gateway/tenants/<tenant_id>/webhooks', methods=['POST'])
    def create_webhook(tenant_id):
        """Create webhook endpoint for tenant"""
        try:
            data = request.get_json()
            
            webhook = enterprise_service.webhook_manager.create_webhook_endpoint(
                tenant_id=tenant_id,
                name=data['name'],
                url=data['url'],
                events=data.get('events', []),
                secret=data.get('secret')
            )
            
            return jsonify({
                'webhook_id': webhook.webhook_id,
                'name': webhook.name,
                'url': webhook.url,
                'events': webhook.events,
                'created_at': webhook.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Webhook creation failed: {str(e)}")
            return jsonify({'error': 'Failed to create webhook'}), 500
    
    @app.route('/api/gateway/tenants/<tenant_id>/dashboard', methods=['GET'])
    def get_tenant_dashboard(tenant_id):
        """Get enterprise dashboard for tenant"""
        try:
            dashboard_data = enterprise_service.get_enterprise_dashboard_data(tenant_id)
            return jsonify(dashboard_data)
        except Exception as e:
            logger.error(f"Tenant dashboard retrieval failed: {str(e)}")
            return jsonify({'error': 'Failed to retrieve tenant dashboard'}), 500
    
    # Health check endpoint
    @app.route('/api/gateway/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {
                'gateway': 'healthy',
                'authentication': 'healthy',
                'monitoring': 'healthy',
                'documentation': 'healthy',
                'enterprise': 'healthy'
            }
        })

def setup_api_gateway_integration(app: Flask):
    """Setup complete API Gateway integration"""
    
    # Initialize middleware
    middleware = APIGatewayMiddleware(app)
    
    # Create management routes
    create_api_gateway_routes(app)
    
    # Add CORS headers for API Gateway endpoints
    @app.after_request
    def add_cors_headers(response):
        if request.path.startswith('/api/gateway/'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, X-Tenant-ID'
        return response
    
    logger.info("API Gateway integration setup completed")
    
    return middleware