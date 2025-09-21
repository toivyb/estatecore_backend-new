from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import uuid
import random

# Import environmental monitoring components
import os
import sys
sys.path.append(os.path.dirname(__file__))

from environmental_monitor import (
    EnvironmentalMonitor, 
    serialize_environmental_reading, 
    serialize_environmental_alert, 
    serialize_sustainability_report,
    EnvironmentalMetric,
    AlertLevel
)

class EnvironmentalAPI:
    """
    Environmental monitoring API for EstateCore
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.environmental_monitor = EnvironmentalMonitor()
        
        # Generate sample data for demonstration
        self._generate_sample_data()
        self._register_routes()
    
    def _generate_sample_data(self):
        """Generate sample environmental data for demonstration"""
        
        properties = ['PROP001', 'PROP002', 'PROP003']
        
        for property_id in properties:
            # Generate sample sensor readings
            for _ in range(20):  # 20 readings per property
                sample_sensor_data = {
                    'sensor_readings': [
                        {
                            'sensor_type': 'air_quality',
                            'sensor_id': f'aq_sensor_{property_id}',
                            'value': random.uniform(20, 80),
                            'location': 'Main Lobby',
                            'confidence': 0.95,
                            'calibration_status': 'calibrated',
                            'weather': {
                                'temperature': random.uniform(68, 75),
                                'humidity': random.uniform(30, 60)
                            },
                            'occupancy': random.uniform(0.3, 0.8)
                        },
                        {
                            'sensor_type': 'co2',
                            'sensor_id': f'co2_sensor_{property_id}',
                            'value': random.uniform(400, 1200),
                            'location': 'Office Floor 3',
                            'confidence': 0.92,
                            'calibration_status': 'calibrated',
                            'weather': {},
                            'occupancy': random.uniform(0.4, 0.9)
                        },
                        {
                            'sensor_type': 'noise',
                            'sensor_id': f'noise_sensor_{property_id}',
                            'value': random.uniform(35, 65),
                            'location': 'Common Area',
                            'confidence': 0.89,
                            'calibration_status': 'calibrated',
                            'weather': {},
                            'occupancy': random.uniform(0.2, 0.7)
                        },
                        {
                            'sensor_type': 'energy',
                            'sensor_id': f'energy_sensor_{property_id}',
                            'value': random.uniform(1.5, 4.5),
                            'location': 'Main Building',
                            'confidence': 0.98,
                            'calibration_status': 'calibrated',
                            'weather': {},
                            'occupancy': random.uniform(0.3, 0.8)
                        },
                        {
                            'sensor_type': 'water_quality',
                            'sensor_id': f'water_sensor_{property_id}',
                            'value': random.uniform(5, 25),
                            'location': 'Water Supply',
                            'confidence': 0.94,
                            'calibration_status': 'calibrated',
                            'weather': {},
                            'occupancy': 0.0
                        }
                    ]
                }
                
                # Process the readings
                self.environmental_monitor.process_environmental_data(sample_sensor_data, property_id)
    
    def _register_routes(self):
        """Register all environmental API routes"""
        
        # Real-time status
        self.app.add_url_rule('/api/environmental/status/<property_id>', 'get_environmental_status',
                             self.get_environmental_status, methods=['GET'])
        
        # Process sensor data
        self.app.add_url_rule('/api/environmental/process-data', 'process_sensor_data',
                             self.process_sensor_data, methods=['POST'])
        
        # Sustainability reporting
        self.app.add_url_rule('/api/environmental/sustainability-report/<property_id>', 'get_sustainability_report',
                             self.get_sustainability_report, methods=['GET'])
        
        # Environmental alerts
        self.app.add_url_rule('/api/environmental/alerts/<property_id>', 'get_environmental_alerts',
                             self.get_environmental_alerts, methods=['GET'])
        
        # Acknowledge alert
        self.app.add_url_rule('/api/environmental/alerts/<alert_id>/acknowledge', 'acknowledge_alert',
                             self.acknowledge_alert, methods=['POST'])
        
        # Resolve alert
        self.app.add_url_rule('/api/environmental/alerts/<alert_id>/resolve', 'resolve_alert',
                             self.resolve_alert, methods=['POST'])
        
        # Environmental readings
        self.app.add_url_rule('/api/environmental/readings/<property_id>', 'get_environmental_readings',
                             self.get_environmental_readings, methods=['GET'])
        
        # Environmental analytics
        self.app.add_url_rule('/api/environmental/analytics/<property_id>', 'get_environmental_analytics',
                             self.get_environmental_analytics, methods=['GET'])
        
        # Update environmental thresholds
        self.app.add_url_rule('/api/environmental/thresholds', 'update_thresholds',
                             self.update_thresholds, methods=['POST'])
        
        # Get environmental metrics
        self.app.add_url_rule('/api/environmental/metrics', 'get_environmental_metrics',
                             self.get_environmental_metrics, methods=['GET'])
    
    def get_environmental_status(self, property_id):
        """Get real-time environmental status for a property"""
        try:
            status = self.environmental_monitor.get_real_time_environmental_status(property_id)
            
            return jsonify({
                'success': True,
                'data': status
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def process_sensor_data(self):
        """Process incoming sensor data"""
        try:
            data = request.get_json()
            
            property_id = data.get('property_id')
            sensor_data = data.get('sensor_data', {})
            
            if not property_id:
                return jsonify({'success': False, 'error': 'Property ID is required'}), 400
            
            # Process the sensor data
            readings = self.environmental_monitor.process_environmental_data(sensor_data, property_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'processed_readings': len(readings),
                    'readings': [serialize_environmental_reading(r) for r in readings]
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_sustainability_report(self, property_id):
        """Get sustainability report for a property"""
        try:
            period = request.args.get('period', 'monthly')
            
            report = self.environmental_monitor.generate_sustainability_report(property_id, period)
            
            return jsonify({
                'success': True,
                'data': serialize_sustainability_report(report)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_environmental_alerts(self, property_id):
        """Get environmental alerts for a property"""
        try:
            status_filter = request.args.get('status')  # 'active', 'resolved', 'acknowledged'
            level_filter = request.args.get('level')    # 'warning', 'critical', 'emergency'
            
            # Get all alerts for the property
            property_alerts = [
                alert for alert in self.environmental_monitor.alerts.values()
                if alert.property_id == property_id
            ]
            
            # Apply filters
            if status_filter == 'active':
                property_alerts = [a for a in property_alerts if not a.resolved]
            elif status_filter == 'resolved':
                property_alerts = [a for a in property_alerts if a.resolved]
            elif status_filter == 'acknowledged':
                property_alerts = [a for a in property_alerts if a.acknowledged and not a.resolved]
            
            if level_filter:
                property_alerts = [a for a in property_alerts if a.alert_level.value == level_filter]
            
            # Sort by creation date (newest first)
            property_alerts.sort(key=lambda x: x.created_at, reverse=True)
            
            return jsonify({
                'success': True,
                'data': [serialize_environmental_alert(alert) for alert in property_alerts]
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def acknowledge_alert(self, alert_id):
        """Acknowledge an environmental alert"""
        try:
            alert = self.environmental_monitor.alerts.get(alert_id)
            if not alert:
                return jsonify({'success': False, 'error': 'Alert not found'}), 404
            
            alert.acknowledged = True
            
            return jsonify({
                'success': True,
                'data': serialize_environmental_alert(alert)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def resolve_alert(self, alert_id):
        """Resolve an environmental alert"""
        try:
            data = request.get_json()
            resolution_notes = data.get('resolution_notes', '')
            
            alert = self.environmental_monitor.alerts.get(alert_id)
            if not alert:
                return jsonify({'success': False, 'error': 'Alert not found'}), 404
            
            alert.resolved = True
            alert.acknowledged = True
            
            return jsonify({
                'success': True,
                'data': serialize_environmental_alert(alert)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_environmental_readings(self, property_id):
        """Get environmental readings for a property"""
        try:
            # Parse query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            metric_type = request.args.get('metric_type')
            limit = int(request.args.get('limit', 100))
            
            # Get readings for the property
            property_readings = self.environmental_monitor.readings.get(property_id, [])
            
            # Apply filters
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                property_readings = [r for r in property_readings if r.timestamp >= start_dt]
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                property_readings = [r for r in property_readings if r.timestamp <= end_dt]
            
            if metric_type:
                property_readings = [r for r in property_readings if r.metric_type.value == metric_type]
            
            # Sort by timestamp (newest first) and limit
            property_readings.sort(key=lambda x: x.timestamp, reverse=True)
            property_readings = property_readings[:limit]
            
            return jsonify({
                'success': True,
                'data': {
                    'readings': [serialize_environmental_reading(r) for r in property_readings],
                    'total_count': len(property_readings),
                    'property_id': property_id
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_environmental_analytics(self, property_id):
        """Get environmental analytics for a property"""
        try:
            # Get readings for analysis
            property_readings = self.environmental_monitor.readings.get(property_id, [])
            
            if not property_readings:
                return jsonify({
                    'success': True,
                    'data': {
                        'property_id': property_id,
                        'metrics': {},
                        'trends': {},
                        'summary': {
                            'total_readings': 0,
                            'active_sensors': 0,
                            'data_quality_score': 0,
                            'last_updated': None
                        }
                    }
                })
            
            # Calculate analytics by metric type
            analytics = {
                'property_id': property_id,
                'metrics': {},
                'trends': {},
                'summary': {
                    'total_readings': len(property_readings),
                    'active_sensors': len(set(r.sensor_id for r in property_readings)),
                    'data_quality_score': sum(r.confidence_score for r in property_readings) / len(property_readings) * 100,
                    'last_updated': max(r.timestamp for r in property_readings).isoformat()
                }
            }
            
            # Analyze each metric type
            for metric in EnvironmentalMetric:
                metric_readings = [r for r in property_readings if r.metric_type == metric]
                
                if metric_readings:
                    latest_reading = max(metric_readings, key=lambda x: x.timestamp)
                    avg_value = sum(r.value for r in metric_readings) / len(metric_readings)
                    
                    # Calculate trend
                    if len(metric_readings) >= 5:
                        recent_avg = sum(r.value for r in metric_readings[-5:]) / 5
                        earlier_avg = sum(r.value for r in metric_readings[:-5][-5:]) / min(5, len(metric_readings[:-5]))
                        trend_direction = 'improving' if recent_avg < earlier_avg else 'declining' if recent_avg > earlier_avg else 'stable'
                        trend_percentage = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                    else:
                        trend_direction = 'stable'
                        trend_percentage = 0
                    
                    analytics['metrics'][metric.value] = {
                        'current_value': latest_reading.value,
                        'average_value': round(avg_value, 2),
                        'min_value': min(r.value for r in metric_readings),
                        'max_value': max(r.value for r in metric_readings),
                        'reading_count': len(metric_readings),
                        'trend_direction': trend_direction,
                        'trend_percentage': round(trend_percentage, 2),
                        'last_updated': latest_reading.timestamp.isoformat(),
                        'unit': latest_reading.unit,
                        'data_quality': round(sum(r.confidence_score for r in metric_readings) / len(metric_readings) * 100, 1)
                    }
            
            # Calculate overall trends
            analytics['trends'] = {
                'improving_metrics': len([m for m in analytics['metrics'].values() if m['trend_direction'] == 'improving']),
                'declining_metrics': len([m for m in analytics['metrics'].values() if m['trend_direction'] == 'declining']),
                'stable_metrics': len([m for m in analytics['metrics'].values() if m['trend_direction'] == 'stable']),
                'high_variance_metrics': [
                    metric for metric, data in analytics['metrics'].items() 
                    if abs(data['trend_percentage']) > 10
                ]
            }
            
            return jsonify({
                'success': True,
                'data': analytics
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def update_thresholds(self):
        """Update environmental thresholds"""
        try:
            data = request.get_json()
            
            metric_type = data.get('metric_type')
            thresholds = data.get('thresholds', {})
            
            if not metric_type or metric_type not in [m.value for m in EnvironmentalMetric]:
                return jsonify({'success': False, 'error': 'Invalid metric type'}), 400
            
            # Update thresholds
            metric_enum = EnvironmentalMetric(metric_type)
            self.environmental_monitor.thresholds[metric_enum] = thresholds
            
            return jsonify({
                'success': True,
                'data': {
                    'metric_type': metric_type,
                    'updated_thresholds': thresholds
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_environmental_metrics(self):
        """Get available environmental metrics and their configurations"""
        try:
            metrics = {}
            
            for metric in EnvironmentalMetric:
                thresholds = self.environmental_monitor.thresholds.get(metric, {})
                
                metrics[metric.value] = {
                    'name': metric.value.replace('_', ' ').title(),
                    'description': self._get_metric_description(metric),
                    'unit': self._get_metric_unit(metric),
                    'thresholds': thresholds,
                    'icon': self._get_metric_icon(metric)
                }
            
            return jsonify({
                'success': True,
                'data': {
                    'metrics': metrics,
                    'alert_levels': [level.value for level in AlertLevel]
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def _get_metric_description(self, metric: EnvironmentalMetric) -> str:
        """Get description for a metric"""
        descriptions = {
            EnvironmentalMetric.AIR_QUALITY: "Overall air quality index measuring pollutants and particulates",
            EnvironmentalMetric.INDOOR_AIR_QUALITY: "Indoor CO2 levels and air circulation quality",
            EnvironmentalMetric.NOISE_LEVEL: "Ambient noise levels in decibels",
            EnvironmentalMetric.WATER_QUALITY: "Water contamination and quality index",
            EnvironmentalMetric.ENERGY_EFFICIENCY: "Energy consumption per square foot",
            EnvironmentalMetric.CARBON_FOOTPRINT: "Carbon emissions and environmental impact",
            EnvironmentalMetric.WATER_CONSUMPTION: "Water usage and conservation metrics",
            EnvironmentalMetric.RENEWABLE_ENERGY: "Renewable energy generation and usage",
            EnvironmentalMetric.WASTE_MANAGEMENT: "Waste generation and recycling efficiency",
            EnvironmentalMetric.LIGHT_POLLUTION: "Light pollution and energy waste from lighting"
        }
        return descriptions.get(metric, "Environmental metric")
    
    def _get_metric_unit(self, metric: EnvironmentalMetric) -> str:
        """Get unit for a metric"""
        units = {
            EnvironmentalMetric.AIR_QUALITY: "AQI",
            EnvironmentalMetric.INDOOR_AIR_QUALITY: "ppm",
            EnvironmentalMetric.NOISE_LEVEL: "dB",
            EnvironmentalMetric.WATER_QUALITY: "WQI",
            EnvironmentalMetric.ENERGY_EFFICIENCY: "kWh/sqft",
            EnvironmentalMetric.CARBON_FOOTPRINT: "kg CO2",
            EnvironmentalMetric.WATER_CONSUMPTION: "gallons",
            EnvironmentalMetric.RENEWABLE_ENERGY: "kWh",
            EnvironmentalMetric.WASTE_MANAGEMENT: "lbs",
            EnvironmentalMetric.LIGHT_POLLUTION: "lux"
        }
        return units.get(metric, "units")
    
    def _get_metric_icon(self, metric: EnvironmentalMetric) -> str:
        """Get icon for a metric"""
        icons = {
            EnvironmentalMetric.AIR_QUALITY: "🌬️",
            EnvironmentalMetric.INDOOR_AIR_QUALITY: "🏠",
            EnvironmentalMetric.NOISE_LEVEL: "🔊",
            EnvironmentalMetric.WATER_QUALITY: "💧",
            EnvironmentalMetric.ENERGY_EFFICIENCY: "⚡",
            EnvironmentalMetric.CARBON_FOOTPRINT: "🌱",
            EnvironmentalMetric.WATER_CONSUMPTION: "🚿",
            EnvironmentalMetric.RENEWABLE_ENERGY: "☀️",
            EnvironmentalMetric.WASTE_MANAGEMENT: "♻️",
            EnvironmentalMetric.LIGHT_POLLUTION: "💡"
        }
        return icons.get(metric, "📊")

# Integration with main EstateCore app
def init_environmental_system(app: Flask):
    """Initialize environmental monitoring system with Flask app"""
    environmental_api = EnvironmentalAPI(app)
    return environmental_api