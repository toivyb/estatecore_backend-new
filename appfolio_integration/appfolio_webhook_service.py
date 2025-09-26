"""
AppFolio Webhook Service

Handles real-time webhook notifications from AppFolio for immediate
data synchronization and event processing.
"""

import logging
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio
from flask import Flask, request, jsonify
import threading
from concurrent.futures import ThreadPoolExecutor

from .appfolio_sync_service import AppFolioSyncService

logger = logging.getLogger(__name__)

class WebhookEventType(Enum):
    """AppFolio webhook event types"""
    PROPERTY_CREATED = "property.created"
    PROPERTY_UPDATED = "property.updated"
    PROPERTY_DELETED = "property.deleted"
    
    UNIT_CREATED = "unit.created"
    UNIT_UPDATED = "unit.updated"
    UNIT_DELETED = "unit.deleted"
    
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_DELETED = "tenant.deleted"
    
    LEASE_CREATED = "lease.created"
    LEASE_UPDATED = "lease.updated"
    LEASE_EXPIRED = "lease.expired"
    LEASE_TERMINATED = "lease.terminated"
    
    PAYMENT_CREATED = "payment.created"
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    WORK_ORDER_CREATED = "work_order.created"
    WORK_ORDER_UPDATED = "work_order.updated"
    WORK_ORDER_COMPLETED = "work_order.completed"
    WORK_ORDER_CANCELLED = "work_order.cancelled"
    
    VENDOR_CREATED = "vendor.created"
    VENDOR_UPDATED = "vendor.updated"
    VENDOR_DELETED = "vendor.deleted"
    
    APPLICATION_SUBMITTED = "application.submitted"
    APPLICATION_APPROVED = "application.approved"
    APPLICATION_REJECTED = "application.rejected"
    
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    
    ACCOUNT_UPDATED = "account.updated"
    TRANSACTION_POSTED = "transaction.posted"

class WebhookStatus(Enum):
    """Webhook processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class WebhookEvent:
    """Webhook event data"""
    event_id: str
    event_type: WebhookEventType
    organization_id: str
    entity_type: str
    entity_id: str
    event_data: Dict[str, Any]
    timestamp: datetime
    status: WebhookStatus = WebhookStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class WebhookSubscription:
    """Webhook subscription configuration"""
    subscription_id: str
    organization_id: str
    event_types: List[WebhookEventType]
    endpoint_url: str
    secret_key: str
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_delivery: Optional[datetime] = None
    delivery_count: int = 0
    failure_count: int = 0

class AppFolioWebhookService:
    """
    AppFolio Webhook Service
    
    Manages webhook subscriptions, processes incoming webhook events,
    and triggers real-time synchronization based on AppFolio events.
    """
    
    def __init__(self, sync_service: AppFolioSyncService):
        self.sync_service = sync_service
        
        # Event management
        self.pending_events: Dict[str, WebhookEvent] = {}
        self.processed_events: List[WebhookEvent] = []
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        
        # Event handlers
        self.event_handlers: Dict[WebhookEventType, List[Callable]] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Flask app for webhook endpoints
        self.app = Flask(__name__)
        self._setup_webhook_routes()
        
        # Processing configuration
        self.processing_enabled = True
        self.batch_processing = True
        self.batch_size = 50
        self.batch_timeout = 30  # seconds
        
        # Setup default event handlers
        self._setup_default_handlers()
        
        logger.info("AppFolio Webhook Service initialized")
    
    def _setup_webhook_routes(self):
        """Setup Flask routes for webhook endpoints"""
        
        @self.app.route('/webhooks/appfolio/<organization_id>', methods=['POST'])
        def handle_webhook(organization_id: str):
            return self._handle_incoming_webhook(organization_id)
        
        @self.app.route('/webhooks/appfolio/health', methods=['GET'])
        def webhook_health():
            return jsonify({
                'status': 'healthy',
                'service': 'AppFolio Webhook Service',
                'timestamp': datetime.utcnow().isoformat(),
                'pending_events': len(self.pending_events),
                'processed_events': len(self.processed_events)
            })
    
    def _handle_incoming_webhook(self, organization_id: str):
        """Handle incoming webhook from AppFolio"""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(request):
                logger.warning(f"Invalid webhook signature for organization {organization_id}")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Parse webhook payload
            payload = request.get_json()
            if not payload:
                return jsonify({'error': 'Invalid payload'}), 400
            
            # Extract event information
            event_type_str = payload.get('event_type')
            entity_type = payload.get('entity_type')
            entity_id = payload.get('entity_id')
            event_data = payload.get('data', {})
            
            if not all([event_type_str, entity_type, entity_id]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Create webhook event
            try:
                event_type = WebhookEventType(event_type_str)
            except ValueError:
                logger.warning(f"Unknown event type: {event_type_str}")
                return jsonify({'error': 'Unknown event type'}), 400
            
            webhook_event = WebhookEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data=event_data,
                timestamp=datetime.utcnow()
            )
            
            # Queue event for processing
            self.pending_events[webhook_event.event_id] = webhook_event
            
            # Process event asynchronously
            if self.processing_enabled:
                self.executor.submit(self._process_webhook_event, webhook_event.event_id)
            
            logger.info(f"Received webhook event {webhook_event.event_id}: {event_type_str}")
            
            return jsonify({
                'success': True,
                'event_id': webhook_event.event_id,
                'message': 'Webhook received and queued for processing'
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def _verify_webhook_signature(self, request) -> bool:
        """Verify webhook signature from AppFolio"""
        try:
            # Get signature from headers
            signature = request.headers.get('X-AppFolio-Signature')
            if not signature:
                return False
            
            # Get organization ID from URL
            organization_id = request.view_args.get('organization_id')
            if not organization_id:
                return False
            
            # Find subscription
            subscription = self._get_organization_subscription(organization_id)
            if not subscription:
                return False
            
            # Calculate expected signature
            payload = request.get_data()
            expected_signature = hmac.new(
                subscription.secret_key.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, f"sha256={expected_signature}")
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def _process_webhook_event(self, event_id: str):
        """Process a webhook event"""
        try:
            if event_id not in self.pending_events:
                logger.error(f"Event {event_id} not found in pending events")
                return
            
            event = self.pending_events[event_id]
            event.status = WebhookStatus.PROCESSING
            
            # Execute event handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Event handler failed for {event_id}: {str(e)}")
                        event.error_message = str(e)
                        event.status = WebhookStatus.FAILED
                        event.retry_count += 1
                        
                        # Retry if under max retries
                        if event.retry_count < event.max_retries:
                            event.status = WebhookStatus.RETRYING
                            # Schedule retry (simple approach - could use more sophisticated retry logic)
                            threading.Timer(60.0 * event.retry_count, lambda: self._process_webhook_event(event_id)).start()
                        
                        return
            
            # Mark as completed
            event.status = WebhookStatus.COMPLETED
            event.processed_at = datetime.utcnow()
            
            # Move to processed events
            self.processed_events.append(event)
            del self.pending_events[event_id]
            
            # Clean up old processed events (keep last 1000)
            if len(self.processed_events) > 1000:
                self.processed_events = self.processed_events[-1000:]
            
            logger.info(f"Successfully processed webhook event {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to process webhook event {event_id}: {str(e)}")
            if event_id in self.pending_events:
                self.pending_events[event_id].status = WebhookStatus.FAILED
                self.pending_events[event_id].error_message = str(e)
    
    def _setup_default_handlers(self):
        """Setup default event handlers"""
        
        # Property handlers
        self.register_event_handler(WebhookEventType.PROPERTY_CREATED, self._handle_property_created)
        self.register_event_handler(WebhookEventType.PROPERTY_UPDATED, self._handle_property_updated)
        self.register_event_handler(WebhookEventType.PROPERTY_DELETED, self._handle_property_deleted)
        
        # Unit handlers
        self.register_event_handler(WebhookEventType.UNIT_CREATED, self._handle_unit_created)
        self.register_event_handler(WebhookEventType.UNIT_UPDATED, self._handle_unit_updated)
        self.register_event_handler(WebhookEventType.UNIT_DELETED, self._handle_unit_deleted)
        
        # Tenant handlers
        self.register_event_handler(WebhookEventType.TENANT_CREATED, self._handle_tenant_created)
        self.register_event_handler(WebhookEventType.TENANT_UPDATED, self._handle_tenant_updated)
        self.register_event_handler(WebhookEventType.TENANT_DELETED, self._handle_tenant_deleted)
        
        # Lease handlers
        self.register_event_handler(WebhookEventType.LEASE_CREATED, self._handle_lease_created)
        self.register_event_handler(WebhookEventType.LEASE_UPDATED, self._handle_lease_updated)
        self.register_event_handler(WebhookEventType.LEASE_EXPIRED, self._handle_lease_expired)
        self.register_event_handler(WebhookEventType.LEASE_TERMINATED, self._handle_lease_terminated)
        
        # Payment handlers
        self.register_event_handler(WebhookEventType.PAYMENT_CREATED, self._handle_payment_created)
        self.register_event_handler(WebhookEventType.PAYMENT_PROCESSED, self._handle_payment_processed)
        self.register_event_handler(WebhookEventType.PAYMENT_FAILED, self._handle_payment_failed)
        
        # Work order handlers
        self.register_event_handler(WebhookEventType.WORK_ORDER_CREATED, self._handle_work_order_created)
        self.register_event_handler(WebhookEventType.WORK_ORDER_UPDATED, self._handle_work_order_updated)
        self.register_event_handler(WebhookEventType.WORK_ORDER_COMPLETED, self._handle_work_order_completed)
        
        # General sync handler for all events
        for event_type in WebhookEventType:
            self.register_event_handler(event_type, self._handle_real_time_sync)
    
    def register_event_handler(self, event_type: WebhookEventType, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type.value}")
    
    def _handle_property_created(self, event: WebhookEvent):
        """Handle property created event"""
        logger.info(f"Property created: {event.entity_id}")
        # Could trigger specific property sync logic here
    
    def _handle_property_updated(self, event: WebhookEvent):
        """Handle property updated event"""
        logger.info(f"Property updated: {event.entity_id}")
        # Could trigger specific property sync logic here
    
    def _handle_property_deleted(self, event: WebhookEvent):
        """Handle property deleted event"""
        logger.info(f"Property deleted: {event.entity_id}")
        # Could trigger cleanup logic here
    
    def _handle_unit_created(self, event: WebhookEvent):
        """Handle unit created event"""
        logger.info(f"Unit created: {event.entity_id}")
    
    def _handle_unit_updated(self, event: WebhookEvent):
        """Handle unit updated event"""
        logger.info(f"Unit updated: {event.entity_id}")
    
    def _handle_unit_deleted(self, event: WebhookEvent):
        """Handle unit deleted event"""
        logger.info(f"Unit deleted: {event.entity_id}")
    
    def _handle_tenant_created(self, event: WebhookEvent):
        """Handle tenant created event"""
        logger.info(f"Tenant created: {event.entity_id}")
    
    def _handle_tenant_updated(self, event: WebhookEvent):
        """Handle tenant updated event"""
        logger.info(f"Tenant updated: {event.entity_id}")
    
    def _handle_tenant_deleted(self, event: WebhookEvent):
        """Handle tenant deleted event"""
        logger.info(f"Tenant deleted: {event.entity_id}")
    
    def _handle_lease_created(self, event: WebhookEvent):
        """Handle lease created event"""
        logger.info(f"Lease created: {event.entity_id}")
    
    def _handle_lease_updated(self, event: WebhookEvent):
        """Handle lease updated event"""
        logger.info(f"Lease updated: {event.entity_id}")
    
    def _handle_lease_expired(self, event: WebhookEvent):
        """Handle lease expired event"""
        logger.info(f"Lease expired: {event.entity_id}")
        # Could trigger lease renewal workflow
    
    def _handle_lease_terminated(self, event: WebhookEvent):
        """Handle lease terminated event"""
        logger.info(f"Lease terminated: {event.entity_id}")
        # Could trigger move-out workflow
    
    def _handle_payment_created(self, event: WebhookEvent):
        """Handle payment created event"""
        logger.info(f"Payment created: {event.entity_id}")
    
    def _handle_payment_processed(self, event: WebhookEvent):
        """Handle payment processed event"""
        logger.info(f"Payment processed: {event.entity_id}")
        # Could trigger accounting sync
    
    def _handle_payment_failed(self, event: WebhookEvent):
        """Handle payment failed event"""
        logger.info(f"Payment failed: {event.entity_id}")
        # Could trigger notification to tenant
    
    def _handle_work_order_created(self, event: WebhookEvent):
        """Handle work order created event"""
        logger.info(f"Work order created: {event.entity_id}")
    
    def _handle_work_order_updated(self, event: WebhookEvent):
        """Handle work order updated event"""
        logger.info(f"Work order updated: {event.entity_id}")
    
    def _handle_work_order_completed(self, event: WebhookEvent):
        """Handle work order completed event"""
        logger.info(f"Work order completed: {event.entity_id}")
        # Could trigger follow-up surveys or billing
    
    def _handle_real_time_sync(self, event: WebhookEvent):
        """Handle real-time synchronization for any event"""
        try:
            # Create selective sync job for the specific entity
            entity_types = [event.entity_type]
            filters = {'entity_ids': [event.entity_id]}
            
            # Create and execute sync job
            asyncio.run(self._trigger_selective_sync(
                event.organization_id,
                entity_types,
                filters
            ))
            
        except Exception as e:
            logger.error(f"Real-time sync failed for event {event.event_id}: {str(e)}")
            raise
    
    async def _trigger_selective_sync(self, organization_id: str, entity_types: List[str], 
                                    filters: Dict[str, Any]):
        """Trigger selective synchronization"""
        try:
            from .appfolio_sync_service import SyncDirection, SyncMode
            
            # Create sync job
            sync_job = await self.sync_service.create_sync_job(
                organization_id=organization_id,
                entity_types=entity_types,
                sync_direction=SyncDirection.FROM_APPFOLIO,
                sync_mode=SyncMode.SELECTIVE,
                filters=filters,
                priority="high",
                batch_size=10
            )
            
            # Execute sync
            await self.sync_service.execute_sync_job(sync_job.job_id)
            
            logger.info(f"Triggered selective sync for {entity_types} in organization {organization_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger selective sync: {str(e)}")
            raise
    
    def setup_organization_webhooks(self, organization_id: str, event_types: List[WebhookEventType] = None) -> Dict[str, Any]:
        """Setup webhook subscription for organization"""
        try:
            if event_types is None:
                # Subscribe to all event types by default
                event_types = list(WebhookEventType)
            
            # Generate subscription
            subscription_id = str(uuid.uuid4())
            secret_key = str(uuid.uuid4())
            
            # Create subscription
            subscription = WebhookSubscription(
                subscription_id=subscription_id,
                organization_id=organization_id,
                event_types=event_types,
                endpoint_url=f"/webhooks/appfolio/{organization_id}",
                secret_key=secret_key
            )
            
            # Store subscription
            self.subscriptions[organization_id] = subscription
            
            logger.info(f"Setup webhooks for organization {organization_id}")
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'endpoint_url': subscription.endpoint_url,
                'secret_key': secret_key,
                'event_types': [et.value for et in event_types]
            }
            
        except Exception as e:
            logger.error(f"Failed to setup webhooks: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def enable_organization_webhooks(self, organization_id: str) -> bool:
        """Enable webhooks for organization"""
        if organization_id in self.subscriptions:
            self.subscriptions[organization_id].active = True
            logger.info(f"Enabled webhooks for organization {organization_id}")
            return True
        return False
    
    def disable_organization_webhooks(self, organization_id: str) -> bool:
        """Disable webhooks for organization"""
        if organization_id in self.subscriptions:
            self.subscriptions[organization_id].active = False
            logger.info(f"Disabled webhooks for organization {organization_id}")
            return True
        return False
    
    def get_webhook_status(self, organization_id: str) -> Dict[str, Any]:
        """Get webhook status for organization"""
        subscription = self.subscriptions.get(organization_id)
        
        if not subscription:
            return {
                'enabled': False,
                'subscription_exists': False
            }
        
        # Get recent events
        recent_events = [
            event for event in self.processed_events[-50:]
            if event.organization_id == organization_id
        ]
        
        return {
            'enabled': subscription.active,
            'subscription_exists': True,
            'subscription_id': subscription.subscription_id,
            'endpoint_url': subscription.endpoint_url,
            'event_types': [et.value for et in subscription.event_types],
            'last_delivery': subscription.last_delivery.isoformat() if subscription.last_delivery else None,
            'delivery_count': subscription.delivery_count,
            'failure_count': subscription.failure_count,
            'recent_events': len(recent_events),
            'pending_events': len([e for e in self.pending_events.values() if e.organization_id == organization_id])
        }
    
    def _get_organization_subscription(self, organization_id: str) -> Optional[WebhookSubscription]:
        """Get webhook subscription for organization"""
        return self.subscriptions.get(organization_id)
    
    def get_webhook_events(self, organization_id: str, limit: int = 50, 
                          status: WebhookStatus = None) -> List[WebhookEvent]:
        """Get webhook events for organization"""
        # Combine pending and processed events
        all_events = list(self.pending_events.values()) + self.processed_events
        
        # Filter by organization
        org_events = [
            event for event in all_events
            if event.organization_id == organization_id
        ]
        
        # Filter by status if specified
        if status:
            org_events = [event for event in org_events if event.status == status]
        
        # Sort by timestamp, most recent first
        org_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return org_events[:limit]
    
    def retry_failed_event(self, event_id: str) -> bool:
        """Retry a failed webhook event"""
        if event_id in self.pending_events:
            event = self.pending_events[event_id]
            if event.status == WebhookStatus.FAILED and event.retry_count < event.max_retries:
                event.status = WebhookStatus.PENDING
                event.error_message = None
                
                # Process event
                self.executor.submit(self._process_webhook_event, event_id)
                
                logger.info(f"Retrying failed webhook event {event_id}")
                return True
        
        return False
    
    def get_webhook_statistics(self, organization_id: str = None) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        if organization_id:
            events = [
                event for event in (list(self.pending_events.values()) + self.processed_events)
                if event.organization_id == organization_id
            ]
        else:
            events = list(self.pending_events.values()) + self.processed_events
        
        # Calculate statistics
        total_events = len(events)
        completed_events = len([e for e in events if e.status == WebhookStatus.COMPLETED])
        failed_events = len([e for e in events if e.status == WebhookStatus.FAILED])
        pending_events = len([e for e in events if e.status == WebhookStatus.PENDING])
        processing_events = len([e for e in events if e.status == WebhookStatus.PROCESSING])
        
        return {
            'total_events': total_events,
            'completed_events': completed_events,
            'failed_events': failed_events,
            'pending_events': pending_events,
            'processing_events': processing_events,
            'success_rate': (completed_events / total_events * 100) if total_events > 0 else 0,
            'failure_rate': (failed_events / total_events * 100) if total_events > 0 else 0,
            'active_subscriptions': len([s for s in self.subscriptions.values() if s.active])
        }
    
    def start_webhook_server(self, host: str = '0.0.0.0', port: int = 5001, debug: bool = False):
        """Start the webhook server"""
        logger.info(f"Starting AppFolio webhook server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)
    
    def stop_processing(self):
        """Stop webhook processing"""
        self.processing_enabled = False
        logger.info("Webhook processing stopped")
    
    def start_processing(self):
        """Start webhook processing"""
        self.processing_enabled = True
        logger.info("Webhook processing started")