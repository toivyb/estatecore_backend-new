"""
EstateCore Yardi Integration Module

Comprehensive Yardi property management software integration for EstateCore
providing seamless data synchronization with Yardi Voyager, Yardi Breeze,
and other Yardi products.

Features:
- Bidirectional data synchronization
- Real-time and batch processing
- Enterprise multi-property support
- Advanced conflict resolution
- Comprehensive audit trails
- Integration health monitoring
"""

from .yardi_integration_service import YardiIntegrationService, get_yardi_integration_service
from .yardi_api_client import YardiAPIClient, YardiProductType, YardiEntityType
from .yardi_auth_service import YardiAuthService, YardiConnectionType, YardiAuthMethod
from .yardi_sync_service import YardiSyncService, SyncDirection, SyncStatus
from .yardi_mapping_service import YardiMappingService
from .yardi_webhook_service import YardiWebhookService
from .yardi_scheduler_service import YardiSchedulerService
from .yardi_enterprise_service import YardiEnterpriseService
from .yardi_monitoring_service import YardiMonitoringService

__version__ = "1.0.0"
__author__ = "EstateCore Development Team"

# Integration status constants
INTEGRATION_STATUS_NOT_CONNECTED = "not_connected"
INTEGRATION_STATUS_CONNECTING = "connecting"
INTEGRATION_STATUS_CONNECTED = "connected"
INTEGRATION_STATUS_SYNCING = "syncing"
INTEGRATION_STATUS_ERROR = "error"
INTEGRATION_STATUS_MAINTENANCE = "maintenance"

# Sync entity types
SYNC_ENTITY_PROPERTIES = "properties"
SYNC_ENTITY_UNITS = "units"
SYNC_ENTITY_TENANTS = "tenants"
SYNC_ENTITY_LEASES = "leases"
SYNC_ENTITY_PAYMENTS = "payments"
SYNC_ENTITY_MAINTENANCE = "maintenance"
SYNC_ENTITY_VENDORS = "vendors"
SYNC_ENTITY_ACCOUNTING = "accounting"

# Export main service for easy access
__all__ = [
    'YardiIntegrationService',
    'get_yardi_integration_service',
    'YardiAPIClient',
    'YardiAuthService',
    'YardiSyncService',
    'YardiMappingService',
    'YardiWebhookService',
    'YardiSchedulerService',
    'YardiEnterpriseService',
    'YardiMonitoringService',
    'YardiProductType',
    'YardiEntityType',
    'YardiConnectionType',
    'YardiAuthMethod',
    'SyncDirection',
    'SyncStatus'
]