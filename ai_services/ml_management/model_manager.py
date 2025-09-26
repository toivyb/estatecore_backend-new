#!/usr/bin/env python3
"""
ML Model Management System for EstateCore Phase 7D
Comprehensive model lifecycle management, monitoring, and deployment
"""

import os
import json
import logging
import asyncio
import pickle
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
import uuid
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
from sklearn.model_selection import train_test_split
import warnings

# Suppress sklearn warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"
    DEEP_LEARNING = "deep_learning"

class ModelStatus(Enum):
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DEPRECATED = "deprecated"
    TESTING = "testing"

class DeploymentEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    A_B_TEST = "a_b_test"

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mse: float
    rmse: float
    mae: float
    r2_score: float
    training_time: float
    inference_time: float
    memory_usage: float
    data_drift_score: float

@dataclass
class ModelVersion:
    """Model version information"""
    version_id: str
    model_id: str
    version_number: str
    created_at: datetime
    created_by: str
    model_file_path: str
    config: Dict[str, Any]
    metrics: ModelMetrics
    status: ModelStatus
    deployment_env: Optional[DeploymentEnvironment]
    notes: str

@dataclass
class MLModel:
    """Machine learning model information"""
    model_id: str
    name: str
    description: str
    model_type: ModelType
    framework: str
    current_version: str
    created_at: datetime
    last_updated: datetime
    created_by: str
    use_case: str
    data_sources: List[str]
    feature_schema: Dict[str, str]
    target_variable: str
    versions: List[ModelVersion]
    tags: List[str]
    is_active: bool

@dataclass
class ModelDeployment:
    """Model deployment information"""
    deployment_id: str
    model_id: str
    version_id: str
    environment: DeploymentEnvironment
    endpoint_url: str
    deployed_at: datetime
    deployed_by: str
    status: str
    traffic_percentage: float
    health_status: str
    last_health_check: datetime
    resource_usage: Dict[str, Any]

@dataclass
class ModelPerformanceAlert:
    """Model performance monitoring alert"""
    alert_id: str
    model_id: str
    alert_type: str
    severity: str
    message: str
    metric_name: str
    threshold_value: float
    actual_value: float
    created_at: datetime
    resolved: bool
    resolved_at: Optional[datetime]

class MLModelManager:
    """Comprehensive ML model management system"""
    
    def __init__(self, database_path: str = "ml_models.db", models_directory: str = "models"):
        self.database_path = database_path
        self.models_directory = models_directory
        self.models: Dict[str, MLModel] = {}
        self.deployments: Dict[str, ModelDeployment] = {}
        self.monitoring_active = False
        
        # Create models directory
        os.makedirs(self.models_directory, exist_ok=True)
        
        self._initialize_database()
        self._load_models()
        
        logger.info("MLModelManager initialized")
    
    def _initialize_database(self):
        """Initialize model management database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_models (
                model_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                model_type TEXT NOT NULL,
                framework TEXT NOT NULL,
                current_version TEXT,
                created_at TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                created_by TEXT,
                use_case TEXT,
                data_sources TEXT,
                feature_schema TEXT,
                target_variable TEXT,
                tags TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Model versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_versions (
                version_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                version_number TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT,
                model_file_path TEXT,
                config TEXT,
                metrics TEXT,
                status TEXT NOT NULL,
                deployment_env TEXT,
                notes TEXT,
                FOREIGN KEY (model_id) REFERENCES ml_models (model_id)
            )
        """)
        
        # Model deployments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_deployments (
                deployment_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                version_id TEXT NOT NULL,
                environment TEXT NOT NULL,
                endpoint_url TEXT,
                deployed_at TEXT NOT NULL,
                deployed_by TEXT,
                status TEXT NOT NULL,
                traffic_percentage REAL DEFAULT 100.0,
                health_status TEXT DEFAULT 'healthy',
                last_health_check TEXT,
                resource_usage TEXT,
                FOREIGN KEY (model_id) REFERENCES ml_models (model_id),
                FOREIGN KEY (version_id) REFERENCES model_versions (version_id)
            )
        """)
        
        # Performance alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_alerts (
                alert_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                metric_name TEXT,
                threshold_value REAL,
                actual_value REAL,
                created_at TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0,
                resolved_at TEXT,
                FOREIGN KEY (model_id) REFERENCES ml_models (model_id)
            )
        """)
        
        # Model experiments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_experiments (
                experiment_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                experiment_name TEXT NOT NULL,
                parameters TEXT,
                metrics TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                results TEXT,
                FOREIGN KEY (model_id) REFERENCES ml_models (model_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_models(self):
        """Load existing models from database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM ml_models WHERE is_active = 1")
            models_data = cursor.fetchall()
            
            for model_row in models_data:
                model_id = model_row[0]
                
                # Load model versions
                cursor.execute("SELECT * FROM model_versions WHERE model_id = ?", (model_id,))
                versions_data = cursor.fetchall()
                
                versions = []
                for version_row in versions_data:
                    metrics_data = json.loads(version_row[8]) if version_row[8] else {}
                    metrics = ModelMetrics(**metrics_data) if metrics_data else None
                    
                    version = ModelVersion(
                        version_id=version_row[0],
                        model_id=version_row[1],
                        version_number=version_row[2],
                        created_at=datetime.fromisoformat(version_row[3]),
                        created_by=version_row[4] or "system",
                        model_file_path=version_row[5] or "",
                        config=json.loads(version_row[6]) if version_row[6] else {},
                        metrics=metrics,
                        status=ModelStatus(version_row[9]),
                        deployment_env=DeploymentEnvironment(version_row[10]) if version_row[10] else None,
                        notes=version_row[11] or ""
                    )
                    versions.append(version)
                
                # Create model object
                model = MLModel(
                    model_id=model_row[0],
                    name=model_row[1],
                    description=model_row[2] or "",
                    model_type=ModelType(model_row[3]),
                    framework=model_row[4],
                    current_version=model_row[5] or "1.0.0",
                    created_at=datetime.fromisoformat(model_row[6]),
                    last_updated=datetime.fromisoformat(model_row[7]),
                    created_by=model_row[8] or "system",
                    use_case=model_row[9] or "",
                    data_sources=json.loads(model_row[10]) if model_row[10] else [],
                    feature_schema=json.loads(model_row[11]) if model_row[11] else {},
                    target_variable=model_row[12] or "",
                    versions=versions,
                    tags=json.loads(model_row[13]) if model_row[13] else [],
                    is_active=bool(model_row[14])
                )
                
                self.models[model_id] = model
            
            conn.close()
            logger.info(f"Loaded {len(self.models)} models from database")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    async def create_model(self, name: str, description: str, model_type: ModelType,
                          framework: str, use_case: str, created_by: str = "system") -> str:
        """Create a new ML model"""
        try:
            model_id = str(uuid.uuid4())
            now = datetime.now()
            
            model = MLModel(
                model_id=model_id,
                name=name,
                description=description,
                model_type=model_type,
                framework=framework,
                current_version="1.0.0",
                created_at=now,
                last_updated=now,
                created_by=created_by,
                use_case=use_case,
                data_sources=[],
                feature_schema={},
                target_variable="",
                versions=[],
                tags=[],
                is_active=True
            )
            
            # Save to database
            await self._save_model(model)
            
            # Store in memory
            self.models[model_id] = model
            
            logger.info(f"Created new model: {name} (ID: {model_id})")
            return model_id
            
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            raise
    
    async def register_model_version(self, model_id: str, version_number: str,
                                   model_object: Any, config: Dict[str, Any],
                                   metrics: ModelMetrics, created_by: str = "system") -> str:
        """Register a new version of an existing model"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            version_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Save model object to file
            model_file_path = os.path.join(
                self.models_directory, 
                f"{model_id}_{version_number}_{version_id}.pkl"
            )
            
            with open(model_file_path, 'wb') as f:
                if hasattr(model_object, 'save'):
                    # For models with save method (like TensorFlow/Keras)
                    model_object.save(model_file_path.replace('.pkl', '.h5'))
                    model_file_path = model_file_path.replace('.pkl', '.h5')
                else:
                    # For sklearn models
                    joblib.dump(model_object, f)
            
            version = ModelVersion(
                version_id=version_id,
                model_id=model_id,
                version_number=version_number,
                created_at=now,
                created_by=created_by,
                model_file_path=model_file_path,
                config=config,
                metrics=metrics,
                status=ModelStatus.TRAINED,
                deployment_env=None,
                notes=""
            )
            
            # Update model
            model = self.models[model_id]
            model.versions.append(version)
            model.current_version = version_number
            model.last_updated = now
            
            # Save to database
            await self._save_model_version(version)
            await self._update_model(model)
            
            logger.info(f"Registered model version {version_number} for model {model_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Error registering model version: {e}")
            raise
    
    async def deploy_model(self, model_id: str, version_id: str, 
                          environment: DeploymentEnvironment,
                          deployed_by: str = "system") -> str:
        """Deploy a model version to an environment"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model = self.models[model_id]
            version = next((v for v in model.versions if v.version_id == version_id), None)
            
            if not version:
                raise ValueError(f"Version {version_id} not found for model {model_id}")
            
            deployment_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Generate endpoint URL (simulated)
            endpoint_url = f"https://api.estatecore.com/models/{model_id}/versions/{version_id}/predict"
            
            deployment = ModelDeployment(
                deployment_id=deployment_id,
                model_id=model_id,
                version_id=version_id,
                environment=environment,
                endpoint_url=endpoint_url,
                deployed_at=now,
                deployed_by=deployed_by,
                status="active",
                traffic_percentage=100.0,
                health_status="healthy",
                last_health_check=now,
                resource_usage={
                    "cpu_usage": 25.5,
                    "memory_usage": 512.0,
                    "gpu_usage": 0.0,
                    "requests_per_minute": 150
                }
            )
            
            # Update version status
            version.deployment_env = environment
            version.status = ModelStatus.DEPLOYED
            
            # Store deployment
            self.deployments[deployment_id] = deployment
            
            # Save to database
            await self._save_deployment(deployment)
            await self._save_model_version(version)
            
            logger.info(f"Deployed model {model_id} version {version_id} to {environment.value}")
            return deployment_id
            
        except Exception as e:
            logger.error(f"Error deploying model: {e}")
            raise
    
    async def get_model_performance(self, model_id: str, days: int = 30) -> Dict[str, Any]:
        """Get model performance metrics over time"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model = self.models[model_id]
            
            # Generate simulated performance data over time
            performance_data = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            for i in range(days):
                date = start_date + timedelta(days=i)
                
                # Simulate performance degradation over time
                degradation_factor = 1 - (i * 0.001)  # Small degradation
                base_accuracy = 0.85
                
                performance_data.append({
                    'date': date.isoformat(),
                    'accuracy': base_accuracy * degradation_factor + np.random.uniform(-0.02, 0.02),
                    'precision': 0.82 * degradation_factor + np.random.uniform(-0.02, 0.02),
                    'recall': 0.88 * degradation_factor + np.random.uniform(-0.02, 0.02),
                    'f1_score': 0.85 * degradation_factor + np.random.uniform(-0.02, 0.02),
                    'inference_time': 50 + np.random.uniform(-10, 20),  # ms
                    'requests_processed': np.random.randint(800, 1500),
                    'error_rate': max(0, 0.02 + i * 0.0001 + np.random.uniform(-0.005, 0.005))
                })
            
            # Calculate trends
            recent_accuracy = np.mean([p['accuracy'] for p in performance_data[-7:]])
            previous_accuracy = np.mean([p['accuracy'] for p in performance_data[-14:-7]])
            accuracy_trend = ((recent_accuracy - previous_accuracy) / previous_accuracy) * 100
            
            # Detect anomalies
            accuracies = [p['accuracy'] for p in performance_data]
            accuracy_std = np.std(accuracies)
            accuracy_mean = np.mean(accuracies)
            anomalies = [
                p for p in performance_data 
                if abs(p['accuracy'] - accuracy_mean) > 2 * accuracy_std
            ]
            
            return {
                'model_id': model_id,
                'model_name': model.name,
                'period_days': days,
                'performance_data': performance_data,
                'summary': {
                    'current_accuracy': recent_accuracy,
                    'accuracy_trend': accuracy_trend,
                    'total_requests': sum(p['requests_processed'] for p in performance_data),
                    'average_inference_time': np.mean([p['inference_time'] for p in performance_data]),
                    'error_rate': np.mean([p['error_rate'] for p in performance_data]),
                    'anomalies_detected': len(anomalies)
                },
                'alerts': await self._get_model_alerts(model_id),
                'deployments': [
                    asdict(d) for d in self.deployments.values() 
                    if d.model_id == model_id
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            raise
    
    async def get_models_overview(self) -> Dict[str, Any]:
        """Get overview of all models"""
        try:
            total_models = len(self.models)
            deployed_models = sum(1 for m in self.models.values() 
                                if any(v.status == ModelStatus.DEPLOYED for v in m.versions))
            training_models = sum(1 for m in self.models.values() 
                                if any(v.status == ModelStatus.TRAINING for v in m.versions))
            
            # Model types distribution
            type_distribution = {}
            for model in self.models.values():
                model_type = model.model_type.value
                type_distribution[model_type] = type_distribution.get(model_type, 0) + 1
            
            # Framework distribution
            framework_distribution = {}
            for model in self.models.values():
                framework = model.framework
                framework_distribution[framework] = framework_distribution.get(framework, 0) + 1
            
            # Recent activity
            recent_models = sorted(
                self.models.values(),
                key=lambda m: m.last_updated,
                reverse=True
            )[:10]
            
            # Performance summary
            total_deployments = len(self.deployments)
            healthy_deployments = sum(1 for d in self.deployments.values() 
                                    if d.health_status == "healthy")
            
            return {
                'summary': {
                    'total_models': total_models,
                    'deployed_models': deployed_models,
                    'training_models': training_models,
                    'total_deployments': total_deployments,
                    'healthy_deployments': healthy_deployments,
                    'health_percentage': (healthy_deployments / max(total_deployments, 1)) * 100
                },
                'distributions': {
                    'model_types': type_distribution,
                    'frameworks': framework_distribution
                },
                'recent_activity': [
                    {
                        'model_id': m.model_id,
                        'name': m.name,
                        'type': m.model_type.value,
                        'framework': m.framework,
                        'current_version': m.current_version,
                        'last_updated': m.last_updated.isoformat(),
                        'status': next((v.status.value for v in m.versions 
                                      if v.version_number == m.current_version), 'unknown')
                    }
                    for m in recent_models
                ],
                'alerts': await self._get_all_alerts(),
                'resource_usage': await self._get_resource_usage_summary()
            }
            
        except Exception as e:
            logger.error(f"Error getting models overview: {e}")
            raise
    
    async def run_model_experiment(self, model_id: str, experiment_name: str,
                                 parameters: Dict[str, Any]) -> str:
        """Run a model experiment with different parameters"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            experiment_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Simulate experiment execution
            await asyncio.sleep(1)  # Simulate training time
            
            # Generate simulated results
            baseline_accuracy = 0.85
            parameter_impact = sum(hash(str(v)) % 100 for v in parameters.values()) / (len(parameters) * 100)
            experiment_accuracy = min(0.99, baseline_accuracy + parameter_impact * 0.1)
            
            results = {
                'accuracy': experiment_accuracy,
                'precision': experiment_accuracy * 0.95,
                'recall': experiment_accuracy * 1.02,
                'f1_score': experiment_accuracy * 0.98,
                'training_time': np.random.uniform(300, 1800),  # seconds
                'validation_loss': np.random.uniform(0.1, 0.5),
                'convergence_epoch': np.random.randint(10, 50)
            }
            
            # Save experiment to database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO model_experiments 
                (experiment_id, model_id, experiment_name, parameters, metrics, created_at, status, results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment_id, model_id, experiment_name,
                json.dumps(parameters), json.dumps({}),
                now.isoformat(), "completed", json.dumps(results)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Completed experiment {experiment_name} for model {model_id}")
            return experiment_id
            
        except Exception as e:
            logger.error(f"Error running experiment: {e}")
            raise
    
    async def _save_model(self, model: MLModel):
        """Save model to database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO ml_models 
                (model_id, name, description, model_type, framework, current_version,
                 created_at, last_updated, created_by, use_case, data_sources,
                 feature_schema, target_variable, tags, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model.model_id, model.name, model.description, model.model_type.value,
                model.framework, model.current_version, model.created_at.isoformat(),
                model.last_updated.isoformat(), model.created_by, model.use_case,
                json.dumps(model.data_sources), json.dumps(model.feature_schema),
                model.target_variable, json.dumps(model.tags), model.is_active
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    async def _save_model_version(self, version: ModelVersion):
        """Save model version to database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            metrics_json = json.dumps(asdict(version.metrics)) if version.metrics else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO model_versions 
                (version_id, model_id, version_number, created_at, created_by,
                 model_file_path, config, metrics, status, deployment_env, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version.version_id, version.model_id, version.version_number,
                version.created_at.isoformat(), version.created_by,
                version.model_file_path, json.dumps(version.config),
                metrics_json, version.status.value,
                version.deployment_env.value if version.deployment_env else None,
                version.notes
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving model version: {e}")
            raise
    
    async def _save_deployment(self, deployment: ModelDeployment):
        """Save deployment to database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO model_deployments 
                (deployment_id, model_id, version_id, environment, endpoint_url,
                 deployed_at, deployed_by, status, traffic_percentage, health_status,
                 last_health_check, resource_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deployment.deployment_id, deployment.model_id, deployment.version_id,
                deployment.environment.value, deployment.endpoint_url,
                deployment.deployed_at.isoformat(), deployment.deployed_by,
                deployment.status, deployment.traffic_percentage,
                deployment.health_status, deployment.last_health_check.isoformat(),
                json.dumps(deployment.resource_usage)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving deployment: {e}")
            raise
    
    async def _update_model(self, model: MLModel):
        """Update existing model in database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE ml_models SET
                    current_version = ?, last_updated = ?
                WHERE model_id = ?
            """, (
                model.current_version, model.last_updated.isoformat(), model.model_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            raise
    
    async def _get_model_alerts(self, model_id: str) -> List[Dict[str, Any]]:
        """Get alerts for a specific model"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM performance_alerts 
                WHERE model_id = ? AND resolved = 0
                ORDER BY created_at DESC
                LIMIT 10
            """, (model_id,))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'alert_id': row[0],
                    'model_id': row[1],
                    'alert_type': row[2],
                    'severity': row[3],
                    'message': row[4],
                    'metric_name': row[5],
                    'threshold_value': row[6],
                    'actual_value': row[7],
                    'created_at': row[8],
                    'resolved': bool(row[9])
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting model alerts: {e}")
            return []
    
    async def _get_all_alerts(self) -> List[Dict[str, Any]]:
        """Get all unresolved alerts"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT pa.*, mm.name as model_name FROM performance_alerts pa
                JOIN ml_models mm ON pa.model_id = mm.model_id
                WHERE pa.resolved = 0
                ORDER BY pa.created_at DESC
                LIMIT 20
            """)
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'alert_id': row[0],
                    'model_id': row[1],
                    'model_name': row[10],
                    'alert_type': row[2],
                    'severity': row[3],
                    'message': row[4],
                    'created_at': row[8]
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting all alerts: {e}")
            return []
    
    async def _get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get overall resource usage summary"""
        total_cpu = sum(d.resource_usage.get('cpu_usage', 0) for d in self.deployments.values())
        total_memory = sum(d.resource_usage.get('memory_usage', 0) for d in self.deployments.values())
        total_requests = sum(d.resource_usage.get('requests_per_minute', 0) for d in self.deployments.values())
        
        return {
            'total_cpu_usage': total_cpu,
            'total_memory_usage_mb': total_memory,
            'total_requests_per_minute': total_requests,
            'active_deployments': len([d for d in self.deployments.values() if d.status == 'active'])
        }

# Global instance
_model_manager = None

def get_model_manager() -> MLModelManager:
    """Get global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = MLModelManager()
    return _model_manager

# API convenience functions
async def get_models_overview() -> Dict[str, Any]:
    """Get models overview for API"""
    manager = get_model_manager()
    return await manager.get_models_overview()

async def get_model_performance_data(model_id: str, days: int = 30) -> Dict[str, Any]:
    """Get model performance data for API"""
    manager = get_model_manager()
    return await manager.get_model_performance(model_id, days)

async def create_new_model(name: str, description: str, model_type: str,
                          framework: str, use_case: str) -> Dict[str, Any]:
    """Create new model for API"""
    manager = get_model_manager()
    model_type_enum = ModelType(model_type.lower())
    model_id = await manager.create_model(name, description, model_type_enum, framework, use_case)
    
    return {
        'model_id': model_id,
        'message': f'Model {name} created successfully'
    }

if __name__ == "__main__":
    # Test the model manager
    async def test_model_manager():
        manager = MLModelManager()
        
        print("Testing ML Model Manager")
        print("=" * 50)
        
        # Create a test model
        print("Creating test model...")
        model_id = await manager.create_model(
            name="Property Price Predictor",
            description="Predicts property prices based on location and features",
            model_type=ModelType.REGRESSION,
            framework="scikit-learn",
            use_case="Property valuation"
        )
        print(f"Created model: {model_id}")
        
        # Get overview
        print("\nGetting models overview...")
        overview = await manager.get_models_overview()
        print(f"Total models: {overview['summary']['total_models']}")
        
        print("\nML Model Manager Test Complete!")
    
    asyncio.run(test_model_manager())