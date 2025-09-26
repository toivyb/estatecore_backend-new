import numpy as np
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import random

class MaintenanceType(Enum):
    HVAC = "hvac"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    STRUCTURAL = "structural"
    APPLIANCES = "appliances"
    SECURITY = "security"
    FIRE_SAFETY = "fire_safety"
    ELEVATOR = "elevator"
    ROOFING = "roofing"
    FLOORING = "flooring"

class PriorityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PREVENTIVE = "preventive"

@dataclass
class MaintenancePrediction:
    prediction_id: str
    equipment_id: str
    equipment_type: str
    maintenance_type: MaintenanceType
    failure_probability: float
    predicted_failure_date: datetime
    confidence_score: float
    priority_level: PriorityLevel
    estimated_cost: float
    recommended_action: str
    trigger_factors: List[str]
    property_id: str
    location: str
    created_at: datetime
    iot_trigger_data: Dict[str, Any] = None

@dataclass
class MaintenanceTask:
    task_id: str
    prediction_id: str
    equipment_id: str
    task_type: str
    description: str
    priority: PriorityLevel
    estimated_duration: timedelta
    estimated_cost: float
    required_skills: List[str]
    required_parts: List[str]
    scheduled_date: datetime
    status: str = "pending"
    assigned_technician: str = None
    property_id: str = ""
    location: str = ""

class PredictiveMaintenanceEngine:
    """
    Advanced predictive maintenance system using IoT sensor data and ML models
    """
    
    def __init__(self):
        self.equipment_models = {}
        self.maintenance_history = []
        self.active_predictions = {}
        self.iot_thresholds = {}
        self.failure_patterns = {}
        self._initialize_equipment_models()
    
    def _initialize_equipment_models(self):
        """Initialize equipment failure prediction models"""
        # HVAC System Model
        self.equipment_models['hvac'] = {
            'baseline_failure_rate': 0.02,  # 2% per month
            'sensor_weights': {
                'temperature_variance': 0.3,
                'energy_consumption': 0.25,
                'runtime_hours': 0.2,
                'vibration': 0.15,
                'air_quality': 0.1
            },
            'age_factor': 0.05,  # 5% increase per year
            'maintenance_factor': -0.3,  # 30% reduction with recent maintenance
            'seasonal_factor': {
                'summer': 1.5,  # Higher failure rate in summer
                'winter': 1.3,
                'spring': 0.8,
                'fall': 0.9
            }
        }
        
        # Plumbing System Model
        self.equipment_models['plumbing'] = {
            'baseline_failure_rate': 0.015,
            'sensor_weights': {
                'water_pressure': 0.4,
                'water_flow': 0.3,
                'temperature': 0.2,
                'humidity': 0.1
            },
            'age_factor': 0.04,
            'maintenance_factor': -0.25,
            'seasonal_factor': {
                'winter': 2.0,  # Higher failure rate due to freezing
                'summer': 0.8,
                'spring': 1.0,
                'fall': 1.2
            }
        }
        
        # Electrical System Model
        self.equipment_models['electrical'] = {
            'baseline_failure_rate': 0.01,
            'sensor_weights': {
                'voltage_fluctuation': 0.35,
                'current_load': 0.3,
                'temperature': 0.2,
                'power_factor': 0.15
            },
            'age_factor': 0.06,
            'maintenance_factor': -0.4,
            'seasonal_factor': {
                'summer': 1.4,  # Higher usage, more failures
                'winter': 1.2,
                'spring': 0.9,
                'fall': 1.0
            }
        }
    
    def analyze_iot_data_for_maintenance(self, iot_data: Dict, property_id: str) -> List[MaintenancePrediction]:
        """
        Analyze IoT sensor data to predict maintenance needs
        """
        predictions = []
        
        # Process each sensor reading
        for sensor_data in iot_data.get('sensor_readings', []):
            equipment_predictions = self._analyze_sensor_for_equipment(sensor_data, property_id)
            predictions.extend(equipment_predictions)
        
        # Correlate multiple sensors for system-level predictions
        system_predictions = self._analyze_system_correlations(iot_data, property_id)
        predictions.extend(system_predictions)
        
        # Filter and prioritize predictions
        filtered_predictions = self._filter_and_prioritize_predictions(predictions)
        
        return filtered_predictions
    
    def _analyze_sensor_for_equipment(self, sensor_data: Dict, property_id: str) -> List[MaintenancePrediction]:
        """Analyze individual sensor data for equipment-specific predictions"""
        predictions = []
        
        sensor_type = sensor_data.get('sensor_type', '')
        value = sensor_data.get('value', 0)
        location = sensor_data.get('location', 'Unknown')
        timestamp = datetime.fromisoformat(sensor_data.get('timestamp', datetime.now().isoformat()))
        
        # HVAC Analysis
        if sensor_type in ['temperature', 'air_quality', 'humidity']:
            hvac_prediction = self._predict_hvac_maintenance(sensor_data, property_id, location)
            if hvac_prediction:
                predictions.append(hvac_prediction)
        
        # Electrical Analysis
        elif sensor_type in ['energy', 'power']:
            electrical_prediction = self._predict_electrical_maintenance(sensor_data, property_id, location)
            if electrical_prediction:
                predictions.append(electrical_prediction)
        
        # Water System Analysis
        elif sensor_type in ['water', 'humidity']:
            plumbing_prediction = self._predict_plumbing_maintenance(sensor_data, property_id, location)
            if plumbing_prediction:
                predictions.append(plumbing_prediction)
        
        return predictions
    
    def _predict_hvac_maintenance(self, sensor_data: Dict, property_id: str, location: str) -> Optional[MaintenancePrediction]:
        """Predict HVAC maintenance needs based on sensor data"""
        sensor_type = sensor_data.get('sensor_type')
        value = sensor_data.get('value', 0)
        
        failure_probability = 0.0
        trigger_factors = []
        
        # Temperature variance analysis
        if sensor_type == 'temperature':
            # Simulate temperature variance analysis
            temp_variance = abs(value - 72)  # Deviation from ideal 72°F
            if temp_variance > 8:
                failure_probability += 0.3
                trigger_factors.append(f'High temperature variance: {temp_variance:.1f}°F')
            elif temp_variance > 5:
                failure_probability += 0.15
                trigger_factors.append(f'Moderate temperature variance: {temp_variance:.1f}°F')
        
        # Air quality analysis
        elif sensor_type == 'air_quality':
            if value > 100:  # Poor air quality
                failure_probability += 0.25
                trigger_factors.append(f'Poor air quality detected: AQI {value}')
            elif value > 75:
                failure_probability += 0.1
                trigger_factors.append(f'Degraded air quality: AQI {value}')
        
        # Energy consumption analysis
        elif sensor_type == 'energy':
            baseline_consumption = 2.5  # kWh baseline
            if value > baseline_consumption * 1.5:
                failure_probability += 0.35
                trigger_factors.append(f'High energy consumption: {value:.2f} kWh')
            elif value > baseline_consumption * 1.2:
                failure_probability += 0.15
                trigger_factors.append(f'Elevated energy usage: {value:.2f} kWh')
        
        # Only create prediction if significant risk
        if failure_probability > 0.1:
            # Calculate days until predicted failure
            days_until_failure = max(7, int(30 * (1 - failure_probability)))
            predicted_date = datetime.now() + timedelta(days=days_until_failure)
            
            # Determine priority
            if failure_probability > 0.5:
                priority = PriorityLevel.CRITICAL
            elif failure_probability > 0.3:
                priority = PriorityLevel.HIGH
            else:
                priority = PriorityLevel.MEDIUM
            
            # Estimate cost
            base_cost = 500
            cost_multiplier = 1 + failure_probability
            estimated_cost = base_cost * cost_multiplier
            
            return MaintenancePrediction(
                prediction_id=f"hvac_{property_id}_{location}_{int(time.time())}",
                equipment_id=f"hvac_unit_{location}",
                equipment_type="HVAC System",
                maintenance_type=MaintenanceType.HVAC,
                failure_probability=round(failure_probability, 3),
                predicted_failure_date=predicted_date,
                confidence_score=min(0.95, 0.6 + failure_probability * 0.3),
                priority_level=priority,
                estimated_cost=round(estimated_cost, 2),
                recommended_action=self._get_hvac_recommendation(failure_probability, trigger_factors),
                trigger_factors=trigger_factors,
                property_id=property_id,
                location=location,
                created_at=datetime.now(),
                iot_trigger_data=sensor_data
            )
        
        return None
    
    def _predict_electrical_maintenance(self, sensor_data: Dict, property_id: str, location: str) -> Optional[MaintenancePrediction]:
        """Predict electrical maintenance needs"""
        sensor_type = sensor_data.get('sensor_type')
        value = sensor_data.get('value', 0)
        
        failure_probability = 0.0
        trigger_factors = []
        
        if sensor_type == 'energy':
            # Analyze power consumption patterns
            baseline_consumption = 2.0
            
            # High consumption indicates potential electrical issues
            if value > baseline_consumption * 2:
                failure_probability += 0.4
                trigger_factors.append(f'Excessive power draw: {value:.2f} kWh')
            elif value > baseline_consumption * 1.5:
                failure_probability += 0.2
                trigger_factors.append(f'High power consumption: {value:.2f} kWh')
            
            # Very low consumption might indicate failing components
            elif value < baseline_consumption * 0.3:
                failure_probability += 0.3
                trigger_factors.append(f'Unusually low power consumption: {value:.2f} kWh')
        
        if failure_probability > 0.15:
            days_until_failure = max(14, int(45 * (1 - failure_probability)))
            predicted_date = datetime.now() + timedelta(days=days_until_failure)
            
            priority = PriorityLevel.HIGH if failure_probability > 0.3 else PriorityLevel.MEDIUM
            estimated_cost = 300 * (1 + failure_probability)
            
            return MaintenancePrediction(
                prediction_id=f"electrical_{property_id}_{location}_{int(time.time())}",
                equipment_id=f"electrical_system_{location}",
                equipment_type="Electrical System",
                maintenance_type=MaintenanceType.ELECTRICAL,
                failure_probability=round(failure_probability, 3),
                predicted_failure_date=predicted_date,
                confidence_score=min(0.9, 0.5 + failure_probability * 0.4),
                priority_level=priority,
                estimated_cost=round(estimated_cost, 2),
                recommended_action=self._get_electrical_recommendation(failure_probability, trigger_factors),
                trigger_factors=trigger_factors,
                property_id=property_id,
                location=location,
                created_at=datetime.now(),
                iot_trigger_data=sensor_data
            )
        
        return None
    
    def _predict_plumbing_maintenance(self, sensor_data: Dict, property_id: str, location: str) -> Optional[MaintenancePrediction]:
        """Predict plumbing maintenance needs"""
        sensor_type = sensor_data.get('sensor_type')
        value = sensor_data.get('value', 0)
        
        failure_probability = 0.0
        trigger_factors = []
        
        if sensor_type == 'water':
            # Analyze water flow patterns
            if value > 3:  # High flow rate
                failure_probability += 0.25
                trigger_factors.append(f'High water flow detected: {value} GPM')
            elif value > 0.5 and 'bathroom' not in location.lower():
                # Unexpected water flow in non-bathroom areas
                failure_probability += 0.4
                trigger_factors.append(f'Unexpected water flow in {location}: {value} GPM')
        
        elif sensor_type == 'humidity':
            # High humidity might indicate leaks
            if value > 70 and 'bathroom' not in location.lower():
                failure_probability += 0.3
                trigger_factors.append(f'High humidity in {location}: {value}%')
            elif value > 80:
                failure_probability += 0.2
                trigger_factors.append(f'Very high humidity: {value}%')
        
        if failure_probability > 0.1:
            days_until_failure = max(3, int(21 * (1 - failure_probability)))
            predicted_date = datetime.now() + timedelta(days=days_until_failure)
            
            if failure_probability > 0.3:
                priority = PriorityLevel.CRITICAL
            elif failure_probability > 0.2:
                priority = PriorityLevel.HIGH
            else:
                priority = PriorityLevel.MEDIUM
            
            estimated_cost = 200 * (1 + failure_probability * 2)
            
            return MaintenancePrediction(
                prediction_id=f"plumbing_{property_id}_{location}_{int(time.time())}",
                equipment_id=f"plumbing_system_{location}",
                equipment_type="Plumbing System",
                maintenance_type=MaintenanceType.PLUMBING,
                failure_probability=round(failure_probability, 3),
                predicted_failure_date=predicted_date,
                confidence_score=min(0.85, 0.4 + failure_probability * 0.5),
                priority_level=priority,
                estimated_cost=round(estimated_cost, 2),
                recommended_action=self._get_plumbing_recommendation(failure_probability, trigger_factors),
                trigger_factors=trigger_factors,
                property_id=property_id,
                location=location,
                created_at=datetime.now(),
                iot_trigger_data=sensor_data
            )
        
        return None
    
    def _analyze_system_correlations(self, iot_data: Dict, property_id: str) -> List[MaintenancePrediction]:
        """Analyze correlations between multiple sensors for system-level predictions"""
        predictions = []
        
        # Group sensors by location
        sensors_by_location = {}
        for sensor in iot_data.get('sensor_readings', []):
            location = sensor.get('location', 'Unknown')
            if location not in sensors_by_location:
                sensors_by_location[location] = []
            sensors_by_location[location].append(sensor)
        
        # Analyze each location for system-level issues
        for location, sensors in sensors_by_location.items():
            system_prediction = self._analyze_location_systems(sensors, property_id, location)
            if system_prediction:
                predictions.extend(system_prediction)
        
        return predictions
    
    def _analyze_location_systems(self, sensors: List[Dict], property_id: str, location: str) -> List[MaintenancePrediction]:
        """Analyze multiple sensors in a location for system-level issues"""
        predictions = []
        
        # Create sensor data lookup
        sensor_data = {}
        for sensor in sensors:
            sensor_data[sensor.get('sensor_type')] = sensor.get('value', 0)
        
        # Multi-system analysis
        if 'temperature' in sensor_data and 'humidity' in sensor_data and 'energy' in sensor_data:
            # Comprehensive HVAC system analysis
            temp = sensor_data['temperature']
            humidity = sensor_data['humidity']
            energy = sensor_data['energy']
            
            # Calculate system efficiency score
            temp_efficiency = 1.0 - abs(temp - 72) / 20  # Ideal temp 72°F
            humidity_efficiency = 1.0 - abs(humidity - 45) / 35  # Ideal humidity 45%
            energy_efficiency = max(0, 1.0 - max(0, energy - 2.5) / 2.5)  # Baseline 2.5 kWh
            
            overall_efficiency = (temp_efficiency + humidity_efficiency + energy_efficiency) / 3
            
            if overall_efficiency < 0.6:
                failure_probability = 0.7 - overall_efficiency
                
                prediction = MaintenancePrediction(
                    prediction_id=f"system_hvac_{property_id}_{location}_{int(time.time())}",
                    equipment_id=f"hvac_system_{location}",
                    equipment_type="HVAC System (Multi-sensor)",
                    maintenance_type=MaintenanceType.HVAC,
                    failure_probability=round(failure_probability, 3),
                    predicted_failure_date=datetime.now() + timedelta(days=int(14 * (1 - failure_probability))),
                    confidence_score=0.85,
                    priority_level=PriorityLevel.HIGH if failure_probability > 0.3 else PriorityLevel.MEDIUM,
                    estimated_cost=round(750 * (1 + failure_probability), 2),
                    recommended_action="Comprehensive HVAC system inspection and tuning required",
                    trigger_factors=[
                        f"System efficiency at {overall_efficiency:.1%}",
                        f"Temperature: {temp}°F, Humidity: {humidity}%, Energy: {energy} kWh"
                    ],
                    property_id=property_id,
                    location=location,
                    created_at=datetime.now(),
                    iot_trigger_data={'multi_sensor_analysis': sensor_data}
                )
                predictions.append(prediction)
        
        return predictions
    
    def _filter_and_prioritize_predictions(self, predictions: List[MaintenancePrediction]) -> List[MaintenancePrediction]:
        """Filter duplicate predictions and prioritize by risk"""
        # Remove duplicates based on equipment_id and maintenance_type
        unique_predictions = {}
        for pred in predictions:
            key = f"{pred.equipment_id}_{pred.maintenance_type.value}"
            if key not in unique_predictions or pred.failure_probability > unique_predictions[key].failure_probability:
                unique_predictions[key] = pred
        
        # Sort by priority and failure probability
        sorted_predictions = sorted(
            unique_predictions.values(),
            key=lambda x: (x.priority_level.value, -x.failure_probability)
        )
        
        return sorted_predictions
    
    def create_maintenance_tasks(self, predictions: List[MaintenancePrediction]) -> List[MaintenanceTask]:
        """Convert predictions into actionable maintenance tasks"""
        tasks = []
        
        for prediction in predictions:
            # Determine task scheduling based on priority and failure probability
            if prediction.priority_level == PriorityLevel.CRITICAL:
                scheduled_date = datetime.now() + timedelta(hours=24)
            elif prediction.priority_level == PriorityLevel.HIGH:
                scheduled_date = datetime.now() + timedelta(days=3)
            else:
                scheduled_date = prediction.predicted_failure_date - timedelta(days=7)
            
            task = MaintenanceTask(
                task_id=f"task_{prediction.prediction_id}",
                prediction_id=prediction.prediction_id,
                equipment_id=prediction.equipment_id,
                task_type=self._get_task_type(prediction),
                description=self._generate_task_description(prediction),
                priority=prediction.priority_level,
                estimated_duration=self._estimate_task_duration(prediction),
                estimated_cost=prediction.estimated_cost,
                required_skills=self._get_required_skills(prediction),
                required_parts=self._get_required_parts(prediction),
                scheduled_date=scheduled_date,
                property_id=prediction.property_id,
                location=prediction.location
            )
            tasks.append(task)
        
        return tasks
    
    def _get_hvac_recommendation(self, probability: float, factors: List[str]) -> str:
        """Get HVAC-specific maintenance recommendation"""
        if probability > 0.5:
            return "URGENT: Schedule immediate HVAC system inspection and repair"
        elif probability > 0.3:
            return "Schedule comprehensive HVAC maintenance within 3 days"
        else:
            return "Monitor HVAC system and schedule preventive maintenance"
    
    def _get_electrical_recommendation(self, probability: float, factors: List[str]) -> str:
        """Get electrical-specific maintenance recommendation"""
        if probability > 0.3:
            return "Schedule electrical system inspection by licensed electrician"
        else:
            return "Monitor electrical consumption and schedule routine inspection"
    
    def _get_plumbing_recommendation(self, probability: float, factors: List[str]) -> str:
        """Get plumbing-specific maintenance recommendation"""
        if probability > 0.3:
            return "URGENT: Inspect for water leaks and plumbing issues immediately"
        else:
            return "Schedule plumbing inspection and preventive maintenance"
    
    def _get_task_type(self, prediction: MaintenancePrediction) -> str:
        """Determine the type of maintenance task"""
        if prediction.failure_probability > 0.5:
            return "Emergency Repair"
        elif prediction.failure_probability > 0.3:
            return "Urgent Maintenance"
        else:
            return "Preventive Maintenance"
    
    def _generate_task_description(self, prediction: MaintenancePrediction) -> str:
        """Generate detailed task description"""
        base_desc = f"{prediction.equipment_type} maintenance in {prediction.location}"
        factors_desc = ". Triggered by: " + ", ".join(prediction.trigger_factors)
        action_desc = f". Action required: {prediction.recommended_action}"
        
        return base_desc + factors_desc + action_desc
    
    def _estimate_task_duration(self, prediction: MaintenancePrediction) -> timedelta:
        """Estimate task duration based on complexity"""
        base_hours = {
            MaintenanceType.HVAC: 4,
            MaintenanceType.ELECTRICAL: 3,
            MaintenanceType.PLUMBING: 2,
            MaintenanceType.STRUCTURAL: 8,
            MaintenanceType.APPLIANCES: 2
        }.get(prediction.maintenance_type, 3)
        
        # Adjust based on failure probability (higher probability = more complex repair)
        complexity_multiplier = 1 + prediction.failure_probability
        estimated_hours = base_hours * complexity_multiplier
        
        return timedelta(hours=estimated_hours)
    
    def _get_required_skills(self, prediction: MaintenancePrediction) -> List[str]:
        """Get required skills for the maintenance task"""
        skill_map = {
            MaintenanceType.HVAC: ["HVAC Technician", "Electrical Knowledge"],
            MaintenanceType.ELECTRICAL: ["Licensed Electrician", "Safety Certification"],
            MaintenanceType.PLUMBING: ["Licensed Plumber", "Pipe Fitting"],
            MaintenanceType.STRUCTURAL: ["General Contractor", "Structural Assessment"],
            MaintenanceType.APPLIANCES: ["Appliance Repair", "General Maintenance"]
        }
        
        return skill_map.get(prediction.maintenance_type, ["General Maintenance"])
    
    def _get_required_parts(self, prediction: MaintenancePrediction) -> List[str]:
        """Get likely required parts/materials"""
        parts_map = {
            MaintenanceType.HVAC: ["Air filter", "Refrigerant", "Electrical components"],
            MaintenanceType.ELECTRICAL: ["Wiring", "Circuit breakers", "Electrical connectors"],
            MaintenanceType.PLUMBING: ["Pipes", "Fittings", "Seals", "Valves"],
            MaintenanceType.STRUCTURAL: ["Building materials", "Fasteners"],
            MaintenanceType.APPLIANCES: ["Replacement parts", "Seals", "Filters"]
        }
        
        return parts_map.get(prediction.maintenance_type, ["General maintenance supplies"])

def serialize_prediction(prediction: MaintenancePrediction) -> Dict:
    """Convert MaintenancePrediction to JSON-serializable dict"""
    result = asdict(prediction)
    result['maintenance_type'] = prediction.maintenance_type.value
    result['priority_level'] = prediction.priority_level.value
    result['predicted_failure_date'] = prediction.predicted_failure_date.isoformat()
    result['created_at'] = prediction.created_at.isoformat()
    return result

def serialize_task(task: MaintenanceTask) -> Dict:
    """Convert MaintenanceTask to JSON-serializable dict"""
    result = asdict(task)
    result['priority'] = task.priority.value
    result['estimated_duration'] = task.estimated_duration.total_seconds() / 3600  # Convert to hours
    result['scheduled_date'] = task.scheduled_date.isoformat()
    return result

def generate_maintenance_dashboard_data(predictions: List[MaintenancePrediction], tasks: List[MaintenanceTask]) -> Dict:
    """Generate dashboard data for predictive maintenance"""
    
    # Calculate summary statistics
    total_predictions = len(predictions)
    critical_predictions = len([p for p in predictions if p.priority_level == PriorityLevel.CRITICAL])
    high_priority_predictions = len([p for p in predictions if p.priority_level == PriorityLevel.HIGH])
    
    total_estimated_cost = sum(p.estimated_cost for p in predictions)
    avg_failure_probability = np.mean([p.failure_probability for p in predictions]) if predictions else 0
    
    # Equipment type breakdown
    equipment_breakdown = {}
    for pred in predictions:
        equipment_type = pred.maintenance_type.value
        if equipment_type not in equipment_breakdown:
            equipment_breakdown[equipment_type] = {
                'count': 0,
                'total_cost': 0,
                'avg_probability': 0,
                'critical_count': 0
            }
        
        equipment_breakdown[equipment_type]['count'] += 1
        equipment_breakdown[equipment_type]['total_cost'] += pred.estimated_cost
        equipment_breakdown[equipment_type]['avg_probability'] += pred.failure_probability
        if pred.priority_level == PriorityLevel.CRITICAL:
            equipment_breakdown[equipment_type]['critical_count'] += 1
    
    # Calculate averages
    for equipment_type in equipment_breakdown:
        count = equipment_breakdown[equipment_type]['count']
        equipment_breakdown[equipment_type]['avg_probability'] = round(
            equipment_breakdown[equipment_type]['avg_probability'] / count, 3
        )
        equipment_breakdown[equipment_type]['avg_cost'] = round(
            equipment_breakdown[equipment_type]['total_cost'] / count, 2
        )
    
    # Task summary
    pending_tasks = len([t for t in tasks if t.status == "pending"])
    urgent_tasks = len([t for t in tasks if t.priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]])
    
    # Generate recommendations
    recommendations = []
    if critical_predictions > 0:
        recommendations.append(f"URGENT: {critical_predictions} critical maintenance issues require immediate attention")
    if high_priority_predictions > 3:
        recommendations.append(f"High maintenance workload detected: {high_priority_predictions} high-priority items")
    if total_estimated_cost > 5000:
        recommendations.append(f"Significant maintenance costs projected: ${total_estimated_cost:,.2f}")
    if avg_failure_probability > 0.3:
        recommendations.append("Multiple systems showing signs of wear - consider preventive maintenance program")
    
    return {
        'summary': {
            'total_predictions': total_predictions,
            'critical_predictions': critical_predictions,
            'high_priority_predictions': high_priority_predictions,
            'total_estimated_cost': round(total_estimated_cost, 2),
            'avg_failure_probability': round(float(avg_failure_probability), 3),
            'pending_tasks': pending_tasks,
            'urgent_tasks': urgent_tasks
        },
        'equipment_breakdown': equipment_breakdown,
        'predictions': [serialize_prediction(p) for p in predictions],
        'tasks': [serialize_task(t) for t in tasks],
        'recommendations': recommendations,
        'dashboard_updated': datetime.now().isoformat()
    }