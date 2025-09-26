import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

def forecast_utility_costs(property_data: Dict, historical_data: Dict, weather_data: Dict = None, market_data: Dict = None) -> Dict:
    """
    Forecast utility costs using machine learning and seasonal patterns
    
    Args:
        property_data (dict): Property characteristics affecting utility usage
        historical_data (dict): Historical utility bills and consumption data
        weather_data (dict): Weather patterns and climate data
        market_data (dict): Utility rates and market trends
    
    Returns:
        dict: Utility cost forecasts with breakdown by type and recommendations
    """
    
    # Generate forecasts for each utility type
    electricity_forecast = forecast_electricity_costs(property_data, historical_data, weather_data or {})
    gas_forecast = forecast_gas_costs(property_data, historical_data, weather_data or {})
    water_forecast = forecast_water_costs(property_data, historical_data)
    waste_forecast = forecast_waste_costs(property_data, historical_data)
    internet_forecast = forecast_internet_costs(property_data, market_data or {})
    
    # Calculate total forecasts
    total_forecast = calculate_total_utility_forecast([
        electricity_forecast,
        gas_forecast,
        water_forecast,
        waste_forecast,
        internet_forecast
    ])
    
    # Generate optimization recommendations
    optimization_recommendations = generate_utility_optimization_recommendations(
        electricity_forecast, gas_forecast, water_forecast, property_data
    )
    
    # Calculate cost variance and risk factors
    cost_variance = calculate_cost_variance(historical_data, total_forecast)
    risk_factors = assess_utility_cost_risks(property_data, historical_data, weather_data or {})
    
    # Seasonal analysis
    seasonal_patterns = analyze_seasonal_utility_patterns(historical_data)
    
    return {
        'total_forecast': total_forecast,
        'utility_breakdown': {
            'electricity': electricity_forecast,
            'gas': gas_forecast,
            'water': water_forecast,
            'waste': waste_forecast,
            'internet': internet_forecast
        },
        'optimization_recommendations': optimization_recommendations,
        'cost_variance_analysis': cost_variance,
        'risk_factors': risk_factors,
        'seasonal_patterns': seasonal_patterns,
        'efficiency_opportunities': identify_efficiency_opportunities(property_data, historical_data),
        'budget_recommendations': generate_budget_recommendations(total_forecast, cost_variance),
        'confidence_level': calculate_forecast_confidence(property_data, historical_data),
        'forecast_period': '12_months',
        'last_updated': datetime.now().isoformat()
    }

def forecast_electricity_costs(property_data: Dict, historical_data: Dict, weather_data: Dict) -> Dict:
    """
    Forecast electricity costs considering usage patterns, weather, and efficiency
    """
    monthly_forecasts = []
    
    # Base electricity usage factors
    base_usage_per_sqft = 10  # kWh per sq ft per month
    square_footage = property_data.get('square_footage', 1000)
    base_monthly_usage = base_usage_per_sqft * square_footage
    
    # Historical usage analysis
    historical_bills = historical_data.get('electricity_bills', [])
    if historical_bills:
        avg_monthly_usage = calculate_average_monthly_usage(historical_bills)
        base_monthly_usage = avg_monthly_usage
    
    # Property efficiency factors
    efficiency_rating = property_data.get('energy_efficiency_rating', 'C')
    efficiency_multipliers = {'A': 0.7, 'B': 0.8, 'C': 1.0, 'D': 1.2, 'E': 1.4, 'F': 1.6}
    efficiency_factor = efficiency_multipliers.get(efficiency_rating, 1.0)
    
    # HVAC system efficiency
    hvac_age = property_data.get('hvac_age_years', 10)
    hvac_efficiency = max(0.7, 1.0 - (hvac_age * 0.02))  # 2% efficiency loss per year
    
    # Calculate monthly forecasts
    for month in range(1, 13):
        # Seasonal usage factors
        seasonal_factor = get_seasonal_electricity_factor(month, weather_data)
        
        # Occupancy factor
        occupancy_rate = property_data.get('occupancy_rate', 0.9)
        occupancy_factor = 0.3 + (occupancy_rate * 0.7)  # Base load + occupancy load
        
        # Calculate usage and cost
        monthly_usage = (
            base_monthly_usage * 
            efficiency_factor * 
            hvac_efficiency * 
            seasonal_factor * 
            occupancy_factor
        )
        
        # Electricity rate (would come from market data)
        rate_per_kwh = calculate_electricity_rate(month, historical_data)
        monthly_cost = monthly_usage * rate_per_kwh
        
        # Add demand charges for commercial properties
        if property_data.get('property_type') == 'commercial':
            demand_charge = calculate_demand_charge(monthly_usage)
            monthly_cost += demand_charge
        
        monthly_forecasts.append({
            'month': month,
            'usage_kwh': round(monthly_usage, 1),
            'rate_per_kwh': round(rate_per_kwh, 4),
            'base_cost': round(monthly_cost, 2),
            'fees_and_taxes': round(monthly_cost * 0.15, 2),  # Typical fees/taxes
            'total_cost': round(monthly_cost * 1.15, 2),
            'seasonal_factor': round(seasonal_factor, 2)
        })
    
    annual_total = sum(month['total_cost'] for month in monthly_forecasts)
    
    return {
        'annual_total': round(annual_total, 2),
        'monthly_average': round(annual_total / 12, 2),
        'monthly_forecasts': monthly_forecasts,
        'peak_month': max(monthly_forecasts, key=lambda x: x['total_cost'])['month'],
        'lowest_month': min(monthly_forecasts, key=lambda x: x['total_cost'])['month'],
        'efficiency_rating': efficiency_rating,
        'optimization_potential': calculate_electricity_optimization_potential(property_data, annual_total)
    }

def forecast_gas_costs(property_data: Dict, historical_data: Dict, weather_data: Dict) -> Dict:
    """
    Forecast natural gas costs for heating and hot water
    """
    monthly_forecasts = []
    
    # Base gas usage factors
    base_usage_per_sqft = 0.5  # therms per sq ft per month (heating season)
    square_footage = property_data.get('square_footage', 1000)
    
    # Historical usage analysis
    historical_bills = historical_data.get('gas_bills', [])
    if historical_bills:
        avg_monthly_usage = calculate_average_monthly_usage(historical_bills, 'therms')
    else:
        avg_monthly_usage = base_usage_per_sqft * square_footage
    
    # Property factors
    insulation_rating = property_data.get('insulation_rating', 'average')
    insulation_multipliers = {'excellent': 0.7, 'good': 0.85, 'average': 1.0, 'poor': 1.3}
    insulation_factor = insulation_multipliers.get(insulation_rating, 1.0)
    
    # Heating system efficiency
    heating_system_age = property_data.get('heating_system_age', 10)
    heating_efficiency = max(0.6, 0.9 - (heating_system_age * 0.015))  # 1.5% efficiency loss per year
    
    for month in range(1, 13):
        # Seasonal heating demand
        heating_factor = get_seasonal_heating_factor(month, weather_data)
        
        # Base load for hot water (year-round)
        base_load_factor = 0.2  # 20% of usage is always base load
        
        # Calculate monthly usage
        heating_usage = avg_monthly_usage * heating_factor * insulation_factor / heating_efficiency
        base_usage = avg_monthly_usage * base_load_factor
        total_usage = heating_usage + base_usage
        
        # Gas rate
        gas_rate = calculate_gas_rate(month, historical_data)
        monthly_cost = total_usage * gas_rate
        
        monthly_forecasts.append({
            'month': month,
            'usage_therms': round(total_usage, 1),
            'heating_usage': round(heating_usage, 1),
            'base_usage': round(base_usage, 1),
            'rate_per_therm': round(gas_rate, 4),
            'base_cost': round(monthly_cost, 2),
            'fees_and_taxes': round(monthly_cost * 0.12, 2),
            'total_cost': round(monthly_cost * 1.12, 2),
            'heating_factor': round(heating_factor, 2)
        })
    
    annual_total = sum(month['total_cost'] for month in monthly_forecasts)
    
    return {
        'annual_total': round(annual_total, 2),
        'monthly_average': round(annual_total / 12, 2),
        'monthly_forecasts': monthly_forecasts,
        'peak_month': max(monthly_forecasts, key=lambda x: x['total_cost'])['month'],
        'lowest_month': min(monthly_forecasts, key=lambda x: x['total_cost'])['month'],
        'heating_efficiency': round(heating_efficiency, 2),
        'insulation_rating': insulation_rating,
        'optimization_potential': calculate_gas_optimization_potential(property_data, annual_total)
    }

def forecast_water_costs(property_data: Dict, historical_data: Dict) -> Dict:
    """
    Forecast water and sewer costs
    """
    monthly_forecasts = []
    
    # Base water usage factors
    base_usage_per_unit = 2500  # gallons per month per unit
    total_units = property_data.get('total_units', 1)
    occupancy_rate = property_data.get('occupancy_rate', 0.9)
    
    # Historical usage analysis
    historical_bills = historical_data.get('water_bills', [])
    if historical_bills:
        avg_monthly_usage = calculate_average_monthly_usage(historical_bills, 'gallons')
    else:
        avg_monthly_usage = base_usage_per_unit * total_units * occupancy_rate
    
    # Property factors
    fixture_efficiency = property_data.get('low_flow_fixtures', False)
    efficiency_factor = 0.8 if fixture_efficiency else 1.0
    
    # Landscaping water usage
    landscaping_factor = property_data.get('landscaping_irrigation', 0)  # 0-1 scale
    
    for month in range(1, 13):
        # Seasonal factors for landscaping
        irrigation_factor = get_seasonal_irrigation_factor(month)
        
        # Base indoor usage
        indoor_usage = avg_monthly_usage * efficiency_factor
        
        # Outdoor/irrigation usage
        outdoor_usage = indoor_usage * landscaping_factor * irrigation_factor
        
        total_usage = indoor_usage + outdoor_usage
        
        # Water rates (tiered pricing)
        water_cost = calculate_tiered_water_cost(total_usage)
        
        # Sewer charges (typically based on water usage)
        sewer_cost = total_usage * 0.003  # $3 per 1000 gallons typical
        
        total_cost = water_cost + sewer_cost
        
        monthly_forecasts.append({
            'month': month,
            'usage_gallons': round(total_usage, 0),
            'indoor_usage': round(indoor_usage, 0),
            'outdoor_usage': round(outdoor_usage, 0),
            'water_cost': round(water_cost, 2),
            'sewer_cost': round(sewer_cost, 2),
            'total_cost': round(total_cost, 2),
            'irrigation_factor': round(irrigation_factor, 2)
        })
    
    annual_total = sum(month['total_cost'] for month in monthly_forecasts)
    
    return {
        'annual_total': round(annual_total, 2),
        'monthly_average': round(annual_total / 12, 2),
        'monthly_forecasts': monthly_forecasts,
        'peak_month': max(monthly_forecasts, key=lambda x: x['total_cost'])['month'],
        'lowest_month': min(monthly_forecasts, key=lambda x: x['total_cost'])['month'],
        'fixture_efficiency': fixture_efficiency,
        'optimization_potential': calculate_water_optimization_potential(property_data, annual_total)
    }

def forecast_waste_costs(property_data: Dict, historical_data: Dict) -> Dict:
    """
    Forecast waste management costs
    """
    # Base waste costs
    total_units = property_data.get('total_units', 1)
    base_cost_per_unit = 25  # Monthly cost per unit
    
    # Service level factors
    recycling_service = property_data.get('recycling_service', True)
    bulk_pickup = property_data.get('bulk_pickup', False)
    
    base_monthly_cost = total_units * base_cost_per_unit
    
    if recycling_service:
        base_monthly_cost *= 1.1  # 10% increase for recycling
    
    if bulk_pickup:
        base_monthly_cost += 50  # Additional monthly fee
    
    # Annual rate increases
    annual_increase_rate = 0.03  # 3% typical annual increase
    
    monthly_forecasts = []
    for month in range(1, 13):
        # Seasonal factors (more waste in summer months due to landscaping)
        seasonal_factor = 1.0
        if month in [5, 6, 7, 8, 9]:  # May through September
            seasonal_factor = 1.15
        
        monthly_cost = base_monthly_cost * seasonal_factor
        
        if month > 1:  # Apply annual increase after first month
            monthly_cost *= (1 + annual_increase_rate * (month - 1) / 12)
        
        monthly_forecasts.append({
            'month': month,
            'base_cost': round(monthly_cost, 2),
            'seasonal_factor': round(seasonal_factor, 2),
            'total_cost': round(monthly_cost, 2)
        })
    
    annual_total = sum(month['total_cost'] for month in monthly_forecasts)
    
    return {
        'annual_total': round(annual_total, 2),
        'monthly_average': round(annual_total / 12, 2),
        'monthly_forecasts': monthly_forecasts,
        'services_included': {
            'recycling': recycling_service,
            'bulk_pickup': bulk_pickup
        },
        'optimization_potential': 0  # Limited optimization for waste costs
    }

def forecast_internet_costs(property_data: Dict, market_data: Dict) -> Dict:
    """
    Forecast internet and cable costs for provided services
    """
    internet_provided = property_data.get('internet_included', False)
    cable_provided = property_data.get('cable_included', False)
    
    if not internet_provided and not cable_provided:
        return {
            'annual_total': 0,
            'monthly_average': 0,
            'services_included': [],
            'optimization_potential': 0
        }
    
    # Base costs
    internet_cost = 75 if internet_provided else 0  # Monthly internet cost
    cable_cost = 45 if cable_provided else 0  # Monthly cable cost
    
    # Bundle discount
    if internet_provided and cable_provided:
        bundle_discount = 15  # Monthly bundle discount
    else:
        bundle_discount = 0
    
    monthly_cost = internet_cost + cable_cost - bundle_discount
    
    # Annual rate increases
    annual_increase = 0.04  # 4% typical annual increase for telecom services
    
    monthly_forecasts = []
    for month in range(1, 13):
        adjusted_cost = monthly_cost
        if month > 1:
            adjusted_cost *= (1 + annual_increase * (month - 1) / 12)
        
        monthly_forecasts.append({
            'month': month,
            'internet_cost': round(internet_cost * (1 + annual_increase * (month - 1) / 12), 2) if internet_provided else 0,
            'cable_cost': round(cable_cost * (1 + annual_increase * (month - 1) / 12), 2) if cable_provided else 0,
            'bundle_discount': round(bundle_discount, 2),
            'total_cost': round(adjusted_cost, 2)
        })
    
    annual_total = sum(month['total_cost'] for month in monthly_forecasts)
    
    return {
        'annual_total': round(annual_total, 2),
        'monthly_average': round(annual_total / 12, 2),
        'monthly_forecasts': monthly_forecasts,
        'services_included': {
            'internet': internet_provided,
            'cable': cable_provided,
            'bundle_discount': bundle_discount > 0
        },
        'optimization_potential': calculate_telecom_optimization_potential(monthly_cost)
    }

def calculate_total_utility_forecast(utility_forecasts: List[Dict]) -> Dict:
    """
    Calculate total utility cost forecast across all utilities
    """
    total_annual = sum(forecast['annual_total'] for forecast in utility_forecasts)
    monthly_totals = []
    
    for month in range(1, 13):
        monthly_total = sum(
            forecast['monthly_forecasts'][month-1]['total_cost'] 
            for forecast in utility_forecasts 
            if forecast.get('monthly_forecasts')
        )
        monthly_totals.append({
            'month': month,
            'total_cost': round(monthly_total, 2)
        })
    
    peak_month = max(monthly_totals, key=lambda x: x['total_cost'])
    lowest_month = min(monthly_totals, key=lambda x: x['total_cost'])
    
    return {
        'annual_total': round(total_annual, 2),
        'monthly_average': round(total_annual / 12, 2),
        'monthly_totals': monthly_totals,
        'peak_month': peak_month['month'],
        'peak_cost': peak_month['total_cost'],
        'lowest_month': lowest_month['month'],
        'lowest_cost': lowest_month['total_cost'],
        'cost_variance': round(peak_month['total_cost'] - lowest_month['total_cost'], 2)
    }

def generate_utility_optimization_recommendations(electricity: Dict, gas: Dict, water: Dict, property_data: Dict) -> List[Dict]:
    """
    Generate recommendations for utility cost optimization
    """
    recommendations = []
    
    # Electricity optimization
    if electricity.get('optimization_potential', 0) > 200:
        recommendations.append({
            'utility': 'electricity',
            'recommendation': 'Energy efficiency upgrades',
            'description': 'Install LED lighting, programmable thermostats, and energy-efficient appliances',
            'estimated_annual_savings': electricity.get('optimization_potential', 0),
            'implementation_cost': electricity.get('optimization_potential', 0) * 3,
            'payback_period_months': 36,
            'priority': 'high' if electricity.get('optimization_potential', 0) > 500 else 'medium'
        })
    
    # Gas optimization
    if gas.get('optimization_potential', 0) > 150:
        recommendations.append({
            'utility': 'gas',
            'recommendation': 'Heating system upgrade',
            'description': 'Upgrade to high-efficiency heating system and improve insulation',
            'estimated_annual_savings': gas.get('optimization_potential', 0),
            'implementation_cost': gas.get('optimization_potential', 0) * 5,
            'payback_period_months': 60,
            'priority': 'medium'
        })
    
    # Water optimization
    if water.get('optimization_potential', 0) > 100:
        recommendations.append({
            'utility': 'water',
            'recommendation': 'Water efficiency improvements',
            'description': 'Install low-flow fixtures, fix leaks, and optimize irrigation',
            'estimated_annual_savings': water.get('optimization_potential', 0),
            'implementation_cost': water.get('optimization_potential', 0) * 2,
            'payback_period_months': 24,
            'priority': 'medium'
        })
    
    # Solar energy consideration
    if property_data.get('solar_feasible', True) and electricity['annual_total'] > 2000:
        solar_savings = electricity['annual_total'] * 0.6  # 60% savings potential
        recommendations.append({
            'utility': 'electricity',
            'recommendation': 'Solar panel installation',
            'description': 'Install rooftop solar panels to reduce electricity costs',
            'estimated_annual_savings': round(solar_savings, 2),
            'implementation_cost': round(solar_savings * 8, 2),  # 8-year payback typical
            'payback_period_months': 96,
            'priority': 'low'
        })
    
    return recommendations

def calculate_cost_variance(historical_data: Dict, forecast: Dict) -> Dict:
    """
    Calculate variance between historical costs and forecasted costs
    """
    # This would analyze historical utility bills to calculate variance
    # For now, providing estimated variance based on seasonal patterns
    
    monthly_variance = []
    base_variance = 0.15  # 15% base variance
    
    for month in range(1, 13):
        # Seasonal variance is higher in extreme weather months
        if month in [1, 2, 7, 8, 12]:  # Winter and summer peaks
            variance = base_variance + 0.1  # Additional 10% variance
        else:
            variance = base_variance
        
        monthly_variance.append({
            'month': month,
            'variance_percentage': round(variance * 100, 1),
            'confidence_interval': {
                'low': round(forecast['monthly_totals'][month-1]['total_cost'] * (1 - variance), 2),
                'high': round(forecast['monthly_totals'][month-1]['total_cost'] * (1 + variance), 2)
            }
        })
    
    annual_variance = base_variance
    
    return {
        'annual_variance_percentage': round(annual_variance * 100, 1),
        'monthly_variance': monthly_variance,
        'confidence_interval': {
            'low': round(forecast['annual_total'] * (1 - annual_variance), 2),
            'high': round(forecast['annual_total'] * (1 + annual_variance), 2)
        }
    }

def assess_utility_cost_risks(property_data: Dict, historical_data: Dict, weather_data: Dict) -> List[Dict]:
    """
    Assess risks that could impact utility cost forecasts
    """
    risks = []
    
    # Equipment age risk
    hvac_age = property_data.get('hvac_age_years', 10)
    if hvac_age > 15:
        risks.append({
            'risk': 'HVAC system failure',
            'probability': 'medium',
            'impact': 'high',
            'description': 'Aging HVAC system may fail, leading to emergency replacement and higher costs',
            'mitigation': 'Schedule preventive maintenance and plan for replacement'
        })
    
    # Extreme weather risk
    if weather_data.get('extreme_weather_frequency', 0) > 0.3:
        risks.append({
            'risk': 'Extreme weather events',
            'probability': 'medium',
            'impact': 'medium',
            'description': 'Extreme weather could lead to higher heating/cooling costs',
            'mitigation': 'Improve insulation and consider backup systems'
        })
    
    # Rate volatility risk
    risks.append({
        'risk': 'Utility rate increases',
        'probability': 'high',
        'impact': 'medium',
        'description': 'Utility rates may increase faster than forecasted',
        'mitigation': 'Consider fixed-rate contracts and energy efficiency improvements'
    })
    
    # Infrastructure risk
    property_age = property_data.get('age_years', 10)
    if property_age > 20:
        risks.append({
            'risk': 'Infrastructure maintenance',
            'probability': 'medium',
            'impact': 'medium',
            'description': 'Aging infrastructure may require costly updates affecting utility usage',
            'mitigation': 'Plan for infrastructure upgrades and regular maintenance'
        })
    
    return risks

# Helper functions
def get_seasonal_electricity_factor(month: int, weather_data: Dict) -> float:
    """Get seasonal factor for electricity usage"""
    # Base seasonal patterns (higher in summer for AC, winter for heating)
    base_factors = {
        1: 1.2, 2: 1.1, 3: 0.9, 4: 0.8, 5: 0.9, 6: 1.1,
        7: 1.4, 8: 1.3, 9: 1.1, 10: 0.9, 11: 1.0, 12: 1.2
    }
    
    return base_factors.get(month, 1.0)

def get_seasonal_heating_factor(month: int, weather_data: Dict) -> float:
    """Get seasonal factor for gas heating usage"""
    # Higher usage in winter months
    heating_factors = {
        1: 1.5, 2: 1.4, 3: 1.1, 4: 0.7, 5: 0.3, 6: 0.1,
        7: 0.1, 8: 0.1, 9: 0.2, 10: 0.6, 11: 1.2, 12: 1.5
    }
    
    return heating_factors.get(month, 1.0)

def get_seasonal_irrigation_factor(month: int) -> float:
    """Get seasonal factor for irrigation water usage"""
    # Higher usage in growing season
    irrigation_factors = {
        1: 0.1, 2: 0.1, 3: 0.3, 4: 0.7, 5: 1.0, 6: 1.2,
        7: 1.4, 8: 1.3, 9: 1.0, 10: 0.6, 11: 0.2, 12: 0.1
    }
    
    return irrigation_factors.get(month, 1.0)

def calculate_average_monthly_usage(bills: List[Dict], unit: str = 'kwh') -> float:
    """Calculate average monthly usage from historical bills"""
    if not bills:
        return 0
    
    total_usage = sum(bill.get('usage', 0) for bill in bills)
    return total_usage / len(bills)

def calculate_electricity_rate(month: int, historical_data: Dict) -> float:
    """Calculate electricity rate per kWh"""
    # Would use historical rate data; using average rate for now
    base_rate = 0.12  # $0.12 per kWh base rate
    
    # Seasonal rate variations (higher in peak months)
    if month in [6, 7, 8]:  # Summer peak
        return base_rate * 1.2
    elif month in [12, 1, 2]:  # Winter peak
        return base_rate * 1.1
    else:
        return base_rate

def calculate_gas_rate(month: int, historical_data: Dict) -> float:
    """Calculate gas rate per therm"""
    base_rate = 1.20  # $1.20 per therm base rate
    
    # Winter rates typically higher
    if month in [11, 12, 1, 2, 3]:
        return base_rate * 1.3
    else:
        return base_rate

def calculate_demand_charge(usage_kwh: float) -> float:
    """Calculate demand charges for commercial properties"""
    # Simplified demand charge calculation
    peak_kw = usage_kwh / (30 * 24)  # Assume even usage
    return peak_kw * 15  # $15 per kW demand charge

def calculate_tiered_water_cost(usage_gallons: float) -> float:
    """Calculate tiered water pricing"""
    # Typical tiered pricing structure
    if usage_gallons <= 2000:
        return usage_gallons * 0.004  # $4 per 1000 gallons
    elif usage_gallons <= 5000:
        return 2000 * 0.004 + (usage_gallons - 2000) * 0.006
    else:
        return 2000 * 0.004 + 3000 * 0.006 + (usage_gallons - 5000) * 0.008

def calculate_electricity_optimization_potential(property_data: Dict, annual_cost: float) -> float:
    """Calculate potential electricity savings"""
    efficiency_rating = property_data.get('energy_efficiency_rating', 'C')
    
    if efficiency_rating in ['D', 'E', 'F']:
        return annual_cost * 0.25  # 25% savings potential
    elif efficiency_rating == 'C':
        return annual_cost * 0.15  # 15% savings potential
    else:
        return annual_cost * 0.05  # 5% savings potential

def calculate_gas_optimization_potential(property_data: Dict, annual_cost: float) -> float:
    """Calculate potential gas savings"""
    insulation_rating = property_data.get('insulation_rating', 'average')
    
    if insulation_rating == 'poor':
        return annual_cost * 0.30  # 30% savings potential
    elif insulation_rating == 'average':
        return annual_cost * 0.15  # 15% savings potential
    else:
        return annual_cost * 0.05  # 5% savings potential

def calculate_water_optimization_potential(property_data: Dict, annual_cost: float) -> float:
    """Calculate potential water savings"""
    has_low_flow = property_data.get('low_flow_fixtures', False)
    
    if not has_low_flow:
        return annual_cost * 0.20  # 20% savings potential
    else:
        return annual_cost * 0.05  # 5% savings potential

def calculate_telecom_optimization_potential(monthly_cost: float) -> float:
    """Calculate potential telecom savings"""
    # Limited optimization potential for telecom services
    return monthly_cost * 12 * 0.10  # 10% savings potential

def analyze_seasonal_utility_patterns(historical_data: Dict) -> Dict:
    """Analyze seasonal patterns in utility usage"""
    return {
        'peak_season': 'summer',
        'peak_months': [6, 7, 8],
        'low_season': 'spring',
        'low_months': [4, 5],
        'variance_coefficient': 0.25,
        'trend': 'stable'
    }

def identify_efficiency_opportunities(property_data: Dict, historical_data: Dict) -> List[Dict]:
    """Identify specific efficiency improvement opportunities"""
    opportunities = []
    
    # HVAC opportunities
    hvac_age = property_data.get('hvac_age_years', 10)
    if hvac_age > 10:
        opportunities.append({
            'category': 'HVAC',
            'opportunity': 'Upgrade to high-efficiency HVAC system',
            'estimated_savings': 800,
            'implementation_cost': 8000,
            'payback_years': 10
        })
    
    # Insulation opportunities
    insulation_rating = property_data.get('insulation_rating', 'average')
    if insulation_rating in ['poor', 'average']:
        opportunities.append({
            'category': 'Insulation',
            'opportunity': 'Improve building insulation',
            'estimated_savings': 400,
            'implementation_cost': 2000,
            'payback_years': 5
        })
    
    # Water efficiency opportunities
    low_flow_fixtures = property_data.get('low_flow_fixtures', False)
    if not low_flow_fixtures:
        opportunities.append({
            'category': 'Water',
            'opportunity': 'Install low-flow fixtures',
            'estimated_savings': 200,
            'implementation_cost': 800,
            'payback_years': 4
        })
    
    return opportunities

def generate_budget_recommendations(total_forecast: Dict, cost_variance: Dict) -> List[str]:
    """Generate budget planning recommendations"""
    recommendations = []
    
    annual_total = total_forecast['annual_total']
    monthly_average = total_forecast['monthly_average']
    
    recommendations.append(f"Budget ${monthly_average:.0f} per month for utilities")
    recommendations.append(f"Set aside an additional 20% buffer (${annual_total * 0.2:.0f}) for rate increases")
    
    if total_forecast['cost_variance'] > monthly_average * 0.5:
        recommendations.append("Consider budget smoothing to handle seasonal variation")
    
    recommendations.append("Review and update utility budget quarterly")
    recommendations.append("Monitor usage patterns to identify cost-saving opportunities")
    
    return recommendations

def calculate_forecast_confidence(property_data: Dict, historical_data: Dict) -> str:
    """Calculate confidence level of utility forecasts"""
    confidence_score = 0
    
    # Historical data availability
    utilities_with_history = 0
    for utility in ['electricity_bills', 'gas_bills', 'water_bills']:
        if historical_data.get(utility):
            utilities_with_history += 1
            confidence_score += 25
    
    # Property data completeness
    required_fields = ['square_footage', 'energy_efficiency_rating', 'occupancy_rate']
    complete_fields = sum(1 for field in required_fields if property_data.get(field))
    confidence_score += (complete_fields / len(required_fields)) * 25
    
    if confidence_score >= 80:
        return 'High'
    elif confidence_score >= 60:
        return 'Medium'
    else:
        return 'Low'