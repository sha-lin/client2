"""
Complete Product Management Forms
Matches the exact structure of your Product models
"""

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import (
    Product, ProductTag, ProductVariable, ProductVariableOption,
    ProductImage, ProductPricing, ProductSEO, ProductVideo,
    ProductDownloadableFile, ProductFAQ, ProductShipping,
    ProductLegal, ProductProduction, Vendor, ProductCategory,
    ProductSubCategory, ProductFamily
)

class ProductGeneralInfoForm(forms.ModelForm):
    """Form for Product General Information"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'internal_code', 'short_description', 'long_description',
            'technical_specs', 'primary_category', 'sub_category', 'product_family',
            'product_type', 'tags', 'is_visible', 'visibility',
            'feature_product', 'bestseller_badge', 'new_arrival', 'new_arrival_expires',
            'on_sale_badge', 'unit_of_measure', 'unit_of_measure_custom',
            'weight', 'weight_unit', 'length', 'width', 'height', 'dimension_unit',
            'warranty', 'country_of_origin', 'internal_notes', 'client_notes'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Premium Business Cards',
                'required': True
            }),
            'internal_code': forms.TextInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'PRD-BC-001',
                'readonly': 'readonly'
            }),
            
            'short_description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'maxlength': 150,
                'placeholder': 'Brief description (max 150 characters)'
            }),
            'long_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border-0 focus:outline-none focus:ring-0',
                'rows': 4,
                'placeholder': 'Detailed product description',
                'id': 'id_long_description'
            }),
            'technical_specs': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Size: 85×55mm, Material: Card stock, etc.'
            }),
            'primary_category': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., Print Products, Signage, Apparel'
            }),
            'sub_category': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., Business Cards, Flyers, Brochures'
            }),
            'product_family': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., Business Cards Family'
            }),
            'product_type': forms.RadioSelect(),
            'tags': forms.CheckboxSelectMultiple(),
            'is_visible': forms.CheckboxInput(attrs={
                'class': 'sr-only peer'
            }),
            'visibility': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'feature_product': forms.CheckboxInput(attrs={'class': 'mr-2 rounded text-blue-600'}),
            'bestseller_badge': forms.CheckboxInput(attrs={'class': 'mr-2 rounded text-blue-600'}),
            'new_arrival': forms.CheckboxInput(attrs={'class': 'mr-2 rounded text-blue-600'}),
            'new_arrival_expires': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'on_sale_badge': forms.CheckboxInput(attrs={'class': 'mr-2 rounded text-blue-600'}),
            'unit_of_measure': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_unit_of_measure'
            }),
            'unit_of_measure_custom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter custom unit',
                'id': 'id_unit_of_measure_custom'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'placeholder': '0.05'
            }),
            'weight_unit': forms.Select(attrs={
                'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'length': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'placeholder': 'L'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'placeholder': 'W'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'placeholder': 'H'
            }),
            'dimension_unit': forms.Select(attrs={
                'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'warranty': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'country_of_origin': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Internal notes (not visible to customers)'
            }),
            'client_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Client-facing notes'
            }),
        }
    
    def clean_internal_code(self):
        """Validate and auto-generate internal code based on product name"""
        internal_code = self.cleaned_data.get('internal_code', '').strip()
        name = self.cleaned_data.get('name', '')
        
        # Check if should auto-generate (if field is empty)
        if not internal_code:
            if name:
                # Generate code based on product name
                name_words = name.split()
                if len(name_words) >= 2:
                    prefix = f"PRD-{name_words[0][:2].upper()}{name_words[1][:2].upper()}"
                else:
                    prefix = f"PRD-{name[:3].upper()}"
            else:
                prefix = 'PRD'
            
            # Get last product with this prefix
            last_product = Product.objects.filter(
                internal_code__startswith=prefix
            ).order_by('-internal_code').first()
            
            if last_product:
                try:
                    last_num = int(last_product.internal_code.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            internal_code = f"{prefix}-{new_num:03d}"
        
        # Check for duplicates (excluding current instance if editing)
        if internal_code:
            qs = Product.objects.filter(internal_code=internal_code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"Product with code '{internal_code}' already exists.")
        
        return internal_code


# ==================== PRODUCT PRICING FORM ====================

class ProductPricingForm(forms.ModelForm):
    """Form for ProductPricing model"""
    
    class Meta:
        model = ProductPricing
        fields = [
            'pricing_model', 'base_cost', 'price_display',
            'default_margin', 'minimum_margin', 'minimum_order_value',
            'lead_time_value', 'lead_time_unit', 'production_method',
            'primary_vendor', 'alternative_vendors', 'minimum_quantity',
            'rush_available', 'rush_lead_time_value', 'rush_lead_time_unit',
            'rush_upcharge', 'enable_conditional_logic', 'enable_conflict_detection'
        ]
        
        widgets = {
            'pricing_model': forms.RadioSelect(),
            'base_cost': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'placeholder': '15.00'
            }),
            'price_display': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'default_margin': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'minimum_margin': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'minimum_order_value': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'lead_time_value': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
            'lead_time_unit': forms.Select(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'production_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'primary_vendor': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'alternative_vendors': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'size': '3'
            }),
            'minimum_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
            'rush_available': forms.CheckboxInput(attrs={'class': 'mr-3 rounded text-blue-600'}),
            'rush_lead_time_value': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
            'rush_lead_time_unit': forms.Select(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'rush_upcharge': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '1',
                'min': '0'
            }),
            'enable_conditional_logic': forms.CheckboxInput(attrs={'class': 'mr-2 rounded text-blue-600'}),
            'enable_conflict_detection': forms.CheckboxInput(attrs={'class': 'mr-2 rounded text-blue-600'}),
        }


class ProductSEOForm(forms.ModelForm):
    """Form for SEO & E-commerce Tab"""
    
    class Meta:
        model = ProductSEO
        fields = [
            'meta_title', 'meta_description', 'slug', 'auto_generate_slug',
            'focus_keyword', 'additional_keywords', 'show_price',
            'price_display_format', 'show_stock_status',
            'related_products', 'upsell_products', 'frequently_bought_together'
        ]
        
        widgets = {
            'meta_title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'maxlength': '60',
                'placeholder': 'Premium Business Cards - Custom Printing | Print Duka'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': '3',
                'maxlength': '160',
                'placeholder': 'Professional business cards on premium stock...'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'premium-business-cards'
            }),
            
            'focus_keyword': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'business cards printing'
            }),
            'additional_keywords': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': '2',
                'placeholder': 'business-cards, corporate-cards, premium-printing'
            }),
            'show_price': forms.CheckboxInput(attrs={
                'class': 'sr-only peer'
            }),
            'price_display_format': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'show_stock_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'related_products': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'size': '3'
            }),
            'upsell_products': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'size': '3'
            }),
            'frequently_bought_together': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'size': '3'
            }),
        }


class ProductShippingForm(forms.ModelForm):
    """Form for Shipping & Delivery settings"""
    
    class Meta:
        model = ProductShipping
        fields = [
            'shipping_weight', 'shipping_weight_unit', 'shipping_class',
            'package_length', 'package_width', 'package_height', 'package_dimension_unit',
            'free_shipping', 'free_shipping_threshold',
            'nairobi_only', 'kenya_only', 'no_international',
            'handling_time', 'handling_time_unit',
            'pickup_available', 'pickup_location'
        ]
        
        widgets = {
            'shipping_weight': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'placeholder': '0.25'
            }),
            'shipping_weight_unit': forms.Select(attrs={
                'class': 'px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'shipping_class': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'package_length': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'placeholder': '10'
            }),
            'package_width': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'placeholder': '7'
            }),
            'package_height': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'placeholder': '3'
            }),
            'package_dimension_unit': forms.Select(attrs={
                'class': 'px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'free_shipping': forms.CheckboxInput(attrs={
                'class': 'mr-3 rounded text-blue-600'
            }),
            'free_shipping_threshold': forms.NumberInput(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-200 rounded-r-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '100',
                'placeholder': '5000'
            }),
            'nairobi_only': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'kenya_only': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'no_international': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'handling_time': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': '1'
            }),
            'handling_time_unit': forms.Select(attrs={
                'class': 'flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'pickup_available': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'pickup_location': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nairobi CBD'
            }),
        }


class ProductLegalForm(forms.ModelForm):
    """Form for Legal & Compliance settings"""
    
    class Meta:
        model = ProductLegal
        fields = [
            'product_terms', 'return_policy', 'age_restriction',
            'cert_fsc', 'cert_eco', 'cert_food_safe',
            'copyright_notice'
        ]
        
        widgets = {
            'product_terms': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': '2',
                'placeholder': 'Custom printed items are non-refundable...'
            }),
            'return_policy': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'age_restriction': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'cert_fsc': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'cert_eco': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'cert_food_safe': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'copyright_notice': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': '2',
                'placeholder': 'Customer must own rights to all submitted artwork...'
            }),
        }


class ProductProductionForm(forms.ModelForm):
    """Form for Production-specific settings"""
    
    class Meta:
        model = ProductProduction
        fields = [
            'production_method_detail', 'machine_equipment',
            'checklist_artwork', 'checklist_preflight',
            'checklist_material', 'checklist_proofs',
            'production_notes'
        ]
        
        widgets = {
            'production_method_detail': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'machine_equipment': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'HP Indigo 7900'
            }),
            'checklist_artwork': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'checklist_preflight': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'checklist_material': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'checklist_proofs': forms.CheckboxInput(attrs={
                'class': 'mr-2 rounded text-blue-600'
            }),
            'production_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': '3',
                'placeholder': 'Special production instructions...'
            }),
        }


# ==================== EXPORT ALL FORMS ====================

__all__ = [
    'ProductGeneralInfoForm',
    'ProductPricingForm',
    'ProductSEOForm',
    'ProductShippingForm',
    'ProductLegalForm',
    'ProductProductionForm',
]