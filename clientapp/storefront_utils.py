"""
Storefront Utility Functions
Price calculations, ID generation, messaging, email templates
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PRICE CALCULATIONS
# ============================================================================

class PriceCalculator:
    """Calculate prices for products with customizations and turnarounds"""
    
    @staticmethod
    def calculate_line_total(
        product_id: str,
        quantity: int,
        turnaround_time: str = 'standard',
        properties: Dict = None,
        product_obj=None
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate unit price and line total for a product
        
        Args:
            product_id: Product ID
            quantity: Quantity ordered
            turnaround_time: 'standard', 'rush', 'expedited'
            properties: Custom properties JSON
            product_obj: Optional pre-loaded product object
            
        Returns:
            Tuple of (unit_price, surcharge, line_total)
        """
        if not product_obj:
            from clientapp.models import StorefrontProduct
            try:
                product_obj = StorefrontProduct.objects.get(product_id=product_id)
            except StorefrontProduct.DoesNotExist:
                raise ValueError(f"Product {product_id} not found")
        
        # Get unit price based on quantity tier
        unit_price = product_obj.get_price_for_quantity(quantity)
        
        # Calculate turnaround surcharge
        surcharge = Decimal('0.00')
        if turnaround_time == 'rush':
            surcharge = product_obj.turnaround_rush_surcharge * quantity
        elif turnaround_time == 'expedited':
            surcharge = product_obj.turnaround_expedited_surcharge * quantity
        
        # Calculate line total
        line_total = (unit_price * quantity) + surcharge
        
        return unit_price, surcharge, line_total
    
    @staticmethod
    def calculate_quote_totals(
        line_items: List[Dict],
        tax_rate: Decimal = None
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate quote subtotal, tax, and total
        
        Args:
            line_items: List of {line_total, ...}
            tax_rate: Tax percentage (e.g., Decimal('18.00') for 18%)
            
        Returns:
            Tuple of (subtotal, tax_amount, total)
        """
        subtotal = sum(Decimal(str(item['line_total'])) for item in line_items)
        
        if not tax_rate:
            tax_rate = Decimal('18.00')  # Default 18% tax rate
        
        tax_amount = subtotal * (tax_rate / Decimal('100'))
        total = subtotal + tax_amount
        
        return subtotal, tax_amount, total


# ============================================================================
# ID GENERATION
# ============================================================================

class IDGenerator:
    """Generate unique IDs for orders, quotes, messages"""
    
    @staticmethod
    def generate_estimate_id() -> str:
        """Generate estimate ID: EST-YYYY-XXXXX"""
        from clientapp.models import EstimateQuote
        from django.utils import timezone
        
        year = timezone.now().year
        last = EstimateQuote.objects.filter(
            estimate_id__startswith=f'EST-{year}'
        ).order_by('-estimate_id').first()
        
        if last:
            num = int(last.estimate_id.split('-')[-1]) + 1
        else:
            num = 1
        
        return f'EST-{year}-{str(num).zfill(5)}'
    
    @staticmethod
    def generate_customer_id() -> str:
        """Generate customer ID: CUST-YYYY-XXXXX"""
        from clientapp.models import StorefrontCustomer
        from django.utils import timezone
        
        year = timezone.now().year
        last = StorefrontCustomer.objects.filter(
            customer_id__startswith=f'CUST-{year}'
        ).order_by('-customer_id').first()
        
        if last:
            num = int(last.customer_id.split('-')[-1]) + 1
        else:
            num = 1
        
        return f'CUST-{year}-{str(num).zfill(5)}'
    
    @staticmethod
    def generate_message_id() -> str:
        """Generate message ID: MSG-YYYY-XXXXX"""
        from clientapp.models import StorefrontMessage
        from django.utils import timezone
        
        year = timezone.now().year
        last = StorefrontMessage.objects.filter(
            message_id__startswith=f'MSG-{year}'
        ).order_by('-message_id').first()
        
        if last:
            num = int(last.message_id.split('-')[-1]) + 1
        else:
            num = 1
        
        return f'MSG-{year}-{str(num).zfill(5)}'


# ============================================================================
# EMAIL UTILITIES
# ============================================================================

class EmailService:
    """Send transactional emails"""
    
    @staticmethod
    def send_registration_email(user_email: str, verification_token: str = '', **kwargs):
        """Send email verification link or other notifications"""
        # Accept flexible kwargs for signal compatibility
        subject = kwargs.get('subject', "Verify Your Email - PrintDuka Storefront")
        
        context = {
            'email': user_email,
            'verification_token': verification_token,
            'verification_link': f"{settings.STOREFRONT_URL}/verify/{verification_token}"
        }
        
        html_message = render_to_string('emails/registration_verification.html', context)
        text_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
    
    @staticmethod
    def send_estimate_shared_notification(
        customer_name: str,
        customer_email: str,
        estimate_id: str,
        share_token: str
    ):
        """Send notification when estimate is shared with AM"""
        subject = f"Your Quote Request - {estimate_id}"
        
        context = {
            'customer_name': customer_name,
            'estimate_id': estimate_id,
            'share_link': f"{settings.STOREFRONT_URL}/quotes/{share_token}",
            'support_email': settings.SUPPORT_EMAIL
        }
        
        html_message = render_to_string('emails/estimate_shared.html', context)
        text_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
    
    @staticmethod
    def send_quote_approved_notification(
        customer_email: str,
        quote_id: str,
        total_amount: Decimal
    ):
        """Send notification when customer approves quote"""
        subject = f"Quote Approved - {quote_id}"
        
        context = {
            'quote_id': quote_id,
            'total_amount': str(total_amount),
            'portal_link': f"{settings.CLIENT_PORTAL_URL}/quotes/{quote_id}"
        }
        
        html_message = render_to_string('emails/quote_approved.html', context)
        text_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
    
    @staticmethod
    def send_invoice_notification(
        customer_email: str,
        invoice_number: str,
        amount: Decimal,
        due_date: datetime
    ):
        """Send invoice to customer"""
        subject = f"Invoice {invoice_number}"
        
        context = {
            'invoice_number': invoice_number,
            'amount': str(amount),
            'due_date': due_date.strftime('%Y-%m-%d'),
            'payment_link': f"{settings.CLIENT_PORTAL_URL}/invoices/{invoice_number}"
        }
        
        html_message = render_to_string('emails/invoice_notification.html', context)
        text_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()


# ============================================================================
# WHATSAPP INTEGRATION
# ============================================================================

class WhatsAppService:
    """Send WhatsApp messages via Africastalking or Twilio"""
    
    @staticmethod
    def send_message(
        phone_number: str,
        message_text: str,
        media_url: Optional[str] = None
    ) -> bool:
        """
        Send WhatsApp message
        
        Args:
            phone_number: Recipient phone number (with country code)
            message_text: Message content
            media_url: Optional image/document URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # TODO: Implement using Africastalking or Twilio
            # For now, just log
            logger.info(f"WhatsApp message to {phone_number}: {message_text}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return False
    
    @staticmethod
    def create_share_link(message: str, phone_number: str) -> str:
        """Create WhatsApp share link"""
        from urllib.parse import quote
        return f"https://wa.me/{phone_number}?text={quote(message)}"
    
    @staticmethod
    def send_estimate_shared_alert(
        sales_phone: str,
        customer_name: str,
        customer_phone: str,
        estimate_id: str,
        share_token: str
    ) -> bool:
        """Send alert to sales team when estimate is shared"""
        message = f"""
New quote request from {customer_name}
📱 {customer_phone}
📄 Quote ID: {estimate_id}

View: {settings.STOREFRONT_URL}/quotes/{share_token}
        """.strip()
        
        return WhatsAppService.send_message(sales_phone, message)


# ============================================================================
# CHATBOT UTILITIES
# ============================================================================

class ChatbotService:
    """Chatbot message processing and response generation"""
    
    INTENTS = {
        'product_inquiry': {
            'keywords': ['price', 'cost', 'how much', 'product', 'pricing'],
            'handler': 'handle_product_inquiry'
        },
        'quote_creation': {
            'keywords': ['quote', 'estimate', 'order', 'buy'],
            'handler': 'handle_quote_creation'
        },
        'contact_sales': {
            'keywords': ['sales', 'speak to', 'call me', 'representative'],
            'handler': 'handle_contact_sales'
        },
        'order_tracking': {
            'keywords': ['track', 'order', 'status', 'delivery', 'where is'],
            'handler': 'handle_order_tracking'
        },
        'faq': {
            'keywords': ['how', 'why', 'what', 'can i', 'do you'],
            'handler': 'handle_faq'
        }
    }
    
    @staticmethod
    def detect_intent(message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        for intent, config in ChatbotService.INTENTS.items():
            for keyword in config['keywords']:
                if keyword in message_lower:
                    return intent
        
        return 'general'
    
    @staticmethod
    def handle_product_inquiry(message: str) -> Dict:
        """Handle product inquiry"""
        return {
            'response': """I'd be happy to help with pricing! 
            
Which product category interests you?
• Business Cards
• Flyers & Brochures
• T-Shirts
• Custom Products

Or you can browse our full catalog at storefront.com/products""",
            'action': 'show_products',
            'suggestions': ['View Business Cards', 'View Custom Products', 'Create Quote']
        }
    
    @staticmethod
    def handle_quote_creation(message: str) -> Dict:
        """Handle quote creation request"""
        return {
            'response': """Great! I can help you create a quote.

Let me open our quote creation form for you. You'll be able to:
✓ Select products
✓ Enter quantities
✓ Customize options
✓ Review pricing
✓ Share with our sales team or save for later""",
            'action': 'open_quote_form',
            'suggestions': ['Create Quote', 'Browse Products']
        }
    
    @staticmethod
    def handle_contact_sales(message: str) -> Dict:
        """Handle contact sales request"""
        return {
            'response': """You can reach our sales team through:

📧 Email: sales@printduka.com
💬 WhatsApp: +254 701 234 567
☎️ Phone: +254 701 234 567
💼 Website: Schedule a call at printduka.com/contact

How would you like to connect?""",
            'action': 'show_contact_options',
            'suggestions': [
                'Send Email',
                'WhatsApp Chat',
                'Request Call Back'
            ]
        }
    
    @staticmethod
    def handle_order_tracking(message: str) -> Dict:
        """Handle order tracking request"""
        return {
            'response': """To track your order, please log in to your account.

If you don't have an account yet, you can:
1. Register on our storefront
2. Use your order email
3. Provide your quote/order number

Login: storefront.com/login""",
            'action': 'redirect_login',
            'suggestions': ['Login', 'Register', 'Contact Sales']
        }
    
    @staticmethod
    def handle_faq(message: str) -> Dict:
        """Handle FAQ questions"""
        faqs = {
            'turnaround': "We offer 3 turnaround options:\n• Standard: 7 days\n• Rush: 3 days (+1000 KES/item)\n• Expedited: 1 day (+2500 KES/item)",
            'payment': "We accept: Prepaid, Net 7/15/30 days, Bank transfer, Card, M-Pesa",
            'delivery': "We offer: Pickup, Courier (Nairobi), Courier (Nationwide)",
            'minimum': "Minimum order depends on product. Most products start at 100 units.",
            'customization': "Most of our products are fully customizable. Contact sales for special requirements."
        }
        
        # Simple FAQ matching
        message_lower = message.lower()
        
        if 'turnaround' in message_lower or 'how long' in message_lower:
            return {'response': faqs['turnaround'], 'action': 'show_faq'}
        elif 'payment' in message_lower:
            return {'response': faqs['payment'], 'action': 'show_faq'}
        elif 'delivery' in message_lower or 'shipping' in message_lower:
            return {'response': faqs['delivery'], 'action': 'show_faq'}
        elif 'minimum' in message_lower:
            return {'response': faqs['minimum'], 'action': 'show_faq'}
        elif 'custom' in message_lower:
            return {'response': faqs['customization'], 'action': 'show_faq'}
        
        return {
            'response': "I can help with common questions. Ask me about turnaround times, payment options, delivery, or customization.",
            'action': 'show_faq_options',
            'suggestions': [
                'Turnaround times',
                'Payment options',
                'Delivery methods',
                'Minimum orders'
            ]
        }
    
    @staticmethod
    def process_message(message: str) -> Dict:
        """Process user message and generate response"""
        intent = ChatbotService.detect_intent(message)
        
        handler_name = ChatbotService.INTENTS.get(intent, {}).get('handler', 'handle_faq')
        handler = getattr(ChatbotService, handler_name, ChatbotService.handle_faq)
        
        return handler(message)


# ============================================================================
# NOTIFICATION SERVICE
# ============================================================================

class NotificationService:
    """Send notifications via multiple channels"""
    
    @staticmethod
    def notify_estimate_shared(
        estimate_id: str,
        customer_name: str,
        customer_phone: str
    ):
        """Notify sales team when customer shares estimate"""
        message = f"New quote request from {customer_name} ({customer_phone})"
        
        # Send WhatsApp to sales
        try:
            WhatsAppService.send_estimate_shared_alert(
                sales_phone=settings.SALES_WHATSAPP_NUMBER,
                customer_name=customer_name,
                customer_phone=customer_phone,
                estimate_id=estimate_id,
                share_token="token_here"
            )
        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification: {e}")
        
        # Send email to sales
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=f"New Quote Request: {estimate_id}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SALES_EMAIL],
                fail_silently=False
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    @staticmethod
    def notify_quote_approved(
        quote_id: str,
        customer_email: str
    ):
        """Notify AM when quote is approved"""
        try:
            EmailService.send_quote_approved_notification(
                customer_email=customer_email,
                quote_id=quote_id,
                total_amount=Decimal('0.00')  # Get from quote object
            )
        except Exception as e:
            logger.error(f"Failed to send quote approval notification: {e}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tax_rate() -> Decimal:
    """Get configured tax rate from settings"""
    return Decimal(str(getattr(settings, 'STOREFRONT_TAX_RATE', '18.00')))


def format_currency(amount: Decimal, currency: str = 'KES') -> str:
    """Format amount as currency"""
    if currency == 'KES':
        return f"KES {amount:,.2f}"
    return f"{currency} {amount:,.2f}"


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    import re
    # Simple validation: at least 7 digits
    cleaned = re.sub(r'\D', '', phone)
    return len(cleaned) >= 7


def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
