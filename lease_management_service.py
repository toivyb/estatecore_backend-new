"""
Lease Management Automation Service for EstateCore
Handles lease lifecycle automation, renewals, expirations, and compliance tracking
"""

import os
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import calendar
import json
from decimal import Decimal
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeaseStatus(Enum):
    """Lease status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    RENEWED = "renewed"
    TERMINATED = "terminated"
    CANCELLED = "cancelled"

class LeaseType(Enum):
    """Lease type enumeration"""
    FIXED_TERM = "fixed_term"
    MONTH_TO_MONTH = "month_to_month"
    WEEK_TO_WEEK = "week_to_week"
    CORPORATE = "corporate"
    SHORT_TERM = "short_term"

class RenewalStatus(Enum):
    """Renewal status enumeration"""
    NOT_STARTED = "not_started"
    NOTICE_SENT = "notice_sent"
    IN_NEGOTIATION = "in_negotiation"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"

@dataclass
class LeaseRenewalConfig:
    """Lease renewal configuration"""
    notice_period_days: int = 60  # Days before expiration to start renewal process
    reminder_intervals: List[int] = field(default_factory=lambda: [60, 45, 30, 14, 7])  # Days before expiration
    auto_renewal_enabled: bool = False
    auto_renewal_terms: Dict = field(default_factory=dict)
    renewal_incentives: List[Dict] = field(default_factory=list)
    market_rate_adjustment: bool = True

@dataclass
class ComplianceConfig:
    """Compliance and legal configuration"""
    required_documents: List[str] = field(default_factory=lambda: [
        'lease_agreement', 'tenant_application', 'background_check', 'credit_report'
    ])
    inspection_required: bool = True
    insurance_required: bool = True
    security_deposit_rules: Dict = field(default_factory=lambda: {
        'max_months': 2,
        'interest_required': False,
        'separate_account': True
    })
    termination_notice_days: int = 30

@dataclass
class LeaseAutomationConfig:
    """Main lease automation configuration"""
    renewal_config: LeaseRenewalConfig = field(default_factory=LeaseRenewalConfig)
    compliance_config: ComplianceConfig = field(default_factory=ComplianceConfig)
    auto_generate_documents: bool = True
    enable_digital_signatures: bool = True
    track_lease_violations: bool = True
    automated_rent_increases: bool = True

@dataclass
class LeaseDocument:
    """Lease document data structure"""
    id: str
    lease_id: str
    document_type: str
    file_path: str
    version: int = 1
    signed: bool = False
    signed_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)

@dataclass
class LeaseViolation:
    """Lease violation tracking"""
    id: str
    lease_id: str
    violation_type: str
    description: str
    severity: str  # low, medium, high, critical
    reported_date: datetime
    resolved_date: Optional[datetime] = None
    resolution_notes: str = ""
    status: str = "open"  # open, resolved, disputed

@dataclass
class Lease:
    """Complete lease data structure"""
    id: str
    tenant_id: int
    property_id: int
    unit_number: str
    lease_type: LeaseType
    status: LeaseStatus
    start_date: date
    end_date: date
    rent_amount: Decimal
    security_deposit: Decimal
    lease_terms: Dict = field(default_factory=dict)
    renewal_status: RenewalStatus = RenewalStatus.NOT_STARTED
    auto_renewal: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    signed_date: Optional[datetime] = None
    documents: List[LeaseDocument] = field(default_factory=list)
    violations: List[LeaseViolation] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class LeaseManagementService:
    def __init__(self, config: LeaseAutomationConfig = None):
        """Initialize lease management service"""
        self.config = config or self._get_default_config()
        self._email_service = None
        self._sms_service = None
        self._database_service = None
        self._document_service = None
        
    def _get_default_config(self) -> LeaseAutomationConfig:
        """Get default configuration from environment"""
        return LeaseAutomationConfig(
            renewal_config=LeaseRenewalConfig(
                notice_period_days=int(os.getenv('LEASE_RENEWAL_NOTICE_DAYS', '60')),
                auto_renewal_enabled=os.getenv('AUTO_RENEWAL_ENABLED', 'false').lower() == 'true'
            ),
            compliance_config=ComplianceConfig(
                termination_notice_days=int(os.getenv('TERMINATION_NOTICE_DAYS', '30'))
            )
        )
    
    def _initialize_services(self):
        """Initialize dependent services"""
        try:
            from email_service import create_email_service
            from sms_service import create_sms_service
            from database_service import get_database_service
            from file_storage_service import create_file_storage_service
            
            self._email_service = create_email_service()
            self._sms_service = create_sms_service()
            self._database_service = get_database_service()
            self._document_service = create_file_storage_service()
            
        except ImportError as e:
            logger.warning(f"Could not import service: {e}")
    
    def process_lease_renewals(self) -> Dict:
        """Process lease renewals for expiring leases"""
        logger.info("Processing lease renewals...")
        
        try:
            self._initialize_services()
            
            # Get leases expiring within notice period
            expiring_leases = self._get_expiring_leases()
            
            processed_renewals = []
            renewal_notifications_sent = 0
            
            for lease in expiring_leases:
                try:
                    renewal_result = self._process_individual_lease_renewal(lease)
                    processed_renewals.append(renewal_result)
                    
                    if renewal_result.get('notification_sent'):
                        renewal_notifications_sent += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process renewal for lease {lease['id']}: {e}")
                    processed_renewals.append({
                        'lease_id': lease['id'],
                        'success': False,
                        'error': str(e)
                    })
            
            result = {
                'success': True,
                'expiring_leases_count': len(expiring_leases),
                'processed_renewals': len(processed_renewals),
                'notifications_sent': renewal_notifications_sent,
                'renewals': processed_renewals
            }
            
            logger.info(f"Lease renewal processing complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Lease renewal processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_expiring_leases(self) -> List[Dict]:
        """Get leases expiring within notice period"""
        if not self._database_service:
            # Mock data for development
            today = date.today()
            return [
                {
                    'id': 'LEASE-2024-001',
                    'tenant_id': 1,
                    'property_id': 1,
                    'unit_number': '101',
                    'start_date': today - timedelta(days=300),
                    'end_date': today + timedelta(days=45),
                    'rent_amount': 1500.00,
                    'status': 'active',
                    'renewal_status': 'not_started',
                    'tenant_email': 'tenant1@example.com',
                    'tenant_name': 'John Doe',
                    'property_name': 'Sunset Apartments'
                },
                {
                    'id': 'LEASE-2024-002',
                    'tenant_id': 2,
                    'property_id': 1,
                    'unit_number': '102',
                    'start_date': today - timedelta(days=350),
                    'end_date': today + timedelta(days=30),
                    'rent_amount': 1600.00,
                    'status': 'active',
                    'renewal_status': 'notice_sent',
                    'tenant_email': 'tenant2@example.com',
                    'tenant_name': 'Jane Smith',
                    'property_name': 'Sunset Apartments'
                }
            ]
        
        try:
            notice_cutoff = date.today() + timedelta(days=self.config.renewal_config.notice_period_days)
            
            query = """
                SELECT l.*, t.unit_number, prop.name as property_name,
                       u.first_name, u.last_name, u.email as tenant_email
                FROM leases l
                LEFT JOIN tenants t ON l.tenant_id = t.id
                LEFT JOIN properties prop ON l.property_id = prop.id
                LEFT JOIN users u ON t.user_id = u.id
                WHERE l.end_date <= ? AND l.status = 'active'
                ORDER BY l.end_date ASC
            """
            
            result = self._database_service.execute_query(query, (notice_cutoff,), fetch='all')
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            logger.error(f"Failed to get expiring leases: {e}")
            return []
    
    def _process_individual_lease_renewal(self, lease: Dict) -> Dict:
        """Process renewal for individual lease"""
        try:
            lease_id = lease['id']
            end_date = lease['end_date']
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            days_until_expiry = (end_date - date.today()).days
            renewal_status = lease.get('renewal_status', 'not_started')
            
            # Determine action based on days until expiry and current status
            action_taken = None
            notification_sent = False
            
            if renewal_status == 'not_started' and days_until_expiry <= self.config.renewal_config.notice_period_days:
                # Send initial renewal notice
                action_taken = self._send_renewal_notice(lease, 'initial')
                if action_taken['success']:
                    self._update_lease_renewal_status(lease_id, RenewalStatus.NOTICE_SENT)
                    notification_sent = True
                    
            elif renewal_status == 'notice_sent' and days_until_expiry in self.config.renewal_config.reminder_intervals:
                # Send reminder
                action_taken = self._send_renewal_notice(lease, 'reminder')
                notification_sent = action_taken.get('success', False)
                
            elif days_until_expiry <= 0:
                # Lease has expired
                action_taken = self._handle_lease_expiration(lease)
            
            # Calculate market rate adjustment if enabled
            market_adjustment = None
            if self.config.renewal_config.market_rate_adjustment:
                market_adjustment = self._calculate_market_rate_adjustment(lease)
            
            return {
                'lease_id': lease_id,
                'success': True,
                'days_until_expiry': days_until_expiry,
                'current_status': renewal_status,
                'action_taken': action_taken,
                'notification_sent': notification_sent,
                'market_adjustment': market_adjustment
            }
            
        except Exception as e:
            logger.error(f"Failed to process lease renewal {lease['id']}: {e}")
            return {
                'lease_id': lease['id'],
                'success': False,
                'error': str(e)
            }
    
    def _send_renewal_notice(self, lease: Dict, notice_type: str) -> Dict:
        """Send lease renewal notice to tenant"""
        try:
            tenant_email = lease.get('tenant_email')
            tenant_name = lease.get('tenant_name', '')
            
            if notice_type == 'initial':
                subject = "Lease Renewal Notice"
                message_type = "lease_renewal_notice"
            else:
                subject = "Lease Renewal Reminder"
                message_type = "lease_renewal_reminder"
            
            # Send email notification
            email_sent = False
            if self._email_service and tenant_email:
                email_result = self._email_service.send_lease_renewal_notice(
                    email=tenant_email,
                    tenant_name=tenant_name,
                    property_name=lease.get('property_name', ''),
                    unit_number=lease.get('unit_number', ''),
                    current_rent=lease.get('rent_amount', 0),
                    lease_end_date=lease.get('end_date'),
                    notice_type=notice_type
                )
                email_sent = email_result.get('success', False)
            
            # Send SMS notification if configured
            sms_sent = False
            if self._sms_service and lease.get('tenant_phone'):
                sms_result = self._sms_service.send_lease_renewal_reminder(
                    phone_number=lease.get('tenant_phone'),
                    tenant_name=tenant_name,
                    property_name=lease.get('property_name', ''),
                    unit_number=lease.get('unit_number', ''),
                    lease_end_date=lease.get('end_date')
                )
                sms_sent = sms_result.get('success', False)
            
            return {
                'success': email_sent or sms_sent,
                'email_sent': email_sent,
                'sms_sent': sms_sent,
                'notice_type': notice_type
            }
            
        except Exception as e:
            logger.error(f"Failed to send renewal notice for lease {lease['id']}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_lease_renewal_status(self, lease_id: str, status: RenewalStatus):
        """Update lease renewal status in database"""
        try:
            if not self._database_service:
                logger.info(f"Mock: Updated lease {lease_id} renewal status to {status.value}")
                return
            
            query = """
                UPDATE leases 
                SET renewal_status = ?, updated_at = ?
                WHERE id = ?
            """
            
            self._database_service.execute_query(
                query, 
                (status.value, datetime.utcnow(), lease_id)
            )
            
        except Exception as e:
            logger.error(f"Failed to update lease renewal status: {e}")
    
    def _handle_lease_expiration(self, lease: Dict) -> Dict:
        """Handle expired lease"""
        try:
            lease_id = lease['id']
            renewal_status = lease.get('renewal_status', 'not_started')
            
            if renewal_status == 'accepted':
                # Process lease renewal
                return self._process_lease_renewal(lease)
            elif renewal_status == 'declined':
                # Process lease termination
                return self._process_lease_termination(lease)
            else:
                # Mark lease as expired
                self._update_lease_status(lease_id, LeaseStatus.EXPIRED)
                
                # Send expiration notice
                self._send_lease_expiration_notice(lease)
                
                return {
                    'action': 'marked_expired',
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"Failed to handle lease expiration for {lease['id']}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_market_rate_adjustment(self, lease: Dict) -> Dict:
        """Calculate market rate adjustment for renewal"""
        try:
            current_rent = Decimal(str(lease.get('rent_amount', 0)))
            property_id = lease.get('property_id')
            
            # Mock market rate calculation
            # In production, this would use market data APIs
            market_rate_increase = Decimal('0.03')  # 3% increase
            new_rent = current_rent * (1 + market_rate_increase)
            
            return {
                'current_rent': float(current_rent),
                'suggested_rent': float(new_rent),
                'increase_amount': float(new_rent - current_rent),
                'increase_percentage': float(market_rate_increase * 100),
                'market_factors': [
                    'Local rental market trends',
                    'Property improvements',
                    'Inflation adjustment'
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate market rate adjustment: {e}")
            return {}
    
    def _update_lease_status(self, lease_id: str, status: LeaseStatus):
        """Update lease status in database"""
        try:
            if not self._database_service:
                logger.info(f"Mock: Updated lease {lease_id} status to {status.value}")
                return
            
            query = """
                UPDATE leases 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """
            
            self._database_service.execute_query(
                query, 
                (status.value, datetime.utcnow(), lease_id)
            )
            
        except Exception as e:
            logger.error(f"Failed to update lease status: {e}")
    
    def create_lease_renewal(self, lease_id: str, renewal_terms: Dict) -> Dict:
        """Create a lease renewal"""
        try:
            # Get original lease
            original_lease = self._get_lease_by_id(lease_id)
            if not original_lease:
                return {'success': False, 'error': 'Original lease not found'}
            
            # Create new lease with renewal terms
            new_lease_id = f"LEASE-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
            
            new_lease = Lease(
                id=new_lease_id,
                tenant_id=original_lease['tenant_id'],
                property_id=original_lease['property_id'],
                unit_number=original_lease['unit_number'],
                lease_type=LeaseType(renewal_terms.get('lease_type', 'fixed_term')),
                status=LeaseStatus.DRAFT,
                start_date=datetime.strptime(renewal_terms['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(renewal_terms['end_date'], '%Y-%m-%d').date(),
                rent_amount=Decimal(str(renewal_terms.get('rent_amount', original_lease['rent_amount']))),
                security_deposit=Decimal(str(renewal_terms.get('security_deposit', original_lease.get('security_deposit', 0)))),
                lease_terms=renewal_terms.get('terms', {}),
                auto_renewal=renewal_terms.get('auto_renewal', False),
                metadata={
                    'previous_lease_id': lease_id,
                    'renewal_date': datetime.utcnow().isoformat(),
                    'created_by': renewal_terms.get('created_by')
                }
            )
            
            # Save new lease
            saved = self._save_lease(new_lease)
            
            if saved:
                # Update original lease status
                self._update_lease_status(lease_id, LeaseStatus.RENEWED)
                self._update_lease_renewal_status(lease_id, RenewalStatus.ACCEPTED)
                
                # Generate lease documents if configured
                if self.config.auto_generate_documents:
                    self._generate_lease_documents(new_lease_id)
                
                return {
                    'success': True,
                    'new_lease_id': new_lease_id,
                    'message': 'Lease renewal created successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to save new lease'}
                
        except Exception as e:
            logger.error(f"Failed to create lease renewal: {e}")
            return {'success': False, 'error': str(e)}
    
    def track_lease_violation(self, lease_id: str, violation_data: Dict) -> Dict:
        """Track a lease violation"""
        try:
            violation = LeaseViolation(
                id=f"VIOL-{uuid.uuid4().hex[:8].upper()}",
                lease_id=lease_id,
                violation_type=violation_data['type'],
                description=violation_data['description'],
                severity=violation_data.get('severity', 'medium'),
                reported_date=datetime.utcnow(),
                status='open'
            )
            
            # Save violation
            saved = self._save_lease_violation(violation)
            
            if saved:
                # Send notification if severe
                if violation.severity in ['high', 'critical']:
                    self._send_violation_notification(lease_id, violation)
                
                return {
                    'success': True,
                    'violation_id': violation.id,
                    'message': 'Lease violation recorded'
                }
            else:
                return {'success': False, 'error': 'Failed to save violation'}
                
        except Exception as e:
            logger.error(f"Failed to track lease violation: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_lease_dashboard_data(self) -> Dict:
        """Get lease management dashboard data"""
        try:
            today = date.today()
            
            dashboard_data = {
                'total_active_leases': self._count_active_leases(),
                'expiring_soon': self._count_expiring_leases(30),  # 30 days
                'expired_leases': self._count_expired_leases(),
                'renewal_pipeline': self._get_renewal_pipeline(),
                'lease_violations': self._get_violation_summary(),
                'occupancy_rate': self._calculate_occupancy_rate(),
                'average_lease_term': self._calculate_average_lease_term(),
                'renewal_rate': self._calculate_renewal_rate(),
                'upcoming_expirations': self._get_upcoming_expirations(60),  # 60 days
                'recent_renewals': self._get_recent_renewals(30),  # 30 days
                'lease_status_breakdown': self._get_lease_status_breakdown()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get lease dashboard data: {e}")
            return {}
    
    def _get_lease_by_id(self, lease_id: str) -> Optional[Dict]:
        """Get lease by ID"""
        # Mock implementation
        return {
            'id': lease_id,
            'tenant_id': 1,
            'property_id': 1,
            'unit_number': '101',
            'rent_amount': 1500.00,
            'security_deposit': 1500.00,
            'status': 'active'
        }
    
    def _save_lease(self, lease: Lease) -> bool:
        """Save lease to database"""
        try:
            if not self._database_service:
                logger.info(f"Mock: Saved lease {lease.id}")
                return True
            
            # Implementation would save to database
            return True
            
        except Exception as e:
            logger.error(f"Failed to save lease: {e}")
            return False
    
    def _save_lease_violation(self, violation: LeaseViolation) -> bool:
        """Save lease violation to database"""
        try:
            if not self._database_service:
                logger.info(f"Mock: Saved violation {violation.id}")
                return True
            
            # Implementation would save to database
            return True
            
        except Exception as e:
            logger.error(f"Failed to save lease violation: {e}")
            return False
    
    def _generate_lease_documents(self, lease_id: str):
        """Generate lease documents"""
        logger.info(f"Mock: Generated documents for lease {lease_id}")
    
    def _send_violation_notification(self, lease_id: str, violation: LeaseViolation):
        """Send violation notification"""
        logger.info(f"Mock: Sent violation notification for lease {lease_id}")
    
    def _send_lease_expiration_notice(self, lease: Dict):
        """Send lease expiration notice"""
        logger.info(f"Mock: Sent expiration notice for lease {lease['id']}")
    
    def _process_lease_renewal(self, lease: Dict) -> Dict:
        """Process accepted lease renewal"""
        return {'action': 'renewal_processed', 'success': True}
    
    def _process_lease_termination(self, lease: Dict) -> Dict:
        """Process lease termination"""
        return {'action': 'termination_processed', 'success': True}
    
    # Dashboard data methods (mock implementations)
    def _count_active_leases(self) -> int:
        return 25
    
    def _count_expiring_leases(self, days: int) -> int:
        return 5
    
    def _count_expired_leases(self) -> int:
        return 2
    
    def _get_renewal_pipeline(self) -> Dict:
        return {
            'not_started': 3,
            'notice_sent': 2,
            'in_negotiation': 1,
            'accepted': 0,
            'declined': 1
        }
    
    def _get_violation_summary(self) -> Dict:
        return {
            'open': 3,
            'resolved': 12,
            'by_severity': {
                'low': 8,
                'medium': 5,
                'high': 2,
                'critical': 0
            }
        }
    
    def _calculate_occupancy_rate(self) -> float:
        return 95.5
    
    def _calculate_average_lease_term(self) -> float:
        return 12.5  # months
    
    def _calculate_renewal_rate(self) -> float:
        return 85.0  # percentage
    
    def _get_upcoming_expirations(self, days: int) -> List[Dict]:
        today = date.today()
        return [
            {
                'lease_id': 'LEASE-2024-001',
                'tenant_name': 'John Doe',
                'unit_number': '101',
                'end_date': (today + timedelta(days=30)).isoformat(),
                'rent_amount': 1500.00,
                'renewal_status': 'not_started'
            }
        ]
    
    def _get_recent_renewals(self, days: int) -> List[Dict]:
        return [
            {
                'lease_id': 'LEASE-2024-003',
                'tenant_name': 'Bob Johnson',
                'unit_number': '201',
                'renewal_date': datetime.utcnow().isoformat(),
                'new_rent': 1650.00,
                'old_rent': 1600.00
            }
        ]
    
    def _get_lease_status_breakdown(self) -> Dict:
        return {
            'active': 25,
            'expiring': 5,
            'expired': 2,
            'renewed': 8,
            'terminated': 3
        }

# Singleton instance
_lease_management_service = None

def get_lease_management_service() -> LeaseManagementService:
    """Get singleton lease management service instance"""
    global _lease_management_service
    if _lease_management_service is None:
        _lease_management_service = LeaseManagementService()
    return _lease_management_service

def create_lease_management_service(config: LeaseAutomationConfig = None) -> LeaseManagementService:
    """Create lease management service with custom configuration"""
    return LeaseManagementService(config)

if __name__ == "__main__":
    # Test the lease management service
    service = get_lease_management_service()
    
    print("🏠 Lease Management Service Test")
    
    # Test lease renewal processing
    result = service.process_lease_renewals()
    print(f"Lease Renewals: {result}")
    
    # Test dashboard data
    dashboard = service.get_lease_dashboard_data()
    print(f"Dashboard Data: {dashboard.get('total_active_leases', 0)} active leases")
    
    print("✅ Lease management service is ready!")