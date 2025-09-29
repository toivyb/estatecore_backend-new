import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import re
from abc import ABC, abstractmethod

from flask import current_app
from estatecore_backend.models import db, User, Property, Payment, MaintenanceRequest
from services.rbac_service import RBACService
from models.rbac import AccessLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TriggerType(Enum):
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    CONDITION_BASED = "condition_based"
    WEBHOOK = "webhook"
    MANUAL = "manual"

class ActionType(Enum):
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    CREATE_TASK = "create_task"
    UPDATE_RECORD = "update_record"
    CALL_API = "call_api"
    EXECUTE_SCRIPT = "execute_script"
    SEND_NOTIFICATION = "send_notification"
    GENERATE_REPORT = "generate_report"
    ESCALATE_ISSUE = "escalate_issue"
    APPROVE_REQUEST = "approve_request"

class WorkflowStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowTrigger:
    trigger_type: TriggerType
    config: Dict[str, Any]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if trigger conditions are met"""
        if self.trigger_type == TriggerType.TIME_BASED:
            return self._evaluate_time_trigger(context)
        elif self.trigger_type == TriggerType.EVENT_BASED:
            return self._evaluate_event_trigger(context)
        elif self.trigger_type == TriggerType.CONDITION_BASED:
            return self._evaluate_condition_trigger(context)
        return False
    
    def _evaluate_time_trigger(self, context: Dict[str, Any]) -> bool:
        """Evaluate time-based triggers"""
        schedule = self.config.get('schedule')
        if not schedule:
            return False
        
        now = datetime.utcnow()
        
        if schedule.get('type') == 'cron':
            # Simplified cron evaluation - in production use proper cron library
            return True
        elif schedule.get('type') == 'interval':
            last_run = context.get('last_run')
            if not last_run:
                return True
            interval_minutes = schedule.get('minutes', 60)
            return now - last_run > timedelta(minutes=interval_minutes)
        
        return False
    
    def _evaluate_event_trigger(self, context: Dict[str, Any]) -> bool:
        """Evaluate event-based triggers"""
        event_type = context.get('event_type')
        target_events = self.config.get('events', [])
        return event_type in target_events
    
    def _evaluate_condition_trigger(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition-based triggers"""
        for condition in self.conditions:
            if not self._evaluate_single_condition(condition, context):
                return False
        return True
    
    def _evaluate_single_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        context_value = context.get(field)
        
        if operator == 'equals':
            return context_value == value
        elif operator == 'not_equals':
            return context_value != value
        elif operator == 'greater_than':
            return context_value > value
        elif operator == 'less_than':
            return context_value < value
        elif operator == 'contains':
            return value in str(context_value)
        elif operator == 'regex':
            return bool(re.match(value, str(context_value)))
        
        return False

@dataclass
class WorkflowAction:
    action_type: ActionType
    config: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow action"""
        try:
            if self.action_type == ActionType.SEND_EMAIL:
                return await self._send_email(context)
            elif self.action_type == ActionType.SEND_SMS:
                return await self._send_sms(context)
            elif self.action_type == ActionType.CREATE_TASK:
                return await self._create_task(context)
            elif self.action_type == ActionType.UPDATE_RECORD:
                return await self._update_record(context)
            elif self.action_type == ActionType.CALL_API:
                return await self._call_api(context)
            elif self.action_type == ActionType.SEND_NOTIFICATION:
                return await self._send_notification(context)
            elif self.action_type == ActionType.GENERATE_REPORT:
                return await self._generate_report(context)
            elif self.action_type == ActionType.ESCALATE_ISSUE:
                return await self._escalate_issue(context)
            
            return {'success': False, 'error': 'Unknown action type'}
            
        except Exception as e:
            logger.error(f"Error executing action {self.action_type}: {str(e)}")
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                logger.info(f"Retrying action {self.action_type} (attempt {self.retry_count})")
                return await self.execute(context)
            
            return {'success': False, 'error': str(e), 'retries_exhausted': True}
    
    async def _send_email(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send email action"""
        to_email = self.config.get('to', context.get('email'))
        subject = self._render_template(self.config.get('subject', ''), context)
        body = self._render_template(self.config.get('body', ''), context)
        
        # In production, integrate with actual email service
        logger.info(f"Sending email to {to_email}: {subject}")
        
        return {'success': True, 'message': f'Email sent to {to_email}'}
    
    async def _send_sms(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS action"""
        phone = self.config.get('phone', context.get('phone'))
        message = self._render_template(self.config.get('message', ''), context)
        
        # In production, integrate with SMS service
        logger.info(f"Sending SMS to {phone}: {message}")
        
        return {'success': True, 'message': f'SMS sent to {phone}'}
    
    async def _create_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create task action"""
        task_data = {
            'title': self._render_template(self.config.get('title', ''), context),
            'description': self._render_template(self.config.get('description', ''), context),
            'assigned_to': self.config.get('assigned_to'),
            'due_date': self.config.get('due_date'),
            'priority': self.config.get('priority', 'medium')
        }
        
        # In production, create actual task in task management system
        logger.info(f"Creating task: {task_data['title']}")
        
        return {'success': True, 'task_id': str(uuid.uuid4()), 'task_data': task_data}
    
    async def _update_record(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update database record action"""
        table = self.config.get('table')
        record_id = context.get('record_id')
        updates = self.config.get('updates', {})
        
        # Render template values
        for key, value in updates.items():
            if isinstance(value, str):
                updates[key] = self._render_template(value, context)
        
        # In production, update actual database record
        logger.info(f"Updating {table} record {record_id} with {updates}")
        
        return {'success': True, 'updated_fields': updates}
    
    async def _call_api(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call external API action"""
        url = self._render_template(self.config.get('url', ''), context)
        method = self.config.get('method', 'POST')
        headers = self.config.get('headers', {})
        data = self.config.get('data', {})
        
        # Render template values in data
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self._render_template(value, context)
        
        # In production, make actual API call
        logger.info(f"Calling API {method} {url} with data: {data}")
        
        return {'success': True, 'api_response': 'Mock response'}
    
    async def _send_notification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send in-app notification action"""
        user_id = self.config.get('user_id', context.get('user_id'))
        title = self._render_template(self.config.get('title', ''), context)
        message = self._render_template(self.config.get('message', ''), context)
        notification_type = self.config.get('type', 'general')
        
        # In production, create actual notification
        logger.info(f"Sending notification to user {user_id}: {title}")
        
        return {'success': True, 'notification_sent': True}
    
    async def _generate_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report action"""
        report_type = self.config.get('report_type')
        filters = self.config.get('filters', {})
        format_type = self.config.get('format', 'pdf')
        
        # In production, generate actual report
        logger.info(f"Generating {report_type} report in {format_type} format")
        
        return {'success': True, 'report_id': str(uuid.uuid4()), 'format': format_type}
    
    async def _escalate_issue(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate issue action"""
        issue_id = context.get('issue_id')
        escalation_level = self.config.get('level', 'manager')
        reason = self._render_template(self.config.get('reason', ''), context)
        
        # In production, perform actual escalation
        logger.info(f"Escalating issue {issue_id} to {escalation_level}: {reason}")
        
        return {'success': True, 'escalated_to': escalation_level}
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables"""
        if not template:
            return template
        
        # Simple template rendering - in production use proper template engine
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))
        
        return template

@dataclass
class Workflow:
    id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    actions: List[WorkflowAction]
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Executing workflow {self.name} (ID: {execution_id})")
        
        try:
            # Check if trigger conditions are met
            if not self.trigger.evaluate(context):
                return {
                    'execution_id': execution_id,
                    'success': False,
                    'message': 'Trigger conditions not met',
                    'skipped': True
                }
            
            # Execute actions sequentially
            action_results = []
            for i, action in enumerate(self.actions):
                logger.info(f"Executing action {i+1}/{len(self.actions)}: {action.action_type}")
                
                result = await action.execute(context)
                action_results.append({
                    'action_type': action.action_type.value,
                    'result': result
                })
                
                # Stop execution if action failed and no error handling is configured
                if not result.get('success', False):
                    break
            
            # Update workflow statistics
            self.last_run = datetime.utcnow()
            self.run_count += 1
            
            all_successful = all(r['result'].get('success', False) for r in action_results)
            if all_successful:
                self.success_count += 1
            else:
                self.failure_count += 1
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'execution_id': execution_id,
                'success': all_successful,
                'action_results': action_results,
                'execution_time': execution_time,
                'context': context
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {self.name}: {str(e)}")
            self.failure_count += 1
            
            return {
                'execution_id': execution_id,
                'success': False,
                'error': str(e),
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

class AutomationEngine:
    """Advanced automation and workflow engine"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_templates = self._load_workflow_templates()
        self.execution_history = []
        self.is_running = False
    
    def _load_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined workflow templates"""
        return {
            'rent_reminder': {
                'name': 'Rent Payment Reminder',
                'description': 'Send automated rent payment reminders',
                'trigger': {
                    'type': 'time_based',
                    'schedule': {'type': 'cron', 'expression': '0 9 * * *'}  # Daily at 9 AM
                },
                'actions': [
                    {
                        'type': 'send_email',
                        'config': {
                            'to': '{tenant_email}',
                            'subject': 'Rent Payment Reminder - Unit {unit_number}',
                            'body': 'Dear {tenant_name}, your rent payment of ${rent_amount} is due on {due_date}.'
                        }
                    }
                ]
            },
            'maintenance_escalation': {
                'name': 'Maintenance Request Escalation',
                'description': 'Escalate overdue maintenance requests',
                'trigger': {
                    'type': 'condition_based',
                    'conditions': [
                        {'field': 'days_overdue', 'operator': 'greater_than', 'value': 2},
                        {'field': 'priority', 'operator': 'equals', 'value': 'urgent'}
                    ]
                },
                'actions': [
                    {
                        'type': 'send_notification',
                        'config': {
                            'user_id': '{manager_id}',
                            'title': 'Urgent Maintenance Request Overdue',
                            'message': 'Maintenance request #{request_id} is {days_overdue} days overdue'
                        }
                    },
                    {
                        'type': 'escalate_issue',
                        'config': {
                            'level': 'senior_manager',
                            'reason': 'Urgent maintenance request overdue for {days_overdue} days'
                        }
                    }
                ]
            },
            'lease_renewal': {
                'name': 'Lease Renewal Process',
                'description': 'Automate lease renewal notifications and processes',
                'trigger': {
                    'type': 'time_based',
                    'schedule': {'type': 'interval', 'minutes': 1440}  # Daily
                },
                'actions': [
                    {
                        'type': 'send_email',
                        'config': {
                            'to': '{tenant_email}',
                            'subject': 'Lease Renewal Notice - Unit {unit_number}',
                            'body': 'Your lease expires on {lease_end_date}. Please contact us to discuss renewal options.'
                        }
                    },
                    {
                        'type': 'create_task',
                        'config': {
                            'title': 'Process lease renewal for {tenant_name}',
                            'description': 'Lease expires on {lease_end_date}',
                            'assigned_to': '{property_manager_id}',
                            'priority': 'high'
                        }
                    }
                ]
            },
            'payment_processing': {
                'name': 'Payment Processing Workflow',
                'description': 'Process and confirm payments automatically',
                'trigger': {
                    'type': 'event_based',
                    'events': ['payment_received']
                },
                'actions': [
                    {
                        'type': 'update_record',
                        'config': {
                            'table': 'payments',
                            'updates': {
                                'status': 'processed',
                                'processed_at': '{current_timestamp}'
                            }
                        }
                    },
                    {
                        'type': 'send_email',
                        'config': {
                            'to': '{tenant_email}',
                            'subject': 'Payment Confirmation',
                            'body': 'Your payment of ${amount} has been received and processed.'
                        }
                    }
                ]
            },
            'security_alert': {
                'name': 'Security Alert Response',
                'description': 'Respond to security alerts automatically',
                'trigger': {
                    'type': 'event_based',
                    'events': ['security_alert_critical', 'security_alert_high']
                },
                'actions': [
                    {
                        'type': 'send_notification',
                        'config': {
                            'user_id': '{security_manager_id}',
                            'title': 'Critical Security Alert',
                            'message': 'Security alert: {alert_description}'
                        }
                    },
                    {
                        'type': 'send_sms',
                        'config': {
                            'phone': '{security_manager_phone}',
                            'message': 'SECURITY ALERT: {alert_description} - IP: {source_ip}'
                        }
                    }
                ]
            }
        }
    
    def create_workflow_from_template(self, template_name: str, config: Dict[str, Any] = None) -> str:
        """Create workflow from predefined template"""
        if template_name not in self.workflow_templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self.workflow_templates[template_name]
        config = config or {}
        
        # Create workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Create trigger
        trigger_config = template['trigger']
        trigger = WorkflowTrigger(
            trigger_type=TriggerType(trigger_config['type']),
            config=trigger_config,
            conditions=trigger_config.get('conditions', [])
        )
        
        # Create actions
        actions = []
        for action_config in template['actions']:
            # Merge with custom config if provided
            merged_config = {**action_config['config']}
            if template_name in config and 'actions' in config[template_name]:
                action_overrides = config[template_name]['actions'].get(action_config['type'], {})
                merged_config.update(action_overrides)
            
            action = WorkflowAction(
                action_type=ActionType(action_config['type']),
                config=merged_config
            )
            actions.append(action)
        
        # Create workflow
        workflow = Workflow(
            id=workflow_id,
            name=template['name'],
            description=template['description'],
            trigger=trigger,
            actions=actions
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow from template {template_name}: {workflow_id}")
        
        return workflow_id
    
    def create_custom_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """Create custom workflow from configuration"""
        workflow_id = str(uuid.uuid4())
        
        # Parse trigger
        trigger_data = workflow_data['trigger']
        trigger = WorkflowTrigger(
            trigger_type=TriggerType(trigger_data['type']),
            config=trigger_data.get('config', {}),
            conditions=trigger_data.get('conditions', [])
        )
        
        # Parse actions
        actions = []
        for action_data in workflow_data['actions']:
            action = WorkflowAction(
                action_type=ActionType(action_data['type']),
                config=action_data.get('config', {})
            )
            actions.append(action)
        
        # Create workflow
        workflow = Workflow(
            id=workflow_id,
            name=workflow_data['name'],
            description=workflow_data.get('description', ''),
            trigger=trigger,
            actions=actions
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created custom workflow: {workflow_id}")
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.ACTIVE:
            return {
                'success': False,
                'message': f'Workflow is {workflow.status.value}'
            }
        
        result = await workflow.execute(context)
        self.execution_history.append({
            'workflow_id': workflow_id,
            'workflow_name': workflow.name,
            'execution_time': datetime.utcnow(),
            'result': result
        })
        
        return result
    
    async def trigger_event(self, event_type: str, context: Dict[str, Any]):
        """Trigger workflows based on events"""
        triggered_workflows = []
        
        for workflow_id, workflow in self.workflows.items():
            if (workflow.status == WorkflowStatus.ACTIVE and 
                workflow.trigger.trigger_type == TriggerType.EVENT_BASED):
                
                # Add event type to context
                event_context = {**context, 'event_type': event_type}
                
                if workflow.trigger.evaluate(event_context):
                    logger.info(f"Event {event_type} triggered workflow {workflow.name}")
                    result = await self.execute_workflow(workflow_id, event_context)
                    triggered_workflows.append({
                        'workflow_id': workflow_id,
                        'workflow_name': workflow.name,
                        'result': result
                    })
        
        return triggered_workflows
    
    async def run_scheduled_workflows(self):
        """Run time-based workflows"""
        current_time = datetime.utcnow()
        
        for workflow_id, workflow in self.workflows.items():
            if (workflow.status == WorkflowStatus.ACTIVE and 
                workflow.trigger.trigger_type == TriggerType.TIME_BASED):
                
                context = {
                    'current_time': current_time,
                    'last_run': workflow.last_run
                }
                
                if workflow.trigger.evaluate(context):
                    logger.info(f"Schedule triggered workflow {workflow.name}")
                    await self.execute_workflow(workflow_id, context)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status and statistics"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        return {
            'id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'status': workflow.status.value,
            'created_at': workflow.created_at.isoformat(),
            'last_run': workflow.last_run.isoformat() if workflow.last_run else None,
            'run_count': workflow.run_count,
            'success_count': workflow.success_count,
            'failure_count': workflow.failure_count,
            'success_rate': workflow.success_count / workflow.run_count if workflow.run_count > 0 else 0
        }
    
    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows with their status"""
        return [self.get_workflow_status(wf_id) for wf_id in self.workflows.keys()]
    
    def pause_workflow(self, workflow_id: str):
        """Pause a workflow"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = WorkflowStatus.PAUSED
            logger.info(f"Paused workflow {workflow_id}")
    
    def resume_workflow(self, workflow_id: str):
        """Resume a paused workflow"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = WorkflowStatus.ACTIVE
            logger.info(f"Resumed workflow {workflow_id}")
    
    def delete_workflow(self, workflow_id: str):
        """Delete a workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info(f"Deleted workflow {workflow_id}")
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get workflow execution history"""
        return sorted(
            self.execution_history[-limit:],
            key=lambda x: x['execution_time'],
            reverse=True
        )
    
    async def start_engine(self):
        """Start the automation engine"""
        self.is_running = True
        logger.info("Automation engine started")
        
        # Create default workflows from templates
        for template_name in ['rent_reminder', 'maintenance_escalation', 'lease_renewal']:
            try:
                self.create_workflow_from_template(template_name)
            except Exception as e:
                logger.error(f"Error creating workflow from template {template_name}: {str(e)}")
        
        # Start background scheduler
        asyncio.create_task(self._scheduler_loop())
    
    async def stop_engine(self):
        """Stop the automation engine"""
        self.is_running = False
        logger.info("Automation engine stopped")
    
    async def _scheduler_loop(self):
        """Background scheduler loop"""
        while self.is_running:
            try:
                await self.run_scheduled_workflows()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(60)

# Global automation engine instance
automation_engine = AutomationEngine()