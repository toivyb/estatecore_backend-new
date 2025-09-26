"""
RealPage Integration Package for EstateCore

Comprehensive integration with RealPage's suite of property management products
including OneSite, LeasingDesk, YieldStar, Velocity, ActiveBuilding, and CrossFire.

This package provides:
- Multi-product authentication and connection management
- Bidirectional data synchronization
- Revenue management and pricing optimization
- Real-time webhook notifications
- Enterprise-grade monitoring and analytics
- Conflict resolution and data quality management
"""

from .realpage_integration_service import RealPageIntegrationService, get_realpage_integration_service
from .realpage_auth_service import RealPageAuthService, RealPageConnection, RealPageProductType
from .realpage_api_client import RealPageAPIClient, RealPageEntityType, RealPageOperationType
from .realpage_sync_service import RealPageSyncService, SyncDirection, SyncStatus
from .realpage_mapping_service import RealPageMappingService
from .realpage_webhook_service import RealPageWebhookService
from .realpage_scheduler_service import RealPageSchedulerService
from .realpage_revenue_service import RealPageRevenueService
from .realpage_monitoring_service import RealPageMonitoringService

__version__ = "1.0.0"
__author__ = "EstateCore Development Team"
__email__ = "dev@estatecore.com"

# Export main service for easy access
__all__ = [
    'RealPageIntegrationService',
    'get_realpage_integration_service',
    'RealPageAuthService',
    'RealPageAPIClient',
    'RealPageSyncService',
    'RealPageMappingService',
    'RealPageWebhookService',
    'RealPageSchedulerService',
    'RealPageRevenueService',
    'RealPageMonitoringService',
    'RealPageConnection',
    'RealPageProductType',
    'RealPageEntityType',
    'RealPageOperationType',
    'SyncDirection',
    'SyncStatus'
]