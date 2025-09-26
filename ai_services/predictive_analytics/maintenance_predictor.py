#!/usr/bin/env python3
"""
Advanced Predictive Maintenance AI System for EstateCore Phase 6
Machine learning-powered maintenance prediction and optimization
"""

import os
import json
import logging
import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pickle

# Try importing ML libraries with fallbacks
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("scikit-learn not available, using simplified predictive models")

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False

class MaintenanceType(Enum):
    HVAC = "hvac"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    APPLIANCE = "appliance"
    STRUCTURAL = "structural"
    ROOFING = "roofing"
    FLOORING = "flooring"
    PAINTING = "painting"
    LANDSCAPING = "landscaping"
    SECURITY = "security"

class MaintenancePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class PredictionConfidence(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class MaintenanceStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

@dataclass
class MaintenanceRecord:
    """Historical maintenance record"""
    record_id: str
    property_id: int
    maintenance_type: MaintenanceType
    description: str
    cost: float
    completion_date: datetime
    duration_hours: int
    priority: MaintenancePriority
    contractor: str
    parts_replaced: List[str]
    issue_severity: int  # 1-10 scale
    customer_satisfaction: int  # 1-5 scale
    weather_conditions: str
    equipment_age_years: float
    last_maintenance_days: int
    property_age_years: int
    tenant_reported: bool

@dataclass
class EquipmentData:
    """Equipment/system information for prediction"""
    equipment_id: str
    property_id: int
    equipment_type: MaintenanceType
    brand: str
    model: str
    installation_date: datetime
    warranty_expiry: Optional[datetime]
    last_service_date: Optional[datetime]
    service_intervals: List[datetime]
    operating_hours: int
    energy_consumption: float
    performance_metrics: Dict[str, float]
    sensor_readings: Dict[str, float]
    maintenance_history: List[str]
    replacement_cost: float

@dataclass
class MaintenancePrediction:
    """Maintenance prediction result"""
    property_id: int
    equipment_id: Optional[str]
    maintenance_type: MaintenanceType
    predicted_date: datetime
    confidence: PredictionConfidence
    confidence_score: float
    
    # Prediction details
    risk_factors: Dict[str, float]
    estimated_cost: Tuple[float, float]  # min, max
    estimated_duration: int  # hours
    recommended_priority: MaintenancePriority
    
    # Supporting information
    reason: str
    preventive_actions: List[str]
    warning_signs: List[str]
    cost_impact_if_delayed: float
    optimal_scheduling_window: Tuple[datetime, datetime]
    
    # Model information
    model_version: str
    prediction_timestamp: datetime
    data_sources: List[str]

@dataclass
class OptimizationRecommendation:
    """Maintenance scheduling optimization"""
    property_id: int
    optimization_period: Tuple[datetime, datetime]
    total_predicted_cost: float
    recommendations: List[Dict[str, Any]]
    cost_savings_potential: float
    efficiency_improvements: Dict[str, float]
    resource_requirements: Dict[str, int]

class PredictiveMaintenanceAI:
    """Advanced predictive maintenance system with ML capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sklearn_available = SKLEARN_AVAILABLE
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_performances = {}
        
        # Load historical data and train models
        self.historical_data = []
        self.equipment_database = {}
        
        # Feature engineering components
        self.feature_columns = []
        self.target_columns = []
        
        # Configuration
        self.config = self._load_configuration()
        
        # Initialize models
        self._initialize_models()
        
        self.logger.info(f"PredictiveMaintenanceAI initialized - sklearn: {SKLEARN_AVAILABLE}")

    def _load_configuration(self) -> Dict:
        """Load system configuration"""
        return {
            'prediction_horizon_days': 90,
            'cost_escalation_factor': 1.5,
            'confidence_thresholds': {
                'very_high': 0.9,
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4,
                'very_low': 0.0
            },
            'maintenance_intervals': {
                MaintenanceType.HVAC: 180,  # days
                MaintenanceType.PLUMBING: 365,
                MaintenanceType.ELECTRICAL: 730,
                MaintenanceType.APPLIANCE: 365,
                MaintenanceType.STRUCTURAL: 1095,
                MaintenanceType.ROOFING: 1825,
                MaintenanceType.FLOORING: 2190,
                MaintenanceType.PAINTING: 1460,
                MaintenanceType.LANDSCAPING: 30,
                MaintenanceType.SECURITY: 90
            },
            'cost_ranges': {
                MaintenanceType.HVAC: (200, 2000),
                MaintenanceType.PLUMBING: (150, 1500),
                MaintenanceType.ELECTRICAL: (100, 1000),
                MaintenanceType.APPLIANCE: (100, 800),
                MaintenanceType.STRUCTURAL: (500, 5000),
                MaintenanceType.ROOFING: (1000, 8000),
                MaintenanceType.FLOORING: (500, 3000),
                MaintenanceType.PAINTING: (200, 1000),
                MaintenanceType.LANDSCAPING: (50, 300),
                MaintenanceType.SECURITY: (100, 500)
            }
        }

    def _initialize_models(self):
        """Initialize ML models for different maintenance types"""
        if not self.sklearn_available:
            self.logger.warning("sklearn not available, using rule-based predictions")
            return
            
        try:
            # Initialize models for each maintenance type
            for maintenance_type in MaintenanceType:
                # Regression model for cost prediction
                self.models[f'{maintenance_type.value}_cost'] = RandomForestRegressor(
                    n_estimators=100, random_state=42, max_depth=10
                )
                
                # Regression model for time prediction
                self.models[f'{maintenance_type.value}_time'] = RandomForestRegressor(
                    n_estimators=100, random_state=42, max_depth=10
                )
                
                # Anomaly detection model
                self.models[f'{maintenance_type.value}_anomaly'] = IsolationForest(
                    contamination=0.1, random_state=42
                )
                
                # Scalers for feature normalization
                self.scalers[maintenance_type.value] = StandardScaler()
            
            # Global clustering model for maintenance optimization
            self.models['clustering'] = KMeans(n_clusters=5, random_state=42)
            
            self.logger.info("ML models initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ML models: {str(e)}")

    def add_maintenance_record(self, record: MaintenanceRecord) -> bool:
        """Add historical maintenance record for model training"""
        try:
            self.historical_data.append(record)
            
            # Retrain models periodically
            if len(self.historical_data) % 50 == 0:
                self._retrain_models()
            
            self.logger.info(f"Added maintenance record: {record.record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add maintenance record: {str(e)}")
            return False

    def add_equipment_data(self, equipment: EquipmentData) -> bool:
        """Add equipment data for predictive analysis"""
        try:
            self.equipment_database[equipment.equipment_id] = equipment
            self.logger.info(f"Added equipment data: {equipment.equipment_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add equipment data: {str(e)}")
            return False

    def predict_maintenance_needs(self, property_id: int, 
                                prediction_days: int = None) -> List[MaintenancePrediction]:
        """Predict maintenance needs for a property"""
        try:
            prediction_days = prediction_days or self.config['prediction_horizon_days']
            
            self.logger.info(f"Predicting maintenance needs for property {property_id}")
            
            # Get property equipment and historical data
            property_equipment = self._get_property_equipment(property_id)
            property_history = self._get_property_maintenance_history(property_id)
            
            predictions = []
            
            # Generate predictions for each maintenance type
            for maintenance_type in MaintenanceType:
                prediction = self._predict_single_maintenance_type(
                    property_id, maintenance_type, property_equipment, 
                    property_history, prediction_days
                )
                
                if prediction:
                    predictions.append(prediction)
            
            # Sort by predicted date and priority
            predictions.sort(key=lambda x: (x.predicted_date, x.recommended_priority.value))
            
            self.logger.info(f"Generated {len(predictions)} predictions for property {property_id}")
            return predictions
            
        except Exception as e:
            self.logger.error(f"Failed to predict maintenance needs: {str(e)}")
            return []

    def _predict_single_maintenance_type(self, property_id: int, maintenance_type: MaintenanceType,
                                       equipment_list: List[EquipmentData],
                                       history: List[MaintenanceRecord],
                                       prediction_days: int) -> Optional[MaintenancePrediction]:
        """Predict maintenance for a specific type"""
        try:
            # Filter relevant equipment and history
            relevant_equipment = [e for e in equipment_list if e.equipment_type == maintenance_type]
            relevant_history = [h for h in history if h.maintenance_type == maintenance_type]
            
            if self.sklearn_available and len(self.historical_data) >= 50:
                return self._ml_based_prediction(
                    property_id, maintenance_type, relevant_equipment, relevant_history, prediction_days
                )
            else:
                return self._rule_based_prediction(
                    property_id, maintenance_type, relevant_equipment, relevant_history, prediction_days
                )
                
        except Exception as e:
            self.logger.error(f"Failed to predict {maintenance_type.value} maintenance: {str(e)}")
            return None

    def _ml_based_prediction(self, property_id: int, maintenance_type: MaintenanceType,
                           equipment_list: List[EquipmentData], history: List[MaintenanceRecord],
                           prediction_days: int) -> Optional[MaintenancePrediction]:
        """Generate ML-based maintenance prediction"""
        try:
            # Feature engineering
            features = self._extract_features_for_prediction(
                property_id, maintenance_type, equipment_list, history
            )
            
            if not features:
                return None
            
            model_key = f'{maintenance_type.value}_time'
            cost_model_key = f'{maintenance_type.value}_cost'
            
            if model_key not in self.models:
                return None
            
            # Prepare feature vector
            feature_vector = np.array([features]).reshape(1, -1)
            
            # Scale features if scaler is trained
            scaler_key = maintenance_type.value
            if scaler_key in self.scalers and hasattr(self.scalers[scaler_key], 'mean_'):
                feature_vector = self.scalers[scaler_key].transform(feature_vector)
            
            # Predict days until maintenance
            days_until = self.models[model_key].predict(feature_vector)[0]
            predicted_date = datetime.now() + timedelta(days=max(1, int(days_until)))
            
            # Predict cost
            estimated_cost_center = self.models[cost_model_key].predict(feature_vector)[0]
            cost_range = self._calculate_cost_range(maintenance_type, estimated_cost_center)
            
            # Calculate confidence based on model performance and data quality
            confidence_score = self._calculate_prediction_confidence(
                maintenance_type, features, len(history)
            )
            confidence = self._score_to_confidence_level(confidence_score)
            
            # Determine priority based on urgency and impact
            priority = self._calculate_maintenance_priority(
                maintenance_type, days_until, estimated_cost_center, equipment_list
            )
            
            # Generate risk factors and recommendations
            risk_factors = self._analyze_risk_factors(
                maintenance_type, equipment_list, history, features
            )
            
            return MaintenancePrediction(
                property_id=property_id,
                equipment_id=equipment_list[0].equipment_id if equipment_list else None,
                maintenance_type=maintenance_type,
                predicted_date=predicted_date,
                confidence=confidence,
                confidence_score=confidence_score,
                risk_factors=risk_factors,
                estimated_cost=cost_range,
                estimated_duration=self._estimate_duration(maintenance_type, estimated_cost_center),
                recommended_priority=priority,
                reason=self._generate_prediction_reason(maintenance_type, days_until, risk_factors),
                preventive_actions=self._get_preventive_actions(maintenance_type),
                warning_signs=self._get_warning_signs(maintenance_type),
                cost_impact_if_delayed=estimated_cost_center * self.config['cost_escalation_factor'],
                optimal_scheduling_window=self._calculate_optimal_window(predicted_date),
                model_version="ml_v1.0",
                prediction_timestamp=datetime.now(),
                data_sources=['historical_records', 'equipment_data', 'ml_model']
            )
            
        except Exception as e:
            self.logger.error(f"ML-based prediction failed: {str(e)}")
            return None

    def _rule_based_prediction(self, property_id: int, maintenance_type: MaintenanceType,
                             equipment_list: List[EquipmentData], history: List[MaintenanceRecord],
                             prediction_days: int) -> Optional[MaintenancePrediction]:
        """Generate rule-based maintenance prediction"""
        try:
            # Get standard interval for this maintenance type
            standard_interval = self.config['maintenance_intervals'][maintenance_type]
            
            # Find last maintenance of this type
            last_maintenance = None
            if history:
                relevant_history = [h for h in history if h.maintenance_type == maintenance_type]
                if relevant_history:
                    last_maintenance = max(relevant_history, key=lambda x: x.completion_date)
            
            # Calculate days since last maintenance
            if last_maintenance:
                days_since_last = (datetime.now() - last_maintenance.completion_date).days
                days_until_next = max(1, standard_interval - days_since_last)
            else:
                # No history, use average based on equipment age
                if equipment_list:
                    avg_age = sum((datetime.now() - e.installation_date).days 
                                for e in equipment_list) / len(equipment_list)
                    days_until_next = max(30, int(standard_interval - (avg_age % standard_interval)))
                else:
                    days_until_next = standard_interval // 2
            
            # Adjust based on property characteristics
            days_until_next = self._adjust_for_property_factors(
                days_until_next, property_id, maintenance_type, equipment_list, history
            )
            
            predicted_date = datetime.now() + timedelta(days=days_until_next)
            
            # Estimate costs
            cost_range = self.config['cost_ranges'][maintenance_type]
            
            # Calculate confidence (lower for rule-based)
            confidence_score = 0.6 if history else 0.4
            confidence = self._score_to_confidence_level(confidence_score)
            
            # Determine priority
            if days_until_next <= 7:
                priority = MaintenancePriority.CRITICAL
            elif days_until_next <= 30:
                priority = MaintenancePriority.HIGH
            elif days_until_next <= 90:
                priority = MaintenancePriority.MEDIUM
            else:
                priority = MaintenancePriority.LOW
            
            return MaintenancePrediction(
                property_id=property_id,
                equipment_id=equipment_list[0].equipment_id if equipment_list else None,
                maintenance_type=maintenance_type,
                predicted_date=predicted_date,
                confidence=confidence,
                confidence_score=confidence_score,
                risk_factors=self._get_default_risk_factors(maintenance_type),
                estimated_cost=cost_range,
                estimated_duration=self._get_default_duration(maintenance_type),
                recommended_priority=priority,
                reason=f"Based on {standard_interval}-day maintenance interval",
                preventive_actions=self._get_preventive_actions(maintenance_type),
                warning_signs=self._get_warning_signs(maintenance_type),
                cost_impact_if_delayed=cost_range[1] * self.config['cost_escalation_factor'],
                optimal_scheduling_window=self._calculate_optimal_window(predicted_date),
                model_version="rule_v1.0",
                prediction_timestamp=datetime.now(),
                data_sources=['maintenance_intervals', 'historical_patterns']
            )
            
        except Exception as e:
            self.logger.error(f"Rule-based prediction failed: {str(e)}")
            return None

    def optimize_maintenance_schedule(self, property_ids: List[int], 
                                    optimization_period_days: int = 365) -> List[OptimizationRecommendation]:
        """Optimize maintenance schedules across multiple properties"""
        try:
            self.logger.info(f"Optimizing maintenance schedules for {len(property_ids)} properties")
            
            recommendations = []
            optimization_start = datetime.now()
            optimization_end = optimization_start + timedelta(days=optimization_period_days)
            
            for property_id in property_ids:
                # Get predictions for this property
                predictions = self.predict_maintenance_needs(property_id, optimization_period_days)
                
                # Generate optimization recommendations
                optimization = self._optimize_single_property_schedule(
                    property_id, predictions, optimization_start, optimization_end
                )
                
                recommendations.append(optimization)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to optimize maintenance schedules: {str(e)}")
            return []

    def _optimize_single_property_schedule(self, property_id: int, 
                                         predictions: List[MaintenancePrediction],
                                         start_date: datetime, end_date: datetime) -> OptimizationRecommendation:
        """Optimize maintenance schedule for a single property"""
        try:
            total_cost = sum((p.estimated_cost[0] + p.estimated_cost[1]) / 2 for p in predictions)
            
            # Group maintenance by optimal timing
            grouped_maintenance = self._group_maintenance_optimally(predictions)
            
            # Calculate potential savings
            cost_savings = self._calculate_optimization_savings(predictions, grouped_maintenance)
            
            # Generate specific recommendations
            optimization_recommendations = []
            
            for group in grouped_maintenance:
                recommendation = {
                    'scheduled_date': group['optimal_date'],
                    'maintenance_items': [
                        {
                            'type': p.maintenance_type.value,
                            'priority': p.recommended_priority.value,
                            'estimated_cost': p.estimated_cost,
                            'duration': p.estimated_duration
                        } for p in group['predictions']
                    ],
                    'total_group_cost': sum((p.estimated_cost[0] + p.estimated_cost[1]) / 2 
                                          for p in group['predictions']),
                    'efficiency_gain': group['efficiency_gain'],
                    'reason': group['reason']
                }
                optimization_recommendations.append(recommendation)
            
            return OptimizationRecommendation(
                property_id=property_id,
                optimization_period=(start_date, end_date),
                total_predicted_cost=total_cost,
                recommendations=optimization_recommendations,
                cost_savings_potential=cost_savings,
                efficiency_improvements={
                    'schedule_conflicts_reduced': len(predictions) - len(grouped_maintenance),
                    'contractor_visits_optimized': self._calculate_visit_optimization(predictions),
                    'downtime_minimized': self._calculate_downtime_reduction(grouped_maintenance)
                },
                resource_requirements=self._calculate_resource_requirements(predictions)
            )
            
        except Exception as e:
            self.logger.error(f"Single property optimization failed: {str(e)}")
            return OptimizationRecommendation(
                property_id=property_id,
                optimization_period=(start_date, end_date),
                total_predicted_cost=0,
                recommendations=[],
                cost_savings_potential=0,
                efficiency_improvements={},
                resource_requirements={}
            )

    def get_maintenance_insights(self, property_id: int) -> Dict[str, Any]:
        """Get comprehensive maintenance insights for a property"""
        try:
            # Get predictions
            predictions = self.predict_maintenance_needs(property_id)
            
            # Analyze trends
            history = self._get_property_maintenance_history(property_id)
            trends = self._analyze_maintenance_trends(history)
            
            # Calculate metrics
            metrics = self._calculate_maintenance_metrics(property_id, history, predictions)
            
            insights = {
                'property_id': property_id,
                'analysis_date': datetime.now().isoformat(),
                'upcoming_maintenance': [
                    {
                        'type': p.maintenance_type.value,
                        'predicted_date': p.predicted_date.isoformat(),
                        'priority': p.recommended_priority.value,
                        'confidence': p.confidence.value,
                        'estimated_cost_range': p.estimated_cost
                    } for p in predictions[:5]  # Top 5 most urgent
                ],
                'trends': trends,
                'metrics': metrics,
                'recommendations': {
                    'immediate_actions': [
                        p.preventive_actions for p in predictions 
                        if p.recommended_priority in [MaintenancePriority.CRITICAL, MaintenancePriority.HIGH]
                    ],
                    'cost_optimization': self._get_cost_optimization_suggestions(predictions),
                    'preventive_focus_areas': self._identify_preventive_focus_areas(history, predictions)
                }
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate maintenance insights: {str(e)}")
            return {'error': str(e)}

    # Helper methods (implementation details)
    def _extract_features_for_prediction(self, property_id: int, maintenance_type: MaintenanceType,
                                       equipment_list: List[EquipmentData], 
                                       history: List[MaintenanceRecord]) -> List[float]:
        """Extract features for ML prediction"""
        features = []
        
        try:
            # Time-based features
            current_date = datetime.now()
            
            # Equipment age features
            if equipment_list:
                avg_equipment_age = sum(
                    (current_date - e.installation_date).days 
                    for e in equipment_list
                ) / len(equipment_list)
                features.extend([
                    avg_equipment_age,
                    len(equipment_list),
                    sum(e.operating_hours for e in equipment_list) / len(equipment_list)
                ])
            else:
                features.extend([0, 0, 0])
            
            # Historical maintenance features
            if history:
                avg_cost = sum(h.cost for h in history) / len(history)
                avg_duration = sum(h.duration_hours for h in history) / len(history)
                last_maintenance_days = (current_date - max(h.completion_date for h in history)).days
                
                features.extend([
                    avg_cost,
                    avg_duration,
                    last_maintenance_days,
                    len(history)
                ])
            else:
                features.extend([0, 0, 365, 0])  # Default values
            
            # Seasonal features
            features.extend([
                current_date.month,
                current_date.weekday(),
                int(current_date.month in [6, 7, 8])  # Summer flag
            ])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {str(e)}")
            return []

    def _get_property_equipment(self, property_id: int) -> List[EquipmentData]:
        """Get equipment data for a property from database"""
        try:
            # Import database service
            from database_service import get_database_service
            db_service = get_database_service()
            
            # Query equipment from database
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if equipment table exists, create if not
                if db_service.is_postgres:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS property_equipment (
                            id SERIAL PRIMARY KEY,
                            property_id INTEGER NOT NULL,
                            equipment_id VARCHAR(255) UNIQUE NOT NULL,
                            equipment_type VARCHAR(50) NOT NULL,
                            brand VARCHAR(255),
                            model VARCHAR(255),
                            installation_date TIMESTAMP,
                            warranty_expiry TIMESTAMP,
                            last_service_date TIMESTAMP,
                            operating_hours INTEGER DEFAULT 0,
                            energy_consumption FLOAT DEFAULT 0.0,
                            performance_metrics TEXT,
                            sensor_readings TEXT,
                            maintenance_history TEXT,
                            replacement_cost FLOAT DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Query equipment for property
                    cursor.execute("""
                        SELECT * FROM property_equipment 
                        WHERE property_id = %s
                        ORDER BY installation_date DESC
                    """, (property_id,))
                else:
                    # SQLite
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS property_equipment (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            property_id INTEGER NOT NULL,
                            equipment_id TEXT UNIQUE NOT NULL,
                            equipment_type TEXT NOT NULL,
                            brand TEXT,
                            model TEXT,
                            installation_date TEXT,
                            warranty_expiry TEXT,
                            last_service_date TEXT,
                            operating_hours INTEGER DEFAULT 0,
                            energy_consumption REAL DEFAULT 0.0,
                            performance_metrics TEXT,
                            sensor_readings TEXT,
                            maintenance_history TEXT,
                            replacement_cost REAL DEFAULT 0.0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cursor.execute("""
                        SELECT * FROM property_equipment 
                        WHERE property_id = ?
                        ORDER BY installation_date DESC
                    """, (property_id,))
                
                conn.commit()
                rows = cursor.fetchall()
                
                # Convert rows to EquipmentData objects
                equipment_list = []
                for row in rows:
                    try:
                        # Parse JSON fields
                        performance_metrics = json.loads(row[11] or '{}')
                        sensor_readings = json.loads(row[12] or '{}')
                        maintenance_history = json.loads(row[13] or '[]')
                        
                        # Parse dates (handle both string and datetime objects)
                        if isinstance(row[6], datetime):
                            installation_date = row[6]
                        elif row[6]:
                            installation_date = datetime.fromisoformat(row[6])
                        else:
                            installation_date = datetime.now()
                            
                        if isinstance(row[7], datetime):
                            warranty_expiry = row[7]
                        elif row[7]:
                            warranty_expiry = datetime.fromisoformat(row[7])
                        else:
                            warranty_expiry = None
                            
                        if isinstance(row[8], datetime):
                            last_service_date = row[8]
                        elif row[8]:
                            last_service_date = datetime.fromisoformat(row[8])
                        else:
                            last_service_date = None
                        
                        equipment = EquipmentData(
                            equipment_id=row[2],
                            property_id=row[1],
                            equipment_type=MaintenanceType(row[3]),
                            brand=row[4] or "Unknown",
                            model=row[5] or "Unknown",
                            installation_date=installation_date,
                            warranty_expiry=warranty_expiry,
                            last_service_date=last_service_date,
                            service_intervals=[],  # Could be expanded
                            operating_hours=row[9] or 0,
                            energy_consumption=row[10] or 0.0,
                            performance_metrics=performance_metrics,
                            sensor_readings=sensor_readings,
                            maintenance_history=maintenance_history,
                            replacement_cost=row[14] or 0.0
                        )
                        equipment_list.append(equipment)
                    except Exception as e:
                        self.logger.warning(f"Error parsing equipment data: {e}")
                        continue
                
                return equipment_list
                
        except Exception as e:
            self.logger.error(f"Error fetching equipment data: {e}")
            # Fallback to in-memory data
            return [eq for eq in self.equipment_database.values() if eq.property_id == property_id]

    def _get_property_maintenance_history(self, property_id: int) -> List[MaintenanceRecord]:
        """Get maintenance history for a property from database"""
        try:
            # Import database service
            from database_service import get_database_service
            db_service = get_database_service()
            
            # Query maintenance history from database
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if maintenance_requests table exists, create if not
                if db_service.is_postgres:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS maintenance_history (
                            id SERIAL PRIMARY KEY,
                            property_id INTEGER NOT NULL,
                            equipment_id VARCHAR(255),
                            maintenance_type VARCHAR(50) NOT NULL,
                            description TEXT,
                            completed_date TIMESTAMP,
                            cost FLOAT DEFAULT 0.0,
                            priority VARCHAR(20) DEFAULT 'MEDIUM',
                            contractor VARCHAR(255),
                            parts_replaced TEXT,
                            issue_severity INTEGER DEFAULT 5,
                            customer_satisfaction INTEGER DEFAULT 5,
                            weather_conditions VARCHAR(100),
                            equipment_age_years FLOAT DEFAULT 0.0,
                            last_maintenance_days INTEGER DEFAULT 0,
                            property_age_years INTEGER DEFAULT 0,
                            tenant_reported BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Query maintenance history for property (last 2 years)
                    cursor.execute("""
                        SELECT * FROM maintenance_history 
                        WHERE property_id = %s 
                        AND completed_date >= %s
                        ORDER BY completed_date DESC
                        LIMIT 100
                    """, (property_id, datetime.now() - timedelta(days=730)))
                else:
                    # SQLite  
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS maintenance_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            property_id INTEGER NOT NULL,
                            equipment_id TEXT,
                            maintenance_type TEXT NOT NULL,
                            description TEXT,
                            completed_date TEXT,
                            cost REAL DEFAULT 0.0,
                            priority TEXT DEFAULT 'MEDIUM',
                            contractor TEXT,
                            parts_replaced TEXT,
                            issue_severity INTEGER DEFAULT 5,
                            customer_satisfaction INTEGER DEFAULT 5,
                            weather_conditions TEXT,
                            equipment_age_years REAL DEFAULT 0.0,
                            last_maintenance_days INTEGER DEFAULT 0,
                            property_age_years INTEGER DEFAULT 0,
                            tenant_reported INTEGER DEFAULT 0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cursor.execute("""
                        SELECT * FROM maintenance_history 
                        WHERE property_id = ?
                        AND datetime(completed_date) >= datetime('now', '-730 days')
                        ORDER BY completed_date DESC
                        LIMIT 100
                    """, (property_id,))
                
                conn.commit()
                rows = cursor.fetchall()
                
                # Convert rows to MaintenanceRecord objects
                history_list = []
                for row in rows:
                    try:
                        # Parse date (handle both string and datetime objects)
                        if isinstance(row[5], datetime):
                            completed_date = row[5]
                        elif row[5]:
                            completed_date = datetime.fromisoformat(row[5])
                        else:
                            completed_date = datetime.now()
                        
                        # Parse parts replaced
                        parts_replaced = json.loads(row[9]) if row[9] and row[9].startswith('[') else [row[9]] if row[9] else []
                        
                        record = MaintenanceRecord(
                            record_id=f"MR_{row[0]}",  # Use database ID
                            property_id=row[1],
                            maintenance_type=MaintenanceType(row[3]),
                            description=row[4] or "",
                            cost=row[6] or 0.0,
                            completion_date=completed_date,
                            duration_hours=random.randint(1, 8),  # Estimated duration
                            priority=MaintenancePriority(row[7].lower()) if row[7] else MaintenancePriority.MEDIUM,
                            contractor=row[8] or "Unknown",
                            parts_replaced=parts_replaced,
                            issue_severity=row[10] or 5,
                            customer_satisfaction=row[11] or 5,
                            weather_conditions=row[12] or "Unknown",
                            equipment_age_years=row[13] or 0.0,
                            last_maintenance_days=row[14] or 0,
                            property_age_years=row[15] or 0,
                            tenant_reported=bool(row[16]) if row[16] is not None else False
                        )
                        history_list.append(record)
                    except Exception as e:
                        self.logger.warning(f"Error parsing maintenance record: {e}")
                        continue
                
                return history_list
                
        except Exception as e:
            self.logger.error(f"Error fetching maintenance history: {e}")
            # Fallback to in-memory data
            return [rec for rec in self.historical_data if rec.property_id == property_id]

    def _score_to_confidence_level(self, score: float) -> PredictionConfidence:
        """Convert confidence score to confidence level"""
        thresholds = self.config['confidence_thresholds']
        
        if score >= thresholds['very_high']:
            return PredictionConfidence.VERY_HIGH
        elif score >= thresholds['high']:
            return PredictionConfidence.HIGH
        elif score >= thresholds['medium']:
            return PredictionConfidence.MEDIUM
        elif score >= thresholds['low']:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW

    def _get_preventive_actions(self, maintenance_type: MaintenanceType) -> List[str]:
        """Get preventive actions for maintenance type"""
        actions = {
            MaintenanceType.HVAC: [
                "Change air filters monthly",
                "Clean air vents and ducts",
                "Check thermostat settings",
                "Inspect for unusual noises"
            ],
            MaintenanceType.PLUMBING: [
                "Check for leaks regularly",
                "Clear drain traps",
                "Inspect water pressure",
                "Test shut-off valves"
            ],
            MaintenanceType.ELECTRICAL: [
                "Test circuit breakers",
                "Inspect electrical panels",
                "Check outlet functionality",
                "Replace old wiring"
            ]
        }
        
        return actions.get(maintenance_type, ["Regular inspection recommended"])

    def _get_warning_signs(self, maintenance_type: MaintenanceType) -> List[str]:
        """Get warning signs for maintenance type"""
        signs = {
            MaintenanceType.HVAC: [
                "Unusual noises or vibrations",
                "Poor air circulation",
                "Higher energy bills",
                "Inconsistent temperatures"
            ],
            MaintenanceType.PLUMBING: [
                "Slow drains",
                "Water stains or damage",
                "Unusual odors",
                "Low water pressure"
            ],
            MaintenanceType.ELECTRICAL: [
                "Flickering lights",
                "Burning smells",
                "Frequent circuit breaker trips",
                "Warm outlets or switches"
            ]
        }
        
        return signs.get(maintenance_type, ["General wear and deterioration"])

    def save_models(self, file_path: str) -> bool:
        """Save trained models to disk"""
        try:
            if not JOBLIB_AVAILABLE:
                with open(file_path, 'wb') as f:
                    pickle.dump({
                        'models': self.models,
                        'scalers': self.scalers,
                        'encoders': self.encoders,
                        'config': self.config
                    }, f)
            else:
                joblib.dump({
                    'models': self.models,
                    'scalers': self.scalers,
                    'encoders': self.encoders,
                    'config': self.config
                }, file_path)
            
            self.logger.info(f"Models saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save models: {str(e)}")
            return False

    def load_models(self, file_path: str) -> bool:
        """Load trained models from disk"""
        try:
            if not os.path.exists(file_path):
                return False
                
            if not JOBLIB_AVAILABLE:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                data = joblib.load(file_path)
            
            self.models = data.get('models', {})
            self.scalers = data.get('scalers', {})
            self.encoders = data.get('encoders', {})
            
            self.logger.info(f"Models loaded from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load models: {str(e)}")
            return False

    def _retrain_models(self):
        """Retrain ML models with new data"""
        try:
            if not self.sklearn_available or len(self.historical_data) < 50:
                return False
            
            self.logger.info("Retraining ML models with updated data")
            
            for maintenance_type in MaintenanceType:
                # Filter relevant data
                type_data = [r for r in self.historical_data if r.maintenance_type == maintenance_type]
                
                if len(type_data) < 10:  # Need minimum data for training
                    continue
                
                # Prepare training data (simplified feature extraction)
                X = []
                y_cost = []
                y_time = []
                
                for record in type_data:
                    features = [
                        record.equipment_age_years,
                        record.last_maintenance_days,
                        record.property_age_years,
                        record.issue_severity,
                        1 if record.tenant_reported else 0
                    ]
                    X.append(features)
                    y_cost.append(record.cost)
                    y_time.append(record.duration_hours)
                
                if len(X) >= 10:
                    X = np.array(X)
                    y_cost = np.array(y_cost)
                    y_time = np.array(y_time)
                    
                    # Train cost prediction model
                    cost_model = self.models.get(f'{maintenance_type.value}_cost')
                    if cost_model:
                        cost_model.fit(X, y_cost)
                    
                    # Train time prediction model
                    time_model = self.models.get(f'{maintenance_type.value}_time')
                    if time_model:
                        time_model.fit(X, y_time)
                    
                    # Train scaler
                    scaler = self.scalers.get(maintenance_type.value)
                    if scaler:
                        scaler.fit(X)
            
            self.logger.info("Model retraining completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Model retraining failed: {str(e)}")
            return False

    def _calculate_cost_range(self, maintenance_type: MaintenanceType, center_cost: float) -> Tuple[float, float]:
        """Calculate cost range around predicted center value"""
        base_range = self.config['cost_ranges'].get(maintenance_type, (100, 1000))
        
        if center_cost > 0:
            # Use predicted cost as center with ±25% variation
            min_cost = max(base_range[0], center_cost * 0.75)
            max_cost = min(base_range[1] * 2, center_cost * 1.25)
        else:
            min_cost, max_cost = base_range
        
        return (min_cost, max_cost)

    def _calculate_prediction_confidence(self, maintenance_type: MaintenanceType, 
                                       features: List[float], history_count: int) -> float:
        """Calculate confidence score for predictions"""
        base_confidence = 0.5
        
        # Increase confidence with more historical data
        data_confidence = min(0.4, history_count * 0.02)
        
        # Increase confidence for well-established maintenance types
        type_confidence = 0.1 if maintenance_type in [MaintenanceType.HVAC, MaintenanceType.PLUMBING] else 0.05
        
        # Feature quality confidence (simplified)
        feature_confidence = 0.1 if all(f > 0 for f in features) else 0.05
        
        total_confidence = base_confidence + data_confidence + type_confidence + feature_confidence
        return min(0.95, max(0.1, total_confidence))

    def _calculate_maintenance_priority(self, maintenance_type: MaintenanceType, 
                                      days_until: float, cost: float, 
                                      equipment_list: List[EquipmentData]) -> MaintenancePriority:
        """Calculate maintenance priority based on multiple factors"""
        if days_until <= 7:
            return MaintenancePriority.CRITICAL
        elif days_until <= 14:
            return MaintenancePriority.HIGH
        elif days_until <= 30:
            return MaintenancePriority.MEDIUM
        elif days_until <= 90:
            return MaintenancePriority.LOW
        else:
            return MaintenancePriority.LOW

    def _analyze_risk_factors(self, maintenance_type: MaintenanceType,
                            equipment_list: List[EquipmentData],
                            history: List[MaintenanceRecord],
                            features: List[float]) -> Dict[str, float]:
        """Analyze risk factors for maintenance prediction"""
        risk_factors = {}
        
        # Age-based risk
        if equipment_list:
            avg_age = sum((datetime.now() - e.installation_date).days / 365.25 for e in equipment_list) / len(equipment_list)
            risk_factors['equipment_age_risk'] = min(1.0, avg_age / 20.0)  # Normalize to 20 years
        
        # Historical frequency risk
        if history:
            avg_interval = sum(
                (history[i].completion_date - history[i-1].completion_date).days 
                for i in range(1, len(history))
            ) / max(1, len(history) - 1) if len(history) > 1 else 365
            
            expected_interval = self.config['maintenance_intervals'][maintenance_type]
            risk_factors['frequency_risk'] = max(0.1, min(1.0, expected_interval / avg_interval))
        
        # Cost escalation risk
        if history:
            recent_costs = [h.cost for h in history[-5:]]  # Last 5 records
            if len(recent_costs) >= 2:
                cost_trend = (recent_costs[-1] - recent_costs[0]) / recent_costs[0]
                risk_factors['cost_escalation_risk'] = max(0.0, min(1.0, cost_trend))
        
        return risk_factors

    def _generate_prediction_reason(self, maintenance_type: MaintenanceType, 
                                  days_until: float, risk_factors: Dict[str, float]) -> str:
        """Generate human-readable reason for maintenance prediction"""
        primary_risk = max(risk_factors.items(), key=lambda x: x[1]) if risk_factors else ('general', 0.5)
        
        if days_until <= 30:
            return f"Urgent {maintenance_type.value.replace('_', ' ')} maintenance needed due to {primary_risk[0].replace('_', ' ')}"
        elif days_until <= 90:
            return f"Scheduled {maintenance_type.value.replace('_', ' ')} maintenance recommended based on {primary_risk[0].replace('_', ' ')}"
        else:
            return f"Routine {maintenance_type.value.replace('_', ' ')} maintenance planned based on standard intervals"

    def _estimate_duration(self, maintenance_type: MaintenanceType, cost: float) -> int:
        """Estimate maintenance duration in hours"""
        duration_map = {
            MaintenanceType.HVAC: 4,
            MaintenanceType.PLUMBING: 3,
            MaintenanceType.ELECTRICAL: 2,
            MaintenanceType.APPLIANCE: 2,
            MaintenanceType.STRUCTURAL: 8,
            MaintenanceType.ROOFING: 6,
            MaintenanceType.FLOORING: 4,
            MaintenanceType.PAINTING: 6,
            MaintenanceType.LANDSCAPING: 2,
            MaintenanceType.SECURITY: 1
        }
        
        base_duration = duration_map.get(maintenance_type, 4)
        
        # Adjust duration based on cost (higher cost = more complex work)
        if cost > 1000:
            return int(base_duration * 1.5)
        elif cost > 500:
            return int(base_duration * 1.2)
        else:
            return base_duration

    def _calculate_optimal_window(self, predicted_date: datetime) -> Tuple[datetime, datetime]:
        """Calculate optimal scheduling window around predicted date"""
        # Allow ±7 days around predicted date for optimal scheduling
        start_window = predicted_date - timedelta(days=7)
        end_window = predicted_date + timedelta(days=7)
        
        # Ensure window doesn't go into the past
        if start_window < datetime.now():
            start_window = datetime.now()
            end_window = start_window + timedelta(days=14)
        
        return (start_window, end_window)

    def _adjust_for_property_factors(self, base_days: int, property_id: int, 
                                   maintenance_type: MaintenanceType,
                                   equipment_list: List[EquipmentData], 
                                   history: List[MaintenanceRecord]) -> int:
        """Adjust prediction based on property-specific factors"""
        adjusted_days = base_days
        
        # Adjust for equipment age
        if equipment_list:
            avg_age_years = sum(
                (datetime.now() - e.installation_date).days / 365.25 
                for e in equipment_list
            ) / len(equipment_list)
            
            if avg_age_years > 10:
                adjusted_days = int(adjusted_days * 0.8)  # Older equipment needs more frequent maintenance
            elif avg_age_years < 2:
                adjusted_days = int(adjusted_days * 1.2)  # Newer equipment can wait longer
        
        # Adjust for historical maintenance frequency
        if len(history) >= 3:
            # Calculate average interval between maintenance
            intervals = []
            for i in range(1, len(history)):
                days_diff = (history[i].completion_date - history[i-1].completion_date).days
                intervals.append(days_diff)
            
            avg_interval = sum(intervals) / len(intervals)
            standard_interval = self.config['maintenance_intervals'][maintenance_type]
            
            # If property historically needs more frequent maintenance
            if avg_interval < standard_interval * 0.8:
                adjusted_days = int(adjusted_days * 0.9)
            elif avg_interval > standard_interval * 1.2:
                adjusted_days = int(adjusted_days * 1.1)
        
        return max(1, adjusted_days)  # Ensure at least 1 day

    def _get_default_risk_factors(self, maintenance_type: MaintenanceType) -> Dict[str, float]:
        """Get default risk factors when no historical data is available"""
        return {
            'equipment_age_risk': 0.3,
            'frequency_risk': 0.2,
            'seasonal_risk': 0.1,
            'general_wear_risk': 0.4
        }

    def _get_default_duration(self, maintenance_type: MaintenanceType) -> int:
        """Get default duration for maintenance type"""
        return self._estimate_duration(maintenance_type, 500)  # Use average cost for duration estimate

# Global predictive maintenance AI instance
_predictive_maintenance_ai = None

def get_predictive_maintenance_ai():
    """Get the global predictive maintenance AI instance"""
    global _predictive_maintenance_ai
    if _predictive_maintenance_ai is None:
        _predictive_maintenance_ai = PredictiveMaintenanceAI()
    return _predictive_maintenance_ai