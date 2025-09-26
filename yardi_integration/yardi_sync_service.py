"""
Yardi Synchronization Service

Comprehensive bidirectional data synchronization engine with conflict resolution,
data transformation, and enterprise-grade error handling.
"""

import os
import logging
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, PriorityQueue
import time

from .models import (
    YardiProductType, SyncDirection, SyncStatus, SyncMode,
    ConflictResolutionStrategy, YardiEntityType, YardiSyncJob,
    YardiSyncRecord, YardiEntityInfo, YardiSyncProgress, YardiConflictInfo
)

logger = logging.getLogger(__name__)

class SyncJobPriority(Enum):
    """Sync job priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0

class DataValidationLevel(Enum):
    """Data validation levels"""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    ENTERPRISE = "enterprise"

@dataclass
class SyncJob:
    """Sync job data class"""
    job_id: str
    organization_id: str
    connection_id: str
    sync_direction: SyncDirection
    sync_mode: SyncMode
    entity_types: List[str]
    status: SyncStatus = SyncStatus.PENDING
    priority: SyncJobPriority = SyncJobPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0
    error_message: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    since_timestamp: Optional[datetime] = None
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority.value < other.priority.value

@dataclass
class SyncConfiguration:
    """Synchronization configuration"""
    organization_id: str
    batch_size: int = 100
    parallel_workers: int = 4
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    timeout: int = 300  # seconds
    validation_level: DataValidationLevel = DataValidationLevel.BASIC
    conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.MANUAL_REVIEW
    backup_enabled: bool = True
    rollback_enabled: bool = True
    incremental_sync_enabled: bool = True
    real_time_sync_enabled: bool = False
    webhook_notifications: bool = True
    email_notifications: bool = True
    sync_filters: Dict[str, Any] = field(default_factory=dict)
    field_mappings: Dict[str, Any] = field(default_factory=dict)
    transformation_rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConflictRecord:
    """Data conflict record"""
    conflict_id: str
    entity_type: str
    entity_id: str
    estatecore_data: Dict[str, Any]
    yardi_data: Dict[str, Any]
    conflict_fields: List[str]
    conflict_reason: str
    suggested_resolution: ConflictResolutionStrategy
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_data: Optional[Dict[str, Any]] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

class YardiSyncService:
    """
    Yardi Synchronization Service
    
    Manages bidirectional data synchronization between EstateCore and Yardi systems
    with advanced conflict resolution, error handling, and performance optimization.
    """
    
    def __init__(self, api_client, mapping_service, auth_service):
        self.api_client = api_client
        self.mapping_service = mapping_service
        self.auth_service = auth_service
        
        # Sync state management
        self.active_jobs: Dict[str, SyncJob] = {}
        self.job_queue = PriorityQueue()
        self.sync_configurations: Dict[str, SyncConfiguration] = {}
        self.conflict_records: Dict[str, ConflictRecord] = {}
        
        # Threading and execution
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.job_processor_running = False
        self.processor_thread = None
        
        # Performance tracking
        self.sync_metrics: Dict[str, Any] = {}
        self.performance_cache: Dict[str, Any] = {}
        
        # Entity processors
        self.entity_processors = self._initialize_entity_processors()
        
        logger.info("Yardi Sync Service initialized")
    
    def _initialize_entity_processors(self) -> Dict[YardiEntityType, Callable]:
        """Initialize entity-specific sync processors"""
        return {
            YardiEntityType.PROPERTIES: self._sync_properties,
            YardiEntityType.UNITS: self._sync_units,
            YardiEntityType.TENANTS: self._sync_tenants,
            YardiEntityType.LEASES: self._sync_leases,
            YardiEntityType.PAYMENTS: self._sync_payments,
            YardiEntityType.WORK_ORDERS: self._sync_work_orders,
            YardiEntityType.VENDORS: self._sync_vendors,
            YardiEntityType.INVOICES: self._sync_invoices
        }
    
    # =====================================================
    # SYNC JOB MANAGEMENT
    # =====================================================
    
    async def create_sync_job(self, organization_id: str, sync_direction: SyncDirection,
                            entity_types: List[str], sync_mode: SyncMode = SyncMode.INCREMENTAL,
                            priority: SyncJobPriority = SyncJobPriority.NORMAL,
                            since_timestamp: Optional[datetime] = None,
                            configuration: Optional[Dict[str, Any]] = None) -> SyncJob:
        """Create a new sync job"""
        
        job_id = f"sync_{organization_id}_{uuid.uuid4().hex[:8]}"
        
        # Get connection for organization
        connection = self.auth_service.get_organization_connection(organization_id)
        if not connection:
            raise ValueError("No active Yardi connection found for organization")
        
        # Create sync job
        job = SyncJob(
            job_id=job_id,
            organization_id=organization_id,
            connection_id=connection.connection_id,
            sync_direction=sync_direction,
            sync_mode=sync_mode,
            entity_types=entity_types,
            priority=priority,
            since_timestamp=since_timestamp,
            configuration=configuration or {}
        )
        
        # Store job
        self.active_jobs[job_id] = job
        
        # Add to processing queue
        self.job_queue.put(job)
        
        # Start job processor if not running
        if not self.job_processor_running:
            self._start_job_processor()
        
        logger.info(f"Created sync job {job_id} for organization {organization_id}")
        
        return job
    
    async def execute_sync_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a specific sync job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return {
                "success": False,
                "error": "Sync job not found"
            }
        
        try:
            # Update job status
            job.status = SyncStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            # Get sync configuration
            config = self.sync_configurations.get(job.organization_id, SyncConfiguration(job.organization_id))
            
            # Execute sync based on direction
            results = {}
            
            if job.sync_direction in [SyncDirection.TO_YARDI, SyncDirection.BOTH]:
                results['to_yardi'] = await self._sync_to_yardi(job, config)
            
            if job.sync_direction in [SyncDirection.FROM_YARDI, SyncDirection.BOTH]:
                results['from_yardi'] = await self._sync_from_yardi(job, config)
            
            # Update job completion
            job.status = SyncStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100.0
            
            # Calculate estimated duration for future jobs
            duration = (job.completed_at - job.started_at).total_seconds()
            
            logger.info(f"Sync job {job_id} completed successfully in {duration:.2f} seconds")
            
            return {
                "success": True,
                "job_id": job_id,
                "results": results,
                "duration": duration,
                "estimated_duration": duration  # For display
            }
            
        except Exception as e:
            job.status = SyncStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            
            logger.error(f"Sync job {job_id} failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "job_id": job_id
            }
    
    def cancel_sync_job(self, job_id: str) -> bool:
        """Cancel a running sync job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return False
        
        if job.status == SyncStatus.RUNNING:
            job.status = SyncStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            logger.info(f"Cancelled sync job {job_id}")
            return True
        
        return False
    
    def get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID"""
        return self.active_jobs.get(job_id)
    
    def get_active_sync_jobs(self, organization_id: str) -> List[SyncJob]:
        """Get active sync jobs for organization"""
        return [
            job for job in self.active_jobs.values()
            if job.organization_id == organization_id and job.status == SyncStatus.RUNNING
        ]
    
    def get_recent_sync_jobs(self, organization_id: str, limit: int = 10) -> List[SyncJob]:
        """Get recent sync jobs for organization"""
        jobs = [
            job for job in self.active_jobs.values()
            if job.organization_id == organization_id
        ]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)[:limit]
    
    def get_last_successful_sync(self, organization_id: str) -> Optional[SyncJob]:
        """Get last successful sync job"""
        jobs = [
            job for job in self.active_jobs.values()
            if job.organization_id == organization_id and job.status == SyncStatus.COMPLETED
        ]
        return max(jobs, key=lambda j: j.completed_at) if jobs else None
    
    def get_sync_progress(self, job_id: str) -> Dict[str, Any]:
        """Get sync job progress"""
        job = self.active_jobs.get(job_id)
        if not job:
            return {"error": "Job not found"}
        
        return {
            "job_id": job_id,
            "status": job.status.value,
            "progress_percentage": job.progress_percentage,
            "total_records": job.total_records,
            "processed_records": job.processed_records,
            "successful_records": job.successful_records,
            "failed_records": job.failed_records,
            "skipped_records": job.skipped_records,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "estimated_completion": self._estimate_completion(job),
            "current_entity": self._get_current_entity(job)
        }
    
    # =====================================================
    # SYNCHRONIZATION EXECUTION
    # =====================================================
    
    async def _sync_to_yardi(self, job: SyncJob, config: SyncConfiguration) -> Dict[str, Any]:
        """Sync data from EstateCore to Yardi"""
        results = {}
        
        for entity_type in job.entity_types:
            try:
                entity_enum = YardiEntityType(entity_type)
                
                # Get EstateCore data
                estatecore_data = await self._get_estatecore_data(
                    job.organization_id, entity_enum, job.since_timestamp
                )
                
                if not estatecore_data:
                    results[entity_type] = {"status": "skipped", "reason": "no_data"}
                    continue
                
                # Process entities in batches
                batch_results = await self._process_entity_batch(
                    job, entity_enum, estatecore_data, SyncDirection.TO_YARDI, config
                )
                
                results[entity_type] = batch_results
                
            except Exception as e:
                logger.error(f"Failed to sync {entity_type} to Yardi: {e}")
                results[entity_type] = {"status": "error", "error": str(e)}
        
        return results
    
    async def _sync_from_yardi(self, job: SyncJob, config: SyncConfiguration) -> Dict[str, Any]:
        """Sync data from Yardi to EstateCore"""
        results = {}
        
        for entity_type in job.entity_types:
            try:
                entity_enum = YardiEntityType(entity_type)
                
                # Get Yardi data
                yardi_data = await self._get_yardi_data(
                    job.connection_id, entity_enum, job.since_timestamp
                )
                
                if not yardi_data:
                    results[entity_type] = {"status": "skipped", "reason": "no_data"}
                    continue
                
                # Process entities in batches
                batch_results = await self._process_entity_batch(
                    job, entity_enum, yardi_data, SyncDirection.FROM_YARDI, config
                )
                
                results[entity_type] = batch_results
                
            except Exception as e:
                logger.error(f"Failed to sync {entity_type} from Yardi: {e}")
                results[entity_type] = {"status": "error", "error": str(e)}
        
        return results
    
    async def _process_entity_batch(self, job: SyncJob, entity_type: YardiEntityType,
                                  data: List[Dict[str, Any]], direction: SyncDirection,
                                  config: SyncConfiguration) -> Dict[str, Any]:
        """Process a batch of entities"""
        
        total_records = len(data)
        processed = 0
        successful = 0
        failed = 0
        skipped = 0
        conflicts = []
        
        # Update job totals
        job.total_records += total_records
        
        # Process in batches
        for i in range(0, total_records, config.batch_size):
            batch = data[i:i + config.batch_size]
            
            # Process batch in parallel
            tasks = []
            for record in batch:
                task = self._process_single_entity(
                    job, entity_type, record, direction, config
                )
                tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                processed += 1
                job.processed_records += 1
                
                if isinstance(result, Exception):
                    failed += 1
                    job.failed_records += 1
                elif result.get('status') == 'success':
                    successful += 1
                    job.successful_records += 1
                elif result.get('status') == 'conflict':
                    conflicts.append(result)
                    skipped += 1
                    job.skipped_records += 1
                else:
                    skipped += 1
                    job.skipped_records += 1
            
            # Update progress
            job.progress_percentage = (job.processed_records / job.total_records) * 100
            
            # Check for cancellation
            if job.status == SyncStatus.CANCELLED:
                break
        
        return {
            "entity_type": entity_type.value,
            "direction": direction.value,
            "total_records": total_records,
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "conflicts": len(conflicts),
            "conflict_details": conflicts
        }
    
    async def _process_single_entity(self, job: SyncJob, entity_type: YardiEntityType,
                                   record: Dict[str, Any], direction: SyncDirection,
                                   config: SyncConfiguration) -> Dict[str, Any]:
        """Process a single entity record"""
        
        try:
            # Transform data using mapping service
            if direction == SyncDirection.TO_YARDI:
                transformed_data = self.mapping_service.transform_to_yardi(
                    job.organization_id, entity_type, record
                )
                target_system = "Yardi"
            else:
                transformed_data = self.mapping_service.transform_to_estatecore(
                    job.organization_id, entity_type, record
                )
                target_system = "EstateCore"
            
            # Validate data
            if config.validation_level != DataValidationLevel.NONE:
                validation_result = self._validate_entity_data(
                    entity_type, transformed_data, config.validation_level
                )
                if not validation_result['valid']:
                    return {
                        "status": "validation_failed",
                        "entity_id": record.get('id'),
                        "errors": validation_result['errors']
                    }
            
            # Check for conflicts
            conflict = await self._detect_conflicts(
                job.organization_id, entity_type, record, direction
            )
            
            if conflict:
                # Handle conflict based on resolution strategy
                resolution_result = await self._handle_conflict(
                    conflict, config.conflict_resolution
                )
                if resolution_result['action'] == 'skip':
                    return {
                        "status": "conflict",
                        "entity_id": record.get('id'),
                        "conflict_id": conflict.conflict_id
                    }
                elif resolution_result['action'] == 'resolve':
                    transformed_data = resolution_result['resolved_data']
            
            # Execute the sync operation
            if direction == SyncDirection.TO_YARDI:
                result = await self._write_to_yardi(
                    job.connection_id, entity_type, transformed_data
                )
            else:
                result = await self._write_to_estatecore(
                    job.organization_id, entity_type, transformed_data
                )
            
            return {
                "status": "success",
                "entity_id": record.get('id'),
                "target_id": result.get('id'),
                "operation": result.get('operation', 'upsert')
            }
            
        except Exception as e:
            logger.error(f"Failed to process {entity_type.value} entity: {e}")
            return {
                "status": "error",
                "entity_id": record.get('id'),
                "error": str(e)
            }
    
    # =====================================================
    # DATA RETRIEVAL METHODS
    # =====================================================
    
    async def _get_estatecore_data(self, organization_id: str, entity_type: YardiEntityType,
                                 since_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get data from EstateCore database"""
        
        # This would integrate with EstateCore's data layer
        # For now, return mock data structure
        
        filters = {"organization_id": organization_id}
        if since_timestamp:
            filters["updated_at__gte"] = since_timestamp
        
        # Entity-specific data retrieval
        if entity_type == YardiEntityType.PROPERTIES:
            return await self._get_estatecore_properties(filters)
        elif entity_type == YardiEntityType.UNITS:
            return await self._get_estatecore_units(filters)
        elif entity_type == YardiEntityType.TENANTS:
            return await self._get_estatecore_tenants(filters)
        elif entity_type == YardiEntityType.LEASES:
            return await self._get_estatecore_leases(filters)
        elif entity_type == YardiEntityType.PAYMENTS:
            return await self._get_estatecore_payments(filters)
        elif entity_type == YardiEntityType.WORK_ORDERS:
            return await self._get_estatecore_work_orders(filters)
        else:
            return []
    
    async def _get_yardi_data(self, connection_id: str, entity_type: YardiEntityType,
                            since_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get data from Yardi system"""
        
        filters = {}
        if since_timestamp:
            filters["modified_since"] = since_timestamp.isoformat()
        
        # Use entity-specific API methods
        if entity_type == YardiEntityType.PROPERTIES:
            response = await self.api_client.get_properties(connection_id, filters)
        elif entity_type == YardiEntityType.UNITS:
            response = await self.api_client.get_units(connection_id, filters=filters)
        elif entity_type == YardiEntityType.TENANTS:
            response = await self.api_client.get_tenants(connection_id, filters)
        elif entity_type == YardiEntityType.LEASES:
            response = await self.api_client.get_leases(connection_id, filters)
        elif entity_type == YardiEntityType.PAYMENTS:
            response = await self.api_client.get_payments(connection_id, filters)
        elif entity_type == YardiEntityType.WORK_ORDERS:
            response = await self.api_client.get_work_orders(connection_id, filters)
        else:
            return []
        
        if response.success:
            return response.data if isinstance(response.data, list) else [response.data]
        else:
            logger.error(f"Failed to get {entity_type.value} from Yardi: {response.error_message}")
            return []
    
    # =====================================================
    # CONFLICT DETECTION AND RESOLUTION
    # =====================================================
    
    async def _detect_conflicts(self, organization_id: str, entity_type: YardiEntityType,
                              record: Dict[str, Any], direction: SyncDirection) -> Optional[ConflictRecord]:
        """Detect data conflicts"""
        
        entity_id = record.get('id')
        if not entity_id:
            return None
        
        try:
            # Get corresponding record from other system
            if direction == SyncDirection.TO_YARDI:
                # Check if Yardi has newer version
                yardi_record = await self._get_yardi_record(entity_type, entity_id)
                if yardi_record:
                    return self._compare_records(record, yardi_record, entity_type, direction)
            else:
                # Check if EstateCore has newer version
                estatecore_record = await self._get_estatecore_record(entity_type, entity_id)
                if estatecore_record:
                    return self._compare_records(estatecore_record, record, entity_type, direction)
            
            return None
            
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return None
    
    def _compare_records(self, record1: Dict[str, Any], record2: Dict[str, Any],
                        entity_type: YardiEntityType, direction: SyncDirection) -> Optional[ConflictRecord]:
        """Compare two records for conflicts"""
        
        # Get critical fields for conflict detection
        critical_fields = self._get_critical_fields(entity_type)
        
        conflict_fields = []
        for field in critical_fields:
            if field in record1 and field in record2:
                if record1[field] != record2[field]:
                    conflict_fields.append(field)
        
        if conflict_fields:
            conflict_id = f"conflict_{uuid.uuid4().hex[:8]}"
            
            conflict = ConflictRecord(
                conflict_id=conflict_id,
                entity_type=entity_type.value,
                entity_id=record1.get('id', 'unknown'),
                estatecore_data=record1 if direction == SyncDirection.TO_YARDI else record2,
                yardi_data=record2 if direction == SyncDirection.TO_YARDI else record1,
                conflict_fields=conflict_fields,
                conflict_reason=f"Field conflicts detected: {', '.join(conflict_fields)}",
                suggested_resolution=ConflictResolutionStrategy.MANUAL_REVIEW
            )
            
            # Store conflict for manual resolution
            self.conflict_records[conflict_id] = conflict
            
            return conflict
        
        return None
    
    async def _handle_conflict(self, conflict: ConflictRecord,
                             resolution_strategy: ConflictResolutionStrategy) -> Dict[str, Any]:
        """Handle data conflict based on resolution strategy"""
        
        if resolution_strategy == ConflictResolutionStrategy.YARDI_WINS:
            return {
                "action": "resolve",
                "resolved_data": conflict.yardi_data
            }
        
        elif resolution_strategy == ConflictResolutionStrategy.ESTATECORE_WINS:
            return {
                "action": "resolve",
                "resolved_data": conflict.estatecore_data
            }
        
        elif resolution_strategy == ConflictResolutionStrategy.MERGE:
            merged_data = self._merge_conflict_data(conflict)
            return {
                "action": "resolve",
                "resolved_data": merged_data
            }
        
        elif resolution_strategy == ConflictResolutionStrategy.SKIP:
            return {"action": "skip"}
        
        else:  # MANUAL_REVIEW
            return {"action": "skip"}
    
    def _merge_conflict_data(self, conflict: ConflictRecord) -> Dict[str, Any]:
        """Merge conflicting data using intelligent rules"""
        
        # Start with EstateCore data
        merged = conflict.estatecore_data.copy()
        
        # Apply merge rules based on entity type and field types
        merge_rules = self._get_merge_rules(conflict.entity_type)
        
        for field in conflict.conflict_fields:
            if field in merge_rules:
                rule = merge_rules[field]
                
                if rule == "latest_wins":
                    # Use the record with latest timestamp
                    ec_timestamp = conflict.estatecore_data.get('updated_at')
                    yardi_timestamp = conflict.yardi_data.get('updated_at')
                    
                    if yardi_timestamp and ec_timestamp:
                        if yardi_timestamp > ec_timestamp:
                            merged[field] = conflict.yardi_data[field]
                
                elif rule == "yardi_wins":
                    merged[field] = conflict.yardi_data[field]
                
                elif rule == "non_empty_wins":
                    yardi_value = conflict.yardi_data.get(field)
                    if yardi_value and str(yardi_value).strip():
                        merged[field] = yardi_value
        
        return merged
    
    # =====================================================
    # ENTITY-SPECIFIC PROCESSORS
    # =====================================================
    
    async def _sync_properties(self, job: SyncJob, properties: List[Dict[str, Any]],
                             direction: SyncDirection) -> Dict[str, Any]:
        """Sync properties"""
        # Implementation specific to properties
        return {"status": "completed", "processed": len(properties)}
    
    async def _sync_units(self, job: SyncJob, units: List[Dict[str, Any]],
                        direction: SyncDirection) -> Dict[str, Any]:
        """Sync units"""
        # Implementation specific to units
        return {"status": "completed", "processed": len(units)}
    
    async def _sync_tenants(self, job: SyncJob, tenants: List[Dict[str, Any]],
                          direction: SyncDirection) -> Dict[str, Any]:
        """Sync tenants"""
        # Implementation specific to tenants
        return {"status": "completed", "processed": len(tenants)}
    
    async def _sync_leases(self, job: SyncJob, leases: List[Dict[str, Any]],
                         direction: SyncDirection) -> Dict[str, Any]:
        """Sync leases"""
        # Implementation specific to leases
        return {"status": "completed", "processed": len(leases)}
    
    async def _sync_payments(self, job: SyncJob, payments: List[Dict[str, Any]],
                           direction: SyncDirection) -> Dict[str, Any]:
        """Sync payments"""
        # Implementation specific to payments
        return {"status": "completed", "processed": len(payments)}
    
    async def _sync_work_orders(self, job: SyncJob, work_orders: List[Dict[str, Any]],
                              direction: SyncDirection) -> Dict[str, Any]:
        """Sync work orders"""
        # Implementation specific to work orders
        return {"status": "completed", "processed": len(work_orders)}
    
    async def _sync_vendors(self, job: SyncJob, vendors: List[Dict[str, Any]],
                          direction: SyncDirection) -> Dict[str, Any]:
        """Sync vendors"""
        # Implementation specific to vendors
        return {"status": "completed", "processed": len(vendors)}
    
    async def _sync_invoices(self, job: SyncJob, invoices: List[Dict[str, Any]],
                           direction: SyncDirection) -> Dict[str, Any]:
        """Sync invoices"""
        # Implementation specific to invoices
        return {"status": "completed", "processed": len(invoices)}
    
    # =====================================================
    # HELPER METHODS
    # =====================================================
    
    def _get_critical_fields(self, entity_type: YardiEntityType) -> List[str]:
        """Get critical fields for conflict detection"""
        field_map = {
            YardiEntityType.PROPERTIES: ['name', 'address', 'property_manager'],
            YardiEntityType.UNITS: ['unit_number', 'rent_amount', 'status'],
            YardiEntityType.TENANTS: ['name', 'email', 'phone'],
            YardiEntityType.LEASES: ['start_date', 'end_date', 'rent_amount'],
            YardiEntityType.PAYMENTS: ['amount', 'payment_date', 'status'],
            YardiEntityType.WORK_ORDERS: ['description', 'priority', 'status']
        }
        return field_map.get(entity_type, [])
    
    def _get_merge_rules(self, entity_type: str) -> Dict[str, str]:
        """Get merge rules for entity fields"""
        return {
            "name": "non_empty_wins",
            "email": "non_empty_wins",
            "phone": "non_empty_wins",
            "address": "yardi_wins",
            "rent_amount": "latest_wins",
            "status": "latest_wins",
            "updated_at": "latest_wins"
        }
    
    def _validate_entity_data(self, entity_type: YardiEntityType, data: Dict[str, Any],
                            validation_level: DataValidationLevel) -> Dict[str, Any]:
        """Validate entity data"""
        errors = []
        
        # Basic validation
        required_fields = self._get_required_fields(entity_type)
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Additional validation based on level
        if validation_level in [DataValidationLevel.STRICT, DataValidationLevel.ENTERPRISE]:
            # Add format validation, business rule validation, etc.
            pass
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _get_required_fields(self, entity_type: YardiEntityType) -> List[str]:
        """Get required fields for entity type"""
        field_map = {
            YardiEntityType.PROPERTIES: ['name'],
            YardiEntityType.UNITS: ['unit_number', 'property_id'],
            YardiEntityType.TENANTS: ['name', 'email'],
            YardiEntityType.LEASES: ['tenant_id', 'unit_id', 'start_date'],
            YardiEntityType.PAYMENTS: ['amount', 'payment_date'],
            YardiEntityType.WORK_ORDERS: ['description', 'unit_id']
        }
        return field_map.get(entity_type, [])
    
    def _estimate_completion(self, job: SyncJob) -> Optional[str]:
        """Estimate job completion time"""
        if job.total_records == 0 or job.processed_records == 0:
            return None
        
        elapsed = (datetime.utcnow() - job.started_at).total_seconds() if job.started_at else 0
        remaining_records = job.total_records - job.processed_records
        
        if remaining_records <= 0:
            return None
        
        avg_time_per_record = elapsed / job.processed_records
        estimated_remaining = remaining_records * avg_time_per_record
        
        completion_time = datetime.utcnow() + timedelta(seconds=estimated_remaining)
        return completion_time.isoformat()
    
    def _get_current_entity(self, job: SyncJob) -> Optional[str]:
        """Get currently processing entity type"""
        # This would track the current entity being processed
        return job.entity_types[0] if job.entity_types else None
    
    def _start_job_processor(self):
        """Start the job processing thread"""
        if not self.job_processor_running:
            self.job_processor_running = True
            self.processor_thread = threading.Thread(target=self._job_processor_loop, daemon=True)
            self.processor_thread.start()
    
    def _job_processor_loop(self):
        """Main job processing loop"""
        while self.job_processor_running:
            try:
                # Get next job from queue (blocking with timeout)
                job = self.job_queue.get(timeout=1)
                
                # Execute job asynchronously
                asyncio.run(self.execute_sync_job(job.job_id))
                
                self.job_queue.task_done()
                
            except Exception as e:
                if "Empty" not in str(e):  # Ignore queue timeout
                    logger.error(f"Job processor error: {e}")
    
    # Configuration and state management
    
    def update_sync_configuration(self, organization_id: str, config: SyncConfiguration):
        """Update sync configuration for organization"""
        self.sync_configurations[organization_id] = config
    
    def get_sync_configuration(self, organization_id: str) -> Optional[SyncConfiguration]:
        """Get sync configuration for organization"""
        return self.sync_configurations.get(organization_id)
    
    def get_sync_history(self, organization_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get sync history for organization"""
        jobs = [
            asdict(job) for job in self.active_jobs.values()
            if job.organization_id == organization_id
        ]
        return sorted(jobs, key=lambda j: j['created_at'], reverse=True)[:limit]
    
    def initialize_connection(self, connection):
        """Initialize sync service for a connection"""
        # Setup default sync configuration
        config = SyncConfiguration(
            organization_id=connection.organization_id,
            batch_size=100,
            parallel_workers=4
        )
        self.sync_configurations[connection.organization_id] = config
        
        logger.info(f"Initialized sync service for connection {connection.connection_id}")
    
    # Mock data retrieval methods (to be replaced with actual database calls)
    
    async def _get_estatecore_properties(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock EstateCore properties data"""
        return []
    
    async def _get_estatecore_units(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock EstateCore units data"""
        return []
    
    async def _get_estatecore_tenants(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock EstateCore tenants data"""
        return []
    
    async def _get_estatecore_leases(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock EstateCore leases data"""
        return []
    
    async def _get_estatecore_payments(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock EstateCore payments data"""
        return []
    
    async def _get_estatecore_work_orders(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock EstateCore work orders data"""
        return []
    
    async def _get_yardi_record(self, entity_type: YardiEntityType, entity_id: str) -> Optional[Dict[str, Any]]:
        """Mock Yardi record retrieval"""
        return None
    
    async def _get_estatecore_record(self, entity_type: YardiEntityType, entity_id: str) -> Optional[Dict[str, Any]]:
        """Mock EstateCore record retrieval"""
        return None
    
    async def _write_to_yardi(self, connection_id: str, entity_type: YardiEntityType,
                            data: Dict[str, Any]) -> Dict[str, Any]:
        """Write data to Yardi system"""
        return {"id": "yardi_id", "operation": "upsert"}
    
    async def _write_to_estatecore(self, organization_id: str, entity_type: YardiEntityType,
                                 data: Dict[str, Any]) -> Dict[str, Any]:
        """Write data to EstateCore database"""
        return {"id": "estatecore_id", "operation": "upsert"}