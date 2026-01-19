from rest_framework.routers import DefaultRouter
from django.urls import path

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
router.register("timeline", api_views.TimelineEventViewSet, basename="timeline")
router.register("shipments", api_views.ShipmentViewSet, basename="shipment")



# Vendors / Purchasing / Finance
router.register("vendors", api_views.VendorViewSet, basename="vendor")
router.register("lpos", api_views.LPOViewSet, basename="lpo")
router.register("purchase-orders", api_views.PurchaseOrderViewSet, basename="purchase-order")
router.register("vendor-invoices", api_views.VendorInvoiceViewSet, basename="vendor-invoice")
router.register("payments", api_views.PaymentViewSet, basename="payment")
router.register("vendor-quotes", api_views.VendorQuoteViewSet, basename="vendor-quote")
router.register("lpo-line-items", api_views.LPOLineItemViewSet, basename="lpo-line-item")
router.register("refunds", api_views.RefundViewSet, basename="refund")
router.register("credit-notes", api_views.CreditNoteViewSet, basename="credit-note")
router.register("adjustments", api_views.AdjustmentViewSet, basename="adjustment")



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
router.register("analytics", api_views.AnalyticsViewSet, basename="analytics")
router.register("search", api_views.SearchViewSet, basename="search")
router.register("product-rules", api_views.ProductRuleViewSet, basename="product-rule")
router.register("material-inventory", api_views.MaterialInventoryViewSet, basename="material-inventory")
router.register("webhook-subscriptions", api_views.WebhookSubscriptionViewSet, basename="webhook-subscription")
router.register("webhook-deliveries", api_views.WebhookDeliveryViewSet, basename="webhook-delivery")


# Production Team Specific APIs
router.register("production-updates", api_views.ProductionUpdateViewSet, basename="production-update")
router.register("costing-engine", api_views.CostingEngineViewSet, basename="costing-engine")
router.register("workload", api_views.WorkloadViewSet, basename="workload")
router.register("production-analytics", api_views.ProductionAnalyticsViewSet, basename="production-analytics")

# Storefront Ecommerce APIs
# router.register("storefront/customers", api_views.CustomerViewSet, basename="storefront-customer")
# router.register("storefront/addresses", api_views.CustomerAddressViewSet, basename="storefront-address")
# router.register("storefront/carts", api_views.CartViewSet, basename="storefront-cart")
# router.register("storefront/orders", api_views.OrderViewSet, basename="storefront-order")
# router.register("storefront/coupons", api_views.CouponViewSet, basename="storefront-coupon")
# router.register("storefront/design-templates", api_views.DesignTemplateViewSet, basename="storefront-design-template")
# router.register("storefront/design-states", api_views.DesignStateViewSet, basename="storefront-design-state")
# router.register("storefront/reviews", api_views.ProductReviewViewSet, basename="storefront-review")
# router.register("storefront/shipping-methods", api_views.ShippingMethodViewSet, basename="storefront-shipping-method")
# router.register("storefront/tax-configurations", api_views.TaxConfigurationViewSet, basename="storefront-tax-config")
# router.register("storefront/design-sessions", api_views.DesignSessionViewSet, basename="storefront-design-session")
# router.register("storefront/design-versions", api_views.DesignVersionViewSet, basename="storefront-design-version")
# router.register("storefront/proof-approvals", api_views.ProofApprovalViewSet, basename="storefront-proof-approval")
# router.register("storefront/promotions", api_views.PromotionViewSet, basename="storefront-promotion")


urlpatterns = router.urls + [
    # Canonical Pricing Engine
    path('pricing/calculate/', api_views.PricingEngineView.as_view(), name='pricing-calculate'),
    # Product Configuration Rules Engine
    path('product-configurations/validate/', api_views.ProductConfigurationValidationView.as_view(), name='product-config-validate'),
    # Preflight Service
    path('files/preflight/', api_views.PreflightView.as_view(), name='preflight'),
]

