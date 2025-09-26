"""
Main Yardi Integration Service

Comprehensive integration service that coordinates all Yardi integration components
and provides a unified interface for EstateCore's Yardi integration functionality.
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

from .yardi_auth_service import YardiAuthService, YardiConnection, YardiConnectionType
from .yardi_api_client import YardiAPIClient, YardiProductType, YardiEntityType
from .yardi_sync_service import YardiSyncService, SyncDirection, SyncStatus, SyncJob
from .yardi_mapping_service import YardiMappingService
from .yardi_webhook_service import YardiWebhookService
from .yardi_scheduler_service import YardiSchedulerService
from .yardi_enterprise_service import YardiEnterpriseService
from .yardi_monitoring_service import YardiMonitoringService

logger = logging.getLogger(__name__)

class IntegrationStatus(Enum):
    """Overall Yardi integration status"""
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
    webhook_health: Dict[str, Any]
    automation_health: Dict[str, Any]
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
    """Yardi integration configuration"""
    organization_id: str
    integration_name: str
    yardi_product: YardiProductType
    connection_type: YardiConnectionType
    sync_enabled: bool = True
    real_time_sync: bool = True
    batch_sync_schedule: Optional[str] = None
    auto_conflict_resolution: bool = True
    data_quality_checks: bool = True
    enterprise_features: bool = False
    webhook_enabled: bool = True
    audit_enabled: bool = True
    backup_enabled: bool = True
    mode: IntegrationMode = IntegrationMode.LIVE
    custom_mappings: Dict[str, Any] = field(default_factory=dict)
    sync_entities: List[str] = field(default_factory=list)
    excluded_entities: List[str] = field(default_factory=list)
    field_level_sync: bool = False
    incremental_sync: bool = True
    max_retry_attempts: int = 3
    timeout_seconds: int = 300
    rate_limit_requests_per_minute: int = 100
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class YardiIntegrationService:
    """
    Main Yardi Integration Service
    
    Coordinates all Yardi integration components and provides a unified interface
    for managing connections, synchronization, monitoring, and enterprise features.
    """
    
    def __init__(self):
        # Initialize all service components
        self.auth_service = YardiAuthService()
        self.api_client = YardiAPIClient(self.auth_service)
        self.mapping_service = YardiMappingService()
        self.sync_service = YardiSyncService(
            self.api_client, self.mapping_service, self.auth_service
        )
        self.webhook_service = YardiWebhookService(self.sync_service)
        self.scheduler_service = YardiSchedulerService(self.sync_service)
        self.enterprise_service = YardiEnterpriseService(
            self.api_client, self.sync_service, self.mapping_service
        )
        self.monitoring_service = YardiMonitoringService()
        
        # Integration state management
        self.active_connections: Dict[str, YardiConnection] = {}
        self.integration_configs: Dict[str, IntegrationConfiguration] = {}
        self.health_cache: Dict[str, IntegrationHealth] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Performance tracking
        self.request_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.sync_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Yardi Integration Service initialized")
    
    # =====================================================
    # CONNECTION MANAGEMENT
    # =====================================================
    
    def create_integration(self, organization_id: str, config: IntegrationConfiguration) -> Dict[str, Any]:
        """
        Create a new Yardi integration for an organization
        
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
            
            # Initialize monitoring
            self.monitoring_service.initialize_monitoring(organization_id, config)
            
            # Setup default mappings
            if config.yardi_product == YardiProductType.VOYAGER:
                self.mapping_service.setup_voyager_default_mappings(organization_id)
            elif config.yardi_product == YardiProductType.BREEZE:
                self.mapping_service.setup_breeze_default_mappings(organization_id)
            
            # Setup webhooks if enabled
            if config.webhook_enabled:
                webhook_result = self.webhook_service.setup_organization_webhooks(
                    organization_id, config.yardi_product
                )
                if not webhook_result['success']:
                    logger.warning(f"Webhook setup failed for {organization_id}: {webhook_result.get('error')}")
            
            logger.info(f"Yardi integration created for organization {organization_id}")
            
            return {
                "success": True,
                "integration_id": organization_id,
                "configuration": asdict(config),
                "next_steps": [
                    "Configure Yardi connection credentials",
                    "Test connection to Yardi system",
                    "Setup field mappings if needed",
                    "Enable synchronization"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to create Yardi integration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def connect_to_yardi(self, organization_id: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Establish connection to Yardi system
        
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
            
            # Create connection
            connection_result = self.auth_service.create_connection(
                organization_id=organization_id,
                yardi_product=config.yardi_product,
                connection_type=config.connection_type,
                connection_params=connection_params
            )
            
            if not connection_result['success']:
                return connection_result
            
            connection = connection_result['connection']
            
            # Test connection
            test_result = self.api_client.test_connection(connection.connection_id)
            if not test_result['success']:
                return {
                    "success": False,
                    "error": f"Connection test failed: {test_result.get('error')}"
                }
            
            # Store active connection
            self.active_connections[organization_id] = connection
            
            # Initialize sync service for this connection
            self.sync_service.initialize_connection(connection)
            
            # Log connection establishment
            self.monitoring_service.log_event(
                organization_id=organization_id,
                event_type="connection_established",
                details={
                    "yardi_product": config.yardi_product.value,
                    "connection_type": config.connection_type.value,
                    "company_info": test_result.get('company_info', {})
                }
            )
            
            logger.info(f"Successfully connected to Yardi for organization {organization_id}")
            
            return {
                "success": True,
                "connection_id": connection.connection_id,
                "yardi_product": config.yardi_product.value,
                "company_info": test_result.get('company_info', {}),
                "capabilities": test_result.get('capabilities', []),
                "message": "Successfully connected to Yardi"
            }
            
        except Exception as e:
            logger.error(f"Failed to connect to Yardi: {e}")
            self.monitoring_service.log_event(
                organization_id=organization_id,
                event_type="connection_failed",
                details={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_connection_status(self, organization_id: str) -> Dict[str, Any]:
        """Get current connection status"""
        try:
            connection = self.active_connections.get(organization_id)
            if not connection:
                return {
                    "connected": False,
                    "status": "not_connected",
                    "message": "No active Yardi connection"
                }
            
            # Test current connection
            test_result = self.api_client.test_connection(connection.connection_id)
            
            # Get recent activity
            recent_syncs = self.sync_service.get_recent_sync_jobs(organization_id, limit=5)
            
            return {
                "connected": test_result['success'],
                "connection_id": connection.connection_id,
                "yardi_product": connection.yardi_product.value,
                "company_name": connection.company_info.get('name', 'Unknown'),
                "status": test_result.get('status', 'unknown'),
                "last_activity": connection.last_activity_at.isoformat() if connection.last_activity_at else None,
                "uptime": self._calculate_uptime(organization_id),
                "recent_syncs": [asdict(sync) for sync in recent_syncs],
                "capabilities": test_result.get('capabilities', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                "connected": False,
                "status": "error",
                "error": str(e)
            }
    
    def disconnect_yardi(self, organization_id: str) -> Dict[str, Any]:
        """Disconnect from Yardi system"""
        try:
            connection = self.active_connections.get(organization_id)
            if not connection:
                return {
                    "success": True,
                    "message": "No active connection to disconnect"
                }
            
            # Stop any running sync jobs
            active_jobs = self.sync_service.get_active_sync_jobs(organization_id)
            for job in active_jobs:
                self.sync_service.cancel_sync_job(job.job_id)
            
            # Disable webhooks
            self.webhook_service.disable_organization_webhooks(organization_id)
            
            # Revoke connection
            revoke_result = self.auth_service.revoke_connection(connection.connection_id)
            
            # Remove from active connections
            del self.active_connections[organization_id]
            
            # Log disconnection
            self.monitoring_service.log_event(
                organization_id=organization_id,
                event_type="connection_disconnected",
                details={"revoke_success": revoke_result['success']}
            )
            
            return {
                "success": True,
                "message": "Successfully disconnected from Yardi"
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting from Yardi: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =====================================================
    # DATA SYNCHRONIZATION
    # =====================================================
    
    async def start_full_sync(self, organization_id: str, sync_direction: str = "both",
                             entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start comprehensive data synchronization
        
        Args:
            organization_id: Organization identifier
            sync_direction: 'to_yardi', 'from_yardi', or 'both'
            entity_types: List of entity types to sync (None for all)
            
        Returns:
            Dict with sync job information
        """
        try:
            connection = self.active_connections.get(organization_id)
            if not connection:
                return {
                    "success": False,
                    "error": "No active Yardi connection"
                }
            
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not configured"
                }
            
            # Determine entities to sync
            if entity_types is None:
                entity_types = config.sync_entities or [
                    "properties", "units", "tenants", "leases", 
                    "payments", "maintenance", "vendors"
                ]
            
            # Remove excluded entities
            entity_types = [e for e in entity_types if e not in config.excluded_entities]
            
            # Create sync job
            sync_job = await self.sync_service.create_sync_job(
                organization_id=organization_id,
                sync_direction=SyncDirection(sync_direction),
                entity_types=entity_types,
                sync_mode="full",
                priority="normal"
            )
            
            # Start sync execution
            execution_result = await self.sync_service.execute_sync_job(sync_job.job_id)
            
            # Log sync start
            self.monitoring_service.log_event(
                organization_id=organization_id,
                event_type="sync_started",
                details={
                    "job_id": sync_job.job_id,
                    "direction": sync_direction,
                    "entities": entity_types,
                    "mode": "full"
                }
            )
            
            return {
                "success": True,
                "job_id": sync_job.job_id,
                "sync_direction": sync_direction,
                "entity_types": entity_types,
                "estimated_duration": execution_result.get('estimated_duration'),
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
                                   entity_types: Optional[List[str]] = None,
                                   since_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Start incremental data synchronization
        
        Args:
            organization_id: Organization identifier
            entity_types: List of entity types to sync
            since_timestamp: Sync changes since this timestamp
            
        Returns:
            Dict with sync job information
        """
        try:
            connection = self.active_connections.get(organization_id)
            if not connection:
                return {
                    "success": False,
                    "error": "No active Yardi connection"
                }
            
            # Default to changes since last sync
            if since_timestamp is None:
                last_sync = self.sync_service.get_last_successful_sync(organization_id)
                since_timestamp = last_sync.completed_at if last_sync else datetime.utcnow() - timedelta(hours=24)
            
            # Create incremental sync job
            sync_job = await self.sync_service.create_sync_job(
                organization_id=organization_id,
                sync_direction=SyncDirection.BOTH,
                entity_types=entity_types,
                sync_mode="incremental",
                since_timestamp=since_timestamp,
                priority="normal"
            )
            
            # Execute sync
            execution_result = await self.sync_service.execute_sync_job(sync_job.job_id)
            
            return {
                "success": True,
                "job_id": sync_job.job_id,
                "sync_mode": "incremental",
                "since_timestamp": since_timestamp.isoformat(),
                "entity_types": entity_types,
                "status": "started"
            }
            
        except Exception as e:
            logger.error(f"Failed to start incremental sync: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_sync_status(self, organization_id: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get synchronization status"""
        try:
            if job_id:
                # Get specific job status
                job = self.sync_service.get_sync_job(job_id)
                if not job:
                    return {
                        "success": False,
                        "error": "Sync job not found"
                    }
                
                return {
                    "success": True,
                    "job": asdict(job),
                    "progress": self.sync_service.get_sync_progress(job_id)
                }
            else:
                # Get overall sync status
                active_jobs = self.sync_service.get_active_sync_jobs(organization_id)
                recent_jobs = self.sync_service.get_recent_sync_jobs(organization_id, limit=10)
                
                return {
                    "success": True,
                    "active_jobs": [asdict(job) for job in active_jobs],
                    "recent_jobs": [asdict(job) for job in recent_jobs],
                    "sync_enabled": self.integration_configs.get(organization_id, {}).sync_enabled,
                    "last_sync": recent_jobs[0].completed_at.isoformat() if recent_jobs and recent_jobs[0].completed_at else None
                }
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_sync(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running sync job"""
        try:
            result = self.sync_service.cancel_sync_job(job_id)
            return {
                "success": result,
                "message": "Sync job cancelled" if result else "Failed to cancel sync job"
            }
        except Exception as e:
            logger.error(f"Error cancelling sync job: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =====================================================
    # CONFIGURATION MANAGEMENT
    # =====================================================
    
    def update_integration_config(self, organization_id: str, 
                                config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update integration configuration"""
        try:
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not found"
                }
            
            # Update configuration
            for key, value in config_updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.utcnow()
            
            # Apply configuration changes
            if 'webhook_enabled' in config_updates:
                if config_updates['webhook_enabled']:
                    self.webhook_service.enable_organization_webhooks(organization_id)
                else:
                    self.webhook_service.disable_organization_webhooks(organization_id)
            
            if 'sync_entities' in config_updates or 'excluded_entities' in config_updates:
                # Update sync service configuration
                self.sync_service.update_sync_configuration(organization_id, config)
            
            return {
                "success": True,
                "updated_config": asdict(config),
                "message": "Integration configuration updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating integration config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_integration_config(self, organization_id: str) -> Dict[str, Any]:
        """Get current integration configuration"""
        try:
            config = self.integration_configs.get(organization_id)
            if not config:
                return {
                    "success": False,
                    "error": "Integration not found"
                }
            
            return {
                "success": True,
                "configuration": asdict(config)
            }
            
        except Exception as e:
            logger.error(f"Error getting integration config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =====================================================
    # HEALTH AND MONITORING
    # =====================================================
    
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
            webhook_health = self._get_webhook_health(organization_id)
            automation_health = self._get_automation_health(organization_id)
            performance_metrics = self._get_performance_metrics(organization_id)
            
            # Calculate data quality score
            data_quality_score = self._calculate_data_quality_score(organization_id)
            
            # Determine overall status
            overall_status = self._determine_overall_status(
                connection_health, sync_health, webhook_health, data_quality_score
            )
            
            # Collect issues and recommendations
            issues, warnings, recommendations = self._analyze_health_issues(
                connection_health, sync_health, webhook_health, data_quality_score
            )
            
            # Calculate uptime and error rates
            uptime_percentage = self._calculate_uptime(organization_id)
            error_rate = self._calculate_error_rate(organization_id)
            
            health = IntegrationHealth(
                status=overall_status,
                connection_health=connection_health,
                sync_health=sync_health,
                webhook_health=webhook_health,
                automation_health=automation_health,
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
                webhook_health={},
                automation_health={},
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
            
            # Get enterprise features status
            enterprise_status = {}
            if config and config.enterprise_features:
                enterprise_status = self.enterprise_service.get_enterprise_status(organization_id)
            
            return {
                "organization_id": organization_id,
                "overall_status": health.status.value,
                "health_score": health.data_quality_score,
                "uptime_percentage": health.uptime_percentage,
                "error_rate": health.error_rate,
                "connection": {
                    "connected": connection is not None,
                    "yardi_product": connection.yardi_product.value if connection else None,
                    "company_name": connection.company_info.get('name') if connection else None,
                    "last_activity": connection.last_activity_at.isoformat() if connection and connection.last_activity_at else None
                },
                "synchronization": {
                    "enabled": config.sync_enabled if config else False,
                    "active_jobs": len(active_jobs),
                    "recent_jobs": len(recent_syncs),
                    "last_sync": recent_syncs[0].completed_at.isoformat() if recent_syncs and recent_syncs[0].completed_at else None
                },
                "configuration": asdict(config) if config else {},
                "enterprise_features": enterprise_status,
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
    
    # =====================================================
    # PRIVATE HELPER METHODS
    # =====================================================
    
    def _validate_integration_config(self, config: IntegrationConfiguration) -> Dict[str, Any]:
        """Validate integration configuration"""
        errors = []
        
        if not config.integration_name:
            errors.append("Integration name is required")
        
        if not config.yardi_product:
            errors.append("Yardi product type is required")
        
        if not config.connection_type:
            errors.append("Connection type is required")
        
        if config.sync_entities and len(config.sync_entities) == 0:
            errors.append("At least one sync entity must be specified")
        
        if config.rate_limit_requests_per_minute < 1:
            errors.append("Rate limit must be at least 1 request per minute")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _get_connection_health(self, organization_id: str) -> Dict[str, Any]:
        """Get connection health status"""
        try:
            connection = self.active_connections.get(organization_id)
            if not connection:
                return {"status": "not_connected", "healthy": False}
            
            test_result = self.api_client.test_connection(connection.connection_id)
            return {
                "status": "connected" if test_result['success'] else "error",
                "healthy": test_result['success'],
                "response_time": test_result.get('response_time', 0),
                "last_test": datetime.utcnow().isoformat(),
                "details": test_result
            }
        except Exception as e:
            return {"status": "error", "healthy": False, "error": str(e)}
    
    def _get_sync_health(self, organization_id: str) -> Dict[str, Any]:
        """Get synchronization health status"""
        try:
            recent_jobs = self.sync_service.get_recent_sync_jobs(organization_id, limit=10)
            active_jobs = self.sync_service.get_active_sync_jobs(organization_id)
            failed_jobs = [job for job in recent_jobs if job.status == SyncStatus.FAILED]
            
            success_rate = 0
            if recent_jobs:
                successful_jobs = [job for job in recent_jobs if job.status == SyncStatus.COMPLETED]
                success_rate = (len(successful_jobs) / len(recent_jobs)) * 100
            
            return {
                "active_jobs": len(active_jobs),
                "recent_jobs": len(recent_jobs),
                "failed_jobs": len(failed_jobs),
                "success_rate": success_rate,
                "healthy": success_rate >= 80 and len(failed_jobs) < 3,
                "last_sync": recent_jobs[0].completed_at.isoformat() if recent_jobs and recent_jobs[0].completed_at else None
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _get_webhook_health(self, organization_id: str) -> Dict[str, Any]:
        """Get webhook health status"""
        try:
            webhook_status = self.webhook_service.get_webhook_status(organization_id)
            return {
                "enabled": webhook_status.get('enabled', False),
                "healthy": webhook_status.get('healthy', False),
                "recent_deliveries": webhook_status.get('recent_deliveries', 0),
                "failed_deliveries": webhook_status.get('failed_deliveries', 0),
                "last_delivery": webhook_status.get('last_delivery')
            }
        except Exception as e:
            return {"enabled": False, "healthy": False, "error": str(e)}
    
    def _get_automation_health(self, organization_id: str) -> Dict[str, Any]:
        """Get automation health status"""
        try:
            scheduler_status = self.scheduler_service.get_scheduler_status(organization_id)
            return {
                "enabled": scheduler_status.get('enabled', False),
                "active_schedules": scheduler_status.get('active_schedules', 0),
                "recent_executions": scheduler_status.get('recent_executions', 0),
                "failed_executions": scheduler_status.get('failed_executions', 0),
                "healthy": scheduler_status.get('healthy', False)
            }
        except Exception as e:
            return {"enabled": False, "healthy": False, "error": str(e)}
    
    def _get_performance_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            return self.monitoring_service.get_performance_metrics(organization_id)
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_data_quality_score(self, organization_id: str) -> float:
        """Calculate overall data quality score"""
        try:
            # This would involve checking data consistency, completeness, accuracy
            # For now, return a simple calculation based on sync success rates
            recent_jobs = self.sync_service.get_recent_sync_jobs(organization_id, limit=20)
            if not recent_jobs:
                return 100.0
            
            successful_jobs = [job for job in recent_jobs if job.status == SyncStatus.COMPLETED]
            return (len(successful_jobs) / len(recent_jobs)) * 100
            
        except Exception:
            return 0.0
    
    def _determine_overall_status(self, connection_health: Dict, sync_health: Dict,
                                webhook_health: Dict, data_quality_score: float) -> IntegrationStatus:
        """Determine overall integration status"""
        if not connection_health.get('healthy', False):
            return IntegrationStatus.ERROR
        
        if not sync_health.get('healthy', False):
            return IntegrationStatus.ERROR
        
        if data_quality_score < 70:
            return IntegrationStatus.ERROR
        
        if data_quality_score < 90:
            return IntegrationStatus.CONNECTED  # Connected but with warnings
        
        return IntegrationStatus.CONNECTED
    
    def _analyze_health_issues(self, connection_health: Dict, sync_health: Dict,
                             webhook_health: Dict, data_quality_score: float) -> Tuple[List[str], List[str], List[str]]:
        """Analyze health data and return issues, warnings, and recommendations"""
        issues = []
        warnings = []
        recommendations = []
        
        # Connection issues
        if not connection_health.get('healthy', False):
            issues.append("Yardi connection is not healthy")
            recommendations.append("Check Yardi connection and credentials")
        
        # Sync issues
        if sync_health.get('success_rate', 0) < 50:
            issues.append("Low sync success rate")
            recommendations.append("Review sync errors and resolve data conflicts")
        elif sync_health.get('success_rate', 0) < 80:
            warnings.append("Sync success rate below optimal")
            recommendations.append("Monitor sync jobs for potential issues")
        
        # Data quality issues
        if data_quality_score < 70:
            issues.append("Poor data quality score")
            recommendations.append("Perform data reconciliation and cleanup")
        elif data_quality_score < 90:
            warnings.append("Data quality could be improved")
            recommendations.append("Consider data validation rules")
        
        # Webhook issues
        if webhook_health.get('enabled', False) and not webhook_health.get('healthy', False):
            warnings.append("Webhook delivery issues detected")
            recommendations.append("Check webhook endpoints and connectivity")
        
        return issues, warnings, recommendations
    
    def _calculate_uptime(self, organization_id: str) -> float:
        """Calculate integration uptime percentage"""
        try:
            return self.monitoring_service.calculate_uptime(organization_id)
        except Exception:
            return 0.0
    
    def _calculate_error_rate(self, organization_id: str) -> float:
        """Calculate error rate percentage"""
        try:
            return self.monitoring_service.calculate_error_rate(organization_id)
        except Exception:
            return 0.0

# Global service instance
_yardi_integration_service = None

def get_yardi_integration_service() -> YardiIntegrationService:
    """Get singleton Yardi integration service instance"""
    global _yardi_integration_service
    if _yardi_integration_service is None:
        _yardi_integration_service = YardiIntegrationService()
    return _yardi_integration_service