#!/usr/bin/env python3
"""
Payment Gateway Connector for EstateCore Phase 8A
Advanced integration with multiple payment processors for rent collection and property transactions
"""

import os
import json
import asyncio
import logging
import aiohttp
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from decimal import Decimal, ROUND_HALF_UP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentProvider(Enum):
    STRIPE = "stripe"
    SQUARE = "square"
    PAYPAL = "paypal"
    ACH_DIRECT = "ach_direct"
    ZELLE = "zelle"
    VENMO = "venmo"
    BANK_TRANSFER = "bank_transfer"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class TransactionType(Enum):
    RENT_PAYMENT = "rent_payment"
    SECURITY_DEPOSIT = "security_deposit"
    LATE_FEE = "late_fee"
    MAINTENANCE_FEE = "maintenance_fee"
    UTILITY_PAYMENT = "utility_payment"
    APPLICATION_FEE = "application_fee"
    REFUND = "refund"
    VENDOR_PAYMENT = "vendor_payment"

@dataclass
class PaymentCredentials:
    """Payment provider credentials"""
    provider: PaymentProvider
    public_key: str
    private_key: str
    webhook_secret: Optional[str]
    merchant_id: Optional[str]
    environment: str  # "sandbox" or "production"
    api_version: str
    endpoint_url: str

@dataclass
class PaymentMethod:
    """Payment method information"""
    method_id: str
    user_id: str
    provider: PaymentProvider
    type: PaymentMethod
    last_four: str
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    brand: Optional[str]
    bank_name: Optional[str]
    account_type: Optional[str]
    is_default: bool
    is_verified: bool
    billing_address: Dict[str, str]
    created_at: datetime
    updated_at: datetime

@dataclass
class PaymentRequest:
    """Payment request details"""
    request_id: str
    user_id: str
    property_id: str
    lease_id: Optional[str]
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    description: str
    payment_method_id: str
    provider: PaymentProvider
    due_date: Optional[datetime]
    late_fee_amount: Optional[Decimal]
    metadata: Dict[str, Any]
    idempotency_key: str

@dataclass
class PaymentResult:
    """Payment processing result"""
    transaction_id: str
    request_id: str
    provider_transaction_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    fees: Decimal
    net_amount: Decimal
    payment_method: str
    provider: PaymentProvider
    processed_at: datetime
    settlement_date: Optional[datetime]
    failure_reason: Optional[str]
    provider_response: Dict[str, Any]

@dataclass
class RefundRequest:
    """Refund request details"""
    refund_id: str
    original_transaction_id: str
    amount: Optional[Decimal]  # None for full refund
    reason: str
    metadata: Dict[str, Any]

@dataclass
class WebhookEvent:
    """Webhook event from payment provider"""
    event_id: str
    provider: PaymentProvider
    event_type: str
    transaction_id: str
    data: Dict[str, Any]
    signature: str
    timestamp: datetime
    processed: bool

class PaymentConnector:
    """Advanced payment connector with multi-provider support"""
    
    def __init__(self):
        self.providers: Dict[PaymentProvider, PaymentCredentials] = {}
        self.payment_methods: Dict[str, PaymentMethod] = {}
        self.transactions: Dict[str, PaymentResult] = {}
        self.webhook_handlers: Dict[PaymentProvider, callable] = {}
        
        # Load provider configurations
        self._load_provider_configs()
        
        # Set up webhook handlers
        self._setup_webhook_handlers()
        
        logger.info("Payment Connector initialized")
    
    def _load_provider_configs(self):
        """Load payment provider configurations"""
        # Stripe configuration
        self.providers[PaymentProvider.STRIPE] = PaymentCredentials(
            provider=PaymentProvider.STRIPE,
            public_key=os.getenv("STRIPE_PUBLIC_KEY", "pk_test_demo"),
            private_key=os.getenv("STRIPE_SECRET_KEY", "sk_test_demo"),
            webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_demo"),
            merchant_id=None,
            environment=os.getenv("STRIPE_ENV", "sandbox"),
            api_version="2023-10-16",
            endpoint_url="https://api.stripe.com/v1/"
        )
        
        # Square configuration
        self.providers[PaymentProvider.SQUARE] = PaymentCredentials(
            provider=PaymentProvider.SQUARE,
            public_key=os.getenv("SQUARE_PUBLIC_KEY", "sq0idp_demo"),
            private_key=os.getenv("SQUARE_SECRET_KEY", "sq0atp_demo"),
            webhook_secret=os.getenv("SQUARE_WEBHOOK_SECRET", "webhook_demo"),
            merchant_id=os.getenv("SQUARE_MERCHANT_ID", "merchant_demo"),
            environment=os.getenv("SQUARE_ENV", "sandbox"),
            api_version="2023-12-13",
            endpoint_url="https://connect.squareupsandbox.com/" if os.getenv("SQUARE_ENV", "sandbox") == "sandbox" else "https://connect.squareup.com/"
        )
        
        # PayPal configuration
        self.providers[PaymentProvider.PAYPAL] = PaymentCredentials(
            provider=PaymentProvider.PAYPAL,
            public_key=os.getenv("PAYPAL_CLIENT_ID", "client_demo"),
            private_key=os.getenv("PAYPAL_CLIENT_SECRET", "secret_demo"),
            webhook_secret=os.getenv("PAYPAL_WEBHOOK_ID", "webhook_demo"),
            merchant_id=None,
            environment=os.getenv("PAYPAL_ENV", "sandbox"),
            api_version="v2",
            endpoint_url="https://api.sandbox.paypal.com/" if os.getenv("PAYPAL_ENV", "sandbox") == "sandbox" else "https://api.paypal.com/"
        )
    
    def _setup_webhook_handlers(self):
        """Set up webhook event handlers"""
        self.webhook_handlers = {
            PaymentProvider.STRIPE: self._handle_stripe_webhook,
            PaymentProvider.SQUARE: self._handle_square_webhook,
            PaymentProvider.PAYPAL: self._handle_paypal_webhook
        }
    
    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        """Process payment through specified provider"""
        try:
            logger.info(f"Processing payment {payment_request.request_id} via {payment_request.provider.value}")
            
            # Validate payment request
            self._validate_payment_request(payment_request)
            
            # Process based on provider
            if payment_request.provider == PaymentProvider.STRIPE:
                result = await self._process_stripe_payment(payment_request)
            elif payment_request.provider == PaymentProvider.SQUARE:
                result = await self._process_square_payment(payment_request)
            elif payment_request.provider == PaymentProvider.PAYPAL:
                result = await self._process_paypal_payment(payment_request)
            else:
                result = await self._process_generic_payment(payment_request)
            
            # Store transaction
            self.transactions[result.transaction_id] = result
            
            # Log result
            logger.info(f"Payment {result.status.value}: {result.transaction_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            
            # Create failure result
            return PaymentResult(
                transaction_id=str(uuid.uuid4()),
                request_id=payment_request.request_id,
                provider_transaction_id="",
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                fees=Decimal("0"),
                net_amount=Decimal("0"),
                payment_method=payment_request.payment_method_id,
                provider=payment_request.provider,
                processed_at=datetime.now(),
                settlement_date=None,
                failure_reason=str(e),
                provider_response={}
            )
    
    def _validate_payment_request(self, request: PaymentRequest):
        """Validate payment request"""
        if request.amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if request.currency not in ["USD", "EUR", "GBP", "CAD"]:
            raise ValueError("Unsupported currency")
        
        if request.provider not in self.providers:
            raise ValueError("Unsupported payment provider")
        
        # Additional validation logic here
    
    async def _process_stripe_payment(self, request: PaymentRequest) -> PaymentResult:
        """Process payment via Stripe"""
        credentials = self.providers[PaymentProvider.STRIPE]
        
        # Simulate Stripe API call
        payment_intent_data = {
            "amount": int(request.amount * 100),  # Stripe uses cents
            "currency": request.currency.lower(),
            "payment_method": request.payment_method_id,
            "description": request.description,
            "metadata": request.metadata,
            "confirm": True,
            "return_url": "https://estatecore.com/payment/return"
        }
        
        # Simulate Stripe response
        await asyncio.sleep(2)  # Simulate network delay
        
        # Generate mock response
        provider_response = {
            "id": f"pi_{uuid.uuid4().hex[:24]}",
            "status": "succeeded",
            "amount": int(request.amount * 100),
            "currency": request.currency.lower(),
            "fees": 30 + int(request.amount * 2.9),  # Stripe fees: $0.30 + 2.9%
            "net": int(request.amount * 100) - (30 + int(request.amount * 2.9))
        }
        
        fees = Decimal(str(provider_response["fees"])) / 100
        net_amount = request.amount - fees
        
        return PaymentResult(
            transaction_id=str(uuid.uuid4()),
            request_id=request.request_id,
            provider_transaction_id=provider_response["id"],
            status=PaymentStatus.COMPLETED,
            amount=request.amount,
            currency=request.currency,
            fees=fees,
            net_amount=net_amount,
            payment_method=request.payment_method_id,
            provider=PaymentProvider.STRIPE,
            processed_at=datetime.now(),
            settlement_date=datetime.now() + timedelta(days=2),
            failure_reason=None,
            provider_response=provider_response
        )
    
    async def _process_square_payment(self, request: PaymentRequest) -> PaymentResult:
        """Process payment via Square"""
        credentials = self.providers[PaymentProvider.SQUARE]
        
        # Simulate Square API call
        payment_data = {
            "source_id": request.payment_method_id,
            "amount_money": {
                "amount": int(request.amount * 100),
                "currency": request.currency
            },
            "idempotency_key": request.idempotency_key,
            "note": request.description
        }
        
        await asyncio.sleep(1.5)  # Simulate network delay
        
        # Generate mock response
        provider_response = {
            "id": f"sq_{uuid.uuid4().hex[:20]}",
            "status": "COMPLETED",
            "amount_money": {
                "amount": int(request.amount * 100),
                "currency": request.currency
            },
            "processing_fee": [
                {
                    "amount_money": {
                        "amount": 30 + int(request.amount * 2.6),  # Square fees
                        "currency": request.currency
                    }
                }
            ]
        }
        
        fees = Decimal("0.30") + (request.amount * Decimal("0.026"))
        net_amount = request.amount - fees
        
        return PaymentResult(
            transaction_id=str(uuid.uuid4()),
            request_id=request.request_id,
            provider_transaction_id=provider_response["id"],
            status=PaymentStatus.COMPLETED,
            amount=request.amount,
            currency=request.currency,
            fees=fees,
            net_amount=net_amount,
            payment_method=request.payment_method_id,
            provider=PaymentProvider.SQUARE,
            processed_at=datetime.now(),
            settlement_date=datetime.now() + timedelta(days=1),
            failure_reason=None,
            provider_response=provider_response
        )
    
    async def _process_paypal_payment(self, request: PaymentRequest) -> PaymentResult:
        """Process payment via PayPal"""
        credentials = self.providers[PaymentProvider.PAYPAL]
        
        # Simulate PayPal payment flow
        await asyncio.sleep(3)  # Simulate longer PayPal processing
        
        # Generate mock response
        provider_response = {
            "id": f"PAY-{uuid.uuid4().hex[:17].upper()}",
            "state": "approved",
            "transactions": [
                {
                    "amount": {
                        "total": str(request.amount),
                        "currency": request.currency
                    },
                    "payee": {
                        "merchant_id": credentials.merchant_id
                    }
                }
            ]
        }
        
        fees = request.amount * Decimal("0.034") + Decimal("0.49")  # PayPal fees
        net_amount = request.amount - fees
        
        return PaymentResult(
            transaction_id=str(uuid.uuid4()),
            request_id=request.request_id,
            provider_transaction_id=provider_response["id"],
            status=PaymentStatus.COMPLETED,
            amount=request.amount,
            currency=request.currency,
            fees=fees,
            net_amount=net_amount,
            payment_method=request.payment_method_id,
            provider=PaymentProvider.PAYPAL,
            processed_at=datetime.now(),
            settlement_date=datetime.now() + timedelta(days=1),
            failure_reason=None,
            provider_response=provider_response
        )
    
    async def _process_generic_payment(self, request: PaymentRequest) -> PaymentResult:
        """Process payment via generic provider"""
        await asyncio.sleep(1)  # Simulate processing
        
        # Generic successful payment
        fees = request.amount * Decimal("0.025")  # 2.5% fee
        net_amount = request.amount - fees
        
        return PaymentResult(
            transaction_id=str(uuid.uuid4()),
            request_id=request.request_id,
            provider_transaction_id=f"gen_{uuid.uuid4().hex[:16]}",
            status=PaymentStatus.COMPLETED,
            amount=request.amount,
            currency=request.currency,
            fees=fees,
            net_amount=net_amount,
            payment_method=request.payment_method_id,
            provider=request.provider,
            processed_at=datetime.now(),
            settlement_date=datetime.now() + timedelta(days=3),
            failure_reason=None,
            provider_response={}
        )
    
    async def process_refund(self, refund_request: RefundRequest) -> PaymentResult:
        """Process refund for a transaction"""
        try:
            # Get original transaction
            original_transaction = self.transactions.get(refund_request.original_transaction_id)
            if not original_transaction:
                raise ValueError("Original transaction not found")
            
            # Determine refund amount
            refund_amount = refund_request.amount or original_transaction.amount
            
            if refund_amount > original_transaction.amount:
                raise ValueError("Refund amount cannot exceed original transaction amount")
            
            # Process refund based on provider
            if original_transaction.provider == PaymentProvider.STRIPE:
                result = await self._process_stripe_refund(original_transaction, refund_amount, refund_request)
            elif original_transaction.provider == PaymentProvider.SQUARE:
                result = await self._process_square_refund(original_transaction, refund_amount, refund_request)
            elif original_transaction.provider == PaymentProvider.PAYPAL:
                result = await self._process_paypal_refund(original_transaction, refund_amount, refund_request)
            else:
                result = await self._process_generic_refund(original_transaction, refund_amount, refund_request)
            
            # Store refund transaction
            self.transactions[result.transaction_id] = result
            
            logger.info(f"Refund processed: {result.transaction_id}")
            return result
            
        except Exception as e:
            logger.error(f"Refund processing failed: {e}")
            raise
    
    async def _process_stripe_refund(self, original: PaymentResult, amount: Decimal, request: RefundRequest) -> PaymentResult:
        """Process Stripe refund"""
        await asyncio.sleep(1)
        
        return PaymentResult(
            transaction_id=str(uuid.uuid4()),
            request_id=request.refund_id,
            provider_transaction_id=f"re_{uuid.uuid4().hex[:24]}",
            status=PaymentStatus.REFUNDED,
            amount=-amount,  # Negative for refund
            currency=original.currency,
            fees=Decimal("0"),  # No fees for refunds
            net_amount=-amount,
            payment_method=original.payment_method,
            provider=PaymentProvider.STRIPE,
            processed_at=datetime.now(),
            settlement_date=datetime.now() + timedelta(days=5),
            failure_reason=None,
            provider_response={"refund_reason": request.reason}
        )
    
    async def save_payment_method(self, user_id: str, provider: PaymentProvider, 
                                 method_data: Dict[str, Any]) -> PaymentMethod:
        """Save payment method for user"""
        try:
            method_id = str(uuid.uuid4())
            
            # Extract payment method details based on provider
            if provider == PaymentProvider.STRIPE:
                payment_method = await self._save_stripe_payment_method(user_id, method_id, method_data)
            elif provider == PaymentProvider.SQUARE:
                payment_method = await self._save_square_payment_method(user_id, method_id, method_data)
            else:
                payment_method = await self._save_generic_payment_method(user_id, method_id, method_data, provider)
            
            # Store payment method
            self.payment_methods[method_id] = payment_method
            
            logger.info(f"Payment method saved: {method_id} for user {user_id}")
            return payment_method
            
        except Exception as e:
            logger.error(f"Failed to save payment method: {e}")
            raise
    
    async def handle_webhook(self, provider: PaymentProvider, payload: Dict[str, Any], 
                           signature: str) -> WebhookEvent:
        """Handle webhook from payment provider"""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(provider, payload, signature):
                raise ValueError("Invalid webhook signature")
            
            # Create webhook event
            event = WebhookEvent(
                event_id=str(uuid.uuid4()),
                provider=provider,
                event_type=payload.get("type", "unknown"),
                transaction_id=payload.get("data", {}).get("object", {}).get("id", ""),
                data=payload,
                signature=signature,
                timestamp=datetime.now(),
                processed=False
            )
            
            # Process webhook based on provider
            handler = self.webhook_handlers.get(provider)
            if handler:
                await handler(event)
            
            event.processed = True
            logger.info(f"Webhook processed: {event.event_id}")
            
            return event
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise
    
    def _verify_webhook_signature(self, provider: PaymentProvider, payload: Dict[str, Any], 
                                 signature: str) -> bool:
        """Verify webhook signature"""
        credentials = self.providers.get(provider)
        if not credentials or not credentials.webhook_secret:
            return False
        
        # Simplified signature verification
        # In production, implement proper HMAC verification for each provider
        expected_signature = hmac.new(
            credentials.webhook_secret.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def _handle_stripe_webhook(self, event: WebhookEvent):
        """Handle Stripe webhook events"""
        event_type = event.event_type
        
        if event_type == "payment_intent.succeeded":
            # Update transaction status
            transaction_id = event.data.get("data", {}).get("object", {}).get("id")
            logger.info(f"Stripe payment succeeded: {transaction_id}")
        
        elif event_type == "payment_intent.payment_failed":
            # Handle payment failure
            transaction_id = event.data.get("data", {}).get("object", {}).get("id")
            logger.warning(f"Stripe payment failed: {transaction_id}")
        
        # Add more event handlers as needed
    
    async def get_transaction_status(self, transaction_id: str) -> Optional[PaymentResult]:
        """Get transaction status"""
        return self.transactions.get(transaction_id)
    
    async def get_payment_methods(self, user_id: str) -> List[PaymentMethod]:
        """Get payment methods for user"""
        return [method for method in self.payment_methods.values() if method.user_id == user_id]
    
    async def get_payment_analytics(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Get payment analytics"""
        start_date = date_range.get("start_date", datetime.now() - timedelta(days=30))
        end_date = date_range.get("end_date", datetime.now())
        
        # Filter transactions by date range
        transactions = [
            tx for tx in self.transactions.values()
            if start_date <= tx.processed_at <= end_date
        ]
        
        if not transactions:
            return {"message": "No transactions in date range"}
        
        # Calculate analytics
        total_volume = sum(tx.amount for tx in transactions if tx.amount > 0)
        total_fees = sum(tx.fees for tx in transactions)
        total_count = len(transactions)
        
        # Success rate
        successful_transactions = [tx for tx in transactions if tx.status == PaymentStatus.COMPLETED]
        success_rate = len(successful_transactions) / total_count if total_count > 0 else 0
        
        # Provider breakdown
        provider_stats = {}
        for provider in PaymentProvider:
            provider_transactions = [tx for tx in transactions if tx.provider == provider]
            if provider_transactions:
                provider_stats[provider.value] = {
                    "count": len(provider_transactions),
                    "volume": sum(tx.amount for tx in provider_transactions if tx.amount > 0),
                    "fees": sum(tx.fees for tx in provider_transactions)
                }
        
        return {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_volume": float(total_volume),
            "total_fees": float(total_fees),
            "transaction_count": total_count,
            "success_rate": success_rate,
            "average_transaction_size": float(total_volume / len(successful_transactions)) if successful_transactions else 0,
            "provider_breakdown": provider_stats,
            "last_updated": datetime.now().isoformat()
        }

# Global instance
_payment_connector = None

def get_payment_connector() -> PaymentConnector:
    """Get global payment connector instance"""
    global _payment_connector
    if _payment_connector is None:
        _payment_connector = PaymentConnector()
    return _payment_connector

# API convenience functions
async def process_payment_api(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment for API"""
    connector = get_payment_connector()
    
    # Convert dict to PaymentRequest
    payment_request = PaymentRequest(
        request_id=payment_data.get("request_id", str(uuid.uuid4())),
        user_id=payment_data["user_id"],
        property_id=payment_data["property_id"],
        lease_id=payment_data.get("lease_id"),
        amount=Decimal(str(payment_data["amount"])),
        currency=payment_data.get("currency", "USD"),
        transaction_type=TransactionType(payment_data.get("transaction_type", "rent_payment")),
        description=payment_data.get("description", "Property payment"),
        payment_method_id=payment_data["payment_method_id"],
        provider=PaymentProvider(payment_data.get("provider", "stripe")),
        due_date=datetime.fromisoformat(payment_data["due_date"]) if payment_data.get("due_date") else None,
        late_fee_amount=Decimal(str(payment_data["late_fee_amount"])) if payment_data.get("late_fee_amount") else None,
        metadata=payment_data.get("metadata", {}),
        idempotency_key=payment_data.get("idempotency_key", str(uuid.uuid4()))
    )
    
    result = await connector.process_payment(payment_request)
    
    return {
        "transaction_id": result.transaction_id,
        "status": result.status.value,
        "amount": float(result.amount),
        "fees": float(result.fees),
        "net_amount": float(result.net_amount),
        "provider_transaction_id": result.provider_transaction_id,
        "processed_at": result.processed_at.isoformat(),
        "settlement_date": result.settlement_date.isoformat() if result.settlement_date else None,
        "failure_reason": result.failure_reason
    }

async def get_payment_analytics_api(date_range: Dict[str, str] = None) -> Dict[str, Any]:
    """Get payment analytics for API"""
    connector = get_payment_connector()
    
    if date_range:
        parsed_range = {
            "start_date": datetime.fromisoformat(date_range["start_date"]),
            "end_date": datetime.fromisoformat(date_range["end_date"])
        }
    else:
        parsed_range = {
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now()
        }
    
    return await connector.get_payment_analytics(parsed_range)

if __name__ == "__main__":
    # Test the Payment Connector
    async def test_payment_connector():
        connector = PaymentConnector()
        
        print("Testing Payment Connector")
        print("=" * 50)
        
        # Test payment processing
        payment_request = PaymentRequest(
            request_id="test-payment-001",
            user_id="user_123",
            property_id="prop_456",
            lease_id="lease_789",
            amount=Decimal("1250.00"),
            currency="USD",
            transaction_type=TransactionType.RENT_PAYMENT,
            description="Monthly rent payment",
            payment_method_id="pm_test_card",
            provider=PaymentProvider.STRIPE,
            due_date=datetime.now() + timedelta(days=5),
            late_fee_amount=None,
            metadata={"property_address": "123 Test St"},
            idempotency_key=str(uuid.uuid4())
        )
        
        print("Processing payment...")
        result = await connector.process_payment(payment_request)
        print(f"Payment status: {result.status.value}")
        print(f"Transaction ID: {result.transaction_id}")
        print(f"Amount: ${result.amount}")
        print(f"Fees: ${result.fees}")
        print(f"Net amount: ${result.net_amount}")
        
        # Test analytics
        print("\nGetting payment analytics...")
        analytics = await connector.get_payment_analytics({
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now()
        })
        print(f"Total volume: ${analytics.get('total_volume', 0):,.2f}")
        print(f"Transaction count: {analytics.get('transaction_count', 0)}")
        print(f"Success rate: {analytics.get('success_rate', 0):.1%}")
        
        print("\nPayment Connector Test Complete!")
    
    asyncio.run(test_payment_connector())