"""
Feature flag management system for tenant-specific capabilities.
Supports dynamic feature toggling, A/B testing, and gradual rollouts.
"""
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from flask import current_app
import json

from services.tenant_context import get_current_tenant_context

class FeatureType(Enum):
    """Types of feature flags."""
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"

class RolloutStrategy(Enum):
    """Feature rollout strategies."""
    ALL_OR_NOTHING = "all_or_nothing"
    PERCENTAGE = "percentage"
    GRADUAL = "gradual"
    WHITELIST = "whitelist"
    EXPERIMENT = "experiment"

@dataclass
class FeatureFlag:
    """Feature flag configuration."""
    key: str
    name: str
    description: str
    feature_type: FeatureType
    default_value: Any
    enabled: bool = True
    rollout_strategy: RolloutStrategy = RolloutStrategy.ALL_OR_NOTHING
    rollout_config: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.rollout_config is None:
            self.rollout_config = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class FeatureFlagService:
    """
    Service for managing feature flags and tenant-specific feature availability.
    """
    
    def __init__(self):
        self.feature_registry = {}
        self._register_default_features()
    
    def _register_default_features(self):
        """Register default EstateCore features."""
        default_features = [
            # Core Features
            FeatureFlag(
                key="ai_analytics",
                name="AI Analytics",
                description="Advanced AI-powered analytics and insights",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            FeatureFlag(
                key="predictive_maintenance",
                name="Predictive Maintenance",
                description="AI-powered maintenance prediction and scheduling",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            FeatureFlag(
                key="lpr_integration",
                name="License Plate Recognition",
                description="License plate recognition for access control",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            FeatureFlag(
                key="video_inspection",
                name="Video Inspection",
                description="AI-powered video property inspection",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            FeatureFlag(
                key="advanced_reporting",
                name="Advanced Reporting",
                description="Comprehensive reporting and dashboard features",
                feature_type=FeatureType.BOOLEAN,
                default_value=True
            ),
            FeatureFlag(
                key="bulk_operations",
                name="Bulk Operations",
                description="Bulk import/export and batch operations",
                feature_type=FeatureType.BOOLEAN,
                default_value=True
            ),
            FeatureFlag(
                key="api_access",
                name="API Access",
                description="RESTful API access for integrations",
                feature_type=FeatureType.BOOLEAN,
                default_value=True
            ),
            FeatureFlag(
                key="sso_integration",
                name="Single Sign-On",
                description="SSO integration with external providers",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            FeatureFlag(
                key="custom_branding",
                name="Custom Branding",
                description="Full white-label branding customization",
                feature_type=FeatureType.BOOLEAN,
                default_value=True
            ),
            FeatureFlag(
                key="custom_domains",
                name="Custom Domains",
                description="Custom domain support with SSL",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            
            # Resource Limits
            FeatureFlag(
                key="max_properties",
                name="Maximum Properties",
                description="Maximum number of properties allowed",
                feature_type=FeatureType.NUMBER,
                default_value=50
            ),
            FeatureFlag(
                key="max_units",
                name="Maximum Units",
                description="Maximum number of units allowed",
                feature_type=FeatureType.NUMBER,
                default_value=500
            ),
            FeatureFlag(
                key="max_users",
                name="Maximum Users",
                description="Maximum number of users allowed",
                feature_type=FeatureType.NUMBER,
                default_value=20
            ),
            FeatureFlag(
                key="api_rate_limit",
                name="API Rate Limit",
                description="API requests per minute limit",
                feature_type=FeatureType.NUMBER,
                default_value=1000
            ),
            FeatureFlag(
                key="storage_limit_gb",
                name="Storage Limit (GB)",
                description="Storage limit in gigabytes",
                feature_type=FeatureType.NUMBER,
                default_value=25
            ),
            
            # Integration Features
            FeatureFlag(
                key="quickbooks_integration",
                name="QuickBooks Integration",
                description="Integration with QuickBooks for accounting",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            FeatureFlag(
                key="yardi_integration",
                name="Yardi Integration",
                description="Integration with Yardi property management",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            FeatureFlag(
                key="stripe_payments",
                name="Stripe Payments",
                description="Online payment processing via Stripe",
                feature_type=FeatureType.BOOLEAN,
                default_value=True
            ),
            FeatureFlag(
                key="email_automation",
                name="Email Automation",
                description="Automated email campaigns and notifications",
                feature_type=FeatureType.BOOLEAN,
                default_value=True
            ),
            FeatureFlag(
                key="sms_notifications",
                name="SMS Notifications",
                description="SMS notifications and alerts",
                feature_type=FeatureType.BOOLEAN,
                default_value=False
            ),
            
            # Experimental Features
            FeatureFlag(
                key="blockchain_leases",
                name="Blockchain Leases",
                description="Blockchain-based lease management (experimental)",
                feature_type=FeatureType.BOOLEAN,
                default_value=False,
                rollout_strategy=RolloutStrategy.WHITELIST,
                rollout_config={"whitelist": []}
            ),
            FeatureFlag(
                key="iot_sensors",
                name="IoT Sensors",
                description="IoT sensor integration for smart buildings",
                feature_type=FeatureType.BOOLEAN,
                default_value=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_config={"percentage": 10}
            ),
            FeatureFlag(
                key="virtual_tours",
                name="Virtual Tours",
                description="360° virtual property tours",
                feature_type=FeatureType.BOOLEAN,
                default_value=False,
                rollout_strategy=RolloutStrategy.GRADUAL,
                rollout_config={"start_date": "2024-01-01", "percentage_per_week": 5}
            )
        ]
        
        for feature in default_features:
            self.feature_registry[feature.key] = feature
    
    def register_feature(self, feature: FeatureFlag):
        """Register a new feature flag."""
        self.feature_registry[feature.key] = feature
        current_app.logger.info(f"Registered feature flag: {feature.key}")
    
    def get_feature(self, feature_key: str, tenant_id: int = None) -> Any:
        """
        Get feature value for a tenant.
        
        Args:
            feature_key: Feature flag key
            tenant_id: Tenant ID (uses current context if None)
            
        Returns:
            Feature value based on tenant configuration and rollout strategy
        """
        # Get feature definition
        feature = self.feature_registry.get(feature_key)
        if not feature:
            current_app.logger.warning(f"Unknown feature flag: {feature_key}")
            return None
        
        # Get tenant context
        if tenant_id is None:
            context = get_current_tenant_context()
            if not context or not context.tenant:
                return feature.default_value
            tenant = context.tenant
        else:
            from models.white_label_tenant import WhiteLabelTenant
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return feature.default_value
        
        # Check tenant-specific override
        tenant_value = tenant.get_feature_flag(feature_key)
        if tenant_value is not None:
            return self._apply_rollout_strategy(feature, tenant, tenant_value)
        
        # Use default value with rollout strategy
        return self._apply_rollout_strategy(feature, tenant, feature.default_value)
    
    def is_feature_enabled(self, feature_key: str, tenant_id: int = None) -> bool:
        """
        Check if a boolean feature is enabled for a tenant.
        
        Args:
            feature_key: Feature flag key
            tenant_id: Tenant ID (uses current context if None)
            
        Returns:
            True if feature is enabled, False otherwise
        """
        value = self.get_feature(feature_key, tenant_id)
        return bool(value) if value is not None else False
    
    def set_tenant_feature(self, tenant_id: int, feature_key: str, value: Any) -> bool:
        """
        Set a feature value for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            feature_key: Feature flag key
            value: Feature value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from models.white_label_tenant import WhiteLabelTenant, db
            
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False
            
            # Validate feature exists
            feature = self.feature_registry.get(feature_key)
            if not feature:
                return False
            
            # Validate value type
            if not self._validate_feature_value(feature, value):
                return False
            
            # Set feature flag
            tenant.set_feature_flag(feature_key, value)
            db.session.commit()
            
            current_app.logger.info(f"Set feature {feature_key}={value} for tenant {tenant.tenant_key}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error setting tenant feature: {str(e)}")
            return False
    
    def get_tenant_features(self, tenant_id: int = None) -> Dict[str, Any]:
        """
        Get all feature values for a tenant.
        
        Args:
            tenant_id: Tenant ID (uses current context if None)
            
        Returns:
            Dict of feature_key -> value
        """
        features = {}
        
        for feature_key in self.feature_registry.keys():
            features[feature_key] = self.get_feature(feature_key, tenant_id)
        
        return features
    
    def get_feature_config(self, feature_key: str) -> Optional[Dict[str, Any]]:
        """
        Get feature configuration for administrative purposes.
        
        Args:
            feature_key: Feature flag key
            
        Returns:
            Feature configuration dict or None if not found
        """
        feature = self.feature_registry.get(feature_key)
        if not feature:
            return None
        
        return {
            'key': feature.key,
            'name': feature.name,
            'description': feature.description,
            'type': feature.feature_type.value,
            'default_value': feature.default_value,
            'enabled': feature.enabled,
            'rollout_strategy': feature.rollout_strategy.value,
            'rollout_config': feature.rollout_config,
            'created_at': feature.created_at.isoformat() if feature.created_at else None,
            'updated_at': feature.updated_at.isoformat() if feature.updated_at else None
        }
    
    def list_features(self) -> List[Dict[str, Any]]:
        """
        List all registered features.
        
        Returns:
            List of feature configurations
        """
        return [self.get_feature_config(key) for key in self.feature_registry.keys()]
    
    def _apply_rollout_strategy(self, feature: FeatureFlag, tenant, value: Any) -> Any:
        """Apply rollout strategy to determine final feature value."""
        if not feature.enabled:
            return feature.default_value
        
        if feature.rollout_strategy == RolloutStrategy.ALL_OR_NOTHING:
            return value
        
        elif feature.rollout_strategy == RolloutStrategy.PERCENTAGE:
            percentage = feature.rollout_config.get('percentage', 0)
            # Use tenant ID to create consistent hash for percentage check
            tenant_hash = hash(f"{tenant.id}:{feature.key}") % 100
            if tenant_hash < percentage:
                return value
            return feature.default_value
        
        elif feature.rollout_strategy == RolloutStrategy.WHITELIST:
            whitelist = feature.rollout_config.get('whitelist', [])
            if tenant.tenant_key in whitelist or tenant.id in whitelist:
                return value
            return feature.default_value
        
        elif feature.rollout_strategy == RolloutStrategy.GRADUAL:
            start_date_str = feature.rollout_config.get('start_date')
            percentage_per_week = feature.rollout_config.get('percentage_per_week', 10)
            
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str)
                weeks_elapsed = (datetime.utcnow() - start_date).days // 7
                current_percentage = min(weeks_elapsed * percentage_per_week, 100)
                
                tenant_hash = hash(f"{tenant.id}:{feature.key}") % 100
                if tenant_hash < current_percentage:
                    return value
            
            return feature.default_value
        
        elif feature.rollout_strategy == RolloutStrategy.EXPERIMENT:
            # For A/B testing - could be more sophisticated
            experiment_group = hash(f"{tenant.id}:{feature.key}") % 2
            experiment_config = feature.rollout_config.get('experiment', {})
            
            if experiment_group == 0:
                return experiment_config.get('control_value', feature.default_value)
            else:
                return experiment_config.get('treatment_value', value)
        
        return value
    
    def _validate_feature_value(self, feature: FeatureFlag, value: Any) -> bool:
        """Validate feature value against its type."""
        if feature.feature_type == FeatureType.BOOLEAN:
            return isinstance(value, bool)
        elif feature.feature_type == FeatureType.STRING:
            return isinstance(value, str)
        elif feature.feature_type == FeatureType.NUMBER:
            return isinstance(value, (int, float))
        elif feature.feature_type == FeatureType.JSON:
            try:
                json.dumps(value)
                return True
            except (TypeError, ValueError):
                return False
        
        return False

# Global feature flag service instance
_feature_flag_service = None

def get_feature_flag_service() -> FeatureFlagService:
    """Get the global feature flag service instance."""
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService()
    return _feature_flag_service

# Convenience functions for common usage patterns

def feature_enabled(feature_key: str, tenant_id: int = None) -> bool:
    """Check if a feature is enabled for a tenant."""
    service = get_feature_flag_service()
    return service.is_feature_enabled(feature_key, tenant_id)

def get_feature_value(feature_key: str, tenant_id: int = None, default=None):
    """Get feature value for a tenant with optional default."""
    service = get_feature_flag_service()
    value = service.get_feature(feature_key, tenant_id)
    return value if value is not None else default

def require_feature(feature_key: str, tenant_id: int = None):
    """Decorator to require a feature to be enabled."""
    def decorator(func):
        from functools import wraps
        from flask import abort
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not feature_enabled(feature_key, tenant_id):
                abort(403, description=f"Feature '{feature_key}' is not available")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Template functions for Jinja2
def template_feature_enabled(feature_key: str) -> bool:
    """Template function to check if feature is enabled."""
    return feature_enabled(feature_key)

def template_get_feature(feature_key: str, default=None):
    """Template function to get feature value."""
    return get_feature_value(feature_key, default=default)

def register_template_functions(app):
    """Register feature flag template functions."""
    app.jinja_env.globals.update(
        feature_enabled=template_feature_enabled,
        get_feature=template_get_feature
    )