"""
Tenant Screening API Routes
RESTful API endpoints for predictive tenant screening system
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, Any

from models.base import db
from models.tenant_screening import TenantApplication, ScreeningResult, ApplicationStatus
from services.tenant_screening_service import get_tenant_screening_service, ScreeningRequest
from utils.validation import validate_json, ValidationError
from utils.permissions import require_permission


logger = logging.getLogger(__name__)

# Create Blueprint
tenant_screening_bp = Blueprint('tenant_screening', __name__, url_prefix='/api/tenant-screening')


# Validation schemas
APPLICATION_SCHEMA = {
    'type': 'object',
    'required': ['property_id', 'applicant_name', 'email', 'annual_income'],
    'properties': {
        'property_id': {'type': 'string', 'minLength': 1},
        'unit_id': {'type': 'string'},
        'applicant_name': {'type': 'string', 'minLength': 1},
        'email': {'type': 'string', 'format': 'email'},
        'phone_number': {'type': 'string'},
        'annual_income': {'type': 'number', 'minimum': 0},
        'monthly_income': {'type': 'number', 'minimum': 0},
        'employment_type': {'type': 'string', 'enum': ['full_time', 'part_time', 'contract', 'self_employed', 'unemployed']},
        'employment_length_months': {'type': 'integer', 'minimum': 0},
        'credit_score': {'type': 'integer', 'minimum': 300, 'maximum': 850},
        'desired_move_in_date': {'type': 'string', 'format': 'date'},
        'monthly_rent_budget': {'type': 'number', 'minimum': 0}
    }
}

SCREENING_REQUEST_SCHEMA = {
    'type': 'object',
    'required': ['application_id'],
    'properties': {
        'application_id': {'type': 'string', 'minLength': 1},
        'priority': {'type': 'string', 'enum': ['normal', 'high', 'urgent']},
        'screening_type': {'type': 'string', 'enum': ['basic', 'comprehensive', 'express']},
        'bypass_cache': {'type': 'boolean'}
    }
}


@tenant_screening_bp.route('/applications', methods=['POST'])
@jwt_required()
@require_permission('tenant_screening:create')
def create_application():
    """Create a new tenant application"""
    try:
        data = validate_json(request.get_json(), APPLICATION_SCHEMA)
        user_id = get_jwt_identity()
        
        # Create application
        application = TenantApplication(
            property_id=data['property_id'],
            unit_id=data.get('unit_id'),
            applicant_name=data['applicant_name'],
            email=data['email'],
            phone_number=data.get('phone_number'),
            annual_income=data['annual_income'],
            monthly_income=data.get('monthly_income'),
            employment_type=data.get('employment_type'),
            employment_length_months=data.get('employment_length_months'),
            credit_score=data.get('credit_score'),
            monthly_rent_budget=data.get('monthly_rent_budget'),
            desired_move_in_date=datetime.fromisoformat(data['desired_move_in_date']) if data.get('desired_move_in_date') else None,
            processed_by=user_id,
            status=ApplicationStatus.SUBMITTED.value
        )
        
        db.session.add(application)
        db.session.commit()
        
        logger.info(f"Application created: {application.id}")
        
        return jsonify({
            'success': True,
            'application_id': str(application.id),
            'status': application.status,
            'created_at': application.created_at.isoformat()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        return jsonify({'error': 'Failed to create application'}), 500


@tenant_screening_bp.route('/applications/<application_id>', methods=['GET'])
@jwt_required()
@require_permission('tenant_screening:read')
def get_application(application_id):
    """Get tenant application details"""
    try:
        application = db.session.query(TenantApplication).filter_by(id=application_id).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Get latest screening result
        latest_screening = db.session.query(ScreeningResult).filter_by(
            application_id=application.id
        ).order_by(ScreeningResult.screening_date.desc()).first()
        
        response_data = {
            'application_id': str(application.id),
            'property_id': application.property_id,
            'unit_id': application.unit_id,
            'applicant_name': application.applicant_name,
            'email': application.email,
            'phone_number': application.phone_number,
            'annual_income': application.annual_income,
            'employment_type': application.employment_type,
            'employment_length_months': application.employment_length_months,
            'credit_score': application.credit_score,
            'status': application.status,
            'application_date': application.application_date.isoformat(),
            'desired_move_in_date': application.desired_move_in_date.isoformat() if application.desired_move_in_date else None,
            'monthly_rent_budget': application.monthly_rent_budget
        }
        
        if latest_screening:
            response_data['latest_screening'] = {
                'screening_id': str(latest_screening.id),
                'overall_score': latest_screening.overall_score,
                'risk_level': latest_screening.risk_level,
                'recommendation': latest_screening.approval_recommendation,
                'confidence_score': latest_screening.confidence_score,
                'screening_date': latest_screening.screening_date.isoformat(),
                'final_decision': latest_screening.final_decision
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error getting application: {e}")
        return jsonify({'error': 'Failed to retrieve application'}), 500


@tenant_screening_bp.route('/applications/<application_id>', methods=['PUT'])
@jwt_required()
@require_permission('tenant_screening:update')
def update_application(application_id):
    """Update tenant application"""
    try:
        application = db.session.query(TenantApplication).filter_by(id=application_id).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        data = request.get_json() or {}
        user_id = get_jwt_identity()
        
        # Update allowed fields
        updatable_fields = [
            'phone_number', 'annual_income', 'monthly_income', 'employment_type',
            'employment_length_months', 'credit_score', 'monthly_rent_budget'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(application, field, data[field])
        
        application.updated_at = datetime.utcnow()
        application.processed_by = user_id
        
        db.session.commit()
        
        logger.info(f"Application updated: {application_id}")
        
        return jsonify({
            'success': True,
            'application_id': str(application.id),
            'updated_at': application.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating application: {e}")
        return jsonify({'error': 'Failed to update application'}), 500


@tenant_screening_bp.route('/screen', methods=['POST'])
@jwt_required()
@require_permission('tenant_screening:screen')
def screen_applicant():
    """Run predictive screening on a tenant application"""
    try:
        data = validate_json(request.get_json(), SCREENING_REQUEST_SCHEMA)
        user_id = get_jwt_identity()
        
        # Create screening request
        screening_request = ScreeningRequest(
            application_id=data['application_id'],
            priority=data.get('priority', 'normal'),
            screening_type=data.get('screening_type', 'comprehensive'),
            bypass_cache=data.get('bypass_cache', False)
        )
        
        # Run screening
        screening_service = get_tenant_screening_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            screening_response = loop.run_until_complete(
                screening_service.process_screening_request(screening_request)
            )
        finally:
            loop.close()
        
        if not screening_response.success:
            return jsonify({
                'success': False,
                'error': screening_response.error
            }), 400
        
        # Format response
        response_data = {
            'success': True,
            'application_id': screening_response.application_id,
            'screening_id': screening_response.screening_id,
            'processing_time': screening_response.processing_time,
            'score': {
                'overall_score': screening_response.score.overall_score,
                'credit_score': screening_response.score.credit_score,
                'income_score': screening_response.score.income_score,
                'rental_history_score': screening_response.score.rental_history_score,
                'employment_score': screening_response.score.employment_score,
                'reference_score': screening_response.score.reference_score,
                'fraud_risk_score': screening_response.score.fraud_risk_score,
                'risk_level': screening_response.score.risk_level.value,
                'recommendation': screening_response.score.recommendation.value,
                'confidence': screening_response.score.confidence
            },
            'insights': {
                'strengths': screening_response.insights.strengths,
                'concerns': screening_response.insights.concerns,
                'recommendations': screening_response.insights.recommendations,
                'probability_of_success': screening_response.insights.probability_of_success
            },
            'recommendations': screening_response.recommendations,
            'next_steps': screening_response.next_steps
        }
        
        logger.info(f"Screening completed for application {screening_request.application_id}")
        
        return jsonify(response_data), 200
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error screening applicant: {e}")
        return jsonify({'error': 'Failed to screen applicant'}), 500


@tenant_screening_bp.route('/applications/<application_id>/screenings', methods=['GET'])
@jwt_required()
@require_permission('tenant_screening:read')
def get_screening_history(application_id):
    """Get screening history for an application"""
    try:
        application = db.session.query(TenantApplication).filter_by(id=application_id).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Get all screening results
        screening_results = db.session.query(ScreeningResult).filter_by(
            application_id=application.id
        ).order_by(ScreeningResult.screening_date.desc()).all()
        
        screenings = []
        for result in screening_results:
            screening_data = {
                'screening_id': str(result.id),
                'screening_date': result.screening_date.isoformat(),
                'overall_score': result.overall_score,
                'risk_level': result.risk_level,
                'recommendation': result.approval_recommendation,
                'confidence_score': result.confidence_score,
                'screening_method': result.screening_method,
                'final_decision': result.final_decision,
                'decision_date': result.decision_date.isoformat() if result.decision_date else None,
                'strengths': result.strengths,
                'concerns': result.concerns,
                'recommendations': result.recommendations
            }
            screenings.append(screening_data)
        
        return jsonify({
            'application_id': str(application.id),
            'screenings': screenings,
            'total_screenings': len(screenings)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting screening history: {e}")
        return jsonify({'error': 'Failed to retrieve screening history'}), 500


@tenant_screening_bp.route('/screenings/<screening_id>/decision', methods=['POST'])
@jwt_required()
@require_permission('tenant_screening:decide')
def make_screening_decision(screening_id):
    """Make final decision on a screening result"""
    try:
        screening_result = db.session.query(ScreeningResult).filter_by(id=screening_id).first()
        
        if not screening_result:
            return jsonify({'error': 'Screening result not found'}), 404
        
        data = request.get_json() or {}
        user_id = get_jwt_identity()
        
        # Validate decision
        valid_decisions = ['approve', 'conditional_approve', 'decline', 'require_cosigner']
        decision = data.get('decision')
        
        if not decision or decision not in valid_decisions:
            return jsonify({'error': 'Invalid decision. Must be one of: ' + ', '.join(valid_decisions)}), 400
        
        # Update screening result
        screening_result.final_decision = decision
        screening_result.decision_date = datetime.utcnow()
        screening_result.decision_maker = user_id
        screening_result.decision_notes = data.get('notes', '')
        
        # Update approval conditions if applicable
        if decision == 'conditional_approve':
            screening_result.approval_conditions = data.get('conditions', [])
            screening_result.required_documents = data.get('required_documents', [])
            screening_result.security_deposit_multiplier = data.get('security_deposit_multiplier', 1.0)
        
        if decision == 'require_cosigner':
            screening_result.cosigner_required = True
        
        # Update application status
        application = screening_result.application
        if decision == 'approve':
            application.status = ApplicationStatus.APPROVED.value
        elif decision == 'conditional_approve':
            application.status = ApplicationStatus.CONDITIONALLY_APPROVED.value
        elif decision == 'decline':
            application.status = ApplicationStatus.DECLINED.value
        elif decision == 'require_cosigner':
            application.status = ApplicationStatus.UNDER_REVIEW.value  # Keep under review pending cosigner
        
        db.session.commit()
        
        logger.info(f"Decision made on screening {screening_id}: {decision}")
        
        return jsonify({
            'success': True,
            'screening_id': str(screening_result.id),
            'decision': decision,
            'decision_date': screening_result.decision_date.isoformat(),
            'application_status': application.status
        }), 200
        
    except Exception as e:
        logger.error(f"Error making screening decision: {e}")
        return jsonify({'error': 'Failed to make decision'}), 500


@tenant_screening_bp.route('/analytics', methods=['GET'])
@jwt_required()
@require_permission('tenant_screening:analytics')
def get_screening_analytics():
    """Get screening system analytics"""
    try:
        # Parse date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = {'start_date': start_date, 'end_date': end_date}
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
        
        # Get analytics
        screening_service = get_tenant_screening_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analytics = loop.run_until_complete(
                screening_service.get_screening_analytics(date_range)
            )
        finally:
            loop.close()
        
        if 'error' in analytics:
            return jsonify(analytics), 400
        
        return jsonify(analytics), 200
        
    except Exception as e:
        logger.error(f"Error getting screening analytics: {e}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500


@tenant_screening_bp.route('/applications', methods=['GET'])
@jwt_required()
@require_permission('tenant_screening:read')
def list_applications():
    """List tenant applications with filtering and pagination"""
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
        status = request.args.get('status')
        property_id = request.args.get('property_id')
        
        # Build query
        query = db.session.query(TenantApplication)
        
        if status:
            query = query.filter(TenantApplication.status == status)
        
        if property_id:
            query = query.filter(TenantApplication.property_id == property_id)
        
        # Order by application date (newest first)
        query = query.order_by(TenantApplication.application_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        applications = pagination.items
        
        # Format response
        applications_data = []
        for app in applications:
            # Get latest screening
            latest_screening = db.session.query(ScreeningResult).filter_by(
                application_id=app.id
            ).order_by(ScreeningResult.screening_date.desc()).first()
            
            app_data = {
                'application_id': str(app.id),
                'property_id': app.property_id,
                'applicant_name': app.applicant_name,
                'email': app.email,
                'annual_income': app.annual_income,
                'status': app.status,
                'application_date': app.application_date.isoformat(),
                'monthly_rent_budget': app.monthly_rent_budget
            }
            
            if latest_screening:
                app_data['latest_screening'] = {
                    'overall_score': latest_screening.overall_score,
                    'risk_level': latest_screening.risk_level,
                    'recommendation': latest_screening.approval_recommendation,
                    'screening_date': latest_screening.screening_date.isoformat()
                }
            
            applications_data.append(app_data)
        
        return jsonify({
            'applications': applications_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        return jsonify({'error': 'Failed to list applications'}), 500


@tenant_screening_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for screening system"""
    try:
        # Basic health checks
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'healthy',
                'screening_engine': 'healthy',
                'api': 'healthy'
            }
        }
        
        # Test database connection
        try:
            db.session.execute('SELECT 1')
            health_status['services']['database'] = 'healthy'
        except Exception:
            health_status['services']['database'] = 'unhealthy'
            health_status['status'] = 'degraded'
        
        # Test screening engine
        try:
            screening_service = get_tenant_screening_service()
            if screening_service:
                health_status['services']['screening_engine'] = 'healthy'
            else:
                health_status['services']['screening_engine'] = 'unhealthy'
                health_status['status'] = 'degraded'
        except Exception:
            health_status['services']['screening_engine'] = 'unhealthy'
            health_status['status'] = 'degraded'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


# Error handlers
@tenant_screening_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({'error': str(error)}), 400


@tenant_screening_bp.errorhandler(404)
def handle_not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@tenant_screening_bp.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500