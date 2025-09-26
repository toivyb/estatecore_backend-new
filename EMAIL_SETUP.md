# 📧 Email Service Setup for EstateCore

EstateCore now includes real email functionality for sending user invitations. Follow this guide to configure email services.

## Quick Setup

1. **Run the setup script:**
   ```bash
   python setup_email.py
   ```

2. **Follow the prompts** to configure your email settings

3. **Test the configuration** - the script will verify your settings

## Manual Setup

If you prefer to configure manually:

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your email settings:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   FROM_NAME=EstateCore System
   ```

## Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to **Security** tab
3. Enable **2-Step Verification**

### Step 2: Generate App Password
1. In Security settings, find **App passwords**
2. Select app: **Mail**
3. Select device: **Other (custom name)** → Enter "EstateCore"
4. **Copy the generated 16-character password**
5. Use this password in your `.env` file (NOT your regular Gmail password)

### Step 3: Update Configuration
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-gmail@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
FROM_NAME=EstateCore System
```

## Other Email Providers

### Outlook/Hotmail
```env
SMTP_SERVER=smtp.live.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@outlook.com
EMAIL_PASSWORD=your-password
```

### Yahoo
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@yahoo.com
EMAIL_PASSWORD=your-password
```

### Custom SMTP Server
```env
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@yourdomain.com
EMAIL_PASSWORD=your-password
```

## Testing Email Configuration

Run this test script to verify your configuration:

```python
import os
import smtplib
import ssl
from email.mime.text import MIMEText

# Load environment variables
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT'))
email_address = os.getenv('EMAIL_ADDRESS')
email_password = os.getenv('EMAIL_PASSWORD')

try:
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls(context=context)
        server.login(email_address, email_password)
    print("✅ Email configuration successful!")
except Exception as e:
    print(f"❌ Configuration failed: {e}")
```

## Email Features

Once configured, EstateCore will send professional HTML emails with:

- **Welcome message** with company branding
- **Access level details** (Property Management, LPR, or Both)
- **Secure invitation links** that expire in 7 days
- **Professional formatting** with responsive design
- **Security notices** and instructions

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Use App Password for Gmail (not regular password)
   - Enable 2-Factor Authentication first
   - Check email/password spelling

2. **"Connection timeout"**
   - Check SMTP server and port
   - Verify firewall/antivirus isn't blocking
   - Try port 465 with SSL instead of 587 with TLS

3. **"Less secure app access"**
   - Enable in Google Account Security settings
   - Or use App Password (recommended)

4. **"SMTP server not found"**
   - Verify SMTP server address
   - Check internet connection

### Security Notes

- **Never commit `.env` file to version control**
- **Use App Passwords instead of regular passwords**
- **Enable 2-Factor Authentication on email accounts**
- **Regularly rotate email passwords**
- **Use environment variables in production**

## Production Deployment

For production environments:

1. **Use environment variables** instead of `.env` files
2. **Set up dedicated email service** (SendGrid, AWS SES, etc.)
3. **Configure proper DNS records** (SPF, DKIM, DMARC)
4. **Monitor email delivery rates**
5. **Set up email templates** in your email service provider

## Support

If you need help with email configuration:

1. Check the troubleshooting section above
2. Verify your email provider's SMTP settings
3. Test with the provided test script
4. Check EstateCore logs for detailed error messages

---

**Security Reminder:** Always use App Passwords for Gmail and enable 2-Factor Authentication on all email accounts used with EstateCore.