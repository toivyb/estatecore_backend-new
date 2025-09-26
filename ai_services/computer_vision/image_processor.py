#!/usr/bin/env python3
"""
Image Processing Utilities for EstateCore Phase 6 Computer Vision
Advanced image preprocessing, enhancement, and analysis utilities
"""

import os
import io
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ImageFormat(Enum):
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    TIFF = "tiff"

class ImageQuality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

@dataclass
class ImageMetadata:
    """Image metadata and properties"""
    filename: str
    format: str
    dimensions: Tuple[int, int]
    file_size: int
    color_mode: str
    has_transparency: bool
    creation_date: Optional[datetime]
    camera_info: Optional[Dict[str, Any]]
    quality_score: float
    sharpness_score: float
    brightness_score: float
    contrast_score: float

@dataclass
class ProcessingResult:
    """Result of image processing operation"""
    success: bool
    processed_image_path: Optional[str]
    processing_time: float
    operations_applied: List[str]
    quality_improvement: float
    metadata: ImageMetadata
    error_message: Optional[str]

class ImageProcessor:
    """Advanced image processing for property analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cv2_available = CV2_AVAILABLE
        self.pil_available = PIL_AVAILABLE
        
        # Quality thresholds
        self.quality_thresholds = {
            'sharpness': {'poor': 100, 'fair': 300, 'good': 500, 'excellent': 800},
            'brightness': {'dark': 50, 'dim': 100, 'normal': 150, 'bright': 200},
            'contrast': {'low': 30, 'medium': 60, 'high': 90, 'very_high': 120}
        }
        
        self.logger.info(f"ImageProcessor initialized - CV2: {CV2_AVAILABLE}, PIL: {PIL_AVAILABLE}")

    def analyze_image_quality(self, image_path: str) -> ImageMetadata:
        """
        Analyze image quality and extract metadata
        """
        try:
            self.logger.info(f"Analyzing image quality: {image_path}")
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Get basic file info
            file_size = os.path.getsize(image_path)
            creation_date = datetime.fromtimestamp(os.path.getctime(image_path))
            
            # Load image and analyze
            if self.cv2_available:
                image = cv2.imread(image_path)
                if image is not None:
                    return self._analyze_quality_cv2(image_path, image, file_size, creation_date)
            
            if self.pil_available:
                with Image.open(image_path) as image:
                    return self._analyze_quality_pil(image_path, image, file_size, creation_date)
            
            # Fallback analysis
            return self._analyze_quality_fallback(image_path, file_size, creation_date)
            
        except Exception as e:
            self.logger.error(f"Error analyzing image quality: {str(e)}")
            return ImageMetadata(
                filename=os.path.basename(image_path),
                format="unknown",
                dimensions=(0, 0),
                file_size=0,
                color_mode="unknown",
                has_transparency=False,
                creation_date=None,
                camera_info=None,
                quality_score=0.0,
                sharpness_score=0.0,
                brightness_score=0.0,
                contrast_score=0.0
            )

    def _analyze_quality_cv2(self, image_path: str, image, file_size: int, 
                           creation_date: datetime) -> ImageMetadata:
        """Analyze image quality using OpenCV"""
        try:
            height, width, channels = image.shape
            
            # Calculate sharpness using Laplacian variance
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate brightness (mean pixel value)
            brightness = np.mean(gray)
            
            # Calculate contrast (standard deviation of pixel values)
            contrast = np.std(gray)
            
            # Overall quality score
            quality_score = self._calculate_quality_score(sharpness, brightness, contrast)
            
            # Detect format
            file_format = os.path.splitext(image_path)[1].lower().replace('.', '')
            
            return ImageMetadata(
                filename=os.path.basename(image_path),
                format=file_format,
                dimensions=(width, height),
                file_size=file_size,
                color_mode=f"{channels}_channel",
                has_transparency=channels == 4,
                creation_date=creation_date,
                camera_info=self._extract_camera_info_cv2(image_path),
                quality_score=quality_score,
                sharpness_score=float(sharpness),
                brightness_score=float(brightness),
                contrast_score=float(contrast)
            )
            
        except Exception as e:
            self.logger.error(f"CV2 quality analysis error: {str(e)}")
            return self._analyze_quality_fallback(image_path, file_size, creation_date)

    def _analyze_quality_pil(self, image_path: str, image: Image.Image, file_size: int,
                           creation_date: datetime) -> ImageMetadata:
        """Analyze image quality using PIL"""
        try:
            width, height = image.size
            
            # Convert to grayscale for analysis
            gray = image.convert('L')
            gray_array = np.array(gray)
            
            # Calculate sharpness (simplified)
            # Using gradient magnitude as sharpness measure
            grad_x = np.abs(np.diff(gray_array, axis=1))
            grad_y = np.abs(np.diff(gray_array, axis=0))
            sharpness = np.mean(grad_x) + np.mean(grad_y)
            
            # Calculate brightness
            brightness = np.mean(gray_array)
            
            # Calculate contrast
            contrast = np.std(gray_array)
            
            # Overall quality score
            quality_score = self._calculate_quality_score(sharpness, brightness, contrast)
            
            return ImageMetadata(
                filename=os.path.basename(image_path),
                format=image.format.lower() if image.format else 'unknown',
                dimensions=(width, height),
                file_size=file_size,
                color_mode=image.mode,
                has_transparency='transparency' in image.info or image.mode in ['RGBA', 'LA'],
                creation_date=creation_date,
                camera_info=self._extract_camera_info_pil(image),
                quality_score=quality_score,
                sharpness_score=float(sharpness),
                brightness_score=float(brightness),
                contrast_score=float(contrast)
            )
            
        except Exception as e:
            self.logger.error(f"PIL quality analysis error: {str(e)}")
            return self._analyze_quality_fallback(image_path, file_size, creation_date)

    def _analyze_quality_fallback(self, image_path: str, file_size: int,
                                creation_date: datetime) -> ImageMetadata:
        """Fallback quality analysis without image processing libraries"""
        filename = os.path.basename(image_path)
        file_format = os.path.splitext(image_path)[1].lower().replace('.', '')
        
        # Estimate quality based on file size and format
        estimated_quality = min(70.0, (file_size / 100000) * 10)  # Rough estimate
        
        return ImageMetadata(
            filename=filename,
            format=file_format,
            dimensions=(1920, 1080),  # Default assumption
            file_size=file_size,
            color_mode="rgb",
            has_transparency=file_format in ['png', 'webp'],
            creation_date=creation_date,
            camera_info=None,
            quality_score=estimated_quality,
            sharpness_score=50.0,  # Default values
            brightness_score=128.0,
            contrast_score=40.0
        )

    def enhance_image_for_analysis(self, image_path: str, output_path: str = None,
                                 enhancement_level: ImageQuality = ImageQuality.HIGH) -> ProcessingResult:
        """
        Enhance image quality for better computer vision analysis
        """
        start_time = datetime.now()
        operations_applied = []
        
        try:
            self.logger.info(f"Enhancing image for analysis: {image_path}")
            
            # Analyze current quality
            original_metadata = self.analyze_image_quality(image_path)
            
            # Determine output path
            if output_path is None:
                base_name = os.path.splitext(image_path)[0]
                output_path = f"{base_name}_enhanced.jpg"
            
            # Enhance based on available libraries
            if self.cv2_available:
                success, enhanced_metadata = self._enhance_image_cv2(
                    image_path, output_path, enhancement_level, operations_applied
                )
            elif self.pil_available:
                success, enhanced_metadata = self._enhance_image_pil(
                    image_path, output_path, enhancement_level, operations_applied
                )
            else:
                # Fallback - just copy file
                import shutil
                shutil.copy2(image_path, output_path)
                success = True
                enhanced_metadata = original_metadata
                operations_applied.append("file_copy")
            
            # Calculate processing time and quality improvement
            processing_time = (datetime.now() - start_time).total_seconds()
            quality_improvement = (enhanced_metadata.quality_score - 
                                 original_metadata.quality_score)
            
            return ProcessingResult(
                success=success,
                processed_image_path=output_path if success else None,
                processing_time=processing_time,
                operations_applied=operations_applied,
                quality_improvement=quality_improvement,
                metadata=enhanced_metadata,
                error_message=None
            )
            
        except Exception as e:
            error_msg = f"Image enhancement failed: {str(e)}"
            self.logger.error(error_msg)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=False,
                processed_image_path=None,
                processing_time=processing_time,
                operations_applied=operations_applied,
                quality_improvement=0.0,
                metadata=original_metadata if 'original_metadata' in locals() else None,
                error_message=error_msg
            )

    def _enhance_image_cv2(self, input_path: str, output_path: str,
                         enhancement_level: ImageQuality,
                         operations: List[str]) -> Tuple[bool, ImageMetadata]:
        """Enhance image using OpenCV"""
        try:
            image = cv2.imread(input_path)
            if image is None:
                raise ValueError(f"Could not load image: {input_path}")
            
            enhanced = image.copy()
            
            # Apply enhancements based on level
            if enhancement_level in [ImageQuality.MEDIUM, ImageQuality.HIGH, ImageQuality.ULTRA]:
                # Noise reduction
                enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
                operations.append("noise_reduction")
                
                # Contrast enhancement using CLAHE
                lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                l_enhanced = clahe.apply(l)
                enhanced = cv2.merge((l_enhanced, a, b))
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
                operations.append("contrast_enhancement")
            
            if enhancement_level in [ImageQuality.HIGH, ImageQuality.ULTRA]:
                # Sharpening
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(enhanced, -1, kernel)
                enhanced = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
                operations.append("sharpening")
            
            if enhancement_level == ImageQuality.ULTRA:
                # Advanced denoising
                enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
                operations.append("advanced_denoising")
                
                # Gamma correction
                gamma = 1.2
                lookup_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255
                                       for i in np.arange(0, 256)]).astype("uint8")
                enhanced = cv2.LUT(enhanced, lookup_table)
                operations.append("gamma_correction")
            
            # Save enhanced image
            quality = 95 if enhancement_level == ImageQuality.ULTRA else 85
            cv2.imwrite(output_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            # Analyze enhanced image quality
            enhanced_metadata = self.analyze_image_quality(output_path)
            
            return True, enhanced_metadata
            
        except Exception as e:
            self.logger.error(f"CV2 enhancement error: {str(e)}")
            return False, None

    def _enhance_image_pil(self, input_path: str, output_path: str,
                         enhancement_level: ImageQuality,
                         operations: List[str]) -> Tuple[bool, ImageMetadata]:
        """Enhance image using PIL"""
        try:
            with Image.open(input_path) as image:
                enhanced = image.copy()
                
                # Apply enhancements based on level
                if enhancement_level in [ImageQuality.MEDIUM, ImageQuality.HIGH, ImageQuality.ULTRA]:
                    # Contrast enhancement
                    enhancer = ImageEnhance.Contrast(enhanced)
                    enhanced = enhancer.enhance(1.2)
                    operations.append("contrast_enhancement")
                    
                    # Brightness adjustment
                    enhancer = ImageEnhance.Brightness(enhanced)
                    enhanced = enhancer.enhance(1.1)
                    operations.append("brightness_adjustment")
                
                if enhancement_level in [ImageQuality.HIGH, ImageQuality.ULTRA]:
                    # Sharpening
                    enhancer = ImageEnhance.Sharpness(enhanced)
                    enhanced = enhancer.enhance(1.3)
                    operations.append("sharpening")
                    
                    # Color enhancement
                    enhancer = ImageEnhance.Color(enhanced)
                    enhanced = enhancer.enhance(1.1)
                    operations.append("color_enhancement")
                
                if enhancement_level == ImageQuality.ULTRA:
                    # Noise reduction using filters
                    enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
                    operations.append("noise_reduction")
                    
                    # Edge enhancement
                    enhanced = enhanced.filter(ImageFilter.EDGE_ENHANCE)
                    operations.append("edge_enhancement")
                
                # Save enhanced image
                quality = 95 if enhancement_level == ImageQuality.ULTRA else 85
                enhanced.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                # Analyze enhanced image quality
                enhanced_metadata = self.analyze_image_quality(output_path)
                
                return True, enhanced_metadata
                
        except Exception as e:
            self.logger.error(f"PIL enhancement error: {str(e)}")
            return False, None

    def resize_image_for_analysis(self, image_path: str, target_size: Tuple[int, int],
                                maintain_aspect_ratio: bool = True) -> str:
        """
        Resize image for optimal analysis performance
        """
        try:
            output_path = f"{os.path.splitext(image_path)[0]}_resized.jpg"
            
            if self.cv2_available:
                image = cv2.imread(image_path)
                if image is not None:
                    if maintain_aspect_ratio:
                        # Calculate new dimensions maintaining aspect ratio
                        h, w = image.shape[:2]
                        target_w, target_h = target_size
                        
                        scale = min(target_w / w, target_h / h)
                        new_w = int(w * scale)
                        new_h = int(h * scale)
                        
                        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    else:
                        resized = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
                    
                    cv2.imwrite(output_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    return output_path
            
            elif self.pil_available:
                with Image.open(image_path) as image:
                    if maintain_aspect_ratio:
                        image.thumbnail(target_size, Image.Resampling.LANCZOS)
                        resized = image
                    else:
                        resized = image.resize(target_size, Image.Resampling.LANCZOS)
                    
                    resized.save(output_path, 'JPEG', quality=90, optimize=True)
                    return output_path
            
            else:
                # Fallback - copy original
                import shutil
                shutil.copy2(image_path, output_path)
                return output_path
                
        except Exception as e:
            self.logger.error(f"Error resizing image: {str(e)}")
            return image_path  # Return original on error

    def extract_image_features(self, image_path: str) -> Dict[str, Any]:
        """
        Extract statistical features from image for ML analysis
        """
        try:
            features = {}
            
            if self.cv2_available:
                image = cv2.imread(image_path)
                if image is not None:
                    features.update(self._extract_cv2_features(image))
            
            elif self.pil_available:
                with Image.open(image_path) as image:
                    features.update(self._extract_pil_features(image))
            
            else:
                # Fallback features
                features = self._extract_fallback_features(image_path)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting image features: {str(e)}")
            return {}

    def _extract_cv2_features(self, image) -> Dict[str, Any]:
        """Extract features using OpenCV"""
        features = {}
        
        try:
            # Basic statistics
            height, width, channels = image.shape
            features['width'] = width
            features['height'] = height
            features['channels'] = channels
            features['aspect_ratio'] = width / height
            
            # Convert to different color spaces
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Color statistics
            features['mean_brightness'] = float(np.mean(gray))
            features['std_brightness'] = float(np.std(gray))
            features['mean_hue'] = float(np.mean(hsv[:,:,0]))
            features['mean_saturation'] = float(np.mean(hsv[:,:,1]))
            features['mean_value'] = float(np.mean(hsv[:,:,2]))
            
            # Texture features
            features['laplacian_variance'] = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            
            # Edge density
            edges = cv2.Canny(gray, 50, 150)
            features['edge_density'] = float(np.sum(edges > 0) / (width * height))
            
            # Histogram features
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            features['histogram_mean'] = float(np.mean(hist))
            features['histogram_std'] = float(np.std(hist))
            
        except Exception as e:
            self.logger.error(f"CV2 feature extraction error: {str(e)}")
        
        return features

    def _extract_pil_features(self, image: Image.Image) -> Dict[str, Any]:
        """Extract features using PIL"""
        features = {}
        
        try:
            width, height = image.size
            features['width'] = width
            features['height'] = height
            features['channels'] = len(image.getbands())
            features['aspect_ratio'] = width / height
            features['format'] = image.format
            features['mode'] = image.mode
            
            # Convert to grayscale for analysis
            gray = image.convert('L')
            gray_array = np.array(gray)
            
            # Basic statistics
            features['mean_brightness'] = float(np.mean(gray_array))
            features['std_brightness'] = float(np.std(gray_array))
            features['min_brightness'] = float(np.min(gray_array))
            features['max_brightness'] = float(np.max(gray_array))
            
            # Simple texture measure
            grad_x = np.abs(np.diff(gray_array, axis=1))
            grad_y = np.abs(np.diff(gray_array, axis=0))
            features['texture_measure'] = float(np.mean(grad_x) + np.mean(grad_y))
            
            # Histogram features
            histogram = gray.histogram()
            features['histogram_entropy'] = self._calculate_entropy(histogram)
            
        except Exception as e:
            self.logger.error(f"PIL feature extraction error: {str(e)}")
        
        return features

    def _extract_fallback_features(self, image_path: str) -> Dict[str, Any]:
        """Extract basic features without image processing libraries"""
        file_size = os.path.getsize(image_path)
        file_format = os.path.splitext(image_path)[1].lower().replace('.', '')
        
        return {
            'file_size': file_size,
            'format': file_format,
            'estimated_quality': min(70.0, (file_size / 100000) * 10),
            'width': 1920,  # Default assumptions
            'height': 1080,
            'aspect_ratio': 1.78,
            'channels': 3
        }

    def _calculate_quality_score(self, sharpness: float, brightness: float, 
                               contrast: float) -> float:
        """Calculate overall quality score from individual metrics"""
        # Normalize each metric to 0-100 scale
        sharpness_score = min(100, (sharpness / 500) * 100)  # Normalize sharpness
        brightness_score = 100 - abs(brightness - 128) / 1.28  # Optimal around 128
        contrast_score = min(100, (contrast / 60) * 100)  # Normalize contrast
        
        # Weighted average
        quality = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
        return max(0.0, min(100.0, quality))

    def _extract_camera_info_cv2(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Extract camera information from EXIF data using OpenCV"""
        # OpenCV doesn't have built-in EXIF reading, would need additional library
        # For now, return None
        return None

    def _extract_camera_info_pil(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """Extract camera information from EXIF data using PIL"""
        try:
            exifdata = image.getexif()
            if exifdata is not None and len(exifdata) > 0:
                camera_info = {}
                
                # Common EXIF tags
                exif_tags = {
                    271: 'make',           # Camera make
                    272: 'model',          # Camera model
                    306: 'datetime',       # DateTime
                    33437: 'f_number',     # F-number
                    33434: 'exposure_time', # Exposure time
                    34855: 'iso',          # ISO speed
                    37386: 'focal_length'  # Focal length
                }
                
                for tag_id, name in exif_tags.items():
                    if tag_id in exifdata:
                        camera_info[name] = exifdata[tag_id]
                
                return camera_info if camera_info else None
        except:
            return None

    def _calculate_entropy(self, histogram: List[int]) -> float:
        """Calculate entropy of histogram"""
        total_pixels = sum(histogram)
        if total_pixels == 0:
            return 0.0
        
        entropy = 0.0
        for count in histogram:
            if count > 0:
                probability = count / total_pixels
                entropy -= probability * np.log2(probability)
        
        return entropy

    def create_thumbnail(self, image_path: str, thumbnail_size: Tuple[int, int] = (256, 256),
                        quality: int = 85) -> str:
        """Create thumbnail version of image"""
        try:
            base_name = os.path.splitext(image_path)[0]
            thumbnail_path = f"{base_name}_thumb.jpg"
            
            if self.pil_available:
                with Image.open(image_path) as image:
                    # Create thumbnail maintaining aspect ratio
                    image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary
                    if image.mode in ['RGBA', 'P']:
                        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                        rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                        image = rgb_image
                    
                    image.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
                    return thumbnail_path
            
            elif self.cv2_available:
                image = cv2.imread(image_path)
                if image is not None:
                    # Resize maintaining aspect ratio
                    h, w = image.shape[:2]
                    scale = min(thumbnail_size[0] / w, thumbnail_size[1] / h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    
                    thumbnail = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    cv2.imwrite(thumbnail_path, thumbnail, [cv2.IMWRITE_JPEG_QUALITY, quality])
                    return thumbnail_path
            
            else:
                # Fallback - copy original
                import shutil
                shutil.copy2(image_path, thumbnail_path)
                return thumbnail_path
                
        except Exception as e:
            self.logger.error(f"Error creating thumbnail: {str(e)}")
            return image_path

    def batch_process_images(self, image_paths: List[str], 
                           enhancement_level: ImageQuality = ImageQuality.MEDIUM) -> List[ProcessingResult]:
        """Process multiple images in batch"""
        results = []
        
        for image_path in image_paths:
            try:
                result = self.enhance_image_for_analysis(image_path, 
                                                       enhancement_level=enhancement_level)
                results.append(result)
            except Exception as e:
                error_result = ProcessingResult(
                    success=False,
                    processed_image_path=None,
                    processing_time=0.0,
                    operations_applied=[],
                    quality_improvement=0.0,
                    metadata=None,
                    error_message=str(e)
                )
                results.append(error_result)
        
        return results

# Global image processor instance
_image_processor = None

def get_image_processor():
    """Get the global image processor instance"""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor