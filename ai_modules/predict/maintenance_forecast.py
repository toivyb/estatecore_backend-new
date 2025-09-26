import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

def forecast_maintenance(equipment_data: Dict, property_data: Dict, historical_data: List[Dict]) -> Dict:
    """
    Advanced maintenance forecasting using multiple predictive models
    
    Args:
        equipment_data (dict): Equipment specifications and current state
        property_data (dict): Property characteristics affecting maintenance
        historical_data (list): Historical maintenance records
    
    Returns:
        dict: Maintenance predictions with timing, costs, and recommendations
    """
    
    # Initialize prediction models
    failure_prediction = predict_equipment_failures(equipment_data, historical_data)
    cost_forecast = forecast_maintenance_costs(equipment_data, historical_data, property_data)
    schedule_optimization = optimize_maintenance_schedule(failure_prediction, cost_forecast)
    
    # Seasonal adjustments
    seasonal_factors = calculate_seasonal_factors(historical_data, equipment_data)
    
    # Risk assessment
    risk_assessment = assess_maintenance_risks(equipment_data, failure_prediction)
    
    return {
        'predictions': failure_prediction,
        'cost_forecast': cost_forecast,
        'recommended_schedule': schedule_optimization,
        'seasonal_factors': seasonal_factors,
        'risk_assessment': risk_assessment,
        'confidence_score': calculate_prediction_confidence(equipment_data, historical_data),
        'last_updated': datetime.now().isoformat(),
        'forecast_period': '12_months'
    }

def predict_equipment_failures(equipment_data: Dict, historical_data: List[Dict]) -> Dict:
    """
    Predict equipment failure probabilities using survival analysis
    """
    predictions = {}
    
    for equipment_id, equipment in equipment_data.items():
        # Get equipment-specific history
        equipment_history = [
            record for record in historical_data 
            if record.get('equipment_id') == equipment_id
        ]
        
        # Calculate failure probability based on age and usage
        age_months = equipment.get('age_months', 0)
        usage_intensity = equipment.get('usage_intensity', 'medium')
        last_service = equipment.get('last_service_date')
        
        # Base failure rate calculation
        failure_probability = calculate_failure_probability(
            age_months, usage_intensity, equipment.get('type'), equipment_history
        )
        
        # Time to next likely failure
        expected_failure_time = calculate_expected_failure_time(
            equipment, equipment_history
        )
        
        # Failure mode analysis
        likely_failure_modes = predict_failure_modes(
            equipment, equipment_history
        )
        
        predictions[equipment_id] = {
            'failure_probability_30d': failure_probability['30_days'],
            'failure_probability_90d': failure_probability['90_days'],
            'failure_probability_12m': failure_probability['12_months'],
            'expected_failure_date': expected_failure_time,
            'likely_failure_modes': likely_failure_modes,
            'equipment_type': equipment.get('type'),
            'current_condition': assess_current_condition(equipment, equipment_history)
        }
    
    return predictions

def calculate_failure_probability(age_months: int, usage_intensity: str, equipment_type: str, history: List[Dict]) -> Dict:
    """
    Calculate failure probability using Weibull distribution and historical patterns
    """
    # Base failure rates by equipment type (failures per month)
    base_failure_rates = {
        'hvac': 0.02,
        'plumbing': 0.015,
        'electrical': 0.01,
        'appliances': 0.025,
        'flooring': 0.005,
        'roofing': 0.008
    }
    
    base_rate = base_failure_rates.get(equipment_type.lower(), 0.015)
    
    # Age factor (Weibull distribution parameters)
    shape_parameter = 2.5  # Increasing failure rate with age
    scale_parameter = 120  # Characteristic life in months
    
    age_factor = 1 - math.exp(-((age_months / scale_parameter) ** shape_parameter))
    
    # Usage intensity multipliers
    usage_multipliers = {
        'low': 0.7,
        'medium': 1.0,
        'high': 1.4,
        'very_high': 1.8
    }
    
    usage_factor = usage_multipliers.get(usage_intensity, 1.0)
    
    # Historical pattern adjustment
    if history:
        # Recent failure frequency
        recent_failures = [
            record for record in history 
            if (datetime.now() - datetime.fromisoformat(record.get('date', '2024-01-01'))).days <= 365
        ]
        
        if len(recent_failures) > 2:
            history_factor = min(2.0, len(recent_failures) * 0.3)
        else:
            history_factor = 1.0
    else:
        history_factor = 1.0
    
    # Calculate time-based probabilities
    base_monthly_prob = base_rate * age_factor * usage_factor * history_factor
    
    return {
        '30_days': min(0.95, base_monthly_prob),
        '90_days': min(0.95, base_monthly_prob * 3),
        '12_months': min(0.95, base_monthly_prob * 12)
    }

def calculate_expected_failure_time(equipment: Dict, history: List[Dict]) -> Optional[str]:
    """
    Calculate expected time to next failure based on current condition and trends
    """
    age_months = equipment.get('age_months', 0)
    equipment_type = equipment.get('type', 'unknown')
    
    # Typical lifespans by equipment type (in months)
    typical_lifespans = {
        'hvac': 180,  # 15 years
        'plumbing': 240,  # 20 years
        'electrical': 360,  # 30 years
        'appliances': 120,  # 10 years
        'flooring': 180,  # 15 years
        'roofing': 300   # 25 years
    }
    
    expected_lifespan = typical_lifespans.get(equipment_type.lower(), 180)
    
    # Adjust based on maintenance history
    if history:
        avg_maintenance_interval = calculate_avg_maintenance_interval(history)
        if avg_maintenance_interval < 6:  # Well maintained
            expected_lifespan *= 1.2
        elif avg_maintenance_interval > 18:  # Poorly maintained
            expected_lifespan *= 0.8
    
    remaining_life = max(0, expected_lifespan - age_months)
    
    if remaining_life > 0:
        expected_failure_date = datetime.now() + timedelta(days=remaining_life * 30)
        return expected_failure_date.isoformat()
    else:
        return None  # Equipment is past expected lifespan

def predict_failure_modes(equipment: Dict, history: List[Dict]) -> List[Dict]:
    """
    Predict most likely failure modes based on equipment type and history
    """
    equipment_type = equipment.get('type', 'unknown').lower()
    
    # Common failure modes by equipment type
    failure_modes = {
        'hvac': [
            {'mode': 'compressor_failure', 'probability': 0.3, 'severity': 'high'},
            {'mode': 'refrigerant_leak', 'probability': 0.25, 'severity': 'medium'},
            {'mode': 'fan_motor_failure', 'probability': 0.2, 'severity': 'medium'},
            {'mode': 'thermostat_malfunction', 'probability': 0.15, 'severity': 'low'},
            {'mode': 'ductwork_issues', 'probability': 0.1, 'severity': 'medium'}
        ],
        'plumbing': [
            {'mode': 'pipe_corrosion', 'probability': 0.35, 'severity': 'high'},
            {'mode': 'fixture_wear', 'probability': 0.25, 'severity': 'medium'},
            {'mode': 'water_pressure_issues', 'probability': 0.2, 'severity': 'medium'},
            {'mode': 'drain_blockage', 'probability': 0.15, 'severity': 'low'},
            {'mode': 'valve_failure', 'probability': 0.05, 'severity': 'medium'}
        ],
        'electrical': [
            {'mode': 'outlet_failure', 'probability': 0.3, 'severity': 'medium'},
            {'mode': 'circuit_overload', 'probability': 0.25, 'severity': 'high'},
            {'mode': 'switch_malfunction', 'probability': 0.2, 'severity': 'low'},
            {'mode': 'wiring_degradation', 'probability': 0.15, 'severity': 'high'},
            {'mode': 'breaker_failure', 'probability': 0.1, 'severity': 'medium'}
        ]
    }
    
    default_modes = [
        {'mode': 'general_wear', 'probability': 0.5, 'severity': 'medium'},
        {'mode': 'component_failure', 'probability': 0.3, 'severity': 'medium'},
        {'mode': 'maintenance_required', 'probability': 0.2, 'severity': 'low'}
    ]
    
    base_modes = failure_modes.get(equipment_type, default_modes)
    
    # Adjust probabilities based on history
    if history:
        for mode in base_modes:
            historical_occurrences = sum(
                1 for record in history 
                if mode['mode'].lower() in record.get('description', '').lower()
            )
            
            if historical_occurrences > 0:
                mode['probability'] *= (1 + historical_occurrences * 0.2)
    
    return sorted(base_modes, key=lambda x: x['probability'], reverse=True)

def forecast_maintenance_costs(equipment_data: Dict, historical_data: List[Dict], property_data: Dict) -> Dict:
    """
    Forecast maintenance costs for the next 12 months
    """
    monthly_forecasts = []
    total_annual_cost = 0
    
    for month in range(1, 13):
        month_forecast = forecast_monthly_costs(
            equipment_data, historical_data, month, property_data
        )
        monthly_forecasts.append(month_forecast)
        total_annual_cost += month_forecast['total_cost']
    
    return {
        'monthly_forecasts': monthly_forecasts,
        'annual_total': total_annual_cost,
        'quarterly_breakdown': calculate_quarterly_breakdown(monthly_forecasts),
        'cost_categories': calculate_cost_categories(monthly_forecasts),
        'budget_recommendations': generate_budget_recommendations(total_annual_cost, historical_data)
    }

def forecast_monthly_costs(equipment_data: Dict, historical_data: List[Dict], month: int, property_data: Dict) -> Dict:
    """
    Forecast maintenance costs for a specific month
    """
    # Seasonal adjustment factors
    seasonal_factors = {
        1: 1.2,   # January - heating issues
        2: 1.1,   # February
        3: 0.9,   # March
        4: 1.0,   # April - spring maintenance
        5: 0.8,   # May
        6: 1.1,   # June - AC preparation
        7: 1.3,   # July - peak AC usage
        8: 1.2,   # August
        9: 1.0,   # September
        10: 0.9,  # October
        11: 1.1,  # November - heating prep
        12: 1.2   # December - winter issues
    }
    
    base_monthly_cost = calculate_base_monthly_cost(equipment_data, historical_data)
    seasonal_adjustment = seasonal_factors.get(month, 1.0)
    
    # Property size adjustment
    property_size = property_data.get('square_footage', 1000)
    size_factor = property_size / 1000  # Base calculation on 1000 sq ft
    
    adjusted_cost = base_monthly_cost * seasonal_adjustment * size_factor
    
    return {
        'month': month,
        'base_cost': base_monthly_cost,
        'seasonal_factor': seasonal_adjustment,
        'size_factor': size_factor,
        'total_cost': round(adjusted_cost, 2),
        'confidence': 'medium'  # Would be calculated based on data quality
    }

def calculate_base_monthly_cost(equipment_data: Dict, historical_data: List[Dict]) -> float:
    """
    Calculate base monthly maintenance cost from historical data
    """
    if not historical_data:
        # Default estimates by equipment type if no history
        return 200.0
    
    # Calculate average monthly cost from last 24 months
    recent_cutoff = datetime.now() - timedelta(days=730)
    recent_costs = [
        float(record.get('cost', 0)) 
        for record in historical_data
        if datetime.fromisoformat(record.get('date', '2024-01-01')) > recent_cutoff
    ]
    
    if recent_costs:
        return sum(recent_costs) / len(recent_costs)
    else:
        return 200.0

def optimize_maintenance_schedule(failure_predictions: Dict, cost_forecasts: Dict) -> Dict:
    """
    Optimize maintenance scheduling based on predictions and costs
    """
    recommendations = []
    
    for equipment_id, prediction in failure_predictions.items():
        # High-risk equipment gets priority
        if prediction['failure_probability_90d'] > 0.3:
            priority = 'high'
            recommended_date = datetime.now() + timedelta(days=14)
        elif prediction['failure_probability_90d'] > 0.15:
            priority = 'medium' 
            recommended_date = datetime.now() + timedelta(days=30)
        else:
            priority = 'low'
            recommended_date = datetime.now() + timedelta(days=90)
        
        recommendations.append({
            'equipment_id': equipment_id,
            'priority': priority,
            'recommended_date': recommended_date.isoformat(),
            'estimated_cost': estimate_maintenance_cost(equipment_id, prediction),
            'reason': f"Failure probability: {prediction['failure_probability_90d']:.1%}"
        })
    
    return {
        'recommendations': sorted(recommendations, key=lambda x: x['priority']),
        'total_estimated_cost': sum(rec['estimated_cost'] for rec in recommendations),
        'schedule_optimization_notes': generate_schedule_notes(recommendations)
    }

def calculate_seasonal_factors(historical_data: List[Dict], equipment_data: Dict) -> Dict:
    """
    Calculate seasonal maintenance patterns
    """
    monthly_patterns = {month: [] for month in range(1, 13)}
    
    for record in historical_data:
        try:
            record_date = datetime.fromisoformat(record.get('date', '2024-01-01'))
            month = record_date.month
            cost = float(record.get('cost', 0))
            monthly_patterns[month].append(cost)
        except (ValueError, TypeError):
            continue
    
    seasonal_factors = {}
    overall_avg = sum(sum(costs) for costs in monthly_patterns.values()) / sum(len(costs) for costs in monthly_patterns.values()) if any(monthly_patterns.values()) else 1
    
    for month, costs in monthly_patterns.items():
        if costs:
            month_avg = sum(costs) / len(costs)
            seasonal_factors[month] = month_avg / overall_avg if overall_avg > 0 else 1.0
        else:
            seasonal_factors[month] = 1.0
    
    return seasonal_factors

def assess_maintenance_risks(equipment_data: Dict, failure_predictions: Dict) -> Dict:
    """
    Assess overall maintenance risks for the property
    """
    high_risk_equipment = [
        eq_id for eq_id, pred in failure_predictions.items()
        if pred['failure_probability_90d'] > 0.3
    ]
    
    medium_risk_equipment = [
        eq_id for eq_id, pred in failure_predictions.items()
        if 0.15 < pred['failure_probability_90d'] <= 0.3
    ]
    
    risk_level = 'low'
    if len(high_risk_equipment) > 2:
        risk_level = 'high'
    elif len(high_risk_equipment) > 0 or len(medium_risk_equipment) > 3:
        risk_level = 'medium'
    
    return {
        'overall_risk_level': risk_level,
        'high_risk_equipment': high_risk_equipment,
        'medium_risk_equipment': medium_risk_equipment,
        'risk_mitigation_strategies': generate_risk_mitigation_strategies(high_risk_equipment, medium_risk_equipment),
        'estimated_downtime_risk': calculate_downtime_risk(failure_predictions)
    }

def calculate_prediction_confidence(equipment_data: Dict, historical_data: List[Dict]) -> str:
    """
    Calculate confidence level of predictions based on data quality
    """
    data_points = len(historical_data)
    equipment_coverage = len([eq for eq in equipment_data.values() if eq.get('age_months')])
    
    score = 0
    if data_points >= 24:
        score += 40
    elif data_points >= 12:
        score += 25
    elif data_points >= 6:
        score += 15
    
    if equipment_coverage >= len(equipment_data) * 0.8:
        score += 35
    elif equipment_coverage >= len(equipment_data) * 0.6:
        score += 25
    elif equipment_coverage >= len(equipment_data) * 0.4:
        score += 15
    
    # Recent data bonus
    recent_data = [
        record for record in historical_data
        if (datetime.now() - datetime.fromisoformat(record.get('date', '2024-01-01'))).days <= 90
    ]
    
    if len(recent_data) >= 3:
        score += 25
    elif len(recent_data) >= 1:
        score += 15
    
    if score >= 80:
        return 'high'
    elif score >= 60:
        return 'medium'
    else:
        return 'low'

# Helper functions
def assess_current_condition(equipment: Dict, history: List[Dict]) -> str:
    """Assess current equipment condition"""
    age_months = equipment.get('age_months', 0)
    last_service = equipment.get('last_service_date')
    
    if age_months < 12:
        return 'excellent'
    elif age_months < 36:
        return 'good'
    elif age_months < 72:
        return 'fair'
    else:
        return 'poor'

def calculate_avg_maintenance_interval(history: List[Dict]) -> float:
    """Calculate average time between maintenance events"""
    if len(history) < 2:
        return 12.0  # Default
    
    dates = sorted([datetime.fromisoformat(record.get('date', '2024-01-01')) for record in history])
    intervals = [(dates[i] - dates[i-1]).days / 30 for i in range(1, len(dates))]
    
    return sum(intervals) / len(intervals) if intervals else 12.0

def calculate_quarterly_breakdown(monthly_forecasts: List[Dict]) -> List[Dict]:
    """Break down annual forecast into quarters"""
    quarters = []
    for q in range(4):
        start_month = q * 3
        quarter_months = monthly_forecasts[start_month:start_month + 3]
        quarters.append({
            'quarter': q + 1,
            'total_cost': sum(month['total_cost'] for month in quarter_months),
            'months': quarter_months
        })
    return quarters

def calculate_cost_categories(monthly_forecasts: List[Dict]) -> Dict:
    """Categorize costs by type"""
    return {
        'preventive': sum(month['total_cost'] * 0.3 for month in monthly_forecasts),
        'corrective': sum(month['total_cost'] * 0.5 for month in monthly_forecasts),
        'emergency': sum(month['total_cost'] * 0.2 for month in monthly_forecasts)
    }

def generate_budget_recommendations(annual_total: float, historical_data: List[Dict]) -> List[str]:
    """Generate budget planning recommendations"""
    recommendations = []
    
    if annual_total > 5000:
        recommendations.append("Consider setting up a monthly maintenance reserve fund")
    
    recommendations.append(f"Budget approximately ${annual_total/12:.0f} per month for maintenance")
    recommendations.append("Plan for 20% buffer for unexpected repairs")
    
    return recommendations

def estimate_maintenance_cost(equipment_id: str, prediction: Dict) -> float:
    """Estimate maintenance cost for specific equipment"""
    base_costs = {
        'hvac': 500,
        'plumbing': 300,
        'electrical': 200,
        'appliances': 250
    }
    
    equipment_type = prediction.get('equipment_type', 'appliances')
    base_cost = base_costs.get(equipment_type.lower(), 250)
    
    # Adjust for failure probability
    probability_factor = 1 + prediction['failure_probability_90d']
    
    return base_cost * probability_factor

def generate_schedule_notes(recommendations: List[Dict]) -> List[str]:
    """Generate scheduling optimization notes"""
    notes = []
    high_priority_count = sum(1 for rec in recommendations if rec['priority'] == 'high')
    
    if high_priority_count > 0:
        notes.append(f"{high_priority_count} equipment items require immediate attention")
    
    notes.append("Schedule preventive maintenance during low-occupancy periods")
    notes.append("Group maintenance tasks by vendor specialty to reduce costs")
    
    return notes

def generate_risk_mitigation_strategies(high_risk: List[str], medium_risk: List[str]) -> List[str]:
    """Generate risk mitigation strategies"""
    strategies = []
    
    if high_risk:
        strategies.append("Immediate inspection and preventive maintenance for high-risk equipment")
        strategies.append("Consider equipment replacement if repair costs exceed 60% of replacement cost")
    
    if medium_risk:
        strategies.append("Schedule preventive maintenance within 30-60 days for medium-risk equipment")
    
    strategies.append("Maintain emergency repair fund for unexpected failures")
    strategies.append("Establish relationships with reliable maintenance vendors")
    
    return strategies

def calculate_downtime_risk(failure_predictions: Dict) -> str:
    """Calculate risk of equipment downtime"""
    high_impact_failures = 0
    
    for equipment_id, prediction in failure_predictions.items():
        if prediction['failure_probability_90d'] > 0.3:
            equipment_type = prediction.get('equipment_type', '').lower()
            if equipment_type in ['hvac', 'plumbing', 'electrical']:
                high_impact_failures += 1
    
    if high_impact_failures >= 2:
        return 'high'
    elif high_impact_failures == 1:
        return 'medium'
    else:
        return 'low'
