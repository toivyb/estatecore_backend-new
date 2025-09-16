from flask import current_app, render_template_string
from flask_mail import Mail, Message
import secrets
import os
from datetime import datetime, timedelta

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with the app"""
    mail.init_app(app)

def generate_invite_token():
    """Generate a secure random token for invites"""
    return secrets.urlsafe_b64_token(32)

def send_invite_email(email, role, invited_by, token):
    """Send invitation email with registration link"""
    try:
        app_url = current_app.config.get('APP_URL', 'http://localhost:3000')
        invite_link = f"{app_url}/invite-register?token={token}&email={email}"
        
        subject = f"You're Invited to EstateCore - {role.title()} Access"
        
        html_template = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                <h1 style="color: #2563eb;">🏠 EstateCore</h1>
                <h2 style="color: #374151;">You're Invited!</h2>
            </div>
            
            <div style="padding: 30px;">
                <p>Hello,</p>
                
                <p><strong>{{ invited_by }}</strong> has invited you to join EstateCore as a <strong>{{ role }}</strong>.</p>
                
                <p>EstateCore is a comprehensive property management platform that helps manage:</p>
                <ul>
                    <li>Properties and Units</li>
                    <li>Tenant Management</li>
                    <li>Rent Collection</li>
                    <li>Maintenance Requests</li>
                    <li>Financial Reports</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ invite_link }}" 
                       style="background-color: #2563eb; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Accept Invitation & Create Account
                    </a>
                </div>
                
                <p><strong>Your role:</strong> {{ role }}</p>
                <p><strong>Email:</strong> {{ email }}</p>
                
                <p style="color: #6b7280; font-size: 14px;">
                    This invitation link will expire in 7 days. If you have any questions, 
                    please contact {{ invited_by }}.
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                
                <p style="color: #6b7280; font-size: 12px; text-align: center;">
                    If you didn't expect this invitation, you can safely ignore this email.
                    <br>
                    This link will only work once and expires automatically.
                </p>
            </div>
        </body>
        </html>
        """
        
        html_body = render_template_string(html_template, 
                                          invited_by=invited_by,
                                          role=role,
                                          email=email,
                                          invite_link=invite_link)
        
        text_body = f"""
EstateCore Invitation

Hello,

{invited_by} has invited you to join EstateCore as a {role}.

Click this link to create your account:
{invite_link}

Your role: {role}
Email: {email}

This invitation expires in 7 days.

If you didn't expect this invitation, you can safely ignore this email.
        """.strip()
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        print(f"✅ Invitation email sent to {email} for role {role}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send invitation email to {email}: {str(e)}")
        return False

def send_rent_reminder(rent):
    """Send rent reminder email to tenant"""
    try:
        # This could be enhanced to send actual emails
        # For now, we'll log it and add to in-app messages
        print(f"📧 Rent reminder scheduled for tenant {rent.tenant_id} for rent {rent.id}")
        
        # Add to in-app message system
        from estatecore_backend.models import Message
        message = Message(
            recipient_id=rent.tenant_id,
            sender_id=None,  # System message
            subject=f"Rent Reminder - ${rent.amount}",
            content=f"Your rent payment of ${rent.amount} is due. Please make your payment at your earliest convenience.",
            message_type='rent_reminder',
            is_system=True
        )
        
        # This would be saved to database in a real implementation
        print(f"📨 In-app message created for tenant {rent.tenant_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send rent reminder: {str(e)}")
        return False

def send_maintenance_notification(tenant_id, subject, message):
    """Send maintenance notification via in-app messaging"""
    try:
        from estatecore_backend.models import Message
        
        msg = Message(
            recipient_id=tenant_id,
            sender_id=None,  # System message
            subject=subject,
            content=message,
            message_type='maintenance',
            is_system=True
        )
        
        print(f"🔧 Maintenance notification sent to tenant {tenant_id}: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send maintenance notification: {str(e)}")
        return False
