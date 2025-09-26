#!/usr/bin/env python3
"""
Simplified Smart Energy Management Engine for EstateCore Phase 5C
Basic energy optimization and consumption analysis without external ML dependencies
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging

class EnergyType(Enum):
    ELECTRICITY = "electricity"
    GAS = "gas"
    WATER = "water"
    SOLAR = "solar"
    HVAC = "hvac"
    LIGHTING = "lighting"

class OptimizationStrategy(Enum):
    COST_REDUCTION = "cost_reduction"
    SUSTAINABILITY = "sustainability"
    EFFICIENCY = "efficiency"
    PEAK_SHAVING = "peak_shaving"
    DEMAND_RESPONSE = "demand_response"

class AlertType(Enum):
    HIGH_CONSUMPTION = "high_consumption"
    EQUIPMENT_INEFFICIENCY = "equipment_inefficiency"
    ANOMALY_DETECTED = "anomaly_detected"
    COST_SPIKE = "cost_spike"
    MAINTENANCE_REQUIRED = "maintenance_required"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"

@dataclass
class EnergyReading:
    """Individual energy consumption reading"""
    property_id: int
    unit_id: Optional[int]
    energy_type: EnergyType
    consumption: float  # kWh, therms, gallons, etc.
    cost: float
    timestamp: datetime
    temperature: Optional[float] = None
    occupancy: Optional[bool] = None
    equipment_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class EnergyForecast:
    """Energy consumption forecast"""
    property_id: int
    energy_type: EnergyType
    forecast_period: str  # daily, weekly, monthly
    predicted_consumption: List[float]
    predicted_cost: List[float]
    confidence_intervals: List[Tuple[float, float]]
    forecast_dates: List[datetime]
    accuracy_score: float
    created_at: datetime

@dataclass
class OptimizationRecommendation:
    """Energy optimization recommendation"""
    property_id: int
    recommendation_type: OptimizationStrategy
    title: str
    description: str
    potential_savings: float  # $ per month
    implementation_cost: float
    payback_period_months: float
    energy_reduction_percent: float
    priority_score: float
    equipment_involved: List[str]
    implementation_steps: List[str]
    created_at: datetime

@dataclass
class EnergyAlert:
    """Energy management alert"""
    property_id: int
    alert_type: AlertType
    severity: str  # low, medium, high, critical
    title: str
    message: str
    current_value: float
    threshold_value: float
    energy_type: EnergyType
    equipment_id: Optional[str] = None
    recommended_action: Optional[str] = None
    created_at: datetime = None

class SimpleSmartEnergyEngine:
    """Simplified AI-powered Smart Energy Management Engine"""
    
    def __init__(self):
        self.energy_readings = []
        self.thresholds = {
            EnergyType.ELECTRICITY: {'high': 500, 'anomaly': 750},  # kWh/day
            EnergyType.GAS: {'high': 100, 'anomaly': 150},  # therms/day
            EnergyType.WATER: {'high': 300, 'anomaly': 500},  # gallons/day
            EnergyType.HVAC: {'high': 300, 'anomaly': 450},  # kWh/day
            EnergyType.LIGHTING: {'high': 50, 'anomaly': 75}  # kWh/day
        }
        
        # Initialize with some baseline training data
        self._generate_baseline_training_data()
    
    def _generate_baseline_training_data(self):
        """Generate baseline training data for initial model training"""
        random.seed(42)
        
        # Generate 90 days of synthetic energy data for training
        dates = [datetime.now() - timedelta(days=x) for x in range(90, 0, -1)]
        
        for date in dates:
            # Simulate seasonal and daily patterns
            day_of_year = date.timetuple().tm_yday
            hour = date.hour
            
            # Base consumption with seasonal variation
            seasonal_factor = 0.8 + 0.4 * math.sin(2 * math.pi * day_of_year / 365)
            daily_factor = 0.6 + 0.4 * math.sin(2 * math.pi * hour / 24)
            
            # Generate readings for different energy types
            for property_id in [1, 2, 3]:
                # Electricity
                base_electricity = 400 * seasonal_factor * daily_factor
                electricity = max(50, base_electricity + random.gauss(0, 50))
                self.energy_readings.append(EnergyReading(
                    property_id=property_id,
                    unit_id=None,
                    energy_type=EnergyType.ELECTRICITY,
                    consumption=electricity,
                    cost=electricity * 0.12,  # $0.12/kWh
                    timestamp=date,
                    temperature=70 + random.gauss(0, 15),
                    occupancy=random.choice([True, False])
                ))
                
                # Gas
                base_gas = 80 * seasonal_factor
                gas = max(10, base_gas + random.gauss(0, 15))
                self.energy_readings.append(EnergyReading(
                    property_id=property_id,
                    unit_id=None,
                    energy_type=EnergyType.GAS,
                    consumption=gas,
                    cost=gas * 1.20,  # $1.20/therm
                    timestamp=date,
                    temperature=70 + random.gauss(0, 15),
                    occupancy=random.choice([True, False])
                ))
                
                # HVAC
                base_hvac = 200 * seasonal_factor * daily_factor
                hvac = max(50, base_hvac + random.gauss(0, 30))
                self.energy_readings.append(EnergyReading(
                    property_id=property_id,
                    unit_id=None,
                    energy_type=EnergyType.HVAC,
                    consumption=hvac,
                    cost=hvac * 0.15,  # Higher rate for HVAC
                    timestamp=date,
                    temperature=70 + random.gauss(0, 15),
                    occupancy=random.choice([True, False])
                ))
    
    def add_energy_reading(self, reading: EnergyReading):
        """Add a new energy reading to the system"""
        self.energy_readings.append(reading)
        
        # Check for alerts
        alerts = self._check_for_alerts(reading)
        return alerts
    
    def predict_consumption(self, property_id: int, energy_type: EnergyType, 
                          forecast_days: int = 7) -> EnergyForecast:
        """Predict energy consumption for the next N days using simple statistical methods"""
        
        # Get historical data for the property and energy type
        historical_data = [r for r in self.energy_readings 
                          if r.property_id == property_id and r.energy_type == energy_type]
        
        if not historical_data:
            # Generate default forecast if no historical data
            return self._generate_default_forecast(property_id, energy_type, forecast_days)
        
        # Calculate simple moving average
        recent_data = historical_data[-30:] if len(historical_data) >= 30 else historical_data
        avg_consumption = sum(r.consumption for r in recent_data) / len(recent_data)
        avg_cost = sum(r.cost for r in recent_data) / len(recent_data)
        
        predictions_consumption = []
        predictions_cost = []
        confidence_intervals = []
        forecast_dates = []
        
        # Generate predictions for each day with some variation
        for day in range(forecast_days):
            future_date = datetime.now() + timedelta(days=day)
            
            # Add seasonal variation
            day_of_year = future_date.timetuple().tm_yday
            seasonal_factor = 0.8 + 0.4 * math.sin(2 * math.pi * day_of_year / 365)
            
            # Add some random variation
            variation = random.uniform(0.85, 1.15)
            
            pred_consumption = avg_consumption * seasonal_factor * variation
            pred_cost = avg_cost * seasonal_factor * variation
            
            predictions_consumption.append(max(0, pred_consumption))
            predictions_cost.append(max(0, pred_cost))
            
            # Calculate confidence interval (simplified)
            std_dev = pred_consumption * 0.2  # 20% standard deviation
            confidence_intervals.append((
                max(0, pred_consumption - std_dev),
                pred_consumption + std_dev
            ))
            
            forecast_dates.append(future_date)
        
        return EnergyForecast(
            property_id=property_id,
            energy_type=energy_type,
            forecast_period=f"{forecast_days}_days",
            predicted_consumption=predictions_consumption,
            predicted_cost=predictions_cost,
            confidence_intervals=confidence_intervals,
            forecast_dates=forecast_dates,
            accuracy_score=0.80,  # Estimated accuracy for simple method
            created_at=datetime.now()
        )
    
    def _generate_default_forecast(self, property_id: int, energy_type: EnergyType, 
                                 forecast_days: int) -> EnergyForecast:
        """Generate a default forecast when no historical data is available"""
        
        # Default consumption values by energy type
        default_consumption = {
            EnergyType.ELECTRICITY: 400,
            EnergyType.GAS: 80,
            EnergyType.WATER: 250,
            EnergyType.HVAC: 200,
            EnergyType.LIGHTING: 40,
            EnergyType.SOLAR: -100  # Negative for generation
        }
        
        default_rates = {
            EnergyType.ELECTRICITY: 0.12,
            EnergyType.GAS: 1.20,
            EnergyType.WATER: 0.008,
            EnergyType.HVAC: 0.15,
            EnergyType.LIGHTING: 0.12,
            EnergyType.SOLAR: -0.08  # Credit for generation
        }
        
        base_consumption = default_consumption.get(energy_type, 100)
        rate = default_rates.get(energy_type, 0.10)
        
        predictions_consumption = []
        predictions_cost = []
        confidence_intervals = []
        forecast_dates = []
        
        for day in range(forecast_days):
            future_date = datetime.now() + timedelta(days=day)
            
            # Add some variation
            variation = random.uniform(0.9, 1.1)
            consumption = base_consumption * variation
            cost = consumption * rate
            
            predictions_consumption.append(consumption)
            predictions_cost.append(cost)
            confidence_intervals.append((consumption * 0.8, consumption * 1.2))
            forecast_dates.append(future_date)
        
        return EnergyForecast(
            property_id=property_id,
            energy_type=energy_type,
            forecast_period=f"{forecast_days}_days",
            predicted_consumption=predictions_consumption,
            predicted_cost=predictions_cost,
            confidence_intervals=confidence_intervals,
            forecast_dates=forecast_dates,
            accuracy_score=0.75,  # Lower accuracy for default forecast
            created_at=datetime.now()
        )
    
    def _check_for_alerts(self, reading: EnergyReading) -> List[EnergyAlert]:
        """Check if a reading triggers any alerts"""
        alerts = []
        
        thresholds = self.thresholds.get(reading.energy_type, {})
        
        # High consumption alert
        if reading.consumption > thresholds.get('high', float('inf')):
            alerts.append(EnergyAlert(
                property_id=reading.property_id,
                alert_type=AlertType.HIGH_CONSUMPTION,
                severity='medium',
                title=f'High {reading.energy_type.value.title()} Consumption',
                message=f'Consumption of {reading.consumption:.1f} exceeds normal levels',
                current_value=reading.consumption,
                threshold_value=thresholds['high'],
                energy_type=reading.energy_type,
                equipment_id=reading.equipment_id,
                recommended_action='Check for equipment issues or unusual usage patterns',
                created_at=datetime.now()
            ))
        
        # Anomaly detection alert
        if reading.consumption > thresholds.get('anomaly', float('inf')):
            alerts.append(EnergyAlert(
                property_id=reading.property_id,
                alert_type=AlertType.ANOMALY_DETECTED,
                severity='high',
                title=f'Energy Usage Anomaly Detected',
                message=f'Unusual {reading.energy_type.value} consumption pattern detected',
                current_value=reading.consumption,
                threshold_value=thresholds['anomaly'],
                energy_type=reading.energy_type,
                equipment_id=reading.equipment_id,
                recommended_action='Immediate investigation required',
                created_at=datetime.now()
            ))
        
        return alerts
    
    def generate_optimization_recommendations(self, property_id: int) -> List[OptimizationRecommendation]:
        """Generate simple optimization recommendations"""
        recommendations = []
        
        # Get recent energy data for the property
        property_readings = [r for r in self.energy_readings 
                           if r.property_id == property_id and 
                           r.timestamp > datetime.now() - timedelta(days=30)]
        
        if not property_readings:
            return recommendations
        
        # Calculate average consumption by type
        consumption_by_type = {}
        for reading in property_readings:
            energy_type = reading.energy_type.value
            if energy_type not in consumption_by_type:
                consumption_by_type[energy_type] = []
            consumption_by_type[energy_type].append(reading.consumption)
        
        # Average consumption for each type
        avg_consumption = {}
        for energy_type, values in consumption_by_type.items():
            avg_consumption[energy_type] = sum(values) / len(values)
        
        # HVAC optimization recommendations
        if avg_consumption.get('hvac', 0) > 250:
            recommendations.append(OptimizationRecommendation(
                property_id=property_id,
                recommendation_type=OptimizationStrategy.EFFICIENCY,
                title='HVAC System Optimization',
                description='Install smart thermostats and optimize HVAC schedules to reduce energy consumption during peak hours',
                potential_savings=180.0,  # $ per month
                implementation_cost=2500.0,
                payback_period_months=13.9,
                energy_reduction_percent=15.0,
                priority_score=8.5,
                equipment_involved=['HVAC', 'Thermostats'],
                implementation_steps=[
                    'Install programmable smart thermostats',
                    'Set optimized temperature schedules',
                    'Regular maintenance and filter replacement',
                    'Monitor and adjust based on occupancy patterns'
                ],
                created_at=datetime.now()
            ))
        
        # Lighting optimization
        if avg_consumption.get('lighting', 0) > 40:
            recommendations.append(OptimizationRecommendation(
                property_id=property_id,
                recommendation_type=OptimizationStrategy.COST_REDUCTION,
                title='LED Lighting Upgrade',
                description='Replace traditional lighting with LED fixtures and install motion sensors',
                potential_savings=75.0,
                implementation_cost=1200.0,
                payback_period_months=16.0,
                energy_reduction_percent=60.0,
                priority_score=7.8,
                equipment_involved=['Lighting', 'Motion Sensors'],
                implementation_steps=[
                    'Audit current lighting fixtures',
                    'Replace with LED equivalents',
                    'Install motion sensors in common areas',
                    'Set up automated lighting schedules'
                ],
                created_at=datetime.now()
            ))
        
        # Peak shaving recommendation
        if avg_consumption.get('electricity', 0) > 400:
            recommendations.append(OptimizationRecommendation(
                property_id=property_id,
                recommendation_type=OptimizationStrategy.PEAK_SHAVING,
                title='Peak Hour Load Management',
                description='Implement demand response strategies and battery storage to reduce peak hour consumption',
                potential_savings=220.0,
                implementation_cost=8000.0,
                payback_period_months=36.4,
                energy_reduction_percent=25.0,
                priority_score=9.2,
                equipment_involved=['Battery Storage', 'Smart Controls'],
                implementation_steps=[
                    'Install battery storage system',
                    'Implement load shifting strategies',
                    'Set up automated peak shaving controls',
                    'Monitor and optimize performance'
                ],
                created_at=datetime.now()
            ))
        
        return sorted(recommendations, key=lambda x: x.priority_score, reverse=True)
    
    def get_energy_analytics(self, property_id: int, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive energy analytics for a property"""
        property_readings = [r for r in self.energy_readings 
                           if r.property_id == property_id and 
                           r.timestamp > datetime.now() - timedelta(days=days)]
        
        if not property_readings:
            return {'error': 'No energy data available for this property'}
        
        # Calculate analytics
        total_consumption = sum(r.consumption for r in property_readings)
        total_cost = sum(r.cost for r in property_readings)
        
        # Group by energy type
        consumption_by_type = {}
        cost_by_type = {}
        
        for reading in property_readings:
            energy_type = reading.energy_type.value
            if energy_type not in consumption_by_type:
                consumption_by_type[energy_type] = []
                cost_by_type[energy_type] = 0
            consumption_by_type[energy_type].append(reading.consumption)
            cost_by_type[energy_type] += reading.cost
        
        # Peak usage analysis
        hourly_consumption = {}
        for reading in property_readings:
            hour = reading.timestamp.hour
            if hour not in hourly_consumption:
                hourly_consumption[hour] = 0
            hourly_consumption[hour] += reading.consumption
        
        peak_hour = max(hourly_consumption.keys(), key=lambda h: hourly_consumption[h]) if hourly_consumption else 12
        peak_consumption = hourly_consumption.get(peak_hour, 0)
        
        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(property_readings)
        
        return {
            'property_id': property_id,
            'analysis_period_days': days,
            'total_consumption': round(total_consumption, 2),
            'total_cost': round(total_cost, 2),
            'average_daily_cost': round(total_cost / max(days, 1), 2),
            'peak_hour': peak_hour,
            'peak_consumption': round(peak_consumption, 2),
            'cost_breakdown': {k: round(v, 2) for k, v in cost_by_type.items()},
            'efficiency_score': efficiency_score,
            'recommendations_count': len(self.generate_optimization_recommendations(property_id))
        }
    
    def _calculate_efficiency_score(self, readings: List[EnergyReading]) -> float:
        """Calculate an efficiency score from 0-100"""
        if not readings:
            return 0
        
        # Simple efficiency calculation based on consumption patterns
        consumptions = [r.consumption for r in readings]
        avg_consumption = sum(consumptions) / len(consumptions)
        
        # Calculate variance manually
        variance = sum((c - avg_consumption) ** 2 for c in consumptions) / len(consumptions)
        
        # Lower variance and reasonable consumption = higher efficiency
        base_score = 85
        variance_penalty = min(20, variance / 100)
        consumption_penalty = max(0, (avg_consumption - 300) / 50)
        
        efficiency_score = max(0, min(100, base_score - variance_penalty - consumption_penalty))
        return round(efficiency_score, 1)