"""
Compliance API Routes
RESTful API endpoints for the Automated Compliance Monitoring system
"""

from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
from functools import wraps
import io
import base64

from models.base import db
from models.compliance import (
    ComplianceViolation, ComplianceRequirement, ComplianceAlert,
    RegulatoryKnowledgeBase, ComplianceMetrics, ComplianceDocument,
    ComplianceTraining, ViolationSeverity, ComplianceStatus, RegulationType,
    AlertChannel
)
from services.regulatory_knowledge_service import get_regulatory_knowledge_service
from services.compliance_integration_service import get_compliance_integration_service
from services.violation_detection_service import get_violation_detection_service
from services.compliance_alert_service import get_compliance_alert_service, AlertType
from services.compliance_reporting_service import (
    get_compliance_reporting_service, ReportType, ReportFormat, ReportConfig
)
from ai_modules.compliance.ai_compliance_monitor import get_ai_compliance_monitor
from permissions_service import require_permission, require_role, Permission, Role


logger = logging.getLogger(__name__)

# Create Blueprint
compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/compliance')


def async_route(f):
    """Decorator to handle async routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return decorated_function


# Error handlers
@compliance_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@compliance_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@compliance_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# =================== REGULATORY KNOWLEDGE BASE ROUTES ===================

@compliance_bp.route('/regulations', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_regulations():
    """Get all regulations or search with filters"""
    try:
        regulatory_service = get_regulatory_knowledge_service()
        
        # Parse query parameters
        query = request.args.get('query')
        regulation_types = request.args.getlist('types')
        jurisdictions = request.args.getlist('jurisdictions')
        
        # Convert string types to enums
        if regulation_types:
            regulation_types = [RegulationType(t) for t in regulation_types if t in [rt.value for rt in RegulationType]]
        
        # Search regulations
        regulations = regulatory_service.search_regulations(
            query=query,
            regulation_types=regulation_types,
            jurisdictions=jurisdictions
        )
        
        # Format response
        result = []
        for reg in regulations:
            result.append({
                'id': reg.id,
                'regulation_code': reg.regulation_code,
                'title': reg.title,
                'description': reg.description,
                'regulation_type': reg.regulation_type.value,
                'jurisdiction': reg.jurisdiction,
                'effective_date': reg.effective_date.isoformat() if reg.effective_date else None,
                'last_updated': reg.last_updated.isoformat() if reg.last_updated else None,
                'version': reg.version,
                'summary': reg.summary,
                'key_requirements': reg.key_requirements,
                'compliance_checklist': reg.compliance_checklist
            })
        
        return jsonify({
            'success': True,
            'regulations': result,
            'total_count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting regulations: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/regulations/<regulation_id>', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_regulation(regulation_id):
    """Get detailed information about a specific regulation"""
    try:
        regulation = db.session.query(RegulatoryKnowledgeBase).get(regulation_id)
        if not regulation:
            return jsonify({'error': 'Regulation not found'}), 404
        
        return jsonify({
            'success': True,
            'regulation': {
                'id': regulation.id,
                'regulation_code': regulation.regulation_code,
                'title': regulation.title,
                'description': regulation.description,
                'regulation_type': regulation.regulation_type.value,
                'jurisdiction': regulation.jurisdiction,
                'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
                'last_updated': regulation.last_updated.isoformat() if regulation.last_updated else None,
                'version': regulation.version,
                'full_text': regulation.full_text,
                'summary': regulation.summary,
                'key_requirements': regulation.key_requirements,
                'compliance_checklist': regulation.compliance_checklist,
                'penalties': regulation.penalties,
                'exemptions': regulation.exemptions,
                'ai_interpretation': regulation.ai_interpretation,
                'risk_factors': regulation.risk_factors,
                'change_log': regulation.change_log
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting regulation: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/regulations', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
def create_regulation():
    """Create a new regulation"""
    try:
        data = request.get_json()
        regulatory_service = get_regulatory_knowledge_service()
        
        # Validate required fields
        required_fields = ['regulation_code', 'title', 'regulation_type', 'jurisdiction']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Add regulation
        regulation_id = regulatory_service.add_regulation(data)
        
        if regulation_id:
            return jsonify({
                'success': True,
                'regulation_id': regulation_id,
                'message': 'Regulation created successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create regulation'}), 500
            
    except Exception as e:
        logger.error(f"Error creating regulation: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/regulations/<regulation_id>', methods=['PUT'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
def update_regulation(regulation_id):
    """Update an existing regulation"""
    try:
        data = request.get_json()
        regulatory_service = get_regulatory_knowledge_service()
        
        success = regulatory_service.update_regulation(regulation_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Regulation updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update regulation'}), 500
            
    except Exception as e:
        logger.error(f"Error updating regulation: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/regulations/statistics', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_regulation_statistics():
    """Get statistics about the regulatory knowledge base"""
    try:
        regulatory_service = get_regulatory_knowledge_service()
        stats = regulatory_service.get_regulation_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting regulation statistics: {e}")
        return jsonify({'error': str(e)}), 500


# =================== PROPERTY COMPLIANCE ROUTES ===================

@compliance_bp.route('/properties/<property_id>/requirements', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_property_requirements(property_id):
    """Get compliance requirements for a property"""
    try:
        requirements = db.session.query(ComplianceRequirement).filter_by(
            property_id=property_id
        ).all()
        
        result = []
        for req in requirements:
            result.append({
                'id': req.id,
                'requirement_name': req.requirement_name,
                'description': req.description,
                'compliance_status': req.compliance_status.value,
                'risk_score': req.risk_score,
                'due_date': req.due_date.isoformat() if req.due_date else None,
                'next_review_date': req.next_review_date.isoformat() if req.next_review_date else None,
                'last_verified_date': req.last_verified_date.isoformat() if req.last_verified_date else None,
                'regulation': {
                    'id': req.regulation.id,
                    'title': req.regulation.title,
                    'regulation_type': req.regulation.regulation_type.value
                } if req.regulation else None
            })
        
        return jsonify({
            'success': True,
            'requirements': result,
            'total_count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting property requirements: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/properties/<property_id>/requirements', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
def create_property_requirements(property_id):
    """Create compliance requirements for a property"""
    try:
        data = request.get_json()
        regulatory_service = get_regulatory_knowledge_service()
        
        # Get property data (this would come from your property model)
        property_data = data.get('property_data', {})
        property_data['property_id'] = property_id
        
        success = regulatory_service.create_property_compliance_requirements(
            property_id, property_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Compliance requirements created successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create compliance requirements'}), 500
            
    except Exception as e:
        logger.error(f"Error creating property requirements: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/properties/<property_id>/analysis', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
@async_route
async def get_property_analysis(property_id):
    """Get AI-powered compliance analysis for a property"""
    try:
        ai_monitor = get_ai_compliance_monitor()
        
        # Get comprehensive analysis
        risk_assessment = ai_monitor.analyze_property_compliance(property_id)
        
        # Get communication patterns
        communication_analysis = ai_monitor.analyze_communication_patterns(property_id)
        
        return jsonify({
            'success': True,
            'analysis': {
                'property_id': property_id,
                'risk_assessment': {
                    'regulation_type': risk_assessment.regulation_type.value,
                    'risk_score': risk_assessment.risk_score,
                    'risk_factors': risk_assessment.risk_factors,
                    'confidence': risk_assessment.confidence,
                    'recommendations': risk_assessment.recommendations,
                    'predicted_violation_date': risk_assessment.predicted_violation_date.isoformat() if risk_assessment.predicted_violation_date else None
                },
                'communication_analysis': communication_analysis,
                'analyzed_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting property analysis: {e}")
        return jsonify({'error': str(e)}), 500


# =================== VIOLATION ROUTES ===================

@compliance_bp.route('/violations', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_violations():
    """Get violations with filtering and pagination"""
    try:
        # Parse query parameters
        property_id = request.args.get('property_id')
        severity = request.args.get('severity')
        resolved = request.args.get('resolved')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Build query
        query = db.session.query(ComplianceViolation)
        
        if property_id:
            query = query.filter(ComplianceViolation.property_id == property_id)
        
        if severity:
            query = query.filter(ComplianceViolation.severity == ViolationSeverity(severity))
        
        if resolved is not None:
            is_resolved = resolved.lower() == 'true'
            query = query.filter(ComplianceViolation.is_resolved == is_resolved)
        
        # Apply pagination
        violations = query.order_by(
            ComplianceViolation.detected_date.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        total_count = query.count()
        
        # Format response
        result = []
        for violation in violations:
            result.append({
                'id': violation.id,
                'property_id': violation.property_id,
                'violation_type': violation.violation_type,
                'title': violation.title,
                'description': violation.description,
                'severity': violation.severity.value,
                'detected_date': violation.detected_date.isoformat(),
                'detection_method': violation.detection_method,
                'detection_confidence': violation.detection_confidence,
                'is_resolved': violation.is_resolved,
                'resolved_date': violation.resolved_date.isoformat() if violation.resolved_date else None,
                'resolution_notes': violation.resolution_notes,
                'financial_impact': violation.financial_impact,
                'legal_risk': violation.legal_risk,
                'ai_recommendations': violation.ai_recommendations
            })
        
        return jsonify({
            'success': True,
            'violations': result,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting violations: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/violations/<violation_id>', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_violation(violation_id):
    """Get detailed information about a specific violation"""
    try:
        violation = db.session.query(ComplianceViolation).get(violation_id)
        if not violation:
            return jsonify({'error': 'Violation not found'}), 404
        
        return jsonify({
            'success': True,
            'violation': {
                'id': violation.id,
                'property_id': violation.property_id,
                'regulation_id': violation.regulation_id,
                'requirement_id': violation.requirement_id,
                'violation_type': violation.violation_type,
                'title': violation.title,
                'description': violation.description,
                'severity': violation.severity.value,
                'detected_date': violation.detected_date.isoformat(),
                'detection_method': violation.detection_method,
                'detection_confidence': violation.detection_confidence,
                'data_sources': violation.data_sources,
                'is_resolved': violation.is_resolved,
                'resolved_date': violation.resolved_date.isoformat() if violation.resolved_date else None,
                'resolution_notes': violation.resolution_notes,
                'resolution_cost': violation.resolution_cost,
                'financial_impact': violation.financial_impact,
                'legal_risk': violation.legal_risk,
                'reputation_risk': violation.reputation_risk,
                'escalation_level': violation.escalation_level,
                'assigned_to': violation.assigned_to,
                'ai_recommendations': violation.ai_recommendations,
                'similar_violations': violation.similar_violations,
                'pattern_indicators': violation.pattern_indicators,
                'created_at': violation.created_at.isoformat(),
                'updated_at': violation.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting violation: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/violations/<violation_id>/resolve', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
def resolve_violation(violation_id):
    """Mark a violation as resolved"""
    try:
        data = request.get_json()
        
        violation = db.session.query(ComplianceViolation).get(violation_id)
        if not violation:
            return jsonify({'error': 'Violation not found'}), 404
        
        # Update violation
        violation.is_resolved = True
        violation.resolved_date = datetime.now()
        violation.resolution_notes = data.get('resolution_notes', '')
        violation.resolution_cost = data.get('resolution_cost')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Violation marked as resolved'
        })
        
    except Exception as e:
        logger.error(f"Error resolving violation: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/violations/detect', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
@async_route
async def run_violation_detection():
    """Run comprehensive violation detection"""
    try:
        data = request.get_json()
        property_ids = data.get('property_ids')  # Optional list of properties
        
        violation_service = get_violation_detection_service()
        
        # Run detection
        results = await violation_service.run_comprehensive_violation_detection(property_ids)
        
        return jsonify({
            'success': True,
            'results': results,
            'message': 'Violation detection completed'
        })
        
    except Exception as e:
        logger.error(f"Error running violation detection: {e}")
        return jsonify({'error': str(e)}), 500


# =================== ALERT ROUTES ===================

@compliance_bp.route('/alerts', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
@async_route
async def get_alerts():
    """Get compliance alerts with filtering"""
    try:
        # Parse query parameters
        property_id = request.args.get('property_id')
        alert_types = request.args.getlist('types')
        priorities = request.args.getlist('priorities')
        unacknowledged_only = request.args.get('unacknowledged_only', 'false').lower() == 'true'
        
        # Convert string types to enums
        alert_type_enums = []
        if alert_types:
            for at in alert_types:
                try:
                    alert_type_enums.append(AlertType(at))
                except ValueError:
                    pass
        
        priority_enums = []
        if priorities:
            for p in priorities:
                try:
                    priority_enums.append(ViolationSeverity(p))
                except ValueError:
                    pass
        
        alert_service = get_compliance_alert_service()
        alerts = await alert_service.get_active_alerts(
            property_id=property_id,
            alert_types=alert_type_enums,
            priorities=priority_enums,
            unacknowledged_only=unacknowledged_only
        )
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total_count': len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/alerts', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
@async_route
async def create_alert():
    """Create a new compliance alert"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['alert_type', 'title', 'message', 'priority']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        alert_service = get_compliance_alert_service()
        
        # Convert string enums
        alert_type = AlertType(data['alert_type'])
        priority = ViolationSeverity(data['priority'])
        
        channels = []
        if data.get('channels'):
            channels = [AlertChannel(c) for c in data['channels']]
        
        alert_id = await alert_service.create_alert(
            alert_type=alert_type,
            title=data['title'],
            message=data['message'],
            priority=priority,
            property_id=data.get('property_id'),
            violation_id=data.get('violation_id'),
            requirement_id=data.get('requirement_id'),
            recipient_roles=data.get('recipient_roles', []),
            recipient_users=data.get('recipient_users', []),
            channels=channels,
            template_data=data.get('template_data', {})
        )
        
        if alert_id:
            return jsonify({
                'success': True,
                'alert_id': alert_id,
                'message': 'Alert created successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create alert'}), 500
            
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
@async_route
async def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'current_user')  # In production, get from auth
        notes = data.get('notes', '')
        
        alert_service = get_compliance_alert_service()
        success = await alert_service.acknowledge_alert(alert_id, user_id, notes)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alert acknowledged'
            })
        else:
            return jsonify({'error': 'Failed to acknowledge alert'}), 500
            
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/alerts/statistics', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
@async_route
async def get_alert_statistics():
    """Get alert statistics"""
    try:
        days_back = int(request.args.get('days_back', 30))
        
        alert_service = get_compliance_alert_service()
        stats = await alert_service.get_alert_statistics(days_back)
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'period_days': days_back
        })
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        return jsonify({'error': str(e)}), 500


# =================== REPORTING ROUTES ===================

@compliance_bp.route('/reports/generate', methods=['POST'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
@async_route
async def generate_report():
    """Generate a compliance report"""
    try:
        data = request.get_json()
        
        # Parse report configuration
        report_type = ReportType(data['report_type'])
        report_format = ReportFormat(data.get('format', 'pdf'))
        
        # Parse date range
        date_range = None
        if data.get('date_range'):
            date_range = {
                'start': datetime.fromisoformat(data['date_range']['start']),
                'end': datetime.fromisoformat(data['date_range']['end'])
            }
        
        # Create report config
        config = ReportConfig(
            report_type=report_type,
            title=data.get('title', f'{report_type.value.title()} Report'),
            description=data.get('description', ''),
            property_ids=data.get('property_ids'),
            date_range=date_range,
            include_charts=data.get('include_charts', True),
            include_recommendations=data.get('include_recommendations', True),
            format=report_format
        )
        
        reporting_service = get_compliance_reporting_service()
        report_result = await reporting_service.generate_custom_report(config)
        
        return jsonify({
            'success': report_result['success'],
            'report_data': report_result.get('report_data'),
            'metadata': report_result.get('metadata'),
            'generated_at': report_result.get('generated_at', datetime.now()).isoformat() if report_result.get('generated_at') else None,
            'error': report_result.get('error')
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/reports/types', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_report_types():
    """Get available report types"""
    try:
        reporting_service = get_compliance_reporting_service()
        report_types = reporting_service.get_available_report_types()
        
        return jsonify({
            'success': True,
            'report_types': report_types
        })
        
    except Exception as e:
        logger.error(f"Error getting report types: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/reports/download/<report_id>', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def download_report(report_id):
    """Download a generated report"""
    try:
        # In a real implementation, you'd store and retrieve report files
        # For now, return a placeholder response
        return jsonify({
            'success': False,
            'message': 'Report download not implemented yet'
        }), 501
        
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return jsonify({'error': str(e)}), 500


# =================== INTEGRATION ROUTES ===================

@compliance_bp.route('/integrations/status', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
@async_route
async def get_integration_status():
    """Get status of all integrations"""
    try:
        integration_service = get_compliance_integration_service()
        status = await integration_service.get_integration_status()
        
        return jsonify({
            'success': True,
            'integrations': status
        })
        
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/integrations/<integration_id>/test', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
@async_route
async def test_integration(integration_id):
    """Test a specific integration"""
    try:
        integration_service = get_compliance_integration_service()
        result = await integration_service.test_integration(integration_id)
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'data_points': result.get('data_points', 0),
            'error': result.get('error')
        })
        
    except Exception as e:
        logger.error(f"Error testing integration: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/integrations/sync', methods=['POST'])
@cross_origin()
@require_permission(Permission.MANAGE_COMPLIANCE)
@async_route
async def sync_integrations():
    """Manually trigger integration sync"""
    try:
        integration_service = get_compliance_integration_service()
        results = await integration_service.sync_all_integrations()
        
        return jsonify({
            'success': True,
            'results': results,
            'total_synced': sum(results.values()),
            'message': 'Integration sync completed'
        })
        
    except Exception as e:
        logger.error(f"Error syncing integrations: {e}")
        return jsonify({'error': str(e)}), 500


# =================== DASHBOARD ROUTES ===================

@compliance_bp.route('/dashboard/overview', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_dashboard_overview():
    """Get compliance dashboard overview"""
    try:
        # Get recent violations
        recent_violations = db.session.query(ComplianceViolation).filter(
            ComplianceViolation.detected_date >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Get compliance metrics
        latest_metrics = db.session.query(ComplianceMetrics).order_by(
            ComplianceMetrics.metric_date.desc()
        ).first()
        
        # Get overdue requirements
        overdue_requirements = db.session.query(ComplianceRequirement).filter(
            ComplianceRequirement.next_review_date < datetime.now(),
            ComplianceRequirement.compliance_status != ComplianceStatus.COMPLIANT
        ).count()
        
        # Get unacknowledged alerts
        unacknowledged_alerts = db.session.query(ComplianceAlert).filter_by(
            acknowledged=False
        ).count()
        
        overview = {
            'recent_violations': recent_violations,
            'overall_compliance_score': latest_metrics.overall_compliance_score if latest_metrics else 0,
            'risk_score': latest_metrics.risk_score if latest_metrics else 0,
            'overdue_requirements': overdue_requirements,
            'unacknowledged_alerts': unacknowledged_alerts,
            'last_updated': latest_metrics.metric_date.isoformat() if latest_metrics else None
        }
        
        return jsonify({
            'success': True,
            'overview': overview
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/dashboard/metrics', methods=['GET'])
@cross_origin()
@require_permission(Permission.VIEW_COMPLIANCE)
def get_dashboard_metrics():
    """Get detailed compliance metrics"""
    try:
        days_back = int(request.args.get('days_back', 90))
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get metrics over time
        metrics = db.session.query(ComplianceMetrics).filter(
            ComplianceMetrics.metric_date >= cutoff_date
        ).order_by(ComplianceMetrics.metric_date.desc()).all()
        
        result = []
        for metric in metrics:
            result.append({
                'date': metric.metric_date.isoformat(),
                'overall_score': metric.overall_compliance_score,
                'risk_score': metric.risk_score,
                'total_violations': metric.total_violations,
                'critical_violations': metric.critical_violations,
                'resolved_violations': metric.resolved_violations,
                'fair_housing_score': metric.fair_housing_score,
                'safety_score': metric.safety_compliance_score,
                'building_code_score': metric.building_code_score,
                'environmental_score': metric.environmental_score
            })
        
        return jsonify({
            'success': True,
            'metrics': result,
            'period_days': days_back
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return jsonify({'error': str(e)}), 500


# =================== HEALTH CHECK ROUTE ===================

@compliance_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint for the compliance system"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Check service status
        service_status = {
            'database': 'healthy',
            'regulatory_service': 'healthy',
            'ai_monitor': 'healthy',
            'integration_service': 'healthy',
            'alert_service': 'healthy',
            'reporting_service': 'healthy'
        }
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'services': service_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# Register the blueprint in your main app.py
# from routes.compliance_api import compliance_bp
# app.register_blueprint(compliance_bp)