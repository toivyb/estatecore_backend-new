"""
Tenant monitoring and usage tracking service.
Provides comprehensive monitoring, analytics, and usage tracking for white-label tenants.
"""
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from flask import current_app, request
import threading
from collections import defaultdict, deque
import time

from models.white_label_tenant import TenantUsageLog, WhiteLabelTenant, db
from services.tenant_context import get_current_tenant_context

class MetricType(Enum):
    """Types of metrics to track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class TenantMetric:
    """Individual tenant metric data point."""
    tenant_id: int
    metric_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

@dataclass
class TenantAlert:
    """Tenant alert configuration and state."""
    tenant_id: int
    alert_name: str
    condition: str
    threshold: float
    level: AlertLevel
    enabled: bool = True
    last_triggered: datetime = None
    trigger_count: int = 0

class TenantMonitoringService:
    """
    Service for monitoring tenant health, usage, and performance.
    """
    
    def __init__(self):
        self.metrics_buffer = defaultdict(deque)
        self.alerts_config = {}
        self.buffer_lock = threading.Lock()
        self.buffer_size = 1000
        self.flush_interval = 60  # seconds
        self.last_flush = time.time()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for metric collection and processing."""
        # In a production environment, this would use Celery or similar
        # For now, we'll use simple in-memory processing
        pass
    
    def log_api_request(self, tenant_id: int, endpoint: str, method: str, 
                       response_status: int, response_time: float = None):
        """
        Log API request for usage tracking.
        
        Args:
            tenant_id: Tenant ID
            endpoint: API endpoint
            method: HTTP method
            response_status: HTTP response status code
            response_time: Response time in milliseconds
        """
        try:
            # Record API call metric
            self.record_metric(
                tenant_id=tenant_id,
                metric_name="api_requests_total",
                metric_type=MetricType.COUNTER,
                value=1,
                labels={
                    "endpoint": endpoint,
                    "method": method,
                    "status": str(response_status)
                }
            )
            
            # Record response time if provided
            if response_time is not None:
                self.record_metric(
                    tenant_id=tenant_id,
                    metric_name="api_response_time",
                    metric_type=MetricType.HISTOGRAM,
                    value=response_time,
                    labels={
                        "endpoint": endpoint,
                        "method": method
                    }
                )
            
            # Update usage statistics
            self._update_usage_statistics(tenant_id, "api_calls", 1)
            
        except Exception as e:
            current_app.logger.error(f"Error logging API request: {str(e)}")
    
    def log_storage_usage(self, tenant_id: int, storage_bytes: int, storage_type: str = "general"):
        """
        Log storage usage for a tenant.
        
        Args:
            tenant_id: Tenant ID
            storage_bytes: Storage usage in bytes
            storage_type: Type of storage (files, database, etc.)
        """
        try:
            self.record_metric(
                tenant_id=tenant_id,
                metric_name="storage_usage_bytes",
                metric_type=MetricType.GAUGE,
                value=storage_bytes,
                labels={"storage_type": storage_type}
            )
            
            # Update usage statistics
            storage_gb = storage_bytes / (1024**3)
            self._update_usage_statistics(tenant_id, "storage_gb", storage_gb)
            
        except Exception as e:
            current_app.logger.error(f"Error logging storage usage: {str(e)}")
    
    def log_user_activity(self, tenant_id: int, user_id: int, activity_type: str, details: Dict[str, Any] = None):
        """
        Log user activity for auditing and analytics.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            activity_type: Type of activity (login, logout, action, etc.)
            details: Additional activity details
        """
        try:
            self.record_metric(
                tenant_id=tenant_id,
                metric_name="user_activities_total",
                metric_type=MetricType.COUNTER,
                value=1,
                labels={
                    "user_id": str(user_id),
                    "activity_type": activity_type
                }
            )
            
            # Log detailed activity if needed
            if details:
                self._log_detailed_activity(tenant_id, user_id, activity_type, details)
                
        except Exception as e:
            current_app.logger.error(f"Error logging user activity: {str(e)}")
    
    def record_metric(self, tenant_id: int, metric_name: str, metric_type: MetricType, 
                     value: float, labels: Dict[str, str] = None):
        """
        Record a metric for a tenant.
        
        Args:
            tenant_id: Tenant ID
            metric_name: Name of the metric
            metric_type: Type of metric
            value: Metric value
            labels: Optional labels for the metric
        """
        try:
            metric = TenantMetric(
                tenant_id=tenant_id,
                metric_name=metric_name,
                metric_type=metric_type,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {}
            )
            
            with self.buffer_lock:
                self.metrics_buffer[tenant_id].append(metric)
                
                # Limit buffer size
                if len(self.metrics_buffer[tenant_id]) > self.buffer_size:
                    self.metrics_buffer[tenant_id].popleft()
            
            # Check if we need to flush
            if time.time() - self.last_flush > self.flush_interval:
                self._flush_metrics()
            
        except Exception as e:
            current_app.logger.error(f"Error recording metric: {str(e)}")
    
    def get_tenant_health_score(self, tenant_id: int) -> Dict[str, Any]:
        """
        Calculate tenant health score based on various metrics.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dict containing health score and breakdown
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return {"health_score": 0, "status": "unknown"}
            
            # Get recent metrics
            recent_metrics = self._get_recent_metrics(tenant_id, hours=24)
            
            # Calculate health components
            api_health = self._calculate_api_health(recent_metrics)
            usage_health = self._calculate_usage_health(tenant, recent_metrics)
            error_health = self._calculate_error_health(recent_metrics)
            activity_health = self._calculate_activity_health(recent_metrics)
            
            # Calculate overall health score (0-100)
            health_score = (
                api_health * 0.3 +
                usage_health * 0.25 +
                error_health * 0.25 +
                activity_health * 0.2
            )
            
            # Determine status
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 75:
                status = "good"
            elif health_score >= 50:
                status = "fair"
            elif health_score >= 25:
                status = "poor"
            else:
                status = "critical"
            
            return {
                "health_score": round(health_score, 2),
                "status": status,
                "components": {
                    "api_health": round(api_health, 2),
                    "usage_health": round(usage_health, 2),
                    "error_health": round(error_health, 2),
                    "activity_health": round(activity_health, 2)
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error calculating health score: {str(e)}")
            return {"health_score": 0, "status": "error"}
    
    def get_usage_analytics(self, tenant_id: int, period_days: int = 30) -> Dict[str, Any]:
        """
        Get usage analytics for a tenant.
        
        Args:
            tenant_id: Tenant ID
            period_days: Number of days to analyze
            
        Returns:
            Dict containing usage analytics
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get usage logs
            usage_logs = TenantUsageLog.query.filter(
                TenantUsageLog.tenant_id == tenant_id,
                TenantUsageLog.period_start >= start_date
            ).all()
            
            # Aggregate usage data
            usage_summary = defaultdict(lambda: {"total": 0, "daily": []})
            
            for log in usage_logs:
                resource_type = log.resource_type
                usage_summary[resource_type]["total"] += log.usage_value
                usage_summary[resource_type]["daily"].append({
                    "date": log.period_start.date().isoformat(),
                    "value": log.usage_value
                })
            
            # Get tenant quotas
            tenant = WhiteLabelTenant.query.get(tenant_id)
            quotas = tenant.resource_quotas if tenant else {}
            
            # Calculate usage percentages
            for resource_type, data in usage_summary.items():
                quota = quotas.get(resource_type)
                if quota:
                    data["quota"] = quota
                    data["percentage"] = (data["total"] / quota) * 100
                else:
                    data["quota"] = None
                    data["percentage"] = None
            
            return {
                "tenant_id": tenant_id,
                "period_days": period_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "usage_summary": dict(usage_summary),
                "total_api_calls": usage_summary.get("api_calls", {}).get("total", 0),
                "total_storage_gb": usage_summary.get("storage_gb", {}).get("total", 0),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting usage analytics: {str(e)}")
            return {}
    
    def create_alert(self, tenant_id: int, alert_name: str, condition: str, 
                    threshold: float, level: AlertLevel) -> bool:
        """
        Create a monitoring alert for a tenant.
        
        Args:
            tenant_id: Tenant ID
            alert_name: Name of the alert
            condition: Alert condition (e.g., "api_error_rate > threshold")
            threshold: Alert threshold value
            level: Alert severity level
            
        Returns:
            True if alert created successfully
        """
        try:
            alert = TenantAlert(
                tenant_id=tenant_id,
                alert_name=alert_name,
                condition=condition,
                threshold=threshold,
                level=level
            )
            
            alert_key = f"{tenant_id}:{alert_name}"
            self.alerts_config[alert_key] = alert
            
            current_app.logger.info(f"Created alert {alert_name} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error creating alert: {str(e)}")
            return False
    
    def check_alerts(self, tenant_id: int) -> List[Dict[str, Any]]:
        """
        Check and trigger alerts for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        try:
            # Get recent metrics for evaluation
            recent_metrics = self._get_recent_metrics(tenant_id, hours=1)
            
            # Check each alert
            for alert_key, alert in self.alerts_config.items():
                if not alert.enabled or alert.tenant_id != tenant_id:
                    continue
                
                # Evaluate alert condition
                if self._evaluate_alert_condition(alert, recent_metrics):
                    triggered_alert = {
                        "alert_name": alert.alert_name,
                        "level": alert.level.value,
                        "threshold": alert.threshold,
                        "condition": alert.condition,
                        "triggered_at": datetime.utcnow().isoformat()
                    }
                    
                    triggered_alerts.append(triggered_alert)
                    
                    # Update alert state
                    alert.last_triggered = datetime.utcnow()
                    alert.trigger_count += 1
                    
                    # Send notification
                    self._send_alert_notification(tenant_id, triggered_alert)
            
        except Exception as e:
            current_app.logger.error(f"Error checking alerts: {str(e)}")
        
        return triggered_alerts
    
    def _update_usage_statistics(self, tenant_id: int, resource_type: str, value: float):
        """Update usage statistics in the database."""
        try:
            # Create or update daily usage log
            today = datetime.utcnow().date()
            period_start = datetime.combine(today, datetime.min.time())
            period_end = period_start + timedelta(days=1)
            
            usage_log = TenantUsageLog.query.filter(
                TenantUsageLog.tenant_id == tenant_id,
                TenantUsageLog.resource_type == resource_type,
                TenantUsageLog.period_start == period_start
            ).first()
            
            if usage_log:
                usage_log.usage_value += value
            else:
                usage_log = TenantUsageLog(
                    tenant_id=tenant_id,
                    resource_type=resource_type,
                    usage_value=value,
                    usage_period="daily",
                    period_start=period_start,
                    period_end=period_end
                )
                db.session.add(usage_log)
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating usage statistics: {str(e)}")
            db.session.rollback()
    
    def _get_recent_metrics(self, tenant_id: int, hours: int = 24) -> List[TenantMetric]:
        """Get recent metrics for a tenant."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.buffer_lock:
            tenant_metrics = self.metrics_buffer.get(tenant_id, deque())
            return [
                metric for metric in tenant_metrics 
                if metric.timestamp >= cutoff_time
            ]
    
    def _calculate_api_health(self, metrics: List[TenantMetric]) -> float:
        """Calculate API health score based on metrics."""
        api_metrics = [m for m in metrics if m.metric_name.startswith("api_")]
        
        if not api_metrics:
            return 100.0  # No data means healthy
        
        # Calculate error rate
        total_requests = len([m for m in api_metrics if m.metric_name == "api_requests_total"])
        error_requests = len([
            m for m in api_metrics 
            if m.metric_name == "api_requests_total" and 
            m.labels.get("status", "200").startswith(("4", "5"))
        ])
        
        if total_requests == 0:
            return 100.0
        
        error_rate = (error_requests / total_requests) * 100
        
        # Health decreases with error rate
        if error_rate <= 1:
            return 100.0
        elif error_rate <= 5:
            return 80.0
        elif error_rate <= 10:
            return 60.0
        else:
            return max(0, 60 - (error_rate - 10) * 2)
    
    def _calculate_usage_health(self, tenant: WhiteLabelTenant, metrics: List[TenantMetric]) -> float:
        """Calculate usage health based on quota utilization."""
        if not tenant.resource_quotas:
            return 100.0
        
        # Get current usage
        current_usage = tenant.usage_metrics or {}
        
        # Calculate usage percentages
        usage_percentages = []
        for resource, quota in tenant.resource_quotas.items():
            current = current_usage.get(resource, 0)
            if quota > 0:
                percentage = (current / quota) * 100
                usage_percentages.append(percentage)
        
        if not usage_percentages:
            return 100.0
        
        max_usage = max(usage_percentages)
        
        # Health decreases as usage approaches quota
        if max_usage <= 70:
            return 100.0
        elif max_usage <= 85:
            return 80.0
        elif max_usage <= 95:
            return 60.0
        else:
            return 40.0
    
    def _calculate_error_health(self, metrics: List[TenantMetric]) -> float:
        """Calculate error health based on error frequency."""
        error_metrics = [
            m for m in metrics 
            if "error" in m.metric_name.lower() or 
            (m.labels and any("error" in v.lower() for v in m.labels.values()))
        ]
        
        if not error_metrics:
            return 100.0
        
        # Simple error count based health
        error_count = len(error_metrics)
        
        if error_count <= 5:
            return 100.0
        elif error_count <= 20:
            return 80.0
        elif error_count <= 50:
            return 60.0
        else:
            return 40.0
    
    def _calculate_activity_health(self, metrics: List[TenantMetric]) -> float:
        """Calculate activity health based on user engagement."""
        activity_metrics = [
            m for m in metrics 
            if m.metric_name == "user_activities_total"
        ]
        
        if not activity_metrics:
            return 50.0  # Neutral score for no activity
        
        # More activity generally means healthier tenant
        activity_count = len(activity_metrics)
        
        if activity_count >= 100:
            return 100.0
        elif activity_count >= 50:
            return 90.0
        elif activity_count >= 20:
            return 80.0
        elif activity_count >= 10:
            return 70.0
        else:
            return 60.0
    
    def _flush_metrics(self):
        """Flush metrics buffer to persistent storage."""
        try:
            with self.buffer_lock:
                # In a real implementation, this would write to a time-series database
                # like InfluxDB, Prometheus, or CloudWatch
                
                # For now, we'll just log the metrics
                total_metrics = sum(len(metrics) for metrics in self.metrics_buffer.values())
                if total_metrics > 0:
                    current_app.logger.debug(f"Flushing {total_metrics} metrics to storage")
                
                # Clear old metrics (keep recent ones)
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                for tenant_id, metrics in self.metrics_buffer.items():
                    while metrics and metrics[0].timestamp < cutoff_time:
                        metrics.popleft()
                
                self.last_flush = time.time()
                
        except Exception as e:
            current_app.logger.error(f"Error flushing metrics: {str(e)}")

# Global monitoring service instance
_monitoring_service = None

def get_tenant_monitoring_service() -> TenantMonitoringService:
    """Get the global tenant monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = TenantMonitoringService()
    return _monitoring_service

# Convenience functions
def log_tenant_api_request(endpoint: str, method: str, response_status: int, response_time: float = None):
    """Log API request for current tenant."""
    context = get_current_tenant_context()
    if context and context.tenant:
        service = get_tenant_monitoring_service()
        service.log_api_request(
            tenant_id=context.tenant_id,
            endpoint=endpoint,
            method=method,
            response_status=response_status,
            response_time=response_time
        )

def log_tenant_activity(user_id: int, activity_type: str, details: Dict[str, Any] = None):
    """Log user activity for current tenant."""
    context = get_current_tenant_context()
    if context and context.tenant:
        service = get_tenant_monitoring_service()
        service.log_user_activity(
            tenant_id=context.tenant_id,
            user_id=user_id,
            activity_type=activity_type,
            details=details
        )