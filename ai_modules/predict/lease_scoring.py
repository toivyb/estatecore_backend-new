import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

def score_lease(tenant_data: Dict, property_data: Dict = None, market_data: Dict = None) -> Dict:
    """
    Advanced tenant risk scoring using machine learning techniques
    
    Args:
        tenant_data (dict): Tenant information including payment history, credit, employment
        property_data (dict): Property characteristics and rental terms
        market_data (dict): Local market conditions and trends
    
    Returns:
        dict: Comprehensive risk assessment with score, factors, and recommendations
    """
    
    # Initialize scoring components
    payment_score = calculate_payment_reliability_score(tenant_data.get('payment_history', []))
    financial_score = calculate_financial_stability_score(tenant_data.get('financial_info', {}))
    behavioral_score = calculate_behavioral_score(tenant_data.get('behavioral_data', {}))
    market_score = calculate_market_risk_score(property_data or {}, market_data or {})
    
    # Calculate weighted composite score
    weights = {
        'payment': 0.35,     # Payment history is most important
        'financial': 0.30,   # Financial stability
        'behavioral': 0.20,  # Tenant behavior patterns
        'market': 0.15       # Market conditions
    }
    
    composite_score = (
        payment_score * weights['payment'] +
        financial_score * weights['financial'] +
        behavioral_score * weights['behavioral'] +
        market_score * weights['market']
    )
    
    # Determine risk level and generate insights
    risk_level, risk_factors = determine_risk_level(composite_score, {
        'payment': payment_score,
        'financial': financial_score,
        'behavioral': behavioral_score,
        'market': market_score
    })
    
    # Generate recommendations
    recommendations = generate_risk_recommendations(risk_level, risk_factors, tenant_data)
    
    # Calculate confidence level
    confidence = calculate_confidence_level(tenant_data, property_data, market_data)
    
    return {
        'score': round(composite_score, 1),
        'risk_level': risk_level,
        'risk_factors': risk_factors,
        'recommendations': recommendations,
        'breakdown': {
            'payment_reliability': round(payment_score, 1),
            'financial_stability': round(financial_score, 1),
            'behavioral_patterns': round(behavioral_score, 1),
            'market_conditions': round(market_score, 1)
        },
        'confidence_level': confidence,
        'predicted_outcomes': predict_tenant_outcomes(composite_score, tenant_data),
        'lease_terms_recommendations': recommend_lease_terms(risk_level, composite_score),
        'monitoring_flags': generate_monitoring_flags(risk_factors, tenant_data),
        'last_updated': datetime.now().isoformat()
    }

def calculate_payment_reliability_score(payment_history: List[Dict]) -> float:
    """
    Score tenant payment reliability based on historical patterns
    """
    if not payment_history:
        return 50.0  # Neutral score for no history
    
    # Sort payments by date
    payments = sorted(payment_history, key=lambda x: datetime.fromisoformat(x.get('date', '2024-01-01')))
    
    # Calculate on-time payment rate
    on_time_payments = sum(1 for payment in payments if payment.get('status') == 'on_time')
    total_payments = len(payments)
    on_time_rate = on_time_payments / total_payments if total_payments > 0 else 0
    
    # Late payment analysis
    late_payments = [p for p in payments if p.get('status') == 'late']
    avg_days_late = calculate_average_days_late(late_payments)
    
    # Payment amount accuracy
    partial_payments = sum(1 for payment in payments if payment.get('status') == 'partial')
    partial_rate = partial_payments / total_payments if total_payments > 0 else 0
    
    # Recent payment trend (last 6 months)
    recent_trend = calculate_recent_payment_trend(payments)
    
    # Payment consistency (variance in payment timing)
    consistency_score = calculate_payment_consistency(payments)
    
    # Calculate composite payment score
    base_score = on_time_rate * 100
    
    # Penalties for late payments
    late_penalty = min(20, avg_days_late * 2)
    partial_penalty = partial_rate * 15
    
    # Bonus for consistency and recent improvements
    consistency_bonus = consistency_score * 5
    trend_bonus = max(-10, min(10, recent_trend))
    
    payment_score = base_score - late_penalty - partial_penalty + consistency_bonus + trend_bonus
    
    return max(0, min(100, payment_score))

def calculate_financial_stability_score(financial_info: Dict) -> float:
    """
    Score tenant financial stability based on income, debt, and employment
    """
    if not financial_info:
        return 50.0  # Neutral score for no data
    
    # Income analysis
    monthly_income = financial_info.get('monthly_income', 0)
    rent_amount = financial_info.get('monthly_rent', 0)
    
    # Debt-to-income ratio
    monthly_debt = financial_info.get('monthly_debt_payments', 0)
    total_monthly_obligations = monthly_debt + rent_amount
    
    # Calculate ratios
    rent_to_income_ratio = rent_amount / monthly_income if monthly_income > 0 else 1.0
    debt_to_income_ratio = total_monthly_obligations / monthly_income if monthly_income > 0 else 1.0
    
    # Employment stability
    employment_months = financial_info.get('employment_length_months', 0)
    employment_type = financial_info.get('employment_type', 'unknown')
    
    # Credit score consideration
    credit_score = financial_info.get('credit_score', 650)
    
    # Savings/assets
    liquid_assets = financial_info.get('liquid_assets', 0)
    months_of_expenses_covered = liquid_assets / total_monthly_obligations if total_monthly_obligations > 0 else 0
    
    # Calculate component scores
    income_score = calculate_income_adequacy_score(rent_to_income_ratio)
    debt_score = calculate_debt_burden_score(debt_to_income_ratio)
    employment_score = calculate_employment_stability_score(employment_months, employment_type)
    credit_score_normalized = normalize_credit_score(credit_score)
    assets_score = min(100, months_of_expenses_covered * 20)
    
    # Weighted financial stability score
    financial_score = (
        income_score * 0.30 +
        debt_score * 0.25 +
        employment_score * 0.20 +
        credit_score_normalized * 0.15 +
        assets_score * 0.10
    )
    
    return max(0, min(100, financial_score))

def calculate_behavioral_score(behavioral_data: Dict) -> float:
    """
    Score tenant behavior patterns and communication
    """
    if not behavioral_data:
        return 75.0  # Default good behavior score
    
    # Communication responsiveness
    response_time_hours = behavioral_data.get('avg_response_time_hours', 24)
    communication_score = max(0, 100 - response_time_hours * 2)
    
    # Maintenance request patterns
    maintenance_requests = behavioral_data.get('maintenance_requests', [])
    maintenance_score = calculate_maintenance_behavior_score(maintenance_requests)
    
    # Lease compliance
    lease_violations = behavioral_data.get('lease_violations', 0)
    compliance_score = max(0, 100 - lease_violations * 15)
    
    # Neighbor relations
    neighbor_complaints = behavioral_data.get('neighbor_complaints', 0)
    neighbor_score = max(0, 100 - neighbor_complaints * 10)
    
    # Property care
    inspection_scores = behavioral_data.get('property_condition_scores', [])
    property_care_score = calculate_property_care_score(inspection_scores)
    
    # Weighted behavioral score
    behavioral_score = (
        communication_score * 0.20 +
        maintenance_score * 0.25 +
        compliance_score * 0.25 +
        neighbor_score * 0.15 +
        property_care_score * 0.15
    )
    
    return max(0, min(100, behavioral_score))

def calculate_market_risk_score(property_data: Dict, market_data: Dict) -> float:
    """
    Score market-related risks affecting tenant stability
    """
    # Market rent comparison
    current_rent = property_data.get('monthly_rent', 0)
    market_rent = market_data.get('average_market_rent', current_rent)
    
    rent_competitiveness = current_rent / market_rent if market_rent > 0 else 1.0
    
    # Market conditions
    vacancy_rate = market_data.get('local_vacancy_rate', 0.05)
    employment_rate = market_data.get('local_employment_rate', 0.95)
    
    # Property type and location desirability
    property_type = property_data.get('type', 'apartment')
    location_score = property_data.get('location_desirability_score', 75)
    
    # Calculate market score components
    competitiveness_score = calculate_rent_competitiveness_score(rent_competitiveness)
    vacancy_score = max(0, 100 - vacancy_rate * 1000)  # Lower vacancy = higher score
    employment_score = employment_rate * 100
    location_score_normalized = location_score
    
    # Weighted market score
    market_score = (
        competitiveness_score * 0.30 +
        vacancy_score * 0.25 +
        employment_score * 0.25 +
        location_score_normalized * 0.20
    )
    
    return max(0, min(100, market_score))

def determine_risk_level(composite_score: float, breakdown: Dict) -> Tuple[str, List[str]]:
    """
    Determine overall risk level and identify specific risk factors
    """
    risk_factors = []
    
    # Determine primary risk level
    if composite_score >= 85:
        risk_level = 'Excellent'
    elif composite_score >= 70:
        risk_level = 'Low'
    elif composite_score >= 55:
        risk_level = 'Medium'
        risk_factors.append('Moderate risk indicators present')
    elif composite_score >= 40:
        risk_level = 'High'
        risk_factors.append('Multiple risk factors identified')
    else:
        risk_level = 'Very High'
        risk_factors.append('Significant risk concerns')
    
    # Identify specific risk factors
    if breakdown['payment'] < 60:
        risk_factors.append('Payment reliability concerns')
    
    if breakdown['financial'] < 60:
        risk_factors.append('Financial stability issues')
    
    if breakdown['behavioral'] < 60:
        risk_factors.append('Behavioral pattern concerns')
    
    if breakdown['market'] < 60:
        risk_factors.append('Market condition risks')
    
    return risk_level, risk_factors

def generate_risk_recommendations(risk_level: str, risk_factors: List[str], tenant_data: Dict) -> List[str]:
    """
    Generate actionable recommendations based on risk assessment
    """
    recommendations = []
    
    if risk_level in ['High', 'Very High']:
        recommendations.append('Require co-signer or guarantor')
        recommendations.append('Increase security deposit to 2 months rent')
        recommendations.append('Consider shorter lease term (6-12 months)')
        
    if 'Payment reliability concerns' in risk_factors:
        recommendations.append('Set up automatic payment monitoring')
        recommendations.append('Consider requiring automatic bank payments')
        
    if 'Financial stability issues' in risk_factors:
        recommendations.append('Verify employment and income documentation')
        recommendations.append('Request additional financial references')
        
    if 'Behavioral pattern concerns' in risk_factors:
        recommendations.append('Schedule more frequent property inspections')
        recommendations.append('Provide clear communication expectations')
        
    if risk_level == 'Excellent':
        recommendations.append('Consider offering lease renewal incentives')
        recommendations.append('Eligible for standard security deposit')
        
    return recommendations

def predict_tenant_outcomes(composite_score: float, tenant_data: Dict) -> Dict:
    """
    Predict likely tenant outcomes based on risk score
    """
    # Early termination probability
    if composite_score >= 80:
        early_termination_prob = 0.05
    elif composite_score >= 60:
        early_termination_prob = 0.15
    elif composite_score >= 40:
        early_termination_prob = 0.30
    else:
        early_termination_prob = 0.50
    
    # Late payment probability
    payment_score = calculate_payment_reliability_score(tenant_data.get('payment_history', []))
    late_payment_prob = max(0, min(1, (100 - payment_score) / 100))
    
    # Lease renewal likelihood
    renewal_likelihood = min(1, composite_score / 100 * 1.2)
    
    # Property damage risk
    behavioral_score = calculate_behavioral_score(tenant_data.get('behavioral_data', {}))
    damage_risk = max(0, min(1, (100 - behavioral_score) / 100))
    
    return {
        'early_termination_probability': round(early_termination_prob, 2),
        'late_payment_probability': round(late_payment_prob, 2),
        'lease_renewal_likelihood': round(renewal_likelihood, 2),
        'property_damage_risk': round(damage_risk, 2),
        'overall_tenant_quality': 'excellent' if composite_score >= 85 else 
                                 'good' if composite_score >= 70 else
                                 'fair' if composite_score >= 55 else 'poor'
    }

def recommend_lease_terms(risk_level: str, composite_score: float) -> Dict:
    """
    Recommend appropriate lease terms based on risk assessment
    """
    if risk_level == 'Excellent':
        return {
            'security_deposit_months': 1,
            'lease_length_months': 12,
            'rent_increase_frequency': 'annual',
            'additional_requirements': []
        }
    elif risk_level == 'Low':
        return {
            'security_deposit_months': 1,
            'lease_length_months': 12,
            'rent_increase_frequency': 'annual',
            'additional_requirements': ['employment_verification']
        }
    elif risk_level == 'Medium':
        return {
            'security_deposit_months': 1.5,
            'lease_length_months': 12,
            'rent_increase_frequency': 'annual',
            'additional_requirements': ['employment_verification', 'additional_references']
        }
    elif risk_level == 'High':
        return {
            'security_deposit_months': 2,
            'lease_length_months': 6,
            'rent_increase_frequency': '6_months',
            'additional_requirements': ['co_signer', 'employment_verification', 'credit_check']
        }
    else:  # Very High
        return {
            'security_deposit_months': 2,
            'lease_length_months': 6,
            'rent_increase_frequency': '6_months',
            'additional_requirements': ['guarantor', 'extensive_background_check', 'first_last_deposit']
        }

def generate_monitoring_flags(risk_factors: List[str], tenant_data: Dict) -> List[Dict]:
    """
    Generate monitoring flags for ongoing tenant management
    """
    flags = []
    
    if 'Payment reliability concerns' in risk_factors:
        flags.append({
            'type': 'payment_monitoring',
            'description': 'Monitor payment timing and amounts closely',
            'frequency': 'weekly',
            'alert_threshold': '5_days_late'
        })
    
    if 'Financial stability issues' in risk_factors:
        flags.append({
            'type': 'employment_verification',
            'description': 'Verify continued employment quarterly',
            'frequency': 'quarterly',
            'alert_threshold': 'employment_change'
        })
    
    if 'Behavioral pattern concerns' in risk_factors:
        flags.append({
            'type': 'property_inspection',
            'description': 'Schedule additional property inspections',
            'frequency': 'quarterly',
            'alert_threshold': 'condition_decline'
        })
    
    return flags

def calculate_confidence_level(tenant_data: Dict, property_data: Dict, market_data: Dict) -> str:
    """
    Calculate confidence level of the risk assessment
    """
    data_completeness = 0
    total_possible = 10
    
    # Check tenant data completeness
    if tenant_data.get('payment_history'):
        data_completeness += 3
    if tenant_data.get('financial_info'):
        data_completeness += 3
    if tenant_data.get('behavioral_data'):
        data_completeness += 2
    if property_data:
        data_completeness += 1
    if market_data:
        data_completeness += 1
    
    confidence_percentage = (data_completeness / total_possible) * 100
    
    if confidence_percentage >= 80:
        return 'High'
    elif confidence_percentage >= 60:
        return 'Medium'
    else:
        return 'Low'

# Helper functions
def calculate_average_days_late(late_payments: List[Dict]) -> float:
    """Calculate average days late for late payments"""
    if not late_payments:
        return 0.0
    
    total_days_late = sum(payment.get('days_late', 0) for payment in late_payments)
    return total_days_late / len(late_payments)

def calculate_recent_payment_trend(payments: List[Dict]) -> float:
    """Calculate recent payment trend (positive = improving, negative = declining)"""
    if len(payments) < 6:
        return 0.0
    
    recent_payments = payments[-6:]  # Last 6 payments
    on_time_scores = [1 if p.get('status') == 'on_time' else 0 for p in recent_payments]
    
    # Simple trend calculation
    if len(on_time_scores) >= 3:
        recent_half = sum(on_time_scores[-3:]) / 3
        earlier_half = sum(on_time_scores[:3]) / 3
        return (recent_half - earlier_half) * 10
    
    return 0.0

def calculate_payment_consistency(payments: List[Dict]) -> float:
    """Calculate payment consistency score (0-1)"""
    if len(payments) < 3:
        return 0.5
    
    # Calculate variance in payment timing
    payment_days = []
    for payment in payments:
        try:
            payment_date = datetime.fromisoformat(payment.get('date', '2024-01-01'))
            payment_days.append(payment_date.day)
        except:
            continue
    
    if len(payment_days) < 3:
        return 0.5
    
    variance = np.var(payment_days)
    consistency_score = max(0, 1 - variance / 100)  # Normalize variance
    
    return consistency_score

def calculate_income_adequacy_score(rent_to_income_ratio: float) -> float:
    """Score income adequacy based on rent-to-income ratio"""
    if rent_to_income_ratio <= 0.25:
        return 100
    elif rent_to_income_ratio <= 0.30:
        return 90
    elif rent_to_income_ratio <= 0.35:
        return 75
    elif rent_to_income_ratio <= 0.40:
        return 60
    elif rent_to_income_ratio <= 0.50:
        return 40
    else:
        return 20

def calculate_debt_burden_score(debt_to_income_ratio: float) -> float:
    """Score debt burden based on total debt-to-income ratio"""
    if debt_to_income_ratio <= 0.36:
        return 100
    elif debt_to_income_ratio <= 0.43:
        return 80
    elif debt_to_income_ratio <= 0.50:
        return 60
    else:
        return max(0, 100 - (debt_to_income_ratio - 0.50) * 200)

def calculate_employment_stability_score(employment_months: int, employment_type: str) -> float:
    """Score employment stability"""
    base_score = min(100, employment_months * 2)  # 2 points per month, max 100
    
    # Employment type adjustments
    type_multipliers = {
        'full_time_permanent': 1.0,
        'full_time_contract': 0.9,
        'part_time': 0.7,
        'seasonal': 0.6,
        'self_employed': 0.8,
        'unemployed': 0.1,
        'unknown': 0.8
    }
    
    multiplier = type_multipliers.get(employment_type, 0.8)
    return base_score * multiplier

def normalize_credit_score(credit_score: int) -> float:
    """Normalize credit score to 0-100 scale"""
    if credit_score >= 750:
        return 100
    elif credit_score >= 700:
        return 85
    elif credit_score >= 650:
        return 70
    elif credit_score >= 600:
        return 55
    elif credit_score >= 550:
        return 40
    else:
        return max(0, (credit_score - 300) / 250 * 40)

def calculate_maintenance_behavior_score(maintenance_requests: List[Dict]) -> float:
    """Score maintenance request behavior patterns"""
    if not maintenance_requests:
        return 85.0  # Good default for no maintenance issues
    
    # Analyze request patterns
    emergency_requests = sum(1 for req in maintenance_requests if req.get('priority') == 'emergency')
    total_requests = len(maintenance_requests)
    
    # Score based on request frequency and type
    if total_requests <= 2:
        base_score = 90
    elif total_requests <= 5:
        base_score = 75
    elif total_requests <= 10:
        base_score = 60
    else:
        base_score = 40
    
    # Penalty for excessive emergency requests
    emergency_penalty = emergency_requests * 10
    
    return max(0, base_score - emergency_penalty)

def calculate_property_care_score(inspection_scores: List[int]) -> float:
    """Score property care based on inspection scores"""
    if not inspection_scores:
        return 75.0  # Neutral score
    
    recent_scores = inspection_scores[-3:] if len(inspection_scores) >= 3 else inspection_scores
    average_score = sum(recent_scores) / len(recent_scores)
    
    return min(100, average_score)

def calculate_rent_competitiveness_score(rent_ratio: float) -> float:
    """Score rent competitiveness (below market = higher score)"""
    if rent_ratio <= 0.9:  # 10% below market
        return 100
    elif rent_ratio <= 1.0:  # At market
        return 85
    elif rent_ratio <= 1.1:  # 10% above market
        return 70
    elif rent_ratio <= 1.2:  # 20% above market
        return 50
    else:  # More than 20% above market
        return 25
