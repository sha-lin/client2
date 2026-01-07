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


# ===== User / Group Serializers =====

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "is_superuser"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]

