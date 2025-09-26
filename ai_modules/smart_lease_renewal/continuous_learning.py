"""
Continuous Learning Engine
Background tasks for continuous learning, model retraining, and data processing
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import pickle
from pathlib import Path
import schedule
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from celery import Celery
from celery.schedules import crontab
import redis
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, mean_squared_error
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningTaskType(Enum):
    """Types of continuous learning tasks"""
    MODEL_RETRAINING = "model_retraining"
    DATA_COLLECTION = "data_collection"
    PERFORMANCE_MONITORING = "performance_monitoring"
    FEATURE_ENGINEERING = "feature_engineering"
    ANOMALY_DETECTION = "anomaly_detection"
    MARKET_ANALYSIS = "market_analysis"
    FEEDBACK_PROCESSING = "feedback_processing"

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ModelUpdateTrigger(Enum):
    """Triggers for model updates"""
    SCHEDULED = "scheduled"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_DRIFT = "data_drift"
    FEEDBACK_THRESHOLD = "feedback_threshold"
    MANUAL = "manual"

@dataclass
class LearningTask:
    """Background learning task definition"""
    task_id: str
    task_type: LearningTaskType
    name: str
    description: str
    scheduled_time: datetime
    priority: int  # 1-10, higher is more important
    parameters: Dict[str, Any]
    dependencies: List[str]  # Task IDs that must complete first
    max_runtime_minutes: int
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ModelPerformanceMetrics:
    """Model performance tracking"""
    model_name: str
    model_version: str
    evaluation_date: datetime
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    mse: Optional[float] = None
    mae: Optional[float] = None
    custom_metrics: Dict[str, float] = None
    data_samples: int = 0
    training_time_seconds: float = 0
    inference_time_ms: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ContinuousLearningEngine:
    """
    Main engine for continuous learning and background processing
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        # Task queue and scheduling
        self.task_queue = []
        self.running_tasks = {}
        self.completed_tasks = []
        self.task_history = {}
        
        # Celery for distributed task processing
        self.celery_app = self._setup_celery()
        
        # Redis for caching and coordination
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()  # Test connection
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using memory cache.")
            self.redis_client = None
        
        # Thread pool for concurrent processing
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Performance tracking
        self.performance_history = {}
        self.model_versions = {}
        
        # Configuration
        self.config = {
            'model_retraining_threshold': 0.05,  # 5% performance drop triggers retraining
            'data_drift_threshold': 0.1,         # 10% drift threshold
            'min_samples_for_retraining': 100,
            'max_model_age_days': 90,
            'performance_check_interval_hours': 6,
            'data_collection_interval_hours': 1,
            'cleanup_retention_days': 30
        }
        
        # Learning modules
        from .prediction_engine import SmartRenewalPredictionEngine
        from .pricing_intelligence import DynamicPricingIntelligence
        from .risk_assessment import TenantRiskAssessment
        
        self.prediction_engine = SmartRenewalPredictionEngine()
        self.pricing_engine = DynamicPricingIntelligence()
        self.risk_engine = TenantRiskAssessment()
        
        # Start background scheduler
        self.scheduler_thread = None
        self.start_scheduler()
    
    def start_scheduler(self):
        """Start the background task scheduler"""
        def run_scheduler():
            # Schedule recurring tasks
            self._schedule_recurring_tasks()
            
            while True:
                try:
                    # Process scheduled tasks
                    self._process_scheduled_tasks()
                    
                    # Clean up completed tasks
                    self._cleanup_old_tasks()
                    
                    # Sleep for 60 seconds before next check
                    time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Scheduler error: {str(e)}")
                    time.sleep(60)  # Continue after error
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Continuous learning scheduler started")
    
    def schedule_task(self, task: LearningTask) -> str:
        """Schedule a learning task"""
        try:
            # Add to task queue
            self.task_queue.append(task)
            
            # Sort by priority and scheduled time
            self.task_queue.sort(key=lambda t: (-t.priority, t.scheduled_time))
            
            logger.info(f"Scheduled task {task.task_id}: {task.name}")
            return task.task_id
            
        except Exception as e:
            logger.error(f"Error scheduling task {task.task_id}: {str(e)}")
            raise
    
    def execute_task_now(self, task_id: str) -> Dict[str, Any]:
        """Execute a specific task immediately"""
        try:
            # Find task in queue
            task = next((t for t in self.task_queue if t.task_id == task_id), None)
            if not task:
                task = next((t for t in self.running_tasks.values() if t.task_id == task_id), None)
                if task and task.status == TaskStatus.RUNNING:
                    return {'error': 'Task is already running'}
            
            if not task:
                return {'error': 'Task not found'}
            
            # Execute task
            result = self._execute_task(task)
            
            return {
                'task_id': task_id,
                'status': task.status.value,
                'result': result,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            }
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            return {'error': str(e)}
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        # Check running tasks
        if task_id in self.running_tasks:
            return self.running_tasks[task_id].to_dict()
        
        # Check queue
        task = next((t for t in self.task_queue if t.task_id == task_id), None)
        if task:
            return task.to_dict()
        
        # Check completed tasks
        task = next((t for t in self.completed_tasks if t.task_id == task_id), None)
        if task:
            return task.to_dict()
        
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'scheduler_running': self.scheduler_thread and self.scheduler_thread.is_alive(),
            'queued_tasks': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'completed_tasks_today': len([
                t for t in self.completed_tasks
                if t.completed_at and t.completed_at.date() == datetime.now().date()
            ]),
            'failed_tasks_today': len([
                t for t in self.completed_tasks
                if t.completed_at and t.completed_at.date() == datetime.now().date() and t.status == TaskStatus.FAILED
            ]),
            'redis_connected': self.redis_client is not None and self._test_redis(),
            'thread_pool_active': self.thread_pool._threads,
            'last_model_update': self._get_last_model_update(),
            'next_scheduled_task': self._get_next_scheduled_task()
        }
    
    def trigger_model_retraining(self, model_name: str, trigger: ModelUpdateTrigger, 
                               reason: str = "") -> str:
        """Trigger model retraining"""
        task_id = f"retrain_{model_name}_{int(datetime.now().timestamp())}"
        
        task = LearningTask(
            task_id=task_id,
            task_type=LearningTaskType.MODEL_RETRAINING,
            name=f"Retrain {model_name} Model",
            description=f"Retrain {model_name} model triggered by {trigger.value}: {reason}",
            scheduled_time=datetime.now(),
            priority=9,  # High priority
            parameters={
                'model_name': model_name,
                'trigger': trigger.value,
                'reason': reason,
                'full_retrain': trigger in [ModelUpdateTrigger.DATA_DRIFT, ModelUpdateTrigger.MANUAL]
            },
            dependencies=[],
            max_runtime_minutes=120  # 2 hours max
        )
        
        return self.schedule_task(task)
    
    def process_feedback_batch(self, feedback_data: List[Dict[str, Any]]) -> str:
        """Process batch of feedback data for model improvement"""
        task_id = f"feedback_batch_{int(datetime.now().timestamp())}"
        
        task = LearningTask(
            task_id=task_id,
            task_type=LearningTaskType.FEEDBACK_PROCESSING,
            name="Process Feedback Batch",
            description=f"Process {len(feedback_data)} feedback records for model improvement",
            scheduled_time=datetime.now(),
            priority=7,
            parameters={
                'feedback_data': feedback_data,
                'batch_size': len(feedback_data)
            },
            dependencies=[],
            max_runtime_minutes=30
        )
        
        return self.schedule_task(task)
    
    def monitor_model_performance(self, model_name: str) -> ModelPerformanceMetrics:
        """Monitor and evaluate model performance"""
        try:
            # Get recent predictions and actual outcomes
            evaluation_data = self._get_evaluation_data(model_name)
            
            if not evaluation_data:
                logger.warning(f"No evaluation data available for {model_name}")
                return None
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(model_name, evaluation_data)
            
            # Store metrics
            self._store_performance_metrics(metrics)
            
            # Check for performance degradation
            if self._detect_performance_degradation(model_name, metrics):
                self.trigger_model_retraining(
                    model_name, 
                    ModelUpdateTrigger.PERFORMANCE_DEGRADATION,
                    f"Performance degraded: {metrics.accuracy:.3f}"
                )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error monitoring {model_name} performance: {str(e)}")
            return None
    
    # Private methods
    
    def _schedule_recurring_tasks(self):
        """Schedule recurring background tasks"""
        # Model performance monitoring every 6 hours
        schedule.every(self.config['performance_check_interval_hours']).hours.do(
            self._schedule_performance_check
        )
        
        # Data collection every hour
        schedule.every(self.config['data_collection_interval_hours']).hours.do(
            self._schedule_data_collection
        )
        
        # Market analysis daily at 2 AM
        schedule.every().day.at("02:00").do(self._schedule_market_analysis)
        
        # Model retraining check weekly on Sundays at 3 AM
        schedule.every().sunday.at("03:00").do(self._schedule_model_age_check)
        
        # Cleanup old tasks daily at 1 AM
        schedule.every().day.at("01:00").do(self._schedule_cleanup)
        
        logger.info("Recurring tasks scheduled")
    
    def _process_scheduled_tasks(self):
        """Process tasks that are due for execution"""
        current_time = datetime.now()
        
        # Find tasks ready to execute
        ready_tasks = [
            task for task in self.task_queue
            if task.scheduled_time <= current_time and task.status == TaskStatus.PENDING
        ]
        
        # Sort by priority
        ready_tasks.sort(key=lambda t: -t.priority)
        
        # Execute tasks (up to thread pool limit)
        available_slots = self.thread_pool._max_workers - len(self.running_tasks)
        
        for task in ready_tasks[:available_slots]:
            if self._check_task_dependencies(task):
                self._start_task_execution(task)
    
    def _start_task_execution(self, task: LearningTask):
        """Start executing a task in background thread"""
        try:
            # Move task from queue to running
            self.task_queue.remove(task)
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.running_tasks[task.task_id] = task
            
            # Submit to thread pool
            future = self.thread_pool.submit(self._execute_task, task)
            
            # Add callback for completion
            def task_completed(fut):
                try:
                    result = fut.result()
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.error_message = str(e)
                    task.status = TaskStatus.FAILED
                finally:
                    task.completed_at = datetime.now()
                    self.running_tasks.pop(task.task_id, None)
                    self.completed_tasks.append(task)
                    logger.info(f"Task {task.task_id} completed with status: {task.status.value}")
            
            future.add_done_callback(task_completed)
            
        except Exception as e:
            logger.error(f"Error starting task {task.task_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
    
    def _execute_task(self, task: LearningTask) -> Dict[str, Any]:
        """Execute a specific task based on its type"""
        logger.info(f"Executing task {task.task_id}: {task.name}")
        
        try:
            if task.task_type == LearningTaskType.MODEL_RETRAINING:
                return self._execute_model_retraining(task)
            
            elif task.task_type == LearningTaskType.DATA_COLLECTION:
                return self._execute_data_collection(task)
            
            elif task.task_type == LearningTaskType.PERFORMANCE_MONITORING:
                return self._execute_performance_monitoring(task)
            
            elif task.task_type == LearningTaskType.FEATURE_ENGINEERING:
                return self._execute_feature_engineering(task)
            
            elif task.task_type == LearningTaskType.ANOMALY_DETECTION:
                return self._execute_anomaly_detection(task)
            
            elif task.task_type == LearningTaskType.MARKET_ANALYSIS:
                return self._execute_market_analysis(task)
            
            elif task.task_type == LearningTaskType.FEEDBACK_PROCESSING:
                return self._execute_feedback_processing(task)
            
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            logger.error(f"Task execution error: {str(e)}")
            raise
    
    def _execute_model_retraining(self, task: LearningTask) -> Dict[str, Any]:
        """Execute model retraining task"""
        model_name = task.parameters['model_name']
        full_retrain = task.parameters.get('full_retrain', False)
        
        logger.info(f"Retraining model: {model_name}")
        
        try:
            # Collect training data
            training_data = self._collect_training_data(model_name)
            
            if len(training_data) < self.config['min_samples_for_retraining']:
                return {
                    'status': 'skipped',
                    'reason': f'Insufficient training data: {len(training_data)} samples'
                }
            
            # Train model based on type
            if model_name == 'renewal_prediction':
                result = self.prediction_engine.train_models(training_data)
            elif model_name == 'pricing_optimization':
                # This would implement pricing model retraining
                result = {'status': 'completed', 'message': 'Pricing model retrained'}
            elif model_name == 'risk_assessment':
                # This would implement risk model retraining
                result = {'status': 'completed', 'message': 'Risk model retrained'}
            else:
                raise ValueError(f"Unknown model: {model_name}")
            
            # Update model version
            new_version = self._increment_model_version(model_name)
            
            # Validate new model performance
            validation_result = self._validate_new_model(model_name, new_version)
            
            if validation_result['performance_improved']:
                # Deploy new model
                self._deploy_model(model_name, new_version)
                
                return {
                    'status': 'completed',
                    'model_name': model_name,
                    'new_version': new_version,
                    'training_samples': len(training_data),
                    'performance_improvement': validation_result['improvement'],
                    'training_result': result
                }
            else:
                return {
                    'status': 'completed_no_improvement',
                    'model_name': model_name,
                    'reason': 'New model did not improve performance',
                    'current_performance': validation_result['current_performance'],
                    'new_performance': validation_result['new_performance']
                }
                
        except Exception as e:
            logger.error(f"Model retraining failed: {str(e)}")
            raise
    
    def _execute_data_collection(self, task: LearningTask) -> Dict[str, Any]:
        """Execute data collection task"""
        collection_type = task.parameters.get('collection_type', 'all')
        
        logger.info(f"Collecting data: {collection_type}")
        
        collected_data = {}
        
        try:
            if collection_type in ['all', 'predictions']:
                # Collect recent prediction outcomes
                prediction_data = self._collect_prediction_outcomes()
                collected_data['predictions'] = len(prediction_data)
            
            if collection_type in ['all', 'market']:
                # Collect market data
                market_data = self._collect_market_data()
                collected_data['market'] = len(market_data)
            
            if collection_type in ['all', 'tenant_behavior']:
                # Collect tenant behavior data
                behavior_data = self._collect_tenant_behavior_data()
                collected_data['tenant_behavior'] = len(behavior_data)
            
            # Store collected data for future use
            self._store_collected_data(collected_data)
            
            return {
                'status': 'completed',
                'collection_type': collection_type,
                'data_collected': collected_data,
                'total_records': sum(collected_data.values())
            }
            
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            raise
    
    def _execute_performance_monitoring(self, task: LearningTask) -> Dict[str, Any]:
        """Execute performance monitoring task"""
        models_to_monitor = task.parameters.get('models', ['renewal_prediction', 'pricing_optimization', 'risk_assessment'])
        
        monitoring_results = {}
        
        for model_name in models_to_monitor:
            try:
                metrics = self.monitor_model_performance(model_name)
                if metrics:
                    monitoring_results[model_name] = {
                        'accuracy': metrics.accuracy,
                        'evaluation_date': metrics.evaluation_date.isoformat(),
                        'data_samples': metrics.data_samples,
                        'status': 'healthy' if metrics.accuracy and metrics.accuracy > 0.8 else 'degraded'
                    }
                else:
                    monitoring_results[model_name] = {'status': 'no_data'}
                    
            except Exception as e:
                logger.error(f"Error monitoring {model_name}: {str(e)}")
                monitoring_results[model_name] = {'status': 'error', 'error': str(e)}
        
        return {
            'status': 'completed',
            'monitoring_results': monitoring_results,
            'models_monitored': len(models_to_monitor)
        }
    
    def _execute_feedback_processing(self, task: LearningTask) -> Dict[str, Any]:
        """Execute feedback processing task"""
        feedback_data = task.parameters['feedback_data']
        
        logger.info(f"Processing {len(feedback_data)} feedback records")
        
        try:
            processed_records = 0
            improvements_identified = 0
            
            # Group feedback by model/prediction type
            feedback_groups = self._group_feedback_by_model(feedback_data)
            
            for model_name, feedback_list in feedback_groups.items():
                # Process feedback for this model
                model_improvements = self._process_model_feedback(model_name, feedback_list)
                improvements_identified += len(model_improvements)
                processed_records += len(feedback_list)
                
                # If significant improvements are identified, schedule retraining
                if len(model_improvements) > 10:  # Threshold for retraining
                    self.trigger_model_retraining(
                        model_name,
                        ModelUpdateTrigger.FEEDBACK_THRESHOLD,
                        f"{len(model_improvements)} improvements identified"
                    )
            
            return {
                'status': 'completed',
                'processed_records': processed_records,
                'improvements_identified': improvements_identified,
                'models_affected': list(feedback_groups.keys())
            }
            
        except Exception as e:
            logger.error(f"Feedback processing failed: {str(e)}")
            raise
    
    def _execute_feature_engineering(self, task: LearningTask) -> Dict[str, Any]:
        """Execute feature engineering task"""
        # This would implement automated feature engineering
        return {'status': 'completed', 'message': 'Feature engineering completed'}
    
    def _execute_anomaly_detection(self, task: LearningTask) -> Dict[str, Any]:
        """Execute anomaly detection task"""
        # This would implement anomaly detection in data patterns
        return {'status': 'completed', 'message': 'Anomaly detection completed'}
    
    def _execute_market_analysis(self, task: LearningTask) -> Dict[str, Any]:
        """Execute market analysis task"""
        # This would implement automated market analysis
        return {'status': 'completed', 'message': 'Market analysis completed'}
    
    # Utility methods
    
    def _check_task_dependencies(self, task: LearningTask) -> bool:
        """Check if task dependencies are satisfied"""
        if not task.dependencies:
            return True
        
        for dep_task_id in task.dependencies:
            dep_task = next(
                (t for t in self.completed_tasks if t.task_id == dep_task_id), 
                None
            )
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _get_evaluation_data(self, model_name: str) -> Optional[pd.DataFrame]:
        """Get evaluation data for model performance monitoring"""
        # This would query the database for recent predictions and outcomes
        # For now, return None to indicate no data available
        return None
    
    def _calculate_performance_metrics(self, model_name: str, data: pd.DataFrame) -> ModelPerformanceMetrics:
        """Calculate model performance metrics"""
        # This would implement actual performance calculation
        return ModelPerformanceMetrics(
            model_name=model_name,
            model_version="1.0.0",
            evaluation_date=datetime.now(),
            accuracy=0.85,  # Placeholder
            data_samples=len(data)
        )
    
    def _detect_performance_degradation(self, model_name: str, current_metrics: ModelPerformanceMetrics) -> bool:
        """Detect if model performance has degraded significantly"""
        # Get historical performance
        historical_metrics = self.performance_history.get(model_name, [])
        
        if not historical_metrics:
            # No history to compare against
            self.performance_history[model_name] = [current_metrics]
            return False
        
        # Compare with recent performance
        recent_accuracy = np.mean([m.accuracy for m in historical_metrics[-5:] if m.accuracy])
        
        if current_metrics.accuracy and recent_accuracy:
            degradation = (recent_accuracy - current_metrics.accuracy) / recent_accuracy
            
            if degradation > self.config['model_retraining_threshold']:
                logger.warning(f"Performance degradation detected for {model_name}: {degradation:.3f}")
                return True
        
        # Add current metrics to history
        self.performance_history[model_name].append(current_metrics)
        
        # Keep only recent history (last 30 evaluations)
        if len(self.performance_history[model_name]) > 30:
            self.performance_history[model_name] = self.performance_history[model_name][-30:]
        
        return False
    
    def _store_performance_metrics(self, metrics: ModelPerformanceMetrics):
        """Store performance metrics for tracking"""
        # This would store metrics in database
        if self.redis_client:
            try:
                key = f"performance:{metrics.model_name}:{metrics.evaluation_date.isoformat()}"
                self.redis_client.setex(key, 86400 * 30, json.dumps(metrics.to_dict(), default=str))
            except Exception as e:
                logger.error(f"Error storing metrics in Redis: {e}")
    
    def _collect_training_data(self, model_name: str) -> pd.DataFrame:
        """Collect training data for model retraining"""
        # This would collect actual training data from database
        # For now, return empty DataFrame
        return pd.DataFrame()
    
    def _increment_model_version(self, model_name: str) -> str:
        """Increment model version number"""
        current_version = self.model_versions.get(model_name, "1.0.0")
        
        # Simple versioning: increment minor version
        parts = current_version.split('.')
        parts[1] = str(int(parts[1]) + 1)
        new_version = '.'.join(parts)
        
        self.model_versions[model_name] = new_version
        return new_version
    
    def _validate_new_model(self, model_name: str, model_version: str) -> Dict[str, Any]:
        """Validate new model performance against current model"""
        # This would implement actual model validation
        return {
            'performance_improved': True,
            'improvement': 0.05,
            'current_performance': 0.85,
            'new_performance': 0.90
        }
    
    def _deploy_model(self, model_name: str, model_version: str):
        """Deploy new model version"""
        logger.info(f"Deploying {model_name} version {model_version}")
        # This would implement actual model deployment
    
    def _collect_prediction_outcomes(self) -> List[Dict[str, Any]]:
        """Collect recent prediction outcomes for evaluation"""
        # This would query database for recent predictions and actual outcomes
        return []
    
    def _collect_market_data(self) -> List[Dict[str, Any]]:
        """Collect market data"""
        # This would collect market data from external sources
        return []
    
    def _collect_tenant_behavior_data(self) -> List[Dict[str, Any]]:
        """Collect tenant behavior data"""
        # This would collect tenant behavior patterns
        return []
    
    def _store_collected_data(self, data: Dict[str, Any]):
        """Store collected data for future use"""
        if self.redis_client:
            try:
                key = f"collected_data:{datetime.now().isoformat()}"
                self.redis_client.setex(key, 86400 * 7, json.dumps(data, default=str))
            except Exception as e:
                logger.error(f"Error storing collected data: {e}")
    
    def _group_feedback_by_model(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group feedback data by model"""
        groups = {}
        
        for feedback in feedback_data:
            model_name = feedback.get('model_name', 'unknown')
            if model_name not in groups:
                groups[model_name] = []
            groups[model_name].append(feedback)
        
        return groups
    
    def _process_model_feedback(self, model_name: str, feedback_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process feedback for a specific model"""
        improvements = []
        
        for feedback in feedback_list:
            # Analyze feedback and identify potential improvements
            if feedback.get('actual_outcome') != feedback.get('predicted_outcome'):
                improvements.append({
                    'prediction_id': feedback.get('prediction_id'),
                    'improvement_type': 'prediction_accuracy',
                    'details': feedback
                })
        
        return improvements
    
    def _schedule_performance_check(self):
        """Schedule performance monitoring task"""
        task_id = f"perf_check_{int(datetime.now().timestamp())}"
        
        task = LearningTask(
            task_id=task_id,
            task_type=LearningTaskType.PERFORMANCE_MONITORING,
            name="Model Performance Check",
            description="Regular model performance monitoring",
            scheduled_time=datetime.now(),
            priority=6,
            parameters={'models': ['renewal_prediction', 'pricing_optimization', 'risk_assessment']},
            dependencies=[],
            max_runtime_minutes=30
        )
        
        self.schedule_task(task)
    
    def _schedule_data_collection(self):
        """Schedule data collection task"""
        task_id = f"data_collection_{int(datetime.now().timestamp())}"
        
        task = LearningTask(
            task_id=task_id,
            task_type=LearningTaskType.DATA_COLLECTION,
            name="Regular Data Collection",
            description="Collect recent data for model training",
            scheduled_time=datetime.now(),
            priority=5,
            parameters={'collection_type': 'all'},
            dependencies=[],
            max_runtime_minutes=60
        )
        
        self.schedule_task(task)
    
    def _schedule_market_analysis(self):
        """Schedule market analysis task"""
        task_id = f"market_analysis_{int(datetime.now().timestamp())}"
        
        task = LearningTask(
            task_id=task_id,
            task_type=LearningTaskType.MARKET_ANALYSIS,
            name="Daily Market Analysis",
            description="Analyze market trends and conditions",
            scheduled_time=datetime.now(),
            priority=4,
            parameters={},
            dependencies=[],
            max_runtime_minutes=45
        )
        
        self.schedule_task(task)
    
    def _schedule_model_age_check(self):
        """Check if models need retraining due to age"""
        for model_name in ['renewal_prediction', 'pricing_optimization', 'risk_assessment']:
            last_training = self._get_last_training_date(model_name)
            
            if not last_training or (datetime.now() - last_training).days > self.config['max_model_age_days']:
                self.trigger_model_retraining(
                    model_name,
                    ModelUpdateTrigger.SCHEDULED,
                    f"Model age exceeded {self.config['max_model_age_days']} days"
                )
    
    def _schedule_cleanup(self):
        """Schedule cleanup of old tasks"""
        task_id = f"cleanup_{int(datetime.now().timestamp())}"
        
        task = LearningTask(
            task_id=task_id,
            task_type=LearningTaskType.DATA_COLLECTION,  # Reuse data collection type
            name="System Cleanup",
            description="Clean up old tasks and data",
            scheduled_time=datetime.now(),
            priority=2,
            parameters={'cleanup': True},
            dependencies=[],
            max_runtime_minutes=15
        )
        
        self.schedule_task(task)
    
    def _cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        cutoff_date = datetime.now() - timedelta(days=self.config['cleanup_retention_days'])
        
        # Remove old completed tasks
        old_tasks = [
            task for task in self.completed_tasks
            if task.completed_at and task.completed_at < cutoff_date
        ]
        
        for task in old_tasks:
            self.completed_tasks.remove(task)
        
        if old_tasks:
            logger.info(f"Cleaned up {len(old_tasks)} old tasks")
    
    def _test_redis(self) -> bool:
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _get_last_model_update(self) -> Optional[str]:
        """Get timestamp of last model update"""
        if not self.completed_tasks:
            return None
        
        retraining_tasks = [
            task for task in self.completed_tasks
            if task.task_type == LearningTaskType.MODEL_RETRAINING and task.status == TaskStatus.COMPLETED
        ]
        
        if retraining_tasks:
            latest_task = max(retraining_tasks, key=lambda t: t.completed_at)
            return latest_task.completed_at.isoformat()
        
        return None
    
    def _get_next_scheduled_task(self) -> Optional[str]:
        """Get next scheduled task"""
        if not self.task_queue:
            return None
        
        next_task = min(self.task_queue, key=lambda t: t.scheduled_time)
        return next_task.scheduled_time.isoformat()
    
    def _get_last_training_date(self, model_name: str) -> Optional[datetime]:
        """Get last training date for a model"""
        # This would query the database for last training date
        # For now, return None
        return None
    
    def _setup_celery(self) -> Celery:
        """Setup Celery for distributed task processing"""
        app = Celery('smart_renewal_continuous_learning')
        
        app.conf.update(
            broker_url='redis://localhost:6379/0',
            result_backend='redis://localhost:6379/0',
            task_serializer='json',
            result_serializer='json',
            accept_content=['json'],
            timezone='UTC',
            enable_utc=True,
            beat_schedule={
                'performance-monitoring': {
                    'task': 'smart_renewal.monitor_performance',
                    'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
                },
                'data-collection': {
                    'task': 'smart_renewal.collect_data',
                    'schedule': crontab(minute=0),  # Every hour
                },
                'market-analysis': {
                    'task': 'smart_renewal.analyze_market',
                    'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
                },
            },
        )
        
        return app
    
    def stop(self):
        """Stop the continuous learning engine"""
        logger.info("Stopping continuous learning engine...")
        
        # Stop scheduler
        if self.scheduler_thread:
            self.scheduler_thread = None
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Close Redis connection
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("Continuous learning engine stopped")


# Celery tasks for distributed processing
@task
def monitor_performance():
    """Celery task for performance monitoring"""
    engine = ContinuousLearningEngine()
    task_id = engine._schedule_performance_check()
    return f"Performance monitoring scheduled: {task_id}"

@task  
def collect_data():
    """Celery task for data collection"""
    engine = ContinuousLearningEngine()
    task_id = engine._schedule_data_collection()
    return f"Data collection scheduled: {task_id}"

@task
def analyze_market():
    """Celery task for market analysis"""
    engine = ContinuousLearningEngine()
    task_id = engine._schedule_market_analysis()
    return f"Market analysis scheduled: {task_id}"

@task
def retrain_model(model_name: str, trigger_reason: str = ""):
    """Celery task for model retraining"""
    engine = ContinuousLearningEngine()
    task_id = engine.trigger_model_retraining(
        model_name, 
        ModelUpdateTrigger.MANUAL,
        trigger_reason
    )
    return f"Model retraining scheduled: {task_id}"

# Global engine instance
_learning_engine = None

def get_continuous_learning_engine() -> ContinuousLearningEngine:
    """Get global continuous learning engine instance"""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = ContinuousLearningEngine()
    return _learning_engine