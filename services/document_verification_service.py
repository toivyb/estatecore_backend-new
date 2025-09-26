"""
Document Verification Service
AI-powered document analysis and authenticity verification
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import random
import base64
import hashlib
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class DocumentVerificationService:
    """Service for document verification and authenticity analysis"""
    
    def __init__(self):
        self.supported_document_types = [
            'drivers_license', 'passport', 'state_id', 'pay_stub', 
            'bank_statement', 'tax_return', 'employment_letter',
            'lease_agreement', 'utility_bill'
        ]
        self.ocr_confidence_threshold = 0.8
        self.authenticity_threshold = 0.85
        
    async def verify_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single document"""
        try:
            document_type = document_data.get('type')
            document_content = document_data.get('content')  # Base64 encoded or file path
            
            logger.info(f"Verifying document type: {document_type}")
            
            if document_type not in self.supported_document_types:
                return {
                    'success': False,
                    'error': f'Unsupported document type: {document_type}'
                }
            
            # Simulate document processing delay
            await asyncio.sleep(1)
            
            verification_result = {
                'document_id': f"DOC_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
                'document_type': document_type,
                'verification_date': datetime.now().isoformat(),
                'authenticity_analysis': await self._analyze_authenticity(document_data),
                'ocr_analysis': await self._perform_ocr_analysis(document_data),
                'data_extraction': await self._extract_document_data(document_data),
                'compliance_check': await self._check_document_compliance(document_data),
                'overall_score': 0,
                'verification_status': '',
                'confidence_level': 0
            }
            
            # Calculate overall verification score
            verification_result['overall_score'] = self._calculate_overall_score(verification_result)
            verification_result['confidence_level'] = self._calculate_confidence(verification_result)
            verification_result['verification_status'] = self._determine_verification_status(verification_result)
            
            logger.info(f"Document verification completed: {verification_result['verification_status']}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def verify_document_set(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify a set of documents and check for consistency"""
        try:
            logger.info(f"Verifying document set with {len(documents)} documents")
            
            individual_results = []
            for doc in documents:
                result = await self.verify_document(doc)
                if result.get('success', True):  # Default to True if not specified
                    individual_results.append(result)
            
            # Cross-reference analysis
            cross_reference_analysis = await self._perform_cross_reference_analysis(individual_results)
            
            # Calculate set-level scores
            average_authenticity = np.mean([r['overall_score'] for r in individual_results]) if individual_results else 0
            consistency_score = cross_reference_analysis.get('consistency_score', 0)
            
            overall_score = (average_authenticity * 0.7 + consistency_score * 0.3)
            
            return {
                'success': True,
                'verification_set_id': f"SET_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'total_documents': len(documents),
                'verified_documents': len(individual_results),
                'individual_results': individual_results,
                'cross_reference_analysis': cross_reference_analysis,
                'overall_score': overall_score,
                'set_verification_status': self._determine_set_status(overall_score, cross_reference_analysis),
                'recommendations': self._generate_document_recommendations(individual_results, cross_reference_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error verifying document set: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _analyze_authenticity(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document authenticity using various techniques"""
        try:
            document_type = document_data.get('type')
            
            # Simulate different authenticity checks
            authenticity_checks = {
                'watermark_detection': random.uniform(0.8, 1.0),
                'font_analysis': random.uniform(0.75, 0.98),
                'layout_verification': random.uniform(0.85, 0.99),
                'security_features': random.uniform(0.7, 0.95),
                'paper_quality': random.uniform(0.8, 0.98),
                'digital_signatures': random.uniform(0.9, 1.0) if document_type in ['bank_statement', 'tax_return'] else 0.0
            }
            
            # Simulate potential fraud indicators
            fraud_indicators = []
            if authenticity_checks['font_analysis'] < 0.8:
                fraud_indicators.append('Inconsistent font usage detected')
            if authenticity_checks['layout_verification'] < 0.85:
                fraud_indicators.append('Layout inconsistencies found')
            if authenticity_checks['security_features'] < 0.75:
                fraud_indicators.append('Missing or altered security features')
            
            # Calculate overall authenticity score
            scores = [score for score in authenticity_checks.values() if score > 0]
            overall_authenticity = np.mean(scores) if scores else 0.5
            
            # Add some randomness for edge cases
            if random.random() < 0.05:  # 5% chance of flagging as potentially fraudulent
                overall_authenticity *= 0.6
                fraud_indicators.append('Document flagged by AI anomaly detection')
            
            return {
                'overall_authenticity_score': overall_authenticity,
                'individual_checks': authenticity_checks,
                'fraud_indicators': fraud_indicators,
                'authenticity_level': self._classify_authenticity_level(overall_authenticity),
                'verification_method': 'ai_analysis',
                'processing_time_ms': random.randint(500, 2000)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing authenticity: {e}")
            return {'error': str(e)}
    
    async def _perform_ocr_analysis(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform OCR analysis on document"""
        try:
            document_type = document_data.get('type')
            
            # Simulate OCR confidence based on document type
            if document_type in ['drivers_license', 'passport', 'state_id']:
                ocr_confidence = random.uniform(0.85, 0.98)
            elif document_type in ['pay_stub', 'bank_statement']:
                ocr_confidence = random.uniform(0.80, 0.95)
            else:
                ocr_confidence = random.uniform(0.75, 0.92)
            
            # Simulate text extraction
            extracted_text_confidence = {}
            text_quality_issues = []
            
            if document_type == 'drivers_license':
                extracted_text_confidence = {
                    'name': random.uniform(0.9, 0.99),
                    'license_number': random.uniform(0.85, 0.98),
                    'address': random.uniform(0.8, 0.95),
                    'date_of_birth': random.uniform(0.9, 0.99),
                    'expiration_date': random.uniform(0.88, 0.97)
                }
            elif document_type == 'pay_stub':
                extracted_text_confidence = {
                    'employee_name': random.uniform(0.85, 0.98),
                    'employer_name': random.uniform(0.88, 0.96),
                    'pay_period': random.uniform(0.8, 0.94),
                    'gross_pay': random.uniform(0.85, 0.97),
                    'net_pay': random.uniform(0.87, 0.98)
                }
            
            # Check for quality issues
            if ocr_confidence < 0.85:
                text_quality_issues.append('Low overall OCR confidence')
            if min(extracted_text_confidence.values(), default=1.0) < 0.8:
                text_quality_issues.append('Some fields have low extraction confidence')
            
            return {
                'ocr_confidence': ocr_confidence,
                'text_extraction_confidence': extracted_text_confidence,
                'text_quality_issues': text_quality_issues,
                'language_detected': 'english',
                'processing_method': 'advanced_ocr',
                'character_count': random.randint(200, 1500)
            }
            
        except Exception as e:
            logger.error(f"Error performing OCR analysis: {e}")
            return {'error': str(e)}
    
    async def _extract_document_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from document"""
        try:
            document_type = document_data.get('type')
            
            # Simulate data extraction based on document type
            if document_type == 'drivers_license':
                extracted_data = {
                    'name': 'John A. Smith',
                    'license_number': f'DL{random.randint(1000000, 9999999)}',
                    'address': '123 Main St, Anytown, ST 12345',
                    'date_of_birth': '1985-03-15',
                    'expiration_date': '2025-03-15',
                    'state': 'ST',
                    'class': 'C'
                }
            elif document_type == 'pay_stub':
                gross_pay = random.randint(3000, 8000)
                extracted_data = {
                    'employee_name': 'John A. Smith',
                    'employer_name': 'ABC Corporation',
                    'pay_period_start': '2023-11-01',
                    'pay_period_end': '2023-11-15',
                    'gross_pay': gross_pay,
                    'net_pay': int(gross_pay * 0.75),
                    'year_to_date_gross': gross_pay * 24,
                    'deductions': int(gross_pay * 0.25)
                }
            elif document_type == 'bank_statement':
                extracted_data = {
                    'account_holder': 'John A. Smith',
                    'account_number': f'****{random.randint(1000, 9999)}',
                    'statement_period': '2023-11-01 to 2023-11-30',
                    'beginning_balance': random.randint(1000, 10000),
                    'ending_balance': random.randint(1500, 12000),
                    'total_deposits': random.randint(3000, 6000),
                    'total_withdrawals': random.randint(2000, 4000)
                }
            else:
                extracted_data = {
                    'document_date': datetime.now().strftime('%Y-%m-%d'),
                    'extraction_method': 'template_matching'
                }
            
            # Calculate extraction quality
            extraction_quality = random.uniform(0.8, 0.98)
            
            return {
                'extracted_data': extracted_data,
                'extraction_quality': extraction_quality,
                'data_completeness': random.uniform(0.85, 1.0),
                'structured_fields_count': len(extracted_data),
                'extraction_method': 'ai_powered'
            }
            
        except Exception as e:
            logger.error(f"Error extracting document data: {e}")
            return {'error': str(e)}
    
    async def _check_document_compliance(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check document compliance with requirements"""
        try:
            document_type = document_data.get('type')
            
            compliance_checks = {
                'format_compliance': random.uniform(0.9, 1.0),
                'data_completeness': random.uniform(0.85, 0.98),
                'date_validity': random.uniform(0.9, 1.0),
                'required_fields_present': random.uniform(0.88, 0.99)
            }
            
            compliance_issues = []
            
            # Check for specific compliance issues
            if document_type in ['drivers_license', 'passport', 'state_id']:
                # Check expiration
                if random.random() < 0.1:  # 10% chance of near expiration
                    compliance_issues.append('Document expires within 30 days')
                    compliance_checks['date_validity'] = 0.7
            
            if document_type == 'pay_stub':
                # Check recency
                if random.random() < 0.15:  # 15% chance of old pay stub
                    compliance_issues.append('Pay stub is older than 30 days')
                    compliance_checks['date_validity'] = 0.6
            
            # Overall compliance score
            overall_compliance = np.mean(list(compliance_checks.values()))
            
            return {
                'overall_compliance_score': overall_compliance,
                'individual_compliance_checks': compliance_checks,
                'compliance_issues': compliance_issues,
                'meets_minimum_requirements': overall_compliance >= 0.8,
                'recommendation': 'accept' if overall_compliance >= 0.85 else 'review' if overall_compliance >= 0.7 else 'reject'
            }
            
        except Exception as e:
            logger.error(f"Error checking document compliance: {e}")
            return {'error': str(e)}
    
    async def _perform_cross_reference_analysis(self, individual_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform cross-reference analysis across multiple documents"""
        try:
            if len(individual_results) < 2:
                return {
                    'consistency_score': 1.0,
                    'cross_reference_checks': [],
                    'inconsistencies_found': [],
                    'data_matches': []
                }
            
            inconsistencies = []
            data_matches = []
            cross_reference_checks = []
            
            # Extract common fields for comparison
            names = []
            addresses = []
            employers = []
            
            for result in individual_results:
                extracted_data = result.get('data_extraction', {}).get('extracted_data', {})
                
                # Collect names
                for field in ['name', 'employee_name', 'account_holder']:
                    if field in extracted_data:
                        names.append(extracted_data[field])
                
                # Collect addresses
                if 'address' in extracted_data:
                    addresses.append(extracted_data['address'])
                
                # Collect employers
                if 'employer_name' in extracted_data:
                    employers.append(extracted_data['employer_name'])
            
            # Check name consistency
            if len(set(names)) > 1:
                inconsistencies.append('Name variations found across documents')
                cross_reference_checks.append({
                    'check_type': 'name_consistency',
                    'status': 'inconsistent',
                    'details': f'Found names: {list(set(names))}'
                })
            else:
                data_matches.append('Names consistent across documents')
                cross_reference_checks.append({
                    'check_type': 'name_consistency',
                    'status': 'consistent'
                })
            
            # Check address consistency
            if len(addresses) > 1 and len(set(addresses)) > 1:
                inconsistencies.append('Address variations found')
                cross_reference_checks.append({
                    'check_type': 'address_consistency',
                    'status': 'inconsistent'
                })
            elif len(addresses) > 1:
                data_matches.append('Addresses consistent')
                cross_reference_checks.append({
                    'check_type': 'address_consistency',
                    'status': 'consistent'
                })
            
            # Calculate consistency score
            total_checks = len(cross_reference_checks)
            consistent_checks = sum(1 for check in cross_reference_checks if check['status'] == 'consistent')
            consistency_score = consistent_checks / total_checks if total_checks > 0 else 1.0
            
            return {
                'consistency_score': consistency_score,
                'cross_reference_checks': cross_reference_checks,
                'inconsistencies_found': inconsistencies,
                'data_matches': data_matches,
                'total_consistency_checks': total_checks,
                'passed_consistency_checks': consistent_checks
            }
            
        except Exception as e:
            logger.error(f"Error performing cross-reference analysis: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_score(self, verification_result: Dict[str, Any]) -> float:
        """Calculate overall verification score"""
        try:
            scores = []
            
            # Authenticity score (40% weight)
            authenticity = verification_result.get('authenticity_analysis', {})
            if 'overall_authenticity_score' in authenticity:
                scores.append(authenticity['overall_authenticity_score'] * 0.4)
            
            # OCR confidence (20% weight)
            ocr = verification_result.get('ocr_analysis', {})
            if 'ocr_confidence' in ocr:
                scores.append(ocr['ocr_confidence'] * 0.2)
            
            # Data extraction quality (20% weight)
            extraction = verification_result.get('data_extraction', {})
            if 'extraction_quality' in extraction:
                scores.append(extraction['extraction_quality'] * 0.2)
            
            # Compliance score (20% weight)
            compliance = verification_result.get('compliance_check', {})
            if 'overall_compliance_score' in compliance:
                scores.append(compliance['overall_compliance_score'] * 0.2)
            
            return sum(scores) if scores else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.5
    
    def _calculate_confidence(self, verification_result: Dict[str, Any]) -> float:
        """Calculate confidence level in verification"""
        try:
            confidence_factors = []
            
            # OCR confidence contributes to overall confidence
            ocr = verification_result.get('ocr_analysis', {})
            if 'ocr_confidence' in ocr:
                confidence_factors.append(ocr['ocr_confidence'])
            
            # Authenticity analysis confidence
            authenticity = verification_result.get('authenticity_analysis', {})
            if 'overall_authenticity_score' in authenticity:
                confidence_factors.append(authenticity['overall_authenticity_score'])
            
            # Data extraction confidence
            extraction = verification_result.get('data_extraction', {})
            if 'data_completeness' in extraction:
                confidence_factors.append(extraction['data_completeness'])
            
            return np.mean(confidence_factors) if confidence_factors else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _classify_authenticity_level(self, score: float) -> str:
        """Classify authenticity level based on score"""
        if score >= 0.95:
            return 'very_high'
        elif score >= 0.85:
            return 'high'
        elif score >= 0.75:
            return 'medium'
        elif score >= 0.60:
            return 'low'
        else:
            return 'very_low'
    
    def _determine_verification_status(self, verification_result: Dict[str, Any]) -> str:
        """Determine overall verification status"""
        overall_score = verification_result.get('overall_score', 0)
        confidence = verification_result.get('confidence_level', 0)
        
        if overall_score >= 0.85 and confidence >= 0.8:
            return 'verified'
        elif overall_score >= 0.70 and confidence >= 0.6:
            return 'conditionally_verified'
        elif overall_score >= 0.50:
            return 'requires_review'
        else:
            return 'rejected'
    
    def _determine_set_status(self, overall_score: float, cross_reference: Dict[str, Any]) -> str:
        """Determine verification status for document set"""
        consistency_score = cross_reference.get('consistency_score', 0)
        
        if overall_score >= 0.85 and consistency_score >= 0.9:
            return 'verified'
        elif overall_score >= 0.70 and consistency_score >= 0.7:
            return 'conditionally_verified'
        else:
            return 'requires_review'
    
    def _generate_document_recommendations(self, individual_results: List[Dict[str, Any]], cross_reference: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        # Check for low-scoring documents
        low_score_docs = [r for r in individual_results if r.get('overall_score', 0) < 0.7]
        if low_score_docs:
            recommendations.append(f'Request re-submission of {len(low_score_docs)} document(s) with low verification scores')
        
        # Check for authenticity issues
        authenticity_issues = [r for r in individual_results 
                             if r.get('authenticity_analysis', {}).get('fraud_indicators')]
        if authenticity_issues:
            recommendations.append('Manual review recommended due to potential authenticity concerns')
        
        # Check for consistency issues
        inconsistencies = cross_reference.get('inconsistencies_found', [])
        if inconsistencies:
            recommendations.append('Resolve data inconsistencies between documents')
        
        # Check for compliance issues
        compliance_issues = []
        for result in individual_results:
            compliance = result.get('compliance_check', {})
            issues = compliance.get('compliance_issues', [])
            compliance_issues.extend(issues)
        
        if compliance_issues:
            recommendations.append('Address document compliance issues before approval')
        
        if not recommendations:
            recommendations.append('All documents passed verification - proceed with application review')
        
        return recommendations


# Global service instance
_document_verification_service = None


def get_document_verification_service() -> DocumentVerificationService:
    """Get or create the document verification service instance"""
    global _document_verification_service
    if _document_verification_service is None:
        _document_verification_service = DocumentVerificationService()
    return _document_verification_service