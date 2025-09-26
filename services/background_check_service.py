"""
Background Check Service
Integration with background check providers and criminal history analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import random

logger = logging.getLogger(__name__)


class BackgroundCheckService:
    """Service for background checks and criminal history analysis"""
    
    def __init__(self):
        self.api_endpoints = {
            'checkr': 'https://api.checkr.com/v1',
            'sterling': 'https://api.sterlingcheck.com/v2',
            'hireright': 'https://api.hireright.com/v1'
        }
        self.credentials = {}  # Would be loaded from secure config
        
    async def run_background_check(self, applicant_data: Dict[str, Any], check_type: str = 'comprehensive') -> Dict[str, Any]:
        """Run background check on applicant"""
        try:
            logger.info(f"Running {check_type} background check")
            
            # Simulate API call delay
            await asyncio.sleep(2)
            
            # Generate mock background check results
            background_result = {
                'check_id': f"BG_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'check_type': check_type,
                'status': 'completed',
                'completion_date': datetime.now().isoformat(),
                'criminal_history': await self._check_criminal_history(applicant_data),
                'sex_offender_registry': await self._check_sex_offender_registry(applicant_data),
                'eviction_history': await self._check_eviction_history(applicant_data),
                'identity_verification': await self._verify_identity(applicant_data),
                'address_history': await self._verify_address_history(applicant_data),
                'employment_verification': await self._verify_employment(applicant_data),
                'overall_risk_assessment': {}
            }
            
            # Calculate overall risk assessment
            background_result['overall_risk_assessment'] = await self._calculate_overall_risk(background_result)
            
            logger.info("Background check completed successfully")
            return background_result
            
        except Exception as e:
            logger.error(f"Error running background check: {e}")
            return {'error': str(e)}
    
    async def _check_criminal_history(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check criminal history"""
        try:
            # Mock criminal history check
            # In reality, this would query various criminal databases
            
            # Simulate very low crime rate (5% chance of any criminal record)
            has_record = random.random() < 0.05
            
            if not has_record:
                return {
                    'status': 'clear',
                    'records_found': 0,
                    'jurisdictions_searched': ['county', 'state', 'federal'],
                    'search_completed': True,
                    'records': []
                }
            else:
                # Generate a minor record
                return {
                    'status': 'records_found',
                    'records_found': 1,
                    'jurisdictions_searched': ['county', 'state', 'federal'],
                    'search_completed': True,
                    'records': [
                        {
                            'type': 'misdemeanor',
                            'charge': 'Traffic violation',
                            'date': (datetime.now() - timedelta(days=random.randint(365, 1825))).isoformat(),
                            'disposition': 'Fine paid',
                            'jurisdiction': 'County Court',
                            'severity': 'minor'
                        }
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error checking criminal history: {e}")
            return {'error': str(e)}
    
    async def _check_sex_offender_registry(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check sex offender registry"""
        try:
            # Mock sex offender registry check
            # This should always be clear in testing scenarios
            
            return {
                'status': 'clear',
                'registries_searched': ['national', 'state', 'local'],
                'search_completed': True,
                'matches_found': 0,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking sex offender registry: {e}")
            return {'error': str(e)}
    
    async def _check_eviction_history(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check eviction history"""
        try:
            # Mock eviction history check
            # Use existing eviction count if provided
            eviction_count = applicant_data.get('previous_evictions', 0)
            
            if eviction_count == 0:
                return {
                    'status': 'clear',
                    'evictions_found': 0,
                    'jurisdictions_searched': ['county', 'state'],
                    'search_completed': True,
                    'records': []
                }
            else:
                # Generate eviction records
                records = []
                for i in range(eviction_count):
                    records.append({
                        'date_filed': (datetime.now() - timedelta(days=random.randint(365, 2555))).isoformat(),
                        'court': 'Local Housing Court',
                        'case_number': f"EV{random.randint(100000, 999999)}",
                        'disposition': 'Judgment for landlord',
                        'amount_owed': random.randint(1000, 5000),
                        'status': 'satisfied' if random.random() < 0.7 else 'outstanding'
                    })
                
                return {
                    'status': 'records_found',
                    'evictions_found': eviction_count,
                    'jurisdictions_searched': ['county', 'state'],
                    'search_completed': True,
                    'records': records
                }
                
        except Exception as e:
            logger.error(f"Error checking eviction history: {e}")
            return {'error': str(e)}
    
    async def _verify_identity(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify applicant identity"""
        try:
            # Mock identity verification
            # Simulate high success rate (95%)
            verification_score = random.uniform(0.85, 1.0)
            
            return {
                'status': 'verified' if verification_score > 0.9 else 'partial_verification',
                'verification_score': verification_score,
                'ssn_verified': verification_score > 0.9,
                'name_match': verification_score > 0.85,
                'address_match': verification_score > 0.88,
                'phone_verified': verification_score > 0.92,
                'identity_confidence': 'high' if verification_score > 0.95 else 'medium' if verification_score > 0.85 else 'low',
                'verification_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verifying identity: {e}")
            return {'error': str(e)}
    
    async def _verify_address_history(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify address history"""
        try:
            # Mock address history verification
            addresses_provided = applicant_data.get('previous_addresses', [])
            
            if not addresses_provided:
                # Generate mock address history
                addresses_provided = [
                    {
                        'address': '123 Current St, City, ST 12345',
                        'duration_months': 24,
                        'residence_type': 'rental'
                    },
                    {
                        'address': '456 Previous Ave, City, ST 12345',
                        'duration_months': 36,
                        'residence_type': 'rental'
                    }
                ]
            
            verified_addresses = []
            for addr in addresses_provided:
                verified_addresses.append({
                    **addr,
                    'verified': random.random() > 0.1,  # 90% verification rate
                    'verification_method': 'postal_records',
                    'confidence': 'high'
                })
            
            verification_rate = sum(1 for addr in verified_addresses if addr['verified']) / len(verified_addresses)
            
            return {
                'status': 'verified' if verification_rate > 0.8 else 'partial_verification',
                'addresses_provided': len(addresses_provided),
                'addresses_verified': sum(1 for addr in verified_addresses if addr['verified']),
                'verification_rate': verification_rate,
                'address_history': verified_addresses,
                'gaps_identified': verification_rate < 0.9,
                'stability_score': min(1.0, sum(addr.get('duration_months', 0) for addr in addresses_provided) / 60)
            }
            
        except Exception as e:
            logger.error(f"Error verifying address history: {e}")
            return {'error': str(e)}
    
    async def _verify_employment(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify employment information"""
        try:
            # Mock employment verification
            employment_type = applicant_data.get('employment_type', 'full_time')
            employment_length = applicant_data.get('employment_length_months', 12)
            
            # Higher verification rate for full-time employment
            if employment_type == 'full_time':
                verification_success = random.random() > 0.1  # 90% success rate
            elif employment_type == 'part_time':
                verification_success = random.random() > 0.2  # 80% success rate
            elif employment_type == 'self_employed':
                verification_success = random.random() > 0.4  # 60% success rate
            else:
                verification_success = random.random() > 0.5  # 50% success rate
            
            if verification_success:
                return {
                    'status': 'verified',
                    'employer_verified': True,
                    'position_verified': True,
                    'employment_dates_verified': True,
                    'income_verified': True,
                    'employment_type': employment_type,
                    'verification_method': 'direct_contact',
                    'verification_confidence': 'high',
                    'employment_stability_score': min(1.0, employment_length / 24)  # 2 years = max score
                }
            else:
                return {
                    'status': 'unable_to_verify',
                    'employer_verified': False,
                    'position_verified': False,
                    'employment_dates_verified': False,
                    'income_verified': False,
                    'employment_type': employment_type,
                    'verification_method': 'attempted_contact',
                    'verification_confidence': 'low',
                    'employment_stability_score': 0.5,  # Default moderate score when unverified
                    'verification_notes': 'Employer did not respond to verification requests'
                }
                
        except Exception as e:
            logger.error(f"Error verifying employment: {e}")
            return {'error': str(e)}
    
    async def _calculate_overall_risk(self, background_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk assessment from background check"""
        try:
            risk_score = 20  # Base risk score (lower is better)
            risk_factors = []
            
            # Criminal history risk
            criminal_history = background_result.get('criminal_history', {})
            if criminal_history.get('status') == 'records_found':
                records = criminal_history.get('records', [])
                for record in records:
                    if record.get('severity') == 'minor':
                        risk_score += 10
                        risk_factors.append('Minor criminal record')
                    elif record.get('severity') == 'moderate':
                        risk_score += 25
                        risk_factors.append('Moderate criminal record')
                    elif record.get('severity') == 'major':
                        risk_score += 50
                        risk_factors.append('Serious criminal record')
            
            # Sex offender registry risk
            sex_offender = background_result.get('sex_offender_registry', {})
            if sex_offender.get('matches_found', 0) > 0:
                risk_score += 100  # Maximum risk
                risk_factors.append('Sex offender registry match')
            
            # Eviction history risk
            eviction_history = background_result.get('eviction_history', {})
            evictions_found = eviction_history.get('evictions_found', 0)
            if evictions_found > 0:
                risk_score += evictions_found * 15
                risk_factors.append(f'{evictions_found} eviction(s) found')
            
            # Identity verification risk
            identity = background_result.get('identity_verification', {})
            if identity.get('identity_confidence') == 'low':
                risk_score += 20
                risk_factors.append('Low identity verification confidence')
            elif identity.get('identity_confidence') == 'medium':
                risk_score += 10
                risk_factors.append('Medium identity verification confidence')
            
            # Employment verification risk
            employment = background_result.get('employment_verification', {})
            if employment.get('status') == 'unable_to_verify':
                risk_score += 15
                risk_factors.append('Unable to verify employment')
            
            # Address verification risk
            address_history = background_result.get('address_history', {})
            if address_history.get('verification_rate', 1) < 0.8:
                risk_score += 10
                risk_factors.append('Low address verification rate')
            
            # Determine risk level
            if risk_score <= 30:
                risk_level = 'low'
            elif risk_score <= 50:
                risk_level = 'medium'
            elif risk_score <= 75:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            # Calculate tenant suitability score (inverse of risk)
            suitability_score = max(0, 100 - risk_score)
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'suitability_score': suitability_score,
                'tenant_recommendation': self._generate_tenant_recommendation(risk_level, risk_factors),
                'additional_requirements': self._generate_additional_requirements(risk_level, risk_factors),
                'assessment_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall risk: {e}")
            return {'error': str(e)}
    
    def _generate_tenant_recommendation(self, risk_level: str, risk_factors: List[str]) -> str:
        """Generate tenant recommendation based on risk assessment"""
        if risk_level == 'low':
            return 'approve'
        elif risk_level == 'medium':
            if any('criminal' in factor.lower() for factor in risk_factors):
                return 'conditional_approve'
            else:
                return 'approve'
        elif risk_level == 'high':
            if any('sex offender' in factor.lower() for factor in risk_factors):
                return 'decline'
            else:
                return 'conditional_approve'
        else:  # critical
            return 'decline'
    
    def _generate_additional_requirements(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Generate additional requirements based on risk factors"""
        requirements = []
        
        if risk_level == 'medium':
            requirements.append('Increase security deposit by 50%')
            requirements.append('Require additional references')
        
        elif risk_level == 'high':
            requirements.append('Increase security deposit by 100%')
            requirements.append('Require cosigner')
            requirements.append('Monthly income verification')
        
        elif risk_level == 'critical':
            requirements.append('Application declined')
        
        # Specific requirements based on risk factors
        if any('eviction' in factor.lower() for factor in risk_factors):
            requirements.append('Provide proof of current rental payment history')
        
        if any('employment' in factor.lower() for factor in risk_factors):
            requirements.append('Provide additional income documentation')
        
        if any('identity' in factor.lower() for factor in risk_factors):
            requirements.append('Additional identity verification required')
        
        return list(set(requirements))  # Remove duplicates


# Global service instance
_background_check_service = None


def get_background_check_service() -> BackgroundCheckService:
    """Get or create the background check service instance"""
    global _background_check_service
    if _background_check_service is None:
        _background_check_service = BackgroundCheckService()
    return _background_check_service