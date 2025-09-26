"""
RentManager Sync Service

Comprehensive synchronization service for RentManager integration with support for
real-time sync, batch operations, compliance tracking, and multi-property management.
"""

import logging
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .rentmanager_auth_service import RentManagerAuthService
from .rentmanager_api_client import RentManagerAPIClient, RentManagerEntityType
from .rentmanager_mapping_service import RentManagerMappingService, MappingDirection
from .models import ComplianceType, PropertyType

logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    """Synchronization direction"""
    TO_ESTATECORE = "to_estatecore"
    TO_RENTMANAGER = "to_rentmanager"
    BIDIRECTIONAL = "bidirectional"

class SyncMode(Enum):
    """Synchronization mode"""
    FULL = "full"
    INCREMENTAL = "incremental"
    REAL_TIME = "real_time"
    MANUAL = "manual"

class SyncStatus(Enum):
    """Sync job status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    RENTMANAGER_WINS = "rentmanager_wins"
    ESTATECORE_WINS = "estatecore_wins"
    MANUAL_REVIEW = "manual_review"
    MERGE = "merge"
    SKIP = "skip"

@dataclass
class SyncJobConfiguration:
    """Sync job configuration"""
    organization_id: str
    job_name: str
    sync_direction: SyncDirection
    sync_mode: SyncMode
    entity_types: List[str]
    
    # Filtering and selection
    property_ids: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Timing configuration
    schedule: Optional[str] = None  # Cron expression
    since_timestamp: Optional[datetime] = None
    batch_size: int = 100
    
    # Conflict resolution
    conflict_resolution: ConflictResolution = ConflictResolution.MANUAL_REVIEW
    
    # Compliance configuration
    compliance_validation: bool = True
    compliance_types: List[ComplianceType] = field(default_factory=list)
    
    # Performance settings
    parallel_processing: bool = True
    max_workers: int = 5
    retry_count: int = 3
    timeout_seconds: int = 300
    
    # Data quality
    validate_before_sync: bool = True
    backup_before_sync: bool = True
    
    # Custom configuration
    custom_mappings: Dict[str, Any] = field(default_factory=dict)
    pre_sync_hooks: List[str] = field(default_factory=list)
    post_sync_hooks: List[str] = field(default_factory=list)

@dataclass
class SyncJob:
    """Sync job instance"""
    job_id: str
    organization_id: str
    configuration: SyncJobConfiguration
    status: SyncStatus
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress tracking
    total_entities: int = 0
    processed_entities: int = 0
    successful_entities: int = 0
    failed_entities: int = 0
    skipped_entities: int = 0
    
    # Results
    sync_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance metrics
    execution_time_seconds: Optional[float] = None
    entities_per_second: Optional[float] = None
    
    # Compliance tracking
    compliance_results: Dict[str, Any] = field(default_factory=dict)
    compliance_violations: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class SyncEntityResult:
    """Result of syncing individual entity"""
    entity_id: str
    entity_type: str
    status: str  # success, failed, skipped, conflict
    
    # Data
    source_data: Optional[Dict[str, Any]] = None
    target_data: Optional[Dict[str, Any]] = None
    mapped_data: Optional[Dict[str, Any]] = None
    
    # Results
    error_message: Optional[str] = None
    warning_messages: List[str] = field(default_factory=list)
    conflict_details: Optional[Dict[str, Any]] = None
    
    # Compliance
    compliance_status: Optional[Dict[str, Any]] = None
    
    # Timing
    processed_at: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = None

class RentManagerSyncService:
    """
    RentManager Synchronization Service
    
    Manages comprehensive data synchronization between RentManager and EstateCore
    with support for compliance tracking, multi-property management, and real-time sync.
    """
    
    def __init__(self, api_client: RentManagerAPIClient, 
                 mapping_service: RentManagerMappingService,
                 auth_service: RentManagerAuthService):
        self.api_client = api_client
        self.mapping_service = mapping_service
        self.auth_service = auth_service
        
        # Job management
        self.active_jobs: Dict[str, SyncJob] = {}
        self.job_history: Dict[str, List[SyncJob]] = {}
        self.scheduled_jobs: Dict[str, SyncJobConfiguration] = {}
        
        # Sync state tracking
        self.sync_states: Dict[str, Dict[str, Any]] = {}
        self.last_sync_timestamps: Dict[str, datetime] = {}
        self.conflict_registry: Dict[str, List[Dict[str, Any]]] = {}
        
        # Performance tracking
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.sync_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Compliance tracking
        self.compliance_monitors: Dict[str, Any] = {}
        self.compliance_audit_trail: Dict[str, List[Dict[str, Any]]] = {}
        
        # Configuration
        self.default_batch_size = 100
        self.max_concurrent_jobs = 5
        self.sync_timeout = 3600  # 1 hour
        
        logger.info("RentManager Sync Service initialized")
    
    # ===================================================
    # SYNC JOB MANAGEMENT
    # ===================================================
    
    async def create_sync_job(self, configuration: SyncJobConfiguration) -> SyncJob:
        """
        Create new sync job
        
        Args:
            configuration: Sync job configuration
            
        Returns:
            Created SyncJob
        """
        try:
            job_id = str(uuid.uuid4())
            
            sync_job = SyncJob(
                job_id=job_id,
                organization_id=configuration.organization_id,
                configuration=configuration,
                status=SyncStatus.PENDING
            )
            
            # Store job
            self.active_jobs[job_id] = sync_job
            
            # Initialize job history for organization
            if configuration.organization_id not in self.job_history:
                self.job_history[configuration.organization_id] = []
            
            logger.info(f"Created sync job {job_id} for organization {configuration.organization_id}")
            
            return sync_job
            
        except Exception as e:
            logger.error(f"Failed to create sync job: {e}")
            raise
    
    async def execute_sync_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute sync job
        
        Args:
            job_id: Sync job identifier
            
        Returns:
            Execution results
        """
        try:
            if job_id not in self.active_jobs:
                return {
                    "success": False,
                    "error": "Sync job not found"
                }
            
            sync_job = self.active_jobs[job_id]
            
            # Check if job already running
            if sync_job.status == SyncStatus.IN_PROGRESS:
                return {
                    "success": False,
                    "error": "Sync job already in progress"
                }
            
            # Update job status
            sync_job.status = SyncStatus.IN_PROGRESS
            sync_job.started_at = datetime.utcnow()
            
            # Execute sync based on mode
            if sync_job.configuration.sync_mode == SyncMode.FULL:
                result = await self._execute_full_sync(sync_job)
            elif sync_job.configuration.sync_mode == SyncMode.INCREMENTAL:
                result = await self._execute_incremental_sync(sync_job)
            elif sync_job.configuration.sync_mode == SyncMode.REAL_TIME:
                result = await self._execute_real_time_sync(sync_job)
            else:
                result = await self._execute_manual_sync(sync_job)
            
            # Update job status and metrics
            sync_job.completed_at = datetime.utcnow()
            if sync_job.started_at:
                sync_job.execution_time_seconds = (
                    sync_job.completed_at - sync_job.started_at
                ).total_seconds()
                
                if sync_job.execution_time_seconds > 0:
                    sync_job.entities_per_second = (
                        sync_job.processed_entities / sync_job.execution_time_seconds
                    )
            
            # Determine final status
            if result["success"]:
                sync_job.status = SyncStatus.COMPLETED
            else:
                sync_job.status = SyncStatus.FAILED
            
            # Move to job history
            self._archive_job(sync_job)
            
            logger.info(f"Sync job {job_id} completed with status {sync_job.status.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Sync job execution failed: {e}")
            
            # Update job status
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = SyncStatus.FAILED
                self.active_jobs[job_id].completed_at = datetime.utcnow()
                self.active_jobs[job_id].errors.append({
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                self._archive_job(self.active_jobs[job_id])
            
            return {
                "success": False,
                "error": str(e)
            }
    
    # ===================================================
    # SYNC EXECUTION METHODS
    # ===================================================
    
    async def _execute_full_sync(self, sync_job: SyncJob) -> Dict[str, Any]:
        """Execute full synchronization"""
        try:
            config = sync_job.configuration
            results = {"success": True, "entity_results": {}}
            
            # Get all entities to sync
            for entity_type in config.entity_types:
                entity_results = await self._sync_entity_type(
                    sync_job, entity_type, full_sync=True
                )
                results["entity_results"][entity_type] = entity_results
                
                if not entity_results["success"]:
                    results["success"] = False
            
            # Update sync state
            self._update_sync_state(config.organization_id, sync_job)
            
            return results
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_incremental_sync(self, sync_job: SyncJob) -> Dict[str, Any]:
        """Execute incremental synchronization"""
        try:
            config = sync_job.configuration
            results = {"success": True, "entity_results": {}}
            
            # Determine timestamp for incremental sync
            since_timestamp = config.since_timestamp
            if not since_timestamp:
                since_timestamp = self.last_sync_timestamps.get(
                    config.organization_id, 
                    datetime.utcnow() - timedelta(hours=24)
                )
            
            # Sync only changed entities
            for entity_type in config.entity_types:
                entity_results = await self._sync_entity_type(
                    sync_job, entity_type, since_timestamp=since_timestamp
                )
                results["entity_results"][entity_type] = entity_results
                
                if not entity_results["success"]:
                    results["success"] = False
            
            # Update sync timestamp
            if results["success"]:
                self.last_sync_timestamps[config.organization_id] = datetime.utcnow()
            
            return results
            
        except Exception as e:
            logger.error(f"Incremental sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _sync_entity_type(self, sync_job: SyncJob, entity_type: str,
                              full_sync: bool = False, 
                              since_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Sync specific entity type"""
        try:
            config = sync_job.configuration
            entity_results = {"success": True, "entities": [], "errors": []}
            
            # Map entity type to RentManager entity
            rentmanager_entity = self._map_entity_type(entity_type)
            if not rentmanager_entity:
                return {
                    "success": False,
                    "error": f"Unknown entity type: {entity_type}"
                }
            
            # Build filters
            filters = dict(config.filters)
            if config.property_ids:
                filters["property_id"] = config.property_ids
            if since_timestamp and not full_sync:
                filters["modified_since"] = since_timestamp.isoformat()
            
            # Get entities from RentManager
            offset = 0
            batch_size = config.batch_size
            
            while True:
                # Fetch batch
                response = await self._fetch_entity_batch(
                    config.organization_id, rentmanager_entity, 
                    filters, batch_size, offset
                )
                
                if not response.success:
                    entity_results["errors"].append({
                        "error": response.error,
                        "batch_offset": offset
                    })
                    break
                
                entities = response.data.get("entities", []) if response.data else []
                if not entities:
                    break
                
                # Update total count
                sync_job.total_entities += len(entities)
                
                # Process entities in parallel if enabled
                if config.parallel_processing:
                    entity_tasks = [
                        self._sync_individual_entity(
                            sync_job, entity_type, entity_data
                        )
                        for entity_data in entities
                    ]
                    
                    # Process with limited concurrency
                    semaphore = asyncio.Semaphore(config.max_workers)
                    
                    async def process_with_semaphore(task):
                        async with semaphore:
                            return await task
                    
                    batch_results = await asyncio.gather(
                        *[process_with_semaphore(task) for task in entity_tasks],
                        return_exceptions=True
                    )
                else:
                    # Process sequentially
                    batch_results = []
                    for entity_data in entities:
                        result = await self._sync_individual_entity(
                            sync_job, entity_type, entity_data
                        )
                        batch_results.append(result)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        entity_results["errors"].append({
                            "error": str(result),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        sync_job.failed_entities += 1
                    else:
                        entity_results["entities"].append(result)
                        
                        if result.status == "success":
                            sync_job.successful_entities += 1
                        elif result.status == "failed":
                            sync_job.failed_entities += 1
                        elif result.status == "skipped":
                            sync_job.skipped_entities += 1
                        elif result.status == "conflict":
                            sync_job.conflicts.append(asdict(result))
                    
                    sync_job.processed_entities += 1
                
                # Check if we should continue
                if len(entities) < batch_size:
                    break
                
                offset += batch_size
            
            return entity_results
            
        except Exception as e:
            logger.error(f"Entity type sync failed for {entity_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _sync_individual_entity(self, sync_job: SyncJob, entity_type: str,
                                    entity_data: Dict[str, Any]) -> SyncEntityResult:
        """Sync individual entity"""
        entity_id = entity_data.get("id", "unknown")
        start_time = datetime.utcnow()
        
        try:
            result = SyncEntityResult(
                entity_id=entity_id,
                entity_type=entity_type,
                status="success",
                source_data=entity_data
            )
            
            # Map data to EstateCore format
            mapping_result = self.mapping_service.map_to_estatecore(
                entity_type, entity_data, sync_job.organization_id
            )
            
            if not mapping_result.success:
                result.status = "failed"
                result.error_message = "; ".join(mapping_result.errors)
                result.warning_messages = mapping_result.warnings
                return result
            
            result.mapped_data = mapping_result.mapped_data
            result.compliance_status = mapping_result.compliance_status
            
            # Validate compliance if required
            if sync_job.configuration.compliance_validation:
                compliance_result = await self._validate_entity_compliance(
                    entity_data, entity_type, sync_job.configuration.compliance_types
                )
                
                if not compliance_result["compliant"]:
                    result.status = "failed"
                    result.error_message = "Compliance validation failed"
                    result.compliance_status = compliance_result
                    return result
            
            # Check for conflicts if bidirectional sync
            if sync_job.configuration.sync_direction == SyncDirection.BIDIRECTIONAL:
                conflict_result = await self._check_entity_conflicts(
                    entity_id, entity_type, mapping_result.mapped_data
                )
                
                if conflict_result["has_conflict"]:
                    result.status = "conflict"
                    result.conflict_details = conflict_result
                    
                    # Apply conflict resolution strategy
                    resolution_result = await self._resolve_entity_conflict(
                        conflict_result, sync_job.configuration.conflict_resolution
                    )
                    
                    if resolution_result["resolved"]:
                        result.status = "success"
                        result.target_data = resolution_result["resolved_data"]
                    else:
                        return result
            
            # Sync to EstateCore
            sync_result = await self._sync_to_estatecore(
                entity_type, result.mapped_data, sync_job.organization_id
            )
            
            if sync_result["success"]:
                result.target_data = sync_result["data"]
                result.status = "success"
            else:
                result.status = "failed"
                result.error_message = sync_result.get("error", "Sync failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Individual entity sync failed for {entity_id}: {e}")
            return SyncEntityResult(
                entity_id=entity_id,
                entity_type=entity_type,
                status="failed",
                source_data=entity_data,
                error_message=str(e)
            )
        finally:
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            if 'result' in locals():
                result.processing_time_ms = int(processing_time)
    
    # ===================================================
    # COMPLIANCE AND VALIDATION
    # ===================================================
    
    async def _validate_entity_compliance(self, entity_data: Dict[str, Any],
                                        entity_type: str,
                                        compliance_types: List[ComplianceType]) -> Dict[str, Any]:
        """Validate entity compliance requirements"""
        try:
            compliance_result = {
                "compliant": True,
                "violations": [],
                "warnings": [],
                "compliance_checks": {}
            }
            
            for compliance_type in compliance_types:
                # Validate compliance-specific requirements
                check_result = await self._check_compliance_type(
                    entity_data, entity_type, compliance_type
                )
                
                compliance_result["compliance_checks"][compliance_type.value] = check_result
                
                if not check_result.get("compliant", True):
                    compliance_result["compliant"] = False
                    compliance_result["violations"].extend(
                        check_result.get("violations", [])
                    )
                
                compliance_result["warnings"].extend(
                    check_result.get("warnings", [])
                )
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {e}")
            return {
                "compliant": False,
                "violations": [f"Compliance validation error: {str(e)}"],
                "warnings": [],
                "compliance_checks": {}
            }
    
    async def _check_compliance_type(self, entity_data: Dict[str, Any],
                                   entity_type: str,
                                   compliance_type: ComplianceType) -> Dict[str, Any]:
        """Check specific compliance type requirements"""
        try:
            if compliance_type == ComplianceType.LIHTC:
                return await self._check_lihtc_compliance(entity_data, entity_type)
            elif compliance_type == ComplianceType.SECTION_8:
                return await self._check_section8_compliance(entity_data, entity_type)
            elif compliance_type == ComplianceType.HUD:
                return await self._check_hud_compliance(entity_data, entity_type)
            else:
                return {"compliant": True, "violations": [], "warnings": []}
                
        except Exception as e:
            return {
                "compliant": False,
                "violations": [f"Compliance check failed: {str(e)}"],
                "warnings": []
            }
    
    async def _check_lihtc_compliance(self, entity_data: Dict[str, Any],
                                    entity_type: str) -> Dict[str, Any]:
        """Check LIHTC compliance requirements"""
        violations = []
        warnings = []
        
        # Example LIHTC compliance checks
        if entity_type == "resident":
            # Check income certification
            if not entity_data.get("income_certification"):
                violations.append("Missing LIHTC income certification")
            
            # Check AMI percentage
            ami_percentage = entity_data.get("ami_percentage")
            if ami_percentage and ami_percentage > 60:
                violations.append(f"AMI percentage {ami_percentage}% exceeds LIHTC limit")
        
        elif entity_type == "unit":
            # Check rent limits
            current_rent = entity_data.get("current_rent", 0)
            rent_limit = entity_data.get("rent_limit", 0)
            
            if current_rent > rent_limit:
                violations.append(f"Rent ${current_rent} exceeds LIHTC limit ${rent_limit}")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    async def _check_section8_compliance(self, entity_data: Dict[str, Any],
                                       entity_type: str) -> Dict[str, Any]:
        """Check Section 8 compliance requirements"""
        violations = []
        warnings = []
        
        # Example Section 8 compliance checks
        if entity_type == "resident":
            # Check voucher information
            if not entity_data.get("voucher_number"):
                violations.append("Missing Section 8 voucher number")
            
            # Check HAP contract
            if not entity_data.get("hap_contract"):
                violations.append("Missing HAP contract information")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    async def _check_hud_compliance(self, entity_data: Dict[str, Any],
                                  entity_type: str) -> Dict[str, Any]:
        """Check HUD compliance requirements"""
        violations = []
        warnings = []
        
        # Example HUD compliance checks
        if entity_type == "property":
            # Check required inspections
            last_inspection = entity_data.get("last_inspection")
            if not last_inspection:
                violations.append("Missing HUD property inspection")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    # ===================================================
    # UTILITY METHODS
    # ===================================================
    
    def get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID"""
        return self.active_jobs.get(job_id)
    
    def get_active_sync_jobs(self, organization_id: str) -> List[SyncJob]:
        """Get active sync jobs for organization"""
        return [
            job for job in self.active_jobs.values()
            if job.organization_id == organization_id
        ]
    
    def get_recent_sync_jobs(self, organization_id: str, limit: int = 10) -> List[SyncJob]:
        """Get recent sync jobs for organization"""
        if organization_id not in self.job_history:
            return []
        
        jobs = self.job_history[organization_id]
        return sorted(jobs, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def cancel_sync_job(self, job_id: str) -> bool:
        """Cancel running sync job"""
        try:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                if job.status == SyncStatus.IN_PROGRESS:
                    job.status = SyncStatus.CANCELLED
                    job.completed_at = datetime.utcnow()
                    self._archive_job(job)
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to cancel sync job: {e}")
            return False
    
    def get_sync_progress(self, job_id: str) -> Dict[str, Any]:
        """Get sync job progress"""
        job = self.get_sync_job(job_id)
        if not job:
            return {"error": "Job not found"}
        
        progress = 0
        if job.total_entities > 0:
            progress = (job.processed_entities / job.total_entities) * 100
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "progress_percentage": round(progress, 2),
            "total_entities": job.total_entities,
            "processed_entities": job.processed_entities,
            "successful_entities": job.successful_entities,
            "failed_entities": job.failed_entities,
            "skipped_entities": job.skipped_entities,
            "conflicts": len(job.conflicts),
            "estimated_completion": self._estimate_completion_time(job)
        }
    
    # ===================================================
    # HELPER METHODS
    # ===================================================
    
    def _map_entity_type(self, entity_type: str) -> Optional[RentManagerEntityType]:
        """Map entity type to RentManager entity type"""
        mapping = {
            "property": RentManagerEntityType.PROPERTIES,
            "unit": RentManagerEntityType.UNITS,
            "resident": RentManagerEntityType.RESIDENTS,
            "tenant": RentManagerEntityType.RESIDENTS,
            "lease": RentManagerEntityType.LEASES,
            "payment": RentManagerEntityType.PAYMENTS,
            "work_order": RentManagerEntityType.WORK_ORDERS,
            "vendor": RentManagerEntityType.VENDORS
        }
        return mapping.get(entity_type)
    
    async def _fetch_entity_batch(self, organization_id: str, 
                                entity_type: RentManagerEntityType,
                                filters: Dict[str, Any], 
                                limit: int, offset: int):
        """Fetch batch of entities from RentManager"""
        if entity_type == RentManagerEntityType.PROPERTIES:
            return await self.api_client.get_properties(
                organization_id, filters, limit, offset
            )
        elif entity_type == RentManagerEntityType.UNITS:
            return await self.api_client.get_units(
                organization_id, filters=filters, limit=limit, offset=offset
            )
        elif entity_type == RentManagerEntityType.RESIDENTS:
            return await self.api_client.get_residents(
                organization_id, filters, limit, offset
            )
        # Add other entity types as needed
        else:
            return {"success": False, "error": f"Unsupported entity type: {entity_type}"}
    
    def _archive_job(self, job: SyncJob):
        """Move job from active to history"""
        try:
            # Remove from active jobs
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
            
            # Add to history
            if job.organization_id not in self.job_history:
                self.job_history[job.organization_id] = []
            
            self.job_history[job.organization_id].append(job)
            
            # Keep only recent jobs in history (limit to 100)
            if len(self.job_history[job.organization_id]) > 100:
                self.job_history[job.organization_id] = sorted(
                    self.job_history[job.organization_id],
                    key=lambda x: x.created_at,
                    reverse=True
                )[:100]
            
        except Exception as e:
            logger.error(f"Failed to archive job: {e}")
    
    def _update_sync_state(self, organization_id: str, sync_job: SyncJob):
        """Update sync state for organization"""
        if organization_id not in self.sync_states:
            self.sync_states[organization_id] = {}
        
        self.sync_states[organization_id].update({
            "last_sync_job_id": sync_job.job_id,
            "last_sync_timestamp": datetime.utcnow(),
            "last_sync_status": sync_job.status.value,
            "entities_synced": sync_job.successful_entities,
            "sync_mode": sync_job.configuration.sync_mode.value
        })
    
    def _estimate_completion_time(self, job: SyncJob) -> Optional[str]:
        """Estimate job completion time"""
        if job.status != SyncStatus.IN_PROGRESS or not job.started_at:
            return None
        
        if job.processed_entities == 0:
            return None
        
        elapsed = (datetime.utcnow() - job.started_at).total_seconds()
        rate = job.processed_entities / elapsed
        remaining = job.total_entities - job.processed_entities
        
        if rate > 0:
            estimated_seconds = remaining / rate
            estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
            return estimated_completion.isoformat()
        
        return None
    
    # Placeholder methods for completeness
    async def _execute_real_time_sync(self, sync_job: SyncJob) -> Dict[str, Any]:
        return {"success": True, "message": "Real-time sync started"}
    
    async def _execute_manual_sync(self, sync_job: SyncJob) -> Dict[str, Any]:
        return {"success": True, "message": "Manual sync completed"}
    
    async def _check_entity_conflicts(self, entity_id: str, entity_type: str, 
                                    mapped_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"has_conflict": False}
    
    async def _resolve_entity_conflict(self, conflict_result: Dict[str, Any],
                                     resolution_strategy: ConflictResolution) -> Dict[str, Any]:
        return {"resolved": True, "resolved_data": {}}
    
    async def _sync_to_estatecore(self, entity_type: str, mapped_data: Dict[str, Any],
                                organization_id: str) -> Dict[str, Any]:
        return {"success": True, "data": mapped_data}

# Global service instance
_sync_service = None

def get_rentmanager_sync_service(api_client=None, mapping_service=None, auth_service=None):
    """Get singleton sync service instance"""
    global _sync_service
    if _sync_service is None:
        if not all([api_client, mapping_service, auth_service]):
            # Import here to avoid circular imports
            from .rentmanager_auth_service import get_rentmanager_auth_service
            from .rentmanager_api_client import get_rentmanager_api_client
            from .rentmanager_mapping_service import get_rentmanager_mapping_service
            
            auth_service = auth_service or get_rentmanager_auth_service()
            api_client = api_client or get_rentmanager_api_client(auth_service)
            mapping_service = mapping_service or get_rentmanager_mapping_service()
        
        _sync_service = RentManagerSyncService(api_client, mapping_service, auth_service)
    return _sync_service