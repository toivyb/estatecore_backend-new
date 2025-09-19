# 🚗 LPR Camera FTP Integration Setup Guide

## Overview
This guide explains how to configure LPR cameras to automatically upload images to your EstateCore platform for license plate recognition and blacklist checking.

## 🔧 Server Setup

### 1. Install FTP Dependencies
```bash
pip install -r ftp_requirements.txt
```

### 2. Configure Environment Variables
Update your `.env` file with FTP settings:
```env
# FTP Server Configuration
FTP_HOST=0.0.0.0          # Listen on all interfaces
FTP_PORT=21               # Standard FTP port
FTP_USERNAME=lpr_camera   # Camera login username
FTP_PASSWORD=CameraUpload123!  # Camera login password
FTP_ADMIN_PASSWORD=AdminAccess456!  # Admin access password
```

### 3. Start the Complete LPR System
```bash
# Option 1: Start everything together
python start_lpr_system.py

# Option 2: Start services separately
python app.py          # Flask backend (Terminal 1)
python ftp_server.py   # FTP server (Terminal 2)
```

## 📷 Camera Configuration

### Connection Settings
Configure your LPR cameras with these FTP upload settings:

| Setting | Value |
|---------|--------|
| **FTP Server** | `your-server-ip-address` |
| **Port** | `21` |
| **Username** | `lpr_camera` |
| **Password** | `CameraUpload123!` |
| **Upload Directory** | `/` (root) |
| **Transfer Mode** | `Passive (PASV)` |

### 🎯 Recommended Camera Settings

#### Upload Triggers
- **Motion Detection**: Upload on vehicle detection
- **Schedule**: Continuous monitoring 24/7
- **File Format**: JPEG (recommended for speed)
- **Image Quality**: High (for better OCR accuracy)
- **Resolution**: 1920x1080 minimum

#### Filename Convention
Use descriptive filenames for better processing:
```
camera1_YYYYMMDD_HHMMSS.jpg
cam_001_20231201_120530.jpg
lpr_camera_5_motion_detected.jpg
```

## 🔄 Automatic Processing Workflow

1. **Camera captures image** → Uploads via FTP
2. **FTP server receives file** → Triggers processing
3. **AI Recognition** → Extracts license plates
4. **Blacklist Check** → Compares against database
5. **Alert System** → Notifies if blacklisted plate found
6. **Database Logging** → Records all events

## 🚨 Alert Configuration

### Blacklist Alerts
When a blacklisted plate is detected:
- **Immediate notification** sent to system
- **Email alerts** (if configured)
- **Dashboard alerts** in real-time
- **Event logging** with timestamp and camera ID

### Alert Channels
- Web dashboard notifications
- Email notifications
- SMS (if configured)
- Webhook integrations

## 📊 Supported Camera Brands

### Tested Compatible Cameras
- **Hikvision** - DS-2CD2xxx series
- **Dahua** - IPC-HFW series  
- **Axis** - P1xxx series
- **FLIR** - C series
- **Generic IP cameras** with FTP upload capability

### Configuration Examples

#### Hikvision Configuration
1. Web interface → Configuration → Network → FTP
2. Set FTP server details as above
3. Enable "Upload picture when motion detection"
4. Set picture quality to "High"

#### Dahua Configuration  
1. Web interface → Setup → Network → FTP
2. Configure server settings
3. Setup → Event → Motion Detection → FTP Upload
4. Enable "Snapshot" on motion events

## 🔧 Advanced Configuration

### Custom Upload Directories
Organize uploads by camera location:
```python
# Modify ftp_server.py to create subdirectories
upload_dir = os.path.join(os.getcwd(), "lpr_uploads", camera_location)
```

### Processing Filters
Configure which files to process:
- File size limits
- Image format restrictions  
- Time-based filtering
- Camera-specific rules

### Performance Optimization
- **Batch processing** for high-volume cameras
- **Image compression** before processing
- **Parallel recognition** for multiple cameras
- **Database connection pooling**

## 🐛 Troubleshooting

### Common Issues

#### FTP Connection Failed
- Check firewall settings (port 21)
- Verify network connectivity
- Confirm username/password
- Test with FTP client first

#### Images Not Processing
- Check file permissions in upload directory
- Verify image format compatibility
- Monitor server logs for errors
- Ensure Flask backend is running

#### Poor Recognition Accuracy
- Increase image resolution
- Improve camera positioning
- Adjust lighting conditions
- Clean camera lens regularly

### Debug Commands
```bash
# Test FTP connection
telnet your-server-ip 21

# Check upload directory
ls -la lpr_uploads/

# Monitor real-time logs
tail -f ftp_server.log

# Test API endpoint
curl -X POST http://localhost:5000/api/lpr/recognize -F "image=@test.jpg"
```

## 📈 Monitoring & Analytics

### Dashboard Metrics
- Upload success rate
- Recognition accuracy
- Alert frequency
- Camera status monitoring

### Performance Monitoring
- Processing time per image
- Queue length
- Error rates
- Storage usage

## 🔒 Security Considerations

### FTP Security
- Use strong passwords
- Limit FTP user permissions
- Consider SFTP for encryption
- Regular password rotation

### Network Security
- VPN access for remote cameras
- Firewall rules for FTP port
- Network segmentation
- Access logging

## 📞 Support

### Log Files
- FTP Server: `ftp_server.log`
- Flask Backend: `app.log`
- Recognition: Check console output

### Contact Information
For technical support with LPR camera integration:
- Check system logs first
- Test individual components
- Verify network connectivity
- Review camera documentation

---

🎯 **Quick Start Checklist:**
- [ ] Install dependencies (`pip install -r ftp_requirements.txt`)
- [ ] Configure `.env` file with FTP settings
- [ ] Start LPR system (`python start_lpr_system.py`)
- [ ] Configure camera FTP upload settings
- [ ] Test with sample image upload
- [ ] Verify recognition in dashboard
- [ ] Set up blacklist alerts
- [ ] Monitor system performance