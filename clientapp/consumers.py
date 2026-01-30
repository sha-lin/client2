# clientapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Job, MaterialSubstitutionRequest, VendorInvoice


class JobUpdateConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time job updates"""
    
    async def connect(self):
        """Handle WebSocket connection for job updates"""
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.job_group_name = f'job_{self.job_id}'
        
        # Verify user has access to this job
        if not await self.user_has_job_access(self.job_id):
            await self.close()
            return
        
        # Join job group
        await self.channel_layer.group_add(
            self.job_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial job data
        job_data = await self.get_job_data(self.job_id)
        await self.send(text_data=json.dumps({
            'type': 'job_update',
            'action': 'initial',
            'data': job_data
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.job_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        event_type = data.get('type')
        
        if event_type == 'status_update':
            await self.broadcast_job_update({
                'type': 'job_status_updated',
                'job_id': self.job_id,
                'status': data.get('status'),
                'timestamp': timezone.now().isoformat()
            })
        
        elif event_type == 'progress_update':
            await self.broadcast_job_update({
                'type': 'job_progress_updated',
                'job_id': self.job_id,
                'progress': data.get('progress'),
                'notes': data.get('notes'),
                'timestamp': timezone.now().isoformat()
            })
    
    async def job_status_updated(self, event):
        """Broadcast job status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'job_status_updated',
            'job_id': event['job_id'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    async def job_progress_updated(self, event):
        """Broadcast job progress update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'job_progress_updated',
            'job_id': event['job_id'],
            'progress': event['progress'],
            'notes': event['notes'],
            'timestamp': event['timestamp']
        }))
    
    async def broadcast_job_update(self, event):
        """Broadcast update to all clients in job group"""
        await self.channel_layer.group_send(
            self.job_group_name,
            event
        )
    
    @database_sync_to_async
    def user_has_job_access(self, job_id):
        """Verify user has access to job"""
        try:
            job = Job.objects.get(pk=job_id)
            user = self.scope['user']
            
            # Check if user is assigned to this job or is in PT/AM/Admin
            return (
                job.person_in_charge == user or
                user.groups.filter(name__in=['Production Team', 'Account Manager']).exists() or
                user.is_superuser
            )
        except Job.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_job_data(self, job_id):
        """Get current job data"""
        try:
            job = Job.objects.get(pk=job_id)
            return {
                'id': job.id,
                'job_number': job.job_number,
                'status': job.status,
                'progress': job.progress if hasattr(job, 'progress') else 0,
                'deadline': job.deadline.isoformat() if job.deadline else None,
                'person_in_charge': job.person_in_charge.get_full_name() if job.person_in_charge else None,
            }
        except Job.DoesNotExist:
            return None


class DashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time dashboard updates"""
    
    async def connect(self):
        """Handle WebSocket connection for dashboard"""
        self.dashboard_type = self.scope['url_route']['kwargs']['dashboard_type']
        self.user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None
        
        if not self.user_id:
            await self.close()
            return
        
        self.group_name = f'dashboard_{self.dashboard_type}_{self.user_id}'
        
        # Join dashboard group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        data = json.loads(text_data)
        
        # Broadcast dashboard update
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'dashboard_update',
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def dashboard_update(self, event):
        """Send dashboard update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def new_job_alert(self, event):
        """Alert about new job"""
        await self.send(text_data=json.dumps({
            'type': 'new_job_alert',
            'job_id': event['job_id'],
            'job_number': event['job_number'],
            'priority': event['priority'],
            'timestamp': event['timestamp']
        }))
    
    async def job_count_updated(self, event):
        """Send updated job counts"""
        await self.send(text_data=json.dumps({
            'type': 'job_count_updated',
            'total': event['total'],
            'assigned': event['assigned'],
            'in_progress': event['in_progress'],
            'completed': event['completed']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        """Handle WebSocket connection for notifications"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Verify requesting user is the target user
        if self.scope['user'].id != int(self.user_id):
            await self.close()
            return
        
        self.notification_group = f'notifications_{self.user_id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.notification_group,
            self.channel_name
        )
    
    async def job_assigned(self, event):
        """Notify about job assignment"""
        await self.send(text_data=json.dumps({
            'type': 'job_assigned',
            'title': f"Job {event['job_number']} assigned to you",
            'job_id': event['job_id'],
            'job_number': event['job_number'],
            'priority': event['priority'],
            'timestamp': event['timestamp']
        }))
    
    async def substitution_approved(self, event):
        """Notify about material substitution approval"""
        await self.send(text_data=json.dumps({
            'type': 'substitution_approved',
            'title': 'Material substitution approved',
            'substitution_id': event['substitution_id'],
            'po_number': event['po_number'],
            'material_change': f"{event['original_material']} → {event['proposed_material']}",
            'timestamp': event['timestamp']
        }))
    
    async def substitution_rejected(self, event):
        """Notify about material substitution rejection"""
        await self.send(text_data=json.dumps({
            'type': 'substitution_rejected',
            'title': 'Material substitution rejected',
            'substitution_id': event['substitution_id'],
            'po_number': event['po_number'],
            'reason': event['reason'],
            'timestamp': event['timestamp']
        }))
    
    async def invoice_status_changed(self, event):
        """Notify about invoice status change"""
        await self.send(text_data=json.dumps({
            'type': 'invoice_status_changed',
            'title': f"Invoice status changed to {event['status']}",
            'invoice_id': event['invoice_id'],
            'po_number': event['po_number'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    async def deadline_approaching(self, event):
        """Alert about approaching deadline"""
        await self.send(text_data=json.dumps({
            'type': 'deadline_approaching',
            'title': 'Deadline approaching',
            'job_id': event['job_id'],
            'job_number': event['job_number'],
            'days_remaining': event['days_remaining'],
            'severity': event['severity'],  # 'warning', 'critical'
            'timestamp': event['timestamp']
        }))


class SubstitutionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for material substitution updates"""
    
    async def connect(self):
        """Handle WebSocket connection for substitution updates"""
        self.substitution_id = self.scope['url_route']['kwargs']['substitution_id']
        self.substitution_group = f'substitution_{self.substitution_id}'
        
        # Verify user has access to this substitution
        if not await self.user_has_substitution_access(self.substitution_id):
            await self.close()
            return
        
        # Join substitution group
        await self.channel_layer.group_add(
            self.substitution_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial substitution data
        sub_data = await self.get_substitution_data(self.substitution_id)
        await self.send(text_data=json.dumps({
            'type': 'substitution_update',
            'action': 'initial',
            'data': sub_data
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.substitution_group,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        data = json.loads(text_data)
        event_type = data.get('type')
        
        if event_type == 'comment_added':
            await self.broadcast_substitution_update({
                'type': 'substitution_comment_added',
                'substitution_id': self.substitution_id,
                'comment': data.get('comment'),
                'author': data.get('author'),
                'timestamp': timezone.now().isoformat()
            })
    
    async def substitution_status_changed(self, event):
        """Notify about status change"""
        await self.send(text_data=json.dumps({
            'type': 'substitution_status_changed',
            'substitution_id': event['substitution_id'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    async def substitution_comment_added(self, event):
        """Notify about comment added"""
        await self.send(text_data=json.dumps({
            'type': 'substitution_comment_added',
            'substitution_id': event['substitution_id'],
            'comment': event['comment'],
            'author': event['author'],
            'timestamp': event['timestamp']
        }))
    
    async def broadcast_substitution_update(self, event):
        """Broadcast update to all clients"""
        await self.channel_layer.group_send(
            self.substitution_group,
            event
        )
    
    @database_sync_to_async
    def user_has_substitution_access(self, substitution_id):
        """Verify user has access to substitution"""
        try:
            substitution = MaterialSubstitutionRequest.objects.get(pk=substitution_id)
            user = self.scope['user']
            
            # Vendor can see their own requests
            # PT can see all for their clients
            # Admin can see all
            return (
                substitution.purchase_order.vendor_stage.vendor.user == user or
                user.groups.filter(name__in=['Production Team', 'Account Manager']).exists() or
                user.is_superuser
            )
        except MaterialSubstitutionRequest.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_substitution_data(self, substitution_id):
        """Get current substitution data"""
        try:
            sub = MaterialSubstitutionRequest.objects.get(pk=substitution_id)
            return {
                'id': sub.id,
                'original_material': sub.original_material,
                'proposed_material': sub.proposed_material,
                'status': sub.status,
                'match_percentage': sub.match_percentage,
                'created_at': sub.created_at.isoformat(),
            }
        except MaterialSubstitutionRequest.DoesNotExist:
            return None
