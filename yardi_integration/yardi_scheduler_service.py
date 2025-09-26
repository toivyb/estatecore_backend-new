"""
Yardi Scheduler Service

Manages scheduled synchronization jobs, automated workflows, and recurring tasks
for the Yardi integration system.
"""

import os
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import threading
import schedule
import time
from croniter import croniter

from .models import SyncDirection, SyncMode

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    """Schedule type enumeration"""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"
    ON_DEMAND = "on_demand"

class ScheduleStatus(Enum):
    """Schedule status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"

@dataclass
class ScheduledJob:
    """Scheduled job configuration"""
    schedule_id: str
    organization_id: str
    job_name: str
    schedule_type: ScheduleType
    sync_direction: SyncDirection
    sync_mode: SyncMode
    entity_types: List[str]
    
    # Schedule configuration
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    
    # Execution settings
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    max_runtime: int = 3600  # seconds
    timeout: int = 300  # seconds
    retry_on_failure: bool = True
    max_retries: int = 3
    
    # Execution tracking
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    
    # Notifications
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_emails: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScheduleExecution:
    """Schedule execution record"""
    execution_id: str
    schedule_id: str
    organization_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    sync_job_id: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

class YardiSchedulerService:
    """Yardi Scheduler Service for automated sync jobs"""
    
    def __init__(self, sync_service):
        self.sync_service = sync_service
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}
        self.executions: Dict[str, ScheduleExecution] = {}
        
        # Scheduler state
        self.scheduler_running = False
        self.scheduler_thread = None
        
        # Default schedules
        self._setup_default_schedules()
        
        logger.info("Yardi Scheduler Service initialized")
    
    def _setup_default_schedules(self):
        """Setup default scheduled jobs"""
        
        # Daily full sync schedule
        default_daily_sync = ScheduledJob(
            schedule_id="default_daily_sync",
            organization_id="default",
            job_name="Daily Full Sync",
            schedule_type=ScheduleType.CRON,
            sync_direction=SyncDirection.BOTH,
            sync_mode=SyncMode.INCREMENTAL,
            entity_types=["properties", "units", "tenants", "leases"],
            cron_expression="0 2 * * *",  # 2 AM daily
            notify_on_failure=True
        )
        
        # Hourly incremental sync
        default_hourly_sync = ScheduledJob(
            schedule_id="default_hourly_sync",
            organization_id="default",
            job_name="Hourly Incremental Sync",
            schedule_type=ScheduleType.INTERVAL,
            sync_direction=SyncDirection.BOTH,
            sync_mode=SyncMode.INCREMENTAL,
            entity_types=["payments", "work_orders"],
            interval_minutes=60,
            notify_on_failure=True
        )
        
        # Store default schedules
        self.scheduled_jobs[default_daily_sync.schedule_id] = default_daily_sync
        self.scheduled_jobs[default_hourly_sync.schedule_id] = default_hourly_sync
    
    # =====================================================
    # SCHEDULE MANAGEMENT
    # =====================================================
    
    def create_schedule(self, organization_id: str, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new scheduled job"""
        try:
            schedule_id = f"schedule_{organization_id}_{uuid.uuid4().hex[:8]}"
            
            # Validate schedule configuration
            validation_result = self._validate_schedule_config(schedule_config)
            if not validation_result['valid']:
                return {
                    "success": False,
                    "error": "Invalid schedule configuration",
                    "validation_errors": validation_result['errors']
                }
            
            # Create scheduled job
            scheduled_job = ScheduledJob(
                schedule_id=schedule_id,
                organization_id=organization_id,
                job_name=schedule_config['job_name'],
                schedule_type=ScheduleType(schedule_config['schedule_type']),
                sync_direction=SyncDirection(schedule_config['sync_direction']),
                sync_mode=SyncMode(schedule_config.get('sync_mode', 'incremental')),
                entity_types=schedule_config['entity_types'],
                cron_expression=schedule_config.get('cron_expression'),
                interval_minutes=schedule_config.get('interval_minutes'),
                scheduled_time=schedule_config.get('scheduled_time'),
                max_runtime=schedule_config.get('max_runtime', 3600),
                timeout=schedule_config.get('timeout', 300),
                retry_on_failure=schedule_config.get('retry_on_failure', True),
                max_retries=schedule_config.get('max_retries', 3),
                notify_on_success=schedule_config.get('notify_on_success', False),
                notify_on_failure=schedule_config.get('notify_on_failure', True),
                notification_emails=schedule_config.get('notification_emails', []),
                created_by=schedule_config.get('created_by'),
                configuration=schedule_config.get('configuration', {})
            )
            
            # Calculate next run time
            scheduled_job.next_run = self._calculate_next_run(scheduled_job)
            
            # Store scheduled job
            self.scheduled_jobs[schedule_id] = scheduled_job
            
            # Start scheduler if not running
            if not self.scheduler_running:
                self.start_scheduler()
            
            logger.info(f"Created schedule {schedule_id} for organization {organization_id}")
            
            return {
                "success": True,
                "schedule_id": schedule_id,
                "next_run": scheduled_job.next_run.isoformat() if scheduled_job.next_run else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create schedule: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update scheduled job configuration"""
        try:
            scheduled_job = self.scheduled_jobs.get(schedule_id)
            if not scheduled_job:
                return {
                    "success": False,
                    "error": "Schedule not found"
                }
            
            # Update allowed fields
            allowed_fields = [
                'job_name', 'cron_expression', 'interval_minutes', 'scheduled_time',
                'status', 'max_runtime', 'timeout', 'retry_on_failure', 'max_retries',
                'notify_on_success', 'notify_on_failure', 'notification_emails'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(scheduled_job, field):
                    setattr(scheduled_job, field, value)
            
            # Recalculate next run time if schedule changed
            if any(field in updates for field in ['cron_expression', 'interval_minutes', 'scheduled_time']):
                scheduled_job.next_run = self._calculate_next_run(scheduled_job)
            
            return {
                "success": True,
                "next_run": scheduled_job.next_run.isoformat() if scheduled_job.next_run else None
            }
            
        except Exception as e:
            logger.error(f"Failed to update schedule: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Delete scheduled job"""
        try:
            if schedule_id not in self.scheduled_jobs:
                return {
                    "success": False,
                    "error": "Schedule not found"
                }
            
            del self.scheduled_jobs[schedule_id]
            
            return {
                "success": True,
                "message": "Schedule deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete schedule: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def pause_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Pause scheduled job"""
        scheduled_job = self.scheduled_jobs.get(schedule_id)
        if not scheduled_job:
            return {"success": False, "error": "Schedule not found"}
        
        scheduled_job.status = ScheduleStatus.PAUSED
        return {"success": True, "message": "Schedule paused"}
    
    def resume_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Resume scheduled job"""
        scheduled_job = self.scheduled_jobs.get(schedule_id)
        if not scheduled_job:
            return {"success": False, "error": "Schedule not found"}
        
        scheduled_job.status = ScheduleStatus.ACTIVE
        scheduled_job.next_run = self._calculate_next_run(scheduled_job)
        return {"success": True, "message": "Schedule resumed"}
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduledJob]:
        """Get scheduled job by ID"""
        return self.scheduled_jobs.get(schedule_id)
    
    def list_schedules(self, organization_id: Optional[str] = None) -> List[ScheduledJob]:
        """List scheduled jobs"""
        if organization_id:
            return [
                job for job in self.scheduled_jobs.values()
                if job.organization_id == organization_id
            ]
        return list(self.scheduled_jobs.values())
    
    # =====================================================
    # SCHEDULER EXECUTION
    # =====================================================
    
    def start_scheduler(self):
        """Start the scheduler"""
        if not self.scheduler_running:
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            logger.info("Scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            try:
                current_time = datetime.utcnow()
                
                # Check for jobs ready to run
                for scheduled_job in self.scheduled_jobs.values():
                    if self._should_run_job(scheduled_job, current_time):
                        # Execute job asynchronously
                        asyncio.run(self._execute_scheduled_job(scheduled_job))
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)
    
    def _should_run_job(self, scheduled_job: ScheduledJob, current_time: datetime) -> bool:
        """Check if job should run now"""
        if scheduled_job.status != ScheduleStatus.ACTIVE:
            return False
        
        if not scheduled_job.next_run:
            return False
        
        return current_time >= scheduled_job.next_run
    
    async def _execute_scheduled_job(self, scheduled_job: ScheduledJob):
        """Execute a scheduled job"""
        execution_id = f"exec_{scheduled_job.schedule_id}_{uuid.uuid4().hex[:8]}"
        
        execution = ScheduleExecution(
            execution_id=execution_id,
            schedule_id=scheduled_job.schedule_id,
            organization_id=scheduled_job.organization_id,
            started_at=datetime.utcnow()
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Create sync job
            sync_job = await self.sync_service.create_sync_job(
                organization_id=scheduled_job.organization_id,
                sync_direction=scheduled_job.sync_direction,
                entity_types=scheduled_job.entity_types,
                sync_mode=scheduled_job.sync_mode,
                configuration=scheduled_job.configuration
            )
            
            execution.sync_job_id = sync_job.job_id
            
            # Execute sync job
            result = await self.sync_service.execute_sync_job(sync_job.job_id)
            
            # Update execution record
            execution.completed_at = datetime.utcnow()
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
            
            if result['success']:
                execution.status = "completed"
                scheduled_job.successful_runs += 1
                
                if scheduled_job.notify_on_success:
                    await self._send_notification(scheduled_job, execution, "success")
            else:
                execution.status = "failed"
                execution.error_message = result.get('error')
                scheduled_job.failed_runs += 1
                
                if scheduled_job.notify_on_failure:
                    await self._send_notification(scheduled_job, execution, "failure")
            
            # Update schedule counters
            scheduled_job.total_runs += 1
            scheduled_job.last_run = datetime.utcnow()
            
            # Calculate next run time
            scheduled_job.next_run = self._calculate_next_run(scheduled_job)
            
            logger.info(f"Executed scheduled job {scheduled_job.schedule_id}")
            
        except Exception as e:
            execution.completed_at = datetime.utcnow()
            execution.status = "failed"
            execution.error_message = str(e)
            scheduled_job.failed_runs += 1
            
            if scheduled_job.notify_on_failure:
                await self._send_notification(scheduled_job, execution, "failure")
            
            logger.error(f"Scheduled job execution failed: {e}")
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
    def _calculate_next_run(self, scheduled_job: ScheduledJob) -> Optional[datetime]:
        """Calculate next run time for scheduled job"""
        current_time = datetime.utcnow()
        
        if scheduled_job.schedule_type == ScheduleType.CRON:
            if scheduled_job.cron_expression:
                cron = croniter(scheduled_job.cron_expression, current_time)
                return cron.get_next(datetime)
        
        elif scheduled_job.schedule_type == ScheduleType.INTERVAL:
            if scheduled_job.interval_minutes:
                return current_time + timedelta(minutes=scheduled_job.interval_minutes)
        
        elif scheduled_job.schedule_type == ScheduleType.ONE_TIME:
            if scheduled_job.scheduled_time and scheduled_job.scheduled_time > current_time:
                return scheduled_job.scheduled_time
        
        return None
    
    def _validate_schedule_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schedule configuration"""
        errors = []
        
        required_fields = ['job_name', 'schedule_type', 'sync_direction', 'entity_types']
        for field in required_fields:
            if field not in config:
                errors.append(f"Required field '{field}' is missing")
        
        schedule_type = config.get('schedule_type')
        if schedule_type == 'cron' and not config.get('cron_expression'):
            errors.append("Cron expression is required for cron schedule type")
        
        if schedule_type == 'interval' and not config.get('interval_minutes'):
            errors.append("Interval minutes is required for interval schedule type")
        
        if schedule_type == 'one_time' and not config.get('scheduled_time'):
            errors.append("Scheduled time is required for one-time schedule type")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _send_notification(self, scheduled_job: ScheduledJob, 
                               execution: ScheduleExecution, status: str):
        """Send notification for job execution"""
        if not scheduled_job.notification_emails:
            return
        
        subject = f"Yardi Sync Job {status.title()}: {scheduled_job.job_name}"
        
        if status == "success":
            message = f"Scheduled job '{scheduled_job.job_name}' completed successfully."
        else:
            message = f"Scheduled job '{scheduled_job.job_name}' failed: {execution.error_message}"
        
        # Here you would integrate with your email service
        logger.info(f"Would send notification: {subject}")
    
    def get_execution_history(self, schedule_id: Optional[str] = None, 
                            limit: int = 50) -> List[ScheduleExecution]:
        """Get execution history"""
        executions = list(self.executions.values())
        
        if schedule_id:
            executions = [e for e in executions if e.schedule_id == schedule_id]
        
        # Sort by start time, most recent first
        executions.sort(key=lambda e: e.started_at, reverse=True)
        
        return executions[:limit]
    
    def get_scheduler_status(self, organization_id: str) -> Dict[str, Any]:
        """Get scheduler status for organization"""
        schedules = self.list_schedules(organization_id)
        active_schedules = [s for s in schedules if s.status == ScheduleStatus.ACTIVE]
        
        recent_executions = [
            e for e in self.executions.values()
            if e.organization_id == organization_id
        ]
        
        failed_executions = [e for e in recent_executions if e.status == "failed"]
        
        return {
            "enabled": len(active_schedules) > 0,
            "active_schedules": len(active_schedules),
            "recent_executions": len(recent_executions),
            "failed_executions": len(failed_executions),
            "healthy": len(failed_executions) < 5,  # Simple health check
            "scheduler_running": self.scheduler_running
        }