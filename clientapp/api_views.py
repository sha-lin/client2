from django.utils import timezone
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, status, decorators
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

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
    resolve_unit_price,
)
from .api_serializers import (
    LeadSerializer,
    ClientSerializer,
    ClientContactSerializer,
    BrandAssetSerializer,
    ComplianceDocumentSerializer,
    ProductSerializer,
    QuoteSerializer,
    QuoteLineItemSerializer,
    JobSerializer,
    VendorSerializer,
    LPOSerializer,
    PaymentSerializer,
    NotificationSerializer,
    ActivityLogSerializer,
    PropertyTypeSerializer,
    PropertyValueSerializer,
    ProductPropertySerializer,
    QuantityPricingSerializer,
    TurnAroundTimeSerializer,
    SystemSettingSerializer,
    ProcessSerializer,
    ProcessTierSerializer,
    ProcessVariableSerializer,
    ProductVariableSerializer,
    ProductVariableOptionSerializer,
    ProcessVendorSerializer,
    PricingTierSerializer,
    VendorTierPricingSerializer,
    ProcessVariableRangeSerializer,
    ProductImageSerializer,
    ProductVideoSerializer,
    ProductDownloadableFileSerializer,
    ProductSEOSerializer,
    ProductReviewSettingsSerializer,
    ProductFAQSerializer,
    ProductShippingSerializer,
    ProductLegalSerializer,
    ProductProductionSerializer,
    ProductChangeHistorySerializer,
    ProductTemplateSerializer,
    JobVendorStageSerializer,
    JobNoteSerializer,
    JobAttachmentSerializer,
    VendorQuoteSerializer,
    QCInspectionSerializer,
    DeliverySerializer,
    QuoteAttachmentSerializer,
    LPOLineItemSerializer,
    SystemAlertSerializer,
    UserSerializer,
    GroupSerializer,
)
from .permissions import (
    IsAdmin,
    IsAccountManager,
    IsProductionTeam,
    IsOwnerOrAdmin,
)


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.select_related("created_by").all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["status", "source", "created_by"]
    search_fields = ["lead_id", "name", "email", "phone"]
    ordering_fields = ["created_at", "status"]

    @decorators.action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        """Convert a lead to a client (simple version)."""
        lead = self.get_object()
        if lead.converted_to_client:
            return Response({"detail": "Lead already converted."}, status=status.HTTP_400_BAD_REQUEST)

        existing_client = Client.objects.filter(email=lead.email).first()
        if existing_client:
            lead.converted_to_client = True
            lead.converted_at = timezone.now()
            lead.status = "Converted"
            lead.save(update_fields=["converted_to_client", "converted_at", "status", "updated_at"])
            return Response({"detail": "Lead marked converted; client already exists.", "client_id": existing_client.id})

        client = Client.objects.create(
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            client_type="B2C",
            lead_source=lead.source if hasattr(lead, "source") else "",
            preferred_channel=lead.preferred_contact if hasattr(lead, "preferred_contact") else "Email",
            status="Active",
            converted_from_lead=lead,
            onboarded_by=request.user,
            account_manager=request.user,
        )
        lead.converted_to_client = True
        lead.converted_at = timezone.now()
        lead.status = "Converted"
        lead.save(update_fields=["converted_to_client", "converted_at", "status", "updated_at"])

        return Response({"detail": "Lead converted", "client_id": client.id})


class ClientContactViewSet(viewsets.ModelViewSet):
    queryset = ClientContact.objects.select_related("client").all()
    serializer_class = ClientContactSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["client", "role", "is_primary"]
    search_fields = ["full_name", "email", "phone"]


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.select_related("account_manager", "converted_from_lead").all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["client_type", "status", "account_manager"]
    search_fields = ["client_id", "name", "email", "phone", "company"]
    ordering_fields = ["created_at", "last_activity"]


class BrandAssetViewSet(viewsets.ModelViewSet):
    queryset = BrandAsset.objects.select_related("client", "uploaded_by").all()
    serializer_class = BrandAssetSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["client", "asset_type"]
    search_fields = ["description"]


class ComplianceDocumentViewSet(viewsets.ModelViewSet):
    queryset = ComplianceDocument.objects.select_related("client", "uploaded_by").all()
    serializer_class = ComplianceDocumentSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["client", "document_type"]
    search_fields = ["notes"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["customization_level", "status", "is_visible", "primary_category", "sub_category"]
    search_fields = ["name", "internal_code"]
    ordering_fields = ["created_at", "updated_at", "base_price"]


class StorefrontProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public storefront-safe product listing for ecommerce/landing pages.
    Only returns visible, published products.
    """

    queryset = Product.objects.filter(status="published", is_visible=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["primary_category", "sub_category", "customization_level"]
    search_fields = ["name", "short_description", "primary_category", "sub_category"]
    ordering_fields = ["created_at", "base_price"]


class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.select_related("client", "lead", "created_by").prefetch_related("line_items")
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["status", "production_status", "client", "lead", "channel", "checkout_status"]
    search_fields = ["quote_id", "product_name", "reference_number"]
    ordering_fields = ["created_at", "quote_date", "valid_until"]

    @decorators.action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def ecommerce_create(self, request):
        """
        Lightweight public endpoint for ecommerce/landing-page checkout.
        Creates a Lead + single-product Quote tagged as channel='ecommerce'.
        """
        data = request.data or {}
        customer = data.get("customer", {})
        product_id = data.get("product_id")
        quantity = data.get("quantity") or 1
        notes = data.get("notes", "")

        if not product_id:
            return Response({"detail": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        name = customer.get("name") or "Online Customer"
        email = customer.get("email", "")
        phone = customer.get("phone", "")

        # Create a simple lead for tracking
        lead = None
        if email or phone:
            lead = Lead.objects.create(
                name=name,
                email=email or "",
                phone=phone or "",
                source="Website",
                product_interest=product.name,
                preferred_contact="Email",
                created_by=None,
            )

        unit_price = resolve_unit_price(product, quantity=quantity)

        quote = Quote.objects.create(
            client=None,
            lead=lead,
            product=product,
            product_name=product.name,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=unit_price * int(quantity),
            include_vat=True,
            payment_terms="Prepaid",
            status="Draft",
            channel="ecommerce",
            checkout_status="cart",
            customer_notes=notes,
        )

        serializer = self.get_serializer(quote)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        quote = self.get_object()
        quote._skip_status_validation = True
        quote.status = "Approved"
        quote.approved_at = timezone.now()
        quote.save()
        return Response({"detail": "Quote approved"})

    @decorators.action(detail=True, methods=["post"])
    def send_to_production(self, request, pk=None):
        quote = self.get_object()
        if hasattr(quote, "job"):
            return Response({"detail": "Job already exists", "job_id": quote.job.id})
        job = Job.objects.create(
            client=quote.client,
            quote=quote,
            job_name=quote.product_name,
            job_type="printing",
            priority="normal",
            product=quote.product_name,
            quantity=quote.quantity or 1,
            person_in_charge=request.user.get_full_name() or request.user.username,
             source=quote.channel,
            created_by=request.user,
        )
        return Response({"detail": "Job created", "job_id": job.id})


class QuoteLineItemViewSet(viewsets.ModelViewSet):
    queryset = QuoteLineItem.objects.select_related("quote", "product").all()
    serializer_class = QuoteLineItemSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["quote", "product"]
    search_fields = ["product_name"]


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related("client", "quote", "created_by").all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["status", "client", "quote"]
    search_fields = ["job_number", "job_name", "product"]
    ordering_fields = ["created_at", "start_date", "expected_completion"]

    @decorators.action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        job = self.get_object()
        next_status = request.data.get("status")
        if next_status not in dict(Job.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        job.status = next_status
        job.save(update_fields=["status", "updated_at"])
        return Response({"detail": "Status updated", "status": job.status})


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["vps_score", "active"]
    search_fields = ["name", "email", "phone", "services"]


class LPOViewSet(viewsets.ModelViewSet):
    queryset = LPO.objects.select_related("client", "quote", "created_by").all()
    serializer_class = LPOSerializer
    permission_classes = [IsAuthenticated, IsAdmin | IsAccountManager]
    filterset_fields = ["status", "client", "quote"]
    search_fields = ["lpo_number", "terms_and_conditions"]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("lpo", "recorded_by").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsAdmin | IsAccountManager]
    filterset_fields = ["status", "payment_method", "lpo"]
    search_fields = ["reference_number"]
    ordering_fields = ["payment_date", "amount"]


class PropertyTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["property_type", "affects_price"]
    search_fields = ["name", "description"]


class PropertyValueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyValue.objects.select_related("property_type").all()
    serializer_class = PropertyValueSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["property_type", "is_active"]
    search_fields = ["value", "description"]


class ProductPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductProperty.objects.select_related("product", "property_value", "property_value__property_type").all()
    serializer_class = ProductPropertySerializer
    permission_classes = [AllowAny]
    filterset_fields = ["product", "property_value__property_type", "is_available"]


class QuantityPricingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuantityPricing.objects.select_related("product").all()
    serializer_class = QuantityPricingSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["product"]


class TurnAroundTimeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TurnAroundTime.objects.select_related("product").all()
    serializer_class = TurnAroundTimeSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["product", "is_available", "is_default"]


# ===== Costing / Process ViewSets =====

class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["pricing_type", "category", "status"]
    search_fields = ["process_id", "process_name", "description"]


class ProcessTierViewSet(viewsets.ModelViewSet):
    queryset = ProcessTier.objects.select_related("process").all()
    serializer_class = ProcessTierSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["process", "tier_number"]


class ProcessVariableViewSet(viewsets.ModelViewSet):
    queryset = ProcessVariable.objects.select_related("process").all()
    serializer_class = ProcessVariableSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["process", "variable_type"]


class ProductVariableViewSet(viewsets.ModelViewSet):
    queryset = ProductVariable.objects.select_related("product").all()
    serializer_class = ProductVariableSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["product", "variable_type", "pricing_type", "is_active"]


class ProductVariableOptionViewSet(viewsets.ModelViewSet):
    queryset = ProductVariableOption.objects.select_related("variable").all()
    serializer_class = ProductVariableOptionSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["variable", "is_active", "is_default"]


class ProcessVendorViewSet(viewsets.ModelViewSet):
    queryset = ProcessVendor.objects.select_related("process").all()
    serializer_class = ProcessVendorSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["process", "priority"]


class PricingTierViewSet(viewsets.ModelViewSet):
    queryset = PricingTier.objects.select_related("process").all()
    serializer_class = PricingTierSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["process"]


class VendorTierPricingViewSet(viewsets.ModelViewSet):
    queryset = VendorTierPricing.objects.select_related("process_vendor").all()
    serializer_class = VendorTierPricingSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["process_vendor"]


class ProcessVariableRangeViewSet(viewsets.ModelViewSet):
    queryset = ProcessVariableRange.objects.select_related("variable").all()
    serializer_class = ProcessVariableRangeSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["variable"]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related("recipient").all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["recipient", "is_read", "notification_type"]
    search_fields = ["title", "message"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        # Only return notifications for the current user by default
        qs = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.groups.filter(name="Admin").exists():
            return qs
        return qs.filter(recipient=self.request.user)

    @decorators.action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"detail": "Marked read"})


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.select_related("client", "created_by").all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["client", "activity_type"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at"]


class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


# ===== Product Metadata ViewSets =====

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.select_related("product").all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["product", "image_type", "is_primary"]


class ProductVideoViewSet(viewsets.ModelViewSet):
    queryset = ProductVideo.objects.select_related("product").all()
    serializer_class = ProductVideoSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["product", "video_type"]


class ProductDownloadableFileViewSet(viewsets.ModelViewSet):
    queryset = ProductDownloadableFile.objects.select_related("product").all()
    serializer_class = ProductDownloadableFileSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["product", "file_type"]


class ProductSEOViewSet(viewsets.ModelViewSet):
    queryset = ProductSEO.objects.select_related("product").all()
    serializer_class = ProductSEOSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]


class ProductReviewSettingsViewSet(viewsets.ModelViewSet):
    queryset = ProductReviewSettings.objects.select_related("product").all()
    serializer_class = ProductReviewSettingsSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]


class ProductFAQViewSet(viewsets.ModelViewSet):
    queryset = ProductFAQ.objects.select_related("product").all()
    serializer_class = ProductFAQSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["product", "is_active"]


class ProductShippingViewSet(viewsets.ModelViewSet):
    queryset = ProductShipping.objects.select_related("product").all()
    serializer_class = ProductShippingSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]


class ProductLegalViewSet(viewsets.ModelViewSet):
    queryset = ProductLegal.objects.select_related("product").all()
    serializer_class = ProductLegalSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]


class ProductProductionViewSet(viewsets.ModelViewSet):
    queryset = ProductProduction.objects.select_related("product").all()
    serializer_class = ProductProductionSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]


class ProductChangeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductChangeHistory.objects.select_related("product", "changed_by").all()
    serializer_class = ProductChangeHistorySerializer
    permission_classes = [IsAuthenticated, IsAdmin | IsProductionTeam]
    filterset_fields = ["product", "change_type"]


class ProductTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProductTemplate.objects.select_related("product").all()
    serializer_class = ProductTemplateSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]


class QuickBooksSyncViewSet(viewsets.ViewSet):
    """
    Placeholder sync endpoints for QuickBooks integration.
    Replace with real sync logic in quickbooks_services.py.
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def list(self, request):
        return Response({"detail": "QuickBooks sync endpoints"}, status=status.HTTP_200_OK)

    @decorators.action(detail=False, methods=["post"])
    def push_clients(self, request):
        return Response({"detail": "Client sync not yet implemented"}, status=status.HTTP_200_OK)

    @decorators.action(detail=False, methods=["post"])
    def push_invoices(self, request):
        return Response({"detail": "Invoice sync not yet implemented"}, status=status.HTTP_200_OK)


# ===== QC, Delivery, Attachments, Notes, Alerts =====

class JobVendorStageViewSet(viewsets.ModelViewSet):
    queryset = JobVendorStage.objects.select_related("job", "vendor").all()
    serializer_class = JobVendorStageSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["job", "vendor", "status"]


class JobNoteViewSet(viewsets.ModelViewSet):
    queryset = JobNote.objects.select_related("job", "created_by").all()
    serializer_class = JobNoteSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["job", "note_type"]


class JobAttachmentViewSet(viewsets.ModelViewSet):
    queryset = JobAttachment.objects.select_related("job", "uploaded_by").all()
    serializer_class = JobAttachmentSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["job"]


class VendorQuoteViewSet(viewsets.ModelViewSet):
    queryset = VendorQuote.objects.select_related("job", "vendor").all()
    serializer_class = VendorQuoteSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["job", "vendor", "selected"]


class QCInspectionViewSet(viewsets.ModelViewSet):
    queryset = QCInspection.objects.select_related("job", "vendor", "inspector").all()
    serializer_class = QCInspectionSerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin]
    filterset_fields = ["job", "vendor", "status"]


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.select_related("job", "qc_inspection", "handoff_confirmed_by", "created_by").all()
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsProductionTeam | IsAdmin | IsAccountManager]
    filterset_fields = ["job", "status", "staging_location"]


class QuoteAttachmentViewSet(viewsets.ModelViewSet):
    queryset = QuoteAttachment.objects.select_related("quote", "uploaded_by").all()
    serializer_class = QuoteAttachmentSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["quote"]


class LPOLineItemViewSet(viewsets.ModelViewSet):
    queryset = LPOLineItem.objects.select_related("lpo").all()
    serializer_class = LPOLineItemSerializer
    permission_classes = [IsAuthenticated, IsAdmin | IsAccountManager]
    filterset_fields = ["lpo"]


class SystemAlertViewSet(viewsets.ModelViewSet):
    queryset = SystemAlert.objects.all()
    serializer_class = SystemAlertSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["alert_type", "severity", "is_active", "is_dismissed"]


# ===== User / Group Management =====

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["is_active", "is_superuser"]
    search_fields = ["username", "email", "first_name", "last_name"]


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password:
            return Response({"detail": "username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"detail": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"detail": "old_password and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(old_password):
            return Response({"detail": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)


# ===== Dashboard / Analytics =====

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdmin | IsAccountManager | IsProductionTeam]

    def list(self, request):
        """Return high-level metrics for dashboards."""
        data = {
            "leads": {
                "total": Lead.objects.count(),
                "new": Lead.objects.filter(status="New").count(),
                "converted": Lead.objects.filter(status="Converted").count(),
            },
            "clients": {
                "total": Client.objects.count(),
                "b2b": Client.objects.filter(client_type="B2B").count(),
                "b2c": Client.objects.filter(client_type="B2C").count(),
            },
            "quotes": {
                "total": Quote.objects.count(),
                "draft": Quote.objects.filter(status="Draft").count(),
                "sent_to_customer": Quote.objects.filter(status="Sent to Customer").count(),
                "approved": Quote.objects.filter(status="Approved").count(),
                "lost": Quote.objects.filter(status="Lost").count(),
                "ecommerce": Quote.objects.filter(channel="ecommerce").count(),
            },
            "jobs": {
                "total": Job.objects.count(),
                "pending": Job.objects.filter(status="pending").count(),
                "in_progress": Job.objects.filter(status="in_progress").count(),
                "on_hold": Job.objects.filter(status="on_hold").count(),
                "completed": Job.objects.filter(status="completed").count(),
            },
            "lpos": {
                "total": LPO.objects.count(),
                "pending": LPO.objects.filter(status="pending").count(),
                "approved": LPO.objects.filter(status="approved").count(),
                "completed": LPO.objects.filter(status="completed").count(),
            },
        }
        return Response(data, status=status.HTTP_200_OK)

