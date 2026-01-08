"""
Storefront Ecommerce Services
Handles business logic for abandoned carts, shipping calculations, and payment processing
"""
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from decimal import Decimal
from .models import (
    Cart, Customer, Order, ShippingMethod, TaxConfiguration, PaymentTransaction,
    Product
)


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

