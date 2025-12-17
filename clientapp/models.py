# clients/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import timedelta
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class Lead(models.Model):
    """Lead model for prospect tracking"""
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Converted', 'Converted'),
        ('Lost', 'Lost'),
    ]
    
    SOURCE_CHOICES = [
        ('Website', 'Website'),
        ('Referral', 'Referral'),
        ('Cold Call', 'Cold Call'),
        ('Social Media', 'Social Media'),
        ('Event', 'Event'),
        ('Other', 'Other'),
    ]
    
    CONTACT_METHOD_CHOICES = [
        ('Email', 'Email'),
        ('Phone', 'Phone'),
        ('WhatsApp', 'WhatsApp'),
    ]
    
    lead_id = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True)
    product_interest = models.CharField(max_length=200, blank=True)
    preferred_contact = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES, default='Email')
    follow_up_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='leads_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    converted_to_client = models.BooleanField(default=False)
    converted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.lead_id} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.lead_id:
            # Generate lead ID: LD-YYYY-XXX
            year = timezone.now().year
            last_lead = Lead.objects.filter(
                lead_id__startswith=f'LD-{year}-'
            ).order_by('lead_id').last()
            
            if last_lead:
                last_number = int(last_lead.lead_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.lead_id = f'LD-{year}-{new_number:03d}'
        
        super().save(*args, **kwargs)


class Client(models.Model):
    """Client model for active customers"""
    CLIENT_TYPE_CHOICES = [
        ('B2B', 'B2B Business'),
        ('B2C', 'B2C Retail'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Dormant', 'Dormant'),
        ('Inactive', 'Inactive'),
    ]
    
    PAYMENT_TERMS_CHOICES = [
        ('Prepaid', 'Prepaid Before Production'),
        ('Net 7', 'Net 7 Days'),
        ('Net 15', 'Net 15 Days'),
        ('Net 30', 'Net 30 Days'),
        ('Net 60', 'Net 60 Days'),
    ]
    
    RISK_RATING_CHOICES = [
        ('Low', 'Low Risk'),
        ('Medium', 'Medium Risk'),
        ('High', 'High Risk'),
    ]
    
    CHANNEL_CHOICES = [
        ('Email', 'Email'),
        ('Phone', 'Phone'),
        ('WhatsApp', 'WhatsApp'),
        ('In-Person', 'In-Person'),
    ]
    
    # Basic Information
    client_id = models.CharField(max_length=20, unique=True, editable=False)
    client_type = models.CharField(max_length=10, choices=CLIENT_TYPE_CHOICES, default='B2B')
    company = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Business Details
    vat_tax_id = models.CharField(max_length=50, blank=True)
    kra_pin = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    
    # Financial
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='Prepaid')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    default_markup = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    risk_rating = models.CharField(max_length=20, choices=RISK_RATING_CHOICES, default='Low')
    is_reseller = models.BooleanField(default=False)

    # Delivery Details
    delivery_address = models.CharField(max_length=200, blank=True, null=True)
    delivery_instructions = models.TextField(blank=True, help_text="Specific delivery instructions (e.g., gate codes, contact person)")
    
    # Communication
    preferred_channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='Email')
    lead_source = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    # Relationships
    account_manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='managed_clients'
    )
    converted_from_lead = models.OneToOneField(
        Lead, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='client_profile'
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    onboarded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='clients_onboarded'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['client_type']),
        ]
    
    def __str__(self):
        return f"{self.client_id} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.client_id:
            # Generate client ID: CL-YYYY-XXX
            year = timezone.now().year
            last_client = Client.objects.filter(
                client_id__startswith=f'CL-{year}-'
            ).order_by('client_id').last()
            
            if last_client:
                last_number = int(last_client.client_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.client_id = f'CL-{year}-{new_number:03d}'
        
        # Set payment terms to Prepaid for B2C by default
        if self.client_type == 'B2C' and not self.pk:
            self.payment_terms = 'Prepaid'
        
        # Update status based on activity
        if self.last_activity:
            days_inactive = (timezone.now() - self.last_activity).days
            if days_inactive > 180:
                self.status = 'Dormant'
        
        super().save(*args, **kwargs)
    
    def get_last_activity_display(self):
        """Get human-readable last activity"""
        if not self.last_activity:
            return "Never"
        
        delta = timezone.now() - self.last_activity
        
        if delta.days == 0:
            return "Today"
        elif delta.days == 1:
            return "Yesterday"
        elif delta.days < 7:
            return f"{delta.days} days ago"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif delta.days < 365:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    
    @property
    def total_jobs(self):
        """Count total quotes/jobs"""
        return self.quotes.count()
    
    @property
    def total_revenue(self):
        """Calculate total revenue from approved quotes"""
        from django.db.models import Sum
        total = self.quotes.filter(
            status='Approved'
        ).aggregate(Sum('total_amount'))['total_amount__sum']
        return total or 0
    
    @property
    def conversion_rate(self):
        """Calculate quote to approval conversion rate"""
        total = self.quotes.count()
        if total == 0:
            return 0
        approved = self.quotes.filter(status='Approved').count()
        return round((approved / total) * 100, 1)


class ClientContact(models.Model):
    """Additional contacts for a client"""
    ROLE_CHOICES = [
        ('None', 'None'),
        ('Approve Quotes', 'Approve Quotes'),
        ('Approve Artwork', 'Approve Artwork'),
        ('Billing Contact', 'Billing Contact'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='None')
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', 'full_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.client.name}"


class BrandAsset(models.Model):
    """Brand assets library for clients"""
    ASSET_TYPE_CHOICES = [
        ('Logo', 'Logo'),
        ('Brand Guide', 'Brand Guidelines'),
        ('Color Palette', 'Color Palette'),
        ('Font', 'Font Files'),
        ('Other', 'Other'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='brand_assets')
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPE_CHOICES)
    file = models.FileField(upload_to='brand_assets/%Y/%m/')
    description = models.CharField(max_length=200, blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.client.name} - {self.asset_type}"


class ComplianceDocument(models.Model):
    """Compliance and legal documents for clients"""
    DOCUMENT_TYPE_CHOICES = [
        ('COI', 'Certificate of Incorporation'),
        ('KRA', 'KRA Pin Certificate'),
        ('PO Terms', 'Purchase Order Terms'),
        ('NDA', 'Non-Disclosure Agreement'),
        ('Other', 'Other Legal Document'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='compliance_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='compliance/%Y/%m/')
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.client.name} - {self.document_type}"
    
    @property
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def expires_soon(self):
        """Check if document expires in next 30 days"""
        if self.expiry_date:
            days_until_expiry = (self.expiry_date - timezone.now().date()).days
            return 0 < days_until_expiry <= 30
        return False

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductCategory(models.Model):
    """Primary categories for products"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
from django import forms
class ProductCategoryForm(forms.ModelForm):
    """Form for creating/editing product categories"""
    
    class Meta:
        model = ProductCategory
        fields = ['name', 'slug', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input w-full', 'placeholder': 'Category Name'}),
            'slug': forms.TextInput(attrs={'class': 'form-input w-full', 'placeholder': 'slug-name'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea w-full', 'rows': 3}),
        }
class ProductSubCategory(models.Model):
    """Sub-categories under primary categories"""
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Product Sub-Categories"
        ordering = ['category', 'name']
        unique_together = ['category', 'slug']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class ProductFamily(models.Model):
    """Product families for grouping related products"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Product Families"
        ordering = ['name']
    
    def __str__(self):
        return self.name



class Product(models.Model):
    """Main Product Model - General Info Tab"""
    
    # Product Type Choices
    PRODUCT_TYPE_CHOICES = [
        ('physical', 'Physical Product'),
        ('digital', 'Digital Product'),
        ('service', 'Service'),
    ]
    CUSTOMIZATION_LEVELS = [
        ('non_customizable', 'Non-Customizable'),
        ('semi_customizable', 'Semi-Customizable'),
        ('fully_customizable', 'Fully Customizable'),
    ]

    customization_level = models.CharField(
        max_length=30,
        choices=CUSTOMIZATION_LEVELS,
        default='non_customizable',
        help_text="Determines which pricing methods are available"
    )
    
    # Visibility Choices
    VISIBILITY_CHOICES = [
        ('catalog-search', 'Catalog and Search'),
        ('catalog-only', 'Catalog Only'),
        ('search-only', 'Search Only'),
        ('hidden', 'Hidden'),
    ]
    
    # Unit of Measure Choices
    UNIT_CHOICES = [
        ('pieces', 'Pieces'),
        ('packs', 'Packs'),
        ('sets', 'Sets'),
        ('sqm', 'm²'),
        ('other', 'Other'),
    ]
    
    # Weight Unit Choices
    WEIGHT_UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('lb', 'Pounds'),
    ]
    
    # Dimension Unit Choices
    DIMENSION_UNIT_CHOICES = [
        ('cm', 'Centimeters'),
        ('mm', 'Millimeters'),
        ('in', 'Inches'),
    ]
    
    # Warranty Choices
    WARRANTY_CHOICES = [
        ('satisfaction-guarantee', 'Satisfaction Guarantee - Reprint if defective'),
        ('no-warranty', 'No Warranty'),
        ('30-days', '30 Days'),
        ('90-days', '90 Days'),
    ]
    
    # Country Choices
    COUNTRY_CHOICES = [
        ('kenya', 'Kenya'),
        ('china', 'China'),
        ('india', 'India'),
        ('uae', 'UAE'),
    ]
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Basic Product Information
    name = models.CharField(max_length=255, help_text="Customer-facing name")
    internal_code = models.CharField(max_length=50, unique=True, blank=True, help_text="Internal SKU/Code (auto-generated)")
    auto_generate_code = models.BooleanField(default=True, editable=False)  # Always True, hidden from forms
    short_description = models.CharField(max_length=150)
    long_description = models.TextField()
    technical_specs = models.TextField(blank=True)
    
    # Classification
    primary_category = models.CharField(max_length=100, blank=True, help_text="e.g., Print Products, Signage, Apparel")
    sub_category = models.CharField(max_length=100, blank=True, help_text="e.g., Business Cards, Flyers, Brochures")
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='physical')
    product_family = models.CharField(max_length=100, blank=True, help_text="e.g., Business Cards Family")

    tags = models.ManyToManyField('ProductTag', blank=True, related_name='products')
    
    # Status & Visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_visible = models.BooleanField(default=True, help_text="Visible to customers?")
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='catalog-search')
    feature_product = models.BooleanField(default=False)
    bestseller_badge = models.BooleanField(default=False)
    new_arrival = models.BooleanField(default=False)
    new_arrival_expires = models.DateField(null=True, blank=True)
    on_sale_badge = models.BooleanField(default=False)
    
    # Product Attributes
    unit_of_measure = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pieces')
    unit_of_measure_custom = models.CharField(max_length=50, blank=True, help_text="Custom unit if 'Other' is selected")
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight_unit = models.CharField(max_length=5, choices=WEIGHT_UNIT_CHOICES, default='kg')
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimension_unit = models.CharField(max_length=5, choices=DIMENSION_UNIT_CHOICES, default='cm')
    warranty = models.CharField(max_length=50, choices=WARRANTY_CHOICES, default='satisfaction-guarantee')
    country_of_origin = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default='kenya')
    
    # Notes & Comments
    internal_notes = models.TextField(blank=True, help_text="Internal use only")
    client_notes = models.TextField(blank=True, help_text="Visible to clients")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='products_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='products_updated')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['internal_code']),
            models.Index(fields=['status', 'is_visible']),
        ]
    
    def __str__(self):
        return f"{self.internal_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        if self.auto_generate_code or not self.internal_code:
            # Generate code based on product name
            name_words = self.name.split()
            if len(name_words) >= 2:
                # Use first letters of first two words
                prefix = f"PRD-{name_words[0][:2].upper()}{name_words[1][:2].upper()}"
            else:
                # Use first 2-3 letters of product name
                prefix = f"PRD-{self.name[:3].upper()}"
            
            # Get last product with this prefix
            last_product = Product.objects.filter(
                internal_code__startswith=prefix
            ).order_by('-internal_code').first()
            
            if last_product:
                try:
                    # Extract number from code like PRD-BC-001
                    last_num = int(last_product.internal_code.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.internal_code = f"{prefix}-{new_num:03d}"
        
        super().save(*args, **kwargs)


class ProductTag(models.Model):
    """Tags for products"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductPricing(models.Model):
    """Pricing & Variables Tab"""
    
    PRICING_MODEL_CHOICES = [
        ('variable', 'Variable Pricing (customer selects options)'),
        ('simple', 'Simple/Fixed Pricing (one price)'),
        ('quote', 'Quote-Based (PT must cost)'),
    ]
    
    PRICE_DISPLAY_CHOICES = [
        ('from', 'From KES X'),
        ('starting', 'Starting at KES X'),
        ('plus', 'KES X+'),
    ]
    
    PRODUCTION_METHOD_CHOICES = [
        ('digital-offset', 'Digital Offset Printing'),
        ('offset', 'Offset Printing'),
        ('screen', 'Screen Printing'),
        ('digital', 'Digital Printing'),
    ]
    
    LEAD_TIME_UNIT_CHOICES = [
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('hours', 'Hours'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='pricing')
    def calculate_cost(self, quantity=1, customization_values=None):
        """
        Calculate total cost based on customization level and selected processes
        
        Args:
            quantity: Order quantity
            customization_values: Dict of {variable_name: value} for customizations
        
        Returns:
            dict: {
                'base_cost': Decimal,
                'tier_cost': Decimal,
                'customization_cost': Decimal,
                'total_cost': Decimal,
                'breakdown': list of cost components
            }
        """
        breakdown = []
        base_cost = Decimal('0')
        tier_cost = Decimal('0')
        customization_cost = Decimal('0')
        
        customization_level = self.product.customization_level
        customization_values = customization_values or {}
        
        # 1. Base Cost (for non-customizable and semi-customizable)
        if customization_level in ['non_customizable', 'semi_customizable']:
            base_cost = self.base_cost * quantity
            breakdown.append({
                'component': 'Base Cost',
                'calculation': f'{self.base_cost} × {quantity}',
                'amount': base_cost
            })
        
        # 2. Tier-Based Cost (quantity discounts)
        if self.tier_process:
            tier = self.tier_process.tiers.filter(
                quantity_from__lte=quantity,
                quantity_to__gte=quantity
            ).first()
            
            if tier:
                # For non-customizable: tier cost replaces base cost
                # For semi/fully customizable: tier cost is adjustment
                if customization_level == 'non_customizable':
                    tier_cost = tier.cost * quantity
                    base_cost = Decimal('0')  # Override base cost
                    breakdown = [{
                        'component': 'Tier Cost',
                        'calculation': f'{tier.cost} × {quantity} (Tier {tier.tier_number})',
                        'amount': tier_cost
                    }]
                else:
                    tier_cost = tier.cost * quantity
                    breakdown.append({
                        'component': f'Tier {tier.tier_number} Cost',
                        'calculation': f'{tier.cost} × {quantity}',
                        'amount': tier_cost
                    })
        
        # 3. Formula-Based Customization Cost
        if self.formula_process and customization_values:
            for variable in self.formula_process.variables.all():
                var_value = customization_values.get(variable.variable_name)
                
                if var_value is not None:
                    # Find applicable range
                    applicable_range = variable.ranges.filter(
                        min_value__lte=var_value,
                        max_value__gte=var_value
                    ).first()
                    
                    if applicable_range:
                        var_cost = (applicable_range.price * applicable_range.rate) * quantity
                        customization_cost += var_cost
                        
                        breakdown.append({
                            'component': f'{variable.variable_name} Cost',
                            'calculation': f'{applicable_range.price} × {quantity} (Rate {applicable_range.rate})',
                            'amount': var_cost
                        })
        
        # 4. Total Cost
        total_cost = base_cost + tier_cost + customization_cost
        
        return {
            'base_cost': base_cost,
            'tier_cost': tier_cost,
            'customization_cost': customization_cost,
            'total_cost': total_cost,
            'breakdown': breakdown
        }

    # Base pricing (always available)
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Base cost before customization (EVP)"
    )
    
    # Link to tier-based process (for quantity discounts)
    tier_process = models.ForeignKey(
        'Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_using_tiers',
        limit_choices_to={'pricing_type': 'tier', 'status': 'active'},
        help_text="Tier-based pricing process for quantity discounts"
    )
    
    # Link to formula-based process (for customizations)
    formula_process = models.ForeignKey(
        'Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_using_formula',
        limit_choices_to={'pricing_type': 'formula', 'status': 'active'},
        help_text="Formula-based pricing process for customizations"
    )
    
    use_process_costs = models.BooleanField(
        default=False,
        help_text="Use process costs instead of manual base cost"
    )
    # ===== NEW: Link to Process (Costing System Integration) =====
    process = models.ForeignKey(
        'Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Select the costing process for this product"
    )
    use_process_costs = models.BooleanField(
        default=True,
        help_text="Use costs from linked process, or override with custom values"
    )
    # ===== END NEW =====
    
    # Base Pricing Information
    pricing_model = models.CharField(max_length=20, choices=PRICING_MODEL_CHOICES, default='variable')
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, default=15, help_text="Lowest possible vendor cost per piece (EVP)")
    price_display = models.CharField(max_length=20, choices=PRICE_DISPLAY_CHOICES, default='from')
    default_margin = models.DecimalField(max_digits=5, decimal_places=2, default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    minimum_margin = models.DecimalField(max_digits=5, decimal_places=2, default=15, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Below this triggers approval")
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Production & Vendor Information
    lead_time_value = models.IntegerField(default=3)
    lead_time_unit = models.CharField(max_length=10, choices=LEAD_TIME_UNIT_CHOICES, default='days')
    production_method = models.CharField(max_length=50, choices=PRODUCTION_METHOD_CHOICES, default='digital-offset')
    primary_vendor = models.ForeignKey('Vendor', on_delete=models.PROTECT, related_name='primary_products', null=True, blank=True)
    alternative_vendors = models.ManyToManyField('Vendor', related_name='alternative_products', blank=True)
    minimum_quantity = models.IntegerField(default=1)
    
    # Rush Production
    rush_available = models.BooleanField(default=False)
    rush_lead_time_value = models.IntegerField(null=True, blank=True)
    rush_lead_time_unit = models.CharField(max_length=10, choices=LEAD_TIME_UNIT_CHOICES, default='days', blank=True)
    rush_upcharge = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Percentage upcharge")
    
    # Advanced Settings
    enable_conditional_logic = models.BooleanField(default=False)
    enable_conflict_detection = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Product Pricing"
    
    def __str__(self):
        return f"Pricing for {self.product.name}"


class ProductVariable(models.Model):
    """Product Variables for configurable products"""
    
    VARIABLE_TYPE_CHOICES = [
        ('required', 'Required'),
        ('conditional', 'Conditional'),
        ('optional', 'Optional'),
    ]
    
    PRICING_TYPE_CHOICES = [
        ('fixed', 'Fixed per tier'),
        ('increment', 'Increment per piece'),
        ('percentage', 'Percentage markup'),
        ('none', 'No price impact'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variables')
    name = models.CharField(max_length=100, help_text="e.g., Quantity Options, Paper Weight")
    display_order = models.IntegerField(default=0)
    variable_type = models.CharField(max_length=20, choices=VARIABLE_TYPE_CHOICES, default='required')
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES, default='fixed')
    
    # ===== NEW: Link to Process Variable (Source Tracking) =====
    source_process_variable = models.ForeignKey(
        'ProcessVariable',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_variables',
        help_text="Source variable from process (if auto-imported)"
    )
    # ===== END NEW =====
    
    # Conditional Logic
    show_when_variable = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_variables')
    show_when_option = models.ForeignKey('ProductVariableOption', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['product', 'display_order']
        unique_together = ['product', 'name']
    
    def __str__(self):
        return f"{self.product.internal_code} - {self.name}"


class ProductVariableOption(models.Model):
    """Options for each product variable"""
    variable = models.ForeignKey(ProductVariable, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=100, help_text="e.g., 100pcs, 250gsm, Matte")
    display_order = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)
    
    # Pricing
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Amount to add/subtract")
    
    # Additional info
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['variable', 'display_order']
        unique_together = ['variable', 'name']
    
    def __str__(self):
        return f"{self.variable.name}: {self.name}"


class ProductImage(models.Model):
    """Product Images - Images & Media Tab"""
    
    IMAGE_TYPE_CHOICES = [
        ('product-photo', 'Product Photo'),
        ('detail', 'Detail/Close-up'),
        ('mockup', 'Mockup/In-Use'),
        ('size-comparison', 'Size Comparison'),
        ('sample', 'Sample/Example'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/%Y/%m/')
    alt_text = models.CharField(max_length=255, help_text="For SEO & accessibility")
    caption = models.CharField(max_length=255, blank=True)
    image_type = models.CharField(max_length=30, choices=IMAGE_TYPE_CHOICES, default='product-photo')
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    # Association with variable option
    associated_variable = models.ForeignKey(ProductVariable, on_delete=models.SET_NULL, null=True, blank=True)
    associated_option = models.ForeignKey(ProductVariableOption, on_delete=models.SET_NULL, null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['product', 'display_order']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.display_order}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per product
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVideo(models.Model):
    """Product Videos"""
    
    VIDEO_TYPE_CHOICES = [
        ('demo', 'Product Demo'),
        ('tutorial', 'Tutorial'),
        ('review', 'Customer Review'),
        ('unboxing', 'Unboxing'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos')
    video_url = models.URLField(help_text="YouTube, Vimeo, or direct MP4 link")
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPE_CHOICES, default='demo')
    thumbnail = models.ImageField(upload_to='products/video_thumbnails/%Y/%m/', blank=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['product', 'display_order']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_video_type_display()}"


class ProductDownloadableFile(models.Model):
    """Downloadable files like templates, specs"""
    
    FILE_TYPE_CHOICES = [
        ('illustrator', 'Adobe Illustrator'),
        ('pdf', 'PDF'),
        ('psd', 'Photoshop'),
        ('indd', 'InDesign'),
        ('zip', 'ZIP Archive'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='downloadable_files')
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='products/downloads/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(help_text="File size in bytes", editable=False)
    display_order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['product', 'display_order']
    
    def __str__(self):
        return f"{self.product.name} - {self.file_name}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class ProductSEO(models.Model):
    """SEO & E-commerce Settings"""
    
    PRICE_DISPLAY_FORMAT_CHOICES = [
        ('from', 'From KES X'),
        ('starting', 'Starting at KES X'),
        ('plus', 'KES X+'),
        ('range', 'KES X - Y'),
    ]
    
    STOCK_STATUS_CHOICES = [
        ('in-stock-only', 'Show "In Stock" only'),
        ('always', 'Always show stock level'),
        ('low-stock', 'Show when low stock'),
        ('never', 'Never show'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='seo')
    
    # SEO
    meta_title = models.CharField(max_length=60)
    meta_description = models.CharField(max_length=160)
    slug = models.SlugField(max_length=255, unique=True)
    auto_generate_slug = models.BooleanField(default=True)
    focus_keyword = models.CharField(max_length=100, blank=True)
    additional_keywords = models.TextField(blank=True, help_text="Comma-separated")
    
    # Display Settings
    show_price = models.BooleanField(default=True, help_text="Display price or 'Request Quote'")
    price_display_format = models.CharField(max_length=20, choices=PRICE_DISPLAY_FORMAT_CHOICES, default='from')
    show_stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, default='in-stock-only')
    
    # Related Products
    related_products = models.ManyToManyField(Product, blank=True, related_name='related_to')
    upsell_products = models.ManyToManyField(Product, blank=True, related_name='upsells_for')
    frequently_bought_together = models.ManyToManyField(Product, blank=True, related_name='bundles_with')
    
    class Meta:
        verbose_name = "Product SEO"
        verbose_name_plural = "Product SEO"
    
    def __str__(self):
        return f"SEO for {self.product.name}"
    
    def save(self, *args, **kwargs):
        if self.auto_generate_slug and not self.slug:
            self.slug = slugify(self.product.name)
        super().save(*args, **kwargs)


class ProductReviewSettings(models.Model):
    """Customer Review Settings"""
    
    REVIEW_REMINDER_CHOICES = [
        ('3', '3 days after delivery'),
        ('7', '7 days after delivery'),
        ('14', '14 days after delivery'),
        ('30', '30 days after delivery'),
        ('never', 'Never'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='review_settings')
    enable_reviews = models.BooleanField(default=True)
    require_purchase = models.BooleanField(default=True, help_text="Only verified buyers can review")
    auto_approve_reviews = models.BooleanField(default=False, help_text="Publish without moderation")
    review_reminder = models.CharField(max_length=10, choices=REVIEW_REMINDER_CHOICES, default='7')
    
    def __str__(self):
        return f"Review Settings for {self.product.name}"


class ProductFAQ(models.Model):
    """Frequently Asked Questions"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['product', 'display_order']
        verbose_name = "Product FAQ"
        verbose_name_plural = "Product FAQs"
    
    def __str__(self):
        return f"{self.product.name} - FAQ {self.display_order}"


class ProductShipping(models.Model):
    """Shipping & Delivery Settings"""
    
    SHIPPING_CLASS_CHOICES = [
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('overnight', 'Overnight'),
        ('fragile', 'Fragile'),
    ]
    
    HANDLING_TIME_UNIT_CHOICES = [
        ('days', 'Business Days'),
        ('weeks', 'Weeks'),
        ('hours', 'Hours'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='shipping')
    
    # Shipping Details
    shipping_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_weight_unit = models.CharField(max_length=5, default='kg')
    shipping_class = models.CharField(max_length=20, choices=SHIPPING_CLASS_CHOICES, default='standard')
    
    # Package Dimensions
    package_length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    package_width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    package_height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    package_dimension_unit = models.CharField(max_length=5, default='cm')
    
    # Free Shipping
    free_shipping = models.BooleanField(default=False)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Delivery Restrictions
    nairobi_only = models.BooleanField(default=False)
    kenya_only = models.BooleanField(default=False)
    no_international = models.BooleanField(default=False)
    
    # Handling Time
    handling_time = models.IntegerField(default=1)
    handling_time_unit = models.CharField(max_length=10, choices=HANDLING_TIME_UNIT_CHOICES, default='days')
    pickup_available = models.BooleanField(default=False)
    pickup_location = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Shipping for {self.product.name}"


class ProductLegal(models.Model):
    """Legal & Compliance"""
    
    RETURN_POLICY_CHOICES = [
        ('non-refundable', 'Non-refundable (custom items)'),
        ('7-days', '7 days'),
        ('14-days', '14 days'),
        ('30-days', '30 days'),
        ('custom', 'Custom policy'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='legal')
    
    # Terms & Policies
    product_terms = models.TextField(blank=True)
    return_policy = models.CharField(max_length=30, choices=RETURN_POLICY_CHOICES, default='non-refundable')
    age_restriction = models.BooleanField(default=False, help_text="Age 18+ required")
    
    # Certifications
    cert_fsc = models.BooleanField(default=False, verbose_name="FSC Certified Paper")
    cert_eco = models.BooleanField(default=False, verbose_name="Eco-Friendly")
    cert_food_safe = models.BooleanField(default=False, verbose_name="Food Safe")
    
    copyright_notice = models.TextField(blank=True)
    
    def __str__(self):
        return f"Legal for {self.product.name}"


class ProductProduction(models.Model):
    """Production-specific settings"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='production')
    
    production_method_detail = models.CharField(max_length=100, blank=True)
    machine_equipment = models.CharField(max_length=100, blank=True)
    
    # Pre-Production Checklist
    checklist_artwork = models.BooleanField(default=False, verbose_name="Client artwork approved")
    checklist_preflight = models.BooleanField(default=False, verbose_name="Pre-flight check passed")
    checklist_material = models.BooleanField(default=False, verbose_name="Material in stock")
    checklist_proofs = models.BooleanField(default=False, verbose_name="Color proofs confirmed")
    
    production_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Production for {self.product.name}"


class ProductChangeHistory(models.Model):
    """Track all changes to products"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='change_history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    change_type = models.CharField(max_length=50)  # 'created', 'updated', 'published', etc.
    field_changed = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Product Change History"
    
    def __str__(self):
        return f"{self.product.internal_code} - {self.change_type} at {self.changed_at}"


# Updated Quote Model - Replace in your models.py

class Quote(models.Model):
    """Quote/Proposal model - Simplified pricing"""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Quoted', 'Quoted'),
        ('Client Review', 'Client Review'),
        ('Approved', 'Approved'),
        ('Lost', 'Lost'),
    ]

    PRODUCTION_STATUS_CHOICES = [
        ('pending', 'Pending Costing'),
        ('in_progress', 'Costing In Progress'),
        ('costed', 'Costed'),
        ('sent_to_client', 'Sent To Client'),
        ('on_hold', 'On Hold'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
    ]
    
    PAYMENT_TERMS_CHOICES = [
        ('Prepaid', 'Prepaid Before Production'),
        ('Net 7', 'Net 7 Days'),
        ('Net 15', 'Net 15 Days'),
        ('Net 30', 'Net 30 Days'),
        ('Net 60', 'Net 60 Days'),
    ]
    
    # Basic Info
    quote_id = models.CharField(max_length=20, editable=False, db_index=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='quotes', null=True, blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotes')
    
    # Product Details
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Simplified Pricing - ONLY UNIT PRICE
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Quote Details
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='Prepaid')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    include_vat = models.BooleanField(default=False)
    production_status = models.CharField(max_length=20, choices=PRODUCTION_STATUS_CHOICES, default='pending')
    production_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    production_notes = models.TextField(blank=True)
    costed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes_costed'
    )
    
    # Dates
    quote_date = models.DateField(default=timezone.now)
    valid_until = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Info
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    loss_reason = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='quotes_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['quote_id']),
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['production_status']),
        ]
    
    def __str__(self):
        return f"{self.quote_id} - {self.product_name}"
    
    def save(self, *args, **kwargs):
        # Generate quote_id if not exists
        if not self.quote_id:
            year = timezone.now().year
            last_quote = Quote.objects.filter(
                quote_id__startswith=f'QT-{year}-'
            ).order_by('quote_id').last()
            
            if last_quote:
                try:
                    last_number = int(last_quote.quote_id.split('-')[-1])
                    new_number = last_number + 1
                except:
                    new_number = 1
            else:
                new_number = 1
            
            self.quote_id = f'QT-{year}-{new_number:03d}'
        
        # Calculate total amount (unit_price * quantity)
        unit_price = self.unit_price if self.unit_price is not None else Decimal('0')
        subtotal = unit_price * self.quantity
        if self.include_vat:
            vat_amount = subtotal * Decimal('0.16')
            self.total_amount = subtotal + vat_amount
        else:
            self.total_amount = subtotal
        
        # Set valid_until if not set (default 30 days)
        if not self.valid_until:
            self.valid_until = timezone.now().date() + timedelta(days=30)

        # Update production status transitions automatically
        if self.status in ['Quoted', 'Client Review'] and self.production_status == 'pending':
            self.production_status = 'costed'
        if self.status == 'Approved' and self.production_status not in ['in_production', 'completed']:
            self.production_status = 'in_production'
        if self.status == 'Lost':
            self.production_status = 'completed'
        
        # Handle Lead to Client conversion when approved
        if self.status == 'Approved' and self.lead and not self.lead.converted_to_client:
            self.convert_lead_to_client()
        
        super().save(*args, **kwargs)
    
    def convert_lead_to_client(self):
        """Convert lead to client when quote is approved"""
        lead = self.lead
        
        # Check if client already exists with this email
        existing_client = Client.objects.filter(email=lead.email).first()
        
        if not existing_client:
            # Create new client from lead
            client = Client.objects.create(
                name=lead.name,
                email=lead.email,
                phone=lead.phone,
                client_type='B2C',  # Default to B2C, can be changed later
                lead_source=lead.source if hasattr(lead, 'source') else '',
                preferred_channel=lead.preferred_contact if hasattr(lead, 'preferred_contact') else 'Email',
                status='Active',
                converted_from_lead=lead,
                onboarded_by=self.created_by,
                account_manager=self.created_by
            )
            
            # Update lead status
            lead.status = 'Converted'
            lead.converted_to_client = True
            lead.converted_at = timezone.now()
            lead.save()
            
            # Transfer quote to new client
            self.client = client
            self.lead = None  # Remove lead reference
            
            # Log activity
            ActivityLog.objects.create(
                client=client,
                activity_type='Note',
                title=f"Client Converted from Lead {lead.lead_id}",
                description=f"Lead automatically converted to client after quote {self.quote_id} was approved.",
                created_by=self.created_by
            )
        else:
            # Use existing client
            self.client = existing_client
            self.lead = None
            lead.status = 'Converted'
            lead.converted_to_client = True
            lead.converted_at = timezone.now()
            lead.save()
    
    @property
    def is_expired(self):
        """Check if quote is expired"""
        return timezone.now().date() > self.valid_until
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        delta = self.valid_until - timezone.now().date()
        return delta.days


class ActivityLog(models.Model):
    """Activity log for tracking client interactions"""
    ACTIVITY_TYPE_CHOICES = [
        ('Quote', 'Quote'),
        ('Order', 'Order'),
        ('Payment', 'Payment'),
        ('Meeting', 'Meeting'),
        ('Email', 'Email'),
        ('Call', 'Phone Call'),
        ('Note', 'Note'),
        ('Other', 'Other'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    related_quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.activity_type} - {self.client.name} - {self.created_at.strftime('%Y-%m-%d')}"
    

class ProductionUpdate(models.Model):
    """Progress updates submitted by the production team"""

    UPDATE_TYPE_CHOICES = [
        ('quote', 'Quote'),
        ('job', 'Job'),
    ]

    update_type = models.CharField(max_length=10, choices=UPDATE_TYPE_CHOICES)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='production_updates',
        null=True,
        blank=True
    )
    job = models.ForeignKey(
        'Job',
        on_delete=models.CASCADE,
        related_name='production_updates',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=Quote.PRODUCTION_STATUS_CHOICES, default='pending')
    progress = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='production_updates_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['update_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        subject = self.quote.quote_id if self.quote else (self.job.job_number if self.job else 'Update')
        return f"{subject} - {self.get_status_display()}"

    def clean(self):
        super().clean()
        if not self.quote and not self.job:
            raise ValidationError('A production update must be linked to a quote or a job.')
        if self.quote and self.job:
            raise ValidationError('A production update can only target a quote or a job, not both.')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.clean()
        target_client = None

        if self.quote and self.status:
            # Sync quote production status
            self.quote.production_status = self.status
            if self.status in ['costed', 'sent_to_client'] and self.created_by:
                self.quote.costed_by = self.created_by
            self.quote.save(update_fields=['production_status', 'costed_by', 'updated_at'])
            target_client = self.quote.client
        elif self.job:
            target_client = self.job.client

        super().save(*args, **kwargs)

        # Notify account manager on fresh updates
        if is_new and target_client and target_client.account_manager:
            title = 'Production Update'
            if self.quote:
                title = f"Quote {self.quote.quote_id} Update"
            elif self.job:
                title = f"Job {self.job.job_number} Update"

            Notification.objects.create(
                recipient=target_client.account_manager,
                title=title,
                message=self.notes or f"Production status changed to {self.get_status_display()}",
                link=self._resolve_notification_link()
            )

    def _resolve_notification_link(self):
        if self.quote:
            return reverse('quote_detail', args=[self.quote.quote_id])
        if self.job:
            return reverse('job_detail', args=[self.job.pk])
        return ''


class Notification(models.Model):
    """Internal notifications for account managers"""

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.title}"

#  Add this to your models.py - Enhanced Job model
from datetime import date
class Job(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('printing', 'Printing'),
        ('design', 'Design'),
        ('branding', 'Branding'),
        ('packaging', 'Packaging'),
        ('signage', 'Signage'),
        ('other', 'Other'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('courier', 'Courier'),
    ]
    
    # Basic Info
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='jobs')
    quote = models.OneToOneField(Quote, on_delete=models.CASCADE, related_name='job', null=True, blank=True)
    job_number = models.CharField(max_length=50, editable=False, null=True, blank=True)
    job_name = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Product Info
    product = models.CharField(max_length=255)  # Main product
    quantity = models.PositiveIntegerField()
    
    # Assignment
    person_in_charge = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Dates
    start_date = models.DateField(default=date.today)
    expected_completion = models.DateField(default=date.today)
    delivery_date = models.DateField(null=True, blank=True)
    actual_completion = models.DateField(null=True, blank=True)
    
    # Delivery
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, default='pickup')
    
    # Additional Info
    notes = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='jobs_created'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['start_date']),
        ]

    def __str__(self):
        return f"{self.job_number} - {self.job_name}"
    
    def save(self, *args, **kwargs):
        if not self.job_number:
            # Generate job number: JOB-YYYY-XXX
            year = timezone.now().year
            last_job = Job.objects.filter(
                job_number__startswith=f'JOB-{year}-'
            ).order_by('job_number').last()
            
            if last_job:
                last_number = int(last_job.job_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.job_number = f'JOB-{year}-{new_number:03d}'
        
        super().save(*args, **kwargs)


class JobProduct(models.Model):
    """Individual products within a job"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='products')
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=20, default='pcs')
    specifications = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product_name} ({self.quantity} {self.unit})"


class JobAttachment(models.Model):
    """File attachments for jobs"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='job_attachments/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # in bytes
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.job.job_number}"

# ===== PRODUCT MANAGEMENT MODELS =====

# Old Product models removed to avoid duplication


# Duplicate ProductImage class removed - using the definition at lines 726-761 which has image_type, caption, etc.


class PropertyType(models.Model):
    """Types of properties like Size, Finish, Paper Stock, Corners, etc."""
    PROPERTY_TYPE_CHOICES = [
        ('size', 'Size'),
        ('finish', 'Finish'),
        ('paper_stock', 'Paper Stock'),
        ('thickness', 'Thickness'),
        ('corners', 'Corners'),
        ('shape', 'Shape'),
        ('coating', 'Coating'),
        ('color', 'Color'),
        ('orientation', 'Orientation'),
        ('folding', 'Folding Style'),
        ('quantity', 'Quantity'),
        ('special_finish', 'Special Finish'),
        ('material', 'Material'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False, help_text="Is this property required for the product?")
    affects_price = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = "Property Types"
    
    def __str__(self):
        return f"{self.name} ({self.get_property_type_display()})"


class PropertyValue(models.Model):
    """Specific values for each property type"""
    property_type = models.ForeignKey(PropertyType, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=200)
    value_code = models.CharField(max_length=50, blank=True, help_text="Short code for internal use")
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['property_type', 'display_order', 'value']
        unique_together = ['property_type', 'value']
    
    def __str__(self):
        return f"{self.property_type.name}: {self.value}"


class ProductProperty(models.Model):
    """Links products to their available property values with pricing"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='properties')
    property_value = models.ForeignKey(PropertyValue, on_delete=models.CASCADE)
    price_modifier = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Additional price for this property (+/-)"
    )
    is_default = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0, help_text="Stock specific to this property variant")
    
    class Meta:
        unique_together = ['product', 'property_value']
        verbose_name_plural = "Product Properties"
    
    def __str__(self):
        return f"{self.product.name} - {self.property_value}"
    
    def get_total_price(self):
        """Calculate total price including modifier"""
        return self.product.base_price + self.price_modifier




class QuantityPricing(models.Model):
    """Quantity-based pricing tiers"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quantity_pricing')
    min_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    max_quantity = models.IntegerField(null=True, blank=True, help_text="Leave blank for no upper limit")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    percentage_discount = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Discount percentage (0-100)"
    )
    
    class Meta:
        ordering = ['product', 'min_quantity']
        verbose_name_plural = "Quantity Pricing Tiers"
        unique_together = ['product', 'min_quantity']
    
    def __str__(self):
        if self.max_quantity:
            return f"{self.product.name}: {self.min_quantity}-{self.max_quantity} units @ KES {self.unit_price}"
        return f"{self.product.name}: {self.min_quantity}+ units @ KES {self.unit_price}"


class ProductTemplate(models.Model):
    """Design templates available for products"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to='templates/')
    thumbnail = models.ImageField(upload_to='templates/thumbnails/', blank=True)
    category_tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"


class TurnAroundTime(models.Model):
    """Production turnaround times with pricing"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='turnaround_times')
    name = models.CharField(max_length=100, help_text="e.g., Standard, 2-Day, Next-Day")
    business_days = models.IntegerField(help_text="Number of business days")
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_default = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'business_days']
        unique_together = ['product', 'name']
    
    def __str__(self):
        return f"{self.product.name} - {self.name} ({self.business_days} days)"


class LPO(models.Model):
    """Local Purchase Order model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    lpo_number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='lpos')
    quote = models.OneToOneField(Quote, on_delete=models.CASCADE, related_name='lpo')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Details
    payment_terms = models.CharField(max_length=20)
    delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # QuickBooks Integration
    quickbooks_invoice_id = models.CharField(max_length=50, null=True, blank=True)
    quickbooks_invoice_number = models.CharField(max_length=50, null=True, blank=True)
    synced_to_quickbooks = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lpos_created')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lpos_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lpo_number']),
            models.Index(fields=['client']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.lpo_number} - {self.client.name}"
    
    def save(self, *args, **kwargs):
        if not self.lpo_number:
            # Generate LPO number: LPO-YYYY-XXX
            year = timezone.now().year
            last_lpo = LPO.objects.filter(
                lpo_number__startswith=f'LPO-{year}-'
            ).order_by('lpo_number').last()
            
            if last_lpo:
                try:
                    last_number = int(last_lpo.lpo_number.split('-')[-1])
                    new_number = last_number + 1
                except:
                    new_number = 1
            else:
                new_number = 1
            
            self.lpo_number = f'LPO-{year}-{new_number:03d}'
            
        super().save(*args, **kwargs)
    
    
    def sync_to_quickbooks(self, user=None):
        """Sync this LPO to QuickBooks as an invoice"""
        # FIX: Changed import from .utils to .helpers and function name
        from quickbooks_integration.helpers import get_qb_client
        from quickbooks.objects.invoice import Invoice
        from quickbooks.objects.detailline import DetailLine, SalesItemLineDetail
        from quickbooks.objects.customer import Customer
        
        try:
            # FIX: Pass the user to get_qb_client
            if not user:
                return {'success': False, 'message': 'User required for QuickBooks sync'}
                
            client = get_qb_client(user)
            
            # 1. Find or Create Customer in QB
            qb_customer = None
            customers = Customer.filter(DisplayName=self.client.name, qb=client)
            
            if customers:
                qb_customer = customers[0]
            else:
                # Create new customer
                qb_customer = Customer()
                qb_customer.DisplayName = self.client.name
                qb_customer.PrimaryEmailAddr = {"Address": self.client.email}
                qb_customer.PrimaryPhone = {"FreeFormNumber": self.client.phone}
                qb_customer.CompanyName = self.client.company or self.client.name
                qb_customer.save(qb=client)
            
            # 2. Create Invoice
            invoice = Invoice()
            invoice.CustomerRef = {"value": qb_customer.Id}
            invoice.DocNumber = self.lpo_number
            
            # Add Line Items
            lines = []
            for item in self.line_items.all():
                line = DetailLine()
                line.Amount = float(item.line_total)
                line.Description = item.product_name
                line.DetailType = "SalesItemLineDetail"
                
                # Create SalesItemLineDetail object or dict
                sales_item = SalesItemLineDetail()
                sales_item.Qty = item.quantity
                sales_item.UnitPrice = float(item.unit_price)
                # Note: Usually need ItemRef here, but maybe it works without for ad-hoc items? 
                # If not, we might need a default service item.
                
                line.SalesItemLineDetail = sales_item
                lines.append(line)
            
            invoice.Line = lines
            
            # Save Invoice
            invoice.save(qb=client)
            
            # Update LPO
            self.quickbooks_invoice_id = invoice.Id
            self.quickbooks_invoice_number = invoice.DocNumber
            self.synced_to_quickbooks = True
            self.synced_at = timezone.now()
            self.save()
            
            # Log activity (Ensure ActivityLog is imported or available)
            try:
                from clientapp.models import ActivityLog
                ActivityLog.objects.create(
                    client=self.client,
                    activity_type='Other',
                    title='QuickBooks Sync',
                    description=f"LPO {self.lpo_number} synced to QuickBooks as Invoice #{invoice.DocNumber}",
                    created_by=user
                )
            except ImportError:
                pass # Skip logging if model not found
            
            return {'success': True, 'message': f"Successfully synced to QuickBooks as Invoice #{invoice.DocNumber}"}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}

class LPOLineItem(models.Model):
    """Line items for LPO"""
    lpo = models.ForeignKey(LPO, on_delete=models.CASCADE, related_name='line_items')
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.product_name} - {self.lpo.lpo_number}"
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class QuoteApprovalToken(models.Model):
    """Secure tokens for external quote approval"""
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='approval_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Token for {self.quote.quote_id}"
    
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()


class SystemAlert(models.Model):
    """System-wide alerts for admin dashboard"""
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock Alert'),
        ('urgent_order', 'Urgent Order'),
        ('payment_due', 'Payment Due'),
        ('system_error', 'System Error'),
        ('new_lead', 'New Lead'),
        ('quote_expired', 'Quote Expired'),
        ('info', 'General Information'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True, help_text="URL to related object")
    
    # Who should see this
    visible_to_admins = models.BooleanField(default=True)
    visible_to_production = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dismissed_alerts')
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects (optional)
    related_client = models.ForeignKey('Client', on_delete=models.CASCADE, null=True, blank=True)
    related_quote = models.ForeignKey('Quote', on_delete=models.CASCADE, null=True, blank=True)
    related_lpo = models.ForeignKey('LPO', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='alerts_created')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_dismissed']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"{self.get_severity_display()} - {self.title}"
    
    def dismiss(self, user):
        """Dismiss this alert"""
        self.is_dismissed = True
        self.dismissed_by = user
        self.dismissed_at = timezone.now()
        self.save()


# =============================================================================
# JOB VENDOR STAGE - Track job progress through different vendors
# =============================================================================
class JobVendorStage(models.Model):
    """Track job progress through different vendor stages"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent_to_vendor', 'Sent to Vendor'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
        ('issues', 'Issues Reported'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='vendor_stages')
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='job_stages')
    stage_order = models.PositiveIntegerField(default=1)  # 1, 2, 3... for multiple vendors
    stage_name = models.CharField(max_length=100)  # e.g., "Printing", "Lamination", "Cutting"
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveIntegerField(default=0)  # 0-100%
    
    # Dates
    started_at = models.DateTimeField(null=True, blank=True)
    expected_completion = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Cost tracking
    vendor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['stage_order']
    
    def __str__(self):
        return f"{self.job.job_number} - Stage {self.stage_order}: {self.stage_name} ({self.vendor.name})"


class JobNote(models.Model):
    """Notes and updates for jobs"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_notes')
    content = models.TextField()
    note_type = models.CharField(max_length=20, default='general', choices=[
        ('general', 'General'),
        ('vendor_update', 'Vendor Update'),
        ('issue', 'Issue'),
        ('resolution', 'Resolution'),
    ])
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note on {self.job.job_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class Payment(models.Model):
    """Payment tracking for invoices/LPOs"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('credit_card', 'Credit Card'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    lpo = models.ForeignKey('LPO', on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='completed')
    reference_number = models.CharField(max_length=100, blank=True, help_text="Transaction ID, Cheque #, etc.")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment {self.reference_number} - KES {self.amount}"



from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Vendor(models.Model):
    """
    Vendor/Supplier model.
    Stores vendor information including VPS (Vendor Performance Score).
    """
    VPS_CHOICES = [
        ('A', 'A - Excellent'),
        ('B', 'B - Good'),
        ('C', 'C - Acceptable'),
    ]
    
    RATING_CHOICES = [
        ('Excellent', 'Excellent'),
        ('Very Good', 'Very Good'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
    ]
    
    PAYMENT_TERMS_CHOICES = [
        ('Net 7', 'Net 7 Days'),
        ('Net 14', 'Net 14 Days'),
        ('Net 30', 'Net 30 Days'),
        ('Prepaid', 'Prepaid'),
        ('Cash on Delivery', 'Cash on Delivery'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
        ('Cash', 'Cash'),
        ('Check', 'Check'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    business_address = models.TextField(blank=True, null=True)
    
    # Business Details
    tax_pin = models.CharField(max_length=50, blank=True, null=True)
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS_CHOICES, blank=True, null=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    
    # Services & Specialization
    services = models.TextField(blank=True, null=True)  # Comma-separated list
    specialization = models.TextField(blank=True, null=True)
    
    # Capacity
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lead_time = models.CharField(max_length=100, blank=True, null=True)  # e.g., "5 days"
    rush_capable = models.BooleanField(default=False)
    
    # Ratings
    quality_rating = models.CharField(max_length=50, choices=RATING_CHOICES, blank=True, null=True)
    reliability_rating = models.CharField(max_length=50, choices=RATING_CHOICES, blank=True, null=True)
    
    # Vendor Performance Score
    vps_score = models.CharField(max_length=1, choices=VPS_CHOICES, default='B')
    vps_score_value = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    
    # Rating (1-5 stars)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    
    # Additional info
    internal_notes = models.TextField(blank=True, null=True)
    internal_notes_updated = models.DateTimeField(blank=True, null=True)
    recommended = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    
    # Legacy field for backward compatibility
    address = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-vps_score_value', 'name']
    
    def __str__(self):
        return f"{self.name} (VPS: {self.vps_score})"


class VendorSpecialty(models.Model):
    """Vendor specialties/capabilities"""
    name = models.CharField(max_length=100)
    vendors = models.ManyToManyField(Vendor, related_name='specialties')
    
    class Meta:
        verbose_name_plural = 'Vendor Specialties'
    
    def __str__(self):
        return self.name





class VendorQuote(models.Model):
    """
    Vendor quote for a specific job.
    Multiple vendors can submit quotes for the same job.
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='vendor_quotes')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='quotes')
    
    # Quote details
    lead_time = models.IntegerField(help_text="Lead time in days")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    selected = models.BooleanField(default=False)
    
    # Special notices or conditions
    notice = models.CharField(max_length=200, blank=True, help_text="e.g., Watch out (2 close misses this month)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['lead_time', 'total_cost']
        unique_together = ['job', 'vendor']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.job.job_number}"



class QCInspection(models.Model):
    """Quality Control Inspection for jobs"""
    INSPECTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('rework', 'Needs Rework'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='qc_inspections')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='qc_inspections', null=True, blank=True)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections')
    
    status = models.CharField(max_length=20, choices=INSPECTION_STATUS_CHOICES, default='pending')
    inspection_date = models.DateTimeField(auto_now_add=True)
    
    # Inspection checklist
    color_accuracy = models.BooleanField(default=False)
    print_quality = models.BooleanField(default=False)
    cutting_accuracy = models.BooleanField(default=False)
    finishing_quality = models.BooleanField(default=False)
    quantity_verified = models.BooleanField(default=False)
    packaging_checked = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"QC for {self.job.job_number} - {self.get_status_display()}"



# Add Delivery model
class Delivery(models.Model):
    """Delivery handoff from PT to AM"""
    STATUS_CHOICES = [
        ('staged', 'Staged - Awaiting Pickup'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Delivery Failed'),
    ]
    
    STAGING_LOCATION_CHOICES = [
        ('shelf-a', 'Shelf A - Urgent/Priority'),
        ('shelf-b', 'Shelf B - Standard/Ready Today'),
        ('shelf-c', 'Shelf C - Future Delivery'),
        ('warehouse', 'Warehouse - Overflow'),
    ]
    
    # Identification
    delivery_number = models.CharField(max_length=50, unique=True, editable=False)
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='delivery')
    qc_inspection = models.OneToOneField(QCInspection, on_delete=models.CASCADE, related_name='delivery', null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='staged')
    
    # Staging
    staging_location = models.CharField(max_length=20, choices=STAGING_LOCATION_CHOICES, default='shelf-b')
    
    # Packaging verification
    packaging_verified = models.JSONField(default=dict, blank=True)
    # Structure: {
    #   "boxes_sealed": true,
    #   "job_labels": true,
    #   "quantity_marked": true,
    #   "total_quantity": true,
    #   "fragile_stickers": false
    # }
    
    # Photos
    package_photos = models.JSONField(default=list, blank=True)  # List of photo URLs/paths
    
    # Notes
    notes_to_am = models.TextField(blank=True)
    
    # Costs
    locked_evp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Handoff confirmation
    handoff_confirmed = models.BooleanField(default=False)
    handoff_confirmed_at = models.DateTimeField(null=True, blank=True)
    handoff_confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deliveries_confirmed')
    
    # Notifications
    notify_am = models.BooleanField(default=True)
    notify_via_email = models.BooleanField(default=True)
    mark_urgent = models.BooleanField(default=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deliveries_created')
    
    class Meta:
        verbose_name_plural = 'Deliveries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.delivery_number} - {self.job.job_number}"
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            # Generate delivery number: DLV-YYYY-XXX
            year = timezone.now().year
            last_delivery = Delivery.objects.filter(
                delivery_number__startswith=f'DLV-{year}-'
            ).order_by('-delivery_number').first()
            
            if last_delivery:
                try:
                    last_num = int(last_delivery.delivery_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.delivery_number = f'DLV-{year}-{new_num:03d}'
        
        super().save(*args, **kwargs)
    
    @property
    def cost_variance(self):
        """Calculate cost variance"""
        if self.locked_evp and self.actual_cost:
            return self.actual_cost - self.locked_evp
        return Decimal('0')
    
    @property
    def cost_variance_percentage(self):
        """Calculate cost variance percentage"""
        if self.locked_evp and self.locked_evp > 0:
            return (self.cost_variance / self.locked_evp) * 100
        return Decimal('0')


# ============================================
# ADD THESE MODELS TO clientapp/models.py
# ============================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class Process(models.Model):
    """Main Process model - represents a production process with pricing logic"""
    
    PRICING_TYPE_CHOICES = [
        ('tier', 'Tier-Based Pricing'),
        ('formula', 'Formula-Based Pricing'),
    ]
    
    CATEGORY_CHOICES = [
        ('outsourced', 'Outsourced'),
        ('in_house', 'In-house'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    # Basic Information
    process_id = models.CharField(max_length=50, unique=True, db_index=True)
    process_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    standard_lead_time = models.IntegerField(help_text="Days")
    
    # Pricing Configuration
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES)
    unit_of_measure = models.CharField(max_length=50, blank=True, null=True)
    
    # Approval Settings
    approval_type = models.CharField(max_length=50, default='auto_approve')
    approval_margin_threshold = models.DecimalField(
        max_digits=5, decimal_places=2, default=25.00
    )
    
    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   related_name='processes_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Process'
        verbose_name_plural = 'Processes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.process_id} - {self.process_name}"
    
    def generate_process_id(self):
        """Auto-generate process ID from name"""
        words = self.process_name.upper().split()
        if len(words) >= 2:
            code = f"PR-{words[0][:3]}-{words[1][:3]}"
        else:
            code = f"PR-{words[0][:6]}"
        
        # Ensure uniqueness
        counter = 1
        original_code = code
        while Process.objects.filter(process_id=code).exists():
            code = f"{original_code}-{counter}"
            counter += 1
        return code
    
    def save(self, *args, **kwargs):
        if not self.process_id:
            self.process_id = self.generate_process_id()
        super().save(*args, **kwargs)


class ProcessTier(models.Model):
    """Quantity tiers for tier-based pricing"""
    
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='tiers')
    tier_number = models.IntegerField()
    
    # Quantity Range
    quantity_from = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_to = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Auto-calculated fields
    per_unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    margin_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['tier_number']
        unique_together = ['process', 'tier_number']
    
    def __str__(self):
        return f"{self.process.process_id} - Tier {self.tier_number}"
    
    def calculate_values(self):
        """Calculate per-unit price and margin"""
        if self.quantity_to > 0:
            self.per_unit_price = self.price / self.quantity_to
        self.margin_amount = self.price - self.cost
        if self.price > 0:
            self.margin_percentage = (self.margin_amount / self.price) * 100
    
    def save(self, *args, **kwargs):
        self.calculate_values()
        super().save(*args, **kwargs)


class ProcessVariable(models.Model):
    """Variables for formula-based pricing"""
    
    VARIABLE_TYPE_CHOICES = [
        ('number', 'Number'),
        ('text', 'Text'),
        ('dropdown', 'Dropdown'),
        ('boolean', 'Boolean'),
    ]
    
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='variables')
    variable_name = models.CharField(max_length=100)
    variable_type = models.CharField(max_length=20, choices=VARIABLE_TYPE_CHOICES)
    unit = models.CharField(max_length=50, blank=True)
    
    # Validation
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    default_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.process.process_id} - {self.variable_name}"


class ProcessVendor(models.Model):
    """Vendors linked to a process"""
    
    PRIORITY_CHOICES = [
        ('preferred', 'Preferred'),
        ('alternative', 'Alternative'),
        ('backup', 'Backup'),
    ]
    
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='process_vendors')
    vendor_name = models.CharField(max_length=200)
    vendor_id = models.CharField(max_length=50)
    vps_score = models.DecimalField(max_digits=5, decimal_places=2, 
                                    help_text="Vendor Performance Score")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='alternative')
    
    # Pricing (stored as JSON for flexibility)
    tier_costs = models.JSONField(null=True, blank=True)
    formula_rates = models.JSONField(null=True, blank=True)
    
    # Rush fees
    rush_enabled = models.BooleanField(default=False)
    rush_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rush_threshold_days = models.IntegerField(default=3)
    
    # Other settings
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    standard_lead_time = models.IntegerField(help_text="Days")
    rush_lead_time = models.IntegerField(help_text="Days", null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['priority', '-vps_score']
    
    def __str__(self):
        return f"{self.process.process_id} - {self.vendor_name}"

class PricingTier(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='pricing_tiers')
    tier_number = models.IntegerField()
    quantity_from = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_to = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['tier_number']
        unique_together = ['process', 'tier_number']
    
    @property
    def margin_amount(self):
        return self.price - self.cost
    
    @property
    def margin_percentage(self):
        if self.cost > 0:
            return ((self.price - self.cost) / self.cost) * 100
        return 0
    
    @property
    def per_unit_price(self):
        if self.quantity_to > 0:
            return self.price / self.quantity_to
        return 0
    
    def __str__(self):
        return f"Tier {self.tier_number}: {self.quantity_from}-{self.quantity_to}"


# class Vendor(models.Model):
#     vendor_id = models.CharField(max_length=50, unique=True)
#     name = models.CharField(max_length=255)
#     vps_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Vendor Performance Score")
#     is_active = models.BooleanField(default=True)
    
#     def __str__(self):
#         return f"{self.name} ({self.vps_score}%)"





class VendorTierPricing(models.Model):
    process_vendor = models.ForeignKey(ProcessVendor, on_delete=models.CASCADE, related_name='tier_pricing')
    tier_number = models.IntegerField()
    quantity_from = models.IntegerField()
    quantity_to = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['tier_number']
        unique_together = ['process_vendor', 'tier_number']
    
    def __str__(self):
        return f"{self.process_vendor.vendor.name} - Tier {self.tier_number}"

class Notification(models.Model):
    """Notification system for all users"""
    NOTIFICATION_TYPES = [
        ('lead_created', 'New Lead Created'),
        ('quote_reminder', 'Quote Creation Reminder'),
        ('quote_approved', 'Quote Approved by Client'),
        ('quote_sent_pt', 'Quote Sent to PT for Approval'),
        ('convert_lead', 'Convert Lead to Client'),
        ('delivery_ready', 'Delivery Ready for AM'),
        ('job_completed', 'Job Completed'),
        ('general', 'General Notification'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related objects
    related_lead = models.ForeignKey('Lead', on_delete=models.CASCADE, null=True, blank=True)
    related_quote_id = models.CharField(max_length=50, null=True, blank=True)
    related_job = models.ForeignKey('Job', on_delete=models.CASCADE, null=True, blank=True)
    
    # Action button data
    action_url = models.CharField(max_length=500, blank=True, null=True)
    action_label = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Convert to Client", "Create Quote"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"


class Delivery(models.Model):
    """Delivery tracking for completed jobs"""
    STAGING_LOCATION_CHOICES = [
        ('shelf-a', 'Shelf A'),
        ('shelf-b', 'Shelf B'),
        ('shelf-c', 'Shelf C'),
        ('counter', 'Counter'),
        ('warehouse', 'Warehouse'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('staged', 'Staged for Pickup'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]
    
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='delivery')
    
    # Staging
    staging_location = models.CharField(max_length=50, choices=STAGING_LOCATION_CHOICES, default='shelf-b')
    notes_to_am = models.TextField(blank=True)
    
    # Packaging verification (stored as JSON)
    packaging_verified = models.JSONField(default=dict, blank=True)
    
    # Costs
    locked_evp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Handoff confirmation
    handoff_confirmed = models.BooleanField(default=False)
    handoff_confirmed_at = models.DateTimeField(null=True, blank=True)
    handoff_confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handoffs_confirmed')
    
    # Notification settings
    notify_am = models.BooleanField(default=True)
    notify_via_email = models.BooleanField(default=True)
    mark_urgent = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deliveries_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Deliveries"
    
    def __str__(self):
        return f"Delivery for {self.job.job_number}"
    
    def get_staging_location_display(self):
        return dict(self.STAGING_LOCATION_CHOICES).get(self.staging_location, self.staging_location)


class AuditLog(models.Model):
    """Audit log for tracking admin actions"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    object_repr = models.CharField(max_length=200, null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
            models.Index(fields=['timestamp']),
        ]
        
    def __str__(self):
        return f"{self.user} - {self.action} {self.model_name} - {self.timestamp}"


class SystemSetting(models.Model):
    """System-wide settings"""
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=200, blank=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"


class ProcessVariableRange(models.Model):
    """Ranges for formula-based pricing variables"""
    variable = models.ForeignKey(
        'ProcessVariable',
        on_delete=models.CASCADE,
        related_name='ranges'
    )
    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum value for this range"
    )
    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum value for this range"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base price for this range (KES)"
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.0,
        help_text="Multiplier rate for this range"
    )
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'min_value']
        verbose_name = "Variable Range"
        verbose_name_plural = "Variable Ranges"
    
    def __str__(self):
        return f"{self.variable.variable_name}: {self.min_value}-{self.max_value}"
    
    def applies_to(self, value):
        """Check if this range applies to a given value"""
        return self.min_value <= Decimal(str(value)) <= self.max_value