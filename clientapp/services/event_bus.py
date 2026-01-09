"""
Timeline & Event Bus - Internal event emission system
Drives notifications, webhooks, and audit trails
"""
from typing import Optional, Dict, Any
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import TimelineEvent, WebhookSubscription, WebhookDelivery

User = get_user_model()


class EventBus:
    """
    Internal Event Bus - Emit events for timeline tracking
    """
    
    @staticmethod
    def emit_event(
        event_type: str,
        entity_type: str,
        entity_id: int,
        actor: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TimelineEvent:
        """
        Emit an event to the timeline
        
        Args:
            event_type: Event type (e.g., 'quote.approved')
            entity_type: Entity type (e.g., 'quote', 'order', 'job')
            entity_id: Entity ID
            actor: User who triggered the event (optional)
            metadata: Additional event data (optional)
        
        Returns:
            TimelineEvent instance
        """
        event = TimelineEvent.objects.create(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            metadata=metadata or {}
        )
        
        # Trigger webhook deliveries asynchronously (would use Celery/Dramatiq in production)
        EventBus._trigger_webhooks(event)
        
        return event
    
    @staticmethod
    def _trigger_webhooks(event: TimelineEvent):
        """
        Trigger webhook deliveries for matching subscriptions
        In production, this would be async via Celery/Dramatiq
        """
        subscriptions = WebhookSubscription.objects.filter(
            is_active=True,
            event_types__contains=[event.event_type]
        )
        
        for subscription in subscriptions:
            # Create delivery record
            delivery = WebhookDelivery.objects.create(
                subscription=subscription,
                event=event,
                status='pending',
                payload=EventBus._build_webhook_payload(event, subscription)
            )
            
            # In production, send via async task
            # send_webhook.delay(delivery.id)
            # For now, we'll just create the delivery record
    
    @staticmethod
    def _build_webhook_payload(event: TimelineEvent, subscription: WebhookSubscription) -> Dict[str, Any]:
        """Build webhook payload with signature"""
        import hmac
        import hashlib
        import json
        
        payload = {
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "timestamp": event.timestamp.isoformat(),
            "metadata": event.metadata,
        }
        
        if event.actor:
            payload["actor"] = {
                "id": event.actor.id,
                "email": event.actor.email,
                "username": event.actor.username,
            }
        
        # Sign payload
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            subscription.secret_key.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        payload["signature"] = signature
        
        return payload

