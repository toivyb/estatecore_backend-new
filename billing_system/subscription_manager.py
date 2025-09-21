import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class SubscriptionTier(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class BillingCycle(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    EXPIRED = "expired"

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"

@dataclass
class PricingTier:
    tier: SubscriptionTier
    name: str
    description: str
    
    # Base pricing
    monthly_price: float
    quarterly_price: float
    annual_price: float
    
    # Feature limits
    max_properties: int
    max_units: int
    max_users: int
    max_documents_gb: float
    max_api_calls_per_month: int
    
    # Feature access
    ai_analytics: bool
    predictive_maintenance: bool
    iot_integration: bool
    advanced_reporting: bool
    white_labeling: bool
    priority_support: bool
    custom_integrations: bool
    
    # Usage-based pricing
    overage_property_price: float
    overage_unit_price: float
    overage_user_price: float
    overage_storage_gb_price: float
    overage_api_call_price: float

@dataclass
class Subscription:
    subscription_id: str
    customer_id: str
    company_name: str
    
    # Subscription details
    tier: SubscriptionTier
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    
    # Dates
    start_date: datetime
    current_period_start: datetime
    current_period_end: datetime
    trial_end_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    
    # Pricing
    base_price: float
    current_price: float
    currency: str
    
    # Usage limits
    properties_included: int
    units_included: int
    users_included: int
    storage_gb_included: float
    api_calls_included: int
    
    # Current usage
    properties_used: int
    units_used: int
    users_used: int
    storage_gb_used: float
    api_calls_used: int
    
    # Billing
    auto_renew: bool
    payment_method_id: Optional[str]
    last_payment_date: Optional[datetime]
    next_billing_date: datetime
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    notes: str

@dataclass
class UsageRecord:
    record_id: str
    subscription_id: str
    customer_id: str
    
    # Usage metrics
    property_count: int
    unit_count: int
    user_count: int
    storage_gb_used: float
    api_calls_made: int
    
    # Feature usage
    ai_analytics_calls: int
    predictive_maintenance_runs: int
    iot_data_points: int
    reports_generated: int
    
    # Time period
    usage_date: datetime
    billing_period_start: datetime
    billing_period_end: datetime
    
    created_at: datetime

@dataclass
class Invoice:
    invoice_id: str
    subscription_id: str
    customer_id: str
    company_name: str
    
    # Invoice details
    invoice_number: str
    issue_date: datetime
    due_date: datetime
    billing_period_start: datetime
    billing_period_end: datetime
    
    # Amounts
    subtotal: float
    tax_rate: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    currency: str
    
    # Line items
    base_subscription_amount: float
    overage_charges: Dict[str, float]
    one_time_charges: Dict[str, float]
    credits_applied: float
    
    # Status
    status: PaymentStatus
    paid_date: Optional[datetime]
    payment_method: Optional[str]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    notes: str

class SubscriptionManager:
    """
    Comprehensive subscription management system for SaaS billing
    """
    
    def __init__(self):
        self.pricing_tiers = {}
        self.subscriptions = {}
        self.usage_records = {}
        self.invoices = {}
        self._initialize_pricing_tiers()
    
    def _initialize_pricing_tiers(self):
        """Initialize default pricing tiers"""
        
        # Starter Tier - Unit-based pricing
        self.pricing_tiers[SubscriptionTier.STARTER] = PricingTier(
            tier=SubscriptionTier.STARTER,
            name="Starter",
            description="Perfect for small property managers - $2.50 per unit",
            monthly_price=0.0,      # Base monthly fee is now 0
            quarterly_price=0.0,    # Base quarterly fee is now 0
            annual_price=0.0,       # Base annual fee is now 0
            max_properties=999999,  # Unlimited properties
            max_units=999999,       # Unlimited units
            max_users=999999,       # Unlimited users
            max_documents_gb=999999.0,
            max_api_calls_per_month=999999999,
            ai_analytics=True,
            predictive_maintenance=True,
            iot_integration=True,
            advanced_reporting=True,
            white_labeling=False,
            priority_support=False,
            custom_integrations=False,
            overage_property_price=0.0,
            overage_unit_price=2.50,  # $2.50 per unit
            overage_user_price=0.0,
            overage_storage_gb_price=0.0,
            overage_api_call_price=0.0
        )
        
        # Professional Tier - Unit-based pricing with premium features
        self.pricing_tiers[SubscriptionTier.PROFESSIONAL] = PricingTier(
            tier=SubscriptionTier.PROFESSIONAL,
            name="Professional",
            description="Advanced features for growing businesses - $2.50 per unit",
            monthly_price=0.0,      # Base monthly fee is now 0
            quarterly_price=0.0,    # Base quarterly fee is now 0
            annual_price=0.0,       # Base annual fee is now 0
            max_properties=999999,  # Unlimited properties
            max_units=999999,       # Unlimited units
            max_users=999999,       # Unlimited users
            max_documents_gb=999999.0,
            max_api_calls_per_month=999999999,
            ai_analytics=True,
            predictive_maintenance=True,
            iot_integration=True,
            advanced_reporting=True,
            white_labeling=True,
            priority_support=True,
            custom_integrations=True,
            overage_property_price=0.0,
            overage_unit_price=2.50,  # $2.50 per unit
            overage_user_price=0.0,
            overage_storage_gb_price=0.0,
            overage_api_call_price=0.0
        )
        
        # Enterprise Tier - Unit-based pricing with all features
        self.pricing_tiers[SubscriptionTier.ENTERPRISE] = PricingTier(
            tier=SubscriptionTier.ENTERPRISE,
            name="Enterprise",
            description="Full-featured solution for large organizations - $2.50 per unit",
            monthly_price=0.0,       # Base monthly fee is now 0
            quarterly_price=0.0,     # Base quarterly fee is now 0
            annual_price=0.0,        # Base annual fee is now 0
            max_properties=999999,   # Unlimited
            max_units=999999,        # Unlimited
            max_users=999999,        # Unlimited
            max_documents_gb=999999.0,
            max_api_calls_per_month=999999999,
            ai_analytics=True,
            predictive_maintenance=True,
            iot_integration=True,
            advanced_reporting=True,
            white_labeling=True,
            priority_support=True,
            custom_integrations=True,
            overage_property_price=0.0,
            overage_unit_price=2.50,  # $2.50 per unit
            overage_user_price=0.0,
            overage_storage_gb_price=0.0,
            overage_api_call_price=0.0
        )
    
    def create_subscription(self, customer_id: str, company_name: str, tier: SubscriptionTier, 
                          billing_cycle: BillingCycle, trial_days: int = 14) -> Subscription:
        """Create a new subscription"""
        
        pricing = self.pricing_tiers[tier]
        subscription_id = str(uuid.uuid4())
        
        now = datetime.now()
        trial_end = now + timedelta(days=trial_days) if trial_days > 0 else None
        
        # Calculate pricing based on billing cycle
        if billing_cycle == BillingCycle.MONTHLY:
            base_price = pricing.monthly_price
            next_billing = now + timedelta(days=30)
        elif billing_cycle == BillingCycle.QUARTERLY:
            base_price = pricing.quarterly_price
            next_billing = now + timedelta(days=90)
        else:  # ANNUAL
            base_price = pricing.annual_price
            next_billing = now + timedelta(days=365)
        
        subscription = Subscription(
            subscription_id=subscription_id,
            customer_id=customer_id,
            company_name=company_name,
            tier=tier,
            billing_cycle=billing_cycle,
            status=SubscriptionStatus.TRIAL if trial_days > 0 else SubscriptionStatus.ACTIVE,
            start_date=now,
            current_period_start=now,
            current_period_end=next_billing,
            trial_end_date=trial_end,
            cancelled_at=None,
            base_price=base_price,
            current_price=base_price,
            currency="USD",
            properties_included=pricing.max_properties,
            units_included=pricing.max_units,
            users_included=pricing.max_users,
            storage_gb_included=pricing.max_documents_gb,
            api_calls_included=pricing.max_api_calls_per_month,
            properties_used=0,
            units_used=0,
            users_used=0,
            storage_gb_used=0.0,
            api_calls_used=0,
            auto_renew=True,
            payment_method_id=None,
            last_payment_date=None,
            next_billing_date=next_billing,
            created_at=now,
            updated_at=now,
            notes=""
        )
        
        self.subscriptions[subscription_id] = subscription
        return subscription
    
    def record_usage(self, subscription_id: str, property_count: int = 0, unit_count: int = 0,
                    user_count: int = 0, storage_gb: float = 0.0, api_calls: int = 0,
                    ai_analytics_calls: int = 0, predictive_maintenance_runs: int = 0,
                    iot_data_points: int = 0, reports_generated: int = 0) -> UsageRecord:
        """Record usage for a subscription"""
        
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        record_id = str(uuid.uuid4())
        now = datetime.now()
        
        usage_record = UsageRecord(
            record_id=record_id,
            subscription_id=subscription_id,
            customer_id=subscription.customer_id,
            property_count=property_count,
            unit_count=unit_count,
            user_count=user_count,
            storage_gb_used=storage_gb,
            api_calls_made=api_calls,
            ai_analytics_calls=ai_analytics_calls,
            predictive_maintenance_runs=predictive_maintenance_runs,
            iot_data_points=iot_data_points,
            reports_generated=reports_generated,
            usage_date=now,
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end,
            created_at=now
        )
        
        # Update subscription usage
        subscription.properties_used = max(subscription.properties_used, property_count)
        subscription.units_used = max(subscription.units_used, unit_count)
        subscription.users_used = max(subscription.users_used, user_count)
        subscription.storage_gb_used = max(subscription.storage_gb_used, storage_gb)
        subscription.api_calls_used += api_calls
        subscription.updated_at = now
        
        # Store usage record
        if subscription_id not in self.usage_records:
            self.usage_records[subscription_id] = []
        self.usage_records[subscription_id].append(usage_record)
        
        return usage_record
    
    def calculate_overage_charges(self, subscription_id: str) -> Dict[str, float]:
        """Calculate overage charges for a subscription"""
        
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        pricing = self.pricing_tiers[subscription.tier]
        overages = {}
        
        # Property overages
        if subscription.properties_used > subscription.properties_included:
            overage_count = subscription.properties_used - subscription.properties_included
            overages['properties'] = overage_count * pricing.overage_property_price
        
        # Unit overages
        if subscription.units_used > subscription.units_included:
            overage_count = subscription.units_used - subscription.units_included
            overages['units'] = overage_count * pricing.overage_unit_price
        
        # User overages
        if subscription.users_used > subscription.users_included:
            overage_count = subscription.users_used - subscription.users_included
            overages['users'] = overage_count * pricing.overage_user_price
        
        # Storage overages
        if subscription.storage_gb_used > subscription.storage_gb_included:
            overage_amount = subscription.storage_gb_used - subscription.storage_gb_included
            overages['storage'] = overage_amount * pricing.overage_storage_gb_price
        
        # API call overages
        if subscription.api_calls_used > subscription.api_calls_included:
            overage_count = subscription.api_calls_used - subscription.api_calls_included
            overages['api_calls'] = overage_count * pricing.overage_api_call_price
        
        return overages
    
    def generate_invoice(self, subscription_id: str, tax_rate: float = 0.0,
                        discount_amount: float = 0.0, one_time_charges: Dict[str, float] = None) -> Invoice:
        """Generate an invoice for a subscription"""
        
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        invoice_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Generate invoice number
        invoice_number = f"INV-{now.strftime('%Y%m')}-{len(self.invoices) + 1:04d}"
        
        # Calculate charges
        base_amount = subscription.base_price
        overage_charges = self.calculate_overage_charges(subscription_id)
        overage_total = sum(overage_charges.values())
        
        one_time_charges = one_time_charges or {}
        one_time_total = sum(one_time_charges.values())
        
        subtotal = base_amount + overage_total + one_time_total - discount_amount
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        # Due date (typically 30 days)
        due_date = now + timedelta(days=30)
        
        invoice = Invoice(
            invoice_id=invoice_id,
            subscription_id=subscription_id,
            customer_id=subscription.customer_id,
            company_name=subscription.company_name,
            invoice_number=invoice_number,
            issue_date=now,
            due_date=due_date,
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency=subscription.currency,
            base_subscription_amount=base_amount,
            overage_charges=overage_charges,
            one_time_charges=one_time_charges,
            credits_applied=0.0,
            status=PaymentStatus.PENDING,
            paid_date=None,
            payment_method=None,
            created_at=now,
            updated_at=now,
            notes=""
        )
        
        self.invoices[invoice_id] = invoice
        return invoice
    
    def process_payment(self, invoice_id: str, payment_method: str, amount_paid: float = None) -> bool:
        """Process payment for an invoice"""
        
        if invoice_id not in self.invoices:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        invoice = self.invoices[invoice_id]
        amount_paid = amount_paid or invoice.total_amount
        
        now = datetime.now()
        
        if amount_paid >= invoice.total_amount:
            invoice.status = PaymentStatus.PAID
            invoice.paid_date = now
            invoice.payment_method = payment_method
            
            # Update subscription
            subscription = self.subscriptions[invoice.subscription_id]
            subscription.last_payment_date = now
            subscription.status = SubscriptionStatus.ACTIVE
            
            # Reset usage counters for new billing period
            self._reset_usage_counters(subscription)
            
            return True
        elif amount_paid > 0:
            invoice.status = PaymentStatus.PARTIAL
            # Handle partial payments (could create credit memo)
            return False
        else:
            invoice.status = PaymentStatus.FAILED
            # Handle failed payment (suspend account, send notifications)
            subscription = self.subscriptions[invoice.subscription_id]
            subscription.status = SubscriptionStatus.PAST_DUE
            return False
    
    def _reset_usage_counters(self, subscription: Subscription):
        """Reset usage counters for new billing period"""
        subscription.api_calls_used = 0
        # Note: Properties, units, users, and storage are cumulative and don't reset
        
        # Update billing period
        if subscription.billing_cycle == BillingCycle.MONTHLY:
            subscription.current_period_start = subscription.current_period_end
            subscription.current_period_end = subscription.current_period_start + timedelta(days=30)
            subscription.next_billing_date = subscription.current_period_end
        elif subscription.billing_cycle == BillingCycle.QUARTERLY:
            subscription.current_period_start = subscription.current_period_end
            subscription.current_period_end = subscription.current_period_start + timedelta(days=90)
            subscription.next_billing_date = subscription.current_period_end
        else:  # ANNUAL
            subscription.current_period_start = subscription.current_period_end
            subscription.current_period_end = subscription.current_period_start + timedelta(days=365)
            subscription.next_billing_date = subscription.current_period_end
    
    def upgrade_subscription(self, subscription_id: str, new_tier: SubscriptionTier) -> Subscription:
        """Upgrade subscription to a higher tier"""
        
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        old_tier = subscription.tier
        
        if new_tier.value <= old_tier.value:
            raise ValueError("Can only upgrade to a higher tier")
        
        new_pricing = self.pricing_tiers[new_tier]
        
        # Calculate prorated amount for upgrade
        days_remaining = (subscription.current_period_end - datetime.now()).days
        total_days = (subscription.current_period_end - subscription.current_period_start).days
        proration_factor = days_remaining / total_days
        
        # Update subscription
        subscription.tier = new_tier
        subscription.properties_included = new_pricing.max_properties
        subscription.units_included = new_pricing.max_units
        subscription.users_included = new_pricing.max_users
        subscription.storage_gb_included = new_pricing.max_documents_gb
        subscription.api_calls_included = new_pricing.max_api_calls_per_month
        
        # Update pricing
        if subscription.billing_cycle == BillingCycle.MONTHLY:
            subscription.base_price = new_pricing.monthly_price
        elif subscription.billing_cycle == BillingCycle.QUARTERLY:
            subscription.base_price = new_pricing.quarterly_price
        else:
            subscription.base_price = new_pricing.annual_price
        
        subscription.current_price = subscription.base_price
        subscription.updated_at = datetime.now()
        
        return subscription
    
    def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> Subscription:
        """Cancel a subscription"""
        
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        now = datetime.now()
        
        if immediate:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.current_period_end = now
        else:
            # Cancel at end of billing period
            subscription.auto_renew = False
            subscription.status = SubscriptionStatus.ACTIVE  # Still active until period ends
        
        subscription.cancelled_at = now
        subscription.updated_at = now
        
        return subscription
    
    def calculate_unit_based_charges(self, subscription_id: str, units_used: int) -> float:
        """Calculate charges based on units used"""
        
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        pricing = self.pricing_tiers[subscription.tier]
        
        # Calculate unit-based charges
        unit_charge = units_used * pricing.overage_unit_price
        
        return round(unit_charge, 2)
    
    def generate_invoice(self, subscription_id: str, units_used: int = 0, 
                        tax_rate: float = 0.0, discount_amount: float = 0.0,
                        one_time_charges: Dict[str, float] = None) -> 'Invoice':
        """Generate an invoice for a subscription based on units used"""
        
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription = self.subscriptions[subscription_id]
        
        # Calculate unit-based charges
        unit_charges = self.calculate_unit_based_charges(subscription_id, units_used)
        
        # Calculate one-time charges
        one_time_total = sum((one_time_charges or {}).values())
        
        # Calculate subtotal
        subtotal = unit_charges + one_time_total
        
        # Apply discount
        discounted_amount = subtotal - discount_amount
        
        # Calculate tax
        tax_amount = discounted_amount * (tax_rate / 100)
        
        # Total amount
        total_amount = discounted_amount + tax_amount
        
        now = datetime.now()
        invoice_id = str(uuid.uuid4())
        invoice_number = f"INV-{now.strftime('%Y%m')}-{len(self.invoices) + 1:04d}"
        
        invoice = Invoice(
            invoice_id=invoice_id,
            subscription_id=subscription_id,
            customer_id=subscription.customer_id,
            company_name=subscription.company_name,
            invoice_number=invoice_number,
            status=InvoiceStatus.PENDING,
            issue_date=now,
            due_date=now + timedelta(days=30),
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end,
            subtotal_amount=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency=subscription.currency,
            units_billed=units_used,
            unit_price=self.pricing_tiers[subscription.tier].overage_unit_price,
            one_time_charges=one_time_charges or {},
            paid_date=None,
            payment_method_id=subscription.payment_method_id,
            notes=f"Units used: {units_used} @ ${self.pricing_tiers[subscription.tier].overage_unit_price:.2f} per unit",
            created_at=now,
            updated_at=now
        )
        
        self.invoices[invoice_id] = invoice
        return invoice
    
    def get_subscription_analytics(self, customer_id: str = None) -> Dict[str, Any]:
        """Get subscription analytics"""
        
        subscriptions = list(self.subscriptions.values())
        if customer_id:
            subscriptions = [s for s in subscriptions if s.customer_id == customer_id]
        
        # Calculate metrics
        total_subscriptions = len(subscriptions)
        active_subscriptions = len([s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE])
        trial_subscriptions = len([s for s in subscriptions if s.status == SubscriptionStatus.TRIAL])
        
        # Revenue metrics - Now based on average units used
        # For unit-based pricing, we'll estimate based on average units per customer
        average_units_per_customer = 50  # This could be calculated from actual usage data
        unit_price = 2.50
        mrr = active_subscriptions * average_units_per_customer * unit_price
        arr = mrr * 12
        
        # Tier distribution
        tier_distribution = {}
        for tier in SubscriptionTier:
            count = len([s for s in subscriptions if s.tier == tier])
            tier_distribution[tier.value] = count
        
        return {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'trial_subscriptions': trial_subscriptions,
            'monthly_recurring_revenue': round(mrr, 2),
            'annual_recurring_revenue': round(arr, 2),
            'tier_distribution': tier_distribution,
            'churn_rate': 0.0,  # Would calculate based on cancellations
            'average_revenue_per_user': round(mrr / max(active_subscriptions, 1), 2)
        }

def serialize_subscription(subscription: Subscription) -> Dict:
    """Convert Subscription to JSON-serializable dict"""
    result = asdict(subscription)
    result['tier'] = subscription.tier.value
    result['billing_cycle'] = subscription.billing_cycle.value
    result['status'] = subscription.status.value
    result['start_date'] = subscription.start_date.isoformat()
    result['current_period_start'] = subscription.current_period_start.isoformat()
    result['current_period_end'] = subscription.current_period_end.isoformat()
    result['trial_end_date'] = subscription.trial_end_date.isoformat() if subscription.trial_end_date else None
    result['cancelled_at'] = subscription.cancelled_at.isoformat() if subscription.cancelled_at else None
    result['last_payment_date'] = subscription.last_payment_date.isoformat() if subscription.last_payment_date else None
    result['next_billing_date'] = subscription.next_billing_date.isoformat()
    result['created_at'] = subscription.created_at.isoformat()
    result['updated_at'] = subscription.updated_at.isoformat()
    return result

def serialize_invoice(invoice: Invoice) -> Dict:
    """Convert Invoice to JSON-serializable dict"""
    result = asdict(invoice)
    result['status'] = invoice.status.value
    result['issue_date'] = invoice.issue_date.isoformat()
    result['due_date'] = invoice.due_date.isoformat()
    result['billing_period_start'] = invoice.billing_period_start.isoformat()
    result['billing_period_end'] = invoice.billing_period_end.isoformat()
    result['paid_date'] = invoice.paid_date.isoformat() if invoice.paid_date else None
    result['created_at'] = invoice.created_at.isoformat()
    result['updated_at'] = invoice.updated_at.isoformat()
    return result

def serialize_usage_record(record: UsageRecord) -> Dict:
    """Convert UsageRecord to JSON-serializable dict"""
    result = asdict(record)
    result['usage_date'] = record.usage_date.isoformat()
    result['billing_period_start'] = record.billing_period_start.isoformat()
    result['billing_period_end'] = record.billing_period_end.isoformat()
    result['created_at'] = record.created_at.isoformat()
    return result