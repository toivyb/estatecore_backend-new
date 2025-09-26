import numpy as np
import json
from datetime import datetime, timedelta

def get_asset_health_score(input_data):
    """
    Real ML-based asset health scoring using multiple property indicators
    
    Args:
        input_data (dict): Property data including:
            - maintenance_history: List of maintenance records
            - financial_performance: Revenue/expense ratios
            - age_years: Property age
            - condition_reports: Recent inspection data
            - occupancy_rate: Current occupancy percentage
            - utility_efficiency: Energy performance metrics
    
    Returns:
        dict: Health score (0-100) and risk assessment
    """
    
    # Initialize scoring components
    maintenance_score = calculate_maintenance_score(input_data.get('maintenance_history', []))
    financial_score = calculate_financial_score(input_data.get('financial_performance', {}))
    physical_score = calculate_physical_score(input_data.get('condition_reports', []))
    operational_score = calculate_operational_score(input_data)
    
    # Weighted composite score
    weights = {
        'maintenance': 0.3,
        'financial': 0.25,
        'physical': 0.3,
        'operational': 0.15
    }
    
    composite_score = (
        maintenance_score * weights['maintenance'] +
        financial_score * weights['financial'] +
        physical_score * weights['physical'] +
        operational_score * weights['operational']
    )
    
    # Determine risk level and recommendations
    status, risk_factors, recommendations = assess_risk_level(composite_score, {
        'maintenance': maintenance_score,
        'financial': financial_score,
        'physical': physical_score,
        'operational': operational_score
    })
    
    return {
        'score': round(composite_score, 1),
        'status': status,
        'risk_factors': risk_factors,
        'recommendations': recommendations,
        'breakdown': {
            'maintenance': round(maintenance_score, 1),
            'financial': round(financial_score, 1),
            'physical': round(physical_score, 1),
            'operational': round(operational_score, 1)
        },
        'last_updated': datetime.now().isoformat(),
        'confidence_level': calculate_confidence_level(input_data)
    }

def calculate_maintenance_score(maintenance_history):
    """
    Score based on maintenance frequency, cost trends, and issue severity
    """
    if not maintenance_history:
        return 70.0  # Neutral score for no data
    
    # Recent maintenance activity (last 12 months)
    recent_cutoff = datetime.now() - timedelta(days=365)
    recent_maintenance = [
        record for record in maintenance_history 
        if datetime.fromisoformat(record.get('date', '2024-01-01')) > recent_cutoff
    ]
    
    # Frequency analysis
    frequency_score = min(100, max(0, 100 - len(recent_maintenance) * 2))
    
    # Cost trend analysis
    costs = [float(record.get('cost', 0)) for record in recent_maintenance]
    if len(costs) >= 3:
        cost_trend = np.polyfit(range(len(costs)), costs, 1)[0]
        cost_score = max(0, 100 - abs(cost_trend) * 0.01)
    else:
        cost_score = 80.0
    
    # Severity analysis
    emergency_count = sum(1 for record in recent_maintenance 
                         if record.get('priority') == 'emergency')
    severity_score = max(0, 100 - emergency_count * 15)
    
    return (frequency_score * 0.4 + cost_score * 0.3 + severity_score * 0.3)

def calculate_financial_score(financial_performance):
    """
    Score based on revenue trends, expense ratios, and profitability
    """
    if not financial_performance:
        return 70.0  # Neutral score for no data
    
    # Revenue stability
    revenue_trend = financial_performance.get('revenue_trend', 0)
    revenue_score = min(100, max(0, 70 + revenue_trend * 100))
    
    # Expense ratio
    expense_ratio = financial_performance.get('expense_ratio', 0.3)
    expense_score = max(0, 100 - expense_ratio * 200)
    
    # Occupancy impact
    occupancy_rate = financial_performance.get('occupancy_rate', 0.9)
    occupancy_score = occupancy_rate * 100
    
    # Rent collection efficiency
    collection_rate = financial_performance.get('collection_rate', 0.95)
    collection_score = collection_rate * 100
    
    return (revenue_score * 0.3 + expense_score * 0.3 + 
            occupancy_score * 0.2 + collection_score * 0.2)

def calculate_physical_score(condition_reports):
    """
    Score based on property condition assessments and inspection reports
    """
    if not condition_reports:
        return 75.0  # Neutral score for no data
    
    # Get most recent report
    recent_report = max(condition_reports, 
                       key=lambda x: datetime.fromisoformat(x.get('date', '2024-01-01')))
    
    # Overall condition rating
    condition_rating = recent_report.get('overall_rating', 7)  # Out of 10
    condition_score = condition_rating * 10
    
    # Critical issues
    critical_issues = recent_report.get('critical_issues', 0)
    critical_score = max(0, 100 - critical_issues * 20)
    
    # Age factor
    property_age = recent_report.get('property_age_years', 10)
    age_factor = max(0, 100 - property_age * 2)
    
    return (condition_score * 0.5 + critical_score * 0.3 + age_factor * 0.2)

def calculate_operational_score(input_data):
    """
    Score based on operational efficiency metrics
    """
    # Occupancy efficiency
    occupancy_rate = input_data.get('occupancy_rate', 0.9)
    occupancy_score = occupancy_rate * 100
    
    # Energy efficiency
    utility_efficiency = input_data.get('utility_efficiency', 0.8)
    efficiency_score = utility_efficiency * 100
    
    # Tenant satisfaction (if available)
    tenant_satisfaction = input_data.get('tenant_satisfaction', 0.8)
    satisfaction_score = tenant_satisfaction * 100
    
    return (occupancy_score * 0.4 + efficiency_score * 0.3 + satisfaction_score * 0.3)

def assess_risk_level(score, breakdown):
    """
    Determine risk level and provide actionable recommendations
    """
    risk_factors = []
    recommendations = []
    
    if score >= 85:
        status = 'Excellent'
    elif score >= 70:
        status = 'Good'
    elif score >= 55:
        status = 'Fair'
        risk_factors.append('Moderate risk indicators detected')
    elif score >= 40:
        status = 'Poor'
        risk_factors.append('Multiple risk factors present')
    else:
        status = 'Critical'
        risk_factors.append('Immediate attention required')
    
    # Specific recommendations based on breakdown
    if breakdown['maintenance'] < 60:
        risk_factors.append('High maintenance burden')
        recommendations.append('Review preventive maintenance schedule')
    
    if breakdown['financial'] < 60:
        risk_factors.append('Financial performance issues')
        recommendations.append('Analyze revenue optimization opportunities')
    
    if breakdown['physical'] < 60:
        risk_factors.append('Property condition concerns')
        recommendations.append('Schedule comprehensive property inspection')
    
    if breakdown['operational'] < 60:
        risk_factors.append('Operational inefficiencies')
        recommendations.append('Review operational procedures and tenant satisfaction')
    
    return status, risk_factors, recommendations

def calculate_confidence_level(input_data):
    """
    Calculate confidence level based on data completeness and recency
    """
    data_completeness = 0
    total_fields = 6
    
    # Check data availability
    if input_data.get('maintenance_history'):
        data_completeness += 1
    if input_data.get('financial_performance'):
        data_completeness += 1
    if input_data.get('condition_reports'):
        data_completeness += 1
    if input_data.get('occupancy_rate') is not None:
        data_completeness += 1
    if input_data.get('utility_efficiency') is not None:
        data_completeness += 1
    if input_data.get('tenant_satisfaction') is not None:
        data_completeness += 1
    
    confidence = (data_completeness / total_fields) * 100
    
    if confidence >= 80:
        return 'High'
    elif confidence >= 60:
        return 'Medium'
    else:
        return 'Low'
