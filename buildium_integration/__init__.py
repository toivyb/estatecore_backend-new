"""
Buildium Integration for EstateCore

Comprehensive integration package for Buildium property management platform,
serving 2M+ units with specialized focus on small property managers,
individual investors, and growing rental portfolios.

This package provides:
- Property and unit management synchronization
- Tenant and lease management integration
- Rent collection and payment processing
- Maintenance request automation
- Financial reporting and accounting
- Tenant screening and applications
- Document storage management
- Owner/investor reporting
- Small portfolio optimizations
"""

from .buildium_integration_service import BuildiumIntegrationService, get_buildium_integration_service
from .buildium_auth_service import BuildiumAuthService, BuildiumConnection, BuildiumProductType
from .buildium_api_client import BuildiumAPIClient, BuildiumEntityType, BuildiumRequest
from .buildium_sync_service import BuildiumSyncService, SyncDirection, SyncStatus
from .buildium_mapping_service import BuildiumMappingService
from .buildium_webhook_service import BuildiumWebhookService
from .buildium_enterprise_service import BuildiumEnterpriseService
from .buildium_monitoring_service import BuildiumMonitoringService

__version__ = "1.0.0"
__author__ = "EstateCore Development Team"
__description__ = "Comprehensive Buildium integration for EstateCore property management platform"

# Integration capabilities
SUPPORTED_PRODUCTS = [
    "Buildium Property Management",
    "Buildium Rent Collection", 
    "Buildium Maintenance",
    "Buildium Tenant Screening",
    "Buildium Accounting",
    "Buildium Owner Reporting",
    "Buildium Vendor Management"
]

SUPPORTED_ENTITIES = [
    "properties",
    "units", 
    "tenants",
    "leases",
    "payments",
    "maintenance",
    "vendors",
    "applications",
    "screening",
    "accounting",
    "documents",
    "communications",
    "owners",
    "reports"
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
    "advanced_reporting",
    "small_portfolio_optimization",
    "self_service_features",
    "cost_effective_integration"
]

SMALL_PORTFOLIO_FEATURES = [
    "simplified_workflow_management",
    "automated_routine_tasks",
    "self_service_landlord_portal",
    "basic_compliance_support",
    "simple_reporting_dashboards",
    "cost_effective_pricing",
    "quick_setup_wizard",
    "mobile_friendly_interface"
]