"""
Storefront Models for Public/Customer-Facing Features
Includes: EstimateQuote, Customer profiles,
Messaging, Chatbot, and Production Units

NOTE: StorefrontProduct is defined in models.py (line ~5625)
to avoid model conflicts. This file contains other storefront models only.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
import uuid
import json


class EstimateQuote(models.Model):
    """
    Draft/Estimate Quote created by customer from storefront
    Not yet in system - anonymous or awaiting AM review
    """
    STATUS_CHOICES = [
        ('draft_unsaved', 'Draft - Not Saved'),
        ('shared_with_am', 'Shared with Account Manager'),
        ('converted_to_quote', 'Converted to Official Quote'),
        ('archived', 'Archived'),
    ]
    
    estimate_id = models.CharField(max_length=20, unique=True, editable=False)
    share_token = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Public share token for viewing estimate"
    )
    
    # Customer information
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_company = models.CharField(max_length=255, blank=True)
    
    # Quote details
    line_items = models.JSONField(
        default=list,
        help_text="Line items: [{product_id, quantity, properties, notes, unit_price, line_total}]"
    )
    subtotal = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Options
    turnaround_time = models.CharField(
        max_length=50,
        choices=[
            ('standard', 'Standard (7 days)'),
            ('rush', 'Rush (3 days)'),
            ('expedited', 'Expedited (1 day)'),
        ],
        default='standard'
    )
    delivery_method = models.CharField(
        max_length=50,
        choices=[
            ('pickup', 'Pickup'),
            ('courier_nairobi', 'Courier (Nairobi)'),
            ('courier_nationwide', 'Courier (Nationwide)'),
        ],
        blank=True
    )
    payment_terms = models.CharField(
        max_length=50,
        choices=[
            ('prepaid', 'Prepaid (Full payment before production)'),
            ('net7', 'Net 7 Days'),
            ('net15', 'Net 15 Days'),
            ('net30', 'Net 30 Days'),
        ],
        default='prepaid'
    )
    special_notes = models.TextField(blank=True)
    
    # Status & sharing
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='draft_unsaved',
        db_index=True
    )
    shared_via = models.CharField(
        max_length=50,
        choices=[
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
            ('direct_link', 'Direct Link'),
        ],
        blank=True
    )
    share_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Conversion tracking
    converted_quote_id = models.CharField(
        max_length=20,
        blank=True,
        help_text="Quote ID after conversion"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Estimate expires after this date"
    )
    source = models.CharField(
        max_length=50,
        choices=[
            ('storefront_public', 'Storefront - Public'),
            ('storefront_customer', 'Storefront - Registered Customer'),
        ],
        default='storefront_public'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['share_token']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"{self.estimate_id} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.estimate_id:
            # Generate estimate ID: EST-YYYY-XXXXX
            year = timezone.now().year
            last = EstimateQuote.objects.filter(
                estimate_id__startswith=f'EST-{year}'
            ).order_by('-estimate_id').first()
            
            if last:
                num = int(last.estimate_id.split('-')[-1]) + 1
            else:
                num = 1
            
            self.estimate_id = f'EST-{year}-{str(num).zfill(5)}'
        
        if not self.share_token:
            self.share_token = str(uuid.uuid4())
        
        # Set expiration (7 days from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        
        super().save(*args, **kwargs)


class Customer(models.Model):
    """
    Storefront customer account
    Created when customer registers on storefront
    """
    CUSTOMER_TYPE_CHOICES = [
        ('b2b', 'B2B - Business'),
        ('b2c', 'B2C - Retail'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='storefront_customer')
    customer_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Contact info
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=255, blank=True)
    
    # Account details
    profile_picture = models.URLField(blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    customer_type = models.CharField(
        max_length=10,
        choices=CUSTOMER_TYPE_CHOICES,
        default='b2b'
    )
    
    # Sales notes
    notes = models.TextField(blank=True)
    
    # Preferences
    communication_channel = models.CharField(
        max_length=50,
        choices=[
            ('email', 'Email'),
            ('whatsapp', 'WhatsApp'),
            ('call', 'Phone Call'),
            ('chat', 'Chat'),
        ],
        default='email'
    )
    language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('sw', 'Swahili'),
            ('es', 'Spanish'),
        ],
        default='en'
    )
    newsletter_subscribed = models.BooleanField(default=False)
    
    # Relationships
    linked_client = models.OneToOneField(
        'Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='storefront_customer'
    )
    linked_lead = models.OneToOneField(
        'Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='storefront_customer'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['customer_type']),
        ]
    
    def __str__(self):
        return f"{self.customer_id} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.customer_id:
            # Generate customer ID: CUST-YYYY-XXXXX
            year = timezone.now().year
            last = Customer.objects.filter(
                customer_id__startswith=f'CUST-{year}'
            ).order_by('-customer_id').first()
            
            if last:
                num = int(last.customer_id.split('-')[-1]) + 1
            else:
                num = 1
            
            self.customer_id = f'CUST-{year}-{str(num).zfill(5)}'
        
        super().save(*args, **kwargs)


class StorefrontMessage(models.Model):
    """
    Messages from chatbot, email inquiries, WhatsApp, phone requests
    Tracks all customer communication
    """
    MESSAGE_TYPE_CHOICES = [
        ('chat', 'Chatbot Chat'),
        ('email_inquiry', 'Email Inquiry'),
        ('whatsapp_inquiry', 'WhatsApp Inquiry'),
        ('call_request', 'Call Request'),
        ('contact_form', 'Contact Form'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('archived', 'Archived'),
    ]
    
    message_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # From customer
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages'
    )
    
    # For anonymous users
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Message details
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPE_CHOICES)
    subject = models.CharField(max_length=255, blank=True)
    message_content = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    
    # Communication
    channel = models.CharField(
        max_length=50,
        choices=[
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('chat', 'Chat'),
        ]
    )
    
    # Status & assignment
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_messages',
        help_text="Account Manager assigned to handle"
    )
    
    # Response
    response_message = models.TextField(blank=True)
    response_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    related_estimate_quote = models.ForeignKey(
        EstimateQuote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['message_type']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.message_id} - {self.message_type}"
    
    def save(self, *args, **kwargs):
        if not self.message_id:
            # Generate message ID: MSG-YYYY-XXXXX
            year = timezone.now().year
            last = StorefrontMessage.objects.filter(
                message_id__startswith=f'MSG-{year}'
            ).order_by('-message_id').first()
            
            if last:
                num = int(last.message_id.split('-')[-1]) + 1
            else:
                num = 1
            
            self.message_id = f'MSG-{year}-{str(num).zfill(5)}'
        
        super().save(*args, **kwargs)


class ChatbotConversation(models.Model):
    """
    Stores chatbot conversation history
    Enables context awareness and conversation tracking
    """
    conversation_id = models.CharField(max_length=100, unique=True, editable=False)
    
    # Participants
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chatbot_conversations'
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Session ID for anonymous users"
    )
    
    # Messages (JSON array)
    messages = models.JSONField(
        default=list,
        help_text="[{timestamp, sender: 'customer'|'bot', text, action, metadata}]"
    )
    
    # Context & state
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Collected info: {name, email, phone, product_interest, ...}"
    )
    
    # Status
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    
    # Escalation
    escalated_to_human = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_conversations'
    )
    
    # Related objects
    related_estimate_quote = models.ForeignKey(
        EstimateQuote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chatbot_conversations'
    )
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['escalated_to_human']),
        ]
    
    def __str__(self):
        return f"{self.conversation_id}"
    
    def save(self, *args, **kwargs):
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())
        super().save(*args, **kwargs)


class QuotePricingSnapshot(models.Model):
    """
    Audit trail for quote pricing changes
    Tracks estimate creation, AM adjustments, approvals
    """
    SNAPSHOT_TYPE_CHOICES = [
        ('estimate_created', 'Estimate Created'),
        ('adjusted_by_am', 'Adjusted by Account Manager'),
        ('approved_by_customer', 'Approved by Customer'),
        ('quote_created', 'Quote Created'),
        ('quote_adjusted', 'Quote Adjusted'),
    ]
    
    snapshot_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # Related quote/estimate
    estimate_quote = models.ForeignKey(
        EstimateQuote,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pricing_snapshots'
    )
    quote_id = models.CharField(max_length=20, blank=True)  # For quotes in main system
    
    # Pricing data
    snapshot_type = models.CharField(max_length=50, choices=SNAPSHOT_TYPE_CHOICES)
    base_amount = models.DecimalField(max_digits=15, decimal_places=2)
    adjustments = models.JSONField(default=dict, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Who made the change
    applied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pricing_snapshots_created'
    )
    reason = models.TextField(blank=True)
    
    # Timestamp
    snapshot_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-snapshot_at']
        indexes = [
            models.Index(fields=['estimate_quote', 'snapshot_type']),
            models.Index(fields=['snapshot_type']),
        ]
    
    def __str__(self):
        return f"{self.snapshot_id} - {self.snapshot_type}"
    
    def save(self, *args, **kwargs):
        if not self.snapshot_id:
            self.snapshot_id = f"SNAP-{timezone.now().timestamp()}"
        super().save(*args, **kwargs)


class ProductionUnit(models.Model):
    """
    Represents a single task/production unit within a job
    Jobs can be broken down into multiple units sent to different vendors
    """
    UNIT_TYPE_CHOICES = [
        ('material_sourcing', 'Material Sourcing'),
        ('design_preparation', 'Design Preparation'),
        ('production', 'Production'),
        ('quality_check', 'Quality Check'),
        ('packaging', 'Packaging'),
        ('delivery', 'Delivery'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending_po', 'Pending PO'),
        ('po_sent', 'PO Sent'),
        ('accepted', 'Accepted by Vendor'),
        ('in_progress', 'In Progress'),
        ('delayed', 'Delayed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    unit_id = models.CharField(max_length=30, unique=True, editable=False)
    
    # Job relationship
    job = models.ForeignKey(
        'Job',
        on_delete=models.CASCADE,
        related_name='production_units'
    )
    
    # Unit details
    unit_sequence = models.IntegerField(
        help_text="Order of execution (1, 2, 3, ...)"
    )
    unit_type = models.CharField(max_length=50, choices=UNIT_TYPE_CHOICES)
    task_description = models.TextField()
    
    # Vendor
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_units'
    )
    
    # Quantities & costs
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_measure = models.CharField(max_length=50, blank=True, default='units')
    estimated_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    actual_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timeline
    estimated_timeline_days = models.IntegerField(validators=[MinValueValidator(1)])
    expected_start_date = models.DateField(null=True, blank=True)
    expected_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Status & tracking
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending_po',
        db_index=True
    )
    
    # PO relationship
    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_units'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['job', 'unit_sequence']
        unique_together = ('job', 'unit_sequence')
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['vendor']),
        ]
    
    def __str__(self):
        return f"{self.unit_id} - {self.job.job_number}"
    
    def save(self, *args, **kwargs):
        if not self.unit_id:
            # Generate: UNIT-JOB-YYYY-SEQ
            if self.job:
                self.unit_id = f"UNIT-{self.job.job_number}-{str(self.unit_sequence).zfill(2)}"
        super().save(*args, **kwargs)
