#!/usr/bin/env python3
"""
EstateCore LPR System Startup Script
Runs both Flask backend and FTP server for complete LPR integration
"""
import subprocess
import threading
import time
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def start_flask_backend():
    """Start Flask backend server"""
    print("🚀 Starting Flask Backend...")
    try:
        subprocess.run([sys.executable, "app.py"], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("⏹️  Flask backend stopped")
    except Exception as e:
        print(f"❌ Flask backend error: {e}")

def start_ftp_server():
    """Start FTP server for camera uploads"""
    print("📁 Starting FTP Server...")
    try:
        subprocess.run([sys.executable, "ftp_server.py"], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("⏹️  FTP server stopped")
    except Exception as e:
        print(f"❌ FTP server error: {e}")

def main():
    """Main function to start both services"""
    print("🏢 EstateCore LPR Complete System Startup")
    print("=" * 50)
    
    # Start Flask backend in thread
    flask_thread = threading.Thread(target=start_flask_backend, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    time.sleep(3)
    
    # Start FTP server in main thread (blocking)
    try:
        start_ftp_server()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down LPR system...")
        print("✅ System stopped")

if __name__ == "__main__":
    main()