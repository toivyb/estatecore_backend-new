"""
Advanced API Monitoring and Analytics Service for EstateCore API Gateway
Real-time metrics, performance monitoring, SLA tracking, and comprehensive analytics
"""

import os
import time
import logging
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics
import uuid
import hashlib
from concurrent.futures import ThreadPoolExecutor
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SLAMetric(Enum):
    """SLA metrics to track"""
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

@dataclass
class APIMetric:
    """Individual API metric"""
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RequestMetrics:
    """Comprehensive request metrics"""
    request_id: str
    timestamp: datetime
    client_id: Optional[str]
    endpoint: str
    method: str
    version: str
    response_status: int
    response_time: float
    request_size: int
    response_size: int
    ip_address: str
    user_agent: str
    error_message: Optional[str] = None
    cache_hit: bool = False
    upstream_service: Optional[str] = None
    rate_limited: bool = False
    authentication_time: float = 0.0
    authorization_time: float = 0.0
    transformation_time: float = 0.0
    circuit_breaker_state: Optional[str] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics summary"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    total_bandwidth: int = 0

@dataclass
class SLATarget:
    """SLA target definition"""
    metric: SLAMetric
    threshold: float
    operator: str  # ">=", "<=", ">", "<"
    time_window: int  # seconds
    description: str

@dataclass
class SLAViolation:
    """SLA violation record"""
    violation_id: str
    sla_target: SLATarget
    actual_value: float
    timestamp: datetime
    duration: int  # seconds
    affected_requests: int
    severity: AlertSeverity
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class Alert:
    """System alert"""
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    timestamp: datetime
    source: str
    labels: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TimeSeriesData:
    """Time series data storage"""
    
    def __init__(self, max_points: int = 10000):
        self.data = deque(maxlen=max_points)
        self.lock = threading.Lock()
    
    def add_point(self, timestamp: datetime, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a data point"""
        with self.lock:
            self.data.append({
                'timestamp': timestamp,
                'value': value,
                'labels': labels or {}
            })
    
    def get_points(self, start_time: Optional[datetime] = None, 
                  end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get data points within time range"""
        with self.lock:
            points = list(self.data)
        
        if start_time:
            points = [p for p in points if p['timestamp'] >= start_time]
        
        if end_time:
            points = [p for p in points if p['timestamp'] <= end_time]
        
        return points
    
    def get_latest(self, count: int = 1) -> List[Dict[str, Any]]:
        """Get latest data points"""
        with self.lock:
            return list(self.data)[-count:] if self.data else []

class MetricsAggregator:
    """Metrics aggregation engine"""
    
    def __init__(self):
        self.aggregated_metrics = defaultdict(lambda: defaultdict(list))
        self.lock = threading.Lock()
    
    def aggregate_counter(self, metrics: List[APIMetric], time_window: int = 60) -> Dict[str, float]:
        """Aggregate counter metrics"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=time_window)
        
        aggregated = defaultdict(float)
        for metric in metrics:
            if metric.timestamp >= cutoff and metric.metric_type == MetricType.COUNTER:
                key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in metric.labels.items())}"
                aggregated[key] += metric.value
        
        return dict(aggregated)
    
    def aggregate_gauge(self, metrics: List[APIMetric], time_window: int = 60) -> Dict[str, float]:
        """Aggregate gauge metrics (latest value)"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=time_window)
        
        aggregated = {}
        for metric in metrics:
            if metric.timestamp >= cutoff and metric.metric_type == MetricType.GAUGE:
                key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in metric.labels.items())}"
                aggregated[key] = metric.value
        
        return aggregated
    
    def aggregate_histogram(self, metrics: List[APIMetric], time_window: int = 60) -> Dict[str, Dict[str, float]]:
        """Aggregate histogram metrics"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=time_window)
        
        histogram_data = defaultdict(list)
        for metric in metrics:
            if metric.timestamp >= cutoff and metric.metric_type == MetricType.HISTOGRAM:
                key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in metric.labels.items())}"
                histogram_data[key].append(metric.value)
        
        aggregated = {}
        for key, values in histogram_data.items():
            if values:
                aggregated[key] = {
                    'count': len(values),
                    'sum': sum(values),
                    'avg': statistics.mean(values),
                    'p50': statistics.median(values),
                    'p95': self._percentile(values, 95),
                    'p99': self._percentile(values, 99),
                    'min': min(values),
                    'max': max(values)
                }
        
        return aggregated
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        return sorted_values[index]

class SLAManager:
    """SLA monitoring and violation detection"""
    
    def __init__(self):
        self.sla_targets: List[SLATarget] = []
        self.violations: List[SLAViolation] = []
        self.lock = threading.Lock()
        
        # Initialize default SLA targets
        self._initialize_default_slas()
    
    def _initialize_default_slas(self):
        """Initialize default SLA targets"""
        default_slas = [
            SLATarget(
                metric=SLAMetric.AVAILABILITY,
                threshold=99.9,
                operator=">=",
                time_window=3600,
                description="API availability should be >= 99.9% over 1 hour"
            ),
            SLATarget(
                metric=SLAMetric.RESPONSE_TIME,
                threshold=1000.0,
                operator="<=",
                time_window=300,
                description="95th percentile response time should be <= 1000ms over 5 minutes"
            ),
            SLATarget(
                metric=SLAMetric.ERROR_RATE,
                threshold=1.0,
                operator="<=",
                time_window=600,
                description="Error rate should be <= 1% over 10 minutes"
            ),
            SLATarget(
                metric=SLAMetric.THROUGHPUT,
                threshold=100.0,
                operator=">=",
                time_window=300,
                description="Minimum throughput of 100 req/min over 5 minutes"
            )
        ]
        
        self.sla_targets.extend(default_slas)
    
    def add_sla_target(self, target: SLATarget):
        """Add SLA target"""
        with self.lock:
            self.sla_targets.append(target)
    
    def check_sla_compliance(self, metrics: List[RequestMetrics]) -> List[SLAViolation]:
        """Check SLA compliance and detect violations"""
        violations = []
        now = datetime.utcnow()
        
        for target in self.sla_targets:
            cutoff = now - timedelta(seconds=target.time_window)
            relevant_metrics = [m for m in metrics if m.timestamp >= cutoff]
            
            if not relevant_metrics:
                continue
            
            actual_value = self._calculate_sla_metric(target.metric, relevant_metrics)
            is_violation = self._check_threshold(actual_value, target.threshold, target.operator)
            
            if is_violation:
                violation = SLAViolation(
                    violation_id=str(uuid.uuid4()),
                    sla_target=target,
                    actual_value=actual_value,
                    timestamp=now,
                    duration=target.time_window,
                    affected_requests=len(relevant_metrics),
                    severity=self._determine_severity(target.metric, actual_value, target.threshold)
                )
                violations.append(violation)
        
        with self.lock:
            self.violations.extend(violations)
        
        return violations
    
    def _calculate_sla_metric(self, metric: SLAMetric, request_metrics: List[RequestMetrics]) -> float:
        """Calculate SLA metric value"""
        if not request_metrics:
            return 0.0
        
        if metric == SLAMetric.AVAILABILITY:
            successful = sum(1 for m in request_metrics if 200 <= m.response_status < 400)
            return (successful / len(request_metrics)) * 100
        
        elif metric == SLAMetric.RESPONSE_TIME:
            response_times = [m.response_time * 1000 for m in request_metrics]  # Convert to ms
            response_times.sort()
            p95_index = int(0.95 * len(response_times))
            return response_times[p95_index] if response_times else 0.0
        
        elif metric == SLAMetric.ERROR_RATE:
            errors = sum(1 for m in request_metrics if m.response_status >= 400)
            return (errors / len(request_metrics)) * 100
        
        elif metric == SLAMetric.THROUGHPUT:
            time_span = max(m.timestamp for m in request_metrics) - min(m.timestamp for m in request_metrics)
            time_minutes = max(time_span.total_seconds() / 60, 1)
            return len(request_metrics) / time_minutes
        
        return 0.0
    
    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value violates threshold"""
        if operator == ">=":
            return value < threshold
        elif operator == "<=":
            return value > threshold
        elif operator == ">":
            return value <= threshold
        elif operator == "<":
            return value >= threshold
        return False
    
    def _determine_severity(self, metric: SLAMetric, actual: float, threshold: float) -> AlertSeverity:
        """Determine alert severity based on metric deviation"""
        if metric == SLAMetric.AVAILABILITY:
            if actual < threshold - 5:
                return AlertSeverity.CRITICAL
            elif actual < threshold - 1:
                return AlertSeverity.ERROR
            else:
                return AlertSeverity.WARNING
        
        elif metric == SLAMetric.RESPONSE_TIME:
            deviation = (actual - threshold) / threshold
            if deviation > 1.0:  # 100% over threshold
                return AlertSeverity.CRITICAL
            elif deviation > 0.5:  # 50% over threshold
                return AlertSeverity.ERROR
            else:
                return AlertSeverity.WARNING
        
        elif metric == SLAMetric.ERROR_RATE:
            if actual > threshold * 5:
                return AlertSeverity.CRITICAL
            elif actual > threshold * 2:
                return AlertSeverity.ERROR
            else:
                return AlertSeverity.WARNING
        
        return AlertSeverity.WARNING

class AlertManager:
    """Alert management system"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.notification_queue = queue.Queue()
        
        # Initialize default alert rules
        self._initialize_default_rules()
        
        # Start notification worker
        self.notification_worker = threading.Thread(target=self._notification_worker, daemon=True)
        self.notification_worker.start()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            {
                'name': 'high_error_rate',
                'condition': 'error_rate > 5',
                'severity': AlertSeverity.ERROR,
                'description': 'Error rate exceeds 5%'
            },
            {
                'name': 'slow_response_time',
                'condition': 'avg_response_time > 2000',
                'severity': AlertSeverity.WARNING,
                'description': 'Average response time exceeds 2 seconds'
            },
            {
                'name': 'high_traffic',
                'condition': 'requests_per_second > 1000',
                'severity': AlertSeverity.INFO,
                'description': 'High traffic detected'
            },
            {
                'name': 'circuit_breaker_open',
                'condition': 'circuit_breaker_open == true',
                'severity': AlertSeverity.CRITICAL,
                'description': 'Circuit breaker is open'
            }
        ]
        
        self.alert_rules.extend(default_rules)
    
    def create_alert(self, title: str, description: str, severity: AlertSeverity,
                    source: str, labels: Optional[Dict[str, str]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """Create a new alert"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            title=title,
            description=description,
            severity=severity,
            timestamp=datetime.utcnow(),
            source=source,
            labels=labels or {},
            metadata=metadata or {}
        )
        
        with self.lock:
            self.alerts.append(alert)
        
        # Queue for notification
        self.notification_queue.put(alert)
        
        logger.warning(f"Alert created: {title} - {description}")
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    logger.info(f"Alert resolved: {alert.title}")
                    return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        with self.lock:
            return [alert for alert in self.alerts if not alert.resolved]
    
    def _notification_worker(self):
        """Background worker for alert notifications"""
        while True:
            try:
                alert = self.notification_queue.get(timeout=1)
                self._send_notification(alert)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Alert notification failed: {str(e)}")
    
    def _send_notification(self, alert: Alert):
        """Send alert notification"""
        # Implementation would send notifications via email, Slack, etc.
        # For now, just log the alert
        logger.error(f"ALERT [{alert.severity.value.upper()}]: {alert.title} - {alert.description}")

class APIMonitoringService:
    """Main API monitoring and analytics service"""
    
    def __init__(self):
        self.request_metrics: List[RequestMetrics] = []
        self.api_metrics: List[APIMetric] = []
        self.time_series_data: Dict[str, TimeSeriesData] = defaultdict(TimeSeriesData)
        self.aggregator = MetricsAggregator()
        self.sla_manager = SLAManager()
        self.alert_manager = AlertManager()
        self.lock = threading.Lock()
        
        # Background threads
        self.monitoring_active = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_data, daemon=True)
        self.cleanup_thread.start()
        
        self.sla_check_thread = threading.Thread(target=self._periodic_sla_check, daemon=True)
        self.sla_check_thread.start()
    
    def record_request(self, request_metrics: RequestMetrics):
        """Record request metrics"""
        with self.lock:
            self.request_metrics.append(request_metrics)
        
        # Record time series data
        self._record_time_series_metrics(request_metrics)
        
        # Check for immediate alerts
        self._check_request_alerts(request_metrics)
    
    def record_metric(self, metric: APIMetric):
        """Record API metric"""
        with self.lock:
            self.api_metrics.append(metric)
        
        # Add to time series
        key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in metric.labels.items())}"
        self.time_series_data[key].add_point(metric.timestamp, metric.value, metric.labels)
    
    def _record_time_series_metrics(self, request_metrics: RequestMetrics):
        """Record request metrics as time series data"""
        timestamp = request_metrics.timestamp
        
        # Response time
        self.time_series_data['response_time'].add_point(
            timestamp, request_metrics.response_time,
            {'endpoint': request_metrics.endpoint, 'method': request_metrics.method}
        )
        
        # Request count
        self.time_series_data['request_count'].add_point(
            timestamp, 1,
            {'endpoint': request_metrics.endpoint, 'status': str(request_metrics.response_status)}
        )
        
        # Error count
        if request_metrics.response_status >= 400:
            self.time_series_data['error_count'].add_point(
                timestamp, 1,
                {'endpoint': request_metrics.endpoint, 'status': str(request_metrics.response_status)}
            )
        
        # Bandwidth
        total_size = request_metrics.request_size + request_metrics.response_size
        self.time_series_data['bandwidth'].add_point(
            timestamp, total_size,
            {'endpoint': request_metrics.endpoint, 'client_id': request_metrics.client_id or 'anonymous'}
        )
    
    def _check_request_alerts(self, request_metrics: RequestMetrics):
        """Check for alerts based on request metrics"""
        # High response time
        if request_metrics.response_time > 5.0:  # 5 seconds
            self.alert_manager.create_alert(
                "High Response Time",
                f"Response time of {request_metrics.response_time:.2f}s for {request_metrics.endpoint}",
                AlertSeverity.WARNING,
                "api_monitoring",
                {
                    'endpoint': request_metrics.endpoint,
                    'client_id': request_metrics.client_id or 'anonymous',
                    'response_time': str(request_metrics.response_time)
                }
            )
        
        # Server errors
        if request_metrics.response_status >= 500:
            self.alert_manager.create_alert(
                "Server Error",
                f"HTTP {request_metrics.response_status} error for {request_metrics.endpoint}",
                AlertSeverity.ERROR,
                "api_monitoring",
                {
                    'endpoint': request_metrics.endpoint,
                    'status_code': str(request_metrics.response_status),
                    'error_message': request_metrics.error_message or 'Unknown error'
                }
            )
    
    def get_performance_metrics(self, time_window: int = 3600, 
                              endpoint: Optional[str] = None,
                              client_id: Optional[str] = None) -> PerformanceMetrics:
        """Get performance metrics for specified time window"""
        cutoff = datetime.utcnow() - timedelta(seconds=time_window)
        
        with self.lock:
            filtered_metrics = [
                m for m in self.request_metrics
                if m.timestamp >= cutoff
            ]
        
        if endpoint:
            filtered_metrics = [m for m in filtered_metrics if m.endpoint == endpoint]
        
        if client_id:
            filtered_metrics = [m for m in filtered_metrics if m.client_id == client_id]
        
        if not filtered_metrics:
            return PerformanceMetrics()
        
        total_requests = len(filtered_metrics)
        successful_requests = sum(1 for m in filtered_metrics if 200 <= m.response_status < 400)
        failed_requests = total_requests - successful_requests
        
        response_times = [m.response_time for m in filtered_metrics]
        cache_hits = sum(1 for m in filtered_metrics if m.cache_hit)
        total_bandwidth = sum(m.request_size + m.response_size for m in filtered_metrics)
        
        # Calculate time-based metrics
        time_span = max(m.timestamp for m in filtered_metrics) - min(m.timestamp for m in filtered_metrics)
        time_seconds = max(time_span.total_seconds(), 1)
        requests_per_second = total_requests / time_seconds
        
        return PerformanceMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=statistics.mean(response_times),
            p50_response_time=statistics.median(response_times),
            p95_response_time=self._percentile(response_times, 95),
            p99_response_time=self._percentile(response_times, 99),
            requests_per_second=requests_per_second,
            error_rate=(failed_requests / total_requests) * 100,
            cache_hit_rate=(cache_hits / total_requests) * 100 if total_requests > 0 else 0,
            total_bandwidth=total_bandwidth
        )
    
    def get_endpoint_analytics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get analytics by endpoint"""
        cutoff = datetime.utcnow() - timedelta(seconds=time_window)
        
        with self.lock:
            filtered_metrics = [
                m for m in self.request_metrics
                if m.timestamp >= cutoff
            ]
        
        endpoint_stats = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'error_statuses': defaultdict(int),
            'clients': set(),
            'bandwidth': 0
        })
        
        for metric in filtered_metrics:
            endpoint = metric.endpoint
            stats = endpoint_stats[endpoint]
            
            stats['total_requests'] += 1
            stats['response_times'].append(metric.response_time)
            stats['bandwidth'] += metric.request_size + metric.response_size
            
            if 200 <= metric.response_status < 400:
                stats['successful_requests'] += 1
            else:
                stats['failed_requests'] += 1
                stats['error_statuses'][metric.response_status] += 1
            
            if metric.client_id:
                stats['clients'].add(metric.client_id)
        
        # Process analytics
        analytics = {}
        for endpoint, stats in endpoint_stats.items():
            if stats['response_times']:
                analytics[endpoint] = {
                    'total_requests': stats['total_requests'],
                    'success_rate': (stats['successful_requests'] / stats['total_requests']) * 100,
                    'average_response_time': statistics.mean(stats['response_times']),
                    'p95_response_time': self._percentile(stats['response_times'], 95),
                    'unique_clients': len(stats['clients']),
                    'total_bandwidth': stats['bandwidth'],
                    'top_errors': dict(sorted(stats['error_statuses'].items(), 
                                            key=lambda x: x[1], reverse=True)[:5])
                }
        
        return analytics
    
    def get_client_analytics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get analytics by client"""
        cutoff = datetime.utcnow() - timedelta(seconds=time_window)
        
        with self.lock:
            filtered_metrics = [
                m for m in self.request_metrics
                if m.timestamp >= cutoff and m.client_id
            ]
        
        client_stats = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'endpoints': defaultdict(int),
            'response_times': [],
            'bandwidth': 0,
            'rate_limited': 0
        })
        
        for metric in filtered_metrics:
            client_id = metric.client_id
            if not client_id:
                continue
            
            stats = client_stats[client_id]
            stats['total_requests'] += 1
            stats['response_times'].append(metric.response_time)
            stats['bandwidth'] += metric.request_size + metric.response_size
            stats['endpoints'][metric.endpoint] += 1
            
            if 200 <= metric.response_status < 400:
                stats['successful_requests'] += 1
            
            if metric.rate_limited:
                stats['rate_limited'] += 1
        
        # Process analytics
        analytics = {}
        for client_id, stats in client_stats.items():
            if stats['response_times']:
                analytics[client_id] = {
                    'total_requests': stats['total_requests'],
                    'success_rate': (stats['successful_requests'] / stats['total_requests']) * 100,
                    'average_response_time': statistics.mean(stats['response_times']),
                    'total_bandwidth': stats['bandwidth'],
                    'rate_limited_requests': stats['rate_limited'],
                    'most_used_endpoints': dict(sorted(stats['endpoints'].items(), 
                                                     key=lambda x: x[1], reverse=True)[:10])
                }
        
        return analytics
    
    def get_sla_status(self) -> Dict[str, Any]:
        """Get current SLA status"""
        cutoff = datetime.utcnow() - timedelta(hours=1)  # Last hour
        
        with self.lock:
            recent_metrics = [
                m for m in self.request_metrics
                if m.timestamp >= cutoff
            ]
        
        sla_status = {}
        for target in self.sla_manager.sla_targets:
            actual_value = self.sla_manager._calculate_sla_metric(target.metric, recent_metrics)
            is_compliant = not self.sla_manager._check_threshold(
                actual_value, target.threshold, target.operator
            )
            
            sla_status[target.metric.value] = {
                'target': target.threshold,
                'actual': actual_value,
                'compliant': is_compliant,
                'description': target.description
            }
        
        return sla_status
    
    def get_time_series_data(self, metric_name: str, start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get time series data for a metric"""
        if metric_name not in self.time_series_data:
            return []
        
        return self.time_series_data[metric_name].get_points(start_time, end_time)
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        return sorted_values[index]
    
    def _cleanup_old_data(self):
        """Clean up old metrics data"""
        while self.monitoring_active:
            try:
                cutoff = datetime.utcnow() - timedelta(days=7)  # Keep 7 days
                
                with self.lock:
                    self.request_metrics = [
                        m for m in self.request_metrics
                        if m.timestamp > cutoff
                    ]
                    
                    self.api_metrics = [
                        m for m in self.api_metrics
                        if m.timestamp > cutoff
                    ]
                
                # Clean up resolved alerts older than 30 days
                alert_cutoff = datetime.utcnow() - timedelta(days=30)
                self.alert_manager.alerts = [
                    a for a in self.alert_manager.alerts
                    if not a.resolved or (a.resolved_at and a.resolved_at > alert_cutoff)
                ]
                
                time.sleep(3600)  # Run cleanup every hour
                
            except Exception as e:
                logger.error(f"Data cleanup failed: {str(e)}")
                time.sleep(3600)
    
    def _periodic_sla_check(self):
        """Periodic SLA compliance check"""
        while self.monitoring_active:
            try:
                with self.lock:
                    recent_metrics = self.request_metrics[-1000:]  # Check last 1000 requests
                
                violations = self.sla_manager.check_sla_compliance(recent_metrics)
                
                for violation in violations:
                    self.alert_manager.create_alert(
                        f"SLA Violation: {violation.sla_target.metric.value}",
                        f"{violation.sla_target.description}. Actual: {violation.actual_value:.2f}, Target: {violation.sla_target.threshold}",
                        violation.severity,
                        "sla_manager",
                        {
                            'metric': violation.sla_target.metric.value,
                            'actual_value': str(violation.actual_value),
                            'target_value': str(violation.sla_target.threshold)
                        }
                    )
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"SLA check failed: {str(e)}")
                time.sleep(300)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        current_performance = self.get_performance_metrics(3600)  # Last hour
        endpoint_analytics = self.get_endpoint_analytics(3600)
        client_analytics = self.get_client_analytics(3600)
        sla_status = self.get_sla_status()
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            'performance': asdict(current_performance),
            'endpoint_analytics': endpoint_analytics,
            'client_analytics': client_analytics,
            'sla_status': sla_status,
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'timestamp': datetime.utcnow().isoformat()
        }

# Global monitoring service instance
_monitoring_service = None

def get_monitoring_service() -> APIMonitoringService:
    """Get or create the API monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = APIMonitoringService()
    return _monitoring_service