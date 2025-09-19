"""
Tenant Screening Service for EstateCore
Comprehensive tenant background checks, credit scoring, and application processing
"""

import os
import logging
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApplicationStatus(Enum):
    """Tenant application status"""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    BACKGROUND_CHECK = "background_check"
    CREDIT_CHECK = "credit_check"
    REFERENCES_CHECK = "references_check"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class ScreeningType(Enum):
    """Types of screening checks"""
    CREDIT_CHECK = "credit_check"
    BACKGROUND_CHECK = "background_check"
    EVICTION_HISTORY = "eviction_history"
    EMPLOYMENT_VERIFICATION = "employment_verification"
    INCOME_VERIFICATION = "income_verification"
    REFERENCE_CHECK = "reference_check"
    RENTAL_HISTORY = "rental_history"

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class DecisionStatus(Enum):
    """Screening decision status"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"
    PENDING = "pending"

@dataclass
class TenantApplication:
    """Tenant rental application"""
    id: str
    property_id: int
    unit_id: Optional[str]
    submitted_at: datetime
    status: ApplicationStatus
    personal_info: Dict
    employment_info: Dict
    rental_history: List[Dict]
    references: List[Dict]
    emergency_contacts: List[Dict]
    documents: List[str] = field(default_factory=list)
    screening_results: Dict = field(default_factory=dict)
    decision_notes: str = ""
    lease_terms: Dict = field(default_factory=dict)
    application_fee_paid: bool = False
    security_deposit_paid: bool = False
    is_complete: bool = False
    metadata: Dict = field(default_factory=dict)

@dataclass
class ScreeningCheck:
    """Individual screening check result"""
    id: str
    application_id: str
    check_type: ScreeningType
    status: DecisionStatus
    score: Optional[float]
    details: Dict
    provider: str
    completed_at: Optional[datetime]
    notes: str = ""
    cost: float = 0.0

@dataclass
class CreditReport:
    """Credit report details"""
    score: int
    report_date: datetime
    tradelines: List[Dict] = field(default_factory=list)
    public_records: List[Dict] = field(default_factory=list)
    inquiries: List[Dict] = field(default_factory=list)
    payment_history: Dict = field(default_factory=dict)
    debt_to_income_ratio: Optional[float] = None
    available_credit: float = 0.0
    total_debt: float = 0.0

@dataclass
class BackgroundCheck:
    """Background check results"""
    criminal_history: List[Dict] = field(default_factory=list)
    eviction_history: List[Dict] = field(default_factory=list)
    civil_judgments: List[Dict] = field(default_factory=list)
    sex_offender_registry: bool = False
    identity_verification: bool = False
    ssn_verification: bool = False
    address_history: List[Dict] = field(default_factory=list)

@dataclass
class ReferenceCheck:
    """Reference verification results"""
    id: str
    application_id: str
    reference_type: str  # landlord, employer, personal
    contact_name: str
    contact_phone: str
    contact_email: str
    verification_status: str
    verification_date: Optional[datetime]
    responses: Dict = field(default_factory=dict)
    notes: str = ""
    recommendation_score: int = 0  # 1-10 scale

@dataclass
class ScreeningCriteria:
    """Screening criteria and thresholds"""
    min_credit_score: int = 650
    max_debt_to_income_ratio: float = 0.4
    min_income_multiplier: float = 3.0  # Monthly rent multiplier
    require_employment_verification: bool = True
    require_rental_history: bool = True
    max_evictions_allowed: int = 0
    max_criminal_convictions: int = 0
    require_references: int = 2
    background_check_years: int = 7
    credit_check_required: bool = True

@dataclass
class ScoringModel:
    """Tenant scoring model weights"""
    credit_score_weight: float = 0.30
    income_weight: float = 0.25
    rental_history_weight: float = 0.20
    employment_weight: float = 0.15
    references_weight: float = 0.10
    max_score: int = 1000

class TenantScreeningService:
    def __init__(self):
        """Initialize tenant screening service"""
        self.api_keys = {
            'credit_bureau': os.getenv('CREDIT_BUREAU_API_KEY', ''),
            'background_check': os.getenv('BACKGROUND_CHECK_API_KEY', ''),
            'employment_verification': os.getenv('EMPLOYMENT_VERIFICATION_API_KEY', '')
        }
        
        # Email configuration
        self.email_server = os.getenv('EMAIL_SERVER', 'smtp.gmail.com')
        self.email_port = int(os.getenv('EMAIL_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        # In-memory storage for demonstration (would use database in production)
        self.applications = {}
        self.screening_checks = {}
        self.reference_checks = {}
        self.screening_criteria = ScreeningCriteria()
        self.scoring_model = ScoringModel()
        
        # Initialize with sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample screening data"""
        # Sample application
        sample_app = TenantApplication(
            id="app_001",
            property_id=1,
            unit_id="unit_101",
            submitted_at=datetime.utcnow() - timedelta(days=2),
            status=ApplicationStatus.UNDER_REVIEW,
            personal_info={
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@email.com',
                'phone': '555-1234',
                'ssn': '***-**-1234',
                'date_of_birth': '1990-01-15',
                'current_address': '123 Current St, City, State 12345'
            },
            employment_info={
                'employer': 'Tech Corp',
                'position': 'Software Engineer',
                'annual_income': 75000,
                'employment_start_date': '2020-01-01',
                'supervisor_name': 'Jane Smith',
                'supervisor_phone': '555-5678'
            },
            rental_history=[
                {
                    'address': '456 Previous St, City, State',
                    'landlord_name': 'Bob Property Manager',
                    'landlord_phone': '555-9999',
                    'monthly_rent': 1200,
                    'lease_start': '2020-06-01',
                    'lease_end': '2023-05-31',
                    'reason_for_leaving': 'Moving for larger space'
                }
            ],
            references=[
                {
                    'name': 'Alice Johnson',
                    'relationship': 'Previous Landlord',
                    'phone': '555-1111',
                    'email': 'alice@property.com'
                },
                {
                    'name': 'Bob Wilson',
                    'relationship': 'Supervisor',
                    'phone': '555-2222',
                    'email': 'bob@techcorp.com'
                }
            ],
            emergency_contacts=[
                {
                    'name': 'Mary Doe',
                    'relationship': 'Mother',
                    'phone': '555-3333',
                    'email': 'mary@email.com'
                }
            ],
            application_fee_paid=True,
            is_complete=True
        )
        
        self.applications[sample_app.id] = sample_app
        logger.info("Sample tenant screening data initialized")
    
    def submit_application(self, property_id: int, personal_info: Dict, 
                          employment_info: Dict, **kwargs) -> Dict:
        """Submit a new tenant application"""
        try:
            app_id = str(uuid.uuid4())
            
            application = TenantApplication(
                id=app_id,
                property_id=property_id,
                submitted_at=datetime.utcnow(),
                status=ApplicationStatus.SUBMITTED,
                personal_info=personal_info,
                employment_info=employment_info,
                unit_id=kwargs.get('unit_id'),
                rental_history=kwargs.get('rental_history', []),
                references=kwargs.get('references', []),
                emergency_contacts=kwargs.get('emergency_contacts', []),
                lease_terms=kwargs.get('lease_terms', {}),
                application_fee_paid=kwargs.get('application_fee_paid', False)
            )
            
            # Validate application completeness
            application.is_complete = self._validate_application_completeness(application)
            
            self.applications[app_id] = application
            
            # Send confirmation email
            self._send_application_confirmation(application)
            
            # Auto-start screening if application is complete and fee is paid
            if application.is_complete and application.application_fee_paid:
                self._start_automated_screening(app_id)
            
            logger.info(f"Tenant application submitted: {app_id}")
            return {
                'success': True,
                'application_id': app_id,
                'status': application.status.value,
                'is_complete': application.is_complete
            }
            
        except Exception as e:
            logger.error(f"Failed to submit application: {e}")
            return {'success': False, 'error': str(e)}
    
    def _validate_application_completeness(self, application: TenantApplication) -> bool:
        """Validate if application has all required information"""
        try:
            required_personal_fields = ['first_name', 'last_name', 'email', 'phone', 'ssn', 'date_of_birth']
            required_employment_fields = ['employer', 'annual_income', 'employment_start_date']
            
            # Check personal info
            for field in required_personal_fields:
                if not application.personal_info.get(field):
                    return False
            
            # Check employment info
            for field in required_employment_fields:
                if not application.employment_info.get(field):
                    return False
            
            # Check if minimum references provided
            if len(application.references) < self.screening_criteria.require_references:
                return False
            
            # Check rental history requirement
            if self.screening_criteria.require_rental_history and not application.rental_history:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Application validation failed: {e}")
            return False
    
    def _start_automated_screening(self, application_id: str):
        """Start automated screening process"""
        try:
            application = self.applications.get(application_id)
            if not application:
                return
            
            application.status = ApplicationStatus.UNDER_REVIEW
            
            # Queue screening checks
            screening_tasks = [
                ScreeningType.CREDIT_CHECK,
                ScreeningType.BACKGROUND_CHECK,
                ScreeningType.EMPLOYMENT_VERIFICATION,
                ScreeningType.REFERENCE_CHECK
            ]
            
            for task in screening_tasks:
                self._queue_screening_check(application_id, task)
            
            logger.info(f"Automated screening started for application {application_id}")
            
        except Exception as e:
            logger.error(f"Failed to start automated screening: {e}")
    
    def _queue_screening_check(self, application_id: str, check_type: ScreeningType):
        """Queue a screening check for processing"""
        try:
            check_id = str(uuid.uuid4())
            
            screening_check = ScreeningCheck(
                id=check_id,
                application_id=application_id,
                check_type=check_type,
                status=DecisionStatus.PENDING,
                score=None,
                details={},
                provider="internal",
                completed_at=None
            )
            
            self.screening_checks[check_id] = screening_check
            
            # Simulate processing different types of checks
            if check_type == ScreeningType.CREDIT_CHECK:
                self._process_credit_check(check_id)
            elif check_type == ScreeningType.BACKGROUND_CHECK:
                self._process_background_check(check_id)
            elif check_type == ScreeningType.EMPLOYMENT_VERIFICATION:
                self._process_employment_verification(check_id)
            elif check_type == ScreeningType.REFERENCE_CHECK:
                self._process_reference_checks(check_id)
            
        except Exception as e:
            logger.error(f"Failed to queue screening check: {e}")
    
    def _process_credit_check(self, check_id: str):
        """Process credit check (simulated)"""
        try:
            check = self.screening_checks[check_id]
            application = self.applications[check.application_id]
            
            # Simulate credit check API call
            # In production, this would call actual credit bureau APIs
            simulated_credit_score = 720  # Mock score
            
            credit_report = CreditReport(
                score=simulated_credit_score,
                report_date=datetime.utcnow(),
                tradelines=[
                    {
                        'creditor': 'Credit Card Company',
                        'account_type': 'Credit Card',
                        'balance': 2500,
                        'limit': 10000,
                        'payment_status': 'Current'
                    }
                ],
                debt_to_income_ratio=0.25,
                total_debt=15000,
                available_credit=35000
            )
            
            # Evaluate against criteria
            if simulated_credit_score >= self.screening_criteria.min_credit_score:
                check.status = DecisionStatus.PASS
                check.score = simulated_credit_score
            elif simulated_credit_score >= self.screening_criteria.min_credit_score - 50:
                check.status = DecisionStatus.CONDITIONAL
                check.score = simulated_credit_score
                check.notes = "Credit score below preferred threshold but within acceptable range"
            else:
                check.status = DecisionStatus.FAIL
                check.score = simulated_credit_score
                check.notes = "Credit score below minimum requirement"
            
            check.details = {
                'credit_report': credit_report.__dict__,
                'meets_criteria': check.status in [DecisionStatus.PASS, DecisionStatus.CONDITIONAL]
            }
            check.completed_at = datetime.utcnow()
            check.cost = 25.00
            
            # Update application screening results
            application.screening_results['credit_check'] = {
                'status': check.status.value,
                'score': check.score,
                'completed_at': check.completed_at.isoformat()
            }
            
            logger.info(f"Credit check completed for application {check.application_id}: {check.status.value}")
            
        except Exception as e:
            logger.error(f"Credit check processing failed: {e}")
            check.status = DecisionStatus.FAIL
            check.notes = f"Processing error: {str(e)}"
    
    def _process_background_check(self, check_id: str):
        """Process background check (simulated)"""
        try:
            check = self.screening_checks[check_id]
            application = self.applications[check.application_id]
            
            # Simulate background check API call
            background_report = BackgroundCheck(
                criminal_history=[],  # Clean record
                eviction_history=[],  # No evictions
                civil_judgments=[],
                sex_offender_registry=False,
                identity_verification=True,
                ssn_verification=True,
                address_history=[
                    {
                        'address': '123 Previous St, City, State',
                        'from_date': '2020-01-01',
                        'to_date': '2023-12-31'
                    }
                ]
            )
            
            # Evaluate results
            has_disqualifying_records = (
                len(background_report.criminal_history) > self.screening_criteria.max_criminal_convictions or
                len(background_report.eviction_history) > self.screening_criteria.max_evictions_allowed or
                background_report.sex_offender_registry
            )
            
            if not has_disqualifying_records and background_report.identity_verification:
                check.status = DecisionStatus.PASS
                check.score = 100.0
            elif not has_disqualifying_records:
                check.status = DecisionStatus.CONDITIONAL
                check.score = 75.0
                check.notes = "Identity verification incomplete"
            else:
                check.status = DecisionStatus.FAIL
                check.score = 0.0
                check.notes = "Disqualifying records found"
            
            check.details = {
                'background_report': background_report.__dict__,
                'meets_criteria': check.status in [DecisionStatus.PASS, DecisionStatus.CONDITIONAL]
            }
            check.completed_at = datetime.utcnow()
            check.cost = 35.00
            
            # Update application screening results
            application.screening_results['background_check'] = {
                'status': check.status.value,
                'score': check.score,
                'completed_at': check.completed_at.isoformat()
            }
            
            logger.info(f"Background check completed for application {check.application_id}: {check.status.value}")
            
        except Exception as e:
            logger.error(f"Background check processing failed: {e}")
            check.status = DecisionStatus.FAIL
            check.notes = f"Processing error: {str(e)}"
    
    def _process_employment_verification(self, check_id: str):
        """Process employment verification (simulated)"""
        try:
            check = self.screening_checks[check_id]
            application = self.applications[check.application_id]
            
            employment_info = application.employment_info
            annual_income = employment_info.get('annual_income', 0)
            
            # Simulate employment verification
            # In production, this would contact employers or use verification services
            verification_result = {
                'employment_verified': True,
                'income_verified': True,
                'position_verified': True,
                'start_date_verified': True,
                'supervisor_contacted': True
            }
            
            # Calculate income requirements (assume we have monthly rent)
            estimated_monthly_rent = 1500  # This would come from property/unit data
            required_monthly_income = estimated_monthly_rent * self.screening_criteria.min_income_multiplier
            monthly_income = annual_income / 12
            
            meets_income_requirement = monthly_income >= required_monthly_income
            
            if verification_result['employment_verified'] and meets_income_requirement:
                check.status = DecisionStatus.PASS
                check.score = 100.0
            elif verification_result['employment_verified']:
                check.status = DecisionStatus.CONDITIONAL
                check.score = 70.0
                check.notes = "Employment verified but income below preferred threshold"
            else:
                check.status = DecisionStatus.FAIL
                check.score = 0.0
                check.notes = "Unable to verify employment"
            
            check.details = {
                'verification_result': verification_result,
                'income_analysis': {
                    'annual_income': annual_income,
                    'monthly_income': monthly_income,
                    'required_monthly_income': required_monthly_income,
                    'meets_requirement': meets_income_requirement
                },
                'meets_criteria': check.status in [DecisionStatus.PASS, DecisionStatus.CONDITIONAL]
            }
            check.completed_at = datetime.utcnow()
            check.cost = 15.00
            
            # Update application screening results
            application.screening_results['employment_verification'] = {
                'status': check.status.value,
                'score': check.score,
                'completed_at': check.completed_at.isoformat()
            }
            
            logger.info(f"Employment verification completed for application {check.application_id}: {check.status.value}")
            
        except Exception as e:
            logger.error(f"Employment verification failed: {e}")
            check.status = DecisionStatus.FAIL
            check.notes = f"Processing error: {str(e)}"
    
    def _process_reference_checks(self, check_id: str):
        """Process reference checks (simulated)"""
        try:
            check = self.screening_checks[check_id]
            application = self.applications[check.application_id]
            
            reference_results = []
            total_score = 0
            
            for ref in application.references:
                ref_check_id = str(uuid.uuid4())
                
                # Simulate contacting references
                reference_check = ReferenceCheck(
                    id=ref_check_id,
                    application_id=check.application_id,
                    reference_type=ref.get('relationship', 'personal').lower(),
                    contact_name=ref.get('name', ''),
                    contact_phone=ref.get('phone', ''),
                    contact_email=ref.get('email', ''),
                    verification_status='verified',
                    verification_date=datetime.utcnow(),
                    responses={
                        'would_rent_again': True,
                        'paid_on_time': True,
                        'property_care': 'excellent',
                        'noise_complaints': False,
                        'lease_violations': False,
                        'recommendation': 'highly_recommended'
                    },
                    recommendation_score=9  # 1-10 scale
                )
                
                self.reference_checks[ref_check_id] = reference_check
                reference_results.append(reference_check.__dict__)
                total_score += reference_check.recommendation_score
            
            # Calculate overall reference score
            avg_score = total_score / len(application.references) if application.references else 0
            
            if avg_score >= 8:
                check.status = DecisionStatus.PASS
                check.score = avg_score * 10  # Convert to 100-point scale
            elif avg_score >= 6:
                check.status = DecisionStatus.CONDITIONAL
                check.score = avg_score * 10
                check.notes = "Mixed references, some concerns noted"
            else:
                check.status = DecisionStatus.FAIL
                check.score = avg_score * 10
                check.notes = "Poor references, multiple concerns"
            
            check.details = {
                'reference_results': reference_results,
                'average_score': avg_score,
                'total_references': len(application.references),
                'meets_criteria': check.status in [DecisionStatus.PASS, DecisionStatus.CONDITIONAL]
            }
            check.completed_at = datetime.utcnow()
            check.cost = 10.00 * len(application.references)
            
            # Update application screening results
            application.screening_results['reference_check'] = {
                'status': check.status.value,
                'score': check.score,
                'completed_at': check.completed_at.isoformat()
            }
            
            logger.info(f"Reference checks completed for application {check.application_id}: {check.status.value}")
            
        except Exception as e:
            logger.error(f"Reference check processing failed: {e}")
            check.status = DecisionStatus.FAIL
            check.notes = f"Processing error: {str(e)}"
    
    def calculate_overall_score(self, application_id: str) -> Dict:
        """Calculate overall tenant score based on all screening results"""
        try:
            application = self.applications.get(application_id)
            if not application:
                return {'success': False, 'error': 'Application not found'}
            
            # Get completed screening checks
            app_checks = [check for check in self.screening_checks.values() 
                         if check.application_id == application_id and check.completed_at]
            
            if not app_checks:
                return {'success': False, 'error': 'No completed screening checks'}
            
            # Calculate weighted score
            total_score = 0
            max_possible_score = 0
            
            scoring_weights = {
                ScreeningType.CREDIT_CHECK: self.scoring_model.credit_score_weight,
                ScreeningType.BACKGROUND_CHECK: self.scoring_model.income_weight,
                ScreeningType.EMPLOYMENT_VERIFICATION: self.scoring_model.employment_weight,
                ScreeningType.REFERENCE_CHECK: self.scoring_model.references_weight
            }
            
            for check in app_checks:
                weight = scoring_weights.get(check.check_type, 0)
                if weight > 0 and check.score is not None:
                    # Normalize score to 100-point scale
                    normalized_score = min(100, max(0, check.score))
                    weighted_score = normalized_score * weight
                    total_score += weighted_score
                    max_possible_score += 100 * weight
            
            # Calculate final score out of max possible
            if max_possible_score > 0:
                final_score = (total_score / max_possible_score) * self.scoring_model.max_score
            else:
                final_score = 0
            
            # Determine risk level
            if final_score >= 800:
                risk_level = RiskLevel.LOW
            elif final_score >= 650:
                risk_level = RiskLevel.MEDIUM
            elif final_score >= 500:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.VERY_HIGH
            
            # Generate recommendation
            recommendation = self._generate_recommendation(application_id, final_score, app_checks)
            
            score_breakdown = {
                'overall_score': round(final_score, 1),
                'risk_level': risk_level.value,
                'max_possible_score': self.scoring_model.max_score,
                'component_scores': {
                    check.check_type.value: {
                        'score': check.score,
                        'status': check.status.value,
                        'weight': scoring_weights.get(check.check_type, 0)
                    } for check in app_checks
                },
                'recommendation': recommendation
            }
            
            # Update application with final score
            application.screening_results['overall_score'] = score_breakdown
            
            return {
                'success': True,
                'score_breakdown': score_breakdown
            }
            
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_recommendation(self, application_id: str, score: float, 
                               checks: List[ScreeningCheck]) -> Dict:
        """Generate approval recommendation based on screening results"""
        try:
            # Count pass/fail/conditional results
            pass_count = len([c for c in checks if c.status == DecisionStatus.PASS])
            fail_count = len([c for c in checks if c.status == DecisionStatus.FAIL])
            conditional_count = len([c for c in checks if c.status == DecisionStatus.CONDITIONAL])
            
            # Determine recommendation
            if fail_count > 0:
                recommendation = ApplicationStatus.REJECTED
                reason = "One or more screening checks failed"
            elif score >= 750 and pass_count >= 3:
                recommendation = ApplicationStatus.APPROVED
                reason = "Excellent screening results across all categories"
            elif score >= 650 and conditional_count <= 1:
                recommendation = ApplicationStatus.CONDITIONALLY_APPROVED
                reason = "Good screening results with minor concerns"
            elif score >= 500:
                recommendation = ApplicationStatus.CONDITIONALLY_APPROVED
                reason = "Acceptable screening results requiring additional review"
            else:
                recommendation = ApplicationStatus.REJECTED
                reason = "Screening results below acceptable threshold"
            
            # Generate conditions if conditionally approved
            conditions = []
            if recommendation == ApplicationStatus.CONDITIONALLY_APPROVED:
                if any(c.check_type == ScreeningType.CREDIT_CHECK and c.status == DecisionStatus.CONDITIONAL 
                       for c in checks):
                    conditions.append("Increased security deposit required")
                if any(c.check_type == ScreeningType.EMPLOYMENT_VERIFICATION and c.status == DecisionStatus.CONDITIONAL 
                       for c in checks):
                    conditions.append("Guarantor or co-signer required")
                if any(c.check_type == ScreeningType.REFERENCE_CHECK and c.status == DecisionStatus.CONDITIONAL 
                       for c in checks):
                    conditions.append("Additional rental references required")
            
            return {
                'status': recommendation.value,
                'reason': reason,
                'conditions': conditions,
                'score': score,
                'checks_summary': {
                    'pass': pass_count,
                    'conditional': conditional_count,
                    'fail': fail_count,
                    'total': len(checks)
                }
            }
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {
                'status': ApplicationStatus.REJECTED.value,
                'reason': f"Error generating recommendation: {str(e)}",
                'conditions': [],
                'score': 0
            }
    
    def approve_application(self, application_id: str, decision: ApplicationStatus, 
                          notes: str = "", conditions: List[str] = None) -> Dict:
        """Approve or reject an application"""
        try:
            application = self.applications.get(application_id)
            if not application:
                return {'success': False, 'error': 'Application not found'}
            
            application.status = decision
            application.decision_notes = notes
            
            if conditions:
                application.metadata['approval_conditions'] = conditions
            
            # Send decision notification
            self._send_decision_notification(application, decision, notes, conditions or [])
            
            logger.info(f"Application {application_id} decision: {decision.value}")
            return {
                'success': True,
                'application_id': application_id,
                'decision': decision.value,
                'notes': notes
            }
            
        except Exception as e:
            logger.error(f"Application decision failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_screening_dashboard_data(self) -> Dict:
        """Get screening dashboard data"""
        try:
            current_date = datetime.utcnow()
            last_30_days = current_date - timedelta(days=30)
            
            # Application statistics
            total_applications = len(self.applications)
            recent_applications = [app for app in self.applications.values() 
                                 if app.submitted_at > last_30_days]
            
            status_counts = {}
            for status in ApplicationStatus:
                status_counts[status.value] = len([app for app in self.applications.values() 
                                                 if app.status == status])
            
            # Screening statistics
            total_checks = len(self.screening_checks)
            completed_checks = len([check for check in self.screening_checks.values() 
                                  if check.completed_at])
            pending_checks = total_checks - completed_checks
            
            # Average processing time
            completed_apps = [app for app in self.applications.values() 
                            if app.status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED, 
                                            ApplicationStatus.CONDITIONALLY_APPROVED]]
            
            avg_processing_days = 0
            if completed_apps:
                total_processing_time = sum((datetime.utcnow() - app.submitted_at).days 
                                          for app in completed_apps)
                avg_processing_days = total_processing_time / len(completed_apps)
            
            # Revenue from screening fees
            total_screening_costs = sum(check.cost for check in self.screening_checks.values() 
                                      if check.completed_at)
            
            return {
                'success': True,
                'overview': {
                    'total_applications': total_applications,
                    'applications_30_days': len(recent_applications),
                    'pending_reviews': status_counts.get('under_review', 0) + 
                                     status_counts.get('background_check', 0) + 
                                     status_counts.get('credit_check', 0),
                    'completed_screenings': completed_checks,
                    'pending_checks': pending_checks,
                    'avg_processing_days': round(avg_processing_days, 1),
                    'screening_revenue': total_screening_costs
                },
                'status_breakdown': status_counts,
                'recent_applications': [
                    {
                        'id': app.id,
                        'applicant_name': f"{app.personal_info.get('first_name', '')} {app.personal_info.get('last_name', '')}",
                        'property_id': app.property_id,
                        'submitted_at': app.submitted_at.isoformat(),
                        'status': app.status.value,
                        'is_complete': app.is_complete
                    }
                    for app in sorted(recent_applications, key=lambda x: x.submitted_at, reverse=True)[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get screening dashboard data: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_application_confirmation(self, application: TenantApplication):
        """Send application confirmation email"""
        try:
            email = application.personal_info.get('email')
            if not email:
                return
            
            name = f"{application.personal_info.get('first_name', '')} {application.personal_info.get('last_name', '')}"
            subject = f"Rental Application Received - Application #{application.id[:8]}"
            
            body = f"""
            Dear {name},
            
            Thank you for submitting your rental application for Property #{application.property_id}.
            
            Application Details:
            - Application ID: {application.id}
            - Property: {application.property_id}
            - Unit: {application.unit_id or 'TBD'}
            - Submitted: {application.submitted_at.strftime('%Y-%m-%d %H:%M')}
            - Status: {application.status.value.replace('_', ' ').title()}
            
            Next Steps:
            {self._get_next_steps_text(application)}
            
            You can check your application status at any time by contacting our office.
            
            Best regards,
            Property Management Team
            """
            
            self._send_email(email, subject, body)
            logger.info(f"Application confirmation sent to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send application confirmation: {e}")
    
    def _send_decision_notification(self, application: TenantApplication, 
                                  decision: ApplicationStatus, notes: str, conditions: List[str]):
        """Send application decision notification"""
        try:
            email = application.personal_info.get('email')
            if not email:
                return
            
            name = f"{application.personal_info.get('first_name', '')} {application.personal_info.get('last_name', '')}"
            subject = f"Rental Application Decision - Application #{application.id[:8]}"
            
            decision_text = {
                ApplicationStatus.APPROVED: "APPROVED",
                ApplicationStatus.CONDITIONALLY_APPROVED: "CONDITIONALLY APPROVED",
                ApplicationStatus.REJECTED: "NOT APPROVED"
            }.get(decision, decision.value.upper())
            
            body = f"""
            Dear {name},
            
            We have completed the review of your rental application for Property #{application.property_id}.
            
            Application Decision: {decision_text}
            
            """
            
            if decision == ApplicationStatus.APPROVED:
                body += """
                Congratulations! Your application has been approved. Our leasing team will contact you within 
                24 hours to proceed with lease signing and move-in coordination.
                """
            elif decision == ApplicationStatus.CONDITIONALLY_APPROVED:
                body += f"""
                Your application has been conditionally approved subject to the following requirements:
                
                {chr(10).join(f"• {condition}" for condition in conditions)}
                
                Please contact our office to discuss next steps and fulfill the conditions.
                """
            else:
                body += f"""
                Unfortunately, we are unable to approve your application at this time.
                
                {notes if notes else 'Thank you for your interest in our property.'}
                """
            
            body += """
            
            If you have any questions about this decision, please don't hesitate to contact us.
            
            Best regards,
            Property Management Team
            """
            
            self._send_email(email, subject, body)
            logger.info(f"Decision notification sent to {email}: {decision.value}")
            
        except Exception as e:
            logger.error(f"Failed to send decision notification: {e}")
    
    def _get_next_steps_text(self, application: TenantApplication) -> str:
        """Generate next steps text for application confirmation"""
        if not application.is_complete:
            return "Please complete your application by providing all required information and documents."
        elif not application.application_fee_paid:
            return "Please submit the application fee to begin the screening process."
        else:
            return "Your application is complete and screening will begin shortly. We'll notify you of any updates."
    
    def _send_email(self, to_email: str, subject: str, body: str):
        """Send email notification"""
        try:
            if not self.email_username or not self.email_password:
                logger.info(f"Email simulation: {subject} to {to_email}")
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_server, self.email_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_username, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

# Singleton instance
_screening_service = None

def get_tenant_screening_service() -> TenantScreeningService:
    """Get singleton tenant screening service instance"""
    global _screening_service
    if _screening_service is None:
        _screening_service = TenantScreeningService()
    return _screening_service

if __name__ == "__main__":
    # Test the tenant screening service
    service = get_tenant_screening_service()
    
    print("🔍 Tenant Screening Service Test")
    
    # Test application submission
    app_result = service.submit_application(
        property_id=1,
        personal_info={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@email.com',
            'phone': '555-4567',
            'ssn': '123-45-6789',
            'date_of_birth': '1985-03-20',
            'current_address': '789 Current Ave, City, State 54321'
        },
        employment_info={
            'employer': 'Design Studio',
            'position': 'Graphic Designer',
            'annual_income': 65000,
            'employment_start_date': '2019-06-01'
        },
        unit_id='unit_201',
        rental_history=[
            {
                'address': '321 Old St, City, State',
                'landlord_name': 'Property LLC',
                'landlord_phone': '555-7777',
                'monthly_rent': 1100,
                'lease_start': '2019-08-01',
                'lease_end': '2023-07-31'
            }
        ],
        references=[
            {
                'name': 'Tom Manager',
                'relationship': 'Previous Landlord',
                'phone': '555-8888',
                'email': 'tom@property.com'
            },
            {
                'name': 'Sarah Boss',
                'relationship': 'Supervisor',
                'phone': '555-9999',
                'email': 'sarah@designstudio.com'
            }
        ],
        application_fee_paid=True
    )
    print(f"Application submission: {app_result.get('success', False)}")
    
    # Test score calculation
    if app_result.get('success'):
        app_id = app_result['application_id']
        # Wait a moment for simulated screening to complete
        time.sleep(1)
        
        score_result = service.calculate_overall_score(app_id)
        print(f"Score calculation: {score_result.get('success', False)}")
        
        if score_result.get('success'):
            score = score_result['score_breakdown']['overall_score']
            print(f"Overall score: {score}/1000")
    
    # Test dashboard data
    dashboard = service.get_screening_dashboard_data()
    print(f"Dashboard data: {dashboard.get('success', False)}")
    
    print("✅ Tenant screening service is ready!")