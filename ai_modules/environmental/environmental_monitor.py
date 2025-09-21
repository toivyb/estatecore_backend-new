import numpy as np
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import random
import math

class EnvironmentalMetric(Enum):
    AIR_QUALITY = "air_quality"
    CARBON_FOOTPRINT = "carbon_footprint"
    WATER_QUALITY = "water_quality"
    NOISE_LEVEL = "noise_level"
    LIGHT_POLLUTION = "light_pollution"
    WASTE_MANAGEMENT = "waste_management"
    ENERGY_EFFICIENCY = "energy_efficiency"
    INDOOR_AIR_QUALITY = "indoor_air_quality"
    WATER_CONSUMPTION = "water_consumption"
    RENEWABLE_ENERGY = "renewable_energy"

class AlertLevel(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SustainabilityRating(Enum):
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 70-89
    FAIR = "fair"           # 50-69
    POOR = "poor"           # 30-49
    CRITICAL = "critical"   # 0-29

@dataclass
class EnvironmentalReading:
    reading_id: str
    property_id: str
    location: str
    metric_type: EnvironmentalMetric
    value: float
    unit: str
    timestamp: datetime
    sensor_id: str
    
    # Quality metrics
    confidence_score: float
    calibration_status: str
    
    # Context
    weather_conditions: Dict[str, Any]
    occupancy_level: float
    
    # Analysis
    baseline_value: float
    deviation_percentage: float
    trend_direction: str  # "improving", "stable", "declining"

@dataclass
class EnvironmentalAlert:
    alert_id: str
    property_id: str
    metric_type: EnvironmentalMetric
    alert_level: AlertLevel
    
    # Alert details
    current_value: float
    threshold_value: float
    severity_score: float
    
    # Impact assessment
    health_impact: str
    environmental_impact: str
    regulatory_compliance: bool
    
    # Recommendations
    immediate_actions: List[str]
    long_term_solutions: List[str]
    estimated_cost: float
    
    # Metadata
    created_at: datetime
    acknowledged: bool
    resolved: bool

@dataclass
class SustainabilityReport:
    report_id: str
    property_id: str
    report_period: str
    generated_at: datetime
    
    # Overall ratings
    overall_sustainability_score: float
    sustainability_rating: SustainabilityRating
    previous_period_score: float
    improvement_percentage: float
    
    # Metric breakdowns
    air_quality_score: float
    energy_efficiency_score: float
    water_conservation_score: float
    waste_management_score: float
    carbon_footprint_score: float
    
    # ESG Compliance
    esg_compliance_score: float
    regulatory_violations: int
    certifications_eligible: List[str]
    
    # Financial impact
    sustainability_cost_savings: float
    environmental_penalties: float
    green_incentives_earned: float
    
    # Recommendations
    priority_improvements: List[str]
    investment_recommendations: List[Dict[str, Any]]
    certification_opportunities: List[str]

class EnvironmentalMonitor:
    """
    Advanced environmental monitoring and sustainability analytics system
    """
    
    def __init__(self):
        self.readings = {}
        self.alerts = {}
        self.baselines = {}
        self.thresholds = {}
        self.sustainability_reports = {}
        self._initialize_environmental_standards()
    
    def _initialize_environmental_standards(self):
        """Initialize environmental standards and thresholds"""
        
        # Air Quality Index (AQI) standards
        self.thresholds[EnvironmentalMetric.AIR_QUALITY] = {
            'excellent': 50,    # 0-50: Good
            'good': 100,        # 51-100: Moderate  
            'warning': 150,     # 101-150: Unhealthy for sensitive groups
            'critical': 200,    # 151-200: Unhealthy
            'emergency': 300    # 201-300: Very unhealthy
        }
        
        # Indoor Air Quality (CO2 ppm)
        self.thresholds[EnvironmentalMetric.INDOOR_AIR_QUALITY] = {
            'excellent': 400,   # Outdoor level
            'good': 800,        # Acceptable
            'warning': 1000,    # Drowsiness
            'critical': 5000,   # Workplace exposure limit
            'emergency': 40000  # Immediately dangerous
        }
        
        # Noise levels (dB)
        self.thresholds[EnvironmentalMetric.NOISE_LEVEL] = {
            'excellent': 35,    # Very quiet
            'good': 45,         # Quiet residential
            'warning': 55,      # Normal conversation
            'critical': 70,     # Traffic noise
            'emergency': 85     # Hearing damage risk
        }
        
        # Water Quality (contamination index)
        self.thresholds[EnvironmentalMetric.WATER_QUALITY] = {
            'excellent': 5,     # Excellent quality
            'good': 15,         # Good quality
            'warning': 30,      # Fair quality
            'critical': 50,     # Poor quality
            'emergency': 100    # Unacceptable
        }
        
        # Energy Efficiency (kWh per sq ft per month)
        self.thresholds[EnvironmentalMetric.ENERGY_EFFICIENCY] = {
            'excellent': 1.0,   # Very efficient
            'good': 2.0,        # Efficient
            'warning': 3.5,     # Average
            'critical': 5.0,    # Inefficient
            'emergency': 7.0    # Very inefficient
        }
    
    def process_environmental_data(self, sensor_data: Dict[str, Any], property_id: str) -> List[EnvironmentalReading]:
        """Process raw sensor data into environmental readings"""
        
        readings = []
        timestamp = datetime.now()
        
        for sensor_reading in sensor_data.get('sensor_readings', []):
            reading = self._create_environmental_reading(sensor_reading, property_id, timestamp)
            if reading:
                readings.append(reading)
                
                # Store reading
                if property_id not in self.readings:
                    self.readings[property_id] = []
                self.readings[property_id].append(reading)
                
                # Check for alerts
                alert = self._evaluate_alert_conditions(reading)
                if alert:
                    self.alerts[alert.alert_id] = alert
        
        return readings
    
    def _create_environmental_reading(self, sensor_data: Dict[str, Any], property_id: str, timestamp: datetime) -> Optional[EnvironmentalReading]:
        """Create environmental reading from sensor data"""
        
        sensor_type = sensor_data.get('sensor_type', '')
        value = sensor_data.get('value', 0)
        location = sensor_data.get('location', 'Unknown')
        
        # Map sensor types to environmental metrics
        metric_mapping = {
            'air_quality': EnvironmentalMetric.AIR_QUALITY,
            'co2': EnvironmentalMetric.INDOOR_AIR_QUALITY,
            'noise': EnvironmentalMetric.NOISE_LEVEL,
            'water_quality': EnvironmentalMetric.WATER_QUALITY,
            'energy': EnvironmentalMetric.ENERGY_EFFICIENCY
        }
        
        metric_type = metric_mapping.get(sensor_type)
        if not metric_type:
            return None
        
        # Get baseline for comparison
        baseline = self._get_baseline_value(property_id, metric_type, location)
        deviation = ((value - baseline) / baseline * 100) if baseline > 0 else 0
        
        # Determine trend
        trend = self._calculate_trend(property_id, metric_type, location, value)
        
        # Unit mapping
        unit_mapping = {
            EnvironmentalMetric.AIR_QUALITY: 'AQI',
            EnvironmentalMetric.INDOOR_AIR_QUALITY: 'ppm',
            EnvironmentalMetric.NOISE_LEVEL: 'dB',
            EnvironmentalMetric.WATER_QUALITY: 'WQI',
            EnvironmentalMetric.ENERGY_EFFICIENCY: 'kWh/sqft'
        }
        
        reading = EnvironmentalReading(
            reading_id=f"env_{property_id}_{int(time.time())}_{random.randint(1000, 9999)}",
            property_id=property_id,
            location=location,
            metric_type=metric_type,
            value=value,
            unit=unit_mapping.get(metric_type, 'units'),
            timestamp=timestamp,
            sensor_id=sensor_data.get('sensor_id', f"sensor_{sensor_type}_{location}"),
            confidence_score=sensor_data.get('confidence', 0.95),
            calibration_status=sensor_data.get('calibration_status', 'calibrated'),
            weather_conditions=sensor_data.get('weather', {}),
            occupancy_level=sensor_data.get('occupancy', 0.5),
            baseline_value=baseline,
            deviation_percentage=round(deviation, 2),
            trend_direction=trend
        )
        
        return reading
    
    def _get_baseline_value(self, property_id: str, metric_type: EnvironmentalMetric, location: str) -> float:
        """Get baseline value for a metric"""
        
        key = f"{property_id}_{metric_type.value}_{location}"
        
        if key in self.baselines:
            return self.baselines[key]
        
        # Default baselines based on metric type
        default_baselines = {
            EnvironmentalMetric.AIR_QUALITY: 25,        # Good air quality
            EnvironmentalMetric.INDOOR_AIR_QUALITY: 400, # Outdoor CO2 level
            EnvironmentalMetric.NOISE_LEVEL: 40,        # Quiet environment
            EnvironmentalMetric.WATER_QUALITY: 10,      # Good water quality
            EnvironmentalMetric.ENERGY_EFFICIENCY: 2.0  # Efficient usage
        }
        
        baseline = default_baselines.get(metric_type, 50)
        self.baselines[key] = baseline
        return baseline
    
    def _calculate_trend(self, property_id: str, metric_type: EnvironmentalMetric, location: str, current_value: float) -> str:
        """Calculate trend direction for a metric"""
        
        # Get recent readings for this metric
        recent_readings = []
        if property_id in self.readings:
            recent_readings = [
                r for r in self.readings[property_id][-10:]  # Last 10 readings
                if r.metric_type == metric_type and r.location == location
            ]
        
        if len(recent_readings) < 3:
            return "stable"
        
        # Calculate trend using linear regression
        values = [r.value for r in recent_readings] + [current_value]
        x = list(range(len(values)))
        
        # Simple linear regression
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.1:
            return "improving" if metric_type in [EnvironmentalMetric.ENERGY_EFFICIENCY] else "declining"
        elif slope < -0.1:
            return "declining" if metric_type in [EnvironmentalMetric.ENERGY_EFFICIENCY] else "improving"
        else:
            return "stable"
    
    def _evaluate_alert_conditions(self, reading: EnvironmentalReading) -> Optional[EnvironmentalAlert]:
        """Evaluate if reading triggers an alert"""
        
        metric_thresholds = self.thresholds.get(reading.metric_type, {})
        value = reading.value
        
        # Determine alert level
        alert_level = None
        threshold_value = 0
        
        if value >= metric_thresholds.get('emergency', float('inf')):
            alert_level = AlertLevel.EMERGENCY
            threshold_value = metric_thresholds['emergency']
        elif value >= metric_thresholds.get('critical', float('inf')):
            alert_level = AlertLevel.CRITICAL
            threshold_value = metric_thresholds['critical']
        elif value >= metric_thresholds.get('warning', float('inf')):
            alert_level = AlertLevel.WARNING
            threshold_value = metric_thresholds['warning']
        
        if alert_level is None:
            return None
        
        # Calculate severity score
        severity_score = min(100, (value / threshold_value) * 100)
        
        # Generate recommendations
        immediate_actions, long_term_solutions, cost = self._generate_environmental_recommendations(
            reading.metric_type, alert_level, value
        )
        
        alert = EnvironmentalAlert(
            alert_id=f"alert_{reading.property_id}_{reading.metric_type.value}_{int(time.time())}",
            property_id=reading.property_id,
            metric_type=reading.metric_type,
            alert_level=alert_level,
            current_value=value,
            threshold_value=threshold_value,
            severity_score=severity_score,
            health_impact=self._assess_health_impact(reading.metric_type, alert_level),
            environmental_impact=self._assess_environmental_impact(reading.metric_type, alert_level),
            regulatory_compliance=self._check_regulatory_compliance(reading.metric_type, value),
            immediate_actions=immediate_actions,
            long_term_solutions=long_term_solutions,
            estimated_cost=cost,
            created_at=reading.timestamp,
            acknowledged=False,
            resolved=False
        )
        
        return alert
    
    def _generate_environmental_recommendations(self, metric_type: EnvironmentalMetric, alert_level: AlertLevel, value: float) -> Tuple[List[str], List[str], float]:
        """Generate environmental improvement recommendations"""
        
        immediate_actions = []
        long_term_solutions = []
        estimated_cost = 0
        
        if metric_type == EnvironmentalMetric.AIR_QUALITY:
            if alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                immediate_actions = [
                    "Activate air filtration systems",
                    "Restrict outdoor activities",
                    "Close windows and doors",
                    "Use HEPA air purifiers"
                ]
                long_term_solutions = [
                    "Install building-wide air filtration system",
                    "Implement green roof or vertical gardens",
                    "Upgrade HVAC system with advanced filters"
                ]
                estimated_cost = 15000
            else:
                immediate_actions = [
                    "Increase ventilation",
                    "Monitor air quality hourly"
                ]
                long_term_solutions = [
                    "Plant air-purifying vegetation",
                    "Improve building envelope"
                ]
                estimated_cost = 5000
        
        elif metric_type == EnvironmentalMetric.INDOOR_AIR_QUALITY:
            if alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                immediate_actions = [
                    "Increase fresh air intake",
                    "Evacuate affected areas if necessary",
                    "Check HVAC system operation"
                ]
                long_term_solutions = [
                    "Install CO2 monitoring and control system",
                    "Upgrade ventilation system",
                    "Implement demand-controlled ventilation"
                ]
                estimated_cost = 12000
            else:
                immediate_actions = [
                    "Open windows for natural ventilation",
                    "Reduce occupancy density"
                ]
                long_term_solutions = [
                    "Install smart ventilation controls",
                    "Add indoor plants for natural air purification"
                ]
                estimated_cost = 3000
        
        elif metric_type == EnvironmentalMetric.NOISE_LEVEL:
            if alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                immediate_actions = [
                    "Identify and eliminate noise sources",
                    "Provide hearing protection",
                    "Temporarily relocate sensitive activities"
                ]
                long_term_solutions = [
                    "Install acoustic insulation",
                    "Implement noise barriers",
                    "Upgrade to quieter equipment"
                ]
                estimated_cost = 8000
            else:
                immediate_actions = [
                    "Monitor noise levels throughout day",
                    "Adjust equipment schedules"
                ]
                long_term_solutions = [
                    "Add sound-absorbing materials",
                    "Landscape with noise-reducing vegetation"
                ]
                estimated_cost = 2500
        
        elif metric_type == EnvironmentalMetric.ENERGY_EFFICIENCY:
            if alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                immediate_actions = [
                    "Conduct energy audit",
                    "Identify energy waste sources",
                    "Implement immediate conservation measures"
                ]
                long_term_solutions = [
                    "Upgrade to energy-efficient equipment",
                    "Install renewable energy systems",
                    "Implement smart building automation"
                ]
                estimated_cost = 25000
            else:
                immediate_actions = [
                    "Optimize equipment schedules",
                    "Improve building operations"
                ]
                long_term_solutions = [
                    "LED lighting upgrade",
                    "Smart thermostat installation"
                ]
                estimated_cost = 8000
        
        return immediate_actions, long_term_solutions, estimated_cost
    
    def _assess_health_impact(self, metric_type: EnvironmentalMetric, alert_level: AlertLevel) -> str:
        """Assess health impact of environmental condition"""
        
        impact_matrix = {
            EnvironmentalMetric.AIR_QUALITY: {
                AlertLevel.WARNING: "Mild respiratory irritation for sensitive individuals",
                AlertLevel.CRITICAL: "Respiratory symptoms, eye irritation",
                AlertLevel.EMERGENCY: "Serious health risks, avoid outdoor exposure"
            },
            EnvironmentalMetric.INDOOR_AIR_QUALITY: {
                AlertLevel.WARNING: "Reduced cognitive performance, drowsiness",
                AlertLevel.CRITICAL: "Headaches, fatigue, poor concentration",
                AlertLevel.EMERGENCY: "Immediate health danger, evacuation required"
            },
            EnvironmentalMetric.NOISE_LEVEL: {
                AlertLevel.WARNING: "Sleep disruption, stress increase",
                AlertLevel.CRITICAL: "Hearing damage risk, cardiovascular stress",
                AlertLevel.EMERGENCY: "Immediate hearing damage risk"
            },
            EnvironmentalMetric.WATER_QUALITY: {
                AlertLevel.WARNING: "Taste and odor issues",
                AlertLevel.CRITICAL: "Potential gastrointestinal issues",
                AlertLevel.EMERGENCY: "Serious health risk, do not consume"
            }
        }
        
        return impact_matrix.get(metric_type, {}).get(alert_level, "Monitor for potential health impacts")
    
    def _assess_environmental_impact(self, metric_type: EnvironmentalMetric, alert_level: AlertLevel) -> str:
        """Assess environmental impact"""
        
        impact_matrix = {
            EnvironmentalMetric.AIR_QUALITY: {
                AlertLevel.WARNING: "Reduced air quality affects local ecosystem",
                AlertLevel.CRITICAL: "Significant environmental degradation",
                AlertLevel.EMERGENCY: "Severe environmental damage"
            },
            EnvironmentalMetric.ENERGY_EFFICIENCY: {
                AlertLevel.WARNING: "Increased carbon footprint",
                AlertLevel.CRITICAL: "Significant environmental waste",
                AlertLevel.EMERGENCY: "Unsustainable resource consumption"
            }
        }
        
        return impact_matrix.get(metric_type, {}).get(alert_level, "Minimal environmental impact")
    
    def _check_regulatory_compliance(self, metric_type: EnvironmentalMetric, value: float) -> bool:
        """Check if reading meets regulatory standards"""
        
        # Simplified regulatory compliance check
        regulatory_limits = {
            EnvironmentalMetric.AIR_QUALITY: 150,          # EPA standard
            EnvironmentalMetric.INDOOR_AIR_QUALITY: 1000,  # OSHA standard
            EnvironmentalMetric.NOISE_LEVEL: 70,           # EPA residential limit
            EnvironmentalMetric.WATER_QUALITY: 50          # EPA drinking water standard
        }
        
        limit = regulatory_limits.get(metric_type)
        return limit is None or value <= limit
    
    def generate_sustainability_report(self, property_id: str, period: str = "monthly") -> SustainabilityReport:
        """Generate comprehensive sustainability report"""
        
        report_id = f"sustainability_{property_id}_{period}_{int(time.time())}"
        
        # Calculate period dates
        now = datetime.now()
        if period == "monthly":
            period_start = now.replace(day=1)
        elif period == "quarterly":
            period_start = now.replace(month=((now.month-1)//3)*3+1, day=1)
        else:  # yearly
            period_start = now.replace(month=1, day=1)
        
        # Get readings for the period
        property_readings = self.readings.get(property_id, [])
        period_readings = [
            r for r in property_readings
            if r.timestamp >= period_start
        ]
        
        # Calculate metric scores
        air_quality_score = self._calculate_metric_score(period_readings, EnvironmentalMetric.AIR_QUALITY)
        energy_efficiency_score = self._calculate_metric_score(period_readings, EnvironmentalMetric.ENERGY_EFFICIENCY)
        water_conservation_score = self._calculate_metric_score(period_readings, EnvironmentalMetric.WATER_QUALITY)
        noise_score = self._calculate_metric_score(period_readings, EnvironmentalMetric.NOISE_LEVEL)
        
        # Calculate overall sustainability score
        overall_score = (
            air_quality_score * 0.25 +
            energy_efficiency_score * 0.30 +
            water_conservation_score * 0.20 +
            noise_score * 0.15 +
            70  # Base score for other factors
        )
        
        # Determine sustainability rating
        if overall_score >= 90:
            rating = SustainabilityRating.EXCELLENT
        elif overall_score >= 70:
            rating = SustainabilityRating.GOOD
        elif overall_score >= 50:
            rating = SustainabilityRating.FAIR
        elif overall_score >= 30:
            rating = SustainabilityRating.POOR
        else:
            rating = SustainabilityRating.CRITICAL
        
        # Calculate financial impacts
        cost_savings = self._calculate_sustainability_savings(overall_score)
        penalties = self._calculate_environmental_penalties(property_id)
        incentives = self._calculate_green_incentives(overall_score)
        
        # Generate recommendations
        priority_improvements = self._generate_priority_improvements(period_readings)
        investment_recommendations = self._generate_investment_recommendations(overall_score)
        certifications = self._identify_certification_opportunities(overall_score)
        
        report = SustainabilityReport(
            report_id=report_id,
            property_id=property_id,
            report_period=period,
            generated_at=now,
            overall_sustainability_score=round(overall_score, 1),
            sustainability_rating=rating,
            previous_period_score=round(overall_score - random.uniform(-5, 8), 1),  # Simulated
            improvement_percentage=round(random.uniform(-5, 12), 1),  # Simulated
            air_quality_score=round(air_quality_score, 1),
            energy_efficiency_score=round(energy_efficiency_score, 1),
            water_conservation_score=round(water_conservation_score, 1),
            waste_management_score=75.0,  # Simulated
            carbon_footprint_score=round(energy_efficiency_score * 0.8, 1),
            esg_compliance_score=round(overall_score * 0.9, 1),
            regulatory_violations=len([a for a in self.alerts.values() if not a.regulatory_compliance]),
            certifications_eligible=certifications,
            sustainability_cost_savings=cost_savings,
            environmental_penalties=penalties,
            green_incentives_earned=incentives,
            priority_improvements=priority_improvements,
            investment_recommendations=investment_recommendations,
            certification_opportunities=certifications
        )
        
        self.sustainability_reports[report_id] = report
        return report
    
    def _calculate_metric_score(self, readings: List[EnvironmentalReading], metric_type: EnvironmentalMetric) -> float:
        """Calculate score for a specific environmental metric"""
        
        metric_readings = [r for r in readings if r.metric_type == metric_type]
        if not metric_readings:
            return 50  # Default neutral score
        
        # Calculate average value
        avg_value = sum(r.value for r in metric_readings) / len(metric_readings)
        
        # Score based on thresholds (inverted for "lower is better" metrics)
        thresholds = self.thresholds.get(metric_type, {})
        
        if metric_type in [EnvironmentalMetric.AIR_QUALITY, EnvironmentalMetric.NOISE_LEVEL, 
                          EnvironmentalMetric.INDOOR_AIR_QUALITY]:
            # Lower values are better
            if avg_value <= thresholds.get('excellent', 0):
                return 95
            elif avg_value <= thresholds.get('good', 0):
                return 80
            elif avg_value <= thresholds.get('warning', 0):
                return 60
            elif avg_value <= thresholds.get('critical', 0):
                return 35
            else:
                return 15
        else:
            # Higher values are better (for efficiency metrics)
            if avg_value >= thresholds.get('excellent', 100):
                return 95
            elif avg_value >= thresholds.get('good', 80):
                return 80
            elif avg_value >= thresholds.get('warning', 60):
                return 60
            elif avg_value >= thresholds.get('critical', 40):
                return 35
            else:
                return 15
    
    def _calculate_sustainability_savings(self, overall_score: float) -> float:
        """Calculate cost savings from sustainability initiatives"""
        # Higher sustainability scores correlate with cost savings
        base_savings = 1000  # Base monthly savings
        score_multiplier = overall_score / 100
        return round(base_savings * score_multiplier * random.uniform(0.8, 1.5), 2)
    
    def _calculate_environmental_penalties(self, property_id: str) -> float:
        """Calculate environmental penalties and fines"""
        # Based on regulatory violations
        property_alerts = [a for a in self.alerts.values() if a.property_id == property_id and not a.regulatory_compliance]
        penalty_per_violation = 500
        return len(property_alerts) * penalty_per_violation
    
    def _calculate_green_incentives(self, overall_score: float) -> float:
        """Calculate green incentives and rebates earned"""
        if overall_score >= 80:
            return round(random.uniform(2000, 5000), 2)
        elif overall_score >= 60:
            return round(random.uniform(500, 2000), 2)
        else:
            return 0
    
    def _generate_priority_improvements(self, readings: List[EnvironmentalReading]) -> List[str]:
        """Generate priority improvement recommendations"""
        improvements = []
        
        # Analyze worst-performing metrics
        metric_scores = {}
        for metric in EnvironmentalMetric:
            score = self._calculate_metric_score(readings, metric)
            metric_scores[metric] = score
        
        # Sort by lowest scores
        sorted_metrics = sorted(metric_scores.items(), key=lambda x: x[1])
        
        for metric, score in sorted_metrics[:3]:  # Top 3 worst metrics
            if score < 60:
                improvements.append(f"Improve {metric.value.replace('_', ' ')} (current score: {score:.1f}/100)")
        
        return improvements
    
    def _generate_investment_recommendations(self, overall_score: float) -> List[Dict[str, Any]]:
        """Generate investment recommendations for sustainability"""
        recommendations = []
        
        if overall_score < 70:
            recommendations.append({
                'category': 'Air Quality',
                'investment': 'Building-wide air filtration system',
                'cost': 15000,
                'payback_months': 18,
                'annual_savings': 3200,
                'environmental_impact': 'Significant air quality improvement'
            })
        
        if overall_score < 60:
            recommendations.append({
                'category': 'Energy Efficiency',
                'investment': 'Smart building automation system',
                'cost': 25000,
                'payback_months': 24,
                'annual_savings': 12000,
                'environmental_impact': 'Reduce energy consumption by 20%'
            })
        
        recommendations.append({
            'category': 'Renewable Energy',
            'investment': 'Solar panel installation',
            'cost': 40000,
            'payback_months': 60,
            'annual_savings': 8000,
            'environmental_impact': 'Carbon neutral energy generation'
        })
        
        return recommendations
    
    def _identify_certification_opportunities(self, overall_score: float) -> List[str]:
        """Identify available green building certifications"""
        certifications = []
        
        if overall_score >= 80:
            certifications.extend(['LEED Gold', 'ENERGY STAR', 'Green Globes'])
        elif overall_score >= 60:
            certifications.extend(['LEED Silver', 'BREEAM Good'])
        elif overall_score >= 40:
            certifications.extend(['LEED Certified', 'BREEAM Pass'])
        
        return certifications
    
    def get_real_time_environmental_status(self, property_id: str) -> Dict[str, Any]:
        """Get real-time environmental status for a property"""
        
        # Get recent readings (last hour)
        recent_readings = []
        if property_id in self.readings:
            cutoff_time = datetime.now() - timedelta(hours=1)
            recent_readings = [
                r for r in self.readings[property_id]
                if r.timestamp >= cutoff_time
            ]
        
        # Get active alerts
        active_alerts = [
            a for a in self.alerts.values()
            if a.property_id == property_id and not a.resolved
        ]
        
        # Calculate current status
        status = {
            'property_id': property_id,
            'last_updated': datetime.now().isoformat(),
            'overall_status': 'normal',
            'active_alerts_count': len(active_alerts),
            'critical_alerts': len([a for a in active_alerts if a.alert_level == AlertLevel.CRITICAL]),
            'metrics': {},
            'trends': {},
            'recommendations': []
        }
        
        # Process recent readings by metric
        for metric in EnvironmentalMetric:
            metric_readings = [r for r in recent_readings if r.metric_type == metric]
            if metric_readings:
                latest_reading = max(metric_readings, key=lambda x: x.timestamp)
                status['metrics'][metric.value] = {
                    'current_value': latest_reading.value,
                    'unit': latest_reading.unit,
                    'status': 'normal',  # Would be calculated based on thresholds
                    'trend': latest_reading.trend_direction,
                    'deviation_from_baseline': latest_reading.deviation_percentage
                }
        
        # Set overall status based on alerts
        if any(a.alert_level == AlertLevel.EMERGENCY for a in active_alerts):
            status['overall_status'] = 'emergency'
        elif any(a.alert_level == AlertLevel.CRITICAL for a in active_alerts):
            status['overall_status'] = 'critical'
        elif any(a.alert_level == AlertLevel.WARNING for a in active_alerts):
            status['overall_status'] = 'warning'
        
        return status

def serialize_environmental_reading(reading: EnvironmentalReading) -> Dict:
    """Convert EnvironmentalReading to JSON-serializable dict"""
    result = asdict(reading)
    result['metric_type'] = reading.metric_type.value
    result['timestamp'] = reading.timestamp.isoformat()
    return result

def serialize_environmental_alert(alert: EnvironmentalAlert) -> Dict:
    """Convert EnvironmentalAlert to JSON-serializable dict"""
    result = asdict(alert)
    result['metric_type'] = alert.metric_type.value
    result['alert_level'] = alert.alert_level.value
    result['created_at'] = alert.created_at.isoformat()
    return result

def serialize_sustainability_report(report: SustainabilityReport) -> Dict:
    """Convert SustainabilityReport to JSON-serializable dict"""
    result = asdict(report)
    result['sustainability_rating'] = report.sustainability_rating.value
    result['generated_at'] = report.generated_at.isoformat()
    return result