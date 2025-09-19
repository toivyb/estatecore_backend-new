"""
Email utilities for EstateCore
Supports multiple email providers and SMTP configuration
"""
import smtplib
import os
import uuid
import secrets
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from datetime import datetime

def generate_invite_token():
    """Generate a secure invitation token"""
    return secrets.token_hex(16)

def get_smtp_config():
    """Get SMTP configuration from environment variables"""
    return {
        'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
        'smtp_username': os.environ.get('SMTP_USERNAME', ''),
        'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
        'smtp_use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true',
        'from_email': os.environ.get('FROM_EMAIL', os.environ.get('SMTP_USERNAME', '')),
        'from_name': os.environ.get('FROM_NAME', 'EstateCore System')
    }

def send_email(to_email, subject, html_content, text_content=None):
    """
    Send an email using SMTP configuration
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML email content
        text_content (str): Plain text email content (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        config = get_smtp_config()
        
        if not config['smtp_username'] or not config['smtp_password']:
            print("Email configuration missing - skipping actual email send")
            print(f"Would send email to {to_email} with subject: {subject}")
            return False
        
        # Create message
        msg = MimeMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = to_email
        
        # Add text content
        if text_content:
            text_part = MimeText(text_content, 'plain')
            msg.attach(text_part)
        
        # Add HTML content
        html_part = MimeText(html_content, 'html')
        msg.attach(html_part)
        
        # Connect to server and send email
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        
        if config['smtp_use_tls']:
            server.starttls()
        
        server.login(config['smtp_username'], config['smtp_password'])
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False

def get_invite_email_template(email, role, invited_by, token, access_details=None):
    """
    Generate HTML and text content for invitation emails
    
    Args:
        email (str): Recipient email
        role (str): User role
        invited_by (str): Name of person sending invite
        token (str): Invitation token
        access_details (dict): Additional access details for enhanced invites
    
    Returns:
        tuple: (html_content, text_content)
    """
    
    # Base URL for the application
    base_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    invite_url = f"{base_url}/invite/accept?token={token}&email={email}"
    
    # Determine access description
    if access_details:
        access_desc = []
        if access_details.get('property_role'):
            access_desc.append(f"Property Management ({access_details['property_role']})")
        if access_details.get('lpr_role'):
            company_name = access_details.get('company_name', 'assigned company')
            permissions = access_details.get('lpr_permissions', 'standard')
            access_desc.append(f"LPR Management ({access_details['lpr_role']}) with {permissions} permissions at {company_name}")
        role_description = " and ".join(access_desc) if access_desc else role
    else:
        role_description = role
    
    # HTML template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to EstateCore</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                line-height: 1.6;
                color: #333333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .email-container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 2px solid #007bff;
            }}
            .logo {{
                font-size: 28px;
                font-weight: bold;
                color: #007bff;
                margin-bottom: 10px;
            }}
            .invite-button {{
                display: inline-block;
                background-color: #007bff;
                color: #ffffff;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
                text-align: center;
            }}
            .invite-button:hover {{
                background-color: #0056b3;
            }}
            .details-box {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #007bff;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                font-size: 14px;
                color: #6c757d;
                text-align: center;
            }}
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                color: #856404;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo">EstateCore</div>
                <p>Property & License Plate Recognition Management System</p>
            </div>
            
            <h2>You're Invited to Join EstateCore!</h2>
            
            <p>Hello,</p>
            
            <p><strong>{invited_by}</strong> has invited you to join EstateCore with the following access:</p>
            
            <div class="details-box">
                <h3>Your Access Details:</h3>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Role:</strong> {role_description}</p>
                <p><strong>Invited by:</strong> {invited_by}</p>
                <p><strong>Invitation Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <p>To accept this invitation and create your account, click the button below:</p>
            
            <div style="text-align: center;">
                <a href="{invite_url}" class="invite-button">Accept Invitation & Create Account</a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 3px;">
                {invite_url}
            </p>
            
            <div class="warning">
                <strong>Important:</strong> This invitation will expire in 7 days. If you don't accept it within that time, please contact {invited_by} for a new invitation.
            </div>
            
            <div class="footer">
                <p>This email was sent by EstateCore System.</p>
                <p>If you did not expect this invitation, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    Welcome to EstateCore!
    
    {invited_by} has invited you to join EstateCore with the following access:
    
    Your Access Details:
    - Email: {email}
    - Role: {role_description}
    - Invited by: {invited_by}
    - Invitation Date: {datetime.now().strftime('%B %d, %Y')}
    
    To accept this invitation and create your account, visit:
    {invite_url}
    
    Important: This invitation will expire in 7 days.
    
    If you did not expect this invitation, please ignore this email.
    
    ---
    EstateCore System
    Property & License Plate Recognition Management
    """
    
    return html_content, text_content

def send_invite_email(email, role, invited_by, token):
    """
    Send a basic invitation email
    
    Args:
        email (str): Recipient email
        role (str): User role
        invited_by (str): Name of person sending invite
        token (str): Invitation token
    
    Returns:
        bool: True if sent successfully
    """
    subject = f"Invitation to Join EstateCore - {role.title()} Access"
    html_content, text_content = get_invite_email_template(email, role, invited_by, token)
    return send_email(email, subject, html_content, text_content)

def send_enhanced_invite_email(email, access_type, property_role, lpr_role, company_name, invited_by, token):
    """
    Send an enhanced invitation email with detailed access information
    
    Args:
        email (str): Recipient email
        access_type (str): Type of access (property_management, lpr_management, both)
        property_role (str): Property management role (if applicable)
        lpr_role (str): LPR management role (if applicable)
        company_name (str): LPR company name (if applicable)
        invited_by (str): Name of person sending invite
        token (str): Invitation token
    
    Returns:
        bool: True if sent successfully
    """
    # Build detailed access information
    access_details = {
        'access_type': access_type,
        'property_role': property_role,
        'lpr_role': lpr_role,
        'company_name': company_name,
        'lpr_permissions': 'manage_alerts'  # You can pass this as parameter if needed
    }
    
    # Generate role description for subject
    role_parts = []
    if property_role:
        role_parts.append(f"Property {property_role.replace('_', ' ').title()}")
    if lpr_role:
        role_parts.append(f"LPR {lpr_role.replace('_', ' ').title()}")
    
    role_description = " & ".join(role_parts) if role_parts else "User"
    
    subject = f"Invitation to Join EstateCore - {role_description} Access"
    html_content, text_content = get_invite_email_template(
        email, role_description, invited_by, token, access_details
    )
    return send_email(email, subject, html_content, text_content)

def send_rent_reminder(rent):
    """Send rent reminder email (existing function)"""
    print(f"Email reminder sent to tenant {rent.tenant_id} for rent {rent.id}")

def send_test_email(to_email):
    """
    Send a test email to verify SMTP configuration
    
    Args:
        to_email (str): Test recipient email
    
    Returns:
        bool: True if sent successfully
    """
    subject = "EstateCore Email Test"
    html_content = """
    <html>
    <body>
        <h2>Email Configuration Test</h2>
        <p>If you received this email, your EstateCore email configuration is working correctly!</p>
        <p><strong>Test sent at:</strong> {}</p>
    </body>
    </html>
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    text_content = f"""
    Email Configuration Test
    
    If you received this email, your EstateCore email configuration is working correctly!
    
    Test sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    return send_email(to_email, subject, html_content, text_content)

# Configuration check function
def check_email_config():
    """
    Check if email configuration is properly set up
    
    Returns:
        dict: Configuration status and details
    """
    config = get_smtp_config()
    
    status = {
        'configured': bool(config['smtp_username'] and config['smtp_password']),
        'server': config['smtp_server'],
        'port': config['smtp_port'],
        'username': config['smtp_username'],
        'from_email': config['from_email'],
        'from_name': config['from_name'],
        'tls_enabled': config['smtp_use_tls']
    }
    
    return status

if __name__ == "__main__":
    # Test the email configuration
    print("EstateCore Email Configuration Test")
    print("=" * 40)
    
    config_status = check_email_config()
    
    if config_status['configured']:
        print("✅ Email configuration found")
        print(f"Server: {config_status['server']}:{config_status['port']}")
        print(f"From: {config_status['from_name']} <{config_status['from_email']}>")
        print(f"TLS: {'Enabled' if config_status['tls_enabled'] else 'Disabled'}")
        
        # Optional: Send test email
        test_recipient = input("\nEnter email address to send test email (or press Enter to skip): ").strip()
        if test_recipient:
            if send_test_email(test_recipient):
                print("✅ Test email sent successfully!")
            else:
                print("❌ Test email failed to send")
    else:
        print("❌ Email configuration missing")
        print("\nTo enable email functionality, set these environment variables:")
        print("SMTP_SERVER=smtp.gmail.com")
        print("SMTP_PORT=587")
        print("SMTP_USERNAME=your_email@gmail.com")
        print("SMTP_PASSWORD=your_app_password")
        print("FROM_EMAIL=your_email@gmail.com")
        print("FROM_NAME=EstateCore System")
        print("SMTP_USE_TLS=true")