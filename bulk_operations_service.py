"""
Bulk Operations Service for EstateCore
Efficient bulk processing for properties, tenants, maintenance, and financial operations
"""

import os
import logging
import uuid
import json
import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import concurrent.futures
from threading import Lock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Types of bulk operations"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    ARCHIVE = "archive"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"

class OperationStatus(Enum):
    """Status of bulk operations"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"

class EntityType(Enum):
    """Types of entities for bulk operations"""
    PROPERTIES = "properties"
    TENANTS = "tenants"
    MAINTENANCE_REQUESTS = "maintenance_requests"
    LEASE_AGREEMENTS = "lease_agreements"
    RENT_COLLECTIONS = "rent_collections"
    DOCUMENTS = "documents"
    USERS = "users"
    PAYMENTS = "payments"

@dataclass
class BulkOperation:
    """Bulk operation record"""
    id: str
    operation_type: OperationType
    entity_type: EntityType
    status: OperationStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: int  # user_id
    total_records: int
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    parameters: Dict = field(default_factory=dict)
    results: Dict = field(default_factory=dict)
    error_details: List[Dict] = field(default_factory=list)
    progress_percentage: float = 0.0
    estimated_completion: Optional[datetime] = None

@dataclass
class BulkOperationResult:
    """Result of a bulk operation"""
    operation_id: str
    success: bool
    total_processed: int
    successful_count: int
    failed_count: int
    errors: List[Dict]
    execution_time_seconds: float
    output_file_path: Optional[str] = None

@dataclass
class ValidationResult:
    """Validation result for bulk data"""
    is_valid: bool
    errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    valid_records: List[Dict] = field(default_factory=list)
    invalid_records: List[Dict] = field(default_factory=list)

class BulkOperationsService:
    def __init__(self):
        """Initialize bulk operations service"""
        self.operations = {}
        self.operation_lock = Lock()
        self.max_concurrent_operations = int(os.getenv('MAX_CONCURRENT_BULK_OPS', '3'))
        self.chunk_size = int(os.getenv('BULK_CHUNK_SIZE', '100'))
        self.max_file_size_mb = int(os.getenv('MAX_BULK_FILE_SIZE_MB', '50'))
        
        # File storage paths
        self.upload_dir = os.getenv('BULK_UPLOAD_DIR', 'uploads/bulk')
        self.output_dir = os.getenv('BULK_OUTPUT_DIR', 'outputs/bulk')
        
        # Create directories if they don't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize with sample operations
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample bulk operations"""
        sample_operation = BulkOperation(
            id="bulk_001",
            operation_type=OperationType.UPDATE,
            entity_type=EntityType.PROPERTIES,
            status=OperationStatus.COMPLETED,
            created_at=datetime.utcnow() - timedelta(hours=2),
            started_at=datetime.utcnow() - timedelta(hours=2, minutes=5),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            created_by=1,
            total_records=50,
            processed_records=50,
            successful_records=48,
            failed_records=2,
            progress_percentage=100.0,
            parameters={'fields': ['rent_amount', 'property_type']},
            results={'updated_properties': 48, 'errors': 2}
        )
        
        self.operations[sample_operation.id] = sample_operation
        logger.info("Sample bulk operations data initialized")
    
    def create_bulk_operation(self, operation_type: OperationType, entity_type: EntityType,
                            created_by: int, parameters: Dict = None) -> str:
        """Create a new bulk operation"""
        try:
            operation_id = str(uuid.uuid4())
            
            operation = BulkOperation(
                id=operation_id,
                operation_type=operation_type,
                entity_type=entity_type,
                status=OperationStatus.QUEUED,
                created_at=datetime.utcnow(),
                created_by=created_by,
                total_records=0,
                parameters=parameters or {}
            )
            
            with self.operation_lock:
                self.operations[operation_id] = operation
            
            logger.info(f"Created bulk operation: {operation_id} - {operation_type.value} {entity_type.value}")
            return operation_id
            
        except Exception as e:
            logger.error(f"Failed to create bulk operation: {e}")
            raise
    
    def validate_bulk_data(self, entity_type: EntityType, data: List[Dict]) -> ValidationResult:
        """Validate bulk data before processing"""
        try:
            validation_rules = self._get_validation_rules(entity_type)
            valid_records = []
            invalid_records = []
            errors = []
            warnings = []
            
            for idx, record in enumerate(data):
                record_errors = []
                record_warnings = []
                
                # Validate required fields
                for field in validation_rules.get('required_fields', []):
                    if field not in record or not record[field]:
                        record_errors.append({
                            'field': field,
                            'message': f'Required field {field} is missing or empty',
                            'row': idx + 1
                        })
                
                # Validate field types and formats
                for field, field_rules in validation_rules.get('field_rules', {}).items():
                    if field in record and record[field]:
                        value = record[field]
                        
                        # Type validation
                        if 'type' in field_rules:
                            expected_type = field_rules['type']
                            if expected_type == 'int':
                                try:
                                    int(value)
                                except ValueError:
                                    record_errors.append({
                                        'field': field,
                                        'message': f'{field} must be an integer',
                                        'row': idx + 1,
                                        'value': value
                                    })
                            elif expected_type == 'float':
                                try:
                                    float(value)
                                except ValueError:
                                    record_errors.append({
                                        'field': field,
                                        'message': f'{field} must be a number',
                                        'row': idx + 1,
                                        'value': value
                                    })
                            elif expected_type == 'email':
                                if '@' not in value or '.' not in value:
                                    record_errors.append({
                                        'field': field,
                                        'message': f'{field} must be a valid email address',
                                        'row': idx + 1,
                                        'value': value
                                    })
                        
                        # Range validation
                        if 'min_value' in field_rules:
                            try:
                                if float(value) < field_rules['min_value']:
                                    record_errors.append({
                                        'field': field,
                                        'message': f'{field} must be at least {field_rules["min_value"]}',
                                        'row': idx + 1,
                                        'value': value
                                    })
                            except ValueError:
                                pass  # Type error already caught above
                        
                        if 'max_value' in field_rules:
                            try:
                                if float(value) > field_rules['max_value']:
                                    record_errors.append({
                                        'field': field,
                                        'message': f'{field} must be at most {field_rules["max_value"]}',
                                        'row': idx + 1,
                                        'value': value
                                    })
                            except ValueError:
                                pass
                        
                        # Allowed values validation
                        if 'allowed_values' in field_rules:
                            if value not in field_rules['allowed_values']:
                                record_errors.append({
                                    'field': field,
                                    'message': f'{field} must be one of: {", ".join(field_rules["allowed_values"])}',
                                    'row': idx + 1,
                                    'value': value
                                })
                
                # Check for duplicates within the dataset
                if 'unique_fields' in validation_rules:
                    for unique_field in validation_rules['unique_fields']:
                        if unique_field in record:
                            value = record[unique_field]
                            duplicate_found = False
                            for prev_idx, prev_record in enumerate(data[:idx]):
                                if prev_record.get(unique_field) == value:
                                    record_warnings.append({
                                        'field': unique_field,
                                        'message': f'Duplicate value found for {unique_field} at rows {prev_idx + 1} and {idx + 1}',
                                        'row': idx + 1,
                                        'value': value
                                    })
                                    duplicate_found = True
                                    break
                
                # Categorize record
                if record_errors:
                    invalid_records.append({
                        'record': record,
                        'row': idx + 1,
                        'errors': record_errors
                    })
                    errors.extend(record_errors)
                else:
                    valid_records.append(record)
                
                if record_warnings:
                    warnings.extend(record_warnings)
            
            return ValidationResult(
                is_valid=len(invalid_records) == 0,
                errors=errors,
                warnings=warnings,
                valid_records=valid_records,
                invalid_records=invalid_records
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[{'message': f'Validation error: {str(e)}'}]
            )
    
    def _get_validation_rules(self, entity_type: EntityType) -> Dict:
        """Get validation rules for entity type"""
        rules = {
            EntityType.PROPERTIES: {
                'required_fields': ['property_name', 'address', 'property_type'],
                'field_rules': {
                    'rent_amount': {'type': 'float', 'min_value': 0},
                    'bedrooms': {'type': 'int', 'min_value': 0, 'max_value': 20},
                    'bathrooms': {'type': 'float', 'min_value': 0, 'max_value': 20},
                    'property_type': {'allowed_values': ['apartment', 'house', 'condo', 'townhouse', 'commercial']},
                    'status': {'allowed_values': ['available', 'occupied', 'maintenance', 'inactive']}
                },
                'unique_fields': ['property_name', 'address']
            },
            EntityType.TENANTS: {
                'required_fields': ['first_name', 'last_name', 'email', 'phone'],
                'field_rules': {
                    'email': {'type': 'email'},
                    'phone': {'type': 'str'},
                    'monthly_income': {'type': 'float', 'min_value': 0},
                    'credit_score': {'type': 'int', 'min_value': 300, 'max_value': 850}
                },
                'unique_fields': ['email']
            },
            EntityType.MAINTENANCE_REQUESTS: {
                'required_fields': ['property_id', 'title', 'description', 'priority'],
                'field_rules': {
                    'property_id': {'type': 'int', 'min_value': 1},
                    'priority': {'allowed_values': ['low', 'medium', 'high', 'critical', 'emergency']},
                    'status': {'allowed_values': ['pending', 'scheduled', 'in_progress', 'completed', 'cancelled']},
                    'estimated_cost': {'type': 'float', 'min_value': 0}
                }
            },
            EntityType.USERS: {
                'required_fields': ['username', 'email', 'role'],
                'field_rules': {
                    'email': {'type': 'email'},
                    'role': {'allowed_values': ['tenant', 'manager', 'admin', 'super_admin']},
                    'is_active': {'allowed_values': ['true', 'false', True, False]}
                },
                'unique_fields': ['username', 'email']
            }
        }
        
        return rules.get(entity_type, {'required_fields': [], 'field_rules': {}})
    
    def process_bulk_import(self, operation_id: str, file_data: str, file_type: str = 'csv') -> BulkOperationResult:
        """Process bulk import from file data"""
        try:
            operation = self.operations.get(operation_id)
            if not operation:
                raise ValueError(f"Operation {operation_id} not found")
            
            # Update operation status
            operation.status = OperationStatus.PROCESSING
            operation.started_at = datetime.utcnow()
            
            # Parse file data
            if file_type.lower() == 'csv':
                data = self._parse_csv_data(file_data)
            elif file_type.lower() == 'json':
                data = json.loads(file_data)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            operation.total_records = len(data)
            
            # Validate data
            validation_result = self.validate_bulk_data(operation.entity_type, data)
            
            if not validation_result.is_valid:
                operation.status = OperationStatus.FAILED
                operation.completed_at = datetime.utcnow()
                operation.error_details = validation_result.errors
                
                return BulkOperationResult(
                    operation_id=operation_id,
                    success=False,
                    total_processed=len(data),
                    successful_count=0,
                    failed_count=len(data),
                    errors=validation_result.errors,
                    execution_time_seconds=0
                )
            
            # Process valid records in chunks
            successful_count = 0
            failed_count = 0
            errors = []
            
            valid_data = validation_result.valid_records
            total_chunks = (len(valid_data) + self.chunk_size - 1) // self.chunk_size
            
            for chunk_idx in range(total_chunks):
                start_idx = chunk_idx * self.chunk_size
                end_idx = min(start_idx + self.chunk_size, len(valid_data))
                chunk_data = valid_data[start_idx:end_idx]
                
                chunk_results = self._process_chunk(operation.entity_type, chunk_data, operation.operation_type)
                
                successful_count += chunk_results['successful']
                failed_count += chunk_results['failed']
                errors.extend(chunk_results['errors'])
                
                # Update progress
                operation.processed_records = min(end_idx, len(valid_data))
                operation.successful_records = successful_count
                operation.failed_records = failed_count
                operation.progress_percentage = (operation.processed_records / operation.total_records) * 100
                
                # Simulate processing time
                time.sleep(0.1)
            
            # Complete operation
            operation.status = OperationStatus.COMPLETED if failed_count == 0 else OperationStatus.PARTIAL_SUCCESS
            operation.completed_at = datetime.utcnow()
            operation.results = {
                'total_processed': len(valid_data),
                'successful': successful_count,
                'failed': failed_count,
                'validation_warnings': len(validation_result.warnings)
            }
            
            execution_time = (operation.completed_at - operation.started_at).total_seconds()
            
            return BulkOperationResult(
                operation_id=operation_id,
                success=failed_count == 0,
                total_processed=len(valid_data),
                successful_count=successful_count,
                failed_count=failed_count,
                errors=errors,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            logger.error(f"Bulk import failed: {e}")
            operation.status = OperationStatus.FAILED
            operation.completed_at = datetime.utcnow()
            operation.error_details = [{'message': str(e)}]
            
            raise
    
    def process_bulk_update(self, operation_id: str, record_ids: List[str], 
                          update_data: Dict) -> BulkOperationResult:
        """Process bulk update operation"""
        try:
            operation = self.operations.get(operation_id)
            if not operation:
                raise ValueError(f"Operation {operation_id} not found")
            
            operation.status = OperationStatus.PROCESSING
            operation.started_at = datetime.utcnow()
            operation.total_records = len(record_ids)
            
            successful_count = 0
            failed_count = 0
            errors = []
            
            # Process records in chunks
            total_chunks = (len(record_ids) + self.chunk_size - 1) // self.chunk_size
            
            for chunk_idx in range(total_chunks):
                start_idx = chunk_idx * self.chunk_size
                end_idx = min(start_idx + self.chunk_size, len(record_ids))
                chunk_ids = record_ids[start_idx:end_idx]
                
                chunk_results = self._process_bulk_update_chunk(
                    operation.entity_type, chunk_ids, update_data
                )
                
                successful_count += chunk_results['successful']
                failed_count += chunk_results['failed']
                errors.extend(chunk_results['errors'])
                
                # Update progress
                operation.processed_records = end_idx
                operation.successful_records = successful_count
                operation.failed_records = failed_count
                operation.progress_percentage = (operation.processed_records / operation.total_records) * 100
                
                time.sleep(0.05)  # Simulate processing time
            
            # Complete operation
            operation.status = OperationStatus.COMPLETED if failed_count == 0 else OperationStatus.PARTIAL_SUCCESS
            operation.completed_at = datetime.utcnow()
            operation.results = {
                'updated_records': successful_count,
                'failed_updates': failed_count,
                'update_fields': list(update_data.keys())
            }
            
            execution_time = (operation.completed_at - operation.started_at).total_seconds()
            
            return BulkOperationResult(
                operation_id=operation_id,
                success=failed_count == 0,
                total_processed=len(record_ids),
                successful_count=successful_count,
                failed_count=failed_count,
                errors=errors,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            operation.status = OperationStatus.FAILED
            operation.completed_at = datetime.utcnow()
            raise
    
    def process_bulk_export(self, operation_id: str, filters: Dict = None, 
                          format: str = 'csv') -> BulkOperationResult:
        """Process bulk export operation"""
        try:
            operation = self.operations.get(operation_id)
            if not operation:
                raise ValueError(f"Operation {operation_id} not found")
            
            operation.status = OperationStatus.PROCESSING
            operation.started_at = datetime.utcnow()
            
            # Simulate data retrieval and export
            export_data = self._get_export_data(operation.entity_type, filters or {})
            operation.total_records = len(export_data)
            
            # Generate export file
            output_filename = f"{operation.entity_type.value}_export_{operation.id}.{format}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            if format.lower() == 'csv':
                self._export_to_csv(export_data, output_path)
            elif format.lower() == 'json':
                self._export_to_json(export_data, output_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            # Update progress
            operation.processed_records = len(export_data)
            operation.successful_records = len(export_data)
            operation.progress_percentage = 100.0
            
            # Complete operation
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = datetime.utcnow()
            operation.results = {
                'exported_records': len(export_data),
                'output_file': output_filename,
                'format': format
            }
            
            execution_time = (operation.completed_at - operation.started_at).total_seconds()
            
            return BulkOperationResult(
                operation_id=operation_id,
                success=True,
                total_processed=len(export_data),
                successful_count=len(export_data),
                failed_count=0,
                errors=[],
                execution_time_seconds=execution_time,
                output_file_path=output_path
            )
            
        except Exception as e:
            logger.error(f"Bulk export failed: {e}")
            operation.status = OperationStatus.FAILED
            operation.completed_at = datetime.utcnow()
            raise
    
    def _parse_csv_data(self, csv_data: str) -> List[Dict]:
        """Parse CSV data into list of dictionaries"""
        try:
            csv_file = io.StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            return list(reader)
        except Exception as e:
            logger.error(f"CSV parsing failed: {e}")
            raise ValueError(f"Invalid CSV data: {str(e)}")
    
    def _process_chunk(self, entity_type: EntityType, chunk_data: List[Dict], 
                      operation_type: OperationType) -> Dict:
        """Process a chunk of data"""
        successful = 0
        failed = 0
        errors = []
        
        for idx, record in enumerate(chunk_data):
            try:
                # Simulate processing based on entity type and operation
                if entity_type == EntityType.PROPERTIES:
                    self._process_property_record(record, operation_type)
                elif entity_type == EntityType.TENANTS:
                    self._process_tenant_record(record, operation_type)
                elif entity_type == EntityType.MAINTENANCE_REQUESTS:
                    self._process_maintenance_record(record, operation_type)
                elif entity_type == EntityType.USERS:
                    self._process_user_record(record, operation_type)
                
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    'record_index': idx,
                    'record_data': record,
                    'error': str(e)
                })
        
        return {
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def _process_bulk_update_chunk(self, entity_type: EntityType, record_ids: List[str], 
                                 update_data: Dict) -> Dict:
        """Process a chunk of bulk updates"""
        successful = 0
        failed = 0
        errors = []
        
        for record_id in record_ids:
            try:
                # Simulate update operation
                if entity_type == EntityType.PROPERTIES:
                    # Would update property in database
                    pass
                elif entity_type == EntityType.TENANTS:
                    # Would update tenant in database
                    pass
                elif entity_type == EntityType.MAINTENANCE_REQUESTS:
                    # Would update maintenance request in database
                    pass
                
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    'record_id': record_id,
                    'error': str(e)
                })
        
        return {
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def _process_property_record(self, record: Dict, operation_type: OperationType):
        """Process a property record"""
        # Simulate property processing
        if operation_type == OperationType.CREATE:
            # Would create property in database
            logger.debug(f"Creating property: {record.get('property_name')}")
        elif operation_type == OperationType.UPDATE:
            # Would update property in database
            logger.debug(f"Updating property: {record.get('property_name')}")
        
        # Simulate potential failure for some records
        if record.get('property_name', '').lower().startswith('invalid'):
            raise ValueError("Invalid property name")
    
    def _process_tenant_record(self, record: Dict, operation_type: OperationType):
        """Process a tenant record"""
        # Simulate tenant processing
        logger.debug(f"Processing tenant: {record.get('first_name')} {record.get('last_name')}")
        
        # Simulate potential failure
        if record.get('email', '').endswith('invalid.com'):
            raise ValueError("Invalid email domain")
    
    def _process_maintenance_record(self, record: Dict, operation_type: OperationType):
        """Process a maintenance record"""
        # Simulate maintenance request processing
        logger.debug(f"Processing maintenance: {record.get('title')}")
    
    def _process_user_record(self, record: Dict, operation_type: OperationType):
        """Process a user record"""
        # Simulate user processing
        logger.debug(f"Processing user: {record.get('username')}")
    
    def _get_export_data(self, entity_type: EntityType, filters: Dict) -> List[Dict]:
        """Get data for export based on entity type and filters"""
        # Simulate data retrieval - in production, this would query the database
        if entity_type == EntityType.PROPERTIES:
            return [
                {
                    'id': 1,
                    'property_name': 'Sunset Apartments',
                    'address': '123 Main St',
                    'property_type': 'apartment',
                    'rent_amount': 1200,
                    'bedrooms': 2,
                    'bathrooms': 1,
                    'status': 'occupied'
                },
                {
                    'id': 2,
                    'property_name': 'Downtown Loft',
                    'address': '456 Oak Ave',
                    'property_type': 'loft',
                    'rent_amount': 1800,
                    'bedrooms': 1,
                    'bathrooms': 1,
                    'status': 'available'
                }
            ]
        elif entity_type == EntityType.TENANTS:
            return [
                {
                    'id': 1,
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@email.com',
                    'phone': '555-1234',
                    'property_id': 1,
                    'lease_start': '2023-01-01',
                    'lease_end': '2023-12-31'
                }
            ]
        else:
            return []
    
    def _export_to_csv(self, data: List[Dict], output_path: str):
        """Export data to CSV file"""
        if not data:
            return
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
    
    def _export_to_json(self, data: List[Dict], output_path: str):
        """Export data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str)
    
    def get_operation_status(self, operation_id: str) -> Optional[BulkOperation]:
        """Get status of a bulk operation"""
        return self.operations.get(operation_id)
    
    def get_operations_summary(self, user_id: Optional[int] = None, 
                             limit: int = 50) -> List[Dict]:
        """Get summary of bulk operations"""
        operations = list(self.operations.values())
        
        # Filter by user if specified
        if user_id:
            operations = [op for op in operations if op.created_by == user_id]
        
        # Sort by creation date (newest first)
        operations.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limit results
        operations = operations[:limit]
        
        # Convert to summary format
        summary = []
        for op in operations:
            summary.append({
                'id': op.id,
                'operation_type': op.operation_type.value,
                'entity_type': op.entity_type.value,
                'status': op.status.value,
                'created_at': op.created_at.isoformat(),
                'completed_at': op.completed_at.isoformat() if op.completed_at else None,
                'total_records': op.total_records,
                'successful_records': op.successful_records,
                'failed_records': op.failed_records,
                'progress_percentage': op.progress_percentage,
                'created_by': op.created_by
            })
        
        return summary
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a bulk operation"""
        try:
            operation = self.operations.get(operation_id)
            if not operation:
                return False
            
            if operation.status in [OperationStatus.QUEUED, OperationStatus.PROCESSING]:
                operation.status = OperationStatus.CANCELLED
                operation.completed_at = datetime.utcnow()
                logger.info(f"Cancelled bulk operation: {operation_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel operation {operation_id}: {e}")
            return False

# Singleton instance
_bulk_operations_service = None

def get_bulk_operations_service() -> BulkOperationsService:
    """Get singleton bulk operations service instance"""
    global _bulk_operations_service
    if _bulk_operations_service is None:
        _bulk_operations_service = BulkOperationsService()
    return _bulk_operations_service

if __name__ == "__main__":
    # Test the bulk operations service
    service = get_bulk_operations_service()
    
    print("📊 Bulk Operations Service Test")
    
    # Test bulk import
    csv_data = """property_name,address,property_type,rent_amount,bedrooms,bathrooms
    Sunset Apartments,123 Main St,apartment,1200,2,1
    Downtown Loft,456 Oak Ave,loft,1800,1,1
    Garden View,789 Pine St,house,2000,3,2"""
    
    operation_id = service.create_bulk_operation(
        operation_type=OperationType.IMPORT,
        entity_type=EntityType.PROPERTIES,
        created_by=1,
        parameters={'file_type': 'csv'}
    )
    
    print(f"Created operation: {operation_id}")
    
    # Process import
    result = service.process_bulk_import(operation_id, csv_data, 'csv')
    print(f"Import result: {result.success}, processed: {result.total_processed}")
    
    # Test bulk update
    update_operation_id = service.create_bulk_operation(
        operation_type=OperationType.UPDATE,
        entity_type=EntityType.PROPERTIES,
        created_by=1
    )
    
    update_result = service.process_bulk_update(
        update_operation_id,
        record_ids=['1', '2', '3'],
        update_data={'status': 'available', 'rent_amount': 1300}
    )
    print(f"Update result: {update_result.success}, updated: {update_result.successful_count}")
    
    # Test operations summary
    summary = service.get_operations_summary()
    print(f"Operations summary: {len(summary)} operations")
    
    print("✅ Bulk operations service is ready!")