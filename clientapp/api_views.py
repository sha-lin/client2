from django.utils import timezone
from rest_framework import viewsets, status, decorators
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

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


class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.select_related("client", "lead", "created_by").prefetch_related("line_items")
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsAccountManager | IsAdmin]
    filterset_fields = ["status", "production_status", "client", "lead"]
    search_fields = ["quote_id", "product_name", "reference_number"]
    ordering_fields = ["created_at", "quote_date", "valid_until"]

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

