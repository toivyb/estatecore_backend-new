from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import uuid

# Import billing system components
import os
import sys
sys.path.append(os.path.dirname(__file__))

from subscription_manager import (
    SubscriptionManager, SubscriptionTier, BillingCycle, SubscriptionStatus,
    serialize_subscription, serialize_invoice, serialize_usage_record
)
from usage_tracker import (
    UsageTracker, serialize_usage_event, serialize_usage_aggregation
)
from invoice_generator import (
    InvoiceGenerator, InvoiceTemplate
)
from payment_processor import (
    PaymentProcessor, PaymentMethod, PaymentProvider, PaymentStatus,
    serialize_payment_method, serialize_payment_transaction, serialize_payment_schedule
)

class BillingAPI:
    """
    Comprehensive billing API for EstateCore SaaS platform
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.subscription_manager = SubscriptionManager()
        self.usage_tracker = UsageTracker()
        self.invoice_generator = InvoiceGenerator()
        self.payment_processor = PaymentProcessor()
        
        # Setup webhooks and automation
        self._setup_usage_hooks()
        self._register_routes()
    
    def _setup_usage_hooks(self):
        """Setup usage tracking hooks for billing automation"""
        
        def on_usage_tracked(usage_event):
            # Auto-bill when usage exceeds limits
            customer_id = usage_event.customer_id
            subscription_id = usage_event.subscription_id
            
            # Get current usage
            current_usage = self.usage_tracker.get_current_usage(
                customer_id, subscription_id, usage_event.metric_name
            )
            
            # Check if exceeds limits (would trigger notifications in real system)
            if current_usage > 1000:  # Example threshold
                print(f"High usage alert for {customer_id}: {usage_event.metric_name} = {current_usage}")
        
        def on_rate_limit_exceeded(data):
            # Handle rate limiting
            print(f"Rate limit exceeded for {data['customer_id']}: {data['metric_name']}")
        
        self.usage_tracker.add_hook('usage_tracked', on_usage_tracked)
        self.usage_tracker.add_hook('rate_limit_exceeded', on_rate_limit_exceeded)
    
    def _register_routes(self):
        """Register all billing API routes"""
        
        # Subscription Management Routes
        self.app.add_url_rule('/api/billing/subscriptions', 'create_subscription', 
                             self.create_subscription, methods=['POST'])
        self.app.add_url_rule('/api/billing/subscriptions/<subscription_id>', 'get_subscription',
                             self.get_subscription, methods=['GET'])
        self.app.add_url_rule('/api/billing/subscriptions/<subscription_id>', 'update_subscription',
                             self.update_subscription, methods=['PUT'])
        self.app.add_url_rule('/api/billing/subscriptions/<subscription_id>/cancel', 'cancel_subscription',
                             self.cancel_subscription, methods=['POST'])
        self.app.add_url_rule('/api/billing/subscriptions/<subscription_id>/upgrade', 'upgrade_subscription',
                             self.upgrade_subscription, methods=['POST'])
        
        # Usage Tracking Routes
        self.app.add_url_rule('/api/billing/usage/track', 'track_usage',
                             self.track_usage, methods=['POST'])
        self.app.add_url_rule('/api/billing/usage/<customer_id>/<subscription_id>', 'get_usage_summary',
                             self.get_usage_summary, methods=['GET'])
        self.app.add_url_rule('/api/billing/usage/<customer_id>/<subscription_id>/export', 'export_usage',
                             self.export_usage, methods=['GET'])
        
        # Invoice Management Routes
        self.app.add_url_rule('/api/billing/invoices/generate', 'generate_invoice',
                             self.generate_invoice, methods=['POST'])
        self.app.add_url_rule('/api/billing/invoices/<invoice_id>', 'get_invoice',
                             self.get_invoice, methods=['GET'])
        self.app.add_url_rule('/api/billing/invoices/<invoice_id>/html', 'get_invoice_html',
                             self.get_invoice_html, methods=['GET'])
        self.app.add_url_rule('/api/billing/invoices/<invoice_id>/preview', 'get_invoice_preview',
                             self.get_invoice_preview, methods=['GET'])
        
        # Payment Processing Routes
        self.app.add_url_rule('/api/billing/payment-methods', 'add_payment_method',
                             self.add_payment_method, methods=['POST'])
        self.app.add_url_rule('/api/billing/payment-methods/<customer_id>', 'get_payment_methods',
                             self.get_payment_methods, methods=['GET'])
        self.app.add_url_rule('/api/billing/payments/process', 'process_payment',
                             self.process_payment, methods=['POST'])
        self.app.add_url_rule('/api/billing/payments/<transaction_id>/refund', 'process_refund',
                             self.process_refund, methods=['POST'])
        self.app.add_url_rule('/api/billing/payments/schedule', 'create_payment_schedule',
                             self.create_payment_schedule, methods=['POST'])
        
        # Webhook Routes
        self.app.add_url_rule('/api/billing/webhooks/stripe', 'billing_stripe_webhook',
                             self.stripe_webhook, methods=['POST'])
        self.app.add_url_rule('/api/billing/webhooks/paypal', 'billing_paypal_webhook',
                             self.paypal_webhook, methods=['POST'])
        
        # Analytics and Reporting Routes
        self.app.add_url_rule('/api/billing/analytics/subscriptions', 'subscription_analytics',
                             self.subscription_analytics, methods=['GET'])
        self.app.add_url_rule('/api/billing/analytics/payments', 'payment_analytics',
                             self.payment_analytics, methods=['GET'])
        self.app.add_url_rule('/api/billing/analytics/revenue', 'revenue_analytics',
                             self.revenue_analytics, methods=['GET'])
        
        # Admin Routes
        self.app.add_url_rule('/api/billing/admin/pricing-tiers', 'get_pricing_tiers',
                             self.get_pricing_tiers, methods=['GET'])
        self.app.add_url_rule('/api/billing/admin/process-scheduled-payments', 'process_scheduled_payments',
                             self.process_scheduled_payments, methods=['POST'])
        
        # Unit-based billing routes
        self.app.add_url_rule('/api/billing/calculate-unit-charges', 'calculate_unit_charges',
                             self.calculate_unit_charges, methods=['POST'])
    
    # Subscription Management Endpoints
    
    def create_subscription(self):
        """Create a new subscription"""
        try:
            data = request.get_json()
            
            customer_id = data.get('customer_id')
            company_name = data.get('company_name')
            tier = SubscriptionTier(data.get('tier', 'professional'))
            billing_cycle = BillingCycle(data.get('billing_cycle', 'monthly'))
            trial_days = data.get('trial_days', 14)
            
            subscription = self.subscription_manager.create_subscription(
                customer_id=customer_id,
                company_name=company_name,
                tier=tier,
                billing_cycle=billing_cycle,
                trial_days=trial_days
            )
            
            return jsonify({
                'success': True,
                'data': serialize_subscription(subscription)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_subscription(self, subscription_id):
        """Get subscription details"""
        try:
            subscription = self.subscription_manager.subscriptions.get(subscription_id)
            if not subscription:
                return jsonify({'success': False, 'error': 'Subscription not found'}), 404
            
            return jsonify({
                'success': True,
                'data': serialize_subscription(subscription)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def update_subscription(self, subscription_id):
        """Update subscription details"""
        try:
            data = request.get_json()
            subscription = self.subscription_manager.subscriptions.get(subscription_id)
            
            if not subscription:
                return jsonify({'success': False, 'error': 'Subscription not found'}), 404
            
            # Update allowed fields
            if 'auto_renew' in data:
                subscription.auto_renew = data['auto_renew']
            if 'payment_method_id' in data:
                subscription.payment_method_id = data['payment_method_id']
            if 'notes' in data:
                subscription.notes = data['notes']
            
            subscription.updated_at = datetime.now()
            
            return jsonify({
                'success': True,
                'data': serialize_subscription(subscription)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def cancel_subscription(self, subscription_id):
        """Cancel a subscription"""
        try:
            data = request.get_json()
            immediate = data.get('immediate', False)
            
            subscription = self.subscription_manager.cancel_subscription(
                subscription_id=subscription_id,
                immediate=immediate
            )
            
            return jsonify({
                'success': True,
                'data': serialize_subscription(subscription)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def upgrade_subscription(self, subscription_id):
        """Upgrade subscription to higher tier"""
        try:
            data = request.get_json()
            new_tier = SubscriptionTier(data.get('new_tier'))
            
            subscription = self.subscription_manager.upgrade_subscription(
                subscription_id=subscription_id,
                new_tier=new_tier
            )
            
            return jsonify({
                'success': True,
                'data': serialize_subscription(subscription)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # Usage Tracking Endpoints
    
    def track_usage(self):
        """Track usage for a customer"""
        try:
            data = request.get_json()
            
            customer_id = data.get('customer_id')
            subscription_id = data.get('subscription_id')
            metric_name = data.get('metric_name')
            value = data.get('value')
            metadata = data.get('metadata', {})
            
            usage_event = self.usage_tracker.track_usage(
                customer_id=customer_id,
                subscription_id=subscription_id,
                metric_name=metric_name,
                value=value,
                metadata=metadata
            )
            
            return jsonify({
                'success': True,
                'data': serialize_usage_event(usage_event)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_usage_summary(self, customer_id, subscription_id):
        """Get usage summary for a customer/subscription"""
        try:
            # Parse query parameters
            period_start = request.args.get('period_start')
            period_end = request.args.get('period_end')
            
            if period_start:
                period_start = datetime.fromisoformat(period_start)
            
            if period_end:
                period_end = datetime.fromisoformat(period_end)
            
            summary = self.usage_tracker.get_usage_summary(
                customer_id=customer_id,
                subscription_id=subscription_id,
                period_start=period_start,
                period_end=period_end
            )
            
            return jsonify({
                'success': True,
                'data': summary
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def export_usage(self, customer_id, subscription_id):
        """Export usage data"""
        try:
            period_start = datetime.fromisoformat(request.args.get('period_start'))
            period_end = datetime.fromisoformat(request.args.get('period_end'))
            
            export_data = self.usage_tracker.export_usage_data(
                customer_id=customer_id,
                subscription_id=subscription_id,
                period_start=period_start,
                period_end=period_end
            )
            
            return jsonify({
                'success': True,
                'data': export_data
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # Invoice Management Endpoints
    
    def generate_invoice(self):
        """Generate an invoice"""
        try:
            data = request.get_json()
            
            subscription_id = data.get('subscription_id')
            customer_info = data.get('customer_info', {})
            template = InvoiceTemplate(data.get('template', 'standard'))
            tax_rate = data.get('tax_rate', 0.0)
            discount_amount = data.get('discount_amount', 0.0)
            one_time_charges = data.get('one_time_charges', {})
            units_used = data.get('units_used', 0)  # Number of units to bill for
            
            # Get subscription
            subscription = self.subscription_manager.subscriptions.get(subscription_id)
            if not subscription:
                return jsonify({'success': False, 'error': 'Subscription not found'}), 404
            
            # Generate unit-based invoice using new method
            invoice = self.subscription_manager.generate_invoice(
                subscription_id=subscription_id,
                units_used=units_used,
                tax_rate=tax_rate,
                discount_amount=discount_amount,
                one_time_charges=one_time_charges
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'invoice': serialize_invoice(invoice),
                    'units_billed': units_used,
                    'unit_price': 2.50,
                    'total_amount': invoice.total_amount
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_invoice(self, invoice_id):
        """Get invoice details"""
        try:
            invoice = self.subscription_manager.invoices.get(invoice_id)
            if not invoice:
                return jsonify({'success': False, 'error': 'Invoice not found'}), 404
            
            return jsonify({
                'success': True,
                'data': serialize_invoice(invoice)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_invoice_html(self, invoice_id):
        """Get invoice as HTML"""
        try:
            invoice = self.subscription_manager.invoices.get(invoice_id)
            if not invoice:
                return jsonify({'success': False, 'error': 'Invoice not found'}), 404
            
            # Generate HTML (would need to reconstruct invoice data)
            # For now, return a simple response
            return jsonify({
                'success': True,
                'data': {
                    'html': f"<html><body><h1>Invoice {invoice.invoice_number}</h1></body></html>"
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_invoice_preview(self, invoice_id):
        """Get invoice preview"""
        try:
            invoice = self.subscription_manager.invoices.get(invoice_id)
            if not invoice:
                return jsonify({'success': False, 'error': 'Invoice not found'}), 404
            
            # Generate preview data
            preview = self.invoice_generator.get_invoice_preview({
                'invoice_number': invoice.invoice_number,
                'customer': {'company_name': invoice.company_name},
                'due_date': invoice.due_date.isoformat(),
                'amounts': {'total_amount': invoice.total_amount, 'currency': invoice.currency},
                'line_items': [],  # Would need to reconstruct
                'taxes': []  # Would need to reconstruct
            })
            
            return jsonify({
                'success': True,
                'data': preview
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # Payment Processing Endpoints
    
    def add_payment_method(self):
        """Add a payment method"""
        try:
            data = request.get_json()
            
            customer_id = data.get('customer_id')
            payment_type = PaymentMethod(data.get('payment_type'))
            provider = PaymentProvider(data.get('provider'))
            provider_data = data.get('provider_data', {})
            
            payment_method = self.payment_processor.add_payment_method(
                customer_id=customer_id,
                payment_type=payment_type,
                provider=provider,
                provider_data=provider_data
            )
            
            return jsonify({
                'success': True,
                'data': serialize_payment_method(payment_method)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def get_payment_methods(self, customer_id):
        """Get payment methods for a customer"""
        try:
            methods = self.payment_processor.payment_methods.get(customer_id, [])
            
            return jsonify({
                'success': True,
                'data': [serialize_payment_method(method) for method in methods]
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def process_payment(self):
        """Process a payment"""
        try:
            data = request.get_json()
            
            customer_id = data.get('customer_id')
            subscription_id = data.get('subscription_id')
            invoice_id = data.get('invoice_id')
            amount = data.get('amount')
            currency = data.get('currency', 'USD')
            payment_method_id = data.get('payment_method_id')
            metadata = data.get('metadata', {})
            
            transaction = self.payment_processor.process_payment(
                customer_id=customer_id,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                amount=amount,
                currency=currency,
                payment_method_id=payment_method_id,
                metadata=metadata
            )
            
            return jsonify({
                'success': True,
                'data': serialize_payment_transaction(transaction)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def process_refund(self, transaction_id):
        """Process a refund"""
        try:
            data = request.get_json()
            
            amount = data.get('amount')
            reason = data.get('reason', 'Customer request')
            metadata = data.get('metadata', {})
            
            refund = self.payment_processor.process_refund(
                original_transaction_id=transaction_id,
                amount=amount,
                reason=reason,
                metadata=metadata
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'refund_id': refund.refund_id,
                    'amount': refund.amount,
                    'status': refund.status.value,
                    'provider_refund_id': refund.provider_refund_id
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def create_payment_schedule(self):
        """Create a recurring payment schedule"""
        try:
            data = request.get_json()
            
            customer_id = data.get('customer_id')
            subscription_id = data.get('subscription_id')
            payment_method_id = data.get('payment_method_id')
            amount = data.get('amount')
            currency = data.get('currency', 'USD')
            frequency = data.get('frequency', 'monthly')
            start_date = data.get('start_date')
            
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            
            schedule = self.payment_processor.create_payment_schedule(
                customer_id=customer_id,
                subscription_id=subscription_id,
                payment_method_id=payment_method_id,
                amount=amount,
                currency=currency,
                frequency=frequency,
                start_date=start_date
            )
            
            return jsonify({
                'success': True,
                'data': serialize_payment_schedule(schedule)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # Webhook Endpoints
    
    def stripe_webhook(self):
        """Handle Stripe webhook"""
        try:
            payload = request.get_json()
            signature = request.headers.get('Stripe-Signature')
            
            result = self.payment_processor.handle_webhook(
                provider=PaymentProvider.STRIPE,
                payload=payload,
                signature=signature
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    def paypal_webhook(self):
        """Handle PayPal webhook"""
        try:
            payload = request.get_json()
            signature = request.headers.get('PayPal-Transmission-Sig')
            
            result = self.payment_processor.handle_webhook(
                provider=PaymentProvider.PAYPAL,
                payload=payload,
                signature=signature
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # Analytics and Reporting Endpoints
    
    def subscription_analytics(self):
        """Get subscription analytics"""
        try:
            customer_id = request.args.get('customer_id')
            
            analytics = self.subscription_manager.get_subscription_analytics(customer_id)
            
            return jsonify({
                'success': True,
                'data': analytics
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def payment_analytics(self):
        """Get payment analytics"""
        try:
            customer_id = request.args.get('customer_id')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            if end_date:
                end_date = datetime.fromisoformat(end_date)
            
            analytics = self.payment_processor.get_payment_analytics(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return jsonify({
                'success': True,
                'data': analytics
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def revenue_analytics(self):
        """Get revenue analytics"""
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            if end_date:
                end_date = datetime.fromisoformat(end_date)
            
            # Calculate revenue metrics
            subscriptions = list(self.subscription_manager.subscriptions.values())
            transactions = list(self.payment_processor.transactions.values())
            
            if start_date:
                transactions = [t for t in transactions if t.attempted_at >= start_date]
            if end_date:
                transactions = [t for t in transactions if t.attempted_at <= end_date]
            
            # Revenue calculations
            total_revenue = sum(t.amount for t in transactions if t.status == PaymentStatus.COMPLETED)
            transaction_count = len([t for t in transactions if t.status == PaymentStatus.COMPLETED])
            
            # Subscription metrics
            active_subscriptions = len([s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE])
            mrr = sum(s.base_price for s in subscriptions if s.billing_cycle == BillingCycle.MONTHLY and s.status == SubscriptionStatus.ACTIVE)
            
            return jsonify({
                'success': True,
                'data': {
                    'total_revenue': round(total_revenue, 2),
                    'transaction_count': transaction_count,
                    'active_subscriptions': active_subscriptions,
                    'monthly_recurring_revenue': round(mrr, 2),
                    'annual_run_rate': round(mrr * 12, 2),
                    'average_transaction_size': round(total_revenue / max(transaction_count, 1), 2)
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # Admin Endpoints
    
    def get_pricing_tiers(self):
        """Get available pricing tiers"""
        try:
            tiers = {}
            for tier, pricing in self.subscription_manager.pricing_tiers.items():
                tiers[tier.value] = {
                    'name': pricing.name,
                    'description': pricing.description,
                    'monthly_price': pricing.monthly_price,
                    'quarterly_price': pricing.quarterly_price,
                    'annual_price': pricing.annual_price,
                    'max_properties': pricing.max_properties,
                    'max_units': pricing.max_units,
                    'max_users': pricing.max_users,
                    'max_documents_gb': pricing.max_documents_gb,
                    'max_api_calls_per_month': pricing.max_api_calls_per_month,
                    'features': {
                        'ai_analytics': pricing.ai_analytics,
                        'predictive_maintenance': pricing.predictive_maintenance,
                        'iot_integration': pricing.iot_integration,
                        'advanced_reporting': pricing.advanced_reporting,
                        'white_labeling': pricing.white_labeling,
                        'priority_support': pricing.priority_support,
                        'custom_integrations': pricing.custom_integrations
                    }
                }
            
            return jsonify({
                'success': True,
                'data': tiers
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def process_scheduled_payments(self):
        """Process all scheduled payments"""
        try:
            transactions = self.payment_processor.process_scheduled_payments()
            
            return jsonify({
                'success': True,
                'data': {
                    'processed_count': len(transactions),
                    'transactions': [serialize_payment_transaction(t) for t in transactions]
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    def calculate_unit_charges(self):
        """Calculate charges for a given number of units"""
        try:
            data = request.get_json()
            
            subscription_id = data.get('subscription_id')
            units_used = data.get('units_used', 0)
            
            if not subscription_id:
                return jsonify({'success': False, 'error': 'Subscription ID is required'}), 400
            
            # Calculate unit-based charges
            total_charge = self.subscription_manager.calculate_unit_based_charges(
                subscription_id=subscription_id,
                units_used=units_used
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'units_used': units_used,
                    'unit_price': 2.50,
                    'total_charge': total_charge,
                    'billing_model': 'unit_based'
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

# Integration with main EstateCore app
def init_billing_system(app: Flask):
    """Initialize billing system with Flask app"""
    billing_api = BillingAPI(app)
    return billing_api