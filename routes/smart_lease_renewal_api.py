"""
Smart Lease Renewal API Endpoints
Comprehensive REST API for the AI-powered lease renewal system
"""

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import asyncio
import json
from functools import wraps

# Import the smart lease renewal modules
from ai_modules.smart_lease_renewal.prediction_engine import SmartRenewalPredictionEngine
from ai_modules.smart_lease_renewal.workflow_engine import AutomatedRenewalWorkflowEngine
from ai_modules.smart_lease_renewal.pricing_intelligence import DynamicPricingIntelligence
from ai_modules.smart_lease_renewal.risk_assessment import TenantRiskAssessment
from ai_modules.smart_lease_renewal.portfolio_optimizer import PortfolioOptimizer
from ai_modules.smart_lease_renewal.integration_manager import PlatformIntegrationManager
from ai_modules.smart_lease_renewal.dashboard_service import RenewalDashboardService

# Import database models
from models.smart_lease_renewal import (
    RenewalPrediction, RenewalWorkflow, WorkflowStep, PricingRecommendation,
    TenantRiskProfile, PortfolioOptimization, MarketIntelligence,
    IntegrationSync, DashboardAlert, get_latest_prediction, get_active_workflows,
    get_high_risk_tenants, get_pending_workflow_steps
)
from db import db

# Import authentication and utilities
from auth import require_auth, require_permission
from decorators import rate_limited, cached
from permissions_service import Permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
smart_renewal_bp = Blueprint('smart_lease_renewal', __name__, url_prefix='/api/smart-renewal')
api = Api(smart_renewal_bp)

# Initialize services
prediction_engine = SmartRenewalPredictionEngine()
workflow_engine = AutomatedRenewalWorkflowEngine()
pricing_intelligence = DynamicPricingIntelligence()
risk_assessment = TenantRiskAssessment()
portfolio_optimizer = PortfolioOptimizer()
dashboard_service = RenewalDashboardService()

# Utility decorators
def handle_async(f):
    """Decorator to handle async functions in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

def validate_json_request(required_fields: List[str] = None):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return {'error': 'Content-Type must be application/json'}, 400
            
            data = request.get_json()
            if not data:
                return {'error': 'Request body must contain valid JSON'}, 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return {'error': f'Missing required fields: {", ".join(missing_fields)}'}, 400
            
            return f(*args, data=data, **kwargs)
        return wrapper
    return decorator

# Prediction API Endpoints
class RenewalPredictionResource(Resource):
    """Lease renewal prediction endpoints"""
    
    @require_auth
    @require_permission(Permission.VIEW_ANALYTICS)
    @rate_limited(requests_per_minute=60)
    def get(self, tenant_id=None):
        """Get renewal predictions"""
        try:
            if tenant_id:
                # Get prediction for specific tenant
                prediction = get_latest_prediction(tenant_id)
                if not prediction:
                    return {'error': 'No prediction found for tenant'}, 404
                
                return {
                    'prediction': {
                        'tenant_id': prediction.tenant_id,
                        'property_id': prediction.property_id,
                        'renewal_probability': prediction.renewal_probability,
                        'churn_risk_score': prediction.churn_risk_score,
                        'confidence_score': prediction.confidence_score,
                        'risk_factors': prediction.risk_factors,
                        'recommended_actions': prediction.recommended_actions,
                        'optimal_timing': prediction.optimal_timing,
                        'market_factors': prediction.market_factors,
                        'component_scores': {
                            'tenant_satisfaction': prediction.tenant_satisfaction_score,
                            'financial_stability': prediction.financial_stability_score,
                            'property_attractiveness': prediction.property_attractiveness_score
                        },
                        'prediction_date': prediction.prediction_date.isoformat(),
                        'model_version': prediction.model_version
                    }
                }, 200
            
            else:
                # Get predictions summary
                page = request.args.get('page', 1, type=int)
                per_page = min(request.args.get('per_page', 20, type=int), 100)
                risk_threshold = request.args.get('risk_threshold', type=float)
                
                query = db.session.query(RenewalPrediction)
                
                if risk_threshold:
                    query = query.filter(RenewalPrediction.churn_risk_score >= risk_threshold)
                
                predictions = query.order_by(RenewalPrediction.prediction_date.desc()).paginate(
                    page=page, per_page=per_page, error_out=False
                )
                
                return {
                    'predictions': [{
                        'tenant_id': pred.tenant_id,
                        'property_id': pred.property_id,
                        'renewal_probability': pred.renewal_probability,
                        'churn_risk_score': pred.churn_risk_score,
                        'confidence_score': pred.confidence_score,
                        'prediction_date': pred.prediction_date.isoformat()
                    } for pred in predictions.items],
                    'pagination': {
                        'page': predictions.page,
                        'pages': predictions.pages,
                        'per_page': predictions.per_page,
                        'total': predictions.total
                    }
                }, 200
                
        except Exception as e:
            logger.error(f"Error retrieving predictions: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @require_auth
    @require_permission(Permission.MANAGE_ANALYTICS)
    @validate_json_request(['tenant_data', 'lease_data', 'property_data'])
    def post(self, data):
        """Generate new renewal prediction"""
        try:
            # Extract request data
            tenant_data = data['tenant_data']
            lease_data = data['lease_data']
            property_data = data['property_data']
            market_data = data.get('market_data', {})
            historical_data = data.get('historical_data', {})
            
            # Generate prediction
            prediction_result = prediction_engine.predict_renewal(
                tenant_data, lease_data, property_data, market_data, historical_data
            )
            
            # Save prediction to database
            db_prediction = RenewalPrediction(
                tenant_id=prediction_result.tenant_id,
                property_id=prediction_result.property_id,
                lease_id=prediction_result.lease_id,
                renewal_probability=prediction_result.renewal_probability,
                churn_risk_score=prediction_result.churn_risk_score,
                confidence_score=prediction_result.confidence_score,
                model_version=prediction_result.model_version,
                predicted_lease_terms=prediction_result.predicted_lease_terms,
                risk_factors=prediction_result.risk_factors,
                recommended_actions=prediction_result.recommended_actions,
                optimal_timing=prediction_result.optimal_timing,
                market_factors=prediction_result.market_factors,
                tenant_satisfaction_score=prediction_result.tenant_satisfaction_score,
                financial_stability_score=prediction_result.financial_stability_score,
                property_attractiveness_score=prediction_result.property_attractiveness_score
            )
            
            db.session.add(db_prediction)
            db.session.commit()
            
            return {
                'prediction': prediction_result.to_dict(),
                'message': 'Prediction generated successfully'
            }, 201
            
        except Exception as e:
            logger.error(f"Error generating prediction: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to generate prediction'}, 500

class BatchPredictionResource(Resource):
    """Batch prediction processing"""
    
    @require_auth
    @require_permission(Permission.MANAGE_ANALYTICS)
    @validate_json_request(['tenant_portfolio'])
    def post(self, data):
        """Generate predictions for multiple tenants"""
        try:
            tenant_portfolio = data['tenant_portfolio']
            
            if len(tenant_portfolio) > 100:
                return {'error': 'Maximum 100 tenants per batch request'}, 400
            
            # Generate batch predictions
            predictions = prediction_engine.batch_predict(tenant_portfolio)
            
            # Save predictions to database
            db_predictions = []
            for prediction_result in predictions:
                db_prediction = RenewalPrediction(
                    tenant_id=prediction_result.tenant_id,
                    property_id=prediction_result.property_id,
                    lease_id=prediction_result.lease_id,
                    renewal_probability=prediction_result.renewal_probability,
                    churn_risk_score=prediction_result.churn_risk_score,
                    confidence_score=prediction_result.confidence_score,
                    model_version=prediction_result.model_version,
                    predicted_lease_terms=prediction_result.predicted_lease_terms,
                    risk_factors=prediction_result.risk_factors,
                    recommended_actions=prediction_result.recommended_actions,
                    optimal_timing=prediction_result.optimal_timing,
                    market_factors=prediction_result.market_factors,
                    tenant_satisfaction_score=prediction_result.tenant_satisfaction_score,
                    financial_stability_score=prediction_result.financial_stability_score,
                    property_attractiveness_score=prediction_result.property_attractiveness_score
                )
                db_predictions.append(db_prediction)
            
            db.session.add_all(db_predictions)
            db.session.commit()
            
            return {
                'predictions': [pred.to_dict() for pred in predictions],
                'summary': {
                    'total_processed': len(predictions),
                    'high_risk_count': len([p for p in predictions if p.churn_risk_score > 0.7]),
                    'low_confidence_count': len([p for p in predictions if p.confidence_score < 0.6])
                }
            }, 201
            
        except Exception as e:
            logger.error(f"Error in batch prediction: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to process batch predictions'}, 500

# Workflow API Endpoints
class WorkflowResource(Resource):
    """Renewal workflow management"""
    
    @require_auth
    @require_permission(Permission.VIEW_WORKFLOWS)
    @rate_limited(requests_per_minute=100)
    def get(self, workflow_id=None):
        """Get workflow information"""
        try:
            if workflow_id:
                # Get specific workflow
                workflow = db.session.query(RenewalWorkflow).filter(
                    RenewalWorkflow.workflow_id == workflow_id
                ).first()
                
                if not workflow:
                    return {'error': 'Workflow not found'}, 404
                
                # Get workflow steps
                steps = db.session.query(WorkflowStep).filter(
                    WorkflowStep.workflow_id == workflow.id
                ).order_by(WorkflowStep.scheduled_date).all()
                
                return {
                    'workflow': {
                        'workflow_id': workflow.workflow_id,
                        'tenant_id': workflow.tenant_id,
                        'lease_id': workflow.lease_id,
                        'property_id': workflow.property_id,
                        'workflow_type': workflow.workflow_type,
                        'status': workflow.status,
                        'priority': workflow.priority,
                        'renewal_probability': workflow.renewal_probability,
                        'current_step': workflow.current_step,
                        'created_at': workflow.created_at.isoformat(),
                        'updated_at': workflow.updated_at.isoformat(),
                        'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None
                    },
                    'steps': [{
                        'step_id': step.step_id,
                        'step_type': step.step_type,
                        'name': step.name,
                        'status': step.status,
                        'scheduled_date': step.scheduled_date.isoformat(),
                        'completed_at': step.completed_at.isoformat() if step.completed_at else None,
                        'retry_count': step.retry_count
                    } for step in steps]
                }, 200
            
            else:
                # Get workflows list
                status_filter = request.args.getlist('status')
                priority_min = request.args.get('priority_min', type=int)
                tenant_id = request.args.get('tenant_id')
                page = request.args.get('page', 1, type=int)
                per_page = min(request.args.get('per_page', 20, type=int), 100)
                
                query = db.session.query(RenewalWorkflow)
                
                if status_filter:
                    query = query.filter(RenewalWorkflow.status.in_(status_filter))
                
                if priority_min:
                    query = query.filter(RenewalWorkflow.priority >= priority_min)
                
                if tenant_id:
                    query = query.filter(RenewalWorkflow.tenant_id == tenant_id)
                
                workflows = query.order_by(
                    RenewalWorkflow.priority.desc(), RenewalWorkflow.created_at.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
                
                return {
                    'workflows': [{
                        'workflow_id': wf.workflow_id,
                        'tenant_id': wf.tenant_id,
                        'property_id': wf.property_id,
                        'workflow_type': wf.workflow_type,
                        'status': wf.status,
                        'priority': wf.priority,
                        'renewal_probability': wf.renewal_probability,
                        'created_at': wf.created_at.isoformat(),
                        'updated_at': wf.updated_at.isoformat()
                    } for wf in workflows.items],
                    'pagination': {
                        'page': workflows.page,
                        'pages': workflows.pages,
                        'per_page': workflows.per_page,
                        'total': workflows.total
                    }
                }, 200
                
        except Exception as e:
            logger.error(f"Error retrieving workflows: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @require_auth
    @require_permission(Permission.MANAGE_WORKFLOWS)
    @validate_json_request(['tenant_data', 'lease_data', 'property_data', 'prediction_data'])
    @handle_async
    async def post(self, data):
        """Create new renewal workflow"""
        try:
            # Extract data
            tenant_data = data['tenant_data']
            lease_data = data['lease_data']
            property_data = data['property_data']
            prediction_data = data['prediction_data']
            
            # Create workflow
            workflow = workflow_engine.create_renewal_workflow(
                tenant_data, lease_data, property_data, prediction_data
            )
            
            # Save to database
            db_workflow = RenewalWorkflow(
                workflow_id=workflow.workflow_id,
                tenant_id=workflow.tenant_id,
                lease_id=workflow.lease_id,
                property_id=workflow.property_id,
                workflow_type=workflow.workflow_type,
                status=workflow.status.value,
                priority=workflow.priority,
                renewal_probability=workflow.renewal_probability,
                optimal_timing=workflow.optimal_timing,
                personalization_data=workflow.personalization_data,
                steps=workflow.steps,
                metadata=workflow.metadata
            )
            
            db.session.add(db_workflow)
            db.session.commit()
            
            return {
                'workflow': workflow.to_dict(),
                'message': 'Workflow created successfully'
            }, 201
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to create workflow'}, 500
    
    @require_auth
    @require_permission(Permission.MANAGE_WORKFLOWS)
    def put(self, workflow_id):
        """Update workflow status"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'Request body required'}, 400
            
            workflow = db.session.query(RenewalWorkflow).filter(
                RenewalWorkflow.workflow_id == workflow_id
            ).first()
            
            if not workflow:
                return {'error': 'Workflow not found'}, 404
            
            # Update allowed fields
            if 'status' in data:
                workflow.status = data['status']
            if 'priority' in data:
                workflow.priority = data['priority']
            if 'current_step' in data:
                workflow.current_step = data['current_step']
            
            workflow.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'workflow_id': workflow_id,
                'message': 'Workflow updated successfully'
            }, 200
            
        except Exception as e:
            logger.error(f"Error updating workflow: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to update workflow'}, 500

class WorkflowExecutionResource(Resource):
    """Workflow execution control"""
    
    @require_auth
    @require_permission(Permission.MANAGE_WORKFLOWS)
    @handle_async
    async def post(self, workflow_id, action):
        """Execute workflow actions"""
        try:
            workflow = db.session.query(RenewalWorkflow).filter(
                RenewalWorkflow.workflow_id == workflow_id
            ).first()
            
            if not workflow:
                return {'error': 'Workflow not found'}, 404
            
            if action == 'pause':
                reason = request.json.get('reason', '') if request.is_json else ''
                result = workflow_engine.pause_workflow(workflow_id, reason)
                
            elif action == 'resume':
                result = workflow_engine.resume_workflow(workflow_id)
                
            elif action == 'execute_step':
                step_id = request.json.get('step_id') if request.is_json else None
                if not step_id:
                    return {'error': 'step_id required for step execution'}, 400
                
                result = workflow_engine.execute_workflow_step(workflow_id, step_id)
                
            else:
                return {'error': f'Unknown action: {action}'}, 400
            
            if result:
                return {
                    'workflow_id': workflow_id,
                    'action': action,
                    'result': result,
                    'message': f'Action {action} executed successfully'
                }, 200
            else:
                return {'error': f'Failed to execute action: {action}'}, 400
                
        except Exception as e:
            logger.error(f"Error executing workflow action: {str(e)}")
            return {'error': 'Failed to execute workflow action'}, 500

# Pricing Intelligence API Endpoints
class PricingRecommendationResource(Resource):
    """Pricing intelligence and recommendations"""
    
    @require_auth
    @require_permission(Permission.VIEW_ANALYTICS)
    @rate_limited(requests_per_minute=60)
    def get(self, property_id=None):
        """Get pricing recommendations"""
        try:
            if property_id:
                # Get latest recommendation for property
                recommendation = db.session.query(PricingRecommendation).filter(
                    PricingRecommendation.property_id == property_id
                ).order_by(PricingRecommendation.recommendation_timestamp.desc()).first()
                
                if not recommendation:
                    return {'error': 'No pricing recommendation found'}, 404
                
                return {
                    'recommendation': {
                        'property_id': recommendation.property_id,
                        'tenant_id': recommendation.tenant_id,
                        'current_rent': recommendation.current_rent,
                        'recommended_rent': recommendation.recommended_rent,
                        'rent_change_percentage': recommendation.rent_change_percentage,
                        'confidence_level': recommendation.confidence_level,
                        'strategy': recommendation.strategy,
                        'market_segment': recommendation.market_segment,
                        'seasonal_adjustment': recommendation.seasonal_adjustment,
                        'concessions_value': recommendation.concessions_value,
                        'total_effective_rent': recommendation.total_effective_rent,
                        'market_analysis': recommendation.market_analysis,
                        'risk_assessment': recommendation.risk_assessment,
                        'competitive_position': recommendation.competitive_position,
                        'optimization_factors': recommendation.optimization_factors,
                        'recommendation_timestamp': recommendation.recommendation_timestamp.isoformat()
                    }
                }, 200
            
            else:
                # Get recommendations list
                page = request.args.get('page', 1, type=int)
                per_page = min(request.args.get('per_page', 20, type=int), 100)
                min_confidence = request.args.get('min_confidence', type=float)
                
                query = db.session.query(PricingRecommendation)
                
                if min_confidence:
                    query = query.filter(PricingRecommendation.confidence_level >= min_confidence)
                
                recommendations = query.order_by(
                    PricingRecommendation.recommendation_timestamp.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
                
                return {
                    'recommendations': [{
                        'property_id': rec.property_id,
                        'tenant_id': rec.tenant_id,
                        'current_rent': rec.current_rent,
                        'recommended_rent': rec.recommended_rent,
                        'rent_change_percentage': rec.rent_change_percentage,
                        'confidence_level': rec.confidence_level,
                        'strategy': rec.strategy,
                        'recommendation_timestamp': rec.recommendation_timestamp.isoformat()
                    } for rec in recommendations.items],
                    'pagination': {
                        'page': recommendations.page,
                        'pages': recommendations.pages,
                        'per_page': recommendations.per_page,
                        'total': recommendations.total
                    }
                }, 200
                
        except Exception as e:
            logger.error(f"Error retrieving pricing recommendations: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @require_auth
    @require_permission(Permission.MANAGE_ANALYTICS)
    @validate_json_request(['property_data', 'tenant_data', 'lease_data'])
    def post(self, data):
        """Generate pricing recommendation"""
        try:
            property_data = data['property_data']
            tenant_data = data['tenant_data']
            lease_data = data['lease_data']
            market_data = data.get('market_data', {})
            
            # Generate pricing recommendation
            recommendation = pricing_intelligence.analyze_market_pricing(
                property_data, tenant_data, lease_data, market_data
            )
            
            # Save to database
            db_recommendation = PricingRecommendation(
                property_id=recommendation.property_id,
                tenant_id=recommendation.tenant_id,
                current_rent=recommendation.current_rent,
                recommended_rent=recommendation.recommended_rent,
                rent_change_percentage=recommendation.rent_change_percentage,
                confidence_level=recommendation.confidence_level,
                strategy=recommendation.strategy.value,
                market_segment=recommendation.market_segment.value,
                seasonal_adjustment=recommendation.seasonal_adjustment,
                concessions_value=recommendation.concessions_value,
                total_effective_rent=recommendation.total_effective_rent,
                market_analysis=recommendation.market_analysis,
                risk_assessment=recommendation.risk_assessment,
                competitive_position=recommendation.competitive_position,
                optimization_factors=recommendation.optimization_factors
            )
            
            db.session.add(db_recommendation)
            db.session.commit()
            
            return {
                'recommendation': recommendation.to_dict(),
                'message': 'Pricing recommendation generated successfully'
            }, 201
            
        except Exception as e:
            logger.error(f"Error generating pricing recommendation: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to generate pricing recommendation'}, 500

# Risk Assessment API Endpoints
class RiskAssessmentResource(Resource):
    """Tenant risk assessment"""
    
    @require_auth
    @require_permission(Permission.VIEW_ANALYTICS)
    @rate_limited(requests_per_minute=60)
    def get(self, tenant_id=None):
        """Get risk assessments"""
        try:
            if tenant_id:
                # Get latest risk profile for tenant
                risk_profile = db.session.query(TenantRiskProfile).filter(
                    TenantRiskProfile.tenant_id == tenant_id
                ).order_by(TenantRiskProfile.assessment_timestamp.desc()).first()
                
                if not risk_profile:
                    return {'error': 'No risk assessment found'}, 404
                
                return {
                    'risk_profile': {
                        'tenant_id': risk_profile.tenant_id,
                        'overall_risk_score': risk_profile.overall_risk_score,
                        'risk_level': risk_profile.risk_level,
                        'tenant_segment': risk_profile.tenant_segment,
                        'confidence_score': risk_profile.confidence_score,
                        'risk_factors': risk_profile.risk_factors,
                        'category_scores': risk_profile.category_scores,
                        'early_warning_indicators': risk_profile.early_warning_indicators,
                        'mitigation_strategies': risk_profile.mitigation_strategies,
                        'monitoring_recommendations': risk_profile.monitoring_recommendations,
                        'next_review_date': risk_profile.next_review_date.isoformat(),
                        'assessment_timestamp': risk_profile.assessment_timestamp.isoformat()
                    }
                }, 200
            
            else:
                # Get risk assessments list
                risk_level = request.args.get('risk_level')
                tenant_segment = request.args.get('tenant_segment')
                page = request.args.get('page', 1, type=int)
                per_page = min(request.args.get('per_page', 20, type=int), 100)
                
                query = db.session.query(TenantRiskProfile)
                
                if risk_level:
                    query = query.filter(TenantRiskProfile.risk_level == risk_level)
                
                if tenant_segment:
                    query = query.filter(TenantRiskProfile.tenant_segment == tenant_segment)
                
                risk_profiles = query.order_by(
                    TenantRiskProfile.overall_risk_score.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
                
                return {
                    'risk_profiles': [{
                        'tenant_id': profile.tenant_id,
                        'overall_risk_score': profile.overall_risk_score,
                        'risk_level': profile.risk_level,
                        'tenant_segment': profile.tenant_segment,
                        'confidence_score': profile.confidence_score,
                        'assessment_timestamp': profile.assessment_timestamp.isoformat()
                    } for profile in risk_profiles.items],
                    'pagination': {
                        'page': risk_profiles.page,
                        'pages': risk_profiles.pages,
                        'per_page': risk_profiles.per_page,
                        'total': risk_profiles.total
                    }
                }, 200
                
        except Exception as e:
            logger.error(f"Error retrieving risk assessments: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @require_auth
    @require_permission(Permission.MANAGE_ANALYTICS)
    @validate_json_request(['tenant_data', 'lease_data', 'property_data'])
    def post(self, data):
        """Generate risk assessment"""
        try:
            tenant_data = data['tenant_data']
            lease_data = data['lease_data']
            property_data = data['property_data']
            market_data = data.get('market_data', {})
            historical_data = data.get('historical_data', {})
            
            # Generate risk assessment
            risk_profile = risk_assessment.assess_tenant_risk(
                tenant_data, lease_data, property_data, market_data, historical_data
            )
            
            # Save to database
            db_risk_profile = TenantRiskProfile(
                tenant_id=risk_profile.tenant_id,
                overall_risk_score=risk_profile.overall_risk_score,
                risk_level=risk_profile.risk_level.value,
                tenant_segment=risk_profile.tenant_segment.value,
                confidence_score=risk_profile.confidence_score,
                risk_factors=[factor.to_dict() for factor in risk_profile.risk_factors],
                category_scores=risk_profile.category_scores,
                trend_analysis=risk_profile.trend_analysis,
                comparative_analysis=risk_profile.comparative_analysis,
                early_warning_indicators=risk_profile.early_warning_indicators,
                mitigation_strategies=risk_profile.mitigation_strategies,
                monitoring_recommendations=risk_profile.monitoring_recommendations,
                next_review_date=risk_profile.next_review_date
            )
            
            db.session.add(db_risk_profile)
            db.session.commit()
            
            return {
                'risk_profile': risk_profile.to_dict(),
                'message': 'Risk assessment completed successfully'
            }, 201
            
        except Exception as e:
            logger.error(f"Error generating risk assessment: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to generate risk assessment'}, 500

# Portfolio Optimization API Endpoints
class PortfolioOptimizationResource(Resource):
    """Portfolio optimization"""
    
    @require_auth
    @require_permission(Permission.VIEW_ANALYTICS)
    @rate_limited(requests_per_minute=30)
    def get(self, optimization_id=None):
        """Get portfolio optimization results"""
        try:
            if optimization_id:
                optimization = db.session.query(PortfolioOptimization).filter(
                    PortfolioOptimization.optimization_id == optimization_id
                ).first()
                
                if not optimization:
                    return {'error': 'Optimization not found'}, 404
                
                return {
                    'optimization': {
                        'optimization_id': optimization.optimization_id,
                        'objective': optimization.objective,
                        'strategy': optimization.strategy,
                        'property_recommendations': optimization.property_recommendations,
                        'expected_outcomes': optimization.expected_outcomes,
                        'risk_metrics': optimization.risk_metrics,
                        'portfolio_metrics': optimization.portfolio_metrics,
                        'sensitivity_analysis': optimization.sensitivity_analysis,
                        'implementation_timeline': optimization.implementation_timeline,
                        'confidence_score': optimization.confidence_score,
                        'optimization_timestamp': optimization.optimization_timestamp.isoformat()
                    }
                }, 200
            
            else:
                # Get optimization history
                page = request.args.get('page', 1, type=int)
                per_page = min(request.args.get('per_page', 10, type=int), 50)
                objective = request.args.get('objective')
                
                query = db.session.query(PortfolioOptimization)
                
                if objective:
                    query = query.filter(PortfolioOptimization.objective == objective)
                
                optimizations = query.order_by(
                    PortfolioOptimization.optimization_timestamp.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
                
                return {
                    'optimizations': [{
                        'optimization_id': opt.optimization_id,
                        'objective': opt.objective,
                        'strategy': opt.strategy,
                        'confidence_score': opt.confidence_score,
                        'optimization_timestamp': opt.optimization_timestamp.isoformat()
                    } for opt in optimizations.items],
                    'pagination': {
                        'page': optimizations.page,
                        'pages': optimizations.pages,
                        'per_page': optimizations.per_page,
                        'total': optimizations.total
                    }
                }, 200
                
        except Exception as e:
            logger.error(f"Error retrieving portfolio optimizations: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @require_auth
    @require_permission(Permission.MANAGE_ANALYTICS)
    @validate_json_request(['properties'])
    def post(self, data):
        """Run portfolio optimization"""
        try:
            properties = data['properties']
            objective = data.get('objective', 'balanced_optimization')
            strategy = data.get('strategy', 'balanced')
            constraints = data.get('constraints', [])
            
            if len(properties) > 1000:
                return {'error': 'Maximum 1000 properties per optimization'}, 400
            
            # Run optimization
            optimization_result = portfolio_optimizer.optimize_portfolio(
                properties, objective, constraints, strategy
            )
            
            # Save to database
            db_optimization = PortfolioOptimization(
                optimization_id=optimization_result.optimization_id,
                objective=optimization_result.objective.value,
                strategy=optimization_result.strategy.value,
                property_recommendations=optimization_result.property_recommendations,
                expected_outcomes=optimization_result.expected_outcomes,
                risk_metrics=optimization_result.risk_metrics,
                portfolio_metrics=optimization_result.portfolio_metrics,
                sensitivity_analysis=optimization_result.sensitivity_analysis,
                implementation_timeline=optimization_result.implementation_timeline,
                confidence_score=optimization_result.confidence_score
            )
            
            db.session.add(db_optimization)
            db.session.commit()
            
            return {
                'optimization': optimization_result.to_dict(),
                'message': 'Portfolio optimization completed successfully'
            }, 201
            
        except Exception as e:
            logger.error(f"Error running portfolio optimization: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to run portfolio optimization'}, 500

# Dashboard API Endpoints
class DashboardResource(Resource):
    """Dashboard data and analytics"""
    
    @require_auth
    @require_permission(Permission.VIEW_DASHBOARD)
    @rate_limited(requests_per_minute=120)
    @cached(timeout=300)  # Cache for 5 minutes
    @handle_async
    async def get(self):
        """Get dashboard data"""
        try:
            user_type = request.args.get('user_type', 'property_manager')
            timeframe = request.args.get('timeframe', '30d')
            filters = request.args.to_dict()
            
            # Remove non-filter parameters
            filters.pop('user_type', None)
            filters.pop('timeframe', None)
            
            # Generate dashboard data
            dashboard_data = await dashboard_service.get_dashboard_data(
                user_type=user_type,
                timeframe=timeframe,
                filters=filters if filters else None
            )
            
            return dashboard_data, 200
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            return {'error': 'Failed to generate dashboard data'}, 500

class AlertResource(Resource):
    """Dashboard alerts management"""
    
    @require_auth
    @require_permission(Permission.VIEW_DASHBOARD)
    @rate_limited(requests_per_minute=60)
    def get(self):
        """Get active alerts"""
        try:
            status = request.args.getlist('status') or ['active']
            severity = request.args.getlist('severity')
            category = request.args.getlist('category')
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            query = db.session.query(DashboardAlert)
            
            if status:
                query = query.filter(DashboardAlert.status.in_(status))
            
            if severity:
                query = query.filter(DashboardAlert.severity.in_(severity))
            
            if category:
                query = query.filter(DashboardAlert.category.in_(category))
            
            alerts = query.order_by(
                DashboardAlert.severity.desc(),
                DashboardAlert.triggered_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'alerts': [{
                    'alert_id': alert.alert_id,
                    'title': alert.title,
                    'message': alert.message,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'category': alert.category,
                    'status': alert.status,
                    'action_required': alert.action_required,
                    'recommended_action': alert.recommended_action,
                    'related_entity_type': alert.related_entity_type,
                    'related_entity_id': alert.related_entity_id,
                    'triggered_at': alert.triggered_at.isoformat(),
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                } for alert in alerts.items],
                'pagination': {
                    'page': alerts.page,
                    'pages': alerts.pages,
                    'per_page': alerts.per_page,
                    'total': alerts.total
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error retrieving alerts: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @require_auth
    @require_permission(Permission.MANAGE_DASHBOARD)
    def put(self, alert_id):
        """Update alert status"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'Request body required'}, 400
            
            alert = db.session.query(DashboardAlert).filter(
                DashboardAlert.alert_id == alert_id
            ).first()
            
            if not alert:
                return {'error': 'Alert not found'}, 404
            
            # Update alert
            if 'status' in data:
                alert.status = data['status']
                
                if data['status'] == 'acknowledged':
                    alert.acknowledged_by = data.get('acknowledged_by')
                    alert.acknowledged_at = datetime.utcnow()
                elif data['status'] == 'resolved':
                    alert.resolved_at = datetime.utcnow()
            
            if 'action_taken' in data:
                alert.action_taken = data['action_taken']
                alert.action_taken_by = data.get('action_taken_by')
                alert.action_taken_at = datetime.utcnow()
            
            alert.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'alert_id': alert_id,
                'message': 'Alert updated successfully'
            }, 200
            
        except Exception as e:
            logger.error(f"Error updating alert: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to update alert'}, 500

# System Health and Status Endpoints
class SystemStatusResource(Resource):
    """System status and health monitoring"""
    
    @require_auth
    @require_permission(Permission.VIEW_SYSTEM_STATUS)
    @rate_limited(requests_per_minute=30)
    def get(self):
        """Get system status"""
        try:
            # Get basic system metrics
            active_workflows = db.session.query(RenewalWorkflow).filter(
                RenewalWorkflow.status.in_(['pending', 'active', 'in_progress'])
            ).count()
            
            recent_predictions = db.session.query(RenewalPrediction).filter(
                RenewalPrediction.prediction_date >= datetime.utcnow() - timedelta(days=1)
            ).count()
            
            active_alerts = db.session.query(DashboardAlert).filter(
                DashboardAlert.status == 'active'
            ).count()
            
            # Get recent integration syncs
            recent_syncs = db.session.query(IntegrationSync).filter(
                IntegrationSync.sync_started_at >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            sync_status = {}
            for sync in recent_syncs:
                if sync.integration_id not in sync_status:
                    sync_status[sync.integration_id] = {
                        'last_sync': sync.sync_completed_at.isoformat() if sync.sync_completed_at else None,
                        'status': sync.status,
                        'records_processed': sync.records_processed
                    }
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': {
                    'active_workflows': active_workflows,
                    'recent_predictions': recent_predictions,
                    'active_alerts': active_alerts
                },
                'integrations': sync_status,
                'services': {
                    'prediction_engine': 'operational',
                    'workflow_engine': 'operational',
                    'pricing_intelligence': 'operational',
                    'risk_assessment': 'operational',
                    'portfolio_optimizer': 'operational',
                    'dashboard_service': 'operational'
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error retrieving system status: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to retrieve system status',
                'timestamp': datetime.utcnow().isoformat()
            }, 500

# Register API resources
api.add_resource(RenewalPredictionResource, '/predictions', '/predictions/<string:tenant_id>')
api.add_resource(BatchPredictionResource, '/predictions/batch')
api.add_resource(WorkflowResource, '/workflows', '/workflows/<string:workflow_id>')
api.add_resource(WorkflowExecutionResource, '/workflows/<string:workflow_id>/actions/<string:action>')
api.add_resource(PricingRecommendationResource, '/pricing', '/pricing/<string:property_id>')
api.add_resource(RiskAssessmentResource, '/risk-assessment', '/risk-assessment/<string:tenant_id>')
api.add_resource(PortfolioOptimizationResource, '/portfolio-optimization', '/portfolio-optimization/<string:optimization_id>')
api.add_resource(DashboardResource, '/dashboard')
api.add_resource(AlertResource, '/alerts', '/alerts/<string:alert_id>')
api.add_resource(SystemStatusResource, '/system/status')

# Error handlers
@smart_renewal_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@smart_renewal_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@smart_renewal_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403

@smart_renewal_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

@smart_renewal_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded', 'message': 'Too many requests'}), 429

@smart_renewal_bp.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error', 'message': 'Something went wrong'}), 500

# Health check endpoint
@smart_renewal_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'smart-lease-renewal-api',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200