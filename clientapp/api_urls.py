from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()

# Core CRM / AM
router.register("leads", api_views.LeadViewSet, basename="lead")
router.register("clients", api_views.ClientViewSet, basename="client")
router.register("client-contacts", api_views.ClientContactViewSet, basename="client-contact")
router.register("brand-assets", api_views.BrandAssetViewSet, basename="brand-asset")
router.register("compliance-documents", api_views.ComplianceDocumentViewSet, basename="compliance-document")

# Catalog / Products
router.register("products", api_views.ProductViewSet, basename="product")
router.register("storefront-products", api_views.StorefrontProductViewSet, basename="storefront-product")
router.register("property-types", api_views.PropertyTypeViewSet, basename="property-type")
router.register("property-values", api_views.PropertyValueViewSet, basename="property-value")
router.register("product-properties", api_views.ProductPropertyViewSet, basename="product-property")
router.register("quantity-pricing", api_views.QuantityPricingViewSet, basename="quantity-pricing")
router.register("turnaround-times", api_views.TurnAroundTimeViewSet, basename="turnaround-time")
router.register("product-images", api_views.ProductImageViewSet, basename="product-image")
router.register("product-videos", api_views.ProductVideoViewSet, basename="product-video")
router.register("product-downloads", api_views.ProductDownloadableFileViewSet, basename="product-download")
router.register("product-seo", api_views.ProductSEOViewSet, basename="product-seo")
router.register("product-review-settings", api_views.ProductReviewSettingsViewSet, basename="product-review-settings")
router.register("product-faqs", api_views.ProductFAQViewSet, basename="product-faq")
router.register("product-shipping", api_views.ProductShippingViewSet, basename="product-shipping")
router.register("product-legal", api_views.ProductLegalViewSet, basename="product-legal")
router.register("product-production", api_views.ProductProductionViewSet, basename="product-production")
router.register("product-change-history", api_views.ProductChangeHistoryViewSet, basename="product-change-history")
router.register("product-templates", api_views.ProductTemplateViewSet, basename="product-template")

# Costing & Process Configuration
router.register("processes", api_views.ProcessViewSet, basename="process")
router.register("process-tiers", api_views.ProcessTierViewSet, basename="process-tier")
router.register("process-variables", api_views.ProcessVariableViewSet, basename="process-variable")
router.register("product-variables", api_views.ProductVariableViewSet, basename="product-variable")
router.register("product-variable-options", api_views.ProductVariableOptionViewSet, basename="product-variable-option")
router.register("process-vendors", api_views.ProcessVendorViewSet, basename="process-vendor")
router.register("pricing-tiers", api_views.PricingTierViewSet, basename="pricing-tier")
router.register("vendor-tier-pricing", api_views.VendorTierPricingViewSet, basename="vendor-tier-pricing")
router.register("process-variable-ranges", api_views.ProcessVariableRangeViewSet, basename="process-variable-range")

# Quotes / Orders / Jobs
router.register("quotes", api_views.QuoteViewSet, basename="quote")
router.register("quote-line-items", api_views.QuoteLineItemViewSet, basename="quote-line-item")
router.register("jobs", api_views.JobViewSet, basename="job")
router.register("job-vendor-stages", api_views.JobVendorStageViewSet, basename="job-vendor-stage")
router.register("job-notes", api_views.JobNoteViewSet, basename="job-note")
router.register("job-attachments", api_views.JobAttachmentViewSet, basename="job-attachment")

# Vendors / Purchasing / Finance
router.register("vendors", api_views.VendorViewSet, basename="vendor")
router.register("lpos", api_views.LPOViewSet, basename="lpo")
router.register("payments", api_views.PaymentViewSet, basename="payment")
router.register("vendor-quotes", api_views.VendorQuoteViewSet, basename="vendor-quote")
router.register("lpo-line-items", api_views.LPOLineItemViewSet, basename="lpo-line-item")

# Notifications / Logs / Settings / Integrations / QC / Delivery / Users / Dashboard
router.register("notifications", api_views.NotificationViewSet, basename="notification")
router.register("activity-log", api_views.ActivityLogViewSet, basename="activity-log")
router.register("system-settings", api_views.SystemSettingViewSet, basename="system-setting")
router.register("quickbooks", api_views.QuickBooksSyncViewSet, basename="quickbooks")
router.register("qc-inspections", api_views.QCInspectionViewSet, basename="qc-inspection")
router.register("deliveries", api_views.DeliveryViewSet, basename="delivery")
router.register("quote-attachments", api_views.QuoteAttachmentViewSet, basename="quote-attachment")
router.register("system-alerts", api_views.SystemAlertViewSet, basename="system-alert")
router.register("users", api_views.UserViewSet, basename="user")
router.register("groups", api_views.GroupViewSet, basename="group")
router.register("dashboard", api_views.DashboardViewSet, basename="dashboard")

urlpatterns = router.urls

