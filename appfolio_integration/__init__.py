"""
AppFolio Integration for EstateCore

Comprehensive integration package for AppFolio Property Manager, Investment Manager,
and related property management systems. Supports 7M+ units with enterprise-grade
features for the small to mid-size property management market.

This package provides:
- Property Manager integration for core property management
- Investment Manager for real estate investments
- APM (AppFolio Property Manager) leasing and operations
- Maintenance and work order management
- Accounting and financial reporting
- Tenant/resident portal integration
- Vendor management and payments
"""

from .appfolio_integration_service import AppFolioIntegrationService, get_appfolio_integration_service
from .appfolio_auth_service import AppFolioAuthService, AppFolioConnection, AppFolioProductType
from .appfolio_api_client import AppFolioAPIClient, AppFolioEntityType, AppFolioRequest
from .appfolio_sync_service import AppFolioSyncService, SyncDirection, SyncStatus
from .appfolio_mapping_service import AppFolioMappingService
from .appfolio_webhook_service import AppFolioWebhookService
from .appfolio_enterprise_service import AppFolioEnterpriseService
from .appfolio_monitoring_service import AppFolioMonitoringService

__version__ = "1.0.0"
__author__ = "EstateCore Development Team"
__description__ = "Comprehensive AppFolio integration for EstateCore property management platform"

# Integration capabilities
SUPPORTED_PRODUCTS = [
    "AppFolio Property Manager",
    "AppFolio Investment Manager", 
    "APM (AppFolio Property Manager)",
    "AppFolio Maintenance",
    "AppFolio Accounting",
    "AppFolio Tenant Portal",
    "AppFolio Vendor Management"
]

SUPPORTED_ENTITIES = [
    "properties",
    "units", 
    "tenants",
    "leases",
    "payments",
    "maintenance",
    "vendors",
    "accounting",
    "documents",
    "communications"
]

ENTERPRISE_FEATURES = [
    "multi_property_portfolios",
    "real_time_webhooks", 
    "bidirectional_sync",
    "custom_field_mapping",
    "role_based_access_control",
    "white_label_configuration",
    "integration_health_monitoring",
    "automated_workflows",
    "bulk_operations",
    "advanced_reporting"
]