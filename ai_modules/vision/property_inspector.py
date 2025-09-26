import numpy as np
import base64
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import json

def analyze_property_image(image_data: Union[str, bytes], analysis_type: str = "general_inspection") -> Dict:
    """
    Advanced computer vision analysis for property inspection images
    
    Args:
        image_data: Base64 encoded image string or raw bytes
        analysis_type: Type of analysis to perform
    
    Returns:
        dict: Comprehensive analysis results with damage detection, condition assessment, and recommendations
    """
    
    # Simulate computer vision analysis (in production, would use OpenCV, TensorFlow, or cloud vision APIs)
    image_analysis = perform_image_analysis(image_data, analysis_type)
    
    # Damage and defect detection
    damage_detection = detect_damage_and_defects(image_analysis)
    
    # Condition assessment
    condition_assessment = assess_overall_condition(damage_detection, analysis_type)
    
    # Safety hazard identification
    safety_assessment = identify_safety_hazards(image_analysis, damage_detection)
    
    # Maintenance recommendations
    maintenance_recommendations = generate_maintenance_recommendations(damage_detection, condition_assessment)
    
    # Cost estimation
    cost_estimation = estimate_repair_costs(damage_detection, maintenance_recommendations)
    
    # Priority scoring
    priority_score = calculate_priority_score(damage_detection, safety_assessment, condition_assessment)
    
    return {
        'analysis_id': generate_analysis_id(),
        'analysis_type': analysis_type,
        'image_metadata': extract_image_metadata(image_data),
        'damage_detection': damage_detection,
        'condition_assessment': condition_assessment,
        'safety_assessment': safety_assessment,
        'maintenance_recommendations': maintenance_recommendations,
        'cost_estimation': cost_estimation,
        'priority_score': priority_score,
        'confidence_level': calculate_confidence_level(image_analysis),
        'analysis_timestamp': datetime.now().isoformat(),
        'requires_human_review': priority_score >= 8 or len(safety_assessment['hazards']) > 0,
        'ai_insights': generate_ai_insights(damage_detection, condition_assessment, safety_assessment)
    }

def perform_image_analysis(image_data: Union[str, bytes], analysis_type: str) -> Dict:
    """
    Core computer vision analysis (simulated - would use real CV models in production)
    """
    # Simulate different analysis results based on type
    if analysis_type == "exterior_inspection":
        return simulate_exterior_analysis()
    elif analysis_type == "interior_inspection":
        return simulate_interior_analysis()
    elif analysis_type == "hvac_inspection":
        return simulate_hvac_analysis()
    elif analysis_type == "electrical_inspection":
        return simulate_electrical_analysis()
    elif analysis_type == "plumbing_inspection":
        return simulate_plumbing_analysis()
    else:
        return simulate_general_analysis()

def simulate_exterior_analysis() -> Dict:
    """Simulate exterior property analysis"""
    return {
        'detected_objects': [
            {'object': 'roof', 'confidence': 0.95, 'condition': 'good', 'bbox': [100, 50, 400, 200]},
            {'object': 'siding', 'confidence': 0.92, 'condition': 'fair', 'bbox': [0, 200, 500, 600]},
            {'object': 'windows', 'confidence': 0.88, 'condition': 'good', 'bbox': [150, 250, 200, 350]},
            {'object': 'front_door', 'confidence': 0.91, 'condition': 'excellent', 'bbox': [225, 400, 275, 550]},
            {'object': 'driveway', 'confidence': 0.85, 'condition': 'fair', 'bbox': [0, 550, 200, 700]}
        ],
        'structural_elements': [
            {'element': 'foundation', 'visible_area': 0.3, 'condition': 'good'},
            {'element': 'gutters', 'visible_area': 0.8, 'condition': 'needs_attention'},
            {'element': 'landscaping', 'visible_area': 0.6, 'condition': 'good'}
        ],
        'weather_conditions': 'clear',
        'lighting_quality': 'good',
        'image_quality_score': 0.85
    }

def simulate_interior_analysis() -> Dict:
    """Simulate interior property analysis"""
    return {
        'detected_objects': [
            {'object': 'walls', 'confidence': 0.94, 'condition': 'good', 'material': 'drywall'},
            {'object': 'flooring', 'confidence': 0.89, 'condition': 'fair', 'material': 'hardwood'},
            {'object': 'ceiling', 'confidence': 0.91, 'condition': 'good', 'material': 'painted'},
            {'object': 'fixtures', 'confidence': 0.87, 'condition': 'good', 'type': 'lighting'},
            {'object': 'outlets', 'confidence': 0.82, 'condition': 'excellent', 'count': 4}
        ],
        'room_classification': 'living_room',
        'space_measurements': {'estimated_sqft': 220, 'ceiling_height': 9.5},
        'lighting_analysis': {'natural_light': 'adequate', 'artificial_light': 'good'},
        'air_quality_indicators': {'visible_dust': 'minimal', 'ventilation': 'adequate'},
        'image_quality_score': 0.88
    }

def detect_damage_and_defects(image_analysis: Dict) -> Dict:
    """
    Detect damage and defects from image analysis
    """
    damages = []
    defects = []
    
    # Analyze detected objects for issues
    for obj in image_analysis.get('detected_objects', []):
        condition = obj.get('condition', 'unknown')
        object_type = obj.get('object', 'unknown')
        
        if condition in ['poor', 'needs_repair']:
            damages.append({
                'type': f'{object_type}_damage',
                'severity': 'high' if condition == 'poor' else 'medium',
                'location': obj.get('bbox', []),
                'description': f'{object_type.title()} showing signs of damage or wear',
                'confidence': obj.get('confidence', 0.0),
                'repair_urgency': 'immediate' if condition == 'poor' else 'within_30_days'
            })
        elif condition == 'needs_attention':
            defects.append({
                'type': f'{object_type}_maintenance',
                'severity': 'low',
                'location': obj.get('bbox', []),
                'description': f'{object_type.title()} requires maintenance attention',
                'confidence': obj.get('confidence', 0.0),
                'repair_urgency': 'within_90_days'
            })
    
    # Simulate additional damage detection based on patterns
    additional_damages = simulate_advanced_damage_detection(image_analysis)
    damages.extend(additional_damages)
    
    # Calculate damage statistics
    damage_stats = calculate_damage_statistics(damages, defects)
    
    return {
        'damages': damages,
        'defects': defects,
        'total_issues': len(damages) + len(defects),
        'high_severity_count': len([d for d in damages if d['severity'] == 'high']),
        'immediate_attention_count': len([d for d in damages if d['repair_urgency'] == 'immediate']),
        'damage_statistics': damage_stats,
        'damage_score': calculate_damage_score(damages, defects)
    }

def simulate_advanced_damage_detection(image_analysis: Dict) -> List[Dict]:
    """Simulate advanced damage detection algorithms"""
    additional_damages = []
    
    # Simulate detection based on image analysis type and quality
    image_quality = image_analysis.get('image_quality_score', 0.8)
    
    if image_quality > 0.8:
        # High quality image - can detect subtle issues
        additional_damages.extend([
            {
                'type': 'paint_wear',
                'severity': 'low',
                'location': [50, 100, 150, 200],
                'description': 'Minor paint wear detected on trim',
                'confidence': 0.75,
                'repair_urgency': 'within_90_days'
            },
            {
                'type': 'caulk_deterioration',
                'severity': 'medium',
                'location': [200, 300, 250, 350],
                'description': 'Caulking around windows shows deterioration',
                'confidence': 0.68,
                'repair_urgency': 'within_60_days'
            }
        ])
    
    # Weather-based damage detection
    weather = image_analysis.get('weather_conditions', 'unknown')
    if weather in ['rainy', 'humid']:
        additional_damages.append({
            'type': 'moisture_risk',
            'severity': 'medium',
            'location': [0, 0, 100, 100],
            'description': 'Weather conditions indicate potential moisture issues',
            'confidence': 0.60,
            'repair_urgency': 'monitor'
        })
    
    return additional_damages

def assess_overall_condition(damage_detection: Dict, analysis_type: str) -> Dict:
    """
    Assess overall property condition based on detected issues
    """
    damages = damage_detection.get('damages', [])
    defects = damage_detection.get('defects', [])
    damage_score = damage_detection.get('damage_score', 0)
    
    # Calculate condition scores by category
    structural_score = calculate_category_score(damages + defects, 'structural')
    cosmetic_score = calculate_category_score(damages + defects, 'cosmetic')
    functional_score = calculate_category_score(damages + defects, 'functional')
    
    # Overall condition calculation
    overall_score = (structural_score * 0.5 + functional_score * 0.3 + cosmetic_score * 0.2)
    
    # Determine condition rating
    if overall_score >= 90:
        condition_rating = 'excellent'
        condition_description = 'Property is in excellent condition with minimal issues'
    elif overall_score >= 75:
        condition_rating = 'good'
        condition_description = 'Property is in good condition with minor maintenance needs'
    elif overall_score >= 60:
        condition_rating = 'fair'
        condition_description = 'Property is in fair condition with moderate maintenance required'
    elif overall_score >= 40:
        condition_rating = 'poor'
        condition_description = 'Property is in poor condition requiring significant attention'
    else:
        condition_rating = 'critical'
        condition_description = 'Property has critical issues requiring immediate intervention'
    
    # Generate condition trends
    condition_trends = analyze_condition_trends(damages, analysis_type)
    
    return {
        'overall_score': round(overall_score, 1),
        'condition_rating': condition_rating,
        'condition_description': condition_description,
        'category_scores': {
            'structural': round(structural_score, 1),
            'cosmetic': round(cosmetic_score, 1),
            'functional': round(functional_score, 1)
        },
        'condition_trends': condition_trends,
        'inspection_summary': generate_inspection_summary(overall_score, damages, defects),
        'next_inspection_recommended': calculate_next_inspection_date(condition_rating)
    }

def identify_safety_hazards(image_analysis: Dict, damage_detection: Dict) -> Dict:
    """
    Identify potential safety hazards from image analysis
    """
    hazards = []
    
    # Check for safety-related damage
    damages = damage_detection.get('damages', [])
    for damage in damages:
        if damage['severity'] == 'high' and damage['type'] in ['electrical_damage', 'structural_damage', 'roof_damage']:
            hazards.append({
                'hazard_type': 'structural_safety',
                'severity': 'high',
                'description': f'Potential safety hazard: {damage["description"]}',
                'immediate_action_required': True,
                'location': damage['location']
            })
    
    # Simulate additional safety detection
    additional_hazards = simulate_safety_hazard_detection(image_analysis)
    hazards.extend(additional_hazards)
    
    # Calculate safety score
    safety_score = calculate_safety_score(hazards)
    
    return {
        'hazards': hazards,
        'total_hazards': len(hazards),
        'high_risk_hazards': len([h for h in hazards if h['severity'] == 'high']),
        'immediate_action_required': any(h.get('immediate_action_required', False) for h in hazards),
        'safety_score': safety_score,
        'safety_rating': determine_safety_rating(safety_score),
        'emergency_recommendations': generate_emergency_recommendations(hazards)
    }

def generate_maintenance_recommendations(damage_detection: Dict, condition_assessment: Dict) -> List[Dict]:
    """
    Generate specific maintenance recommendations based on analysis
    """
    recommendations = []
    
    damages = damage_detection.get('damages', [])
    defects = damage_detection.get('defects', [])
    
    # Process each damage/defect
    for issue in damages + defects:
        rec = create_maintenance_recommendation(issue, condition_assessment)
        if rec:
            recommendations.append(rec)
    
    # Add preventive maintenance recommendations
    preventive_recs = generate_preventive_recommendations(condition_assessment)
    recommendations.extend(preventive_recs)
    
    # Sort by priority and urgency
    recommendations.sort(key=lambda x: (x['priority_score'], x['urgency_days']), reverse=True)
    
    return recommendations

def estimate_repair_costs(damage_detection: Dict, maintenance_recommendations: List[Dict]) -> Dict:
    """
    Estimate repair costs for identified issues
    """
    # Base cost estimates by damage type
    cost_estimates = {
        'paint_wear': {'low': 200, 'high': 500},
        'roof_damage': {'low': 800, 'high': 3000},
        'siding_damage': {'low': 300, 'high': 1200},
        'window_damage': {'low': 150, 'high': 600},
        'door_damage': {'low': 100, 'high': 800},
        'flooring_damage': {'low': 400, 'high': 2000},
        'electrical_damage': {'low': 300, 'high': 1500},
        'plumbing_damage': {'low': 250, 'high': 1000},
        'hvac_damage': {'low': 500, 'high': 2500}
    }
    
    total_cost_low = 0
    total_cost_high = 0
    itemized_costs = []
    
    damages = damage_detection.get('damages', [])
    
    for damage in damages:
        damage_type = damage['type']
        severity = damage['severity']
        
        # Get base cost estimate
        base_cost = cost_estimates.get(damage_type, {'low': 100, 'high': 500})
        
        # Adjust for severity
        if severity == 'high':
            cost_multiplier = 1.5
        elif severity == 'medium':
            cost_multiplier = 1.0
        else:
            cost_multiplier = 0.7
        
        item_cost_low = base_cost['low'] * cost_multiplier
        item_cost_high = base_cost['high'] * cost_multiplier
        
        total_cost_low += item_cost_low
        total_cost_high += item_cost_high
        
        itemized_costs.append({
            'item': damage_type.replace('_', ' ').title(),
            'severity': severity,
            'cost_range': {
                'low': round(item_cost_low, 2),
                'high': round(item_cost_high, 2)
            },
            'description': damage['description']
        })
    
    return {
        'total_estimated_cost': {
            'low': round(total_cost_low, 2),
            'high': round(total_cost_high, 2),
            'average': round((total_cost_low + total_cost_high) / 2, 2)
        },
        'itemized_costs': itemized_costs,
        'cost_breakdown_by_severity': calculate_cost_by_severity(itemized_costs),
        'cost_confidence': calculate_cost_confidence(damages),
        'cost_factors': {
            'labor_region_multiplier': 1.0,
            'material_cost_index': 1.0,
            'urgency_premium': calculate_urgency_premium(damages)
        }
    }

# Helper functions
def generate_analysis_id() -> str:
    """Generate unique analysis ID"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"PROP_ANALYSIS_{timestamp}_{random_suffix}"

def extract_image_metadata(image_data: Union[str, bytes]) -> Dict:
    """Extract metadata from image (simulated)"""
    return {
        'format': 'JPEG',
        'dimensions': {'width': 1920, 'height': 1080},
        'file_size_kb': 245,
        'capture_date': datetime.now().isoformat(),
        'camera_info': 'Mobile Device',
        'location_data': None,  # Would extract GPS if available
        'quality_score': 0.85
    }

def calculate_damage_score(damages: List[Dict], defects: List[Dict]) -> float:
    """Calculate overall damage score (0-100, lower is worse)"""
    if not damages and not defects:
        return 100.0
    
    total_score_reduction = 0
    
    for damage in damages:
        if damage['severity'] == 'high':
            total_score_reduction += 15
        elif damage['severity'] == 'medium':
            total_score_reduction += 8
        else:
            total_score_reduction += 3
    
    for defect in defects:
        total_score_reduction += 2
    
    return max(0, 100 - total_score_reduction)

def calculate_damage_statistics(damages: List[Dict], defects: List[Dict]) -> Dict:
    """Calculate statistical analysis of damages"""
    if not damages and not defects:
        return {'total_issues': 0, 'severity_distribution': {}}
    
    all_issues = damages + defects
    severity_counts = {}
    urgency_counts = {}
    
    for issue in all_issues:
        severity = issue.get('severity', 'unknown')
        urgency = issue.get('repair_urgency', 'unknown')
        
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
    
    return {
        'total_issues': len(all_issues),
        'severity_distribution': severity_counts,
        'urgency_distribution': urgency_counts,
        'damage_density': len(all_issues) / 100,  # Issues per 100 sq ft (estimated)
        'critical_issues_percentage': (severity_counts.get('high', 0) / len(all_issues)) * 100 if all_issues else 0
    }

def calculate_category_score(issues: List[Dict], category: str) -> float:
    """Calculate condition score for a specific category"""
    category_mapping = {
        'structural': ['roof', 'foundation', 'walls', 'structural'],
        'cosmetic': ['paint', 'flooring', 'cosmetic', 'appearance'],
        'functional': ['electrical', 'plumbing', 'hvac', 'mechanical']
    }
    
    category_keywords = category_mapping.get(category, [])
    relevant_issues = []
    
    for issue in issues:
        issue_type = issue.get('type', '').lower()
        if any(keyword in issue_type for keyword in category_keywords):
            relevant_issues.append(issue)
    
    if not relevant_issues:
        return 95.0  # No issues in this category
    
    total_deduction = 0
    for issue in relevant_issues:
        if issue['severity'] == 'high':
            total_deduction += 20
        elif issue['severity'] == 'medium':
            total_deduction += 10
        else:
            total_deduction += 5
    
    return max(0, 100 - total_deduction)

def analyze_condition_trends(damages: List[Dict], analysis_type: str) -> Dict:
    """Analyze condition trends and deterioration patterns"""
    return {
        'deterioration_rate': 'moderate',
        'primary_concerns': get_primary_concerns(damages),
        'maintenance_backlog': 'low',
        'seasonal_factors': get_seasonal_factors(analysis_type),
        'improvement_recommendations': get_improvement_recommendations(damages)
    }

def generate_inspection_summary(overall_score: float, damages: List[Dict], defects: List[Dict]) -> str:
    """Generate human-readable inspection summary"""
    if overall_score >= 90:
        return f"Property inspection reveals excellent condition with {len(damages + defects)} minor items requiring attention."
    elif overall_score >= 75:
        return f"Property is in good condition with {len(damages)} damage items and {len(defects)} maintenance items identified."
    elif overall_score >= 60:
        return f"Property requires moderate attention with {len(damages)} damage items needing repair."
    else:
        return f"Property inspection reveals significant issues requiring immediate attention ({len(damages)} damage items identified)."

def calculate_next_inspection_date(condition_rating: str) -> str:
    """Calculate recommended next inspection date"""
    from datetime import datetime, timedelta
    
    inspection_intervals = {
        'excellent': 365,  # 1 year
        'good': 180,       # 6 months
        'fair': 90,        # 3 months
        'poor': 30,        # 1 month
        'critical': 7      # 1 week
    }
    
    days_until_next = inspection_intervals.get(condition_rating, 180)
    next_date = datetime.now() + timedelta(days=days_until_next)
    
    return next_date.isoformat()

def simulate_safety_hazard_detection(image_analysis: Dict) -> List[Dict]:
    """Simulate safety hazard detection"""
    hazards = []
    
    # Check for electrical hazards
    detected_objects = image_analysis.get('detected_objects', [])
    for obj in detected_objects:
        if obj['object'] == 'outlets' and obj['condition'] in ['poor', 'needs_repair']:
            hazards.append({
                'hazard_type': 'electrical_safety',
                'severity': 'high',
                'description': 'Damaged electrical outlets pose shock/fire risk',
                'immediate_action_required': True,
                'location': obj.get('bbox', [])
            })
    
    return hazards

def calculate_safety_score(hazards: List[Dict]) -> float:
    """Calculate overall safety score"""
    if not hazards:
        return 100.0
    
    score_reduction = 0
    for hazard in hazards:
        if hazard['severity'] == 'high':
            score_reduction += 25
        elif hazard['severity'] == 'medium':
            score_reduction += 10
        else:
            score_reduction += 5
    
    return max(0, 100 - score_reduction)

def determine_safety_rating(safety_score: float) -> str:
    """Determine safety rating from score"""
    if safety_score >= 90:
        return 'safe'
    elif safety_score >= 70:
        return 'minor_concerns'
    elif safety_score >= 50:
        return 'moderate_risk'
    else:
        return 'high_risk'

def generate_emergency_recommendations(hazards: List[Dict]) -> List[str]:
    """Generate emergency action recommendations"""
    recommendations = []
    
    immediate_hazards = [h for h in hazards if h.get('immediate_action_required', False)]
    
    if immediate_hazards:
        recommendations.append('Immediately restrict access to affected areas')
        recommendations.append('Contact qualified contractors for emergency repairs')
        recommendations.append('Document all safety hazards with additional photos')
        recommendations.append('Consider temporary tenant relocation if necessary')
    
    return recommendations

def create_maintenance_recommendation(issue: Dict, condition_assessment: Dict) -> Optional[Dict]:
    """Create maintenance recommendation for a specific issue"""
    return {
        'issue_id': issue.get('type', 'unknown'),
        'recommendation': f"Repair {issue.get('type', 'unknown').replace('_', ' ')}",
        'description': issue.get('description', ''),
        'priority_score': calculate_issue_priority(issue, condition_assessment),
        'urgency_days': convert_urgency_to_days(issue.get('repair_urgency', 'within_90_days')),
        'estimated_duration': estimate_repair_duration(issue),
        'required_skills': determine_required_skills(issue),
        'safety_precautions': get_safety_precautions(issue)
    }

def generate_preventive_recommendations(condition_assessment: Dict) -> List[Dict]:
    """Generate preventive maintenance recommendations"""
    recommendations = []
    
    if condition_assessment['overall_score'] < 80:
        recommendations.append({
            'issue_id': 'preventive_inspection',
            'recommendation': 'Schedule comprehensive preventive maintenance inspection',
            'description': 'Regular inspection to prevent further deterioration',
            'priority_score': 6,
            'urgency_days': 30,
            'estimated_duration': '2-4 hours',
            'required_skills': ['general_maintenance'],
            'safety_precautions': ['standard_safety_equipment']
        })
    
    return recommendations

def calculate_confidence_level(image_analysis: Dict) -> str:
    """Calculate confidence level of the analysis"""
    image_quality = image_analysis.get('image_quality_score', 0.5)
    
    if image_quality >= 0.8:
        return 'High'
    elif image_quality >= 0.6:
        return 'Medium'
    else:
        return 'Low'

def generate_ai_insights(damage_detection: Dict, condition_assessment: Dict, safety_assessment: Dict) -> List[str]:
    """Generate AI-powered insights from the analysis"""
    insights = []
    
    damage_score = damage_detection.get('damage_score', 100)
    overall_score = condition_assessment.get('overall_score', 100)
    safety_score = safety_assessment.get('safety_score', 100)
    
    if damage_score < 70:
        insights.append('Property shows significant wear requiring proactive maintenance strategy')
    
    if overall_score > 85:
        insights.append('Property is well-maintained and suitable for premium rental rates')
    
    if safety_score < 80:
        insights.append('Safety concerns identified - prioritize immediate remediation')
    
    damages = damage_detection.get('damages', [])
    if len(damages) > 5:
        insights.append('High number of issues detected - consider comprehensive renovation')
    
    return insights

# Additional helper functions
def calculate_cost_by_severity(itemized_costs: List[Dict]) -> Dict:
    """Calculate cost breakdown by severity"""
    severity_costs = {'high': 0, 'medium': 0, 'low': 0}
    
    for item in itemized_costs:
        severity = item['severity']
        avg_cost = (item['cost_range']['low'] + item['cost_range']['high']) / 2
        severity_costs[severity] += avg_cost
    
    return {k: round(v, 2) for k, v in severity_costs.items()}

def calculate_cost_confidence(damages: List[Dict]) -> str:
    """Calculate confidence in cost estimates"""
    if len(damages) <= 2:
        return 'High'
    elif len(damages) <= 5:
        return 'Medium'
    else:
        return 'Low'

def calculate_urgency_premium(damages: List[Dict]) -> float:
    """Calculate urgency premium for immediate repairs"""
    immediate_repairs = [d for d in damages if d.get('repair_urgency') == 'immediate']
    return 1.2 if immediate_repairs else 1.0

def get_primary_concerns(damages: List[Dict]) -> List[str]:
    """Get primary areas of concern"""
    concern_areas = set()
    for damage in damages:
        if damage['severity'] in ['high', 'medium']:
            damage_type = damage['type'].split('_')[0]  # Get main category
            concern_areas.add(damage_type)
    
    return list(concern_areas)

def get_seasonal_factors(analysis_type: str) -> List[str]:
    """Get seasonal factors affecting the analysis"""
    current_month = datetime.now().month
    
    if current_month in [12, 1, 2]:  # Winter
        return ['cold_weather_stress', 'ice_damage_risk', 'heating_system_load']
    elif current_month in [6, 7, 8]:  # Summer
        return ['heat_stress', 'uv_exposure', 'cooling_system_load']
    else:
        return ['moderate_conditions', 'seasonal_transition']

def get_improvement_recommendations(damages: List[Dict]) -> List[str]:
    """Get general improvement recommendations"""
    recommendations = []
    
    damage_types = [d['type'] for d in damages]
    
    if any('paint' in dt for dt in damage_types):
        recommendations.append('Consider premium paint for better durability')
    
    if any('roof' in dt for dt in damage_types):
        recommendations.append('Regular roof inspections every 6 months')
    
    if any('electrical' in dt for dt in damage_types):
        recommendations.append('Electrical system upgrade recommended')
    
    return recommendations

def calculate_issue_priority(issue: Dict, condition_assessment: Dict) -> int:
    """Calculate priority score for an issue (1-10)"""
    base_priority = {'high': 9, 'medium': 6, 'low': 3}.get(issue.get('severity', 'low'), 3)
    
    # Adjust based on overall condition
    overall_score = condition_assessment.get('overall_score', 75)
    if overall_score < 60:
        base_priority = min(10, base_priority + 2)
    
    return base_priority

def convert_urgency_to_days(urgency: str) -> int:
    """Convert urgency string to days"""
    urgency_map = {
        'immediate': 1,
        'within_7_days': 7,
        'within_30_days': 30,
        'within_60_days': 60,
        'within_90_days': 90,
        'monitor': 180
    }
    return urgency_map.get(urgency, 30)

def estimate_repair_duration(issue: Dict) -> str:
    """Estimate repair duration"""
    severity = issue.get('severity', 'low')
    
    if severity == 'high':
        return '1-3 days'
    elif severity == 'medium':
        return '4-8 hours'
    else:
        return '1-2 hours'

def determine_required_skills(issue: Dict) -> List[str]:
    """Determine required skills for repair"""
    issue_type = issue.get('type', '').lower()
    
    if 'electrical' in issue_type:
        return ['licensed_electrician']
    elif 'plumbing' in issue_type:
        return ['licensed_plumber']
    elif 'roof' in issue_type:
        return ['roofing_contractor']
    else:
        return ['general_maintenance']

def get_safety_precautions(issue: Dict) -> List[str]:
    """Get safety precautions for repair"""
    issue_type = issue.get('type', '').lower()
    severity = issue.get('severity', 'low')
    
    precautions = ['standard_safety_equipment']
    
    if 'electrical' in issue_type:
        precautions.extend(['power_shutoff', 'electrical_safety_gear'])
    
    if severity == 'high':
        precautions.append('supervisor_oversight')
    
    return precautions

def calculate_priority_score(damage_detection: Dict, safety_assessment: Dict, condition_assessment: Dict) -> int:
    """Calculate overall priority score for the inspection (1-10 scale)"""
    damage_score = damage_detection.get('damage_score', 100)
    safety_score = safety_assessment.get('safety_score', 100)
    overall_score = condition_assessment.get('overall_score', 100)
    
    # High priority if safety issues
    if safety_score < 70:
        return 10
    
    # High priority if many damages
    total_issues = damage_detection.get('total_issues', 0)
    immediate_issues = damage_detection.get('immediate_attention_count', 0)
    
    if immediate_issues > 0:
        return 9
    elif total_issues > 5:
        return 8
    elif overall_score < 60:
        return 7
    elif overall_score < 80:
        return 5
    else:
        return 3