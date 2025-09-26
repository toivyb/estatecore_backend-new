"""
Yardi Monitoring Service

Comprehensive monitoring, alerting, and performance tracking for the Yardi integration
with health checks, metrics collection, and proactive issue detection.
"""

import os
import logging
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

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

class MonitoringEventType(Enum):
    """Monitoring event types"""
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    API_ERROR = "api_error"
    WEBHOOK_RECEIVED = "webhook_received"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_QUALITY_ISSUE = "data_quality_issue"

@dataclass
class MonitoringEvent:
    """Monitoring event record"""
    event_id: str
    organization_id: str
    event_type: MonitoringEventType
    severity: AlertSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_notes: Optional[str] = None

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_name: str
    metric_type: MetricType
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class HealthCheck:
    """Health check configuration"""
    check_name: str
    organization_id: str
    check_function: Callable
    interval_seconds: int = 300  # 5 minutes
    timeout_seconds: int = 30
    failure_threshold: int = 3
    enabled: bool = True
    last_run: Optional[datetime] = None
    consecutive_failures: int = 0
    last_result: Optional[Dict[str, Any]] = None

@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    organization_id: str
    rule_name: str
    condition: str
    severity: AlertSeverity
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)
    cooldown_minutes: int = 30
    last_triggered: Optional[datetime] = None

class YardiMonitoringService:
    """Yardi Monitoring Service for comprehensive system monitoring"""
    
    def __init__(self):
        # Event and metric storage
        self.events: Dict[str, MonitoringEvent] = {}
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        
        # Performance tracking
        self.request_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.uptime_tracker: Dict[str, List[datetime]] = defaultdict(list)
        
        # Monitoring state
        self.monitoring_enabled = True
        self.health_check_thread = None
        self.metric_aggregation_thread = None
        
        # Alert channels
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Initialize default monitoring
        self._setup_default_health_checks()
        self._setup_default_alert_rules()
        self._start_monitoring_threads()
        
        logger.info("Yardi Monitoring Service initialized")
    
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        # These would be registered for each organization
        pass
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        # Default alert rules for common issues
        default_rules = [
            {
                "rule_name": "High Error Rate",
                "condition": "error_rate > 5%",
                "severity": AlertSeverity.WARNING
            },
            {
                "rule_name": "Sync Failure",
                "condition": "sync_failed",
                "severity": AlertSeverity.ERROR
            },
            {
                "rule_name": "Connection Lost",
                "condition": "connection_lost",
                "severity": AlertSeverity.CRITICAL
            }
        ]
        
        for rule_config in default_rules:
            rule_id = f"default_{rule_config['rule_name'].lower().replace(' ', '_')}"
            rule = AlertRule(
                rule_id=rule_id,
                organization_id="default",
                rule_name=rule_config['rule_name'],
                condition=rule_config['condition'],
                severity=rule_config['severity']
            )
            self.alert_rules[rule_id] = rule
    
    def _start_monitoring_threads(self):
        """Start monitoring background threads"""
        if self.monitoring_enabled:
            self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_check_thread.start()
            
            self.metric_aggregation_thread = threading.Thread(target=self._metric_aggregation_loop, daemon=True)
            self.metric_aggregation_thread.start()
    
    # =====================================================
    # EVENT LOGGING
    # =====================================================
    
    def log_event(self, organization_id: str, event_type: MonitoringEventType,
                 message: str, severity: AlertSeverity = AlertSeverity.INFO,
                 details: Optional[Dict[str, Any]] = None):
        """Log monitoring event"""
        
        event_id = f"event_{uuid.uuid4().hex[:8]}"
        
        event = MonitoringEvent(
            event_id=event_id,
            organization_id=organization_id,
            event_type=event_type,
            severity=severity,
            message=message,
            details=details or {}
        )
        
        self.events[event_id] = event
        
        # Check alert rules
        self._check_alert_rules(event)
        
        # Log to system logger
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(severity, logging.INFO)
        
        logger.log(log_level, f"[{organization_id}] {event_type.value}: {message}")
    
    def get_events(self, organization_id: str, 
                  event_types: Optional[List[MonitoringEventType]] = None,
                  severity_filter: Optional[AlertSeverity] = None,
                  limit: int = 100) -> List[MonitoringEvent]:
        """Get monitoring events"""
        
        events = [
            event for event in self.events.values()
            if event.organization_id == organization_id
        ]
        
        # Apply filters
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        
        if severity_filter:
            events = [e for e in events if e.severity == severity_filter]
        
        # Sort by timestamp, most recent first
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def resolve_event(self, event_id: str, resolution_notes: str) -> Dict[str, Any]:
        """Resolve a monitoring event"""
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        
        event.resolved = True
        event.resolution_notes = resolution_notes
        
        return {"success": True, "message": "Event resolved"}
    
    # =====================================================
    # METRICS COLLECTION
    # =====================================================
    
    def record_metric(self, organization_id: str, metric_name: str, 
                     value: float, metric_type: MetricType = MetricType.GAUGE,
                     tags: Optional[Dict[str, str]] = None):
        """Record performance metric"""
        
        metric = PerformanceMetric(
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            tags=tags or {}
        )
        
        metric_key = f"{organization_id}:{metric_name}"
        self.metrics[metric_key].append(metric)
        
        # Check for performance alerts
        self._check_performance_alerts(organization_id, metric_name, value)
    
    def get_metrics(self, organization_id: str, metric_name: Optional[str] = None,
                   time_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Get performance metrics"""
        
        if metric_name:
            metric_key = f"{organization_id}:{metric_name}"
            metrics = list(self.metrics.get(metric_key, []))
        else:
            metrics = []
            for key, metric_list in self.metrics.items():
                if key.startswith(f"{organization_id}:"):
                    metrics.extend(metric_list)
        
        # Apply time range filter
        if time_range and 'start' in time_range and 'end' in time_range:
            metrics = [
                m for m in metrics
                if time_range['start'] <= m.timestamp <= time_range['end']
            ]
        
        # Calculate aggregations
        if metrics:
            values = [m.value for m in metrics]
            aggregations = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1] if values else 0
            }
        else:
            aggregations = {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "latest": 0
            }
        
        return {
            "metric_name": metric_name,
            "organization_id": organization_id,
            "aggregations": aggregations,
            "data_points": len(metrics),
            "time_range": time_range
        }
    
    def get_performance_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        
        # Calculate various performance metrics
        metrics = {}
        
        # API response times
        api_times = self.request_times.get(f"{organization_id}:api_request", [])
        if api_times:
            metrics["api_response_time"] = {
                "avg": sum(api_times) / len(api_times),
                "min": min(api_times),
                "max": max(api_times),
                "p95": sorted(api_times)[int(len(api_times) * 0.95)] if len(api_times) > 20 else 0
            }
        
        # Error rates
        total_requests = len(api_times)
        error_count = self.error_counts.get(organization_id, 0)
        if total_requests > 0:
            metrics["error_rate"] = (error_count / total_requests) * 100
        else:
            metrics["error_rate"] = 0
        
        # Sync performance
        sync_times = self.request_times.get(f"{organization_id}:sync_duration", [])
        if sync_times:
            metrics["sync_performance"] = {
                "avg_duration": sum(sync_times) / len(sync_times),
                "total_syncs": len(sync_times)
            }
        
        # Uptime calculation
        metrics["uptime_percentage"] = self.calculate_uptime(organization_id)
        
        return metrics
    
    # =====================================================
    # HEALTH CHECKS
    # =====================================================
    
    def register_health_check(self, organization_id: str, check_name: str,
                            check_function: Callable, interval_seconds: int = 300) -> str:
        """Register health check"""
        
        check_id = f"{organization_id}:{check_name}"
        
        health_check = HealthCheck(
            check_name=check_name,
            organization_id=organization_id,
            check_function=check_function,
            interval_seconds=interval_seconds
        )
        
        self.health_checks[check_id] = health_check
        
        logger.info(f"Registered health check '{check_name}' for organization {organization_id}")
        
        return check_id
    
    def _health_check_loop(self):
        """Health check execution loop"""
        while self.monitoring_enabled:
            try:
                current_time = datetime.utcnow()
                
                for check_id, health_check in self.health_checks.items():
                    if not health_check.enabled:
                        continue
                    
                    # Check if it's time to run
                    if (health_check.last_run is None or 
                        (current_time - health_check.last_run).total_seconds() >= health_check.interval_seconds):
                        
                        asyncio.run(self._execute_health_check(health_check))
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                time.sleep(60)
    
    async def _execute_health_check(self, health_check: HealthCheck):
        """Execute individual health check"""
        try:
            start_time = time.time()
            
            # Execute check function with timeout
            result = await asyncio.wait_for(
                health_check.check_function(),
                timeout=health_check.timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            health_check.last_run = datetime.utcnow()
            health_check.last_result = result
            
            if result.get('healthy', False):
                health_check.consecutive_failures = 0
                
                if result.get('log_success', False):
                    self.log_event(
                        health_check.organization_id,
                        MonitoringEventType.CONNECTION_ESTABLISHED,
                        f"Health check '{health_check.check_name}' passed",
                        AlertSeverity.INFO,
                        {"execution_time": execution_time, "result": result}
                    )
            else:
                health_check.consecutive_failures += 1
                
                severity = AlertSeverity.WARNING
                if health_check.consecutive_failures >= health_check.failure_threshold:
                    severity = AlertSeverity.ERROR
                
                self.log_event(
                    health_check.organization_id,
                    MonitoringEventType.CONNECTION_LOST,
                    f"Health check '{health_check.check_name}' failed: {result.get('error', 'Unknown error')}",
                    severity,
                    {"consecutive_failures": health_check.consecutive_failures, "result": result}
                )
                
        except asyncio.TimeoutError:
            health_check.consecutive_failures += 1
            self.log_event(
                health_check.organization_id,
                MonitoringEventType.CONNECTION_LOST,
                f"Health check '{health_check.check_name}' timed out",
                AlertSeverity.ERROR,
                {"consecutive_failures": health_check.consecutive_failures}
            )
        except Exception as e:
            health_check.consecutive_failures += 1
            self.log_event(
                health_check.organization_id,
                MonitoringEventType.CONNECTION_LOST,
                f"Health check '{health_check.check_name}' failed with exception: {str(e)}",
                AlertSeverity.ERROR,
                {"consecutive_failures": health_check.consecutive_failures, "exception": str(e)}
            )
    
    # =====================================================
    # ALERTING
    # =====================================================
    
    def create_alert_rule(self, organization_id: str, rule_config: Dict[str, Any]) -> str:
        """Create alert rule"""
        
        rule_id = f"rule_{organization_id}_{uuid.uuid4().hex[:8]}"
        
        rule = AlertRule(
            rule_id=rule_id,
            organization_id=organization_id,
            rule_name=rule_config['rule_name'],
            condition=rule_config['condition'],
            severity=AlertSeverity(rule_config.get('severity', 'warning')),
            enabled=rule_config.get('enabled', True),
            notification_channels=rule_config.get('notification_channels', []),
            cooldown_minutes=rule_config.get('cooldown_minutes', 30)
        )
        
        self.alert_rules[rule_id] = rule
        
        logger.info(f"Created alert rule '{rule.rule_name}' for organization {organization_id}")
        
        return rule_id
    
    def _check_alert_rules(self, event: MonitoringEvent):
        """Check if event triggers any alert rules"""
        
        for rule in self.alert_rules.values():
            if rule.organization_id != event.organization_id and rule.organization_id != "default":
                continue
            
            if not rule.enabled:
                continue
            
            # Check cooldown
            if (rule.last_triggered and 
                (datetime.utcnow() - rule.last_triggered).total_seconds() < rule.cooldown_minutes * 60):
                continue
            
            # Evaluate rule condition
            if self._evaluate_rule_condition(rule.condition, event):
                self._trigger_alert(rule, event)
    
    def _evaluate_rule_condition(self, condition: str, event: MonitoringEvent) -> bool:
        """Evaluate alert rule condition"""
        
        # Simple condition evaluation (would need more sophisticated parser for production)
        if condition == "sync_failed" and event.event_type == MonitoringEventType.SYNC_FAILED:
            return True
        
        if condition == "connection_lost" and event.event_type == MonitoringEventType.CONNECTION_LOST:
            return True
        
        if condition == "error_rate > 5%" and event.event_type == MonitoringEventType.API_ERROR:
            # Would calculate actual error rate here
            return True
        
        return False
    
    def _trigger_alert(self, rule: AlertRule, event: MonitoringEvent):
        """Trigger alert notification"""
        
        rule.last_triggered = datetime.utcnow()
        
        alert_message = f"ALERT: {rule.rule_name}\n"
        alert_message += f"Severity: {rule.severity.value.upper()}\n"
        alert_message += f"Event: {event.message}\n"
        alert_message += f"Organization: {event.organization_id}\n"
        alert_message += f"Time: {event.timestamp.isoformat()}\n"
        
        # Send to notification channels
        for channel in rule.notification_channels:
            self._send_notification(channel, alert_message, rule.severity)
        
        # Log alert
        self.log_event(
            event.organization_id,
            MonitoringEventType.API_ERROR,  # Generic alert event type
            f"Alert triggered: {rule.rule_name}",
            rule.severity,
            {"rule_id": rule.rule_id, "original_event_id": event.event_id}
        )
    
    def _check_performance_alerts(self, organization_id: str, metric_name: str, value: float):
        """Check for performance-based alerts"""
        
        # Define performance thresholds
        thresholds = {
            "api_response_time": {"warning": 1000, "error": 5000},  # milliseconds
            "sync_duration": {"warning": 300, "error": 900},  # seconds
            "error_rate": {"warning": 5, "error": 10},  # percentage
        }
        
        if metric_name in thresholds:
            threshold = thresholds[metric_name]
            
            if value >= threshold["error"]:
                self.log_event(
                    organization_id,
                    MonitoringEventType.PERFORMANCE_DEGRADATION,
                    f"Performance metric '{metric_name}' exceeded error threshold: {value}",
                    AlertSeverity.ERROR,
                    {"metric_name": metric_name, "value": value, "threshold": threshold["error"]}
                )
            elif value >= threshold["warning"]:
                self.log_event(
                    organization_id,
                    MonitoringEventType.PERFORMANCE_DEGRADATION,
                    f"Performance metric '{metric_name}' exceeded warning threshold: {value}",
                    AlertSeverity.WARNING,
                    {"metric_name": metric_name, "value": value, "threshold": threshold["warning"]}
                )
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
    def initialize_monitoring(self, organization_id: str, config: Dict[str, Any]):
        """Initialize monitoring for organization"""
        
        # Register default health checks for this organization
        self.register_health_check(
            organization_id,
            "yardi_connection",
            lambda: self._check_yardi_connection(organization_id),
            interval_seconds=300
        )
        
        self.register_health_check(
            organization_id,
            "sync_performance",
            lambda: self._check_sync_performance(organization_id),
            interval_seconds=600
        )
        
        logger.info(f"Initialized monitoring for organization {organization_id}")
    
    async def _check_yardi_connection(self, organization_id: str) -> Dict[str, Any]:
        """Health check for Yardi connection"""
        # This would test the actual Yardi connection
        return {"healthy": True, "response_time": 120.5}
    
    async def _check_sync_performance(self, organization_id: str) -> Dict[str, Any]:
        """Health check for sync performance"""
        # This would check recent sync performance
        return {"healthy": True, "average_duration": 45.2}
    
    def record_request_time(self, organization_id: str, request_type: str, duration: float):
        """Record request timing"""
        key = f"{organization_id}:{request_type}"
        self.request_times[key].append(duration)
        
        # Also record as metric
        self.record_metric(organization_id, f"{request_type}_duration", duration, MetricType.TIMER)
    
    def record_error(self, organization_id: str, error_type: str, error_message: str):
        """Record error occurrence"""
        self.error_counts[organization_id] += 1
        
        # Log as monitoring event
        self.log_event(
            organization_id,
            MonitoringEventType.API_ERROR,
            f"{error_type}: {error_message}",
            AlertSeverity.ERROR,
            {"error_type": error_type}
        )
    
    def calculate_uptime(self, organization_id: str) -> float:
        """Calculate uptime percentage"""
        # This is a simplified calculation
        # In production, would track actual service availability
        
        recent_errors = len([
            event for event in self.events.values()
            if (event.organization_id == organization_id and 
                event.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL] and
                event.timestamp > datetime.utcnow() - timedelta(hours=24))
        ])
        
        if recent_errors == 0:
            return 100.0
        elif recent_errors < 5:
            return 99.5
        else:
            return max(95.0, 100.0 - recent_errors * 0.5)
    
    def calculate_error_rate(self, organization_id: str) -> float:
        """Calculate error rate percentage"""
        api_requests = len(self.request_times.get(f"{organization_id}:api_request", []))
        errors = self.error_counts.get(organization_id, 0)
        
        if api_requests == 0:
            return 0.0
        
        return (errors / api_requests) * 100
    
    def _send_notification(self, channel: str, message: str, severity: AlertSeverity):
        """Send notification through specified channel"""
        
        if channel in self.notification_handlers:
            handler = self.notification_handlers[channel]
            try:
                handler(message, severity)
            except Exception as e:
                logger.error(f"Notification failed for channel {channel}: {e}")
        else:
            # Default: log the notification
            logger.warning(f"NOTIFICATION [{channel}] {severity.value.upper()}: {message}")
    
    def register_notification_handler(self, channel: str, handler: Callable):
        """Register notification handler"""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for channel '{channel}'")
    
    def _metric_aggregation_loop(self):
        """Background thread for metric aggregation"""
        while self.monitoring_enabled:
            try:
                # Aggregate metrics every 5 minutes
                # This would perform time-series aggregations, cleanup old data, etc.
                time.sleep(300)
            except Exception as e:
                logger.error(f"Metric aggregation error: {e}")
                time.sleep(300)
    
    def get_monitoring_summary(self, organization_id: str) -> Dict[str, Any]:
        """Get monitoring summary for organization"""
        
        # Get recent events
        recent_events = self.get_events(organization_id, limit=50)
        critical_events = [e for e in recent_events if e.severity == AlertSeverity.CRITICAL]
        error_events = [e for e in recent_events if e.severity == AlertSeverity.ERROR]
        
        # Get health check status
        org_health_checks = [
            hc for hc in self.health_checks.values()
            if hc.organization_id == organization_id
        ]
        
        healthy_checks = [hc for hc in org_health_checks if hc.consecutive_failures == 0]
        
        return {
            "organization_id": organization_id,
            "overall_health": "healthy" if len(critical_events) == 0 else "degraded",
            "uptime_percentage": self.calculate_uptime(organization_id),
            "error_rate": self.calculate_error_rate(organization_id),
            "health_checks": {
                "total": len(org_health_checks),
                "healthy": len(healthy_checks),
                "failing": len(org_health_checks) - len(healthy_checks)
            },
            "recent_events": {
                "total": len(recent_events),
                "critical": len(critical_events),
                "errors": len(error_events)
            },
            "last_updated": datetime.utcnow().isoformat()
        }