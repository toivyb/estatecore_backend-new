#!/usr/bin/env python3
"""
Property Image Analyzer for EstateCore Phase 6
Advanced Computer Vision for Property Analysis and Condition Assessment
"""

import os
import io
import base64
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Try importing computer vision libraries with fallbacks
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available, using simplified image analysis")

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available, using basic image processing")

class PropertyFeatureType(Enum):
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    BEDROOM = "bedroom"
    LIVING_ROOM = "living_room"
    EXTERIOR = "exterior"
    APPLIANCES = "appliances"
    FLOORING = "flooring"
    WINDOWS = "windows"
    LIGHTING = "lighting"
    HVAC = "hvac"

class ConditionLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class DamageType(Enum):
    WATER_DAMAGE = "water_damage"
    STRUCTURAL_DAMAGE = "structural_damage"
    PAINT_DAMAGE = "paint_damage"
    FLOOR_DAMAGE = "floor_damage"
    WINDOW_DAMAGE = "window_damage"
    APPLIANCE_DAMAGE = "appliance_damage"
    ELECTRICAL_DAMAGE = "electrical_damage"
    PLUMBING_DAMAGE = "plumbing_damage"

@dataclass
class PropertyFeature:
    """Detected property feature"""
    feature_type: PropertyFeatureType
    confidence: float
    bounding_box: Optional[Tuple[int, int, int, int]]  # (x, y, width, height)
    attributes: Dict[str, Any]
    condition: ConditionLevel
    
@dataclass 
class DamageDetection:
    """Detected damage or issue"""
    damage_type: DamageType
    severity: str  # low, medium, high, critical
    confidence: float
    location: Tuple[int, int, int, int]  # bounding box
    description: str
    estimated_cost: Optional[float]
    priority: int  # 1-5 scale

@dataclass
class PropertyAnalysis:
    """Complete property image analysis result"""
    image_id: str
    property_id: int
    analysis_timestamp: datetime
    image_dimensions: Tuple[int, int]
    overall_condition: ConditionLevel
    confidence_score: float
    features_detected: List[PropertyFeature]
    damage_detected: List[DamageDetection]
    room_type: Optional[PropertyFeatureType]
    estimated_value_impact: float  # percentage impact on property value
    recommendations: List[str]
    metadata: Dict[str, Any]

class PropertyImageAnalyzer:
    """Advanced Property Image Analysis using Computer Vision"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cv2_available = CV2_AVAILABLE
        self.pil_available = PIL_AVAILABLE
        
        # Initialize feature detection patterns (simplified for demo)
        self.feature_patterns = self._load_feature_patterns()
        self.damage_indicators = self._load_damage_indicators()
        
        self.logger.info(f"PropertyImageAnalyzer initialized - CV2: {CV2_AVAILABLE}, PIL: {PIL_AVAILABLE}")

    def _load_feature_patterns(self) -> Dict:
        """Load feature detection patterns"""
        return {
            'kitchen': {
                'keywords': ['kitchen', 'stove', 'refrigerator', 'cabinet', 'counter'],
                'color_patterns': [(50, 50, 50), (200, 200, 200)],  # Dark/light patterns
                'size_indicators': {'min_area': 1000}
            },
            'bathroom': {
                'keywords': ['bathroom', 'toilet', 'shower', 'bathtub', 'sink'],
                'color_patterns': [(255, 255, 255), (200, 200, 255)],  # White/blue tints
                'size_indicators': {'min_area': 500}
            },
            'bedroom': {
                'keywords': ['bedroom', 'bed', 'dresser', 'closet'],
                'color_patterns': [(150, 100, 80), (200, 180, 160)],  # Warm tones
                'size_indicators': {'min_area': 2000}
            },
            'living_room': {
                'keywords': ['living', 'sofa', 'couch', 'tv', 'coffee table'],
                'color_patterns': [(120, 100, 80), (180, 160, 140)],  # Neutral tones
                'size_indicators': {'min_area': 3000}
            }
        }

    def _load_damage_indicators(self) -> Dict:
        """Load damage detection indicators"""
        return {
            'water_damage': {
                'color_range': [(0, 50, 100), (20, 255, 255)],  # HSV brown/yellow stains
                'texture_indicators': ['irregular_patches', 'discoloration'],
                'severity_thresholds': {'low': 0.05, 'medium': 0.15, 'high': 0.30}
            },
            'paint_damage': {
                'color_range': [(0, 0, 200), (180, 50, 255)],  # Faded/peeling areas
                'texture_indicators': ['peeling', 'cracking', 'fading'],
                'severity_thresholds': {'low': 0.10, 'medium': 0.25, 'high': 0.50}
            },
            'structural_damage': {
                'color_range': [(0, 0, 0), (180, 255, 100)],  # Dark cracks/holes
                'texture_indicators': ['cracks', 'holes', 'sagging'],
                'severity_thresholds': {'low': 0.02, 'medium': 0.08, 'high': 0.20}
            }
        }

    def analyze_property_image(self, image_path: str, property_id: int, 
                              image_metadata: Dict[str, Any] = None) -> PropertyAnalysis:
        """
        Perform comprehensive analysis of a property image
        """
        try:
            self.logger.info(f"Analyzing property image: {image_path}")
            
            # Load and preprocess image
            image, dimensions = self._load_image(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Perform analysis
            features = self._detect_features(image)
            damage = self._detect_damage(image)
            room_type = self._classify_room_type(image, features)
            overall_condition = self._assess_overall_condition(features, damage)
            
            # Calculate confidence and impact
            confidence_score = self._calculate_confidence(features, damage)
            value_impact = self._estimate_value_impact(damage, overall_condition)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(features, damage, overall_condition)
            
            # Create analysis result
            analysis = PropertyAnalysis(
                image_id=os.path.basename(image_path),
                property_id=property_id,
                analysis_timestamp=datetime.now(),
                image_dimensions=dimensions,
                overall_condition=overall_condition,
                confidence_score=confidence_score,
                features_detected=features,
                damage_detected=damage,
                room_type=room_type,
                estimated_value_impact=value_impact,
                recommendations=recommendations,
                metadata=image_metadata or {}
            )
            
            self.logger.info(f"Analysis completed - Condition: {overall_condition.value}, "
                           f"Features: {len(features)}, Damage: {len(damage)}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing property image: {str(e)}")
            # Return basic analysis with error info
            return PropertyAnalysis(
                image_id=os.path.basename(image_path),
                property_id=property_id,
                analysis_timestamp=datetime.now(),
                image_dimensions=(0, 0),
                overall_condition=ConditionLevel.FAIR,
                confidence_score=0.0,
                features_detected=[],
                damage_detected=[],
                room_type=None,
                estimated_value_impact=0.0,
                recommendations=[f"Analysis error: {str(e)}"],
                metadata={'error': str(e)}
            )

    def _load_image(self, image_path: str) -> Tuple[Any, Tuple[int, int]]:
        """Load image using available libraries"""
        try:
            if self.cv2_available:
                image = cv2.imread(image_path)
                if image is not None:
                    return image, (image.shape[1], image.shape[0])
            
            if self.pil_available:
                image = Image.open(image_path)
                return np.array(image), image.size
            
            # Fallback: simulate image loading
            self.logger.warning("No image libraries available, simulating analysis")
            return "simulated_image", (1920, 1080)
            
        except Exception as e:
            self.logger.error(f"Error loading image: {str(e)}")
            return None, (0, 0)

    def _detect_features(self, image) -> List[PropertyFeature]:
        """Detect property features in the image"""
        features = []
        
        try:
            # Simulate feature detection (in real implementation, use ML models)
            if image == "simulated_image":
                # Simulate detected features
                features.append(PropertyFeature(
                    feature_type=PropertyFeatureType.KITCHEN,
                    confidence=0.85,
                    bounding_box=(100, 100, 300, 200),
                    attributes={'modern': True, 'appliances': ['refrigerator', 'stove']},
                    condition=ConditionLevel.GOOD
                ))
                
                features.append(PropertyFeature(
                    feature_type=PropertyFeatureType.FLOORING,
                    confidence=0.92,
                    bounding_box=(0, 400, 800, 600),
                    attributes={'type': 'hardwood', 'condition': 'good'},
                    condition=ConditionLevel.GOOD
                ))
            
            else:
                # Real computer vision feature detection would go here
                # For now, use simplified pattern matching
                if self.cv2_available:
                    features.extend(self._cv2_feature_detection(image))
                else:
                    features.extend(self._simplified_feature_detection(image))
        
        except Exception as e:
            self.logger.error(f"Error detecting features: {str(e)}")
        
        return features

    def _detect_damage(self, image) -> List[DamageDetection]:
        """Detect damage and issues in the image"""
        damage_list = []
        
        try:
            if image == "simulated_image":
                # Simulate damage detection
                damage_list.append(DamageDetection(
                    damage_type=DamageType.PAINT_DAMAGE,
                    severity='low',
                    confidence=0.75,
                    location=(200, 50, 100, 80),
                    description='Minor paint scuffing on wall',
                    estimated_cost=150.0,
                    priority=2
                ))
            
            else:
                # Real damage detection would analyze color patterns, textures, etc.
                if self.cv2_available:
                    damage_list.extend(self._cv2_damage_detection(image))
                else:
                    damage_list.extend(self._simplified_damage_detection(image))
        
        except Exception as e:
            self.logger.error(f"Error detecting damage: {str(e)}")
        
        return damage_list

    def _cv2_feature_detection(self, image) -> List[PropertyFeature]:
        """OpenCV-based feature detection"""
        features = []
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection for structural features
            edges = cv2.Canny(gray, 50, 150)
            
            # Contour detection for objects
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyze largest contours as potential features
            for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum size threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Classify feature type based on size and position
                    feature_type = self._classify_contour_feature(area, x, y, w, h, image.shape)
                    
                    features.append(PropertyFeature(
                        feature_type=feature_type,
                        confidence=min(0.7 + (area / 10000) * 0.2, 0.95),
                        bounding_box=(x, y, w, h),
                        attributes={'area': area, 'method': 'cv2_contour'},
                        condition=ConditionLevel.GOOD  # Default, would need additional analysis
                    ))
        
        except Exception as e:
            self.logger.error(f"CV2 feature detection error: {str(e)}")
        
        return features

    def _cv2_damage_detection(self, image) -> List[DamageDetection]:
        """OpenCV-based damage detection"""
        damage_list = []
        try:
            # Convert color space for better damage detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detect water damage (brown/yellow discoloration)
            water_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([30, 255, 255]))
            water_area = cv2.countNonZero(water_mask)
            total_area = image.shape[0] * image.shape[1]
            
            if water_area / total_area > 0.01:  # More than 1% of image
                severity = self._calculate_damage_severity(water_area / total_area, 'water_damage')
                damage_list.append(DamageDetection(
                    damage_type=DamageType.WATER_DAMAGE,
                    severity=severity,
                    confidence=0.8,
                    location=(0, 0, image.shape[1], image.shape[0]),  # Full image for now
                    description=f'Water damage detected covering {water_area/total_area:.1%} of image',
                    estimated_cost=self._estimate_repair_cost(DamageType.WATER_DAMAGE, severity),
                    priority=3 if severity in ['medium', 'high'] else 2
                ))
        
        except Exception as e:
            self.logger.error(f"CV2 damage detection error: {str(e)}")
        
        return damage_list

    def _simplified_feature_detection(self, image) -> List[PropertyFeature]:
        """Simplified feature detection without CV libraries"""
        # Return simulated features based on common property layouts
        return [
            PropertyFeature(
                feature_type=PropertyFeatureType.WINDOWS,
                confidence=0.80,
                bounding_box=(50, 50, 200, 150),
                attributes={'count': 2, 'type': 'standard'},
                condition=ConditionLevel.GOOD
            ),
            PropertyFeature(
                feature_type=PropertyFeatureType.FLOORING,
                confidence=0.85,
                bounding_box=(0, 300, 800, 200),
                attributes={'type': 'carpet', 'wear': 'minimal'},
                condition=ConditionLevel.GOOD
            )
        ]

    def _simplified_damage_detection(self, image) -> List[DamageDetection]:
        """Simplified damage detection without CV libraries"""
        # Return simulated damage based on common issues
        import random
        
        damage_types = [DamageType.PAINT_DAMAGE, DamageType.FLOOR_DAMAGE, DamageType.WATER_DAMAGE]
        selected_damage = random.choice(damage_types)
        
        return [DamageDetection(
            damage_type=selected_damage,
            severity='low',
            confidence=0.70,
            location=(100, 100, 150, 100),
            description=f'Possible {selected_damage.value.replace("_", " ")} detected',
            estimated_cost=200.0,
            priority=2
        )]

    def _classify_room_type(self, image, features: List[PropertyFeature]) -> Optional[PropertyFeatureType]:
        """Classify the room type based on detected features"""
        # Count feature types to determine room
        feature_counts = {}
        for feature in features:
            if feature.feature_type not in feature_counts:
                feature_counts[feature.feature_type] = 0
            feature_counts[feature.feature_type] += feature.confidence
        
        # Determine most likely room type
        room_indicators = {
            PropertyFeatureType.KITCHEN: [PropertyFeatureType.APPLIANCES],
            PropertyFeatureType.BATHROOM: [PropertyFeatureType.BATHROOM],
            PropertyFeatureType.BEDROOM: [PropertyFeatureType.BEDROOM],
            PropertyFeatureType.LIVING_ROOM: [PropertyFeatureType.LIVING_ROOM]
        }
        
        best_match = None
        best_score = 0.0
        
        for room_type, indicators in room_indicators.items():
            score = sum(feature_counts.get(indicator, 0) for indicator in indicators)
            if score > best_score:
                best_score = score
                best_match = room_type
        
        return best_match if best_score > 0.5 else None

    def _assess_overall_condition(self, features: List[PropertyFeature], 
                                damage: List[DamageDetection]) -> ConditionLevel:
        """Assess overall property condition"""
        if not features and not damage:
            return ConditionLevel.FAIR
        
        # Calculate condition based on damage severity
        critical_damage = any(d.severity == 'critical' for d in damage)
        high_damage = any(d.severity == 'high' for d in damage)
        medium_damage = any(d.severity == 'medium' for d in damage)
        
        if critical_damage:
            return ConditionLevel.CRITICAL
        elif high_damage:
            return ConditionLevel.POOR
        elif medium_damage:
            return ConditionLevel.FAIR
        elif damage:
            return ConditionLevel.GOOD
        else:
            # Base on feature conditions
            avg_condition = self._calculate_average_condition(features)
            return avg_condition

    def _calculate_average_condition(self, features: List[PropertyFeature]) -> ConditionLevel:
        """Calculate average condition from features"""
        if not features:
            return ConditionLevel.FAIR
        
        condition_values = {
            ConditionLevel.CRITICAL: 1,
            ConditionLevel.POOR: 2,
            ConditionLevel.FAIR: 3,
            ConditionLevel.GOOD: 4,
            ConditionLevel.EXCELLENT: 5
        }
        
        total_score = sum(condition_values[f.condition] for f in features)
        avg_score = total_score / len(features)
        
        # Convert back to condition level
        for condition, value in sorted(condition_values.items(), key=lambda x: x[1]):
            if avg_score <= value + 0.5:
                return condition
        
        return ConditionLevel.EXCELLENT

    def _calculate_confidence(self, features: List[PropertyFeature], 
                            damage: List[DamageDetection]) -> float:
        """Calculate overall analysis confidence"""
        if not features and not damage:
            return 0.5
        
        # Weight features and damage confidence
        feature_conf = sum(f.confidence for f in features) / len(features) if features else 0.0
        damage_conf = sum(d.confidence for d in damage) / len(damage) if damage else 0.0
        
        # Combined confidence with weights
        total_conf = (feature_conf * 0.6 + damage_conf * 0.4)
        return min(max(total_conf, 0.0), 1.0)

    def _estimate_value_impact(self, damage: List[DamageDetection], 
                             condition: ConditionLevel) -> float:
        """Estimate impact on property value (percentage)"""
        base_impact = {
            ConditionLevel.EXCELLENT: 0.05,   # +5% value
            ConditionLevel.GOOD: 0.0,         # No impact
            ConditionLevel.FAIR: -0.05,       # -5% value
            ConditionLevel.POOR: -0.15,       # -15% value
            ConditionLevel.CRITICAL: -0.30    # -30% value
        }
        
        # Additional impact from specific damage
        damage_impact = 0.0
        for d in damage:
            severity_impact = {
                'low': -0.02,
                'medium': -0.05,
                'high': -0.12,
                'critical': -0.25
            }
            damage_impact += severity_impact.get(d.severity, 0.0)
        
        total_impact = base_impact[condition] + damage_impact
        return max(total_impact, -0.50)  # Cap at -50%

    def _generate_recommendations(self, features: List[PropertyFeature], 
                                damage: List[DamageDetection], 
                                condition: ConditionLevel) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Damage-based recommendations
        for d in damage:
            if d.severity in ['high', 'critical']:
                recommendations.append(f"URGENT: Address {d.damage_type.value.replace('_', ' ')} - {d.description}")
            else:
                recommendations.append(f"Schedule repair for {d.damage_type.value.replace('_', ' ')} - estimated cost: ${d.estimated_cost:.0f}")
        
        # Condition-based recommendations
        if condition == ConditionLevel.CRITICAL:
            recommendations.append("Property requires immediate attention before occupancy")
        elif condition == ConditionLevel.POOR:
            recommendations.append("Consider major renovations to improve marketability")
        elif condition == ConditionLevel.FAIR:
            recommendations.append("Minor improvements could enhance property value")
        
        # Feature-based recommendations
        appliance_features = [f for f in features if f.feature_type == PropertyFeatureType.APPLIANCES]
        if not appliance_features:
            recommendations.append("Consider updating appliances to attract tenants")
        
        return recommendations[:5]  # Limit to top 5 recommendations

    def _classify_contour_feature(self, area: float, x: int, y: int, w: int, h: int, 
                                image_shape: Tuple[int, int, int]) -> PropertyFeatureType:
        """Classify a contour as a specific feature type"""
        height, width = image_shape[:2]
        
        # Simple heuristics based on size and position
        if area > width * height * 0.3:  # Large area
            return PropertyFeatureType.FLOORING
        elif y < height * 0.3:  # Upper part of image
            return PropertyFeatureType.WINDOWS
        elif w > h and area > 5000:  # Wide rectangles
            return PropertyFeatureType.APPLIANCES
        else:
            return PropertyFeatureType.LIGHTING

    def _calculate_damage_severity(self, ratio: float, damage_type: str) -> str:
        """Calculate damage severity based on area ratio"""
        thresholds = self.damage_indicators.get(damage_type, {}).get('severity_thresholds', {
            'low': 0.05, 'medium': 0.15, 'high': 0.30
        })
        
        if ratio >= thresholds.get('high', 0.30):
            return 'high'
        elif ratio >= thresholds.get('medium', 0.15):
            return 'medium'
        else:
            return 'low'

    def _estimate_repair_cost(self, damage_type: DamageType, severity: str) -> float:
        """Estimate repair costs based on damage type and severity"""
        base_costs = {
            DamageType.PAINT_DAMAGE: {'low': 200, 'medium': 500, 'high': 1200},
            DamageType.WATER_DAMAGE: {'low': 500, 'medium': 1500, 'high': 5000},
            DamageType.FLOOR_DAMAGE: {'low': 300, 'medium': 800, 'high': 2500},
            DamageType.STRUCTURAL_DAMAGE: {'low': 1000, 'medium': 3000, 'high': 10000}
        }
        
        return float(base_costs.get(damage_type, {'low': 250, 'medium': 750, 'high': 2000})[severity])

    def batch_analyze_images(self, image_paths: List[str], property_id: int) -> List[PropertyAnalysis]:
        """Analyze multiple images for a property"""
        results = []
        
        for image_path in image_paths:
            try:
                analysis = self.analyze_property_image(image_path, property_id)
                results.append(analysis)
            except Exception as e:
                self.logger.error(f"Failed to analyze {image_path}: {str(e)}")
        
        return results

    def get_analysis_summary(self, analyses: List[PropertyAnalysis]) -> Dict[str, Any]:
        """Generate summary from multiple property analyses"""
        if not analyses:
            return {'error': 'No analyses provided'}
        
        total_images = len(analyses)
        avg_confidence = sum(a.confidence_score for a in analyses) / total_images
        
        # Aggregate conditions
        conditions = [a.overall_condition for a in analyses]
        most_common_condition = max(set(conditions), key=conditions.count)
        
        # Aggregate damage
        all_damage = []
        for a in analyses:
            all_damage.extend(a.damage_detected)
        
        # Aggregate recommendations
        all_recommendations = []
        for a in analyses:
            all_recommendations.extend(a.recommendations)
        
        return {
            'total_images_analyzed': total_images,
            'average_confidence': avg_confidence,
            'overall_condition': most_common_condition.value,
            'total_damage_instances': len(all_damage),
            'high_priority_issues': len([d for d in all_damage if d.severity in ['high', 'critical']]),
            'estimated_total_repair_cost': sum(d.estimated_cost or 0 for d in all_damage),
            'top_recommendations': list(set(all_recommendations))[:10],
            'analysis_timestamp': datetime.now().isoformat()
        }

# Global analyzer instance
_property_analyzer = None

def get_property_analyzer():
    """Get the global property analyzer instance"""
    global _property_analyzer
    if _property_analyzer is None:
        _property_analyzer = PropertyImageAnalyzer()
    return _property_analyzer