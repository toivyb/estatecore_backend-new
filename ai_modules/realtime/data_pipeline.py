import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import threading
import queue
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

class DataStreamType(Enum):
    SENSOR_DATA = "sensor_data"
    AI_PREDICTIONS = "ai_predictions"
    ALERTS = "alerts"
    FINANCIAL = "financial"
    MAINTENANCE = "maintenance"
    TENANT_ACTIVITY = "tenant_activity"

@dataclass
class DataEvent:
    event_id: str
    stream_type: DataStreamType
    timestamp: datetime
    property_id: str
    data: Dict[str, Any]
    priority: int = 1
    processed: bool = False
    
    def __lt__(self, other):
        """Enable comparison for priority queue"""
        return self.priority < other.priority

class RealTimeDataPipeline:
    """
    Real-time data pipeline for streaming property management data
    """
    
    def __init__(self):
        self.data_streams = {}
        self.subscribers = {}
        self.event_queue = queue.PriorityQueue()
        self.processing_thread = None
        self.is_running = False
        self.data_buffer = {}
        self.stream_analytics = {}
        
    def create_data_stream(self, stream_id: str, stream_type: DataStreamType, config: Dict = None) -> str:
        """Create a new data stream"""
        if config is None:
            config = {}
            
        stream_config = {
            'id': stream_id,
            'type': stream_type,
            'created_at': datetime.now(),
            'last_update': datetime.now(),
            'event_count': 0,
            'subscriber_count': 0,
            'buffer_size': config.get('buffer_size', 1000),
            'retention_hours': config.get('retention_hours', 24),
            'compression_enabled': config.get('compression_enabled', False),
            'real_time_processing': config.get('real_time_processing', True),
            'alert_thresholds': config.get('alert_thresholds', {}),
            'status': 'active'
        }
        
        self.data_streams[stream_id] = stream_config
        self.data_buffer[stream_id] = []
        self.stream_analytics[stream_id] = {
            'events_per_minute': 0,
            'avg_processing_time': 0,
            'error_count': 0,
            'last_error': None
        }
        
        return stream_id
    
    def publish_event(self, stream_id: str, event_data: Dict, priority: int = 1) -> str:
        """Publish an event to a data stream"""
        if stream_id not in self.data_streams:
            raise ValueError(f"Stream {stream_id} does not exist")
        
        event_id = f"{stream_id}_{int(time.time())}_{hash(str(event_data)) % 10000}"
        
        event = DataEvent(
            event_id=event_id,
            stream_type=self.data_streams[stream_id]['type'],
            timestamp=datetime.now(),
            property_id=event_data.get('property_id', 'unknown'),
            data=event_data,
            priority=priority
        )
        
        # Add to queue for processing
        self.event_queue.put((priority, event))
        
        # Update stream statistics
        self.data_streams[stream_id]['event_count'] += 1
        self.data_streams[stream_id]['last_update'] = datetime.now()
        
        return event_id
    
    def subscribe_to_stream(self, stream_id: str, callback: Callable, filters: Dict = None) -> str:
        """Subscribe to a data stream with optional filters"""
        if stream_id not in self.data_streams:
            raise ValueError(f"Stream {stream_id} does not exist")
        
        subscription_id = f"sub_{stream_id}_{int(time.time())}_{hash(str(callback)) % 10000}"
        
        if stream_id not in self.subscribers:
            self.subscribers[stream_id] = {}
        
        self.subscribers[stream_id][subscription_id] = {
            'callback': callback,
            'filters': filters or {},
            'created_at': datetime.now(),
            'event_count': 0,
            'active': True
        }
        
        self.data_streams[stream_id]['subscriber_count'] += 1
        
        return subscription_id
    
    def start_pipeline(self):
        """Start the real-time data pipeline"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._process_events)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # Start analytics collection
        self.analytics_thread = threading.Thread(target=self._collect_analytics)
        self.analytics_thread.daemon = True
        self.analytics_thread.start()
    
    def stop_pipeline(self):
        """Stop the real-time data pipeline"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
    
    def _process_events(self):
        """Process events from the queue"""
        while self.is_running:
            try:
                if not self.event_queue.empty():
                    priority, event = self.event_queue.get(timeout=1)
                    self._handle_event(event)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing event: {e}")
    
    def _handle_event(self, event: DataEvent):
        """Handle a single event"""
        start_time = time.time()
        
        try:
            # Add to buffer
            stream_id = f"{event.stream_type.value}_{event.property_id}"
            if stream_id in self.data_buffer:
                self.data_buffer[stream_id].append(event)
                
                # Maintain buffer size limit
                buffer_size = self.data_streams.get(stream_id, {}).get('buffer_size', 1000)
                if len(self.data_buffer[stream_id]) > buffer_size:
                    self.data_buffer[stream_id] = self.data_buffer[stream_id][-buffer_size:]
            
            # Notify subscribers
            self._notify_subscribers(stream_id, event)
            
            # Process real-time analytics
            self._process_real_time_analytics(event)
            
            # Check for alerts
            self._check_event_alerts(event)
            
            event.processed = True
            
        except Exception as e:
            if stream_id in self.stream_analytics:
                self.stream_analytics[stream_id]['error_count'] += 1
                self.stream_analytics[stream_id]['last_error'] = str(e)
        
        finally:
            # Update processing time
            processing_time = time.time() - start_time
            if stream_id in self.stream_analytics:
                current_avg = self.stream_analytics[stream_id]['avg_processing_time']
                self.stream_analytics[stream_id]['avg_processing_time'] = (current_avg + processing_time) / 2
    
    def _notify_subscribers(self, stream_id: str, event: DataEvent):
        """Notify all subscribers of a stream"""
        if stream_id in self.subscribers:
            for sub_id, subscription in self.subscribers[stream_id].items():
                if subscription['active'] and self._passes_filters(event, subscription['filters']):
                    try:
                        subscription['callback'](event)
                        subscription['event_count'] += 1
                    except Exception as e:
                        print(f"Error notifying subscriber {sub_id}: {e}")
    
    def _passes_filters(self, event: DataEvent, filters: Dict) -> bool:
        """Check if event passes subscription filters"""
        if not filters:
            return True
        
        # Property filter
        if 'property_ids' in filters:
            if event.property_id not in filters['property_ids']:
                return False
        
        # Priority filter
        if 'min_priority' in filters:
            if event.priority < filters['min_priority']:
                return False
        
        # Data filters
        if 'data_filters' in filters:
            for key, expected_value in filters['data_filters'].items():
                if key not in event.data or event.data[key] != expected_value:
                    return False
        
        return True
    
    def _process_real_time_analytics(self, event: DataEvent):
        """Process real-time analytics for the event"""
        stream_type = event.stream_type.value
        
        # Update stream-specific analytics
        if stream_type == DataStreamType.SENSOR_DATA.value:
            self._process_sensor_analytics(event)
        elif stream_type == DataStreamType.AI_PREDICTIONS.value:
            self._process_ai_analytics(event)
        elif stream_type == DataStreamType.ALERTS.value:
            self._process_alert_analytics(event)
    
    def _process_sensor_analytics(self, event: DataEvent):
        """Process sensor data analytics"""
        sensor_type = event.data.get('sensor_type')
        value = event.data.get('value')
        
        if sensor_type and value is not None:
            analytics_key = f"sensor_{sensor_type}_{event.property_id}"
            
            if analytics_key not in self.stream_analytics:
                self.stream_analytics[analytics_key] = {
                    'value_sum': 0,
                    'value_count': 0,
                    'min_value': float('inf'),
                    'max_value': float('-inf'),
                    'recent_values': []
                }
            
            analytics = self.stream_analytics[analytics_key]
            analytics['value_sum'] += value
            analytics['value_count'] += 1
            analytics['min_value'] = min(analytics['min_value'], value)
            analytics['max_value'] = max(analytics['max_value'], value)
            analytics['recent_values'].append(value)
            
            # Keep only recent values
            if len(analytics['recent_values']) > 100:
                analytics['recent_values'] = analytics['recent_values'][-100:]
    
    def _process_ai_analytics(self, event: DataEvent):
        """Process AI prediction analytics"""
        prediction_type = event.data.get('prediction_type')
        confidence = event.data.get('confidence', 0)
        
        analytics_key = f"ai_{prediction_type}_{event.property_id}"
        
        if analytics_key not in self.stream_analytics:
            self.stream_analytics[analytics_key] = {
                'prediction_count': 0,
                'avg_confidence': 0,
                'high_confidence_count': 0
            }
        
        analytics = self.stream_analytics[analytics_key]
        analytics['prediction_count'] += 1
        analytics['avg_confidence'] = (analytics['avg_confidence'] + confidence) / 2
        
        if confidence > 0.8:
            analytics['high_confidence_count'] += 1
    
    def _process_alert_analytics(self, event: DataEvent):
        """Process alert analytics"""
        alert_type = event.data.get('alert_type')
        severity = event.data.get('severity')
        
        analytics_key = f"alerts_{event.property_id}"
        
        if analytics_key not in self.stream_analytics:
            self.stream_analytics[analytics_key] = {
                'total_alerts': 0,
                'critical_alerts': 0,
                'alert_types': {}
            }
        
        analytics = self.stream_analytics[analytics_key]
        analytics['total_alerts'] += 1
        
        if severity == 'critical':
            analytics['critical_alerts'] += 1
        
        if alert_type:
            analytics['alert_types'][alert_type] = analytics['alert_types'].get(alert_type, 0) + 1
    
    def _check_event_alerts(self, event: DataEvent):
        """Check if event should trigger alerts"""
        stream_id = f"{event.stream_type.value}_{event.property_id}"
        
        if stream_id in self.data_streams:
            thresholds = self.data_streams[stream_id].get('alert_thresholds', {})
            
            # Check various threshold types
            if event.stream_type == DataStreamType.SENSOR_DATA:
                self._check_sensor_thresholds(event, thresholds)
    
    def _check_sensor_thresholds(self, event: DataEvent, thresholds: Dict):
        """Check sensor data against thresholds"""
        sensor_type = event.data.get('sensor_type')
        value = event.data.get('value')
        
        if sensor_type in thresholds and value is not None:
            sensor_thresholds = thresholds[sensor_type]
            
            if 'max' in sensor_thresholds and value > sensor_thresholds['max']:
                self._create_threshold_alert(event, 'max', sensor_thresholds['max'])
            
            if 'min' in sensor_thresholds and value < sensor_thresholds['min']:
                self._create_threshold_alert(event, 'min', sensor_thresholds['min'])
    
    def _create_threshold_alert(self, event: DataEvent, threshold_type: str, threshold_value: float):
        """Create an alert for threshold violation"""
        alert_data = {
            'alert_type': 'threshold_violation',
            'sensor_type': event.data.get('sensor_type'),
            'threshold_type': threshold_type,
            'threshold_value': threshold_value,
            'actual_value': event.data.get('value'),
            'property_id': event.property_id,
            'timestamp': event.timestamp.isoformat(),
            'severity': 'high'
        }
        
        # Publish alert to alerts stream
        alert_stream_id = f"{DataStreamType.ALERTS.value}_{event.property_id}"
        if alert_stream_id in self.data_streams:
            self.publish_event(alert_stream_id, alert_data, priority=5)
    
    def _collect_analytics(self):
        """Collect and update stream analytics"""
        while self.is_running:
            time.sleep(60)  # Update every minute
            
            current_time = datetime.now()
            
            for stream_id, stream_config in self.data_streams.items():
                # Calculate events per minute
                recent_events = self._count_recent_events(stream_id, minutes=1)
                if stream_id in self.stream_analytics:
                    self.stream_analytics[stream_id]['events_per_minute'] = recent_events
    
    def _count_recent_events(self, stream_id: str, minutes: int = 1) -> int:
        """Count events in the last N minutes"""
        if stream_id not in self.data_buffer:
            return 0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_events = [
            event for event in self.data_buffer[stream_id]
            if event.timestamp >= cutoff_time
        ]
        
        return len(recent_events)
    
    def get_stream_status(self, stream_id: str = None) -> Dict:
        """Get status of streams"""
        if stream_id:
            if stream_id not in self.data_streams:
                return {'error': 'Stream not found'}
            
            stream_config = self.data_streams[stream_id]
            analytics = self.stream_analytics.get(stream_id, {})
            
            return {
                'stream_id': stream_id,
                'type': stream_config['type'].value,
                'status': stream_config['status'],
                'event_count': stream_config['event_count'],
                'subscriber_count': stream_config['subscriber_count'],
                'events_per_minute': analytics.get('events_per_minute', 0),
                'avg_processing_time': analytics.get('avg_processing_time', 0),
                'error_count': analytics.get('error_count', 0),
                'last_update': stream_config['last_update'].isoformat()
            }
        else:
            # Return all streams
            return {
                stream_id: self.get_stream_status(stream_id)
                for stream_id in self.data_streams.keys()
            }
    
    def get_recent_events(self, stream_id: str, limit: int = 100) -> List[Dict]:
        """Get recent events from a stream"""
        if stream_id not in self.data_buffer:
            return []
        
        recent_events = self.data_buffer[stream_id][-limit:]
        return [asdict(event) for event in recent_events]
    
    def get_analytics_summary(self, property_id: str = None) -> Dict:
        """Get analytics summary for streams"""
        summary = {
            'total_streams': len(self.data_streams),
            'total_events_processed': sum(stream['event_count'] for stream in self.data_streams.values()),
            'total_subscribers': sum(stream['subscriber_count'] for stream in self.data_streams.values()),
            'pipeline_status': 'running' if self.is_running else 'stopped',
            'stream_breakdown': {},
            'performance_metrics': {}
        }
        
        # Stream breakdown by type
        for stream_id, stream_config in self.data_streams.items():
            stream_type = stream_config['type'].value
            if stream_type not in summary['stream_breakdown']:
                summary['stream_breakdown'][stream_type] = {
                    'count': 0,
                    'total_events': 0,
                    'avg_events_per_minute': 0
                }
            
            summary['stream_breakdown'][stream_type]['count'] += 1
            summary['stream_breakdown'][stream_type]['total_events'] += stream_config['event_count']
            
            analytics = self.stream_analytics.get(stream_id, {})
            current_epm = analytics.get('events_per_minute', 0)
            summary['stream_breakdown'][stream_type]['avg_events_per_minute'] += current_epm
        
        # Average events per minute by type
        for stream_type in summary['stream_breakdown']:
            count = summary['stream_breakdown'][stream_type]['count']
            if count > 0:
                total_epm = summary['stream_breakdown'][stream_type]['avg_events_per_minute']
                summary['stream_breakdown'][stream_type]['avg_events_per_minute'] = total_epm / count
        
        # Performance metrics
        all_processing_times = [
            analytics.get('avg_processing_time', 0)
            for analytics in self.stream_analytics.values()
            if 'avg_processing_time' in analytics
        ]
        
        if all_processing_times:
            summary['performance_metrics'] = {
                'avg_processing_time': float(np.mean(all_processing_times)),
                'max_processing_time': float(np.max(all_processing_times)),
                'total_errors': sum(analytics.get('error_count', 0) for analytics in self.stream_analytics.values())
            }
        
        return summary

# Real-time data pipeline integration functions
def create_property_data_streams(pipeline: RealTimeDataPipeline, property_id: str) -> Dict[str, str]:
    """Create all necessary data streams for a property"""
    streams = {}
    
    # Create sensor data stream
    sensor_stream_id = f"sensors_{property_id}"
    streams['sensors'] = pipeline.create_data_stream(
        sensor_stream_id,
        DataStreamType.SENSOR_DATA,
        {
            'buffer_size': 2000,
            'retention_hours': 48,
            'alert_thresholds': {
                'temperature': {'min': 60, 'max': 85},
                'humidity': {'max': 70},
                'air_quality': {'max': 100}
            }
        }
    )
    
    # Create AI predictions stream
    ai_stream_id = f"ai_predictions_{property_id}"
    streams['ai_predictions'] = pipeline.create_data_stream(
        ai_stream_id,
        DataStreamType.AI_PREDICTIONS,
        {'buffer_size': 500, 'retention_hours': 24}
    )
    
    # Create alerts stream
    alerts_stream_id = f"alerts_{property_id}"
    streams['alerts'] = pipeline.create_data_stream(
        alerts_stream_id,
        DataStreamType.ALERTS,
        {'buffer_size': 1000, 'retention_hours': 72}
    )
    
    # Create maintenance stream
    maintenance_stream_id = f"maintenance_{property_id}"
    streams['maintenance'] = pipeline.create_data_stream(
        maintenance_stream_id,
        DataStreamType.MAINTENANCE,
        {'buffer_size': 300, 'retention_hours': 168}  # 1 week
    )
    
    return streams

def setup_ai_model_integration(pipeline: RealTimeDataPipeline, property_id: str):
    """Set up integration between real-time data and AI models"""
    
    def process_sensor_data_for_ai(event: DataEvent):
        """Process sensor data and trigger AI predictions"""
        sensor_data = event.data
        
        # Trigger maintenance prediction if HVAC data
        if sensor_data.get('sensor_type') == 'temperature':
            # Simulate AI prediction trigger
            ai_prediction = {
                'prediction_type': 'maintenance_forecast',
                'property_id': property_id,
                'prediction': 'HVAC maintenance recommended within 30 days',
                'confidence': 0.75,
                'factors': ['temperature_variance', 'usage_patterns'],
                'timestamp': datetime.now().isoformat()
            }
            
            ai_stream_id = f"ai_predictions_{property_id}"
            pipeline.publish_event(ai_stream_id, ai_prediction, priority=3)
    
    # Subscribe to sensor data stream
    sensor_stream_id = f"sensors_{property_id}"
    pipeline.subscribe_to_stream(sensor_stream_id, process_sensor_data_for_ai)

def setup_dashboard_subscriptions(pipeline: RealTimeDataPipeline, property_id: str, dashboard_callback: Callable):
    """Set up subscriptions for real-time dashboard updates"""
    
    # Subscribe to all relevant streams
    stream_types = ['sensors', 'ai_predictions', 'alerts', 'maintenance']
    
    for stream_type in stream_types:
        stream_id = f"{stream_type}_{property_id}"
        pipeline.subscribe_to_stream(stream_id, dashboard_callback)