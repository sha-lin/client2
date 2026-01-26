"""
Django signal handlers for storefront backend.
Automatically creates related objects and sends notifications on model events.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .models import (
    EstimateQuote, StorefrontMessage, ChatbotConversation,
    StorefrontCustomer, ProductionUnit, StorefrontProduct,
    QuotePricingSnapshot
)
from .storefront_utils import (
    EmailService, WhatsAppService, ChatbotService,
    NotificationService, IDGenerator
)


# ===================== EstimateQuote Signals =====================

@receiver(post_save, sender=EstimateQuote)
def estimate_quote_created(sender, instance, created, **kwargs):
    """
    Handle EstimateQuote creation.
    - Generate estimate_id if not present
    - Set expiration date (7 days from creation)
    - Log to QuotePricingSnapshot
    """
    if created:
        # Generate estimate_id if not set
        if not instance.estimate_id or instance.estimate_id.startswith('TEMP'):
            instance.estimate_id = IDGenerator.generate_estimate_id()
            instance.save(update_fields=['estimate_id'])

        # Set expiration date if not set
        if not instance.expires_at:
            instance.expires_at = timezone.now() + timedelta(days=7)
            instance.save(update_fields=['expires_at'])

        # Create pricing snapshot
        QuotePricingSnapshot.objects.create(
            estimate_quote=instance,
            snapshot_type='estimate_created',
            base_amount=instance.subtotal,
            adjustments={},
            total_amount=instance.total_amount,
            reason='Initial estimate creation'
        )


@receiver(pre_save, sender=EstimateQuote)
def estimate_quote_status_changed(sender, instance, **kwargs):
    """
    Handle EstimateQuote status changes.
    - Track when estimate is shared
    - Create Lead when estimate is shared
    """
    try:
        old_instance = EstimateQuote.objects.get(pk=instance.pk)
        
        # If status changed to shared_with_am
        if old_instance.status != instance.status and instance.status == 'shared_with_am':
            if not instance.share_timestamp:
                instance.share_timestamp = timezone.now()
            
            # Create Lead from estimate
            try:
                from .models import Lead
                lead = Lead.objects.create(
                    name=instance.customer_name,
                    email=instance.customer_email,
                    phone=instance.customer_phone,
                    company=instance.customer_company,
                    source='Storefront - Estimate',
                    status='Qualified',
                    created_by=None  # System created
                )
                
                # Link estimate to lead
                instance.linked_lead_id = lead.id
            except Exception as e:
                print(f"Error creating Lead from Estimate: {e}")

        # If status changed to converted_to_quote
        if old_instance.status != instance.status and instance.status == 'converted_to_quote':
            # Archive the estimate
            pass  # Status change itself indicates conversion
            
    except EstimateQuote.DoesNotExist:
        pass


# ===================== StorefrontMessage Signals =====================

@receiver(post_save, sender=StorefrontMessage)
def message_created(sender, instance, created, **kwargs):
    """
    Handle StorefrontMessage creation.
    - Generate message_id if not present
    - Send confirmation to customer
    - Route to unassigned queue for Account Managers
    """
    if created:
        # Generate message_id if not set
        if not instance.message_id or instance.message_id.startswith('TEMP'):
            instance.message_id = IDGenerator.generate_message_id()
            instance.save(update_fields=['message_id'])

        # Send confirmation based on channel
        if instance.channel == 'email':
            try:
                EmailService.send_registration_email(
                    instance.customer_email,
                    verification_token='',
                    message_id=instance.message_id
                )
            except Exception as e:
                print(f"Error sending email confirmation: {e}")

        elif instance.channel == 'whatsapp':
            try:
                WhatsAppService.send_message(
                    instance.customer_phone,
                    f"Thank you for your message. We'll respond shortly. Reference: {instance.message_id}"
                )
            except Exception as e:
                print(f"Error sending WhatsApp confirmation: {e}")

        # Create ChatbotConversation if this is from chat
        if instance.channel == 'chat' and not instance.related_estimate_quote:
            try:
                ChatbotConversation.objects.create(
                    customer=instance.customer,
                    session_id=instance.message_id,
                    messages=[{
                        'timestamp': timezone.now().isoformat(),
                        'sender': 'customer',
                        'text': instance.message_content,
                        'action': None
                    }],
                    context={'channel': 'chat'},
                    escalated_to_human=False
                )
            except Exception as e:
                print(f"Error creating ChatbotConversation: {e}")


@receiver(post_save, sender=StorefrontMessage)
def message_resolved(sender, instance, created, **kwargs):
    """
    Handle StorefrontMessage resolution.
    - Send response to customer
    - Update conversation status
    """
    if not created and instance.status == 'resolved' and instance.response_message:
        # Send response based on channel
        if instance.channel == 'email':
            try:
                EmailService.send_registration_email(
                    instance.customer_email,
                    verification_token='',
                    subject=f"Re: {instance.subject}"
                )
            except Exception as e:
                print(f"Error sending email response: {e}")

        elif instance.channel == 'whatsapp':
            try:
                WhatsAppService.send_message(
                    instance.customer_phone,
                    instance.response_message
                )
            except Exception as e:
                print(f"Error sending WhatsApp response: {e}")


# ===================== ChatbotConversation Signals =====================

@receiver(post_save, sender=ChatbotConversation)
def chatbot_conversation_escalated(sender, instance, created, **kwargs):
    """
    Handle ChatbotConversation escalation.
    - Create StorefrontMessage when escalated
    - Assign to Account Manager
    """
    if instance.escalated_to_human and not created:
        try:
            # Create message from conversation
            last_message = instance.messages[-1] if instance.messages else {}
            
            StorefrontMessage.objects.create(
                customer=instance.customer,
                customer_name=instance.context.get('name', 'Unknown'),
                customer_email=instance.context.get('email', ''),
                customer_phone=instance.context.get('phone', ''),
                message_type='chat',
                channel='chat',
                subject='Chatbot Escalation',
                message_content=last_message.get('text', 'User escalated from chatbot'),
                status='new',
                related_estimate_quote=instance.related_estimate_quote
            )
        except Exception as e:
            print(f"Error creating message from escalation: {e}")


# ===================== ProductionUnit Signals =====================

@receiver(post_save, sender=ProductionUnit)
def production_unit_created(sender, instance, created, **kwargs):
    """
    Handle ProductionUnit creation.
    - Generate unit_id if not present
    - Notify vendor of upcoming PO
    """
    if created:
        # Generate unit_id if not set
        if not instance.unit_id or instance.unit_id.startswith('TEMP'):
            job_id = instance.job.id
            sequence = instance.unit_sequence
            instance.unit_id = f"UNIT-JOB-{timezone.now().year}-{job_id:06d}-{sequence:02d}"
            instance.save(update_fields=['unit_id'])


@receiver(pre_save, sender=ProductionUnit)
def production_unit_status_changed(sender, instance, **kwargs):
    """
    Handle ProductionUnit status changes.
    - Send notifications on status changes
    - Track timeline changes
    """
    try:
        old_instance = ProductionUnit.objects.get(pk=instance.pk)
        
        # If status changed to po_sent
        if old_instance.status != instance.status and instance.status == 'po_sent':
            if not instance.actual_start_date:
                instance.actual_start_date = timezone.now().date()
            
            # Notify vendor
            if instance.vendor:
                try:
                    vendor_email = instance.vendor.email
                    EmailService.send_registration_email(
                        vendor_email,
                        verification_token='',
                        subject=f"Purchase Order for {instance.job.job_id}"
                    )
                except Exception as e:
                    print(f"Error notifying vendor: {e}")

        # If status changed to completed
        if old_instance.status != instance.status and instance.status == 'completed':
            if not instance.actual_end_date:
                instance.actual_end_date = timezone.now().date()
            
            # Check if all units in job are completed
            try:
                job = instance.job
                completed_units = ProductionUnit.objects.filter(
                    job=job,
                    status='completed'
                ).count()
                total_units = ProductionUnit.objects.filter(job=job).count()
                
                if completed_units == total_units:
                    # All units completed - mark job as complete
                    job.status = 'completed'
                    job.save()
            except Exception as e:
                print(f"Error updating job status: {e}")

    except ProductionUnit.DoesNotExist:
        pass


# ===================== StorefrontCustomer Signals =====================

@receiver(post_save, sender=StorefrontCustomer)
def customer_created(sender, instance, created, **kwargs):
    """
    Handle StorefrontCustomer creation.
    - Generate customer_id if not present
    - Send welcome email
    """
    if created:
        # Generate customer_id if not set
        if not instance.customer_id or instance.customer_id.startswith('TEMP'):
            instance.customer_id = IDGenerator.generate_customer_id()
            instance.save(update_fields=['customer_id'])

        # Send welcome email
        try:
            EmailService.send_registration_email(
                instance.user.email,
                verification_token='',
                subject='Welcome to Storefront'
            )
        except Exception as e:
            print(f"Error sending welcome email: {e}")


# ===================== QuotePricingSnapshot Signals =====================

@receiver(post_save, sender=QuotePricingSnapshot)
def pricing_snapshot_created(sender, instance, created, **kwargs):
    """
    Handle QuotePricingSnapshot creation.
    - Generate snapshot_id if not present
    - Log pricing changes
    """
    if created and not instance.snapshot_id:
        instance.snapshot_id = f"SNAP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{instance.id}"
        instance.save(update_fields=['snapshot_id'])


# ===================== StorefrontProduct Signals =====================

@receiver(post_save, sender=StorefrontProduct)
def product_price_changed(sender, instance, created, **kwargs):
    """
    Handle StorefrontProduct price changes.
    - Create pricing snapshot
    - Log changes for admin review
    """
    if not created:
        # Check if price changed by comparing with last snapshot
        try:
            last_snapshot = QuotePricingSnapshot.objects.filter(
                product_id=instance.id
            ).latest('snapshot_at')
            
            if Decimal(last_snapshot.total_amount or 0) != Decimal(instance.base_price or 0):
                QuotePricingSnapshot.objects.create(
                    snapshot_type='product_price_updated',
                    base_amount=instance.base_price,
                    total_amount=instance.base_price,
                    reason=f'Product {instance.name} price updated'
                )
        except QuotePricingSnapshot.DoesNotExist:
            pass
