"""
Canonical Pricing Engine - Single Source of Truth for Pricing
Deterministic, stateless pricing calculation used by carts, quotes, orders, and admin
"""
from decimal import Decimal
from typing import Dict, Optional, Any
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import (
    Product,
    ShippingMethod,
    TaxConfiguration,
    TurnAroundTime,
    Coupon,
    resolve_unit_price,
)


class PricingEngine:
    """
    Canonical pricing engine - NO DB writes, deterministic calculations
    Used by: carts, quotes, orders, admin recalculation
    """
    
    @staticmethod
    def calculate(
        product_id: int,
        quantity: int,
        variables: Optional[Dict[str, Any]] = None,
        turnaround_id: Optional[int] = None,
        shipping_method_id: Optional[int] = None,
        coupon_code: Optional[str] = None,
        customer_type: str = "B2C",
        currency: str = "KES",
        customer_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate complete pricing breakdown
        
        Args:
            product_id: Product ID
            quantity: Quantity ordered
            variables: Product variables dict (e.g., {"paper": "300gsm", "finish": "matte"})
            turnaround_id: Turnaround time ID
            shipping_method_id: Shipping method ID
            coupon_code: Coupon code
            customer_type: B2C or B2B
            currency: Currency code (default KES)
            customer_id: Optional customer ID for customer-specific pricing
        
        Returns:
            Dict with pricing breakdown:
            {
                "base_price": Decimal,
                "variable_price": Decimal,
                "turnaround_price": Decimal,
                "discounts": Decimal,
                "subtotal": Decimal,
                "tax": Decimal,
                "shipping": Decimal,
                "total": Decimal,
                "margin": Decimal,
            }
        """
        variables = variables or {}
        
        # Get product
        try:
            product = Product.objects.select_related('pricing').get(pk=product_id)
        except Product.DoesNotExist:
            raise ValidationError(f"Product {product_id} not found")
        
        # Calculate base price
        base_price = resolve_unit_price(product, variables, quantity)
        base_total = base_price * quantity
        
        # Calculate variable pricing (for semi-customizable products)
        variable_price = Decimal('0')
        if product.customization_level in ['semi_customizable', 'fully_customizable']:
            variable_price = PricingEngine._calculate_variable_pricing(
                product, variables, quantity
            )
        
        # Calculate turnaround pricing
        turnaround_price = Decimal('0')
        if turnaround_id:
            turnaround_price = PricingEngine._calculate_turnaround_pricing(
                product, turnaround_id, quantity
            )
        
        # Calculate subtotal (before discounts, tax, shipping)
        subtotal = base_total + variable_price + turnaround_price
        
        # Apply discounts (coupons, promotions)
        discounts = Decimal('0')
        if coupon_code:
            discounts = PricingEngine._calculate_discounts(
                product, quantity, subtotal, coupon_code, customer_id
            )
        
        # Calculate shipping
        shipping = Decimal('0')
        if shipping_method_id:
            shipping = PricingEngine._calculate_shipping(
                product, quantity, shipping_method_id, subtotal - discounts
            )
        
        # Calculate tax
        tax = Decimal('0')
        tax_config = TaxConfiguration.objects.filter(
            is_active=True
        ).first()
        if tax_config:
            # Check if tax applies to customer type
            if (customer_type == 'B2B' and tax_config.applies_to_b2b) or \
               (customer_type == 'B2C' and tax_config.applies_to_b2c):
                tax = PricingEngine._calculate_tax(
                    subtotal - discounts, tax_config
                )
        
        # Calculate total
        total = subtotal - discounts + tax + shipping
        
        # Calculate margin (if product has cost data)
        margin = Decimal('0')
        if hasattr(product, 'pricing') and product.pricing.base_cost:
            cost = product.pricing.base_cost * quantity
            margin = total - cost - variable_price - turnaround_price
        
        return {
            "base_price": base_total,
            "variable_price": variable_price,
            "turnaround_price": turnaround_price,
            "discounts": discounts,
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "total": total,
            "margin": margin,
            "currency": currency,
        }
    
    @staticmethod
    def _calculate_variable_pricing(
        product: Product,
        variables: Dict[str, Any],
        quantity: int
    ) -> Decimal:
        """Calculate additional price from product variables"""
        if not variables:
            return Decimal('0')
        
        total_variable_price = Decimal('0')
        
        # Get product variables and their options
        for var_name, var_value in variables.items():
            try:
                product_var = product.variables.get(name=var_name)
                option = product_var.options.get(value=var_value)
                
                # Calculate price based on pricing type
                if option.price_modifier:
                    if product_var.pricing_type == 'fixed':
                        total_variable_price += option.price_modifier
                    elif product_var.pricing_type == 'increment':
                        total_variable_price += option.price_modifier * quantity
                    elif product_var.pricing_type == 'percentage':
                        # Percentage of base price
                        base = resolve_unit_price(product, None, quantity)
                        total_variable_price += base * (option.price_modifier / Decimal('100'))
            except Exception:
                # Variable or option not found, skip
                continue
        
        return total_variable_price
    
    @staticmethod
    def _calculate_turnaround_pricing(
        product: Product,
        turnaround_id: int,
        quantity: int
    ) -> Decimal:
        """Calculate turnaround time upcharge"""
        try:
            turnaround = TurnAroundTime.objects.get(pk=turnaround_id, product=product)
            if turnaround.price_modifier:
                # TurnAroundTime model doesn't have modifier_type, assume fixed per unit
                return turnaround.price_modifier * quantity
        except TurnAroundTime.DoesNotExist:
            pass
        
        return Decimal('0')
    
    @staticmethod
    def _calculate_discounts(
        product: Product,
        quantity: int,
        subtotal: Decimal,
        coupon_code: str,
        customer_id: Optional[int] = None
    ) -> Decimal:
        """Calculate discount from coupon"""
        try:
            coupon = Coupon.objects.get(
                code=coupon_code,
                is_active=True
            )
            
            # Check if coupon is valid
            if not PricingEngine._is_coupon_valid(coupon, product, quantity, subtotal, customer_id):
                return Decimal('0')
            
            # Calculate discount
            if coupon.discount_type == 'percentage':
                discount = subtotal * (coupon.discount_value / Decimal('100'))
            elif coupon.discount_type == 'fixed':
                discount = coupon.discount_value
            elif coupon.discount_type == 'free_shipping':
                # Handled separately in shipping calculation
                return Decimal('0')
            else:
                return Decimal('0')
            
            # Apply maximum discount if set
            if coupon.maximum_discount_amount and discount > coupon.maximum_discount_amount:
                discount = coupon.maximum_discount_amount
            
            return discount
        except Coupon.DoesNotExist:
            return Decimal('0')
    
    @staticmethod
    def _is_coupon_valid(
        coupon: Coupon,
        product: Product,
        quantity: int,
        subtotal: Decimal,
        customer_id: Optional[int] = None
    ) -> bool:
        """Validate coupon eligibility"""
        from django.utils import timezone
        
        # Check active status
        if not coupon.is_active:
            return False
        
        # Check expiry
        if coupon.expires_at and coupon.expires_at < timezone.now():
            return False
        
        # Check minimum order amount
        if coupon.minimum_order_amount and subtotal < coupon.minimum_order_amount:
            return False
        
        # Check usage limits
        if coupon.usage_limit:
            usage_count = coupon.orders.count() if hasattr(coupon, 'orders') else 0
            if usage_count >= coupon.usage_limit:
                return False
        
        # Check per-customer limit
        if coupon.usage_limit_per_customer and customer_id:
            customer_usage = coupon.orders.filter(customer_id=customer_id).count()
            if customer_usage >= coupon.usage_limit_per_customer:
                return False
        
        return True
    
    @staticmethod
    def _calculate_shipping(
        product: Product,
        quantity: int,
        shipping_method_id: int,
        subtotal: Decimal
    ) -> Decimal:
        """Calculate shipping cost"""
        try:
            shipping_method = ShippingMethod.objects.get(pk=shipping_method_id)
            
            # Check if free shipping threshold is met
            if hasattr(product, 'shipping') and product.shipping:
                if product.shipping.free_shipping_threshold:
                    if subtotal >= product.shipping.free_shipping_threshold:
                        return Decimal('0')
            
            # Calculate shipping cost
            if shipping_method.pricing_type == 'flat':
                return shipping_method.flat_rate or Decimal('0')
            elif shipping_method.pricing_type == 'weight_based':
                # Would need product weight
                if hasattr(product, 'shipping') and product.shipping:
                    weight = product.shipping.shipping_weight or Decimal('0')
                    return (shipping_method.weight_rate_per_kg or Decimal('0')) * weight
            elif shipping_method.pricing_type == 'price_based':
                return subtotal * ((shipping_method.price_rate_percentage or Decimal('0')) / Decimal('100'))
        except ShippingMethod.DoesNotExist:
            pass
        
        return Decimal('0')
    
    @staticmethod
    def _calculate_tax(
        subtotal: Decimal,
        tax_config: 'TaxConfiguration'
    ) -> Decimal:
        """Calculate tax based on configuration"""
        if not tax_config.is_active:
            return Decimal('0')
        
        if tax_config.tax_type == 'vat':
            return subtotal * (tax_config.rate / Decimal('100'))
        elif tax_config.tax_type == 'sales_tax':
            return subtotal * (tax_config.rate / Decimal('100'))
        
        return Decimal('0')

