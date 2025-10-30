from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Lead, Client, ClientContact, 
    BrandAsset, ComplianceDocument, Quote, 
    ActivityLog
)

# --- INLINE MODELS ---

class ClientContactInline(admin.TabularInline):
    """Allows editing of Client Contacts directly on the Client page."""
    model = ClientContact
    extra = 1
    fields = ('full_name', 'email', 'phone', 'role', 'is_primary')
    
class BrandAssetInline(admin.TabularInline):
    """Allows viewing/adding Brand Assets on the Client page."""
    model = BrandAsset
    extra = 0
    fields = ('asset_type', 'file', 'description', 'uploaded_by')
    readonly_fields = ('uploaded_by',) # Set automatically on save

class ComplianceDocumentInline(admin.TabularInline):
    """Allows viewing/adding Compliance Documents on the Client page."""
    model = ComplianceDocument
    extra = 0
    fields = ('document_type', 'file', 'expiry_date', 'is_expired', 'expires_soon', 'notes', 'uploaded_by')
    readonly_fields = ('is_expired', 'expires_soon', 'uploaded_by')

class QuoteInline(admin.TabularInline):
    """Allows viewing Quotes associated with a Client or Lead."""
    model = Quote
    extra = 0
    fields = ('quote_id', 'product_name', 'status', 'total_amount', 'valid_until')
    readonly_fields = ('quote_id', 'total_amount')
    show_change_link = True # Allows quick navigation to the Quote detail page

class ActivityLogInline(admin.TabularInline):
    """Allows viewing/adding Activity Logs on the Client page."""
    model = ActivityLog
    extra = 1
    fields = ('activity_type', 'title', 'description', 'related_quote', 'created_by')
    readonly_fields = ('created_by',)


# --- MODEL ADMINS ---

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin configuration for the Lead model."""
    list_display = ('lead_id', 'name', 'email', 'phone', 'status', 'source', 'preferred_contact', 'follow_up_date', 'created_at', 'created_by')
    list_filter = ('status', 'source', 'preferred_contact', 'converted_to_client')
    search_fields = ('lead_id', 'name', 'email', 'phone', 'product_interest')
    readonly_fields = ('lead_id', 'created_at', 'updated_at', 'converted_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ("Lead Details", {
            'fields': ('lead_id', 'name', 'email', 'phone', 'product_interest', 'preferred_contact')
        }),
        ("Status & Source", {
            'fields': ('status', 'source', 'follow_up_date', 'notes')
        }),
        ("Conversion Tracking", {
            'fields': ('converted_to_client', 'converted_at', 'created_by')
        }),
    )

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin configuration for the Client model."""
    list_display = (
        'client_id', 'name', 'company', 'client_type', 'email', 
        'phone', 'status', 'risk_rating', 'display_total_revenue', 
        'get_last_activity_display'
    )
    list_filter = ('status', 'client_type', 'risk_rating', 'payment_terms', 'is_reseller')
    search_fields = ('client_id', 'name', 'company', 'email', 'phone', 'vat_tax_id')
    readonly_fields = (
        'client_id', 'created_at', 'updated_at', 'last_activity', 
        'total_jobs', 'total_revenue', 'conversion_rate', 'get_last_activity_display',
        'converted_from_lead'
    )
    date_hierarchy = 'created_at'
    inlines = [
        ClientContactInline, QuoteInline, ActivityLogInline,
        BrandAssetInline, ComplianceDocumentInline 
    ]
    
    fieldsets = (
        ("Basic Information", {
            'fields': ('client_id', 'client_type', 'name', 'company', 'email', 'phone', 'industry')
        }),
        ("Business & Compliance", {
            'fields': ('vat_tax_id', 'kra_pin', 'address', 'is_reseller', 'converted_from_lead')
        }),
        ("Financial & Terms", {
            'fields': ('payment_terms', 'credit_limit', 'default_markup', 'risk_rating')
        }),
        ("Activity & Management", {
            'fields': ('status', 'preferred_channel', 'lead_source', 'account_manager', 'onboarded_by', 'last_activity'),
        }),
        ("Key Metrics", {
            'fields': ('total_jobs', 'total_revenue', 'conversion_rate', 'get_last_activity_display'),
            'classes': ('collapse',)
        }),
    )

    def display_total_revenue(self, obj):
        """Custom display for revenue formatted as currency."""
        return f"Ksh {obj.total_revenue:,.2f}"
    display_total_revenue.short_description = 'Total Revenue'


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Admin configuration for the Quote model."""
    list_display = ('quote_id', 'client', 'product_name', 'status', 'quantity', 'selling_price', 'total_amount', 'quote_date', 'valid_until', 'created_by')
    list_filter = ('status', 'quote_date', 'valid_until')
    search_fields = ('quote_id', 'product_name', 'client__name')
    readonly_fields = ('quote_id', 'total_amount', 'margin_amount', 'margin_percentage', 'created_at', 'updated_at', 'approved_at')
    date_hierarchy = 'quote_date'
    raw_id_fields = ('client', 'lead') # Useful for many clients/leads
    
    fieldsets = (
        ("Quote Identification", {
            'fields': ('quote_id', 'client', 'lead', 'product_name', 'quantity', 'status')
        }),
        ("Pricing & Margins", {
            'fields': ('cost_price', 'markup_percentage', 'selling_price', 'total_amount', 'margin_amount', 'margin_percentage')
        }),
        ("Dates & Tracking", {
            'fields': ('quote_date', 'valid_until', 'due_date', 'approved_at', 'created_by', 'created_at')
        }),
        ("Notes & Loss", {
            'fields': ('notes', 'loss_reason')
        }),
    )

# --- Register remaining models using default options ---
admin.site.register(ClientContact) # Managed via Inline
admin.site.register(BrandAsset) # Managed via Inline
admin.site.register(ComplianceDocument) # Managed via Inline
admin.site.register(ActivityLog) # Managed via Inline