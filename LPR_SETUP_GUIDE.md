# License Plate Recognition System Setup Guide

## Overview

This system provides two main LPR capabilities:
1. **FTP Server System** - Automatically processes images uploaded by cameras via FTP
2. **Standalone LPR Client** - API-based service for external client integration

## Features

- **Automatic License Plate Recognition** using OpenALPR API
- **Blacklist Management** with instant notifications
- **FTP Server** for camera image uploads
- **REST API** for client integration
- **Web Dashboard** for management and monitoring
- **Multi-camera Support** with individual authentication
- **Real-time Notifications** for blacklisted plates

## Prerequisites

1. **OpenALPR API Key** - Sign up at https://www.openalpr.com/
2. **Python 3.8+** with required packages
3. **PostgreSQL Database** (already configured)

## Installation

### 1. Install LPR Dependencies

```bash
pip install -r requirements-lpr.txt
```

### 2. Set Environment Variables

```bash
# OpenALPR Configuration
export OPENALPR_API_KEY="your_api_key_here"

# FTP Server Configuration (optional)
export LPR_FTP_HOST="0.0.0.0"
export LPR_FTP_PORT="21"

# Camera Configuration
export LPR_RTSP_URL="rtsp://camera_ip:554/stream"
export LPR_SAVE_FOLDER="captured_frames"
export LPR_FRAME_SKIP="30"
```

### 3. Create Database Tables

```bash
python create_lpr_tables.py
```

This creates:
- `lpr_events` - Recognition events log
- `lpr_blacklist` - Blacklisted plates
- `lpr_cameras` - Camera configuration
- `lpr_clients` - API client management

## Usage

### FTP Server System

#### Start the FTP Server
```bash
python lpr_ftp_server.py
```

Default FTP credentials:
- `cam001` / `cam001pass`
- `cam002` / `cam002pass` 
- `cam003` / `cam003pass`
- `anonymous` (for testing)

#### Camera Configuration
Configure your IP cameras to upload images via FTP:
- **Server**: Your server IP
- **Port**: 21 (or configured port)
- **Username/Password**: Use camera-specific credentials
- **Upload Path**: Camera will auto-create folders

#### How It Works
1. Camera takes photo and uploads via FTP
2. Server receives image and processes it
3. License plate is recognized using OpenALPR
4. System checks against blacklist
5. Event is logged to database
6. Notification sent if plate is blacklisted

### Standalone LPR Client System

#### Command Line Interface

**Recognize single image:**
```bash
python lpr_client_system.py recognize image.jpg
```

**Batch process multiple images:**
```bash
python lpr_client_system.py batch *.jpg
```

**Blacklist management:**
```bash
# Check if plate is blacklisted
python lpr_client_system.py blacklist check ABC123

# Add to blacklist
python lpr_client_system.py blacklist add ABC123 --reason "Stolen vehicle"

# Remove from blacklist
python lpr_client_system.py blacklist remove ABC123

# List all blacklisted plates
python lpr_client_system.py blacklist list
```

**Get recent events:**
```bash
python lpr_client_system.py events --limit 100
```

#### Python API Integration

```python
from lpr_client_system import LPRClient

# Initialize client
client = LPRClient('http://localhost:5000', api_key='your_api_key')

# Recognize license plate
result = client.recognize_image('car_image.jpg')
print(f"Plate: {result['plate']}, Confidence: {result['confidence']}%")

# Check blacklist
status = client.check_blacklist('ABC123')
print(f"Blacklisted: {status['is_blacklisted']}")

# Add to blacklist
client.add_to_blacklist('DEF456', 'Security concern')
```

### Web Dashboard

Access the LPR Dashboard at: `http://localhost:5173/lpr-dashboard`

Features:
- **Real-time Statistics** - Events, blacklist count, alerts
- **Image Recognition Test** - Upload and test images
- **Blacklist Management** - Add/remove plates
- **Recent Detections** - View latest events
- **Camera Status** - Monitor camera activity

## API Endpoints

### Recognition
- `POST /api/lpr/recognize` - Recognize plate from uploaded image
- `GET /api/lpr/events` - Get recognition events
- `POST /api/lpr/events` - Log new event

### Blacklist Management
- `GET /api/lpr/blacklist` - Get blacklist
- `POST /api/lpr/blacklist` - Add plate to blacklist
- `DELETE /api/lpr/blacklist` - Remove plate from blacklist
- `GET /api/lpr/blacklist/check` - Check if plate is blacklisted

### Notifications
- `POST /api/notifications/send` - Send notification

## Camera Setup Examples

### Hikvision Camera FTP Upload
1. Go to Configuration > Network > Advanced Settings > FTP
2. Enable FTP upload
3. Set server address, port, username, password
4. Configure upload schedule or motion trigger

### Dahua Camera FTP Upload
1. Go to Setup > Network > FTP
2. Enable FTP upload
3. Configure server settings
4. Set upload conditions (schedule/event)

### Generic IP Camera
Most IP cameras support FTP upload in their web interface:
1. Find Network/FTP settings
2. Enable FTP client
3. Configure server details
4. Set upload triggers

## Troubleshooting

### Common Issues

**FTP Server not accessible:**
- Check firewall settings (port 21)
- Verify FTP server is running
- Test with FTP client

**Recognition not working:**
- Verify OpenALPR API key
- Check image quality and format
- Ensure internet connectivity

**Database errors:**
- Run `create_lpr_tables.py` to create tables
- Check database connection
- Verify PostgreSQL is running

### Logs and Monitoring

**FTP Server logs:**
```bash
# Check console output when running lpr_ftp_server.py
[FTP] New image received: /path/to/image.jpg
[LPR] Plate detected: ABC123 (confidence: 85.2%)
[ALERT] Blacklist notification sent for plate: ABC123
```

**API logs:**
```bash
# Check Flask app logs
LPR events error: (details)
Blacklist check error: (details)
```

## Security Considerations

1. **Change default FTP passwords** for production
2. **Use HTTPS** for API endpoints in production
3. **Implement API rate limiting** for client access
4. **Secure OpenALPR API key** (environment variable)
5. **Regular blacklist audits** to remove outdated entries

## Performance Optimization

1. **Adjust frame skip** rate for RTSP cameras to reduce API usage
2. **Implement image caching** to avoid duplicate processing
3. **Use database indexing** on frequently queried columns
4. **Configure proper logging levels** for production

## Integration Examples

### Slack Notifications
Modify the notification endpoint to send Slack messages:

```python
import requests

def send_slack_notification(data):
    webhook_url = "your_slack_webhook_url"
    message = f"🚨 Blacklisted plate detected: {data['plate']} at {data['camera_id']}"
    requests.post(webhook_url, json={"text": message})
```

### Email Alerts
Add email notifications for critical events:

```python
import smtplib
from email.mime.text import MIMEText

def send_email_alert(plate, camera_id):
    msg = MIMEText(f"Blacklisted plate {plate} detected at {camera_id}")
    msg['Subject'] = 'LPR Security Alert'
    msg['From'] = 'security@yourcompany.com'
    msg['To'] = 'admin@yourcompany.com'
    
    smtp = smtplib.SMTP('localhost')
    smtp.send_message(msg)
    smtp.quit()
```

## Support

For technical support or feature requests:
1. Check the troubleshooting section
2. Review API documentation
3. Test with the web dashboard
4. Contact system administrator