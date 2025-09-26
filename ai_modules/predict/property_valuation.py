import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

def estimate_property_value(property_data: Dict, market_data: Dict, financial_data: Dict = None, comparable_sales: List[Dict] = None) -> Dict:
    """
    Estimate property value using multiple valuation approaches
    
    Args:
        property_data (dict): Property characteristics and features
        market_data (dict): Local market conditions and trends
        financial_data (dict): Income and expense data for income approach
        comparable_sales (list): Recent comparable property sales
    
    Returns:
        dict: Property valuation with multiple approaches and confidence analysis
    """
    
    # Calculate using different valuation approaches
    market_approach = calculate_market_approach_value(property_data, comparable_sales or [])
    income_approach = calculate_income_approach_value(property_data, financial_data or {})
    cost_approach = calculate_cost_approach_value(property_data, market_data)
    
    # Calculate weighted composite valuation
    composite_valuation = calculate_composite_valuation([
        market_approach, income_approach, cost_approach
    ], property_data)
    
    # Market trend analysis
    trend_analysis = analyze_market_trends(market_data, property_data)
    
    # Value drivers analysis
    value_drivers = analyze_value_drivers(property_data, market_data)
    
    # Risk assessment
    valuation_risks = assess_valuation_risks(property_data, market_data, financial_data or {})
    
    # Price range estimation
    price_range = calculate_price_range(composite_valuation, valuation_risks)
    
    return {
        'estimated_value': composite_valuation['value'],
        'value_range': price_range,
        'valuation_approaches': {
            'market_approach': market_approach,
            'income_approach': income_approach,
            'cost_approach': cost_approach,
            'composite': composite_valuation
        },
        'market_trends': trend_analysis,
        'value_drivers': value_drivers,
        'risk_assessment': valuation_risks,
        'confidence_level': calculate_valuation_confidence(property_data, market_data, comparable_sales or []),
        'valuation_date': datetime.now().isoformat(),
        'next_review_date': (datetime.now() + timedelta(days=90)).isoformat(),
        'market_position': assess_market_position(composite_valuation['value'], market_data),
        'investment_metrics': calculate_investment_metrics(composite_valuation['value'], financial_data or {})
    }

def calculate_market_approach_value(property_data: Dict, comparable_sales: List[Dict]) -> Dict:
    """
    Calculate property value using market/sales comparison approach
    """
    if not comparable_sales:
        # Generate sample comparable sales for demonstration
        comparable_sales = generate_sample_comparables(property_data)
    
    adjusted_sales = []
    
    for sale in comparable_sales:
        # Start with sale price
        adjusted_price = sale.get('sale_price', 0)
        adjustments = {}
        total_adjustment = 0
        
        # Size adjustment
        subject_sqft = property_data.get('square_footage', 1000)
        comp_sqft = sale.get('square_footage', 1000)
        
        if comp_sqft > 0:
            size_diff_per_sqft = (subject_sqft - comp_sqft)
            size_adjustment = size_diff_per_sqft * 50  # $50 per sq ft difference
            adjustments['size'] = size_adjustment
            total_adjustment += size_adjustment
        
        # Age adjustment
        subject_age = property_data.get('age_years', 10)
        comp_age = sale.get('age_years', 10)
        age_adjustment = (comp_age - subject_age) * 1000  # $1000 per year difference
        adjustments['age'] = age_adjustment
        total_adjustment += age_adjustment
        
        # Condition adjustment
        subject_condition = condition_to_score(property_data.get('condition', 'average'))
        comp_condition = condition_to_score(sale.get('condition', 'average'))
        condition_adjustment = (subject_condition - comp_condition) * 5000
        adjustments['condition'] = condition_adjustment
        total_adjustment += condition_adjustment
        
        # Location adjustment
        subject_location_score = property_data.get('location_score', 7)
        comp_location_score = sale.get('location_score', 7)
        location_adjustment = (subject_location_score - comp_location_score) * 3000
        adjustments['location'] = location_adjustment
        total_adjustment += location_adjustment
        
        # Amenities adjustment
        subject_amenities = len(property_data.get('amenities', []))
        comp_amenities = len(sale.get('amenities', []))
        amenity_adjustment = (subject_amenities - comp_amenities) * 2000
        adjustments['amenities'] = amenity_adjustment
        total_adjustment += amenity_adjustment
        
        # Date of sale adjustment (time adjustment)
        sale_date = datetime.fromisoformat(sale.get('sale_date', '2024-01-01'))
        months_ago = (datetime.now() - sale_date).days / 30
        market_appreciation_rate = 0.005  # 0.5% per month
        time_adjustment = adjusted_price * market_appreciation_rate * months_ago
        adjustments['time'] = time_adjustment
        total_adjustment += time_adjustment
        
        final_adjusted_price = adjusted_price + total_adjustment
        
        adjusted_sales.append({
            'comparable_id': sale.get('id', 'unknown'),
            'original_price': adjusted_price,
            'adjustments': adjustments,
            'total_adjustment': round(total_adjustment, 2),
            'adjusted_price': round(final_adjusted_price, 2),
            'weight': calculate_comparable_weight(sale, property_data)
        })
    
    # Calculate weighted average
    total_weight = sum(comp['weight'] for comp in adjusted_sales)
    if total_weight > 0:
        weighted_value = sum(comp['adjusted_price'] * comp['weight'] for comp in adjusted_sales) / total_weight
    else:
        weighted_value = sum(comp['adjusted_price'] for comp in adjusted_sales) / len(adjusted_sales)
    
    return {
        'approach': 'market_comparison',
        'value': round(weighted_value, 2),
        'comparables_used': len(adjusted_sales),
        'adjusted_sales': adjusted_sales,
        'value_per_sqft': round(weighted_value / property_data.get('square_footage', 1000), 2),
        'reliability': calculate_market_approach_reliability(adjusted_sales, property_data)
    }

def calculate_income_approach_value(property_data: Dict, financial_data: Dict) -> Dict:
    """
    Calculate property value using income capitalization approach
    """
    if not financial_data:
        return {
            'approach': 'income_capitalization',
            'value': 0,
            'reliability': 'low',
            'note': 'No financial data provided'
        }
    
    # Annual rental income
    monthly_rent = financial_data.get('monthly_rent', 0)
    annual_rent = monthly_rent * 12
    
    # Vacancy adjustment
    vacancy_rate = financial_data.get('vacancy_rate', 0.05)  # 5% default
    effective_gross_income = annual_rent * (1 - vacancy_rate)
    
    # Operating expenses
    operating_expenses = financial_data.get('annual_operating_expenses', effective_gross_income * 0.45)
    
    # Net operating income
    net_operating_income = effective_gross_income - operating_expenses
    
    # Capitalization rate
    cap_rate = calculate_market_cap_rate(property_data, financial_data)
    
    # Property value calculation
    if cap_rate > 0:
        property_value = net_operating_income / cap_rate
    else:
        property_value = 0
    
    # Gross rent multiplier method (alternative calculation)
    grm = calculate_gross_rent_multiplier(property_data)
    grm_value = annual_rent * grm
    
    return {
        'approach': 'income_capitalization',
        'value': round(property_value, 2),
        'annual_rent': annual_rent,
        'effective_gross_income': round(effective_gross_income, 2),
        'operating_expenses': round(operating_expenses, 2),
        'net_operating_income': round(net_operating_income, 2),
        'cap_rate': round(cap_rate, 4),
        'gross_rent_multiplier': round(grm, 1),
        'grm_value': round(grm_value, 2),
        'expense_ratio': round(operating_expenses / effective_gross_income, 3) if effective_gross_income > 0 else 0,
        'reliability': calculate_income_approach_reliability(financial_data)
    }

def calculate_cost_approach_value(property_data: Dict, market_data: Dict) -> Dict:
    """
    Calculate property value using cost approach (replacement cost)
    """
    # Land value
    land_area = property_data.get('land_area_sqft', 5000)
    land_value_per_sqft = market_data.get('land_value_per_sqft', 20)
    land_value = land_area * land_value_per_sqft
    
    # Building replacement cost
    building_sqft = property_data.get('square_footage', 1000)
    construction_cost_per_sqft = get_construction_cost_per_sqft(property_data)
    replacement_cost_new = building_sqft * construction_cost_per_sqft
    
    # Depreciation calculation
    depreciation = calculate_depreciation(property_data)
    depreciated_building_value = replacement_cost_new - depreciation
    
    # Total property value
    total_value = land_value + depreciated_building_value
    
    return {
        'approach': 'cost_replacement',
        'value': round(total_value, 2),
        'land_value': round(land_value, 2),
        'replacement_cost_new': round(replacement_cost_new, 2),
        'total_depreciation': round(depreciation, 2),
        'depreciated_building_value': round(depreciated_building_value, 2),
        'construction_cost_per_sqft': construction_cost_per_sqft,
        'land_value_per_sqft': land_value_per_sqft,
        'reliability': calculate_cost_approach_reliability(property_data)
    }

def calculate_composite_valuation(approaches: List[Dict], property_data: Dict) -> Dict:
    """
    Calculate weighted composite valuation from multiple approaches
    """
    # Filter out approaches with zero values
    valid_approaches = [app for app in approaches if app.get('value', 0) > 0]
    
    if not valid_approaches:
        return {'value': 0, 'weights': {}, 'note': 'No valid approaches available'}
    
    # Determine weights based on reliability and property type
    property_type = property_data.get('property_type', 'residential')
    
    if property_type == 'residential':
        base_weights = {'market_comparison': 0.6, 'income_capitalization': 0.3, 'cost_replacement': 0.1}
    else:  # commercial
        base_weights = {'market_comparison': 0.4, 'income_capitalization': 0.5, 'cost_replacement': 0.1}
    
    # Adjust weights based on reliability
    adjusted_weights = {}
    total_weight = 0
    
    for approach in valid_approaches:
        approach_name = approach['approach']
        reliability = approach.get('reliability', 'medium')
        
        base_weight = base_weights.get(approach_name, 0.33)
        
        # Adjust based on reliability
        if reliability == 'high':
            weight_multiplier = 1.2
        elif reliability == 'low':
            weight_multiplier = 0.7
        else:
            weight_multiplier = 1.0
        
        adjusted_weight = base_weight * weight_multiplier
        adjusted_weights[approach_name] = adjusted_weight
        total_weight += adjusted_weight
    
    # Normalize weights
    if total_weight > 0:
        for approach_name in adjusted_weights:
            adjusted_weights[approach_name] /= total_weight
    
    # Calculate weighted value
    weighted_value = 0
    for approach in valid_approaches:
        approach_name = approach['approach']
        weight = adjusted_weights.get(approach_name, 0)
        weighted_value += approach['value'] * weight
    
    return {
        'value': round(weighted_value, 2),
        'weights': {k: round(v, 3) for k, v in adjusted_weights.items()},
        'approaches_used': len(valid_approaches),
        'valuation_method': 'weighted_composite'
    }

def analyze_market_trends(market_data: Dict, property_data: Dict) -> Dict:
    """
    Analyze market trends affecting property value
    """
    # Market appreciation trends
    annual_appreciation = market_data.get('annual_appreciation_rate', 0.03)
    price_trend = market_data.get('price_trend', 'stable')
    
    # Inventory levels
    inventory_months = market_data.get('months_of_inventory', 6)
    
    # Days on market
    average_dom = market_data.get('average_days_on_market', 45)
    
    # Price per square foot trends
    current_price_per_sqft = market_data.get('median_price_per_sqft', 150)
    year_ago_price_per_sqft = market_data.get('year_ago_price_per_sqft', 145)
    
    price_per_sqft_change = (current_price_per_sqft - year_ago_price_per_sqft) / year_ago_price_per_sqft if year_ago_price_per_sqft > 0 else 0
    
    # Market conditions assessment
    if inventory_months < 4 and average_dom < 30:
        market_condition = 'seller_market'
        condition_impact = 1.05  # 5% positive impact
    elif inventory_months > 8 and average_dom > 60:
        market_condition = 'buyer_market'
        condition_impact = 0.95  # 5% negative impact
    else:
        market_condition = 'balanced_market'
        condition_impact = 1.0
    
    return {
        'annual_appreciation_rate': round(annual_appreciation, 4),
        'price_trend': price_trend,
        'inventory_months': inventory_months,
        'average_days_on_market': average_dom,
        'price_per_sqft_change': round(price_per_sqft_change, 4),
        'market_condition': market_condition,
        'condition_impact_factor': round(condition_impact, 3),
        'forecast_12_month': {
            'appreciation_range': {
                'low': round(annual_appreciation * 0.5, 4),
                'high': round(annual_appreciation * 1.5, 4)
            },
            'market_outlook': determine_market_outlook(annual_appreciation, inventory_months, average_dom)
        }
    }

def analyze_value_drivers(property_data: Dict, market_data: Dict) -> Dict:
    """
    Analyze key factors driving property value
    """
    drivers = {
        'positive_drivers': [],
        'negative_drivers': [],
        'neutral_factors': []
    }
    
    # Location factors
    location_score = property_data.get('location_score', 7)
    if location_score >= 8:
        drivers['positive_drivers'].append({
            'factor': 'Prime location',
            'impact': 'high',
            'value_impact': '+10-15%'
        })
    elif location_score <= 5:
        drivers['negative_drivers'].append({
            'factor': 'Poor location',
            'impact': 'high',
            'value_impact': '-10-15%'
        })
    
    # Property condition
    condition = property_data.get('condition', 'average')
    if condition in ['excellent', 'good']:
        drivers['positive_drivers'].append({
            'factor': f'{condition.title()} condition',
            'impact': 'medium',
            'value_impact': '+5-10%'
        })
    elif condition == 'poor':
        drivers['negative_drivers'].append({
            'factor': 'Poor condition',
            'impact': 'high',
            'value_impact': '-15-25%'
        })
    
    # Property age
    age_years = property_data.get('age_years', 10)
    if age_years <= 5:
        drivers['positive_drivers'].append({
            'factor': 'New construction',
            'impact': 'medium',
            'value_impact': '+5-8%'
        })
    elif age_years >= 30:
        drivers['negative_drivers'].append({
            'factor': 'Older property',
            'impact': 'medium',
            'value_impact': '-5-10%'
        })
    
    # Amenities
    amenities = property_data.get('amenities', [])
    high_value_amenities = ['pool', 'gym', 'parking', 'updated_kitchen', 'hardwood_floors']
    
    valuable_amenities = [a for a in amenities if a in high_value_amenities]
    if len(valuable_amenities) >= 3:
        drivers['positive_drivers'].append({
            'factor': 'Premium amenities',
            'impact': 'medium',
            'value_impact': '+3-7%'
        })
    
    # Market factors
    appreciation_rate = market_data.get('annual_appreciation_rate', 0.03)
    if appreciation_rate > 0.05:
        drivers['positive_drivers'].append({
            'factor': 'Strong market appreciation',
            'impact': 'medium',
            'value_impact': '+2-5%'
        })
    elif appreciation_rate < 0:
        drivers['negative_drivers'].append({
            'factor': 'Market depreciation',
            'impact': 'high',
            'value_impact': '-5-15%'
        })
    
    return drivers

def assess_valuation_risks(property_data: Dict, market_data: Dict, financial_data: Dict) -> Dict:
    """
    Assess risks affecting property valuation accuracy
    """
    risks = []
    risk_score = 0  # 0-100 scale
    
    # Market volatility risk
    market_volatility = market_data.get('price_volatility', 0.1)  # Standard deviation
    if market_volatility > 0.15:
        risks.append({
            'risk': 'High market volatility',
            'impact': 'medium',
            'description': 'Property values subject to significant fluctuation'
        })
        risk_score += 15
    
    # Liquidity risk
    average_dom = market_data.get('average_days_on_market', 45)
    if average_dom > 90:
        risks.append({
            'risk': 'Low market liquidity',
            'impact': 'medium',
            'description': 'Properties taking longer to sell'
        })
        risk_score += 10
    
    # Property-specific risks
    age_years = property_data.get('age_years', 10)
    if age_years > 30:
        risks.append({
            'risk': 'Property age',
            'impact': 'medium',
            'description': 'Older property may have hidden maintenance issues'
        })
        risk_score += 10
    
    # Income risk (for income-producing properties)
    if financial_data:
        vacancy_rate = financial_data.get('vacancy_rate', 0.05)
        if vacancy_rate > 0.10:
            risks.append({
                'risk': 'High vacancy risk',
                'impact': 'high',
                'description': 'Property experiencing high vacancy rates'
            })
            risk_score += 20
    
    # Market conditions risk
    inventory_months = market_data.get('months_of_inventory', 6)
    if inventory_months > 10:
        risks.append({
            'risk': 'Oversupply',
            'impact': 'medium',
            'description': 'High inventory may depress prices'
        })
        risk_score += 10
    
    # Economic factors
    local_unemployment = market_data.get('local_unemployment_rate', 0.05)
    if local_unemployment > 0.08:
        risks.append({
            'risk': 'Economic conditions',
            'impact': 'medium',
            'description': 'High local unemployment may affect demand'
        })
        risk_score += 10
    
    # Determine overall risk level
    if risk_score <= 20:
        risk_level = 'low'
    elif risk_score <= 40:
        risk_level = 'medium'
    else:
        risk_level = 'high'
    
    return {
        'overall_risk_level': risk_level,
        'risk_score': risk_score,
        'identified_risks': risks,
        'risk_mitigation_strategies': generate_risk_mitigation_strategies(risks)
    }

def calculate_price_range(composite_valuation: Dict, risk_assessment: Dict) -> Dict:
    """
    Calculate reasonable price range based on valuation and risks
    """
    base_value = composite_valuation['value']
    risk_level = risk_assessment['overall_risk_level']
    
    # Base confidence interval
    if risk_level == 'low':
        confidence_interval = 0.05  # ±5%
    elif risk_level == 'medium':
        confidence_interval = 0.10  # ±10%
    else:
        confidence_interval = 0.15  # ±15%
    
    low_value = base_value * (1 - confidence_interval)
    high_value = base_value * (1 + confidence_interval)
    
    return {
        'low_estimate': round(low_value, 2),
        'high_estimate': round(high_value, 2),
        'confidence_interval': round(confidence_interval * 100, 1),
        'most_likely_value': base_value
    }

# Helper functions
def condition_to_score(condition: str) -> int:
    """Convert condition string to numeric score"""
    condition_scores = {
        'excellent': 5,
        'good': 4,
        'average': 3,
        'fair': 2,
        'poor': 1
    }
    return condition_scores.get(condition.lower(), 3)

def generate_sample_comparables(property_data: Dict) -> List[Dict]:
    """Generate sample comparable sales for demonstration"""
    base_sqft = property_data.get('square_footage', 1000)
    base_age = property_data.get('age_years', 10)
    
    comparables = []
    for i in range(3):
        sqft_variance = np.random.normal(0, 200)
        age_variance = np.random.normal(0, 5)
        price_per_sqft = np.random.normal(180, 20)
        
        comp_sqft = max(500, base_sqft + sqft_variance)
        comp_age = max(0, base_age + age_variance)
        sale_price = comp_sqft * price_per_sqft
        
        comparables.append({
            'id': f'comp_{i+1}',
            'sale_price': round(sale_price, 2),
            'square_footage': round(comp_sqft),
            'age_years': round(comp_age),
            'condition': 'average',
            'location_score': 7,
            'amenities': ['parking'],
            'sale_date': (datetime.now() - timedelta(days=np.random.randint(30, 180))).isoformat()
        })
    
    return comparables

def calculate_comparable_weight(sale: Dict, property_data: Dict) -> float:
    """Calculate weight for comparable sale based on similarity"""
    weight = 1.0
    
    # Size similarity
    subject_sqft = property_data.get('square_footage', 1000)
    comp_sqft = sale.get('square_footage', 1000)
    size_diff_pct = abs(subject_sqft - comp_sqft) / subject_sqft
    weight *= max(0.5, 1 - size_diff_pct)
    
    # Age similarity
    subject_age = property_data.get('age_years', 10)
    comp_age = sale.get('age_years', 10)
    age_diff = abs(subject_age - comp_age)
    weight *= max(0.5, 1 - age_diff / 20)
    
    # Date of sale (more recent = higher weight)
    sale_date = datetime.fromisoformat(sale.get('sale_date', '2024-01-01'))
    days_ago = (datetime.now() - sale_date).days
    weight *= max(0.3, 1 - days_ago / 365)
    
    return weight

def calculate_market_cap_rate(property_data: Dict, financial_data: Dict) -> float:
    """Calculate appropriate cap rate for property"""
    # Base cap rate by property type
    property_type = property_data.get('property_type', 'residential')
    
    if property_type == 'residential':
        base_cap_rate = 0.06  # 6%
    elif property_type == 'commercial':
        base_cap_rate = 0.08  # 8%
    else:
        base_cap_rate = 0.07  # 7%
    
    # Risk adjustments
    risk_adjustments = 0
    
    # Location adjustment
    location_score = property_data.get('location_score', 7)
    if location_score >= 9:
        risk_adjustments -= 0.005  # Prime location reduces risk
    elif location_score <= 5:
        risk_adjustments += 0.01   # Poor location increases risk
    
    # Age adjustment
    age_years = property_data.get('age_years', 10)
    if age_years > 20:
        risk_adjustments += 0.005  # Older properties have higher risk
    
    # Tenant quality (if applicable)
    if financial_data.get('vacancy_rate', 0.05) > 0.10:
        risk_adjustments += 0.005  # High vacancy increases risk
    
    return max(0.04, base_cap_rate + risk_adjustments)

def calculate_gross_rent_multiplier(property_data: Dict) -> float:
    """Calculate appropriate gross rent multiplier"""
    property_type = property_data.get('property_type', 'residential')
    location_score = property_data.get('location_score', 7)
    
    # Base GRM by property type
    if property_type == 'residential':
        base_grm = 12
    else:
        base_grm = 10
    
    # Location adjustment
    if location_score >= 9:
        base_grm += 2  # Premium location
    elif location_score <= 5:
        base_grm -= 2  # Poor location
    
    return max(8, base_grm)

def get_construction_cost_per_sqft(property_data: Dict) -> float:
    """Get construction cost per square foot"""
    property_type = property_data.get('property_type', 'residential')
    quality = property_data.get('construction_quality', 'average')
    
    # Base costs per sq ft
    base_costs = {
        'residential': 150,
        'commercial': 200,
        'industrial': 100
    }
    
    quality_multipliers = {
        'luxury': 1.5,
        'high': 1.3,
        'average': 1.0,
        'economy': 0.8
    }
    
    base_cost = base_costs.get(property_type, 150)
    quality_multiplier = quality_multipliers.get(quality, 1.0)
    
    return base_cost * quality_multiplier

def calculate_depreciation(property_data: Dict) -> float:
    """Calculate total depreciation (physical, functional, external)"""
    age_years = property_data.get('age_years', 10)
    replacement_cost = property_data.get('square_footage', 1000) * get_construction_cost_per_sqft(property_data)
    
    # Physical depreciation (straight-line over 50 years)
    physical_depreciation = replacement_cost * (age_years / 50)
    
    # Functional obsolescence
    functional_depreciation = 0
    if not property_data.get('updated_kitchen', False) and age_years > 15:
        functional_depreciation += replacement_cost * 0.05
    if not property_data.get('updated_bathrooms', False) and age_years > 15:
        functional_depreciation += replacement_cost * 0.03
    
    # External obsolescence (market factors)
    external_depreciation = 0
    location_score = property_data.get('location_score', 7)
    if location_score <= 5:
        external_depreciation = replacement_cost * 0.10  # 10% for poor location
    
    total_depreciation = physical_depreciation + functional_depreciation + external_depreciation
    
    # Cap total depreciation at 80% of replacement cost
    return min(total_depreciation, replacement_cost * 0.8)

def calculate_market_approach_reliability(adjusted_sales: List[Dict], property_data: Dict) -> str:
    """Calculate reliability of market approach"""
    if len(adjusted_sales) >= 3:
        # Check variance in adjusted prices
        prices = [sale['adjusted_price'] for sale in adjusted_sales]
        variance = np.var(prices) / np.mean(prices)
        
        if variance < 0.05:  # Low variance
            return 'high'
        elif variance < 0.15:
            return 'medium'
        else:
            return 'low'
    else:
        return 'low'  # Not enough comparables

def calculate_income_approach_reliability(financial_data: Dict) -> str:
    """Calculate reliability of income approach"""
    required_fields = ['monthly_rent', 'annual_operating_expenses', 'vacancy_rate']
    available_fields = sum(1 for field in required_fields if financial_data.get(field) is not None)
    
    if available_fields == len(required_fields):
        return 'high'
    elif available_fields >= len(required_fields) * 0.7:
        return 'medium'
    else:
        return 'low'

def calculate_cost_approach_reliability(property_data: Dict) -> str:
    """Calculate reliability of cost approach"""
    # Cost approach is generally less reliable for older properties
    age_years = property_data.get('age_years', 10)
    
    if age_years <= 5:
        return 'high'
    elif age_years <= 15:
        return 'medium'
    else:
        return 'low'

def calculate_valuation_confidence(property_data: Dict, market_data: Dict, comparable_sales: List[Dict]) -> str:
    """Calculate overall confidence in valuation"""
    confidence_score = 0
    
    # Data completeness
    if len(comparable_sales) >= 3:
        confidence_score += 30
    elif len(comparable_sales) >= 1:
        confidence_score += 15
    
    # Market data quality
    if market_data.get('annual_appreciation_rate') is not None:
        confidence_score += 20
    
    # Property data completeness
    required_fields = ['square_footage', 'age_years', 'condition', 'location_score']
    complete_fields = sum(1 for field in required_fields if property_data.get(field) is not None)
    confidence_score += (complete_fields / len(required_fields)) * 30
    
    # Market conditions
    if market_data.get('months_of_inventory', 6) <= 8:  # Stable market
        confidence_score += 20
    
    if confidence_score >= 80:
        return 'High'
    elif confidence_score >= 60:
        return 'Medium'
    else:
        return 'Low'

def assess_market_position(estimated_value: float, market_data: Dict) -> Dict:
    """Assess property's position in the market"""
    median_value = market_data.get('median_home_value', estimated_value)
    
    if estimated_value > median_value * 1.2:
        position = 'premium'
        percentile = 80
    elif estimated_value > median_value * 1.1:
        position = 'above_average'
        percentile = 70
    elif estimated_value < median_value * 0.9:
        position = 'below_average'
        percentile = 30
    elif estimated_value < median_value * 0.8:
        position = 'discount'
        percentile = 20
    else:
        position = 'average'
        percentile = 50
    
    return {
        'market_position': position,
        'percentile': percentile,
        'median_market_value': median_value,
        'value_vs_median': round((estimated_value / median_value - 1) * 100, 1) if median_value > 0 else 0
    }

def calculate_investment_metrics(estimated_value: float, financial_data: Dict) -> Dict:
    """Calculate investment metrics for the property"""
    if not financial_data:
        return {}
    
    monthly_rent = financial_data.get('monthly_rent', 0)
    annual_rent = monthly_rent * 12
    
    if estimated_value > 0 and annual_rent > 0:
        # Cap rate
        noi = annual_rent * 0.7  # Assume 70% of rent is NOI
        cap_rate = noi / estimated_value
        
        # Cash-on-cash return (assuming 25% down payment)
        down_payment = estimated_value * 0.25
        annual_cash_flow = noi - (estimated_value * 0.75 * 0.04)  # Assume 4% mortgage rate
        cash_on_cash = annual_cash_flow / down_payment if down_payment > 0 else 0
        
        # Price-to-rent ratio
        price_to_rent = estimated_value / annual_rent
        
        return {
            'cap_rate': round(cap_rate, 4),
            'cash_on_cash_return': round(cash_on_cash, 4),
            'price_to_rent_ratio': round(price_to_rent, 1),
            'gross_yield': round(annual_rent / estimated_value, 4),
            'estimated_monthly_cash_flow': round(annual_cash_flow / 12, 2)
        }
    
    return {}

def determine_market_outlook(appreciation_rate: float, inventory_months: float, avg_dom: float) -> str:
    """Determine market outlook based on key indicators"""
    if appreciation_rate > 0.05 and inventory_months < 4 and avg_dom < 30:
        return 'strong_seller_market'
    elif appreciation_rate > 0.03 and inventory_months < 6:
        return 'moderate_seller_market'
    elif appreciation_rate < 0 or inventory_months > 10:
        return 'buyer_market'
    else:
        return 'balanced_market'

def generate_risk_mitigation_strategies(risks: List[Dict]) -> List[str]:
    """Generate strategies to mitigate identified valuation risks"""
    strategies = []
    
    risk_types = [risk['risk'] for risk in risks]
    
    if 'High market volatility' in risk_types:
        strategies.append('Consider shorter holding periods to reduce market risk exposure')
    
    if 'Low market liquidity' in risk_types:
        strategies.append('Price competitively and enhance marketing to improve saleability')
    
    if 'Property age' in risk_types:
        strategies.append('Conduct thorough property inspection and budget for maintenance')
    
    if 'High vacancy risk' in risk_types:
        strategies.append('Improve tenant retention and consider rent adjustments')
    
    if 'Oversupply' in risk_types:
        strategies.append('Focus on unique value propositions and property differentiation')
    
    if not strategies:
        strategies.append('Continue monitoring market conditions and property performance')
    
    return strategies