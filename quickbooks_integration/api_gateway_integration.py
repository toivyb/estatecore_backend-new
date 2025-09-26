"""
API Gateway Integration for QuickBooks Integration

Integrates QuickBooks functionality with the EstateCore API Gateway,
providing versioned endpoints, authentication, rate limiting, and monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, g

# Import API Gateway services
from api_gateway_service import (
    get_api_gateway_service, APIVersion, HTTPMethod, AuthenticationType,
    APIEndpoint, APIRequest
)
from api_key_management_service import get_api_key_service, APIKeyType, APIKeyPermissions
from api_monitoring_service import get_monitoring_service
from enterprise_features_service import get_enterprise_service

# Import QuickBooks services
from .quickbooks_integration_service import get_quickbooks_integration_service
from .quickbooks_routes import register_quickbooks_routes

logger = logging.getLogger(__name__)

class QuickBooksAPIGatewayIntegration:
    """
    Integrates QuickBooks functionality with the API Gateway
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.gateway_service = get_api_gateway_service()
        self.key_service = get_api_key_service()
        self.monitoring_service = get_monitoring_service()
        self.enterprise_service = get_enterprise_service()
        self.quickbooks_service = get_quickbooks_integration_service()
        
        # Register QuickBooks endpoints with API Gateway
        self._register_quickbooks_endpoints()
        
        # Setup billing integration hooks
        self._setup_billing_hooks()
        
        logger.info("QuickBooks API Gateway integration initialized")
    
    def _register_quickbooks_endpoints(self):
        """Register QuickBooks endpoints with the API Gateway"""
        
        # QuickBooks Connection Management
        connection_endpoints = [
            APIEndpoint(
                path="/api/v1/quickbooks/connect",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/connect",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:connect"],
                rate_limit=5,  # Limited for security
                documentation={
                    "summary": "Start QuickBooks OAuth connection",
                    "description": "Initiate OAuth flow to connect QuickBooks Online",
                    "tags": ["QuickBooks"],
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {
                        "200": {
                            "description": "OAuth URL generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "authorization_url": {"type": "string"},
                                            "state": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/status",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/status",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:read"],
                rate_limit=100,
                enable_caching=True,
                cache_ttl=300,
                documentation={
                    "summary": "Get QuickBooks connection status",
                    "description": "Retrieve current QuickBooks connection status",
                    "tags": ["QuickBooks"],
                    "responses": {
                        "200": {
                            "description": "Connection status retrieved",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "connected": {"type": "boolean"},
                                            "company_name": {"type": "string"},
                                            "last_sync": {"type": "string", "format": "date-time"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/disconnect",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/disconnect",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:connect"],
                rate_limit=10,
                documentation={
                    "summary": "Disconnect QuickBooks",
                    "description": "Disconnect and revoke QuickBooks Online connection",
                    "tags": ["QuickBooks"]
                }
            )
        ]
        
        # Data Synchronization Endpoints
        sync_endpoints = [
            APIEndpoint(
                path="/api/v1/quickbooks/sync",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/sync",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:sync"],
                rate_limit=10,  # Sync operations are expensive
                request_timeout=300,  # 5 minute timeout for sync
                documentation={
                    "summary": "Synchronize data with QuickBooks",
                    "description": "Sync data between EstateCore and QuickBooks Online",
                    "tags": ["QuickBooks", "Synchronization"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "direction": {
                                            "type": "string",
                                            "enum": ["to_qb", "from_qb", "both"],
                                            "default": "both"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/sync/entity",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/sync/entity",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:sync"],
                rate_limit=25,
                documentation={
                    "summary": "Sync specific entities",
                    "description": "Manually synchronize specific entity types",
                    "tags": ["QuickBooks", "Synchronization"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/sync/history",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/sync/history",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:read"],
                rate_limit=50,
                enable_caching=True,
                cache_ttl=60,
                documentation={
                    "summary": "Get synchronization history",
                    "description": "Retrieve history of sync operations",
                    "tags": ["QuickBooks", "Synchronization"]
                }
            )
        ]
        
        # Automation Endpoints
        automation_endpoints = [
            APIEndpoint(
                path="/api/v1/quickbooks/automation/enable",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/automation/enable",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:automation"],
                rate_limit=10,
                documentation={
                    "summary": "Enable automation workflows",
                    "description": "Enable automated QuickBooks workflows",
                    "tags": ["QuickBooks", "Automation"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/automation/execute",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/automation/execute",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:automation"],
                rate_limit=20,
                documentation={
                    "summary": "Execute workflow manually",
                    "description": "Manually trigger a specific workflow",
                    "tags": ["QuickBooks", "Automation"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/automation/status",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/automation/status",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:read"],
                rate_limit=50,
                enable_caching=True,
                cache_ttl=120,
                documentation={
                    "summary": "Get automation status",
                    "description": "Retrieve automation workflow status",
                    "tags": ["QuickBooks", "Automation"]
                }
            )
        ]
        
        # Data Quality and Reconciliation Endpoints
        quality_endpoints = [
            APIEndpoint(
                path="/api/v1/quickbooks/reconcile",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/reconcile",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:reconcile"],
                rate_limit=5,  # Reconciliation is resource intensive
                request_timeout=600,  # 10 minute timeout
                documentation={
                    "summary": "Perform data reconciliation",
                    "description": "Reconcile data between EstateCore and QuickBooks",
                    "tags": ["QuickBooks", "Data Quality"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/data-quality",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/data-quality",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:read"],
                rate_limit=30,
                enable_caching=True,
                cache_ttl=300,
                documentation={
                    "summary": "Get data quality score",
                    "description": "Retrieve data integrity and quality metrics",
                    "tags": ["QuickBooks", "Data Quality"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/audit-trail",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/audit-trail",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:audit"],
                rate_limit=25,
                documentation={
                    "summary": "Get audit trail",
                    "description": "Retrieve audit trail for QuickBooks operations",
                    "tags": ["QuickBooks", "Audit"]
                }
            )
        ]
        
        # Enterprise Features Endpoints
        enterprise_endpoints = [
            APIEndpoint(
                path="/api/v1/quickbooks/enterprise/portfolios",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/enterprise/portfolios",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:enterprise", "portfolios:write"],
                rate_limit=10,
                documentation={
                    "summary": "Create property portfolio",
                    "description": "Create multi-property portfolio for enterprise clients",
                    "tags": ["QuickBooks", "Enterprise"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/enterprise/portfolios",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/enterprise/portfolios",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:enterprise", "portfolios:read"],
                rate_limit=50,
                enable_caching=True,
                cache_ttl=300,
                documentation={
                    "summary": "List property portfolios",
                    "description": "Retrieve property portfolios for organization",
                    "tags": ["QuickBooks", "Enterprise"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/enterprise/reports",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/enterprise/reports",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:enterprise", "reports:write"],
                rate_limit=15,
                documentation={
                    "summary": "Create custom report",
                    "description": "Create custom financial report configuration",
                    "tags": ["QuickBooks", "Enterprise", "Reports"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/enterprise/reports/{report_id}/generate",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/enterprise/reports/{report_id}/generate",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:enterprise", "reports:read"],
                rate_limit=20,
                request_timeout=120,
                documentation={
                    "summary": "Generate custom report",
                    "description": "Generate and retrieve custom financial report",
                    "tags": ["QuickBooks", "Enterprise", "Reports"]
                }
            )
        ]
        
        # Health and Monitoring Endpoints
        monitoring_endpoints = [
            APIEndpoint(
                path="/api/v1/quickbooks/health",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/health",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:read"],
                rate_limit=100,
                enable_caching=True,
                cache_ttl=60,
                documentation={
                    "summary": "Get integration health",
                    "description": "Retrieve comprehensive QuickBooks integration health status",
                    "tags": ["QuickBooks", "Monitoring"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/summary",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/summary",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:read"],
                rate_limit=50,
                enable_caching=True,
                cache_ttl=300,
                documentation={
                    "summary": "Get integration summary",
                    "description": "Retrieve comprehensive integration status summary",
                    "tags": ["QuickBooks", "Monitoring"]
                }
            )
        ]
        
        # Configuration Endpoints
        config_endpoints = [
            APIEndpoint(
                path="/api/v1/quickbooks/config/sync",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/config/sync",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:config:read"],
                rate_limit=50,
                documentation={
                    "summary": "Get sync configuration",
                    "description": "Retrieve synchronization configuration",
                    "tags": ["QuickBooks", "Configuration"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/config/sync",
                method=HTTPMethod.PUT,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/config/sync",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:config:write"],
                rate_limit=10,
                documentation={
                    "summary": "Update sync configuration",
                    "description": "Update synchronization configuration settings",
                    "tags": ["QuickBooks", "Configuration"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/accounts",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/accounts",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:read"],
                rate_limit=25,
                enable_caching=True,
                cache_ttl=3600,  # Account data changes infrequently
                documentation={
                    "summary": "Get QuickBooks accounts",
                    "description": "Retrieve QuickBooks chart of accounts",
                    "tags": ["QuickBooks", "Configuration"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/mapping/properties",
                method=HTTPMethod.POST,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/mapping/properties",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:config:write"],
                rate_limit=20,
                documentation={
                    "summary": "Create property mapping",
                    "description": "Create account mapping for property",
                    "tags": ["QuickBooks", "Configuration"]
                }
            ),
            APIEndpoint(
                path="/api/v1/quickbooks/mapping/properties",
                method=HTTPMethod.GET,
                version=APIVersion.V1,
                upstream_url="http://localhost:5000/api/quickbooks/mapping/properties",
                authentication=AuthenticationType.API_KEY,
                required_scopes=["quickbooks:config:read"],
                rate_limit=50,
                enable_caching=True,
                cache_ttl=600,
                documentation={
                    "summary": "List property mappings",
                    "description": "Retrieve property account mappings",
                    "tags": ["QuickBooks", "Configuration"]
                }
            )
        ]
        
        # Register all endpoints
        all_endpoints = (
            connection_endpoints + sync_endpoints + automation_endpoints +
            quality_endpoints + enterprise_endpoints + monitoring_endpoints +
            config_endpoints
        )
        
        for endpoint in all_endpoints:
            self.gateway_service.register_endpoint(endpoint)
            logger.info(f"Registered QuickBooks endpoint: {endpoint.method.value} {endpoint.path}")
        
        logger.info(f"Registered {len(all_endpoints)} QuickBooks endpoints with API Gateway")
    
    def _setup_billing_hooks(self):
        """Setup hooks with the billing system for usage tracking"""
        
        # Hook into API request processing to track usage
        def track_quickbooks_usage(request_metrics):
            """Track QuickBooks API usage for billing"""
            try:
                # Only track QuickBooks endpoints
                if '/quickbooks/' in request_metrics.endpoint:
                    
                    # Extract organization ID from request
                    organization_id = getattr(g, 'organization_id', None)
                    if not organization_id:
                        return
                    
                    # Determine usage type based on endpoint
                    usage_type = self._determine_usage_type(request_metrics.endpoint)
                    
                    # Track usage in billing system
                    from billing_system.usage_tracker import get_usage_tracker
                    usage_tracker = get_usage_tracker()
                    
                    usage_tracker.track_usage(
                        customer_id=organization_id,
                        subscription_id=f"qb_sub_{organization_id}",
                        metric_name=f"quickbooks_{usage_type}",
                        value=1,
                        metadata={
                            'endpoint': request_metrics.endpoint,
                            'method': request_metrics.method,
                            'response_status': request_metrics.response_status,
                            'response_time': request_metrics.response_time,
                            'timestamp': request_metrics.timestamp.isoformat()
                        }
                    )
                    
                    logger.debug(f"Tracked QuickBooks usage: {usage_type} for {organization_id}")
                    
            except Exception as e:
                logger.error(f"Failed to track QuickBooks usage: {e}")
        
        # Register usage tracking hook with monitoring service
        self.monitoring_service.add_hook('request_completed', track_quickbooks_usage)
        
        # Setup quota management
        def check_quickbooks_quota(client_id, endpoint):
            """Check if client has quota for QuickBooks operations"""
            try:
                if '/quickbooks/' not in endpoint:
                    return True, None
                
                # Get client's subscription from billing system
                from billing_system.subscription_manager import get_subscription_manager
                subscription_manager = get_subscription_manager()
                
                # Find subscription for client
                subscription = subscription_manager.get_client_subscription(client_id)
                if not subscription:
                    return False, "No active subscription found"
                
                # Check QuickBooks feature access
                if not subscription.has_feature('quickbooks_integration'):
                    return False, "QuickBooks integration not included in subscription"
                
                # Check usage limits
                usage_type = self._determine_usage_type(endpoint)
                monthly_limit = subscription.get_limit(f"quickbooks_{usage_type}_monthly")
                
                if monthly_limit:
                    # Get current usage
                    from billing_system.usage_tracker import get_usage_tracker
                    usage_tracker = get_usage_tracker()
                    
                    current_usage = usage_tracker.get_current_usage(
                        client_id, subscription.subscription_id, f"quickbooks_{usage_type}"
                    )
                    
                    if current_usage >= monthly_limit:
                        return False, f"Monthly quota exceeded for {usage_type}"
                
                return True, None
                
            except Exception as e:
                logger.error(f"Quota check failed: {e}")
                return True, None  # Allow request if quota check fails
        
        # Register quota check with gateway
        self.gateway_service.add_quota_checker('quickbooks', check_quickbooks_quota)
        
        logger.info("QuickBooks billing hooks configured")
    
    def _determine_usage_type(self, endpoint: str) -> str:
        """Determine usage type from endpoint"""
        if '/sync' in endpoint:
            return 'sync_operations'
        elif '/automation' in endpoint:
            return 'automation_executions'
        elif '/reconcile' in endpoint:
            return 'reconciliation_runs'
        elif '/enterprise' in endpoint:
            return 'enterprise_features'
        elif '/reports' in endpoint:
            return 'report_generations'
        else:
            return 'api_calls'
    
    def create_quickbooks_api_key(self, organization_id: str, client_id: str, 
                                 tier: str = "professional") -> Dict[str, Any]:
        """Create API key with QuickBooks permissions"""
        try:
            # Define permissions based on tier
            permissions_by_tier = {
                "basic": {
                    "endpoints": [
                        "/api/v1/quickbooks/status",
                        "/api/v1/quickbooks/connect",
                        "/api/v1/quickbooks/sync/history"
                    ],
                    "methods": ["GET", "POST"],
                    "rate_limits": {
                        "requests_per_minute": 30,
                        "requests_per_hour": 500
                    },
                    "scopes": ["quickbooks:read", "quickbooks:connect"]
                },
                "professional": {
                    "endpoints": [
                        "/api/v1/quickbooks/*"
                    ],
                    "methods": ["GET", "POST", "PUT"],
                    "rate_limits": {
                        "requests_per_minute": 100,
                        "requests_per_hour": 2000
                    },
                    "scopes": [
                        "quickbooks:read", "quickbooks:connect", 
                        "quickbooks:sync", "quickbooks:automation"
                    ]
                },
                "enterprise": {
                    "endpoints": [
                        "/api/v1/quickbooks/*"
                    ],
                    "methods": ["GET", "POST", "PUT", "DELETE"],
                    "rate_limits": {
                        "requests_per_minute": 200,
                        "requests_per_hour": 5000
                    },
                    "scopes": [
                        "quickbooks:read", "quickbooks:connect", "quickbooks:sync",
                        "quickbooks:automation", "quickbooks:enterprise", 
                        "quickbooks:reconcile", "quickbooks:audit",
                        "quickbooks:config:read", "quickbooks:config:write"
                    ]
                }
            }
            
            tier_config = permissions_by_tier.get(tier, permissions_by_tier["professional"])
            
            # Create permissions
            permissions = APIKeyPermissions(
                endpoints=tier_config["endpoints"],
                methods=tier_config["methods"],
                rate_limits=tier_config["rate_limits"],
                scopes=tier_config["scopes"]
            )
            
            # Create API key
            api_key, key_obj = self.key_service.create_api_key(
                client_id=client_id,
                organization_id=organization_id,
                name=f"QuickBooks Integration - {tier.title()}",
                description=f"API key for QuickBooks integration ({tier} tier)",
                key_type=APIKeyType.INTEGRATION_SPECIFIC,
                permissions=permissions,
                expires_in_days=365  # 1 year expiration
            )
            
            return {
                "success": True,
                "api_key": api_key,
                "key_id": key_obj.key_id,
                "tier": tier,
                "permissions": tier_config,
                "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create QuickBooks API key: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_quickbooks_analytics(self, organization_id: str, 
                                time_window: int = 3600) -> Dict[str, Any]:
        """Get QuickBooks-specific analytics"""
        try:
            # Get metrics for QuickBooks endpoints
            quickbooks_metrics = self.monitoring_service.get_endpoint_metrics(
                endpoint_pattern="/api/*/quickbooks/*",
                time_window=time_window,
                client_filter={"organization_id": organization_id}
            )
            
            # Get usage data from billing system
            from billing_system.usage_tracker import get_usage_tracker
            usage_tracker = get_usage_tracker()
            
            usage_summary = usage_tracker.get_usage_summary(
                customer_id=organization_id,
                subscription_id=f"qb_sub_{organization_id}"
            )
            
            # Get health status
            health = self.quickbooks_service.get_integration_health(organization_id)
            
            return {
                "organization_id": organization_id,
                "time_window": time_window,
                "api_metrics": {
                    "total_requests": quickbooks_metrics.get("total_requests", 0),
                    "successful_requests": quickbooks_metrics.get("successful_requests", 0),
                    "error_rate": quickbooks_metrics.get("error_rate", 0),
                    "average_response_time": quickbooks_metrics.get("avg_response_time", 0),
                    "requests_per_second": quickbooks_metrics.get("requests_per_second", 0)
                },
                "usage_summary": usage_summary,
                "health_status": {
                    "overall_status": health.status.value,
                    "data_quality_score": health.data_quality.get("integrity_score", 0),
                    "connection_health": health.connection_health.get("status", "unknown"),
                    "automation_enabled": health.automation_health.get("automation_enabled", False)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get QuickBooks analytics: {e}")
            return {
                "error": str(e),
                "organization_id": organization_id
            }

def setup_quickbooks_api_gateway_integration(app: Flask) -> QuickBooksAPIGatewayIntegration:
    """Setup QuickBooks integration with API Gateway"""
    
    # Register QuickBooks routes first
    register_quickbooks_routes(app)
    
    # Create and configure the integration
    integration = QuickBooksAPIGatewayIntegration(app)
    
    # Add QuickBooks-specific middleware
    @app.before_request
    def quickbooks_request_middleware():
        """Handle QuickBooks-specific request processing"""
        if request.path.startswith('/api/') and '/quickbooks/' in request.path:
            # Extract organization ID
            organization_id = request.headers.get('X-Organization-ID')
            if not organization_id:
                # Try to get from API key
                api_key = request.headers.get('X-API-Key')
                if api_key:
                    is_valid, key_obj, _ = integration.key_service.verify_api_key(api_key)
                    if is_valid and key_obj:
                        organization_id = key_obj.organization_id
            
            if organization_id:
                g.organization_id = organization_id
                
                # Check QuickBooks-specific quotas and limits
                quota_ok, quota_error = integration._check_quickbooks_quota(
                    organization_id, request.path
                )
                
                if not quota_ok:
                    return jsonify({
                        'error': 'Quota exceeded',
                        'message': quota_error,
                        'retry_after': 3600  # 1 hour
                    }), 429
    
    def _check_quickbooks_quota(self, organization_id: str, endpoint: str) -> tuple[bool, Optional[str]]:
        """Check QuickBooks-specific quotas"""
        try:
            # This would integrate with the billing system to check quotas
            # For now, we'll implement basic checks
            
            # Check if organization has active QuickBooks subscription
            connection = self.quickbooks_service.oauth_service.get_organization_connection(organization_id)
            if not connection:
                return False, "QuickBooks not connected"
            
            # Check daily API limits (example)
            daily_limit = 1000  # This would come from subscription
            
            # Get today's usage
            from datetime import datetime, timedelta
            today = datetime.now().date()
            usage_count = self.monitoring_service.get_request_count(
                organization_id=organization_id,
                endpoint_pattern="/api/*/quickbooks/*",
                start_time=datetime.combine(today, datetime.min.time()),
                end_time=datetime.combine(today, datetime.max.time())
            )
            
            if usage_count >= daily_limit:
                return False, f"Daily API limit ({daily_limit}) exceeded"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Quota check failed: {e}")
            return True, None  # Allow on error
    
    # Bind the method to the integration instance
    integration._check_quickbooks_quota = _check_quickbooks_quota.__get__(integration)
    
    logger.info("QuickBooks API Gateway integration setup completed")
    
    return integration