# clients/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import timedelta
from decimal import Decimal

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


class Product(models.Model):
    """Product catalog entries maintained by the production team"""

    # Add category field
    CATEGORY_CHOICES = [
        ('business_cards', 'Business Cards'),
        ('brochures', 'Brochures & Flyers'),
        ('posters', 'Posters & Banners'),
        ('t-shirts', 'T-Shirts & Apparel'),
        ('mugs', 'Mugs & Drinkware'),
        ('bags', 'Bags & Totes'),
        ('stickers', 'Stickers & Labels'),
        ('signage', 'Signage & Displays'),
        ('packaging', 'Packaging'),
        ('other', 'Other'),
    ]

    PRODUCT_TYPE_CHOICES = [
        ('non_custom', 'Non-Custom'),
        ('semi_custom', 'Semi-Custom'),
        ('custom', 'Custom'),
    ]

    AVAILABILITY_CHOICES = [
        ('always', 'Always Available'),
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('lead_time', 'Lead Time'),
    ]

    # Add category field first
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='other',
        help_text="Product category for organization"
    )
    
    sku = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='non_custom')
    base_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='always')
    stock_quantity = models.PositiveIntegerField(default=0)
    lead_time = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products_updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
            models.Index(fields=['product_type']),
            models.Index(fields=['availability']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.sku:
            year = timezone.now().year
            prefix = f'PRD-{year}-'
            last_product = Product.objects.filter(sku__startswith=prefix).order_by('sku').last()
            if last_product:
                try:
                    last_number = int(last_product.sku.split('-')[-1])
                except (ValueError, IndexError):
                    last_number = 0
                new_number = last_number + 1
            else:
                new_number = 1
            self.sku = f'{prefix}{new_number:03d}'

        super().save(*args, **kwargs)
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