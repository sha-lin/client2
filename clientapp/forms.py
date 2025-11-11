from django import forms
from .models import Lead, Client, Job, Product, Quote, ProductionUpdate

class LeadForm(forms.ModelForm):
    PRODUCT_CHOICES = [
        ('', 'Select product'),
        ('Business Cards', 'Business Cards'),
        ('Brochures', 'Brochures'),
        ('Banners & Signage', 'Banners & Signage'),
        ('Packaging', 'Packaging'),
        ('Corporate Stationery', 'Corporate Stationery'),
        ('Labels', 'Labels'),
    ]
   
    product_interest = forms.ChoiceField(
        choices=PRODUCT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
   
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'source', 'product_interest',
                  'preferred_contact', 'follow_up_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter name or company',
                'id': 'id_name'
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
            'source': forms.Select(attrs={
                'class': 'form-select w-full',
                'id': 'id_source'
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
        }


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
                  'payment_terms', 'credit_limit', 'risk_rating', 'is_reseller']
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


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'product_type', 'base_price', 'availability',
            'stock_quantity', 'lead_time', 'description', 'is_active'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'availability': forms.Select(attrs={'class': 'form-select'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'lead_time': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
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