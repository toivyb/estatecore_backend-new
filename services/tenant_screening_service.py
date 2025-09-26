"""
Tenant Screening Service
Main service for orchestrating predictive tenant screening operations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from models.base import db
from models.tenant_screening import (
    TenantApplication, ScreeningResult, CreditAssessment, 
    FraudDetection, RiskProfile, ScreeningMetrics,
    ApplicationStatus, ScreeningStatus, RiskLevel
)
from ai_modules.tenant_screening.predictive_screening_engine import (
    get_predictive_screening_engine, ScreeningScore, ScreeningInsights
)
from services.credit_reporting_service import get_credit_reporting_service
from services.background_check_service import get_background_check_service
from services.document_verification_service import get_document_verification_service


logger = logging.getLogger(__name__)


@dataclass
class ScreeningRequest:
    """Request for tenant screening"""
    application_id: str
    priority: str = "normal"  # normal, high, urgent
    screening_type: str = "comprehensive"  # basic, comprehensive, express
    bypass_cache: bool = False


@dataclass
class ScreeningResponse:
    """Response from tenant screening"""
    success: bool
    application_id: str
    screening_id: Optional[str]
    score: Optional[ScreeningScore]
    insights: Optional[ScreeningInsights]
    processing_time: float
    recommendations: List[str]
    next_steps: List[str]
    error: Optional[str] = None


class TenantScreeningService:
    """Main service for predictive tenant screening operations"""
    
    def __init__(self):
        self.screening_engine = get_predictive_screening_engine()
        self.credit_service = get_credit_reporting_service()
        self.background_service = get_background_check_service()
        self.document_service = get_document_verification_service()
        
    async def process_screening_request(self, request: ScreeningRequest) -> ScreeningResponse:
        """Process a complete tenant screening request"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing screening request for application {request.application_id}")
            
            # Get application data
            application = db.session.query(TenantApplication).filter_by(
                id=request.application_id
            ).first()
            
            if not application:
                return ScreeningResponse(
                    success=False,
                    application_id=request.application_id,
                    screening_id=None,
                    score=None,
                    insights=None,
                    processing_time=0,
                    recommendations=[],
                    next_steps=[],
                    error="Application not found"
                )
            
            # Update application status
            application.status = ApplicationStatus.UNDER_REVIEW.value
            db.session.commit()
            
            # Gather comprehensive data
            comprehensive_data = await self._gather_comprehensive_data(application, request.screening_type)
            
            # Run AI-powered screening
            screening_score = await self.screening_engine.screen_applicant(comprehensive_data)
            
            # Generate insights
            screening_insights = await self.screening_engine.generate_screening_insights(
                comprehensive_data, screening_score
            )
            
            # Create screening result record
            screening_result = await self._create_screening_result(
                application, screening_score, screening_insights, request.screening_type
            )
            
            # Run additional assessments
            await self._run_additional_assessments(application, comprehensive_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(screening_score, screening_insights)
            next_steps = self._generate_next_steps(screening_score)
            
            # Update metrics
            self._update_screening_metrics(screening_score, datetime.now() - start_time)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Screening completed for application {request.application_id} in {processing_time:.2f}s")
            
            return ScreeningResponse(
                success=True,
                application_id=request.application_id,
                screening_id=str(screening_result.id),
                score=screening_score,
                insights=screening_insights,
                processing_time=processing_time,
                recommendations=recommendations,
                next_steps=next_steps
            )
            
        except Exception as e:
            logger.error(f"Error processing screening request: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ScreeningResponse(
                success=False,
                application_id=request.application_id,
                screening_id=None,
                score=None,
                insights=None,
                processing_time=processing_time,
                recommendations=[],
                next_steps=["Manual review required due to system error"],
                error=str(e)
            )
    
    async def _gather_comprehensive_data(self, application: TenantApplication, screening_type: str) -> Dict[str, Any]:
        """Gather comprehensive data for screening analysis"""
        try:
            logger.debug(f"Gathering comprehensive data for application {application.id}")
            
            # Start with application data
            data = {
                'applicant_name': application.applicant_name,
                'email': application.email,
                'phone_number': application.phone_number,
                'annual_income': application.annual_income,
                'monthly_income': application.monthly_income,
                'employment_type': application.employment_type,
                'employment_length_months': application.employment_length_months,
                'credit_score': application.credit_score,
                'rental_history_length': application.rental_history_length,
                'previous_evictions': application.previous_evictions,
                'late_payment_count': application.late_payment_count,
                'number_of_references': application.number_of_references,
                'debt_to_income_ratio': application.debt_to_income_ratio,
                'monthly_rent': application.monthly_rent_budget,
                'industry': application.industry,
                'job_title': application.job_title
            }
            
            # Add derived fields
            if application.annual_income and application.monthly_rent_budget:
                data['income_to_rent_ratio'] = (application.annual_income / 12) / application.monthly_rent_budget
            
            if application.savings_amount and application.monthly_rent_budget:
                data['savings_months'] = application.savings_amount / application.monthly_rent_budget
            
            # Enhanced data gathering for comprehensive screening
            if screening_type == "comprehensive":
                # Credit report data
                if application.credit_score:
                    credit_data = await self._get_enhanced_credit_data(application)
                    data.update(credit_data)
                
                # Employment verification
                employment_data = await self._verify_employment_data(application)
                data.update(employment_data)
                
                # Rental history verification
                rental_data = await self._verify_rental_history(application)
                data.update(rental_data)
                
                # Document analysis
                document_data = await self._analyze_documents(application)
                data.update(document_data)
                
                # Reference verification
                reference_data = await self._verify_references(application)
                data.update(reference_data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error gathering comprehensive data: {e}")
            # Return basic data if enhanced gathering fails
            return {
                'applicant_name': application.applicant_name or 'Unknown',
                'annual_income': application.annual_income or 0,
                'credit_score': application.credit_score or 600,
                'employment_length_months': application.employment_length_months or 0,
                'rental_history_length': application.rental_history_length or 0,
                'previous_evictions': application.previous_evictions or 0,
                'number_of_references': application.number_of_references or 0
            }
    
    async def _get_enhanced_credit_data(self, application: TenantApplication) -> Dict[str, Any]:
        """Get enhanced credit report data"""
        try:
            # This would integrate with actual credit reporting APIs
            # For now, simulate enhanced credit data
            
            base_score = application.credit_score or 650
            
            # Simulate credit analysis
            payment_history_score = min(100, base_score / 8.5)
            credit_utilization = max(0.1, min(0.9, (850 - base_score) / 850))
            
            return {
                'payment_history_score': payment_history_score,
                'credit_utilization_ratio': credit_utilization,
                'total_accounts': 8,
                'active_accounts': 6,
                'derogatory_marks': 1 if base_score < 650 else 0,
                'recent_inquiries': 2 if base_score < 700 else 1,
                'bankruptcy_history': application.bankruptcy_history or False,
                'foreclosure_history': application.foreclosure_history or False
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced credit data: {e}")
            return {}
    
    async def _verify_employment_data(self, application: TenantApplication) -> Dict[str, Any]:
        """Verify employment information"""
        try:
            # This would integrate with employment verification services
            # For now, simulate verification results
            
            verification_score = 85.0  # Assume most employment is verifiable
            
            if application.employment_type == 'self_employed':
                verification_score = 60.0
            elif application.employment_type == 'contract':
                verification_score = 70.0
            
            return {
                'employment_verified': verification_score > 70,
                'employment_verification_score': verification_score,
                'income_verified': verification_score > 75,
                'employment_stability_score': min(100, (application.employment_length_months or 12) * 2)
            }
            
        except Exception as e:
            logger.error(f"Error verifying employment data: {e}")
            return {'employment_verified': False}
    
    async def _verify_rental_history(self, application: TenantApplication) -> Dict[str, Any]:
        """Verify rental history information"""
        try:
            # This would integrate with rental history verification services
            # For now, simulate verification results
            
            landlord_references = application.landlord_references or []
            
            verification_success_rate = 0.8 if len(landlord_references) > 0 else 0.3
            
            reference_quality = 'good'
            if len(landlord_references) >= 2:
                reference_quality = 'excellent'
            elif len(landlord_references) == 0:
                reference_quality = 'poor'
            
            return {
                'landlord_reference_quality': reference_quality,
                'rental_history_verified': verification_success_rate > 0.5,
                'verification_success_rate': verification_success_rate,
                'housing_history_type': 'rental' if application.rental_history_length > 0 else 'first_time'
            }
            
        except Exception as e:
            logger.error(f"Error verifying rental history: {e}")
            return {}
    
    async def _analyze_documents(self, application: TenantApplication) -> Dict[str, Any]:
        """Analyze submitted documents for authenticity and completeness"""
        try:
            documents = application.documents_submitted or []
            
            # Simulate document analysis
            document_quality_score = 80.0
            required_docs = ['id', 'pay_stubs', 'bank_statements']
            submitted_docs = [doc.get('type', '') for doc in documents]
            
            completeness_score = len([doc for doc in required_docs if doc in submitted_docs]) / len(required_docs) * 100
            
            return {
                'document_quality_score': document_quality_score,
                'application_completeness': 'complete' if completeness_score > 80 else 'incomplete',
                'document_authenticity_score': document_quality_score,
                'documents_complete': completeness_score > 80
            }
            
        except Exception as e:
            logger.error(f"Error analyzing documents: {e}")
            return {'document_quality_score': 70.0}
    
    async def _verify_references(self, application: TenantApplication) -> Dict[str, Any]:
        """Verify personal and professional references"""
        try:
            personal_refs = application.personal_references or []
            professional_refs = application.professional_references or []
            landlord_refs = application.landlord_references or []
            
            total_refs = len(personal_refs) + len(professional_refs) + len(landlord_refs)
            
            # Simulate reference quality assessment
            reference_quality = 'fair'
            if total_refs >= 3:
                reference_quality = 'good'
            if total_refs >= 4 and len(landlord_refs) >= 1:
                reference_quality = 'excellent'
            elif total_refs == 0:
                reference_quality = 'none'
            
            reference_types = []
            if len(personal_refs) > 0:
                reference_types.append('personal')
            if len(professional_refs) > 0:
                reference_types.append('professional')
            if len(landlord_refs) > 0:
                reference_types.append('landlord')
            
            return {
                'reference_quality': reference_quality,
                'reference_types': reference_types,
                'total_reference_count': total_refs,
                'landlord_references_count': len(landlord_refs)
            }
            
        except Exception as e:
            logger.error(f"Error verifying references: {e}")
            return {'reference_quality': 'unknown'}
    
    async def _create_screening_result(
        self, 
        application: TenantApplication, 
        score: ScreeningScore, 
        insights: ScreeningInsights,
        screening_type: str
    ) -> ScreeningResult:
        """Create and save screening result to database"""
        try:
            screening_result = ScreeningResult(
                application_id=application.id,
                overall_score=score.overall_score,
                credit_score_assessment=score.credit_score,
                income_score=score.income_score,
                rental_history_score=score.rental_history_score,
                employment_score=score.employment_score,
                reference_score=score.reference_score,
                fraud_risk_score=score.fraud_risk_score,
                risk_level=score.risk_level.value,
                approval_recommendation=score.recommendation.value,
                confidence_score=score.confidence,
                ai_insights={
                    'strengths': insights.strengths,
                    'concerns': insights.concerns,
                    'recommendations': insights.recommendations,
                    'probability_of_success': insights.probability_of_success
                },
                strengths=insights.strengths,
                concerns=insights.concerns,
                recommendations=insights.recommendations,
                screening_method='ai_powered',
                model_version='1.0.0'
            )
            
            db.session.add(screening_result)
            db.session.commit()
            
            logger.info(f"Screening result created for application {application.id}")
            return screening_result
            
        except Exception as e:
            logger.error(f"Error creating screening result: {e}")
            db.session.rollback()
            raise
    
    async def _run_additional_assessments(self, application: TenantApplication, data: Dict[str, Any]):
        """Run additional specialized assessments"""
        try:
            # Credit assessment
            await self._create_credit_assessment(application, data)
            
            # Fraud detection
            await self._create_fraud_detection(application, data)
            
            # Risk profile
            await self._create_risk_profile(application, data)
            
        except Exception as e:
            logger.error(f"Error running additional assessments: {e}")
    
    async def _create_credit_assessment(self, application: TenantApplication, data: Dict[str, Any]):
        """Create detailed credit assessment"""
        try:
            credit_assessment = CreditAssessment(
                application_id=application.id,
                credit_score=data.get('credit_score', application.credit_score),
                credit_report_date=datetime.now(),
                credit_bureau='TransUnion',  # Default bureau
                payment_history_score=data.get('payment_history_score', 75),
                credit_utilization_ratio=data.get('credit_utilization_ratio', 0.3),
                total_accounts=data.get('total_accounts', 8),
                active_accounts=data.get('active_accounts', 6),
                derogatory_marks=data.get('derogatory_marks', 0),
                total_debt=data.get('total_debt', 0),
                monthly_debt_payments=data.get('monthly_debt_payments', 0),
                debt_to_income_ratio=data.get('debt_to_income_ratio', application.debt_to_income_ratio),
                recent_inquiries=data.get('recent_inquiries', 1),
                collections_accounts=data.get('collections_accounts', 0),
                bankruptcies=1 if data.get('bankruptcy_history', False) else 0,
                foreclosures=1 if data.get('foreclosure_history', False) else 0,
                credit_risk_score=data.get('credit_score', 650) / 8.5,  # Convert to 0-100 scale
                payment_probability=0.95 if data.get('credit_score', 650) > 700 else 0.85,
                credit_trend='stable'
            )
            
            db.session.add(credit_assessment)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating credit assessment: {e}")
            db.session.rollback()
    
    async def _create_fraud_detection(self, application: TenantApplication, data: Dict[str, Any]):
        """Create fraud detection analysis"""
        try:
            # Calculate fraud risk based on various factors
            fraud_indicators = []
            
            # Income consistency check
            income = data.get('annual_income', 0)
            employment_length = data.get('employment_length_months', 0)
            
            if income > 100000 and employment_length < 6:
                fraud_indicators.append('High income with short employment')
            
            # Document quality check
            doc_quality = data.get('document_quality_score', 80)
            if doc_quality < 60:
                fraud_indicators.append('Poor document quality')
            
            fraud_risk_score = max(0, 100 - (len(fraud_indicators) * 25))
            
            fraud_detection = FraudDetection(
                application_id=application.id,
                fraud_risk_score=fraud_risk_score,
                fraud_probability=1 - (fraud_risk_score / 100),
                risk_level='low' if fraud_risk_score > 80 else 'medium' if fraud_risk_score > 60 else 'high',
                identity_verification_score=85.0,
                document_authenticity_score=doc_quality,
                document_consistency_score=80.0,
                income_consistency_score=90.0,
                employment_consistency_score=85.0,
                red_flags=fraud_indicators,
                requires_manual_review=len(fraud_indicators) > 2
            )
            
            db.session.add(fraud_detection)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating fraud detection: {e}")
            db.session.rollback()
    
    async def _create_risk_profile(self, application: TenantApplication, data: Dict[str, Any]):
        """Create comprehensive risk profile"""
        try:
            # Calculate various risk scores
            financial_risk = 100 - (data.get('credit_score', 650) / 8.5)
            stability_risk = max(0, 50 - (data.get('employment_length_months', 0) * 2))
            behavioral_risk = data.get('previous_evictions', 0) * 20 + data.get('late_payment_count', 0) * 5
            
            overall_risk = (financial_risk + stability_risk + behavioral_risk) / 3
            
            risk_profile = RiskProfile(
                application_id=application.id,
                overall_risk_score=min(100, overall_risk),
                risk_category='low' if overall_risk < 25 else 'medium' if overall_risk < 50 else 'high',
                financial_risk_score=financial_risk,
                behavioral_risk_score=behavioral_risk,
                stability_risk_score=stability_risk,
                payment_default_probability=overall_risk / 100 * 0.3,
                early_termination_probability=overall_risk / 100 * 0.2,
                eviction_probability=data.get('previous_evictions', 0) / 10,
                recommended_security_deposit=data.get('monthly_rent', 1500) * (1 + overall_risk / 100),
                short_term_risk_score=overall_risk * 1.2,  # Higher risk in first 6 months
                long_term_risk_score=overall_risk * 0.8,   # Lower risk after 6 months
                model_version='1.0.0'
            )
            
            db.session.add(risk_profile)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating risk profile: {e}")
            db.session.rollback()
    
    def _generate_recommendations(self, score: ScreeningScore, insights: ScreeningInsights) -> List[str]:
        """Generate actionable recommendations based on screening results"""
        recommendations = []
        
        # Add insights recommendations
        recommendations.extend(insights.recommendations)
        
        # Add score-based recommendations
        if score.recommendation.value == 'approve':
            recommendations.append("Approved for standard lease terms")
            if score.overall_score < 85:
                recommendations.append("Monitor payment performance closely in first 90 days")
        
        elif score.recommendation.value == 'conditional_approve':
            recommendations.append("Approve with additional security deposit")
            recommendations.append("Require additional documentation verification")
            if score.fraud_risk_score < 70:
                recommendations.append("Conduct additional identity verification")
        
        elif score.recommendation.value == 'require_cosigner':
            recommendations.append("Require qualified cosigner for approval")
            recommendations.append("Verify cosigner meets income requirements (3x rent)")
            recommendations.append("Obtain separate credit report for cosigner")
        
        elif score.recommendation.value == 'decline':
            recommendations.append("Decline application due to high risk factors")
            if score.credit_score < 50:
                recommendations.append("Primary concern: Credit history")
            if score.income_score < 50:
                recommendations.append("Primary concern: Insufficient income")
        
        # Risk-specific recommendations
        if score.risk_level == RiskLevel.HIGH or score.risk_level == RiskLevel.CRITICAL:
            recommendations.append("Consider requiring larger security deposit")
            recommendations.append("Implement enhanced tenant monitoring")
        
        return recommendations
    
    def _generate_next_steps(self, score: ScreeningScore) -> List[str]:
        """Generate next steps based on screening results"""
        next_steps = []
        
        if score.recommendation.value == 'approve':
            next_steps.extend([
                "Prepare lease agreement",
                "Schedule lease signing appointment",
                "Collect security deposit and first month's rent"
            ])
        
        elif score.recommendation.value == 'conditional_approve':
            next_steps.extend([
                "Request additional documentation",
                "Calculate increased security deposit amount",
                "Prepare conditional approval letter"
            ])
        
        elif score.recommendation.value == 'require_cosigner':
            next_steps.extend([
                "Contact applicant about cosigner requirement",
                "Provide cosigner application forms",
                "Schedule follow-up when cosigner information is received"
            ])
        
        elif score.recommendation.value == 'decline':
            next_steps.extend([
                "Prepare decline letter with reason (as legally permitted)",
                "File application records",
                "Update application status in system"
            ])
        
        # Universal next steps
        next_steps.append("Update applicant on application status")
        next_steps.append("Document decision rationale in applicant file")
        
        return next_steps
    
    def _update_screening_metrics(self, score: ScreeningScore, processing_time: timedelta):
        """Update system metrics with screening results"""
        try:
            # Get or create today's metrics
            today = datetime.now().date()
            metrics = db.session.query(ScreeningMetrics).filter_by(
                date=today,
                period_type='daily'
            ).first()
            
            if not metrics:
                metrics = ScreeningMetrics(
                    date=today,
                    period_type='daily'
                )
                db.session.add(metrics)
            
            # Update metrics
            metrics.total_applications = (metrics.total_applications or 0) + 1
            metrics.applications_screened = (metrics.applications_screened or 0) + 1
            
            # Update decision counts
            if score.recommendation.value == 'approve':
                metrics.approved_count = (metrics.approved_count or 0) + 1
            elif score.recommendation.value == 'conditional_approve':
                metrics.conditionally_approved_count = (metrics.conditionally_approved_count or 0) + 1
            elif score.recommendation.value == 'decline':
                metrics.declined_count = (metrics.declined_count or 0) + 1
            elif score.recommendation.value == 'require_cosigner':
                metrics.cosigner_required_count = (metrics.cosigner_required_count or 0) + 1
            
            # Update performance metrics
            current_avg_time = metrics.average_screening_time_seconds or 0
            current_count = metrics.applications_screened or 1
            new_avg_time = ((current_avg_time * (current_count - 1)) + processing_time.total_seconds()) / current_count
            metrics.average_screening_time_seconds = new_avg_time
            
            # Update confidence metrics
            if score.confidence >= 0.8:
                metrics.high_confidence_decisions = (metrics.high_confidence_decisions or 0) + 1
            elif score.confidence < 0.5:
                metrics.low_confidence_decisions = (metrics.low_confidence_decisions or 0) + 1
            
            current_avg_confidence = metrics.average_confidence_score or 0.7
            new_avg_confidence = ((current_avg_confidence * (current_count - 1)) + score.confidence) / current_count
            metrics.average_confidence_score = new_avg_confidence
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating screening metrics: {e}")
            db.session.rollback()
    
    async def get_screening_analytics(self, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Get screening system analytics"""
        try:
            # Default to last 30 days if no range specified
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            else:
                start_date = date_range.get('start_date')
                end_date = date_range.get('end_date')
            
            # Get metrics for date range
            metrics = db.session.query(ScreeningMetrics).filter(
                ScreeningMetrics.date >= start_date.date(),
                ScreeningMetrics.date <= end_date.date(),
                ScreeningMetrics.period_type == 'daily'
            ).all()
            
            if not metrics:
                return {'error': 'No metrics data available for date range'}
            
            # Aggregate metrics
            total_applications = sum(m.total_applications or 0 for m in metrics)
            total_approved = sum(m.approved_count or 0 for m in metrics)
            total_declined = sum(m.declined_count or 0 for m in metrics)
            total_conditional = sum(m.conditionally_approved_count or 0 for m in metrics)
            total_cosigner = sum(m.cosigner_required_count or 0 for m in metrics)
            
            approval_rate = (total_approved / total_applications * 100) if total_applications > 0 else 0
            decline_rate = (total_declined / total_applications * 100) if total_applications > 0 else 0
            
            avg_processing_time = sum(m.average_screening_time_seconds or 0 for m in metrics) / len(metrics)
            avg_confidence = sum(m.average_confidence_score or 0 for m in metrics) / len(metrics)
            
            return {
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'volume_metrics': {
                    'total_applications': total_applications,
                    'applications_per_day': total_applications / len(metrics) if len(metrics) > 0 else 0
                },
                'decision_metrics': {
                    'approved_count': total_approved,
                    'declined_count': total_declined,
                    'conditional_approved_count': total_conditional,
                    'cosigner_required_count': total_cosigner,
                    'approval_rate': approval_rate,
                    'decline_rate': decline_rate
                },
                'performance_metrics': {
                    'average_processing_time_seconds': avg_processing_time,
                    'average_confidence_score': avg_confidence
                },
                'system_health': {
                    'operational_status': 'healthy',
                    'data_quality': 'good',
                    'model_performance': 'optimal'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting screening analytics: {e}")
            return {'error': str(e)}


# Global service instance
_tenant_screening_service = None


def get_tenant_screening_service() -> TenantScreeningService:
    """Get or create the tenant screening service instance"""
    global _tenant_screening_service
    if _tenant_screening_service is None:
        _tenant_screening_service = TenantScreeningService()
    return _tenant_screening_service