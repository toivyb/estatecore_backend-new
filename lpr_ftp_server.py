"""
FTP Server for License Plate Recognition
Monitors FTP uploads from cameras and processes images for LPR
"""

import os
import time
import threading
import json
from datetime import datetime
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import requests
from lpr_recognizer import recognize_plate

class LPRFTPHandler(FTPHandler):
    """Custom FTP handler that processes uploaded images"""
    
    def on_file_received(self, file_path):
        """Called when a file upload is completed"""
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            print(f"[FTP] New image received: {file_path}")
            # Process in background thread to avoid blocking FTP
            thread = threading.Thread(target=self.process_image, args=(file_path,))
            thread.daemon = True
            thread.start()
    
    def process_image(self, image_path):
        """Process uploaded image for license plate recognition"""
        try:
            # Extract camera info from path
            camera_id = self.extract_camera_id(image_path)
            
            # Recognize license plate
            api_key = os.environ.get("OPENALPR_API_KEY", "")
            plate, confidence = recognize_plate(image_path, api_key)
            
            if plate and confidence > 70:  # Minimum confidence threshold
                print(f"[LPR] Plate detected: {plate} (confidence: {confidence}%)")
                
                # Check blacklist
                is_blacklisted = self.check_blacklist(plate)
                
                # Log event
                event_data = {
                    'plate': plate,
                    'confidence': confidence,
                    'camera_id': camera_id,
                    'image_path': image_path,
                    'timestamp': datetime.utcnow().isoformat(),
                    'is_blacklisted': is_blacklisted
                }
                
                # Send to backend
                self.log_event(event_data)
                
                # Send notification if blacklisted
                if is_blacklisted:
                    self.send_blacklist_notification(event_data)
                    
            else:
                print(f"[LPR] No valid plate detected in {image_path}")
                
        except Exception as e:
            print(f"[ERROR] Processing image {image_path}: {str(e)}")
    
    def extract_camera_id(self, file_path):
        """Extract camera ID from file path or filename"""
        # Example: /cameras/cam001/image.jpg -> cam001
        path_parts = file_path.replace('\\', '/').split('/')
        for part in path_parts:
            if part.startswith('cam') or part.startswith('camera'):
                return part
        return 'unknown'
    
    def check_blacklist(self, plate):
        """Check if plate is on blacklist"""
        try:
            response = requests.get(
                'http://localhost:5000/api/lpr/blacklist/check',
                params={'plate': plate},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('is_blacklisted', False)
        except Exception as e:
            print(f"[ERROR] Checking blacklist: {str(e)}")
        return False
    
    def log_event(self, event_data):
        """Log LPR event to backend"""
        try:
            response = requests.post(
                'http://localhost:5000/api/lpr/events',
                json=event_data,
                timeout=5
            )
            if response.status_code == 201:
                print(f"[LOG] Event logged successfully")
            else:
                print(f"[ERROR] Failed to log event: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Logging event: {str(e)}")
    
    def send_blacklist_notification(self, event_data):
        """Send notification for blacklisted plate"""
        try:
            notification_data = {
                'type': 'blacklist_alert',
                'plate': event_data['plate'],
                'camera_id': event_data['camera_id'],
                'timestamp': event_data['timestamp'],
                'confidence': event_data['confidence']
            }
            
            response = requests.post(
                'http://localhost:5000/api/notifications/send',
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"[ALERT] Blacklist notification sent for plate: {event_data['plate']}")
            else:
                print(f"[ERROR] Failed to send notification: {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Sending notification: {str(e)}")


def start_ftp_server(host='0.0.0.0', port=21):
    """Start the FTP server for camera uploads"""
    
    # Create upload directories
    upload_dir = os.path.join(os.getcwd(), 'ftp_uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Set up FTP authorizer
    authorizer = DummyAuthorizer()
    
    # Add camera users (you can configure these)
    camera_users = [
        {'username': 'cam001', 'password': 'cam001pass', 'homedir': os.path.join(upload_dir, 'cam001')},
        {'username': 'cam002', 'password': 'cam002pass', 'homedir': os.path.join(upload_dir, 'cam002')},
        {'username': 'cam003', 'password': 'cam003pass', 'homedir': os.path.join(upload_dir, 'cam003')},
    ]
    
    for user in camera_users:
        os.makedirs(user['homedir'], exist_ok=True)
        authorizer.add_user(
            user['username'], 
            user['password'], 
            user['homedir'], 
            perm='elradfmwMT'
        )
    
    # Add anonymous user for testing
    authorizer.add_anonymous(upload_dir)
    
    # Set up handler
    handler = LPRFTPHandler
    handler.authorizer = authorizer
    handler.banner = "EstateCore LPR FTP Server Ready"
    
    # Start server
    server = FTPServer((host, port), handler)
    server.max_cons = 256
    server.max_cons_per_ip = 5
    
    print(f"[FTP] Starting LPR FTP Server on {host}:{port}")
    print(f"[FTP] Upload directory: {upload_dir}")
    print(f"[FTP] Camera users configured: {[u['username'] for u in camera_users]}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[FTP] Server stopped by user")
    finally:
        server.close_all()


if __name__ == '__main__':
    # Configuration from environment
    ftp_host = os.environ.get('LPR_FTP_HOST', '0.0.0.0')
    ftp_port = int(os.environ.get('LPR_FTP_PORT', '21'))
    
    start_ftp_server(ftp_host, ftp_port)