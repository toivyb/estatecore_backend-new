# Email Configuration Guide

## Overview

EstateCore now includes email functionality for sending user invitations and notifications. This guide explains how to configure email settings.

## Email Features

### ✅ **Implemented Features**
- **User Invitations**: Automatic email sending when creating new users
- **Re-invitations**: Send invitation emails to existing users
- **Email Templates**: Professional email templates with registration links
- **Error Handling**: Graceful fallback to console logging if email fails
- **Configuration Validation**: Checks for proper email settings

### 📧 **Email Types**
1. **Welcome Invitations** - Sent when creating new users
2. **Re-invitations** - Sent when re-inviting existing users
3. **Future**: Password reset, notifications, alerts

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Email Configuration (for invite emails and notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=EstateCore <your_email@gmail.com>
```

### Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "EstateCore"
   - Use this 16-character password for `MAIL_PASSWORD`

3. **Configuration Example**:
   ```bash
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=myestatecore@gmail.com
   MAIL_PASSWORD=abcd efgh ijkl mnop  # Your 16-character app password
   MAIL_DEFAULT_SENDER=EstateCore <myestatecore@gmail.com>
   ```

### Other Email Providers

#### Outlook/Hotmail
```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
```

#### SendGrid
```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key
```

#### AWS SES
```bash
MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_aws_smtp_username
MAIL_PASSWORD=your_aws_smtp_password
```

## Testing Email Configuration

### Run Email Test Script

```bash
cd estatecore_backend
python scripts/test_email.py
```

This script will:
- ✅ Check email configuration
- ✅ Display current settings
- ✅ Send a test email (if configured)
- ✅ Report success/failure

### Expected Output

**With Proper Configuration:**
```
🧪 Testing Email Functionality
==================================================
📧 MAIL_SERVER: smtp.gmail.com
📧 MAIL_PORT: 587
📧 MAIL_USE_TLS: True
📧 MAIL_USERNAME: myestatecore@gmail.com
📧 MAIL_DEFAULT_SENDER: EstateCore <myestatecore@gmail.com>
📧 Email Configured: ✅ Yes

🚀 Testing email send...
[EMAIL - SENT] To: myestatecore@gmail.com | Subject: EstateCore Email Test
📨 Email send result: ✅ Success

✅ Email test completed
```

**Without Configuration:**
```
📧 Email Configured: ❌ No
⚠️  Email not configured. Set MAIL_USERNAME and MAIL_PASSWORD in .env file
```

## Usage

### Creating Users with Email Invites

When you create a new user via the API:

```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "name": "John Doe",
    "role": "user"
  }'
```

**Response includes email status:**
```json
{
  "id": 2,
  "email": "newuser@example.com",
  "name": "John Doe",
  "role": "user",
  "status": "invited",
  "invite_url": "http://127.0.0.1:5173/register?token=abc123",
  "email_sent": true
}
```

### Re-sending Invitations

```bash
curl -X POST http://localhost:5000/api/users/2/invite
```

**Response:**
```json
{
  "invite_url": "http://127.0.0.1:5173/register?token=def456",
  "user": {...},
  "email_sent": true
}
```

## Email Templates

### Invitation Email Template

```
Subject: Welcome to EstateCore - Complete Your Registration

Hello John Doe,

You've been invited to join EstateCore as a user.

Please click the link below to complete your registration:
http://127.0.0.1:5173/register?token=abc123

This invitation will expire in 7 days.

Best regards,
The EstateCore Team
```

## Troubleshooting

### Common Issues

#### 1. "Email not configured" message
- **Cause**: Missing `MAIL_USERNAME` or `MAIL_PASSWORD` in `.env`
- **Solution**: Add proper email credentials

#### 2. "Authentication failed" error
- **Cause**: Wrong password or 2FA not enabled
- **Solution**: Use App Password for Gmail, enable 2FA

#### 3. "Connection refused" error
- **Cause**: Wrong MAIL_SERVER or MAIL_PORT
- **Solution**: Verify SMTP settings for your provider

#### 4. Emails sent but not received
- **Cause**: Emails in spam folder
- **Solution**: Check spam, add sender to contacts

### Debug Mode

To see detailed email logs, emails will show in console:

```
[EMAIL - SENT] To: user@example.com | Subject: Welcome to EstateCore
```

If email fails:
```
[EMAIL - ERROR] Failed to send to user@example.com: [error details]
[EMAIL - FALLBACK] To: user@example.com | Subject: Welcome to EstateCore | Body: Hello...
```

## Security Best Practices

1. **Never commit real credentials** to version control
2. **Use App Passwords** instead of account passwords
3. **Restrict SMTP access** to your application only
4. **Use environment variables** for all sensitive data
5. **Monitor email sending** for suspicious activity

## Production Deployment

### Recommended Setup

1. **Use a dedicated email service** (SendGrid, AWS SES, Mailgun)
2. **Set up SPF/DKIM records** for your domain
3. **Use a professional sender address** (e.g., noreply@yourcompany.com)
4. **Monitor bounce rates** and delivery metrics
5. **Implement rate limiting** to prevent abuse

### Environment Variables Checklist

- [ ] `MAIL_SERVER` - SMTP server address
- [ ] `MAIL_PORT` - SMTP port (usually 587)
- [ ] `MAIL_USE_TLS` - Enable TLS encryption
- [ ] `MAIL_USERNAME` - SMTP username
- [ ] `MAIL_PASSWORD` - SMTP password/API key
- [ ] `MAIL_DEFAULT_SENDER` - Default sender address

## Future Enhancements

- [ ] HTML email templates with styling
- [ ] Email delivery tracking and analytics
- [ ] Bulk email sending for notifications
- [ ] Email queue for high-volume sending
- [ ] Webhook support for bounce handling
- [ ] Multi-language email templates