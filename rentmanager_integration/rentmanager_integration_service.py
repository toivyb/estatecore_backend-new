"""
RentManager Integration Service

Main integration service that coordinates all RentManager integration components
and provides a unified interface for EstateCore's RentManager integration functionality.
"""

import os
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from .rentmanager_auth_service import RentManagerAuthService, RentManagerConnection, RentManagerProductType
from .rentmanager_api_client import RentManagerAPIClient, RentManagerEntityType
from .rentmanager_sync_service import (
    RentManagerSyncService, SyncDirection, SyncStatus, SyncMode, 
    SyncJobConfiguration, ConflictResolution
)
from .rentmanager_mapping_service import RentManagerMappingService
from .models import ComplianceType, PropertyType

logger = logging.getLogger(__name__)

class IntegrationStatus(Enum):
    """Overall RentManager integration status"""
    NOT_CONNECTED = "not_connected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"

class IntegrationMode(Enum):
    """Integration operation modes"""
    LIVE = "live"
    SANDBOX = "sandbox"
    TESTING = "testing"
    DEVELOPMENT = "development"

@dataclass
class IntegrationHealth:
    """Comprehensive integration health status"""
    status: IntegrationStatus
    connection_health: Dict[str, Any]
    sync_health: Dict[str, Any]
    compliance_health: Dict[str, Any]
    data_quality_score: float
    performance_metrics: Dict[str, Any]
    last_check: datetime
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    uptime_percentage: float = 0.0
    error_rate: float = 0.0

@dataclass
class IntegrationConfiguration:
    """RentManager integration configuration"""
    organization_id: str
    integration_name: str
    product_types: List[RentManagerProductType]
    property_types: List[PropertyType]
    compliance_programs: List[ComplianceType]
    
    # Sync configuration
    sync_enabled: bool = True
    real_time_sync: bool = True
    batch_sync_schedule: Optional[str] = None
    auto_conflict_resolution: bool = True
    conflict_resolution_strategy: ConflictResolution = ConflictResolution.MANUAL_REVIEW
    
    # Data quality and validation
    data_quality_checks: bool = True
    compliance_validation: bool = True
    field_level_validation: bool = True
    
    # Enterprise features
    enterprise_features: bool = False
    multi_property_support: bool = True
    portfolio_management: bool = False
    
    # Security and audit
    audit_enabled: bool = True
    encryption_enabled: bool = True
    backup_enabled: bool = True
    
    # Performance settings
    mode: IntegrationMode = IntegrationMode.LIVE
    batch_size: int = 100
    max_workers: int = 5
    timeout_seconds: int = 300
    rate_limit_requests_per_minute: int = 100
    
    # Custom configuration
    custom_mappings: Dict[str, Any] = field(default_factory=dict)
    sync_entities: List[str] = field(default_factory=list)
    excluded_entities: List[str] = field(default_factory=list)
    property_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Specialized configurations
    student_housing_config: Dict[str, Any] = field(default_factory=dict)
    affordable_housing_config: Dict[str, Any] = field(default_factory=dict)
    commercial_config: Dict[str, Any] = field(default_factory=dict)
    hoa_config: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class RentManagerIntegrationService:
    """
    Main RentManager Integration Service
    
    Coordinates all RentManager integration components and provides a unified interface
    for managing connections, synchronization, monitoring, and enterprise features.
    """
    
    def __init__(self):
        # Initialize all service components
        self.auth_service = RentManagerAuthService()
        self.api_client = RentManagerAPIClient(self.auth_service)
        self.mapping_service = RentManagerMappingService()
        self.sync_service = RentManagerSyncService(
            self.api_client, self.mapping_service, self.auth_service
        )
        
        # Integration state management
        self.active_connections: Dict[str, RentManagerConnection] = {}
        self.integration_configs: Dict[str, IntegrationConfiguration] = {}
        self.health_cache: Dict[str, IntegrationHealth] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Performance and monitoring
        self.request_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.sync_history: Dict[str, List[Dict[str, Any]]] = {}
        self.compliance_audit_trail: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("RentManager Integration Service initialized")
    
    # ===================================================
    # INTEGRATION SETUP AND CONFIGURATION
    # ===================================================
    
    def create_integration(self, organization_id: str, config: IntegrationConfiguration) -> Dict[str, Any]:
        """
        Create a new RentManager integration for an organization
        
        Args:
            organization_id: Organization identifier
            config: Integration configuration
            
        Returns:
            Dict with integration creation results
        """
        try:
            # Validate configuration
            validation_result = self._validate_integration_config(config)
            if not validation_result['valid']:
                return {
                    "success": False,
                    "error": "Invalid configuration",
                    "validation_errors": validation_result['errors']
                }
            
            # Store configuration
            config.organization_id = organization_id
            config.created_at = datetime.utcnow()
            self.integration_configs[organization_id] = config
            
            # Setup default mappings based on property types
            self._setup_property_type_mappings(organization_id, config)
            
            # Setup compliance mappings
            self._setup_compliance_mappings(organization_id, config)
            
            # Initialize monitoring and audit
            self._initialize_monitoring(organization_id, config)
            
            logger.info(f"RentManager integration created for organization {organization_id}")
            
            return {
                "success": True,
                "integration_id": organization_id,
                "configuration": asdict(config),
                "next_steps": [
                    "Configure RentManager connection credentials",
                    "Test connection to RentManager system",
                    "Setup field mappings if needed",
                    "Configure compliance monitoring",
                    "Enable synchronization"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to create RentManager integration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def connect_to_rentmanager(self, organization_id: str, 
                             connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Establish connection to RentManager system
        
        Args:
            organization_id: Organization identifier
            connection_params: Connection parameters (credentials, endpoints, etc.)
            
        Returns:
            Dict with connection results
        """
        try:
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not configured. Create integration first."
                }
            
            # Create connection based on authentication type
            auth_type = connection_params.get("auth_type", "oauth2")
            
            if auth_type == "oauth2":
                # Start OAuth flow
                oauth_result = self.auth_service.generate_authorization_url(
                    organization_id=organization_id,
                    product_types=config.product_types,
                    redirect_uri=connection_params.get("redirect_uri"),
                    custom_scopes=connection_params.get("custom_scopes", [])
                )
                
                return {
                    "success": True,
                    "connection_type": "oauth2",
                    "authorization_url": oauth_result[0],
                    "state": oauth_result[1],
                    "instructions": "Redirect user to authorization_url to complete RentManager connection"
                }
            
            elif auth_type == "api_key":
                # Create API key connection
                connection = self.auth_service.create_api_key_connection(
                    organization_id=organization_id,
                    api_key=connection_params["api_key"],
                    api_secret=connection_params["api_secret"],
                    base_url=connection_params["base_url"],
                    product_types=config.product_types
                )
                
                # Store active connection
                self.active_connections[organization_id] = connection
                
                # Initialize sync service for this connection
                self._initialize_sync_configuration(connection, config)
                
                return {
                    "success": True,
                    "connection_id": connection.connection_id,
                    "product_types": [pt.value for pt in connection.product_types],
                    "company_info": connection.company_info,
                    "property_count": connection.property_count,
                    "unit_count": connection.unit_count,
                    "resident_count": connection.resident_count,
                    "message": "Successfully connected to RentManager"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported authentication type: {auth_type}"
                }
                
        except Exception as e:
            logger.error(f"Failed to connect to RentManager: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def complete_oauth_flow(self, code: str, state: str) -> Dict[str, Any]:
        """
        Complete OAuth authentication flow
        
        Args:
            code: Authorization code from RentManager callback
            state: OAuth state parameter
            
        Returns:
            Dict with connection details
        """
        try:
            connection = self.auth_service.exchange_code_for_tokens(code, state)
            
            # Store active connection
            self.active_connections[connection.organization_id] = connection
            
            # Get configuration
            config = self.integration_configs.get(connection.organization_id)
            if config:
                # Initialize sync service for this connection
                self._initialize_sync_configuration(connection, config)
            
            logger.info(f"Successfully completed OAuth flow for organization {connection.organization_id}")
            
            return {
                "success": True,
                "connection_id": connection.connection_id,
                "product_types": [pt.value for pt in connection.product_types],
                "company_info": connection.company_info,
                "property_count": connection.property_count,
                "unit_count": connection.unit_count,
                "resident_count": connection.resident_count,
                "compliance_flags": connection.compliance_flags,
                "message": "Successfully connected to RentManager"
            }
            
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ===================================================
    # SYNCHRONIZATION MANAGEMENT
    # ===================================================
    
    async def start_full_sync(self, organization_id: str, 
                            sync_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start comprehensive data synchronization
        
        Args:
            organization_id: Organization identifier
            sync_options: Additional sync options
            
        Returns:
            Dict with sync job information
        """
        try:
            connection = self.active_connections.get(organization_id)
            if not connection:
                return {
                    "success": False,
                    "error": "No active RentManager connection found"
                }
            
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not configured"
                }
            
            # Build sync configuration
            sync_config = self._build_sync_configuration(config, sync_options)
            
            # Create sync job
            sync_job = await self.sync_service.create_sync_job(sync_config)
            
            # Start sync execution
            execution_result = await self.sync_service.execute_sync_job(sync_job.job_id)
            
            # Update sync history
            self._update_sync_history(organization_id, sync_job, execution_result)
            
            return {
                "success": True,
                "job_id": sync_job.job_id,
                "sync_direction": sync_config.sync_direction.value,
                "entity_types": sync_config.entity_types,
                "compliance_programs": [cp.value for cp in sync_config.compliance_types],
                "status": "started",
                "message": "Full synchronization started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start full sync: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def start_incremental_sync(self, organization_id: str,
                                   since_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Start incremental data synchronization
        
        Args:
            organization_id: Organization identifier
            since_timestamp: Sync changes since this timestamp
            
        Returns:
            Dict with sync job information
        """
        try:
            connection = self.active_connections.get(organization_id)
            if not connection:
                return {
                    "success": False,
                    "error": "No active RentManager connection found"
                }
            
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not configured"
                }
            
            # Default to changes since last sync
            if since_timestamp is None:
                recent_jobs = self.sync_service.get_recent_sync_jobs(organization_id, limit=1)
                if recent_jobs:
                    since_timestamp = recent_jobs[0].completed_at
                else:
                    since_timestamp = datetime.utcnow() - timedelta(hours=24)
            
            # Build incremental sync configuration
            sync_config = self._build_sync_configuration(config, {
                "sync_mode": SyncMode.INCREMENTAL,
                "since_timestamp": since_timestamp
            })
            
            # Create and execute sync job
            sync_job = await self.sync_service.create_sync_job(sync_config)
            execution_result = await self.sync_service.execute_sync_job(sync_job.job_id)
            
            # Update sync history
            self._update_sync_history(organization_id, sync_job, execution_result)
            
            return {
                "success": True,
                "job_id": sync_job.job_id,
                "sync_mode": "incremental",
                "since_timestamp": since_timestamp.isoformat(),
                "status": "started"
            }
            
        except Exception as e:
            logger.error(f"Failed to start incremental sync: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ===================================================
    # COMPLIANCE MANAGEMENT
    # ===================================================
    
    def get_compliance_status(self, organization_id: str, 
                            property_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get compliance status for organization or specific property
        
        Args:
            organization_id: Organization identifier
            property_id: Optional property identifier
            
        Returns:
            Dict with compliance status
        """
        try:
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not configured"
                }
            
            compliance_status = {
                "success": True,
                "organization_id": organization_id,
                "property_id": property_id,
                "compliance_programs": {},
                "overall_compliance": True,
                "violations": [],
                "warnings": [],
                "last_check": datetime.utcnow().isoformat()
            }
            
            # Check each compliance program
            for compliance_type in config.compliance_programs:
                program_status = self._check_compliance_program(
                    organization_id, compliance_type, property_id
                )
                
                compliance_status["compliance_programs"][compliance_type.value] = program_status
                
                if not program_status.get("compliant", True):
                    compliance_status["overall_compliance"] = False
                    compliance_status["violations"].extend(
                        program_status.get("violations", [])
                    )
                
                compliance_status["warnings"].extend(
                    program_status.get("warnings", [])
                )
            
            return compliance_status
            
        except Exception as e:
            logger.error(f"Failed to get compliance status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_compliance_report(self, organization_id: str,
                                 compliance_type: ComplianceType,
                                 report_period: str = "monthly") -> Dict[str, Any]:
        """
        Generate compliance report
        
        Args:
            organization_id: Organization identifier
            compliance_type: Type of compliance program
            report_period: Report period (monthly, quarterly, annual)
            
        Returns:
            Dict with compliance report
        """
        try:
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not configured"
                }
            
            if compliance_type not in config.compliance_programs:
                return {
                    "success": False,
                    "error": f"Compliance program {compliance_type.value} not configured"
                }
            
            # Generate report based on compliance type
            report = self._generate_compliance_report(
                organization_id, compliance_type, report_period
            )
            
            # Store in audit trail
            self._add_to_compliance_audit_trail(
                organization_id, "report_generated", {
                    "compliance_type": compliance_type.value,
                    "report_period": report_period,
                    "report_id": report.get("report_id")
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ===================================================
    # MONITORING AND HEALTH
    # ===================================================
    
    def get_integration_health(self, organization_id: str, 
                             force_refresh: bool = False) -> IntegrationHealth:
        """Get comprehensive integration health status"""
        
        # Check cache
        if not force_refresh and organization_id in self.health_cache:
            cached_health = self.health_cache[organization_id]
            if (datetime.utcnow() - cached_health.last_check).seconds < 300:  # 5 minutes
                return cached_health
        
        try:
            # Collect health data from all components
            connection_health = self._get_connection_health(organization_id)
            sync_health = self._get_sync_health(organization_id)
            compliance_health = self._get_compliance_health(organization_id)
            performance_metrics = self._get_performance_metrics(organization_id)
            
            # Calculate data quality score
            data_quality_score = self._calculate_data_quality_score(organization_id)
            
            # Determine overall status
            overall_status = self._determine_overall_status(
                connection_health, sync_health, compliance_health, data_quality_score
            )
            
            # Collect issues and recommendations
            issues, warnings, recommendations = self._analyze_health_issues(
                connection_health, sync_health, compliance_health, data_quality_score
            )
            
            # Calculate uptime and error rates
            uptime_percentage = self._calculate_uptime(organization_id)
            error_rate = self._calculate_error_rate(organization_id)
            
            health = IntegrationHealth(
                status=overall_status,
                connection_health=connection_health,
                sync_health=sync_health,
                compliance_health=compliance_health,
                data_quality_score=data_quality_score,
                performance_metrics=performance_metrics,
                last_check=datetime.utcnow(),
                issues=issues,
                warnings=warnings,
                recommendations=recommendations,
                uptime_percentage=uptime_percentage,
                error_rate=error_rate
            )
            
            # Cache result
            self.health_cache[organization_id] = health
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking integration health: {e}")
            return IntegrationHealth(
                status=IntegrationStatus.ERROR,
                connection_health={},
                sync_health={},
                compliance_health={},
                data_quality_score=0.0,
                performance_metrics={},
                last_check=datetime.utcnow(),
                issues=[f"Health check failed: {str(e)}"],
                warnings=[],
                recommendations=["Contact support for assistance"]
            )
    
    def get_integration_summary(self, organization_id: str) -> Dict[str, Any]:
        """Get comprehensive integration summary"""
        try:
            health = self.get_integration_health(organization_id)
            config = self.integration_configs.get(organization_id)
            connection = self.active_connections.get(organization_id)
            
            # Get recent activity
            recent_syncs = self.sync_service.get_recent_sync_jobs(organization_id, limit=5)
            active_jobs = self.sync_service.get_active_sync_jobs(organization_id)
            
            return {
                "organization_id": organization_id,
                "overall_status": health.status.value,
                "health_score": health.data_quality_score,
                "uptime_percentage": health.uptime_percentage,
                "error_rate": health.error_rate,
                "connection": {
                    "connected": connection is not None,
                    "product_types": [pt.value for pt in connection.product_types] if connection else [],
                    "company_name": connection.company_info.get('name') if connection else None,
                    "property_count": connection.property_count if connection else 0,
                    "unit_count": connection.unit_count if connection else 0,
                    "resident_count": connection.resident_count if connection else 0,
                    "compliance_flags": connection.compliance_flags if connection else [],
                    "last_activity": connection.last_used_at.isoformat() if connection and connection.last_used_at else None
                },
                "synchronization": {
                    "enabled": config.sync_enabled if config else False,
                    "active_jobs": len(active_jobs),
                    "recent_jobs": len(recent_syncs),
                    "last_sync": recent_syncs[0].completed_at.isoformat() if recent_syncs and recent_syncs[0].completed_at else None
                },
                "compliance": {
                    "programs": [cp.value for cp in config.compliance_programs] if config else [],
                    "overall_compliance": health.compliance_health.get("overall_compliant", True),
                    "violations_count": len(health.compliance_health.get("violations", [])),
                    "last_check": health.compliance_health.get("last_check")
                },
                "configuration": asdict(config) if config else {},
                "issues": health.issues,
                "warnings": health.warnings,
                "recommendations": health.recommendations,
                "last_updated": health.last_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting integration summary: {e}")
            return {
                "organization_id": organization_id,
                "overall_status": "error",
                "error": str(e)
            }
    
    # ===================================================
    # UTILITY AND HELPER METHODS
    # ===================================================
    
    def _validate_integration_config(self, config: IntegrationConfiguration) -> Dict[str, Any]:
        """Validate integration configuration"""
        errors = []
        
        if not config.integration_name:
            errors.append("Integration name is required")
        
        if not config.product_types:
            errors.append("At least one RentManager product type must be specified")
        
        if not config.property_types:
            errors.append("At least one property type must be specified")
        
        if config.sync_entities and len(config.sync_entities) == 0:
            errors.append("At least one sync entity must be specified")
        
        if config.rate_limit_requests_per_minute < 1:
            errors.append("Rate limit must be at least 1 request per minute")
        
        # Validate compliance configuration
        if config.compliance_validation and not config.compliance_programs:
            errors.append("Compliance programs must be specified when compliance validation is enabled")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _build_sync_configuration(self, config: IntegrationConfiguration, 
                                sync_options: Optional[Dict[str, Any]] = None) -> SyncJobConfiguration:
        """Build sync job configuration"""
        sync_options = sync_options or {}
        
        return SyncJobConfiguration(
            organization_id=config.organization_id,
            job_name=f"RentManager Sync - {config.integration_name}",
            sync_direction=SyncDirection(sync_options.get("sync_direction", "bidirectional")),
            sync_mode=sync_options.get("sync_mode", SyncMode.FULL),
            entity_types=config.sync_entities or [
                "properties", "units", "residents", "leases", "payments", "work_orders"
            ],
            property_ids=sync_options.get("property_ids", []),
            filters=dict(config.property_filters, **sync_options.get("filters", {})),
            schedule=sync_options.get("schedule"),
            since_timestamp=sync_options.get("since_timestamp"),
            batch_size=sync_options.get("batch_size", config.batch_size),
            conflict_resolution=config.conflict_resolution_strategy,
            compliance_validation=config.compliance_validation,
            compliance_types=config.compliance_programs,
            parallel_processing=sync_options.get("parallel_processing", True),
            max_workers=sync_options.get("max_workers", config.max_workers),
            retry_count=sync_options.get("retry_count", 3),
            timeout_seconds=sync_options.get("timeout_seconds", config.timeout_seconds),
            validate_before_sync=config.data_quality_checks,
            backup_before_sync=config.backup_enabled,
            custom_mappings=config.custom_mappings
        )
    
    # Placeholder methods for implementation
    def _setup_property_type_mappings(self, organization_id: str, config: IntegrationConfiguration):
        """Setup property type specific mappings"""
        for property_type in config.property_types:
            if property_type == PropertyType.STUDENT_HOUSING:
                self.mapping_service.setup_custom_mapping(
                    organization_id, "student_housing", config.student_housing_config
                )
            elif property_type == PropertyType.AFFORDABLE_HOUSING:
                self.mapping_service.setup_custom_mapping(
                    organization_id, "affordable_housing", config.affordable_housing_config
                )
            elif property_type == PropertyType.COMMERCIAL:
                self.mapping_service.setup_custom_mapping(
                    organization_id, "commercial", config.commercial_config
                )
    
    def _setup_compliance_mappings(self, organization_id: str, config: IntegrationConfiguration):
        """Setup compliance specific mappings"""
        pass
    
    def _initialize_monitoring(self, organization_id: str, config: IntegrationConfiguration):
        """Initialize monitoring and audit systems"""
        pass
    
    def _initialize_sync_configuration(self, connection: RentManagerConnection, 
                                     config: IntegrationConfiguration):
        """Initialize sync service configuration"""
        pass
    
    def _update_sync_history(self, organization_id: str, sync_job, execution_result):
        """Update sync history"""
        pass
    
    def _check_compliance_program(self, organization_id: str, compliance_type: ComplianceType,
                                property_id: Optional[str] = None) -> Dict[str, Any]:
        """Check specific compliance program"""
        return {"compliant": True, "violations": [], "warnings": []}
    
    def _generate_compliance_report(self, organization_id: str, compliance_type: ComplianceType,
                                  report_period: str) -> Dict[str, Any]:
        """Generate compliance report"""
        return {
            "success": True,
            "report_id": str(uuid.uuid4()),
            "compliance_type": compliance_type.value,
            "report_period": report_period,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _add_to_compliance_audit_trail(self, organization_id: str, event_type: str, details: Dict[str, Any]):
        """Add entry to compliance audit trail"""
        pass
    
    def _get_connection_health(self, organization_id: str) -> Dict[str, Any]:
        """Get connection health status"""
        return {"healthy": True, "status": "connected"}
    
    def _get_sync_health(self, organization_id: str) -> Dict[str, Any]:
        """Get sync health status"""
        return {"healthy": True, "recent_syncs": 0, "failed_syncs": 0}
    
    def _get_compliance_health(self, organization_id: str) -> Dict[str, Any]:
        """Get compliance health status"""
        return {"overall_compliant": True, "violations": [], "warnings": []}
    
    def _get_performance_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Get performance metrics"""
        return {"avg_response_time": 0, "requests_per_minute": 0}
    
    def _calculate_data_quality_score(self, organization_id: str) -> float:
        """Calculate data quality score"""
        return 95.0
    
    def _determine_overall_status(self, connection_health, sync_health, compliance_health, data_quality_score) -> IntegrationStatus:
        """Determine overall integration status"""
        return IntegrationStatus.CONNECTED
    
    def _analyze_health_issues(self, connection_health, sync_health, compliance_health, data_quality_score):
        """Analyze health issues and return recommendations"""
        return [], [], []
    
    def _calculate_uptime(self, organization_id: str) -> float:
        """Calculate uptime percentage"""
        return 99.5
    
    def _calculate_error_rate(self, organization_id: str) -> float:
        """Calculate error rate"""
        return 0.1

# Global service instance
_integration_service = None

def get_rentmanager_integration_service() -> RentManagerIntegrationService:
    """Get singleton integration service instance"""
    global _integration_service
    if _integration_service is None:
        _integration_service = RentManagerIntegrationService()
    return _integration_service