import numpy as np
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import random

class OptimizationStrategy(Enum):
    PEAK_SHAVING = "peak_shaving"
    LOAD_BALANCING = "load_balancing"
    DEMAND_RESPONSE = "demand_response"
    ENERGY_EFFICIENCY = "energy_efficiency"
    RENEWABLE_INTEGRATION = "renewable_integration"
    TIME_OF_USE = "time_of_use"

class EquipmentType(Enum):
    HVAC = "hvac"
    LIGHTING = "lighting"
    WATER_HEATER = "water_heater"
    APPLIANCES = "appliances"
    ELEVATOR = "elevator"
    SECURITY = "security"
    PUMPS = "pumps"

@dataclass
class EnergyUsagePattern:
    equipment_id: str
    equipment_type: EquipmentType
    hourly_consumption: List[float]  # 24 hours
    peak_hours: List[int]
    off_peak_hours: List[int]
    average_daily_consumption: float
    efficiency_rating: float
    controllable: bool
    property_id: str
    location: str

@dataclass
class OptimizationRecommendation:
    recommendation_id: str
    strategy: OptimizationStrategy
    equipment_id: str
    equipment_type: str
    description: str
    estimated_savings: float
    implementation_cost: float
    payback_period_months: int
    difficulty: str  # easy, medium, hard
    priority_score: float
    annual_kwh_savings: float
    co2_reduction_tons: float
    property_id: str
    location: str
    created_at: datetime

@dataclass
class SmartSchedule:
    schedule_id: str
    equipment_id: str
    equipment_type: str
    schedule_type: str  # time_based, occupancy_based, weather_based
    schedule_data: Dict[str, Any]
    estimated_savings: float
    active: bool
    property_id: str
    created_at: datetime

class EnergyOptimizationEngine:
    """
    Advanced energy optimization system using IoT data and machine learning
    """
    
    def __init__(self):
        self.usage_patterns = {}
        self.optimization_history = []
        self.smart_schedules = {}
        self.utility_rates = self._initialize_utility_rates()
        self.weather_data = {}
        self.occupancy_patterns = {}
    
    def _initialize_utility_rates(self) -> Dict:
        """Initialize utility rate structures"""
        return {
            'time_of_use': {
                'peak': {'hours': [16, 17, 18, 19, 20, 21], 'rate': 0.28},  # $0.28/kWh
                'mid_peak': {'hours': [14, 15, 22], 'rate': 0.18},  # $0.18/kWh
                'off_peak': {'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 23], 'rate': 0.12}  # $0.12/kWh
            },
            'demand_charges': 15.50,  # $/kW for peak demand
            'base_rate': 0.15,  # $/kWh flat rate
            'renewable_credit': 0.03  # $/kWh credit for renewable usage
        }
    
    def analyze_energy_usage(self, iot_data: Dict, property_id: str) -> Dict:
        """
        Analyze energy usage patterns from IoT sensor data
        """
        usage_analysis = {}
        
        # Process energy sensor data
        for sensor_data in iot_data.get('sensor_readings', []):
            if sensor_data.get('sensor_type') == 'energy':
                equipment_analysis = self._analyze_equipment_usage(sensor_data, property_id)
                if equipment_analysis:
                    usage_analysis[equipment_analysis['equipment_id']] = equipment_analysis
        
        # Correlate with occupancy and environmental data
        correlation_analysis = self._analyze_usage_correlations(iot_data, usage_analysis, property_id)
        
        # Generate energy patterns
        energy_patterns = self._generate_energy_patterns(usage_analysis, property_id)
        
        return {
            'usage_analysis': usage_analysis,
            'correlation_analysis': correlation_analysis,
            'energy_patterns': energy_patterns,
            'total_consumption': sum(pattern.average_daily_consumption for pattern in energy_patterns.values()),
            'efficiency_score': self._calculate_efficiency_score(energy_patterns),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_equipment_usage(self, sensor_data: Dict, property_id: str) -> Optional[Dict]:
        """Analyze individual equipment energy usage"""
        location = sensor_data.get('location', 'Unknown')
        value = sensor_data.get('value', 0)
        timestamp = datetime.fromisoformat(sensor_data.get('timestamp', datetime.now().isoformat()))
        
        # Determine equipment type based on location and consumption pattern
        equipment_type = self._infer_equipment_type(location, value)
        equipment_id = f"{equipment_type.value}_{location.replace(' ', '_')}"
        
        # Simulate 24-hour consumption pattern
        hourly_pattern = self._generate_hourly_pattern(equipment_type, value, timestamp.hour)
        
        # Calculate efficiency metrics
        efficiency_score = self._calculate_equipment_efficiency(equipment_type, value, hourly_pattern)
        
        # Identify peak and off-peak hours
        peak_hours, off_peak_hours = self._identify_peak_hours(hourly_pattern)
        
        return {
            'equipment_id': equipment_id,
            'equipment_type': equipment_type.value,
            'current_consumption': value,
            'hourly_pattern': hourly_pattern,
            'daily_consumption': sum(hourly_pattern),
            'peak_hours': peak_hours,
            'off_peak_hours': off_peak_hours,
            'efficiency_score': efficiency_score,
            'controllable': self._is_controllable(equipment_type),
            'location': location,
            'optimization_potential': self._calculate_optimization_potential(equipment_type, efficiency_score, hourly_pattern)
        }
    
    def _infer_equipment_type(self, location: str, consumption: float) -> EquipmentType:
        """Infer equipment type from location and consumption"""
        location_lower = location.lower()
        
        if 'hvac' in location_lower or 'air' in location_lower:
            return EquipmentType.HVAC
        elif 'panel' in location_lower and consumption > 3.0:
            return EquipmentType.HVAC  # High consumption at main panel likely HVAC
        elif 'water' in location_lower or 'heater' in location_lower:
            return EquipmentType.WATER_HEATER
        elif 'light' in location_lower or consumption < 0.5:
            return EquipmentType.LIGHTING
        elif 'elevator' in location_lower:
            return EquipmentType.ELEVATOR
        elif 'pump' in location_lower:
            return EquipmentType.PUMPS
        else:
            return EquipmentType.APPLIANCES
    
    def _generate_hourly_pattern(self, equipment_type: EquipmentType, current_value: float, current_hour: int) -> List[float]:
        """Generate 24-hour consumption pattern for equipment"""
        base_pattern = [0.0] * 24
        
        if equipment_type == EquipmentType.HVAC:
            # HVAC: Higher during day and evening, lower at night
            for hour in range(24):
                if 6 <= hour <= 8:  # Morning startup
                    base_pattern[hour] = current_value * 1.2
                elif 9 <= hour <= 17:  # Daytime
                    base_pattern[hour] = current_value * 1.0
                elif 18 <= hour <= 22:  # Evening
                    base_pattern[hour] = current_value * 1.1
                else:  # Night
                    base_pattern[hour] = current_value * 0.6
        
        elif equipment_type == EquipmentType.LIGHTING:
            # Lighting: Peak during evening, minimal during day and night
            for hour in range(24):
                if 6 <= hour <= 8:  # Morning
                    base_pattern[hour] = current_value * 0.8
                elif 9 <= hour <= 17:  # Daytime (natural light)
                    base_pattern[hour] = current_value * 0.3
                elif 18 <= hour <= 23:  # Evening
                    base_pattern[hour] = current_value * 1.2
                else:  # Night
                    base_pattern[hour] = current_value * 0.1
        
        elif equipment_type == EquipmentType.WATER_HEATER:
            # Water heater: Peaks during morning and evening usage
            for hour in range(24):
                if hour in [6, 7, 8, 19, 20, 21]:  # Peak usage times
                    base_pattern[hour] = current_value * 1.5
                elif hour in [9, 10, 18, 22]:  # Moderate usage
                    base_pattern[hour] = current_value * 0.8
                else:  # Standby
                    base_pattern[hour] = current_value * 0.4
        
        elif equipment_type == EquipmentType.APPLIANCES:
            # Appliances: Varied usage throughout the day
            for hour in range(24):
                if 7 <= hour <= 10:  # Morning
                    base_pattern[hour] = current_value * 1.1
                elif 12 <= hour <= 14:  # Lunch
                    base_pattern[hour] = current_value * 0.9
                elif 17 <= hour <= 21:  # Evening
                    base_pattern[hour] = current_value * 1.3
                else:
                    base_pattern[hour] = current_value * 0.5
        
        else:
            # Default pattern: Relatively constant with slight daytime increase
            for hour in range(24):
                if 8 <= hour <= 18:
                    base_pattern[hour] = current_value * 1.1
                else:
                    base_pattern[hour] = current_value * 0.9
        
        # Add some random variation
        for i in range(24):
            variation = random.uniform(0.9, 1.1)
            base_pattern[i] *= variation
            base_pattern[i] = round(base_pattern[i], 2)
        
        return base_pattern
    
    def _calculate_equipment_efficiency(self, equipment_type: EquipmentType, current_consumption: float, hourly_pattern: List[float]) -> float:
        """Calculate equipment efficiency score (0-100)"""
        # Baseline consumption expectations by equipment type
        baselines = {
            EquipmentType.HVAC: 3.0,
            EquipmentType.LIGHTING: 0.5,
            EquipmentType.WATER_HEATER: 2.0,
            EquipmentType.APPLIANCES: 1.5,
            EquipmentType.ELEVATOR: 5.0,
            EquipmentType.PUMPS: 2.5,
            EquipmentType.SECURITY: 0.3
        }
        
        baseline = baselines.get(equipment_type, 2.0)
        daily_consumption = sum(hourly_pattern)
        baseline_daily = baseline * 24
        
        # Calculate efficiency (lower consumption = higher efficiency)
        if daily_consumption <= baseline_daily:
            efficiency = 100
        else:
            excess = (daily_consumption - baseline_daily) / baseline_daily
            efficiency = max(0, 100 - (excess * 50))  # Penalty for excess consumption
        
        return round(efficiency, 1)
    
    def _identify_peak_hours(self, hourly_pattern: List[float]) -> Tuple[List[int], List[int]]:
        """Identify peak and off-peak consumption hours"""
        avg_consumption = np.mean(hourly_pattern)
        peak_threshold = avg_consumption * 1.2
        off_peak_threshold = avg_consumption * 0.8
        
        peak_hours = [hour for hour, consumption in enumerate(hourly_pattern) if consumption >= peak_threshold]
        off_peak_hours = [hour for hour, consumption in enumerate(hourly_pattern) if consumption <= off_peak_threshold]
        
        return peak_hours, off_peak_hours
    
    def _is_controllable(self, equipment_type: EquipmentType) -> bool:
        """Determine if equipment can be controlled/scheduled"""
        controllable_types = {
            EquipmentType.HVAC: True,
            EquipmentType.LIGHTING: True,
            EquipmentType.WATER_HEATER: True,
            EquipmentType.PUMPS: True,
            EquipmentType.APPLIANCES: False,  # Most appliances are manually operated
            EquipmentType.ELEVATOR: False,   # Safety critical
            EquipmentType.SECURITY: False    # Safety critical
        }
        return controllable_types.get(equipment_type, False)
    
    def _calculate_optimization_potential(self, equipment_type: EquipmentType, efficiency_score: float, hourly_pattern: List[float]) -> float:
        """Calculate optimization potential (0-100)"""
        # Base potential inversely related to efficiency
        base_potential = (100 - efficiency_score) * 0.6
        
        # Add potential based on peak/off-peak distribution
        daily_consumption = sum(hourly_pattern)
        if daily_consumption > 0:
            peak_consumption = sum(hourly_pattern[16:22])  # Peak hours 4-10 PM
            peak_ratio = peak_consumption / daily_consumption
            
            # Higher peak ratio = more optimization potential
            distribution_potential = peak_ratio * 40
        else:
            distribution_potential = 0
        
        # Equipment-specific multipliers
        equipment_multipliers = {
            EquipmentType.HVAC: 1.2,
            EquipmentType.LIGHTING: 1.1,
            EquipmentType.WATER_HEATER: 1.3,
            EquipmentType.APPLIANCES: 0.8,
            EquipmentType.PUMPS: 1.0
        }
        
        multiplier = equipment_multipliers.get(equipment_type, 1.0)
        total_potential = (base_potential + distribution_potential) * multiplier
        
        return min(100, round(total_potential, 1))
    
    def _analyze_usage_correlations(self, iot_data: Dict, usage_analysis: Dict, property_id: str) -> Dict:
        """Analyze correlations between energy usage and other factors"""
        correlations = {}
        
        # Temperature correlation
        temp_sensors = [s for s in iot_data.get('sensor_readings', []) if s.get('sensor_type') == 'temperature']
        if temp_sensors:
            avg_temp = np.mean([s.get('value', 72) for s in temp_sensors])
            temp_impact = self._calculate_temperature_impact(avg_temp, usage_analysis)
            correlations['temperature'] = {
                'average_temp': round(avg_temp, 1),
                'impact_on_consumption': temp_impact,
                'optimization_opportunity': 'high' if abs(avg_temp - 72) > 5 else 'medium'
            }
        
        # Occupancy correlation
        occupancy_sensors = [s for s in iot_data.get('sensor_readings', []) if s.get('sensor_type') == 'occupancy']
        if occupancy_sensors:
            avg_occupancy = np.mean([s.get('value', 0) for s in occupancy_sensors])
            occupancy_impact = avg_occupancy * 0.3  # 30% consumption increase per occupied space
            correlations['occupancy'] = {
                'average_occupancy': round(avg_occupancy, 2),
                'impact_on_consumption': round(occupancy_impact, 2),
                'optimization_opportunity': 'high' if avg_occupancy > 0.7 else 'medium'
            }
        
        return correlations
    
    def _calculate_temperature_impact(self, temperature: float, usage_analysis: Dict) -> float:
        """Calculate temperature impact on energy consumption"""
        ideal_temp = 72
        temp_deviation = abs(temperature - ideal_temp)
        
        # Each degree from ideal increases consumption by ~8%
        impact_percentage = temp_deviation * 0.08
        
        # Find HVAC consumption
        hvac_consumption = 0
        for equipment_id, data in usage_analysis.items():
            if data.get('equipment_type') == 'hvac':
                hvac_consumption += data.get('daily_consumption', 0)
        
        impact_kwh = hvac_consumption * impact_percentage
        return round(impact_kwh, 2)
    
    def _generate_energy_patterns(self, usage_analysis: Dict, property_id: str) -> Dict[str, EnergyUsagePattern]:
        """Generate energy usage patterns for optimization"""
        patterns = {}
        
        for equipment_id, data in usage_analysis.items():
            pattern = EnergyUsagePattern(
                equipment_id=equipment_id,
                equipment_type=EquipmentType(data['equipment_type']),
                hourly_consumption=data['hourly_pattern'],
                peak_hours=data['peak_hours'],
                off_peak_hours=data['off_peak_hours'],
                average_daily_consumption=data['daily_consumption'],
                efficiency_rating=data['efficiency_score'],
                controllable=data['controllable'],
                property_id=property_id,
                location=data['location']
            )
            patterns[equipment_id] = pattern
        
        return patterns
    
    def _calculate_efficiency_score(self, energy_patterns: Dict) -> float:
        """Calculate overall property efficiency score"""
        if not energy_patterns:
            return 0.0
        
        total_weighted_score = 0
        total_consumption = 0
        
        for pattern in energy_patterns.values():
            consumption = pattern.average_daily_consumption
            efficiency = pattern.efficiency_rating
            
            total_weighted_score += efficiency * consumption
            total_consumption += consumption
        
        if total_consumption == 0:
            return 0.0
        
        overall_efficiency = total_weighted_score / total_consumption
        return round(overall_efficiency, 1)
    
    def generate_optimization_recommendations(self, energy_analysis: Dict, property_id: str) -> List[OptimizationRecommendation]:
        """Generate energy optimization recommendations"""
        recommendations = []
        
        usage_analysis = energy_analysis.get('usage_analysis', {})
        energy_patterns = energy_analysis.get('energy_patterns', {})
        
        # Generate recommendations for each equipment
        for equipment_id, data in usage_analysis.items():
            equipment_recs = self._generate_equipment_recommendations(equipment_id, data, property_id)
            recommendations.extend(equipment_recs)
        
        # Generate system-level recommendations
        system_recs = self._generate_system_recommendations(energy_analysis, property_id)
        recommendations.extend(system_recs)
        
        # Sort by priority score
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)
        
        return recommendations
    
    def _generate_equipment_recommendations(self, equipment_id: str, data: Dict, property_id: str) -> List[OptimizationRecommendation]:
        """Generate recommendations for specific equipment"""
        recommendations = []
        equipment_type = data.get('equipment_type', 'appliances')
        efficiency_score = data.get('efficiency_score', 75)
        optimization_potential = data.get('optimization_potential', 0)
        daily_consumption = data.get('daily_consumption', 0)
        
        if optimization_potential > 30:  # Significant optimization potential
            if equipment_type == 'hvac':
                recommendations.extend(self._generate_hvac_recommendations(equipment_id, data, property_id))
            elif equipment_type == 'lighting':
                recommendations.extend(self._generate_lighting_recommendations(equipment_id, data, property_id))
            elif equipment_type == 'water_heater':
                recommendations.extend(self._generate_water_heater_recommendations(equipment_id, data, property_id))
            elif equipment_type == 'appliances':
                recommendations.extend(self._generate_appliance_recommendations(equipment_id, data, property_id))
        
        return recommendations
    
    def _generate_hvac_recommendations(self, equipment_id: str, data: Dict, property_id: str) -> List[OptimizationRecommendation]:
        """Generate HVAC-specific optimization recommendations"""
        recommendations = []
        daily_consumption = data.get('daily_consumption', 0)
        efficiency_score = data.get('efficiency_score', 75)
        location = data.get('location', 'Unknown')
        
        # Smart thermostat recommendation
        if efficiency_score < 80:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"hvac_smart_thermostat_{equipment_id}_{int(time.time())}",
                strategy=OptimizationStrategy.ENERGY_EFFICIENCY,
                equipment_id=equipment_id,
                equipment_type='HVAC System',
                description=f"Install smart thermostat for {location} HVAC system with occupancy sensing and scheduling",
                estimated_savings=daily_consumption * 365 * 0.15 * 0.15,  # 15% savings at $0.15/kWh
                implementation_cost=250.0,
                payback_period_months=int((250.0 / (daily_consumption * 365 * 0.15 * 0.15)) * 12),
                difficulty='easy',
                priority_score=85.0,
                annual_kwh_savings=daily_consumption * 365 * 0.15,
                co2_reduction_tons=daily_consumption * 365 * 0.15 * 0.0004,  # 0.4 kg CO2/kWh
                property_id=property_id,
                location=location,
                created_at=datetime.now()
            ))
        
        # Time-of-use optimization
        peak_hours = data.get('peak_hours', [])
        if len(set(peak_hours) & set([16, 17, 18, 19, 20, 21])) > 2:  # Peak overlaps with utility peak
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"hvac_tou_optimization_{equipment_id}_{int(time.time())}",
                strategy=OptimizationStrategy.TIME_OF_USE,
                equipment_id=equipment_id,
                equipment_type='HVAC System',
                description=f"Implement time-of-use optimization to pre-cool/pre-heat {location} during off-peak hours",
                estimated_savings=daily_consumption * 365 * 0.12 * 0.08,  # 12% consumption shift, 8¢ savings/kWh
                implementation_cost=150.0,
                payback_period_months=int((150.0 / (daily_consumption * 365 * 0.12 * 0.08)) * 12),
                difficulty='medium',
                priority_score=75.0,
                annual_kwh_savings=0,  # Same consumption, just shifted
                co2_reduction_tons=0,
                property_id=property_id,
                location=location,
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _generate_lighting_recommendations(self, equipment_id: str, data: Dict, property_id: str) -> List[OptimizationRecommendation]:
        """Generate lighting-specific optimization recommendations"""
        recommendations = []
        daily_consumption = data.get('daily_consumption', 0)
        location = data.get('location', 'Unknown')
        
        # LED upgrade recommendation
        recommendations.append(OptimizationRecommendation(
            recommendation_id=f"lighting_led_upgrade_{equipment_id}_{int(time.time())}",
            strategy=OptimizationStrategy.ENERGY_EFFICIENCY,
            equipment_id=equipment_id,
            equipment_type='Lighting System',
            description=f"Upgrade {location} lighting to LED with occupancy sensors and dimming controls",
            estimated_savings=daily_consumption * 365 * 0.40 * 0.15,  # 40% energy savings
            implementation_cost=300.0,
            payback_period_months=int((300.0 / (daily_consumption * 365 * 0.40 * 0.15)) * 12),
            difficulty='easy',
            priority_score=80.0,
            annual_kwh_savings=daily_consumption * 365 * 0.40,
            co2_reduction_tons=daily_consumption * 365 * 0.40 * 0.0004,
            property_id=property_id,
            location=location,
            created_at=datetime.now()
        ))
        
        return recommendations
    
    def _generate_water_heater_recommendations(self, equipment_id: str, data: Dict, property_id: str) -> List[OptimizationRecommendation]:
        """Generate water heater optimization recommendations"""
        recommendations = []
        daily_consumption = data.get('daily_consumption', 0)
        location = data.get('location', 'Unknown')
        
        # Smart water heater scheduling
        recommendations.append(OptimizationRecommendation(
            recommendation_id=f"water_heater_scheduling_{equipment_id}_{int(time.time())}",
            strategy=OptimizationStrategy.TIME_OF_USE,
            equipment_id=equipment_id,
            equipment_type='Water Heater',
            description=f"Install smart water heater controller for {location} to heat during off-peak hours",
            estimated_savings=daily_consumption * 365 * 0.20 * 0.08,  # 20% shift to off-peak
            implementation_cost=200.0,
            payback_period_months=int((200.0 / (daily_consumption * 365 * 0.20 * 0.08)) * 12),
            difficulty='medium',
            priority_score=70.0,
            annual_kwh_savings=0,  # Energy shifting, not reduction
            co2_reduction_tons=0,
            property_id=property_id,
            location=location,
            created_at=datetime.now()
        ))
        
        return recommendations
    
    def _generate_appliance_recommendations(self, equipment_id: str, data: Dict, property_id: str) -> List[OptimizationRecommendation]:
        """Generate appliance optimization recommendations"""
        recommendations = []
        daily_consumption = data.get('daily_consumption', 0)
        efficiency_score = data.get('efficiency_score', 75)
        location = data.get('location', 'Unknown')
        
        if efficiency_score < 70:
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"appliance_upgrade_{equipment_id}_{int(time.time())}",
                strategy=OptimizationStrategy.ENERGY_EFFICIENCY,
                equipment_id=equipment_id,
                equipment_type='Appliances',
                description=f"Replace {location} appliances with ENERGY STAR certified models",
                estimated_savings=daily_consumption * 365 * 0.25 * 0.15,  # 25% efficiency improvement
                implementation_cost=1500.0,
                payback_period_months=int((1500.0 / (daily_consumption * 365 * 0.25 * 0.15)) * 12),
                difficulty='hard',
                priority_score=60.0,
                annual_kwh_savings=daily_consumption * 365 * 0.25,
                co2_reduction_tons=daily_consumption * 365 * 0.25 * 0.0004,
                property_id=property_id,
                location=location,
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _generate_system_recommendations(self, energy_analysis: Dict, property_id: str) -> List[OptimizationRecommendation]:
        """Generate system-level optimization recommendations"""
        recommendations = []
        total_consumption = energy_analysis.get('total_consumption', 0)
        efficiency_score = energy_analysis.get('efficiency_score', 75)
        
        # Building automation system
        if total_consumption > 50:  # High consumption property
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"building_automation_{property_id}_{int(time.time())}",
                strategy=OptimizationStrategy.LOAD_BALANCING,
                equipment_id='building_automation_system',
                equipment_type='Building Management System',
                description="Install comprehensive building automation system for centralized energy management",
                estimated_savings=total_consumption * 365 * 0.18 * 0.15,  # 18% system-wide savings
                implementation_cost=5000.0,
                payback_period_months=int((5000.0 / (total_consumption * 365 * 0.18 * 0.15)) * 12),
                difficulty='hard',
                priority_score=90.0,
                annual_kwh_savings=total_consumption * 365 * 0.18,
                co2_reduction_tons=total_consumption * 365 * 0.18 * 0.0004,
                property_id=property_id,
                location='Building-wide',
                created_at=datetime.now()
            ))
        
        # Solar installation recommendation
        if efficiency_score > 70:  # Good efficiency baseline
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"solar_installation_{property_id}_{int(time.time())}",
                strategy=OptimizationStrategy.RENEWABLE_INTEGRATION,
                equipment_id='solar_system',
                equipment_type='Solar PV System',
                description="Install rooftop solar system with battery storage for renewable energy generation",
                estimated_savings=(total_consumption * 365 * 0.30 * 0.15) + (total_consumption * 365 * 0.30 * 0.03),  # 30% offset + renewable credits
                implementation_cost=15000.0,
                payback_period_months=int((15000.0 / ((total_consumption * 365 * 0.30 * 0.18))) * 12),
                difficulty='hard',
                priority_score=85.0,
                annual_kwh_savings=total_consumption * 365 * 0.30,
                co2_reduction_tons=total_consumption * 365 * 0.30 * 0.0004,
                property_id=property_id,
                location='Rooftop',
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def create_smart_schedules(self, recommendations: List[OptimizationRecommendation], energy_analysis: Dict) -> List[SmartSchedule]:
        """Create smart schedules based on optimization recommendations"""
        schedules = []
        
        for rec in recommendations:
            if rec.strategy in [OptimizationStrategy.TIME_OF_USE, OptimizationStrategy.LOAD_BALANCING]:
                schedule = self._create_equipment_schedule(rec, energy_analysis)
                if schedule:
                    schedules.append(schedule)
        
        return schedules
    
    def _create_equipment_schedule(self, recommendation: OptimizationRecommendation, energy_analysis: Dict) -> Optional[SmartSchedule]:
        """Create smart schedule for specific equipment"""
        equipment_id = recommendation.equipment_id
        
        # Find equipment data
        equipment_data = None
        for eq_id, data in energy_analysis.get('usage_analysis', {}).items():
            if eq_id == equipment_id:
                equipment_data = data
                break
        
        if not equipment_data:
            return None
        
        # Create time-based schedule
        if recommendation.strategy == OptimizationStrategy.TIME_OF_USE:
            schedule_data = self._create_time_of_use_schedule(equipment_data)
            schedule_type = 'time_based'
        elif recommendation.strategy == OptimizationStrategy.LOAD_BALANCING:
            schedule_data = self._create_load_balancing_schedule(equipment_data)
            schedule_type = 'load_balancing'
        else:
            return None
        
        return SmartSchedule(
            schedule_id=f"schedule_{equipment_id}_{int(time.time())}",
            equipment_id=equipment_id,
            equipment_type=equipment_data.get('equipment_type', 'unknown'),
            schedule_type=schedule_type,
            schedule_data=schedule_data,
            estimated_savings=recommendation.estimated_savings,
            active=False,  # Needs to be activated
            property_id=recommendation.property_id,
            created_at=datetime.now()
        )
    
    def _create_time_of_use_schedule(self, equipment_data: Dict) -> Dict:
        """Create time-of-use optimization schedule"""
        equipment_type = equipment_data.get('equipment_type', 'appliances')
        
        if equipment_type == 'hvac':
            return {
                'pre_cooling': {'hours': [14, 15], 'temperature_offset': -2},
                'peak_reduction': {'hours': [16, 17, 18, 19, 20, 21], 'temperature_offset': +3},
                'post_peak_recovery': {'hours': [22, 23], 'temperature_offset': -1}
            }
        elif equipment_type == 'water_heater':
            return {
                'heating_schedule': {'hours': [2, 3, 4, 5, 6, 23], 'operation': 'enabled'},
                'peak_hours': {'hours': [16, 17, 18, 19, 20, 21], 'operation': 'disabled'}
            }
        elif equipment_type == 'lighting':
            return {
                'daylight_dimming': {'hours': [9, 10, 11, 12, 13, 14, 15, 16], 'dimming_level': 0.3},
                'occupancy_control': {'enabled': True, 'timeout_minutes': 10},
                'peak_dimming': {'hours': [17, 18, 19, 20], 'dimming_level': 0.8}
            }
        else:
            return {'schedule_type': 'basic', 'peak_hours_operation': 'reduced'}
    
    def _create_load_balancing_schedule(self, equipment_data: Dict) -> Dict:
        """Create load balancing schedule"""
        return {
            'priority_level': 3,  # Medium priority
            'load_shedding_enabled': True,
            'max_demand_limit': equipment_data.get('daily_consumption', 10) * 0.8,
            'recovery_time_minutes': 30,
            'conditions': {
                'peak_demand_threshold': 50,  # kW
                'outdoor_temperature_threshold': 85,  # °F
                'occupancy_threshold': 0.8
            }
        }

def serialize_recommendation(rec: OptimizationRecommendation) -> Dict:
    """Convert OptimizationRecommendation to JSON-serializable dict"""
    result = asdict(rec)
    result['strategy'] = rec.strategy.value
    result['created_at'] = rec.created_at.isoformat()
    return result

def serialize_schedule(schedule: SmartSchedule) -> Dict:
    """Convert SmartSchedule to JSON-serializable dict"""
    result = asdict(schedule)
    result['created_at'] = schedule.created_at.isoformat()
    return result

def generate_energy_optimization_dashboard(energy_analysis: Dict, recommendations: List[OptimizationRecommendation], schedules: List[SmartSchedule]) -> Dict:
    """Generate comprehensive energy optimization dashboard data"""
    
    # Calculate summary metrics
    total_consumption = energy_analysis.get('total_consumption', 0)
    efficiency_score = energy_analysis.get('efficiency_score', 0)
    
    total_potential_savings = sum(rec.estimated_savings for rec in recommendations)
    total_implementation_cost = sum(rec.implementation_cost for rec in recommendations)
    total_annual_kwh_savings = sum(rec.annual_kwh_savings for rec in recommendations)
    total_co2_reduction = sum(rec.co2_reduction_tons for rec in recommendations)
    
    # ROI calculation
    if total_implementation_cost > 0:
        simple_payback_years = total_implementation_cost / total_potential_savings if total_potential_savings > 0 else float('inf')
    else:
        simple_payback_years = 0
    
    # Categorize recommendations by strategy
    strategy_breakdown = {}
    for rec in recommendations:
        strategy = rec.strategy.value
        if strategy not in strategy_breakdown:
            strategy_breakdown[strategy] = {
                'count': 0,
                'total_savings': 0,
                'total_cost': 0,
                'avg_payback_months': 0
            }
        
        strategy_breakdown[strategy]['count'] += 1
        strategy_breakdown[strategy]['total_savings'] += rec.estimated_savings
        strategy_breakdown[strategy]['total_cost'] += rec.implementation_cost
    
    # Calculate average payback for each strategy
    for strategy in strategy_breakdown:
        data = strategy_breakdown[strategy]
        if data['total_savings'] > 0:
            avg_payback_years = data['total_cost'] / data['total_savings']
            data['avg_payback_months'] = round(avg_payback_years * 12, 1)
        else:
            data['avg_payback_months'] = float('inf')
    
    # Priority recommendations (top 5)
    priority_recommendations = sorted(recommendations, key=lambda x: x.priority_score, reverse=True)[:5]
    
    return {
        'summary': {
            'total_consumption_kwh_day': round(total_consumption, 2),
            'current_efficiency_score': round(efficiency_score, 1),
            'total_potential_annual_savings': round(total_potential_savings, 2),
            'total_implementation_cost': round(total_implementation_cost, 2),
            'simple_payback_years': round(simple_payback_years, 1),
            'total_annual_kwh_savings': round(total_annual_kwh_savings, 2),
            'total_co2_reduction_tons': round(total_co2_reduction, 3),
            'total_recommendations': len(recommendations),
            'active_schedules': len([s for s in schedules if s.active])
        },
        'strategy_breakdown': strategy_breakdown,
        'priority_recommendations': [serialize_recommendation(rec) for rec in priority_recommendations],
        'all_recommendations': [serialize_recommendation(rec) for rec in recommendations],
        'smart_schedules': [serialize_schedule(schedule) for schedule in schedules],
        'optimization_opportunities': {
            'high_impact': len([r for r in recommendations if r.priority_score >= 80]),
            'medium_impact': len([r for r in recommendations if 60 <= r.priority_score < 80]),
            'low_impact': len([r for r in recommendations if r.priority_score < 60])
        },
        'dashboard_updated': datetime.now().isoformat()
    }