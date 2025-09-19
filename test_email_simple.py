#!/usr/bin/env python3
"""
Simple email test script
"""
import sys
import os

print("Testing email functionality...")
print("Python version:", sys.version)

try:
    import smtplib
    print("OK: smtplib imported successfully")
except ImportError as e:
    print("ERROR: Failed to import smtplib:", str(e))
    
try:
    from email.mime.text import MimeText
    print("OK: MimeText imported successfully")
except ImportError as e:
    print("ERROR: Failed to import MimeText:", str(e))
    
try:
    from email.mime.multipart import MimeMultipart
    print("OK: MimeMultipart imported successfully")
except ImportError as e:
    print("ERROR: Failed to import MimeMultipart:", str(e))

# Check environment variables
print("\nEmail configuration environment variables:")
env_vars = [
    'SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 
    'SMTP_PASSWORD', 'FROM_EMAIL', 'FROM_NAME'
]

for var in env_vars:
    value = os.environ.get(var, 'NOT_SET')
    if var == 'SMTP_PASSWORD' and value != 'NOT_SET':
        value = '*' * len(value)  # Hide password
    print(f"{var}: {value}")

# Test basic email sending function (without actual sending)
def test_email_creation():
    try:
        from email.mime.text import MimeText
        msg = MimeText("Test message", 'plain')
        msg['Subject'] = "Test Subject"
        msg['From'] = "test@example.com"
        msg['To'] = "recipient@example.com"
        print("OK: Email message creation successful")
        return True
    except Exception as e:
        print("ERROR: Email message creation failed:", str(e))
        return False

if __name__ == "__main__":
    test_email_creation()
    
    # Show current working directory
    print(f"\nCurrent working directory: {os.getcwd()}")
    
    # Check if we can access utils module
    try:
        sys.path.insert(0, '.')
        from utils.email_utils import check_email_config
        print("OK: email_utils module imported successfully")
        
        config = check_email_config()
        print(f"Email configured: {config['configured']}")
        
    except ImportError as e:
        print("ERROR: Failed to import email_utils:", str(e))
    except Exception as e:
        print("ERROR: Error checking email config:", str(e))