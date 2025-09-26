"""
Yardi Integration Data Models

Database models for storing Yardi integration configuration, connections,
sync jobs, mappings, and audit data.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from dataclasses import dataclass

Base = declarative_base()

class YardiProductType(Enum):
    """Supported Yardi products"""
    VOYAGER = "voyager"
    BREEZE = "breeze"
    GENESIS2 = "genesis2"
    RENT_CAFE = "rent_cafe"
    MAINTENANCE_CAFE = "maintenance_cafe"
    PROCURE_CAFE = "procure_cafe"
    INVEST_CAFE = "invest_cafe"

class YardiConnectionType(Enum):
    """Yardi connection types"""
    API = "api"
    SFTP = "sftp"
    WEBSERVICE = "webservice"
    DATABASE = "database"

class YardiAuthMethod(Enum):
    """Yardi authentication methods"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    USERNAME_PASSWORD = "username_password"
    CERTIFICATE = "certificate"
    TOKEN = "token"

class SyncDirection(Enum):
    """Data synchronization directions"""
    TO_YARDI = "to_yardi"
    FROM_YARDI = "from_yardi"
    BOTH = "both"

class SyncStatus(Enum):
    """Sync job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class SyncMode(Enum):
    """Sync operation modes"""
    FULL = "full"
    INCREMENTAL = "incremental"
    REAL_TIME = "real_time"
    MANUAL = "manual"

class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    YARDI_WINS = "yardi_wins"
    ESTATECORE_WINS = "estatecore_wins"
    MANUAL_REVIEW = "manual_review"
    MERGE = "merge"
    SKIP = "skip"

class YardiConnection(Base):
    """Yardi connection configuration and credentials"""
    __tablename__ = 'yardi_connections'
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    connection_name = Column(String(255), nullable=False)
    
    # Yardi system details
    yardi_product = Column(String(50), nullable=False)  # YardiProductType
    connection_type = Column(String(50), nullable=False)  # YardiConnectionType
    auth_method = Column(String(50), nullable=False)  # YardiAuthMethod
    
    # Connection endpoints
    base_url = Column(String(255))
    api_endpoint = Column(String(255))
    sftp_host = Column(String(255))
    sftp_port = Column(Integer)
    database_host = Column(String(255))
    database_port = Column(Integer)
    database_name = Column(String(255))
    
    # Authentication credentials (encrypted)
    credentials = Column(Text)  # JSON encrypted credentials
    
    # Company/tenant information
    company_info = Column(JSON)
    yardi_company_id = Column(String(100))
    yardi_database_id = Column(String(100))
    
    # Connection status
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False)
    last_test_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    connection_validated = Column(Boolean, default=False)
    
    # Token management
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    
    # Rate limiting and performance
    rate_limit_per_minute = Column(Integer, default=60)
    request_timeout = Column(Integer, default=30)
    max_retries = Column(Integer, default=3)
    
    # Capabilities and features
    supported_entities = Column(JSON)  # List of supported entity types
    supported_operations = Column(JSON)  # List of supported operations
    api_version = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sync_jobs = relationship("YardiSyncJob", back_populates="connection")
    field_mappings = relationship("YardiFieldMapping", back_populates="connection")
    audit_logs = relationship("YardiAuditLog", back_populates="connection")

class YardiSyncJob(Base):
    """Yardi data synchronization jobs"""
    __tablename__ = 'yardi_sync_jobs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), unique=True, nullable=False)
    connection_id = Column(String(50), ForeignKey('yardi_connections.connection_id'), nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    
    # Job configuration
    job_name = Column(String(255))
    sync_direction = Column(String(20), nullable=False)  # SyncDirection
    sync_mode = Column(String(20), nullable=False)  # SyncMode
    entity_types = Column(JSON)  # List of entity types to sync
    
    # Sync parameters
    since_timestamp = Column(DateTime)  # For incremental syncs
    until_timestamp = Column(DateTime)
    batch_size = Column(Integer, default=100)
    parallel_workers = Column(Integer, default=1)
    
    # Job status
    status = Column(String(20), default='pending')  # SyncStatus
    priority = Column(String(20), default='normal')
    progress_percentage = Column(Float, default=0.0)
    
    # Execution details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_duration = Column(Integer)  # seconds
    actual_duration = Column(Integer)  # seconds
    
    # Results and statistics
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Configuration and settings
    conflict_resolution = Column(String(50), default='manual_review')  # ConflictResolutionStrategy
    validation_enabled = Column(Boolean, default=True)
    backup_enabled = Column(Boolean, default=True)
    dry_run = Column(Boolean, default=False)
    
    # Sync results by entity type
    sync_results = Column(JSON)  # Detailed results per entity type
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("YardiConnection", back_populates="sync_jobs")
    sync_records = relationship("YardiSyncRecord", back_populates="sync_job")

class YardiSyncRecord(Base):
    """Individual sync record details"""
    __tablename__ = 'yardi_sync_records'
    
    id = Column(Integer, primary_key=True)
    record_id = Column(String(50), unique=True, nullable=False)
    job_id = Column(String(50), ForeignKey('yardi_sync_jobs.job_id'), nullable=False)
    
    # Record identification
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    estatecore_id = Column(String(100))
    yardi_id = Column(String(100))
    
    # Sync details
    operation = Column(String(20))  # create, update, delete
    direction = Column(String(20))  # to_yardi, from_yardi
    status = Column(String(20))  # success, failed, skipped, conflict
    
    # Data
    source_data = Column(JSON)
    target_data = Column(JSON)
    transformed_data = Column(JSON)
    
    # Conflict resolution
    conflict_detected = Column(Boolean, default=False)
    conflict_reason = Column(Text)
    conflict_resolution = Column(String(50))
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    
    # Error handling
    error_message = Column(Text)
    error_code = Column(String(50))
    retry_count = Column(Integer, default=0)
    
    # Validation
    validation_passed = Column(Boolean, default=True)
    validation_errors = Column(JSON)
    
    # Timestamps
    processed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sync_job = relationship("YardiSyncJob", back_populates="sync_records")

class YardiFieldMapping(Base):
    """Field mapping configuration between EstateCore and Yardi"""
    __tablename__ = 'yardi_field_mappings'
    
    id = Column(Integer, primary_key=True)
    mapping_id = Column(String(50), unique=True, nullable=False)
    connection_id = Column(String(50), ForeignKey('yardi_connections.connection_id'), nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    
    # Mapping configuration
    mapping_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Field mappings
    estatecore_to_yardi = Column(JSON)  # EstateCore field -> Yardi field mappings
    yardi_to_estatecore = Column(JSON)  # Yardi field -> EstateCore field mappings
    
    # Transformation rules
    data_transformations = Column(JSON)  # Field transformation rules
    validation_rules = Column(JSON)  # Data validation rules
    default_values = Column(JSON)  # Default values for missing fields
    
    # Conditional mappings
    conditional_mappings = Column(JSON)  # Conditional field mappings
    business_rules = Column(JSON)  # Business rule configurations
    
    # Sync behavior
    sync_direction = Column(String(20), default='both')  # SyncDirection
    conflict_resolution = Column(String(50), default='manual_review')
    field_level_sync = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("YardiConnection", back_populates="field_mappings")

class YardiWebhookConfig(Base):
    """Yardi webhook configuration"""
    __tablename__ = 'yardi_webhook_configs'
    
    id = Column(Integer, primary_key=True)
    webhook_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    connection_id = Column(String(50), ForeignKey('yardi_connections.connection_id'))
    
    # Webhook configuration
    webhook_name = Column(String(255), nullable=False)
    webhook_url = Column(String(500), nullable=False)
    secret_key = Column(String(255))
    
    # Event configuration
    enabled_events = Column(JSON)  # List of enabled webhook events
    entity_filters = Column(JSON)  # Entity type filters
    property_filters = Column(JSON)  # Property-specific filters
    
    # Delivery settings
    retry_enabled = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # seconds
    timeout = Column(Integer, default=30)  # seconds
    
    # Authentication
    auth_method = Column(String(50))  # none, api_key, oauth2, custom
    auth_config = Column(JSON)  # Authentication configuration
    
    # Status and monitoring
    is_active = Column(Boolean, default=True)
    last_delivery_at = Column(DateTime)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    deliveries = relationship("YardiWebhookDelivery", back_populates="webhook_config")

class YardiWebhookDelivery(Base):
    """Yardi webhook delivery log"""
    __tablename__ = 'yardi_webhook_deliveries'
    
    id = Column(Integer, primary_key=True)
    delivery_id = Column(String(50), unique=True, nullable=False)
    webhook_id = Column(String(50), ForeignKey('yardi_webhook_configs.webhook_id'), nullable=False)
    
    # Delivery details
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    
    # Request details
    payload = Column(JSON)
    headers = Column(JSON)
    url = Column(String(500))
    
    # Response details
    status_code = Column(Integer)
    response_body = Column(Text)
    response_headers = Column(JSON)
    
    # Delivery status
    delivered = Column(Boolean, default=False)
    delivery_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    next_retry_at = Column(DateTime)
    
    # Error information
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Performance
    response_time = Column(Float)  # milliseconds
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    
    # Relationships
    webhook_config = relationship("YardiWebhookConfig", back_populates="deliveries")

class YardiScheduleConfig(Base):
    """Yardi sync schedule configuration"""
    __tablename__ = 'yardi_schedule_configs'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    connection_id = Column(String(50), ForeignKey('yardi_connections.connection_id'))
    
    # Schedule configuration
    schedule_name = Column(String(255), nullable=False)
    schedule_type = Column(String(50))  # cron, interval, one_time
    cron_expression = Column(String(100))
    interval_minutes = Column(Integer)
    
    # Sync configuration
    sync_direction = Column(String(20), default='both')
    sync_mode = Column(String(20), default='incremental')
    entity_types = Column(JSON)
    
    # Execution settings
    is_active = Column(Boolean, default=True)
    timezone = Column(String(50), default='UTC')
    max_duration = Column(Integer, default=3600)  # seconds
    
    # Status
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # Error handling
    on_failure = Column(String(50), default='retry')  # retry, skip, pause
    notification_enabled = Column(Boolean, default=True)
    notification_emails = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class YardiAuditLog(Base):
    """Yardi integration audit log"""
    __tablename__ = 'yardi_audit_logs'
    
    id = Column(Integer, primary_key=True)
    log_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    connection_id = Column(String(50), ForeignKey('yardi_connections.connection_id'))
    
    # Event details
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(50))  # connection, sync, webhook, config
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    
    # User and context
    user_id = Column(String(100))
    user_email = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Event data
    event_data = Column(JSON)
    previous_values = Column(JSON)
    new_values = Column(JSON)
    
    # Event outcome
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Performance and metadata
    duration_ms = Column(Integer)
    request_id = Column(String(50))
    session_id = Column(String(50))
    
    # Timestamps
    event_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    connection = relationship("YardiConnection", back_populates="audit_logs")

class YardiDataQualityReport(Base):
    """Yardi data quality assessment reports"""
    __tablename__ = 'yardi_data_quality_reports'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    connection_id = Column(String(50), ForeignKey('yardi_connections.connection_id'))
    
    # Report details
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(50))  # manual, scheduled, automated
    entity_types = Column(JSON)
    
    # Quality metrics
    overall_score = Column(Float)
    completeness_score = Column(Float)
    accuracy_score = Column(Float)
    consistency_score = Column(Float)
    validity_score = Column(Float)
    
    # Detailed results
    quality_issues = Column(JSON)  # List of identified issues
    recommendations = Column(JSON)  # Improvement recommendations
    entity_scores = Column(JSON)  # Per-entity quality scores
    
    # Comparison data
    previous_report_id = Column(String(50))
    improvement_trends = Column(JSON)
    
    # Status
    report_status = Column(String(20), default='completed')
    generated_by = Column(String(100))
    
    # Timestamps
    report_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class YardiPerformanceMetrics(Base):
    """Yardi integration performance metrics"""
    __tablename__ = 'yardi_performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(String(50), nullable=False, index=True)
    connection_id = Column(String(50), ForeignKey('yardi_connections.connection_id'))
    
    # Metric details
    metric_name = Column(String(255), nullable=False)
    metric_category = Column(String(50))  # performance, reliability, usage
    metric_type = Column(String(50))  # counter, gauge, histogram
    
    # Metric values
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    tags = Column(JSON)  # Additional metric tags
    
    # Time series data
    time_bucket = Column(String(20))  # minute, hour, day, week, month
    bucket_start = Column(DateTime)
    bucket_end = Column(DateTime)
    
    # Aggregation info
    sample_count = Column(Integer)
    min_value = Column(Float)
    max_value = Column(Float)
    avg_value = Column(Float)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Data classes for API responses and internal use

@dataclass
class YardiEntityInfo:
    """Information about a Yardi entity"""
    entity_type: str
    entity_id: str
    yardi_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    last_sync: Optional[datetime] = None
    sync_status: Optional[str] = None
    data_hash: Optional[str] = None

@dataclass
class YardiSyncProgress:
    """Sync job progress information"""
    job_id: str
    status: str
    progress_percentage: float
    current_entity: Optional[str] = None
    processed_records: int = 0
    total_records: int = 0
    estimated_completion: Optional[datetime] = None
    errors: List[str] = None

@dataclass
class YardiConnectionHealth:
    """Connection health status"""
    connection_id: str
    is_healthy: bool
    last_test: datetime
    response_time: float
    error_count: int = 0
    uptime_percentage: float = 100.0
    issues: List[str] = None

@dataclass
class YardiConflictInfo:
    """Data conflict information"""
    entity_type: str
    entity_id: str
    conflict_type: str
    estatecore_data: Dict[str, Any]
    yardi_data: Dict[str, Any]
    suggested_resolution: str
    conflict_timestamp: datetime