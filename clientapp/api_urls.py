from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register("leads", api_views.LeadViewSet, basename="lead")
router.register("clients", api_views.ClientViewSet, basename="client")
router.register("client-contacts", api_views.ClientContactViewSet, basename="client-contact")
router.register("brand-assets", api_views.BrandAssetViewSet, basename="brand-asset")
router.register("compliance-documents", api_views.ComplianceDocumentViewSet, basename="compliance-document")
router.register("products", api_views.ProductViewSet, basename="product")
router.register("quotes", api_views.QuoteViewSet, basename="quote")
router.register("quote-line-items", api_views.QuoteLineItemViewSet, basename="quote-line-item")
router.register("jobs", api_views.JobViewSet, basename="job")
router.register("vendors", api_views.VendorViewSet, basename="vendor")
router.register("lpos", api_views.LPOViewSet, basename="lpo")
router.register("payments", api_views.PaymentViewSet, basename="payment")
router.register("notifications", api_views.NotificationViewSet, basename="notification")
router.register("activity-log", api_views.ActivityLogViewSet, basename="activity-log")
router.register("quickbooks", api_views.QuickBooksSyncViewSet, basename="quickbooks")

urlpatterns = router.urls

