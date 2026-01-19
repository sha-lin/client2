from rest_framework import serializers
from django.contrib.auth.models import User, Group

from .models import (
    Lead,
    Client,
    ClientContact,
    BrandAsset,
    ComplianceDocument,
    Product,
    Quote,
    QuoteLineItem,
    Job,
    Vendor,
    LPO,
    Payment,
    Notification,
    ActivityLog,
    PropertyType,
    PropertyValue,
    ProductProperty,
    QuantityPricing,
    TurnAroundTime,
    SystemSetting,
    # Costing / process models
    Process,
    ProcessTier,
    ProcessVariable,
    ProductVariable,
    ProductVariableOption,
    ProcessVendor,
    PricingTier,
    VendorTierPricing,
    ProcessVariableRange,
    # Product metadata
    ProductImage,
    ProductVideo,
    ProductDownloadableFile,
    ProductSEO,
    ProductReviewSettings,
    ProductFAQ,
    ProductShipping,
    ProductLegal,
    ProductProduction,
    ProductChangeHistory,
    ProductTemplate,
    # Operations / QC / delivery / attachments
    JobVendorStage,
    JobNote,
    JobAttachment,
    VendorQuote,
    QCInspection,
    Delivery,
    QuoteAttachment,
    LPOLineItem,
    SystemAlert,
    ProductionUpdate,
    # Storefront models
    Customer,
    CustomerAddress,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Coupon,
    TaxConfiguration,
    DesignTemplate,
    DesignState,
    ProductReview,
    ShippingMethod,
    PaymentTransaction,
    #webhook and other models
    ProductRule,
    TimelineEvent,
    DesignSession,
    DesignVersion,
    ProofApproval,
    Shipment,
    Promotion,
    MaterialInventory,
    Refund,
    CreditNote,
    Adjustment,
    WebhookSubscription,
    WebhookDelivery,

    # Vendor Portal models
    PurchaseOrder,
    VendorInvoice,
    PurchaseOrderProof,
    PurchaseOrderIssue,
    PurchaseOrderNote,
    MaterialSubstitutionRequest,
)


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = "__all__"


class ClientContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContact
        fields = "__all__"


class ClientSerializer(serializers.ModelSerializer):
    contacts = ClientContactSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = "__all__"

    def validate(self, attrs):
        """
        Enforce different field rules for B2B vs B2C clients.
        """
        client_type = attrs.get("client_type")
        if self.instance and not client_type:
            client_type = self.instance.client_type

        if client_type == "B2C":
            # Fields that should not be set for B2C clients
            b2b_only_fields = [
                "company",
                "vat_tax_id",
                "kra_pin",
                "industry",
                "credit_limit",
                "default_markup",
                "risk_rating",
                "is_reseller",
            ]
            invalid_fields = [f for f in b2b_only_fields if attrs.get(f)]
            if invalid_fields:
                raise serializers.ValidationError(
                    {"detail": f"Fields {', '.join(invalid_fields)} are only allowed for B2B clients."}
                )

        return super().validate(attrs)

    def to_representation(self, instance):
        """
        Remove B2B-specific fields from the response if the client is B2C.
        This keeps the API response clean and only shows relevant fields.
        """
        ret = super().to_representation(instance)
        
        if instance.client_type == 'B2C':
            # B2B-specific fields to hide for B2C clients
            b2b_fields = [
                'company',
                'vat_tax_id',
                'kra_pin',
                'industry',
                'payment_terms',
                'credit_limit',
                'default_markup',
                'risk_rating',
                'is_reseller',
            ]
            for field in b2b_fields:
                ret.pop(field, None)
        
        return ret


class BrandAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandAsset
        fields = "__all__"


class ComplianceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceDocument
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = "__all__"


class PropertyValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyValue
        fields = "__all__"


class ProductPropertySerializer(serializers.ModelSerializer):
    property_value = PropertyValueSerializer(read_only=True)

    class Meta:
        model = ProductProperty
        fields = "__all__"


class QuantityPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantityPricing
        fields = "__all__"


class TurnAroundTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurnAroundTime
        fields = "__all__"


class QuoteLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteLineItem
        fields = "__all__"


class QuoteSerializer(serializers.ModelSerializer):
    line_items = QuoteLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Quote
        fields = "__all__"


class JobSerializer(serializers.ModelSerializer):
    person_in_charge_name = serializers.CharField(source='person_in_charge.get_full_name', read_only=True)
    person_in_charge_email = serializers.EmailField(source='person_in_charge.email', read_only=True)
    
    class Meta:
        model = Job
        fields = "__all__"


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class LPOSerializer(serializers.ModelSerializer):
    class Meta:
        model = LPO
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = "__all__"


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = "__all__"


# ===== Costing / Process Serializers =====

class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = "__all__"


class ProcessTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessTier
        fields = "__all__"


class ProcessVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessVariable
        fields = "__all__"


class ProductVariableOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariableOption
        fields = "__all__"


class ProductVariableSerializer(serializers.ModelSerializer):
    options = ProductVariableOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariable
        fields = "__all__"


class ProcessVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessVendor
        fields = "__all__"


class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingTier
        fields = "__all__"


class VendorTierPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorTierPricing
        fields = "__all__"


class ProcessVariableRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessVariableRange
        fields = "__all__"


# ===== Product Metadata Serializers =====

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "__all__"


class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = "__all__"


class ProductDownloadableFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDownloadableFile
        fields = "__all__"


class ProductSEOSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSEO
        fields = "__all__"


class ProductReviewSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReviewSettings
        fields = "__all__"


class ProductFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFAQ
        fields = "__all__"


class ProductShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductShipping
        fields = "__all__"


class ProductLegalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLegal
        fields = "__all__"


class ProductProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductProduction
        fields = "__all__"


class ProductChangeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductChangeHistory
        fields = "__all__"


class ProductTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTemplate
        fields = "__all__"


# ===== QC, Delivery, Attachments, Notes =====

class JobVendorStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobVendorStage
        fields = "__all__"


class JobNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobNote
        fields = "__all__"


class JobAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAttachment
        fields = "__all__"


class VendorQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorQuote
        fields = "__all__"


class QCInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCInspection
        fields = "__all__"


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"


class QuoteAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteAttachment
        fields = "__all__"


class LPOLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LPOLineItem
        fields = "__all__"


class SystemAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemAlert
        fields = "__all__"


class ProductionUpdateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    job_number = serializers.CharField(source='job.job_number', read_only=True)
    quote_id = serializers.CharField(source='quote.quote_id', read_only=True)
    
    class Meta:
        model = ProductionUpdate
        fields = "__all__"
    
    def validate(self, attrs):
        """Ensure either job or quote is provided"""
        job = attrs.get('job') or (self.instance.job if self.instance else None)
        quote = attrs.get('quote') or (self.instance.quote if self.instance else None)
        
        if not job and not quote:
            raise serializers.ValidationError("Either job or quote must be provided.")
        
        if job and quote:
            raise serializers.ValidationError("Cannot provide both job and quote.")
        
        return attrs


# ===== User / Group Serializers =====

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "is_superuser"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


# ============================================================================
# STOREFRONT ECOMMERCE SERIALIZERS
# ============================================================================

class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    matched_client_name = serializers.CharField(source='matched_client.name', read_only=True)
    
    class Meta:
        model = Customer
        fields = "__all__"
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = "__all__"


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = "__all__"
    
    def get_product_image(self, obj):
        # Get first product image if available
        first_image = obj.product.product_images.first()
        if first_image:
            return first_image.image.url if hasattr(first_image.image, 'url') else ''
        return ''


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    
    class Meta:
        model = Cart
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ['order_number', 'created_at', 'updated_at']


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class TaxConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxConfiguration
        fields = "__all__"


class DesignTemplateSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = DesignTemplate
        fields = "__all__"


class DesignStateSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = DesignState
        fields = "__all__"


class ProductReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at', 'helpful_count']


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = "__all__"


class PaymentTransactionSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at', 'initiated_at']



class ProductRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRule
        fields = "__all__"

class TimelineEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.get_full_name', read_only=True)
    class Meta:
        model = TimelineEvent
        fields = "__all__"

class DesignVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignVersion
        fields = "__all__"

class DesignSessionSerializer(serializers.ModelSerializer):
    versions = DesignVersionSerializer(many=True, read_only=True)
    class Meta:
        model = DesignSession
        fields = "__all__"

class ProofApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProofApproval
        fields = "__all__"

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = "__all__"

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = "__all__"

class MaterialInventorySerializer(serializers.ModelSerializer):
    available_stock = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    class Meta:
        model = MaterialInventory
        fields = "__all__"

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = "__all__"

class CreditNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNote
        fields = "__all__"

class AdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adjustment
        fields = "__all__"

class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookSubscription
        fields = "__all__"

class WebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = "__all__"


# Vendor Portal Serializers

class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for Purchase Orders"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    job_number = serializers.CharField(source='job.job_number', read_only=True)
    client_name = serializers.CharField(source='job.client.name', read_only=True)
    is_delayed = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'job', 'job_number', 'vendor', 'vendor_name',
            'client_name', 'product_type', 'product_description', 'quantity',
            'unit_cost', 'total_cost', 'required_by', 'estimated_completion',
            'actual_completion', 'status', 'milestone', 'vendor_accepted',
            'vendor_accepted_at', 'vendor_notes', 'special_instructions',
            'assets_acknowledged', 'assets_acknowledged_at', 'shipping_method',
            'tracking_number', 'carrier', 'ready_for_pickup', 'coordination_group',
            'internal_notes', 'is_delayed', 'days_until_due', 'created_at', 'updated_at'
        ]
        read_only_fields = ['po_number', 'created_at', 'updated_at', 'is_delayed', 'days_until_due']


class VendorInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Invoices"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    job_number = serializers.CharField(source='job.job_number', read_only=True)
    
    class Meta:
        model = VendorInvoice
        fields = [
            'id', 'invoice_number', 'vendor_invoice_ref', 'purchase_order',
            'po_number', 'vendor', 'vendor_name', 'job', 'job_number',
            'invoice_date', 'due_date', 'line_items', 'subtotal', 'tax_rate',
            'tax_amount', 'total_amount', 'payment_terms', 'payment_method',
            'status', 'invoice_file', 'supporting_documents', 'vendor_notes',
            'internal_notes', 'rejection_reason', 'submitted_at', 'approved_at', 
            'approved_by', 'paid_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['invoice_number', 'tax_amount', 'total_amount', 
                           'submitted_at', 'approved_at', 'paid_at', 'created_at', 'updated_at']


class PurchaseOrderProofSerializer(serializers.ModelSerializer):
    """Serializer for Purchase Order Proofs"""
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrderProof
        fields = [
            'id', 'purchase_order', 'po_number', 'proof_image', 'proof_type',
            'submitted_at', 'status', 'rejection_reason', 'reviewed_by',
            'reviewed_by_name', 'reviewed_at'
        ]
        read_only_fields = ['submitted_at']


class PurchaseOrderIssueSerializer(serializers.ModelSerializer):
    """Serializer for Purchase Order Issues"""
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrderIssue
        fields = [
            'id', 'purchase_order', 'po_number', 'issue_type', 'description',
            'photo', 'status', 'resolution_notes', 'resolved_by',
            'resolved_by_name', 'resolved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PurchaseOrderNoteSerializer(serializers.ModelSerializer):
    """Serializer for Purchase Order Notes"""
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrderNote
        fields = [
            'id', 'purchase_order', 'po_number', 'sender', 'sender_name',
            'category', 'message', 'created_at'
        ]
        read_only_fields = ['created_at']


class MaterialSubstitutionRequestSerializer(serializers.ModelSerializer):
    """Serializer for Material Substitution Requests"""
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    
    class Meta:
        model = MaterialSubstitutionRequest
        fields = [
            'id', 'purchase_order', 'po_number', 'original_material',
            'original_pantone', 'original_supplier', 'proposed_material',
            'proposed_pantone', 'match_percentage', 'comparison_photo',
            'justification', 'status', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class VendorPerformanceSerializer(serializers.Serializer):
    """Serializer for Vendor Performance Metrics"""
    overall_score = serializers.IntegerField()
    vps_grade = serializers.CharField()
    tax_status = serializers.CharField()
    certifications = serializers.ListField(child=serializers.CharField())
    
    # Performance metrics
    on_time_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    quality_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    avg_turnaround = serializers.DecimalField(max_digits=5, decimal_places=2)
    defect_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    cost_per_job = serializers.DecimalField(max_digits=10, decimal_places=2)
    acceptance_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    response_time = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    ghosting_incidents = serializers.IntegerField(required=False)
    decline_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    # Performance insights
    insights = serializers.ListField(child=serializers.DictField())
