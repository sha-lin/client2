# clientapp/services/quote_approval_service.py
"""
Quote Approval Service - Handles quote sending, approval, and LPO generation
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)


class QuoteApprovalService:
    """Service for handling quote approvals"""
    
    @staticmethod
    def get_quote_from_token(token):
        """
        Get quote details from approval token (for display purposes)
        
        Returns:
            dict: {'success': bool, 'quote': Quote, 'line_items': list, 'totals': dict, 'message': str}
        """
        try:
            from clientapp.models import QuoteApprovalToken, QuoteLineItem
            from decimal import Decimal
            
            # Validate token
            try:
                approval_token = QuoteApprovalToken.objects.get(
                    token=token,
                    expires_at__gt=timezone.now()
                )
            except QuoteApprovalToken.DoesNotExist:
                return {
                    'success': False,
                    'message': 'Invalid or expired approval link'
                }
            
            quote = approval_token.quote
            
            # Get line items
            line_items = QuoteLineItem.objects.filter(quote=quote).order_by('order', 'created_at')
            
            # Calculate totals
            if line_items.exists():
                subtotal = sum(float(item.line_total) for item in line_items)
            else:
                # Fallback to quote total
                subtotal = float(quote.total_amount or 0)
            
            vat_amount = subtotal * 0.16 if quote.include_vat else 0
            total_amount = subtotal + vat_amount
            
            # Format line items for display
            quote_items = []
            if line_items.exists():
                for item in line_items:
                    quote_items.append({
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_amount': float(item.line_total),
                    })
            else:
                # Fallback - use quote itself
                quote_items.append({
                    'product_name': quote.product_name,
                    'quantity': quote.quantity,
                    'unit_price': float(quote.unit_price or 0),
                    'total_amount': float(quote.total_amount or 0),
                })
            
            return {
                'success': True,
                'quote': quote,
                'line_items': line_items,
                'quote_items': quote_items,
                'totals': {
                    'subtotal': subtotal,
                    'vat_amount': vat_amount,
                    'total_amount': total_amount,
                },
                'token_valid': not approval_token.used,
                'token_used': approval_token.used,
            }
            
        except Exception as e:
            logger.error(f"Error getting quote from token: {e}")
            return {
                'success': False,
                'message': f'Error loading quote: {str(e)}'
            }
    
    @staticmethod
    def generate_approval_token(quote):
        """Generate unique approval token for quote"""
        from clientapp.models import QuoteApprovalToken, Quote
        
        # Ensure we have a quote ID (primary key)
        if not quote.pk:
            quote.save()
        
        quote_id = quote.pk
        
        # Verify quote exists in database (this ensures it's committed)
        try:
            Quote.objects.get(pk=quote_id)
        except Quote.DoesNotExist:
            raise ValueError(f"Quote with pk={quote_id} does not exist in database")
        
        token = str(uuid.uuid4())
        
        # Create or update token - use quote_id to ensure we're using the saved quote
        # Reset used status and extend expiration when updating
        approval_token, created = QuoteApprovalToken.objects.update_or_create(
            quote_id=quote_id,  # Use quote_id instead of quote object
            defaults={
                'token': token,
                'expires_at': timezone.now() + timezone.timedelta(days=30),
                'used': False,  # Reset used status if updating
                'used_at': None  # Clear used_at if updating
            }
        )
        
        # Verify the token was saved correctly
        if not approval_token.token == token:
            logger.error(f"Token mismatch! Expected {token[:10]}..., got {approval_token.token[:10]}...")
            raise ValueError("Token was not saved correctly")
        
        logger.info(f"Generated approval token for quote {quote.quote_id} (pk={quote_id}): {token[:10]}... (created={created}, expires_at={approval_token.expires_at})")
        
        return token
    
    @staticmethod
    def send_quote_via_email(quote, request=None):
        """
        Send quote to client/lead via email with approval link and PDF attachment
        Quotes can be sent to customers at any time (no costed requirement)
        
        Args:
            quote: Quote instance
            request: Django request object (for building absolute URLs)
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        from clientapp.models import Quote
        
        # Ensure quote is saved
        if not quote.pk:
            quote.save()
        
        quote_id = quote.pk
        
        # Get a fresh instance from database (ensures it's committed)
        quote = Quote.objects.get(pk=quote_id)
        
        # Check if quote can be sent to customer
        can_send, error_msg = quote.can_send_to_customer()
        if not can_send:
            logger.warning(f"Cannot send quote {quote.quote_id}: {error_msg}")
            return {
                'success': False,
                'message': error_msg
            }
        
        try:
            from django.core.mail import EmailMessage
            from clientapp.pdf_utils import QuotePDFGenerator
            
            # Generate approval token
            token = QuoteApprovalService.generate_approval_token(quote)
            
            # Build approval URL
            if request:
                approval_url = request.build_absolute_uri(
                    reverse('quote_approval', kwargs={'token': token})
                )
            else:
                # Fallback if no request
                approval_url = f"{settings.SITE_URL}/quotes/approve/{token}/"
            
            # Get recipient
            recipient_email = quote.client.email if quote.client else quote.lead.email
            recipient_name = quote.client.name if quote.client else quote.lead.name
            
            # Get line items for email display
            from clientapp.models import QuoteLineItem
            from decimal import Decimal
            
            line_items = QuoteLineItem.objects.filter(quote=quote).order_by('order', 'created_at')
            
            # Calculate totals
            if line_items.exists():
                subtotal = sum(float(item.line_total) for item in line_items)
                quote_items = [{
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_amount': float(item.line_total),
                } for item in line_items]
            else:
                # Fallback to quote totals
                subtotal = float(quote.total_amount or 0)
                quote_items = [{
                    'product_name': quote.product_name,
                    'quantity': quote.quantity,
                    'unit_price': float(quote.unit_price or 0),
                    'total_amount': float(quote.total_amount or 0),
                }]
            
            vat_amount = subtotal * 0.16 if quote.include_vat else 0
            total_amount = subtotal + vat_amount
            
            # Prepare context
            context = {
                'quote': quote,
                'quote_id': quote.quote_id,
                'recipient_name': recipient_name,
                'client_name': recipient_name,
                'approval_url': approval_url,
                'company_name': 'PrintDuka',
                'quote_items': quote_items,
                'subtotal': subtotal,
                'vat': vat_amount,
                'vat_amount': vat_amount,
                'total': total_amount,
                'total_amount': total_amount,
            }
            
            # Render email
            html_message = render_to_string('emails/quote_email.html', context)
            plain_message = render_to_string('emails/quote_email.txt', context)
            
            # Create email message
            email = EmailMessage(
                subject=f'Quote {quote.quote_id} - Awaiting Your Approval',
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            
            # Add HTML alternative
            email.content_subtype = "html"
            email.body = html_message
            
            # Generate and attach PDF
            try:
                pdf_file = QuotePDFGenerator.generate_quote_pdf(quote.quote_id, request)
                email.attach(
                    filename=f'Quote_{quote.quote_id}.pdf',
                    content=pdf_file.read(),
                    mimetype='application/pdf'
                )
                logger.info(f"PDF attached to email for quote {quote.quote_id}")
            except Exception as pdf_error:
                logger.warning(f"Could not attach PDF to email: {pdf_error}")
                # Continue sending email without PDF
            
            # Send email
            email.send(fail_silently=False)
            
            # Update quote status to "Sent to Customer"
            quote.status = 'Sent to Customer'
            quote.production_status = 'sent_to_client'
            quote.save()
            
            logger.info(f"Quote {quote.quote_id} sent to {recipient_email}")
            
            return {
                'success': True,
                'message': f'Quote sent to {recipient_email}'
            }
            
        except Exception as e:
            logger.error(f"Error sending quote email: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    @staticmethod
    def send_quote_via_whatsapp(quote):
        """
        Send quote to client/lead via WhatsApp
        Uses WhatsApp Business API or simple wa.me link
        
        Returns:
            dict: {'success': bool, 'message': str, 'whatsapp_url': str}
        """
        try:
            # Get phone number
            phone = quote.client.phone if quote.client else quote.lead.phone
            
            # Remove any non-numeric characters
            clean_phone = ''.join(filter(str.isdigit, phone))
            
            # Format message
            message = f"""
Hello! 👋

Your quote is ready for review:

*Quote #{quote.quote_id}*
Product: {quote.product_name}
Quantity: {quote.quantity}
Total: KES {quote.total_amount:,.2f}

Valid until: {quote.valid_until.strftime('%B %d, %Y')}

To view and approve your quote, please visit:
[Quote Approval Link]

Thank you for choosing PrintDuka!
            """.strip()
            
            # Create WhatsApp URL
            whatsapp_url = f"https://wa.me/{clean_phone}?text={message}"
            
            # Update quote status
            quote.status = 'Client Review'
            quote.save()
            
            return {
                'success': True,
                'message': 'WhatsApp link generated',
                'whatsapp_url': whatsapp_url
            }
            
        except Exception as e:
            logger.error(f"Error generating WhatsApp link: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    @staticmethod
    def request_price_reduction(token, discount_notes):
        """
        Request price reduction for a quote
        
        Args:
            token: Approval token
            discount_notes: Notes from customer about the discount request
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            from clientapp.models import QuoteApprovalToken, ActivityLog, Notification
            
            # Validate token - check if it exists first, then check expiration
            try:
                approval_token = QuoteApprovalToken.objects.get(token=token)
            except QuoteApprovalToken.DoesNotExist:
                logger.warning(f"Token not found in database: {token[:10]}...")
                return {
                    'success': False,
                    'message': 'Invalid approval link. Please contact us for a new link.'
                }
            
            # Check if token is expired
            if approval_token.expires_at <= timezone.now():
                logger.warning(f"Token expired: {token[:10]}..., expires_at: {approval_token.expires_at}, now: {timezone.now()}")
                return {
                    'success': False,
                    'message': 'This approval link has expired. Please contact us for a new link.'
                }
            
            quote = approval_token.quote
            
            # Create activity log
            if quote.client:
                ActivityLog.objects.create(
                    client=quote.client,
                    activity_type='Quote',
                    title=f"Price Reduction Requested - Quote {quote.quote_id}",
                    description=f"Customer requested price reduction: {discount_notes}",
                    related_quote=quote,
                    created_by=None  # Customer request
                )
            
            # Notify Account Manager
            if quote.created_by:
                Notification.objects.create(
                    recipient=quote.created_by,
                    notification_type='quote_discount_request',
                    title=f'💰 Price Reduction Request - Quote {quote.quote_id}',
                    message=f'Customer has requested a price reduction. Notes: {discount_notes}',
                    link=reverse('quote_detail', args=[quote.quote_id]),
                    related_quote_id=quote.quote_id,
                    action_url=reverse('quote_detail', args=[quote.quote_id]),
                    action_label='Review Request'
                )
            
            return {
                'success': True,
                'message': 'Your price reduction request has been submitted. We will review it and get back to you shortly.'
            }
            
        except Exception as e:
            logger.error(f"Error requesting price reduction: {e}")
            return {
                'success': False,
                'message': f'Error submitting request: {str(e)}'
            }
    
    @staticmethod
    def request_quote_adjustment(token, adjustment_notes):
        """
        Request adjustments to a quote (quantities, products, specifications, etc.)
        
        Args:
            token: Approval token
            adjustment_notes: Notes from customer about the adjustments needed
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            from clientapp.models import QuoteApprovalToken, ActivityLog, Notification
            
            # Validate token - check if it exists first, then check expiration
            try:
                approval_token = QuoteApprovalToken.objects.get(token=token)
            except QuoteApprovalToken.DoesNotExist:
                logger.warning(f"Token not found in database: {token[:10]}...")
                return {
                    'success': False,
                    'message': 'Invalid approval link. Please contact us for a new link.'
                }
            
            # Check if token is expired
            if approval_token.expires_at <= timezone.now():
                logger.warning(f"Token expired: {token[:10]}..., expires_at: {approval_token.expires_at}, now: {timezone.now()}")
                return {
                    'success': False,
                    'message': 'This approval link has expired. Please contact us for a new link.'
                }
            
            quote = approval_token.quote
            
            # Create activity log
            if quote.client:
                ActivityLog.objects.create(
                    client=quote.client,
                    activity_type='Quote',
                    title=f"Quote Adjustments Requested - Quote {quote.quote_id}",
                    description=f"Customer requested adjustments: {adjustment_notes}",
                    related_quote=quote,
                    created_by=None  # Customer request
                )
            
            # Notify Account Manager
            if quote.created_by:
                Notification.objects.create(
                    recipient=quote.created_by,
                    notification_type='quote_adjustment_request',
                    title=f'✏️ Quote Adjustments Requested - Quote {quote.quote_id}',
                    message=f'Customer has requested adjustments to the quote. Details: {adjustment_notes}',
                    link=reverse('quote_detail', args=[quote.quote_id]),
                    related_quote_id=quote.quote_id,
                    action_url=reverse('quote_detail', args=[quote.quote_id]),
                    action_label='Review & Edit Quote'
                )
            
            return {
                'success': True,
                'message': 'Your adjustment request has been submitted. We will review it and get back to you shortly with an updated quote.'
            }
            
        except Exception as e:
            logger.error(f"Error requesting quote adjustment: {e}")
            return {
                'success': False,
                'message': f'Error submitting request: {str(e)}'
            }
    
    @staticmethod
    def approve_quote(token):
        """
        Approve quote using token
        This is called when client clicks approval link
        
        Returns:
            dict: {'success': bool, 'message': str, 'quote': Quote, 'lpo': LPO, 'job': Job}
        """
        try:
            from clientapp.models import QuoteApprovalToken, LPO, LPOLineItem, Job, Quote, ActivityLog
            
            # Validate token - check if it exists first, then check expiration and usage
            try:
                approval_token = QuoteApprovalToken.objects.get(token=token)
            except QuoteApprovalToken.DoesNotExist:
                logger.warning(f"Token not found in database: {token[:10]}...")
                return {
                    'success': False,
                    'message': 'Invalid approval link. Please contact us for a new link.'
                }
            
            # Check if token is expired
            if approval_token.expires_at <= timezone.now():
                logger.warning(f"Token expired: {token[:10]}..., expires_at: {approval_token.expires_at}, now: {timezone.now()}")
                return {
                    'success': False,
                    'message': 'This approval link has expired. Please contact us for a new link.'
                }
            
            # Check if token is already used
            if approval_token.used:
                logger.warning(f"Token already used: {token[:10]}...")
                return {
                    'success': False,
                    'message': 'This approval link has already been used. Please contact us if you need assistance.'
                }
            
            quote = approval_token.quote
            
            # Check if already approved
            if quote.status == 'Approved':
                # Get existing LPO and Job if they exist
                existing_lpo = LPO.objects.filter(quote=quote).first()
                existing_job = Job.objects.filter(quote=quote).first()
                
                return {
                    'success': False,
                    'message': 'Quote already approved',
                    'quote': quote,
                    'lpo': existing_lpo,
                    'job': existing_job
                }
            
            # Approve quote
            quote.status = 'Approved'
            quote.approved_at = timezone.now()
            quote.production_status = 'in_production'
            quote.save()
            
            # Mark token as used
            approval_token.used = True
            approval_token.used_at = timezone.now()
            approval_token.save()
            
            # ===== GENERATE LPO =====
            lpo = QuoteApprovalService.generate_lpo(quote)
            
            # ===== CREATE JOB FOR PRODUCTION =====
            job = Job.objects.create(
                client=quote.client,
                quote=quote,
                job_name=f"Job for {quote.product_name}",
                job_type='printing',
                product=quote.product_name,
                quantity=quote.quantity,
                person_in_charge='Production Team',
                status='pending',
                expected_completion=quote.valid_until,
                created_by=quote.created_by
            )
            
            # Now job has been saved and has a job_number
            logger.info(f"Job {job.job_number} created for quote {quote.quote_id}")
            
            # ===== SEND NOTIFICATIONS =====
            QuoteApprovalService.send_approval_notifications(quote, lpo, job)
            
            # ===== CREATE ACTIVITY LOG =====
            if quote.client:
                ActivityLog.objects.create(
                    client=quote.client,
                    activity_type='Quote',
                    title=f"Quote {quote.quote_id} Approved by Client",
                    description=f"Client approved quote. LPO {lpo.lpo_number} and Job {job.job_number} created.",
                    related_quote=quote,
                    created_by=quote.created_by
                )
            
            logger.info(f"Quote {quote.quote_id} approved, LPO {lpo.lpo_number}, Job {job.job_number} generated")
            
            return {
                'success': True,
                'message': 'Quote approved successfully',
                'quote': quote,
                'lpo': lpo,
                'job': job
            }
            
        except Exception as e:
            logger.error(f"Error approving quote: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def generate_lpo(quote):
        """Generate LPO from approved quote"""
        from clientapp.models import LPO, LPOLineItem, Quote
        
        # Get all quote items with the same quote_id
        quote_items = Quote.objects.filter(quote_id=quote.quote_id)
        
        # Calculate totals
        subtotal = sum(item.unit_price * item.quantity for item in quote_items)
        vat_amount = subtotal * Decimal('0.16') if quote.include_vat else Decimal('0')
        total = subtotal + vat_amount
        
        # Check if LPO already exists
        existing_lpo = LPO.objects.filter(quote=quote).first()
        if existing_lpo:
            logger.info(f"LPO {existing_lpo.lpo_number} already exists for quote {quote.quote_id}")
            return existing_lpo
        
        # Create LPO
        lpo = LPO.objects.create(
            quote=quote,
            client=quote.client,
            status='approved',
            subtotal=subtotal,
            vat_amount=vat_amount,
            total_amount=total,
            payment_terms=quote.payment_terms,
            delivery_date=quote.valid_until,
            notes=quote.notes,
            created_by=quote.created_by,
            approved_at=timezone.now(),
            approved_by=quote.created_by
        )
        
        # Create line items for each quote item
        for item in quote_items:
            LPOLineItem.objects.create(
                lpo=lpo,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.unit_price * item.quantity
            )
        
        logger.info(f"LPO {lpo.lpo_number} created for quote {quote.quote_id}")
        return lpo
    
    @staticmethod
    def send_approval_notifications(quote, lpo, job):
        """Send notifications to account manager and production team"""
        from clientapp.models import Notification
        from django.contrib.auth.models import Group
        
        # Notify account manager
        if quote.created_by:
            Notification.objects.create(
                recipient=quote.created_by,
                notification_type='quote_approved',
                title=f'🎉 Quote {quote.quote_id} Approved!',
                message=f'Client approved quote. LPO {lpo.lpo_number} generated and Job {job.job_number} created.',
                link=reverse('lpo_detail', kwargs={'lpo_number': lpo.lpo_number}),
                related_quote_id=quote.quote_id,
                related_job=job
            )
        
        # Notify ALL production team members
        try:
            production_group = Group.objects.get(name='Production Team')
            for user in production_group.user_set.all():
                Notification.objects.create(
                    recipient=user,
                    notification_type='quote_approved',
                    title=f'✅ New Job: {job.job_number}',
                    message=f'Quote {quote.quote_id} approved. Job created for {quote.product_name} (x{quote.quantity}). Value: KES {quote.total_amount:,.0f}',
                    link=reverse('job_detail', kwargs={'pk': job.pk}),
                    related_quote_id=quote.quote_id,
                    related_job=job,
                    action_url=reverse('job_detail', kwargs={'pk': job.pk}),
                    action_label='View Job'
                )
        except Group.DoesNotExist:
            logger.warning("Production Team group not found")