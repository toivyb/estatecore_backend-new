#!/usr/bin/env python3
"""
Live Camera Analysis System for EstateCore Phase 6
Real-time computer vision analysis from camera feeds for instant property assessment
"""

import os
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available, Live Camera Analysis will use simplified mode")
import threading
import queue
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Import our existing CV modules
from .property_analyzer import PropertyImageAnalyzer, PropertyAnalysis, get_property_analyzer
from .damage_detector import AdvancedDamageDetector, DamageAssessment, get_damage_detector
from .image_processor import ImageProcessor, get_image_processor

class CameraType(Enum):
    WEBCAM = "webcam"
    IP_CAMERA = "ip_camera"
    USB_CAMERA = "usb_camera"
    PHONE_CAMERA = "phone_camera"
    SECURITY_CAMERA = "security_camera"

class AnalysisMode(Enum):
    CONTINUOUS = "continuous"        # Analyze every frame
    INTERVAL = "interval"           # Analyze at set intervals
    MOTION_TRIGGER = "motion_trigger"  # Analyze when motion detected
    MANUAL_CAPTURE = "manual_capture"  # Analyze on button press

class StreamQuality(Enum):
    LOW = "low"        # 640x480
    MEDIUM = "medium"  # 1280x720
    HIGH = "high"      # 1920x1080
    ULTRA = "ultra"    # 4K if available

@dataclass
class CameraConfig:
    """Camera configuration settings"""
    camera_id: str
    camera_type: CameraType
    source: str  # Camera index, IP address, or device path
    resolution: Tuple[int, int]
    fps: int
    auto_focus: bool
    auto_exposure: bool
    brightness: float
    contrast: float
    saturation: float
    recording_enabled: bool
    recording_path: Optional[str]

@dataclass
class LiveAnalysisFrame:
    """Single frame analysis result"""
    frame_id: str
    timestamp: datetime
    camera_id: str
    property_id: int
    frame_size: Tuple[int, int]
    
    # Computer Vision Results
    property_analysis: Optional[PropertyAnalysis]
    damage_assessment: Optional[DamageAssessment]
    
    # Detection Results
    objects_detected: List[Dict[str, Any]]
    motion_detected: bool
    motion_areas: List[Tuple[int, int, int, int]]  # Bounding boxes
    
    # Quality Metrics
    image_quality_score: float
    focus_score: float
    lighting_score: float
    
    # Processing Stats
    analysis_time: float
    confidence_score: float

@dataclass
class LiveStreamStats:
    """Live stream statistics"""
    stream_id: str
    start_time: datetime
    total_frames_processed: int
    analysis_count: int
    average_fps: float
    average_analysis_time: float
    total_detections: int
    quality_issues_detected: int
    motion_events: int
    current_status: str

class LiveCameraAnalyzer:
    """Real-time camera analysis system with computer vision"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize CV components
        self.property_analyzer = get_property_analyzer()
        self.damage_detector = get_damage_detector()
        self.image_processor = get_image_processor()
        
        # Camera management
        self.active_cameras = {}
        self.camera_threads = {}
        self.analysis_queues = {}
        self.stream_stats = {}
        
        # Motion detection
        self.background_subtractors = {}
        self.motion_thresholds = {}
        
        # Analysis callbacks
        self.analysis_callbacks = []
        self.motion_callbacks = []
        self.alert_callbacks = []
        
        # Configuration
        self.default_config = self._get_default_config()
        
        self.logger.info("LiveCameraAnalyzer initialized")

    def _get_default_config(self) -> Dict:
        """Get default camera configuration"""
        return {
            'resolution': (1280, 720),
            'fps': 30,
            'analysis_interval': 2.0,  # seconds
            'motion_threshold': 1000,  # pixels
            'quality_threshold': 50.0,
            'focus_threshold': 100.0,
            'lighting_min': 50,
            'lighting_max': 200,
            'recording_enabled': True,
            'auto_enhance': True,
            'save_analysis_frames': True
        }

    def add_camera(self, camera_config: CameraConfig, property_id: int) -> bool:
        """
        Add a new camera to the live analysis system
        """
        try:
            self.logger.info(f"Adding camera: {camera_config.camera_id}")
            
            # Initialize camera capture
            if camera_config.camera_type == CameraType.WEBCAM:
                cap = cv2.VideoCapture(int(camera_config.source))
            elif camera_config.camera_type == CameraType.IP_CAMERA:
                cap = cv2.VideoCapture(camera_config.source)
            else:
                cap = cv2.VideoCapture(camera_config.source)
            
            if not cap.isOpened():
                raise Exception(f"Could not open camera: {camera_config.source}")
            
            # Configure camera settings
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config.resolution[1])
            cap.set(cv2.CAP_PROP_FPS, camera_config.fps)
            
            if hasattr(cv2, 'CAP_PROP_BRIGHTNESS'):
                cap.set(cv2.CAP_PROP_BRIGHTNESS, camera_config.brightness)
                cap.set(cv2.CAP_PROP_CONTRAST, camera_config.contrast)
                cap.set(cv2.CAP_PROP_SATURATION, camera_config.saturation)
            
            # Store camera
            self.active_cameras[camera_config.camera_id] = {
                'capture': cap,
                'config': camera_config,
                'property_id': property_id,
                'active': True,
                'last_frame': None,
                'last_analysis': None
            }
            
            # Initialize motion detection
            self.background_subtractors[camera_config.camera_id] = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True
            )
            self.motion_thresholds[camera_config.camera_id] = self.default_config['motion_threshold']
            
            # Create analysis queue
            self.analysis_queues[camera_config.camera_id] = queue.Queue(maxsize=10)
            
            # Initialize stream stats
            self.stream_stats[camera_config.camera_id] = LiveStreamStats(
                stream_id=camera_config.camera_id,
                start_time=datetime.now(),
                total_frames_processed=0,
                analysis_count=0,
                average_fps=0.0,
                average_analysis_time=0.0,
                total_detections=0,
                quality_issues_detected=0,
                motion_events=0,
                current_status="active"
            )
            
            self.logger.info(f"Camera {camera_config.camera_id} added successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add camera {camera_config.camera_id}: {str(e)}")
            return False

    def start_live_analysis(self, camera_id: str, analysis_mode: AnalysisMode = AnalysisMode.INTERVAL) -> bool:
        """
        Start live analysis for a camera
        """
        try:
            if camera_id not in self.active_cameras:
                raise Exception(f"Camera {camera_id} not found")
            
            self.logger.info(f"Starting live analysis for camera: {camera_id}")
            
            # Create and start analysis thread
            analysis_thread = threading.Thread(
                target=self._analysis_thread,
                args=(camera_id, analysis_mode),
                daemon=True
            )
            
            self.camera_threads[camera_id] = analysis_thread
            analysis_thread.start()
            
            self.logger.info(f"Live analysis started for camera: {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start live analysis for {camera_id}: {str(e)}")
            return False

    def _analysis_thread(self, camera_id: str, analysis_mode: AnalysisMode):
        """
        Main analysis thread for live camera processing
        """
        try:
            camera_info = self.active_cameras[camera_id]
            cap = camera_info['capture']
            config = camera_info['config']
            property_id = camera_info['property_id']
            
            frame_count = 0
            last_analysis_time = 0
            fps_start_time = time.time()
            
            self.logger.info(f"Analysis thread started for camera {camera_id}")
            
            while camera_info.get('active', False):
                ret, frame = cap.read()
                if not ret:
                    self.logger.warning(f"Failed to read frame from camera {camera_id}")
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                frame_count += 1
                
                # Update FPS statistics
                if current_time - fps_start_time >= 1.0:
                    fps = frame_count / (current_time - fps_start_time)
                    self.stream_stats[camera_id].average_fps = fps
                    frame_count = 0
                    fps_start_time = current_time
                
                # Store current frame
                camera_info['last_frame'] = frame.copy()
                self.stream_stats[camera_id].total_frames_processed += 1
                
                # Determine if analysis should be performed
                should_analyze = self._should_analyze_frame(
                    camera_id, current_time, last_analysis_time, analysis_mode, frame
                )
                
                if should_analyze:
                    # Perform live analysis
                    analysis_result = self._analyze_live_frame(
                        camera_id, frame, property_id, current_time
                    )
                    
                    if analysis_result:
                        camera_info['last_analysis'] = analysis_result
                        self.stream_stats[camera_id].analysis_count += 1
                        
                        # Process callbacks
                        self._process_analysis_callbacks(analysis_result)
                        
                        # Check for alerts
                        self._check_for_alerts(analysis_result)
                    
                    last_analysis_time = current_time
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
        except Exception as e:
            self.logger.error(f"Analysis thread error for camera {camera_id}: {str(e)}")
        finally:
            self.logger.info(f"Analysis thread stopped for camera {camera_id}")

    def _should_analyze_frame(self, camera_id: str, current_time: float, 
                            last_analysis_time: float, analysis_mode: AnalysisMode, 
                            frame: np.ndarray) -> bool:
        """
        Determine if current frame should be analyzed
        """
        try:
            if analysis_mode == AnalysisMode.CONTINUOUS:
                return True
            
            elif analysis_mode == AnalysisMode.INTERVAL:
                interval = self.default_config['analysis_interval']
                return (current_time - last_analysis_time) >= interval
            
            elif analysis_mode == AnalysisMode.MOTION_TRIGGER:
                return self._detect_motion(camera_id, frame)
            
            elif analysis_mode == AnalysisMode.MANUAL_CAPTURE:
                # Check if manual capture was requested
                return self._check_manual_capture_request(camera_id)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error determining frame analysis: {str(e)}")
            return False

    def _detect_motion(self, camera_id: str, frame: np.ndarray) -> bool:
        """
        Detect motion in current frame
        """
        try:
            if camera_id not in self.background_subtractors:
                return False
            
            # Apply background subtraction
            bg_subtractor = self.background_subtractors[camera_id]
            fg_mask = bg_subtractor.apply(frame)
            
            # Count non-zero pixels (motion pixels)
            motion_pixels = cv2.countNonZero(fg_mask)
            threshold = self.motion_thresholds[camera_id]
            
            if motion_pixels > threshold:
                self.stream_stats[camera_id].motion_events += 1
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Motion detection error: {str(e)}")
            return False

    def _analyze_live_frame(self, camera_id: str, frame: np.ndarray, 
                          property_id: int, timestamp: float) -> Optional[LiveAnalysisFrame]:
        """
        Perform comprehensive analysis on a live frame
        """
        start_time = time.time()
        
        try:
            frame_id = f"{camera_id}_{int(timestamp * 1000)}"
            
            # Save frame temporarily for analysis
            temp_frame_path = f"temp_{frame_id}.jpg"
            cv2.imwrite(temp_frame_path, frame)
            
            # Enhance image if configured
            if self.default_config.get('auto_enhance', False):
                enhanced_result = self.image_processor.enhance_image_for_analysis(temp_frame_path)
                analysis_frame_path = enhanced_result.processed_image_path or temp_frame_path
            else:
                analysis_frame_path = temp_frame_path
            
            # Perform property analysis
            property_analysis = None
            if self._should_run_property_analysis(camera_id):
                try:
                    property_analysis = self.property_analyzer.analyze_property_image(
                        analysis_frame_path, property_id
                    )
                except Exception as e:
                    self.logger.error(f"Property analysis error: {str(e)}")
            
            # Perform damage assessment
            damage_assessment = None
            if self._should_run_damage_analysis(camera_id):
                try:
                    damage_assessment = self.damage_detector.assess_property_damage(
                        analysis_frame_path, property_id
                    )
                except Exception as e:
                    self.logger.error(f"Damage assessment error: {str(e)}")
            
            # Detect objects and motion
            objects_detected = self._detect_objects_in_frame(frame)
            motion_detected = self._detect_motion(camera_id, frame)
            motion_areas = self._get_motion_areas(camera_id, frame) if motion_detected else []
            
            # Calculate quality metrics
            image_quality_score = self._calculate_frame_quality(frame)
            focus_score = self._calculate_focus_score(frame)
            lighting_score = self._calculate_lighting_score(frame)
            
            # Calculate confidence
            confidence_score = self._calculate_overall_confidence(
                property_analysis, damage_assessment, image_quality_score
            )
            
            # Clean up temporary files
            try:
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)
                if analysis_frame_path != temp_frame_path and os.path.exists(analysis_frame_path):
                    os.remove(analysis_frame_path)
            except:
                pass
            
            # Create analysis result
            analysis_result = LiveAnalysisFrame(
                frame_id=frame_id,
                timestamp=datetime.fromtimestamp(timestamp),
                camera_id=camera_id,
                property_id=property_id,
                frame_size=(frame.shape[1], frame.shape[0]),
                property_analysis=property_analysis,
                damage_assessment=damage_assessment,
                objects_detected=objects_detected,
                motion_detected=motion_detected,
                motion_areas=motion_areas,
                image_quality_score=image_quality_score,
                focus_score=focus_score,
                lighting_score=lighting_score,
                analysis_time=time.time() - start_time,
                confidence_score=confidence_score
            )
            
            # Update statistics
            self.stream_stats[camera_id].average_analysis_time = (
                self.stream_stats[camera_id].average_analysis_time * 0.9 + 
                analysis_result.analysis_time * 0.1
            )
            
            if objects_detected or (property_analysis and property_analysis.features_detected):
                self.stream_stats[camera_id].total_detections += 1
            
            if image_quality_score < self.default_config['quality_threshold']:
                self.stream_stats[camera_id].quality_issues_detected += 1
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Live frame analysis error: {str(e)}")
            return None

    def _should_run_property_analysis(self, camera_id: str) -> bool:
        """Determine if property analysis should run (resource management)"""
        # Run property analysis less frequently to save resources
        stats = self.stream_stats.get(camera_id)
        if stats:
            return stats.analysis_count % 5 == 0  # Every 5th analysis
        return True

    def _should_run_damage_analysis(self, camera_id: str) -> bool:
        """Determine if damage analysis should run (resource management)"""
        # Run damage analysis even less frequently
        stats = self.stream_stats.get(camera_id)
        if stats:
            return stats.analysis_count % 10 == 0  # Every 10th analysis
        return True

    def _detect_objects_in_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect objects in frame using computer vision
        """
        objects = []
        
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Use Haar cascades for basic object detection (faces, etc.)
            # Note: In production, you'd use more advanced models like YOLO
            
            # Detect edges as potential objects
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter and classify contours as objects
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum size threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Simple object classification based on size and shape
                    aspect_ratio = w / h if h > 0 else 0
                    object_type = self._classify_object_by_shape(area, aspect_ratio)
                    
                    objects.append({
                        'id': i,
                        'type': object_type,
                        'confidence': min(area / 10000, 1.0),
                        'bounding_box': (x, y, w, h),
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
            
        except Exception as e:
            self.logger.error(f"Object detection error: {str(e)}")
        
        return objects[:20]  # Limit to top 20 objects

    def _classify_object_by_shape(self, area: float, aspect_ratio: float) -> str:
        """Simple object classification based on shape characteristics"""
        if aspect_ratio > 3:
            return "linear_object"  # Could be pipes, wires, etc.
        elif 0.8 <= aspect_ratio <= 1.2 and area > 5000:
            return "square_object"  # Could be windows, appliances
        elif area > 10000:
            return "large_object"   # Furniture, fixtures
        else:
            return "unknown_object"

    def _get_motion_areas(self, camera_id: str, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Get bounding boxes of motion areas"""
        motion_areas = []
        
        try:
            if camera_id not in self.background_subtractors:
                return motion_areas
            
            # Get motion mask
            bg_subtractor = self.background_subtractors[camera_id]
            fg_mask = bg_subtractor.apply(frame)
            
            # Find contours of motion areas
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 200:  # Minimum motion area
                    x, y, w, h = cv2.boundingRect(contour)
                    motion_areas.append((x, y, w, h))
            
        except Exception as e:
            self.logger.error(f"Motion area detection error: {str(e)}")
        
        return motion_areas

    def _calculate_frame_quality(self, frame: np.ndarray) -> float:
        """Calculate image quality score for frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate sharpness using Laplacian variance
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate brightness
            brightness = np.mean(gray)
            
            # Calculate contrast
            contrast = np.std(gray)
            
            # Normalize to 0-100 scale
            sharpness_score = min(100, (sharpness / 500) * 100)
            brightness_score = 100 - abs(brightness - 128) / 1.28
            contrast_score = min(100, (contrast / 60) * 100)
            
            # Weighted average
            quality = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            return max(0.0, min(100.0, quality))
            
        except Exception as e:
            self.logger.error(f"Quality calculation error: {str(e)}")
            return 50.0

    def _calculate_focus_score(self, frame: np.ndarray) -> float:
        """Calculate focus score using gradient magnitude"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate gradient magnitude
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Focus score is mean gradient magnitude
            focus_score = np.mean(magnitude)
            
            return min(focus_score, 255.0)  # Cap at 255
            
        except Exception as e:
            self.logger.error(f"Focus calculation error: {str(e)}")
            return 100.0

    def _calculate_lighting_score(self, frame: np.ndarray) -> float:
        """Calculate lighting quality score"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            
            # Optimal lighting around 128 (mid-gray)
            lighting_score = 100 - abs(mean_brightness - 128) / 1.28
            
            return max(0.0, min(100.0, lighting_score))
            
        except Exception as e:
            self.logger.error(f"Lighting calculation error: {str(e)}")
            return 50.0

    def _calculate_overall_confidence(self, property_analysis: Optional[PropertyAnalysis],
                                    damage_assessment: Optional[DamageAssessment],
                                    image_quality: float) -> float:
        """Calculate overall analysis confidence"""
        confidence_factors = []
        
        # Image quality factor
        confidence_factors.append(image_quality / 100.0)
        
        # Property analysis confidence
        if property_analysis:
            confidence_factors.append(property_analysis.confidence_score)
        
        # Damage assessment confidence
        if damage_assessment:
            confidence_factors.append(damage_assessment.confidence_score)
        
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5

    def capture_analysis_frame(self, camera_id: str, property_id: int, 
                             description: str = "") -> Optional[LiveAnalysisFrame]:
        """
        Manually capture and analyze a frame from specified camera
        """
        try:
            if camera_id not in self.active_cameras:
                raise Exception(f"Camera {camera_id} not found")
            
            camera_info = self.active_cameras[camera_id]
            frame = camera_info.get('last_frame')
            
            if frame is None:
                raise Exception(f"No frame available from camera {camera_id}")
            
            # Perform analysis on captured frame
            analysis_result = self._analyze_live_frame(
                camera_id, frame, property_id, time.time()
            )
            
            if analysis_result and self.default_config.get('save_analysis_frames', False):
                # Save the analyzed frame
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                frame_path = f"captured_analysis_{camera_id}_{timestamp}.jpg"
                cv2.imwrite(frame_path, frame)
                
                # Add metadata
                metadata = {
                    'description': description,
                    'manual_capture': True,
                    'saved_frame_path': frame_path
                }
                
                if hasattr(analysis_result, 'metadata'):
                    analysis_result.metadata = metadata
            
            self.logger.info(f"Manual frame capture completed for camera {camera_id}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Manual frame capture error: {str(e)}")
            return None

    def stop_camera_analysis(self, camera_id: str) -> bool:
        """
        Stop analysis for a specific camera
        """
        try:
            if camera_id not in self.active_cameras:
                return False
            
            # Stop the analysis thread
            self.active_cameras[camera_id]['active'] = False
            
            # Wait for thread to finish
            if camera_id in self.camera_threads:
                self.camera_threads[camera_id].join(timeout=5.0)
                del self.camera_threads[camera_id]
            
            # Release camera resources
            cap = self.active_cameras[camera_id]['capture']
            cap.release()
            
            # Update status
            self.stream_stats[camera_id].current_status = "stopped"
            
            self.logger.info(f"Camera analysis stopped: {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping camera analysis: {str(e)}")
            return False

    def remove_camera(self, camera_id: str) -> bool:
        """
        Remove camera from the system
        """
        try:
            # Stop analysis first
            self.stop_camera_analysis(camera_id)
            
            # Clean up resources
            if camera_id in self.active_cameras:
                del self.active_cameras[camera_id]
            if camera_id in self.analysis_queues:
                del self.analysis_queues[camera_id]
            if camera_id in self.background_subtractors:
                del self.background_subtractors[camera_id]
            if camera_id in self.motion_thresholds:
                del self.motion_thresholds[camera_id]
            if camera_id in self.stream_stats:
                del self.stream_stats[camera_id]
            
            self.logger.info(f"Camera removed: {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing camera: {str(e)}")
            return False

    def get_live_stream_data(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current live stream data for display
        """
        try:
            if camera_id not in self.active_cameras:
                return None
            
            camera_info = self.active_cameras[camera_id]
            stats = self.stream_stats.get(camera_id)
            
            return {
                'camera_id': camera_id,
                'status': 'active' if camera_info.get('active', False) else 'inactive',
                'current_frame': camera_info.get('last_frame'),
                'last_analysis': camera_info.get('last_analysis'),
                'stats': asdict(stats) if stats else None,
                'config': asdict(camera_info['config']),
                'property_id': camera_info.get('property_id')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting live stream data: {str(e)}")
            return None

    def register_analysis_callback(self, callback: Callable[[LiveAnalysisFrame], None]):
        """Register callback for analysis results"""
        self.analysis_callbacks.append(callback)

    def register_motion_callback(self, callback: Callable[[str, List[Tuple]], None]):
        """Register callback for motion detection"""
        self.motion_callbacks.append(callback)

    def register_alert_callback(self, callback: Callable[[str, Dict], None]):
        """Register callback for alerts"""
        self.alert_callbacks.append(callback)

    def _process_analysis_callbacks(self, analysis_result: LiveAnalysisFrame):
        """Process registered analysis callbacks"""
        for callback in self.analysis_callbacks:
            try:
                callback(analysis_result)
            except Exception as e:
                self.logger.error(f"Analysis callback error: {str(e)}")

    def _check_for_alerts(self, analysis_result: LiveAnalysisFrame):
        """Check analysis result for alert conditions"""
        try:
            alerts = []
            
            # Check for damage detection alerts
            if analysis_result.damage_assessment:
                if analysis_result.damage_assessment.urgency_level.value in ['high', 'critical']:
                    alerts.append({
                        'type': 'damage_detected',
                        'severity': analysis_result.damage_assessment.urgency_level.value,
                        'message': f"Damage detected requiring {analysis_result.damage_assessment.urgency_level.value} attention",
                        'camera_id': analysis_result.camera_id,
                        'timestamp': analysis_result.timestamp
                    })
            
            # Check for quality issues
            if analysis_result.image_quality_score < self.default_config['quality_threshold']:
                alerts.append({
                    'type': 'quality_issue',
                    'severity': 'medium',
                    'message': f"Poor image quality detected (score: {analysis_result.image_quality_score:.1f})",
                    'camera_id': analysis_result.camera_id,
                    'timestamp': analysis_result.timestamp
                })
            
            # Check for focus issues
            if analysis_result.focus_score < self.default_config['focus_threshold']:
                alerts.append({
                    'type': 'focus_issue',
                    'severity': 'low',
                    'message': f"Camera focus issue detected",
                    'camera_id': analysis_result.camera_id,
                    'timestamp': analysis_result.timestamp
                })
            
            # Process alert callbacks
            for alert in alerts:
                for callback in self.alert_callbacks:
                    try:
                        callback(analysis_result.camera_id, alert)
                    except Exception as e:
                        self.logger.error(f"Alert callback error: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Alert checking error: {str(e)}")

    def _check_manual_capture_request(self, camera_id: str) -> bool:
        """Check if manual capture was requested (placeholder)"""
        # This would typically check a flag or queue for manual capture requests
        return False

    def get_available_cameras(self) -> List[Dict[str, Any]]:
        """
        Get list of available cameras on the system
        """
        available_cameras = []
        
        try:
            # Check for USB/webcam cameras (indices 0-10)
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Get camera info
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    available_cameras.append({
                        'id': f"camera_{i}",
                        'type': CameraType.USB_CAMERA.value,
                        'source': str(i),
                        'resolution': (int(width), int(height)),
                        'fps': int(fps),
                        'status': 'available'
                    })
                    cap.release()
                else:
                    break  # No more cameras
            
        except Exception as e:
            self.logger.error(f"Error detecting cameras: {str(e)}")
        
        return available_cameras

    def create_camera_config(self, camera_id: str, source: str, 
                           camera_type: CameraType = CameraType.USB_CAMERA,
                           quality: StreamQuality = StreamQuality.MEDIUM) -> CameraConfig:
        """
        Create camera configuration
        """
        resolution_map = {
            StreamQuality.LOW: (640, 480),
            StreamQuality.MEDIUM: (1280, 720),
            StreamQuality.HIGH: (1920, 1080),
            StreamQuality.ULTRA: (3840, 2160)
        }
        
        return CameraConfig(
            camera_id=camera_id,
            camera_type=camera_type,
            source=source,
            resolution=resolution_map[quality],
            fps=30,
            auto_focus=True,
            auto_exposure=True,
            brightness=0.5,
            contrast=0.5,
            saturation=0.5,
            recording_enabled=False,
            recording_path=None
        )

# Global live camera analyzer instance
_live_camera_analyzer = None

def get_live_camera_analyzer():
    """Get the global live camera analyzer instance"""
    global _live_camera_analyzer
    if _live_camera_analyzer is None:
        _live_camera_analyzer = LiveCameraAnalyzer()
    return _live_camera_analyzer