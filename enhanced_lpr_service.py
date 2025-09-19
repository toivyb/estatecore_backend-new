"""
Enhanced License Plate Recognition Service for EstateCore
Advanced LPR integration with multiple camera systems and AI processing
"""

import os
import time
import logging
import json
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import sqlite3
import base64
import requests
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LPRProvider(Enum):
    """LPR service providers"""
    OPENALPR = "openalpr"
    PLATERECOGNIZER = "platerecognizer"
    SIGHTHOUND = "sighthound"
    CUSTOM_AI = "custom_ai"
    MOCK = "mock"

class CameraType(Enum):
    """Camera types"""
    ENTRANCE = "entrance"
    EXIT = "exit"
    PARKING = "parking"
    PERIMETER = "perimeter"
    GENERAL = "general"

class AccessAction(Enum):
    """Access control actions"""
    ALLOW = "allow"
    DENY = "deny"
    ALERT = "alert"
    LOG_ONLY = "log_only"

class VehicleStatus(Enum):
    """Vehicle status in system"""
    AUTHORIZED = "authorized"
    VISITOR = "visitor"
    BLACKLISTED = "blacklisted"
    UNKNOWN = "unknown"
    EXPIRED = "expired"

@dataclass
class LPRCamera:
    """LPR Camera configuration"""
    id: str
    name: str
    location: str
    camera_type: CameraType
    rtsp_url: str
    property_id: int
    provider: LPRProvider
    confidence_threshold: float = 0.8
    is_active: bool = True
    settings: Dict = field(default_factory=dict)
    last_detection: Optional[datetime] = None
    total_detections: int = 0

@dataclass
class LPRDetection:
    """LPR detection result"""
    id: str
    camera_id: str
    license_plate: str
    confidence: float
    timestamp: datetime
    image_path: Optional[str]
    property_id: int
    vehicle_status: VehicleStatus
    access_action: AccessAction
    coordinates: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

@dataclass
class VehicleRecord:
    """Vehicle record in system"""
    license_plate: str
    owner_name: Optional[str]
    tenant_id: Optional[int]
    property_id: int
    status: VehicleStatus
    valid_from: datetime
    valid_until: Optional[datetime]
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class MockLPRProcessor:
    """Mock LPR processor for testing"""
    
    def __init__(self):
        self.mock_plates = [
            "ABC123", "XYZ789", "DEF456", "GHI321", "JKL654",
            "MNO987", "PQR111", "STU222", "VWX333", "YZA444"
        ]
        self.detection_count = 0
    
    def process_frame(self, frame, confidence_threshold: float = 0.8) -> List[Dict]:
        """Process frame and return mock detections"""
        # Simulate processing time
        time.sleep(0.1)
        
        # Randomly detect plates
        import random
        detections = []
        
        if random.random() < 0.3:  # 30% chance of detection
            plate = random.choice(self.mock_plates)
            confidence = random.uniform(0.7, 0.99)
            
            if confidence >= confidence_threshold:
                detections.append({
                    'plate': plate,
                    'confidence': confidence,
                    'coordinates': {
                        'x': random.randint(50, 200),
                        'y': random.randint(50, 150),
                        'width': random.randint(80, 120),
                        'height': random.randint(20, 40)
                    }
                })
        
        self.detection_count += 1
        return detections

class EnhancedLPRService:
    """Enhanced License Plate Recognition Service"""
    
    def __init__(self, db_path: str = "lpr_database.db"):
        self.db_path = db_path
        self.cameras = {}
        self.vehicle_records = {}
        self.detections = []
        self.active_streams = {}
        self.processors = {}
        
        # Threading
        self.camera_threads = {}
        self.is_running = False
        self.detection_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'authorized_vehicles': 0,
            'unauthorized_vehicles': 0,
            'alerts_generated': 0,
            'cameras_active': 0
        }
        
        # Initialize database
        self._init_database()
        
        # Initialize processors
        self._init_processors()
        
        logger.info("Enhanced LPR Service initialized")
    
    def _init_database(self):
        """Initialize LPR database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cameras (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location TEXT,
                    camera_type TEXT,
                    rtsp_url TEXT,
                    property_id INTEGER,
                    provider TEXT,
                    confidence_threshold REAL,
                    is_active BOOLEAN,
                    settings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicle_records (
                    license_plate TEXT PRIMARY KEY,
                    owner_name TEXT,
                    tenant_id INTEGER,
                    property_id INTEGER,
                    status TEXT,
                    valid_from TIMESTAMP,
                    valid_until TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id TEXT PRIMARY KEY,
                    camera_id TEXT,
                    license_plate TEXT,
                    confidence REAL,
                    timestamp TIMESTAMP,
                    image_path TEXT,
                    property_id INTEGER,
                    vehicle_status TEXT,
                    access_action TEXT,
                    coordinates TEXT,
                    metadata TEXT,
                    FOREIGN KEY (camera_id) REFERENCES cameras (id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_detections_plate ON detections(license_plate)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("LPR database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LPR database: {e}")
    
    def _init_processors(self):
        """Initialize LPR processors"""
        # For now, we'll use mock processor
        # In production, you would initialize actual LPR SDKs here
        self.processors[LPRProvider.MOCK] = MockLPRProcessor()
        
        # Example of how to add real processors:
        # self.processors[LPRProvider.OPENALPR] = OpenALPRProcessor()
        # self.processors[LPRProvider.PLATERECOGNIZER] = PlateRecognizerProcessor()
        
        logger.info("LPR processors initialized")
    
    def add_camera(self, camera: LPRCamera) -> bool:
        """Add new LPR camera"""
        try:
            # Store in memory
            self.cameras[camera.id] = camera
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cameras 
                (id, name, location, camera_type, rtsp_url, property_id, provider, 
                 confidence_threshold, is_active, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                camera.id, camera.name, camera.location, camera.camera_type.value,
                camera.rtsp_url, camera.property_id, camera.provider.value,
                camera.confidence_threshold, camera.is_active, json.dumps(camera.settings)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added camera: {camera.name} ({camera.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add camera: {e}")
            return False
    
    def add_vehicle_record(self, vehicle: VehicleRecord) -> bool:
        """Add vehicle record"""
        try:
            # Store in memory
            self.vehicle_records[vehicle.license_plate] = vehicle
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO vehicle_records 
                (license_plate, owner_name, tenant_id, property_id, status, 
                 valid_from, valid_until, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vehicle.license_plate, vehicle.owner_name, vehicle.tenant_id,
                vehicle.property_id, vehicle.status.value, vehicle.valid_from,
                vehicle.valid_until, vehicle.notes, datetime.utcnow()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added vehicle record: {vehicle.license_plate}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vehicle record: {e}")
            return False
    
    def start_camera_monitoring(self, camera_id: str) -> bool:
        """Start monitoring specific camera"""
        try:
            if camera_id not in self.cameras:
                logger.error(f"Camera {camera_id} not found")
                return False
            
            camera = self.cameras[camera_id]
            if not camera.is_active:
                logger.warning(f"Camera {camera_id} is not active")
                return False
            
            # Start camera thread
            if camera_id not in self.camera_threads or not self.camera_threads[camera_id].is_alive():
                thread = threading.Thread(
                    target=self._monitor_camera,
                    args=(camera,),
                    daemon=True
                )
                thread.start()
                self.camera_threads[camera_id] = thread
                
                logger.info(f"Started monitoring camera: {camera.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start camera monitoring: {e}")
            return False
    
    def _monitor_camera(self, camera: LPRCamera):
        """Monitor camera for license plate detections"""
        try:
            processor = self.processors.get(camera.provider)
            if not processor:
                logger.error(f"No processor available for provider: {camera.provider}")
                return
            
            # For mock implementation, we'll simulate camera frames
            frame_count = 0
            
            while self.is_running and camera.is_active:
                try:
                    # In production, this would capture from RTSP stream:
                    # cap = cv2.VideoCapture(camera.rtsp_url)
                    # ret, frame = cap.read()
                    
                    # For now, create a mock frame
                    if CV2_AVAILABLE:
                        frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    else:
                        frame = None  # Mock frame when CV2 not available
                    frame_count += 1
                    
                    # Process frame for license plates
                    detections = processor.process_frame(frame, camera.confidence_threshold)
                    
                    # Handle detections
                    for detection in detections:
                        self._handle_detection(camera, detection, frame)
                    
                    # Update camera stats
                    camera.last_detection = datetime.utcnow()
                    camera.total_detections += len(detections)
                    
                    # Sleep to simulate frame rate
                    time.sleep(1.0 / 10)  # 10 FPS
                    
                except Exception as e:
                    logger.error(f"Error processing camera {camera.id}: {e}")
                    time.sleep(5)  # Wait before retrying
            
        except Exception as e:
            logger.error(f"Camera monitoring failed for {camera.id}: {e}")
    
    def _handle_detection(self, camera: LPRCamera, detection: Dict, frame):
        """Handle license plate detection"""
        try:
            license_plate = self._clean_license_plate(detection['plate'])
            
            # Check vehicle status
            vehicle_status = self._get_vehicle_status(license_plate, camera.property_id)
            access_action = self._determine_access_action(vehicle_status, camera)
            
            # Create detection record
            detection_id = f"det_{int(time.time() * 1000)}"
            
            # Save frame image (in production, you'd save actual frame)
            image_path = f"detections/{detection_id}.jpg"
            
            lpr_detection = LPRDetection(
                id=detection_id,
                camera_id=camera.id,
                license_plate=license_plate,
                confidence=detection['confidence'],
                timestamp=datetime.utcnow(),
                image_path=image_path,
                property_id=camera.property_id,
                vehicle_status=vehicle_status,
                access_action=access_action,
                coordinates=detection['coordinates'],
                metadata={
                    'camera_name': camera.name,
                    'camera_location': camera.location,
                    'frame_number': camera.total_detections + 1
                }
            )
            
            # Store detection
            self._store_detection(lpr_detection)
            
            # Handle access control
            self._handle_access_control(lpr_detection)
            
            # Update statistics
            with self.detection_lock:
                self.stats['total_detections'] += 1
                if vehicle_status == VehicleStatus.AUTHORIZED:
                    self.stats['authorized_vehicles'] += 1
                else:
                    self.stats['unauthorized_vehicles'] += 1
            
            logger.info(f"Detected: {license_plate} ({vehicle_status.value}) - {access_action.value}")
            
        except Exception as e:
            logger.error(f"Failed to handle detection: {e}")
    
    def _clean_license_plate(self, plate: str) -> str:
        """Clean and normalize license plate text"""
        # Remove non-alphanumeric characters and convert to uppercase
        cleaned = re.sub(r'[^A-Z0-9]', '', plate.upper())
        return cleaned
    
    def _get_vehicle_status(self, license_plate: str, property_id: int) -> VehicleStatus:
        """Get vehicle status from records"""
        try:
            vehicle = self.vehicle_records.get(license_plate)
            
            if not vehicle:
                return VehicleStatus.UNKNOWN
            
            if vehicle.property_id != property_id:
                return VehicleStatus.UNKNOWN
            
            # Check if vehicle record is still valid
            now = datetime.utcnow()
            if vehicle.valid_until and now > vehicle.valid_until:
                return VehicleStatus.EXPIRED
            
            return vehicle.status
            
        except Exception as e:
            logger.error(f"Failed to get vehicle status: {e}")
            return VehicleStatus.UNKNOWN
    
    def _determine_access_action(self, vehicle_status: VehicleStatus, camera: LPRCamera) -> AccessAction:
        """Determine access control action based on vehicle status"""
        if vehicle_status == VehicleStatus.BLACKLISTED:
            return AccessAction.DENY
        elif vehicle_status == VehicleStatus.AUTHORIZED:
            return AccessAction.ALLOW
        elif vehicle_status in [VehicleStatus.UNKNOWN, VehicleStatus.EXPIRED]:
            if camera.camera_type in [CameraType.ENTRANCE, CameraType.EXIT]:
                return AccessAction.ALERT
            else:
                return AccessAction.LOG_ONLY
        elif vehicle_status == VehicleStatus.VISITOR:
            return AccessAction.ALERT
        else:
            return AccessAction.LOG_ONLY
    
    def _store_detection(self, detection: LPRDetection):
        """Store detection in database"""
        try:
            # Store in memory
            self.detections.append(detection)
            
            # Keep only last 1000 detections in memory
            if len(self.detections) > 1000:
                self.detections = self.detections[-1000:]
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO detections 
                (id, camera_id, license_plate, confidence, timestamp, image_path,
                 property_id, vehicle_status, access_action, coordinates, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                detection.id, detection.camera_id, detection.license_plate,
                detection.confidence, detection.timestamp, detection.image_path,
                detection.property_id, detection.vehicle_status.value,
                detection.access_action.value, json.dumps(detection.coordinates),
                json.dumps(detection.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store detection: {e}")
    
    def _handle_access_control(self, detection: LPRDetection):
        """Handle access control actions"""
        try:
            if detection.access_action == AccessAction.DENY:
                self._trigger_security_alert(detection, "DENIED ACCESS")
                self._log_security_event(detection, "Access denied for blacklisted vehicle")
                
            elif detection.access_action == AccessAction.ALERT:
                self._trigger_security_alert(detection, "UNKNOWN VEHICLE")
                self._log_security_event(detection, "Unknown vehicle detected")
                
            elif detection.access_action == AccessAction.ALLOW:
                self._log_security_event(detection, "Authorized vehicle access")
                
            # In production, you would integrate with physical access control systems:
            # - Open/close gates
            # - Turn on/off barrier lights
            # - Send signals to security systems
            
        except Exception as e:
            logger.error(f"Failed to handle access control: {e}")
    
    def _trigger_security_alert(self, detection: LPRDetection, alert_type: str):
        """Trigger security alert"""
        try:
            alert_data = {
                'type': alert_type,
                'license_plate': detection.license_plate,
                'camera': detection.camera_id,
                'timestamp': detection.timestamp.isoformat(),
                'confidence': detection.confidence,
                'property_id': detection.property_id
            }
            
            # Update stats
            with self.detection_lock:
                self.stats['alerts_generated'] += 1
            
            # In production, you would:
            # - Send notifications to security personnel
            # - Trigger alarms or lights
            # - Send emails/SMS to property managers
            # - Update security dashboard in real-time
            
            logger.warning(f"SECURITY ALERT: {alert_type} - {detection.license_plate}")
            
        except Exception as e:
            logger.error(f"Failed to trigger security alert: {e}")
    
    def _log_security_event(self, detection: LPRDetection, message: str):
        """Log security event"""
        try:
            # In production, integrate with main security logging system
            security_event = {
                'event_type': 'LPR_DETECTION',
                'message': message,
                'license_plate': detection.license_plate,
                'camera_id': detection.camera_id,
                'timestamp': detection.timestamp.isoformat(),
                'property_id': detection.property_id
            }
            
            logger.info(f"Security Event: {message} - {detection.license_plate}")
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def start_all_cameras(self) -> Dict[str, bool]:
        """Start monitoring all active cameras"""
        results = {}
        self.is_running = True
        
        for camera_id, camera in self.cameras.items():
            if camera.is_active:
                results[camera_id] = self.start_camera_monitoring(camera_id)
        
        with self.detection_lock:
            self.stats['cameras_active'] = len([r for r in results.values() if r])
        
        logger.info(f"Started {sum(results.values())} cameras")
        return results
    
    def stop_all_cameras(self):
        """Stop all camera monitoring"""
        self.is_running = False
        
        for thread in self.camera_threads.values():
            if thread.is_alive():
                thread.join(timeout=5.0)
        
        self.camera_threads.clear()
        
        with self.detection_lock:
            self.stats['cameras_active'] = 0
        
        logger.info("Stopped all camera monitoring")
    
    def get_recent_detections(self, hours: int = 24, property_id: Optional[int] = None) -> List[Dict]:
        """Get recent detections"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.utcnow() - timedelta(hours=hours)
            
            if property_id:
                cursor.execute('''
                    SELECT * FROM detections 
                    WHERE timestamp > ? AND property_id = ?
                    ORDER BY timestamp DESC
                ''', (since, property_id))
            else:
                cursor.execute('''
                    SELECT * FROM detections 
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                ''', (since,))
            
            detections = []
            for row in cursor.fetchall():
                detections.append({
                    'id': row[0],
                    'camera_id': row[1],
                    'license_plate': row[2],
                    'confidence': row[3],
                    'timestamp': row[4],
                    'image_path': row[5],
                    'property_id': row[6],
                    'vehicle_status': row[7],
                    'access_action': row[8],
                    'coordinates': json.loads(row[9]) if row[9] else {},
                    'metadata': json.loads(row[10]) if row[10] else {}
                })
            
            conn.close()
            return detections
            
        except Exception as e:
            logger.error(f"Failed to get recent detections: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get LPR system statistics"""
        try:
            with self.detection_lock:
                stats = self.stats.copy()
            
            # Add camera statistics
            stats['total_cameras'] = len(self.cameras)
            stats['active_cameras'] = len([c for c in self.cameras.values() if c.is_active])
            
            # Add vehicle statistics
            stats['total_vehicle_records'] = len(self.vehicle_records)
            stats['authorized_vehicles_count'] = len([v for v in self.vehicle_records.values() 
                                                    if v.status == VehicleStatus.AUTHORIZED])
            stats['blacklisted_vehicles_count'] = len([v for v in self.vehicle_records.values() 
                                                     if v.status == VehicleStatus.BLACKLISTED])
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def search_detections(self, license_plate: str = None, camera_id: str = None,
                         start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Search detections with filters"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM detections WHERE 1=1"
            params = []
            
            if license_plate:
                query += " AND license_plate LIKE ?"
                params.append(f"%{license_plate}%")
            
            if camera_id:
                query += " AND camera_id = ?"
                params.append(camera_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'camera_id': row[1],
                    'license_plate': row[2],
                    'confidence': row[3],
                    'timestamp': row[4],
                    'image_path': row[5],
                    'property_id': row[6],
                    'vehicle_status': row[7],
                    'access_action': row[8],
                    'coordinates': json.loads(row[9]) if row[9] else {},
                    'metadata': json.loads(row[10]) if row[10] else {}
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to search detections: {e}")
            return []

# Singleton instance
_enhanced_lpr_service = None

def get_enhanced_lpr_service() -> EnhancedLPRService:
    """Get singleton enhanced LPR service instance"""
    global _enhanced_lpr_service
    if _enhanced_lpr_service is None:
        _enhanced_lpr_service = EnhancedLPRService()
    return _enhanced_lpr_service

if __name__ == "__main__":
    # Test the enhanced LPR service
    service = get_enhanced_lpr_service()
    
    print("📷 Enhanced LPR Service Test")
    
    # Add test camera
    camera = LPRCamera(
        id="cam_001",
        name="Main Entrance Camera",
        location="Property Entrance",
        camera_type=CameraType.ENTRANCE,
        rtsp_url="rtsp://192.168.1.100:554/stream",
        property_id=1,
        provider=LPRProvider.MOCK,
        confidence_threshold=0.8
    )
    
    service.add_camera(camera)
    print(f"Added camera: {camera.name}")
    
    # Add test vehicle records
    authorized_vehicle = VehicleRecord(
        license_plate="ABC123",
        owner_name="John Doe",
        tenant_id=1,
        property_id=1,
        status=VehicleStatus.AUTHORIZED,
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=365)
    )
    
    blacklisted_vehicle = VehicleRecord(
        license_plate="XYZ999",
        owner_name="Unknown",
        tenant_id=None,
        property_id=1,
        status=VehicleStatus.BLACKLISTED,
        valid_from=datetime.utcnow(),
        valid_until=None,
        notes="Security concern"
    )
    
    service.add_vehicle_record(authorized_vehicle)
    service.add_vehicle_record(blacklisted_vehicle)
    print("Added vehicle records")
    
    # Start monitoring
    print("Starting camera monitoring...")
    service.start_all_cameras()
    
    # Let it run for a few seconds
    time.sleep(10)
    
    # Get statistics
    stats = service.get_statistics()
    print(f"Statistics: {stats}")
    
    # Get recent detections
    detections = service.get_recent_detections(hours=1)
    print(f"Recent detections: {len(detections)}")
    
    # Stop monitoring
    service.stop_all_cameras()
    
    print("✅ Enhanced LPR service test completed!")