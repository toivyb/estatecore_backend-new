#!/usr/bin/env python3
"""
Smart Energy Management Engine for EstateCore Phase 5C
AI-powered energy optimization and consumption analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

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

class SmartEnergyEngine:
    """AI-powered Smart Energy Management Engine"""
    
    def __init__(self):
        self.consumption_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.anomaly_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        self.cost_model = RandomForestRegressor(n_estimators=75, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
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
        np.random.seed(42)
        
        # Generate 90 days of synthetic energy data for training
        dates = [datetime.now() - timedelta(days=x) for x in range(90, 0, -1)]
        
        for date in dates:
            # Simulate seasonal and daily patterns
            day_of_year = date.timetuple().tm_yday
            hour = date.hour
            
            # Base consumption with seasonal variation
            seasonal_factor = 0.8 + 0.4 * np.sin(2 * np.pi * day_of_year / 365)
            daily_factor = 0.6 + 0.4 * np.sin(2 * np.pi * hour / 24)
            
            # Generate readings for different energy types
            for property_id in [1, 2, 3]:
                # Electricity
                base_electricity = 400 * seasonal_factor * daily_factor
                electricity = max(50, base_electricity + np.random.normal(0, 50))
                self.energy_readings.append(EnergyReading(
                    property_id=property_id,
                    unit_id=None,
                    energy_type=EnergyType.ELECTRICITY,
                    consumption=electricity,
                    cost=electricity * 0.12,  # $0.12/kWh
                    timestamp=date,
                    temperature=70 + np.random.normal(0, 15),
                    occupancy=np.random.choice([True, False], p=[0.7, 0.3])
                ))
                
                # Gas
                base_gas = 80 * seasonal_factor
                gas = max(10, base_gas + np.random.normal(0, 15))
                self.energy_readings.append(EnergyReading(
                    property_id=property_id,
                    unit_id=None,
                    energy_type=EnergyType.GAS,
                    consumption=gas,
                    cost=gas * 1.20,  # $1.20/therm
                    timestamp=date,
                    temperature=70 + np.random.normal(0, 15),
                    occupancy=np.random.choice([True, False], p=[0.7, 0.3])
                ))
                
                # HVAC
                base_hvac = 200 * seasonal_factor * daily_factor
                hvac = max(50, base_hvac + np.random.normal(0, 30))
                self.energy_readings.append(EnergyReading(
                    property_id=property_id,
                    unit_id=None,
                    energy_type=EnergyType.HVAC,
                    consumption=hvac,
                    cost=hvac * 0.15,  # Higher rate for HVAC
                    timestamp=date,
                    temperature=70 + np.random.normal(0, 15),
                    occupancy=np.random.choice([True, False], p=[0.7, 0.3])
                ))
    
    def add_energy_reading(self, reading: EnergyReading):
        """Add a new energy reading to the system"""
        self.energy_readings.append(reading)
        
        # Check for alerts
        alerts = self._check_for_alerts(reading)
        return alerts
    
    def train_models(self, retrain: bool = False):
        """Train the AI models with available energy data"""
        if self.is_trained and not retrain:
            return
            
        if len(self.energy_readings) < 50:
            logging.warning("Insufficient data for training. Need at least 50 readings.")
            return
        
        # Prepare training data
        features, targets_consumption, targets_cost = self._prepare_training_data()
        
        if len(features) == 0:
            return
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train consumption model
        X_train, X_test, y_train_cons, y_test_cons = train_test_split(
            features_scaled, targets_consumption, test_size=0.2, random_state=42
        )
        
        self.consumption_model.fit(X_train, y_train_cons)
        
        # Train cost model
        _, _, y_train_cost, y_test_cost = train_test_split(
            features_scaled, targets_cost, test_size=0.2, random_state=42
        )
        
        self.cost_model.fit(X_train, y_train_cost)
        
        # Calculate model accuracy
        cons_pred = self.consumption_model.predict(X_test)
        cost_pred = self.cost_model.predict(X_test)
        
        cons_mae = mean_absolute_error(y_test_cons, cons_pred)
        cost_mae = mean_absolute_error(y_test_cost, cost_pred)
        
        self.is_trained = True
        
        logging.info(f"Models trained successfully. Consumption MAE: {cons_mae:.2f}, Cost MAE: {cost_mae:.2f}")
    
    def _prepare_training_data(self) -> Tuple[List[List[float]], List[float], List[float]]:
        """Prepare training data from energy readings"""
        features = []
        targets_consumption = []
        targets_cost = []
        
        # Group readings by property and energy type for feature engineering
        df = pd.DataFrame([{
            'property_id': r.property_id,
            'energy_type': r.energy_type.value,
            'consumption': r.consumption,
            'cost': r.cost,
            'timestamp': r.timestamp,
            'temperature': r.temperature or 70,
            'occupancy': 1 if r.occupancy else 0,
            'hour': r.timestamp.hour,
            'day_of_week': r.timestamp.weekday(),
            'month': r.timestamp.month,
            'day_of_year': r.timestamp.timetuple().tm_yday
        } for r in self.energy_readings])
        
        # Create features for each reading
        for _, row in df.iterrows():
            feature_vector = [
                row['property_id'],
                hash(row['energy_type']) % 1000,  # Energy type encoding
                row['temperature'],
                row['occupancy'],
                row['hour'],
                row['day_of_week'],
                row['month'],
                np.sin(2 * np.pi * row['day_of_year'] / 365),  # Seasonal component
                np.cos(2 * np.pi * row['day_of_year'] / 365),
                np.sin(2 * np.pi * row['hour'] / 24),  # Daily component
                np.cos(2 * np.pi * row['hour'] / 24)
            ]
            
            features.append(feature_vector)
            targets_consumption.append(row['consumption'])
            targets_cost.append(row['cost'])
        
        return features, targets_consumption, targets_cost
    
    def predict_consumption(self, property_id: int, energy_type: EnergyType, 
                          forecast_days: int = 7) -> EnergyForecast:
        """Predict energy consumption for the next N days"""
        if not self.is_trained:
            self.train_models()
        
        predictions_consumption = []
        predictions_cost = []
        confidence_intervals = []
        forecast_dates = []
        
        # Generate predictions for each day
        for day in range(forecast_days):
            future_date = datetime.now() + timedelta(days=day)
            
            # Create feature vector for prediction
            features = [
                property_id,
                hash(energy_type.value) % 1000,
                70,  # Default temperature
                1,   # Assume occupied
                12,  # Noon hour as default
                future_date.weekday(),
                future_date.month,
                np.sin(2 * np.pi * future_date.timetuple().tm_yday / 365),
                np.cos(2 * np.pi * future_date.timetuple().tm_yday / 365),
                np.sin(2 * np.pi * 12 / 24),
                np.cos(2 * np.pi * 12 / 24)
            ]
            
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Predict consumption and cost
            pred_consumption = self.consumption_model.predict(features_scaled)[0]
            pred_cost = self.cost_model.predict(features_scaled)[0]
            
            predictions_consumption.append(max(0, pred_consumption))
            predictions_cost.append(max(0, pred_cost))
            
            # Calculate confidence interval (simplified)
            std_dev = pred_consumption * 0.15  # 15% standard deviation
            confidence_intervals.append((
                max(0, pred_consumption - 1.96 * std_dev),
                pred_consumption + 1.96 * std_dev
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
            accuracy_score=0.85,  # Placeholder accuracy
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
        """Generate AI-powered optimization recommendations"""
        recommendations = []
        
        # Get recent energy data for the property
        property_readings = [r for r in self.energy_readings 
                           if r.property_id == property_id and 
                           r.timestamp > datetime.now() - timedelta(days=30)]
        
        if not property_readings:
            return recommendations
        
        # Analyze consumption patterns
        df = pd.DataFrame([{
            'energy_type': r.energy_type.value,
            'consumption': r.consumption,
            'cost': r.cost,
            'hour': r.timestamp.hour
        } for r in property_readings])
        
        # HVAC optimization recommendations
        hvac_data = df[df['energy_type'] == 'hvac']
        if not hvac_data.empty and hvac_data['consumption'].mean() > 250:
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
        lighting_data = df[df['energy_type'] == 'lighting']
        if not lighting_data.empty and lighting_data['consumption'].mean() > 40:
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
        peak_hours_consumption = df[df['hour'].isin([17, 18, 19, 20])]['consumption'].mean()
        if peak_hours_consumption > 400:
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
        df = pd.DataFrame([{
            'energy_type': r.energy_type.value,
            'consumption': r.consumption,
            'cost': r.cost,
            'timestamp': r.timestamp,
            'hour': r.timestamp.hour
        } for r in property_readings])
        
        # Aggregate by energy type
        energy_summary = df.groupby('energy_type').agg({
            'consumption': ['sum', 'mean', 'max'],
            'cost': ['sum', 'mean', 'max']
        }).round(2)
        
        # Peak usage analysis
        peak_hour = df.groupby('hour')['consumption'].sum().idxmax()
        peak_consumption = df.groupby('hour')['consumption'].sum().max()
        
        # Cost breakdown
        total_cost = df['cost'].sum()
        cost_by_type = df.groupby('energy_type')['cost'].sum().to_dict()
        
        return {
            'property_id': property_id,
            'analysis_period_days': days,
            'total_consumption': round(df['consumption'].sum(), 2),
            'total_cost': round(total_cost, 2),
            'average_daily_cost': round(total_cost / days, 2),
            'peak_hour': peak_hour,
            'peak_consumption': round(peak_consumption, 2),
            'energy_breakdown': energy_summary.to_dict(),
            'cost_breakdown': cost_by_type,
            'efficiency_score': self._calculate_efficiency_score(df),
            'recommendations_count': len(self.generate_optimization_recommendations(property_id))
        }
    
    def _calculate_efficiency_score(self, df: pd.DataFrame) -> float:
        """Calculate an efficiency score from 0-100"""
        # Simple efficiency calculation based on consumption patterns
        avg_consumption = df['consumption'].mean()
        consumption_variance = df['consumption'].var()
        
        # Lower variance and reasonable consumption = higher efficiency
        base_score = 85
        variance_penalty = min(20, consumption_variance / 100)
        consumption_penalty = max(0, (avg_consumption - 300) / 50)
        
        efficiency_score = max(0, min(100, base_score - variance_penalty - consumption_penalty))
        return round(efficiency_score, 1)

# Example usage and testing
if __name__ == "__main__":
    # Initialize the smart energy engine
    engine = SmartEnergyEngine()
    
    # Train models with baseline data
    engine.train_models()
    
    # Generate forecast
    forecast = engine.predict_consumption(property_id=1, energy_type=EnergyType.ELECTRICITY, forecast_days=7)
    print(f"7-day electricity forecast: {forecast.predicted_consumption}")
    
    # Get optimization recommendations
    recommendations = engine.generate_optimization_recommendations(property_id=1)
    for rec in recommendations:
        print(f"Recommendation: {rec.title} - Potential savings: ${rec.potential_savings}/month")
    
    # Get analytics
    analytics = engine.get_energy_analytics(property_id=1)
    print(f"Energy analytics: Total cost ${analytics['total_cost']}, Efficiency score: {analytics['efficiency_score']}")