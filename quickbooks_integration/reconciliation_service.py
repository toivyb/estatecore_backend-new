"""
Reconciliation and Error Handling Service for QuickBooks Integration

Provides comprehensive reconciliation, error handling, audit trails,
and data integrity validation for QuickBooks synchronization.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
from decimal import Decimal, ROUND_HALF_UP

from .quickbooks_api_client import QuickBooksAPIClient
from .financial_sync_service import FinancialSyncService
from .quickbooks_oauth_service import QuickBooksOAuthService

logger = logging.getLogger(__name__)

class DiscrepancyType(Enum):
    """Types of data discrepancies"""
    AMOUNT_MISMATCH = "amount_mismatch"
    DATE_MISMATCH = "date_mismatch"
    MISSING_RECORD = "missing_record"
    DUPLICATE_RECORD = "duplicate_record"
    STATUS_MISMATCH = "status_mismatch"
    CUSTOMER_MISMATCH = "customer_mismatch"
    ACCOUNT_MISMATCH = "account_mismatch"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ReconciliationStatus(Enum):
    """Reconciliation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"

@dataclass
class Discrepancy:
    """Represents a data discrepancy between EstateCore and QuickBooks"""
    discrepancy_id: str
    organization_id: str
    discrepancy_type: DiscrepancyType
    severity: ErrorSeverity
    entity_type: str
    estatecore_record: Optional[Dict[str, Any]]
    quickbooks_record: Optional[Dict[str, Any]]
    field_name: Optional[str]
    estatecore_value: Optional[Any]
    quickbooks_value: Optional[Any]
    description: str
    discovered_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    auto_resolvable: bool = False

@dataclass
class AuditLogEntry:
    """Audit log entry for tracking all changes"""
    log_id: str
    organization_id: str
    connection_id: str
    operation_type: str  # create, update, delete, sync
    entity_type: str
    entity_id: str
    user_id: Optional[str]
    timestamp: datetime
    before_data: Optional[Dict[str, Any]] = None
    after_data: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None
    sync_direction: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class ReconciliationReport:
    """Reconciliation report"""
    report_id: str
    organization_id: str
    reconciliation_date: datetime
    period_start: datetime
    period_end: datetime
    status: ReconciliationStatus
    total_records_checked: int
    discrepancies_found: int
    discrepancies_resolved: int
    discrepancies_pending: int
    data_integrity_score: float  # 0-100%
    recommendations: List[str]
    summary: Dict[str, Any]

class ReconciliationService:
    """
    Service for reconciling data between EstateCore and QuickBooks
    """
    
    def __init__(self, api_client: Optional[QuickBooksAPIClient] = None,
                 oauth_service: Optional[QuickBooksOAuthService] = None):
        self.api_client = api_client or QuickBooksAPIClient()
        self.oauth_service = oauth_service or QuickBooksOAuthService()
        
        # Storage for reconciliation data
        self.discrepancies: Dict[str, Discrepancy] = {}
        self.audit_logs: List[AuditLogEntry] = []
        self.reconciliation_reports: Dict[str, ReconciliationReport] = {}
        
        # Tolerance settings for reconciliation
        self.amount_tolerance = Decimal('0.01')  # 1 cent tolerance
        self.date_tolerance_days = 0  # Exact date match required
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load existing reconciliation data"""
        try:
            # Load discrepancies
            with open('instance/discrepancies.json', 'r') as f:
                data = json.load(f)
                for disc_data in data.get('discrepancies', []):
                    disc_data['discrepancy_type'] = DiscrepancyType(disc_data['discrepancy_type'])
                    disc_data['severity'] = ErrorSeverity(disc_data['severity'])
                    disc_data['discovered_at'] = datetime.fromisoformat(disc_data['discovered_at'])
                    if disc_data.get('resolved_at'):
                        disc_data['resolved_at'] = datetime.fromisoformat(disc_data['resolved_at'])
                    
                    discrepancy = Discrepancy(**disc_data)
                    self.discrepancies[discrepancy.discrepancy_id] = discrepancy
        
        except FileNotFoundError:
            logger.info("No discrepancies file found")
        except Exception as e:
            logger.error(f"Error loading discrepancies: {e}")
        
        try:
            # Load audit logs (recent ones only for performance)
            with open('instance/audit_logs.json', 'r') as f:
                data = json.load(f)
                for log_data in data.get('recent_logs', []):
                    log_data['timestamp'] = datetime.fromisoformat(log_data['timestamp'])
                    audit_log = AuditLogEntry(**log_data)
                    self.audit_logs.append(audit_log)
        
        except FileNotFoundError:
            logger.info("No audit logs file found")
        except Exception as e:
            logger.error(f"Error loading audit logs: {e}")
    
    def _save_data(self):
        """Save reconciliation data"""
        try:
            import os
            os.makedirs('instance', exist_ok=True)
            
            # Save discrepancies
            discrepancies_data = {
                'discrepancies': [
                    {**asdict(disc), 
                     'discrepancy_type': disc.discrepancy_type.value,
                     'severity': disc.severity.value}
                    for disc in self.discrepancies.values()
                ]
            }
            with open('instance/discrepancies.json', 'w') as f:
                json.dump(discrepancies_data, f, indent=2, default=str)
            
            # Save recent audit logs (last 1000 entries)
            recent_logs = sorted(self.audit_logs, key=lambda x: x.timestamp, reverse=True)[:1000]
            audit_data = {
                'recent_logs': [asdict(log) for log in recent_logs]
            }
            with open('instance/audit_logs.json', 'w') as f:
                json.dump(audit_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving reconciliation data: {e}")
    
    def log_operation(self, organization_id: str, connection_id: str, operation_type: str,
                     entity_type: str, entity_id: str, user_id: Optional[str] = None,
                     before_data: Optional[Dict[str, Any]] = None,
                     after_data: Optional[Dict[str, Any]] = None,
                     sync_direction: Optional[str] = None,
                     success: bool = True, error_message: Optional[str] = None,
                     ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Log an operation for audit trail"""
        
        # Calculate changes if before/after data provided
        changes = None
        if before_data and after_data:
            changes = self._calculate_changes(before_data, after_data)
        
        audit_log = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            organization_id=organization_id,
            connection_id=connection_id,
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            timestamp=datetime.now(),
            before_data=before_data,
            after_data=after_data,
            changes=changes,
            sync_direction=sync_direction,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.audit_logs.append(audit_log)
        
        # Save to persistent storage periodically
        if len(self.audit_logs) % 10 == 0:
            self._save_data()
        
        logger.info(f"Logged operation: {operation_type} {entity_type} {entity_id}")
    
    def _calculate_changes(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes between before and after data"""
        changes = {}
        
        # Find modified fields
        all_keys = set(before.keys()) | set(after.keys())
        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)
            
            if before_val != after_val:
                changes[key] = {
                    'from': before_val,
                    'to': after_val
                }
        
        return changes
    
    def reconcile_data(self, organization_id: str, entity_types: List[str] = None,
                      period_start: Optional[datetime] = None,
                      period_end: Optional[datetime] = None) -> ReconciliationReport:
        """
        Perform comprehensive data reconciliation
        
        Args:
            organization_id: Organization to reconcile
            entity_types: List of entity types to reconcile (default: all)
            period_start: Start date for reconciliation period
            period_end: End date for reconciliation period
            
        Returns:
            ReconciliationReport with results
        """
        report_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        if entity_types is None:
            entity_types = ['customers', 'invoices', 'payments', 'expenses']
        
        if period_start is None:
            period_start = datetime.now() - timedelta(days=30)
        
        if period_end is None:
            period_end = datetime.now()
        
        logger.info(f"Starting reconciliation for organization {organization_id}")
        
        connection = self.oauth_service.get_organization_connection(organization_id)
        if not connection:
            return ReconciliationReport(
                report_id=report_id,
                organization_id=organization_id,
                reconciliation_date=start_time,
                period_start=period_start,
                period_end=period_end,
                status=ReconciliationStatus.FAILED,
                total_records_checked=0,
                discrepancies_found=0,
                discrepancies_resolved=0,
                discrepancies_pending=0,
                data_integrity_score=0.0,
                recommendations=["QuickBooks connection not found"],
                summary={}
            )
        
        total_records = 0
        new_discrepancies = []
        
        try:
            # Reconcile each entity type
            for entity_type in entity_types:
                entity_discrepancies = []
                
                if entity_type == 'customers':
                    entity_discrepancies = self._reconcile_customers(
                        organization_id, connection.connection_id, period_start, period_end
                    )
                elif entity_type == 'invoices':
                    entity_discrepancies = self._reconcile_invoices(
                        organization_id, connection.connection_id, period_start, period_end
                    )
                elif entity_type == 'payments':
                    entity_discrepancies = self._reconcile_payments(
                        organization_id, connection.connection_id, period_start, period_end
                    )
                elif entity_type == 'expenses':
                    entity_discrepancies = self._reconcile_expenses(
                        organization_id, connection.connection_id, period_start, period_end
                    )
                
                new_discrepancies.extend(entity_discrepancies)
                total_records += len(entity_discrepancies)
            
            # Store new discrepancies
            for discrepancy in new_discrepancies:
                self.discrepancies[discrepancy.discrepancy_id] = discrepancy
            
            # Calculate metrics
            discrepancies_found = len(new_discrepancies)
            discrepancies_resolved = self._attempt_auto_resolution(new_discrepancies)
            discrepancies_pending = discrepancies_found - discrepancies_resolved
            
            # Calculate data integrity score
            if total_records > 0:
                integrity_score = ((total_records - discrepancies_pending) / total_records) * 100
            else:
                integrity_score = 100.0
            
            # Generate recommendations
            recommendations = self._generate_recommendations(new_discrepancies)
            
            # Create summary
            summary = self._create_reconciliation_summary(new_discrepancies)
            
            report = ReconciliationReport(
                report_id=report_id,
                organization_id=organization_id,
                reconciliation_date=start_time,
                period_start=period_start,
                period_end=period_end,
                status=ReconciliationStatus.COMPLETED,
                total_records_checked=total_records,
                discrepancies_found=discrepancies_found,
                discrepancies_resolved=discrepancies_resolved,
                discrepancies_pending=discrepancies_pending,
                data_integrity_score=integrity_score,
                recommendations=recommendations,
                summary=summary
            )
            
            self.reconciliation_reports[report_id] = report
            self._save_data()
            
            logger.info(f"Reconciliation completed: {discrepancies_found} discrepancies found")
            return report
        
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return ReconciliationReport(
                report_id=report_id,
                organization_id=organization_id,
                reconciliation_date=start_time,
                period_start=period_start,
                period_end=period_end,
                status=ReconciliationStatus.FAILED,
                total_records_checked=total_records,
                discrepancies_found=0,
                discrepancies_resolved=0,
                discrepancies_pending=0,
                data_integrity_score=0.0,
                recommendations=[f"Reconciliation failed: {str(e)}"],
                summary={}
            )
    
    def _reconcile_customers(self, organization_id: str, connection_id: str,
                           period_start: datetime, period_end: datetime) -> List[Discrepancy]:
        """Reconcile customer data"""
        discrepancies = []
        
        try:
            # Get EstateCore tenants
            estatecore_tenants = self._get_estatecore_tenants(organization_id, period_start, period_end)
            
            # Get QuickBooks customers
            qb_customers = self.api_client.get_customers(connection_id)
            
            # Create lookup maps
            ec_by_id = {tenant['tenant_id']: tenant for tenant in estatecore_tenants}
            qb_by_acct = {customer.get('AcctNum', '').replace('EC-', ''): customer 
                         for customer in qb_customers if customer.get('AcctNum', '').startswith('EC-')}
            
            # Check for missing records in QuickBooks
            for tenant_id, tenant in ec_by_id.items():
                if tenant_id not in qb_by_acct:
                    discrepancy = Discrepancy(
                        discrepancy_id=str(uuid.uuid4()),
                        organization_id=organization_id,
                        discrepancy_type=DiscrepancyType.MISSING_RECORD,
                        severity=ErrorSeverity.MEDIUM,
                        entity_type='customer',
                        estatecore_record=tenant,
                        quickbooks_record=None,
                        field_name=None,
                        estatecore_value=tenant_id,
                        quickbooks_value=None,
                        description=f"Tenant {tenant_id} exists in EstateCore but not in QuickBooks",
                        discovered_at=datetime.now(),
                        auto_resolvable=True
                    )
                    discrepancies.append(discrepancy)
            
            # Check for data mismatches
            for tenant_id in set(ec_by_id.keys()) & set(qb_by_acct.keys()):
                tenant = ec_by_id[tenant_id]
                customer = qb_by_acct[tenant_id]
                
                # Check name mismatch
                ec_name = f"{tenant.get('first_name', '')} {tenant.get('last_name', '')}".strip()
                qb_name = customer.get('Name', '')
                
                if ec_name != qb_name:
                    discrepancy = Discrepancy(
                        discrepancy_id=str(uuid.uuid4()),
                        organization_id=organization_id,
                        discrepancy_type=DiscrepancyType.CUSTOMER_MISMATCH,
                        severity=ErrorSeverity.LOW,
                        entity_type='customer',
                        estatecore_record=tenant,
                        quickbooks_record=customer,
                        field_name='name',
                        estatecore_value=ec_name,
                        quickbooks_value=qb_name,
                        description=f"Name mismatch for tenant {tenant_id}",
                        discovered_at=datetime.now(),
                        auto_resolvable=True
                    )
                    discrepancies.append(discrepancy)
                
                # Check email mismatch
                ec_email = tenant.get('email', '')
                qb_email = customer.get('PrimaryEmailAddr', {}).get('Address', '')
                
                if ec_email != qb_email:
                    discrepancy = Discrepancy(
                        discrepancy_id=str(uuid.uuid4()),
                        organization_id=organization_id,
                        discrepancy_type=DiscrepancyType.CUSTOMER_MISMATCH,
                        severity=ErrorSeverity.LOW,
                        entity_type='customer',
                        estatecore_record=tenant,
                        quickbooks_record=customer,
                        field_name='email',
                        estatecore_value=ec_email,
                        quickbooks_value=qb_email,
                        description=f"Email mismatch for tenant {tenant_id}",
                        discovered_at=datetime.now(),
                        auto_resolvable=True
                    )
                    discrepancies.append(discrepancy)
        
        except Exception as e:
            logger.error(f"Error reconciling customers: {e}")
        
        return discrepancies
    
    def _reconcile_invoices(self, organization_id: str, connection_id: str,
                          period_start: datetime, period_end: datetime) -> List[Discrepancy]:
        """Reconcile invoice data"""
        discrepancies = []
        
        try:
            # Get EstateCore rent payments (which should have corresponding invoices)
            ec_payments = self._get_estatecore_rent_payments(organization_id, period_start, period_end)
            
            # Get QuickBooks invoices
            qb_invoices = self.api_client.get_invoices(connection_id, period_start, period_end)
            
            # Create lookup maps
            ec_by_ref = {payment.get('rent_payment_id'): payment for payment in ec_payments}
            qb_by_doc = {invoice.get('DocNumber', '').replace('EC-', ''): invoice 
                        for invoice in qb_invoices if invoice.get('DocNumber', '').startswith('EC-')}
            
            # Check for missing invoices
            for payment_id, payment in ec_by_ref.items():
                if payment_id not in qb_by_doc:
                    discrepancy = Discrepancy(
                        discrepancy_id=str(uuid.uuid4()),
                        organization_id=organization_id,
                        discrepancy_type=DiscrepancyType.MISSING_RECORD,
                        severity=ErrorSeverity.HIGH,
                        entity_type='invoice',
                        estatecore_record=payment,
                        quickbooks_record=None,
                        field_name=None,
                        estatecore_value=payment_id,
                        quickbooks_value=None,
                        description=f"Rent payment {payment_id} has no corresponding invoice in QuickBooks",
                        discovered_at=datetime.now(),
                        auto_resolvable=True
                    )
                    discrepancies.append(discrepancy)
            
            # Check for amount mismatches
            for payment_id in set(ec_by_ref.keys()) & set(qb_by_doc.keys()):
                payment = ec_by_ref[payment_id]
                invoice = qb_by_doc[payment_id]
                
                ec_amount = Decimal(str(payment.get('amount', 0)))
                qb_amount = Decimal(str(invoice.get('TotalAmt', 0)))
                
                if abs(ec_amount - qb_amount) > self.amount_tolerance:
                    discrepancy = Discrepancy(
                        discrepancy_id=str(uuid.uuid4()),
                        organization_id=organization_id,
                        discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                        severity=ErrorSeverity.HIGH,
                        entity_type='invoice',
                        estatecore_record=payment,
                        quickbooks_record=invoice,
                        field_name='amount',
                        estatecore_value=float(ec_amount),
                        quickbooks_value=float(qb_amount),
                        description=f"Amount mismatch for payment {payment_id}: EC={ec_amount}, QB={qb_amount}",
                        discovered_at=datetime.now(),
                        auto_resolvable=False
                    )
                    discrepancies.append(discrepancy)
        
        except Exception as e:
            logger.error(f"Error reconciling invoices: {e}")
        
        return discrepancies
    
    def _reconcile_payments(self, organization_id: str, connection_id: str,
                          period_start: datetime, period_end: datetime) -> List[Discrepancy]:
        """Reconcile payment data"""
        discrepancies = []
        
        try:
            # Get EstateCore payments
            ec_payments = self._get_estatecore_rent_payments(organization_id, period_start, period_end)
            
            # Get QuickBooks payments
            qb_payments = self.api_client.get_payments(connection_id, period_start, period_end)
            
            # Check for payment consistency
            for payment in ec_payments:
                if payment.get('status') == 'paid':
                    # Should have corresponding QB payment
                    payment_ref = f"RENT-{payment.get('rent_payment_id')}"
                    qb_payment = next((p for p in qb_payments 
                                     if p.get('PaymentRefNum') == payment_ref), None)
                    
                    if not qb_payment:
                        discrepancy = Discrepancy(
                            discrepancy_id=str(uuid.uuid4()),
                            organization_id=organization_id,
                            discrepancy_type=DiscrepancyType.MISSING_RECORD,
                            severity=ErrorSeverity.HIGH,
                            entity_type='payment',
                            estatecore_record=payment,
                            quickbooks_record=None,
                            field_name=None,
                            estatecore_value=payment.get('rent_payment_id'),
                            quickbooks_value=None,
                            description=f"Paid rent {payment.get('rent_payment_id')} has no corresponding payment in QuickBooks",
                            discovered_at=datetime.now(),
                            auto_resolvable=True
                        )
                        discrepancies.append(discrepancy)
        
        except Exception as e:
            logger.error(f"Error reconciling payments: {e}")
        
        return discrepancies
    
    def _reconcile_expenses(self, organization_id: str, connection_id: str,
                          period_start: datetime, period_end: datetime) -> List[Discrepancy]:
        """Reconcile expense data"""
        discrepancies = []
        
        try:
            # Get EstateCore expenses
            ec_expenses = self._get_estatecore_expenses(organization_id, period_start, period_end)
            
            # Get QuickBooks bills/expenses
            # This would need to be implemented in the API client
            # qb_bills = self.api_client.get_bills(connection_id, period_start, period_end)
            
            # For now, just check if expenses exist
            for expense in ec_expenses:
                # Placeholder for expense reconciliation logic
                pass
        
        except Exception as e:
            logger.error(f"Error reconciling expenses: {e}")
        
        return discrepancies
    
    def _attempt_auto_resolution(self, discrepancies: List[Discrepancy]) -> int:
        """Attempt to automatically resolve discrepancies"""
        resolved_count = 0
        
        for discrepancy in discrepancies:
            if discrepancy.auto_resolvable:
                try:
                    if self._auto_resolve_discrepancy(discrepancy):
                        discrepancy.resolved_at = datetime.now()
                        discrepancy.resolution_notes = "Auto-resolved"
                        resolved_count += 1
                except Exception as e:
                    logger.error(f"Failed to auto-resolve discrepancy {discrepancy.discrepancy_id}: {e}")
        
        return resolved_count
    
    def _auto_resolve_discrepancy(self, discrepancy: Discrepancy) -> bool:
        """Attempt to automatically resolve a discrepancy"""
        try:
            if discrepancy.discrepancy_type == DiscrepancyType.MISSING_RECORD:
                if discrepancy.entity_type == 'customer':
                    # Create missing customer in QuickBooks
                    return self._create_missing_customer(discrepancy)
                elif discrepancy.entity_type == 'invoice':
                    # Create missing invoice in QuickBooks
                    return self._create_missing_invoice(discrepancy)
                elif discrepancy.entity_type == 'payment':
                    # Create missing payment in QuickBooks
                    return self._create_missing_payment(discrepancy)
            
            elif discrepancy.discrepancy_type == DiscrepancyType.CUSTOMER_MISMATCH:
                # Update customer information in QuickBooks
                return self._update_customer_data(discrepancy)
            
            return False
        
        except Exception as e:
            logger.error(f"Auto-resolution failed: {e}")
            return False
    
    def _create_missing_customer(self, discrepancy: Discrepancy) -> bool:
        """Create missing customer in QuickBooks"""
        # This would use the mapping service to create the customer
        # For now, just log the action
        logger.info(f"Would create customer for tenant {discrepancy.estatecore_value}")
        return True
    
    def _create_missing_invoice(self, discrepancy: Discrepancy) -> bool:
        """Create missing invoice in QuickBooks"""
        logger.info(f"Would create invoice for payment {discrepancy.estatecore_value}")
        return True
    
    def _create_missing_payment(self, discrepancy: Discrepancy) -> bool:
        """Create missing payment in QuickBooks"""
        logger.info(f"Would create payment for rent {discrepancy.estatecore_value}")
        return True
    
    def _update_customer_data(self, discrepancy: Discrepancy) -> bool:
        """Update customer data in QuickBooks"""
        logger.info(f"Would update customer data for {discrepancy.field_name}")
        return True
    
    def _generate_recommendations(self, discrepancies: List[Discrepancy]) -> List[str]:
        """Generate recommendations based on discrepancies"""
        recommendations = []
        
        # Count discrepancy types
        missing_customers = len([d for d in discrepancies 
                               if d.discrepancy_type == DiscrepancyType.MISSING_RECORD 
                               and d.entity_type == 'customer'])
        
        missing_invoices = len([d for d in discrepancies 
                              if d.discrepancy_type == DiscrepancyType.MISSING_RECORD 
                              and d.entity_type == 'invoice'])
        
        amount_mismatches = len([d for d in discrepancies 
                               if d.discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH])
        
        if missing_customers > 5:
            recommendations.append("Consider enabling automatic customer creation during sync")
        
        if missing_invoices > 10:
            recommendations.append("Review rent invoice generation workflow")
        
        if amount_mismatches > 0:
            recommendations.append("Review amount calculation logic for discrepancies")
        
        high_severity = len([d for d in discrepancies if d.severity == ErrorSeverity.HIGH])
        if high_severity > 0:
            recommendations.append(f"Prioritize resolution of {high_severity} high-severity discrepancies")
        
        return recommendations
    
    def _create_reconciliation_summary(self, discrepancies: List[Discrepancy]) -> Dict[str, Any]:
        """Create reconciliation summary"""
        summary = {
            'by_type': {},
            'by_severity': {},
            'by_entity': {},
            'auto_resolvable': 0,
            'manual_review_required': 0
        }
        
        for discrepancy in discrepancies:
            # By type
            type_key = discrepancy.discrepancy_type.value
            summary['by_type'][type_key] = summary['by_type'].get(type_key, 0) + 1
            
            # By severity
            severity_key = discrepancy.severity.value
            summary['by_severity'][severity_key] = summary['by_severity'].get(severity_key, 0) + 1
            
            # By entity
            entity_key = discrepancy.entity_type
            summary['by_entity'][entity_key] = summary['by_entity'].get(entity_key, 0) + 1
            
            # Resolvability
            if discrepancy.auto_resolvable:
                summary['auto_resolvable'] += 1
            else:
                summary['manual_review_required'] += 1
        
        return summary
    
    # Mock data methods (would be replaced with actual database queries)
    
    def _get_estatecore_tenants(self, organization_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get EstateCore tenants for the period"""
        # This would query the EstateCore database
        return []
    
    def _get_estatecore_rent_payments(self, organization_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get EstateCore rent payments for the period"""
        # This would query the EstateCore database
        return []
    
    def _get_estatecore_expenses(self, organization_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get EstateCore expenses for the period"""
        # This would query the EstateCore database
        return []
    
    # Public API methods
    
    def get_discrepancies(self, organization_id: str, status: Optional[str] = None,
                         severity: Optional[ErrorSeverity] = None) -> List[Dict[str, Any]]:
        """Get discrepancies for an organization"""
        discrepancies = [
            d for d in self.discrepancies.values()
            if d.organization_id == organization_id
        ]
        
        if status == "unresolved":
            discrepancies = [d for d in discrepancies if d.resolved_at is None]
        elif status == "resolved":
            discrepancies = [d for d in discrepancies if d.resolved_at is not None]
        
        if severity:
            discrepancies = [d for d in discrepancies if d.severity == severity]
        
        return [
            {
                'discrepancy_id': d.discrepancy_id,
                'type': d.discrepancy_type.value,
                'severity': d.severity.value,
                'entity_type': d.entity_type,
                'description': d.description,
                'discovered_at': d.discovered_at.isoformat(),
                'resolved_at': d.resolved_at.isoformat() if d.resolved_at else None,
                'auto_resolvable': d.auto_resolvable
            }
            for d in discrepancies
        ]
    
    def resolve_discrepancy(self, discrepancy_id: str, resolution_notes: str) -> bool:
        """Manually resolve a discrepancy"""
        if discrepancy_id not in self.discrepancies:
            return False
        
        discrepancy = self.discrepancies[discrepancy_id]
        discrepancy.resolved_at = datetime.now()
        discrepancy.resolution_notes = resolution_notes
        
        self._save_data()
        return True
    
    def get_audit_trail(self, organization_id: str, entity_type: Optional[str] = None,
                       entity_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail for organization"""
        logs = [
            log for log in self.audit_logs
            if log.organization_id == organization_id
        ]
        
        if entity_type:
            logs = [log for log in logs if log.entity_type == entity_type]
        
        if entity_id:
            logs = [log for log in logs if log.entity_id == entity_id]
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                'log_id': log.log_id,
                'operation_type': log.operation_type,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'timestamp': log.timestamp.isoformat(),
                'success': log.success,
                'error_message': log.error_message,
                'user_id': log.user_id,
                'changes': log.changes
            }
            for log in logs[:limit]
        ]
    
    def get_data_integrity_score(self, organization_id: str) -> Dict[str, Any]:
        """Get data integrity score for organization"""
        # Get recent discrepancies
        recent_discrepancies = [
            d for d in self.discrepancies.values()
            if d.organization_id == organization_id
            and d.discovered_at > datetime.now() - timedelta(days=30)
        ]
        
        unresolved = [d for d in recent_discrepancies if d.resolved_at is None]
        critical = [d for d in unresolved if d.severity == ErrorSeverity.CRITICAL]
        high = [d for d in unresolved if d.severity == ErrorSeverity.HIGH]
        
        # Calculate score (0-100)
        score = 100
        score -= len(critical) * 20  # Critical issues heavily penalize
        score -= len(high) * 10      # High issues moderately penalize
        score -= len(unresolved) * 2 # All unresolved issues slightly penalize
        score = max(0, score)
        
        return {
            'integrity_score': score,
            'total_discrepancies': len(recent_discrepancies),
            'unresolved_discrepancies': len(unresolved),
            'critical_issues': len(critical),
            'high_priority_issues': len(high),
            'last_reconciliation': datetime.now().isoformat()  # Would be actual last reconciliation
        }

# Service instance
_reconciliation_service = None

def get_reconciliation_service() -> ReconciliationService:
    """Get singleton reconciliation service instance"""
    global _reconciliation_service
    if _reconciliation_service is None:
        _reconciliation_service = ReconciliationService()
    return _reconciliation_service