import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

def generate_smart_notifications(tenant_data: Dict, property_data: Dict, maintenance_data: Dict, financial_data: Dict) -> Dict:
    """
    Generate intelligent, prioritized notifications using ML-based analysis
    
    Args:
        tenant_data (dict): Tenant information and behavior patterns
        property_data (dict): Property status and conditions
        maintenance_data (dict): Maintenance requests and history
        financial_data (dict): Payment and financial data
    
    Returns:
        dict: Prioritized notifications with urgency levels and routing recommendations
    """
    
    # Generate different types of notifications
    urgent_notifications = generate_urgent_notifications(tenant_data, property_data, maintenance_data, financial_data)
    proactive_notifications = generate_proactive_notifications(tenant_data, property_data, maintenance_data)
    routine_notifications = generate_routine_notifications(tenant_data, property_data, financial_data)
    
    # Prioritize and score all notifications
    all_notifications = urgent_notifications + proactive_notifications + routine_notifications
    prioritized_notifications = prioritize_notifications(all_notifications, tenant_data, property_data)
    
    # Generate routing recommendations
    routing_recommendations = generate_routing_recommendations(prioritized_notifications)
    
    # Create notification schedules
    notification_schedule = create_notification_schedule(prioritized_notifications)
    
    # Analytics and insights
    notification_analytics = analyze_notification_patterns(prioritized_notifications, tenant_data)
    
    return {
        'total_notifications': len(prioritized_notifications),
        'urgent_count': len([n for n in prioritized_notifications if n['urgency'] == 'urgent']),
        'high_priority_count': len([n for n in prioritized_notifications if n['priority_score'] >= 8]),
        'notifications': prioritized_notifications[:20],  # Top 20 notifications
        'routing_recommendations': routing_recommendations,
        'notification_schedule': notification_schedule,
        'analytics': notification_analytics,
        'ai_insights': generate_ai_insights(prioritized_notifications, tenant_data, property_data),
        'last_updated': datetime.now().isoformat()
    }

def generate_urgent_notifications(tenant_data: Dict, property_data: Dict, maintenance_data: Dict, financial_data: Dict) -> List[Dict]:
    """
    Generate urgent notifications requiring immediate attention
    """
    notifications = []
    
    # Emergency maintenance issues
    emergency_requests = maintenance_data.get('emergency_requests', [])
    for request in emergency_requests:
        if request.get('status') == 'open' and request.get('priority') == 'emergency':
            notifications.append({
                'id': f"emergency_maintenance_{request.get('id')}",
                'type': 'emergency_maintenance',
                'title': f"Emergency Maintenance: {request.get('description', 'Unknown issue')}",
                'message': f"Emergency maintenance request reported at {request.get('property_address', 'Unknown location')}",
                'urgency': 'urgent',
                'priority_score': 10,
                'tenant_id': request.get('tenant_id'),
                'property_id': request.get('property_id'),
                'created_time': request.get('created_time', datetime.now().isoformat()),
                'deadline': (datetime.now() + timedelta(hours=2)).isoformat(),
                'tags': ['emergency', 'maintenance', 'immediate_action'],
                'estimated_response_time': '2 hours',
                'escalation_required': True
            })
    
    # Late payment alerts (over 10 days)
    late_payments = financial_data.get('late_payments', [])
    for payment in late_payments:
        if payment.get('days_late', 0) > 10:
            notifications.append({
                'id': f"late_payment_{payment.get('tenant_id')}",
                'type': 'late_payment',
                'title': f"Severe Late Payment: {payment.get('tenant_name', 'Unknown tenant')}",
                'message': f"Payment overdue by {payment.get('days_late')} days. Amount: ${payment.get('amount', 0)}",
                'urgency': 'urgent',
                'priority_score': 9,
                'tenant_id': payment.get('tenant_id'),
                'property_id': payment.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': (datetime.now() + timedelta(days=3)).isoformat(),
                'tags': ['finance', 'late_payment', 'collections'],
                'estimated_response_time': '24 hours',
                'escalation_required': True
            })
    
    # Safety and security issues
    security_incidents = property_data.get('security_incidents', [])
    for incident in security_incidents:
        if incident.get('severity') in ['high', 'critical']:
            notifications.append({
                'id': f"security_incident_{incident.get('id')}",
                'type': 'security_incident',
                'title': f"Security Incident: {incident.get('type', 'Unknown incident')}",
                'message': f"Security incident reported at {incident.get('location', 'Unknown location')}",
                'urgency': 'urgent',
                'priority_score': 9,
                'property_id': incident.get('property_id'),
                'created_time': incident.get('reported_time', datetime.now().isoformat()),
                'deadline': (datetime.now() + timedelta(hours=4)).isoformat(),
                'tags': ['security', 'safety', 'incident'],
                'estimated_response_time': '4 hours',
                'escalation_required': True
            })
    
    # Lease expiration warnings (30 days or less)
    tenant_leases = tenant_data.get('lease_expirations', [])
    for lease in tenant_leases:
        expiry_date = datetime.fromisoformat(lease.get('expiry_date', '2024-12-31'))
        days_until_expiry = (expiry_date - datetime.now()).days
        
        if days_until_expiry <= 30 and not lease.get('renewal_initiated', False):
            notifications.append({
                'id': f"lease_expiring_{lease.get('tenant_id')}",
                'type': 'lease_expiration',
                'title': f"Lease Expiring Soon: {lease.get('tenant_name', 'Unknown tenant')}",
                'message': f"Lease expires in {days_until_expiry} days. Renewal status: {lease.get('renewal_status', 'Unknown')}",
                'urgency': 'urgent' if days_until_expiry <= 14 else 'high',
                'priority_score': 8 if days_until_expiry <= 14 else 7,
                'tenant_id': lease.get('tenant_id'),
                'property_id': lease.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': (expiry_date - timedelta(days=7)).isoformat(),
                'tags': ['lease', 'expiration', 'renewal'],
                'estimated_response_time': '24 hours',
                'escalation_required': days_until_expiry <= 14
            })
    
    return notifications

def generate_proactive_notifications(tenant_data: Dict, property_data: Dict, maintenance_data: Dict) -> List[Dict]:
    """
    Generate proactive notifications for preventive actions
    """
    notifications = []
    
    # Predictive maintenance alerts
    equipment_health = maintenance_data.get('equipment_health', [])
    for equipment in equipment_health:
        if equipment.get('failure_probability_30d', 0) > 0.3:
            notifications.append({
                'id': f"predictive_maintenance_{equipment.get('id')}",
                'type': 'predictive_maintenance',
                'title': f"Preventive Maintenance Recommended: {equipment.get('name', 'Unknown equipment')}",
                'message': f"Equipment showing signs of potential failure. Probability: {equipment.get('failure_probability_30d', 0):.1%}",
                'urgency': 'high',
                'priority_score': 7,
                'property_id': equipment.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': (datetime.now() + timedelta(days=14)).isoformat(),
                'tags': ['maintenance', 'preventive', 'equipment'],
                'estimated_response_time': '72 hours',
                'escalation_required': False
            })
    
    # Tenant satisfaction alerts
    satisfaction_scores = tenant_data.get('satisfaction_scores', [])
    for score in satisfaction_scores:
        if score.get('score', 10) <= 3:  # Low satisfaction
            notifications.append({
                'id': f"tenant_satisfaction_{score.get('tenant_id')}",
                'type': 'tenant_satisfaction',
                'title': f"Low Tenant Satisfaction: {score.get('tenant_name', 'Unknown tenant')}",
                'message': f"Tenant satisfaction score: {score.get('score', 0)}/10. Recent issues: {', '.join(score.get('issues', []))}",
                'urgency': 'medium',
                'priority_score': 6,
                'tenant_id': score.get('tenant_id'),
                'property_id': score.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': (datetime.now() + timedelta(days=7)).isoformat(),
                'tags': ['tenant', 'satisfaction', 'retention'],
                'estimated_response_time': '48 hours',
                'escalation_required': False
            })
    
    # Market rent analysis alerts
    rent_analysis = property_data.get('rent_analysis', [])
    for analysis in rent_analysis:
        if analysis.get('market_position') == 'significantly_below':
            notifications.append({
                'id': f"rent_optimization_{analysis.get('property_id')}",
                'type': 'rent_optimization',
                'title': f"Rent Optimization Opportunity: {analysis.get('property_address', 'Unknown property')}",
                'message': f"Current rent is {analysis.get('below_market_pct', 0)}% below market. Potential increase: ${analysis.get('potential_increase', 0)}/month",
                'urgency': 'medium',
                'priority_score': 5,
                'property_id': analysis.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': (datetime.now() + timedelta(days=30)).isoformat(),
                'tags': ['revenue', 'rent', 'optimization'],
                'estimated_response_time': '1 week',
                'escalation_required': False
            })
    
    # Lease renewal opportunities
    renewal_predictions = tenant_data.get('renewal_predictions', [])
    for prediction in renewal_predictions:
        if prediction.get('renewal_probability', 1.0) < 0.6:  # Low renewal probability
            notifications.append({
                'id': f"renewal_risk_{prediction.get('tenant_id')}",
                'type': 'renewal_risk',
                'title': f"Lease Renewal Risk: {prediction.get('tenant_name', 'Unknown tenant')}",
                'message': f"Low renewal probability ({prediction.get('renewal_probability', 0):.1%}). Consider retention strategies.",
                'urgency': 'medium',
                'priority_score': 6,
                'tenant_id': prediction.get('tenant_id'),
                'property_id': prediction.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': (datetime.now() + timedelta(days=21)).isoformat(),
                'tags': ['lease', 'renewal', 'retention'],
                'estimated_response_time': '3 days',
                'escalation_required': False
            })
    
    return notifications

def generate_routine_notifications(tenant_data: Dict, property_data: Dict, financial_data: Dict) -> List[Dict]:
    """
    Generate routine operational notifications
    """
    notifications = []
    
    # Regular maintenance reminders (using property_data for now since maintenance_data not passed)
    scheduled_maintenance = property_data.get('scheduled_maintenance', [])
    for maintenance in scheduled_maintenance:
        scheduled_date = datetime.fromisoformat(maintenance.get('scheduled_date', '2024-12-31'))
        days_until = (scheduled_date - datetime.now()).days
        
        if 0 <= days_until <= 7:
            notifications.append({
                'id': f"scheduled_maintenance_{maintenance.get('id')}",
                'type': 'scheduled_maintenance',
                'title': f"Upcoming Maintenance: {maintenance.get('description', 'Unknown maintenance')}",
                'message': f"Scheduled maintenance in {days_until} days at {maintenance.get('property_address', 'Unknown location')}",
                'urgency': 'low',
                'priority_score': 4,
                'property_id': maintenance.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': scheduled_date.isoformat(),
                'tags': ['maintenance', 'scheduled', 'routine'],
                'estimated_response_time': '24 hours',
                'escalation_required': False
            })
    
    # Monthly financial reports
    current_date = datetime.now()
    if current_date.day <= 5:  # First 5 days of month
        notifications.append({
            'id': f"monthly_report_{current_date.strftime('%Y_%m')}",
            'type': 'monthly_report',
            'title': "Monthly Financial Report Available",
            'message': f"Monthly financial report for {current_date.strftime('%B %Y')} is ready for review",
            'urgency': 'low',
            'priority_score': 3,
            'created_time': datetime.now().isoformat(),
            'deadline': (datetime.now() + timedelta(days=10)).isoformat(),
            'tags': ['finance', 'report', 'monthly'],
            'estimated_response_time': '1 week',
            'escalation_required': False
        })
    
    # Routine inspections
    inspection_schedule = property_data.get('inspection_schedule', [])
    for inspection in inspection_schedule:
        inspection_date = datetime.fromisoformat(inspection.get('scheduled_date', '2024-12-31'))
        days_until = (inspection_date - datetime.now()).days
        
        if 0 <= days_until <= 14:
            notifications.append({
                'id': f"routine_inspection_{inspection.get('id')}",
                'type': 'routine_inspection',
                'title': f"Routine Inspection Due: {inspection.get('property_address', 'Unknown property')}",
                'message': f"Routine inspection scheduled in {days_until} days",
                'urgency': 'low',
                'priority_score': 3,
                'property_id': inspection.get('property_id'),
                'created_time': datetime.now().isoformat(),
                'deadline': inspection_date.isoformat(),
                'tags': ['inspection', 'routine', 'property'],
                'estimated_response_time': '48 hours',
                'escalation_required': False
            })
    
    return notifications

def prioritize_notifications(notifications: List[Dict], tenant_data: Dict, property_data: Dict) -> List[Dict]:
    """
    Prioritize notifications using ML-based scoring
    """
    for notification in notifications:
        # Base priority score
        base_score = notification.get('priority_score', 5)
        
        # Adjust based on tenant history
        tenant_id = notification.get('tenant_id')
        if tenant_id:
            tenant_history = get_tenant_history(tenant_id, tenant_data)
            
            # High-value tenants get priority
            if tenant_history.get('tenant_value', 'medium') == 'high':
                base_score += 1
            
            # Frequent complainers get lower priority for non-urgent issues
            if (notification.get('urgency') != 'urgent' and 
                tenant_history.get('complaint_frequency', 'low') == 'high'):
                base_score -= 0.5
        
        # Adjust based on property portfolio value
        property_id = notification.get('property_id')
        if property_id:
            property_value = get_property_value(property_id, property_data)
            if property_value == 'high':
                base_score += 0.5
        
        # Time-based urgency multiplier
        deadline = notification.get('deadline')
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline)
            hours_until_deadline = (deadline_dt - datetime.now()).total_seconds() / 3600
            
            if hours_until_deadline < 4:
                base_score += 2
            elif hours_until_deadline < 24:
                base_score += 1
        
        # Business hours consideration
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            if notification.get('type') in ['maintenance', 'tenant_satisfaction']:
                base_score += 0.5
        else:  # After hours
            if notification.get('urgency') == 'urgent':
                base_score += 1
        
        notification['adjusted_priority_score'] = round(base_score, 1)
    
    # Sort by adjusted priority score (descending)
    return sorted(notifications, key=lambda x: x.get('adjusted_priority_score', 0), reverse=True)

def generate_routing_recommendations(notifications: List[Dict]) -> Dict:
    """
    Generate intelligent routing recommendations for notifications
    """
    routing_rules = {
        'emergency_maintenance': {
            'primary_recipient': 'maintenance_supervisor',
            'cc_recipients': ['property_manager', 'emergency_contact'],
            'escalation_time': '2 hours',
            'communication_method': ['phone', 'sms', 'email']
        },
        'late_payment': {
            'primary_recipient': 'collections_specialist',
            'cc_recipients': ['property_manager'],
            'escalation_time': '24 hours',
            'communication_method': ['email', 'phone']
        },
        'security_incident': {
            'primary_recipient': 'security_manager',
            'cc_recipients': ['property_manager', 'legal_team'],
            'escalation_time': '4 hours',
            'communication_method': ['phone', 'email']
        },
        'lease_expiration': {
            'primary_recipient': 'leasing_specialist',
            'cc_recipients': ['property_manager'],
            'escalation_time': '48 hours',
            'communication_method': ['email', 'phone']
        },
        'predictive_maintenance': {
            'primary_recipient': 'maintenance_coordinator',
            'cc_recipients': ['property_manager'],
            'escalation_time': '72 hours',
            'communication_method': ['email']
        },
        'tenant_satisfaction': {
            'primary_recipient': 'property_manager',
            'cc_recipients': ['customer_service'],
            'escalation_time': '48 hours',
            'communication_method': ['email', 'phone']
        }
    }
    
    # Generate specific routing for top priority notifications
    high_priority_routing = []
    for notification in notifications[:10]:  # Top 10 notifications
        notification_type = notification.get('type')
        routing_rule = routing_rules.get(notification_type, {
            'primary_recipient': 'property_manager',
            'cc_recipients': [],
            'escalation_time': '24 hours',
            'communication_method': ['email']
        })
        
        high_priority_routing.append({
            'notification_id': notification['id'],
            'routing_rule': routing_rule,
            'send_immediately': notification.get('urgency') == 'urgent',
            'follow_up_required': notification.get('escalation_required', False)
        })
    
    return {
        'routing_rules': routing_rules,
        'high_priority_routing': high_priority_routing,
        'auto_escalation_enabled': True,
        'business_hours_routing': True
    }

def create_notification_schedule(notifications: List[Dict]) -> Dict:
    """
    Create an intelligent notification delivery schedule
    """
    immediate_notifications = [n for n in notifications if n.get('urgency') == 'urgent']
    
    scheduled_notifications = []
    for notification in notifications:
        if notification.get('urgency') != 'urgent':
            # Schedule non-urgent notifications for optimal times
            optimal_time = calculate_optimal_delivery_time(notification)
            scheduled_notifications.append({
                'notification_id': notification['id'],
                'scheduled_time': optimal_time,
                'delivery_method': determine_delivery_method(notification),
                'follow_up_schedule': generate_follow_up_schedule(notification)
            })
    
    return {
        'immediate_count': len(immediate_notifications),
        'scheduled_count': len(scheduled_notifications),
        'next_batch_time': (datetime.now() + timedelta(hours=2)).isoformat(),
        'scheduled_notifications': scheduled_notifications[:20],
        'delivery_optimization': 'enabled'
    }

def analyze_notification_patterns(notifications: List[Dict], tenant_data: Dict) -> Dict:
    """
    Analyze notification patterns for insights
    """
    # Notification type distribution
    type_counts = {}
    for notification in notifications:
        notification_type = notification.get('type', 'unknown')
        type_counts[notification_type] = type_counts.get(notification_type, 0) + 1
    
    # Urgency distribution
    urgency_counts = {}
    for notification in notifications:
        urgency = notification.get('urgency', 'unknown')
        urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
    
    # Property-specific patterns
    property_notification_counts = {}
    for notification in notifications:
        property_id = notification.get('property_id', 'unknown')
        if property_id != 'unknown':
            property_notification_counts[property_id] = property_notification_counts.get(property_id, 0) + 1
    
    # Tenant-specific patterns
    tenant_notification_counts = {}
    for notification in notifications:
        tenant_id = notification.get('tenant_id')
        if tenant_id:
            tenant_notification_counts[tenant_id] = tenant_notification_counts.get(tenant_id, 0) + 1
    
    return {
        'total_notifications': len(notifications),
        'type_distribution': type_counts,
        'urgency_distribution': urgency_counts,
        'properties_with_notifications': len(property_notification_counts),
        'tenants_with_notifications': len(tenant_notification_counts),
        'top_notification_types': sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        'notification_trends': analyze_notification_trends(notifications),
        'efficiency_metrics': calculate_efficiency_metrics(notifications)
    }

def generate_ai_insights(notifications: List[Dict], tenant_data: Dict, property_data: Dict) -> List[Dict]:
    """
    Generate AI-powered insights from notification patterns
    """
    insights = []
    
    # Pattern analysis
    urgent_notifications = [n for n in notifications if n.get('urgency') == 'urgent']
    if len(urgent_notifications) > 5:
        insights.append({
            'type': 'pattern_alert',
            'insight': 'High volume of urgent notifications detected',
            'recommendation': 'Review operational processes to identify preventive measures',
            'impact': 'operational_efficiency',
            'confidence': 0.8
        })
    
    # Maintenance patterns
    maintenance_notifications = [n for n in notifications if 'maintenance' in n.get('type', '')]
    if len(maintenance_notifications) > len(notifications) * 0.4:
        insights.append({
            'type': 'maintenance_insight',
            'insight': 'Maintenance notifications comprise majority of alerts',
            'recommendation': 'Implement preventive maintenance program to reduce reactive issues',
            'impact': 'cost_reduction',
            'confidence': 0.7
        })
    
    # Tenant satisfaction patterns
    satisfaction_notifications = [n for n in notifications if n.get('type') == 'tenant_satisfaction']
    if satisfaction_notifications:
        insights.append({
            'type': 'tenant_insight',
            'insight': f'Tenant satisfaction issues detected across {len(satisfaction_notifications)} tenants',
            'recommendation': 'Conduct tenant satisfaction survey and implement improvement plan',
            'impact': 'tenant_retention',
            'confidence': 0.9
        })
    
    # Revenue optimization opportunities
    rent_notifications = [n for n in notifications if n.get('type') == 'rent_optimization']
    if rent_notifications:
        total_potential = sum(float(n.get('message', '0').split('$')[-1].split('/')[0]) if '$' in n.get('message', '') else 0 for n in rent_notifications)
        insights.append({
            'type': 'revenue_insight',
            'insight': f'Revenue optimization opportunities identified worth ${total_potential:.0f}/month',
            'recommendation': 'Prioritize rent analysis and implement strategic increases',
            'impact': 'revenue_growth',
            'confidence': 0.8
        })
    
    return insights

# Helper functions
def get_tenant_history(tenant_id: str, tenant_data: Dict) -> Dict:
    """Get tenant history for priority scoring"""
    tenants = tenant_data.get('tenants', [])
    for tenant in tenants:
        if tenant.get('id') == tenant_id:
            return {
                'tenant_value': tenant.get('value_tier', 'medium'),
                'complaint_frequency': tenant.get('complaint_frequency', 'low'),
                'payment_reliability': tenant.get('payment_reliability', 'good')
            }
    return {'tenant_value': 'medium', 'complaint_frequency': 'low', 'payment_reliability': 'good'}

def get_property_value(property_id: str, property_data: Dict) -> str:
    """Get property value tier for priority scoring"""
    properties = property_data.get('properties', [])
    for prop in properties:
        if prop.get('id') == property_id:
            return prop.get('value_tier', 'medium')
    return 'medium'

def calculate_optimal_delivery_time(notification: Dict) -> str:
    """Calculate optimal delivery time for notification"""
    notification_type = notification.get('type')
    urgency = notification.get('urgency')
    
    current_time = datetime.now()
    
    if urgency == 'urgent':
        return current_time.isoformat()
    elif urgency == 'high':
        # Schedule for next business hour
        if current_time.hour < 9:
            optimal_time = current_time.replace(hour=9, minute=0, second=0)
        elif current_time.hour >= 17:
            optimal_time = (current_time + timedelta(days=1)).replace(hour=9, minute=0, second=0)
        else:
            optimal_time = current_time + timedelta(hours=1)
    else:
        # Schedule for next business day morning
        if current_time.hour >= 17:
            optimal_time = (current_time + timedelta(days=1)).replace(hour=9, minute=0, second=0)
        else:
            optimal_time = current_time.replace(hour=9, minute=0, second=0) + timedelta(days=1)
    
    return optimal_time.isoformat()

def determine_delivery_method(notification: Dict) -> List[str]:
    """Determine optimal delivery method for notification"""
    urgency = notification.get('urgency')
    notification_type = notification.get('type')
    
    if urgency == 'urgent':
        return ['sms', 'phone', 'email', 'push']
    elif urgency == 'high':
        return ['phone', 'email', 'push']
    elif notification_type in ['scheduled_maintenance', 'routine_inspection']:
        return ['email']
    else:
        return ['email', 'push']

def generate_follow_up_schedule(notification: Dict) -> List[Dict]:
    """Generate follow-up schedule for notification"""
    urgency = notification.get('urgency')
    
    if urgency == 'urgent':
        return [
            {'time': (datetime.now() + timedelta(hours=2)).isoformat(), 'action': 'escalate_if_no_response'},
            {'time': (datetime.now() + timedelta(hours=4)).isoformat(), 'action': 'emergency_escalation'}
        ]
    elif urgency == 'high':
        return [
            {'time': (datetime.now() + timedelta(hours=24)).isoformat(), 'action': 'follow_up_reminder'},
            {'time': (datetime.now() + timedelta(hours=48)).isoformat(), 'action': 'escalate_to_manager'}
        ]
    else:
        return [
            {'time': (datetime.now() + timedelta(days=3)).isoformat(), 'action': 'status_check'}
        ]

def analyze_notification_trends(notifications: List[Dict]) -> Dict:
    """Analyze trends in notifications"""
    current_hour = datetime.now().hour
    
    return {
        'peak_notification_time': f"{current_hour}:00",
        'average_priority_score': round(np.mean([n.get('priority_score', 5) for n in notifications]), 1),
        'escalation_rate': len([n for n in notifications if n.get('escalation_required', False)]) / len(notifications) if notifications else 0,
        'urgent_percentage': len([n for n in notifications if n.get('urgency') == 'urgent']) / len(notifications) * 100 if notifications else 0
    }

def calculate_efficiency_metrics(notifications: List[Dict]) -> Dict:
    """Calculate notification system efficiency metrics"""
    return {
        'notifications_per_property': len(notifications) / 10,  # Assuming 10 properties
        'urgent_to_total_ratio': len([n for n in notifications if n.get('urgency') == 'urgent']) / len(notifications) if notifications else 0,
        'average_response_time_hours': 4,  # Would be calculated from historical data
        'escalation_prevention_rate': 0.85  # Would be calculated from historical data
    }