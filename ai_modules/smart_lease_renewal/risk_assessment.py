"""
Tenant Risk Assessment and Scoring System
Comprehensive risk analysis for lease renewal decisions
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import statistics
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RiskCategory(Enum):
    """Risk category types"""
    PAYMENT_RISK = "payment_risk"
    PROPERTY_RISK = "property_risk"
    BEHAVIORAL_RISK = "behavioral_risk"
    FINANCIAL_RISK = "financial_risk"
    COMPLIANCE_RISK = "compliance_risk"
    MARKET_RISK = "market_risk"

class TenantSegment(Enum):
    """Tenant segmentation"""
    PREMIUM = "premium"
    STABLE = "stable"
    STANDARD = "standard"
    CAUTION = "caution"
    HIGH_RISK = "high_risk"

@dataclass
class RiskFactor:
    """Individual risk factor"""
    factor_id: str
    category: RiskCategory
    description: str
    severity: RiskLevel
    score: float  # 0-100, higher is riskier
    weight: float  # Importance weight 0-1
    evidence: List[str]
    recommendations: List[str]
    trend: str  # improving, stable, deteriorating
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TenantRiskProfile:
    """Comprehensive tenant risk profile"""
    tenant_id: str
    overall_risk_score: float  # 0-100
    risk_level: RiskLevel
    tenant_segment: TenantSegment
    confidence_score: float
    risk_factors: List[RiskFactor]
    category_scores: Dict[str, float]
    trend_analysis: Dict[str, Any]
    comparative_analysis: Dict[str, Any]
    early_warning_indicators: List[str]
    mitigation_strategies: List[str]
    monitoring_recommendations: List[str]
    assessment_timestamp: datetime
    next_review_date: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

@dataclass
class RiskMetrics:
    """Risk assessment metrics"""
    payment_reliability_score: float
    financial_stability_score: float
    behavioral_score: float
    property_care_score: float
    compliance_score: float
    communication_score: float
    longevity_score: float
    market_risk_score: float
    
class TenantRiskAssessment:
    """
    Advanced tenant risk assessment and scoring system
    """
    
    def __init__(self):
        # Risk assessment models
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.risk_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        # Risk scoring weights by category
        self.category_weights = {
            RiskCategory.PAYMENT_RISK: 0.30,
            RiskCategory.FINANCIAL_RISK: 0.20,
            RiskCategory.BEHAVIORAL_RISK: 0.15,
            RiskCategory.PROPERTY_RISK: 0.15,
            RiskCategory.COMPLIANCE_RISK: 0.10,
            RiskCategory.MARKET_RISK: 0.10
        }
        
        # Risk factor definitions
        self.risk_factor_definitions = self._initialize_risk_factors()
        
        # Tenant benchmarks
        self.tenant_benchmarks = {
            'payment_reliability': {'excellent': 98, 'good': 95, 'fair': 90, 'poor': 85},
            'financial_stability': {'excellent': 90, 'good': 80, 'fair': 70, 'poor': 60},
            'property_care': {'excellent': 95, 'good': 85, 'fair': 75, 'poor': 65}
        }
        
        # Historical data for trend analysis
        self.historical_assessments = {}
        
        # Early warning system thresholds
        self.warning_thresholds = {
            'payment_decline': 0.15,  # 15% decline in payment score
            'financial_stress': 0.70,  # DTI ratio above 70%
            'complaint_spike': 3,      # More than 3 complaints in 30 days
            'maintenance_neglect': 5   # More than 5 overdue maintenance items
        }
        
    def assess_tenant_risk(self, 
                          tenant_data: Dict[str, Any],
                          lease_data: Dict[str, Any],
                          property_data: Dict[str, Any],
                          market_data: Dict[str, Any] = None,
                          historical_data: Dict[str, Any] = None) -> TenantRiskProfile:
        """
        Conduct comprehensive tenant risk assessment
        """
        try:
            logger.info(f"Starting risk assessment for tenant {tenant_data.get('tenant_id')}")
            
            # Calculate detailed risk metrics
            risk_metrics = self._calculate_risk_metrics(
                tenant_data, lease_data, property_data, market_data
            )
            
            # Identify individual risk factors
            risk_factors = self._identify_risk_factors(
                tenant_data, lease_data, property_data, risk_metrics
            )
            
            # Calculate category scores
            category_scores = self._calculate_category_scores(risk_factors)
            
            # Calculate overall risk score
            overall_score = self._calculate_overall_risk_score(category_scores)
            
            # Determine risk level and tenant segment
            risk_level = self._determine_risk_level(overall_score)
            tenant_segment = self._determine_tenant_segment(overall_score, risk_factors)
            
            # Perform trend analysis
            trend_analysis = self._analyze_risk_trends(
                tenant_data.get('tenant_id', ''), historical_data
            )
            
            # Comparative analysis against portfolio
            comparative_analysis = self._perform_comparative_analysis(
                overall_score, category_scores, risk_metrics
            )
            
            # Early warning indicators
            early_warnings = self._detect_early_warning_indicators(
                tenant_data, lease_data, risk_metrics, trend_analysis
            )
            
            # Generate mitigation strategies
            mitigation_strategies = self._generate_mitigation_strategies(
                risk_factors, early_warnings, tenant_segment
            )
            
            # Monitoring recommendations
            monitoring_recs = self._generate_monitoring_recommendations(
                risk_level, risk_factors, early_warnings
            )
            
            # Calculate confidence score
            confidence = self._calculate_assessment_confidence(
                tenant_data, lease_data, historical_data
            )
            
            # Create risk profile
            risk_profile = TenantRiskProfile(
                tenant_id=tenant_data.get('tenant_id', ''),
                overall_risk_score=round(overall_score, 2),
                risk_level=risk_level,
                tenant_segment=tenant_segment,
                confidence_score=round(confidence, 2),
                risk_factors=risk_factors,
                category_scores={cat.value: round(score, 2) for cat, score in category_scores.items()},
                trend_analysis=trend_analysis,
                comparative_analysis=comparative_analysis,
                early_warning_indicators=early_warnings,
                mitigation_strategies=mitigation_strategies,
                monitoring_recommendations=monitoring_recs,
                assessment_timestamp=datetime.now(),
                next_review_date=self._calculate_next_review_date(risk_level)
            )
            
            # Store assessment for future trend analysis
            self._store_assessment_history(risk_profile)
            
            logger.info(f"Risk assessment completed for tenant {tenant_data.get('tenant_id')}")
            return risk_profile
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {str(e)}")
            return self._get_fallback_risk_profile(tenant_data)
    
    def batch_assess_portfolio_risk(self, 
                                  portfolio_tenants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess risk across entire tenant portfolio
        """
        assessments = []
        portfolio_metrics = {
            'total_tenants': len(portfolio_tenants),
            'risk_distribution': {level.value: 0 for level in RiskLevel},
            'segment_distribution': {seg.value: 0 for seg in TenantSegment},
            'average_risk_score': 0,
            'high_risk_count': 0,
            'early_warning_count': 0,
            'portfolio_risk_score': 0
        }
        
        total_risk_score = 0
        
        for tenant_package in portfolio_tenants:
            try:
                assessment = self.assess_tenant_risk(
                    tenant_package.get('tenant_data', {}),
                    tenant_package.get('lease_data', {}),
                    tenant_package.get('property_data', {}),
                    tenant_package.get('market_data', {}),
                    tenant_package.get('historical_data', {})
                )
                
                assessments.append(assessment.to_dict())
                
                # Update portfolio metrics
                portfolio_metrics['risk_distribution'][assessment.risk_level.value] += 1
                portfolio_metrics['segment_distribution'][assessment.tenant_segment.value] += 1
                total_risk_score += assessment.overall_risk_score
                
                if assessment.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                    portfolio_metrics['high_risk_count'] += 1
                
                if assessment.early_warning_indicators:
                    portfolio_metrics['early_warning_count'] += 1
                    
            except Exception as e:
                logger.error(f"Error assessing tenant {tenant_package.get('tenant_data', {}).get('tenant_id', 'unknown')}: {str(e)}")
                continue
        
        # Calculate portfolio-wide metrics
        if len(assessments) > 0:
            portfolio_metrics['average_risk_score'] = round(total_risk_score / len(assessments), 2)
            portfolio_metrics['portfolio_risk_score'] = self._calculate_portfolio_risk_score(assessments)
        
        # Generate portfolio insights
        portfolio_insights = self._generate_portfolio_risk_insights(assessments, portfolio_metrics)
        
        # Risk correlation analysis
        correlation_analysis = self._analyze_risk_correlations(assessments)
        
        return {
            'portfolio_metrics': portfolio_metrics,
            'individual_assessments': assessments,
            'portfolio_insights': portfolio_insights,
            'correlation_analysis': correlation_analysis,
            'recommended_actions': self._generate_portfolio_risk_actions(portfolio_metrics, assessments),
            'assessment_timestamp': datetime.now().isoformat()
        }
    
    def monitor_risk_changes(self, 
                           tenant_id: str,
                           new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor and alert on significant risk changes
        """
        try:
            # Get previous assessment
            previous_assessment = self.historical_assessments.get(tenant_id, {}).get('latest')
            
            if not previous_assessment:
                return {'status': 'no_baseline', 'message': 'No previous assessment for comparison'}
            
            # Conduct new assessment
            new_assessment = self.assess_tenant_risk(
                new_data.get('tenant_data', {}),
                new_data.get('lease_data', {}),
                new_data.get('property_data', {}),
                new_data.get('market_data', {})
            )
            
            # Compare assessments
            risk_change = new_assessment.overall_risk_score - previous_assessment['overall_risk_score']
            level_change = new_assessment.risk_level.value != previous_assessment['risk_level']
            
            # Identify significant changes
            significant_changes = []
            alerts = []
            
            if abs(risk_change) >= 10:  # 10+ point change
                significant_changes.append({
                    'type': 'overall_risk_score',
                    'change': round(risk_change, 2),
                    'direction': 'increased' if risk_change > 0 else 'decreased'
                })
                
                if risk_change > 15:  # Major increase
                    alerts.append({
                        'level': 'high',
                        'message': f'Significant risk increase: +{risk_change:.1f} points'
                    })
            
            if level_change:
                significant_changes.append({
                    'type': 'risk_level',
                    'from': previous_assessment['risk_level'],
                    'to': new_assessment.risk_level.value
                })
                
                alerts.append({
                    'level': 'medium',
                    'message': f'Risk level changed from {previous_assessment["risk_level"]} to {new_assessment.risk_level.value}'
                })
            
            # Check for new early warning indicators
            new_warnings = set(new_assessment.early_warning_indicators) - set(previous_assessment.get('early_warning_indicators', []))
            if new_warnings:
                alerts.append({
                    'level': 'medium',
                    'message': f'New early warning indicators: {", ".join(new_warnings)}'
                })
            
            return {
                'tenant_id': tenant_id,
                'monitoring_status': 'completed',
                'risk_change': round(risk_change, 2),
                'level_changed': level_change,
                'significant_changes': significant_changes,
                'alerts': alerts,
                'new_assessment': new_assessment.to_dict(),
                'previous_assessment': previous_assessment,
                'monitoring_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring risk changes for tenant {tenant_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_risk_report(self, 
                           tenant_id: str,
                           report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate detailed risk assessment report
        """
        try:
            # Get latest assessment
            latest_assessment = self.historical_assessments.get(tenant_id, {}).get('latest')
            
            if not latest_assessment:
                return {'status': 'no_data', 'message': 'No assessment data available'}
            
            # Get assessment history
            assessment_history = self.historical_assessments.get(tenant_id, {}).get('history', [])
            
            if report_type == "comprehensive":
                return self._generate_comprehensive_report(latest_assessment, assessment_history)
            elif report_type == "executive_summary":
                return self._generate_executive_summary(latest_assessment)
            elif report_type == "trend_analysis":
                return self._generate_trend_report(assessment_history)
            else:
                return self._generate_standard_report(latest_assessment)
                
        except Exception as e:
            logger.error(f"Error generating risk report: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    # Private methods for risk calculation and analysis
    
    def _calculate_risk_metrics(self, 
                              tenant_data: Dict[str, Any],
                              lease_data: Dict[str, Any],
                              property_data: Dict[str, Any],
                              market_data: Dict[str, Any] = None) -> RiskMetrics:
        """
        Calculate detailed risk metrics across all categories
        """
        # Payment reliability metrics
        payment_score = self._calculate_payment_reliability_score(tenant_data)
        
        # Financial stability metrics
        financial_score = self._calculate_financial_stability_score(tenant_data, lease_data)
        
        # Behavioral risk metrics
        behavioral_score = self._calculate_behavioral_score(tenant_data)
        
        # Property care metrics
        property_care_score = self._calculate_property_care_score(tenant_data, property_data)
        
        # Compliance metrics
        compliance_score = self._calculate_compliance_score(tenant_data, lease_data)
        
        # Communication metrics
        communication_score = self._calculate_communication_score(tenant_data)
        
        # Longevity/retention metrics
        longevity_score = self._calculate_longevity_score(tenant_data, lease_data)
        
        # Market risk metrics
        market_risk_score = self._calculate_market_risk_score(market_data or {})
        
        return RiskMetrics(
            payment_reliability_score=payment_score,
            financial_stability_score=financial_score,
            behavioral_score=behavioral_score,
            property_care_score=property_care_score,
            compliance_score=compliance_score,
            communication_score=communication_score,
            longevity_score=longevity_score,
            market_risk_score=market_risk_score
        )
    
    def _calculate_payment_reliability_score(self, tenant_data: Dict[str, Any]) -> float:
        """
        Calculate payment reliability score (0-100, lower is riskier)
        """
        score = 100.0  # Start with perfect score
        
        payment_history = tenant_data.get('payment_history', [])
        if not payment_history:
            return 70.0  # Default for no history
        
        # On-time payment rate
        on_time_payments = sum(1 for p in payment_history if p.get('days_late', 0) == 0)
        on_time_rate = on_time_payments / len(payment_history)
        score = on_time_rate * 100
        
        # Late payment severity
        late_payments = [p for p in payment_history if p.get('days_late', 0) > 0]
        if late_payments:
            avg_lateness = sum(p.get('days_late', 0) for p in late_payments) / len(late_payments)
            
            if avg_lateness > 30:  # Very late payments
                score *= 0.7
            elif avg_lateness > 10:  # Moderately late
                score *= 0.85
            elif avg_lateness > 5:  # Slightly late
                score *= 0.95
        
        # Recent payment trend (last 6 payments)
        recent_payments = payment_history[-6:] if len(payment_history) >= 6 else payment_history
        if recent_payments:
            recent_on_time_rate = sum(1 for p in recent_payments if p.get('days_late', 0) == 0) / len(recent_payments)
            
            # Weight recent performance more heavily
            score = (score * 0.6) + (recent_on_time_rate * 100 * 0.4)
        
        # NSF/bounced check penalties
        nsf_count = tenant_data.get('nsf_checks_12m', 0)
        score -= nsf_count * 10  # 10 points per NSF
        
        # Partial payment history
        partial_payments = tenant_data.get('partial_payments_12m', 0)
        score -= partial_payments * 5  # 5 points per partial payment
        
        return max(0, min(100, score))
    
    def _calculate_financial_stability_score(self, 
                                           tenant_data: Dict[str, Any],
                                           lease_data: Dict[str, Any]) -> float:
        """
        Calculate financial stability score
        """
        financial_info = tenant_data.get('financial_info', {})
        if not financial_info:
            return 65.0  # Default moderate score
        
        score = 80.0  # Base score
        
        # Debt-to-income ratio
        monthly_income = financial_info.get('monthly_income', 0)
        monthly_rent = lease_data.get('monthly_rent', 0)
        
        if monthly_income > 0 and monthly_rent > 0:
            rent_to_income = monthly_rent / monthly_income
            
            if rent_to_income <= 0.25:  # 25% or less - excellent
                score += 15
            elif rent_to_income <= 0.30:  # 30% or less - good
                score += 10
            elif rent_to_income <= 0.35:  # 35% or less - fair
                score += 0
            elif rent_to_income <= 0.40:  # 40% or less - concerning
                score -= 10
            else:  # Over 40% - risky
                score -= 25
        
        # Employment stability
        employment_months = financial_info.get('employment_length_months', 0)
        if employment_months >= 24:  # 2+ years
            score += 10
        elif employment_months >= 12:  # 1+ year
            score += 5
        elif employment_months < 6:  # Less than 6 months
            score -= 15
        
        # Credit score
        credit_score = financial_info.get('credit_score', 650)
        if credit_score >= 750:
            score += 15
        elif credit_score >= 700:
            score += 10
        elif credit_score >= 650:
            score += 5
        elif credit_score < 600:
            score -= 20
        elif credit_score < 550:
            score -= 35
        
        # Savings/emergency fund
        savings = financial_info.get('savings_months_rent', 0)
        if savings >= 6:  # 6+ months rent saved
            score += 10
        elif savings >= 3:  # 3+ months
            score += 5
        elif savings < 1:  # Less than 1 month
            score -= 10
        
        # Other debt obligations
        other_debts = financial_info.get('other_monthly_debts', 0)
        if monthly_income > 0:
            debt_ratio = other_debts / monthly_income
            if debt_ratio > 0.20:  # More than 20% of income in other debts
                score -= 15
            elif debt_ratio > 0.15:
                score -= 10
        
        # Income stability (multiple sources, job type)
        income_sources = financial_info.get('income_sources', 1)
        if income_sources > 1:
            score += 5  # Multiple income sources
        
        job_type = financial_info.get('employment_type', 'unknown')
        if job_type in ['government', 'healthcare', 'education']:
            score += 5  # Stable industries
        elif job_type in ['gig_economy', 'seasonal', 'commission_only']:
            score -= 10  # Less stable
        
        return max(0, min(100, score))
    
    def _calculate_behavioral_score(self, tenant_data: Dict[str, Any]) -> float:
        """
        Calculate behavioral risk score
        """
        score = 85.0  # Base good behavior score
        
        # Lease violations
        violations = tenant_data.get('lease_violations', [])
        for violation in violations:
            severity = violation.get('severity', 'minor')
            if severity == 'major':
                score -= 15
            elif severity == 'moderate':
                score -= 10
            else:  # minor
                score -= 5
        
        # Complaints from neighbors/management
        complaints = tenant_data.get('complaints_received', [])
        score -= len(complaints) * 8  # 8 points per complaint
        
        # Noise complaints specifically
        noise_complaints = tenant_data.get('noise_complaints_12m', 0)
        score -= noise_complaints * 12  # Higher penalty for noise
        
        # Police incidents
        police_incidents = tenant_data.get('police_incidents_12m', 0)
        score -= police_incidents * 20  # Serious penalty
        
        # Guest policy violations
        guest_violations = tenant_data.get('guest_policy_violations', 0)
        score -= guest_violations * 6
        
        # Unauthorized occupants
        if tenant_data.get('unauthorized_occupants', False):
            score -= 25
        
        # Cooperation with management
        cooperation_rating = tenant_data.get('cooperation_rating', 4.0)  # 1-5 scale
        score += (cooperation_rating - 3.0) * 10  # Adjust based on cooperation
        
        # Response to notices/communications
        notice_compliance = tenant_data.get('notice_compliance_rate', 0.8)
        score += (notice_compliance - 0.7) * 50  # Penalty for not responding to notices
        
        # Pet policy compliance (if applicable)
        if tenant_data.get('has_pets', False):
            pet_compliance = tenant_data.get('pet_policy_compliance', True)
            if not pet_compliance:
                score -= 15
        
        return max(0, min(100, score))
    
    def _calculate_property_care_score(self, 
                                     tenant_data: Dict[str, Any],
                                     property_data: Dict[str, Any]) -> float:
        """
        Calculate property care and maintenance score
        """
        score = 85.0  # Base score assuming good care
        
        # Maintenance requests analysis
        maintenance_requests = tenant_data.get('maintenance_requests', [])
        
        if maintenance_requests:
            # Excessive maintenance requests
            if len(maintenance_requests) > 10:  # More than 10 per year
                score -= 15
            elif len(maintenance_requests) > 6:
                score -= 10
            
            # Preventable maintenance issues
            preventable_issues = sum(1 for req in maintenance_requests 
                                   if req.get('preventable', False))
            score -= preventable_issues * 8
            
            # Emergency maintenance frequency
            emergency_requests = sum(1 for req in maintenance_requests 
                                   if req.get('priority', 'normal') == 'emergency')
            if emergency_requests > 3:  # More than 3 emergencies
                score -= 20
            
            # Damage caused by tenant
            tenant_damage = sum(1 for req in maintenance_requests 
                              if req.get('cause', 'normal_wear') == 'tenant_damage')
            score -= tenant_damage * 12
        
        # Property inspections
        inspection_results = tenant_data.get('inspection_results', [])
        for inspection in inspection_results:
            cleanliness_score = inspection.get('cleanliness_score', 8)  # Out of 10
            score += (cleanliness_score - 6) * 5  # Adjust based on cleanliness
            
            damage_noted = inspection.get('damage_items', [])
            score -= len(damage_noted) * 8
        
        # Unit condition changes
        move_in_condition = property_data.get('move_in_condition_score', 8)
        current_condition = tenant_data.get('current_condition_estimate', 8)
        
        if current_condition < move_in_condition:
            condition_decline = move_in_condition - current_condition
            score -= condition_decline * 10
        
        # Smoking violations (if non-smoking unit)
        if property_data.get('no_smoking', False):
            smoking_violations = tenant_data.get('smoking_violations', 0)
            score -= smoking_violations * 20
        
        # Hoarding or cleanliness issues
        if tenant_data.get('cleanliness_issues', False):
            score -= 25
        
        # Lawn/exterior care (if applicable)
        if property_data.get('tenant_responsible_lawn', False):
            lawn_care_score = tenant_data.get('lawn_care_compliance', 8)  # Out of 10
            score += (lawn_care_score - 6) * 3
        
        return max(0, min(100, score))
    
    def _calculate_compliance_score(self, 
                                  tenant_data: Dict[str, Any],
                                  lease_data: Dict[str, Any]) -> float:
        """
        Calculate lease compliance score
        """
        score = 90.0  # Base compliance score
        
        # Lease term violations
        lease_violations = tenant_data.get('lease_violations', [])
        for violation in lease_violations:
            if violation.get('resolved', False):
                score -= 5  # Lighter penalty if resolved
            else:
                score -= 15  # Heavier penalty if unresolved
        
        # Notice period compliance
        notice_compliance = tenant_data.get('notice_compliance_rate', 0.9)
        score += (notice_compliance - 0.8) * 50
        
        # Insurance compliance (if required)
        if lease_data.get('insurance_required', False):
            insurance_current = tenant_data.get('insurance_current', True)
            if not insurance_current:
                score -= 20
        
        # Subletting violations
        unauthorized_subletting = tenant_data.get('unauthorized_subletting', False)
        if unauthorized_subletting:
            score -= 30
        
        # Parking violations
        parking_violations = tenant_data.get('parking_violations', 0)
        score -= parking_violations * 8
        
        # Common area violations
        common_area_violations = tenant_data.get('common_area_violations', 0)
        score -= common_area_violations * 10
        
        # Late fee payments
        late_fees_outstanding = tenant_data.get('late_fees_outstanding', 0)
        if late_fees_outstanding > 0:
            score -= 15
        
        # HOA violations (if applicable)
        hoa_violations = tenant_data.get('hoa_violations', 0)
        score -= hoa_violations * 12
        
        return max(0, min(100, score))
    
    def _calculate_communication_score(self, tenant_data: Dict[str, Any]) -> float:
        """
        Calculate communication and responsiveness score
        """
        score = 80.0  # Base communication score
        
        # Response time to management communications
        avg_response_hours = tenant_data.get('avg_response_time_hours', 24)
        if avg_response_hours <= 4:  # Very responsive
            score += 15
        elif avg_response_hours <= 24:  # Good response
            score += 10
        elif avg_response_hours <= 48:  # Fair response
            score += 0
        elif avg_response_hours > 72:  # Poor response
            score -= 15
        
        # Communication quality rating
        communication_rating = tenant_data.get('communication_quality_rating', 4.0)  # 1-5
        score += (communication_rating - 3.0) * 15
        
        # Preferred contact method compliance
        contact_compliance = tenant_data.get('contact_method_compliance', 0.8)
        score += (contact_compliance - 0.7) * 30
        
        # Language barriers
        if tenant_data.get('language_barrier', False):
            # Not necessarily negative, but may need special handling
            score -= 5
        
        # Attitude/professionalism
        professionalism_rating = tenant_data.get('professionalism_rating', 4.0)  # 1-5
        score += (professionalism_rating - 3.0) * 12
        
        # Escalation history
        escalations = tenant_data.get('escalations_to_management', 0)
        score -= escalations * 8
        
        # Missed appointments
        missed_appointments = tenant_data.get('missed_appointments_12m', 0)
        score -= missed_appointments * 10
        
        return max(0, min(100, score))
    
    def _calculate_longevity_score(self, 
                                 tenant_data: Dict[str, Any],
                                 lease_data: Dict[str, Any]) -> float:
        """
        Calculate longevity/retention likelihood score
        """
        score = 70.0  # Base retention score
        
        # Current tenancy length
        tenancy_months = tenant_data.get('total_tenancy_months', 0)
        if tenancy_months >= 36:  # 3+ years
            score += 20
        elif tenancy_months >= 24:  # 2+ years
            score += 15
        elif tenancy_months >= 12:  # 1+ year
            score += 10
        elif tenancy_months < 6:  # Less than 6 months
            score -= 10
        
        # Renewal history
        renewals = tenant_data.get('lease_renewals_count', 0)
        score += renewals * 8  # Each renewal adds stability
        
        # Move frequency (from previous addresses)
        previous_addresses = tenant_data.get('previous_addresses', [])
        if len(previous_addresses) > 3:  # Frequent mover
            score -= 15
        elif len(previous_addresses) <= 1:  # Stable history
            score += 10
        
        # Age factor (older tenants tend to be more stable)
        age = tenant_data.get('age', 35)
        if age >= 45:
            score += 10
        elif age >= 35:
            score += 5
        elif age < 25:
            score -= 5
        
        # Family status
        household_size = tenant_data.get('household_size', 1)
        if household_size >= 3:  # Families tend to be more stable
            score += 8
        
        # Local ties
        local_employment = tenant_data.get('works_locally', False)
        if local_employment:
            score += 10
        
        # Satisfaction indicators
        satisfaction_rating = tenant_data.get('satisfaction_rating', 3.5)  # 1-5
        score += (satisfaction_rating - 3.0) * 20
        
        # Financial stability (from employment)
        employment_type = tenant_data.get('financial_info', {}).get('employment_type', 'unknown')
        if employment_type in ['government', 'healthcare', 'education']:
            score += 8
        elif employment_type in ['contract', 'seasonal']:
            score -= 8
        
        return max(0, min(100, score))
    
    def _calculate_market_risk_score(self, market_data: Dict[str, Any]) -> float:
        """
        Calculate market-related risk factors
        """
        if not market_data:
            return 50.0  # Neutral market risk
        
        score = 50.0  # Base neutral score
        
        # Vacancy rate impact
        vacancy_rate = market_data.get('vacancy_rate', 0.05)
        if vacancy_rate < 0.03:  # Very tight market - low risk
            score -= 15
        elif vacancy_rate < 0.05:  # Tight market
            score -= 10
        elif vacancy_rate > 0.10:  # Loose market - higher risk
            score += 15
        elif vacancy_rate > 0.08:
            score += 10
        
        # Rent growth trends
        rent_growth = market_data.get('rent_growth_12m', 0.03)
        if rent_growth < 0:  # Declining rents
            score += 20
        elif rent_growth < 0.02:  # Slow growth
            score += 10
        elif rent_growth > 0.08:  # Rapid growth may cause affordability issues
            score += 5
        
        # Employment trends
        employment_growth = market_data.get('employment_growth', 0.02)
        if employment_growth < -0.02:  # Job losses
            score += 25
        elif employment_growth < 0:
            score += 15
        elif employment_growth > 0.03:
            score -= 10
        
        # New supply coming online
        new_supply = market_data.get('new_supply_ratio', 0.02)
        if new_supply > 0.05:  # Lots of new competition
            score += 15
        elif new_supply > 0.03:
            score += 8
        
        return max(0, min(100, score))
    
    def _identify_risk_factors(self, 
                             tenant_data: Dict[str, Any],
                             lease_data: Dict[str, Any],
                             property_data: Dict[str, Any],
                             risk_metrics: RiskMetrics) -> List[RiskFactor]:
        """
        Identify specific risk factors and their details
        """
        risk_factors = []
        
        # Payment risk factors
        if risk_metrics.payment_reliability_score < 80:
            payment_history = tenant_data.get('payment_history', [])
            late_payments = sum(1 for p in payment_history if p.get('days_late', 0) > 5)
            
            severity = RiskLevel.HIGH if risk_metrics.payment_reliability_score < 60 else RiskLevel.MODERATE
            
            risk_factors.append(RiskFactor(
                factor_id="payment_reliability",
                category=RiskCategory.PAYMENT_RISK,
                description="History of late or missed payments",
                severity=severity,
                score=100 - risk_metrics.payment_reliability_score,
                weight=0.30,
                evidence=[
                    f"{late_payments} late payments in recent history",
                    f"Payment reliability score: {risk_metrics.payment_reliability_score:.1f}%"
                ],
                recommendations=[
                    "Implement payment monitoring",
                    "Consider payment plan options",
                    "Set up automatic payment reminders"
                ],
                trend="deteriorating" if late_payments > 2 else "stable"
            ))
        
        # Financial stability risk factors
        if risk_metrics.financial_stability_score < 70:
            financial_info = tenant_data.get('financial_info', {})
            monthly_income = financial_info.get('monthly_income', 0)
            monthly_rent = lease_data.get('monthly_rent', 0)
            
            rent_to_income = (monthly_rent / monthly_income) if monthly_income > 0 else 0
            
            severity = RiskLevel.HIGH if risk_metrics.financial_stability_score < 50 else RiskLevel.MODERATE
            
            evidence = [f"Financial stability score: {risk_metrics.financial_stability_score:.1f}%"]
            if rent_to_income > 0.35:
                evidence.append(f"Rent-to-income ratio: {rent_to_income:.1%}")
            
            risk_factors.append(RiskFactor(
                factor_id="financial_stability",
                category=RiskCategory.FINANCIAL_RISK,
                description="Financial stress or instability indicators",
                severity=severity,
                score=100 - risk_metrics.financial_stability_score,
                weight=0.20,
                evidence=evidence,
                recommendations=[
                    "Monitor payment patterns closely",
                    "Discuss financial assistance programs",
                    "Consider rent adjustment if appropriate"
                ],
                trend="stable"  # Would need historical data to determine trend
            ))
        
        # Behavioral risk factors
        if risk_metrics.behavioral_score < 75:
            violations = tenant_data.get('lease_violations', [])
            complaints = tenant_data.get('complaints_received', [])
            
            severity = RiskLevel.HIGH if risk_metrics.behavioral_score < 60 else RiskLevel.MODERATE
            
            evidence = []
            if violations:
                evidence.append(f"{len(violations)} lease violations")
            if complaints:
                evidence.append(f"{len(complaints)} complaints received")
            
            risk_factors.append(RiskFactor(
                factor_id="behavioral_issues",
                category=RiskCategory.BEHAVIORAL_RISK,
                description="Behavioral issues or lease violations",
                severity=severity,
                score=100 - risk_metrics.behavioral_score,
                weight=0.15,
                evidence=evidence,
                recommendations=[
                    "Schedule tenant meeting",
                    "Review lease terms and expectations",
                    "Consider additional monitoring"
                ],
                trend="stable"
            ))
        
        # Property care risk factors
        if risk_metrics.property_care_score < 75:
            maintenance_requests = tenant_data.get('maintenance_requests', [])
            preventable_issues = sum(1 for req in maintenance_requests 
                                   if req.get('preventable', False))
            
            severity = RiskLevel.MODERATE
            
            risk_factors.append(RiskFactor(
                factor_id="property_care",
                category=RiskCategory.PROPERTY_RISK,
                description="Poor property care or excessive maintenance issues",
                severity=severity,
                score=100 - risk_metrics.property_care_score,
                weight=0.15,
                evidence=[
                    f"{len(maintenance_requests)} maintenance requests",
                    f"{preventable_issues} preventable issues"
                ],
                recommendations=[
                    "Schedule property inspection",
                    "Provide property care education",
                    "Consider maintenance agreement"
                ],
                trend="stable"
            ))
        
        # Add more risk factors based on other metrics...
        
        return risk_factors
    
    def _calculate_category_scores(self, risk_factors: List[RiskFactor]) -> Dict[RiskCategory, float]:
        """
        Calculate average scores by risk category
        """
        category_scores = {category: 0.0 for category in RiskCategory}
        category_counts = {category: 0 for category in RiskCategory}
        
        for factor in risk_factors:
            category_scores[factor.category] += factor.score * factor.weight
            category_counts[factor.category] += factor.weight
        
        # Calculate weighted averages
        for category in RiskCategory:
            if category_counts[category] > 0:
                category_scores[category] /= category_counts[category]
            else:
                # Use base score if no factors in category
                category_scores[category] = 20.0  # Low risk default
        
        return category_scores
    
    def _calculate_overall_risk_score(self, category_scores: Dict[RiskCategory, float]) -> float:
        """
        Calculate overall risk score from category scores
        """
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            weight = self.category_weights.get(category, 0.1)
            total_weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            return total_weighted_score / total_weight
        else:
            return 50.0  # Default moderate risk
    
    def _determine_risk_level(self, overall_score: float) -> RiskLevel:
        """
        Determine risk level from overall score
        """
        if overall_score >= 80:
            return RiskLevel.VERY_HIGH
        elif overall_score >= 60:
            return RiskLevel.HIGH
        elif overall_score >= 40:
            return RiskLevel.MODERATE
        elif overall_score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def _determine_tenant_segment(self, overall_score: float, risk_factors: List[RiskFactor]) -> TenantSegment:
        """
        Determine tenant segment classification
        """
        high_severity_factors = sum(1 for factor in risk_factors if factor.severity in [RiskLevel.HIGH, RiskLevel.VERY_HIGH])
        
        if overall_score < 20 and high_severity_factors == 0:
            return TenantSegment.PREMIUM
        elif overall_score < 30:
            return TenantSegment.STABLE
        elif overall_score < 50:
            return TenantSegment.STANDARD
        elif overall_score < 70:
            return TenantSegment.CAUTION
        else:
            return TenantSegment.HIGH_RISK
    
    def _analyze_risk_trends(self, tenant_id: str, historical_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze risk trends over time
        """
        # Get historical assessments
        tenant_history = self.historical_assessments.get(tenant_id, {}).get('history', [])
        
        if len(tenant_history) < 2:
            return {
                'trend_available': False,
                'message': 'Insufficient historical data for trend analysis'
            }
        
        # Calculate trends
        recent_scores = [assessment['overall_risk_score'] for assessment in tenant_history[-6:]]
        score_trend = 'stable'
        
        if len(recent_scores) >= 3:
            # Simple trend analysis
            if recent_scores[-1] > recent_scores[0] + 10:
                score_trend = 'deteriorating'
            elif recent_scores[-1] < recent_scores[0] - 10:
                score_trend = 'improving'
        
        return {
            'trend_available': True,
            'overall_trend': score_trend,
            'score_history': recent_scores,
            'trend_period_months': len(recent_scores),
            'volatility': np.std(recent_scores) if len(recent_scores) > 1 else 0
        }
    
    def _perform_comparative_analysis(self, 
                                    overall_score: float,
                                    category_scores: Dict[RiskCategory, float],
                                    risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """
        Compare tenant against portfolio benchmarks
        """
        # For now, use static benchmarks
        # In production, these would be calculated from actual portfolio data
        
        portfolio_averages = {
            'overall_risk_score': 35.0,
            'payment_reliability': 88.0,
            'financial_stability': 75.0,
            'behavioral_score': 82.0
        }
        
        return {
            'overall_percentile': max(0, min(100, 100 - (overall_score / 100 * 100))),
            'payment_percentile': max(0, min(100, risk_metrics.payment_reliability_score)),
            'financial_percentile': max(0, min(100, risk_metrics.financial_stability_score)),
            'behavioral_percentile': max(0, min(100, risk_metrics.behavioral_score)),
            'vs_portfolio_average': overall_score - portfolio_averages['overall_risk_score']
        }
    
    def _detect_early_warning_indicators(self, 
                                       tenant_data: Dict[str, Any],
                                       lease_data: Dict[str, Any],
                                       risk_metrics: RiskMetrics,
                                       trend_analysis: Dict[str, Any]) -> List[str]:
        """
        Detect early warning indicators
        """
        warnings = []
        
        # Payment trend deterioration
        if trend_analysis.get('overall_trend') == 'deteriorating':
            warnings.append('risk_score_deteriorating')
        
        # Recent late payments
        payment_history = tenant_data.get('payment_history', [])
        recent_payments = payment_history[-3:] if len(payment_history) >= 3 else payment_history
        recent_late = sum(1 for p in recent_payments if p.get('days_late', 0) > 5)
        
        if recent_late >= 2:
            warnings.append('recent_payment_issues')
        
        # Financial stress indicators
        financial_info = tenant_data.get('financial_info', {})
        monthly_income = financial_info.get('monthly_income', 0)
        monthly_rent = lease_data.get('monthly_rent', 0)
        
        if monthly_income > 0 and monthly_rent > 0:
            rent_ratio = monthly_rent / monthly_income
            if rent_ratio > self.warning_thresholds['financial_stress']:
                warnings.append('high_rent_to_income_ratio')
        
        # Complaint spike
        complaints_30d = tenant_data.get('complaints_30d', 0)
        if complaints_30d >= self.warning_thresholds['complaint_spike']:
            warnings.append('complaint_spike')
        
        # Maintenance neglect
        overdue_maintenance = tenant_data.get('overdue_maintenance_requests', 0)
        if overdue_maintenance >= self.warning_thresholds['maintenance_neglect']:
            warnings.append('maintenance_neglect')
        
        # Communication breakdown
        if risk_metrics.communication_score < 60:
            warnings.append('communication_issues')
        
        # Lease expiration approaching with renewal uncertainty
        lease_end_date = lease_data.get('lease_end_date')
        if lease_end_date:
            try:
                lease_end = datetime.fromisoformat(lease_end_date) if isinstance(lease_end_date, str) else lease_end_date
                days_to_expiration = (lease_end - datetime.now()).days
                
                if days_to_expiration <= 60 and not tenant_data.get('renewal_intent_expressed', False):
                    warnings.append('renewal_uncertainty')
            except:
                pass
        
        return warnings
    
    def _generate_mitigation_strategies(self, 
                                      risk_factors: List[RiskFactor],
                                      early_warnings: List[str],
                                      tenant_segment: TenantSegment) -> List[str]:
        """
        Generate risk mitigation strategies
        """
        strategies = []
        
        # Segment-based strategies
        if tenant_segment == TenantSegment.HIGH_RISK:
            strategies.extend([
                'implement_weekly_payment_monitoring',
                'require_additional_security_deposit',
                'schedule_monthly_property_inspections'
            ])
        elif tenant_segment == TenantSegment.CAUTION:
            strategies.extend([
                'implement_bi_weekly_payment_monitoring',
                'schedule_quarterly_tenant_meetings'
            ])
        
        # Factor-specific strategies
        payment_factors = [f for f in risk_factors if f.category == RiskCategory.PAYMENT_RISK]
        if payment_factors:
            strategies.extend([
                'offer_payment_plan_options',
                'implement_automatic_payment_setup',
                'provide_financial_counseling_resources'
            ])
        
        behavioral_factors = [f for f in risk_factors if f.category == RiskCategory.BEHAVIORAL_RISK]
        if behavioral_factors:
            strategies.extend([
                'schedule_lease_education_meeting',
                'implement_neighbor_mediation_if_needed',
                'provide_community_guidelines_reminder'
            ])
        
        # Early warning specific strategies
        if 'recent_payment_issues' in early_warnings:
            strategies.append('immediate_payment_plan_discussion')
        
        if 'complaint_spike' in early_warnings:
            strategies.append('urgent_tenant_meeting_required')
        
        if 'renewal_uncertainty' in early_warnings:
            strategies.append('proactive_renewal_discussion')
        
        return list(set(strategies))  # Remove duplicates
    
    def _generate_monitoring_recommendations(self, 
                                           risk_level: RiskLevel,
                                           risk_factors: List[RiskFactor],
                                           early_warnings: List[str]) -> List[str]:
        """
        Generate monitoring recommendations
        """
        recommendations = []
        
        # Risk level based monitoring
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            recommendations.extend([
                'weekly_payment_status_checks',
                'monthly_property_drive_by',
                'quarterly_formal_inspection'
            ])
        elif risk_level == RiskLevel.MODERATE:
            recommendations.extend([
                'bi_weekly_payment_monitoring',
                'semi_annual_property_inspection'
            ])
        else:
            recommendations.extend([
                'monthly_payment_monitoring',
                'annual_property_inspection'
            ])
        
        # Factor-specific monitoring
        high_payment_risk = any(f.category == RiskCategory.PAYMENT_RISK and f.severity in [RiskLevel.HIGH, RiskLevel.VERY_HIGH] 
                               for f in risk_factors)
        if high_payment_risk:
            recommendations.append('daily_payment_status_monitoring')
        
        if early_warnings:
            recommendations.append('escalated_monitoring_protocol')
        
        return recommendations
    
    def _calculate_assessment_confidence(self, 
                                       tenant_data: Dict[str, Any],
                                       lease_data: Dict[str, Any],
                                       historical_data: Dict[str, Any] = None) -> float:
        """
        Calculate confidence in the risk assessment
        """
        confidence = 0.5  # Base confidence
        
        # Data completeness factors
        payment_history_length = len(tenant_data.get('payment_history', []))
        if payment_history_length >= 12:
            confidence += 0.2
        elif payment_history_length >= 6:
            confidence += 0.1
        
        # Financial information completeness
        financial_info = tenant_data.get('financial_info', {})
        if financial_info:
            confidence += 0.15
        
        # Tenancy length
        tenancy_months = tenant_data.get('total_tenancy_months', 0)
        if tenancy_months >= 12:
            confidence += 0.1
        
        # Historical assessment data
        if historical_data and len(historical_data.get('history', [])) >= 3:
            confidence += 0.15
        
        # Property inspection data
        if tenant_data.get('inspection_results'):
            confidence += 0.1
        
        return max(0.3, min(1.0, confidence))
    
    def _calculate_next_review_date(self, risk_level: RiskLevel) -> datetime:
        """
        Calculate next review date based on risk level
        """
        if risk_level == RiskLevel.VERY_HIGH:
            return datetime.now() + timedelta(days=30)
        elif risk_level == RiskLevel.HIGH:
            return datetime.now() + timedelta(days=60)
        elif risk_level == RiskLevel.MODERATE:
            return datetime.now() + timedelta(days=90)
        else:
            return datetime.now() + timedelta(days=180)
    
    def _store_assessment_history(self, risk_profile: TenantRiskProfile):
        """
        Store assessment in history for trend analysis
        """
        tenant_id = risk_profile.tenant_id
        
        if tenant_id not in self.historical_assessments:
            self.historical_assessments[tenant_id] = {'history': [], 'latest': None}
        
        # Add to history
        self.historical_assessments[tenant_id]['history'].append(risk_profile.to_dict())
        
        # Keep only last 12 assessments
        if len(self.historical_assessments[tenant_id]['history']) > 12:
            self.historical_assessments[tenant_id]['history'] = self.historical_assessments[tenant_id]['history'][-12:]
        
        # Update latest
        self.historical_assessments[tenant_id]['latest'] = risk_profile.to_dict()
    
    # Portfolio analysis methods
    
    def _calculate_portfolio_risk_score(self, assessments: List[Dict[str, Any]]) -> float:
        """
        Calculate overall portfolio risk score
        """
        if not assessments:
            return 50.0
        
        # Weight by risk level distribution
        risk_weights = {
            'very_low': 0.1,
            'low': 0.3,
            'moderate': 0.5,
            'high': 0.8,
            'very_high': 1.0
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for assessment in assessments:
            risk_level = assessment['risk_level']
            weight = risk_weights.get(risk_level, 0.5)
            score = assessment['overall_risk_score']
            
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 50.0
    
    def _generate_portfolio_risk_insights(self, assessments: List[Dict[str, Any]], 
                                        portfolio_metrics: Dict[str, Any]) -> List[str]:
        """
        Generate portfolio-level risk insights
        """
        insights = []
        
        # Risk distribution insights
        high_risk_pct = (portfolio_metrics['risk_distribution']['high'] + 
                        portfolio_metrics['risk_distribution']['very_high']) / portfolio_metrics['total_tenants'] * 100
        
        if high_risk_pct > 20:
            insights.append(f"High concentration of high-risk tenants ({high_risk_pct:.1f}%)")
        
        # Early warning insights
        warning_pct = portfolio_metrics['early_warning_count'] / portfolio_metrics['total_tenants'] * 100
        if warning_pct > 15:
            insights.append(f"Significant number of tenants with early warning indicators ({warning_pct:.1f}%)")
        
        # Segment insights
        caution_and_high_risk = (portfolio_metrics['segment_distribution']['caution'] + 
                               portfolio_metrics['segment_distribution']['high_risk'])
        
        if caution_and_high_risk > portfolio_metrics['total_tenants'] * 0.3:
            insights.append("Over 30% of tenants require heightened attention")
        
        return insights
    
    def _analyze_risk_correlations(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze correlations between different risk factors
        """
        # This would perform more sophisticated correlation analysis
        # For now, return basic correlation insights
        
        return {
            'payment_behavioral_correlation': 0.65,  # Payment issues often correlate with behavioral issues
            'financial_payment_correlation': 0.78,   # Financial stress strongly correlates with payment issues
            'property_care_behavioral_correlation': 0.45,  # Moderate correlation
        }
    
    def _generate_portfolio_risk_actions(self, portfolio_metrics: Dict[str, Any], 
                                       assessments: List[Dict[str, Any]]) -> List[str]:
        """
        Generate portfolio-level recommended actions
        """
        actions = []
        
        high_risk_count = portfolio_metrics['high_risk_count']
        total_tenants = portfolio_metrics['total_tenants']
        
        if high_risk_count > total_tenants * 0.15:  # More than 15% high risk
            actions.append('implement_portfolio_wide_risk_monitoring')
            actions.append('review_tenant_screening_criteria')
        
        if portfolio_metrics['early_warning_count'] > total_tenants * 0.10:
            actions.append('activate_early_intervention_protocols')
        
        if portfolio_metrics['average_risk_score'] > 50:
            actions.append('consider_portfolio_risk_insurance')
            actions.append('implement_tenant_retention_programs')
        
        actions.append('schedule_quarterly_portfolio_risk_review')
        
        return actions
    
    # Reporting methods
    
    def _generate_comprehensive_report(self, latest_assessment: Dict[str, Any], 
                                     assessment_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive risk report
        """
        return {
            'report_type': 'comprehensive',
            'tenant_id': latest_assessment['tenant_id'],
            'executive_summary': self._generate_executive_summary(latest_assessment),
            'detailed_assessment': latest_assessment,
            'trend_analysis': self._generate_trend_report(assessment_history),
            'recommendations': {
                'mitigation_strategies': latest_assessment['mitigation_strategies'],
                'monitoring_plan': latest_assessment['monitoring_recommendations']
            },
            'next_review_date': latest_assessment['next_review_date'],
            'report_timestamp': datetime.now().isoformat()
        }
    
    def _generate_executive_summary(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executive summary of risk assessment
        """
        return {
            'overall_risk_level': assessment['risk_level'],
            'risk_score': assessment['overall_risk_score'],
            'tenant_segment': assessment['tenant_segment'],
            'confidence': assessment['confidence_score'],
            'key_risk_factors': [factor['description'] for factor in assessment['risk_factors'][:3]],
            'early_warnings': assessment['early_warning_indicators'],
            'immediate_actions_required': len([action for action in assessment['mitigation_strategies'] 
                                             if 'immediate' in action or 'urgent' in action]) > 0
        }
    
    def _generate_trend_report(self, assessment_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate trend analysis report
        """
        if len(assessment_history) < 2:
            return {'status': 'insufficient_data'}
        
        scores = [assessment['overall_risk_score'] for assessment in assessment_history]
        
        return {
            'trend_period_months': len(scores),
            'score_trend': 'improving' if scores[-1] < scores[0] else 'stable' if abs(scores[-1] - scores[0]) < 5 else 'deteriorating',
            'score_history': scores,
            'volatility': round(np.std(scores), 2) if len(scores) > 1 else 0,
            'best_score': min(scores),
            'worst_score': max(scores),
            'current_vs_best': scores[-1] - min(scores)
        }
    
    def _generate_standard_report(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate standard risk report
        """
        return {
            'report_type': 'standard',
            'tenant_id': assessment['tenant_id'],
            'risk_summary': self._generate_executive_summary(assessment),
            'category_breakdown': assessment['category_scores'],
            'top_risk_factors': assessment['risk_factors'][:5],
            'recommended_actions': assessment['mitigation_strategies'][:3],
            'next_review': assessment['next_review_date']
        }
    
    # Fallback methods
    
    def _get_fallback_risk_profile(self, tenant_data: Dict[str, Any]) -> TenantRiskProfile:
        """
        Generate fallback risk profile when assessment fails
        """
        return TenantRiskProfile(
            tenant_id=tenant_data.get('tenant_id', ''),
            overall_risk_score=50.0,
            risk_level=RiskLevel.MODERATE,
            tenant_segment=TenantSegment.STANDARD,
            confidence_score=0.3,
            risk_factors=[],
            category_scores={cat.value: 50.0 for cat in RiskCategory},
            trend_analysis={'trend_available': False},
            comparative_analysis={'status': 'insufficient_data'},
            early_warning_indicators=['insufficient_data_for_assessment'],
            mitigation_strategies=['collect_more_tenant_data', 'schedule_comprehensive_review'],
            monitoring_recommendations=['monthly_review_until_more_data_available'],
            assessment_timestamp=datetime.now(),
            next_review_date=datetime.now() + timedelta(days=30)
        )
    
    def _initialize_risk_factors(self) -> Dict[str, Any]:
        """
        Initialize risk factor definitions and thresholds
        """
        return {
            'payment_risk_thresholds': {
                'late_payment_rate_high': 0.20,
                'late_payment_rate_moderate': 0.10,
                'avg_days_late_high': 15,
                'avg_days_late_moderate': 7
            },
            'financial_risk_thresholds': {
                'rent_to_income_high': 0.40,
                'rent_to_income_moderate': 0.35,
                'credit_score_low': 600,
                'credit_score_moderate': 650
            },
            'behavioral_risk_thresholds': {
                'violations_high': 3,
                'violations_moderate': 1,
                'complaints_high': 5,
                'complaints_moderate': 2
            }
        }