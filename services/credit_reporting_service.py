"""
Credit Reporting Service
Integration with credit reporting APIs and credit analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
import json

logger = logging.getLogger(__name__)


class CreditReportingService:
    """Service for credit reporting and analysis"""
    
    def __init__(self):
        self.api_endpoints = {
            'experian': 'https://sandbox.api.experian.com',
            'equifax': 'https://sandbox.api.equifax.com',
            'transunion': 'https://sandbox.api.transunion.com'
        }
        self.credentials = {}  # Would be loaded from secure config
        
    async def get_credit_report(self, applicant_data: Dict[str, Any], bureau: str = 'experian') -> Dict[str, Any]:
        """Get credit report from specified bureau"""
        try:
            # This is a mock implementation - real integration would use actual APIs
            logger.info(f"Requesting credit report from {bureau}")
            
            # Simulate API call delay
            await asyncio.sleep(1)
            
            # Generate mock credit report based on existing credit score
            credit_score = applicant_data.get('credit_score', 650)
            
            mock_report = {
                'credit_score': credit_score,
                'bureau': bureau,
                'report_date': datetime.now().isoformat(),
                'payment_history': self._generate_payment_history(credit_score),
                'credit_utilization': self._calculate_credit_utilization(credit_score),
                'account_mix': self._generate_account_mix(credit_score),
                'credit_inquiries': self._generate_inquiries(credit_score),
                'derogatory_marks': self._generate_derogatory_marks(credit_score),
                'credit_age': self._calculate_credit_age(credit_score)
            }
            
            logger.info(f"Credit report retrieved successfully from {bureau}")
            return mock_report
            
        except Exception as e:
            logger.error(f"Error getting credit report from {bureau}: {e}")
            return {'error': str(e)}
    
    def _generate_payment_history(self, credit_score: int) -> Dict[str, Any]:
        """Generate mock payment history based on credit score"""
        if credit_score >= 750:
            return {
                'on_time_percentage': 98.5,
                'late_30_days': 1,
                'late_60_days': 0,
                'late_90_days': 0,
                'collections': 0,
                'charge_offs': 0
            }
        elif credit_score >= 700:
            return {
                'on_time_percentage': 92.0,
                'late_30_days': 3,
                'late_60_days': 1,
                'late_90_days': 0,
                'collections': 0,
                'charge_offs': 0
            }
        elif credit_score >= 650:
            return {
                'on_time_percentage': 85.0,
                'late_30_days': 6,
                'late_60_days': 2,
                'late_90_days': 1,
                'collections': 0,
                'charge_offs': 0
            }
        else:
            return {
                'on_time_percentage': 75.0,
                'late_30_days': 10,
                'late_60_days': 4,
                'late_90_days': 2,
                'collections': 1,
                'charge_offs': 0
            }
    
    def _calculate_credit_utilization(self, credit_score: int) -> Dict[str, Any]:
        """Calculate mock credit utilization based on score"""
        if credit_score >= 750:
            utilization = 0.15
        elif credit_score >= 700:
            utilization = 0.25
        elif credit_score >= 650:
            utilization = 0.40
        else:
            utilization = 0.65
            
        return {
            'overall_utilization': utilization,
            'per_card_utilization': [utilization * 0.8, utilization * 1.2, utilization * 0.9],
            'total_credit_limit': 25000,
            'total_balance': int(25000 * utilization)
        }
    
    def _generate_account_mix(self, credit_score: int) -> Dict[str, Any]:
        """Generate mock account mix based on credit score"""
        if credit_score >= 700:
            return {
                'credit_cards': 4,
                'auto_loans': 1,
                'mortgage': 1,
                'student_loans': 0,
                'personal_loans': 0,
                'total_accounts': 6
            }
        else:
            return {
                'credit_cards': 2,
                'auto_loans': 0,
                'mortgage': 0,
                'student_loans': 1,
                'personal_loans': 1,
                'total_accounts': 4
            }
    
    def _generate_inquiries(self, credit_score: int) -> Dict[str, Any]:
        """Generate mock credit inquiries based on score"""
        if credit_score >= 750:
            recent_inquiries = 1
        elif credit_score >= 700:
            recent_inquiries = 2
        elif credit_score >= 650:
            recent_inquiries = 3
        else:
            recent_inquiries = 5
            
        return {
            'hard_inquiries_6_months': recent_inquiries,
            'hard_inquiries_12_months': recent_inquiries + 1,
            'soft_inquiries': 8,
            'recent_inquiries': [
                {
                    'date': (datetime.now() - timedelta(days=30)).isoformat(),
                    'creditor': 'Credit Card Company',
                    'type': 'hard'
                }
            ]
        }
    
    def _generate_derogatory_marks(self, credit_score: int) -> Dict[str, Any]:
        """Generate mock derogatory marks based on credit score"""
        if credit_score >= 700:
            return {
                'bankruptcies': 0,
                'foreclosures': 0,
                'tax_liens': 0,
                'judgments': 0,
                'collections': 0
            }
        elif credit_score >= 650:
            return {
                'bankruptcies': 0,
                'foreclosures': 0,
                'tax_liens': 0,
                'judgments': 0,
                'collections': 1
            }
        else:
            return {
                'bankruptcies': 0,
                'foreclosures': 0,
                'tax_liens': 0,
                'judgments': 1,
                'collections': 2
            }
    
    def _calculate_credit_age(self, credit_score: int) -> Dict[str, Any]:
        """Calculate mock credit age based on score"""
        if credit_score >= 750:
            average_age_months = 84  # 7 years
            oldest_account_months = 120  # 10 years
        elif credit_score >= 700:
            average_age_months = 60  # 5 years
            oldest_account_months = 84  # 7 years
        elif credit_score >= 650:
            average_age_months = 36  # 3 years
            oldest_account_months = 60  # 5 years
        else:
            average_age_months = 24  # 2 years
            oldest_account_months = 36  # 3 years
            
        return {
            'average_account_age_months': average_age_months,
            'oldest_account_months': oldest_account_months,
            'newest_account_months': 6
        }
    
    async def analyze_credit_risk(self, credit_report: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze credit risk from credit report"""
        try:
            credit_score = credit_report.get('credit_score', 650)
            payment_history = credit_report.get('payment_history', {})
            utilization = credit_report.get('credit_utilization', {})
            inquiries = credit_report.get('credit_inquiries', {})
            derogatory = credit_report.get('derogatory_marks', {})
            
            # Calculate risk factors
            risk_factors = []
            risk_score = 50  # Base risk score
            
            # Payment history risk
            on_time_pct = payment_history.get('on_time_percentage', 90)
            if on_time_pct < 85:
                risk_factors.append('Poor payment history')
                risk_score += 20
            elif on_time_pct > 95:
                risk_score -= 10
            
            # Utilization risk
            overall_util = utilization.get('overall_utilization', 0.3)
            if overall_util > 0.5:
                risk_factors.append('High credit utilization')
                risk_score += 15
            elif overall_util < 0.2:
                risk_score -= 5
            
            # Recent inquiries risk
            recent_inquiries = inquiries.get('hard_inquiries_6_months', 0)
            if recent_inquiries > 3:
                risk_factors.append('Multiple recent credit inquiries')
                risk_score += 10
            
            # Derogatory marks risk
            total_derogatory = sum(derogatory.values())
            if total_derogatory > 0:
                risk_factors.append('Derogatory marks present')
                risk_score += total_derogatory * 15
            
            # Credit score adjustment
            if credit_score >= 750:
                risk_score -= 20
            elif credit_score >= 700:
                risk_score -= 10
            elif credit_score < 600:
                risk_score += 25
            
            risk_score = max(0, min(100, risk_score))
            
            # Determine risk level
            if risk_score < 25:
                risk_level = 'low'
            elif risk_score < 50:
                risk_level = 'medium'
            elif risk_score < 75:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            # Payment probability
            payment_probability = 1 - (risk_score / 100) * 0.5
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'payment_probability': payment_probability,
                'recommended_deposit_multiplier': 1.0 + (risk_score / 100),
                'analysis_date': datetime.now().isoformat(),
                'credit_strengths': self._identify_credit_strengths(credit_report),
                'improvement_suggestions': self._generate_improvement_suggestions(risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing credit risk: {e}")
            return {'error': str(e)}
    
    def _identify_credit_strengths(self, credit_report: Dict[str, Any]) -> List[str]:
        """Identify credit strengths from report"""
        strengths = []
        
        credit_score = credit_report.get('credit_score', 650)
        payment_history = credit_report.get('payment_history', {})
        utilization = credit_report.get('credit_utilization', {})
        credit_age = credit_report.get('credit_age', {})
        
        if credit_score >= 750:
            strengths.append('Excellent credit score')
        elif credit_score >= 700:
            strengths.append('Good credit score')
        
        if payment_history.get('on_time_percentage', 0) > 95:
            strengths.append('Excellent payment history')
        
        if utilization.get('overall_utilization', 1) < 0.2:
            strengths.append('Low credit utilization')
        
        if credit_age.get('average_account_age_months', 0) > 60:
            strengths.append('Established credit history')
        
        if payment_history.get('collections', 1) == 0 and payment_history.get('charge_offs', 1) == 0:
            strengths.append('No collections or charge-offs')
        
        return strengths
    
    def _generate_improvement_suggestions(self, risk_factors: List[str]) -> List[str]:
        """Generate suggestions for credit improvement"""
        suggestions = []
        
        for factor in risk_factors:
            if 'payment history' in factor.lower():
                suggestions.append('Focus on making all payments on time going forward')
            elif 'utilization' in factor.lower():
                suggestions.append('Pay down credit card balances to reduce utilization')
            elif 'inquiries' in factor.lower():
                suggestions.append('Avoid applying for new credit in the near term')
            elif 'derogatory' in factor.lower():
                suggestions.append('Work on resolving any outstanding collections or judgments')
        
        if not suggestions:
            suggestions.append('Continue maintaining good credit habits')
        
        return suggestions


# Global service instance
_credit_reporting_service = None


def get_credit_reporting_service() -> CreditReportingService:
    """Get or create the credit reporting service instance"""
    global _credit_reporting_service
    if _credit_reporting_service is None:
        _credit_reporting_service = CreditReportingService()
    return _credit_reporting_service