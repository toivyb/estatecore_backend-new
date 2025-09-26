"""
Violation Detection & Prevention System
Proactive identification and prevention of compliance violations
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import sessionmaker
import json
import asyncio

from models.base import db
from models.compliance import (
    ComplianceViolation, ComplianceRequirement, RegulatoryKnowledgeBase,
    ViolationSeverity, ComplianceStatus, RegulationType, ComplianceAlert,
    ComplianceMetrics
)
from ai_modules.compliance.ai_compliance_monitor import get_ai_compliance_monitor, ComplianceRisk, ViolationPrediction
from services.regulatory_knowledge_service import get_regulatory_knowledge_service


logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ViolationPattern:
    """Data structure for violation patterns"""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    properties_affected: List[str]
    risk_score: float
    prevention_strategies: List[str]


@dataclass
class PreventionRecommendation:
    """Data structure for prevention recommendations"""
    property_id: str
    recommendation_type: str
    priority: ViolationSeverity
    description: str
    estimated_cost: Optional[float]
    estimated_impact: float
    implementation_timeline: str
    success_probability: float


@dataclass
class ComplianceGap:
    """Data structure for compliance gaps"""
    property_id: str
    regulation_type: RegulationType
    gap_type: str
    description: str
    severity: ViolationSeverity
    time_to_violation: Optional[int]  # Days until likely violation
    remediation_actions: List[str]


class ViolationPatternAnalyzer:
    """Analyzes patterns in compliance violations"""
    
    def __init__(self):
        self.session = db.session
        
    def analyze_violation_patterns(
        self, 
        lookback_days: int = 365,
        min_frequency: int = 2
    ) -> List[ViolationPattern]:
        """Analyze patterns in historical violations"""
        patterns = []
        
        try:
            # Get violations from the specified period
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            violations = self.session.query(ComplianceViolation).filter(
                ComplianceViolation.detected_date >= cutoff_date
            ).all()
            
            if not violations:
                return patterns
            
            # Group violations by type
            violation_groups = {}
            for violation in violations:
                key = violation.violation_type
                if key not in violation_groups:
                    violation_groups[key] = []
                violation_groups[key].append(violation)
            
            # Analyze each group for patterns
            for violation_type, group_violations in violation_groups.items():
                if len(group_violations) >= min_frequency:
                    pattern = self._analyze_violation_group(violation_type, group_violations)
                    if pattern:
                        patterns.append(pattern)
            
            # Look for seasonal patterns
            seasonal_patterns = self._analyze_seasonal_patterns(violations)
            patterns.extend(seasonal_patterns)
            
            # Look for property-specific patterns
            property_patterns = self._analyze_property_patterns(violations)
            patterns.extend(property_patterns)
            
            logger.info(f"Identified {len(patterns)} violation patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing violation patterns: {e}")
            return []
    
    def _analyze_violation_group(self, violation_type: str, violations: List[ComplianceViolation]) -> Optional[ViolationPattern]:
        """Analyze a group of similar violations"""
        try:
            # Calculate frequency and affected properties
            frequency = len(violations)
            properties_affected = list(set(v.property_id for v in violations))
            
            # Calculate average risk score
            severity_scores = {
                ViolationSeverity.CRITICAL: 100,
                ViolationSeverity.HIGH: 80,
                ViolationSeverity.MEDIUM: 60,
                ViolationSeverity.LOW: 40,
                ViolationSeverity.INFORMATIONAL: 20
            }
            
            avg_risk = np.mean([severity_scores.get(v.severity, 60) for v in violations])
            
            # Identify common factors
            common_factors = self._identify_common_factors(violations)
            
            # Generate prevention strategies
            prevention_strategies = self._generate_prevention_strategies(violation_type, common_factors)
            
            return ViolationPattern(
                pattern_id=f"pattern_{violation_type}_{datetime.now().strftime('%Y%m%d')}",
                pattern_type=violation_type,
                description=f"Recurring {violation_type} violations affecting {len(properties_affected)} properties",
                frequency=frequency,
                properties_affected=properties_affected,
                risk_score=avg_risk,
                prevention_strategies=prevention_strategies
            )
            
        except Exception as e:
            logger.error(f"Error analyzing violation group: {e}")
            return None
    
    def _analyze_seasonal_patterns(self, violations: List[ComplianceViolation]) -> List[ViolationPattern]:
        """Analyze seasonal violation patterns"""
        patterns = []
        
        try:
            # Group violations by month
            monthly_violations = {}
            for violation in violations:
                month = violation.detected_date.month
                if month not in monthly_violations:
                    monthly_violations[month] = []
                monthly_violations[month].append(violation)
            
            # Look for months with significantly higher violation rates
            avg_monthly_violations = len(violations) / 12
            high_months = []
            
            for month, month_violations in monthly_violations.items():
                if len(month_violations) > avg_monthly_violations * 1.5:  # 50% above average
                    high_months.append((month, month_violations))
            
            # Create patterns for high-violation months
            for month, month_violations in high_months:
                pattern = ViolationPattern(
                    pattern_id=f"seasonal_month_{month}",
                    pattern_type="seasonal",
                    description=f"Increased violations in month {month}",
                    frequency=len(month_violations),
                    properties_affected=list(set(v.property_id for v in month_violations)),
                    risk_score=75.0,
                    prevention_strategies=[
                        f"Increase monitoring in month {month}",
                        "Schedule preventive inspections before peak violation period",
                        "Review seasonal maintenance schedules"
                    ]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing seasonal patterns: {e}")
            return []
    
    def _analyze_property_patterns(self, violations: List[ComplianceViolation]) -> List[ViolationPattern]:
        """Analyze property-specific violation patterns"""
        patterns = []
        
        try:
            # Group violations by property
            property_violations = {}
            for violation in violations:
                prop_id = violation.property_id
                if prop_id not in property_violations:
                    property_violations[prop_id] = []
                property_violations[prop_id].append(violation)
            
            # Find properties with high violation rates
            avg_violations_per_property = len(violations) / len(property_violations) if property_violations else 0
            
            for prop_id, prop_violations in property_violations.items():
                if len(prop_violations) > max(3, avg_violations_per_property * 2):  # Significantly above average
                    pattern = ViolationPattern(
                        pattern_id=f"property_{prop_id}_pattern",
                        pattern_type="property_specific",
                        description=f"Property {prop_id} has recurring violations",
                        frequency=len(prop_violations),
                        properties_affected=[prop_id],
                        risk_score=85.0,
                        prevention_strategies=[
                            "Comprehensive property audit required",
                            "Enhanced monitoring for this property",
                            "Management review and improvement plan"
                        ]
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing property patterns: {e}")
            return []
    
    def _identify_common_factors(self, violations: List[ComplianceViolation]) -> List[str]:
        """Identify common factors across violations"""
        factors = []
        
        try:
            # Analyze detection methods
            detection_methods = [v.detection_method for v in violations if v.detection_method]
            if detection_methods:
                most_common_method = max(set(detection_methods), key=detection_methods.count)
                if detection_methods.count(most_common_method) > len(violations) * 0.5:
                    factors.append(f"Most detected via {most_common_method}")
            
            # Analyze timing patterns
            hours = [v.detected_date.hour for v in violations]
            if hours:
                avg_hour = np.mean(hours)
                if 9 <= avg_hour <= 17:
                    factors.append("Violations typically detected during business hours")
                elif 18 <= avg_hour <= 23 or 0 <= avg_hour <= 6:
                    factors.append("Violations typically detected outside business hours")
            
            # Analyze resolution times
            resolution_times = []
            for v in violations:
                if v.resolved_date and v.detected_date:
                    resolution_times.append((v.resolved_date - v.detected_date).days)
            
            if resolution_times:
                avg_resolution = np.mean(resolution_times)
                if avg_resolution > 30:
                    factors.append("Violations take longer than average to resolve")
                elif avg_resolution < 7:
                    factors.append("Violations resolved quickly")
            
            return factors
            
        except Exception as e:
            logger.error(f"Error identifying common factors: {e}")
            return []
    
    def _generate_prevention_strategies(self, violation_type: str, common_factors: List[str]) -> List[str]:
        """Generate prevention strategies based on violation type and factors"""
        strategies = []
        
        # Type-specific strategies
        if 'maintenance' in violation_type.lower():
            strategies.extend([
                "Implement predictive maintenance program",
                "Increase routine inspection frequency",
                "Improve tenant communication for maintenance requests"
            ])
        elif 'fair_housing' in violation_type.lower():
            strategies.extend([
                "Enhance fair housing training for staff",
                "Review and update tenant screening procedures",
                "Implement bias-free application process"
            ])
        elif 'safety' in violation_type.lower():
            strategies.extend([
                "Increase safety inspections",
                "Update safety equipment and procedures",
                "Implement safety monitoring systems"
            ])
        
        # Factor-based strategies
        for factor in common_factors:
            if "business hours" in factor:
                strategies.append("Implement 24/7 monitoring systems")
            elif "longer than average to resolve" in factor:
                strategies.append("Streamline violation resolution process")
            elif "AI" in factor or "automated" in factor:
                strategies.append("Review AI detection parameters for accuracy")
        
        # Default strategies
        if not strategies:
            strategies.extend([
                "Increase monitoring frequency",
                "Implement preventive measures",
                "Enhance staff training"
            ])
        
        return strategies


class RiskScoringEngine:
    """Advanced risk scoring for compliance violations"""
    
    def __init__(self):
        self.session = db.session
        self.ai_monitor = get_ai_compliance_monitor()
        
        # Risk factors and their weights
        self.risk_factors = {
            'historical_violations': 0.3,
            'property_age': 0.15,
            'property_size': 0.1,
            'affordable_housing_program': 0.2,
            'recent_complaints': 0.15,
            'inspection_failures': 0.25,
            'maintenance_backlog': 0.2,
            'staff_training_status': 0.15,
            'document_compliance': 0.2
        }
    
    def calculate_comprehensive_risk_score(self, property_id: str) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a property"""
        try:
            # Get property data
            property_data = self._get_property_data(property_id)
            
            # Calculate individual risk factor scores
            factor_scores = {}
            
            factor_scores['historical_violations'] = self._score_historical_violations(property_id)
            factor_scores['property_age'] = self._score_property_age(property_data)
            factor_scores['property_size'] = self._score_property_size(property_data)
            factor_scores['affordable_housing_program'] = self._score_affordable_housing(property_data)
            factor_scores['recent_complaints'] = self._score_recent_complaints(property_id)
            factor_scores['inspection_failures'] = self._score_inspection_failures(property_id)
            factor_scores['maintenance_backlog'] = self._score_maintenance_backlog(property_id)
            factor_scores['staff_training_status'] = self._score_staff_training(property_data)
            factor_scores['document_compliance'] = self._score_document_compliance(property_id)
            
            # Calculate weighted overall score
            overall_score = sum(
                score * self.risk_factors[factor] 
                for factor, score in factor_scores.items()
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)
            
            # Generate risk factors summary
            high_risk_factors = [
                factor for factor, score in factor_scores.items() 
                if score > 70
            ]
            
            return {
                'overall_score': round(overall_score, 2),
                'risk_level': risk_level,
                'factor_scores': factor_scores,
                'high_risk_factors': high_risk_factors,
                'calculated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return {
                'overall_score': 50.0,
                'risk_level': RiskLevel.MEDIUM,
                'factor_scores': {},
                'high_risk_factors': [],
                'calculated_at': datetime.now(),
                'error': str(e)
            }
    
    def _score_historical_violations(self, property_id: str) -> float:
        """Score based on historical violations"""
        try:
            # Get violations from last 2 years
            cutoff_date = datetime.now() - timedelta(days=730)
            violations = self.session.query(ComplianceViolation).filter(
                and_(
                    ComplianceViolation.property_id == property_id,
                    ComplianceViolation.detected_date >= cutoff_date
                )
            ).all()
            
            if not violations:
                return 10.0  # Low risk if no violations
            
            # Weight by severity and recency
            score = 0
            for violation in violations:
                severity_weight = {
                    ViolationSeverity.CRITICAL: 25,
                    ViolationSeverity.HIGH: 20,
                    ViolationSeverity.MEDIUM: 15,
                    ViolationSeverity.LOW: 10,
                    ViolationSeverity.INFORMATIONAL: 5
                }.get(violation.severity, 15)
                
                # Recent violations weighted more heavily
                days_ago = (datetime.now() - violation.detected_date).days
                recency_weight = max(0.5, 1 - (days_ago / 730))  # Decay over 2 years
                
                score += severity_weight * recency_weight
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error scoring historical violations: {e}")
            return 50.0
    
    def _score_property_age(self, property_data: Dict) -> float:
        """Score based on property age"""
        build_year = property_data.get('build_year', datetime.now().year)
        age = datetime.now().year - build_year
        
        if age < 10:
            return 15.0  # New properties - lower risk
        elif age < 25:
            return 30.0  # Moderate age - moderate risk
        elif age < 40:
            return 50.0  # Older properties - higher risk
        else:
            return 75.0  # Very old properties - high risk
    
    def _score_property_size(self, property_data: Dict) -> float:
        """Score based on property size (complexity)"""
        unit_count = property_data.get('unit_count', 1)
        
        if unit_count <= 4:
            return 20.0  # Small properties - lower complexity
        elif unit_count <= 20:
            return 40.0  # Medium properties
        elif unit_count <= 100:
            return 60.0  # Large properties
        else:
            return 80.0  # Very large properties - high complexity
    
    def _score_affordable_housing(self, property_data: Dict) -> float:
        """Score based on affordable housing program participation"""
        program = property_data.get('affordable_housing_program')
        
        if not program:
            return 30.0  # No program - moderate risk
        elif program in ['LIHTC', 'Section 8']:
            return 70.0  # High compliance requirements
        else:
            return 50.0  # Other programs - moderate risk
    
    def _score_recent_complaints(self, property_id: str) -> float:
        """Score based on recent tenant complaints"""
        # This would integrate with your complaint/communication system
        # Placeholder implementation
        return 40.0
    
    def _score_inspection_failures(self, property_id: str) -> float:
        """Score based on recent inspection failures"""
        # This would integrate with your inspection system
        # Placeholder implementation
        return 35.0
    
    def _score_maintenance_backlog(self, property_id: str) -> float:
        """Score based on maintenance request backlog"""
        # This would integrate with your maintenance system
        # Placeholder implementation
        return 45.0
    
    def _score_staff_training(self, property_data: Dict) -> float:
        """Score based on staff training compliance"""
        # This would check training records
        # Placeholder implementation
        return 25.0
    
    def _score_document_compliance(self, property_id: str) -> float:
        """Score based on document compliance status"""
        # This would check document expiration and completeness
        # Placeholder implementation
        return 30.0
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score"""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 65:
            return RiskLevel.HIGH
        elif score >= 45:
            return RiskLevel.MEDIUM
        elif score >= 25:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def _get_property_data(self, property_id: str) -> Dict:
        """Get property data for scoring"""
        # This would integrate with your property model
        # Placeholder implementation
        return {
            'property_id': property_id,
            'build_year': 1995,
            'unit_count': 24,
            'affordable_housing_program': 'Section 8'
        }


class ViolationDetectionService:
    """Main service for violation detection and prevention"""
    
    def __init__(self):
        self.session = db.session
        self.pattern_analyzer = ViolationPatternAnalyzer()
        self.risk_engine = RiskScoringEngine()
        self.ai_monitor = get_ai_compliance_monitor()
        self.regulatory_service = get_regulatory_knowledge_service()
    
    async def run_comprehensive_violation_detection(
        self, 
        property_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Run comprehensive violation detection across properties"""
        try:
            # Get properties to analyze
            if not property_ids:
                property_ids = self._get_all_property_ids()
            
            results = {
                'properties_analyzed': len(property_ids),
                'violations_detected': [],
                'high_risk_properties': [],
                'prevention_recommendations': [],
                'compliance_gaps': [],
                'patterns_identified': []
            }
            
            # Analyze violation patterns
            patterns = self.pattern_analyzer.analyze_violation_patterns()
            results['patterns_identified'] = [
                {
                    'pattern_id': p.pattern_id,
                    'type': p.pattern_type,
                    'description': p.description,
                    'frequency': p.frequency,
                    'risk_score': p.risk_score,
                    'prevention_strategies': p.prevention_strategies
                }
                for p in patterns
            ]
            
            # Analyze each property
            for property_id in property_ids:
                # Calculate risk score
                risk_assessment = self.risk_engine.calculate_comprehensive_risk_score(property_id)
                
                # Run AI analysis
                ai_assessment = self.ai_monitor.analyze_property_compliance(property_id)
                
                # Detect potential violations
                violation_predictions = await self._detect_potential_violations(property_id, risk_assessment, ai_assessment)
                results['violations_detected'].extend(violation_predictions)
                
                # Identify high-risk properties
                if risk_assessment['risk_level'] in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    results['high_risk_properties'].append({
                        'property_id': property_id,
                        'risk_level': risk_assessment['risk_level'].value,
                        'risk_score': risk_assessment['overall_score'],
                        'high_risk_factors': risk_assessment['high_risk_factors']
                    })
                
                # Generate prevention recommendations
                recommendations = await self._generate_prevention_recommendations(
                    property_id, risk_assessment, ai_assessment
                )
                results['prevention_recommendations'].extend(recommendations)
                
                # Identify compliance gaps
                gaps = await self._identify_compliance_gaps(property_id)
                results['compliance_gaps'].extend(gaps)
            
            # Update compliance metrics
            await self._update_compliance_metrics(results)
            
            logger.info(f"Completed violation detection for {len(property_ids)} properties")
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive violation detection: {e}")
            return {'error': str(e)}
    
    async def _detect_potential_violations(
        self, 
        property_id: str, 
        risk_assessment: Dict, 
        ai_assessment: ComplianceRisk
    ) -> List[Dict[str, Any]]:
        """Detect potential violations for a property"""
        violations = []
        
        try:
            # Check if risk score indicates potential violation
            if risk_assessment['overall_score'] > 70:
                # Use AI to predict specific violation types
                violation_predictions = self.ai_monitor.detect_potential_violations([property_id])
                
                for prediction in violation_predictions:
                    if prediction.probability > 0.6:  # High probability threshold
                        violation_data = {
                            'property_id': property_id,
                            'violation_type': prediction.violation_type,
                            'probability': prediction.probability,
                            'severity': prediction.severity.value,
                            'confidence': prediction.confidence,
                            'contributing_factors': prediction.contributing_factors,
                            'prevention_actions': prediction.prevention_actions,
                            'predicted_date': datetime.now() + timedelta(days=30),  # Default prediction
                            'risk_score': risk_assessment['overall_score']
                        }
                        violations.append(violation_data)
                        
                        # Create violation record in database
                        await self._create_predicted_violation(violation_data)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error detecting potential violations: {e}")
            return []
    
    async def _create_predicted_violation(self, violation_data: Dict):
        """Create a predicted violation record"""
        try:
            # Check if similar predicted violation already exists
            existing = self.session.query(ComplianceViolation).filter(
                and_(
                    ComplianceViolation.property_id == violation_data['property_id'],
                    ComplianceViolation.violation_type == violation_data['violation_type'],
                    ComplianceViolation.is_resolved == False,
                    ComplianceViolation.detection_method == 'AI_Prediction'
                )
            ).first()
            
            if existing:
                # Update existing prediction
                existing.detection_confidence = violation_data['confidence']
                existing.ai_recommendations = violation_data['prevention_actions']
            else:
                # Create new predicted violation
                violation = ComplianceViolation(
                    property_id=violation_data['property_id'],
                    violation_type=violation_data['violation_type'],
                    title=f"Predicted {violation_data['violation_type']}",
                    description=f"AI-predicted violation with {violation_data['probability']:.1%} probability",
                    severity=ViolationSeverity(violation_data['severity']),
                    detected_date=datetime.now(),
                    detection_method='AI_Prediction',
                    detection_confidence=violation_data['confidence'],
                    ai_recommendations=violation_data['prevention_actions'],
                    contributing_factors=violation_data['contributing_factors']
                )
                
                self.session.add(violation)
            
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating predicted violation: {e}")
            self.session.rollback()
    
    async def _generate_prevention_recommendations(
        self, 
        property_id: str, 
        risk_assessment: Dict, 
        ai_assessment: ComplianceRisk
    ) -> List[Dict[str, Any]]:
        """Generate prevention recommendations for a property"""
        recommendations = []
        
        try:
            # Base recommendations on risk factors
            for factor in risk_assessment['high_risk_factors']:
                rec = self._get_factor_recommendation(property_id, factor, risk_assessment['overall_score'])
                if rec:
                    recommendations.append(rec)
            
            # Add AI-generated recommendations
            for ai_rec in ai_assessment.recommendations:
                recommendation = {
                    'property_id': property_id,
                    'type': 'ai_generated',
                    'priority': ViolationSeverity.MEDIUM.value,
                    'description': ai_rec,
                    'estimated_cost': None,
                    'estimated_impact': 0.7,  # Default impact
                    'implementation_timeline': '30-60 days',
                    'success_probability': ai_assessment.confidence / 100
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating prevention recommendations: {e}")
            return []
    
    def _get_factor_recommendation(self, property_id: str, factor: str, risk_score: float) -> Optional[Dict[str, Any]]:
        """Get recommendation for specific risk factor"""
        recommendations_map = {
            'historical_violations': {
                'type': 'process_improvement',
                'description': 'Implement enhanced compliance monitoring to prevent recurring violations',
                'estimated_cost': 5000,
                'implementation_timeline': '60-90 days'
            },
            'property_age': {
                'type': 'infrastructure_upgrade',
                'description': 'Schedule comprehensive building systems assessment and upgrades',
                'estimated_cost': 15000,
                'implementation_timeline': '90-180 days'
            },
            'affordable_housing_program': {
                'type': 'training_compliance',
                'description': 'Enhance staff training on affordable housing program requirements',
                'estimated_cost': 2000,
                'implementation_timeline': '30-45 days'
            },
            'maintenance_backlog': {
                'type': 'operational',
                'description': 'Implement proactive maintenance program to reduce backlog',
                'estimated_cost': 8000,
                'implementation_timeline': '45-90 days'
            }
        }
        
        base_rec = recommendations_map.get(factor)
        if not base_rec:
            return None
        
        return {
            'property_id': property_id,
            'type': base_rec['type'],
            'priority': ViolationSeverity.HIGH.value if risk_score > 80 else ViolationSeverity.MEDIUM.value,
            'description': base_rec['description'],
            'estimated_cost': base_rec['estimated_cost'],
            'estimated_impact': 0.8 if risk_score > 80 else 0.6,
            'implementation_timeline': base_rec['implementation_timeline'],
            'success_probability': 0.85
        }
    
    async def _identify_compliance_gaps(self, property_id: str) -> List[Dict[str, Any]]:
        """Identify compliance gaps for a property"""
        gaps = []
        
        try:
            # Get compliance requirements for property
            requirements = self.session.query(ComplianceRequirement).filter_by(
                property_id=property_id
            ).all()
            
            for requirement in requirements:
                # Check if requirement is overdue or at risk
                if requirement.next_review_date < datetime.now():
                    gap = {
                        'property_id': property_id,
                        'regulation_type': requirement.regulation.regulation_type.value,
                        'gap_type': 'overdue_review',
                        'description': f'Compliance review overdue for {requirement.requirement_name}',
                        'severity': ViolationSeverity.MEDIUM.value,
                        'time_to_violation': 0,  # Already overdue
                        'remediation_actions': [
                            'Schedule immediate compliance review',
                            'Update compliance documentation',
                            'Verify current compliance status'
                        ]
                    }
                    gaps.append(gap)
                elif requirement.compliance_status != ComplianceStatus.COMPLIANT:
                    # Estimate time to violation based on status
                    time_to_violation = self._estimate_time_to_violation(requirement)
                    
                    gap = {
                        'property_id': property_id,
                        'regulation_type': requirement.regulation.regulation_type.value,
                        'gap_type': 'non_compliant',
                        'description': f'{requirement.requirement_name} is {requirement.compliance_status.value}',
                        'severity': ViolationSeverity.HIGH.value,
                        'time_to_violation': time_to_violation,
                        'remediation_actions': [
                            'Immediate compliance assessment required',
                            'Implement corrective measures',
                            'Document remediation actions'
                        ]
                    }
                    gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error identifying compliance gaps: {e}")
            return []
    
    def _estimate_time_to_violation(self, requirement: ComplianceRequirement) -> int:
        """Estimate days until violation occurs"""
        if requirement.compliance_status == ComplianceStatus.NON_COMPLIANT:
            return 0  # Already in violation
        elif requirement.compliance_status == ComplianceStatus.AT_RISK:
            return 30  # Likely violation within 30 days
        elif requirement.compliance_status == ComplianceStatus.UNDER_REVIEW:
            return 60  # Potential violation within 60 days
        else:
            return 90  # Default estimate
    
    async def _update_compliance_metrics(self, results: Dict[str, Any]):
        """Update compliance metrics based on detection results"""
        try:
            # Calculate overall metrics
            total_properties = results['properties_analyzed']
            high_risk_count = len(results['high_risk_properties'])
            violations_detected = len(results['violations_detected'])
            
            # Create or update metrics record
            metrics = ComplianceMetrics(
                metric_date=datetime.now(),
                total_violations=violations_detected,
                overall_compliance_score=max(0, 100 - (violations_detected / total_properties * 10)) if total_properties > 0 else 100,
                risk_score=sum(p['risk_score'] for p in results['high_risk_properties']) / max(high_risk_count, 1),
                ai_recommendations_count=len([r for r in results['prevention_recommendations'] if r.get('type') == 'ai_generated'])
            )
            
            self.session.add(metrics)
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating compliance metrics: {e}")
            self.session.rollback()
    
    def _get_all_property_ids(self) -> List[str]:
        """Get all property IDs for analysis"""
        # This would integrate with your property model
        # Placeholder implementation
        return ['prop_1', 'prop_2', 'prop_3', 'prop_4', 'prop_5']
    
    async def schedule_proactive_monitoring(self, property_id: str, monitoring_frequency: str = 'daily'):
        """Schedule proactive monitoring for a property"""
        try:
            # This would integrate with your task scheduler (Celery, etc.)
            logger.info(f"Scheduled {monitoring_frequency} proactive monitoring for property {property_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling proactive monitoring: {e}")


# Global service instance
_violation_detection_service = None


def get_violation_detection_service() -> ViolationDetectionService:
    """Get or create the violation detection service instance"""
    global _violation_detection_service
    if _violation_detection_service is None:
        _violation_detection_service = ViolationDetectionService()
    return _violation_detection_service