"""
Compliance Alert and Notification System
Multi-channel alert delivery with escalation workflows
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy import and_, or_
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
import websockets
from twilio.rest import Client as TwilioClient
from slack_sdk import WebClient as SlackClient
from slack_sdk.errors import SlackApiError

from models.base import db
from models.compliance import (
    ComplianceAlert, ComplianceViolation, ComplianceRequirement,
    ViolationSeverity, AlertChannel, ComplianceStatus
)


logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of compliance alerts"""
    VIOLATION_DETECTED = "violation_detected"
    DEADLINE_WARNING = "deadline_warning"
    OVERDUE_REQUIREMENT = "overdue_requirement"
    HIGH_RISK_PROPERTY = "high_risk_property"
    DOCUMENT_EXPIRATION = "document_expiration"
    TRAINING_REQUIRED = "training_required"
    SYSTEM_ISSUE = "system_issue"
    ESCALATION = "escalation"


@dataclass
class AlertRecipient:
    """Alert recipient information"""
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: Optional[str] = None
    notification_preferences: Dict[str, bool] = None


@dataclass
class AlertTemplate:
    """Alert message template"""
    template_id: str
    alert_type: AlertType
    subject_template: str
    message_template: str
    html_template: Optional[str] = None
    channels: List[AlertChannel] = None


@dataclass
class EscalationRule:
    """Escalation rule configuration"""
    rule_id: str
    alert_type: AlertType
    severity: ViolationSeverity
    initial_delay_hours: int
    escalation_levels: List[Dict[str, Any]]
    max_escalations: int


class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
    
    async def send_notification(
        self, 
        recipient: AlertRecipient, 
        alert: ComplianceAlert, 
        message: str,
        subject: str = None
    ) -> Dict[str, Any]:
        """Send notification through this channel"""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get('smtp_server', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email', 'noreply@estatecore.com')
        self.use_tls = config.get('use_tls', True)
    
    async def send_notification(
        self, 
        recipient: AlertRecipient, 
        alert: ComplianceAlert, 
        message: str,
        subject: str = None
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            if not recipient.email:
                return {'success': False, 'error': 'No email address'}
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject or f"Compliance Alert: {alert.title}"
            msg['From'] = self.from_email
            msg['To'] = recipient.email
            msg['Message-ID'] = f"<{alert.id}@estatecore.com>"
            
            # Add plain text part
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if available
            html_message = self._generate_html_message(alert, message, recipient)
            if html_message:
                html_part = MIMEText(html_message, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipient.email} for alert {alert.id}")
            return {'success': True, 'channel': 'email', 'recipient': recipient.email}
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return {'success': False, 'error': str(e), 'channel': 'email'}
    
    def _generate_html_message(self, alert: ComplianceAlert, message: str, recipient: AlertRecipient) -> str:
        """Generate HTML email message"""
        severity_colors = {
            ViolationSeverity.CRITICAL: '#dc3545',
            ViolationSeverity.HIGH: '#fd7e14',
            ViolationSeverity.MEDIUM: '#ffc107',
            ViolationSeverity.LOW: '#28a745',
            ViolationSeverity.INFORMATIONAL: '#17a2b8'
        }
        
        color = severity_colors.get(alert.priority, '#6c757d')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
                .content {{ border: 1px solid #ddd; padding: 20px; border-radius: 0 0 5px 5px; }}
                .priority {{ font-weight: bold; color: {color}; }}
                .footer {{ margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>EstateCore Compliance Alert</h2>
            </div>
            <div class="content">
                <p>Dear {recipient.name},</p>
                <p><strong>Alert:</strong> {alert.title}</p>
                <p><strong>Priority:</strong> <span class="priority">{alert.priority.value.upper()}</span></p>
                <p><strong>Message:</strong></p>
                <p>{message.replace(chr(10), '<br>')}</p>
                <p><strong>Time:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div class="footer">
                <p>This is an automated message from EstateCore Compliance Monitoring System.</p>
                <p>Please do not reply to this email. For questions, contact your system administrator.</p>
            </div>
        </body>
        </html>
        """
        return html


class SMSNotificationChannel(NotificationChannel):
    """SMS notification channel using Twilio"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_sid = config.get('twilio_account_sid')
        self.auth_token = config.get('twilio_auth_token')
        self.from_phone = config.get('from_phone')
        self.client = None
        
        if self.account_sid and self.auth_token:
            self.client = TwilioClient(self.account_sid, self.auth_token)
    
    async def send_notification(
        self, 
        recipient: AlertRecipient, 
        alert: ComplianceAlert, 
        message: str,
        subject: str = None
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            if not self.client:
                return {'success': False, 'error': 'SMS client not configured'}
            
            if not recipient.phone:
                return {'success': False, 'error': 'No phone number'}
            
            # Truncate message for SMS (160 character limit)
            sms_message = f"EstateCore Alert: {alert.title}\n{message[:120]}..."
            if len(message) <= 100:
                sms_message = f"EstateCore Alert: {alert.title}\n{message}"
            
            # Send SMS
            message_obj = self.client.messages.create(
                body=sms_message,
                from_=self.from_phone,
                to=recipient.phone
            )
            
            logger.info(f"SMS sent to {recipient.phone} for alert {alert.id}")
            return {
                'success': True, 
                'channel': 'sms', 
                'recipient': recipient.phone,
                'message_sid': message_obj.sid
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return {'success': False, 'error': str(e), 'channel': 'sms'}


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('bot_token')
        self.channel = config.get('default_channel', '#compliance-alerts')
        self.client = None
        
        if self.bot_token:
            self.client = SlackClient(token=self.bot_token)
    
    async def send_notification(
        self, 
        recipient: AlertRecipient, 
        alert: ComplianceAlert, 
        message: str,
        subject: str = None
    ) -> Dict[str, Any]:
        """Send Slack notification"""
        try:
            if not self.client:
                return {'success': False, 'error': 'Slack client not configured'}
            
            # Create Slack message blocks
            blocks = self._create_slack_blocks(alert, message, recipient)
            
            # Send message
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"Compliance Alert: {alert.title}"  # Fallback text
            )
            
            logger.info(f"Slack message sent to {self.channel} for alert {alert.id}")
            return {
                'success': True,
                'channel': 'slack',
                'recipient': self.channel,
                'message_ts': response.get('ts')
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return {'success': False, 'error': str(e), 'channel': 'slack'}
        except Exception as e:
            logger.error(f"Unexpected error sending Slack notification: {e}")
            return {'success': False, 'error': str(e), 'channel': 'slack'}
    
    def _create_slack_blocks(self, alert: ComplianceAlert, message: str, recipient: AlertRecipient) -> List[Dict]:
        """Create Slack message blocks"""
        priority_emojis = {
            ViolationSeverity.CRITICAL: ':rotating_light:',
            ViolationSeverity.HIGH: ':warning:',
            ViolationSeverity.MEDIUM: ':exclamation:',
            ViolationSeverity.LOW: ':information_source:',
            ViolationSeverity.INFORMATIONAL: ':memo:'
        }
        
        emoji = priority_emojis.get(alert.priority, ':bell:')
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Compliance Alert: {alert.title}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:* {alert.priority.value.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:* {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n{message}"
                }
            }
        ]
        
        # Add action buttons if applicable
        if alert.violation_id:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "style": "primary",
                        "url": f"https://app.estatecore.com/compliance/violations/{alert.violation_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Acknowledge"
                        },
                        "action_id": f"ack_alert_{alert.id}"
                    }
                ]
            })
        
        return blocks


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_urls = config.get('webhook_urls', [])
        self.headers = config.get('headers', {})
        self.timeout = config.get('timeout', 30)
    
    async def send_notification(
        self, 
        recipient: AlertRecipient, 
        alert: ComplianceAlert, 
        message: str,
        subject: str = None
    ) -> Dict[str, Any]:
        """Send webhook notification"""
        results = []
        
        try:
            payload = {
                'alert_id': alert.id,
                'alert_type': alert.alert_type,
                'title': alert.title,
                'message': message,
                'priority': alert.priority.value,
                'created_at': alert.created_at.isoformat(),
                'recipient': {
                    'user_id': recipient.user_id,
                    'name': recipient.name,
                    'email': recipient.email
                }
            }
            
            for webhook_url in self.webhook_urls:
                try:
                    response = requests.post(
                        webhook_url,
                        json=payload,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        results.append({
                            'success': True,
                            'url': webhook_url,
                            'status_code': response.status_code
                        })
                        logger.info(f"Webhook sent to {webhook_url} for alert {alert.id}")
                    else:
                        results.append({
                            'success': False,
                            'url': webhook_url,
                            'status_code': response.status_code,
                            'error': response.text
                        })
                        
                except requests.RequestException as e:
                    results.append({
                        'success': False,
                        'url': webhook_url,
                        'error': str(e)
                    })
            
            return {
                'success': any(r['success'] for r in results),
                'channel': 'webhook',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Failed to send webhook notifications: {e}")
            return {'success': False, 'error': str(e), 'channel': 'webhook'}


class ComplianceAlertService:
    """Main service for compliance alerts and notifications"""
    
    def __init__(self):
        self.session = db.session
        self.notification_channels = {}
        self.alert_templates = {}
        self.escalation_rules = {}
        
        # Initialize notification channels
        self._initialize_channels()
        
        # Initialize alert templates
        self._initialize_templates()
        
        # Initialize escalation rules
        self._initialize_escalation_rules()
    
    def _initialize_channels(self):
        """Initialize notification channels"""
        try:
            # Email channel
            email_config = {
                'enabled': True,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': 'alerts@estatecore.com',
                'password': 'your-app-password',
                'from_email': 'alerts@estatecore.com',
                'use_tls': True
            }
            self.notification_channels[AlertChannel.EMAIL] = EmailNotificationChannel(email_config)
            
            # SMS channel
            sms_config = {
                'enabled': True,
                'twilio_account_sid': 'your-twilio-sid',
                'twilio_auth_token': 'your-twilio-token',
                'from_phone': '+1234567890'
            }
            self.notification_channels[AlertChannel.SMS] = SMSNotificationChannel(sms_config)
            
            # Slack channel
            slack_config = {
                'enabled': True,
                'bot_token': 'xoxb-your-bot-token',
                'default_channel': '#compliance-alerts'
            }
            self.notification_channels[AlertChannel.SLACK] = SlackNotificationChannel(slack_config)
            
            # Webhook channel
            webhook_config = {
                'enabled': True,
                'webhook_urls': ['https://api.example.com/compliance-webhooks'],
                'headers': {'Content-Type': 'application/json'}
            }
            self.notification_channels[AlertChannel.WEBHOOK] = WebhookNotificationChannel(webhook_config)
            
            logger.info("Notification channels initialized")
            
        except Exception as e:
            logger.error(f"Error initializing notification channels: {e}")
    
    def _initialize_templates(self):
        """Initialize alert message templates"""
        self.alert_templates = {
            AlertType.VIOLATION_DETECTED: AlertTemplate(
                template_id="violation_detected",
                alert_type=AlertType.VIOLATION_DETECTED,
                subject_template="COMPLIANCE VIOLATION DETECTED: {violation_type}",
                message_template="""
A compliance violation has been detected:

Property: {property_id}
Violation Type: {violation_type}
Severity: {severity}
Description: {description}
Detected: {detected_date}

Immediate action may be required to address this violation.
Please review and take appropriate corrective measures.
                """.strip(),
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.SMS]
            ),
            
            AlertType.DEADLINE_WARNING: AlertTemplate(
                template_id="deadline_warning",
                alert_type=AlertType.DEADLINE_WARNING,
                subject_template="COMPLIANCE DEADLINE WARNING: {requirement_name}",
                message_template="""
A compliance requirement deadline is approaching:

Property: {property_id}
Requirement: {requirement_name}
Due Date: {due_date}
Days Remaining: {days_remaining}

Please ensure compliance before the deadline to avoid violations.
                """.strip(),
                channels=[AlertChannel.EMAIL, AlertChannel.DASHBOARD]
            ),
            
            AlertType.HIGH_RISK_PROPERTY: AlertTemplate(
                template_id="high_risk_property",
                alert_type=AlertType.HIGH_RISK_PROPERTY,
                subject_template="HIGH RISK PROPERTY ALERT: {property_id}",
                message_template="""
A property has been flagged as high risk for compliance violations:

Property: {property_id}
Risk Score: {risk_score}
Risk Level: {risk_level}
Key Risk Factors: {risk_factors}

Recommended Actions: {recommendations}

Please review and implement preventive measures immediately.
                """.strip(),
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            
            AlertType.DOCUMENT_EXPIRATION: AlertTemplate(
                template_id="document_expiration",
                alert_type=AlertType.DOCUMENT_EXPIRATION,
                subject_template="DOCUMENT EXPIRATION ALERT: {document_name}",
                message_template="""
A compliance document is expiring soon:

Property: {property_id}
Document: {document_name}
Expiration Date: {expiration_date}
Days Until Expiration: {days_until_expiration}

Please renew this document before expiration to maintain compliance.
                """.strip(),
                channels=[AlertChannel.EMAIL, AlertChannel.DASHBOARD]
            )
        }
    
    def _initialize_escalation_rules(self):
        """Initialize escalation rules"""
        self.escalation_rules = {
            'critical_violation': EscalationRule(
                rule_id='critical_violation',
                alert_type=AlertType.VIOLATION_DETECTED,
                severity=ViolationSeverity.CRITICAL,
                initial_delay_hours=1,
                escalation_levels=[
                    {'level': 1, 'delay_hours': 2, 'roles': ['property_manager']},
                    {'level': 2, 'delay_hours': 4, 'roles': ['regional_manager']},
                    {'level': 3, 'delay_hours': 8, 'roles': ['compliance_director']}
                ],
                max_escalations=3
            ),
            
            'high_violation': EscalationRule(
                rule_id='high_violation',
                alert_type=AlertType.VIOLATION_DETECTED,
                severity=ViolationSeverity.HIGH,
                initial_delay_hours=4,
                escalation_levels=[
                    {'level': 1, 'delay_hours': 8, 'roles': ['property_manager']},
                    {'level': 2, 'delay_hours': 24, 'roles': ['regional_manager']}
                ],
                max_escalations=2
            ),
            
            'overdue_requirement': EscalationRule(
                rule_id='overdue_requirement',
                alert_type=AlertType.OVERDUE_REQUIREMENT,
                severity=ViolationSeverity.HIGH,
                initial_delay_hours=2,
                escalation_levels=[
                    {'level': 1, 'delay_hours': 12, 'roles': ['property_manager']},
                    {'level': 2, 'delay_hours': 24, 'roles': ['compliance_manager']}
                ],
                max_escalations=2
            )
        }
    
    async def create_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        priority: ViolationSeverity,
        property_id: Optional[str] = None,
        violation_id: Optional[str] = None,
        requirement_id: Optional[str] = None,
        recipient_roles: List[str] = None,
        recipient_users: List[str] = None,
        channels: List[AlertChannel] = None,
        template_data: Dict[str, Any] = None
    ) -> Optional[str]:
        """Create and send a compliance alert"""
        try:
            # Create alert record
            alert = ComplianceAlert(
                alert_type=alert_type.value,
                title=title,
                message=message,
                priority=priority,
                violation_id=violation_id,
                requirement_id=requirement_id,
                recipient_roles=recipient_roles or [],
                recipient_users=recipient_users or [],
                channels=[c.value for c in (channels or [])]
            )
            
            self.session.add(alert)
            self.session.flush()  # Get the ID
            
            # Get recipients
            recipients = await self._get_alert_recipients(
                property_id, recipient_roles, recipient_users
            )
            
            # Use template if available
            if alert_type in self.alert_templates:
                template = self.alert_templates[alert_type]
                formatted_message = self._format_template_message(template, template_data or {})
                formatted_subject = self._format_template_subject(template, template_data or {})
                channels = channels or template.channels
            else:
                formatted_message = message
                formatted_subject = title
            
            # Send notifications
            delivery_results = await self._send_notifications(
                alert, recipients, formatted_message, formatted_subject, channels or []
            )
            
            # Update alert with delivery status
            alert.is_sent = any(r['success'] for r in delivery_results)
            alert.sent_at = datetime.now() if alert.is_sent else None
            alert.delivery_status = delivery_results
            
            self.session.commit()
            
            # Schedule escalation if needed
            await self._schedule_escalation(alert, property_id)
            
            logger.info(f"Created alert {alert.id} with {len(delivery_results)} delivery attempts")
            return alert.id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            self.session.rollback()
            return None
    
    async def _get_alert_recipients(
        self,
        property_id: Optional[str],
        recipient_roles: List[str],
        recipient_users: List[str]
    ) -> List[AlertRecipient]:
        """Get recipients for an alert"""
        recipients = []
        
        try:
            # This would integrate with your user management system
            # For now, return mock recipients
            if 'property_manager' in (recipient_roles or []):
                recipients.append(AlertRecipient(
                    user_id='pm_001',
                    name='Property Manager',
                    email='pm@example.com',
                    phone='+1234567890',
                    role='property_manager'
                ))
            
            if 'compliance_manager' in (recipient_roles or []):
                recipients.append(AlertRecipient(
                    user_id='cm_001',
                    name='Compliance Manager',
                    email='compliance@example.com',
                    phone='+1234567891',
                    role='compliance_manager'
                ))
            
            return recipients
            
        except Exception as e:
            logger.error(f"Error getting alert recipients: {e}")
            return []
    
    def _format_template_message(self, template: AlertTemplate, data: Dict[str, Any]) -> str:
        """Format template message with data"""
        try:
            return template.message_template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing template data key: {e}")
            return template.message_template
        except Exception as e:
            logger.error(f"Error formatting template message: {e}")
            return template.message_template
    
    def _format_template_subject(self, template: AlertTemplate, data: Dict[str, Any]) -> str:
        """Format template subject with data"""
        try:
            return template.subject_template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing template data key: {e}")
            return template.subject_template
        except Exception as e:
            logger.error(f"Error formatting template subject: {e}")
            return template.subject_template
    
    async def _send_notifications(
        self,
        alert: ComplianceAlert,
        recipients: List[AlertRecipient],
        message: str,
        subject: str,
        channels: List[AlertChannel]
    ) -> List[Dict[str, Any]]:
        """Send notifications through multiple channels"""
        delivery_results = []
        
        try:
            # Send to each recipient through each channel
            for recipient in recipients:
                for channel in channels:
                    if channel in self.notification_channels:
                        notification_channel = self.notification_channels[channel]
                        
                        # Check if channel is enabled and recipient allows this channel
                        if (notification_channel.enabled and 
                            self._recipient_allows_channel(recipient, channel)):
                            
                            result = await notification_channel.send_notification(
                                recipient, alert, message, subject
                            )
                            result['recipient_id'] = recipient.user_id
                            delivery_results.append(result)
            
            return delivery_results
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            return [{'success': False, 'error': str(e)}]
    
    def _recipient_allows_channel(self, recipient: AlertRecipient, channel: AlertChannel) -> bool:
        """Check if recipient allows notifications via this channel"""
        if not recipient.notification_preferences:
            return True  # Default to allow all channels
        
        return recipient.notification_preferences.get(channel.value, True)
    
    async def _schedule_escalation(self, alert: ComplianceAlert, property_id: Optional[str]):
        """Schedule escalation for the alert if needed"""
        try:
            # Find matching escalation rule
            escalation_rule = None
            for rule in self.escalation_rules.values():
                if (rule.alert_type.value == alert.alert_type and 
                    rule.severity == alert.priority):
                    escalation_rule = rule
                    break
            
            if escalation_rule:
                # This would integrate with your task scheduler (Celery, etc.)
                logger.info(f"Scheduled escalation for alert {alert.id} using rule {escalation_rule.rule_id}")
                
        except Exception as e:
            logger.error(f"Error scheduling escalation: {e}")
    
    async def acknowledge_alert(self, alert_id: str, user_id: str, notes: str = None) -> bool:
        """Acknowledge an alert"""
        try:
            alert = self.session.query(ComplianceAlert).get(alert_id)
            if not alert:
                logger.error(f"Alert {alert_id} not found")
                return False
            
            alert.acknowledged = True
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.now()
            
            if notes:
                # Add acknowledgment notes (you might want a separate notes table)
                pass
            
            self.session.commit()
            
            logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            self.session.rollback()
            return False
    
    async def get_active_alerts(
        self,
        property_id: Optional[str] = None,
        alert_types: List[AlertType] = None,
        priorities: List[ViolationSeverity] = None,
        unacknowledged_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get active alerts based on filters"""
        try:
            query = self.session.query(ComplianceAlert)
            
            # Apply filters
            if property_id:
                query = query.join(ComplianceViolation).filter(
                    ComplianceViolation.property_id == property_id
                )
            
            if alert_types:
                query = query.filter(
                    ComplianceAlert.alert_type.in_([t.value for t in alert_types])
                )
            
            if priorities:
                query = query.filter(ComplianceAlert.priority.in_(priorities))
            
            if unacknowledged_only:
                query = query.filter(ComplianceAlert.acknowledged == False)
            
            alerts = query.order_by(
                ComplianceAlert.priority.desc(),
                ComplianceAlert.created_at.desc()
            ).all()
            
            return [
                {
                    'id': alert.id,
                    'alert_type': alert.alert_type,
                    'title': alert.title,
                    'message': alert.message,
                    'priority': alert.priority.value,
                    'created_at': alert.created_at,
                    'acknowledged': alert.acknowledged,
                    'acknowledged_by': alert.acknowledged_by,
                    'acknowledged_at': alert.acknowledged_at
                }
                for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def get_alert_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            alerts = self.session.query(ComplianceAlert).filter(
                ComplianceAlert.created_at >= cutoff_date
            ).all()
            
            stats = {
                'total_alerts': len(alerts),
                'by_type': {},
                'by_priority': {},
                'acknowledged_count': 0,
                'average_response_time_hours': 0
            }
            
            response_times = []
            
            for alert in alerts:
                # Count by type
                alert_type = alert.alert_type
                stats['by_type'][alert_type] = stats['by_type'].get(alert_type, 0) + 1
                
                # Count by priority
                priority = alert.priority.value
                stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
                
                # Count acknowledged
                if alert.acknowledged:
                    stats['acknowledged_count'] += 1
                    
                    # Calculate response time
                    if alert.acknowledged_at:
                        response_time = (alert.acknowledged_at - alert.created_at).total_seconds() / 3600
                        response_times.append(response_time)
            
            if response_times:
                stats['average_response_time_hours'] = sum(response_times) / len(response_times)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}


# Global service instance
_compliance_alert_service = None


def get_compliance_alert_service() -> ComplianceAlertService:
    """Get or create the compliance alert service instance"""
    global _compliance_alert_service
    if _compliance_alert_service is None:
        _compliance_alert_service = ComplianceAlertService()
    return _compliance_alert_service