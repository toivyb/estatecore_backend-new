from flask import Blueprint, request, jsonify
from estatecore_backend.models import db, Payment, TenantBalance, PaymentReceipt, PaymentNotificationLog, User, Tenant, Property
import stripe
import os
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

payments_bp = Blueprint('payments', __name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Payment type configurations
PAYMENT_TYPES = {
    'rent': {'name': 'Rent Payment', 'description': 'Monthly rent payment'},
    'late_fee': {'name': 'Late Fee', 'description': 'Late payment fee'},
    'deposit': {'name': 'Security Deposit', 'description': 'Security deposit payment'},
    'utilities': {'name': 'Utilities', 'description': 'Utility bill payment'},
    'maintenance': {'name': 'Maintenance Fee', 'description': 'Maintenance service fee'},
    'other': {'name': 'Other Fee', 'description': 'Miscellaneous payment'}
}

def generate_receipt_number():
    """Generate unique receipt number"""
    timestamp = datetime.now().strftime('%Y%m%d')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"RCP-{timestamp}-{unique_id}"

def calculate_processing_fee(amount, payment_method='credit_card'):
    """Calculate Stripe processing fees"""
    if payment_method == 'credit_card':
        return round((amount * 0.029) + 0.30, 2)  # 2.9% + $0.30
    elif payment_method == 'ach':
        return min(round(amount * 0.008, 2), 5.00)  # 0.8% capped at $5
    else:
        return 0.0

def update_tenant_balance(tenant_id, payment_amount, payment_type):
    """Update tenant balance after successful payment"""
    balance = TenantBalance.query.filter_by(tenant_id=tenant_id).first()
    if not balance:
        balance = TenantBalance(tenant_id=tenant_id)
        db.session.add(balance)
    
    # Update balance based on payment type
    if payment_type in ['rent', 'late_fee', 'utilities', 'maintenance', 'other']:
        balance.current_balance -= payment_amount
    elif payment_type == 'deposit':
        balance.security_deposit += payment_amount
    
    balance.last_payment_date = datetime.utcnow()
    balance.last_payment_amount = payment_amount
    balance.total_paid += payment_amount
    balance.updated_at = datetime.utcnow()
    
    return balance

@payments_bp.route('', methods=['GET'])
def get_payments():
    """Get payment history with filtering and pagination"""
    try:
        # Query parameters
        tenant_id = request.args.get('tenant_id', type=int)
        property_id = request.args.get('property_id', type=int)
        status = request.args.get('status')
        payment_type = request.args.get('payment_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Payment.query
        
        if tenant_id:
            query = query.filter(Payment.tenant_id == tenant_id)
        if property_id:
            query = query.filter(Payment.property_id == property_id)
        if status:
            query = query.filter(Payment.status == status)
        if payment_type:
            query = query.filter(Payment.payment_type == payment_type)
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Payment.payment_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Payment.payment_date <= end_dt)
        
        # Get paginated results
        payments = query.order_by(Payment.payment_date.desc()).offset(offset).limit(limit).all()
        total_count = query.count()
        
        result = []
        for payment in payments:
            result.append({
                'id': payment.id,
                'amount': float(payment.amount),
                'status': payment.status,
                'payment_type': payment.payment_type,
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'due_date': payment.due_date.isoformat() if payment.due_date else None,
                'tenant_id': payment.tenant_id,
                'property_id': payment.property_id,
                'description': payment.description,
                'receipt_number': payment.receipt_number,
                'processing_fee': float(payment.processing_fee) if payment.processing_fee else 0,
                'net_amount': float(payment.net_amount) if payment.net_amount else 0,
                'tenant_name': payment.tenant.username if payment.tenant else None,
                'property_name': payment.property.name if payment.property else None
            })
        
        return jsonify({
            'payments': result,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create Stripe payment intent for tenant payment"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['tenant_id', 'property_id', 'amount', 'payment_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        tenant_id = data['tenant_id']
        property_id = data['property_id']
        amount = float(data['amount'])
        payment_type = data['payment_type']
        payment_method = data.get('payment_method', 'credit_card')
        description = data.get('description', '')
        due_date = data.get('due_date')
        
        # Validate payment type
        if payment_type not in PAYMENT_TYPES:
            return jsonify({'error': 'Invalid payment type'}), 400
        
        # Validate tenant and property exist
        tenant = User.query.get(tenant_id)
        if not tenant or tenant.role != 'tenant':
            return jsonify({'error': 'Invalid tenant'}), 400
        
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return jsonify({'error': 'Invalid property'}), 400
        
        # Calculate processing fee
        processing_fee = calculate_processing_fee(amount, payment_method)
        net_amount = amount - processing_fee
        
        # Generate receipt number
        receipt_number = generate_receipt_number()
        
        # Create payment record
        payment = Payment(
            amount=amount,
            payment_type=payment_type,
            payment_method=payment_method,
            tenant_id=tenant_id,
            property_id=property_id,
            description=description or PAYMENT_TYPES[payment_type]['description'],
            processing_fee=processing_fee,
            net_amount=net_amount,
            receipt_number=receipt_number,
            status='pending'
        )
        
        if due_date:
            payment.due_date = datetime.fromisoformat(due_date)
        
        db.session.add(payment)
        db.session.flush()  # Get the payment ID
        
        # Create Stripe payment intent
        intent_metadata = {
            'payment_id': str(payment.id),
            'tenant_id': str(tenant_id),
            'property_id': str(property_id),
            'payment_type': payment_type,
            'receipt_number': receipt_number
        }
        
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency='usd',
            payment_method_types=['card'] if payment_method == 'credit_card' else ['us_bank_account'],
            metadata=intent_metadata,
            description=f"{PAYMENT_TYPES[payment_type]['name']} - {tenant.username}",
            receipt_email=tenant.email
        )
        
        # Update payment with Stripe payment intent ID
        payment.stripe_payment_intent_id = intent.id
        payment.metadata = json.dumps(intent_metadata)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'payment_id': payment.id,
            'client_secret': intent.client_secret,
            'amount': amount,
            'processing_fee': processing_fee,
            'net_amount': net_amount,
            'receipt_number': receipt_number,
            'payment_type': payment_type,
            'description': payment.description
        }), 201
        
    except stripe.error.StripeError as e:
        db.session.rollback()
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/<int:payment_id>/confirm', methods=['POST'])
def confirm_payment(payment_id):
    """Confirm payment status and update records"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        if not payment.stripe_payment_intent_id:
            return jsonify({'error': 'No Stripe payment intent found'}), 400
        
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
        
        if intent.status == 'succeeded':
            # Update payment status
            payment.status = 'completed'
            payment.updated_at = datetime.utcnow()
            
            # Store payment method details if available
            if intent.payment_method:
                payment.stripe_payment_method_id = intent.payment_method
            
            # Update tenant balance
            update_tenant_balance(payment.tenant_id, payment.amount, payment.payment_type)
            
            # Create receipt record
            receipt = PaymentReceipt(
                payment_id=payment.id,
                receipt_number=payment.receipt_number
            )
            db.session.add(receipt)
            
            # Create notification for tenant
            from estatecore_backend.models import Notification
            notification = Notification(
                user_id=payment.tenant_id,
                title='Payment Confirmed',
                message=f'Your {payment.payment_type} payment of ${payment.amount} has been successfully processed.',
                type='payment',
                priority='normal'
            )
            db.session.add(notification)
            
            # Create notification log
            notif_log = PaymentNotificationLog(
                payment_id=payment.id,
                notification_type='payment_success',
                recipient_id=payment.tenant_id,
                notification_method='in_app',
                status='sent',
                message='Payment confirmation notification sent'
            )
            db.session.add(notif_log)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment confirmed successfully',
                'payment': {
                    'id': payment.id,
                    'status': payment.status,
                    'amount': float(payment.amount),
                    'receipt_number': payment.receipt_number,
                    'payment_date': payment.payment_date.isoformat()
                }
            }), 200
            
        elif intent.status == 'requires_payment_method':
            payment.status = 'failed'
            payment.failure_reason = 'Payment method declined'
            payment.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'error': 'Payment method was declined'}), 400
            
        elif intent.status == 'requires_action':
            return jsonify({
                'requires_action': True,
                'client_secret': intent.client_secret
            }), 200
            
        else:
            return jsonify({
                'error': 'Payment not completed',
                'status': intent.status
            }), 400
            
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/<int:payment_id>', methods=['GET'])
def get_payment_details(payment_id):
    """Get detailed payment information"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        payment_data = {
            'id': payment.id,
            'amount': float(payment.amount),
            'status': payment.status,
            'payment_type': payment.payment_type,
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'due_date': payment.due_date.isoformat() if payment.due_date else None,
            'description': payment.description,
            'receipt_number': payment.receipt_number,
            'processing_fee': float(payment.processing_fee) if payment.processing_fee else 0,
            'net_amount': float(payment.net_amount) if payment.net_amount else 0,
            'failure_reason': payment.failure_reason,
            'tenant': {
                'id': payment.tenant.id,
                'name': payment.tenant.username,
                'email': payment.tenant.email
            } if payment.tenant else None,
            'property': {
                'id': payment.property.id,
                'name': payment.property.name,
                'address': payment.property.address
            } if payment.property else None,
            'receipts': [{
                'id': receipt.id,
                'receipt_number': receipt.receipt_number,
                'email_sent': receipt.email_sent,
                'created_at': receipt.created_at.isoformat()
            } for receipt in payment.receipts],
            'created_at': payment.created_at.isoformat() if payment.created_at else None,
            'updated_at': payment.updated_at.isoformat() if payment.updated_at else None
        }
        
        return jsonify(payment_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/tenant/<int:tenant_id>/balance', methods=['GET'])
def get_tenant_balance(tenant_id):
    """Get tenant balance information"""
    try:
        # Verify tenant exists
        tenant = User.query.get_or_404(tenant_id)
        if tenant.role != 'tenant':
            return jsonify({'error': 'Invalid tenant'}), 400
        
        # Get or create balance record
        balance = TenantBalance.query.filter_by(tenant_id=tenant_id).first()
        if not balance:
            balance = TenantBalance(tenant_id=tenant_id)
            db.session.add(balance)
            db.session.commit()
        
        # Get recent payment history
        recent_payments = Payment.query.filter_by(
            tenant_id=tenant_id,
            status='completed'
        ).order_by(Payment.payment_date.desc()).limit(5).all()
        
        balance_data = {
            'tenant_id': tenant_id,
            'current_balance': float(balance.current_balance),
            'last_payment_date': balance.last_payment_date.isoformat() if balance.last_payment_date else None,
            'last_payment_amount': float(balance.last_payment_amount) if balance.last_payment_amount else 0,
            'total_paid': float(balance.total_paid),
            'total_charges': float(balance.total_charges),
            'late_fees': float(balance.late_fees),
            'security_deposit': float(balance.security_deposit),
            'recent_payments': [{
                'id': payment.id,
                'amount': float(payment.amount),
                'payment_type': payment.payment_type,
                'payment_date': payment.payment_date.isoformat(),
                'receipt_number': payment.receipt_number
            } for payment in recent_payments],
            'updated_at': balance.updated_at.isoformat() if balance.updated_at else None
        }
        
        return jsonify(balance_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/types', methods=['GET'])
def get_payment_types():
    """Get available payment types"""
    return jsonify({
        'payment_types': PAYMENT_TYPES
    }), 200

@payments_bp.route('/<int:payment_id>/receipt', methods=['GET'])
def get_payment_receipt(payment_id):
    """Get payment receipt details"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        if payment.status != 'completed':
            return jsonify({'error': 'Receipt only available for completed payments'}), 400
        
        receipt_data = {
            'payment_id': payment.id,
            'receipt_number': payment.receipt_number,
            'payment_date': payment.payment_date.isoformat(),
            'amount': float(payment.amount),
            'payment_type': payment.payment_type,
            'payment_method': payment.payment_method,
            'description': payment.description,
            'processing_fee': float(payment.processing_fee) if payment.processing_fee else 0,
            'tenant': {
                'name': payment.tenant.username,
                'email': payment.tenant.email
            },
            'property': {
                'name': payment.property.name,
                'address': payment.property.address
            }
        }
        
        return jsonify(receipt_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    try:
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment_id = payment_intent['metadata'].get('payment_id')
            
            if payment_id:
                payment = Payment.query.get(int(payment_id))
                if payment and payment.status == 'pending':
                    payment.status = 'completed'
                    payment.updated_at = datetime.utcnow()
                    
                    # Update tenant balance
                    update_tenant_balance(payment.tenant_id, payment.amount, payment.payment_type)
                    
                    # Create notifications
                    from estatecore_backend.models import Notification
                    notification = Notification(
                        user_id=payment.tenant_id,
                        title='Payment Processed',
                        message=f'Your payment of ${payment.amount} has been successfully processed.',
                        type='payment',
                        priority='normal'
                    )
                    db.session.add(notification)
                    
                    db.session.commit()
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment_id = payment_intent['metadata'].get('payment_id')
            
            if payment_id:
                payment = Payment.query.get(int(payment_id))
                if payment:
                    payment.status = 'failed'
                    payment.failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
                    payment.updated_at = datetime.utcnow()
                    
                    # Create notification for failed payment
                    from estatecore_backend.models import Notification
                    notification = Notification(
                        user_id=payment.tenant_id,
                        title='Payment Failed',
                        message=f'Your payment of ${payment.amount} could not be processed. Please try again.',
                        type='payment',
                        priority='high',
                        action_required=True
                    )
                    db.session.add(notification)
                    
                    db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500