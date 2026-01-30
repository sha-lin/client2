# clientapp/websocket_helpers.py
import asyncio
from channels.layers import get_channel_layer
from django.utils import timezone


def broadcast_job_update(job_id, update_type, data):
    """
    Broadcast job update to all connected clients
    
    Args:
        job_id: Job ID to broadcast to
        update_type: Type of update (status_update, progress_update, etc)
        data: Data to send
    """
    channel_layer = get_channel_layer()
    group_name = f'job_{job_id}'
    
    asyncio.run(
        channel_layer.group_send(
            group_name,
            {
                'type': 'job_' + update_type,
                'job_id': job_id,
                'timestamp': timezone.now().isoformat(),
                **data
            }
        )
    )


def broadcast_dashboard_update(dashboard_type, user_id, update_type, data):
    """
    Broadcast dashboard update to user
    
    Args:
        dashboard_type: Type of dashboard (jobs, substitutions, etc)
        user_id: User ID to broadcast to
        update_type: Type of update
        data: Data to send
    """
    channel_layer = get_channel_layer()
    group_name = f'dashboard_{dashboard_type}_{user_id}'
    
    asyncio.run(
        channel_layer.group_send(
            group_name,
            {
                'type': update_type,
                'timestamp': timezone.now().isoformat(),
                **data
            }
        )
    )


def send_notification(user_id, notification_type, data):
    """
    Send notification to specific user
    
    Args:
        user_id: User ID to notify
        notification_type: Type of notification
        data: Notification data
    """
    channel_layer = get_channel_layer()
    group_name = f'notifications_{user_id}'
    
    asyncio.run(
        channel_layer.group_send(
            group_name,
            {
                'type': notification_type,
                'timestamp': timezone.now().isoformat(),
                **data
            }
        )
    )


def send_job_assigned_notification(user_id, job_id, job_number, priority):
    """Send job assigned notification"""
    send_notification(user_id, 'job_assigned', {
        'job_id': job_id,
        'job_number': job_number,
        'priority': priority,
    })


def send_substitution_approved_notification(user_id, substitution_id, po_number, original_material, proposed_material):
    """Send substitution approved notification"""
    send_notification(user_id, 'substitution_approved', {
        'substitution_id': substitution_id,
        'po_number': po_number,
        'original_material': original_material,
        'proposed_material': proposed_material,
    })


def send_substitution_rejected_notification(user_id, substitution_id, po_number, reason):
    """Send substitution rejected notification"""
    send_notification(user_id, 'substitution_rejected', {
        'substitution_id': substitution_id,
        'po_number': po_number,
        'reason': reason,
    })


def send_invoice_status_notification(user_id, invoice_id, po_number, status):
    """Send invoice status notification"""
    send_notification(user_id, 'invoice_status_changed', {
        'invoice_id': invoice_id,
        'po_number': po_number,
        'status': status,
    })


def send_deadline_approaching_notification(user_id, job_id, job_number, days_remaining, severity='warning'):
    """Send deadline approaching notification"""
    send_notification(user_id, 'deadline_approaching', {
        'job_id': job_id,
        'job_number': job_number,
        'days_remaining': days_remaining,
        'severity': severity,
    })


def broadcast_substitution_update(substitution_id, update_type, data):
    """
    Broadcast substitution update to all connected clients
    
    Args:
        substitution_id: Substitution ID to broadcast to
        update_type: Type of update
        data: Data to send
    """
    channel_layer = get_channel_layer()
    group_name = f'substitution_{substitution_id}'
    
    asyncio.run(
        channel_layer.group_send(
            group_name,
            {
                'type': 'substitution_' + update_type,
                'substitution_id': substitution_id,
                **data
            }
        )
    )
