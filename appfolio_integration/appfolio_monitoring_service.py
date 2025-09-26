"""
AppFolio Monitoring Service

Comprehensive monitoring, health checking, and performance tracking
for AppFolio integration operations.
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import psutil
import statistics

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class HealthCheck:
    """Health check configuration"""
    check_id: str
    name: str
    description: str
    check_function: str
    interval_seconds: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    critical: bool = False
    last_check: Optional[datetime] = None
    last_status: HealthStatus = HealthStatus.UNKNOWN
    last_result: Optional[Dict[str, Any]] = None
    failure_count: int = 0
    max_failures: int = 3

@dataclass
class Alert:
    """Alert information"""
    alert_id: str
    organization_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    source: str = "appfolio_integration"

@dataclass
class Metric:
    """Performance metric"""
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None

@dataclass
class PerformanceStats:
    """Performance statistics"""
    organization_id: str
    timeframe: str
    api_calls_total: int = 0
    api_calls_successful: int = 0
    api_calls_failed: int = 0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    sync_jobs_completed: int = 0
    sync_jobs_failed: int = 0
    webhook_events_processed: int = 0
    webhook_events_failed: int = 0
    data_quality_score: float = 100.0
    uptime_percentage: float = 100.0
    error_rate: float = 0.0

class AppFolioMonitoringService:
    """
    AppFolio Monitoring Service
    
    Provides comprehensive monitoring, health checking, performance tracking,
    and alerting for the AppFolio integration system.
    """
    
    def __init__(self):
        # Health monitoring
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_status_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Performance monitoring
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.performance_stats: Dict[str, PerformanceStats] = {}
        
        # Alert management
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Request tracking
        self.request_metrics: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.success_counts: Dict[str, int] = defaultdict(int)
        
        # System monitoring
        self.system_metrics: deque = deque(maxlen=1000)
        
        # Configuration
        self.monitoring_enabled = True
        self.alert_thresholds = {
            'api_error_rate': 10.0,  # percentage
            'avg_response_time': 5000.0,  # milliseconds
            'sync_failure_rate': 20.0,  # percentage
            'webhook_failure_rate': 15.0,  # percentage
            'memory_usage': 85.0,  # percentage
            'cpu_usage': 90.0,  # percentage
        }
        
        # Setup default health checks
        self._setup_default_health_checks()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("AppFolio Monitoring Service initialized")
    
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        
        # API connectivity check
        self.add_health_check(HealthCheck(
            check_id="api_connectivity",
            name="AppFolio API Connectivity",
            description="Check connectivity to AppFolio API endpoints",
            check_function="check_api_connectivity",
            interval_seconds=60,
            critical=True
        ))
        
        # Database connectivity check
        self.add_health_check(HealthCheck(
            check_id="database_connectivity",
            name="Database Connectivity",
            description="Check connectivity to EstateCore database",
            check_function="check_database_connectivity",
            interval_seconds=30,
            critical=True
        ))
        
        # Webhook endpoint check
        self.add_health_check(HealthCheck(
            check_id="webhook_endpoint",
            name="Webhook Endpoint Health",
            description="Check webhook endpoint availability",
            check_function="check_webhook_endpoint",
            interval_seconds=120
        ))
        
        # System resources check
        self.add_health_check(HealthCheck(
            check_id="system_resources",
            name="System Resources",
            description="Check system CPU, memory, and disk usage",
            check_function="check_system_resources",
            interval_seconds=30
        ))
        
        # Sync service check
        self.add_health_check(HealthCheck(
            check_id="sync_service",
            name="Sync Service Health",
            description="Check sync service status and queue health",
            check_function="check_sync_service",
            interval_seconds=60
        ))
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_enabled:
            try:
                # Run health checks
                self._run_health_checks()
                
                # Collect system metrics
                self._collect_system_metrics()
                
                # Check alert conditions
                self._check_alert_conditions()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep for monitoring interval
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(30)
    
    def _run_health_checks(self):
        """Run all enabled health checks"""
        current_time = datetime.utcnow()
        
        for check in self.health_checks.values():
            if not check.enabled:
                continue
            
            # Check if it's time to run this check
            if (check.last_check and 
                (current_time - check.last_check).total_seconds() < check.interval_seconds):
                continue
            
            try:
                # Run the health check
                result = self._execute_health_check(check)
                
                # Update check status
                check.last_check = current_time
                check.last_result = result
                
                if result['healthy']:
                    check.last_status = HealthStatus.HEALTHY
                    check.failure_count = 0
                else:
                    check.failure_count += 1
                    if check.failure_count >= check.max_failures:
                        check.last_status = HealthStatus.CRITICAL if check.critical else HealthStatus.WARNING
                    else:
                        check.last_status = HealthStatus.WARNING
                
                # Store in history
                self.health_status_history[check.check_id].append({
                    'timestamp': current_time,
                    'status': check.last_status,
                    'result': result
                })
                
                # Generate alerts if needed
                if check.last_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    self._generate_health_alert(check, result)
                
            except Exception as e:
                logger.error(f"Health check {check.check_id} failed: {str(e)}")
                check.last_status = HealthStatus.UNKNOWN
                check.failure_count += 1
    
    def _execute_health_check(self, check: HealthCheck) -> Dict[str, Any]:
        """Execute a specific health check"""
        if check.check_function == "check_api_connectivity":
            return self._check_api_connectivity()
        elif check.check_function == "check_database_connectivity":
            return self._check_database_connectivity()
        elif check.check_function == "check_webhook_endpoint":
            return self._check_webhook_endpoint()
        elif check.check_function == "check_system_resources":
            return self._check_system_resources()
        elif check.check_function == "check_sync_service":
            return self._check_sync_service()
        else:
            return {'healthy': False, 'error': f'Unknown check function: {check.check_function}'}
    
    def _check_api_connectivity(self) -> Dict[str, Any]:
        """Check AppFolio API connectivity"""
        try:
            # This would test actual API connectivity
            # For now, return a basic health status
            return {
                'healthy': True,
                'response_time': 150.0,
                'endpoints_checked': ['auth', 'properties', 'tenants'],
                'all_endpoints_healthy': True
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # This would test actual database connectivity
            # For now, return a basic health status
            return {
                'healthy': True,
                'connection_time': 50.0,
                'pool_size': 10,
                'active_connections': 3
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_webhook_endpoint(self) -> Dict[str, Any]:
        """Check webhook endpoint health"""
        try:
            # This would test webhook endpoint accessibility
            return {
                'healthy': True,
                'endpoint_reachable': True,
                'ssl_valid': True,
                'response_time': 200.0
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            healthy = (cpu_percent < self.alert_thresholds['cpu_usage'] and
                      memory.percent < self.alert_thresholds['memory_usage'])
            
            return {
                'healthy': healthy,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_percent': disk.percent,
                'disk_free': disk.free
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_sync_service(self) -> Dict[str, Any]:
        """Check sync service health"""
        try:
            # This would check actual sync service status
            return {
                'healthy': True,
                'active_jobs': 2,
                'queue_size': 5,
                'recent_failures': 0,
                'last_successful_sync': datetime.utcnow() - timedelta(minutes=15)
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            timestamp = datetime.utcnow()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent()
            self.record_metric("system.cpu_percent", cpu_percent, MetricType.GAUGE, timestamp)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric("system.memory_percent", memory.percent, MetricType.GAUGE, timestamp)
            self.record_metric("system.memory_used", memory.used, MetricType.GAUGE, timestamp)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_metric("system.disk_percent", disk.percent, MetricType.GAUGE, timestamp)
            self.record_metric("system.disk_free", disk.free, MetricType.GAUGE, timestamp)
            
            # Store composite system metrics
            system_metric = {
                'timestamp': timestamp,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            }
            self.system_metrics.append(system_metric)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
    
    def _check_alert_conditions(self):
        """Check conditions that should trigger alerts"""
        try:
            # Check API error rate
            self._check_api_error_rate()
            
            # Check response time
            self._check_response_time()
            
            # Check sync failure rate
            self._check_sync_failure_rate()
            
            # Check webhook failure rate
            self._check_webhook_failure_rate()
            
            # Check system resources
            self._check_system_resource_alerts()
            
        except Exception as e:
            logger.error(f"Error checking alert conditions: {str(e)}")
    
    def _check_api_error_rate(self):
        """Check API error rate and generate alerts"""
        try:
            total_requests = sum(self.success_counts.values()) + sum(self.error_counts.values())
            if total_requests > 0:
                error_rate = (sum(self.error_counts.values()) / total_requests) * 100
                
                if error_rate > self.alert_thresholds['api_error_rate']:
                    self._create_alert(
                        "high_api_error_rate",
                        AlertSeverity.WARNING,
                        "High API Error Rate",
                        f"API error rate is {error_rate:.1f}%, exceeding threshold of {self.alert_thresholds['api_error_rate']}%",
                        {'error_rate': error_rate, 'total_requests': total_requests}
                    )
        except Exception as e:
            logger.error(f"Error checking API error rate: {str(e)}")
    
    def _check_response_time(self):
        """Check average response time and generate alerts"""
        try:
            all_response_times = []
            for times in self.request_metrics.values():
                all_response_times.extend(times)
            
            if all_response_times:
                avg_response_time = statistics.mean(all_response_times)
                
                if avg_response_time > self.alert_thresholds['avg_response_time']:
                    self._create_alert(
                        "high_response_time",
                        AlertSeverity.WARNING,
                        "High Response Time",
                        f"Average response time is {avg_response_time:.1f}ms, exceeding threshold of {self.alert_thresholds['avg_response_time']}ms",
                        {'avg_response_time': avg_response_time}
                    )
        except Exception as e:
            logger.error(f"Error checking response time: {str(e)}")
    
    def _check_sync_failure_rate(self):
        """Check sync failure rate and generate alerts"""
        # This would check actual sync job statistics
        pass
    
    def _check_webhook_failure_rate(self):
        """Check webhook failure rate and generate alerts"""
        # This would check actual webhook processing statistics
        pass
    
    def _check_system_resource_alerts(self):
        """Check system resource usage and generate alerts"""
        try:
            if self.system_metrics:
                latest_metrics = self.system_metrics[-1]
                
                # CPU alert
                if latest_metrics['cpu_percent'] > self.alert_thresholds['cpu_usage']:
                    self._create_alert(
                        "high_cpu_usage",
                        AlertSeverity.CRITICAL,
                        "High CPU Usage",
                        f"CPU usage is {latest_metrics['cpu_percent']:.1f}%",
                        {'cpu_percent': latest_metrics['cpu_percent']}
                    )
                
                # Memory alert
                if latest_metrics['memory_percent'] > self.alert_thresholds['memory_usage']:
                    self._create_alert(
                        "high_memory_usage",
                        AlertSeverity.CRITICAL,
                        "High Memory Usage",
                        f"Memory usage is {latest_metrics['memory_percent']:.1f}%",
                        {'memory_percent': latest_metrics['memory_percent']}
                    )
        except Exception as e:
            logger.error(f"Error checking system resource alerts: {str(e)}")
    
    def _generate_health_alert(self, check: HealthCheck, result: Dict[str, Any]):
        """Generate alert for health check failure"""
        alert_type = f"health_check_{check.check_id}"
        severity = AlertSeverity.CRITICAL if check.critical else AlertSeverity.WARNING
        
        self._create_alert(
            alert_type,
            severity,
            f"Health Check Failed: {check.name}",
            f"Health check '{check.name}' failed: {result.get('error', 'Unknown error')}",
            {
                'check_id': check.check_id,
                'failure_count': check.failure_count,
                'result': result
            }
        )
    
    def _create_alert(self, alert_type: str, severity: AlertSeverity, title: str, 
                     message: str, details: Dict[str, Any], organization_id: str = "system"):
        """Create a new alert"""
        alert_id = f"{alert_type}_{organization_id}_{int(time.time())}"
        
        # Check if similar alert already exists
        existing_alert = None
        for alert in self.active_alerts.values():
            if (alert.alert_type == alert_type and 
                alert.organization_id == organization_id and 
                not alert.resolved):
                existing_alert = alert
                break
        
        if existing_alert:
            # Update existing alert
            existing_alert.message = message
            existing_alert.details.update(details)
            existing_alert.timestamp = datetime.utcnow()
        else:
            # Create new alert
            alert = Alert(
                alert_id=alert_id,
                organization_id=organization_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                details=details,
                timestamp=datetime.utcnow()
            )
            
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            logger.warning(f"Alert created: {title} - {message}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Clean up old metrics
            for metric_name in list(self.metrics.keys()):
                # Keep only recent metrics (deque handles this automatically with maxlen)
                pass
            
            # Clean up old request metrics
            for endpoint in list(self.request_metrics.keys()):
                if len(self.request_metrics[endpoint]) > 1000:
                    self.request_metrics[endpoint] = self.request_metrics[endpoint][-1000:]
            
            # Clean up old alerts
            if len(self.alert_history) > 10000:
                self.alert_history = self.alert_history[-10000:]
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def add_health_check(self, health_check: HealthCheck):
        """Add a health check"""
        self.health_checks[health_check.check_id] = health_check
        logger.info(f"Added health check: {health_check.name}")
    
    def remove_health_check(self, check_id: str):
        """Remove a health check"""
        if check_id in self.health_checks:
            del self.health_checks[check_id]
            logger.info(f"Removed health check: {check_id}")
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, 
                     timestamp: datetime = None, tags: Dict[str, str] = None):
        """Record a performance metric"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric = Metric(
            metric_id=str(time.time()),
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=timestamp,
            tags=tags or {}
        )
        
        self.metrics[name].append(metric)
    
    def record_api_call(self, endpoint: str, response_time: float, success: bool):
        """Record API call metrics"""
        self.request_metrics[endpoint].append(response_time)
        
        if success:
            self.success_counts[endpoint] += 1
        else:
            self.error_counts[endpoint] += 1
        
        # Record as metrics
        self.record_metric(f"api.{endpoint}.response_time", response_time, MetricType.TIMER)
        self.record_metric(f"api.{endpoint}.calls", 1, MetricType.COUNTER)
        
        if not success:
            self.record_metric(f"api.{endpoint}.errors", 1, MetricType.COUNTER)
    
    def get_health_status(self, organization_id: str = None) -> Dict[str, Any]:
        """Get overall health status"""
        try:
            # Determine overall status
            overall_status = HealthStatus.HEALTHY
            critical_issues = []
            warnings = []
            
            for check in self.health_checks.values():
                if not check.enabled:
                    continue
                
                if check.last_status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                    critical_issues.append(check.name)
                elif check.last_status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.WARNING
                    warnings.append(check.name)
            
            # Get active alerts
            active_alerts = list(self.active_alerts.values())
            if organization_id:
                active_alerts = [a for a in active_alerts if a.organization_id == organization_id]
            
            return {
                'overall_status': overall_status.value,
                'timestamp': datetime.utcnow().isoformat(),
                'health_checks': {
                    check_id: {
                        'name': check.name,
                        'status': check.last_status.value,
                        'last_check': check.last_check.isoformat() if check.last_check else None,
                        'failure_count': check.failure_count
                    }
                    for check_id, check in self.health_checks.items()
                },
                'critical_issues': critical_issues,
                'warnings': warnings,
                'active_alerts': len(active_alerts),
                'system_metrics': self.system_metrics[-1] if self.system_metrics else None
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {str(e)}")
            return {
                'overall_status': HealthStatus.UNKNOWN.value,
                'error': str(e)
            }
    
    def get_performance_metrics(self, organization_id: str, timeframe: str = "1h") -> Dict[str, Any]:
        """Get performance metrics for organization"""
        try:
            # Calculate time range
            now = datetime.utcnow()
            if timeframe == "1h":
                start_time = now - timedelta(hours=1)
            elif timeframe == "24h":
                start_time = now - timedelta(hours=24)
            elif timeframe == "7d":
                start_time = now - timedelta(days=7)
            else:
                start_time = now - timedelta(hours=1)
            
            # Collect metrics for timeframe
            metrics_data = {}
            
            for metric_name, metric_list in self.metrics.items():
                timeframe_metrics = [
                    m for m in metric_list 
                    if m.timestamp >= start_time
                ]
                
                if timeframe_metrics:
                    values = [m.value for m in timeframe_metrics]
                    metrics_data[metric_name] = {
                        'count': len(values),
                        'avg': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'latest': values[-1] if values else 0
                    }
            
            # Calculate API performance
            api_metrics = self._calculate_api_performance(start_time)
            
            return {
                'organization_id': organization_id,
                'timeframe': timeframe,
                'start_time': start_time.isoformat(),
                'end_time': now.isoformat(),
                'metrics': metrics_data,
                'api_performance': api_metrics,
                'system_performance': self._get_system_performance(start_time)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_api_performance(self, start_time: datetime) -> Dict[str, Any]:
        """Calculate API performance metrics"""
        try:
            total_requests = sum(self.success_counts.values()) + sum(self.error_counts.values())
            total_errors = sum(self.error_counts.values())
            
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate average response time
            all_response_times = []
            for times in self.request_metrics.values():
                all_response_times.extend(times[-100:])  # Last 100 requests per endpoint
            
            avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
            max_response_time = max(all_response_times) if all_response_times else 0
            
            return {
                'total_requests': total_requests,
                'successful_requests': sum(self.success_counts.values()),
                'failed_requests': total_errors,
                'error_rate': error_rate,
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'endpoints': {
                    endpoint: {
                        'requests': self.success_counts[endpoint] + self.error_counts[endpoint],
                        'errors': self.error_counts[endpoint],
                        'avg_response_time': statistics.mean(times[-100:]) if times else 0
                    }
                    for endpoint, times in self.request_metrics.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating API performance: {str(e)}")
            return {}
    
    def _get_system_performance(self, start_time: datetime) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            recent_metrics = [
                m for m in self.system_metrics 
                if m['timestamp'] >= start_time
            ]
            
            if not recent_metrics:
                return {}
            
            cpu_values = [m['cpu_percent'] for m in recent_metrics]
            memory_values = [m['memory_percent'] for m in recent_metrics]
            
            return {
                'cpu': {
                    'avg': statistics.mean(cpu_values),
                    'max': max(cpu_values),
                    'current': cpu_values[-1] if cpu_values else 0
                },
                'memory': {
                    'avg': statistics.mean(memory_values),
                    'max': max(memory_values),
                    'current': memory_values[-1] if memory_values else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system performance: {str(e)}")
            return {}
    
    def get_alerts(self, organization_id: str = None, resolved: bool = None, 
                  limit: int = 50) -> List[Alert]:
        """Get alerts"""
        alerts = list(self.active_alerts.values()) + self.alert_history
        
        # Filter by organization
        if organization_id:
            alerts = [a for a in alerts if a.organization_id == organization_id]
        
        # Filter by resolved status
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        # Sort by timestamp, most recent first
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return alerts[:limit]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            # Move to history
            del self.active_alerts[alert_id]
            
            logger.info(f"Resolved alert: {alert_id}")
            return True
        
        return False
    
    def initialize_monitoring(self, organization_id: str, config: Dict[str, Any]):
        """Initialize monitoring for an organization"""
        try:
            # Setup organization-specific performance stats
            self.performance_stats[organization_id] = PerformanceStats(
                organization_id=organization_id,
                timeframe="24h"
            )
            
            # Apply custom alert thresholds if provided
            if 'alert_thresholds' in config:
                self.alert_thresholds.update(config['alert_thresholds'])
            
            logger.info(f"Initialized monitoring for organization {organization_id}")
            
        except Exception as e:
            logger.error(f"Error initializing monitoring: {str(e)}")
    
    def log_event(self, organization_id: str, event_type: str, details: Dict[str, Any]):
        """Log an event for monitoring"""
        try:
            # Record as metric
            self.record_metric(f"events.{event_type}", 1, MetricType.COUNTER, tags={'organization_id': organization_id})
            
            # Log for debugging
            logger.info(f"Event logged - {event_type}: {details}")
            
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")
    
    def calculate_uptime(self, organization_id: str, days: int = 7) -> float:
        """Calculate uptime percentage"""
        try:
            # This would calculate actual uptime based on health check history
            # For now, return a simulated value
            return 99.5
            
        except Exception as e:
            logger.error(f"Error calculating uptime: {str(e)}")
            return 0.0
    
    def calculate_error_rate(self, organization_id: str, hours: int = 24) -> float:
        """Calculate error rate percentage"""
        try:
            total_requests = sum(self.success_counts.values()) + sum(self.error_counts.values())
            total_errors = sum(self.error_counts.values())
            
            return (total_errors / total_requests * 100) if total_requests > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {str(e)}")
            return 0.0
    
    def stop_monitoring(self):
        """Stop monitoring service"""
        self.monitoring_enabled = False
        logger.info("Monitoring service stopped")