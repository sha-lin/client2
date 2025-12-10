from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import (
    Lead, Client, Job, Product, Quote, ProductionUpdate,
    ProductVariable, ProductVariableOption, ProductImage, ProductTag, Vendor, Process,LPO,Payment,
)
from django.contrib.auth.models import User

class LeadForm(forms.ModelForm):
    account_manager = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Account Manager').order_by('first_name'),
        required=False,
        empty_label='Select Account Manager',
        widget=forms.Select(attrs={'class': 'form-select w-full', 'id': 'id_account_manager'})
    )
   
    class Meta:
        model = Lead
        fields = [
            'name', 'email', 'phone', 'source', 'product_interest',
            'preferred_contact', 'follow_up_date', 'status', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter prospect name or company',
                'id': 'id_name',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'email@example.com',
                'id': 'id_email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '+254700000000',
                'id': 'id_phone',
                'required': 'required'
            }),
            'source': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_source'
            }),
            'product_interest': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., Business Cards, Flyers, etc.',
                'id': 'id_product_interest'
            }),
            'preferred_contact': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_preferred_contact'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-input w-full',
                'type': 'date',
                'id': 'id_follow_up_date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_status'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 4,
                'placeholder': 'Enter any additional notes about this lead',
                'id': 'id_notes'
            }),
        }



class ClientForm(forms.ModelForm):
    account_manager = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Account Manager').order_by('first_name'),
        required=False,
        empty_label='Select Account Manager',
        widget=forms.Select(attrs={
            'class': 'form-select w-full',
            'id': 'id_account_manager'
        })
    )
   
    class Meta:
        model = Client
        fields = [
            'client_type', 'name', 'company', 'email', 'phone',
            'vat_tax_id', 'kra_pin', 'address', 'industry',
            'payment_terms', 'credit_limit', 'default_markup', 'risk_rating', 'is_reseller',
            'delivery_address', 'delivery_instructions',
            'preferred_channel', 'lead_source', 'account_manager', 'status'
        ]
        widgets = {
            'client_type': forms.RadioSelect(attrs={
                'class': 'form-radio',
                'id': 'id_client_type'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter client name',
                'id': 'id_name'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter company name',
                'id': 'id_company'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'email@example.com',
                'id': 'id_email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '+1234567890',
                'id': 'id_phone'
            }),
            'vat_tax_id': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., P001234567A',
                'id': 'id_vat_tax_id'
            }),
            'kra_pin': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., A001234567B',
                'id': 'id_kra_pin'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 3,
                'placeholder': 'Enter business address',
                'id': 'id_address'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., Retail, Manufacturing, Services',
                'id': 'id_industry'
            }),
            'payment_terms': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_payment_terms'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., 25000',
                'id': 'id_credit_limit',
                'step': '0.01'
            }),
            'default_markup': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., 30 (percentage)',
                'id': 'id_default_markup',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'risk_rating': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_risk_rating'
            }),
            'is_reseller': forms.CheckboxInput(attrs={
                'class': 'w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 relative',
                'id': 'id_is_reseller'
            }),
            'delivery_address': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter default delivery address',
                'id': 'id_delivery_address'
            }),
            'delivery_instructions': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 3,
                'placeholder': 'Enter delivery instructions (gate codes, contact person, etc.)',
                'id': 'id_delivery_instructions'
            }),
            'preferred_channel': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_preferred_channel'
            }),
            'lead_source': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., Referral, Website, Cold Call',
                'id': 'id_lead_source'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_status'
            }),
        }


class QuoteForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.filter(status='Active').order_by('name'),
        required=False,
        empty_label='Select Client (Optional)',
        widget=forms.Select(attrs={'class': 'form-select w-full', 'id': 'id_client'})
    )
    
    lead = forms.ModelChoiceField(
        queryset=Lead.objects.filter(status__in=['New', 'Contacted', 'Qualified']).order_by('name'),
        required=False,
        empty_label='Select Lead (Optional)',
        widget=forms.Select(attrs={'class': 'form-select w-full', 'id': 'id_lead'})
    )
   
    class Meta:
        model = Quote
        fields = [
            'client', 'lead', 'product_name', 'quantity', 'unit_price',
            'payment_terms', 'include_vat', 'valid_until',
            'notes', 'terms', 'status'
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter product name or description',
                'id': 'id_product_name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter quantity',
                'id': 'id_quantity',
                'min': '1',
                'required': 'required'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter unit price',
                'id': 'id_unit_price',
                'step': '0.01',
                'required': 'required'
            }),
            'payment_terms': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_payment_terms'
            }),
            'include_vat': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4',
                'id': 'id_include_vat'
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-input w-full',
                'type': 'date',
                'id': 'id_valid_until'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 3,
                'placeholder': 'Enter any additional notes',
                'id': 'id_notes'
            }),
            'terms': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 3,
                'placeholder': 'Enter terms and conditions',
                'id': 'id_terms'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_status'
            }),
        }


class ProductForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=ProductTag.objects.all().order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        })
    )
   
    class Meta:
        model = Product
        fields = [
            'name', 'short_description', 'long_description', 'technical_specs',
            'primary_category', 'sub_category', 'product_type', 'product_family',
            'tags', 'status', 'is_visible', 'visibility',
            'feature_product', 'bestseller_badge', 'new_arrival',
            'unit_of_measure', 'weight', 'weight_unit',
            'length', 'width', 'height', 'dimension_unit',
            'warranty', 'country_of_origin',
            'internal_notes', 'client_notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter product name',
                'id': 'id_name',
                'required': 'required'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter short description (max 150 characters)',
                'id': 'id_short_description',
                'maxlength': '150'
            }),
            'long_description': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 4,
                'placeholder': 'Enter detailed product description',
                'id': 'id_long_description'
            }),
            'technical_specs': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 3,
                'placeholder': 'Enter technical specifications',
                'id': 'id_technical_specs'
            }),
            'primary_category': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., Print Products, Signage, Apparel',
                'id': 'id_primary_category'
            }),
            'sub_category': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., Business Cards, Flyers, Brochures',
                'id': 'id_sub_category'
            }),
            'product_type': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_product_type'
            }),
            'product_family': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g., Business Cards Family',
                'id': 'id_product_family'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_status'
            }),
            'is_visible': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4',
                'id': 'id_is_visible'
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_visibility'
            }),
            'feature_product': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4',
                'id': 'id_feature_product'
            }),
            'bestseller_badge': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4',
                'id': 'id_bestseller_badge'
            }),
            'new_arrival': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4',
                'id': 'id_new_arrival'
            }),
            'unit_of_measure': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_unit_of_measure'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter weight',
                'id': 'id_weight',
                'step': '0.01'
            }),
            'weight_unit': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_weight_unit'
            }),
            'length': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter length',
                'id': 'id_length',
                'step': '0.01'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter width',
                'id': 'id_width',
                'step': '0.01'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter height',
                'id': 'id_height',
                'step': '0.01'
            }),
            'dimension_unit': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_dimension_unit'
            }),
            'warranty': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_warranty'
            }),
            'country_of_origin': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_country_of_origin'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 2,
                'placeholder': 'Internal use only',
                'id': 'id_internal_notes'
            }),
            'client_notes': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 2,
                'placeholder': 'Visible to clients',
                'id': 'id_client_notes'
            }),
        }

    class Meta:
        model = Job
        fields = ['client', 'product', 'quantity', 'person_in_charge', 'status']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-select border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-black focus:border-black w-full'
            }),
            'product': forms.TextInput(attrs={
                'class': 'form-input border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-black focus:border-black w-full'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-black focus:border-black w-full',
                'min': '1'
            }),
            'person_in_charge': forms.TextInput(attrs={
                'class': 'form-input border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-black focus:border-black w-full'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-black focus:border-black w-full'
            }),
        }


class QuoteCostingForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = [
            'unit_price', 'production_cost', 'production_status',
            'production_notes', 'status', 'payment_terms', 'include_vat'
        ]
        widgets = {
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'production_cost': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'production_status': forms.Select(attrs={'class': 'form-select'}),
            'production_notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'include_vat': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
        }


class ProductionUpdateForm(forms.ModelForm):
    class Meta:
        model = ProductionUpdate
        fields = ['status', 'progress', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'progress': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'max': '100'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }


class VendorForm(forms.ModelForm):
    """Form for creating/editing vendors"""
    
    class Meta:
        model = Vendor
        fields = [
            'name', 'contact_person', 'email', 'phone', 'business_address',
            'tax_pin', 'payment_terms', 'payment_method', 'services', 
            'specialization', 'minimum_order', 'lead_time', 'rush_capable',
            'quality_rating', 'reliability_rating', 'vps_score', 'vps_score_value',
            'rating', 'internal_notes', 'recommended', 'active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'business_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tax_pin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tax PIN'}),
            'payment_terms': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Comma-separated services'}),
            'specialization': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'minimum_order': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lead_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 5 days'}),
            'rush_capable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'quality_rating': forms.Select(attrs={'class': 'form-control'}),
            'reliability_rating': forms.Select(attrs={'class': 'form-control'}),
            'vps_score': forms.Select(attrs={'class': 'form-control'}),
            'vps_score_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '5'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recommended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class ProcessForm(forms.ModelForm):
    """Form for creating/editing processes"""
    
    class Meta:
        model = Process
        fields = ['process_name', 'description', 'category', 'standard_lead_time', 
                  'pricing_type', 'unit_of_measure', 'status']
        widgets = {
            'process_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Process name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'standard_lead_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'pricing_type': forms.Select(attrs={'class': 'form-control'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class LPO_Form(forms.ModelForm):
    """Form for creating/editing LPOs"""
    
    class Meta:
        model = LPO
        fields = ['client', 'quote', 'status', 'subtotal', 'vat_amount', 'total_amount',
                  'payment_terms', 'delivery_date', 'notes', 'terms_and_conditions']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'quote': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
class PaymentForm(forms.ModelForm):
    """Form for creating/editing payments"""
    
    class Meta:
        model = Payment
        fields = ['lpo', 'payment_date', 'amount', 'payment_method', 'status', 
                  'reference_number', 'notes']
        widgets = {
            'lpo': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Payment reference'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
class UserForm(forms.ModelForm):
    """Form for creating/editing users"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Leave blank to keep current password"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user