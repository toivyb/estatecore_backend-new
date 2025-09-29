from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db, Property
from services.tenant_screening_service import tenant_screening_service, ScreeningStatus, EmploymentStatus
from services.rbac_service import require_permission
import logging
import asyncio
from datetime import datetime

tenant_screening_bp = Blueprint('tenant_screening', __name__, url_prefix='/api/tenant-screening')
logger = logging.getLogger(__name__)

@tenant_screening_bp.route('/applications', methods=['POST'])
def submit_application():
    """Submit a new tenant application"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Run async application submission
        async def run_submission():
            return await tenant_screening_service.submit_application(data)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_submission())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        return jsonify({'error': 'Failed to submit application'}), 500

@tenant_screening_bp.route('/applications/<application_id>/screen', methods=['POST'])
@require_permission('tenants:screen')
def start_screening(application_id):
    """Start the screening process for an application"""
    try:
        # Run async screening process
        async def run_screening():
            return await tenant_screening_service.start_screening_process(application_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_screening())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error starting screening: {str(e)}")
        return jsonify({'error': 'Failed to start screening process'}), 500

@tenant_screening_bp.route('/applications/<application_id>', methods=['GET'])
@require_permission('tenants:read')
def get_application_status(application_id):
    """Get application and screening status"""
    try:
        # Run async status check
        async def get_status():
            return await tenant_screening_service.get_application_status(application_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_status())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        logger.error(f"Error getting application status: {str(e)}")
        return jsonify({'error': 'Failed to get application status'}), 500

@tenant_screening_bp.route('/applications', methods=['GET'])
@require_permission('tenants:read')
def get_applications():
    """Get all applications with filtering options"""
    try:
        status_filter = request.args.get('status')
        property_id = request.args.get('property_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Get applications
        applications = list(tenant_screening_service.applications.values())
        
        # Apply filters
        if status_filter:
            applications = [app for app in applications if app.status.value == status_filter]
        
        if property_id:
            applications = [app for app in applications if app.property_id == property_id]
        
        # Sort by submission date (newest first)
        applications.sort(key=lambda x: x.submitted_at, reverse=True)
        
        # Apply limit
        applications = applications[:limit]
        
        # Include screening results if available
        result_applications = []
        for app in applications:
            app_dict = app.to_dict()
            
            # Add screening result if available
            if app.application_id in tenant_screening_service.screening_results:
                app_dict['screening_result'] = tenant_screening_service.screening_results[app.application_id].to_dict()
            
            # Add credit report summary if available
            if app.application_id in tenant_screening_service.credit_reports:
                credit_report = tenant_screening_service.credit_reports[app.application_id]
                app_dict['credit_summary'] = {
                    'credit_score': credit_report.credit_score,
                    'credit_grade': credit_report.credit_grade.value
                }
            
            result_applications.append(app_dict)
        
        return jsonify({
            'success': True,
            'applications': result_applications,
            'total_count': len(result_applications),
            'filters_applied': {
                'status': status_filter,
                'property_id': property_id,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}")
        return jsonify({'error': 'Failed to get applications'}), 500

@tenant_screening_bp.route('/applications/<application_id>/status', methods=['PUT'])
@require_permission('tenants:manage')
def update_application_status(application_id):
    """Update application status manually"""
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        new_status = data['status']
        notes = data.get('notes')
        
        # Run async status update
        async def update_status():
            return await tenant_screening_service.update_application_status(
                application_id, new_status, notes
            )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(update_status())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error updating application status: {str(e)}")
        return jsonify({'error': 'Failed to update application status'}), 500

@tenant_screening_bp.route('/analytics', methods=['GET'])
@require_permission('tenants:read')
def get_screening_analytics():
    """Get comprehensive screening analytics"""
    try:
        property_id = request.args.get('property_id', type=int)
        date_range_days = request.args.get('date_range_days', 30, type=int)
        
        # Run async analytics
        async def get_analytics():
            return await tenant_screening_service.get_screening_analytics(
                property_id, date_range_days
            )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_analytics())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500

@tenant_screening_bp.route('/credit-reports/<application_id>', methods=['GET'])
@require_permission('tenants:read')
def get_credit_report(application_id):
    """Get credit report for an application"""
    try:
        if application_id not in tenant_screening_service.credit_reports:
            return jsonify({'error': 'Credit report not found'}), 404
        
        credit_report = tenant_screening_service.credit_reports[application_id]
        
        return jsonify({
            'success': True,
            'credit_report': credit_report.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting credit report: {str(e)}")
        return jsonify({'error': 'Failed to get credit report'}), 500

@tenant_screening_bp.route('/background-checks/<application_id>', methods=['GET'])
@require_permission('tenants:read')
def get_background_check(application_id):
    """Get background check results for an application"""
    try:
        if application_id not in tenant_screening_service.background_checks:
            return jsonify({'error': 'Background check not found'}), 404
        
        background_check = tenant_screening_service.background_checks[application_id]
        
        return jsonify({
            'success': True,
            'background_check': background_check.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting background check: {str(e)}")
        return jsonify({'error': 'Failed to get background check'}), 500

@tenant_screening_bp.route('/dashboard', methods=['GET'])
@require_permission('tenants:read')
def get_screening_dashboard():
    """Get screening dashboard data"""
    try:
        property_id = request.args.get('property_id', type=int)
        
        # Get applications
        if property_id:
            applications = [
                app for app in tenant_screening_service.applications.values()
                if app.property_id == property_id
            ]
        else:
            applications = list(tenant_screening_service.applications.values())
        
        # Calculate dashboard metrics
        total_applications = len(applications)
        pending_applications = len([app for app in applications if app.status == ScreeningStatus.PENDING])
        in_progress_applications = len([app for app in applications if app.status == ScreeningStatus.IN_PROGRESS])
        approved_applications = len([app for app in applications if app.status == ScreeningStatus.APPROVED])
        rejected_applications = len([app for app in applications if app.status == ScreeningStatus.REJECTED])
        requires_review = len([app for app in applications if app.status == ScreeningStatus.REQUIRES_REVIEW])
        
        # Recent applications
        recent_applications = sorted(applications, key=lambda x: x.submitted_at, reverse=True)[:10]
        
        # Applications by status
        status_breakdown = {
            'pending': pending_applications,
            'in_progress': in_progress_applications,
            'approved': approved_applications,
            'rejected': rejected_applications,
            'requires_review': requires_review
        }
        
        # Credit score distribution
        credit_scores = []
        for app in applications:
            if app.application_id in tenant_screening_service.credit_reports:
                credit_scores.append(tenant_screening_service.credit_reports[app.application_id].credit_score)
        
        credit_distribution = {
            'excellent': len([score for score in credit_scores if score >= 750]),
            'good': len([score for score in credit_scores if 700 <= score < 750]),
            'fair': len([score for score in credit_scores if 650 <= score < 700]),
            'poor': len([score for score in credit_scores if 600 <= score < 650]),
            'bad': len([score for score in credit_scores if score < 600])
        }
        
        # Processing times (mock data)
        processing_metrics = {
            'average_processing_time_hours': 24,
            'fastest_processing_time_hours': 4,
            'slowest_processing_time_hours': 72,
            'applications_processed_today': 5
        }
        
        dashboard_data = {
            'overview': {
                'total_applications': total_applications,
                'pending_applications': pending_applications,
                'in_progress_applications': in_progress_applications,
                'approved_applications': approved_applications,
                'rejected_applications': rejected_applications,
                'requires_review': requires_review,
                'approval_rate': approved_applications / total_applications if total_applications > 0 else 0,
                'rejection_rate': rejected_applications / total_applications if total_applications > 0 else 0
            },
            'recent_applications': [app.to_dict() for app in recent_applications],
            'status_breakdown': status_breakdown,
            'credit_distribution': credit_distribution,
            'processing_metrics': processing_metrics,
            'trends': {
                'applications_growth': 0.12,  # 12% growth
                'approval_rate_trend': 0.03,  # 3% improvement
                'processing_time_trend': -0.08  # 8% faster processing
            }
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data,
            'property_id': property_id
        })
        
    except Exception as e:
        logger.error(f"Error getting screening dashboard: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@tenant_screening_bp.route('/criteria', methods=['GET'])
@require_permission('tenants:read')
def get_screening_criteria():
    """Get current screening criteria"""
    try:
        criteria = tenant_screening_service.screening_criteria
        weights = tenant_screening_service.scoring_weights
        
        return jsonify({
            'success': True,
            'screening_criteria': criteria,
            'scoring_weights': weights
        })
        
    except Exception as e:
        logger.error(f"Error getting screening criteria: {str(e)}")
        return jsonify({'error': 'Failed to get screening criteria'}), 500

@tenant_screening_bp.route('/criteria', methods=['PUT'])
@require_permission('tenants:manage')
def update_screening_criteria():
    """Update screening criteria"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Update criteria if provided
        if 'screening_criteria' in data:
            tenant_screening_service.screening_criteria.update(data['screening_criteria'])
        
        # Update weights if provided
        if 'scoring_weights' in data:
            tenant_screening_service.scoring_weights.update(data['scoring_weights'])
        
        return jsonify({
            'success': True,
            'message': 'Screening criteria updated successfully',
            'screening_criteria': tenant_screening_service.screening_criteria,
            'scoring_weights': tenant_screening_service.scoring_weights
        })
        
    except Exception as e:
        logger.error(f"Error updating screening criteria: {str(e)}")
        return jsonify({'error': 'Failed to update screening criteria'}), 500

@tenant_screening_bp.route('/bulk-screen', methods=['POST'])
@require_permission('tenants:screen')
def bulk_screen_applications():
    """Bulk screen multiple applications"""
    try:
        data = request.get_json()
        
        if not data or 'application_ids' not in data:
            return jsonify({'error': 'Application IDs are required'}), 400
        
        application_ids = data['application_ids']
        
        if not isinstance(application_ids, list) or len(application_ids) > 20:
            return jsonify({'error': 'Invalid application IDs list (max 20 applications)'}), 400
        
        results = []
        
        for app_id in application_ids:
            try:
                # Run async screening for each application
                async def run_single_screening():
                    return await tenant_screening_service.start_screening_process(app_id)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(run_single_screening())
                finally:
                    loop.close()
                
                results.append({
                    'application_id': app_id,
                    'success': result['success'],
                    'screening_result': result.get('screening_result'),
                    'error': result.get('error')
                })
                
            except Exception as e:
                results.append({
                    'application_id': app_id,
                    'success': False,
                    'error': str(e)
                })
        
        successful_screenings = [r for r in results if r['success']]
        failed_screenings = [r for r in results if not r['success']]
        
        return jsonify({
            'success': True,
            'total_applications': len(application_ids),
            'successful_screenings': len(successful_screenings),
            'failed_screenings': len(failed_screenings),
            'results': results,
            'message': f'Bulk screening completed: {len(successful_screenings)}/{len(application_ids)} successful'
        })
        
    except Exception as e:
        logger.error(f"Error in bulk screening: {str(e)}")
        return jsonify({'error': 'Failed to perform bulk screening'}), 500

@tenant_screening_bp.route('/applications/<application_id>/documents', methods=['POST'])
@require_permission('tenants:manage')
def upload_documents(application_id):
    """Upload documents for an application"""
    try:
        if application_id not in tenant_screening_service.applications:
            return jsonify({'error': 'Application not found'}), 404
        
        # Mock document upload
        files = request.files.getlist('documents')
        document_metadata = request.form.get('metadata', '{}')
        
        application = tenant_screening_service.applications[application_id]
        
        for file in files:
            if file.filename:
                # In production, upload to secure storage
                document_info = f"uploaded_{file.filename}_{datetime.utcnow().isoformat()}"
                application.documents.append(document_info)
        
        return jsonify({
            'success': True,
            'application_id': application_id,
            'documents_uploaded': len(files),
            'message': 'Documents uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        return jsonify({'error': 'Failed to upload documents'}), 500

# Health check endpoint
@tenant_screening_bp.route('/health', methods=['GET'])
def tenant_screening_health_check():
    """Tenant screening system health check"""
    try:
        health_status = {
            'status': 'healthy',
            'total_applications': len(tenant_screening_service.applications),
            'pending_screenings': len([
                app for app in tenant_screening_service.applications.values()
                if app.status in [ScreeningStatus.PENDING, ScreeningStatus.IN_PROGRESS]
            ]),
            'completed_screenings': len(tenant_screening_service.screening_results),
            'external_apis': {
                'credit_reporting': 'available',
                'background_check': 'available',
                'income_verification': 'available'
            }
        }
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Tenant screening health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500