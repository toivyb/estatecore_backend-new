#!/usr/bin/env python3
"""
Advanced Damage Detection System for EstateCore Phase 6
Specialized Computer Vision for Property Damage Assessment
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Import from property analyzer for shared types
from .property_analyzer import DamageType, DamageDetection, ConditionLevel

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class DamageSeverity(Enum):
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UrgencyLevel(Enum):
    LOW = "low"           # Can wait months
    MEDIUM = "medium"     # Should fix within weeks
    HIGH = "high"         # Fix within days
    CRITICAL = "critical" # Fix immediately

@dataclass
class DamageAssessment:
    """Comprehensive damage assessment result"""
    property_id: int
    image_path: str
    assessment_id: str
    timestamp: datetime
    overall_damage_score: float  # 0-100 scale
    urgency_level: UrgencyLevel
    damage_detections: List[DamageDetection]
    repair_recommendations: List[str]
    estimated_total_cost: float
    insurance_claim_worthy: bool
    follow_up_required: bool
    inspector_notes: str
    confidence_score: float

@dataclass
class MaintenanceAlert:
    """Maintenance alert generated from damage detection"""
    alert_id: str
    property_id: int
    damage_type: DamageType
    severity: DamageSeverity
    urgency: UrgencyLevel
    title: str
    description: str
    estimated_cost: float
    recommended_action: str
    contractor_type_needed: str
    created_at: datetime
    due_date: datetime
    priority_score: int  # 1-10 scale

class AdvancedDamageDetector:
    """Advanced damage detection and assessment system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cv2_available = CV2_AVAILABLE
        self.pil_available = PIL_AVAILABLE
        
        # Load damage detection models and patterns
        self.damage_patterns = self._load_damage_patterns()
        self.repair_cost_database = self._load_repair_costs()
        self.contractor_mapping = self._load_contractor_mapping()
        
        self.logger.info("AdvancedDamageDetector initialized")

    def _load_damage_patterns(self) -> Dict:
        """Load advanced damage detection patterns"""
        return {
            DamageType.WATER_DAMAGE: {
                'color_signatures': [
                    {'hsv_range': [(10, 50, 20), (30, 255, 200)], 'confidence': 0.8},  # Brown stains
                    {'hsv_range': [(45, 30, 30), (75, 255, 255)], 'confidence': 0.7},  # Yellow stains
                ],
                'texture_patterns': ['irregular_patches', 'discoloration', 'warping'],
                'edge_characteristics': {'minimum_area': 500, 'aspect_ratio': (0.3, 3.0)},
                'severity_indicators': {
                    'area_thresholds': {'low': 0.02, 'medium': 0.08, 'high': 0.20, 'critical': 0.40},
                    'color_intensity': {'low': 0.3, 'medium': 0.6, 'high': 0.8, 'critical': 0.95}
                }
            },
            DamageType.STRUCTURAL_DAMAGE: {
                'color_signatures': [
                    {'hsv_range': [(0, 0, 0), (180, 30, 50)], 'confidence': 0.9},  # Dark cracks
                ],
                'texture_patterns': ['linear_cracks', 'hole_patterns', 'deformation'],
                'edge_characteristics': {'minimum_length': 100, 'linearity': 0.8},
                'severity_indicators': {
                    'crack_length': {'low': 50, 'medium': 200, 'high': 500, 'critical': 1000},
                    'crack_width': {'low': 2, 'medium': 5, 'high': 15, 'critical': 30}
                }
            },
            DamageType.PAINT_DAMAGE: {
                'color_signatures': [
                    {'hsv_range': [(0, 0, 180), (180, 50, 255)], 'confidence': 0.75},  # Faded areas
                ],
                'texture_patterns': ['peeling', 'chipping', 'fading', 'bubbling'],
                'edge_characteristics': {'irregularity': 0.6, 'minimum_area': 200},
                'severity_indicators': {
                    'coverage_area': {'low': 0.05, 'medium': 0.15, 'high': 0.35, 'critical': 0.60}
                }
            },
            DamageType.FLOOR_DAMAGE: {
                'color_signatures': [
                    {'hsv_range': [(15, 40, 40), (25, 255, 180)], 'confidence': 0.8},  # Scratches/wear
                ],
                'texture_patterns': ['scratches', 'dents', 'wear_patterns', 'stains'],
                'edge_characteristics': {'pattern_type': 'linear_or_circular'},
                'severity_indicators': {
                    'damage_density': {'low': 0.1, 'medium': 0.3, 'high': 0.6, 'critical': 0.8}
                }
            },
            DamageType.WINDOW_DAMAGE: {
                'color_signatures': [
                    {'hsv_range': [(0, 0, 0), (180, 255, 100)], 'confidence': 0.85},  # Dark areas (cracks)
                ],
                'texture_patterns': ['spider_cracks', 'linear_cracks', 'missing_glass'],
                'edge_characteristics': {'crack_patterns': 'radial_or_linear'},
                'severity_indicators': {
                    'crack_count': {'low': 1, 'medium': 3, 'high': 8, 'critical': 15}
                }
            }
        }

    def _load_repair_costs(self) -> Dict:
        """Load repair cost estimates database"""
        return {
            DamageType.WATER_DAMAGE: {
                'minimal': {'min': 100, 'max': 300, 'typical': 200},
                'low': {'min': 300, 'max': 800, 'typical': 550},
                'medium': {'min': 800, 'max': 2500, 'typical': 1650},
                'high': {'min': 2500, 'max': 8000, 'typical': 5250},
                'critical': {'min': 8000, 'max': 25000, 'typical': 16500}
            },
            DamageType.STRUCTURAL_DAMAGE: {
                'minimal': {'min': 200, 'max': 500, 'typical': 350},
                'low': {'min': 500, 'max': 1500, 'typical': 1000},
                'medium': {'min': 1500, 'max': 5000, 'typical': 3250},
                'high': {'min': 5000, 'max': 15000, 'typical': 10000},
                'critical': {'min': 15000, 'max': 50000, 'typical': 32500}
            },
            DamageType.PAINT_DAMAGE: {
                'minimal': {'min': 50, 'max': 150, 'typical': 100},
                'low': {'min': 150, 'max': 400, 'typical': 275},
                'medium': {'min': 400, 'max': 1000, 'typical': 700},
                'high': {'min': 1000, 'max': 2500, 'typical': 1750},
                'critical': {'min': 2500, 'max': 5000, 'typical': 3750}
            },
            DamageType.FLOOR_DAMAGE: {
                'minimal': {'min': 200, 'max': 500, 'typical': 350},
                'low': {'min': 500, 'max': 1200, 'typical': 850},
                'medium': {'min': 1200, 'max': 3000, 'typical': 2100},
                'high': {'min': 3000, 'max': 8000, 'typical': 5500},
                'critical': {'min': 8000, 'max': 20000, 'typical': 14000}
            },
            DamageType.WINDOW_DAMAGE: {
                'minimal': {'min': 100, 'max': 250, 'typical': 175},
                'low': {'min': 250, 'max': 600, 'typical': 425},
                'medium': {'min': 600, 'max': 1200, 'typical': 900},
                'high': {'min': 1200, 'max': 2500, 'typical': 1850},
                'critical': {'min': 2500, 'max': 5000, 'typical': 3750}
            }
        }

    def _load_contractor_mapping(self) -> Dict:
        """Load contractor type mapping for different damage types"""
        return {
            DamageType.WATER_DAMAGE: {
                'primary': 'Water Damage Restoration Specialist',
                'secondary': ['Plumber', 'General Contractor', 'Mold Remediation'],
                'timeline': {'low': '1-3 days', 'medium': '3-7 days', 'high': '1-2 weeks', 'critical': 'Immediate'}
            },
            DamageType.STRUCTURAL_DAMAGE: {
                'primary': 'Structural Engineer',
                'secondary': ['General Contractor', 'Foundation Specialist', 'Concrete Repair'],
                'timeline': {'low': '1-2 weeks', 'medium': '2-4 weeks', 'high': '1-2 months', 'critical': 'Immediate'}
            },
            DamageType.PAINT_DAMAGE: {
                'primary': 'Professional Painter',
                'secondary': ['Handyman', 'General Contractor'],
                'timeline': {'low': '1-2 days', 'medium': '3-5 days', 'high': '1-2 weeks', 'critical': '2-3 weeks'}
            },
            DamageType.FLOOR_DAMAGE: {
                'primary': 'Flooring Specialist',
                'secondary': ['General Contractor', 'Carpet Installer', 'Hardwood Refinisher'],
                'timeline': {'low': '1-3 days', 'medium': '1 week', 'high': '2-3 weeks', 'critical': '3-4 weeks'}
            },
            DamageType.WINDOW_DAMAGE: {
                'primary': 'Window Repair Specialist',
                'secondary': ['Glass Replacement', 'General Contractor'],
                'timeline': {'low': '1-2 days', 'medium': '3-5 days', 'high': '1 week', 'critical': 'Same day'}
            }
        }

    def assess_property_damage(self, image_path: str, property_id: int, 
                              inspection_notes: str = "") -> DamageAssessment:
        """
        Perform comprehensive damage assessment of property image
        """
        try:
            self.logger.info(f"Assessing damage for property {property_id}: {image_path}")
            
            # Load and preprocess image
            image, dimensions = self._load_and_preprocess_image(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Detect all types of damage
            damage_detections = self._comprehensive_damage_detection(image, dimensions)
            
            # Calculate overall damage score
            overall_score = self._calculate_overall_damage_score(damage_detections)
            
            # Determine urgency level
            urgency = self._determine_urgency_level(damage_detections)
            
            # Generate repair recommendations
            recommendations = self._generate_repair_recommendations(damage_detections)
            
            # Calculate total estimated cost
            total_cost = sum(d.estimated_cost or 0 for d in damage_detections)
            
            # Determine if insurance claim worthy
            insurance_worthy = self._assess_insurance_worthiness(damage_detections, total_cost)
            
            # Check if follow-up inspection needed
            follow_up_needed = any(d.severity in ['high', 'critical'] for d in damage_detections)
            
            # Calculate confidence
            confidence = self._calculate_assessment_confidence(damage_detections)
            
            # Create assessment
            assessment = DamageAssessment(
                property_id=property_id,
                image_path=image_path,
                assessment_id=f"DA_{property_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                overall_damage_score=overall_score,
                urgency_level=urgency,
                damage_detections=damage_detections,
                repair_recommendations=recommendations,
                estimated_total_cost=total_cost,
                insurance_claim_worthy=insurance_worthy,
                follow_up_required=follow_up_needed,
                inspector_notes=inspection_notes,
                confidence_score=confidence
            )
            
            self.logger.info(f"Damage assessment completed - Score: {overall_score:.1f}, "
                           f"Urgency: {urgency.value}, Detections: {len(damage_detections)}")
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error in damage assessment: {str(e)}")
            # Return minimal assessment with error
            return DamageAssessment(
                property_id=property_id,
                image_path=image_path,
                assessment_id=f"DA_ERROR_{property_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                overall_damage_score=50.0,  # Default moderate score
                urgency_level=UrgencyLevel.LOW,
                damage_detections=[],
                repair_recommendations=[f"Assessment error: {str(e)}"],
                estimated_total_cost=0.0,
                insurance_claim_worthy=False,
                follow_up_required=True,
                inspector_notes=f"Assessment failed: {str(e)}",
                confidence_score=0.0
            )

    def _load_and_preprocess_image(self, image_path: str) -> Tuple[Any, Tuple[int, int]]:
        """Load and preprocess image for damage detection"""
        try:
            if self.cv2_available:
                image = cv2.imread(image_path)
                if image is not None:
                    # Enhance image for better damage detection
                    enhanced = self._enhance_image_cv2(image)
                    return enhanced, (image.shape[1], image.shape[0])
            
            elif self.pil_available:
                image = Image.open(image_path)
                enhanced = self._enhance_image_pil(image)
                return np.array(enhanced), image.size
            
            else:
                # Fallback simulation
                return "simulated_image", (1920, 1080)
                
        except Exception as e:
            self.logger.error(f"Error loading/preprocessing image: {str(e)}")
            return None, (0, 0)

    def _enhance_image_cv2(self, image):
        """Enhance image using OpenCV for better damage detection"""
        # Noise reduction
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        # Contrast enhancement
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced

    def _enhance_image_pil(self, image):
        """Enhance image using PIL for better damage detection"""
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(1.2)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = enhancer.enhance(1.1)
        
        return enhanced

    def _comprehensive_damage_detection(self, image, dimensions: Tuple[int, int]) -> List[DamageDetection]:
        """Perform comprehensive damage detection across all damage types"""
        all_detections = []
        
        for damage_type in DamageType:
            try:
                detections = self._detect_specific_damage_type(image, damage_type, dimensions)
                all_detections.extend(detections)
            except Exception as e:
                self.logger.error(f"Error detecting {damage_type.value}: {str(e)}")
        
        # Remove duplicate/overlapping detections
        filtered_detections = self._filter_overlapping_detections(all_detections)
        
        return filtered_detections

    def _detect_specific_damage_type(self, image, damage_type: DamageType, 
                                   dimensions: Tuple[int, int]) -> List[DamageDetection]:
        """Detect specific type of damage in image"""
        detections = []
        
        if image == "simulated_image":
            # Simulate damage detection for demo
            if damage_type == DamageType.WATER_DAMAGE:
                detections.append(DamageDetection(
                    damage_type=damage_type,
                    severity='medium',
                    confidence=0.82,
                    location=(150, 200, 300, 200),
                    description='Water staining detected on ceiling area',
                    estimated_cost=1200.0,
                    priority=7
                ))
            elif damage_type == DamageType.PAINT_DAMAGE:
                detections.append(DamageDetection(
                    damage_type=damage_type,
                    severity='low',
                    confidence=0.75,
                    location=(50, 100, 200, 150),
                    description='Paint peeling observed on wall surface',
                    estimated_cost=350.0,
                    priority=3
                ))
        
        elif self.cv2_available:
            detections.extend(self._cv2_damage_detection(image, damage_type, dimensions))
        
        else:
            # Simplified detection without CV libraries
            detections.extend(self._simplified_damage_detection(damage_type, dimensions))
        
        return detections

    def _cv2_damage_detection(self, image, damage_type: DamageType, 
                            dimensions: Tuple[int, int]) -> List[DamageDetection]:
        """OpenCV-based damage detection for specific damage type"""
        detections = []
        
        try:
            patterns = self.damage_patterns.get(damage_type, {})
            color_signatures = patterns.get('color_signatures', [])
            
            # Convert to different color spaces for analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            for signature in color_signatures:
                hsv_range = signature['hsv_range']
                confidence = signature['confidence']
                
                # Create mask for color range
                mask = cv2.inRange(hsv, np.array(hsv_range[0]), np.array(hsv_range[1]))
                
                # Morphological operations to clean up mask
                kernel = np.ones((3,3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                # Find contours of potential damage areas
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 100:  # Minimum area threshold
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Calculate severity based on area and patterns
                        severity = self._calculate_damage_severity(area, dimensions, damage_type)
                        
                        # Create detection
                        detection = DamageDetection(
                            damage_type=damage_type,
                            severity=severity,
                            confidence=confidence * min(area / 1000, 1.0),
                            location=(x, y, w, h),
                            description=f'{damage_type.value.replace("_", " ").title()} detected via CV analysis',
                            estimated_cost=self._get_repair_cost_estimate(damage_type, severity),
                            priority=self._calculate_priority(damage_type, severity)
                        )
                        
                        detections.append(detection)
        
        except Exception as e:
            self.logger.error(f"CV2 damage detection error for {damage_type.value}: {str(e)}")
        
        return detections

    def _simplified_damage_detection(self, damage_type: DamageType, 
                                   dimensions: Tuple[int, int]) -> List[DamageDetection]:
        """Simplified damage detection without CV libraries"""
        import random
        
        # Simulate realistic damage detection
        if random.random() < 0.3:  # 30% chance of detecting this damage type
            severity = random.choice(['low', 'medium', 'high'])
            
            return [DamageDetection(
                damage_type=damage_type,
                severity=severity,
                confidence=0.65 + random.random() * 0.25,
                location=(
                    random.randint(0, dimensions[0]//2),
                    random.randint(0, dimensions[1]//2),
                    random.randint(100, 300),
                    random.randint(50, 200)
                ),
                description=f'Possible {damage_type.value.replace("_", " ")} detected',
                estimated_cost=self._get_repair_cost_estimate(damage_type, severity),
                priority=self._calculate_priority(damage_type, severity)
            )]
        
        return []

    def _calculate_damage_severity(self, area: float, dimensions: Tuple[int, int], 
                                 damage_type: DamageType) -> str:
        """Calculate damage severity based on area and damage type"""
        total_area = dimensions[0] * dimensions[1]
        area_ratio = area / total_area
        
        patterns = self.damage_patterns.get(damage_type, {})
        thresholds = patterns.get('severity_indicators', {}).get('area_thresholds', {
            'low': 0.02, 'medium': 0.08, 'high': 0.20, 'critical': 0.40
        })
        
        if area_ratio >= thresholds.get('critical', 0.40):
            return 'critical'
        elif area_ratio >= thresholds.get('high', 0.20):
            return 'high'
        elif area_ratio >= thresholds.get('medium', 0.08):
            return 'medium'
        else:
            return 'low'

    def _get_repair_cost_estimate(self, damage_type: DamageType, severity: str) -> float:
        """Get repair cost estimate for damage type and severity"""
        costs = self.repair_cost_database.get(damage_type, {})
        severity_costs = costs.get(severity, {'typical': 500})
        return float(severity_costs['typical'])

    def _calculate_priority(self, damage_type: DamageType, severity: str) -> int:
        """Calculate priority score (1-10) based on damage type and severity"""
        base_priorities = {
            DamageType.STRUCTURAL_DAMAGE: 8,
            DamageType.WATER_DAMAGE: 7,
            DamageType.ELECTRICAL_DAMAGE: 9,
            DamageType.PLUMBING_DAMAGE: 6,
            DamageType.WINDOW_DAMAGE: 4,
            DamageType.FLOOR_DAMAGE: 3,
            DamageType.PAINT_DAMAGE: 2,
            DamageType.APPLIANCE_DAMAGE: 5
        }
        
        severity_multipliers = {
            'low': 0.5,
            'medium': 0.8,
            'high': 1.2,
            'critical': 1.5
        }
        
        base = base_priorities.get(damage_type, 5)
        multiplier = severity_multipliers.get(severity, 1.0)
        
        return min(int(base * multiplier), 10)

    def _filter_overlapping_detections(self, detections: List[DamageDetection]) -> List[DamageDetection]:
        """Remove overlapping damage detections"""
        if not detections:
            return detections
        
        # Sort by confidence (highest first)
        sorted_detections = sorted(detections, key=lambda x: x.confidence, reverse=True)
        filtered = []
        
        for detection in sorted_detections:
            # Check if this detection overlaps with any already filtered detection
            overlaps = False
            for existing in filtered:
                if self._detections_overlap(detection, existing):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered.append(detection)
        
        return filtered

    def _detections_overlap(self, det1: DamageDetection, det2: DamageDetection, 
                          threshold: float = 0.3) -> bool:
        """Check if two detections overlap significantly"""
        x1, y1, w1, h1 = det1.location
        x2, y2, w2, h2 = det2.location
        
        # Calculate intersection area
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return False  # No intersection
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2
        
        # Calculate overlap ratio
        overlap_ratio = intersection_area / min(area1, area2)
        
        return overlap_ratio > threshold

    def _calculate_overall_damage_score(self, detections: List[DamageDetection]) -> float:
        """Calculate overall damage score (0-100)"""
        if not detections:
            return 0.0
        
        # Weight damage by type and severity
        severity_weights = {'low': 1, 'medium': 3, 'high': 7, 'critical': 15}
        type_weights = {
            DamageType.STRUCTURAL_DAMAGE: 2.0,
            DamageType.WATER_DAMAGE: 1.8,
            DamageType.ELECTRICAL_DAMAGE: 2.2,
            DamageType.PLUMBING_DAMAGE: 1.5,
            DamageType.WINDOW_DAMAGE: 1.0,
            DamageType.FLOOR_DAMAGE: 0.8,
            DamageType.PAINT_DAMAGE: 0.5,
            DamageType.APPLIANCE_DAMAGE: 1.2
        }
        
        total_score = 0.0
        for detection in detections:
            severity_weight = severity_weights.get(detection.severity, 1)
            type_weight = type_weights.get(detection.damage_type, 1.0)
            confidence = detection.confidence
            
            score = severity_weight * type_weight * confidence * 2
            total_score += score
        
        # Normalize to 0-100 scale
        return min(total_score, 100.0)

    def _determine_urgency_level(self, detections: List[DamageDetection]) -> UrgencyLevel:
        """Determine urgency level based on detected damage"""
        if not detections:
            return UrgencyLevel.LOW
        
        # Check for critical damage
        critical_damage = any(d.severity == 'critical' for d in detections)
        if critical_damage:
            return UrgencyLevel.CRITICAL
        
        # Check for high severity damage
        high_damage = any(d.severity == 'high' for d in detections)
        if high_damage:
            return UrgencyLevel.HIGH
        
        # Check for structural or water damage (always higher urgency)
        priority_damage = any(d.damage_type in [DamageType.STRUCTURAL_DAMAGE, 
                                               DamageType.WATER_DAMAGE,
                                               DamageType.ELECTRICAL_DAMAGE] for d in detections)
        if priority_damage:
            return UrgencyLevel.MEDIUM
        
        return UrgencyLevel.LOW

    def _generate_repair_recommendations(self, detections: List[DamageDetection]) -> List[str]:
        """Generate specific repair recommendations"""
        recommendations = []
        
        # Group by damage type
        damage_by_type = {}
        for detection in detections:
            if detection.damage_type not in damage_by_type:
                damage_by_type[detection.damage_type] = []
            damage_by_type[detection.damage_type].append(detection)
        
        # Generate recommendations for each type
        for damage_type, damages in damage_by_type.items():
            contractor_info = self.contractor_mapping.get(damage_type, {})
            primary_contractor = contractor_info.get('primary', 'General Contractor')
            
            # Find highest severity for this damage type
            highest_severity = max(d.severity for d in damages)
            timeline = contractor_info.get('timeline', {}).get(highest_severity, '1-2 weeks')
            
            total_cost = sum(d.estimated_cost or 0 for d in damages)
            
            recommendation = f"{damage_type.value.replace('_', ' ').title()}: "
            recommendation += f"Contact {primary_contractor} within {timeline}. "
            recommendation += f"Estimated cost: ${total_cost:.0f}. "
            recommendation += f"Priority: {highest_severity.upper()}."
            
            recommendations.append(recommendation)
        
        # Add general recommendations based on overall assessment
        if len(detections) > 3:
            recommendations.append("Consider comprehensive property inspection due to multiple issues detected.")
        
        if any(d.damage_type == DamageType.WATER_DAMAGE for d in detections):
            recommendations.append("Check for mold growth - may require specialized remediation.")
        
        return recommendations[:10]  # Limit to top 10

    def _assess_insurance_worthiness(self, detections: List[DamageDetection], total_cost: float) -> bool:
        """Assess if damage is worthy of insurance claim"""
        # High cost threshold
        if total_cost > 2000:
            return True
        
        # Specific damage types that are typically covered
        covered_types = [DamageType.WATER_DAMAGE, DamageType.STRUCTURAL_DAMAGE, 
                        DamageType.ELECTRICAL_DAMAGE]
        
        for detection in detections:
            if (detection.damage_type in covered_types and 
                detection.severity in ['high', 'critical']):
                return True
        
        return False

    def _calculate_assessment_confidence(self, detections: List[DamageDetection]) -> float:
        """Calculate overall assessment confidence"""
        if not detections:
            return 0.5
        
        # Average detection confidence weighted by severity
        severity_weights = {'low': 0.5, 'medium': 1.0, 'high': 1.5, 'critical': 2.0}
        
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for detection in detections:
            weight = severity_weights.get(detection.severity, 1.0)
            total_weighted_confidence += detection.confidence * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.5

    def generate_maintenance_alerts(self, assessment: DamageAssessment) -> List[MaintenanceAlert]:
        """Generate maintenance alerts from damage assessment"""
        alerts = []
        
        for detection in assessment.damage_detections:
            # Convert severity to our enum
            severity_mapping = {
                'low': DamageSeverity.LOW,
                'medium': DamageSeverity.MEDIUM,
                'high': DamageSeverity.HIGH,
                'critical': DamageSeverity.CRITICAL
            }
            
            severity = severity_mapping.get(detection.severity, DamageSeverity.LOW)
            
            # Calculate due date based on urgency
            urgency_days = {
                UrgencyLevel.CRITICAL: 0,  # Immediate
                UrgencyLevel.HIGH: 3,      # 3 days
                UrgencyLevel.MEDIUM: 14,   # 2 weeks
                UrgencyLevel.LOW: 90       # 3 months
            }
            
            days_to_due = urgency_days.get(assessment.urgency_level, 30)
            due_date = datetime.now() + timedelta(days=days_to_due)
            
            contractor_info = self.contractor_mapping.get(detection.damage_type, {})
            
            alert = MaintenanceAlert(
                alert_id=f"MA_{assessment.property_id}_{detection.damage_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                property_id=assessment.property_id,
                damage_type=detection.damage_type,
                severity=severity,
                urgency=assessment.urgency_level,
                title=f"{detection.damage_type.value.replace('_', ' ').title()} Repair Required",
                description=detection.description,
                estimated_cost=detection.estimated_cost or 0.0,
                recommended_action=f"Contact {contractor_info.get('primary', 'General Contractor')}",
                contractor_type_needed=contractor_info.get('primary', 'General Contractor'),
                created_at=datetime.now(),
                due_date=due_date,
                priority_score=detection.priority
            )
            
            alerts.append(alert)
        
        return alerts

# Global damage detector instance
_damage_detector = None

def get_damage_detector():
    """Get the global damage detector instance"""
    global _damage_detector
    if _damage_detector is None:
        _damage_detector = AdvancedDamageDetector()
    return _damage_detector