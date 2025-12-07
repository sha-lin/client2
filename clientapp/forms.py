from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import (
    Lead, Client, Job, Product, Quote, ProductionUpdate,
    ProductVariable, ProductVariableOption, ProductImage, ProductTag
)

class LeadForm(forms.ModelForm):
    # Product interest will be populated from Product model dynamically
    product_interest = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_visible=True, status='published').order_by('name'),
        required=True,
        empty_label='Select a product',
        widget=forms.Select(attrs={'class': 'form-select w-full', 'id': 'id_product_interest'}),
        to_field_name='name'
    )
   
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'source', 'product_interest',
                  'preferred_contact', 'follow_up_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter name or company',
                'id': 'id_name',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'email@example.com',
                'id': 'id_email',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '+1234567890',
                'id': 'id_phone',
                'required': 'required'
            }),
            'source': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_source',
                'required': 'required'
            }),
            'preferred_contact': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_preferred_contact',
                'required': 'required'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-input w-full',
                'type': 'date',
                'id': 'id_follow_up_date',
                'required': 'required'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        for field_name in self.fields:
            self.fields[field_name].required = True


class ClientForm(forms.ModelForm):
    CHANNEL_CHOICES = [
        ('', 'Select channel'),
        ('WhatsApp', 'WhatsApp'),
        ('Email', 'Email'),
        ('Phone', 'Phone'),
        ('SMS', 'SMS'),
    ]
   
    preferred_channel = forms.ChoiceField(
        choices=CHANNEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select w-full', 
            'id': 'id_preferred_channel'
        })
    )
   
    class Meta:
        model = Client
        fields = ['client_type', 'name', 'company', 'email', 'phone',
                  'preferred_channel', 'lead_source', 'vat_tax_id',
                  'payment_terms', 'credit_limit', 'risk_rating', 'is_reseller',
                  'delivery_address', 'delivery_instructions']
        widgets = {
            'client_type': forms.RadioSelect(attrs={
                'class': 'form-radio'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter name',
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
            'lead_source': forms.TextInput(attrs={
                'class': 'form-input w-full bg-gray-100',
                'readonly': 'readonly',
                'id': 'id_lead_source'
            }),
            'vat_tax_id': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter VAT/Tax ID',
                'id': 'id_vat_tax_id'
            }),
            'payment_terms': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_payment_terms'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'e.g 25000',
                'id': 'id_credit_limit'
            }),
            'risk_rating': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_risk_rating'
            }),
            'is_reseller': forms.CheckboxInput(attrs={
                'class': 'w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 relative',
                'id': 'id_is_reseller'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 3,
                'placeholder': 'Enter default delivery address',
                'id': 'id_delivery_address'
            }),
            'delivery_instructions': forms.Textarea(attrs={
                'class': 'form-textarea w-full',
                'rows': 3,
                'placeholder': 'Enter specific delivery instructions',
                'id': 'id_delivery_instructions'
            }),
        }


class JobForm(forms.ModelForm):
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


