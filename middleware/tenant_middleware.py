"""
Multi-tenant middleware for automatic tenant resolution and context management.
Handles subdomain routing, custom domains, and tenant-specific configuration.
"""
from flask import request, g, current_app, abort, jsonify
from functools import wraps
import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from services.tenant_context import (
    TenantResolver, 
    TenantContext, 
    set_tenant_context, 
    clear_tenant_context,
    get_current_tenant_context
)

class TenantMiddleware:
    """
    WSGI middleware for multi-tenant request processing.
    Automatically resolves tenant context and applies tenant-specific configurations.
    """
    
    def __init__(self, app, config=None):
        self.app = app
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            'require_tenant_for_api': True,
            'require_tenant_for_frontend': False,
            'tenant_header_name': 'X-Tenant-Key',
            'partner_header_name': 'X-API-Key',
            'allowed_no_tenant_paths': [
                '/health',
                '/api/health',
                '/api/system',
                '/admin',
                '/static',
                '/favicon.ico'
            ],
            'subdomain_pattern': r'^([a-z0-9][a-z0-9\-]*[a-z0-9])\.estatecore\.com$',
            'custom_domain_validation': True,
            'enforce_ssl_custom_domains': True
        }
        
        # Merge configuration
        self.config = {**self.default_config, **self.config}
        
        # Register before request handler
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        
        # Register error handlers
        self._register_error_handlers()
    
    def _before_request(self):
        """Process request before route handler."""
        try:
            # Clear any existing tenant context
            clear_tenant_context()
            
            # Skip tenant resolution for certain paths
            if self._should_skip_tenant_resolution():
                return
            
            # Resolve tenant context
            tenant_info = TenantResolver.resolve_from_request()
            
            if tenant_info:
                # Validate tenant and set context
                if self._validate_tenant_access(tenant_info):
                    context = TenantContext(
                        tenant=tenant_info.get('tenant'),
                        organization=tenant_info.get('organization')
                    )
                    set_tenant_context(context)
                    
                    # Log successful tenant resolution
                    current_app.logger.info(
                        f"Tenant resolved: {context.tenant_key} "
                        f"from {tenant_info.get('domain_type', 'unknown')} "
                        f"({request.url})"
                    )
                    
                    # Apply tenant-specific configurations
                    self._apply_tenant_configurations(context)
                else:
                    # Tenant validation failed
                    abort(403, description="Tenant access denied")
            else:
                # No tenant found
                if self._is_tenant_required():
                    abort(400, description="Tenant identification required")
                else:
                    current_app.logger.debug("No tenant context - proceeding without tenant")
                    
        except Exception as e:
            current_app.logger.error(f"Error in tenant middleware: {str(e)}")
            # Decide whether to fail the request or continue
            if self._is_tenant_required():
                abort(500, description="Tenant resolution error")
    
    def _after_request(self, response):
        """Process response after route handler."""
        try:
            context = get_current_tenant_context()
            if context:
                # Add tenant-specific headers
                self._add_tenant_headers(response, context)
                
                # Log tenant usage metrics
                self._log_tenant_usage(context)
                
        except Exception as e:
            current_app.logger.error(f"Error in tenant middleware after_request: {str(e)}")
        
        return response
    
    def _should_skip_tenant_resolution(self) -> bool:
        """Check if tenant resolution should be skipped for this request."""
        path = request.path
        
        # Skip for allowed paths
        for allowed_path in self.config['allowed_no_tenant_paths']:
            if path.startswith(allowed_path):
                return True
        
        # Skip for static files
        if path.startswith('/static/') or path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
            return True
        
        return False
    
    def _is_tenant_required(self) -> bool:
        """Check if tenant context is required for the current request."""
        path = request.path
        
        # API endpoints typically require tenant context
        if path.startswith('/api/') and self.config['require_tenant_for_api']:
            # Except for system/admin endpoints
            if not (path.startswith('/api/admin/') or path.startswith('/api/system/')):
                return True
        
        # Frontend pages might require tenant context
        if self.config['require_tenant_for_frontend']:
            return True
        
        return False
    
    def _validate_tenant_access(self, tenant_info: Dict[str, Any]) -> bool:
        """Validate tenant access and status."""
        tenant = tenant_info.get('tenant')
        
        if not tenant:
            return False
        
        # Check if tenant is active
        if not tenant.is_active:
            current_app.logger.warning(f"Inactive tenant access attempt: {tenant.tenant_key}")
            return False
        
        # Validate SSL for custom domains if enforced
        if (self.config['enforce_ssl_custom_domains'] and 
            tenant.has_custom_domain and 
            not request.is_secure):
            current_app.logger.warning(f"Non-SSL access to custom domain: {tenant.custom_domain}")
            return False
        
        # Additional validation can be added here
        # e.g., IP restrictions, rate limiting, etc.
        
        return True
    
    def _apply_tenant_configurations(self, context: TenantContext):
        """Apply tenant-specific configurations to the request."""
        # Set CORS origins based on tenant configuration
        tenant_cors_origins = context.get_api_config('cors_origins')
        if tenant_cors_origins:
            # This would need to be integrated with Flask-CORS
            g.tenant_cors_origins = tenant_cors_origins
        
        # Set rate limiting based on tenant plan
        tenant_rate_limits = context.get_api_config('rate_limits')
        if tenant_rate_limits:
            g.tenant_rate_limits = tenant_rate_limits
        
        # Apply tenant-specific security settings
        security_config = context.tenant.security_config if context.tenant else {}
        if security_config:
            g.tenant_security_config = security_config
    
    def _add_tenant_headers(self, response, context: TenantContext):
        """Add tenant-specific headers to the response."""
        if context.tenant:
            response.headers['X-Tenant-ID'] = str(context.tenant_id)
            response.headers['X-Tenant-Key'] = context.tenant_key
            
            # Add branding headers for frontend
            brand_name = context.get_brand_setting('name')
            if brand_name:
                response.headers['X-Brand-Name'] = brand_name
    
    def _log_tenant_usage(self, context: TenantContext):
        """Log tenant usage metrics for billing and monitoring."""
        if not context.tenant:
            return
        
        try:
            # Import here to avoid circular imports
            from services.tenant_monitoring import TenantMonitoringService
            
            monitoring_service = TenantMonitoringService()
            monitoring_service.log_api_request(
                tenant_id=context.tenant_id,
                endpoint=request.endpoint,
                method=request.method,
                response_status=200  # We don't have the response status here
            )
        except Exception as e:
            current_app.logger.error(f"Error logging tenant usage: {str(e)}")
    
    def _register_error_handlers(self):
        """Register tenant-specific error handlers."""
        
        @self.app.errorhandler(400)
        def handle_bad_request(error):
            return jsonify({
                'error': 'Bad Request',
                'message': str(error.description) if error.description else 'Invalid request'
            }), 400
        
        @self.app.errorhandler(403)
        def handle_forbidden(error):
            return jsonify({
                'error': 'Forbidden',
                'message': str(error.description) if error.description else 'Access denied'
            }), 403
        
        @self.app.errorhandler(404)
        def handle_not_found(error):
            # Check if we have tenant context for custom 404 pages
            context = get_current_tenant_context()
            if context:
                custom_404 = context.get_brand_setting('custom_404_page')
                if custom_404:
                    return jsonify({
                        'error': 'Not Found',
                        'message': 'The requested resource was not found',
                        'custom_page': custom_404
                    }), 404
            
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found'
            }), 404

def require_tenant(f):
    """
    Decorator to require tenant context for a route.
    Use this on routes that absolutely need tenant context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        context = get_current_tenant_context()
        if not context or not context.tenant:
            abort(400, description="Tenant context is required for this endpoint")
        return f(*args, **kwargs)
    return decorated_function

def require_active_tenant(f):
    """
    Decorator to require an active tenant for a route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        context = get_current_tenant_context()
        if not context or not context.tenant:
            abort(400, description="Tenant context is required for this endpoint")
        
        if not context.is_active:
            abort(403, description="Tenant is not active")
        
        return f(*args, **kwargs)
    return decorated_function

def require_tenant_feature(feature_name: str):
    """
    Decorator to require a specific feature to be enabled for the tenant.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = get_current_tenant_context()
            if not context or not context.tenant:
                abort(400, description="Tenant context is required for this endpoint")
            
            if not context.get_feature_flag(feature_name, False):
                abort(403, description=f"Feature '{feature_name}' is not enabled for this tenant")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def tenant_resource_limit(resource_type: str, cost: int = 1):
    """
    Decorator to enforce tenant resource limits.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = get_current_tenant_context()
            if not context or not context.tenant:
                abort(400, description="Tenant context is required for this endpoint")
            
            # Check resource quota
            quota = context.get_resource_quota(resource_type)
            current_usage = context.get_current_usage(resource_type)
            
            if quota is not None and current_usage + cost > quota:
                abort(429, description=f"Resource limit exceeded for {resource_type}")
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Update usage after successful execution
            try:
                context.tenant.update_usage_metric(resource_type, current_usage + cost)
                from models.white_label_tenant import db
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Error updating usage metric: {str(e)}")
            
            return result
        return decorated_function
    return decorator

class TenantAwareRoute:
    """
    Class-based view helper for tenant-aware routes.
    """
    
    def __init__(self, require_tenant=True, require_active=True, required_features=None):
        self.require_tenant = require_tenant
        self.require_active = require_active
        self.required_features = required_features or []
    
    def __call__(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            context = get_current_tenant_context()
            
            if self.require_tenant and (not context or not context.tenant):
                abort(400, description="Tenant context is required for this endpoint")
            
            if self.require_active and context and not context.is_active:
                abort(403, description="Tenant is not active")
            
            for feature in self.required_features:
                if context and not context.get_feature_flag(feature, False):
                    abort(403, description=f"Feature '{feature}' is not enabled for this tenant")
            
            return f(*args, **kwargs)
        return decorated_function

def setup_tenant_middleware(app, config=None):
    """
    Setup tenant middleware for the Flask application.
    
    Args:
        app: Flask application instance
        config: Optional configuration dictionary
    """
    middleware = TenantMiddleware(app, config)
    
    # Register template functions
    from services.tenant_context import register_tenant_template_functions
    register_tenant_template_functions(app)
    
    app.logger.info("Tenant middleware initialized")
    
    return middleware