"""
AppFolio Synchronization Service

Handles bidirectional data synchronization between EstateCore and AppFolio
including properties, units, tenants, leases, payments, maintenance, and more.
"""

import logging
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .appfolio_api_client import AppFolioAPIClient, AppFolioRequest, AppFolioEntityType, AppFolioOperationType
from .appfolio_auth_service import AppFolioAuthService
from .appfolio_mapping_service import AppFolioMappingService, MappingDirection
from .models import *

logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    """Synchronization direction"""
    TO_APPFOLIO = "to_appfolio"
    FROM_APPFOLIO = "from_appfolio"
    BIDIRECTIONAL = "bidirectional"

class SyncStatus(Enum):
    """Synchronization status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class SyncMode(Enum):
    """Synchronization mode"""
    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"
    REAL_TIME = "real_time"

class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    APPFOLIO_WINS = "appfolio_wins"
    ESTATECORE_WINS = "estatecore_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL_REVIEW = "manual_review"
    MERGE_FIELDS = "merge_fields"

@dataclass
class SyncJob:
    """Synchronization job configuration"""
    job_id: str
    organization_id: str
    entity_types: List[str]
    sync_direction: SyncDirection
    sync_mode: SyncMode
    status: SyncStatus = SyncStatus.PENDING
    priority: str = "normal"
    filters: Optional[Dict[str, Any]] = None
    field_filters: Optional[List[str]] = None
    batch_size: int = 100
    max_retries: int = 3
    timeout_seconds: int = 3600
    conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.NEWEST_WINS
    dry_run: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SyncResult:
    """Synchronization result"""
    entity_type: str
    operation: str
    success_count: int = 0
    failure_count: int = 0
    warning_count: int = 0
    skipped_count: int = 0
    total_count: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    created_records: List[str] = field(default_factory=list)
    updated_records: List[str] = field(default_factory=list)

@dataclass
class ConflictRecord:
    """Data conflict record"""
    conflict_id: str
    entity_type: str
    entity_id: str
    field_name: str
    estatecore_value: Any
    appfolio_value: Any
    estatecore_timestamp: datetime
    appfolio_timestamp: datetime
    resolution_strategy: ConflictResolutionStrategy
    resolved: bool = False
    resolved_value: Any = None
    resolved_at: Optional[datetime] = None

class AppFolioSyncService:
    """
    AppFolio Synchronization Service
    
    Manages all aspects of data synchronization between EstateCore and AppFolio
    including scheduling, execution, conflict resolution, and monitoring.
    """
    
    def __init__(self, api_client: AppFolioAPIClient, mapping_service: AppFolioMappingService, 
                 auth_service: AppFolioAuthService):
        self.api_client = api_client
        self.mapping_service = mapping_service
        self.auth_service = auth_service
        
        # Sync management
        self.active_jobs: Dict[str, SyncJob] = {}
        self.job_history: List[SyncJob] = []
        self.conflict_records: Dict[str, ConflictRecord] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Configuration
        self.sync_configurations: Dict[str, Dict[str, Any]] = {}
        self.entity_sync_order = [
            "properties",
            "units", 
            "tenants",
            "leases",
            "payments",
            "work_orders",
            "vendors",
            "accounts",
            "transactions",
            "documents"
        ]
        
        # Sync locks to prevent concurrent syncs
        self.sync_locks: Dict[str, threading.Lock] = {}
        
        logger.info("AppFolio Sync Service initialized")
    
    async def create_sync_job(self, organization_id: str, entity_types: List[str], 
                            sync_direction: SyncDirection, sync_mode: SyncMode = SyncMode.INCREMENTAL,
                            **kwargs) -> SyncJob:
        """
        Create a new synchronization job
        
        Args:
            organization_id: Organization identifier
            entity_types: List of entity types to sync
            sync_direction: Direction of synchronization
            sync_mode: Mode of synchronization
            **kwargs: Additional job configuration
            
        Returns:
            Created sync job
        """
        try:
            job_id = str(uuid.uuid4())
            
            # Create sync job
            sync_job = SyncJob(
                job_id=job_id,
                organization_id=organization_id,
                entity_types=entity_types,
                sync_direction=sync_direction,
                sync_mode=sync_mode,
                **kwargs
            )
            
            # Store job
            self.active_jobs[job_id] = sync_job
            
            # Initialize progress tracking
            sync_job.progress = {
                entity_type: {
                    'total': 0,
                    'processed': 0,
                    'success': 0,
                    'failed': 0,
                    'skipped': 0
                } for entity_type in entity_types
            }
            
            logger.info(f"Created sync job {job_id} for organization {organization_id}")
            return sync_job
            
        except Exception as e:
            logger.error(f"Failed to create sync job: {str(e)}")
            raise
    
    async def execute_sync_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a synchronization job
        
        Args:
            job_id: Sync job identifier
            
        Returns:
            Execution results
        """
        try:
            if job_id not in self.active_jobs:
                raise ValueError(f"Sync job {job_id} not found")
            
            sync_job = self.active_jobs[job_id]
            
            # Check if organization has active connection
            connection = self.auth_service.get_organization_connection(sync_job.organization_id)
            if not connection:
                raise ValueError("No active AppFolio connection found")
            
            # Initialize sync lock
            if sync_job.organization_id not in self.sync_locks:
                self.sync_locks[sync_job.organization_id] = threading.Lock()
            
            sync_lock = self.sync_locks[sync_job.organization_id]
            
            # Check if sync is already running
            if not sync_lock.acquire(blocking=False):
                raise RuntimeError("Another sync is already running for this organization")
            
            try:
                # Update job status
                sync_job.status = SyncStatus.RUNNING
                sync_job.started_at = datetime.utcnow()
                
                # Execute sync based on direction
                if sync_job.sync_direction == SyncDirection.TO_APPFOLIO:
                    results = await self._sync_to_appfolio(sync_job, connection.connection_id)
                elif sync_job.sync_direction == SyncDirection.FROM_APPFOLIO:
                    results = await self._sync_from_appfolio(sync_job, connection.connection_id)
                elif sync_job.sync_direction == SyncDirection.BIDIRECTIONAL:
                    to_results = await self._sync_to_appfolio(sync_job, connection.connection_id)
                    from_results = await self._sync_from_appfolio(sync_job, connection.connection_id)
                    results = self._merge_sync_results(to_results, from_results)
                
                # Update job completion
                sync_job.status = SyncStatus.COMPLETED
                sync_job.completed_at = datetime.utcnow()
                sync_job.results = results
                
                # Move to history
                self.job_history.append(sync_job)
                del self.active_jobs[job_id]
                
                logger.info(f"Sync job {job_id} completed successfully")
                return {
                    'success': True,
                    'job_id': job_id,
                    'results': results,
                    'processing_time': (sync_job.completed_at - sync_job.started_at).total_seconds()
                }
                
            finally:
                sync_lock.release()
                
        except Exception as e:
            logger.error(f"Sync job {job_id} failed: {str(e)}")
            
            if job_id in self.active_jobs:
                sync_job = self.active_jobs[job_id]
                sync_job.status = SyncStatus.FAILED
                sync_job.errors.append(str(e))
                sync_job.completed_at = datetime.utcnow()
                
                # Move to history
                self.job_history.append(sync_job)
                del self.active_jobs[job_id]
            
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e)
            }
    
    async def _sync_to_appfolio(self, sync_job: SyncJob, connection_id: str) -> Dict[str, SyncResult]:
        """Sync data from EstateCore to AppFolio"""
        results = {}
        
        for entity_type in sync_job.entity_types:
            try:
                logger.info(f"Syncing {entity_type} to AppFolio")
                
                # Get EstateCore data
                estatecore_data = await self._get_estatecore_data(
                    sync_job.organization_id, 
                    entity_type, 
                    sync_job.filters,
                    sync_job.sync_mode
                )
                
                # Sync each record
                result = SyncResult(entity_type=entity_type, operation="to_appfolio")
                result.total_count = len(estatecore_data)
                
                # Update progress
                sync_job.progress[entity_type]['total'] = result.total_count
                
                # Process in batches
                for i in range(0, len(estatecore_data), sync_job.batch_size):
                    batch = estatecore_data[i:i + sync_job.batch_size]
                    batch_result = await self._process_batch_to_appfolio(
                        batch, entity_type, connection_id, sync_job
                    )
                    
                    # Aggregate results
                    result.success_count += batch_result.success_count
                    result.failure_count += batch_result.failure_count
                    result.warning_count += batch_result.warning_count
                    result.skipped_count += batch_result.skipped_count
                    result.errors.extend(batch_result.errors)
                    result.warnings.extend(batch_result.warnings)
                    result.conflicts.extend(batch_result.conflicts)
                    result.created_records.extend(batch_result.created_records)
                    result.updated_records.extend(batch_result.updated_records)
                    
                    # Update progress
                    sync_job.progress[entity_type]['processed'] = min(
                        i + sync_job.batch_size, result.total_count
                    )
                    sync_job.progress[entity_type]['success'] = result.success_count
                    sync_job.progress[entity_type]['failed'] = result.failure_count
                    sync_job.progress[entity_type]['skipped'] = result.skipped_count
                
                results[entity_type] = result
                logger.info(f"Completed syncing {entity_type} to AppFolio: {result.success_count} successful, {result.failure_count} failed")
                
            except Exception as e:
                logger.error(f"Failed to sync {entity_type} to AppFolio: {str(e)}")
                result = SyncResult(entity_type=entity_type, operation="to_appfolio")
                result.errors.append(str(e))
                results[entity_type] = result
        
        return results
    
    async def _sync_from_appfolio(self, sync_job: SyncJob, connection_id: str) -> Dict[str, SyncResult]:
        """Sync data from AppFolio to EstateCore"""
        results = {}
        
        for entity_type in sync_job.entity_types:
            try:
                logger.info(f"Syncing {entity_type} from AppFolio")
                
                # Get AppFolio data
                appfolio_data = await self._get_appfolio_data(
                    connection_id,
                    entity_type,
                    sync_job.filters,
                    sync_job.sync_mode
                )
                
                # Sync each record
                result = SyncResult(entity_type=entity_type, operation="from_appfolio")
                result.total_count = len(appfolio_data)
                
                # Update progress
                sync_job.progress[entity_type]['total'] = result.total_count
                
                # Process in batches
                for i in range(0, len(appfolio_data), sync_job.batch_size):
                    batch = appfolio_data[i:i + sync_job.batch_size]
                    batch_result = await self._process_batch_from_appfolio(
                        batch, entity_type, sync_job
                    )
                    
                    # Aggregate results
                    result.success_count += batch_result.success_count
                    result.failure_count += batch_result.failure_count
                    result.warning_count += batch_result.warning_count
                    result.skipped_count += batch_result.skipped_count
                    result.errors.extend(batch_result.errors)
                    result.warnings.extend(batch_result.warnings)
                    result.conflicts.extend(batch_result.conflicts)
                    result.created_records.extend(batch_result.created_records)
                    result.updated_records.extend(batch_result.updated_records)
                    
                    # Update progress
                    sync_job.progress[entity_type]['processed'] = min(
                        i + sync_job.batch_size, result.total_count
                    )
                    sync_job.progress[entity_type]['success'] = result.success_count
                    sync_job.progress[entity_type]['failed'] = result.failure_count
                    sync_job.progress[entity_type]['skipped'] = result.skipped_count
                
                results[entity_type] = result
                logger.info(f"Completed syncing {entity_type} from AppFolio: {result.success_count} successful, {result.failure_count} failed")
                
            except Exception as e:
                logger.error(f"Failed to sync {entity_type} from AppFolio: {str(e)}")
                result = SyncResult(entity_type=entity_type, operation="from_appfolio")
                result.errors.append(str(e))
                results[entity_type] = result
        
        return results
    
    async def _process_batch_to_appfolio(self, batch: List[Dict[str, Any]], entity_type: str, 
                                       connection_id: str, sync_job: SyncJob) -> SyncResult:
        """Process a batch of records to AppFolio"""
        result = SyncResult(entity_type=entity_type, operation="to_appfolio")
        
        for record in batch:
            try:
                # Map EstateCore data to AppFolio format
                mapped_data = self.mapping_service.map_entity(
                    entity_type, record, MappingDirection.TO_APPFOLIO
                )
                
                # Check if record exists in AppFolio
                existing_record = await self._find_appfolio_record(
                    connection_id, entity_type, mapped_data
                )
                
                if existing_record:
                    # Update existing record
                    if not sync_job.dry_run:
                        update_request = AppFolioRequest(
                            entity_type=self._get_appfolio_entity_type(entity_type),
                            operation=AppFolioOperationType.UPDATE,
                            entity_id=existing_record['id'],
                            data=mapped_data
                        )
                        
                        response = self.api_client.execute_request(connection_id, update_request)
                        
                        if response.success:
                            result.success_count += 1
                            result.updated_records.append(existing_record['id'])
                        else:
                            result.failure_count += 1
                            result.errors.extend(response.errors)
                    else:
                        result.success_count += 1
                        result.updated_records.append(existing_record.get('id', 'dry_run'))
                
                else:
                    # Create new record
                    if not sync_job.dry_run:
                        create_request = AppFolioRequest(
                            entity_type=self._get_appfolio_entity_type(entity_type),
                            operation=AppFolioOperationType.CREATE,
                            data=mapped_data
                        )
                        
                        response = self.api_client.execute_request(connection_id, create_request)
                        
                        if response.success:
                            result.success_count += 1
                            if isinstance(response.data, dict) and 'id' in response.data:
                                result.created_records.append(response.data['id'])
                        else:
                            result.failure_count += 1
                            result.errors.extend(response.errors)
                    else:
                        result.success_count += 1
                        result.created_records.append('dry_run_create')
                
            except Exception as e:
                logger.error(f"Failed to process record to AppFolio: {str(e)}")
                result.failure_count += 1
                result.errors.append(str(e))
        
        return result
    
    async def _process_batch_from_appfolio(self, batch: List[Dict[str, Any]], entity_type: str, 
                                         sync_job: SyncJob) -> SyncResult:
        """Process a batch of records from AppFolio"""
        result = SyncResult(entity_type=entity_type, operation="from_appfolio")
        
        for record in batch:
            try:
                # Map AppFolio data to EstateCore format
                mapped_data = self.mapping_service.map_entity(
                    entity_type, record, MappingDirection.FROM_APPFOLIO
                )
                
                # Check if record exists in EstateCore
                existing_record = await self._find_estatecore_record(
                    sync_job.organization_id, entity_type, mapped_data
                )
                
                if existing_record:
                    # Check for conflicts
                    conflicts = self._detect_conflicts(existing_record, mapped_data, entity_type)
                    
                    if conflicts:
                        # Handle conflicts based on resolution strategy
                        resolved_data = self._resolve_conflicts(
                            conflicts, sync_job.conflict_resolution, existing_record, mapped_data
                        )
                        result.conflicts.extend(conflicts)
                    else:
                        resolved_data = mapped_data
                    
                    # Update existing record
                    if not sync_job.dry_run:
                        update_success = await self._update_estatecore_record(
                            sync_job.organization_id, entity_type, existing_record['id'], resolved_data
                        )
                        
                        if update_success:
                            result.success_count += 1
                            result.updated_records.append(existing_record['id'])
                        else:
                            result.failure_count += 1
                            result.errors.append(f"Failed to update EstateCore record {existing_record['id']}")
                    else:
                        result.success_count += 1
                        result.updated_records.append(existing_record.get('id', 'dry_run'))
                
                else:
                    # Create new record
                    if not sync_job.dry_run:
                        new_record_id = await self._create_estatecore_record(
                            sync_job.organization_id, entity_type, mapped_data
                        )
                        
                        if new_record_id:
                            result.success_count += 1
                            result.created_records.append(new_record_id)
                        else:
                            result.failure_count += 1
                            result.errors.append("Failed to create EstateCore record")
                    else:
                        result.success_count += 1
                        result.created_records.append('dry_run_create')
                
            except Exception as e:
                logger.error(f"Failed to process record from AppFolio: {str(e)}")
                result.failure_count += 1
                result.errors.append(str(e))
        
        return result
    
    async def _get_appfolio_data(self, connection_id: str, entity_type: str, 
                               filters: Dict[str, Any] = None, sync_mode: SyncMode = SyncMode.FULL) -> List[Dict[str, Any]]:
        """Get data from AppFolio"""
        try:
            # Build request filters
            request_filters = filters or {}
            
            # Add incremental sync filters
            if sync_mode == SyncMode.INCREMENTAL:
                # Get last sync timestamp
                last_sync = await self._get_last_sync_timestamp(connection_id, entity_type)
                if last_sync:
                    request_filters['updated_since'] = last_sync.isoformat()
            
            # Make API request
            request = AppFolioRequest(
                entity_type=self._get_appfolio_entity_type(entity_type),
                operation=AppFolioOperationType.LIST,
                filters=request_filters
            )
            
            response = self.api_client.execute_request(connection_id, request)
            
            if response.success:
                if isinstance(response.data, dict) and 'data' in response.data:
                    return response.data['data']
                elif isinstance(response.data, list):
                    return response.data
                else:
                    return []
            else:
                logger.error(f"Failed to get AppFolio data for {entity_type}: {response.errors}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting AppFolio data for {entity_type}: {str(e)}")
            return []
    
    async def _get_estatecore_data(self, organization_id: str, entity_type: str, 
                                 filters: Dict[str, Any] = None, sync_mode: SyncMode = SyncMode.FULL) -> List[Dict[str, Any]]:
        """Get data from EstateCore"""
        try:
            # This would integrate with EstateCore's database/API
            # For now, return empty list as placeholder
            logger.warning(f"EstateCore data retrieval not implemented for {entity_type}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting EstateCore data for {entity_type}: {str(e)}")
            return []
    
    def _get_appfolio_entity_type(self, entity_type: str) -> AppFolioEntityType:
        """Map entity type string to AppFolioEntityType enum"""
        mapping = {
            'properties': AppFolioEntityType.PROPERTIES,
            'units': AppFolioEntityType.UNITS,
            'tenants': AppFolioEntityType.TENANTS,
            'residents': AppFolioEntityType.RESIDENTS,
            'leases': AppFolioEntityType.LEASES,
            'payments': AppFolioEntityType.PAYMENTS,
            'work_orders': AppFolioEntityType.WORK_ORDERS,
            'vendors': AppFolioEntityType.VENDORS,
            'accounts': AppFolioEntityType.ACCOUNTS,
            'documents': AppFolioEntityType.DOCUMENTS,
            'portfolios': AppFolioEntityType.PORTFOLIOS,
            'applications': AppFolioEntityType.APPLICATIONS,
            'messages': AppFolioEntityType.MESSAGES
        }
        
        return mapping.get(entity_type, AppFolioEntityType.PROPERTIES)
    
    async def _find_appfolio_record(self, connection_id: str, entity_type: str, 
                                  data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find existing record in AppFolio"""
        try:
            # Use ID if available
            if 'id' in data:
                request = AppFolioRequest(
                    entity_type=self._get_appfolio_entity_type(entity_type),
                    operation=AppFolioOperationType.READ,
                    entity_id=data['id']
                )
                
                response = self.api_client.execute_request(connection_id, request)
                if response.success:
                    return response.data
            
            # Try to find by unique identifiers
            search_filters = {}
            if entity_type == 'properties' and 'name' in data:
                search_filters['name'] = data['name']
            elif entity_type == 'units' and 'unit_number' in data and 'property_id' in data:
                search_filters['unit_number'] = data['unit_number']
                search_filters['property_id'] = data['property_id']
            elif entity_type == 'tenants' and 'email' in data:
                search_filters['email'] = data['email']
            
            if search_filters:
                request = AppFolioRequest(
                    entity_type=self._get_appfolio_entity_type(entity_type),
                    operation=AppFolioOperationType.LIST,
                    filters=search_filters
                )
                
                response = self.api_client.execute_request(connection_id, request)
                if response.success and response.data:
                    if isinstance(response.data, list) and len(response.data) > 0:
                        return response.data[0]
                    elif isinstance(response.data, dict) and 'data' in response.data and response.data['data']:
                        return response.data['data'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding AppFolio record: {str(e)}")
            return None
    
    async def _find_estatecore_record(self, organization_id: str, entity_type: str, 
                                    data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find existing record in EstateCore"""
        try:
            # This would integrate with EstateCore's database/API
            # For now, return None as placeholder
            logger.warning(f"EstateCore record search not implemented for {entity_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding EstateCore record: {str(e)}")
            return None
    
    async def _create_estatecore_record(self, organization_id: str, entity_type: str, 
                                      data: Dict[str, Any]) -> Optional[str]:
        """Create record in EstateCore"""
        try:
            # This would integrate with EstateCore's database/API
            # For now, return a dummy ID as placeholder
            logger.warning(f"EstateCore record creation not implemented for {entity_type}")
            return str(uuid.uuid4())
            
        except Exception as e:
            logger.error(f"Error creating EstateCore record: {str(e)}")
            return None
    
    async def _update_estatecore_record(self, organization_id: str, entity_type: str, 
                                      record_id: str, data: Dict[str, Any]) -> bool:
        """Update record in EstateCore"""
        try:
            # This would integrate with EstateCore's database/API
            # For now, return True as placeholder
            logger.warning(f"EstateCore record update not implemented for {entity_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating EstateCore record: {str(e)}")
            return False
    
    def _detect_conflicts(self, existing_record: Dict[str, Any], new_record: Dict[str, Any], 
                         entity_type: str) -> List[Dict[str, Any]]:
        """Detect conflicts between existing and new record data"""
        conflicts = []
        
        for field_name, new_value in new_record.items():
            if field_name in existing_record:
                existing_value = existing_record[field_name]
                
                # Skip if values are the same
                if existing_value == new_value:
                    continue
                
                # Skip system fields
                if field_name in ['id', 'created_at', 'updated_at']:
                    continue
                
                # Create conflict record
                conflict = {
                    'field_name': field_name,
                    'existing_value': existing_value,
                    'new_value': new_value,
                    'entity_type': entity_type,
                    'entity_id': existing_record.get('id'),
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], strategy: ConflictResolutionStrategy,
                          existing_record: Dict[str, Any], new_record: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts based on strategy"""
        resolved_data = new_record.copy()
        
        for conflict in conflicts:
            field_name = conflict['field_name']
            
            if strategy == ConflictResolutionStrategy.APPFOLIO_WINS:
                # Keep new value (from AppFolio)
                resolved_data[field_name] = conflict['new_value']
            
            elif strategy == ConflictResolutionStrategy.ESTATECORE_WINS:
                # Keep existing value (from EstateCore)
                resolved_data[field_name] = conflict['existing_value']
            
            elif strategy == ConflictResolutionStrategy.NEWEST_WINS:
                # Use timestamps to determine which value to keep
                existing_updated = existing_record.get('updated_at')
                new_updated = new_record.get('updated_at')
                
                if existing_updated and new_updated:
                    if isinstance(existing_updated, str):
                        existing_updated = datetime.fromisoformat(existing_updated)
                    if isinstance(new_updated, str):
                        new_updated = datetime.fromisoformat(new_updated)
                    
                    if new_updated > existing_updated:
                        resolved_data[field_name] = conflict['new_value']
                    else:
                        resolved_data[field_name] = conflict['existing_value']
                else:
                    # Default to new value if timestamps unavailable
                    resolved_data[field_name] = conflict['new_value']
            
            elif strategy == ConflictResolutionStrategy.MANUAL_REVIEW:
                # Store conflict for manual resolution
                conflict_id = str(uuid.uuid4())
                conflict_record = ConflictRecord(
                    conflict_id=conflict_id,
                    entity_type=conflict['entity_type'],
                    entity_id=conflict['entity_id'],
                    field_name=field_name,
                    estatecore_value=conflict['existing_value'],
                    appfolio_value=conflict['new_value'],
                    estatecore_timestamp=datetime.fromisoformat(existing_record.get('updated_at', datetime.utcnow().isoformat())),
                    appfolio_timestamp=datetime.fromisoformat(new_record.get('updated_at', datetime.utcnow().isoformat())),
                    resolution_strategy=strategy
                )
                self.conflict_records[conflict_id] = conflict_record
                
                # Keep existing value until manual resolution
                resolved_data[field_name] = conflict['existing_value']
        
        return resolved_data
    
    def _merge_sync_results(self, to_results: Dict[str, SyncResult], 
                          from_results: Dict[str, SyncResult]) -> Dict[str, Any]:
        """Merge bidirectional sync results"""
        merged = {}
        
        all_entity_types = set(to_results.keys()) | set(from_results.keys())
        
        for entity_type in all_entity_types:
            to_result = to_results.get(entity_type)
            from_result = from_results.get(entity_type)
            
            merged[entity_type] = {
                'to_appfolio': asdict(to_result) if to_result else None,
                'from_appfolio': asdict(from_result) if from_result else None,
                'total_success': (to_result.success_count if to_result else 0) + (from_result.success_count if from_result else 0),
                'total_failures': (to_result.failure_count if to_result else 0) + (from_result.failure_count if from_result else 0)
            }
        
        return merged
    
    async def _get_last_sync_timestamp(self, connection_id: str, entity_type: str) -> Optional[datetime]:
        """Get last sync timestamp for incremental sync"""
        # This would query sync history from database
        # For now, return None to force full sync
        return None
    
    def get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        for job in self.job_history:
            if job.job_id == job_id:
                return job
        
        return None
    
    def get_active_sync_jobs(self, organization_id: str) -> List[SyncJob]:
        """Get active sync jobs for organization"""
        return [
            job for job in self.active_jobs.values() 
            if job.organization_id == organization_id
        ]
    
    def get_recent_sync_jobs(self, organization_id: str, limit: int = 10) -> List[SyncJob]:
        """Get recent sync jobs for organization"""
        org_jobs = [
            job for job in self.job_history 
            if job.organization_id == organization_id
        ]
        
        # Sort by completion time, most recent first
        org_jobs.sort(key=lambda x: x.completed_at or x.created_at, reverse=True)
        
        return org_jobs[:limit]
    
    def get_sync_progress(self, job_id: str) -> Dict[str, Any]:
        """Get sync job progress"""
        job = self.get_sync_job(job_id)
        if job:
            return {
                'job_id': job_id,
                'status': job.status.value,
                'progress': job.progress,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'estimated_completion': None,  # Could calculate based on progress
                'errors': job.errors,
                'warnings': job.warnings
            }
        
        return {'error': 'Job not found'}
    
    def cancel_sync_job(self, job_id: str) -> bool:
        """Cancel a running sync job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == SyncStatus.RUNNING:
                job.status = SyncStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                
                # Move to history
                self.job_history.append(job)
                del self.active_jobs[job_id]
                
                logger.info(f"Cancelled sync job {job_id}")
                return True
        
        return False
    
    def get_conflict_records(self, organization_id: str, resolved: bool = None) -> List[ConflictRecord]:
        """Get conflict records for organization"""
        conflicts = list(self.conflict_records.values())
        
        if resolved is not None:
            conflicts = [c for c in conflicts if c.resolved == resolved]
        
        return conflicts
    
    def resolve_conflict(self, conflict_id: str, resolved_value: Any) -> bool:
        """Manually resolve a conflict"""
        if conflict_id in self.conflict_records:
            conflict = self.conflict_records[conflict_id]
            conflict.resolved = True
            conflict.resolved_value = resolved_value
            conflict.resolved_at = datetime.utcnow()
            
            logger.info(f"Resolved conflict {conflict_id}")
            return True
        
        return False