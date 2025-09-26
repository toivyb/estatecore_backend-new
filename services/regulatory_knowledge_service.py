"""
Regulatory Knowledge Base Service
Manages comprehensive database of housing regulations and compliance requirements
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import sessionmaker
import requests
import re
from dataclasses import dataclass

from models.base import db
from models.compliance import (
    RegulatoryKnowledgeBase, RegulationType, ComplianceRequirement, 
    ComplianceStatus, ViolationSeverity
)


logger = logging.getLogger(__name__)


@dataclass
class RegulationUpdate:
    """Data structure for regulation updates"""
    regulation_code: str
    title: str
    changes: List[str]
    effective_date: datetime
    impact_level: str


class RegulatoryKnowledgeService:
    """Service for managing regulatory knowledge base and compliance requirements"""
    
    def __init__(self):
        self.session = db.session
        
        # Federal regulation sources
        self.federal_sources = {
            'hud': 'https://www.hud.gov/program_offices/fair_housing_equal_opp',
            'cfr': 'https://www.ecfr.gov/current/title-24',
            'ada': 'https://www.ada.gov/reg3a.html',
            'epa': 'https://www.epa.gov/environmental-justice'
        }
        
        # State/local regulation tracking
        self.jurisdiction_sources = {}
        
    def initialize_knowledge_base(self) -> bool:
        """Initialize the regulatory knowledge base with core regulations"""
        try:
            logger.info("Initializing regulatory knowledge base...")
            
            # Core federal housing regulations
            core_regulations = self._get_core_regulations()
            
            for reg_data in core_regulations:
                existing = self.session.query(RegulatoryKnowledgeBase).filter_by(
                    regulation_code=reg_data['regulation_code']
                ).first()
                
                if not existing:
                    regulation = RegulatoryKnowledgeBase(**reg_data)
                    self.session.add(regulation)
                    logger.info(f"Added regulation: {reg_data['regulation_code']}")
            
            self.session.commit()
            logger.info("Regulatory knowledge base initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {str(e)}")
            self.session.rollback()
            return False
    
    def _get_core_regulations(self) -> List[Dict]:
        """Get core housing regulations to populate the knowledge base"""
        return [
            {
                'regulation_code': 'FHA-2023-001',
                'title': 'Fair Housing Act - Prohibited Discriminatory Practices',
                'description': 'Federal law prohibiting discrimination in housing transactions based on protected classes',
                'regulation_type': RegulationType.FAIR_HOUSING,
                'jurisdiction': 'Federal',
                'effective_date': datetime(1968, 4, 11),
                'last_updated': datetime.now(),
                'version': '2023.1',
                'full_text': 'The Fair Housing Act prohibits discrimination in housing transactions...',
                'summary': 'Prohibits housing discrimination based on race, color, religion, sex, national origin, familial status, or disability',
                'key_requirements': [
                    'No discrimination in rental, sale, or financing of housing',
                    'Reasonable accommodations for disabled tenants',
                    'Equal access to housing advertisements',
                    'No harassment or intimidation'
                ],
                'compliance_checklist': [
                    'Rental applications do not ask prohibited questions',
                    'Advertising does not indicate preferences or limitations',
                    'Reasonable accommodation policies in place',
                    'Staff trained on fair housing requirements'
                ],
                'penalties': [
                    'Civil penalties up to $100,000 for first violation',
                    'Criminal penalties for willful violations',
                    'Injunctive relief and monetary damages'
                ],
                'monitoring_keywords': [
                    'discrimination', 'protected class', 'reasonable accommodation',
                    'familial status', 'disability', 'harassment'
                ],
                'risk_factors': [
                    'Inconsistent tenant screening criteria',
                    'Failure to provide reasonable accommodations',
                    'Discriminatory advertising language',
                    'Staff lacking fair housing training'
                ]
            },
            {
                'regulation_code': 'ADA-2010-001',
                'title': 'Americans with Disabilities Act - Housing Accessibility',
                'description': 'Federal requirements for accessibility in housing accommodations',
                'regulation_type': RegulationType.ACCESSIBILITY_ADA,
                'jurisdiction': 'Federal',
                'effective_date': datetime(1990, 7, 26),
                'last_updated': datetime.now(),
                'version': '2010.1',
                'summary': 'Ensures equal access to housing for individuals with disabilities',
                'key_requirements': [
                    'Accessible common areas and amenities',
                    'Reasonable modifications to policies and procedures',
                    'Accessible parking spaces',
                    'Clear width requirements for doorways and hallways'
                ],
                'compliance_checklist': [
                    'Accessibility audit completed',
                    'Reasonable modification policy established',
                    'Accessible parking marked and available',
                    'Common areas meet accessibility standards'
                ],
                'monitoring_keywords': [
                    'accessibility', 'reasonable modification', 'disability accommodation',
                    'wheelchair accessible', 'service animal'
                ]
            },
            {
                'regulation_code': 'HUD-24CFR-982',
                'title': 'Housing Choice Voucher Program (Section 8) Requirements',
                'description': 'Requirements for properties participating in Section 8 housing assistance',
                'regulation_type': RegulationType.SECTION_8,
                'jurisdiction': 'Federal',
                'effective_date': datetime(1974, 8, 22),
                'last_updated': datetime.now(),
                'version': '2023.1',
                'summary': 'Standards and requirements for Section 8 housing assistance program',
                'key_requirements': [
                    'Housing Quality Standards (HQS) compliance',
                    'Rent reasonableness standards',
                    'Lease addendum requirements',
                    'Regular inspections and certifications'
                ],
                'compliance_checklist': [
                    'Current HQS inspection passed',
                    'Rent within reasonable range for area',
                    'Section 8 lease addendum executed',
                    'Tenant files properly maintained'
                ],
                'monitoring_keywords': [
                    'housing quality standards', 'hqs inspection', 'rent reasonableness',
                    'voucher', 'housing assistance payment'
                ]
            },
            {
                'regulation_code': 'LIHTC-IRC-42',
                'title': 'Low-Income Housing Tax Credit Program Requirements',
                'description': 'Compliance requirements for LIHTC properties',
                'regulation_type': RegulationType.LIHTC,
                'jurisdiction': 'Federal',
                'effective_date': datetime(1986, 10, 22),
                'last_updated': datetime.now(),
                'version': '2023.1',
                'summary': 'Income and rent restrictions for Low-Income Housing Tax Credit properties',
                'key_requirements': [
                    'Income certification for all tenants',
                    'Rent restrictions based on AMI',
                    'Minimum set-aside requirements',
                    'Annual compliance monitoring'
                ],
                'compliance_checklist': [
                    'Tenant income certifications current',
                    'Rents within LIHTC limits',
                    'Set-aside requirements met',
                    'Annual compliance report submitted'
                ],
                'monitoring_keywords': [
                    'income certification', 'area median income', 'ami',
                    'set-aside', 'tax credit compliance'
                ]
            },
            {
                'regulation_code': 'EPA-RRP-2010',
                'title': 'EPA Lead-Based Paint Renovation, Repair, and Painting Rule',
                'description': 'Requirements for lead-safe work practices in housing built before 1978',
                'regulation_type': RegulationType.ENVIRONMENTAL_EPA,
                'jurisdiction': 'Federal',
                'effective_date': datetime(2010, 4, 22),
                'last_updated': datetime.now(),
                'version': '2023.1',
                'summary': 'Lead-safe work practices for pre-1978 housing renovation and maintenance',
                'key_requirements': [
                    'EPA certified renovator for work in pre-1978 housing',
                    'Lead disclosure to tenants',
                    'Lead-safe work practices',
                    'Proper containment and cleanup procedures'
                ],
                'compliance_checklist': [
                    'Renovator EPA certification current',
                    'Lead disclosure provided to tenants',
                    'Lead-safe work practices documented',
                    'Proper disposal of lead debris'
                ],
                'monitoring_keywords': [
                    'lead paint', 'renovation', 'epa certified', 'lead disclosure',
                    'containment', 'rrp rule'
                ]
            }
        ]
    
    def add_regulation(self, regulation_data: Dict[str, Any]) -> Optional[str]:
        """Add a new regulation to the knowledge base"""
        try:
            # Validate required fields
            required_fields = ['regulation_code', 'title', 'regulation_type', 'jurisdiction']
            for field in required_fields:
                if field not in regulation_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check for duplicates
            existing = self.session.query(RegulatoryKnowledgeBase).filter_by(
                regulation_code=regulation_data['regulation_code']
            ).first()
            
            if existing:
                logger.warning(f"Regulation {regulation_data['regulation_code']} already exists")
                return None
            
            # Create new regulation
            regulation = RegulatoryKnowledgeBase(**regulation_data)
            self.session.add(regulation)
            self.session.commit()
            
            logger.info(f"Added new regulation: {regulation_data['regulation_code']}")
            return regulation.id
            
        except Exception as e:
            logger.error(f"Failed to add regulation: {str(e)}")
            self.session.rollback()
            return None
    
    def update_regulation(self, regulation_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing regulation with change tracking"""
        try:
            regulation = self.session.query(RegulatoryKnowledgeBase).get(regulation_id)
            if not regulation:
                logger.error(f"Regulation {regulation_id} not found")
                return False
            
            # Track changes
            changes = {}
            for key, new_value in updates.items():
                if hasattr(regulation, key):
                    old_value = getattr(regulation, key)
                    if old_value != new_value:
                        changes[key] = {'old': old_value, 'new': new_value}
                        setattr(regulation, key, new_value)
            
            # Update change log
            if changes:
                change_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'changes': changes,
                    'updated_by': 'system'  # In production, use actual user ID
                }
                
                change_log = regulation.change_log or []
                change_log.append(change_entry)
                regulation.change_log = change_log
                
                regulation.last_updated = datetime.now()
                regulation.notification_sent = False  # Mark for notification
                
                self.session.commit()
                logger.info(f"Updated regulation {regulation.regulation_code} with {len(changes)} changes")
                return True
            
            return True  # No changes needed
            
        except Exception as e:
            logger.error(f"Failed to update regulation: {str(e)}")
            self.session.rollback()
            return False
    
    def search_regulations(
        self, 
        query: str = None,
        regulation_types: List[RegulationType] = None,
        jurisdictions: List[str] = None,
        effective_after: datetime = None
    ) -> List[RegulatoryKnowledgeBase]:
        """Search regulations with various filters"""
        try:
            query_obj = self.session.query(RegulatoryKnowledgeBase)
            
            # Text search in title, description, and keywords
            if query:
                search_filter = or_(
                    RegulatoryKnowledgeBase.title.ilike(f'%{query}%'),
                    RegulatoryKnowledgeBase.description.ilike(f'%{query}%'),
                    RegulatoryKnowledgeBase.summary.ilike(f'%{query}%')
                )
                query_obj = query_obj.filter(search_filter)
            
            # Filter by regulation types
            if regulation_types:
                query_obj = query_obj.filter(
                    RegulatoryKnowledgeBase.regulation_type.in_(regulation_types)
                )
            
            # Filter by jurisdictions
            if jurisdictions:
                query_obj = query_obj.filter(
                    RegulatoryKnowledgeBase.jurisdiction.in_(jurisdictions)
                )
            
            # Filter by effective date
            if effective_after:
                query_obj = query_obj.filter(
                    RegulatoryKnowledgeBase.effective_date >= effective_after
                )
            
            results = query_obj.order_by(
                RegulatoryKnowledgeBase.regulation_type,
                RegulatoryKnowledgeBase.title
            ).all()
            
            logger.info(f"Found {len(results)} regulations matching search criteria")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search regulations: {str(e)}")
            return []
    
    def get_applicable_regulations(self, property_data: Dict) -> List[RegulatoryKnowledgeBase]:
        """Get regulations applicable to a specific property based on its characteristics"""
        try:
            # Extract property characteristics
            property_type = property_data.get('property_type', 'residential')
            location = property_data.get('location', {})
            state = location.get('state', '')
            city = location.get('city', '')
            build_year = property_data.get('build_year')
            unit_count = property_data.get('unit_count', 1)
            affordable_housing = property_data.get('affordable_housing_program')
            
            # Start with all regulations
            query = self.session.query(RegulatoryKnowledgeBase)
            
            # Federal regulations apply to all
            federal_regs = query.filter(
                RegulatoryKnowledgeBase.jurisdiction == 'Federal'
            ).all()
            
            # State-specific regulations
            state_regs = []
            if state:
                state_regs = query.filter(
                    RegulatoryKnowledgeBase.jurisdiction == state
                ).all()
            
            # City-specific regulations
            city_regs = []
            if city:
                city_regs = query.filter(
                    RegulatoryKnowledgeBase.jurisdiction == city
                ).all()
            
            # Combine all applicable regulations
            applicable_regs = federal_regs + state_regs + city_regs
            
            # Filter based on property characteristics
            filtered_regs = []
            for reg in applicable_regs:
                if self._is_regulation_applicable(reg, property_data):
                    filtered_regs.append(reg)
            
            logger.info(f"Found {len(filtered_regs)} regulations applicable to property")
            return filtered_regs
            
        except Exception as e:
            logger.error(f"Failed to get applicable regulations: {str(e)}")
            return []
    
    def _is_regulation_applicable(self, regulation: RegulatoryKnowledgeBase, property_data: Dict) -> bool:
        """Determine if a regulation applies to a specific property"""
        reg_type = regulation.regulation_type
        
        # Age-based applicability (e.g., lead paint rules for pre-1978 housing)
        build_year = property_data.get('build_year')
        if reg_type == RegulationType.ENVIRONMENTAL_EPA and regulation.regulation_code == 'EPA-RRP-2010':
            if build_year and build_year >= 1978:
                return False
        
        # Program-specific regulations
        affordable_program = property_data.get('affordable_housing_program')
        if reg_type == RegulationType.LIHTC and affordable_program != 'LIHTC':
            return False
        if reg_type == RegulationType.SECTION_8 and affordable_program != 'Section 8':
            return False
        
        # Property size considerations
        unit_count = property_data.get('unit_count', 1)
        if unit_count >= 20:  # Large properties may have additional requirements
            # Add logic for large property regulations
            pass
        
        return True
    
    def create_property_compliance_requirements(self, property_id: str, property_data: Dict) -> bool:
        """Create compliance requirements for a property based on applicable regulations"""
        try:
            # Get applicable regulations
            applicable_regs = self.get_applicable_regulations(property_data)
            
            # Create compliance requirements for each applicable regulation
            for regulation in applicable_regs:
                # Check if requirement already exists
                existing = self.session.query(ComplianceRequirement).filter_by(
                    property_id=property_id,
                    regulation_id=regulation.id
                ).first()
                
                if existing:
                    continue
                
                # Create new compliance requirement
                requirement = ComplianceRequirement(
                    property_id=property_id,
                    regulation_id=regulation.id,
                    requirement_name=f"{regulation.title} Compliance",
                    description=regulation.summary,
                    compliance_status=ComplianceStatus.UNDER_REVIEW,
                    due_date=self._calculate_due_date(regulation),
                    next_review_date=self._calculate_next_review_date(regulation),
                    compliance_period=self._get_compliance_period(regulation),
                    risk_score=self._calculate_initial_risk_score(regulation, property_data)
                )
                
                self.session.add(requirement)
            
            self.session.commit()
            logger.info(f"Created {len(applicable_regs)} compliance requirements for property {property_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create compliance requirements: {str(e)}")
            self.session.rollback()
            return False
    
    def _calculate_due_date(self, regulation: RegulatoryKnowledgeBase) -> datetime:
        """Calculate when compliance must be achieved"""
        # Default to 30 days for new requirements
        return datetime.now() + timedelta(days=30)
    
    def _calculate_next_review_date(self, regulation: RegulatoryKnowledgeBase) -> datetime:
        """Calculate when compliance should be reviewed next"""
        reg_type = regulation.regulation_type
        
        # Different review frequencies based on regulation type
        if reg_type in [RegulationType.FAIR_HOUSING, RegulationType.ACCESSIBILITY_ADA]:
            # Annual review for critical compliance areas
            return datetime.now() + timedelta(days=365)
        elif reg_type in [RegulationType.LIHTC, RegulationType.SECTION_8]:
            # Quarterly review for affordable housing programs
            return datetime.now() + timedelta(days=90)
        else:
            # Semi-annual review for other regulations
            return datetime.now() + timedelta(days=180)
    
    def _get_compliance_period(self, regulation: RegulatoryKnowledgeBase) -> int:
        """Get the compliance checking period in days"""
        reg_type = regulation.regulation_type
        
        if reg_type in [RegulationType.LIHTC, RegulationType.SECTION_8]:
            return 90  # Quarterly for affordable housing
        elif reg_type == RegulationType.FAIR_HOUSING:
            return 365  # Annual for fair housing
        else:
            return 180  # Semi-annual default
    
    def _calculate_initial_risk_score(self, regulation: RegulatoryKnowledgeBase, property_data: Dict) -> float:
        """Calculate initial risk score for compliance requirement"""
        base_score = 50.0  # Default medium risk
        
        # Adjust based on regulation type severity
        if regulation.regulation_type == RegulationType.FAIR_HOUSING:
            base_score += 20  # Higher risk for fair housing violations
        elif regulation.regulation_type in [RegulationType.LIHTC, RegulationType.SECTION_8]:
            base_score += 15  # Higher risk for affordable housing compliance
        
        # Adjust based on property characteristics
        unit_count = property_data.get('unit_count', 1)
        if unit_count > 50:
            base_score += 10  # Larger properties have higher complexity
        
        build_year = property_data.get('build_year')
        if build_year and build_year < 1990:
            base_score += 10  # Older properties may have more compliance challenges
        
        return min(base_score, 100.0)  # Cap at 100
    
    def check_regulation_updates(self) -> List[RegulationUpdate]:
        """Check for updates to regulations from external sources"""
        updates = []
        
        try:
            # This would integrate with various government APIs and websites
            # For now, return empty list as placeholder
            
            # TODO: Implement actual regulation monitoring
            # - HUD website scraping
            # - State housing authority APIs
            # - Federal Register API
            # - Legal database integrations
            
            logger.info("Checked for regulation updates")
            
        except Exception as e:
            logger.error(f"Failed to check regulation updates: {str(e)}")
        
        return updates
    
    def get_regulation_statistics(self) -> Dict[str, Any]:
        """Get statistics about the regulatory knowledge base"""
        try:
            stats = {}
            
            # Total regulations
            stats['total_regulations'] = self.session.query(RegulatoryKnowledgeBase).count()
            
            # By regulation type
            type_counts = self.session.query(
                RegulatoryKnowledgeBase.regulation_type,
                func.count(RegulatoryKnowledgeBase.id)
            ).group_by(RegulatoryKnowledgeBase.regulation_type).all()
            
            stats['by_type'] = {reg_type.value: count for reg_type, count in type_counts}
            
            # By jurisdiction
            jurisdiction_counts = self.session.query(
                RegulatoryKnowledgeBase.jurisdiction,
                func.count(RegulatoryKnowledgeBase.id)
            ).group_by(RegulatoryKnowledgeBase.jurisdiction).all()
            
            stats['by_jurisdiction'] = dict(jurisdiction_counts)
            
            # Recent updates
            recent_updates = self.session.query(RegulatoryKnowledgeBase).filter(
                RegulatoryKnowledgeBase.last_updated >= datetime.now() - timedelta(days=30)
            ).count()
            
            stats['recent_updates'] = recent_updates
            
            # Compliance requirements
            stats['total_requirements'] = self.session.query(ComplianceRequirement).count()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get regulation statistics: {str(e)}")
            return {}


# Global service instance
_regulatory_service = None


def get_regulatory_knowledge_service() -> RegulatoryKnowledgeService:
    """Get or create the regulatory knowledge service instance"""
    global _regulatory_service
    if _regulatory_service is None:
        _regulatory_service = RegulatoryKnowledgeService()
    return _regulatory_service