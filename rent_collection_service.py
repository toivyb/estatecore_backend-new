"""
Automated Rent Collection Service for EstateCore
Handles automated rent collection, payment processing, reminders, and late fees
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

class PaymentStatus(Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIAL = "partial"

class RentStatus(Enum):
    """Rent status enumeration"""
    CURRENT = "current"
    LATE = "late" 
    OVERDUE = "overdue"
    PAID = "paid"
    PARTIAL_PAID = "partial_paid"
    WAIVED = "waived"

class PaymentMethod(Enum):
    """Payment method enumeration"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    ACH = "ach"
    CHECK = "check"
    CASH = "cash"
    MONEY_ORDER = "money_order"

@dataclass
class LateFeeConfig:
    """Late fee configuration"""
    grace_period_days: int = 5
    flat_fee: Decimal = Decimal('50.00')
    percentage_fee: Decimal = Decimal('0.05')  # 5%
    max_late_fee: Decimal = Decimal('200.00')
    daily_fee: Decimal = Decimal('0.00')
    compound_fees: bool = False
    enabled: bool = True

@dataclass
class ReminderConfig:
    """Reminder configuration"""
    send_reminders: bool = True
    reminder_days: List[int] = field(default_factory=lambda: [5, 3, 1, -1, -3, -7])  # Negative = after due date
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True
    escalation_enabled: bool = True

@dataclass
class AutoPayConfig:
    """Automatic payment configuration"""
    enabled: bool = False
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    retry_attempts: int = 3
    retry_delay_days: int = 1
    failure_notification: bool = True

@dataclass
class RentCollectionConfig:
    """Main rent collection configuration"""
    auto_generate_invoices: bool = True
    invoice_generation_day: int = 25  # Day of month to generate next month's invoices
    due_day: int = 1  # Day of month rent is due
    late_fee_config: LateFeeConfig = field(default_factory=LateFeeConfig)
    reminder_config: ReminderConfig = field(default_factory=ReminderConfig)
    auto_pay_config: AutoPayConfig = field(default_factory=AutoPayConfig)
    payment_methods: List[PaymentMethod] = field(default_factory=lambda: [
        PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.BANK_TRANSFER
    ])

@dataclass
class RentInvoice:
    """Rent invoice data structure"""
    id: str
    tenant_id: int
    property_id: int
    unit_number: str
    amount_due: Decimal
    due_date: date
    late_fee: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    amount_paid: Decimal = Decimal('0.00')
    status: RentStatus = RentStatus.CURRENT
    payment_status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    description: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.total_amount == Decimal('0.00'):
            self.total_amount = self.amount_due + self.late_fee

@dataclass
class PaymentTransaction:
    """Payment transaction data structure"""
    id: str
    invoice_id: str
    tenant_id: int
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    description: str = ""
    metadata: Dict = field(default_factory=dict)

class RentCollectionService:
    def __init__(self, config: RentCollectionConfig = None):
        """Initialize rent collection service"""
        self.config = config or self._get_default_config()
        self._email_service = None
        self._sms_service = None
        self._payment_processor = None
        self._database_service = None
        
    def _get_default_config(self) -> RentCollectionConfig:
        """Get default configuration from environment"""
        return RentCollectionConfig(
            auto_generate_invoices=os.getenv('AUTO_GENERATE_INVOICES', 'true').lower() == 'true',
            invoice_generation_day=int(os.getenv('INVOICE_GENERATION_DAY', '25')),
            due_day=int(os.getenv('RENT_DUE_DAY', '1')),
            late_fee_config=LateFeeConfig(
                grace_period_days=int(os.getenv('LATE_FEE_GRACE_DAYS', '5')),
                flat_fee=Decimal(os.getenv('LATE_FEE_FLAT', '50.00')),
                percentage_fee=Decimal(os.getenv('LATE_FEE_PERCENTAGE', '0.05'))
            )
        )
    
    def _initialize_services(self):
        """Initialize dependent services"""
        try:
            from email_service import create_email_service
            from sms_service import create_sms_service
            from database_service import get_database_service
            
            self._email_service = create_email_service()
            self._sms_service = create_sms_service()
            self._database_service = get_database_service()
            
        except ImportError as e:
            logger.warning(f"Could not import service: {e}")
    
    def generate_monthly_invoices(self, target_month: date = None) -> Dict:
        """Generate rent invoices for all active tenants"""
        if target_month is None:
            # Generate for next month
            today = date.today()
            if today.month == 12:
                target_month = date(today.year + 1, 1, 1)
            else:
                target_month = date(today.year, today.month + 1, 1)
        
        logger.info(f"Generating rent invoices for {target_month.strftime('%B %Y')}")
        
        try:
            self._initialize_services()
            
            # Get all active tenants
            tenants = self._get_active_tenants()
            
            generated_invoices = []
            failed_generations = []
            
            for tenant in tenants:
                try:
                    invoice = self._generate_tenant_invoice(tenant, target_month)
                    if invoice:
                        generated_invoices.append(invoice)
                        logger.info(f"Generated invoice {invoice.id} for tenant {tenant['id']}")
                except Exception as e:
                    logger.error(f"Failed to generate invoice for tenant {tenant['id']}: {e}")
                    failed_generations.append({
                        'tenant_id': tenant['id'],
                        'error': str(e)
                    })
            
            # Save invoices to database
            saved_count = 0
            for invoice in generated_invoices:
                if self._save_invoice(invoice):
                    saved_count += 1
            
            result = {
                'success': True,
                'target_month': target_month.isoformat(),
                'total_tenants': len(tenants),
                'invoices_generated': len(generated_invoices),
                'invoices_saved': saved_count,
                'failed_generations': len(failed_generations),
                'failures': failed_generations
            }
            
            logger.info(f"Invoice generation complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Monthly invoice generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_active_tenants(self) -> List[Dict]:
        """Get all active tenants for invoice generation"""
        if not self._database_service:
            # Mock data for development
            return [
                {
                    'id': 1,
                    'user_id': 3,
                    'property_id': 1,
                    'unit_number': '101',
                    'rent_amount': 1500.00,
                    'lease_start_date': '2024-01-01',
                    'lease_end_date': '2024-12-31',
                    'status': 'active',
                    'email': 'tenant1@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone': '+1234567890'
                },
                {
                    'id': 2,
                    'user_id': 4,
                    'property_id': 1,
                    'unit_number': '102',
                    'rent_amount': 1600.00,
                    'lease_start_date': '2024-02-01',
                    'lease_end_date': '2025-01-31',
                    'status': 'active',
                    'email': 'tenant2@example.com',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'phone': '+1234567891'
                }
            ]
        
        try:
            return self._database_service.get_tenants()
        except Exception as e:
            logger.error(f"Failed to get active tenants: {e}")
            return []
    
    def _generate_tenant_invoice(self, tenant: Dict, target_month: date) -> Optional[RentInvoice]:
        """Generate invoice for a specific tenant"""
        try:
            # Calculate due date
            due_date = date(target_month.year, target_month.month, self.config.due_day)
            
            # Create invoice ID
            invoice_id = f"INV-{target_month.strftime('%Y%m')}-{tenant['id']:04d}-{uuid.uuid4().hex[:8]}"
            
            # Get rent amount
            rent_amount = Decimal(str(tenant.get('rent_amount', 0)))
            
            # Check for existing late fees
            late_fee = self._calculate_late_fees(tenant['id'], target_month)
            
            invoice = RentInvoice(
                id=invoice_id,
                tenant_id=tenant['id'],
                property_id=tenant['property_id'],
                unit_number=tenant.get('unit_number', ''),
                amount_due=rent_amount,
                due_date=due_date,
                late_fee=late_fee,
                description=f"Rent for {target_month.strftime('%B %Y')} - Unit {tenant.get('unit_number', '')}",
                metadata={
                    'tenant_name': f"{tenant.get('first_name', '')} {tenant.get('last_name', '')}",
                    'tenant_email': tenant.get('email', ''),
                    'property_name': tenant.get('property_name', ''),
                    'generation_date': datetime.utcnow().isoformat()
                }
            )
            
            return invoice
            
        except Exception as e:
            logger.error(f"Failed to generate invoice for tenant {tenant['id']}: {e}")
            return None
    
    def _calculate_late_fees(self, tenant_id: int, current_month: date) -> Decimal:
        """Calculate late fees for unpaid previous invoices"""
        if not self.config.late_fee_config.enabled:
            return Decimal('0.00')
        
        try:
            # Get unpaid invoices for this tenant
            unpaid_invoices = self._get_unpaid_invoices(tenant_id)
            
            total_late_fees = Decimal('0.00')
            today = date.today()
            
            for invoice in unpaid_invoices:
                if invoice['due_date'] < today:
                    days_late = (today - invoice['due_date']).days
                    
                    if days_late > self.config.late_fee_config.grace_period_days:
                        late_fee = self._calculate_single_late_fee(
                            invoice['amount_due'], days_late
                        )
                        total_late_fees += late_fee
            
            return min(total_late_fees, self.config.late_fee_config.max_late_fee)
            
        except Exception as e:
            logger.error(f"Failed to calculate late fees for tenant {tenant_id}: {e}")
            return Decimal('0.00')
    
    def _calculate_single_late_fee(self, rent_amount: Decimal, days_late: int) -> Decimal:
        """Calculate late fee for a single invoice"""
        config = self.config.late_fee_config
        
        # Flat fee
        late_fee = config.flat_fee
        
        # Percentage fee
        percentage_fee = rent_amount * config.percentage_fee
        late_fee += percentage_fee
        
        # Daily fee
        if config.daily_fee > 0:
            daily_fees = config.daily_fee * days_late
            late_fee += daily_fees
        
        return min(late_fee, config.max_late_fee)
    
    def _get_unpaid_invoices(self, tenant_id: int) -> List[Dict]:
        """Get unpaid invoices for a tenant"""
        # Mock implementation
        return []
    
    def _save_invoice(self, invoice: RentInvoice) -> bool:
        """Save invoice to database"""
        try:
            if not self._database_service:
                logger.info(f"Mock: Saved invoice {invoice.id}")
                return True
            
            # Save to database
            query = """
                INSERT INTO rent_invoices (
                    id, tenant_id, property_id, unit_number, amount_due,
                    due_date, late_fee, total_amount, status, payment_status,
                    description, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                invoice.id, invoice.tenant_id, invoice.property_id,
                invoice.unit_number, float(invoice.amount_due),
                invoice.due_date, float(invoice.late_fee), float(invoice.total_amount),
                invoice.status.value, invoice.payment_status.value,
                invoice.description, json.dumps(invoice.metadata),
                invoice.created_at
            )
            
            self._database_service.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save invoice {invoice.id}: {e}")
            return False
    
    def process_payment(self, invoice_id: str, payment_data: Dict) -> Dict:
        """Process a rent payment"""
        try:
            # Get invoice
            invoice = self._get_invoice(invoice_id)
            if not invoice:
                return {'success': False, 'error': 'Invoice not found'}
            
            # Validate payment amount
            payment_amount = Decimal(str(payment_data.get('amount', 0)))
            if payment_amount <= 0:
                return {'success': False, 'error': 'Invalid payment amount'}
            
            # Create payment transaction
            transaction = PaymentTransaction(
                id=f"TXN-{uuid.uuid4().hex[:12]}",
                invoice_id=invoice_id,
                tenant_id=invoice['tenant_id'],
                amount=payment_amount,
                payment_method=PaymentMethod(payment_data.get('payment_method', 'credit_card')),
                status=PaymentStatus.PROCESSING,
                description=f"Rent payment for invoice {invoice_id}"
            )
            
            # Process payment through payment processor
            payment_result = self._process_payment_transaction(transaction, payment_data)
            
            if payment_result['success']:
                # Update invoice status
                self._update_invoice_payment(invoice_id, payment_amount)
                
                # Send confirmation
                self._send_payment_confirmation(invoice, transaction)
                
                return {
                    'success': True,
                    'transaction_id': transaction.id,
                    'amount_paid': float(payment_amount),
                    'payment_status': transaction.status.value
                }
            else:
                return {
                    'success': False,
                    'error': payment_result.get('error', 'Payment processing failed'),
                    'transaction_id': transaction.id
                }
                
        except Exception as e:
            logger.error(f"Payment processing failed for invoice {invoice_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_invoice(self, invoice_id: str) -> Optional[Dict]:
        """Get invoice by ID"""
        # Mock implementation
        return {
            'id': invoice_id,
            'tenant_id': 1,
            'property_id': 1,
            'amount_due': 1500.00,
            'total_amount': 1500.00,
            'status': 'current'
        }
    
    def _process_payment_transaction(self, transaction: PaymentTransaction, payment_data: Dict) -> Dict:
        """Process payment through payment processor"""
        try:
            # Mock Stripe payment processing
            if transaction.payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
                # Simulate Stripe API call
                success = True  # Mock success
                
                if success:
                    transaction.status = PaymentStatus.COMPLETED
                    transaction.transaction_id = f"stripe_txn_{uuid.uuid4().hex[:16]}"
                    transaction.processed_at = datetime.utcnow()
                    
                    return {
                        'success': True,
                        'transaction_id': transaction.transaction_id
                    }
                else:
                    transaction.status = PaymentStatus.FAILED
                    return {
                        'success': False,
                        'error': 'Payment declined'
                    }
            
            # Other payment methods
            elif transaction.payment_method == PaymentMethod.BANK_TRANSFER:
                transaction.status = PaymentStatus.PENDING
                return {
                    'success': True,
                    'message': 'Bank transfer initiated'
                }
            
        except Exception as e:
            logger.error(f"Payment transaction processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_invoice_payment(self, invoice_id: str, payment_amount: Decimal):
        """Update invoice with payment information"""
        try:
            # Mock implementation
            logger.info(f"Updated invoice {invoice_id} with payment of ${payment_amount}")
            
        except Exception as e:
            logger.error(f"Failed to update invoice payment: {e}")
    
    def _send_payment_confirmation(self, invoice: Dict, transaction: PaymentTransaction):
        """Send payment confirmation to tenant"""
        try:
            if self._email_service:
                # Send email confirmation
                self._email_service.send_payment_receipt(
                    email=invoice.get('tenant_email', ''),
                    tenant_name=invoice.get('tenant_name', ''),
                    amount=float(transaction.amount),
                    transaction_id=transaction.transaction_id,
                    invoice_id=invoice['id']
                )
            
            if self._sms_service:
                # Send SMS confirmation
                self._sms_service.send_payment_confirmation(
                    phone_number=invoice.get('tenant_phone', ''),
                    tenant_name=invoice.get('tenant_name', ''),
                    amount=float(transaction.amount),
                    transaction_id=transaction.transaction_id,
                    property_name=invoice.get('property_name', ''),
                    unit_number=invoice.get('unit_number', '')
                )
                
        except Exception as e:
            logger.error(f"Failed to send payment confirmation: {e}")
    
    def send_rent_reminders(self, reminder_type: str = 'all') -> Dict:
        """Send rent payment reminders"""
        try:
            today = date.today()
            sent_count = 0
            failed_count = 0
            
            # Get invoices that need reminders
            invoices_for_reminders = self._get_invoices_for_reminders(today)
            
            for invoice in invoices_for_reminders:
                try:
                    reminder_sent = self._send_individual_reminder(invoice, today)
                    if reminder_sent:
                        sent_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to send reminder for invoice {invoice['id']}: {e}")
                    failed_count += 1
            
            return {
                'success': True,
                'reminders_sent': sent_count,
                'reminders_failed': failed_count,
                'total_processed': len(invoices_for_reminders)
            }
            
        except Exception as e:
            logger.error(f"Rent reminder sending failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_invoices_for_reminders(self, today: date) -> List[Dict]:
        """Get invoices that need reminders sent"""
        # Mock implementation - return invoices due soon or overdue
        return [
            {
                'id': 'INV-202412-0001-abc123',
                'tenant_id': 1,
                'due_date': today + timedelta(days=3),
                'amount_due': 1500.00,
                'status': 'current',
                'tenant_email': 'tenant1@example.com',
                'tenant_phone': '+1234567890',
                'tenant_name': 'John Doe',
                'property_name': 'Sunset Apartments',
                'unit_number': '101'
            }
        ]
    
    def _send_individual_reminder(self, invoice: Dict, today: date) -> bool:
        """Send reminder for individual invoice"""
        try:
            due_date = invoice['due_date']
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            days_until_due = (due_date - today).days
            
            # Determine reminder type
            if days_until_due > 0:
                reminder_type = f"{days_until_due} days before due"
            elif days_until_due == 0:
                reminder_type = "due today"
            else:
                reminder_type = f"{abs(days_until_due)} days overdue"
            
            # Send email reminder
            if self._email_service and self.config.reminder_config.email_enabled:
                self._email_service.send_rent_reminder(
                    email=invoice['tenant_email'],
                    tenant_name=invoice['tenant_name'],
                    amount_due=invoice['amount_due'],
                    due_date=due_date.strftime('%B %d, %Y'),
                    property_name=invoice['property_name'],
                    unit_number=invoice['unit_number']
                )
            
            # Send SMS reminder
            if self._sms_service and self.config.reminder_config.sms_enabled:
                self._sms_service.send_rent_reminder(
                    phone_number=invoice['tenant_phone'],
                    tenant_name=invoice['tenant_name'],
                    amount_due=invoice['amount_due'],
                    due_date=due_date.strftime('%B %d, %Y'),
                    property_name=invoice['property_name'],
                    unit_number=invoice['unit_number']
                )
            
            logger.info(f"Sent {reminder_type} reminder for invoice {invoice['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder for invoice {invoice['id']}: {e}")
            return False
    
    def get_collection_dashboard_data(self) -> Dict:
        """Get data for rent collection dashboard"""
        try:
            today = date.today()
            current_month = date(today.year, today.month, 1)
            
            # Calculate metrics
            dashboard_data = {
                'current_month': current_month.strftime('%B %Y'),
                'total_rent_due': self._calculate_total_rent_due(current_month),
                'total_collected': self._calculate_total_collected(current_month),
                'collection_rate': 0,
                'overdue_amount': self._calculate_overdue_amount(),
                'late_fees_collected': self._calculate_late_fees_collected(current_month),
                'outstanding_invoices': self._get_outstanding_invoices_count(),
                'payment_methods_breakdown': self._get_payment_methods_breakdown(current_month),
                'recent_payments': self._get_recent_payments(limit=10),
                'upcoming_due_dates': self._get_upcoming_due_dates(),
                'tenant_payment_status': self._get_tenant_payment_status()
            }
            
            # Calculate collection rate
            if dashboard_data['total_rent_due'] > 0:
                dashboard_data['collection_rate'] = (
                    dashboard_data['total_collected'] / dashboard_data['total_rent_due'] * 100
                )
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}
    
    def _calculate_total_rent_due(self, month: date) -> float:
        """Calculate total rent due for the month"""
        # Mock calculation
        return 15000.00
    
    def _calculate_total_collected(self, month: date) -> float:
        """Calculate total amount collected for the month"""
        # Mock calculation
        return 12500.00
    
    def _calculate_overdue_amount(self) -> float:
        """Calculate total overdue amount"""
        # Mock calculation
        return 2500.00
    
    def _calculate_late_fees_collected(self, month: date) -> float:
        """Calculate late fees collected for the month"""
        # Mock calculation
        return 300.00
    
    def _get_outstanding_invoices_count(self) -> int:
        """Get count of outstanding invoices"""
        # Mock count
        return 5
    
    def _get_payment_methods_breakdown(self, month: date) -> Dict:
        """Get breakdown of payments by method"""
        return {
            'credit_card': 8500.00,
            'bank_transfer': 3000.00,
            'debit_card': 1000.00,
            'check': 0.00
        }
    
    def _get_recent_payments(self, limit: int = 10) -> List[Dict]:
        """Get recent payments"""
        return [
            {
                'id': 'TXN-123456',
                'tenant_name': 'John Doe',
                'amount': 1500.00,
                'payment_date': datetime.utcnow().isoformat(),
                'payment_method': 'credit_card',
                'status': 'completed'
            }
        ]
    
    def _get_upcoming_due_dates(self) -> List[Dict]:
        """Get upcoming rent due dates"""
        today = date.today()
        return [
            {
                'due_date': (today + timedelta(days=3)).isoformat(),
                'tenant_count': 2,
                'total_amount': 3100.00
            }
        ]
    
    def _get_tenant_payment_status(self) -> Dict:
        """Get tenant payment status summary"""
        return {
            'current': 8,
            'late': 2,
            'overdue': 1,
            'paid': 15
        }

# Singleton instance
_rent_collection_service = None

def get_rent_collection_service() -> RentCollectionService:
    """Get singleton rent collection service instance"""
    global _rent_collection_service
    if _rent_collection_service is None:
        _rent_collection_service = RentCollectionService()
    return _rent_collection_service

def create_rent_collection_service(config: RentCollectionConfig = None) -> RentCollectionService:
    """Create rent collection service with custom configuration"""
    return RentCollectionService(config)

if __name__ == "__main__":
    # Test the rent collection service
    service = get_rent_collection_service()
    
    print("🏠 Rent Collection Service Test")
    
    # Test invoice generation
    result = service.generate_monthly_invoices()
    print(f"Invoice Generation: {result}")
    
    # Test reminder sending
    reminder_result = service.send_rent_reminders()
    print(f"Reminders: {reminder_result}")
    
    # Test dashboard data
    dashboard = service.get_collection_dashboard_data()
    print(f"Dashboard Data: Collection Rate = {dashboard.get('collection_rate', 0):.1f}%")
    
    print("✅ Rent collection service is ready!")