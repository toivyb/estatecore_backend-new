# EstateCore Email Configuration
import os
from typing import Optional

class EmailConfig:
    """Secure email configuration for EstateCore"""
    
    def __init__(self):
        # SMTP Configuration - Use environment variables for security
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'
        
        # Email Authentication - NEVER hardcode credentials
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME')  # Your email address
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Your app-specific password
        
        # Sender Information
        self.SENDER_NAME = os.getenv('SENDER_NAME', 'EstateCore Platform')
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL', self.SMTP_USERNAME)
        self.REPLY_TO_EMAIL = os.getenv('REPLY_TO_EMAIL', self.SENDER_EMAIL)
        
        # Email Templates
        self.TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates', 'email')
        
        # Rate Limiting
        self.MAX_EMAILS_PER_HOUR = int(os.getenv('MAX_EMAILS_PER_HOUR', '100'))
        self.MAX_RECIPIENTS_PER_EMAIL = int(os.getenv('MAX_RECIPIENTS_PER_EMAIL', '50'))
        
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.SMTP_USERNAME and self.SMTP_PASSWORD)
    
    def get_smtp_config(self) -> dict:
        """Get SMTP configuration dictionary"""
        return {
            'server': self.SMTP_SERVER,
            'port': self.SMTP_PORT,
            'username': self.SMTP_USERNAME,
            'password': self.SMTP_PASSWORD,
            'use_tls': self.SMTP_USE_TLS,
            'use_ssl': self.SMTP_USE_SSL,
        }

# Global email configuration instance
email_config = EmailConfig()