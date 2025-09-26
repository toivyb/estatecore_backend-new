import numpy as np
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import random
import threading
from dataclasses import dataclass
from enum import Enum

class SensorType(Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    OCCUPANCY = "occupancy"
    AIR_QUALITY = "air_quality"
    ENERGY = "energy"
    WATER = "water"
    SECURITY = "security"
    NOISE = "noise"
    LIGHT = "light"
    MOTION = "motion"

@dataclass
class SensorReading:
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime
    property_id: str
    location: str
    quality: str = "good"
    alert_triggered: bool = False

class IoTSensorManager:
    """
    Comprehensive IoT sensor management system for smart building integration
    """
    
    def __init__(self):
        self.sensors = {}
        self.sensor_data = {}
        self.alerts = []
        self.data_streams = {}
        self.is_streaming = False
        
    def register_sensor(self, sensor_config: Dict) -> str:
        """Register a new IoT sensor"""
        sensor_id = f"{sensor_config['type']}_{sensor_config['property_id']}_{sensor_config['location']}_{int(time.time())}"
        
        self.sensors[sensor_id] = {
            'id': sensor_id,
            'type': SensorType(sensor_config['type']),
            'property_id': sensor_config['property_id'],
            'location': sensor_config['location'],
            'model': sensor_config.get('model', 'Generic'),
            'manufacturer': sensor_config.get('manufacturer', 'Unknown'),
            'installed_date': datetime.now(),
            'calibration_date': datetime.now(),
            'status': 'active',
            'battery_level': sensor_config.get('battery_level', 100),
            'firmware_version': sensor_config.get('firmware_version', '1.0.0'),
            'sampling_rate': sensor_config.get('sampling_rate', 60),  # seconds
            'thresholds': sensor_config.get('thresholds', {}),
            'last_reading': None
        }
        
        self.sensor_data[sensor_id] = []
        return sensor_id
    
    def get_sensor_reading(self, sensor_id: str) -> Optional[SensorReading]:
        """Get current reading from a specific sensor"""
        if sensor_id not in self.sensors:
            return None
            
        sensor = self.sensors[sensor_id]
        reading = self._simulate_sensor_reading(sensor)
        
        # Store reading
        self.sensor_data[sensor_id].append(reading)
        self.sensors[sensor_id]['last_reading'] = reading.timestamp
        
        # Check for alerts
        self._check_alerts(reading, sensor)
        
        return reading
    
    def get_property_readings(self, property_id: str, sensor_types: List[str] = None) -> List[SensorReading]:
        """Get all current readings for a property"""
        readings = []
        
        for sensor_id, sensor in self.sensors.items():
            if sensor['property_id'] == property_id:
                if sensor_types is None or sensor['type'].value in sensor_types:
                    reading = self.get_sensor_reading(sensor_id)
                    if reading:
                        readings.append(reading)
        
        return readings
    
    def get_historical_data(self, sensor_id: str, hours_back: int = 24) -> List[SensorReading]:
        """Get historical sensor data"""
        if sensor_id not in self.sensor_data:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        return [
            reading for reading in self.sensor_data[sensor_id]
            if reading.timestamp >= cutoff_time
        ]
    
    def start_real_time_monitoring(self, callback_function=None):
        """Start real-time sensor monitoring"""
        self.is_streaming = True
        
        def monitor_loop():
            while self.is_streaming:
                for sensor_id in self.sensors:
                    reading = self.get_sensor_reading(sensor_id)
                    if callback_function and reading:
                        callback_function(reading)
                
                time.sleep(10)  # Check every 10 seconds
        
        self.monitoring_thread = threading.Thread(target=monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_real_time_monitoring(self):
        """Stop real-time sensor monitoring"""
        self.is_streaming = False
    
    def _simulate_sensor_reading(self, sensor: Dict) -> SensorReading:
        """Simulate sensor reading based on type"""
        sensor_type = sensor['type']
        location = sensor['location']
        current_time = datetime.now()
        
        # Simulate different sensor types
        if sensor_type == SensorType.TEMPERATURE:
            # Base temperature with daily variation
            hour = current_time.hour
            base_temp = 72 + 5 * np.sin((hour - 6) * np.pi / 12)  # Daily cycle
            noise = random.gauss(0, 1)
            value = round(base_temp + noise, 1)
            unit = "°F"
            
        elif sensor_type == SensorType.HUMIDITY:
            # Humidity typically inversely related to temperature
            base_humidity = 50 + random.gauss(0, 5)
            value = max(20, min(80, round(base_humidity, 1)))
            unit = "%"
            
        elif sensor_type == SensorType.OCCUPANCY:
            # Occupancy based on time of day
            hour = current_time.hour
            if 'bedroom' in location.lower():
                prob = 0.9 if 22 <= hour or hour <= 6 else 0.1
            elif 'kitchen' in location.lower():
                prob = 0.7 if 7 <= hour <= 9 or 17 <= hour <= 20 else 0.2
            else:
                prob = 0.6 if 9 <= hour <= 17 else 0.3
            
            value = 1 if random.random() < prob else 0
            unit = "occupied"
            
        elif sensor_type == SensorType.AIR_QUALITY:
            # Air quality index (0-500)
            base_aqi = 50 + random.gauss(0, 15)
            value = max(0, min(500, round(base_aqi)))
            unit = "AQI"
            
        elif sensor_type == SensorType.ENERGY:
            # Energy consumption in kWh
            hour = current_time.hour
            base_consumption = 2 + 3 * np.sin((hour - 12) * np.pi / 12)
            value = max(0, round(base_consumption + random.gauss(0, 0.5), 2))
            unit = "kWh"
            
        elif sensor_type == SensorType.WATER:
            # Water flow in gallons per minute
            # Higher during typical usage times
            hour = current_time.hour
            if 6 <= hour <= 9 or 17 <= hour <= 22:
                base_flow = random.choice([0, 0, 0, 2.5, 1.8])  # Intermittent usage
            else:
                base_flow = 0.1 if random.random() < 0.05 else 0  # Rare usage
            value = round(base_flow, 1)
            unit = "GPM"
            
        elif sensor_type == SensorType.SECURITY:
            # Security status (0 = secure, 1 = alert)
            value = 1 if random.random() < 0.01 else 0  # 1% chance of alert
            unit = "status"
            
        elif sensor_type == SensorType.NOISE:
            # Noise level in decibels
            hour = current_time.hour
            if 'street' in location.lower():
                base_noise = 45 if 22 <= hour or hour <= 6 else 55
            else:
                base_noise = 35 if 22 <= hour or hour <= 6 else 42
            
            value = round(base_noise + random.gauss(0, 3), 1)
            unit = "dB"
            
        elif sensor_type == SensorType.LIGHT:
            # Light level in lux
            hour = current_time.hour
            if 'outdoor' in location.lower():
                if 6 <= hour <= 18:
                    base_light = 10000 + random.gauss(0, 2000)
                else:
                    base_light = 1 + random.gauss(0, 0.5)
            else:
                base_light = 300 + random.gauss(0, 50) if 7 <= hour <= 22 else 10
            
            value = max(0, round(base_light, 1))
            unit = "lux"
            
        elif sensor_type == SensorType.MOTION:
            # Motion detection (0 = no motion, 1 = motion detected)
            # Similar to occupancy but more frequent
            prob = 0.3 if 8 <= current_time.hour <= 22 else 0.1
            value = 1 if random.random() < prob else 0
            unit = "detected"
            
        else:
            value = 0
            unit = "unknown"
        
        # Determine quality based on sensor status
        quality = "good"
        if sensor.get('battery_level', 100) < 20:
            quality = "poor"
        elif sensor.get('battery_level', 100) < 50:
            quality = "fair"
        
        return SensorReading(
            sensor_id=sensor['id'],
            sensor_type=sensor_type,
            value=value,
            unit=unit,
            timestamp=current_time,
            property_id=sensor['property_id'],
            location=location,
            quality=quality
        )
    
    def _check_alerts(self, reading: SensorReading, sensor: Dict):
        """Check if reading triggers any alerts"""
        thresholds = sensor.get('thresholds', {})
        
        for threshold_type, threshold_value in thresholds.items():
            alert_triggered = False
            
            if threshold_type == 'max' and reading.value > threshold_value:
                alert_triggered = True
            elif threshold_type == 'min' and reading.value < threshold_value:
                alert_triggered = True
            
            if alert_triggered:
                alert = {
                    'id': f"alert_{int(time.time())}_{random.randint(1000, 9999)}",
                    'sensor_id': reading.sensor_id,
                    'property_id': reading.property_id,
                    'location': reading.location,
                    'sensor_type': reading.sensor_type.value,
                    'alert_type': threshold_type,
                    'current_value': reading.value,
                    'threshold_value': threshold_value,
                    'timestamp': reading.timestamp,
                    'severity': self._determine_alert_severity(reading, threshold_type, threshold_value),
                    'status': 'active'
                }
                
                self.alerts.append(alert)
                reading.alert_triggered = True
    
    def _determine_alert_severity(self, reading: SensorReading, threshold_type: str, threshold_value: float) -> str:
        """Determine alert severity based on how far the value is from threshold"""
        if reading.sensor_type == SensorType.TEMPERATURE:
            if abs(reading.value - threshold_value) > 10:
                return 'critical'
            elif abs(reading.value - threshold_value) > 5:
                return 'high'
            else:
                return 'medium'
        
        elif reading.sensor_type == SensorType.SECURITY:
            return 'critical'
        
        elif reading.sensor_type == SensorType.WATER:
            if reading.value > 5:  # High water flow
                return 'high'
            else:
                return 'medium'
        
        else:
            return 'medium'
    
    def get_active_alerts(self, property_id: str = None) -> List[Dict]:
        """Get all active alerts"""
        active_alerts = [alert for alert in self.alerts if alert['status'] == 'active']
        
        if property_id:
            active_alerts = [alert for alert in active_alerts if alert['property_id'] == property_id]
        
        return active_alerts
    
    def get_sensor_status_summary(self, property_id: str = None) -> Dict:
        """Get summary of all sensor statuses"""
        relevant_sensors = self.sensors
        if property_id:
            relevant_sensors = {k: v for k, v in self.sensors.items() if v['property_id'] == property_id}
        
        total_sensors = len(relevant_sensors)
        active_sensors = len([s for s in relevant_sensors.values() if s['status'] == 'active'])
        low_battery_sensors = len([s for s in relevant_sensors.values() if s.get('battery_level', 100) < 30])
        
        # Get sensor type distribution
        type_distribution = {}
        for sensor in relevant_sensors.values():
            sensor_type = sensor['type'].value
            type_distribution[sensor_type] = type_distribution.get(sensor_type, 0) + 1
        
        return {
            'total_sensors': total_sensors,
            'active_sensors': active_sensors,
            'inactive_sensors': total_sensors - active_sensors,
            'low_battery_sensors': low_battery_sensors,
            'sensor_types': type_distribution,
            'last_updated': datetime.now().isoformat()
        }

def analyze_sensor_data(sensor_readings: List[SensorReading]) -> Dict:
    """
    Analyze sensor data to extract insights and patterns
    """
    if not sensor_readings:
        return {'error': 'No sensor data provided'}
    
    # Group readings by sensor type
    readings_by_type = {}
    for reading in sensor_readings:
        sensor_type = reading.sensor_type.value
        if sensor_type not in readings_by_type:
            readings_by_type[sensor_type] = []
        readings_by_type[sensor_type].append(reading)
    
    # Analyze each sensor type
    analysis_results = {}
    
    for sensor_type, readings in readings_by_type.items():
        if sensor_type == 'temperature':
            analysis_results[sensor_type] = analyze_temperature_data(readings)
        elif sensor_type == 'humidity':
            analysis_results[sensor_type] = analyze_humidity_data(readings)
        elif sensor_type == 'occupancy':
            analysis_results[sensor_type] = analyze_occupancy_data(readings)
        elif sensor_type == 'energy':
            analysis_results[sensor_type] = analyze_energy_data(readings)
        elif sensor_type == 'air_quality':
            analysis_results[sensor_type] = analyze_air_quality_data(readings)
        else:
            analysis_results[sensor_type] = analyze_generic_sensor_data(readings)
    
    # Generate overall insights
    overall_insights = generate_overall_insights(analysis_results, sensor_readings)
    
    return {
        'sensor_analysis': analysis_results,
        'overall_insights': overall_insights,
        'data_quality_score': calculate_data_quality_score(sensor_readings),
        'analysis_timestamp': datetime.now().isoformat()
    }

def analyze_temperature_data(readings: List[SensorReading]) -> Dict:
    """Analyze temperature sensor data"""
    values = [r.value for r in readings]
    
    if not values:
        return {'error': 'No temperature data'}
    
    avg_temp = float(np.mean(values))
    min_temp = float(np.min(values))
    max_temp = float(np.max(values))
    temp_variance = float(np.var(values))
    
    # Comfort analysis
    comfort_range = (68, 78)  # Ideal temperature range
    comfort_percentage = len([v for v in values if comfort_range[0] <= v <= comfort_range[1]]) / len(values) * 100
    
    # Trend analysis
    if len(values) >= 2:
        trend = 'increasing' if values[-1] > values[0] else 'decreasing' if values[-1] < values[0] else 'stable'
    else:
        trend = 'insufficient_data'
    
    return {
        'average_temperature': round(avg_temp, 1),
        'min_temperature': round(min_temp, 1),
        'max_temperature': round(max_temp, 1),
        'temperature_variance': round(temp_variance, 2),
        'comfort_percentage': round(comfort_percentage, 1),
        'trend': trend,
        'recommendations': generate_temperature_recommendations(avg_temp, comfort_percentage)
    }

def analyze_humidity_data(readings: List[SensorReading]) -> Dict:
    """Analyze humidity sensor data"""
    values = [r.value for r in readings]
    
    if not values:
        return {'error': 'No humidity data'}
    
    avg_humidity = float(np.mean(values))
    min_humidity = float(np.min(values))
    max_humidity = float(np.max(values))
    
    # Comfort analysis (30-50% is ideal)
    comfort_range = (30, 50)
    comfort_percentage = len([v for v in values if comfort_range[0] <= v <= comfort_range[1]]) / len(values) * 100
    
    # Mold risk analysis (>60% sustained)
    high_humidity_percentage = len([v for v in values if v > 60]) / len(values) * 100
    
    return {
        'average_humidity': round(avg_humidity, 1),
        'min_humidity': round(min_humidity, 1),
        'max_humidity': round(max_humidity, 1),
        'comfort_percentage': round(comfort_percentage, 1),
        'high_humidity_percentage': round(high_humidity_percentage, 1),
        'mold_risk': 'high' if high_humidity_percentage > 20 else 'low',
        'recommendations': generate_humidity_recommendations(avg_humidity, high_humidity_percentage)
    }

def analyze_occupancy_data(readings: List[SensorReading]) -> Dict:
    """Analyze occupancy sensor data"""
    values = [r.value for r in readings]
    timestamps = [r.timestamp for r in readings]
    
    if not values:
        return {'error': 'No occupancy data'}
    
    total_readings = len(values)
    occupied_readings = sum(values)
    occupancy_rate = occupied_readings / total_readings * 100
    
    # Find peak occupancy hours
    hourly_occupancy = {}
    for reading in readings:
        hour = reading.timestamp.hour
        if hour not in hourly_occupancy:
            hourly_occupancy[hour] = []
        hourly_occupancy[hour].append(reading.value)
    
    peak_hours = []
    for hour, hourly_values in hourly_occupancy.items():
        if np.mean(hourly_values) > 0.5:  # More than 50% occupied
            peak_hours.append(hour)
    
    return {
        'occupancy_rate': round(occupancy_rate, 1),
        'total_readings': total_readings,
        'occupied_periods': occupied_readings,
        'peak_hours': sorted(peak_hours),
        'utilization_pattern': determine_utilization_pattern(peak_hours),
        'recommendations': generate_occupancy_recommendations(occupancy_rate, peak_hours)
    }

def analyze_energy_data(readings: List[SensorReading]) -> Dict:
    """Analyze energy consumption data"""
    values = [r.value for r in readings]
    
    if not values:
        return {'error': 'No energy data'}
    
    total_consumption = sum(values)
    avg_consumption = float(np.mean(values))
    peak_consumption = float(np.max(values))
    
    # Energy efficiency score (lower consumption = higher score)
    baseline_consumption = 3.0  # kWh baseline
    efficiency_score = max(0, 100 - (avg_consumption / baseline_consumption - 1) * 100)
    
    return {
        'total_consumption': round(total_consumption, 2),
        'average_consumption': round(avg_consumption, 2),
        'peak_consumption': round(peak_consumption, 2),
        'efficiency_score': round(efficiency_score, 1),
        'estimated_monthly_cost': round(total_consumption * 0.12 * 30, 2),  # $0.12/kWh
        'recommendations': generate_energy_recommendations(avg_consumption, efficiency_score)
    }

def analyze_air_quality_data(readings: List[SensorReading]) -> Dict:
    """Analyze air quality sensor data"""
    values = [r.value for r in readings]
    
    if not values:
        return {'error': 'No air quality data'}
    
    avg_aqi = float(np.mean(values))
    max_aqi = float(np.max(values))
    
    # AQI categories
    if avg_aqi <= 50:
        category = 'good'
    elif avg_aqi <= 100:
        category = 'moderate'
    elif avg_aqi <= 150:
        category = 'unhealthy_for_sensitive'
    else:
        category = 'unhealthy'
    
    return {
        'average_aqi': round(avg_aqi, 1),
        'max_aqi': round(max_aqi, 1),
        'air_quality_category': category,
        'good_air_percentage': round(len([v for v in values if v <= 50]) / len(values) * 100, 1),
        'recommendations': generate_air_quality_recommendations(avg_aqi, category)
    }

def analyze_generic_sensor_data(readings: List[SensorReading]) -> Dict:
    """Analyze generic sensor data"""
    values = [r.value for r in readings]
    
    if not values:
        return {'error': 'No sensor data'}
    
    return {
        'average_value': round(float(np.mean(values)), 2),
        'min_value': round(float(np.min(values)), 2),
        'max_value': round(float(np.max(values)), 2),
        'reading_count': len(values),
        'data_range': round(float(np.max(values) - np.min(values)), 2)
    }

def generate_overall_insights(analysis_results: Dict, sensor_readings: List[SensorReading]) -> List[str]:
    """Generate overall insights from all sensor data"""
    insights = []
    
    # Temperature insights
    if 'temperature' in analysis_results:
        temp_data = analysis_results['temperature']
        if temp_data.get('comfort_percentage', 0) < 70:
            insights.append('Temperature comfort levels are below optimal - consider HVAC adjustments')
    
    # Humidity insights
    if 'humidity' in analysis_results:
        humidity_data = analysis_results['humidity']
        if humidity_data.get('mold_risk') == 'high':
            insights.append('High humidity levels detected - risk of mold growth')
    
    # Energy insights
    if 'energy' in analysis_results:
        energy_data = analysis_results['energy']
        if energy_data.get('efficiency_score', 100) < 70:
            insights.append('Energy consumption is above average - consider efficiency improvements')
    
    # Occupancy insights
    if 'occupancy' in analysis_results:
        occupancy_data = analysis_results['occupancy']
        if occupancy_data.get('occupancy_rate', 0) > 80:
            insights.append('High occupancy detected - space utilization is excellent')
    
    return insights

def calculate_data_quality_score(sensor_readings: List[SensorReading]) -> float:
    """Calculate overall data quality score"""
    if not sensor_readings:
        return 0.0
    
    quality_scores = {'good': 1.0, 'fair': 0.7, 'poor': 0.3}
    total_score = sum(quality_scores.get(reading.quality, 0.5) for reading in sensor_readings)
    
    return round(total_score / len(sensor_readings) * 100, 1)

# Helper functions for recommendations
def generate_temperature_recommendations(avg_temp: float, comfort_percentage: float) -> List[str]:
    """Generate temperature-specific recommendations"""
    recommendations = []
    
    if avg_temp < 68:
        recommendations.append('Consider increasing heating to improve comfort')
    elif avg_temp > 78:
        recommendations.append('Consider increasing cooling to improve comfort')
    
    if comfort_percentage < 70:
        recommendations.append('Install programmable thermostat for better temperature control')
    
    return recommendations

def generate_humidity_recommendations(avg_humidity: float, high_humidity_percentage: float) -> List[str]:
    """Generate humidity-specific recommendations"""
    recommendations = []
    
    if avg_humidity > 60:
        recommendations.append('Install dehumidifier to reduce moisture levels')
    elif avg_humidity < 30:
        recommendations.append('Consider humidifier to increase moisture levels')
    
    if high_humidity_percentage > 20:
        recommendations.append('Improve ventilation to prevent mold growth')
    
    return recommendations

def generate_occupancy_recommendations(occupancy_rate: float, peak_hours: List[int]) -> List[str]:
    """Generate occupancy-specific recommendations"""
    recommendations = []
    
    if occupancy_rate > 80:
        recommendations.append('Space is highly utilized - consider expansion')
    elif occupancy_rate < 30:
        recommendations.append('Low utilization - consider space optimization')
    
    if len(peak_hours) > 12:
        recommendations.append('Extended usage patterns - ensure adequate maintenance')
    
    return recommendations

def generate_energy_recommendations(avg_consumption: float, efficiency_score: float) -> List[str]:
    """Generate energy-specific recommendations"""
    recommendations = []
    
    if efficiency_score < 70:
        recommendations.append('Consider energy-efficient appliances and LED lighting')
    
    if avg_consumption > 4:
        recommendations.append('High energy usage detected - audit for energy waste')
    
    return recommendations

def generate_air_quality_recommendations(avg_aqi: float, category: str) -> List[str]:
    """Generate air quality-specific recommendations"""
    recommendations = []
    
    if category in ['unhealthy', 'unhealthy_for_sensitive']:
        recommendations.append('Install air purifier and improve ventilation')
    elif category == 'moderate':
        recommendations.append('Monitor air quality and consider filtration improvements')
    
    return recommendations

def determine_utilization_pattern(peak_hours: List[int]) -> str:
    """Determine utilization pattern from peak hours"""
    if not peak_hours:
        return 'minimal_use'
    
    if len(peak_hours) >= 12:
        return 'high_utilization'
    elif 9 <= min(peak_hours) <= 17 and max(peak_hours) <= 17:
        return 'business_hours'
    elif any(hour >= 18 or hour <= 6 for hour in peak_hours):
        return 'extended_hours'
    else:
        return 'standard_use'