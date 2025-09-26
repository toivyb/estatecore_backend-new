import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

def detect_revenue_leakage(property_data: Dict, market_data: Dict, historical_data: Dict) -> Dict:
    """
    Advanced revenue leakage detection using market analysis and optimization models
    
    Args:
        property_data (dict): Current property portfolio and rental data
        market_data (dict): Local market rates and trends
        historical_data (dict): Historical revenue and occupancy data
    
    Returns:
        dict: Comprehensive revenue leakage analysis with recommendations
    """
    
    # Initialize analysis components
    underpricing_analysis = analyze_rent_underpricing(property_data, market_data)
    vacancy_cost_analysis = analyze_vacancy_costs(property_data, historical_data)
    concession_analysis = analyze_concession_impact(property_data, historical_data)
    maintenance_revenue_impact = analyze_maintenance_revenue_impact(property_data, historical_data)
    
    # Calculate total revenue leakage
    total_leakage = calculate_total_revenue_leakage([
        underpricing_analysis,
        vacancy_cost_analysis, 
        concession_analysis,
        maintenance_revenue_impact
    ])
    
    # Generate optimization recommendations
    optimization_recommendations = generate_optimization_recommendations(
        underpricing_analysis, vacancy_cost_analysis, concession_analysis, maintenance_revenue_impact
    )
    
    # Market positioning analysis
    market_positioning = analyze_market_positioning(property_data, market_data)
    
    # ROI impact assessment
    roi_impact = calculate_roi_impact(total_leakage, property_data)
    
    return {
        'total_annual_leakage': total_leakage['annual_amount'],
        'monthly_leakage': total_leakage['monthly_amount'],
        'leakage_percentage': total_leakage['percentage_of_potential'],
        'leakage_sources': {
            'underpricing': underpricing_analysis,
            'vacancy_costs': vacancy_cost_analysis,
            'concessions': concession_analysis,
            'maintenance_impact': maintenance_revenue_impact
        },
        'optimization_recommendations': optimization_recommendations,
        'market_positioning': market_positioning,
        'roi_impact': roi_impact,
        'confidence_level': calculate_confidence_level(property_data, market_data, historical_data),
        'priority_actions': generate_priority_actions(underpricing_analysis, vacancy_cost_analysis),
        'last_updated': datetime.now().isoformat()
    }

def analyze_rent_underpricing(property_data: Dict, market_data: Dict) -> Dict:
    """
    Analyze rental rate underpricing compared to market rates
    """
    underpriced_units = []
    total_monthly_loss = 0
    units_analyzed = 0
    
    units = property_data.get('units', [])
    market_rates = market_data.get('comparable_rents', {})
    
    for unit in units:
        units_analyzed += 1
        current_rent = unit.get('current_rent', 0)
        unit_type = unit.get('type', 'unknown')
        square_footage = unit.get('square_footage', 1000)
        
        # Get market rate for similar units
        market_rate = get_market_rate_for_unit(unit, market_rates)
        
        # Calculate underpricing
        if market_rate > current_rent:
            monthly_loss = market_rate - current_rent
            annual_loss = monthly_loss * 12
            
            # Apply confidence adjustments
            confidence_factor = calculate_market_rate_confidence(unit, market_data)
            adjusted_loss = monthly_loss * confidence_factor
            
            total_monthly_loss += adjusted_loss
            
            underpriced_units.append({
                'unit_id': unit.get('id'),
                'unit_number': unit.get('number'),
                'current_rent': current_rent,
                'market_rate': market_rate,
                'monthly_loss': round(adjusted_loss, 2),
                'annual_loss': round(adjusted_loss * 12, 2),
                'underpricing_percentage': round(((market_rate - current_rent) / current_rent) * 100, 1) if current_rent > 0 else 0,
                'confidence_level': confidence_factor,
                'unit_type': unit_type,
                'square_footage': square_footage
            })
    
    # Calculate aggregate metrics
    average_underpricing = (total_monthly_loss / len(units)) if units else 0
    underpriced_count = len(underpriced_units)
    underpricing_rate = (underpriced_count / units_analyzed) if units_analyzed > 0 else 0
    
    return {
        'underpriced_units': underpriced_units,
        'total_monthly_loss': round(total_monthly_loss, 2),
        'total_annual_loss': round(total_monthly_loss * 12, 2),
        'units_affected': underpriced_count,
        'total_units_analyzed': units_analyzed,
        'underpricing_rate': round(underpricing_rate * 100, 1),
        'average_monthly_loss_per_unit': round(average_underpricing, 2),
        'severity': determine_underpricing_severity(underpricing_rate, average_underpricing)
    }

def analyze_vacancy_costs(property_data: Dict, historical_data: Dict) -> Dict:
    """
    Analyze revenue loss from extended vacancies
    """
    vacancy_analysis = []
    total_vacancy_cost = 0
    
    units = property_data.get('units', [])
    vacancy_history = historical_data.get('vacancy_periods', [])
    
    # Calculate average time to fill units
    avg_time_to_fill = calculate_average_time_to_fill(vacancy_history)
    
    # Identify current vacancies
    current_vacancies = [unit for unit in units if unit.get('status') == 'vacant']
    
    for vacancy in current_vacancies:
        unit_rent = vacancy.get('market_rent', vacancy.get('last_rent', 0))
        days_vacant = vacancy.get('days_vacant', 0)
        
        # Calculate actual cost
        monthly_cost = unit_rent
        actual_cost = (days_vacant / 30) * monthly_cost
        
        # Calculate opportunity cost vs. optimal timing
        optimal_vacancy_days = get_optimal_vacancy_duration(vacancy, historical_data)
        excess_vacancy_days = max(0, days_vacant - optimal_vacancy_days)
        opportunity_cost = (excess_vacancy_days / 30) * monthly_cost
        
        # Estimate turnover costs
        turnover_costs = estimate_turnover_costs(vacancy, historical_data)
        
        total_cost = actual_cost + turnover_costs
        total_vacancy_cost += total_cost
        
        vacancy_analysis.append({
            'unit_id': vacancy.get('id'),
            'unit_number': vacancy.get('number'),
            'days_vacant': days_vacant,
            'monthly_rent': monthly_cost,
            'actual_vacancy_cost': round(actual_cost, 2),
            'opportunity_cost': round(opportunity_cost, 2),
            'turnover_costs': round(turnover_costs, 2),
            'total_cost': round(total_cost, 2),
            'optimal_vacancy_days': optimal_vacancy_days,
            'excess_vacancy_days': excess_vacancy_days
        })
    
    # Calculate metrics
    avg_vacancy_cost = (total_vacancy_cost / len(current_vacancies)) if current_vacancies else 0
    
    return {
        'current_vacancies': vacancy_analysis,
        'total_vacancy_cost': round(total_vacancy_cost, 2),
        'average_cost_per_vacancy': round(avg_vacancy_cost, 2),
        'average_time_to_fill_days': avg_time_to_fill,
        'vacancy_rate': round((len(current_vacancies) / len(units)) * 100, 1) if units else 0,
        'annual_projected_cost': round(total_vacancy_cost * (365 / 30), 2),  # Annualized estimate
        'optimization_potential': calculate_vacancy_optimization_potential(vacancy_analysis)
    }

def analyze_concession_impact(property_data: Dict, historical_data: Dict) -> Dict:
    """
    Analyze revenue impact from rent concessions and incentives
    """
    concession_analysis = []
    total_concession_cost = 0
    
    units = property_data.get('units', [])
    concession_history = historical_data.get('concessions', [])
    
    # Current active concessions
    active_concessions = [unit for unit in units if unit.get('has_concession', False)]
    
    for unit in active_concessions:
        concession_details = unit.get('concession_details', {})
        base_rent = unit.get('base_rent', 0)
        effective_rent = unit.get('effective_rent', base_rent)
        
        monthly_concession_cost = base_rent - effective_rent
        concession_duration = concession_details.get('duration_months', 12)
        total_concession_value = monthly_concession_cost * concession_duration
        
        # Analyze concession necessity
        necessity_score = analyze_concession_necessity(unit, property_data, historical_data)
        
        total_concession_cost += total_concession_value
        
        concession_analysis.append({
            'unit_id': unit.get('id'),
            'unit_number': unit.get('number'),
            'concession_type': concession_details.get('type', 'unknown'),
            'base_rent': base_rent,
            'effective_rent': effective_rent,
            'monthly_discount': round(monthly_concession_cost, 2),
            'total_concession_value': round(total_concession_value, 2),
            'duration_months': concession_duration,
            'necessity_score': necessity_score,
            'potential_elimination': necessity_score < 0.6
        })
    
    # Calculate optimization potential
    unnecessary_concessions = [c for c in concession_analysis if c['potential_elimination']]
    optimization_savings = sum(c['total_concession_value'] for c in unnecessary_concessions)
    
    return {
        'active_concessions': concession_analysis,
        'total_concession_cost': round(total_concession_cost, 2),
        'units_with_concessions': len(active_concessions),
        'average_concession_value': round(total_concession_cost / len(active_concessions), 2) if active_concessions else 0,
        'unnecessary_concessions': unnecessary_concessions,
        'optimization_savings_potential': round(optimization_savings, 2),
        'concession_rate': round((len(active_concessions) / len(units)) * 100, 1) if units else 0
    }

def analyze_maintenance_revenue_impact(property_data: Dict, historical_data: Dict) -> Dict:
    """
    Analyze revenue loss from maintenance-related issues
    """
    maintenance_impact = []
    total_maintenance_loss = 0
    
    units = property_data.get('units', [])
    maintenance_history = historical_data.get('maintenance_records', [])
    
    # Identify units with maintenance-related revenue impacts
    for unit in units:
        unit_id = unit.get('id')
        unit_maintenance = [m for m in maintenance_history if m.get('unit_id') == unit_id]
        
        # Calculate rent reduction due to habitability issues
        habitability_issues = [m for m in unit_maintenance if m.get('affects_habitability', False)]
        rent_reduction = calculate_maintenance_rent_reduction(unit, habitability_issues)
        
        # Calculate vacancy extension due to maintenance delays
        maintenance_vacancy_extension = calculate_maintenance_vacancy_extension(unit, unit_maintenance)
        
        # Calculate tenant turnover due to maintenance issues
        maintenance_turnover_cost = calculate_maintenance_turnover_cost(unit, unit_maintenance, historical_data)
        
        total_impact = rent_reduction + maintenance_vacancy_extension + maintenance_turnover_cost
        
        if total_impact > 0:
            total_maintenance_loss += total_impact
            
            maintenance_impact.append({
                'unit_id': unit_id,
                'unit_number': unit.get('number'),
                'rent_reduction_loss': round(rent_reduction, 2),
                'vacancy_extension_loss': round(maintenance_vacancy_extension, 2),
                'turnover_cost': round(maintenance_turnover_cost, 2),
                'total_impact': round(total_impact, 2),
                'active_issues': len(habitability_issues),
                'preventability_score': calculate_preventability_score(unit_maintenance)
            })
    
    return {
        'units_affected': maintenance_impact,
        'total_annual_loss': round(total_maintenance_loss, 2),
        'average_loss_per_affected_unit': round(total_maintenance_loss / len(maintenance_impact), 2) if maintenance_impact else 0,
        'units_with_impact': len(maintenance_impact),
        'preventable_loss_percentage': calculate_preventable_loss_percentage(maintenance_impact),
        'most_costly_issues': get_most_costly_maintenance_issues(maintenance_impact)
    }

def calculate_total_revenue_leakage(leakage_sources: List[Dict]) -> Dict:
    """
    Calculate total revenue leakage across all sources
    """
    total_annual = 0
    
    # Sum up all leakage sources
    for source in leakage_sources:
        if 'total_annual_loss' in source:
            total_annual += source['total_annual_loss']
        elif 'annual_projected_cost' in source:
            total_annual += source['annual_projected_cost']
        elif 'total_concession_cost' in source:
            total_annual += source['total_concession_cost']
    
    monthly_amount = total_annual / 12
    
    # Calculate as percentage of potential revenue
    # This would need property portfolio total potential revenue
    total_potential_revenue = 500000  # Placeholder - would be calculated from property data
    leakage_percentage = (total_annual / total_potential_revenue) * 100 if total_potential_revenue > 0 else 0
    
    return {
        'annual_amount': round(total_annual, 2),
        'monthly_amount': round(monthly_amount, 2),
        'percentage_of_potential': round(leakage_percentage, 1)
    }

def generate_optimization_recommendations(underpricing: Dict, vacancy: Dict, concessions: Dict, maintenance: Dict) -> List[Dict]:
    """
    Generate prioritized recommendations for revenue optimization
    """
    recommendations = []
    
    # Rent optimization recommendations
    if underpricing.get('total_annual_loss', 0) > 1000:
        recommendations.append({
            'category': 'rent_optimization',
            'priority': 'high',
            'title': 'Implement Market Rate Adjustments',
            'description': f"Adjust rents for {underpricing.get('units_affected', 0)} underpriced units",
            'potential_annual_savings': underpricing.get('total_annual_loss', 0),
            'implementation_timeline': '30-90 days',
            'specific_actions': [
                'Conduct detailed market analysis for underpriced units',
                'Plan phased rent increases at lease renewals',
                'Consider value-add improvements to justify increases'
            ]
        })
    
    # Vacancy optimization recommendations
    if vacancy.get('optimization_potential', 0) > 500:
        recommendations.append({
            'category': 'vacancy_optimization',
            'priority': 'high',
            'title': 'Reduce Time-to-Fill for Vacant Units',
            'description': 'Optimize marketing and screening processes',
            'potential_annual_savings': vacancy.get('optimization_potential', 0),
            'implementation_timeline': '14-30 days',
            'specific_actions': [
                'Enhance online marketing presence',
                'Streamline application and approval process',
                'Adjust pricing strategy for faster fills'
            ]
        })
    
    # Concession optimization recommendations
    if concessions.get('optimization_savings_potential', 0) > 200:
        recommendations.append({
            'category': 'concession_optimization',
            'priority': 'medium',
            'title': 'Eliminate Unnecessary Concessions',
            'description': f"Review and eliminate {len(concessions.get('unnecessary_concessions', []))} unnecessary concessions",
            'potential_annual_savings': concessions.get('optimization_savings_potential', 0),
            'implementation_timeline': '60-120 days',
            'specific_actions': [
                'Review all active concessions for necessity',
                'Phase out concessions at lease renewals',
                'Implement value-based pricing strategy'
            ]
        })
    
    # Maintenance optimization recommendations
    preventable_loss = maintenance.get('total_annual_loss', 0) * (maintenance.get('preventable_loss_percentage', 0) / 100)
    if preventable_loss > 300:
        recommendations.append({
            'category': 'maintenance_optimization',
            'priority': 'medium',
            'title': 'Implement Preventive Maintenance Program',
            'description': 'Reduce revenue loss from preventable maintenance issues',
            'potential_annual_savings': round(preventable_loss, 2),
            'implementation_timeline': '90-180 days',
            'specific_actions': [
                'Establish preventive maintenance schedules',
                'Improve vendor response times',
                'Implement proactive inspections'
            ]
        })
    
    return sorted(recommendations, key=lambda x: x['potential_annual_savings'], reverse=True)

def analyze_market_positioning(property_data: Dict, market_data: Dict) -> Dict:
    """
    Analyze property positioning relative to market
    """
    portfolio_avg_rent = calculate_portfolio_average_rent(property_data)
    market_avg_rent = market_data.get('average_market_rent', portfolio_avg_rent)
    
    positioning_ratio = portfolio_avg_rent / market_avg_rent if market_avg_rent > 0 else 1.0
    
    if positioning_ratio < 0.9:
        positioning = 'below_market'
        recommendation = 'Consider strategic rent increases'
    elif positioning_ratio > 1.1:
        positioning = 'above_market'
        recommendation = 'Focus on value-add services to justify premium'
    else:
        positioning = 'market_rate'
        recommendation = 'Maintain competitive positioning'
    
    return {
        'portfolio_average_rent': round(portfolio_avg_rent, 2),
        'market_average_rent': round(market_avg_rent, 2),
        'positioning_ratio': round(positioning_ratio, 2),
        'positioning_category': positioning,
        'recommendation': recommendation,
        'competitive_percentile': calculate_competitive_percentile(portfolio_avg_rent, market_data)
    }

def calculate_roi_impact(total_leakage: Dict, property_data: Dict) -> Dict:
    """
    Calculate ROI impact of revenue leakage
    """
    annual_leakage = total_leakage.get('annual_amount', 0)
    total_property_value = property_data.get('total_portfolio_value', 1000000)  # Placeholder
    
    # Estimate impact on property value (using cap rate approximation)
    estimated_cap_rate = 0.06  # 6% cap rate assumption
    property_value_impact = annual_leakage / estimated_cap_rate
    
    # ROI impact percentage
    roi_impact_percentage = (property_value_impact / total_property_value) * 100
    
    return {
        'annual_revenue_loss': annual_leakage,
        'estimated_property_value_impact': round(property_value_impact, 2),
        'roi_impact_percentage': round(roi_impact_percentage, 2),
        'payback_period_months': calculate_optimization_payback_period(annual_leakage)
    }

def generate_priority_actions(underpricing: Dict, vacancy: Dict) -> List[Dict]:
    """
    Generate immediate priority actions
    """
    actions = []
    
    # Immediate rent adjustment opportunities
    high_impact_units = [
        unit for unit in underpricing.get('underpriced_units', [])
        if unit.get('annual_loss', 0) > 1000 and unit.get('confidence_level', 0) > 0.8
    ]
    
    if high_impact_units:
        actions.append({
            'action': 'immediate_rent_review',
            'priority': 1,
            'description': f'Review and adjust rents for {len(high_impact_units)} high-impact underpriced units',
            'potential_monthly_gain': sum(unit['monthly_loss'] for unit in high_impact_units),
            'timeline': '30 days'
        })
    
    # Vacancy filling priority
    long_term_vacancies = [
        v for v in vacancy.get('current_vacancies', [])
        if v.get('days_vacant', 0) > 30
    ]
    
    if long_term_vacancies:
        actions.append({
            'action': 'expedite_vacancy_filling',
            'priority': 2,
            'description': f'Focus on filling {len(long_term_vacancies)} long-term vacant units',
            'potential_monthly_gain': sum(v['monthly_rent'] for v in long_term_vacancies),
            'timeline': '14 days'
        })
    
    return actions

def calculate_confidence_level(property_data: Dict, market_data: Dict, historical_data: Dict) -> str:
    """
    Calculate confidence level of revenue leakage analysis
    """
    data_quality_score = 0
    
    # Property data completeness
    if property_data.get('units') and len(property_data['units']) > 0:
        data_quality_score += 30
    
    # Market data availability
    if market_data.get('comparable_rents'):
        data_quality_score += 25
    
    # Historical data depth
    if historical_data.get('vacancy_periods') and len(historical_data['vacancy_periods']) > 0:
        data_quality_score += 25
    
    # Recent data availability
    if has_recent_data(historical_data):
        data_quality_score += 20
    
    if data_quality_score >= 80:
        return 'High'
    elif data_quality_score >= 60:
        return 'Medium'
    else:
        return 'Low'

# Helper functions
def get_market_rate_for_unit(unit: Dict, market_rates: Dict) -> float:
    """Get appropriate market rate for a specific unit"""
    unit_type = unit.get('type', 'apartment')
    square_footage = unit.get('square_footage', 1000)
    
    # Use type-specific rates if available
    type_rates = market_rates.get(unit_type, {})
    if type_rates:
        # Interpolate based on square footage
        return interpolate_rate_by_size(square_footage, type_rates)
    
    # Fallback to average market rate
    return market_rates.get('average', 1200)

def calculate_market_rate_confidence(unit: Dict, market_data: Dict) -> float:
    """Calculate confidence in market rate comparison"""
    # Factors affecting confidence
    comparable_count = market_data.get('comparable_properties_count', 5)
    data_recency_days = market_data.get('data_age_days', 30)
    location_similarity = market_data.get('location_similarity_score', 0.8)
    
    confidence = min(1.0, comparable_count / 10) * 0.4
    confidence += max(0, (90 - data_recency_days) / 90) * 0.3
    confidence += location_similarity * 0.3
    
    return max(0.5, min(1.0, confidence))

def calculate_average_time_to_fill(vacancy_history: List[Dict]) -> float:
    """Calculate average time to fill vacant units"""
    if not vacancy_history:
        return 30.0  # Default assumption
    
    fill_times = [v.get('days_to_fill', 30) for v in vacancy_history if v.get('status') == 'filled']
    return statistics.mean(fill_times) if fill_times else 30.0

def get_optimal_vacancy_duration(unit: Dict, historical_data: Dict) -> int:
    """Get optimal vacancy duration for unit type"""
    unit_type = unit.get('type', 'apartment')
    
    # Base optimal times by unit type
    optimal_times = {
        'studio': 14,
        'apartment': 21,
        'townhouse': 28,
        'single_family': 35
    }
    
    return optimal_times.get(unit_type, 21)

def estimate_turnover_costs(unit: Dict, historical_data: Dict) -> float:
    """Estimate turnover costs for a unit"""
    base_costs = {
        'cleaning': 200,
        'painting': 300,
        'repairs': 250,
        'marketing': 100
    }
    
    return sum(base_costs.values())

def analyze_concession_necessity(unit: Dict, property_data: Dict, historical_data: Dict) -> float:
    """Analyze whether a concession is necessary (0-1 score)"""
    # Factors indicating necessity
    local_vacancy_rate = property_data.get('property_vacancy_rate', 0.05)
    unit_condition = unit.get('condition_score', 8) / 10
    market_competition = property_data.get('market_competition_level', 0.5)
    
    # Higher necessity score means more necessary
    necessity = local_vacancy_rate * 0.4 + (1 - unit_condition) * 0.3 + market_competition * 0.3
    
    return min(1.0, necessity)

def calculate_maintenance_rent_reduction(unit: Dict, habitability_issues: List[Dict]) -> float:
    """Calculate rent reduction due to habitability issues"""
    if not habitability_issues:
        return 0.0
    
    base_rent = unit.get('current_rent', 0)
    
    # Estimate reduction percentage based on issue severity
    total_reduction_percentage = 0
    for issue in habitability_issues:
        severity = issue.get('severity', 'medium')
        reduction_percentages = {
            'low': 0.02,
            'medium': 0.05,
            'high': 0.10,
            'critical': 0.20
        }
        total_reduction_percentage += reduction_percentages.get(severity, 0.05)
    
    total_reduction_percentage = min(0.30, total_reduction_percentage)  # Cap at 30%
    
    return base_rent * total_reduction_percentage * 12  # Annual impact

def calculate_maintenance_vacancy_extension(unit: Dict, maintenance_records: List[Dict]) -> float:
    """Calculate vacancy extension due to maintenance delays"""
    # Implementation would analyze maintenance-caused vacancy extensions
    return 0.0  # Placeholder

def calculate_maintenance_turnover_cost(unit: Dict, maintenance_records: List[Dict], historical_data: Dict) -> float:
    """Calculate turnover costs due to maintenance issues"""
    # Implementation would analyze maintenance-driven tenant turnover
    return 0.0  # Placeholder

def calculate_preventability_score(maintenance_records: List[Dict]) -> float:
    """Calculate what percentage of maintenance issues were preventable"""
    if not maintenance_records:
        return 0.0
    
    preventable_count = sum(1 for record in maintenance_records if record.get('preventable', False))
    return preventable_count / len(maintenance_records)

def calculate_preventable_loss_percentage(maintenance_impact: List[Dict]) -> float:
    """Calculate percentage of maintenance loss that was preventable"""
    if not maintenance_impact:
        return 0.0
    
    total_loss = sum(unit['total_impact'] for unit in maintenance_impact)
    preventable_loss = sum(
        unit['total_impact'] * unit['preventability_score'] 
        for unit in maintenance_impact
    )
    
    return (preventable_loss / total_loss * 100) if total_loss > 0 else 0.0

def get_most_costly_maintenance_issues(maintenance_impact: List[Dict]) -> List[Dict]:
    """Get the most costly maintenance issues"""
    return sorted(maintenance_impact, key=lambda x: x['total_impact'], reverse=True)[:5]

def calculate_vacancy_optimization_potential(vacancy_analysis: List[Dict]) -> float:
    """Calculate potential savings from vacancy optimization"""
    return sum(v.get('opportunity_cost', 0) for v in vacancy_analysis)

def calculate_portfolio_average_rent(property_data: Dict) -> float:
    """Calculate average rent across portfolio"""
    units = property_data.get('units', [])
    if not units:
        return 0.0
    
    total_rent = sum(unit.get('current_rent', 0) for unit in units if unit.get('status') != 'vacant')
    occupied_units = len([unit for unit in units if unit.get('status') != 'vacant'])
    
    return total_rent / occupied_units if occupied_units > 0 else 0.0

def calculate_competitive_percentile(portfolio_rent: float, market_data: Dict) -> int:
    """Calculate what percentile the portfolio rent represents in the market"""
    # Implementation would use market distribution data
    return 50  # Placeholder

def calculate_optimization_payback_period(annual_leakage: float) -> int:
    """Calculate payback period for optimization investments"""
    # Estimate implementation costs vs. savings
    estimated_implementation_cost = annual_leakage * 0.1  # 10% of annual leakage
    monthly_savings = annual_leakage / 12
    
    payback_months = estimated_implementation_cost / monthly_savings if monthly_savings > 0 else 12
    return min(24, max(1, int(payback_months)))

def has_recent_data(historical_data: Dict) -> bool:
    """Check if historical data includes recent information"""
    # Implementation would check data recency
    return True  # Placeholder

def interpolate_rate_by_size(square_footage: int, type_rates: Dict) -> float:
    """Interpolate market rate based on unit size"""
    # Implementation would interpolate rates based on size
    return type_rates.get('average', 1200)  # Placeholder

def determine_underpricing_severity(underpricing_rate: float, average_loss: float) -> str:
    """Determine severity of underpricing issue"""
    if underpricing_rate > 0.5 and average_loss > 200:
        return 'critical'
    elif underpricing_rate > 0.3 and average_loss > 100:
        return 'high'
    elif underpricing_rate > 0.2 or average_loss > 50:
        return 'medium'
    else:
        return 'low'
