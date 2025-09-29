from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db
from services.automation_engine import automation_engine, TriggerType, ActionType, WorkflowStatus
from services.rbac_service import require_permission
import logging
import asyncio

automation_bp = Blueprint('automation', __name__, url_prefix='/api/automation')
logger = logging.getLogger(__name__)

@automation_bp.route('/workflows', methods=['GET'])
@require_permission('automation:read')
def get_workflows():
    """Get all workflows"""
    try:
        workflows = automation_engine.get_all_workflows()
        
        return jsonify({
            'success': True,
            'workflows': workflows,
            'total': len(workflows)
        })
        
    except Exception as e:
        logger.error(f"Error fetching workflows: {str(e)}")
        return jsonify({'error': 'Failed to fetch workflows'}), 500

@automation_bp.route('/workflows', methods=['POST'])
@require_permission('automation:create')
def create_workflow():
    """Create a new workflow"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'trigger', 'actions']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create workflow from template or custom config
        if data.get('template'):
            template_name = data['template']
            config = data.get('config', {})
            workflow_id = automation_engine.create_workflow_from_template(template_name, config)
        else:
            workflow_id = automation_engine.create_custom_workflow(data)
        
        # Get the created workflow
        workflow = automation_engine.get_workflow_status(workflow_id)
        
        return jsonify({
            'success': True,
            'workflow_id': workflow_id,
            'workflow': workflow,
            'message': 'Workflow created successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        return jsonify({'error': 'Failed to create workflow'}), 500

@automation_bp.route('/workflows/<workflow_id>', methods=['GET'])
@require_permission('automation:read')
def get_workflow(workflow_id):
    """Get specific workflow details"""
    try:
        workflow = automation_engine.get_workflow_status(workflow_id)
        
        return jsonify({
            'success': True,
            'workflow': workflow
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error fetching workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch workflow'}), 500

@automation_bp.route('/workflows/<workflow_id>', methods=['PUT'])
@require_permission('automation:update')
def update_workflow(workflow_id):
    """Update workflow configuration"""
    try:
        data = request.get_json()
        
        if workflow_id not in automation_engine.workflows:
            return jsonify({'error': 'Workflow not found'}), 404
        
        workflow = automation_engine.workflows[workflow_id]
        
        # Update basic properties
        if 'name' in data:
            workflow.name = data['name']
        if 'description' in data:
            workflow.description = data['description']
        
        # Update trigger configuration
        if 'trigger' in data:
            trigger_data = data['trigger']
            workflow.trigger.config.update(trigger_data.get('config', {}))
            if 'conditions' in trigger_data:
                workflow.trigger.conditions = trigger_data['conditions']
        
        # Update actions configuration
        if 'actions' in data:
            for i, action_data in enumerate(data['actions']):
                if i < len(workflow.actions):
                    workflow.actions[i].config.update(action_data.get('config', {}))
        
        updated_workflow = automation_engine.get_workflow_status(workflow_id)
        
        return jsonify({
            'success': True,
            'workflow': updated_workflow,
            'message': 'Workflow updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Failed to update workflow'}), 500

@automation_bp.route('/workflows/<workflow_id>', methods=['DELETE'])
@require_permission('automation:delete')
def delete_workflow(workflow_id):
    """Delete a workflow"""
    try:
        if workflow_id not in automation_engine.workflows:
            return jsonify({'error': 'Workflow not found'}), 404
        
        automation_engine.delete_workflow(workflow_id)
        
        return jsonify({
            'success': True,
            'message': 'Workflow deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete workflow'}), 500

@automation_bp.route('/workflows/<workflow_id>/pause', methods=['POST'])
@require_permission('automation:update')
def pause_workflow(workflow_id):
    """Pause a workflow"""
    try:
        if workflow_id not in automation_engine.workflows:
            return jsonify({'error': 'Workflow not found'}), 404
        
        automation_engine.pause_workflow(workflow_id)
        
        return jsonify({
            'success': True,
            'message': 'Workflow paused successfully'
        })
        
    except Exception as e:
        logger.error(f"Error pausing workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Failed to pause workflow'}), 500

@automation_bp.route('/workflows/<workflow_id>/resume', methods=['POST'])
@require_permission('automation:update')
def resume_workflow(workflow_id):
    """Resume a paused workflow"""
    try:
        if workflow_id not in automation_engine.workflows:
            return jsonify({'error': 'Workflow not found'}), 404
        
        automation_engine.resume_workflow(workflow_id)
        
        return jsonify({
            'success': True,
            'message': 'Workflow resumed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error resuming workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Failed to resume workflow'}), 500

@automation_bp.route('/workflows/<workflow_id>/execute', methods=['POST'])
@require_permission('automation:execute')
def execute_workflow(workflow_id):
    """Manually execute a workflow"""
    try:
        data = request.get_json() or {}
        context = data.get('context', {})
        
        # Add user context
        context['triggered_by'] = g.current_user.id
        context['manual_execution'] = True
        
        # Execute workflow asynchronously
        async def run_workflow():
            return await automation_engine.execute_workflow(workflow_id, context)
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_workflow())
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'execution_result': result,
            'message': 'Workflow executed successfully'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Failed to execute workflow'}), 500

@automation_bp.route('/executions', methods=['GET'])
@require_permission('automation:read')
def get_execution_history():
    """Get workflow execution history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        workflow_id = request.args.get('workflow_id')
        
        executions = automation_engine.get_execution_history(limit)
        
        # Filter by workflow_id if specified
        if workflow_id:
            executions = [e for e in executions if e['workflow_id'] == workflow_id]
        
        return jsonify({
            'success': True,
            'executions': executions,
            'total': len(executions)
        })
        
    except Exception as e:
        logger.error(f"Error fetching execution history: {str(e)}")
        return jsonify({'error': 'Failed to fetch execution history'}), 500

@automation_bp.route('/trigger-event', methods=['POST'])
@require_permission('automation:execute')
def trigger_event():
    """Trigger workflows based on an event"""
    try:
        data = request.get_json()
        
        if not data or 'event_type' not in data:
            return jsonify({'error': 'event_type is required'}), 400
        
        event_type = data['event_type']
        context = data.get('context', {})
        
        # Add user context
        context['triggered_by'] = g.current_user.id
        context['event_source'] = 'api'
        
        # Trigger workflows asynchronously
        async def trigger_workflows():
            return await automation_engine.trigger_event(event_type, context)
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            triggered_workflows = loop.run_until_complete(trigger_workflows())
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'event_type': event_type,
            'triggered_workflows': triggered_workflows,
            'count': len(triggered_workflows)
        })
        
    except Exception as e:
        logger.error(f"Error triggering event: {str(e)}")
        return jsonify({'error': 'Failed to trigger event'}), 500

@automation_bp.route('/templates', methods=['GET'])
@require_permission('automation:read')
def get_workflow_templates():
    """Get available workflow templates"""
    try:
        templates = []
        for name, template in automation_engine.workflow_templates.items():
            templates.append({
                'name': name,
                'display_name': template['name'],
                'description': template['description'],
                'trigger_type': template['trigger']['type'],
                'actions_count': len(template['actions'])
            })
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        return jsonify({'error': 'Failed to fetch templates'}), 500

@automation_bp.route('/templates/<template_name>', methods=['GET'])
@require_permission('automation:read')
def get_workflow_template(template_name):
    """Get specific workflow template details"""
    try:
        if template_name not in automation_engine.workflow_templates:
            return jsonify({'error': 'Template not found'}), 404
        
        template = automation_engine.workflow_templates[template_name]
        
        return jsonify({
            'success': True,
            'template': template
        })
        
    except Exception as e:
        logger.error(f"Error fetching template {template_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch template'}), 500

@automation_bp.route('/dashboard', methods=['GET'])
@require_permission('automation:read')
def get_automation_dashboard():
    """Get automation dashboard data"""
    try:
        workflows = automation_engine.get_all_workflows()
        executions = automation_engine.get_execution_history(50)
        
        # Calculate statistics
        total_workflows = len(workflows)
        active_workflows = len([w for w in workflows if w['status'] == 'active'])
        total_executions = sum(w['run_count'] for w in workflows)
        total_successes = sum(w['success_count'] for w in workflows)
        
        # Recent executions (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_executions = [
            e for e in executions 
            if datetime.fromisoformat(e['execution_time'].replace('Z', '+00:00')) > yesterday
        ]
        
        # Success rate by workflow
        workflow_performance = []
        for workflow in workflows:
            if workflow['run_count'] > 0:
                workflow_performance.append({
                    'name': workflow['name'],
                    'success_rate': workflow['success_rate'],
                    'run_count': workflow['run_count']
                })
        
        dashboard_data = {
            'statistics': {
                'total_workflows': total_workflows,
                'active_workflows': active_workflows,
                'paused_workflows': len([w for w in workflows if w['status'] == 'paused']),
                'total_executions': total_executions,
                'success_rate': total_successes / total_executions if total_executions > 0 else 0,
                'executions_24h': len(recent_executions)
            },
            'recent_executions': recent_executions[:10],
            'workflow_performance': sorted(workflow_performance, key=lambda x: x['success_rate'], reverse=True)[:10],
            'workflow_status_breakdown': {
                'active': active_workflows,
                'paused': len([w for w in workflows if w['status'] == 'paused']),
                'inactive': len([w for w in workflows if w['status'] == 'inactive'])
            }
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching automation dashboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

@automation_bp.route('/engine/start', methods=['POST'])
@require_permission('automation:manage')
def start_automation_engine():
    """Start the automation engine"""
    try:
        # Start engine asynchronously
        async def start_engine():
            await automation_engine.start_engine()
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_engine())
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'message': 'Automation engine started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting automation engine: {str(e)}")
        return jsonify({'error': 'Failed to start automation engine'}), 500

@automation_bp.route('/engine/stop', methods=['POST'])
@require_permission('automation:manage')
def stop_automation_engine():
    """Stop the automation engine"""
    try:
        # Stop engine asynchronously
        async def stop_engine():
            await automation_engine.stop_engine()
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(stop_engine())
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'message': 'Automation engine stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping automation engine: {str(e)}")
        return jsonify({'error': 'Failed to stop automation engine'}), 500

@automation_bp.route('/engine/status', methods=['GET'])
@require_permission('automation:read')
def get_engine_status():
    """Get automation engine status"""
    try:
        status = {
            'is_running': automation_engine.is_running,
            'total_workflows': len(automation_engine.workflows),
            'active_workflows': len([w for w in automation_engine.workflows.values() if w.status == WorkflowStatus.ACTIVE]),
            'total_executions': len(automation_engine.execution_history)
        }
        
        return jsonify({
            'success': True,
            'engine_status': status
        })
        
    except Exception as e:
        logger.error(f"Error fetching engine status: {str(e)}")
        return jsonify({'error': 'Failed to fetch engine status'}), 500

@automation_bp.route('/validate-workflow', methods=['POST'])
@require_permission('automation:create')
def validate_workflow():
    """Validate workflow configuration before creation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        validation_errors = []
        
        # Validate basic structure
        required_fields = ['name', 'trigger', 'actions']
        for field in required_fields:
            if field not in data:
                validation_errors.append(f'Missing required field: {field}')
        
        # Validate trigger
        if 'trigger' in data:
            trigger = data['trigger']
            if 'type' not in trigger:
                validation_errors.append('Trigger type is required')
            elif trigger['type'] not in [t.value for t in TriggerType]:
                validation_errors.append(f'Invalid trigger type: {trigger["type"]}')
        
        # Validate actions
        if 'actions' in data:
            actions = data['actions']
            if not isinstance(actions, list) or len(actions) == 0:
                validation_errors.append('At least one action is required')
            else:
                for i, action in enumerate(actions):
                    if 'type' not in action:
                        validation_errors.append(f'Action {i+1} is missing type')
                    elif action['type'] not in [a.value for a in ActionType]:
                        validation_errors.append(f'Action {i+1} has invalid type: {action["type"]}')
        
        is_valid = len(validation_errors) == 0
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'validation_errors': validation_errors
        })
        
    except Exception as e:
        logger.error(f"Error validating workflow: {str(e)}")
        return jsonify({'error': 'Failed to validate workflow'}), 500

# Health check endpoint
@automation_bp.route('/health', methods=['GET'])
def automation_health_check():
    """Automation system health check"""
    try:
        health_status = {
            'status': 'healthy' if automation_engine.is_running else 'stopped',
            'engine_running': automation_engine.is_running,
            'total_workflows': len(automation_engine.workflows),
            'active_workflows': len([w for w in automation_engine.workflows.values() if w.status == WorkflowStatus.ACTIVE]),
            'recent_executions': len([e for e in automation_engine.execution_history[-10:]])
        }
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Automation health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500