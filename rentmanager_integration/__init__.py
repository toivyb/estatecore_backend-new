"""
RentManager Integration Module

Comprehensive RentManager integration for EstateCore with support for:
- Multi-family residential management
- Commercial property management  
- Affordable housing compliance (LIHTC, Section 8, HUD, etc.)
- Student housing management
- HOA and community association management
- Asset management and investment tracking
- Enterprise-grade synchronization and monitoring
"""

from .rentmanager_auth_service import (
    RentManagerAuthService,
    RentManagerCredentials,
    RentManagerConnection,
    RentManagerProductType,
    AuthenticationType,
    get_rentmanager_auth_service
)

from .rentmanager_api_client import (
    RentManagerAPIClient,
    RentManagerEntityType,
    APIOperationType,
    APIRequest,
    APIResponse,
    get_rentmanager_api_client
)

from .rentmanager_mapping_service import (
    RentManagerMappingService,
    MappingDirection,
    MappingType,
    FieldMapping,
    EntityMapping,
    MappingResult,
    get_rentmanager_mapping_service
)

from .rentmanager_sync_service import (
    RentManagerSyncService,
    SyncDirection,
    SyncMode,
    SyncStatus,
    SyncJobConfiguration,
    SyncJob,
    SyncEntityResult,
    ConflictResolution,
    get_rentmanager_sync_service
)

from .rentmanager_integration_service import (
    RentManagerIntegrationService,
    IntegrationStatus,
    IntegrationMode,
    IntegrationHealth,
    IntegrationConfiguration,
    get_rentmanager_integration_service
)

from .models import (
    # Core models
    RentManagerProperty,
    RentManagerUnit,
    RentManagerResident,
    RentManagerLease,
    RentManagerPayment,
    RentManagerWorkOrder,
    RentManagerVendor,
    RentManagerAccount,
    RentManagerTransaction,
    RentManagerDocument,
    RentManagerMessage,
    
    # Specialized models
    StudentHousingApplication,
    AffordableHousingCompliance,
    HOAManagement,
    
    # Enums
    PropertyType,
    UnitType,
    LeaseStatus,
    ComplianceType,
    PaymentStatus,
    WorkOrderStatus,
    WorkOrderPriority,
    VendorType,
    ResidentStatus,
    
    # Utility functions
    dict_to_property,
    property_to_dict
)

__version__ = "1.0.0"
__author__ = "EstateCore Development Team"
__description__ = "Comprehensive RentManager integration for property management"

# Module exports
__all__ = [
    # Services
    "RentManagerAuthService",
    "RentManagerAPIClient", 
    "RentManagerMappingService",
    "RentManagerSyncService",
    "RentManagerIntegrationService",
    
    # Service getters
    "get_rentmanager_auth_service",
    "get_rentmanager_api_client",
    "get_rentmanager_mapping_service", 
    "get_rentmanager_sync_service",
    "get_rentmanager_integration_service",
    
    # Auth models
    "RentManagerCredentials",
    "RentManagerConnection",
    "RentManagerProductType",
    "AuthenticationType",
    
    # API models
    "RentManagerEntityType",
    "APIOperationType",
    "APIRequest",
    "APIResponse",
    
    # Mapping models
    "MappingDirection",
    "MappingType", 
    "FieldMapping",
    "EntityMapping",
    "MappingResult",
    
    # Sync models
    "SyncDirection",
    "SyncMode",
    "SyncStatus",
    "SyncJobConfiguration",
    "SyncJob", 
    "SyncEntityResult",
    "ConflictResolution",
    
    # Integration models
    "IntegrationStatus",
    "IntegrationMode",
    "IntegrationHealth",
    "IntegrationConfiguration",
    
    # Core data models
    "RentManagerProperty",
    "RentManagerUnit",
    "RentManagerResident", 
    "RentManagerLease",
    "RentManagerPayment",
    "RentManagerWorkOrder",
    "RentManagerVendor",
    "RentManagerAccount",
    "RentManagerTransaction",
    "RentManagerDocument",
    "RentManagerMessage",
    
    # Specialized models
    "StudentHousingApplication",
    "AffordableHousingCompliance", 
    "HOAManagement",
    
    # Enums
    "PropertyType",
    "UnitType",
    "LeaseStatus",
    "ComplianceType",
    "PaymentStatus",
    "WorkOrderStatus", 
    "WorkOrderPriority",
    "VendorType",
    "ResidentStatus",
    
    # Utility functions
    "dict_to_property",
    "property_to_dict"
]

# Integration info
RENTMANAGER_INTEGRATION_INFO = {
    "name": "RentManager Integration",
    "version": __version__,
    "description": __description__,
    "supported_products": [
        "Property Management",
        "Asset Management", 
        "Compliance Management",
        "Student Housing",
        "Affordable Housing",
        "Commercial Management",
        "HOA Management",
        "Maintenance Management"
    ],
    "supported_property_types": [
        "Multi-family Residential",
        "Commercial",
        "Affordable Housing", 
        "Student Housing",
        "Senior Housing",
        "Mixed Use",
        "Retail",
        "Office",
        "Industrial",
        "HOA Communities"
    ],
    "compliance_programs": [
        "LIHTC (Low-Income Housing Tax Credit)",
        "Section 8 Housing Choice Voucher",
        "HUD Programs",
        "HOME Investment Partnerships",
        "CDBG (Community Development Block Grant)",
        "USDA Rural Development",
        "Tax-Exempt Bond Financing",
        "State and Local Programs"
    ],
    "features": [
        "Real-time bidirectional synchronization",
        "Comprehensive compliance tracking",
        "Multi-property portfolio management", 
        "Advanced data mapping and transformation",
        "Conflict resolution and data quality checks",
        "Audit trails and monitoring",
        "Enterprise security and encryption",
        "Bulk operations and batch processing",
        "Webhook support for real-time updates",
        "Customizable field mappings",
        "Performance monitoring and analytics"
    ]
}