"""
Storefront API Serializers
For public product catalog, estimate quotes, chatbot, messaging
"""

from rest_framework import serializers
from clientapp.models import (
    StorefrontProduct, EstimateQuote, StorefrontCustomer,
    StorefrontMessage, ChatbotConversation, QuotePricingSnapshot,
    ProductionUnit
)
from django.contrib.auth.models import User
from decimal import Decimal


class StorefrontProductSerializer(serializers.ModelSerializer):
    """Product for public storefront catalog"""
    
    class Meta:
        model = StorefrontProduct
        fields = [
            'product_id', 'name', 'description_short', 'description_long',
            'category', 'base_price', 'price_range_min', 'price_range_max',
            'pricing_tiers', 'hero_image', 'gallery_images',
            'customization_level', 'available_customizations',
            'turnaround_standard_days', 'turnaround_rush_days',
            'turnaround_rush_surcharge', 'turnaround_expedited_days',
            'turnaround_expedited_surcharge', 'minimum_order_quantity',
            'featured', 'rating', 'review_count', 'published_at'
        ]
        read_only_fields = fields


class ProductPriceCalculationSerializer(serializers.Serializer):
    """Calculate product price based on quantity and options"""
    quantity = serializers.IntegerField(min_value=1)
    turnaround_time = serializers.ChoiceField(
        choices=['standard', 'rush', 'expedited']
    )
    properties = serializers.JSONField(required=False, default=dict)


class EstimateQuoteLineItemSerializer(serializers.Serializer):
    """Line item in estimate quote"""
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    properties = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(required=False, default='')
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=15, decimal_places=2)


class EstimateQuoteCreateSerializer(serializers.ModelSerializer):
    """Create estimate quote from storefront"""
    line_items = EstimateQuoteLineItemSerializer(many=True)
    
    class Meta:
        model = EstimateQuote
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'customer_company', 'line_items', 'subtotal', 'tax_amount',
            'total_amount', 'turnaround_time', 'delivery_method',
            'payment_terms', 'special_notes'
        ]
    
    def create(self, validated_data):
        # Extract line_items from validated_data since it's a nested serializer
        line_items_data = validated_data.pop('line_items', [])
        
        # Convert Decimal fields to strings for JSON storage
        for item in line_items_data:
            if 'unit_price' in item:
                item['unit_price'] = str(item['unit_price'])
            if 'line_total' in item:
                item['line_total'] = str(item['line_total'])
        
        # Create the estimate
        estimate = EstimateQuote.objects.create(**validated_data)
        
        # Store line items as JSON (they're already dictionaries from the nested serializer)
        estimate.line_items = line_items_data
        estimate.save()
        
        return estimate


class EstimateQuoteSerializer(serializers.ModelSerializer):
    """Estimate quote details"""
    line_items = serializers.JSONField()
    
    class Meta:
        model = EstimateQuote
        fields = [
            'estimate_id', 'share_token', 'customer_name', 'customer_email',
            'customer_phone', 'customer_company', 'line_items', 'subtotal',
            'tax_amount', 'total_amount', 'turnaround_time', 'delivery_method',
            'payment_terms', 'special_notes', 'status', 'shared_via',
            'created_at', 'expires_at'
        ]
        read_only_fields = [
            'estimate_id', 'share_token', 'created_at', 'expires_at'
        ]


class EstimateQuoteShareSerializer(serializers.Serializer):
    """Share estimate quote via WhatsApp or Email"""
    channel = serializers.ChoiceField(choices=['whatsapp', 'email'])


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """Register new storefront customer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'password_confirm'
        ]
    
    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user


class StorefrontCustomerSerializer(serializers.ModelSerializer):
    """Storefront customer profile"""
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = StorefrontCustomer
        fields = [
            'customer_id', 'email', 'name', 'phone', 'company',
            'email_verified', 'phone_verified', 'customer_type',
            'communication_channel', 'language', 'newsletter_subscribed',
            'created_at'
        ]
        read_only_fields = ['customer_id', 'email', 'created_at']
    
    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class StorefrontCustomerUpdateSerializer(serializers.ModelSerializer):
    """Update storefront customer profile"""
    
    class Meta:
        model = StorefrontCustomer
        fields = [
            'phone', 'company', 'profile_picture', 'customer_type',
            'communication_channel', 'language', 'newsletter_subscribed'
        ]


class StorefrontMessageSerializer(serializers.ModelSerializer):
    """Storefront message (chat, email, WhatsApp)"""
    customer_name_display = serializers.SerializerMethodField()
    
    class Meta:
        model = StorefrontMessage
        fields = [
            'message_id', 'message_type', 'channel', 'subject',
            'message_content', 'customer_name_display', 'customer_email',
            'customer_phone', 'status', 'assigned_to', 'response_message',
            'response_at', 'created_at'
        ]
        read_only_fields = ['message_id', 'created_at']
    
    def get_customer_name_display(self, obj):
        if obj.customer:
            return f"{obj.customer.user.first_name} {obj.customer.user.last_name}".strip()
        return obj.customer_name


class ContactEmailSerializer(serializers.Serializer):
    """Send email to sales"""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()
    phone = serializers.CharField(max_length=20, required=False)


class ContactWhatsAppSerializer(serializers.Serializer):
    """Initiate WhatsApp contact"""
    phone = serializers.CharField(max_length=20)
    message = serializers.CharField()
    name = serializers.CharField(max_length=255)


class CallRequestSerializer(serializers.Serializer):
    """Request a phone call"""
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    preferred_time = serializers.DateTimeField()


class ChatbotMessageSerializer(serializers.Serializer):
    """Send message to chatbot"""
    message = serializers.CharField()
    conversation_id = serializers.CharField(required=False, allow_blank=True)


class ChatbotMessageResponseSerializer(serializers.Serializer):
    """Chatbot response"""
    response = serializers.CharField()
    suggestions = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    action = serializers.CharField(required=False)


class ChatbotConversationSerializer(serializers.ModelSerializer):
    """Chatbot conversation history"""
    
    class Meta:
        model = ChatbotConversation
        fields = [
            'conversation_id', 'messages', 'context', 'started_at',
            'ended_at', 'resolved', 'escalated_to_human'
        ]
        read_only_fields = ['conversation_id', 'started_at']


class ProductionUnitSerializer(serializers.ModelSerializer):
    """Production unit for job breakdown"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    
    class Meta:
        model = ProductionUnit
        fields = [
            'unit_id', 'job', 'unit_sequence', 'unit_type',
            'task_description', 'vendor', 'vendor_name', 'quantity',
            'unit_measure', 'estimated_cost', 'actual_cost',
            'estimated_timeline_days', 'expected_start_date',
            'expected_end_date', 'actual_start_date', 'actual_end_date',
            'status', 'notes', 'created_at'
        ]
        read_only_fields = ['unit_id', 'created_at']


class ProductionUnitCreateSerializer(serializers.ModelSerializer):
    """Create production unit"""
    
    class Meta:
        model = ProductionUnit
        fields = [
            'job', 'unit_sequence', 'unit_type', 'task_description',
            'vendor', 'quantity', 'unit_measure', 'estimated_cost',
            'estimated_timeline_days', 'expected_start_date',
            'expected_end_date', 'notes'
        ]


class QuotePricingSnapshotSerializer(serializers.ModelSerializer):
    """Quote pricing change audit trail"""
    applied_by_name = serializers.CharField(
        source='applied_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = QuotePricingSnapshot
        fields = [
            'snapshot_id', 'snapshot_type', 'base_amount', 'adjustments',
            'total_amount', 'applied_by', 'applied_by_name', 'reason',
            'snapshot_at'
        ]
        read_only_fields = ['snapshot_id', 'snapshot_at']


class CustomerPreferencesSerializer(serializers.ModelSerializer):
    """Customer communication preferences"""
    
    class Meta:
        model = StorefrontCustomer
        fields = [
            'communication_channel', 'language', 'newsletter_subscribed'
        ]


class QuoteListSerializer(serializers.Serializer):
    """Serializer for customer's saved quotes list"""
    id = serializers.IntegerField()
    quote_id = serializers.CharField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    created_at = serializers.DateTimeField()
    modified_at = serializers.DateTimeField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)

