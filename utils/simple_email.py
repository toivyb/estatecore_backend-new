"""
Simplified email utilities for EstateCore
Works around import issues by using basic SMTP
"""
import smtplib
import os
import secrets
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

def send_simple_email(to_email, subject, message_content):
    """
    Send a simple email using basic SMTP
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        message_content (str): Email message content
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        config = get_smtp_config()
        
        if not config['smtp_username'] or not config['smtp_password']:
            print(f"Email configuration missing - skipping actual email send to {to_email}")
            print(f"Subject: {subject}")
            print(f"Message: {message_content[:100]}...")
            return False
        
        # Create simple email message
        from_addr = f"{config['from_name']} <{config['from_email']}>"
        
        message = f"""From: {from_addr}
To: {to_email}
Subject: {subject}

{message_content}
"""
        
        # Connect to server and send email
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        
        if config['smtp_use_tls']:
            server.starttls()
        
        server.login(config['smtp_username'], config['smtp_password'])
        server.sendmail(config['from_email'], [to_email], message)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False

def create_invite_message(email, role, invited_by, token, access_details=None):
    """Create invitation message content"""
    
    base_url = os.environ.get('FRONTEND_URL', 'http://localhost:5174')
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
    
    message = f"""Welcome to EstateCore!

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
    
    return message

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
    message_content = create_invite_message(email, role, invited_by, token)
    return send_simple_email(email, subject, message_content)

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
    message_content = create_invite_message(email, role_description, invited_by, token, access_details)
    return send_simple_email(email, subject, message_content)

def send_test_email(to_email):
    """
    Send a test email to verify SMTP configuration
    """
    subject = "EstateCore Email Test"
    message_content = f"""Email Configuration Test

If you received this email, your EstateCore email configuration is working correctly!

Test sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
EstateCore System"""
    
    return send_simple_email(to_email, subject, message_content)

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
    print("EstateCore Simple Email Configuration Test")
    print("=" * 40)
    
    config_status = check_email_config()
    
    if config_status['configured']:
        print("OK: Email configuration found")
        print(f"Server: {config_status['server']}:{config_status['port']}")
        print(f"From: {config_status['from_name']} <{config_status['from_email']}>")
        print(f"TLS: {'Enabled' if config_status['tls_enabled'] else 'Disabled'}")
        
        # Optional: Send test email
        test_recipient = input("\nEnter email address to send test email (or press Enter to skip): ").strip()
        if test_recipient:
            if send_test_email(test_recipient):
                print("OK: Test email sent successfully!")
            else:
                print("ERROR: Test email failed to send")
    else:
        print("ERROR: Email configuration missing")
        print("\nTo enable email functionality, set these environment variables:")
        print("SMTP_SERVER=smtp.gmail.com")
        print("SMTP_PORT=587") 
        print("SMTP_USERNAME=your_email@gmail.com")
        print("SMTP_PASSWORD=your_app_password")
        print("FROM_EMAIL=your_email@gmail.com")
        print("FROM_NAME=EstateCore System")
        print("SMTP_USE_TLS=true")
        print("\nFor Gmail users:")
        print("1. Enable 2-Factor Authentication")
        print("2. Generate an App Password")
        print("3. Use the App Password as SMTP_PASSWORD")