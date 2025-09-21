import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    TIMER = "timer"
    CUMULATIVE = "cumulative"

class AggregationType(Enum):
    SUM = "sum"
    MAX = "max"
    MIN = "min"
    AVERAGE = "average"
    COUNT = "count"

@dataclass
class UsageMetric:
    metric_id: str
    name: str
    description: str
    metric_type: MetricType
    unit: str
    billable: bool
    price_per_unit: float
    aggregation_type: AggregationType
    reset_frequency: str  # 'monthly', 'never', 'daily'
    
@dataclass
class UsageEvent:
    event_id: str
    customer_id: str
    subscription_id: str
    metric_name: str
    value: float
    metadata: Dict[str, Any]
    timestamp: datetime
    billing_period: str

@dataclass
class UsageAggregation:
    aggregation_id: str
    customer_id: str
    subscription_id: str
    metric_name: str
    period_start: datetime
    period_end: datetime
    total_value: float
    event_count: int
    billable_amount: float
    created_at: datetime

class UsageTracker:
    """
    Advanced usage tracking and metering system
    """
    
    def __init__(self):
        self.metrics = {}
        self.usage_events = defaultdict(list)
        self.aggregations = defaultdict(list)
        self.rate_limits = {}
        self.hooks = defaultdict(list)
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self):
        """Initialize default usage metrics for EstateCore SaaS"""
        
        # API Calls
        self.register_metric(UsageMetric(
            metric_id="api_calls",
            name="API Calls",
            description="Number of API calls made",
            metric_type=MetricType.COUNTER,
            unit="calls",
            billable=True,
            price_per_unit=0.01,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # Properties
        self.register_metric(UsageMetric(
            metric_id="properties",
            name="Properties",
            description="Number of properties managed",
            metric_type=MetricType.GAUGE,
            unit="properties",
            billable=True,
            price_per_unit=20.0,
            aggregation_type=AggregationType.MAX,
            reset_frequency="never"
        ))
        
        # Units
        self.register_metric(UsageMetric(
            metric_id="units",
            name="Units",
            description="Number of rental units managed",
            metric_type=MetricType.GAUGE,
            unit="units",
            billable=True,
            price_per_unit=2.0,
            aggregation_type=AggregationType.MAX,
            reset_frequency="never"
        ))
        
        # Users
        self.register_metric(UsageMetric(
            metric_id="users",
            name="Users",
            description="Number of active users",
            metric_type=MetricType.GAUGE,
            unit="users",
            billable=True,
            price_per_unit=15.0,
            aggregation_type=AggregationType.MAX,
            reset_frequency="never"
        ))
        
        # Document Storage
        self.register_metric(UsageMetric(
            metric_id="storage_gb",
            name="Storage",
            description="Document storage in GB",
            metric_type=MetricType.GAUGE,
            unit="GB",
            billable=True,
            price_per_unit=10.0,
            aggregation_type=AggregationType.MAX,
            reset_frequency="never"
        ))
        
        # AI Analytics Calls
        self.register_metric(UsageMetric(
            metric_id="ai_analytics",
            name="AI Analytics",
            description="AI analytics processing calls",
            metric_type=MetricType.COUNTER,
            unit="calls",
            billable=True,
            price_per_unit=0.50,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # Predictive Maintenance Runs
        self.register_metric(UsageMetric(
            metric_id="predictive_maintenance",
            name="Predictive Maintenance",
            description="Predictive maintenance analysis runs",
            metric_type=MetricType.COUNTER,
            unit="runs",
            billable=True,
            price_per_unit=2.0,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # IoT Data Points
        self.register_metric(UsageMetric(
            metric_id="iot_data_points",
            name="IoT Data Points",
            description="IoT sensor data points processed",
            metric_type=MetricType.COUNTER,
            unit="points",
            billable=True,
            price_per_unit=0.001,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # Email Notifications
        self.register_metric(UsageMetric(
            metric_id="email_notifications",
            name="Email Notifications",
            description="Email notifications sent",
            metric_type=MetricType.COUNTER,
            unit="emails",
            billable=True,
            price_per_unit=0.05,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # SMS Notifications
        self.register_metric(UsageMetric(
            metric_id="sms_notifications",
            name="SMS Notifications",
            description="SMS notifications sent",
            metric_type=MetricType.COUNTER,
            unit="sms",
            billable=True,
            price_per_unit=0.10,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # Reports Generated
        self.register_metric(UsageMetric(
            metric_id="reports_generated",
            name="Reports Generated",
            description="Number of reports generated",
            metric_type=MetricType.COUNTER,
            unit="reports",
            billable=True,
            price_per_unit=1.0,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # Bandwidth Usage
        self.register_metric(UsageMetric(
            metric_id="bandwidth_gb",
            name="Bandwidth",
            description="Bandwidth usage in GB",
            metric_type=MetricType.COUNTER,
            unit="GB",
            billable=True,
            price_per_unit=0.15,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
        
        # Compute Time (for AI processing)
        self.register_metric(UsageMetric(
            metric_id="compute_minutes",
            name="Compute Time",
            description="AI/ML compute time in minutes",
            metric_type=MetricType.TIMER,
            unit="minutes",
            billable=True,
            price_per_unit=0.20,
            aggregation_type=AggregationType.SUM,
            reset_frequency="monthly"
        ))
    
    def register_metric(self, metric: UsageMetric):
        """Register a new usage metric"""
        self.metrics[metric.metric_id] = metric
    
    def track_usage(self, customer_id: str, subscription_id: str, metric_name: str, 
                   value: float, metadata: Dict[str, Any] = None) -> UsageEvent:
        """Track a usage event"""
        
        if metric_name not in self.metrics:
            raise ValueError(f"Unknown metric: {metric_name}")
        
        metric = self.metrics[metric_name]
        event_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Calculate billing period
        billing_period = self._get_billing_period(now)
        
        usage_event = UsageEvent(
            event_id=event_id,
            customer_id=customer_id,
            subscription_id=subscription_id,
            metric_name=metric_name,
            value=value,
            metadata=metadata or {},
            timestamp=now,
            billing_period=billing_period
        )
        
        # Store event
        key = f"{customer_id}:{subscription_id}"
        self.usage_events[key].append(usage_event)
        
        # Check rate limits
        self._check_rate_limits(customer_id, subscription_id, metric_name, value)
        
        # Trigger hooks
        self._trigger_hooks('usage_tracked', usage_event)
        
        return usage_event
    
    def _get_billing_period(self, timestamp: datetime) -> str:
        """Get billing period for a timestamp"""
        return timestamp.strftime("%Y-%m")
    
    def _check_rate_limits(self, customer_id: str, subscription_id: str, 
                          metric_name: str, value: float):
        """Check if usage exceeds rate limits"""
        
        rate_limit_key = f"{customer_id}:{subscription_id}:{metric_name}"
        
        if rate_limit_key in self.rate_limits:
            limit_config = self.rate_limits[rate_limit_key]
            current_usage = self.get_current_usage(customer_id, subscription_id, metric_name)
            
            if current_usage + value > limit_config['limit']:
                self._trigger_hooks('rate_limit_exceeded', {
                    'customer_id': customer_id,
                    'subscription_id': subscription_id,
                    'metric_name': metric_name,
                    'current_usage': current_usage,
                    'attempted_value': value,
                    'limit': limit_config['limit']
                })
    
    def set_rate_limit(self, customer_id: str, subscription_id: str, 
                      metric_name: str, limit: float, window_hours: int = 24):
        """Set a rate limit for a customer's metric"""
        
        rate_limit_key = f"{customer_id}:{subscription_id}:{metric_name}"
        self.rate_limits[rate_limit_key] = {
            'limit': limit,
            'window_hours': window_hours,
            'created_at': datetime.now()
        }
    
    def get_current_usage(self, customer_id: str, subscription_id: str, 
                         metric_name: str, period_start: datetime = None) -> float:
        """Get current usage for a metric"""
        
        if period_start is None:
            period_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        key = f"{customer_id}:{subscription_id}"
        events = self.usage_events.get(key, [])
        
        # Filter events for the metric and period
        relevant_events = [
            e for e in events 
            if e.metric_name == metric_name and e.timestamp >= period_start
        ]
        
        if not relevant_events:
            return 0.0
        
        metric = self.metrics[metric_name]
        
        # Apply aggregation
        if metric.aggregation_type == AggregationType.SUM:
            return sum(e.value for e in relevant_events)
        elif metric.aggregation_type == AggregationType.MAX:
            return max(e.value for e in relevant_events)
        elif metric.aggregation_type == AggregationType.MIN:
            return min(e.value for e in relevant_events)
        elif metric.aggregation_type == AggregationType.AVERAGE:
            return sum(e.value for e in relevant_events) / len(relevant_events)
        elif metric.aggregation_type == AggregationType.COUNT:
            return len(relevant_events)
        
        return 0.0
    
    def aggregate_usage(self, customer_id: str, subscription_id: str, 
                       period_start: datetime, period_end: datetime) -> List[UsageAggregation]:
        """Aggregate usage for a billing period"""
        
        aggregations = []
        key = f"{customer_id}:{subscription_id}"
        
        for metric_name, metric in self.metrics.items():
            events = self.usage_events.get(key, [])
            
            # Filter events for this metric and period
            period_events = [
                e for e in events 
                if (e.metric_name == metric_name and 
                    period_start <= e.timestamp < period_end)
            ]
            
            if not period_events:
                continue
            
            # Calculate aggregated value
            if metric.aggregation_type == AggregationType.SUM:
                total_value = sum(e.value for e in period_events)
            elif metric.aggregation_type == AggregationType.MAX:
                total_value = max(e.value for e in period_events)
            elif metric.aggregation_type == AggregationType.MIN:
                total_value = min(e.value for e in period_events)
            elif metric.aggregation_type == AggregationType.AVERAGE:
                total_value = sum(e.value for e in period_events) / len(period_events)
            elif metric.aggregation_type == AggregationType.COUNT:
                total_value = len(period_events)
            else:
                total_value = 0.0
            
            # Calculate billable amount
            billable_amount = total_value * metric.price_per_unit if metric.billable else 0.0
            
            aggregation = UsageAggregation(
                aggregation_id=str(uuid.uuid4()),
                customer_id=customer_id,
                subscription_id=subscription_id,
                metric_name=metric_name,
                period_start=period_start,
                period_end=period_end,
                total_value=total_value,
                event_count=len(period_events),
                billable_amount=billable_amount,
                created_at=datetime.now()
            )
            
            aggregations.append(aggregation)
            
            # Store aggregation
            agg_key = f"{customer_id}:{subscription_id}"
            self.aggregations[agg_key].append(aggregation)
        
        return aggregations
    
    def get_usage_summary(self, customer_id: str, subscription_id: str, 
                         period_start: datetime = None, period_end: datetime = None) -> Dict[str, Any]:
        """Get comprehensive usage summary"""
        
        if period_start is None:
            period_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if period_end is None:
            period_end = datetime.now()
        
        summary = {
            'customer_id': customer_id,
            'subscription_id': subscription_id,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'metrics': {},
            'total_billable_amount': 0.0,
            'total_events': 0
        }
        
        key = f"{customer_id}:{subscription_id}"
        events = self.usage_events.get(key, [])
        
        # Filter events for period
        period_events = [
            e for e in events 
            if period_start <= e.timestamp < period_end
        ]
        
        summary['total_events'] = len(period_events)
        
        # Group by metric
        for metric_name, metric in self.metrics.items():
            metric_events = [e for e in period_events if e.metric_name == metric_name]
            
            if not metric_events:
                continue
            
            # Calculate aggregated value
            if metric.aggregation_type == AggregationType.SUM:
                total_value = sum(e.value for e in metric_events)
            elif metric.aggregation_type == AggregationType.MAX:
                total_value = max(e.value for e in metric_events)
            elif metric.aggregation_type == AggregationType.MIN:
                total_value = min(e.value for e in metric_events)
            elif metric.aggregation_type == AggregationType.AVERAGE:
                total_value = sum(e.value for e in metric_events) / len(metric_events)
            elif metric.aggregation_type == AggregationType.COUNT:
                total_value = len(metric_events)
            else:
                total_value = 0.0
            
            billable_amount = total_value * metric.price_per_unit if metric.billable else 0.0
            
            summary['metrics'][metric_name] = {
                'name': metric.name,
                'total_value': total_value,
                'unit': metric.unit,
                'event_count': len(metric_events),
                'billable': metric.billable,
                'price_per_unit': metric.price_per_unit,
                'billable_amount': billable_amount
            }
            
            if metric.billable:
                summary['total_billable_amount'] += billable_amount
        
        return summary
    
    def track_api_call(self, customer_id: str, subscription_id: str, 
                      endpoint: str, method: str, response_code: int):
        """Convenience method to track API calls"""
        
        self.track_usage(
            customer_id=customer_id,
            subscription_id=subscription_id,
            metric_name="api_calls",
            value=1.0,
            metadata={
                'endpoint': endpoint,
                'method': method,
                'response_code': response_code,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def track_property_count(self, customer_id: str, subscription_id: str, count: int):
        """Convenience method to track property count"""
        
        self.track_usage(
            customer_id=customer_id,
            subscription_id=subscription_id,
            metric_name="properties",
            value=float(count)
        )
    
    def track_ai_analytics_call(self, customer_id: str, subscription_id: str, 
                               analysis_type: str, compute_time_seconds: float):
        """Convenience method to track AI analytics usage"""
        
        # Track the AI analytics call
        self.track_usage(
            customer_id=customer_id,
            subscription_id=subscription_id,
            metric_name="ai_analytics",
            value=1.0,
            metadata={
                'analysis_type': analysis_type,
                'compute_time_seconds': compute_time_seconds
            }
        )
        
        # Track compute time
        self.track_usage(
            customer_id=customer_id,
            subscription_id=subscription_id,
            metric_name="compute_minutes",
            value=compute_time_seconds / 60.0,
            metadata={
                'analysis_type': analysis_type
            }
        )
    
    def track_storage_usage(self, customer_id: str, subscription_id: str, 
                           storage_gb: float, file_type: str = None):
        """Convenience method to track storage usage"""
        
        self.track_usage(
            customer_id=customer_id,
            subscription_id=subscription_id,
            metric_name="storage_gb",
            value=storage_gb,
            metadata={
                'file_type': file_type
            }
        )
    
    def add_hook(self, event_type: str, callback: Callable):
        """Add a hook for usage events"""
        self.hooks[event_type].append(callback)
    
    def _trigger_hooks(self, event_type: str, data: Any):
        """Trigger hooks for an event"""
        for callback in self.hooks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Hook error for {event_type}: {e}")
    
    def reset_usage(self, customer_id: str, subscription_id: str, metric_name: str):
        """Reset usage for a metric (for new billing periods)"""
        
        metric = self.metrics.get(metric_name)
        if not metric or metric.reset_frequency == 'never':
            return
        
        # Mark events as processed/archived instead of deleting
        key = f"{customer_id}:{subscription_id}"
        events = self.usage_events.get(key, [])
        
        # Filter out events for this metric from current period
        current_period = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.usage_events[key] = [
            e for e in events 
            if not (e.metric_name == metric_name and e.timestamp >= current_period)
        ]
    
    def export_usage_data(self, customer_id: str, subscription_id: str, 
                         period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Export usage data for analysis or backup"""
        
        key = f"{customer_id}:{subscription_id}"
        events = self.usage_events.get(key, [])
        
        # Filter events for period
        period_events = [
            e for e in events 
            if period_start <= e.timestamp < period_end
        ]
        
        return {
            'customer_id': customer_id,
            'subscription_id': subscription_id,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'events': [serialize_usage_event(e) for e in period_events],
            'summary': self.get_usage_summary(customer_id, subscription_id, period_start, period_end)
        }

def serialize_usage_event(event: UsageEvent) -> Dict:
    """Convert UsageEvent to JSON-serializable dict"""
    result = asdict(event)
    result['timestamp'] = event.timestamp.isoformat()
    return result

def serialize_usage_aggregation(aggregation: UsageAggregation) -> Dict:
    """Convert UsageAggregation to JSON-serializable dict"""
    result = asdict(aggregation)
    result['period_start'] = aggregation.period_start.isoformat()
    result['period_end'] = aggregation.period_end.isoformat()
    result['created_at'] = aggregation.created_at.isoformat()
    return result