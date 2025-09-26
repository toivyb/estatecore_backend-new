"""
Maintenance Notification Service
Comprehensive notification system for maintenance request lifecycle events
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of maintenance notifications"""
    REQUEST_CREATED = "request_created"
    REQUEST_ASSIGNED = "request_assigned"
    STATUS_UPDATED = "status_updated"
    COMMENT_ADDED = "comment_added"
    PHOTO_UPLOADED = "photo_uploaded"
    REQUEST_ESCALATED = "request_escalated"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_OVERDUE = "request_overdue"
    VENDOR_ASSIGNED = "vendor_assigned"
    INSPECTION_SCHEDULED = "inspection_scheduled"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    SLACK = "slack"
    WEBHOOK = "webhook"

class RecipientType(Enum):
    """Types of notification recipients"""
    TENANT = "tenant"
    PROPERTY_MANAGER = "property_manager"
    MAINTENANCE_STAFF = "maintenance_staff"
    VENDOR = "vendor"
    ADMIN = "admin"

@dataclass
class NotificationRecipient:
    """Notification recipient information"""
    user_id: int
    email: str
    phone: Optional[str] = None
    name: str = ""
    role: str = ""
    preferences: Dict = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {
                'email': True,
                'sms': True,
                'push': True,
                'in_app': True
            }

@dataclass
class MaintenanceNotification:
    """Maintenance notification data"""
    id: str
    notification_type: NotificationType
    maintenance_request_id: str
    title: str
    message: str
    recipients: List[NotificationRecipient]
    channels: List[NotificationChannel]
    priority: str = "medium"
    data: Dict = None
    scheduled_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class MaintenanceNotificationService:
    """Comprehensive notification service for maintenance requests"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': os.environ.get('SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
            'smtp_username': os.environ.get('SMTP_USERNAME', ''),
            'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
            'from_email': os.environ.get('FROM_EMAIL', 'noreply@estatecore.com'),
            'from_name': os.environ.get('FROM_NAME', 'EstateCore Maintenance')
        }
        
        self.sms_config = {
            'twilio_sid': os.environ.get('TWILIO_SID', ''),
            'twilio_token': os.environ.get('TWILIO_TOKEN', ''),
            'twilio_phone': os.environ.get('TWILIO_PHONE', '')
        }
        
        self.slack_config = {
            'webhook_url': os.environ.get('SLACK_WEBHOOK_URL', ''),
            'channel': os.environ.get('SLACK_CHANNEL', '#maintenance')
        }
        
        # Notification templates
        self.email_templates = self._load_email_templates()
        self.sms_templates = self._load_sms_templates()
        
    def _load_email_templates(self) -> Dict:
        """Load email notification templates"""
        return {
            NotificationType.REQUEST_CREATED: {
                'subject': 'New Maintenance Request #{request_id}',
                'template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #333; margin-bottom: 20px;">New Maintenance Request</h2>
                        
                        <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h3 style="color: #2563eb; margin-top: 0;">Request Details</h3>
                            <p><strong>Request ID:</strong> #{request_id}</p>
                            <p><strong>Title:</strong> {title}</p>
                            <p><strong>Category:</strong> {category}</p>
                            <p><strong>Priority:</strong> <span style="color: {priority_color};">{priority}</span></p>
                            <p><strong>Property:</strong> {property_name}</p>
                            <p><strong>Unit:</strong> {unit_number}</p>
                            <p><strong>Submitted by:</strong> {tenant_name}</p>
                            <p><strong>Description:</strong></p>
                            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 3px;">{description}</p>
                        </div>
                        
                        {photo_section}
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{view_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">View Request</a>
                        </div>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;">
                            <p>This is an automated notification from EstateCore Maintenance System.</p>
                        </div>
                    </div>
                </div>
                '''
            },
            
            NotificationType.REQUEST_ASSIGNED: {
                'subject': 'Maintenance Request #{request_id} Assigned to You',
                'template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #333; margin-bottom: 20px;">Maintenance Request Assigned</h2>
                        
                        <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <h3 style="color: #059669; margin-top: 0;">Assignment Details</h3>
                            <p><strong>Request ID:</strong> #{request_id}</p>
                            <p><strong>Title:</strong> {title}</p>
                            <p><strong>Priority:</strong> <span style="color: {priority_color};">{priority}</span></p>
                            <p><strong>Assigned by:</strong> {assigned_by}</p>
                            <p><strong>Due Date:</strong> {due_date}</p>
                            
                            {assignment_notes}
                        </div>
                        
                        <div style="background-color: #fef3c7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                            <p style="margin: 0; color: #92400e;"><strong>Next Steps:</strong></p>
                            <ul style="margin: 10px 0 0 20px; color: #92400e;">
                                <li>Review the request details</li>
                                <li>Contact the tenant if needed</li>
                                <li>Update the status when work begins</li>
                                <li>Upload progress photos</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{view_url}" style="background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">View Assignment</a>
                        </div>
                    </div>
                </div>
                '''
            },
            
            NotificationType.STATUS_UPDATED: {
                'subject': 'Maintenance Request #{request_id} Status Updated',
                'template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #333; margin-bottom: 20px;">Status Update</h2>
                        
                        <div style="background-color: white; padding: 20px; border-radius: 5px;">
                            <p><strong>Request ID:</strong> #{request_id}</p>
                            <p><strong>Title:</strong> {title}</p>
                            <p><strong>Status changed from:</strong> <span style="color: #6b7280;">{old_status}</span></p>
                            <p><strong>To:</strong> <span style="color: {status_color};">{new_status}</span></p>
                            <p><strong>Updated by:</strong> {updated_by}</p>
                            <p><strong>Date:</strong> {update_date}</p>
                            
                            {update_notes}
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{view_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">View Request</a>
                        </div>
                    </div>
                </div>
                '''
            },
            
            NotificationType.REQUEST_COMPLETED: {
                'subject': 'Maintenance Request #{request_id} Completed',
                'template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #059669; margin-bottom: 20px;">✅ Maintenance Request Completed</h2>
                        
                        <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <p><strong>Request ID:</strong> #{request_id}</p>
                            <p><strong>Title:</strong> {title}</p>
                            <p><strong>Completed by:</strong> {completed_by}</p>
                            <p><strong>Completion Date:</strong> {completion_date}</p>
                            <p><strong>Total Time:</strong> {total_time}</p>
                            
                            {completion_notes}
                        </div>
                        
                        <div style="background-color: #ecfdf5; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                            <p style="margin: 0; color: #059669;"><strong>Thank you for your patience!</strong></p>
                            <p style="margin: 10px 0 0 0; color: #047857;">If you have any concerns about the work performed, please don't hesitate to contact us.</p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{view_url}" style="background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin-right: 10px;">View Details</a>
                            <a href="{feedback_url}" style="background-color: #6b7280; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Leave Feedback</a>
                        </div>
                    </div>
                </div>
                '''
            },
            
            NotificationType.REQUEST_OVERDUE: {
                'subject': '⚠️ OVERDUE: Maintenance Request #{request_id}',
                'template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; border-left: 4px solid #dc2626;">
                        <h2 style="color: #dc2626; margin-bottom: 20px;">⚠️ Overdue Maintenance Request</h2>
                        
                        <div style="background-color: white; padding: 20px; border-radius: 5px;">
                            <p><strong>Request ID:</strong> #{request_id}</p>
                            <p><strong>Title:</strong> {title}</p>
                            <p><strong>Priority:</strong> <span style="color: {priority_color};">{priority}</span></p>
                            <p><strong>Days Overdue:</strong> <span style="color: #dc2626; font-weight: bold;">{days_overdue}</span></p>
                            <p><strong>Assigned to:</strong> {assigned_to}</p>
                            <p><strong>Original Due Date:</strong> {due_date}</p>
                        </div>
                        
                        <div style="background-color: #fee2e2; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0; color: #991b1b;"><strong>Action Required:</strong></p>
                            <p style="margin: 10px 0 0 0; color: #991b1b;">This request requires immediate attention. Please review and take appropriate action.</p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{view_url}" style="background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Take Action</a>
                        </div>
                    </div>
                </div>
                '''
            }
        }
    
    def _load_sms_templates(self) -> Dict:
        """Load SMS notification templates"""
        return {
            NotificationType.REQUEST_CREATED: "New maintenance request #{request_id}: {title}. Priority: {priority}. View: {view_url}",
            NotificationType.REQUEST_ASSIGNED: "Maintenance request #{request_id} assigned to you. Priority: {priority}. View: {view_url}",
            NotificationType.STATUS_UPDATED: "Request #{request_id} status: {old_status} → {new_status}. View: {view_url}",
            NotificationType.REQUEST_COMPLETED: "✅ Request #{request_id} completed! View details: {view_url}",
            NotificationType.REQUEST_OVERDUE: "⚠️ OVERDUE: Request #{request_id} is {days_overdue} days overdue. Take action: {view_url}"
        }
    
    def send_notification(self, notification: MaintenanceNotification) -> Dict:
        """Send notification through specified channels"""
        results = {}
        
        for channel in notification.channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    results[channel.value] = self._send_email_notification(notification)
                elif channel == NotificationChannel.SMS:
                    results[channel.value] = self._send_sms_notification(notification)
                elif channel == NotificationChannel.SLACK:
                    results[channel.value] = self._send_slack_notification(notification)
                elif channel == NotificationChannel.WEBHOOK:
                    results[channel.value] = self._send_webhook_notification(notification)
                elif channel == NotificationChannel.IN_APP:
                    results[channel.value] = self._create_in_app_notification(notification)
                else:
                    results[channel.value] = {'success': False, 'error': 'Channel not implemented'}
                    
            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {str(e)}")
                results[channel.value] = {'success': False, 'error': str(e)}
        
        return results
    
    def _send_email_notification(self, notification: MaintenanceNotification) -> Dict:
        """Send email notification"""
        try:
            template = self.email_templates.get(notification.notification_type)
            if not template:
                return {'success': False, 'error': 'Template not found'}
            
            # Format template with notification data
            subject = template['subject'].format(**notification.data)
            html_body = template['template'].format(**notification.data)
            
            # Send to all recipients
            sent_count = 0
            errors = []
            
            for recipient in notification.recipients:
                if not recipient.preferences.get('email', True):
                    continue
                
                try:
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = f"{self.email_config['from_name']} <{self.email_config['from_email']}>"
                    msg['To'] = recipient.email
                    
                    # Attach HTML body
                    html_part = MIMEText(html_body, 'html')
                    msg.attach(html_part)
                    
                    # Send email
                    with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                        server.starttls()
                        if self.email_config['smtp_username']:
                            server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                        server.send_message(msg)
                    
                    sent_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to send to {recipient.email}: {str(e)}")
            
            return {
                'success': True,
                'sent_count': sent_count,
                'total_recipients': len(notification.recipients),
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_sms_notification(self, notification: MaintenanceNotification) -> Dict:
        """Send SMS notification using Twilio"""
        try:
            if not self.sms_config['twilio_sid']:
                return {'success': False, 'error': 'SMS not configured'}
            
            template = self.sms_templates.get(notification.notification_type)
            if not template:
                return {'success': False, 'error': 'SMS template not found'}
            
            message = template.format(**notification.data)
            
            # Import Twilio client
            from twilio.rest import Client
            client = Client(self.sms_config['twilio_sid'], self.sms_config['twilio_token'])
            
            sent_count = 0
            errors = []
            
            for recipient in notification.recipients:
                if not recipient.preferences.get('sms', True) or not recipient.phone:
                    continue
                
                try:
                    message_obj = client.messages.create(
                        body=message,
                        from_=self.sms_config['twilio_phone'],
                        to=recipient.phone
                    )
                    sent_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to send to {recipient.phone}: {str(e)}")
            
            return {
                'success': True,
                'sent_count': sent_count,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_slack_notification(self, notification: MaintenanceNotification) -> Dict:
        """Send Slack notification"""
        try:
            if not self.slack_config['webhook_url']:
                return {'success': False, 'error': 'Slack not configured'}
            
            # Create Slack message
            priority_colors = {
                'low': '#36a64f',
                'medium': '#ff9500',
                'high': '#ff6b6b',
                'emergency': '#ff0000'
            }
            
            priority = notification.data.get('priority', 'medium')
            color = priority_colors.get(priority, '#36a64f')
            
            slack_message = {
                'channel': self.slack_config['channel'],
                'username': 'EstateCore Maintenance',
                'icon_emoji': ':wrench:',
                'attachments': [
                    {
                        'color': color,
                        'title': notification.title,
                        'text': notification.message,
                        'fields': [
                            {
                                'title': 'Request ID',
                                'value': notification.data.get('request_id', 'N/A'),
                                'short': True
                            },
                            {
                                'title': 'Priority',
                                'value': priority.title(),
                                'short': True
                            }
                        ],
                        'actions': [
                            {
                                'type': 'button',
                                'text': 'View Request',
                                'url': notification.data.get('view_url', '#')
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.slack_config['webhook_url'],
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True}
            else:
                return {'success': False, 'error': f'Slack API error: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_webhook_notification(self, notification: MaintenanceNotification) -> Dict:
        """Send webhook notification"""
        try:
            webhook_url = notification.data.get('webhook_url')
            if not webhook_url:
                return {'success': False, 'error': 'No webhook URL provided'}
            
            payload = {
                'event': notification.notification_type.value,
                'request_id': notification.maintenance_request_id,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'timestamp': notification.created_at.isoformat(),
                'data': notification.data
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201, 202]:
                return {'success': True, 'status_code': response.status_code}
            else:
                return {'success': False, 'error': f'Webhook error: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_in_app_notification(self, notification: MaintenanceNotification) -> Dict:
        """Create in-app notification (store in database)"""
        try:
            # This would integrate with your database to store in-app notifications
            # For now, we'll return a success response
            return {
                'success': True,
                'stored_for': len(notification.recipients),
                'notification_id': notification.id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_request_notification(
        self,
        notification_type: NotificationType,
        maintenance_request: Dict,
        recipients: List[NotificationRecipient],
        channels: List[NotificationChannel] = None,
        additional_data: Dict = None
    ) -> MaintenanceNotification:
        """Create a maintenance request notification"""
        
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        
        if additional_data is None:
            additional_data = {}
        
        # Prepare notification data
        data = {
            'request_id': maintenance_request.get('id', 'N/A'),
            'title': maintenance_request.get('title', 'Maintenance Request'),
            'description': maintenance_request.get('description', ''),
            'category': maintenance_request.get('category', 'General'),
            'priority': maintenance_request.get('priority', 'medium'),
            'status': maintenance_request.get('status', 'pending'),
            'property_name': maintenance_request.get('property_name', 'Property'),
            'unit_number': maintenance_request.get('unit_number', 'N/A'),
            'tenant_name': maintenance_request.get('tenant_name', 'Tenant'),
            'view_url': f"{os.environ.get('BASE_URL', 'https://app.estatecore.com')}/maintenance/{maintenance_request.get('id')}",
            **additional_data
        }
        
        # Add priority color
        priority_colors = {
            'low': '#6b7280',
            'medium': '#f59e0b',
            'high': '#ef4444',
            'emergency': '#dc2626'
        }
        data['priority_color'] = priority_colors.get(data['priority'], '#6b7280')
        
        # Generate notification title and message
        titles = {
            NotificationType.REQUEST_CREATED: f"New Maintenance Request: {data['title']}",
            NotificationType.REQUEST_ASSIGNED: f"Maintenance Request Assigned: {data['title']}",
            NotificationType.STATUS_UPDATED: f"Status Update: {data['title']}",
            NotificationType.REQUEST_COMPLETED: f"Request Completed: {data['title']}",
            NotificationType.REQUEST_OVERDUE: f"Overdue Request: {data['title']}"
        }
        
        messages = {
            NotificationType.REQUEST_CREATED: f"A new {data['priority']} priority maintenance request has been submitted for {data['property_name']}.",
            NotificationType.REQUEST_ASSIGNED: f"You have been assigned a {data['priority']} priority maintenance request.",
            NotificationType.STATUS_UPDATED: f"The status of maintenance request #{data['request_id']} has been updated.",
            NotificationType.REQUEST_COMPLETED: f"Maintenance request #{data['request_id']} has been completed.",
            NotificationType.REQUEST_OVERDUE: f"Maintenance request #{data['request_id']} is overdue and requires immediate attention."
        }
        
        return MaintenanceNotification(
            id=str(uuid.uuid4()),
            notification_type=notification_type,
            maintenance_request_id=data['request_id'],
            title=titles.get(notification_type, "Maintenance Notification"),
            message=messages.get(notification_type, "Maintenance request update"),
            recipients=recipients,
            channels=channels,
            priority=data['priority'],
            data=data
        )

# Service instance
_notification_service = None

def get_maintenance_notification_service() -> MaintenanceNotificationService:
    """Get maintenance notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = MaintenanceNotificationService()
    return _notification_service

# Convenience functions for common notifications

def notify_request_created(maintenance_request: Dict, recipients: List[NotificationRecipient]):
    """Send notification for new maintenance request"""
    service = get_maintenance_notification_service()
    notification = service.create_request_notification(
        NotificationType.REQUEST_CREATED,
        maintenance_request,
        recipients
    )
    return service.send_notification(notification)

def notify_request_assigned(maintenance_request: Dict, assignee: NotificationRecipient, assigned_by: str):
    """Send notification for request assignment"""
    service = get_maintenance_notification_service()
    notification = service.create_request_notification(
        NotificationType.REQUEST_ASSIGNED,
        maintenance_request,
        [assignee],
        additional_data={'assigned_by': assigned_by}
    )
    return service.send_notification(notification)

def notify_status_updated(maintenance_request: Dict, recipients: List[NotificationRecipient], old_status: str, updated_by: str):
    """Send notification for status update"""
    service = get_maintenance_notification_service()
    notification = service.create_request_notification(
        NotificationType.STATUS_UPDATED,
        maintenance_request,
        recipients,
        additional_data={
            'old_status': old_status,
            'new_status': maintenance_request.get('status'),
            'updated_by': updated_by,
            'update_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
    )
    return service.send_notification(notification)

def notify_request_completed(maintenance_request: Dict, recipients: List[NotificationRecipient], completed_by: str):
    """Send notification for request completion"""
    service = get_maintenance_notification_service()
    
    # Calculate total time
    created_at = datetime.fromisoformat(maintenance_request.get('created_at', ''))
    completed_at = datetime.fromisoformat(maintenance_request.get('completed_at', ''))
    total_time = str(completed_at - created_at)
    
    notification = service.create_request_notification(
        NotificationType.REQUEST_COMPLETED,
        maintenance_request,
        recipients,
        additional_data={
            'completed_by': completed_by,
            'completion_date': completed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'total_time': total_time,
            'feedback_url': f"{os.environ.get('BASE_URL', 'https://app.estatecore.com')}/feedback/maintenance/{maintenance_request.get('id')}"
        }
    )
    return service.send_notification(notification)

def notify_request_overdue(maintenance_request: Dict, recipients: List[NotificationRecipient], days_overdue: int):
    """Send notification for overdue request"""
    service = get_maintenance_notification_service()
    notification = service.create_request_notification(
        NotificationType.REQUEST_OVERDUE,
        maintenance_request,
        recipients,
        channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK],
        additional_data={'days_overdue': days_overdue}
    )
    return service.send_notification(notification)

if __name__ == "__main__":
    # Test the notification service
    import uuid
    
    # Example usage
    test_request = {
        'id': str(uuid.uuid4()),
        'title': 'Leaky Faucet in Kitchen',
        'description': 'The kitchen faucet has been dripping constantly for the past week.',
        'category': 'plumbing',
        'priority': 'medium',
        'status': 'pending',
        'property_name': 'Sunset Apartments Unit 2B',
        'unit_number': '2B',
        'tenant_name': 'John Doe'
    }
    
    test_recipient = NotificationRecipient(
        user_id=1,
        email='test@example.com',
        phone='+1234567890',
        name='Test Manager',
        role='property_manager'
    )
    
    # Test notification
    result = notify_request_created(test_request, [test_recipient])
    print("Notification result:", result)