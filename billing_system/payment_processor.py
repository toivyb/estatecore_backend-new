import json
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import requests

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    ACH = "ach"
    WIRE = "wire"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    CRYPTO = "crypto"

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"

class PaymentProvider(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    SQUARE = "square"
    BRAINTREE = "braintree"
    AUTHORIZE_NET = "authorize_net"
    INTERNAL = "internal"

@dataclass
class PaymentMethodInfo:
    method_id: str
    customer_id: str
    provider: PaymentProvider
    payment_type: PaymentMethod
    
    # Card info (if applicable)
    card_last_four: Optional[str]
    card_brand: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    
    # Bank info (if applicable)
    bank_name: Optional[str]
    account_last_four: Optional[str]
    routing_number_last_four: Optional[str]
    
    # Metadata
    is_default: bool
    is_verified: bool
    provider_method_id: str
    created_at: datetime
    updated_at: datetime

@dataclass
class PaymentTransaction:
    transaction_id: str
    customer_id: str
    subscription_id: str
    invoice_id: str
    
    # Payment details
    amount: float
    currency: str
    payment_method: PaymentMethodInfo
    provider: PaymentProvider
    provider_transaction_id: str
    
    # Status
    status: PaymentStatus
    failure_reason: Optional[str]
    
    # Dates
    attempted_at: datetime
    completed_at: Optional[datetime]
    
    # Metadata
    metadata: Dict[str, Any]
    webhook_received: bool

@dataclass
class RefundTransaction:
    refund_id: str
    original_transaction_id: str
    customer_id: str
    
    # Refund details
    amount: float
    currency: str
    reason: str
    
    # Status
    status: PaymentStatus
    provider_refund_id: str
    
    # Dates
    requested_at: datetime
    processed_at: Optional[datetime]
    
    # Metadata
    metadata: Dict[str, Any]

@dataclass
class PaymentSchedule:
    schedule_id: str
    customer_id: str
    subscription_id: str
    payment_method_id: str
    
    # Schedule details
    amount: float
    currency: str
    frequency: str  # monthly, quarterly, annual
    next_payment_date: datetime
    
    # Status
    is_active: bool
    failed_attempts: int
    max_retry_attempts: int
    
    # Dates
    created_at: datetime
    updated_at: datetime

class PaymentProcessor:
    """
    Comprehensive payment processing system with multiple provider support
    """
    
    def __init__(self):
        self.providers = {}
        self.payment_methods = {}
        self.transactions = {}
        self.refunds = {}
        self.schedules = {}
        self.webhooks = {}
        self.retry_config = {
            'max_attempts': 3,
            'retry_delays': [1, 24, 72],  # Hours between retries
            'exponential_backoff': True
        }
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize payment provider configurations"""
        
        # Stripe configuration
        self.providers[PaymentProvider.STRIPE] = {
            'name': 'Stripe',
            'api_key': 'sk_test_...',  # Would be loaded from environment
            'webhook_secret': 'whsec_...',
            'supported_methods': [PaymentMethod.CREDIT_CARD, PaymentMethod.ACH, PaymentMethod.BANK_TRANSFER],
            'fees': {
                'credit_card': 0.029,  # 2.9% + $0.30
                'fixed_fee': 0.30,
                'ach': 0.008,  # 0.8% capped at $5
                'ach_cap': 5.00
            },
            'enabled': True
        }
        
        # PayPal configuration
        self.providers[PaymentProvider.PAYPAL] = {
            'name': 'PayPal',
            'client_id': 'paypal_client_id',
            'client_secret': 'paypal_client_secret',
            'supported_methods': [PaymentMethod.PAYPAL, PaymentMethod.CREDIT_CARD],
            'fees': {
                'paypal': 0.034,  # 3.4% + $0.30
                'fixed_fee': 0.30
            },
            'enabled': True
        }
        
        # Square configuration
        self.providers[PaymentProvider.SQUARE] = {
            'name': 'Square',
            'access_token': 'square_access_token',
            'supported_methods': [PaymentMethod.CREDIT_CARD],
            'fees': {
                'credit_card': 0.029,  # 2.9% + $0.30
                'fixed_fee': 0.30
            },
            'enabled': False
        }
    
    def add_payment_method(self, customer_id: str, payment_type: PaymentMethod,
                          provider: PaymentProvider, provider_data: Dict[str, Any]) -> PaymentMethodInfo:
        """Add a new payment method for a customer"""
        
        method_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Process provider-specific data
        if provider == PaymentProvider.STRIPE:
            payment_method = self._process_stripe_payment_method(provider_data)
        elif provider == PaymentProvider.PAYPAL:
            payment_method = self._process_paypal_payment_method(provider_data)
        else:
            payment_method = provider_data
        
        method_info = PaymentMethodInfo(
            method_id=method_id,
            customer_id=customer_id,
            provider=provider,
            payment_type=payment_type,
            card_last_four=payment_method.get('card_last_four'),
            card_brand=payment_method.get('card_brand'),
            card_exp_month=payment_method.get('card_exp_month'),
            card_exp_year=payment_method.get('card_exp_year'),
            bank_name=payment_method.get('bank_name'),
            account_last_four=payment_method.get('account_last_four'),
            routing_number_last_four=payment_method.get('routing_number_last_four'),
            is_default=payment_method.get('is_default', False),
            is_verified=payment_method.get('is_verified', False),
            provider_method_id=payment_method.get('provider_method_id', ''),
            created_at=now,
            updated_at=now
        )
        
        # Store payment method
        if customer_id not in self.payment_methods:
            self.payment_methods[customer_id] = []
        self.payment_methods[customer_id].append(method_info)
        
        return method_info
    
    def _process_stripe_payment_method(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe payment method data"""
        
        # In a real implementation, this would call Stripe API
        return {
            'provider_method_id': provider_data.get('id', ''),
            'card_last_four': provider_data.get('card', {}).get('last4'),
            'card_brand': provider_data.get('card', {}).get('brand'),
            'card_exp_month': provider_data.get('card', {}).get('exp_month'),
            'card_exp_year': provider_data.get('card', {}).get('exp_year'),
            'is_verified': True
        }
    
    def _process_paypal_payment_method(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process PayPal payment method data"""
        
        return {
            'provider_method_id': provider_data.get('id', ''),
            'is_verified': provider_data.get('verified', False)
        }
    
    def process_payment(self, customer_id: str, subscription_id: str, invoice_id: str,
                       amount: float, currency: str, payment_method_id: str,
                       metadata: Dict[str, Any] = None) -> PaymentTransaction:
        """Process a payment transaction"""
        
        transaction_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Get payment method
        payment_method = self._get_payment_method(customer_id, payment_method_id)
        if not payment_method:
            raise ValueError(f"Payment method {payment_method_id} not found")
        
        # Create transaction record
        transaction = PaymentTransaction(
            transaction_id=transaction_id,
            customer_id=customer_id,
            subscription_id=subscription_id,
            invoice_id=invoice_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            provider=payment_method.provider,
            provider_transaction_id="",
            status=PaymentStatus.PENDING,
            failure_reason=None,
            attempted_at=now,
            completed_at=None,
            metadata=metadata or {},
            webhook_received=False
        )
        
        # Process with provider
        try:
            if payment_method.provider == PaymentProvider.STRIPE:
                provider_result = self._process_stripe_payment(transaction)
            elif payment_method.provider == PaymentProvider.PAYPAL:
                provider_result = self._process_paypal_payment(transaction)
            else:
                provider_result = self._process_mock_payment(transaction)
            
            # Update transaction with provider result
            transaction.provider_transaction_id = provider_result['transaction_id']
            transaction.status = PaymentStatus(provider_result['status'])
            
            if transaction.status == PaymentStatus.COMPLETED:
                transaction.completed_at = now
            elif transaction.status == PaymentStatus.FAILED:
                transaction.failure_reason = provider_result.get('failure_reason')
        
        except Exception as e:
            transaction.status = PaymentStatus.FAILED
            transaction.failure_reason = str(e)
        
        # Store transaction
        self.transactions[transaction_id] = transaction
        
        return transaction
    
    def _get_payment_method(self, customer_id: str, method_id: str) -> Optional[PaymentMethodInfo]:
        """Get payment method by ID"""
        
        customer_methods = self.payment_methods.get(customer_id, [])
        for method in customer_methods:
            if method.method_id == method_id:
                return method
        return None
    
    def _process_stripe_payment(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Process payment with Stripe"""
        
        # In a real implementation, this would call Stripe API
        stripe_config = self.providers[PaymentProvider.STRIPE]
        
        # Simulate API call
        payment_intent_data = {
            'amount': int(transaction.amount * 100),  # Stripe uses cents
            'currency': transaction.currency.lower(),
            'payment_method': transaction.payment_method.provider_method_id,
            'confirm': True,
            'metadata': {
                'customer_id': transaction.customer_id,
                'subscription_id': transaction.subscription_id,
                'invoice_id': transaction.invoice_id
            }
        }
        
        # Mock successful response
        return {
            'transaction_id': f"pi_{uuid.uuid4().hex[:24]}",
            'status': 'completed',
            'provider_fees': self._calculate_stripe_fees(transaction.amount)
        }
    
    def _process_paypal_payment(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Process payment with PayPal"""
        
        # Mock PayPal processing
        return {
            'transaction_id': f"pp_{uuid.uuid4().hex[:20]}",
            'status': 'completed' if transaction.amount < 10000 else 'processing',
            'provider_fees': self._calculate_paypal_fees(transaction.amount)
        }
    
    def _process_mock_payment(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Process mock payment for testing"""
        
        # Simulate various scenarios based on amount
        if transaction.amount < 1:
            status = 'failed'
            failure_reason = 'Amount too small'
        elif transaction.amount > 50000:
            status = 'failed'
            failure_reason = 'Amount exceeds limit'
        else:
            status = 'completed'
            failure_reason = None
        
        return {
            'transaction_id': f"mock_{uuid.uuid4().hex[:16]}",
            'status': status,
            'failure_reason': failure_reason,
            'provider_fees': 0.0
        }
    
    def _calculate_stripe_fees(self, amount: float) -> float:
        """Calculate Stripe processing fees"""
        config = self.providers[PaymentProvider.STRIPE]['fees']
        return (amount * config['credit_card']) + config['fixed_fee']
    
    def _calculate_paypal_fees(self, amount: float) -> float:
        """Calculate PayPal processing fees"""
        config = self.providers[PaymentProvider.PAYPAL]['fees']
        return (amount * config['paypal']) + config['fixed_fee']
    
    def create_payment_schedule(self, customer_id: str, subscription_id: str,
                              payment_method_id: str, amount: float, currency: str,
                              frequency: str, start_date: datetime = None) -> PaymentSchedule:
        """Create a recurring payment schedule"""
        
        schedule_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Calculate next payment date
        if start_date is None:
            start_date = now
        
        if frequency == 'monthly':
            next_payment = start_date + timedelta(days=30)
        elif frequency == 'quarterly':
            next_payment = start_date + timedelta(days=90)
        elif frequency == 'annual':
            next_payment = start_date + timedelta(days=365)
        else:
            raise ValueError(f"Unsupported frequency: {frequency}")
        
        schedule = PaymentSchedule(
            schedule_id=schedule_id,
            customer_id=customer_id,
            subscription_id=subscription_id,
            payment_method_id=payment_method_id,
            amount=amount,
            currency=currency,
            frequency=frequency,
            next_payment_date=next_payment,
            is_active=True,
            failed_attempts=0,
            max_retry_attempts=self.retry_config['max_attempts'],
            created_at=now,
            updated_at=now
        )
        
        self.schedules[schedule_id] = schedule
        return schedule
    
    def process_scheduled_payments(self) -> List[PaymentTransaction]:
        """Process all due scheduled payments"""
        
        now = datetime.now()
        processed_transactions = []
        
        for schedule in self.schedules.values():
            if not schedule.is_active:
                continue
            
            if schedule.next_payment_date <= now:
                try:
                    # Process payment
                    transaction = self.process_payment(
                        customer_id=schedule.customer_id,
                        subscription_id=schedule.subscription_id,
                        invoice_id=f"auto_{schedule.schedule_id}_{int(time.time())}",
                        amount=schedule.amount,
                        currency=schedule.currency,
                        payment_method_id=schedule.payment_method_id,
                        metadata={'scheduled_payment': True, 'schedule_id': schedule.schedule_id}
                    )
                    
                    if transaction.status == PaymentStatus.COMPLETED:
                        # Update next payment date
                        if schedule.frequency == 'monthly':
                            schedule.next_payment_date += timedelta(days=30)
                        elif schedule.frequency == 'quarterly':
                            schedule.next_payment_date += timedelta(days=90)
                        elif schedule.frequency == 'annual':
                            schedule.next_payment_date += timedelta(days=365)
                        
                        schedule.failed_attempts = 0
                        schedule.updated_at = now
                        
                    else:
                        # Handle failed payment
                        schedule.failed_attempts += 1
                        
                        if schedule.failed_attempts >= schedule.max_retry_attempts:
                            schedule.is_active = False
                        else:
                            # Schedule retry
                            retry_delay = self.retry_config['retry_delays'][schedule.failed_attempts - 1]
                            schedule.next_payment_date = now + timedelta(hours=retry_delay)
                        
                        schedule.updated_at = now
                    
                    processed_transactions.append(transaction)
                
                except Exception as e:
                    # Log error and mark schedule for retry
                    schedule.failed_attempts += 1
                    if schedule.failed_attempts >= schedule.max_retry_attempts:
                        schedule.is_active = False
                    schedule.updated_at = now
        
        return processed_transactions
    
    def process_refund(self, original_transaction_id: str, amount: float,
                      reason: str, metadata: Dict[str, Any] = None) -> RefundTransaction:
        """Process a refund for a transaction"""
        
        refund_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Get original transaction
        original_transaction = self.transactions.get(original_transaction_id)
        if not original_transaction:
            raise ValueError(f"Original transaction {original_transaction_id} not found")
        
        if original_transaction.status != PaymentStatus.COMPLETED:
            raise ValueError("Can only refund completed transactions")
        
        if amount > original_transaction.amount:
            raise ValueError("Refund amount cannot exceed original transaction amount")
        
        # Create refund record
        refund = RefundTransaction(
            refund_id=refund_id,
            original_transaction_id=original_transaction_id,
            customer_id=original_transaction.customer_id,
            amount=amount,
            currency=original_transaction.currency,
            reason=reason,
            status=PaymentStatus.PENDING,
            provider_refund_id="",
            requested_at=now,
            processed_at=None,
            metadata=metadata or {}
        )
        
        # Process with provider
        try:
            if original_transaction.provider == PaymentProvider.STRIPE:
                provider_result = self._process_stripe_refund(original_transaction, amount)
            elif original_transaction.provider == PaymentProvider.PAYPAL:
                provider_result = self._process_paypal_refund(original_transaction, amount)
            else:
                provider_result = self._process_mock_refund(original_transaction, amount)
            
            refund.provider_refund_id = provider_result['refund_id']
            refund.status = PaymentStatus(provider_result['status'])
            
            if refund.status == PaymentStatus.COMPLETED:
                refund.processed_at = now
        
        except Exception as e:
            refund.status = PaymentStatus.FAILED
        
        # Store refund
        self.refunds[refund_id] = refund
        
        return refund
    
    def _process_stripe_refund(self, transaction: PaymentTransaction, amount: float) -> Dict[str, Any]:
        """Process refund with Stripe"""
        
        # Mock Stripe refund API call
        return {
            'refund_id': f"re_{uuid.uuid4().hex[:24]}",
            'status': 'completed'
        }
    
    def _process_paypal_refund(self, transaction: PaymentTransaction, amount: float) -> Dict[str, Any]:
        """Process refund with PayPal"""
        
        # Mock PayPal refund API call
        return {
            'refund_id': f"ref_{uuid.uuid4().hex[:20]}",
            'status': 'completed'
        }
    
    def _process_mock_refund(self, transaction: PaymentTransaction, amount: float) -> Dict[str, Any]:
        """Process mock refund"""
        
        return {
            'refund_id': f"refund_{uuid.uuid4().hex[:16]}",
            'status': 'completed'
        }
    
    def handle_webhook(self, provider: PaymentProvider, payload: Dict[str, Any],
                      signature: str = None) -> Dict[str, Any]:
        """Handle payment provider webhooks"""
        
        if provider == PaymentProvider.STRIPE:
            return self._handle_stripe_webhook(payload, signature)
        elif provider == PaymentProvider.PAYPAL:
            return self._handle_paypal_webhook(payload, signature)
        else:
            return {'status': 'unsupported_provider'}
    
    def _handle_stripe_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook"""
        
        # Verify webhook signature
        if not self._verify_stripe_signature(payload, signature):
            return {'status': 'invalid_signature'}
        
        event_type = payload.get('type')
        event_data = payload.get('data', {}).get('object', {})
        
        if event_type == 'payment_intent.succeeded':
            # Update transaction status
            provider_transaction_id = event_data.get('id')
            transaction = self._find_transaction_by_provider_id(provider_transaction_id)
            
            if transaction:
                transaction.status = PaymentStatus.COMPLETED
                transaction.completed_at = datetime.now()
                transaction.webhook_received = True
        
        elif event_type == 'payment_intent.payment_failed':
            provider_transaction_id = event_data.get('id')
            transaction = self._find_transaction_by_provider_id(provider_transaction_id)
            
            if transaction:
                transaction.status = PaymentStatus.FAILED
                transaction.failure_reason = event_data.get('last_payment_error', {}).get('message')
                transaction.webhook_received = True
        
        return {'status': 'processed'}
    
    def _handle_paypal_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Handle PayPal webhook"""
        
        # Mock PayPal webhook handling
        return {'status': 'processed'}
    
    def _verify_stripe_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify Stripe webhook signature"""
        
        if not signature:
            return False
        
        # In a real implementation, this would verify the HMAC signature
        webhook_secret = self.providers[PaymentProvider.STRIPE]['webhook_secret']
        # Mock verification
        return True
    
    def _find_transaction_by_provider_id(self, provider_transaction_id: str) -> Optional[PaymentTransaction]:
        """Find transaction by provider transaction ID"""
        
        for transaction in self.transactions.values():
            if transaction.provider_transaction_id == provider_transaction_id:
                return transaction
        return None
    
    def get_payment_analytics(self, customer_id: str = None, 
                            start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get payment analytics and metrics"""
        
        transactions = list(self.transactions.values())
        
        if customer_id:
            transactions = [t for t in transactions if t.customer_id == customer_id]
        
        if start_date:
            transactions = [t for t in transactions if t.attempted_at >= start_date]
        
        if end_date:
            transactions = [t for t in transactions if t.attempted_at <= end_date]
        
        # Calculate metrics
        total_transactions = len(transactions)
        successful_transactions = len([t for t in transactions if t.status == PaymentStatus.COMPLETED])
        failed_transactions = len([t for t in transactions if t.status == PaymentStatus.FAILED])
        
        total_volume = sum(t.amount for t in transactions if t.status == PaymentStatus.COMPLETED)
        average_transaction = total_volume / max(successful_transactions, 1)
        
        success_rate = (successful_transactions / max(total_transactions, 1)) * 100
        
        # Payment method breakdown
        method_breakdown = {}
        for transaction in transactions:
            method = transaction.payment_method.payment_type.value
            if method not in method_breakdown:
                method_breakdown[method] = {'count': 0, 'volume': 0.0}
            method_breakdown[method]['count'] += 1
            if transaction.status == PaymentStatus.COMPLETED:
                method_breakdown[method]['volume'] += transaction.amount
        
        # Provider breakdown
        provider_breakdown = {}
        for transaction in transactions:
            provider = transaction.provider.value
            if provider not in provider_breakdown:
                provider_breakdown[provider] = {'count': 0, 'volume': 0.0}
            provider_breakdown[provider]['count'] += 1
            if transaction.status == PaymentStatus.COMPLETED:
                provider_breakdown[provider]['volume'] += transaction.amount
        
        return {
            'total_transactions': total_transactions,
            'successful_transactions': successful_transactions,
            'failed_transactions': failed_transactions,
            'success_rate': round(success_rate, 2),
            'total_volume': round(total_volume, 2),
            'average_transaction': round(average_transaction, 2),
            'method_breakdown': method_breakdown,
            'provider_breakdown': provider_breakdown,
            'active_schedules': len([s for s in self.schedules.values() if s.is_active])
        }

def serialize_payment_method(method: PaymentMethodInfo) -> Dict[str, Any]:
    """Convert PaymentMethodInfo to JSON-serializable dict"""
    result = asdict(method)
    result['provider'] = method.provider.value
    result['payment_type'] = method.payment_type.value
    result['created_at'] = method.created_at.isoformat()
    result['updated_at'] = method.updated_at.isoformat()
    return result

def serialize_payment_transaction(transaction: PaymentTransaction) -> Dict[str, Any]:
    """Convert PaymentTransaction to JSON-serializable dict"""
    result = asdict(transaction)
    result['payment_method'] = serialize_payment_method(transaction.payment_method)
    result['provider'] = transaction.provider.value
    result['status'] = transaction.status.value
    result['attempted_at'] = transaction.attempted_at.isoformat()
    result['completed_at'] = transaction.completed_at.isoformat() if transaction.completed_at else None
    return result

def serialize_payment_schedule(schedule: PaymentSchedule) -> Dict[str, Any]:
    """Convert PaymentSchedule to JSON-serializable dict"""
    result = asdict(schedule)
    result['next_payment_date'] = schedule.next_payment_date.isoformat()
    result['created_at'] = schedule.created_at.isoformat()
    result['updated_at'] = schedule.updated_at.isoformat()
    return result