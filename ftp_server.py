#!/usr/bin/env python3
"""
FTP Server for LPR Camera Integration
Receives images from LPR cameras and processes them automatically
"""
import os
import sys
import threading
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pathlib import Path
import json
import requests
from datetime import datetime
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LPRImageHandler(FileSystemEventHandler):
    """Handles new image files uploaded via FTP"""
    
    def __init__(self, api_base_url="http://localhost:5000"):
        self.api_base_url = api_base_url
        self.processed_files = set()
        
    def on_created(self, event):
        """Process new image files"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        filename = os.path.basename(file_path)
        
        # Only process image files
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            return
            
        # Avoid processing the same file multiple times
        if file_path in self.processed_files:
            return
            
        print(f"🔍 Processing new LPR image: {filename}")
        
        # Wait a moment for file to be fully written
        import time
        time.sleep(1)
        
        try:
            self.process_lpr_image(file_path)
            self.processed_files.add(file_path)
        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
    
    def process_lpr_image(self, file_path):
        """Send image to LPR recognition API"""
        try:
            # Extract metadata from filename if available
            filename = os.path.basename(file_path)
            camera_id = self.extract_camera_id(filename)
            
            # Send to LPR recognition API
            with open(file_path, 'rb') as image_file:
                files = {'image': image_file}
                data = {
                    'camera_id': camera_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'ftp_upload'
                }
                
                response = requests.post(
                    f"{self.api_base_url}/api/lpr/ai-recognize",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ LPR Recognition completed for {filename}")
                    
                    # Log results if plates found
                    if result.get('success') and result.get('results'):
                        for plate_result in result['results']:
                            plate = plate_result['plate']
                            confidence = plate_result['confidence']
                            print(f"   📋 Detected: {plate} (confidence: {confidence:.2f})")
                            
                            # Check if blacklisted
                            if plate_result.get('is_blacklisted'):
                                print(f"   🚨 ALERT: {plate} is BLACKLISTED!")
                                self.send_alert(plate, camera_id, file_path, plate_result.get('blacklist_reason'))
                    else:
                        print(f"   ℹ️ No plates detected in {filename}")
                        
                else:
                    print(f"❌ LPR API error: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error in LPR processing: {str(e)}")
    
    def extract_camera_id(self, filename):
        """Extract camera ID from filename"""
        # Common patterns:
        # camera1_20231201_120000.jpg
        # cam_001_image.jpg
        # lpr_camera_5_capture.png
        
        parts = filename.lower().split('_')
        for part in parts:
            if 'cam' in part or 'camera' in part:
                # Extract number after 'cam' or 'camera'
                import re
                numbers = re.findall(r'\d+', part)
                if numbers:
                    return f"camera_{numbers[0]}"
        
        # Default if no camera ID found
        return "camera_unknown"
    
    def send_alert(self, plate, camera_id, image_path, reason):
        """Send alert for blacklisted plate"""
        try:
            alert_data = {
                'type': 'blacklist_alert',
                'plate': plate,
                'camera_id': camera_id,
                'timestamp': datetime.utcnow().isoformat(),
                'image_path': image_path,
                'reason': reason,
                'priority': 'high'
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/notifications/send",
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"🚨 Alert sent for blacklisted plate: {plate}")
            else:
                print(f"❌ Failed to send alert: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending alert: {str(e)}")

class CustomFTPHandler(FTPHandler):
    """Custom FTP handler with logging"""
    
    def on_connect(self):
        print(f"🔗 FTP connection from {self.remote_ip}")
    
    def on_disconnect(self):
        print(f"❌ FTP disconnection from {self.remote_ip}")
    
    def on_login(self, username):
        print(f"👤 FTP login: {username} from {self.remote_ip}")
    
    def on_file_received(self, file):
        print(f"📁 File uploaded: {file}")

def setup_ftp_server():
    """Configure and start FTP server"""
    
    # Create upload directory
    upload_dir = os.path.join(os.getcwd(), "lpr_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Configure authorizer (users and permissions)
    authorizer = DummyAuthorizer()
    
    # Add users from environment or use defaults
    ftp_users = [
        {
            'username': os.environ.get('FTP_USERNAME', 'lpr_camera'),
            'password': os.environ.get('FTP_PASSWORD', 'CameraUpload123!'),
            'homedir': upload_dir,
            'perm': 'elradfmwMT'  # Full permissions
        },
        {
            'username': 'lpr_admin',
            'password': os.environ.get('FTP_ADMIN_PASSWORD', 'AdminAccess456!'),
            'homedir': upload_dir,
            'perm': 'elradfmwMT'
        }
    ]
    
    for user in ftp_users:
        authorizer.add_user(
            user['username'],
            user['password'], 
            user['homedir'],
            perm=user['perm']
        )
        print(f"✅ Added FTP user: {user['username']}")
    
    # Configure handler
    handler = CustomFTPHandler
    handler.authorizer = authorizer
    handler.banner = "EstateCore LPR FTP Server Ready"
    
    # Security settings
    handler.max_cons = 256
    handler.max_cons_per_ip = 5
    handler.passive_ports = range(60000, 65535)
    
    # Configure server
    ftp_host = os.environ.get('FTP_HOST', '0.0.0.0')
    ftp_port = int(os.environ.get('FTP_PORT', '21'))
    
    server = FTPServer((ftp_host, ftp_port), handler)
    
    print(f"🚀 FTP Server starting on {ftp_host}:{ftp_port}")
    print(f"📁 Upload directory: {upload_dir}")
    print(f"👥 FTP Users configured: {len(ftp_users)}")
    
    return server, upload_dir

def start_file_watcher(upload_dir):
    """Start file system watcher for automatic processing"""
    event_handler = LPRImageHandler()
    observer = Observer()
    observer.schedule(event_handler, upload_dir, recursive=True)
    observer.start()
    
    print(f"👀 File watcher started for: {upload_dir}")
    return observer

def main():
    """Main function to start FTP server and file watcher"""
    print("🏢 EstateCore LPR FTP Server")
    print("=" * 50)
    
    try:
        # Start FTP server
        ftp_server, upload_dir = setup_ftp_server()
        
        # Start file watcher in separate thread
        observer = start_file_watcher(upload_dir)
        
        # Start FTP server (blocking)
        print("✅ FTP Server is running...")
        print("📋 Camera Upload Instructions:")
        print(f"   Host: {os.environ.get('FTP_HOST', 'your-server-ip')}")
        print(f"   Port: {os.environ.get('FTP_PORT', '21')}")
        print(f"   Username: {os.environ.get('FTP_USERNAME', 'lpr_camera')}")
        print(f"   Password: {os.environ.get('FTP_PASSWORD', 'CameraUpload123!')}")
        print("   Directory: / (root)")
        print("\n🔄 Automatic LPR processing enabled")
        print("⏹️  Press Ctrl+C to stop")
        
        ftp_server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down FTP server...")
        if 'observer' in locals():
            observer.stop()
            observer.join()
        if 'ftp_server' in locals():
            ftp_server.close_all()
        print("✅ FTP server stopped")
        
    except Exception as e:
        print(f"❌ FTP server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()