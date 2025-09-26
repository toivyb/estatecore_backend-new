"""
Yardi Webhook Service

Handles real-time webhook notifications from Yardi systems for immediate
data synchronization and event processing.
"""

import os
import logging
import json
import hmac
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
import requests
from urllib.parse import urljoin

from .models import YardiProductType, YardiEntityType

logger = logging.getLogger(__name__)

class WebhookEventType(Enum):
    """Yardi webhook event types"""
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_DELETED = "tenant.deleted"
    LEASE_CREATED = "lease.created"
    LEASE_UPDATED = "lease.updated"
    LEASE_EXPIRED = "lease.expired"
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    WORKORDER_CREATED = "workorder.created"
    WORKORDER_COMPLETED = "workorder.completed"
    UNIT_AVAILABLE = "unit.available"
    UNIT_OCCUPIED = "unit.occupied"

@dataclass
class WebhookEvent:
    """Webhook event data"""
    event_id: str
    event_type: WebhookEventType
    entity_type: YardiEntityType
    entity_id: str
    organization_id: str
    yardi_product: YardiProductType
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False
    retry_count: int = 0

class YardiWebhookService:
    """Yardi Webhook Service for real-time notifications"""
    
    def __init__(self, sync_service):
        self.sync_service = sync_service
        self.webhook_handlers: Dict[WebhookEventType, List[Callable]] = {}
        self.webhook_configs: Dict[str, Dict[str, Any]] = {}
        self.pending_events: List[WebhookEvent] = []
        
        # Register default handlers
        self._register_default_handlers()
        
        logger.info("Yardi Webhook Service initialized")
    
    def _register_default_handlers(self):
        """Register default webhook event handlers"""
        self.register_handler(WebhookEventType.TENANT_CREATED, self._handle_tenant_created)
        self.register_handler(WebhookEventType.TENANT_UPDATED, self._handle_tenant_updated)
        self.register_handler(WebhookEventType.PAYMENT_RECEIVED, self._handle_payment_received)
    
    def register_handler(self, event_type: WebhookEventType, handler: Callable):
        """Register webhook event handler"""
        if event_type not in self.webhook_handlers:
            self.webhook_handlers[event_type] = []
        self.webhook_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value}")
    
    def setup_organization_webhooks(self, organization_id: str, 
                                  yardi_product: YardiProductType) -> Dict[str, Any]:
        """Setup webhooks for organization"""
        try:
            # This would configure webhooks with Yardi system
            webhook_config = {
                "organization_id": organization_id,
                "yardi_product": yardi_product,
                "enabled_events": [event.value for event in WebhookEventType],
                "endpoint": f"{os.environ.get('WEBHOOK_BASE_URL', 'https://api.estatecore.com')}/webhooks/yardi/{organization_id}",
                "secret": self._generate_webhook_secret()
            }
            
            self.webhook_configs[organization_id] = webhook_config
            
            return {
                "success": True,
                "webhook_config": webhook_config
            }
        except Exception as e:
            logger.error(f"Failed to setup webhooks: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_webhook(self, organization_id: str, headers: Dict[str, str], 
                            payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook"""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(organization_id, headers, payload):
                return {"success": False, "error": "Invalid signature"}
            
            # Parse webhook event
            event = self._parse_webhook_event(organization_id, payload)
            if not event:
                return {"success": False, "error": "Invalid event format"}
            
            # Process event
            await self._process_webhook_event(event)
            
            return {"success": True, "event_id": event.event_id}
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_webhook_event(self, event: WebhookEvent):
        """Process webhook event"""
        try:
            handlers = self.webhook_handlers.get(event.event_type, [])
            
            for handler in handlers:
                await handler(event)
            
            event.processed = True
            logger.info(f"Processed webhook event {event.event_id}")
            
        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            event.retry_count += 1
            if event.retry_count < 3:
                self.pending_events.append(event)
    
    def _verify_webhook_signature(self, organization_id: str, headers: Dict[str, str],
                                payload: Dict[str, Any]) -> bool:
        """Verify webhook signature"""
        config = self.webhook_configs.get(organization_id)
        if not config:
            return False
        
        signature = headers.get('X-Yardi-Signature', '')
        secret = config.get('secret', '')
        
        expected_signature = hmac.new(
            secret.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _parse_webhook_event(self, organization_id: str, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse webhook payload into event object"""
        try:
            event_type_str = payload.get('event_type')
            event_type = WebhookEventType(event_type_str)
            
            entity_type_str = payload.get('entity_type')
            entity_type = YardiEntityType(entity_type_str)
            
            config = self.webhook_configs.get(organization_id)
            yardi_product = YardiProductType(config.get('yardi_product')) if config else YardiProductType.VOYAGER
            
            return WebhookEvent(
                event_id=payload.get('event_id', str(uuid.uuid4())),
                event_type=event_type,
                entity_type=entity_type,
                entity_id=payload.get('entity_id'),
                organization_id=organization_id,
                yardi_product=yardi_product,
                event_data=payload.get('data', {})
            )
        except Exception as e:
            logger.error(f"Failed to parse webhook event: {e}")
            return None
    
    def _generate_webhook_secret(self) -> str:
        """Generate webhook secret"""
        return f"yardi_webhook_{uuid.uuid4().hex}"
    
    # Default event handlers
    
    async def _handle_tenant_created(self, event: WebhookEvent):
        """Handle tenant created event"""
        # Trigger sync for new tenant
        await self.sync_service.sync_entity_manual(
            event.organization_id, "tenants", [event.event_data]
        )
    
    async def _handle_tenant_updated(self, event: WebhookEvent):
        """Handle tenant updated event"""
        # Trigger incremental sync for updated tenant
        await self.sync_service.sync_entity_manual(
            event.organization_id, "tenants", [event.event_data]
        )
    
    async def _handle_payment_received(self, event: WebhookEvent):
        """Handle payment received event"""
        # Trigger payment sync
        await self.sync_service.sync_entity_manual(
            event.organization_id, "payments", [event.event_data]
        )
    
    def enable_organization_webhooks(self, organization_id: str):
        """Enable webhooks for organization"""
        if organization_id in self.webhook_configs:
            self.webhook_configs[organization_id]["enabled"] = True
    
    def disable_organization_webhooks(self, organization_id: str):
        """Disable webhooks for organization"""
        if organization_id in self.webhook_configs:
            self.webhook_configs[organization_id]["enabled"] = False
    
    def get_webhook_status(self, organization_id: str) -> Dict[str, Any]:
        """Get webhook status for organization"""
        config = self.webhook_configs.get(organization_id, {})
        return {
            "enabled": config.get("enabled", False),
            "healthy": True,  # Would check actual health
            "recent_deliveries": 0,  # Would track actual deliveries
            "failed_deliveries": 0,  # Would track failures
            "last_delivery": None
        }