"""
Email Service for EstateCore
Handles all email communications including invitations, notifications, and reports
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import logging
from typing import List, Dict, Optional
import jinja2
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    """Email configuration settings"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    sender_name: str = "EstateCore"
    sender_email: str = None
    
    def __post_init__(self):
        if not self.sender_email:
            self.sender_email = self.username

class EmailService:
    def __init__(self, config: EmailConfig = None):
        """Initialize email service with configuration"""
        self.config = config or self._get_default_config()
        self.template_loader = jinja2.FileSystemLoader('email_templates')
        self.template_env = jinja2.Environment(loader=self.template_loader)
        
    def _get_default_config(self) -> EmailConfig:
        """Get email configuration from environment variables"""
        return EmailConfig(
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            username=os.getenv('SMTP_USERNAME', ''),
            password=os.getenv('SMTP_PASSWORD', ''),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            sender_name=os.getenv('SENDER_NAME', 'EstateCore'),
            sender_email=os.getenv('SENDER_EMAIL', '')
        )
    
    def _create_smtp_connection(self):
        """Create and return SMTP connection"""
        try:
            if self.config.use_tls:
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls(context=ssl.create_default_context())
            else:
                server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port)
            
            server.login(self.config.username, self.config.password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def _render_template(self, template_name: str, context: Dict) -> str:
        """Render email template with context"""
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return self._get_fallback_template(template_name, context)
    
    def _get_fallback_template(self, template_name: str, context: Dict) -> str:
        """Fallback templates when template files are not available"""
        fallback_templates = {
            'user_invitation.html': """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Welcome to EstateCore!</h2>
                    <p>Hi {{ recipient_name }},</p>
                    <p>You've been invited to join <strong>{{ organization_name }}</strong> on EstateCore.</p>
                    <p><strong>Your Role:</strong> {{ role }}</p>
                    <p><strong>Login Credentials:</strong></p>
                    <ul>
                        <li>Email: {{ email }}</li>
                        <li>Temporary Password: {{ temporary_password }}</li>
                    </ul>
                    <a href="{{ login_url }}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                        Login to EstateCore
                    </a>
                    <p><small>Please change your password after your first login.</small></p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px;">
                        Best regards,<br>
                        The EstateCore Team<br>
                        <a href="mailto:support@estatecore.com">support@estatecore.com</a>
                    </p>
                </div>
            </body>
            </html>
            """,
            'maintenance_notification.html': """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc2626;">Maintenance {{ notification_type }}</h2>
                    <p>Hi {{ recipient_name }},</p>
                    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">{{ title }}</h3>
                        <p><strong>Property:</strong> {{ property_name }}</p>
                        <p><strong>Unit:</strong> {{ unit_number }}</p>
                        <p><strong>Priority:</strong> {{ priority }}</p>
                        <p><strong>Description:</strong></p>
                        <p>{{ description }}</p>
                    </div>
                    <p>Status: <strong>{{ status }}</strong></p>
                    <a href="{{ dashboard_url }}" style="display: inline-block; background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                        View Details
                    </a>
                </div>
            </body>
            </html>
            """,
            'payment_receipt.html': """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #059669;">Payment Receipt</h2>
                    <p>Hi {{ recipient_name }},</p>
                    <p>Thank you for your payment. Here are the details:</p>
                    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Amount:</strong> ${{ amount }}</p>
                        <p><strong>Payment Date:</strong> {{ payment_date }}</p>
                        <p><strong>Property:</strong> {{ property_name }}</p>
                        <p><strong>Unit:</strong> {{ unit_number }}</p>
                        <p><strong>Payment Method:</strong> {{ payment_method }}</p>
                        <p><strong>Transaction ID:</strong> {{ transaction_id }}</p>
                    </div>
                    <a href="{{ receipt_url }}" style="display: inline-block; background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                        Download Receipt
                    </a>
                </div>
            </body>
            </html>
            """
        }
        
        template_content = fallback_templates.get(template_name, 
            f"<html><body><h2>Email Notification</h2><p>Context: {context}</p></body></html>")
        
        # Simple template substitution for fallback
        for key, value in context.items():
            template_content = template_content.replace(f"{{{{ {key} }}}}", str(value))
        
        return template_content
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   html_content: str = None,
                   text_content: str = None,
                   attachments: List[str] = None,
                   cc_emails: List[str] = None,
                   bcc_emails: List[str] = None) -> bool:
        """Send email with optional attachments"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.sender_name} <{self.config.sender_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add text and HTML content
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Send email
            all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
            
            with self._create_smtp_connection() as server:
                server.send_message(msg, to_addrs=all_recipients)
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_user_invitation(self, 
                           email: str, 
                           name: str, 
                           role: str, 
                           temporary_password: str,
                           organization_name: str = "EstateCore",
                           login_url: str = "https://app.estatecore.com") -> bool:
        """Send user invitation email"""
        context = {
            'recipient_name': name,
            'email': email,
            'role': role,
            'temporary_password': temporary_password,
            'organization_name': organization_name,
            'login_url': login_url
        }
        
        html_content = self._render_template('user_invitation.html', context)
        text_content = f"""
        Welcome to EstateCore!
        
        Hi {name},
        
        You've been invited to join {organization_name} on EstateCore.
        
        Your Role: {role}
        Login Email: {email}
        Temporary Password: {temporary_password}
        
        Please login at: {login_url}
        
        Best regards,
        The EstateCore Team
        """
        
        return self.send_email(
            to_emails=[email],
            subject=f"Welcome to {organization_name} - EstateCore Invitation",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_maintenance_notification(self,
                                    to_emails: List[str],
                                    notification_type: str,  # 'Request', 'Update', 'Completion'
                                    title: str,
                                    description: str,
                                    property_name: str,
                                    unit_number: str = None,
                                    priority: str = 'Medium',
                                    status: str = 'Open',
                                    recipient_name: str = 'Tenant',
                                    dashboard_url: str = "https://app.estatecore.com/maintenance") -> bool:
        """Send maintenance notification email"""
        context = {
            'recipient_name': recipient_name,
            'notification_type': notification_type,
            'title': title,
            'description': description,
            'property_name': property_name,
            'unit_number': unit_number or 'N/A',
            'priority': priority,
            'status': status,
            'dashboard_url': dashboard_url
        }
        
        html_content = self._render_template('maintenance_notification.html', context)
        
        return self.send_email(
            to_emails=to_emails,
            subject=f"Maintenance {notification_type}: {title}",
            html_content=html_content
        )
    
    def send_payment_receipt(self,
                           email: str,
                           recipient_name: str,
                           amount: float,
                           property_name: str,
                           unit_number: str = None,
                           payment_method: str = 'Credit Card',
                           transaction_id: str = None,
                           payment_date: str = None,
                           receipt_url: str = None) -> bool:
        """Send payment receipt email"""
        context = {
            'recipient_name': recipient_name,
            'amount': f"{amount:.2f}",
            'payment_date': payment_date or datetime.now().strftime('%B %d, %Y'),
            'property_name': property_name,
            'unit_number': unit_number or 'N/A',
            'payment_method': payment_method,
            'transaction_id': transaction_id or 'N/A',
            'receipt_url': receipt_url or 'https://app.estatecore.com/receipts'
        }
        
        html_content = self._render_template('payment_receipt.html', context)
        
        return self.send_email(
            to_emails=[email],
            subject=f"Payment Receipt - ${amount:.2f}",
            html_content=html_content
        )
    
    def send_lease_reminder(self,
                          email: str,
                          tenant_name: str,
                          property_name: str,
                          unit_number: str,
                          lease_end_date: str,
                          days_until_expiry: int) -> bool:
        """Send lease expiration reminder"""
        context = {
            'tenant_name': tenant_name,
            'property_name': property_name,
            'unit_number': unit_number,
            'lease_end_date': lease_end_date,
            'days_until_expiry': days_until_expiry
        }
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f59e0b;">Lease Expiration Reminder</h2>
                <p>Hi {tenant_name},</p>
                <p>This is a reminder that your lease for <strong>{property_name} - Unit {unit_number}</strong> 
                will expire in <strong>{days_until_expiry} days</strong> on {lease_end_date}.</p>
                <p>Please contact us to discuss renewal options or move-out procedures.</p>
                <a href="https://app.estatecore.com/lease" style="display: inline-block; background-color: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                    Lease Management
                </a>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_emails=[email],
            subject=f"Lease Expiration Reminder - {days_until_expiry} days remaining",
            html_content=html_content
        )
    
    def send_bulk_notification(self,
                             recipients: List[Dict[str, str]],  # [{'email': '', 'name': ''}]
                             subject: str,
                             template_name: str,
                             common_context: Dict = None,
                             individual_contexts: List[Dict] = None) -> Dict[str, bool]:
        """Send bulk notifications with personalization"""
        results = {}
        common_context = common_context or {}
        individual_contexts = individual_contexts or [{}] * len(recipients)
        
        for i, recipient in enumerate(recipients):
            context = {**common_context, **individual_contexts[i]}
            context['recipient_name'] = recipient.get('name', 'User')
            
            html_content = self._render_template(template_name, context)
            
            success = self.send_email(
                to_emails=[recipient['email']],
                subject=subject,
                html_content=html_content
            )
            
            results[recipient['email']] = success
        
        return results
    
    def test_configuration(self) -> bool:
        """Test email configuration by sending a test email"""
        try:
            test_content = """
            <html>
            <body>
                <h2>EstateCore Email Configuration Test</h2>
                <p>This is a test email to verify your email configuration is working correctly.</p>
                <p>Timestamp: {}</p>
            </body>
            </html>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            return self.send_email(
                to_emails=[self.config.sender_email],
                subject="EstateCore Email Configuration Test",
                html_content=test_content
            )
        except Exception as e:
            logger.error(f"Email configuration test failed: {e}")
            return False

# Utility functions for common email operations
def create_email_service() -> EmailService:
    """Create email service with default configuration"""
    return EmailService()

def send_test_email() -> bool:
    """Send a test email to verify configuration"""
    service = create_email_service()
    return service.test_configuration()

if __name__ == "__main__":
    # Test the email service
    service = create_email_service()
    
    # Test configuration
    if service.test_configuration():
        print("✅ Email configuration is working!")
    else:
        print("❌ Email configuration failed!")
        
    # Example usage
    # service.send_user_invitation(
    #     email="user@example.com",
    #     name="John Doe",
    #     role="Tenant",
    #     temporary_password="temp123",
    #     organization_name="Sunset Apartments"
    # )