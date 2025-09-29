import logging
import base64
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import uuid

from flask import current_app, request
from estatecore_backend.models import db, User
from services.rbac_service import RBACService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiometricType(Enum):
    FINGERPRINT = "fingerprint"
    FACE_RECOGNITION = "face_recognition"
    VOICE_RECOGNITION = "voice_recognition"
    IRIS_SCAN = "iris_scan"
    PALM_PRINT = "palm_print"

class BiometricStatus(Enum):
    ENROLLED = "enrolled"
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"

@dataclass
class BiometricTemplate:
    id: str
    user_id: int
    biometric_type: BiometricType
    template_data: str  # Encrypted biometric template
    quality_score: float
    enrolled_at: datetime
    last_used: Optional[datetime] = None
    status: BiometricStatus = BiometricStatus.ENROLLED
    device_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'biometric_type': self.biometric_type.value,
            'quality_score': self.quality_score,
            'enrolled_at': self.enrolled_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'status': self.status.value,
            'device_info': self.device_info,
            'metadata': self.metadata
        }

@dataclass
class BiometricAuthAttempt:
    id: str
    user_id: Optional[int]
    biometric_type: BiometricType
    template_id: Optional[str]
    success: bool
    confidence_score: float
    ip_address: str
    user_agent: str
    device_info: Dict[str, Any]
    timestamp: datetime
    failure_reason: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'biometric_type': self.biometric_type.value,
            'template_id': self.template_id,
            'success': self.success,
            'confidence_score': self.confidence_score,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_info': self.device_info,
            'timestamp': self.timestamp.isoformat(),
            'failure_reason': self.failure_reason
        }

class BiometricAuthService:
    """Biometric authentication service"""
    
    def __init__(self):
        self.templates: Dict[str, BiometricTemplate] = {}
        self.auth_attempts: List[BiometricAuthAttempt] = []
        self.confidence_threshold = 0.8  # Minimum confidence for successful auth
        self.max_enrollment_attempts = 3
        self.template_expiry_days = 90  # Templates expire after 90 days
        
    def enroll_biometric(self, user_id: int, biometric_type: BiometricType, 
                        biometric_data: str, device_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enroll a new biometric template for a user"""
        try:
            # Validate user exists
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Check if user already has this biometric type enrolled
            existing_templates = self._get_user_templates(user_id, biometric_type)
            if len(existing_templates) >= 3:  # Max 3 templates per type
                return {'success': False, 'error': 'Maximum biometric templates reached for this type'}
            
            # Process and validate biometric data
            processed_result = self._process_biometric_data(biometric_data, biometric_type)
            if not processed_result['valid']:
                return {'success': False, 'error': processed_result['error']}
            
            # Create template
            template_id = str(uuid.uuid4())
            template = BiometricTemplate(
                id=template_id,
                user_id=user_id,
                biometric_type=biometric_type,
                template_data=self._encrypt_template(processed_result['template']),
                quality_score=processed_result['quality_score'],
                enrolled_at=datetime.utcnow(),
                device_info=device_info or {},
                metadata={
                    'enrollment_ip': request.remote_addr if request else 'unknown',
                    'enrollment_user_agent': request.headers.get('User-Agent') if request else 'unknown'
                }
            )
            
            # Store template
            self.templates[template_id] = template
            
            logger.info(f"Biometric template enrolled for user {user_id}: {biometric_type.value}")
            
            return {
                'success': True,
                'template_id': template_id,
                'quality_score': template.quality_score,
                'message': 'Biometric template enrolled successfully'
            }
            
        except Exception as e:
            logger.error(f"Error enrolling biometric: {str(e)}")
            return {'success': False, 'error': 'Failed to enroll biometric template'}
    
    def authenticate_biometric(self, biometric_type: BiometricType, biometric_data: str,
                             device_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Authenticate user using biometric data"""
        attempt_id = str(uuid.uuid4())
        
        try:
            # Process biometric data
            processed_result = self._process_biometric_data(biometric_data, biometric_type)
            if not processed_result['valid']:
                self._log_auth_attempt(
                    attempt_id=attempt_id,
                    biometric_type=biometric_type,
                    success=False,
                    confidence_score=0.0,
                    device_info=device_info,
                    failure_reason=processed_result['error']
                )
                return {'success': False, 'error': processed_result['error']}
            
            # Find matching templates
            best_match = self._find_best_match(processed_result['template'], biometric_type)
            
            if not best_match:
                self._log_auth_attempt(
                    attempt_id=attempt_id,
                    biometric_type=biometric_type,
                    success=False,
                    confidence_score=0.0,
                    device_info=device_info,
                    failure_reason='No matching biometric template found'
                )
                return {'success': False, 'error': 'Biometric authentication failed'}
            
            template, confidence_score = best_match
            
            # Check confidence threshold
            if confidence_score < self.confidence_threshold:
                self._log_auth_attempt(
                    attempt_id=attempt_id,
                    user_id=template.user_id,
                    biometric_type=biometric_type,
                    template_id=template.id,
                    success=False,
                    confidence_score=confidence_score,
                    device_info=device_info,
                    failure_reason=f'Confidence score {confidence_score} below threshold {self.confidence_threshold}'
                )
                return {'success': False, 'error': 'Biometric authentication failed'}
            
            # Check template status and expiry
            if template.status != BiometricStatus.ENROLLED and template.status != BiometricStatus.ACTIVE:
                self._log_auth_attempt(
                    attempt_id=attempt_id,
                    user_id=template.user_id,
                    biometric_type=biometric_type,
                    template_id=template.id,
                    success=False,
                    confidence_score=confidence_score,
                    device_info=device_info,
                    failure_reason=f'Template status is {template.status.value}'
                )
                return {'success': False, 'error': 'Biometric template is not active'}
            
            # Check template expiry
            if self._is_template_expired(template):
                template.status = BiometricStatus.EXPIRED
                self._log_auth_attempt(
                    attempt_id=attempt_id,
                    user_id=template.user_id,
                    biometric_type=biometric_type,
                    template_id=template.id,
                    success=False,
                    confidence_score=confidence_score,
                    device_info=device_info,
                    failure_reason='Biometric template has expired'
                )
                return {'success': False, 'error': 'Biometric template has expired'}
            
            # Successful authentication
            template.last_used = datetime.utcnow()
            template.status = BiometricStatus.ACTIVE
            
            self._log_auth_attempt(
                attempt_id=attempt_id,
                user_id=template.user_id,
                biometric_type=biometric_type,
                template_id=template.id,
                success=True,
                confidence_score=confidence_score,
                device_info=device_info
            )
            
            # Get user info
            user = User.query.get(template.user_id)
            
            logger.info(f"Successful biometric authentication for user {template.user_id}")
            
            return {
                'success': True,
                'user_id': template.user_id,
                'username': user.username if user else 'Unknown',
                'email': user.email if user else 'Unknown',
                'confidence_score': confidence_score,
                'biometric_type': biometric_type.value,
                'template_id': template.id
            }
            
        except Exception as e:
            logger.error(f"Error in biometric authentication: {str(e)}")
            self._log_auth_attempt(
                attempt_id=attempt_id,
                biometric_type=biometric_type,
                success=False,
                confidence_score=0.0,
                device_info=device_info,
                failure_reason=f'System error: {str(e)}'
            )
            return {'success': False, 'error': 'Biometric authentication system error'}
    
    def get_user_biometrics(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all biometric templates for a user"""
        user_templates = []
        for template in self.templates.values():
            if template.user_id == user_id:
                template_dict = template.to_dict()
                # Remove sensitive template data
                template_dict.pop('template_data', None)
                user_templates.append(template_dict)
        
        return user_templates
    
    def disable_biometric(self, template_id: str, user_id: int) -> Dict[str, Any]:
        """Disable a biometric template"""
        try:
            if template_id not in self.templates:
                return {'success': False, 'error': 'Biometric template not found'}
            
            template = self.templates[template_id]
            
            # Verify ownership
            if template.user_id != user_id:
                return {'success': False, 'error': 'Unauthorized to disable this template'}
            
            template.status = BiometricStatus.DISABLED
            
            logger.info(f"Biometric template disabled: {template_id}")
            
            return {'success': True, 'message': 'Biometric template disabled successfully'}
            
        except Exception as e:
            logger.error(f"Error disabling biometric template: {str(e)}")
            return {'success': False, 'error': 'Failed to disable biometric template'}
    
    def delete_biometric(self, template_id: str, user_id: int) -> Dict[str, Any]:
        """Delete a biometric template"""
        try:
            if template_id not in self.templates:
                return {'success': False, 'error': 'Biometric template not found'}
            
            template = self.templates[template_id]
            
            # Verify ownership
            if template.user_id != user_id:
                return {'success': False, 'error': 'Unauthorized to delete this template'}
            
            del self.templates[template_id]
            
            logger.info(f"Biometric template deleted: {template_id}")
            
            return {'success': True, 'message': 'Biometric template deleted successfully'}
            
        except Exception as e:
            logger.error(f"Error deleting biometric template: {str(e)}")
            return {'success': False, 'error': 'Failed to delete biometric template'}
    
    def get_auth_history(self, user_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get biometric authentication history"""
        attempts = self.auth_attempts.copy()
        
        if user_id:
            attempts = [a for a in attempts if a.user_id == user_id]
        
        # Sort by timestamp (newest first)
        attempts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [attempt.to_dict() for attempt in attempts[:limit]]
    
    def get_biometric_stats(self) -> Dict[str, Any]:
        """Get biometric system statistics"""
        total_templates = len(self.templates)
        active_templates = len([t for t in self.templates.values() if t.status == BiometricStatus.ACTIVE])
        
        # Authentication stats (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_attempts = [a for a in self.auth_attempts if a.timestamp > thirty_days_ago]
        successful_attempts = [a for a in recent_attempts if a.success]
        
        # Stats by biometric type
        type_stats = {}
        for biometric_type in BiometricType:
            type_templates = [t for t in self.templates.values() if t.biometric_type == biometric_type]
            type_attempts = [a for a in recent_attempts if a.biometric_type == biometric_type]
            type_successes = [a for a in type_attempts if a.success]
            
            type_stats[biometric_type.value] = {
                'templates': len(type_templates),
                'attempts_30d': len(type_attempts),
                'success_rate': len(type_successes) / len(type_attempts) if type_attempts else 0
            }
        
        return {
            'total_templates': total_templates,
            'active_templates': active_templates,
            'total_attempts_30d': len(recent_attempts),
            'successful_attempts_30d': len(successful_attempts),
            'success_rate_30d': len(successful_attempts) / len(recent_attempts) if recent_attempts else 0,
            'type_statistics': type_stats,
            'average_confidence': sum(a.confidence_score for a in successful_attempts) / len(successful_attempts) if successful_attempts else 0
        }
    
    def _process_biometric_data(self, biometric_data: str, biometric_type: BiometricType) -> Dict[str, Any]:
        """Process and validate biometric data"""
        try:
            # Decode base64 data
            decoded_data = base64.b64decode(biometric_data)
            
            # Simulate biometric processing (in production, use actual biometric SDK)
            if len(decoded_data) < 100:  # Minimum data size
                return {'valid': False, 'error': 'Insufficient biometric data'}
            
            # Simulate quality assessment
            quality_score = min(0.95, len(decoded_data) / 10000)  # Mock quality score
            
            if quality_score < 0.3:
                return {'valid': False, 'error': 'Poor biometric quality'}
            
            # Create mock template (in production, extract actual features)
            template_hash = hashlib.sha256(decoded_data).hexdigest()
            
            return {
                'valid': True,
                'template': template_hash,
                'quality_score': quality_score
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Invalid biometric data: {str(e)}'}
    
    def _encrypt_template(self, template_data: str) -> str:
        """Encrypt biometric template data"""
        # In production, use proper encryption
        return base64.b64encode(template_data.encode()).decode()
    
    def _decrypt_template(self, encrypted_data: str) -> str:
        """Decrypt biometric template data"""
        # In production, use proper decryption
        return base64.b64decode(encrypted_data.encode()).decode()
    
    def _find_best_match(self, input_template: str, biometric_type: BiometricType) -> Optional[tuple]:
        """Find the best matching template"""
        best_match = None
        best_confidence = 0.0
        
        for template in self.templates.values():
            if (template.biometric_type == biometric_type and 
                template.status in [BiometricStatus.ENROLLED, BiometricStatus.ACTIVE]):
                
                # Decrypt and compare templates
                stored_template = self._decrypt_template(template.template_data)
                confidence = self._calculate_confidence(input_template, stored_template)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (template, confidence)
        
        return best_match
    
    def _calculate_confidence(self, template1: str, template2: str) -> float:
        """Calculate confidence score between two templates"""
        # Simple mock implementation - in production use proper biometric matching
        if template1 == template2:
            return 1.0
        
        # Calculate similarity based on hash similarity (mock)
        similar_chars = sum(c1 == c2 for c1, c2 in zip(template1, template2))
        max_length = max(len(template1), len(template2))
        
        return similar_chars / max_length if max_length > 0 else 0.0
    
    def _get_user_templates(self, user_id: int, biometric_type: BiometricType) -> List[BiometricTemplate]:
        """Get all templates for a user of a specific type"""
        return [
            template for template in self.templates.values()
            if template.user_id == user_id and template.biometric_type == biometric_type
        ]
    
    def _is_template_expired(self, template: BiometricTemplate) -> bool:
        """Check if a template has expired"""
        expiry_date = template.enrolled_at + timedelta(days=self.template_expiry_days)
        return datetime.utcnow() > expiry_date
    
    def _log_auth_attempt(self, attempt_id: str, biometric_type: BiometricType, 
                         success: bool, confidence_score: float, device_info: Dict[str, Any],
                         user_id: Optional[int] = None, template_id: Optional[str] = None,
                         failure_reason: Optional[str] = None):
        """Log biometric authentication attempt"""
        attempt = BiometricAuthAttempt(
            id=attempt_id,
            user_id=user_id,
            biometric_type=biometric_type,
            template_id=template_id,
            success=success,
            confidence_score=confidence_score,
            ip_address=request.remote_addr if request else 'unknown',
            user_agent=request.headers.get('User-Agent', '') if request else 'unknown',
            device_info=device_info or {},
            timestamp=datetime.utcnow(),
            failure_reason=failure_reason
        )
        
        self.auth_attempts.append(attempt)
        
        # Keep only last 1000 attempts
        if len(self.auth_attempts) > 1000:
            self.auth_attempts = self.auth_attempts[-1000:]

# Global biometric service instance
biometric_service = BiometricAuthService()