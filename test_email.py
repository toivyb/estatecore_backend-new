#!/usr/bin/env python3
"""
Test script to verify email configuration is working
Run this to test the email invite system
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from estatecore_backend import create_app
from utils.email import send_invite_email, generate_invite_token

def test_email_config():
    """Test email configuration"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Testing email configuration...")
            print(f"📧 MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
            print(f"📧 MAIL_PORT: {app.config.get('MAIL_PORT')}")
            print(f"📧 MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
            print(f"📧 APP_URL: {app.config.get('APP_URL')}")
            
            # Test sending an invite email
            test_email = input("\n🎯 Enter a test email address to send an invite to: ").strip()
            if not test_email:
                print("❌ No email provided. Test cancelled.")
                return
                
            print(f"\n📤 Sending test invitation to {test_email}...")
            
            token = generate_invite_token()
            success = send_invite_email(
                email=test_email,
                role="tenant",
                invited_by="EstateCore Admin",
                token=token
            )
            
            if success:
                print("✅ Test invitation sent successfully!")
                print(f"🔗 Invite URL: {app.config.get('APP_URL')}/invite-register?token={token}&email={test_email}")
                print("\n📬 Check the email inbox and spam folder!")
            else:
                print("❌ Failed to send test invitation. Check your email configuration.")
                
        except Exception as e:
            print(f"❌ Error testing email: {str(e)}")
            print("\n🔍 Common issues:")
            print("  - Check that Gmail 2FA is enabled")
            print("  - Verify you're using an App Password (not regular password)")
            print("  - Confirm the App Password has no spaces")
            
if __name__ == "__main__":
    test_email_config()