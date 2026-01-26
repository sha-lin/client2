"""
Celery tasks and scheduled jobs for automated workflows
"""
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def expire_old_quotes():
    """
    Daily task to mark expired quotes as Lost.
    Finds quotes with valid_until < today and status="Sent to Customer",
    then marks them as "Lost".
    
    Can be called directly or scheduled with Celery/APScheduler.
    """
    from .models import Quote, Notification, ActivityLog
    
    try:
        today = timezone.now().date()
        
        # Find expired quotes
        expired_quotes = Quote.objects.filter(
            valid_until__lt=today,
            status__in=['Sent to Customer', 'Sent to PT']
        ).select_related('client', 'created_by')
        
        count = 0
        for quote in expired_quotes:
            # Mark as lost
            quote.status = 'Lost'
            quote.loss_reason = 'Quote expired - customer did not approve within valid period'
            quote.save()
            
            count += 1
            
            # Create notification for AM
            if quote.created_by:
                try:
                    Notification.objects.create(
                        recipient=quote.created_by,
                        notification_type='quote_expired',
                        title=f'Quote {quote.quote_id} Expired',
                        message=f'Quote {quote.quote_id} expired on {quote.valid_until}. Marked as lost.',
                        link=f'/quotes/{quote.id}/',
                    )
                except Exception as e:
                    logger.warning(f"Failed to create notification for quote {quote.quote_id}: {e}")
            
            # Log activity
            if quote.client:
                try:
                    ActivityLog.objects.create(
                        client=quote.client,
                        activity_type='Quote',
                        title=f'Quote {quote.quote_id} Expired',
                        description=f'Quote expired on {quote.valid_until} and was marked as lost',
                        related_quote=quote,
                        created_by=quote.created_by,
                    )
                except Exception as e:
                    logger.warning(f"Failed to log activity for quote {quote.quote_id}: {e}")
        
        logger.info(f"Expired {count} old quotes")
        return {
            'status': 'success',
            'expired_quotes': count,
            'timestamp': str(timezone.now())
        }
    
    except Exception as exc:
        logger.error(f"Error in expire_old_quotes task: {exc}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': str(timezone.now())
        }


def remind_approaching_job_deadlines():
    """
    Send reminders for jobs nearing their deadline (within 3 days).
    Only reminds if job status is "pending" or "in_progress".
    Prevents spam by checking if reminder sent in last 24 hours.
    """
    from .models import Job, Notification, ActivityLog
    
    try:
        today = timezone.now().date()
        three_days = today + timedelta(days=3)
        one_day_ago = timezone.now() - timedelta(days=1)
        
        # Find jobs approaching deadline
        approaching_jobs = Job.objects.filter(
            expected_completion__gte=today,
            expected_completion__lte=three_days,
            status__in=['pending', 'in_progress'],
            person_in_charge__isnull=False
        ).select_related('person_in_charge', 'client')
        
        count = 0
        for job in approaching_jobs:
            # Check if reminder already sent today
            last_reminder = ActivityLog.objects.filter(
                title__contains=f'Deadline Reminder for Job {job.job_number}',
                created_at__gte=one_day_ago
            ).first()
            
            if last_reminder:
                continue
            
            # Send reminder notification
            try:
                Notification.objects.create(
                    recipient=job.person_in_charge,
                    notification_type='job_deadline_reminder',
                    title=f'Deadline Reminder: {job.job_name}',
                    message=f'Job {job.job_number} ({job.client.name}) is due on {job.expected_completion}. Days remaining: {(job.expected_completion - today).days}',
                    link=f'/jobs/{job.id}/',
                )
            except Exception as e:
                logger.warning(f"Failed to create notification for job {job.job_number}: {e}")
            
            # Log activity
            try:
                ActivityLog.objects.create(
                    client=job.client,
                    activity_type='Job',
                    title=f'Deadline Reminder for Job {job.job_number}',
                    description=f'Reminder sent to {job.person_in_charge.get_full_name()}. Due: {job.expected_completion}',
                )
            except Exception as e:
                logger.warning(f"Failed to log activity for job {job.job_number}: {e}")
            
            count += 1
        
        logger.info(f"Sent {count} job deadline reminders")
        return {
            'status': 'success',
            'reminders_sent': count,
            'timestamp': str(timezone.now())
        }
    
    except Exception as exc:
        logger.error(f"Error in remind_approaching_job_deadlines task: {exc}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': str(timezone.now())
        }


def sync_completed_pos_to_qb():
    """
    Sync completed Purchase Orders to QuickBooks.
    Finds POs marked as completed but not yet synced to QB.
    """
    from .models import PurchaseOrder
    
    try:
        # Find completed POs not yet synced
        completed_pos = PurchaseOrder.objects.filter(
            status='COMPLETED',
            invoice_sent=False
        ).select_related('job', 'vendor')
        
        count = 0
        for po in completed_pos:
            try:
                # Mark as ready for QB sync (actual QB sync happens in QB service)
                po.invoice_sent = True
                po.save()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to mark PO {po.po_number} for QB sync: {e}")
        
        logger.info(f"Marked {count} POs ready for QB sync")
        return {
            'status': 'success',
            'pos_synced': count,
            'timestamp': str(timezone.now())
        }
    
    except Exception as exc:
        logger.error(f"Error in sync_completed_pos_to_qb task: {exc}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': str(timezone.now())
        }


def check_po_delivery_overdue():
    """
    Check for Purchase Orders that are overdue (required_by date passed).
    Create alerts for PT to follow up with vendors.
    """
    from .models import PurchaseOrder, SystemAlert
    
    try:
        today = timezone.now().date()
        
        # Find overdue POs
        overdue_pos = PurchaseOrder.objects.filter(
            required_by__lt=today,
            status__in=['NEW', 'ACCEPTED', 'IN_PRODUCTION', 'AWAITING_APPROVAL'],
        ).select_related('job', 'vendor')
        
        count = 0
        for po in overdue_pos:
            # Check if alert already exists
            existing_alert = SystemAlert.objects.filter(
                title__contains=f'PO {po.po_number} Overdue',
                resolved=False
            ).first()
            
            if existing_alert:
                continue
            
            # Create system alert
            try:
                days_overdue = (today - po.required_by).days
                SystemAlert.objects.create(
                    alert_type='po_overdue',
                    title=f'PO {po.po_number} Overdue',
                    description=f'PO {po.po_number} from {po.vendor.name} was due on {po.required_by} ({days_overdue} days overdue). Status: {po.status}',
                    severity='high',
                    related_po=po,
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to create alert for PO {po.po_number}: {e}")
        
        logger.info(f"Created {count} overdue PO alerts")
        return {
            'status': 'success',
            'alerts_created': count,
            'timestamp': str(timezone.now())
        }
    
    except Exception as exc:
        logger.error(f"Error in check_po_delivery_overdue task: {exc}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': str(timezone.now())
        }


# ============================================================================
# PHASE 3: QUICKBOOKS BATCH SYNC TASKS
# ============================================================================

def batch_sync_pending_lpos_to_qb():
    """
    Phase 3 Task: Automatically sync pending LPOs to QuickBooks Invoices.
    Runs daily or can be triggered manually.
    Syncs approved LPOs that haven't been synced to QB yet.
    """
    from .quickbooks_services import QuickBooksFullSyncService
    from .models import User, LPO
    
    try:
        # Find admin user to use for QB sync
        admin_user = User.objects.filter(is_staff=True, is_superuser=True).first()
        
        if not admin_user:
            logger.warning("No admin user found for QB sync")
            return {
                'status': 'error',
                'error': 'No admin user found for QB sync',
                'timestamp': str(timezone.now())
            }
        
        sync_service = QuickBooksFullSyncService(admin_user)
        results = sync_service.batch_sync_lpos(limit=20)
        
        logger.info(f"Batch LPO sync completed: {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in batch LPO QB sync: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': str(timezone.now())
        }


def batch_sync_pending_vendor_invoices_to_qb():
    """
    Phase 3 Task: Automatically sync pending vendor invoices to QuickBooks Bills.
    Runs daily or can be triggered manually.
    Syncs approved vendor invoices that haven't been synced to QB yet.
    """
    from .quickbooks_services import QuickBooksFullSyncService
    from .models import User
    
    try:
        # Find admin user
        admin_user = User.objects.filter(is_staff=True, is_superuser=True).first()
        
        if not admin_user:
            logger.warning("No admin user found for QB sync")
            return {
                'status': 'error',
                'error': 'No admin user found for QB sync',
                'timestamp': str(timezone.now())
            }
        
        sync_service = QuickBooksFullSyncService(admin_user)
        results = sync_service.batch_sync_vendor_invoices(limit=20)
        
        logger.info(f"Batch vendor invoice sync completed: {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in batch vendor invoice QB sync: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': str(timezone.now())
        }


# Celery tasks (if using Celery)
try:
    from celery import shared_task
    
    @shared_task(bind=True, max_retries=3)
    def celery_expire_old_quotes(self):
        """Celery-wrapped version of expire_old_quotes"""
        try:
            return expire_old_quotes()
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60)
    
    @shared_task(bind=True, max_retries=3)
    def celery_remind_approaching_job_deadlines(self):
        """Celery-wrapped version of remind_approaching_job_deadlines"""
        try:
            return remind_approaching_job_deadlines()
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60)
    
    @shared_task(bind=True, max_retries=3)
    def celery_sync_completed_pos_to_qb(self):
        """Celery-wrapped version of sync_completed_pos_to_qb"""
        try:
            return sync_completed_pos_to_qb()
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60)
    
    @shared_task(bind=True, max_retries=3)
    def celery_check_po_delivery_overdue(self):
        """Celery-wrapped version of check_po_delivery_overdue"""
        try:
            return check_po_delivery_overdue()
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60)
    
    # ===== PHASE 3: QUICKBOOKS BATCH SYNC CELERY TASKS =====
    
    @shared_task(bind=True, max_retries=3)
    def celery_batch_sync_lpos_to_qb(self):
        """Celery-wrapped version of batch_sync_pending_lpos_to_qb"""
        try:
            return batch_sync_pending_lpos_to_qb()
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60)
    
    @shared_task(bind=True, max_retries=3)
    def celery_batch_sync_vendor_invoices_to_qb(self):
        """Celery-wrapped version of batch_sync_pending_vendor_invoices_to_qb"""
        try:
            return batch_sync_pending_vendor_invoices_to_qb()
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60)

except ImportError:
    # Celery not installed, tasks will be called directly via APScheduler
    logger.info("Celery not available, scheduled tasks will use APScheduler or direct calls")


# ===================== STOREFRONT CELERY TASKS =====================

try:
    from celery import shared_task
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives

    # Email Tasks
    @shared_task(bind=True, max_retries=3)
    def send_email_async(self, email_type, recipient_email, context=None, **kwargs):
        """Send email asynchronously with template rendering."""
        context = context or {}
        
        email_templates = {
            'welcome': 'emails/welcome.html',
            'registration_verification': 'emails/registration_verification.html',
            'estimate_shared': 'emails/estimate_shared.html',
            'quote_approved': 'emails/quote_approved.html',
            'invoice': 'emails/invoice_notification.html',
        }
        
        try:
            if email_type not in email_templates:
                logger.error(f"Unknown email type: {email_type}")
                return {'status': 'error', 'message': 'Unknown email type'}
            
            template_path = email_templates[email_type]
            html_content = render_to_string(template_path, context)
            
            email = EmailMultiAlternatives(
                subject=context.get('subject', f'{email_type} Notification'),
                body=f"Please view this email in HTML format.",
                from_email='noreply@storefront.local',
                to=[recipient_email]
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email sent: {email_type} to {recipient_email}")
            return {'status': 'success', 'message': 'Email sent'}
            
        except Exception as exc:
            logger.error(f"Error sending {email_type} email: {str(exc)}")
            try:
                raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
            except self.MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for {email_type} email")
                return {'status': 'failed', 'message': 'Max retries exceeded'}

    @shared_task(bind=True, max_retries=3)
    def send_whatsapp_async(self, phone_number, message_text, media_url=None, **kwargs):
        """Send WhatsApp message asynchronously."""
        try:
            from .storefront_utils import WhatsAppService
            result = WhatsAppService.send_message(phone_number, message_text, media_url)
            logger.info(f"WhatsApp sent to {phone_number}")
            return {'status': 'success', 'result': result}
        except Exception as exc:
            logger.error(f"Error sending WhatsApp: {str(exc)}")
            try:
                raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
            except self.MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for WhatsApp")
                return {'status': 'failed'}

    # Webhook Tasks
    @shared_task(bind=True, max_retries=3)
    def process_webhook(self, webhook_type, webhook_data, **kwargs):
        """Process incoming webhooks from payment gateways, WhatsApp, email."""
        try:
            logger.info(f"Processing {webhook_type} webhook")
            
            if webhook_type == 'payment':
                transaction_id = webhook_data.get('transaction_id')
                status = webhook_data.get('status')
                amount = webhook_data.get('amount')
                logger.info(f"Payment: {transaction_id} - {status} - {amount}")
                
            elif webhook_type == 'whatsapp_delivery':
                message_id = webhook_data.get('message_id')
                status = webhook_data.get('status')
                logger.info(f"WhatsApp delivery: {message_id} - {status}")
                
            elif webhook_type == 'email_delivery':
                message_id = webhook_data.get('message_id')
                status = webhook_data.get('status')
                logger.info(f"Email delivery: {message_id} - {status}")
            
            return {'status': 'processed', 'webhook_type': webhook_type}
            
        except Exception as exc:
            logger.error(f"Error processing webhook: {str(exc)}")
            try:
                raise self.retry(exc=exc, countdown=60)
            except self.MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for webhook")
                return {'status': 'failed'}

    # Scheduled Tasks
    @shared_task
    def archive_expired_estimates():
        """Automatically archive expired estimate quotes. Runs daily via Celery Beat."""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            expired = EstimateQuote.objects.filter(
                expires_at__lt=now,
                status__in=['draft_unsaved', 'shared_with_am']
            )
            
            count = expired.count()
            expired.update(status='archived')
            
            logger.info(f"Archived {count} expired estimates")
            return {'status': 'success', 'archived_count': count}
            
        except Exception as exc:
            logger.error(f"Error in archive_expired_estimates: {str(exc)}")
            return {'status': 'error', 'message': str(exc)}

    @shared_task
    def send_expiring_estimate_reminders():
        """Send reminders for estimates expiring within 2 days. Runs daily."""
        try:
            from datetime import timedelta
            
            now = timezone.now()
            expiring_soon = EstimateQuote.objects.filter(
                expires_at__gte=now,
                expires_at__lte=now + timedelta(days=2),
                status='shared_with_am'
            )
            
            count = 0
            for estimate in expiring_soon:
                send_email_async.delay(
                    'estimate_shared',
                    estimate.customer_email,
                    {'estimate_id': estimate.estimate_id}
                )
                count += 1
            
            logger.info(f"Sent {count} expiring estimate reminders")
            return {'status': 'success', 'reminder_count': count}
            
        except Exception as exc:
            logger.error(f"Error in send_expiring_estimate_reminders: {str(exc)}")
            return {'status': 'error', 'message': str(exc)}

    @shared_task
    def update_production_unit_status():
        """Update production unit statuses based on timelines. Runs every 6 hours."""
        try:
            now = timezone.now().date()
            
            units_to_start = ProductionUnit.objects.filter(
                expected_start_date__lte=now,
                status='pending_po'
            )
            units_to_start.update(status='in_progress')
            started = units_to_start.count()
            
            overdue_units = ProductionUnit.objects.filter(
                expected_end_date__lt=now,
                status__in=['pending_po', 'in_progress']
            )
            overdue_units.update(status='delayed')
            delayed = overdue_units.count()
            
            logger.info(f"Updated {started} units to in_progress, {delayed} to delayed")
            return {'status': 'success', 'started': started, 'delayed': delayed}
            
        except Exception as exc:
            logger.error(f"Error in update_production_unit_status: {str(exc)}")
            return {'status': 'error', 'message': str(exc)}

    @shared_task
    def generate_daily_report():
        """Generate daily report of new orders, quotes, messages. Runs daily at 8 AM."""
        try:
            from datetime import timedelta
            
            now = timezone.now()
            yesterday = now - timedelta(days=1)
            
            new_estimates = EstimateQuote.objects.filter(
                created_at__gte=yesterday,
                created_at__lt=now
            ).count()
            
            new_messages = StorefrontMessage.objects.filter(
                created_at__gte=yesterday,
                created_at__lt=now
            ).count()
            
            unassigned_messages = StorefrontMessage.objects.filter(
                status='new',
                assigned_to__isnull=True
            ).count()
            
            report = {
                'date': now.strftime('%Y-%m-%d'),
                'new_estimates': new_estimates,
                'new_messages': new_messages,
                'unassigned_messages': unassigned_messages,
            }
            
            logger.info(f"Daily report: {report}")
            return {'status': 'success', 'report': report}
            
        except Exception as exc:
            logger.error(f"Error in generate_daily_report: {str(exc)}")
            return {'status': 'error', 'message': str(exc)}

    @shared_task
    def cleanup_old_conversations():
        """Archive old chatbot conversations (older than 90 days). Runs weekly."""
        try:
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=90)
            
            old_conversations = ChatbotConversation.objects.filter(
                ended_at__lt=cutoff_date,
                resolved=True
            )
            
            count = old_conversations.count()
            old_conversations.delete()
            
            logger.info(f"Cleaned up {count} old conversations")
            return {'status': 'success', 'deleted_count': count}
            
        except Exception as exc:
            logger.error(f"Error in cleanup_old_conversations: {str(exc)}")
            return {'status': 'error', 'message': str(exc)}

except ImportError:
    logger.info("Celery tasks for storefront available when Celery is installed")
