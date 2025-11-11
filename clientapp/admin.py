from django.contrib import admin
from .models import (
    Lead, Client, ClientContact, BrandAsset, ComplianceDocument,
    Product, Quote, ActivityLog, ProductionUpdate, Notification,
    Job, JobProduct, JobAttachment
)

# ---------------------- LEAD ----------------------
@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'lead_id', 'name', 'email', 'phone', 'status',
        'source', 'preferred_contact', 'created_at', 'converted_to_client'
    )
    search_fields = ('name', 'email', 'phone', 'lead_id')
    list_filter = ('status', 'source', 'preferred_contact', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('lead_id', 'created_at', 'updated_at')


# ---------------------- CLIENT CONTACT INLINE ----------------------
class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 1


# ---------------------- BRAND ASSET INLINE ----------------------
class BrandAssetInline(admin.TabularInline):
    model = BrandAsset
    extra = 1


# ---------------------- COMPLIANCE DOCUMENT INLINE ----------------------
class ComplianceDocumentInline(admin.TabularInline):
    model = ComplianceDocument
    extra = 1


# ---------------------- CLIENT ----------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'client_id', 'name', 'email', 'phone', 'client_type',
        'company', 'status', 'risk_rating', 'payment_terms', 'created_at'
    )
    search_fields = ('client_id', 'name', 'email', 'phone', 'company')
    list_filter = ('status', 'client_type', 'risk_rating', 'payment_terms', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('client_id', 'created_at', 'updated_at', 'last_activity')
    inlines = [ClientContactInline, BrandAssetInline, ComplianceDocumentInline]


# ---------------------- BRAND ASSET ----------------------
@admin.register(BrandAsset)
class BrandAssetAdmin(admin.ModelAdmin):
    list_display = ('client', 'asset_type', 'description', 'uploaded_by', 'uploaded_at')
    list_filter = ('asset_type', 'uploaded_at')
    search_fields = ('client__name', 'asset_type', 'description')
    ordering = ('-uploaded_at',)
    autocomplete_fields = ['client']


# ---------------------- COMPLIANCE DOCUMENT ----------------------
@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display = ('client', 'document_type', 'expiry_date', 'is_expired', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at', 'expiry_date')
    search_fields = ('client__name', 'document_type')
    ordering = ('-uploaded_at',)
    autocomplete_fields = ['client']


# ---------------------- QUOTE ----------------------
@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Admin configuration for Quote model"""
    
    list_display = (
        'quote_id', 'product_name', 'client', 'lead',
        'quantity', 'unit_price', 'total_amount', 'production_status',
        'status', 'payment_terms', 'include_vat',
        'quote_date', 'valid_until', 'is_expired', 'days_until_expiry',
        'created_by', 'costed_by', 'created_at',
    )
    list_filter = ('status', 'production_status', 'payment_terms', 'include_vat', 'quote_date', 'valid_until')
    search_fields = ('quote_id', 'product_name', 'client__name', 'lead__name')
    date_hierarchy = 'quote_date'
    ordering = ('-created_at',)
    readonly_fields = ('quote_id', 'total_amount', 'created_at', 'updated_at', 'approved_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('quote_id', 'client', 'lead', 'product_name', 'quantity', 'unit_price', 'total_amount')
        }),
        ('Quote Details', {
            'fields': ('payment_terms', 'status', 'production_status', 'include_vat', 'quote_date', 'valid_until', 'due_date', 'approved_at')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms', 'loss_reason', 'production_cost', 'production_notes')
        }),
        ('Tracking', {
            'fields': ('created_by', 'costed_by', 'created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        """Auto-assign created_by to the logged-in user"""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'product_type', 'base_price', 'availability', 'stock_quantity', 'is_active']
    list_filter = ['category', 'product_type', 'availability', 'is_active']
    search_fields = ['sku', 'name', 'description']
    ordering = ['category', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description')
        }),
        ('Pricing', {
            'fields': ('base_price',)
        }),
        ('Product Details', {
            'fields': ('product_type', 'availability', 'stock_quantity', 'lead_time')
        }),
        ('Management', {
            'fields': ('is_active', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['sku', 'created_by', 'updated_by', 'created_at', 'updated_at']


@admin.register(ProductionUpdate)
class ProductionUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'update_type', 'quote', 'job', 'status', 'progress', 'created_by', 'created_at'
    )
    search_fields = ('quote__quote_id', 'job__job_number', 'notes')
    list_filter = ('update_type', 'status', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    list_filter = ('is_read', 'created_at')
    ordering = ('-created_at',)

# ---------------------- ACTIVITY LOG ----------------------
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'activity_type', 'title', 'created_by', 'created_at')
    search_fields = ('client__name', 'title', 'activity_type')
    list_filter = ('activity_type', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    autocomplete_fields = ['client', 'related_quote']


# ---------------------- JOB PRODUCT INLINE ----------------------
class JobProductInline(admin.TabularInline):
    model = JobProduct
    extra = 1


# ---------------------- JOB ATTACHMENT INLINE ----------------------
class JobAttachmentInline(admin.TabularInline):
    model = JobAttachment
    extra = 1


# ---------------------- JOB ----------------------
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'job_number', 'job_name', 'client', 'job_type', 'priority',
        'status', 'start_date', 'expected_completion', 'created_at'
    )
    search_fields = ('job_number', 'job_name', 'client__name', 'person_in_charge')
    list_filter = ('job_type', 'priority', 'status', 'start_date', 'expected_completion')
    ordering = ('-created_at',)
    date_hierarchy = 'start_date'
    readonly_fields = ('job_number', 'created_at', 'updated_at')
    inlines = [JobProductInline, JobAttachmentInline]
    autocomplete_fields = ['client']


# ---------------------- JOB PRODUCT ----------------------
@admin.register(JobProduct)
class JobProductAdmin(admin.ModelAdmin):
    list_display = ('job', 'product_name', 'quantity', 'unit', 'created_at')
    search_fields = ('product_name', 'job__job_number')
    ordering = ('-created_at',)
    autocomplete_fields = ['job']


# ---------------------- JOB ATTACHMENT ----------------------
@admin.register(JobAttachment)
class JobAttachmentAdmin(admin.ModelAdmin):
    list_display = ('job', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at')
    search_fields = ('job__job_number', 'file_name')
    ordering = ('-uploaded_at',)
    autocomplete_fields = ['job']
