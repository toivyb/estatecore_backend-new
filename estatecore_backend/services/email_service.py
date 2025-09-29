# EstateCore Email Service
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
import os
from datetime import datetime, timedelta
from config.email_config import email_config

logger = logging.getLogger(__name__)

class EmailService:
    """Enterprise email service for EstateCore"""
    
    def __init__(self):
        self.config = email_config
        self.template_env = None
        self.sent_emails_count = {}  # Rate limiting tracker
        
        # Initialize Jinja2 template environment
        if os.path.exists(self.config.TEMPLATE_DIR):
            self.template_env = Environment(
                loader=FileSystemLoader(self.config.TEMPLATE_DIR)
            )
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Clean old entries
        self.sent_emails_count = {
            hour: count for hour, count in self.sent_emails_count.items()
            if hour >= current_hour - timedelta(hours=1)
        }
        
        # Check current hour limit
        current_count = self.sent_emails_count.get(current_hour, 0)
        return current_count < self.config.MAX_EMAILS_PER_HOUR
    
    def _increment_rate_limit(self):
        """Increment rate limit counter"""
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.sent_emails_count[current_hour] = self.sent_emails_count.get(current_hour, 0) + 1
    
    def send_email(self, 
                   to_emails: List[str],
                   subject: str,
                   body_html: str = None,
                   body_text: str = None,
                   attachments: List[Dict[str, Any]] = None,
                   cc_emails: List[str] = None,
                   bcc_emails: List[str] = None,
                   reply_to: str = None) -> bool:
        """
        Send email with HTML and/or text content
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body
            attachments: List of attachment dicts with 'filename', 'content', 'mimetype'
            cc_emails: CC recipients
            bcc_emails: BCC recipients
            reply_to: Reply-to address
            
        Returns:
            bool: True if email sent successfully
        """
        
        if not self.config.is_configured():
            logger.error("Email service not configured properly")
            return False
        
        if not self._check_rate_limit():
            logger.warning("Email rate limit exceeded")
            return False
        
        if len(to_emails) > self.config.MAX_RECIPIENTS_PER_EMAIL:
            logger.warning(f"Too many recipients: {len(to_emails)}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.SENDER_NAME} <{self.config.SENDER_EMAIL}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            msg['Reply-To'] = reply_to or self.config.REPLY_TO_EMAIL
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add text content
            if body_text:
                text_part = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            if body_html:
                html_part = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                if self.config.SMTP_USE_TLS:
                    server.starttls()
                
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                
                # Combine all recipients
                all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
                server.send_message(msg, to_addrs=all_recipients)
            
            self._increment_rate_limit()
            logger.info(f"Email sent successfully to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_template_email(self,
                           to_emails: List[str],
                           template_name: str,
                           subject: str,
                           template_data: Dict[str, Any] = None,
                           **kwargs) -> bool:
        """
        Send email using Jinja2 template
        
        Args:
            to_emails: Recipient email addresses
            template_name: Template file name (without .html extension)
            subject: Email subject
            template_data: Data to pass to template
            **kwargs: Additional arguments for send_email
            
        Returns:
            bool: True if email sent successfully
        """
        
        if not self.template_env:
            logger.error("Email templates not configured")
            return False
        
        try:
            # Load and render template
            template = self.template_env.get_template(f"{template_name}.html")
            body_html = template.render(template_data or {})
            
            # Try to load text version
            body_text = None
            try:
                text_template = self.template_env.get_template(f"{template_name}.txt")
                body_text = text_template.render(template_data or {})
            except:
                # Text template is optional
                pass
            
            return self.send_email(
                to_emails=to_emails,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Failed to send template email: {str(e)}")
            return False
    
    def send_notification_email(self,
                               user_email: str,
                               notification_type: str,
                               data: Dict[str, Any]) -> bool:
        """
        Send notification email based on type
        
        Args:
            user_email: Recipient email
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            bool: True if sent successfully
        """
        
        notification_templates = {
            'tenant_payment_received': {
                'subject': 'Payment Received - EstateCore',
                'template': 'tenant_payment_received'
            },
            'maintenance_request_created': {
                'subject': 'New Maintenance Request - EstateCore',
                'template': 'maintenance_request_created'
            },
            'lease_expiring_soon': {
                'subject': 'Lease Expiring Soon - EstateCore',
                'template': 'lease_expiring_soon'
            },
            'payment_failed': {
                'subject': 'Payment Failed - EstateCore',
                'template': 'payment_failed'
            },
            'welcome_tenant': {
                'subject': 'Welcome to Your Tenant Portal - EstateCore',
                'template': 'welcome_tenant'
            }
        }
        
        if notification_type not in notification_templates:
            logger.error(f"Unknown notification type: {notification_type}")
            return False
        
        config = notification_templates[notification_type]
        
        return self.send_template_email(
            to_emails=[user_email],
            template_name=config['template'],
            subject=config['subject'],
            template_data=data
        )
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                if self.config.SMTP_USE_TLS:
                    server.starttls()
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                logger.info("SMTP connection test successful")
                return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False

# Global email service instance
email_service = EmailService()