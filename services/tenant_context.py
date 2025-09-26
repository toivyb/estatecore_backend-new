"""
Tenant context management for multi-tenant architecture.
Provides thread-local tenant context and utilities for tenant-aware operations.
"""
import threading
from typing import Optional, Dict, Any
from flask import g, request, current_app
from functools import wraps
import re
from urllib.parse import urlparse

# Thread-local storage for tenant context
_tenant_context = threading.local()

class TenantContext:
    """
    Manages tenant context throughout the request lifecycle.
    Provides utilities for tenant resolution, data isolation, and configuration access.
    """
    
    def __init__(self, tenant=None, organization=None):
        self.tenant = tenant
        self.organization = organization
        self._cache = {}
    
    @property
    def tenant_id(self) -> Optional[int]:
        """Get current tenant ID."""
        return self.tenant.id if self.tenant else None
    
    @property
    def organization_id(self) -> Optional[int]:
        """Get current organization ID."""
        return self.organization.id if self.organization else None
    
    @property
    def tenant_key(self) -> Optional[str]:
        """Get current tenant key."""
        return self.tenant.tenant_key if self.tenant else None
    
    @property
    def subdomain(self) -> Optional[str]:
        """Get current tenant subdomain."""
        return self.tenant.subdomain if self.tenant else None
    
    @property
    def custom_domain(self) -> Optional[str]:
        """Get current tenant custom domain."""
        return self.tenant.custom_domain if self.tenant else None
    
    @property
    def primary_domain(self) -> Optional[str]:
        """Get primary domain for the current tenant."""
        return self.tenant.primary_domain if self.tenant else None
    
    @property
    def is_active(self) -> bool:
        """Check if current tenant is active."""
        return self.tenant.is_active if self.tenant else False
    
    def get_brand_setting(self, key: str, default: Any = None) -> Any:
        """Get tenant-specific brand setting."""
        if not self.tenant:
            return default
        return self.tenant.get_brand_setting(key, default)
    
    def get_feature_flag(self, feature: str, default: bool = False) -> bool:
        """Check if feature is enabled for current tenant."""
        if not self.tenant:
            return default
        return self.tenant.get_feature_flag(feature, default)
    
    def get_resource_quota(self, resource: str) -> Optional[int]:
        """Get resource quota for current tenant."""
        if not self.tenant:
            return None
        return self.tenant.get_resource_quota(resource)
    
    def get_api_config(self, key: str, default: Any = None) -> Any:
        """Get tenant-specific API configuration."""
        if not self.tenant or not self.tenant.api_config:
            return default
        return self.tenant.api_config.get(key, default)
    
    def get_integration_config(self, integration: str, key: str = None, default: Any = None) -> Any:
        """Get tenant-specific integration configuration."""
        if not self.tenant or not self.tenant.integration_config:
            return default
        
        integration_conf = self.tenant.integration_config.get(integration, {})
        if key is None:
            return integration_conf
        return integration_conf.get(key, default)
    
    def cache_get(self, key: str) -> Any:
        """Get value from tenant context cache."""
        return self._cache.get(key)
    
    def cache_set(self, key: str, value: Any) -> None:
        """Set value in tenant context cache."""
        self._cache[key] = value
    
    def cache_clear(self) -> None:
        """Clear tenant context cache."""
        self._cache.clear()

def get_current_tenant_context() -> Optional[TenantContext]:
    """Get current tenant context from thread-local storage."""
    return getattr(_tenant_context, 'current', None)

def set_tenant_context(context: TenantContext) -> None:
    """Set tenant context in thread-local storage."""
    _tenant_context.current = context
    
    # Also set in Flask's g for easy access in templates
    if hasattr(g, '__dict__'):
        g.tenant_context = context

def clear_tenant_context() -> None:
    """Clear tenant context from thread-local storage."""
    _tenant_context.current = None
    if hasattr(g, 'tenant_context'):
        delattr(g, 'tenant_context')

def get_tenant_id() -> Optional[int]:
    """Get current tenant ID."""
    context = get_current_tenant_context()
    return context.tenant_id if context else None

def get_organization_id() -> Optional[int]:
    """Get current organization ID."""
    context = get_current_tenant_context()
    return context.organization_id if context else None

def require_tenant_context(f):
    """Decorator that ensures tenant context is available."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        context = get_current_tenant_context()
        if not context or not context.tenant:
            from flask import abort
            abort(400, description="Tenant context is required but not available")
        return f(*args, **kwargs)
    return decorated_function

def tenant_aware_query(query, model_class):
    """
    Make a SQLAlchemy query tenant-aware by filtering by organization_id.
    
    Args:
        query: SQLAlchemy query object
        model_class: The model class being queried
        
    Returns:
        Modified query with tenant filtering
    """
    organization_id = get_organization_id()
    if not organization_id:
        # If no tenant context, return empty result
        return query.filter(False)
    
    # Check if model has organization_id column
    if hasattr(model_class, 'organization_id'):
        return query.filter(model_class.organization_id == organization_id)
    
    # For models that might be related to organization through relationships
    # This would need to be customized based on your specific model relationships
    return query

class TenantResolver:
    """
    Resolves tenant information from various sources (domain, subdomain, headers, etc.)
    """
    
    @staticmethod
    def resolve_from_domain(domain: str) -> Optional[Dict[str, Any]]:
        """
        Resolve tenant from domain name.
        
        Args:
            domain: The domain name to resolve
            
        Returns:
            Dict with tenant information or None if not found
        """
        from models.white_label_tenant import WhiteLabelTenant, TenantDomain
        
        # Clean domain (remove port, protocol, etc.)
        domain = TenantResolver._clean_domain(domain)
        
        # First, check for exact custom domain match
        tenant_domain = TenantDomain.query.filter_by(
            domain=domain,
            status='verified'
        ).first()
        
        if tenant_domain:
            tenant = WhiteLabelTenant.query.get(tenant_domain.tenant_id)
            if tenant and tenant.is_active:
                return {
                    'tenant': tenant,
                    'organization': tenant.organization,
                    'domain_type': 'custom',
                    'domain': domain
                }
        
        # Check for subdomain pattern (subdomain.estatecore.com)
        if domain.endswith('.estatecore.com'):
            subdomain = domain.replace('.estatecore.com', '')
            tenant = WhiteLabelTenant.query.filter_by(
                subdomain=subdomain,
                status='active'
            ).first()
            
            if tenant:
                return {
                    'tenant': tenant,
                    'organization': tenant.organization,
                    'domain_type': 'subdomain',
                    'domain': domain
                }
        
        return None
    
    @staticmethod
    def resolve_from_tenant_key(tenant_key: str) -> Optional[Dict[str, Any]]:
        """
        Resolve tenant from tenant key.
        
        Args:
            tenant_key: The tenant key identifier
            
        Returns:
            Dict with tenant information or None if not found
        """
        from models.white_label_tenant import WhiteLabelTenant
        
        tenant = WhiteLabelTenant.query.filter_by(
            tenant_key=tenant_key,
            status='active'
        ).first()
        
        if tenant:
            return {
                'tenant': tenant,
                'organization': tenant.organization,
                'domain_type': 'key',
                'tenant_key': tenant_key
            }
        
        return None
    
    @staticmethod
    def resolve_from_api_key(api_key: str) -> Optional[Dict[str, Any]]:
        """
        Resolve tenant from API key (for partner API access).
        
        Args:
            api_key: The API key
            
        Returns:
            Dict with tenant information or None if not found
        """
        from models.white_label_tenant import Partner
        
        partner = Partner.query.filter_by(
            api_key=api_key,
            is_active=True
        ).first()
        
        if partner:
            # For partner API access, we might need additional tenant identification
            # This could be passed as a header or parameter
            return {
                'partner': partner,
                'domain_type': 'api'
            }
        
        return None
    
    @staticmethod
    def resolve_from_request(request_obj=None) -> Optional[Dict[str, Any]]:
        """
        Resolve tenant information from Flask request object.
        
        Args:
            request_obj: Flask request object (uses current request if None)
            
        Returns:
            Dict with tenant information or None if not found
        """
        if request_obj is None:
            request_obj = request
        
        # Check for tenant key in headers (for API access)
        tenant_key = request_obj.headers.get('X-Tenant-Key')
        if tenant_key:
            return TenantResolver.resolve_from_tenant_key(tenant_key)
        
        # Check for API key in headers (for partner access)
        api_key = request_obj.headers.get('X-API-Key')
        if api_key:
            partner_info = TenantResolver.resolve_from_api_key(api_key)
            if partner_info:
                # For partner API, check for tenant specification
                tenant_id = request_obj.headers.get('X-Tenant-ID')
                if tenant_id:
                    from models.white_label_tenant import WhiteLabelTenant
                    tenant = WhiteLabelTenant.query.filter_by(
                        id=tenant_id,
                        partner_id=partner_info['partner'].id,
                        status='active'
                    ).first()
                    if tenant:
                        partner_info.update({
                            'tenant': tenant,
                            'organization': tenant.organization
                        })
                return partner_info
        
        # Resolve from domain/host header
        host = request_obj.headers.get('Host')
        if host:
            return TenantResolver.resolve_from_domain(host)
        
        return None
    
    @staticmethod
    def _clean_domain(domain: str) -> str:
        """Clean domain string by removing port, protocol, etc."""
        # Remove protocol if present
        if '://' in domain:
            domain = domain.split('://', 1)[1]
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':', 1)[0]
        
        # Remove trailing slash
        domain = domain.rstrip('/')
        
        return domain.lower()

def initialize_tenant_context_from_request():
    """
    Initialize tenant context from current Flask request.
    This should be called early in the request lifecycle.
    """
    try:
        tenant_info = TenantResolver.resolve_from_request()
        if tenant_info:
            context = TenantContext(
                tenant=tenant_info.get('tenant'),
                organization=tenant_info.get('organization')
            )
            set_tenant_context(context)
            
            # Log tenant resolution for debugging
            current_app.logger.debug(f"Tenant resolved: {context.tenant_key} ({context.primary_domain})")
        else:
            # No tenant found - this might be okay for some endpoints
            current_app.logger.debug("No tenant context resolved from request")
            
    except Exception as e:
        current_app.logger.error(f"Error initializing tenant context: {str(e)}")
        # Don't fail the request, just log the error
        pass

# Template functions for use in Jinja2 templates
def get_tenant_brand_setting(key, default=None):
    """Template function to get tenant brand setting."""
    context = get_current_tenant_context()
    return context.get_brand_setting(key, default) if context else default

def tenant_has_feature(feature):
    """Template function to check if tenant has feature enabled."""
    context = get_current_tenant_context()
    return context.get_feature_flag(feature, False) if context else False

def get_tenant_api_config(key, default=None):
    """Template function to get tenant API config."""
    context = get_current_tenant_context()
    return context.get_api_config(key, default) if context else default

# Register template functions
def register_tenant_template_functions(app):
    """Register tenant-related functions for use in templates."""
    app.jinja_env.globals.update(
        get_tenant_brand_setting=get_tenant_brand_setting,
        tenant_has_feature=tenant_has_feature,
        get_tenant_api_config=get_tenant_api_config
    )