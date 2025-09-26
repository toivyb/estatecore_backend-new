#!/usr/bin/env python3
"""
Email Configuration Setup for EstateCore
Run this script to configure email settings for sending invitations.
"""

import os
import getpass

def setup_email_config():
    print("🏢 EstateCore Email Configuration Setup")
    print("=" * 50)
    print()
    
    print("This will help you configure email settings for sending user invitations.")
    print("You'll need an email account with SMTP access (Gmail, Outlook, etc.)")
    print()
    
    # Get email provider
    print("Select your email provider:")
    print("1. Gmail")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. Other/Custom")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        smtp_server = "smtp.gmail.com"
        smtp_port = "587"
        print("\n📧 Gmail selected. You'll need to:")
        print("1. Enable 2-Factor Authentication")
        print("2. Generate an App Password (not your regular password)")
        print("3. Go to: Google Account > Security > 2-Step Verification > App passwords")
    elif choice == "2":
        smtp_server = "smtp.live.com"
        smtp_port = "587"
        print("\n📧 Outlook/Hotmail selected.")
    elif choice == "3":
        smtp_server = "smtp.mail.yahoo.com" 
        smtp_port = "587"
        print("\n📧 Yahoo selected.")
    else:
        smtp_server = input("Enter SMTP server: ").strip()
        smtp_port = input("Enter SMTP port (usually 587 or 465): ").strip()
    
    print()
    email_address = input("Enter your email address: ").strip()
    
    print("\n🔒 For security, enter your email password:")
    if choice == "1":
        print("(Use your Gmail App Password, NOT your regular password)")
    email_password = getpass.getpass("Email password: ")
    
    from_name = input("Enter sender name (default: EstateCore System): ").strip()
    if not from_name:
        from_name = "EstateCore System"
    
    # Create .env file
    env_content = f"""# EstateCore Email Configuration
SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
EMAIL_ADDRESS={email_address}
EMAIL_PASSWORD={email_password}
FROM_NAME={from_name}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print()
    print("✅ Email configuration saved to .env file")
    print()
    print("🧪 Testing email configuration...")
    
    # Test email configuration
    try:
        import smtplib
        import ssl
        from email.mime.text import MIMEText
        
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls(context=context)
            server.login(email_address, email_password)
            
        print("✅ Email configuration test successful!")
        print()
        print("🚀 You can now send invitation emails from EstateCore!")
        print("The system will automatically use these settings when sending invites.")
        
    except Exception as e:
        print(f"❌ Email configuration test failed: {e}")
        print()
        print("Please check your settings and try again.")
        print("Common issues:")
        print("- Wrong password (use App Password for Gmail)")
        print("- 2-Factor Authentication not enabled")
        print("- Less secure app access disabled")

if __name__ == "__main__":
    setup_email_config()