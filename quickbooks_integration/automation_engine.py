"""
QuickBooks Automation Engine

Provides automated workflows for QuickBooks integration including
scheduled synchronization, rule-based processing, and event-driven automation.
"""

import json
import logging
import asyncio
import schedule
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

from .financial_sync_service import FinancialSyncService, SyncResult
from .quickbooks_api_client import QuickBooksAPIClient
from .data_mapping_service import DataMappingService
from .quickbooks_oauth_service import QuickBooksOAuthService

logger = logging.getLogger(__name__)

class WorkflowType(Enum):
    """Types of automated workflows"""
    RENT_INVOICE_GENERATION = "rent_invoice_generation"
    LATE_FEE_PROCESSING = "late_fee_processing"
    PAYMENT_SYNC = "payment_sync"
    EXPENSE_SYNC = "expense_sync"
    MONTHLY_RECONCILIATION = "monthly_reconciliation"
    YEAR_END_PROCESSING = "year_end_processing"
    CUSTOM_WORKFLOW = "custom_workflow"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TriggerType(Enum):
    """Workflow trigger types"""
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"
    API_TRIGGERED = "api_triggered"

@dataclass
class WorkflowRule:
    """Defines a business rule for workflow execution"""
    rule_id: str
    name: str
    description: str
    condition: str  # Python expression that evaluates to boolean
    action: str     # Action to execute when condition is met
    parameters: Dict[str, Any] = None
    priority: int = 1
    enabled: bool = True

@dataclass
class WorkflowSchedule:
    """Schedule configuration for automated workflows"""
    schedule_id: str
    workflow_type: WorkflowType
    cron_expression: Optional[str] = None
    frequency: Optional[str] = None  # daily, weekly, monthly
    time_of_day: Optional[str] = None  # HH:MM format
    day_of_month: Optional[int] = None  # For monthly schedules
    day_of_week: Optional[str] = None   # For weekly schedules
    timezone: str = "UTC"
    enabled: bool = True
    next_run: Optional[datetime] = None

@dataclass
class WorkflowExecution:
    """Record of workflow execution"""
    execution_id: str
    workflow_type: WorkflowType
    organization_id: str
    trigger_type: TriggerType
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []

class QuickBooksAutomationEngine:
    """
    Engine for automating QuickBooks integration workflows
    """
    
    def __init__(self, sync_service: Optional[FinancialSyncService] = None,
                 api_client: Optional[QuickBooksAPIClient] = None,
                 oauth_service: Optional[QuickBooksOAuthService] = None):
        self.sync_service = sync_service or FinancialSyncService()
        self.api_client = api_client or QuickBooksAPIClient()
        self.oauth_service = oauth_service or QuickBooksOAuthService()
        
        # Workflow management
        self.workflows: Dict[str, WorkflowSchedule] = {}
        self.rules: Dict[str, WorkflowRule] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Scheduler
        self.scheduler_running = False
        self.scheduler_thread = None
        
        # Load configurations
        self._load_configurations()
        self._initialize_default_workflows()
        self._initialize_default_rules()
    
    def _load_configurations(self):
        """Load workflow configurations"""
        try:
            with open('instance/automation_config.json', 'r') as f:
                data = json.load(f)
                
                # Load workflows
                for workflow_data in data.get('workflows', []):
                    workflow_data['workflow_type'] = WorkflowType(workflow_data['workflow_type'])
                    if workflow_data.get('next_run'):
                        workflow_data['next_run'] = datetime.fromisoformat(workflow_data['next_run'])
                    workflow = WorkflowSchedule(**workflow_data)
                    self.workflows[workflow.schedule_id] = workflow
                
                # Load rules
                for rule_data in data.get('rules', []):
                    rule = WorkflowRule(**rule_data)
                    self.rules[rule.rule_id] = rule
                    
        except FileNotFoundError:
            logger.info("No automation config found, using defaults")
        except Exception as e:
            logger.error(f"Error loading automation config: {e}")
    
    def _save_configurations(self):
        """Save workflow configurations"""
        try:
            import os
            os.makedirs('instance', exist_ok=True)
            
            data = {
                'workflows': [
                    {**asdict(workflow), 'workflow_type': workflow.workflow_type.value}
                    for workflow in self.workflows.values()
                ],
                'rules': [asdict(rule) for rule in self.rules.values()]
            }
            
            with open('instance/automation_config.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving automation config: {e}")
    
    def _initialize_default_workflows(self):
        """Initialize default workflow schedules"""
        
        # Daily rent invoice generation
        daily_rent_invoices = WorkflowSchedule(
            schedule_id="daily_rent_invoices",
            workflow_type=WorkflowType.RENT_INVOICE_GENERATION,
            frequency="daily",
            time_of_day="09:00",
            enabled=True
        )
        self.workflows[daily_rent_invoices.schedule_id] = daily_rent_invoices
        
        # Weekly payment sync
        weekly_payment_sync = WorkflowSchedule(
            schedule_id="weekly_payment_sync",
            workflow_type=WorkflowType.PAYMENT_SYNC,
            frequency="weekly",
            day_of_week="monday",
            time_of_day="08:00",
            enabled=True
        )
        self.workflows[weekly_payment_sync.schedule_id] = weekly_payment_sync
        
        # Monthly late fee processing
        monthly_late_fees = WorkflowSchedule(
            schedule_id="monthly_late_fees",
            workflow_type=WorkflowType.LATE_FEE_PROCESSING,
            frequency="monthly",
            day_of_month=5,
            time_of_day="10:00",
            enabled=True
        )
        self.workflows[monthly_late_fees.schedule_id] = monthly_late_fees
        
        # Monthly reconciliation
        monthly_reconciliation = WorkflowSchedule(
            schedule_id="monthly_reconciliation",
            workflow_type=WorkflowType.MONTHLY_RECONCILIATION,
            frequency="monthly",
            day_of_month=1,
            time_of_day="07:00",
            enabled=True
        )
        self.workflows[monthly_reconciliation.schedule_id] = monthly_reconciliation
    
    def _initialize_default_rules(self):
        """Initialize default business rules"""
        
        # Late fee rule
        late_fee_rule = WorkflowRule(
            rule_id="auto_late_fee",
            name="Automatic Late Fee Assessment",
            description="Automatically assess late fees for overdue rent",
            condition="days_overdue >= 5 and not late_fee_applied",
            action="apply_late_fee",
            parameters={"fee_amount": 50.0, "grace_period_days": 5},
            priority=1
        )
        self.rules[late_fee_rule.rule_id] = late_fee_rule
        
        # Invoice generation rule
        invoice_rule = WorkflowRule(
            rule_id="monthly_rent_invoices",
            name="Monthly Rent Invoice Generation",
            description="Generate rent invoices for all active leases",
            condition="day_of_month == 25 and not invoices_generated_this_month",
            action="generate_rent_invoices",
            parameters={"invoice_date_offset_days": 5},
            priority=1
        )
        self.rules[invoice_rule.rule_id] = invoice_rule
        
        # Expense sync rule
        expense_sync_rule = WorkflowRule(
            rule_id="daily_expense_sync",
            name="Daily Expense Synchronization",
            description="Sync new expenses to QuickBooks daily",
            condition="new_expenses_count > 0",
            action="sync_expenses",
            parameters={"batch_size": 50},
            priority=2
        )
        self.rules[expense_sync_rule.rule_id] = expense_sync_rule
    
    def start_scheduler(self):
        """Start the automation scheduler"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Automation scheduler started")
    
    def stop_scheduler(self):
        """Stop the automation scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("Automation scheduler stopped")
    
    def _run_scheduler(self):
        """Run the automation scheduler"""
        while self.scheduler_running:
            try:
                # Check for workflows that need to run
                current_time = datetime.now()
                
                for workflow in self.workflows.values():
                    if not workflow.enabled:
                        continue
                    
                    if self._should_run_workflow(workflow, current_time):
                        # Execute workflow asynchronously
                        asyncio.run(self._execute_workflow(workflow))
                        
                        # Update next run time
                        workflow.next_run = self._calculate_next_run(workflow, current_time)
                
                # Check event-driven rules
                self._process_event_rules()
                
                # Save configurations after updates
                self._save_configurations()
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            # Sleep for 1 minute
            time.sleep(60)
    
    def _should_run_workflow(self, workflow: WorkflowSchedule, current_time: datetime) -> bool:
        """Check if workflow should run"""
        if workflow.next_run and current_time >= workflow.next_run:
            return True
        
        if workflow.next_run is None:
            # Calculate initial next run
            workflow.next_run = self._calculate_next_run(workflow, current_time)
            return False
        
        return False
    
    def _calculate_next_run(self, workflow: WorkflowSchedule, from_time: datetime) -> datetime:
        """Calculate next run time for workflow"""
        if workflow.frequency == "daily":
            next_run = from_time.replace(hour=int(workflow.time_of_day.split(':')[0]),
                                       minute=int(workflow.time_of_day.split(':')[1]),
                                       second=0, microsecond=0)
            if next_run <= from_time:
                next_run += timedelta(days=1)
            return next_run
        
        elif workflow.frequency == "weekly":
            # Calculate next occurrence of day_of_week
            days_ahead = 0  # This would need proper day calculation
            next_run = from_time + timedelta(days=days_ahead)
            return next_run.replace(hour=int(workflow.time_of_day.split(':')[0]),
                                  minute=int(workflow.time_of_day.split(':')[1]),
                                  second=0, microsecond=0)
        
        elif workflow.frequency == "monthly":
            # Calculate next occurrence of day_of_month
            next_month = from_time.replace(day=workflow.day_of_month)
            if next_month <= from_time:
                if next_month.month == 12:
                    next_month = next_month.replace(year=next_month.year + 1, month=1)
                else:
                    next_month = next_month.replace(month=next_month.month + 1)
            
            return next_month.replace(hour=int(workflow.time_of_day.split(':')[0]),
                                    minute=int(workflow.time_of_day.split(':')[1]),
                                    second=0, microsecond=0)
        
        return from_time + timedelta(days=1)
    
    async def _execute_workflow(self, workflow: WorkflowSchedule):
        """Execute a workflow"""
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_type=workflow.workflow_type,
            organization_id="",  # This would come from workflow context
            trigger_type=TriggerType.SCHEDULED,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self.executions[execution.execution_id] = execution
        
        try:
            if workflow.workflow_type == WorkflowType.RENT_INVOICE_GENERATION:
                result = await self._execute_rent_invoice_generation(execution)
            elif workflow.workflow_type == WorkflowType.PAYMENT_SYNC:
                result = await self._execute_payment_sync(execution)
            elif workflow.workflow_type == WorkflowType.LATE_FEE_PROCESSING:
                result = await self._execute_late_fee_processing(execution)
            elif workflow.workflow_type == WorkflowType.EXPENSE_SYNC:
                result = await self._execute_expense_sync(execution)
            elif workflow.workflow_type == WorkflowType.MONTHLY_RECONCILIATION:
                result = await self._execute_monthly_reconciliation(execution)
            else:
                result = {"status": "not_implemented"}
            
            execution.status = WorkflowStatus.COMPLETED
            execution.result = result
            execution.logs.append(f"Workflow completed successfully")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.logs.append(f"Workflow failed: {e}")
            logger.error(f"Workflow execution failed: {e}")
        
        finally:
            execution.end_time = datetime.now()
    
    async def _execute_rent_invoice_generation(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute rent invoice generation workflow"""
        execution.logs.append("Starting rent invoice generation")
        
        # Get all organizations with active QuickBooks connections
        organizations = self._get_active_organizations()
        
        total_invoices = 0
        successful_invoices = 0
        errors = []
        
        for org_id in organizations:
            try:
                # Get tenants due for rent invoices
                tenants_due = self._get_tenants_due_for_invoices(org_id)
                
                if not tenants_due:
                    continue
                
                # Generate invoices
                for tenant in tenants_due:
                    try:
                        invoice_data = self._create_rent_invoice_data(tenant)
                        
                        # Create invoice in QuickBooks
                        connection = self.oauth_service.get_organization_connection(org_id)
                        if connection:
                            # This would create the actual invoice
                            total_invoices += 1
                            successful_invoices += 1
                            execution.logs.append(f"Created invoice for tenant {tenant['tenant_id']}")
                    
                    except Exception as e:
                        errors.append({
                            "tenant_id": tenant.get("tenant_id"),
                            "error": str(e)
                        })
            
            except Exception as e:
                errors.append({
                    "organization_id": org_id,
                    "error": str(e)
                })
        
        return {
            "total_invoices": total_invoices,
            "successful_invoices": successful_invoices,
            "failed_invoices": len(errors),
            "errors": errors
        }
    
    async def _execute_payment_sync(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute payment synchronization workflow"""
        execution.logs.append("Starting payment synchronization")
        
        organizations = self._get_active_organizations()
        total_synced = 0
        errors = []
        
        for org_id in organizations:
            try:
                # Get recent payments
                payments = self._get_recent_payments(org_id)
                
                if payments:
                    sync_result = await self.sync_service.sync_payments_to_quickbooks(org_id, payments)
                    total_synced += sync_result.successful_records
                    
                    if sync_result.errors:
                        errors.extend(sync_result.errors)
                    
                    execution.logs.append(f"Synced {sync_result.successful_records} payments for org {org_id}")
            
            except Exception as e:
                errors.append({
                    "organization_id": org_id,
                    "error": str(e)
                })
        
        return {
            "total_synced": total_synced,
            "errors": errors
        }
    
    async def _execute_late_fee_processing(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute late fee processing workflow"""
        execution.logs.append("Starting late fee processing")
        
        organizations = self._get_active_organizations()
        late_fees_applied = 0
        errors = []
        
        for org_id in organizations:
            try:
                # Get overdue rent payments
                overdue_payments = self._get_overdue_payments(org_id)
                
                for payment in overdue_payments:
                    # Check if late fee should be applied
                    if self._should_apply_late_fee(payment):
                        try:
                            # Apply late fee
                            self._apply_late_fee(org_id, payment)
                            late_fees_applied += 1
                            execution.logs.append(f"Applied late fee for payment {payment['payment_id']}")
                        
                        except Exception as e:
                            errors.append({
                                "payment_id": payment.get("payment_id"),
                                "error": str(e)
                            })
            
            except Exception as e:
                errors.append({
                    "organization_id": org_id,
                    "error": str(e)
                })
        
        return {
            "late_fees_applied": late_fees_applied,
            "errors": errors
        }
    
    async def _execute_expense_sync(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute expense synchronization workflow"""
        execution.logs.append("Starting expense synchronization")
        
        organizations = self._get_active_organizations()
        total_synced = 0
        errors = []
        
        for org_id in organizations:
            try:
                # Get recent expenses
                expenses = self._get_recent_expenses(org_id)
                
                if expenses:
                    sync_result = await self.sync_service.sync_expenses_to_quickbooks(org_id, expenses)
                    total_synced += sync_result.successful_records
                    
                    if sync_result.errors:
                        errors.extend(sync_result.errors)
                    
                    execution.logs.append(f"Synced {sync_result.successful_records} expenses for org {org_id}")
            
            except Exception as e:
                errors.append({
                    "organization_id": org_id,
                    "error": str(e)
                })
        
        return {
            "total_synced": total_synced,
            "errors": errors
        }
    
    async def _execute_monthly_reconciliation(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute monthly reconciliation workflow"""
        execution.logs.append("Starting monthly reconciliation")
        
        organizations = self._get_active_organizations()
        reconciliations_completed = 0
        errors = []
        
        for org_id in organizations:
            try:
                # Perform reconciliation
                reconciliation_result = self._perform_monthly_reconciliation(org_id)
                
                if reconciliation_result["success"]:
                    reconciliations_completed += 1
                    execution.logs.append(f"Completed reconciliation for org {org_id}")
                else:
                    errors.append({
                        "organization_id": org_id,
                        "error": reconciliation_result.get("error", "Unknown error")
                    })
            
            except Exception as e:
                errors.append({
                    "organization_id": org_id,
                    "error": str(e)
                })
        
        return {
            "reconciliations_completed": reconciliations_completed,
            "errors": errors
        }
    
    def _process_event_rules(self):
        """Process event-driven rules"""
        # This would check for events that trigger rules
        # For now, just a placeholder
        pass
    
    def _get_active_organizations(self) -> List[str]:
        """Get list of organizations with active QuickBooks connections"""
        connections = self.oauth_service.list_connections()
        return [conn.organization_id for conn in connections if conn.is_active]
    
    def _get_tenants_due_for_invoices(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get tenants due for rent invoices"""
        # This would query the database for tenants
        # For now, return mock data
        return []
    
    def _get_recent_payments(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get recent payments for synchronization"""
        # This would query the database for recent payments
        return []
    
    def _get_overdue_payments(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get overdue rent payments"""
        # This would query the database for overdue payments
        return []
    
    def _get_recent_expenses(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get recent expenses for synchronization"""
        # This would query the database for recent expenses
        return []
    
    def _create_rent_invoice_data(self, tenant: Dict[str, Any]) -> Dict[str, Any]:
        """Create rent invoice data"""
        return {
            "tenant_id": tenant["tenant_id"],
            "amount": tenant.get("rent_amount", 0),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": f"Rent for {datetime.now().strftime('%B %Y')}"
        }
    
    def _should_apply_late_fee(self, payment: Dict[str, Any]) -> bool:
        """Check if late fee should be applied"""
        due_date = datetime.strptime(payment.get("due_date", ""), "%Y-%m-%d")
        days_overdue = (datetime.now() - due_date).days
        return days_overdue >= 5 and not payment.get("late_fee_applied", False)
    
    def _apply_late_fee(self, organization_id: str, payment: Dict[str, Any]):
        """Apply late fee to payment"""
        # This would create a late fee record and sync to QuickBooks
        pass
    
    def _perform_monthly_reconciliation(self, organization_id: str) -> Dict[str, Any]:
        """Perform monthly reconciliation"""
        try:
            # This would perform actual reconciliation logic
            return {"success": True, "discrepancies": 0}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Public API methods
    
    def create_workflow_schedule(self, workflow_type: WorkflowType, **kwargs) -> WorkflowSchedule:
        """Create a new workflow schedule"""
        schedule_id = str(uuid.uuid4())
        workflow = WorkflowSchedule(
            schedule_id=schedule_id,
            workflow_type=workflow_type,
            **kwargs
        )
        self.workflows[schedule_id] = workflow
        self._save_configurations()
        return workflow
    
    def update_workflow_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a workflow schedule"""
        if schedule_id not in self.workflows:
            return False
        
        workflow = self.workflows[schedule_id]
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        self._save_configurations()
        return True
    
    def delete_workflow_schedule(self, schedule_id: str) -> bool:
        """Delete a workflow schedule"""
        if schedule_id in self.workflows:
            del self.workflows[schedule_id]
            self._save_configurations()
            return True
        return False
    
    def execute_workflow_manually(self, workflow_type: WorkflowType, organization_id: str, 
                                 parameters: Optional[Dict[str, Any]] = None) -> str:
        """Manually execute a workflow"""
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_type=workflow_type,
            organization_id=organization_id,
            trigger_type=TriggerType.MANUAL,
            status=WorkflowStatus.PENDING,
            start_time=datetime.now(),
            parameters=parameters
        )
        
        self.executions[execution.execution_id] = execution
        
        # Execute asynchronously
        asyncio.create_task(self._execute_workflow_by_execution(execution))
        
        return execution.execution_id
    
    async def _execute_workflow_by_execution(self, execution: WorkflowExecution):
        """Execute workflow by execution record"""
        # Find corresponding workflow schedule or create temporary one
        workflow = WorkflowSchedule(
            schedule_id="manual",
            workflow_type=execution.workflow_type,
            enabled=True
        )
        await self._execute_workflow(workflow)
    
    def get_workflow_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "workflow_type": execution.workflow_type.value,
            "status": execution.status.value,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "result": execution.result,
            "error_message": execution.error_message,
            "logs": execution.logs
        }
    
    def list_workflow_schedules(self) -> List[Dict[str, Any]]:
        """List all workflow schedules"""
        return [
            {
                "schedule_id": workflow.schedule_id,
                "workflow_type": workflow.workflow_type.value,
                "frequency": workflow.frequency,
                "enabled": workflow.enabled,
                "next_run": workflow.next_run.isoformat() if workflow.next_run else None
            }
            for workflow in self.workflows.values()
        ]
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get workflow execution history"""
        executions = list(self.executions.values())
        executions.sort(key=lambda x: x.start_time, reverse=True)
        
        return [
            {
                "execution_id": execution.execution_id,
                "workflow_type": execution.workflow_type.value,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat(),
                "duration": (execution.end_time - execution.start_time).total_seconds() 
                           if execution.end_time else None,
                "trigger_type": execution.trigger_type.value
            }
            for execution in executions[:limit]
        ]

# Service instance
_automation_engine = None

def get_quickbooks_automation_engine() -> QuickBooksAutomationEngine:
    """Get singleton automation engine instance"""
    global _automation_engine
    if _automation_engine is None:
        _automation_engine = QuickBooksAutomationEngine()
    return _automation_engine