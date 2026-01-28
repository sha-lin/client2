"""
Storefront Ecommerce Services
Handles business logic for abandoned carts, shipping calculations, and payment processing
"""
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from decimal import Decimal
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging
from .models import (
    Cart, Customer, Order, ShippingMethod, TaxConfiguration, PaymentTransaction,
    Product
)

logger = logging.getLogger(__name__)


class AbandonedCartService:
    """
    Service to identify and handle abandoned carts
    """
    
    @staticmethod
    def identify_abandoned_carts(hours_threshold=24):
        """
        Identify carts that haven't been updated in X hours
        Returns list of abandoned carts
        """
        threshold_time = timezone.now() - timedelta(hours=hours_threshold)
        
        abandoned_carts = Cart.objects.filter(
            is_active=True,
            is_abandoned=False,
            updated_at__lt=threshold_time
        ).exclude(
            items__isnull=True
        ).distinct()
        
        return abandoned_carts
    
    @staticmethod
    def mark_as_abandoned(cart):
        """Mark a cart as abandoned"""
        cart.is_abandoned = True
        cart.save(update_fields=['is_abandoned'])
    
    @staticmethod
    def send_abandoned_cart_reminder(cart):
        """
        Send reminder email/SMS to customer about abandoned cart
        TODO: Integrate with email/SMS service
        """
        if cart.customer:
            # Send email to customer.email
            pass
        # For guest carts, we'd need to store email in session or cart metadata
        return True
    
    @staticmethod
    def process_abandoned_carts():
        """
        Main method to process all abandoned carts
        Run this as a scheduled task (cron/celery)
        """
        abandoned_carts = AbandonedCartService.identify_abandoned_carts()
        
        for cart in abandoned_carts:
            AbandonedCartService.mark_as_abandoned(cart)
            AbandonedCartService.send_abandoned_cart_reminder(cart)
        
        return len(abandoned_carts)


class ShippingCalculatorService:
    """
    Service to calculate shipping costs
    Integrates with carrier APIs (G4S, DHL, Sendy) for real-time rates
    """
    
    @staticmethod
    def calculate_shipping(order, shipping_method_id=None):
        """
        Calculate shipping cost for an order
        
        Args:
            order: Order instance
            shipping_method_id: Optional shipping method ID
        
        Returns:
            dict with shipping_cost, estimated_days, carrier_info
        """
        if not order.shipping_address:
            return {
                'shipping_cost': Decimal('0'),
                'estimated_days': 0,
                'error': 'Shipping address required'
            }
        
        # If shipping method specified, use it
        if shipping_method_id:
            try:
                shipping_method = ShippingMethod.objects.get(
                    id=shipping_method_id,
                    is_active=True
                )
            except ShippingMethod.DoesNotExist:
                return {
                    'shipping_cost': Decimal('0'),
                    'estimated_days': 0,
                    'error': 'Shipping method not found'
                }
        else:
            # Use default shipping method
            shipping_method = ShippingMethod.objects.filter(
                is_active=True,
                is_default=True
            ).first()
            
            if not shipping_method:
                # Fallback to first active method
                shipping_method = ShippingMethod.objects.filter(is_active=True).first()
        
        if not shipping_method:
            return {
                'shipping_cost': Decimal('0'),
                'estimated_days': 0,
                'error': 'No shipping method available'
            }
        
        # Calculate total weight (placeholder - would need product weights)
        total_weight = Decimal('1.0')  # Placeholder
        
        # Calculate shipping cost based on method
        if shipping_method.pricing_type == 'api' and shipping_method.carrier_api_enabled:
            # Call carrier API
            shipping_cost = ShippingCalculatorService._call_carrier_api(
                shipping_method,
                order,
                total_weight
            )
        else:
            # Use configured pricing
            shipping_cost = shipping_method.calculate_shipping_cost(
                weight=total_weight,
                order_amount=order.subtotal,
                destination=order.shipping_address
            )
        
        return {
            'shipping_cost': shipping_cost,
            'estimated_days_min': shipping_method.estimated_days_min,
            'estimated_days_max': shipping_method.estimated_days_max,
            'carrier': shipping_method.carrier or 'Custom',
            'method_name': shipping_method.name,
            'shipping_method_id': shipping_method.id,
        }
    
    @staticmethod
    def _call_carrier_api(shipping_method, order, weight):
        """
        Call external carrier API for real-time shipping rates
        TODO: Implement actual API integration for G4S, DHL, Sendy
        """
        # Placeholder implementation
        # In production, this would:
        # 1. Authenticate with carrier API using shipping_method.carrier_api_config
        # 2. Send request with origin, destination, weight, dimensions
        # 3. Parse response and return shipping cost
        
        # For now, return a calculated estimate
        if shipping_method.weight_rate_per_kg:
            return weight * shipping_method.weight_rate_per_kg
        elif shipping_method.flat_rate:
            return shipping_method.flat_rate
        else:
            return Decimal('0')


class PaymentGatewayService:
    """
    Payment Gateway Integration Service
    Handles M-Pesa, Stripe, Pesapal integrations
    """
    
    @staticmethod
    def initiate_payment(order, payment_method, customer_data=None):
        """
        Initiate payment with payment gateway
        
        Args:
            order: Order instance
            payment_method: 'mpesa', 'stripe', 'pesapal'
            customer_data: Optional customer payment details
        
        Returns:
            dict with transaction_id, payment_url, or error
        """
        if payment_method == 'mpesa':
            return PaymentGatewayService._initiate_mpesa(order, customer_data)
        elif payment_method == 'stripe':
            return PaymentGatewayService._initiate_stripe(order, customer_data)
        elif payment_method == 'pesapal':
            return PaymentGatewayService._initiate_pesapal(order, customer_data)
        else:
            return {
                'success': False,
                'error': f'Unsupported payment method: {payment_method}'
            }
    
    @staticmethod
    def _initiate_mpesa(order, customer_data):
        """
        Initiate M-Pesa payment
        TODO: Integrate with M-Pesa API (Safaricom Daraja API)
        """
        # Placeholder - would call M-Pesa STK Push API
        # Returns transaction_id and payment instructions
        
        transaction_id = f"MPESA-{order.order_number}-{timezone.now().timestamp()}"
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'payment_method': 'mpesa',
            'instructions': 'Complete payment via M-Pesa STK Push',
            # 'stk_push_reference': stk_reference,
        }
    
    @staticmethod
    def _initiate_stripe(order, customer_data):
        """
        Initiate Stripe payment
        TODO: Integrate with Stripe API
        """
        # Placeholder - would create Stripe PaymentIntent
        transaction_id = f"STRIPE-{order.order_number}-{timezone.now().timestamp()}"
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'payment_method': 'stripe',
            'payment_url': f'/payment/stripe/{transaction_id}',  # Redirect URL
        }
    
    @staticmethod
    def _initiate_pesapal(order, customer_data):
        """
        Initiate Pesapal payment
        TODO: Integrate with Pesapal API
        """
        # Placeholder - would create Pesapal order
        transaction_id = f"PESAPAL-{order.order_number}-{timezone.now().timestamp()}"
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'payment_method': 'pesapal',
            'payment_url': f'/payment/pesapal/{transaction_id}',  # Redirect URL
        }
    
    @staticmethod
    def verify_payment(transaction_id, payment_method):
        """
        Verify payment status with payment gateway
        Called via webhook or polling
        """
        try:
            payment_transaction = PaymentTransaction.objects.get(
                transaction_id=transaction_id,
                payment_method=payment_method
            )
        except PaymentTransaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment transaction not found'
            }
        
        # TODO: Call gateway API to verify payment status
        # For now, return current status
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': payment_transaction.status,
            'amount': float(payment_transaction.amount),
        }
    
    @staticmethod
    def handle_payment_webhook(payment_method, webhook_data):
        """
        Handle payment gateway webhook
        Updates order and payment transaction status
        """
        transaction_id = webhook_data.get('transaction_id') or webhook_data.get('reference')
        
        try:
            payment_transaction = PaymentTransaction.objects.get(
                transaction_id=transaction_id,
                payment_method=payment_method
            )
        except PaymentTransaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment transaction not found'
            }
        
        # Update payment status based on webhook data
        webhook_status = webhook_data.get('status', '').lower()
        
        if webhook_status in ['completed', 'success', 'paid']:
            payment_transaction.status = 'completed'
            payment_transaction.completed_at = timezone.now()
            payment_transaction.gateway_response = webhook_data
            payment_transaction.save()
            
            # Update order
            order = payment_transaction.order
            order.payment_status = 'completed'
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save()
            
            return {
                'success': True,
                'order_number': order.order_number,
                'status': 'completed'
            }
        elif webhook_status in ['failed', 'cancelled']:
            payment_transaction.status = 'failed'
            payment_transaction.failure_reason = webhook_data.get('message', 'Payment failed')
            payment_transaction.gateway_response = webhook_data
            payment_transaction.save()
            
            return {
                'success': False,
                'status': 'failed',
                'message': payment_transaction.failure_reason
            }
        
        return {
            'success': False,
            'error': 'Unknown webhook status'
        }


class InventoryService:
    """
    Inventory/Stock Management Service
    Handles soft-locking inventory during checkout
    """
    
    @staticmethod
    def check_availability(product, quantity):
        """
        Check if product/material is available in required quantity
        TODO: Integrate with actual inventory system
        """
        # Placeholder - would check Material/Inventory model
        # For now, assume all products are available
        return {
            'available': True,
            'quantity_available': 999999,  # Placeholder
            'can_fulfill': True,
        }
    
    @staticmethod
    def reserve_inventory(order):
        """
        Reserve inventory for an order (soft-lock)
        Prevents overselling
        """
        # TODO: Implement inventory reservation
        # Would create InventoryReservation records
        return True
    
    @staticmethod
    def release_inventory(order):
        """
        Release reserved inventory (if order cancelled)
        """
        # TODO: Implement inventory release
        return True


class CrossSellService:
    """
    Cross-sell and Up-sell Engine
    Suggests related products based on purchase history
    """
    
    @staticmethod
    def get_related_products(product, limit=5):
        """
        Get related products for cross-selling
        Based on:
        - Same category
        - Frequently bought together
        - Similar products
        """
        # Get products in same category
        related = Product.objects.filter(
            primary_category=product.primary_category,
            status='published',
            is_active=True
        ).exclude(id=product.id)[:limit]
        
        return related
    
    @staticmethod
    def get_frequently_bought_together(product, limit=5):
        """
        Get products frequently bought together
        Based on order history
        """
        # Get orders containing this product
        orders_with_product = Order.objects.filter(
            items__product=product,
            status__in=['paid', 'processing', 'delivered']
        ).values_list('id', flat=True)
        
        # Get other products in those orders
        from django.db.models import Count
        related_products = Product.objects.filter(
            order_items__order_id__in=orders_with_product
        ).exclude(
            id=product.id
        ).annotate(
            frequency=Count('order_items')
        ).order_by('-frequency')[:limit]
        
        return related_products


# ============================================================================
# EMAIL SERVICE
# ============================================================================

class EmailService:
    """Service to send emails to customers and staff"""
    
    @staticmethod
    def send_registration_email(user, customer):
        """Send welcome email to new customer"""
        try:
            context = {
                'user_name': user.first_name or user.username,
                'customer_id': customer.customer_id,
                'company_name': settings.COMPANY_NAME,
                'company_email': settings.COMPANY_EMAIL,
                'company_phone': settings.COMPANY_PHONE,
            }
            
            html_message = render_to_string(
                'emails/registration_welcome.html',
                context
            )
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=f"Welcome to {settings.COMPANY_NAME}!",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Registration email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send registration email: {str(e)}")
            return False
    
    @staticmethod
    def send_email_verification(user, verification_token):
        """Send email verification link to customer"""
        try:
            verify_link = f"{settings.STOREFRONT_URL}/verify-email?token={verification_token}"
            
            context = {
                'user_name': user.first_name or user.username,
                'verify_link': verify_link,
                'company_name': settings.COMPANY_NAME,
            }
            
            html_message = render_to_string(
                'emails/email_verification.html',
                context
            )
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=f"Verify your email - {settings.COMPANY_NAME}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Verification email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False
    
    @staticmethod
    def send_estimate_shared_email(estimate, recipient_email, share_link):
        """Send estimate to customer or sales team"""
        try:
            context = {
                'customer_name': estimate.customer_name,
                'estimate_id': estimate.estimate_id,
                'share_link': share_link,
                'total_amount': estimate.total_amount,
                'company_name': settings.COMPANY_NAME,
                'company_phone': settings.COMPANY_PHONE,
            }
            
            html_message = render_to_string(
                'emails/estimate_shared.html',
                context
            )
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=f"Your Estimate {estimate.estimate_id} is Ready",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Estimate {estimate.estimate_id} shared with {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send estimate email: {str(e)}")
            return False
    
    @staticmethod
    def send_inquiry_confirmation(message):
        """Send confirmation email for customer inquiry"""
        try:
            context = {
                'customer_name': message.customer_name,
                'message_id': message.message_id,
                'message_type': message.message_type,
                'company_name': settings.COMPANY_NAME,
                'company_email': settings.COMPANY_EMAIL,
            }
            
            html_message = render_to_string(
                'emails/inquiry_confirmation.html',
                context
            )
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=f"We received your inquiry - {settings.COMPANY_NAME}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message.customer_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Inquiry confirmation sent to {message.customer_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send inquiry confirmation: {str(e)}")
            return False
    
    @staticmethod
    def notify_sales_team_inquiry(message):
        """Notify sales team of new customer inquiry"""
        try:
            sales_team_email = settings.SALES_TEAM_EMAIL
            
            context = {
                'customer_name': message.customer_name,
                'customer_email': message.customer_email,
                'customer_phone': message.customer_phone,
                'message_id': message.message_id,
                'message_type': message.get_message_type_display(),
                'message_content': message.message_content,
                'received_at': message.created_at,
            }
            
            html_message = render_to_string(
                'emails/sales_inquiry_alert.html',
                context
            )
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=f"New {message.get_message_type_display()} from {message.customer_name}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sales_team_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Sales team notified of inquiry {message.message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to notify sales team: {str(e)}")
            return False


# ============================================================================
# SMS & WHATSAPP SERVICE
# ============================================================================

class MessagingService:
    """Service to send SMS and WhatsApp messages"""
    
    @staticmethod
    def send_otp_sms(phone_number, otp_code):
        """Send OTP via SMS for phone verification"""
        try:
            import requests
            
            # Using Africastalking as example
            message = f"Your {settings.COMPANY_NAME} verification code is: {otp_code}. Valid for 10 minutes."
            
            url = "https://api.sandbox.africastalking.com/version1/messaging"
            headers = {
                "Authorization": f"Bearer {settings.AFRICASTALKING_API_KEY}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            payload = {
                "username": settings.AFRICASTALKING_USERNAME,
                "message": message,
                "recipients": phone_number,
            }
            
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            logger.info(f"OTP SMS sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP SMS: {str(e)}")
            return False
    
    @staticmethod
    def send_whatsapp_message(phone_number, message_text, template_name=None):
        """Send WhatsApp message to customer"""
        try:
            import requests
            
            # Using Africastalking WhatsApp API
            url = "https://api.sandbox.africastalking.com/version1/messaging"
            headers = {
                "Authorization": f"Bearer {settings.AFRICASTALKING_API_KEY}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            payload = {
                "username": settings.AFRICASTALKING_USERNAME,
                "message": message_text,
                "recipients": phone_number,
                "channel": "WhatsApp",
            }
            
            # If using template
            if template_name:
                payload["template_id"] = template_name
            
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            logger.info(f"WhatsApp message sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return False
    
    @staticmethod
    def send_estimate_via_whatsapp(estimate, phone_number, share_link):
        """Send estimate share link via WhatsApp"""
        try:
            message = (
                f"Hi {estimate.customer_name}!\n\n"
                f"Your estimate {estimate.estimate_id} is ready.\n"
                f"Total: KES {estimate.total_amount:,.2f}\n\n"
                f"View your estimate: {share_link}\n\n"
                f"Thank you!"
            )
            
            return MessagingService.send_whatsapp_message(phone_number, message)
        except Exception as e:
            logger.error(f"Failed to send estimate via WhatsApp: {str(e)}")
            return False


# ============================================================================
# TAX SERVICE
# ============================================================================

class TaxService:
    """Service to calculate and manage taxes"""
    
    # Default tax rates (can be overridden in settings)
    DEFAULT_TAX_RATES = {
        'KE': Decimal('18.00'),  # Kenya VAT
        'UG': Decimal('18.00'),  # Uganda VAT
        'TZ': Decimal('18.00'),  # Tanzania VAT
        'RW': Decimal('18.00'),  # Rwanda VAT
        'ZA': Decimal('15.00'),  # South Africa VAT
        'US': Decimal('0.00'),   # US (varies by state)
    }
    
    @staticmethod
    def get_tax_rate(country_code='KE'):
        """Get applicable tax rate for country"""
        try:
            # Try to get from settings first
            tax_rate = getattr(settings, f'TAX_RATE_{country_code}', None)
            if tax_rate:
                return Decimal(str(tax_rate))
        except:
            pass
        
        # Fall back to default rates
        return TaxService.DEFAULT_TAX_RATES.get(country_code, Decimal('18.00'))
    
    @staticmethod
    def calculate_tax(subtotal, country_code='KE'):
        """Calculate tax amount"""
        tax_rate = TaxService.get_tax_rate(country_code)
        tax_amount = subtotal * (tax_rate / Decimal('100'))
        return tax_amount.quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_total_with_tax(subtotal, country_code='KE'):
        """Calculate total including tax"""
        tax_amount = TaxService.calculate_tax(subtotal, country_code)
        total = subtotal + tax_amount
        return total.quantize(Decimal('0.01')), tax_amount
    
    @staticmethod
    def get_tax_breakdown(subtotal, country_code='KE'):
        """Get detailed tax breakdown"""
        tax_rate = TaxService.get_tax_rate(country_code)
        tax_amount = TaxService.calculate_tax(subtotal, country_code)
        total = subtotal + tax_amount
        
        return {
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total,
            'country_code': country_code,
        }


# ============================================================================
# CHATBOT INTENT MATCHING SERVICE
# ============================================================================

class ChatbotService:
    """Service to handle chatbot AI and intent matching"""
    
    # Simple rule-based intent patterns
    INTENT_PATTERNS = {
        'pricing': ['price', 'cost', 'how much', 'expensive', 'quote', 'estimate'],
        'product_info': ['product', 'feature', 'specification', 'material', 'color', 'size'],
        'turnaround': ['how long', 'delivery', 'turnaround', 'timeline', 'rush', 'expedited'],
        'ordering': ['order', 'buy', 'purchase', 'place order', 'checkout'],
        'support': ['help', 'issue', 'problem', 'error', 'broken', 'not working'],
        'greeting': ['hi', 'hello', 'hey', 'greetings'],
        'farewell': ['bye', 'goodbye', 'thanks', 'thank you'],
    }
    
    @staticmethod
    def detect_intent(message_text):
        """Detect customer intent from message"""
        message_lower = message_text.lower()
        intent_scores = {}
        
        for intent, keywords in ChatbotService.INTENT_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            # Return intent with highest score
            detected_intent = max(intent_scores, key=intent_scores.get)
            return detected_intent
        
        return 'general'
    
    @staticmethod
    def generate_response(intent, message_text):
        """Generate response based on detected intent"""
        responses = {
            'greeting': "Hello! Welcome to {company_name}. How can I help you today?",
            'pricing': "I'd be happy to help with pricing! Could you tell me more about what you need? You can also create an estimate quote in our quote builder.",
            'product_info': "We have a wide range of {category} products. Please visit our product catalog to browse our full selection with detailed specifications.",
            'turnaround': "Our standard turnaround time is {standard_days} days. We also offer rush ({rush_days} days) and expedited ({expedited_days} day) options.",
            'ordering': "You can easily create an estimate quote in our Quote Builder, adjust quantities and options, and then share it with our sales team.",
            'support': "I'm sorry you're experiencing an issue. Please describe the problem, and I'll connect you with our support team or you can call {company_phone}.",
            'farewell': "Thank you for contacting {company_name}. Have a great day!",
            'general': "Thank you for your message. I'm here to help! You can also reach our sales team at {company_email} or {company_phone}.",
        }
        
        response_template = responses.get(intent, responses['general'])
        
        # Format response with company details
        response = response_template.format(
            company_name=settings.COMPANY_NAME,
            company_email=settings.COMPANY_EMAIL,
            company_phone=settings.COMPANY_PHONE,
            category='printing',  # Default category
            standard_days=getattr(settings, 'TURNAROUND_STANDARD_DAYS', 7),
            rush_days=getattr(settings, 'TURNAROUND_RUSH_DAYS', 3),
            expedited_days=getattr(settings, 'TURNAROUND_EXPEDITED_DAYS', 1),
        )
        
        return response
    
    @staticmethod
    def get_suggested_actions(intent):
        """Get suggested actions based on intent"""
        suggestions = {
            'greeting': ['View Products', 'Create Quote', 'Learn More'],
            'pricing': ['Create Quote', 'View Products', 'Contact Sales'],
            'product_info': ['View All Products', 'Create Quote', 'See Specifications'],
            'turnaround': ['Create Quote', 'View Turnaround Options', 'Contact Sales'],
            'ordering': ['Go to Quote Builder', 'Browse Products', 'Chat with Sales'],
            'support': ['Contact Support', 'Call Us', 'Browse FAQ'],
            'farewell': ['Visit Products', 'Create Quote', 'Browse FAQ'],
            'general': ['Browse Catalog', 'Create Quote', 'Contact Sales'],
        }
        
        return suggestions.get(intent, suggestions['general'])

