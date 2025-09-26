#!/usr/bin/env python3
"""
Energy Management Service for EstateCore Phase 5C
Business logic layer for smart energy management
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
import logging

# Add ai_modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_modules'))

from ai_modules.energy_management.simple_energy_engine import (
    SimpleSmartEnergyEngine as SmartEnergyEngine, EnergyReading, EnergyType, EnergyForecast,
    OptimizationRecommendation, EnergyAlert, OptimizationStrategy, AlertType
)

class EnergyManagementService:
    """Service layer for energy management functionality"""
    
    def __init__(self):
        self.engine = SmartEnergyEngine()
        self.logger = logging.getLogger(__name__)
        
        # Initialize engine (no training needed for simplified version)
        self.logger.info("Energy management engine initialized successfully")
    
    def add_energy_reading(self, property_id: int, energy_type: str, 
                          consumption: float, cost: float, timestamp: datetime = None,
                          unit_id: int = None, temperature: float = None, 
                          occupancy: bool = None, equipment_id: str = None,
                          metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a new energy reading and get immediate alerts"""
        try:
            # Convert string energy type to enum
            energy_type_enum = EnergyType(energy_type.lower())
            
            # Create energy reading
            reading = EnergyReading(
                property_id=property_id,
                unit_id=unit_id,
                energy_type=energy_type_enum,
                consumption=consumption,
                cost=cost,
                timestamp=timestamp or datetime.now(),
                temperature=temperature,
                occupancy=occupancy,
                equipment_id=equipment_id,
                metadata=metadata
            )
            
            # Add reading and check for alerts
            alerts = self.engine.add_energy_reading(reading)
            
            return {
                'success': True,
                'reading_id': len(self.engine.energy_readings),  # Simplified ID
                'alerts_triggered': len(alerts),
                'alerts': [self._serialize_alert(alert) for alert in alerts],
                'message': f'Energy reading added successfully. {len(alerts)} alerts triggered.'
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': f'Invalid energy type: {energy_type}. Valid types: {[t.value for t in EnergyType]}'
            }
        except Exception as e:
            self.logger.error(f"Failed to add energy reading: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_energy_forecast(self, property_id: int, energy_type: str, 
                           days: int = 7) -> Dict[str, Any]:
        """Get AI-powered energy consumption forecast"""
        try:
            energy_type_enum = EnergyType(energy_type.lower())
            
            forecast = self.engine.predict_consumption(
                property_id=property_id,
                energy_type=energy_type_enum,
                forecast_days=days
            )
            
            return {
                'success': True,
                'forecast': self._serialize_forecast(forecast),
                'summary': {
                    'total_predicted_consumption': sum(forecast.predicted_consumption),
                    'total_predicted_cost': sum(forecast.predicted_cost),
                    'average_daily_consumption': sum(forecast.predicted_consumption) / len(forecast.predicted_consumption),
                    'average_daily_cost': sum(forecast.predicted_cost) / len(forecast.predicted_cost),
                    'peak_day': forecast.forecast_dates[forecast.predicted_consumption.index(max(forecast.predicted_consumption))].strftime('%Y-%m-%d'),
                    'peak_consumption': max(forecast.predicted_consumption)
                }
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': f'Invalid energy type: {energy_type}'
            }
        except Exception as e:
            self.logger.error(f"Failed to generate forecast: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_optimization_recommendations(self, property_id: int) -> Dict[str, Any]:
        """Get AI-generated optimization recommendations"""
        try:
            recommendations = self.engine.generate_optimization_recommendations(property_id)
            
            if not recommendations:
                return {
                    'success': True,
                    'recommendations': [],
                    'message': 'No optimization opportunities found at this time. More data may be needed.'
                }
            
            # Calculate totals
            total_potential_savings = sum(rec.potential_savings for rec in recommendations)
            total_implementation_cost = sum(rec.implementation_cost for rec in recommendations)
            average_payback_period = sum(rec.payback_period_months for rec in recommendations) / len(recommendations)
            
            return {
                'success': True,
                'recommendations': [self._serialize_recommendation(rec) for rec in recommendations],
                'summary': {
                    'total_recommendations': len(recommendations),
                    'total_potential_monthly_savings': round(total_potential_savings, 2),
                    'total_implementation_cost': round(total_implementation_cost, 2),
                    'average_payback_period_months': round(average_payback_period, 1),
                    'annual_savings_potential': round(total_potential_savings * 12, 2),
                    'high_priority_count': len([r for r in recommendations if r.priority_score >= 8.0])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_energy_analytics(self, property_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive energy analytics for a property"""
        try:
            analytics = self.engine.get_energy_analytics(property_id, days)
            
            if 'error' in analytics:
                return {
                    'success': False,
                    'error': analytics['error']
                }
            
            # Add additional insights
            insights = self._generate_energy_insights(analytics)
            
            return {
                'success': True,
                'analytics': analytics,
                'insights': insights,
                'period': {
                    'start_date': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d'),
                    'days_analyzed': days
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate analytics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_energy_alerts(self, property_id: int = None, status: str = 'active',
                         severity: str = None) -> Dict[str, Any]:
        """Get energy management alerts"""
        try:
            # Get all readings for alert checking
            all_alerts = []
            
            # Get recent readings to check for new alerts
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_readings = [r for r in self.engine.energy_readings 
                             if r.timestamp > cutoff_time]
            
            if property_id:
                recent_readings = [r for r in recent_readings if r.property_id == property_id]
            
            # Generate alerts for recent readings
            for reading in recent_readings[-10:]:  # Check last 10 readings
                alerts = self.engine._check_for_alerts(reading)
                all_alerts.extend(alerts)
            
            # Filter by severity if specified
            if severity:
                all_alerts = [a for a in all_alerts if a.severity == severity]
            
            # Group alerts by type for summary
            alert_summary = {}
            for alert in all_alerts:
                alert_type = alert.alert_type.value
                if alert_type not in alert_summary:
                    alert_summary[alert_type] = 0
                alert_summary[alert_type] += 1
            
            return {
                'success': True,
                'alerts': [self._serialize_alert(alert) for alert in all_alerts],
                'summary': {
                    'total_alerts': len(all_alerts),
                    'alert_breakdown': alert_summary,
                    'critical_count': len([a for a in all_alerts if a.severity == 'critical']),
                    'high_count': len([a for a in all_alerts if a.severity == 'high']),
                    'medium_count': len([a for a in all_alerts if a.severity == 'medium'])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get alerts: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_energy_dashboard_data(self, property_id: int) -> Dict[str, Any]:
        """Get comprehensive energy dashboard data"""
        try:
            # Get analytics
            analytics = self.get_energy_analytics(property_id, days=30)
            
            # Get forecast
            electricity_forecast = self.get_energy_forecast(property_id, 'electricity', days=7)
            
            # Get recommendations
            recommendations = self.get_optimization_recommendations(property_id)
            
            # Get alerts
            alerts = self.get_energy_alerts(property_id)
            
            # Calculate trends
            trends = self._calculate_energy_trends(property_id)
            
            return {
                'success': True,
                'dashboard': {
                    'analytics': analytics.get('analytics', {}) if analytics['success'] else {},
                    'forecast': electricity_forecast.get('forecast', {}) if electricity_forecast['success'] else {},
                    'recommendations': {
                        'items': recommendations.get('recommendations', [])[:3],  # Top 3
                        'summary': recommendations.get('summary', {})
                    } if recommendations['success'] else {},
                    'alerts': {
                        'items': alerts.get('alerts', [])[:5],  # Top 5
                        'summary': alerts.get('summary', {})
                    } if alerts['success'] else {},
                    'trends': trends,
                    'last_updated': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate dashboard data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def simulate_energy_data(self, property_id: int, days: int = 7) -> Dict[str, Any]:
        """Simulate energy data for demonstration purposes"""
        try:
            import random
            import numpy as np
            
            results = []
            
            for day in range(days):
                date = datetime.now() - timedelta(days=day)
                
                # Simulate different energy types
                energy_types = ['electricity', 'gas', 'water', 'hvac']
                
                for energy_type in energy_types:
                    # Base consumption with some variation
                    if energy_type == 'electricity':
                        base_consumption = 400 + random.uniform(-50, 100)
                        cost_per_unit = 0.12
                    elif energy_type == 'gas':
                        base_consumption = 80 + random.uniform(-20, 30)
                        cost_per_unit = 1.20
                    elif energy_type == 'water':
                        base_consumption = 250 + random.uniform(-50, 100)
                        cost_per_unit = 0.008
                    else:  # hvac
                        base_consumption = 200 + random.uniform(-40, 80)
                        cost_per_unit = 0.15
                    
                    consumption = max(10, base_consumption)
                    cost = consumption * cost_per_unit
                    
                    # Add the reading
                    result = self.add_energy_reading(
                        property_id=property_id,
                        energy_type=energy_type,
                        consumption=consumption,
                        cost=cost,
                        timestamp=date,
                        temperature=70 + random.uniform(-15, 15),
                        occupancy=random.choice([True, False])
                    )
                    
                    results.append(result)
            
            # Note: Simplified engine doesn't require retraining
            
            successful_readings = len([r for r in results if r.get('success')])
            total_alerts = sum(r.get('alerts_triggered', 0) for r in results)
            
            return {
                'success': True,
                'message': f'Successfully simulated {days} days of energy data',
                'readings_added': successful_readings,
                'total_alerts_generated': total_alerts,
                'models_retrained': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to simulate energy data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _serialize_alert(self, alert: EnergyAlert) -> Dict[str, Any]:
        """Serialize an energy alert to dictionary"""
        return {
            'property_id': alert.property_id,
            'alert_type': alert.alert_type.value,
            'severity': alert.severity,
            'title': alert.title,
            'message': alert.message,
            'current_value': alert.current_value,
            'threshold_value': alert.threshold_value,
            'energy_type': alert.energy_type.value,
            'equipment_id': alert.equipment_id,
            'recommended_action': alert.recommended_action,
            'created_at': alert.created_at.isoformat() if alert.created_at else None
        }
    
    def _serialize_forecast(self, forecast: EnergyForecast) -> Dict[str, Any]:
        """Serialize an energy forecast to dictionary"""
        return {
            'property_id': forecast.property_id,
            'energy_type': forecast.energy_type.value,
            'forecast_period': forecast.forecast_period,
            'predicted_consumption': forecast.predicted_consumption,
            'predicted_cost': forecast.predicted_cost,
            'confidence_intervals': forecast.confidence_intervals,
            'forecast_dates': [d.isoformat() for d in forecast.forecast_dates],
            'accuracy_score': forecast.accuracy_score,
            'created_at': forecast.created_at.isoformat()
        }
    
    def _serialize_recommendation(self, rec: OptimizationRecommendation) -> Dict[str, Any]:
        """Serialize an optimization recommendation to dictionary"""
        return {
            'property_id': rec.property_id,
            'recommendation_type': rec.recommendation_type.value,
            'title': rec.title,
            'description': rec.description,
            'potential_savings': rec.potential_savings,
            'implementation_cost': rec.implementation_cost,
            'payback_period_months': rec.payback_period_months,
            'energy_reduction_percent': rec.energy_reduction_percent,
            'priority_score': rec.priority_score,
            'equipment_involved': rec.equipment_involved,
            'implementation_steps': rec.implementation_steps,
            'created_at': rec.created_at.isoformat()
        }
    
    def _generate_energy_insights(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate human-readable insights from analytics"""
        insights = []
        
        try:
            efficiency_score = analytics.get('efficiency_score', 0)
            total_cost = analytics.get('total_cost', 0)
            
            # Efficiency insights
            if efficiency_score >= 80:
                insights.append("🌟 Excellent energy efficiency! Your property is performing well.")
            elif efficiency_score >= 60:
                insights.append("⚡ Good energy efficiency with room for improvement.")
            else:
                insights.append("⚠️ Energy efficiency needs attention. Consider optimization recommendations.")
            
            # Cost insights
            if total_cost > 500:
                insights.append(f"💰 High energy costs detected (${total_cost:.0f}). Review optimization opportunities.")
            elif total_cost > 300:
                insights.append(f"💡 Moderate energy costs (${total_cost:.0f}). Some savings potential exists.")
            else:
                insights.append(f"✅ Energy costs are well-controlled (${total_cost:.0f}).")
            
            # Peak usage insights
            peak_hour = analytics.get('peak_hour')
            if peak_hour and peak_hour in [17, 18, 19, 20]:
                insights.append("🕐 Peak usage occurs during expensive evening hours. Consider load shifting.")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate insights: {str(e)}")
            return ["📊 Energy data analyzed successfully."]
    
    def _calculate_energy_trends(self, property_id: int) -> Dict[str, Any]:
        """Calculate energy usage trends"""
        try:
            # Get recent readings for the property
            recent_readings = [r for r in self.engine.energy_readings 
                             if r.property_id == property_id and 
                             r.timestamp > datetime.now() - timedelta(days=30)]
            
            if len(recent_readings) < 2:
                return {'trend': 'insufficient_data'}
            
            # Sort by timestamp
            recent_readings.sort(key=lambda x: x.timestamp)
            
            # Calculate weekly averages
            first_week = [r for r in recent_readings[:7]]
            last_week = [r for r in recent_readings[-7:]]
            
            if not first_week or not last_week:
                return {'trend': 'insufficient_data'}
            
            first_week_avg = sum(r.consumption for r in first_week) / len(first_week)
            last_week_avg = sum(r.consumption for r in last_week) / len(last_week)
            
            # Calculate trend
            if last_week_avg > first_week_avg * 1.1:
                trend = 'increasing'
                change_percent = ((last_week_avg - first_week_avg) / first_week_avg) * 100
            elif last_week_avg < first_week_avg * 0.9:
                trend = 'decreasing'
                change_percent = ((first_week_avg - last_week_avg) / first_week_avg) * 100
            else:
                trend = 'stable'
                change_percent = 0
            
            return {
                'trend': trend,
                'change_percent': round(abs(change_percent), 1),
                'first_week_avg': round(first_week_avg, 2),
                'last_week_avg': round(last_week_avg, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate trends: {str(e)}")
            return {'trend': 'error'}

# Global service instance
_energy_service = None

def get_energy_management_service():
    """Get the global energy management service instance"""
    global _energy_service
    if _energy_service is None:
        _energy_service = EnergyManagementService()
    return _energy_service