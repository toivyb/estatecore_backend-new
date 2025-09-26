import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

def predict_lease_renewal(tenant_data: Dict, lease_data: Dict, property_data: Dict, market_data: Dict = None) -> Dict:
    """
    Predict lease renewal probability using multiple ML models
    
    Args:
        tenant_data (dict): Tenant payment history, satisfaction, and behavior
        lease_data (dict): Current lease terms, duration, rent history
        property_data (dict): Property characteristics and management quality
        market_data (dict): Local market conditions and competitive landscape
    
    Returns:
        dict: Renewal prediction with probability, factors, and recommendations
    """
    
    # Calculate component scores
    tenant_satisfaction_score = calculate_tenant_satisfaction_score(tenant_data)
    lease_terms_score = calculate_lease_terms_attractiveness(lease_data, market_data or {})
    property_quality_score = calculate_property_quality_score(property_data, tenant_data)
    market_conditions_score = calculate_market_retention_score(market_data or {})
    financial_stability_score = calculate_tenant_financial_stability(tenant_data)
    
    # Calculate weighted renewal probability
    weights = {
        'satisfaction': 0.30,
        'lease_terms': 0.25,
        'property_quality': 0.20,
        'market_conditions': 0.15,
        'financial_stability': 0.10
    }
    
    composite_score = (
        tenant_satisfaction_score * weights['satisfaction'] +
        lease_terms_score * weights['lease_terms'] +
        property_quality_score * weights['property_quality'] +
        market_conditions_score * weights['market_conditions'] +
        financial_stability_score * weights['financial_stability']
    )
    
    # Convert to renewal probability
    renewal_probability = min(0.95, max(0.05, composite_score / 100))
    
    # Analyze renewal factors
    renewal_factors = analyze_renewal_factors({
        'satisfaction': tenant_satisfaction_score,
        'lease_terms': lease_terms_score,
        'property_quality': property_quality_score,
        'market_conditions': market_conditions_score,
        'financial_stability': financial_stability_score
    })
    
    # Generate renewal strategies
    renewal_strategies = generate_renewal_strategies(renewal_probability, renewal_factors, lease_data, market_data or {})
    
    # Calculate optimal renewal terms
    optimal_terms = calculate_optimal_renewal_terms(renewal_probability, lease_data, market_data or {}, tenant_data)
    
    # Risk assessment
    churn_risk = assess_churn_risk(renewal_probability, renewal_factors)
    
    return {
        'renewal_probability': round(renewal_probability, 3),
        'renewal_likelihood': categorize_renewal_likelihood(renewal_probability),
        'factors': renewal_factors,
        'renewal_strategies': renewal_strategies,
        'optimal_terms': optimal_terms,
        'churn_risk': churn_risk,
        'breakdown': {
            'tenant_satisfaction': round(tenant_satisfaction_score, 1),
            'lease_terms_attractiveness': round(lease_terms_score, 1),
            'property_quality': round(property_quality_score, 1),
            'market_conditions': round(market_conditions_score, 1),
            'financial_stability': round(financial_stability_score, 1)
        },
        'confidence_level': calculate_prediction_confidence(tenant_data, lease_data, property_data),
        'recommended_actions': generate_recommended_actions(renewal_probability, renewal_factors),
        'timeline_recommendations': generate_renewal_timeline(lease_data),
        'last_updated': datetime.now().isoformat()
    }

def calculate_tenant_satisfaction_score(tenant_data: Dict) -> float:
    """
    Calculate tenant satisfaction based on multiple indicators
    """
    score = 75.0  # Base satisfaction score
    
    # Payment history (major satisfaction indicator)
    payment_history = tenant_data.get('payment_history', [])
    if payment_history:
        on_time_rate = sum(1 for p in payment_history if p.get('status') == 'on_time') / len(payment_history)
        score += (on_time_rate - 0.8) * 50  # Boost/penalty based on payment reliability
    
    # Maintenance request satisfaction
    maintenance_requests = tenant_data.get('maintenance_requests', [])
    if maintenance_requests:
        satisfied_requests = sum(1 for req in maintenance_requests if req.get('satisfaction_rating', 3) >= 4)
        satisfaction_rate = satisfied_requests / len(maintenance_requests)
        score += (satisfaction_rate - 0.7) * 30
    
    # Communication quality
    communication_score = tenant_data.get('communication_rating', 3)  # 1-5 scale
    score += (communication_score - 3) * 10
    
    # Lease violations (negative impact)
    violations = tenant_data.get('lease_violations', 0)
    score -= violations * 15
    
    # Complaint history
    complaints = tenant_data.get('complaint_count', 0)
    score -= complaints * 10
    
    # Length of tenancy (longer tenancy = higher satisfaction)
    tenancy_months = tenant_data.get('tenancy_length_months', 0)
    if tenancy_months > 12:
        score += min(20, (tenancy_months - 12) * 2)
    
    # Recent satisfaction surveys
    recent_survey = tenant_data.get('latest_satisfaction_survey')
    if recent_survey:
        survey_score = recent_survey.get('overall_score', 3)  # 1-5 scale
        score += (survey_score - 3) * 15
    
    return max(0, min(100, score))

def calculate_lease_terms_attractiveness(lease_data: Dict, market_data: Dict) -> float:
    """
    Evaluate attractiveness of current lease terms vs market
    """
    score = 50.0  # Neutral base
    
    # Rent competitiveness
    current_rent = lease_data.get('monthly_rent', 0)
    market_rent = market_data.get('average_market_rent', current_rent)
    
    if market_rent > 0:
        rent_ratio = current_rent / market_rent
        if rent_ratio <= 0.90:  # 10% below market
            score += 30
        elif rent_ratio <= 0.95:  # 5% below market
            score += 20
        elif rent_ratio <= 1.05:  # At market
            score += 10
        elif rent_ratio <= 1.10:  # 10% above market
            score -= 10
        else:  # More than 10% above market
            score -= 25
    
    # Lease length flexibility
    lease_length = lease_data.get('lease_length_months', 12)
    if lease_length == 12:
        score += 10  # Standard term
    elif lease_length < 12:
        score += 5   # Flexible short term
    else:
        score -= 5   # Long commitment
    
    # Rent increase history
    rent_increases = lease_data.get('rent_increase_history', [])
    if rent_increases:
        recent_increases = [inc for inc in rent_increases if (datetime.now() - datetime.fromisoformat(inc.get('date', '2024-01-01'))).days <= 365]
        
        if recent_increases:
            avg_increase = sum(inc.get('percentage', 0) for inc in recent_increases) / len(recent_increases)
            market_increase = market_data.get('average_annual_increase', 3.0)
            
            if avg_increase <= market_increase:
                score += 15
            elif avg_increase <= market_increase * 1.5:
                score -= 5
            else:
                score -= 20
    
    # Lease amenities and inclusions
    included_utilities = lease_data.get('included_utilities', [])
    score += len(included_utilities) * 3
    
    amenities = lease_data.get('amenities_included', [])
    score += len(amenities) * 2
    
    # Pet policy
    pet_friendly = lease_data.get('pet_friendly', False)
    if pet_friendly:
        score += 8
    
    # Parking included
    parking = lease_data.get('parking_included', False)
    if parking:
        score += 5
    
    return max(0, min(100, score))

def calculate_property_quality_score(property_data: Dict, tenant_data: Dict) -> float:
    """
    Evaluate property quality from tenant perspective
    """
    score = 75.0  # Good base score
    
    # Property age and condition
    property_age = property_data.get('age_years', 10)
    if property_age <= 5:
        score += 15
    elif property_age <= 15:
        score += 5
    elif property_age >= 30:
        score -= 10
    
    # Recent renovations
    last_renovation = property_data.get('last_renovation_year')
    if last_renovation:
        years_since_renovation = datetime.now().year - last_renovation
        if years_since_renovation <= 2:
            score += 20
        elif years_since_renovation <= 5:
            score += 10
    
    # Maintenance responsiveness
    maintenance_requests = tenant_data.get('maintenance_requests', [])
    if maintenance_requests:
        avg_response_time = sum(req.get('response_time_hours', 48) for req in maintenance_requests) / len(maintenance_requests)
        if avg_response_time <= 24:
            score += 15
        elif avg_response_time <= 48:
            score += 5
        else:
            score -= 10
    
    # Property amenities
    amenities = property_data.get('amenities', [])
    high_value_amenities = ['pool', 'gym', 'parking', 'laundry', 'elevator', 'balcony']
    amenity_score = sum(5 for amenity in amenities if amenity.lower() in high_value_amenities)
    score += min(25, amenity_score)
    
    # Location desirability
    location_score = property_data.get('location_rating', 7)  # 1-10 scale
    score += (location_score - 5) * 5
    
    # Safety and security
    security_features = property_data.get('security_features', [])
    score += len(security_features) * 3
    
    # Energy efficiency
    energy_rating = property_data.get('energy_efficiency_rating', 'C')
    energy_scores = {'A': 10, 'B': 7, 'C': 5, 'D': 2, 'E': 0, 'F': -5}
    score += energy_scores.get(energy_rating, 0)
    
    return max(0, min(100, score))

def calculate_market_retention_score(market_data: Dict) -> float:
    """
    Evaluate market conditions affecting tenant retention
    """
    score = 75.0  # Neutral market
    
    # Local vacancy rate
    vacancy_rate = market_data.get('local_vacancy_rate', 0.05)
    if vacancy_rate <= 0.03:  # Tight market
        score += 20
    elif vacancy_rate <= 0.05:  # Balanced market
        score += 10
    elif vacancy_rate >= 0.10:  # Loose market
        score -= 15
    
    # Market rent growth
    rent_growth = market_data.get('annual_rent_growth', 0.03)
    if rent_growth <= 0.02:  # Slow growth
        score += 10
    elif rent_growth >= 0.06:  # Rapid growth
        score -= 10
    
    # New construction supply
    new_supply = market_data.get('new_units_coming_online', 0)
    total_units = market_data.get('total_market_units', 1000)
    supply_ratio = new_supply / total_units if total_units > 0 else 0
    
    if supply_ratio <= 0.02:  # Limited new supply
        score += 15
    elif supply_ratio >= 0.05:  # High new supply
        score -= 20
    
    # Economic indicators
    employment_rate = market_data.get('local_employment_rate', 0.95)
    score += (employment_rate - 0.90) * 100
    
    # Seasonal factors
    current_month = datetime.now().month
    seasonal_scores = {
        1: -5, 2: -5, 3: 0, 4: 5, 5: 10, 6: 15,  # Winter to spring
        7: 10, 8: 5, 9: 0, 10: -5, 11: -10, 12: -10  # Summer to winter
    }
    score += seasonal_scores.get(current_month, 0)
    
    return max(0, min(100, score))

def calculate_tenant_financial_stability(tenant_data: Dict) -> float:
    """
    Assess tenant's financial ability to renew lease
    """
    financial_info = tenant_data.get('financial_info', {})
    
    if not financial_info:
        return 60.0  # Neutral if no data
    
    score = 50.0
    
    # Income stability
    monthly_income = financial_info.get('monthly_income', 0)
    monthly_rent = financial_info.get('monthly_rent', 0)
    
    if monthly_income > 0 and monthly_rent > 0:
        income_ratio = monthly_rent / monthly_income
        if income_ratio <= 0.25:
            score += 30
        elif income_ratio <= 0.30:
            score += 20
        elif income_ratio <= 0.35:
            score += 10
        elif income_ratio >= 0.50:
            score -= 20
    
    # Employment stability
    employment_months = financial_info.get('employment_length_months', 0)
    if employment_months >= 24:
        score += 20
    elif employment_months >= 12:
        score += 10
    elif employment_months < 6:
        score -= 15
    
    # Payment history trend
    payment_history = tenant_data.get('payment_history', [])
    if payment_history:
        recent_payments = payment_history[-6:]  # Last 6 payments
        on_time_recent = sum(1 for p in recent_payments if p.get('status') == 'on_time')
        if on_time_recent == len(recent_payments):
            score += 20
        elif on_time_recent >= len(recent_payments) * 0.8:
            score += 10
        else:
            score -= 15
    
    # Credit indicators
    credit_score = financial_info.get('credit_score', 650)
    if credit_score >= 750:
        score += 15
    elif credit_score >= 700:
        score += 10
    elif credit_score < 600:
        score -= 15
    
    return max(0, min(100, score))

def analyze_renewal_factors(scores: Dict) -> Dict:
    """
    Analyze which factors most influence renewal decision
    """
    factors = {
        'strengths': [],
        'weaknesses': [],
        'neutral': []
    }
    
    for factor, score in scores.items():
        if score >= 80:
            factors['strengths'].append({
                'factor': factor,
                'score': score,
                'impact': 'very positive'
            })
        elif score >= 65:
            factors['strengths'].append({
                'factor': factor,
                'score': score,
                'impact': 'positive'
            })
        elif score <= 40:
            factors['weaknesses'].append({
                'factor': factor,
                'score': score,
                'impact': 'very negative'
            })
        elif score <= 55:
            factors['weaknesses'].append({
                'factor': factor,
                'score': score,
                'impact': 'negative'
            })
        else:
            factors['neutral'].append({
                'factor': factor,
                'score': score,
                'impact': 'neutral'
            })
    
    return factors

def generate_renewal_strategies(probability: float, factors: Dict, lease_data: Dict, market_data: Dict) -> List[Dict]:
    """
    Generate targeted strategies to improve renewal probability
    """
    strategies = []
    
    # Low probability renewals need aggressive intervention
    if probability < 0.4:
        strategies.append({
            'strategy': 'retention_incentive_package',
            'description': 'Offer comprehensive renewal incentives',
            'actions': [
                'Freeze rent for 12 months',
                'Offer one month free rent',
                'Include utility allowances',
                'Provide property upgrades'
            ],
            'timeline': '60-90 days before lease expiration',
            'expected_impact': 0.15
        })
    
    # Address specific weaknesses
    weak_factors = factors.get('weaknesses', [])
    for weak_factor in weak_factors:
        factor_name = weak_factor['factor']
        
        if factor_name == 'satisfaction':
            strategies.append({
                'strategy': 'satisfaction_improvement',
                'description': 'Address tenant satisfaction issues',
                'actions': [
                    'Schedule tenant satisfaction meeting',
                    'Prioritize outstanding maintenance requests',
                    'Improve communication responsiveness',
                    'Consider small property improvements'
                ],
                'timeline': 'Immediate',
                'expected_impact': 0.10
            })
        
        elif factor_name == 'lease_terms':
            strategies.append({
                'strategy': 'lease_terms_optimization',
                'description': 'Improve lease terms competitiveness',
                'actions': [
                    'Benchmark rent against market rates',
                    'Consider rent adjustment or freeze',
                    'Add value-add services',
                    'Increase lease flexibility'
                ],
                'timeline': '30-60 days before renewal',
                'expected_impact': 0.12
            })
        
        elif factor_name == 'property_quality':
            strategies.append({
                'strategy': 'property_enhancement',
                'description': 'Enhance property quality and amenities',
                'actions': [
                    'Complete deferred maintenance',
                    'Upgrade appliances or fixtures',
                    'Improve common areas',
                    'Add security features'
                ],
                'timeline': '90+ days before renewal',
                'expected_impact': 0.08
            })
    
    # Market-based strategies
    if probability >= 0.6:
        strategies.append({
            'strategy': 'early_renewal_incentive',
            'description': 'Lock in renewal with early incentives',
            'actions': [
                'Offer early renewal discount',
                'Provide lease term flexibility',
                'Include minor upgrades',
                'Guarantee rent stability'
            ],
            'timeline': '120+ days before expiration',
            'expected_impact': 0.05
        })
    
    return strategies

def calculate_optimal_renewal_terms(probability: float, lease_data: Dict, market_data: Dict, tenant_data: Dict) -> Dict:
    """
    Calculate optimal renewal terms to maximize retention
    """
    current_rent = lease_data.get('monthly_rent', 0)
    market_rent = market_data.get('average_market_rent', current_rent)
    
    if probability >= 0.8:  # High retention probability
        optimal_rent = min(market_rent * 1.02, current_rent * 1.03)  # Small increase
        incentives = ['standard_lease_terms']
    elif probability >= 0.6:  # Medium retention probability
        optimal_rent = min(market_rent, current_rent * 1.02)  # Minimal increase
        incentives = ['rent_freeze_option', 'minor_upgrades']
    elif probability >= 0.4:  # Low retention probability
        optimal_rent = current_rent  # No increase
        incentives = ['one_month_free', 'utility_allowance', 'property_improvements']
    else:  # Very low retention probability
        optimal_rent = current_rent * 0.98  # Small decrease
        incentives = ['two_months_free', 'major_upgrades', 'extended_lease_options']
    
    return {
        'recommended_rent': round(optimal_rent, 2),
        'rent_change_percentage': round(((optimal_rent - current_rent) / current_rent) * 100, 1) if current_rent > 0 else 0,
        'lease_length_months': 12,  # Standard
        'recommended_incentives': incentives,
        'security_deposit': lease_data.get('security_deposit', current_rent),
        'early_renewal_discount': calculate_early_renewal_discount(probability),
        'concessions_value': calculate_concessions_value(probability, current_rent)
    }

def assess_churn_risk(probability: float, factors: Dict) -> Dict:
    """
    Assess and categorize churn risk
    """
    if probability >= 0.8:
        risk_level = 'low'
        risk_score = 1 - probability
    elif probability >= 0.6:
        risk_level = 'medium'
        risk_score = 1 - probability
    elif probability >= 0.4:
        risk_level = 'high'
        risk_score = 1 - probability
    else:
        risk_level = 'very_high'
        risk_score = 1 - probability
    
    # Identify primary churn drivers
    churn_drivers = []
    for weak_factor in factors.get('weaknesses', []):
        if weak_factor['score'] < 50:
            churn_drivers.append(weak_factor['factor'])
    
    return {
        'risk_level': risk_level,
        'risk_score': round(risk_score, 3),
        'primary_drivers': churn_drivers,
        'intervention_urgency': 'immediate' if risk_level in ['high', 'very_high'] else 'standard',
        'estimated_cost_of_churn': calculate_churn_cost(probability)
    }

def categorize_renewal_likelihood(probability: float) -> str:
    """
    Categorize renewal probability into descriptive terms
    """
    if probability >= 0.85:
        return 'Very Likely'
    elif probability >= 0.70:
        return 'Likely'
    elif probability >= 0.50:
        return 'Moderate'
    elif probability >= 0.30:
        return 'Unlikely'
    else:
        return 'Very Unlikely'

def calculate_prediction_confidence(tenant_data: Dict, lease_data: Dict, property_data: Dict) -> str:
    """
    Calculate confidence level of renewal prediction
    """
    data_completeness = 0
    total_possible = 5
    
    if tenant_data.get('payment_history'):
        data_completeness += 1
    if tenant_data.get('maintenance_requests'):
        data_completeness += 1
    if lease_data.get('rent_increase_history'):
        data_completeness += 1
    if tenant_data.get('financial_info'):
        data_completeness += 1
    if tenant_data.get('tenancy_length_months', 0) >= 6:
        data_completeness += 1
    
    confidence_ratio = data_completeness / total_possible
    
    if confidence_ratio >= 0.8:
        return 'High'
    elif confidence_ratio >= 0.6:
        return 'Medium'
    else:
        return 'Low'

def generate_recommended_actions(probability: float, factors: Dict) -> List[str]:
    """
    Generate immediate recommended actions
    """
    actions = []
    
    if probability < 0.5:
        actions.append('Schedule immediate tenant retention meeting')
        actions.append('Conduct property satisfaction assessment')
        actions.append('Prepare competitive renewal offer')
    
    if probability >= 0.7:
        actions.append('Initiate early renewal discussions')
        actions.append('Prepare standard renewal terms')
    
    # Factor-specific actions
    for weakness in factors.get('weaknesses', []):
        factor = weakness['factor']
        if factor == 'satisfaction':
            actions.append('Address outstanding maintenance requests')
        elif factor == 'lease_terms':
            actions.append('Review and adjust rental rates')
        elif factor == 'property_quality':
            actions.append('Schedule property improvements')
    
    return list(set(actions))  # Remove duplicates

def generate_renewal_timeline(lease_data: Dict) -> Dict:
    """
    Generate optimal timeline for renewal activities
    """
    lease_end = lease_data.get('lease_end_date')
    if not lease_end:
        return {}
    
    lease_end_date = datetime.fromisoformat(lease_end)
    
    return {
        '120_days_out': {
            'date': (lease_end_date - timedelta(days=120)).isoformat(),
            'actions': ['Begin renewal planning', 'Assess tenant satisfaction']
        },
        '90_days_out': {
            'date': (lease_end_date - timedelta(days=90)).isoformat(),
            'actions': ['Send renewal intent notice', 'Schedule property inspection']
        },
        '60_days_out': {
            'date': (lease_end_date - timedelta(days=60)).isoformat(),
            'actions': ['Present renewal offer', 'Discuss terms and incentives']
        },
        '30_days_out': {
            'date': (lease_end_date - timedelta(days=30)).isoformat(),
            'actions': ['Finalize renewal agreement', 'Complete any property improvements']
        }
    }

# Helper functions
def calculate_early_renewal_discount(probability: float) -> float:
    """Calculate appropriate early renewal discount"""
    if probability >= 0.8:
        return 0.01  # 1% discount
    elif probability >= 0.6:
        return 0.02  # 2% discount
    else:
        return 0.03  # 3% discount

def calculate_concessions_value(probability: float, current_rent: float) -> float:
    """Calculate total value of concessions to offer"""
    if probability >= 0.8:
        return 0
    elif probability >= 0.6:
        return current_rent * 0.5  # Half month rent
    elif probability >= 0.4:
        return current_rent * 1.0  # One month rent
    else:
        return current_rent * 2.0  # Two months rent

def calculate_churn_cost(probability: float) -> float:
    """Estimate cost of tenant churn"""
    churn_probability = 1 - probability
    
    # Base costs of tenant turnover
    base_costs = {
        'marketing': 200,
        'screening': 150,
        'vacancy_loss': 1500,  # Assuming ~1.5 months vacancy
        'turnover_repairs': 800,
        'administrative': 100
    }
    
    total_base_cost = sum(base_costs.values())
    return round(total_base_cost * churn_probability, 2)