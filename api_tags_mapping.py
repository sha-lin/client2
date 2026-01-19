# API ViewSet to Tags Mapping
# This file defines which tags should be applied to each ViewSet

VIEWSET_TAGS = {
    # ==================== ACCOUNT MANAGER ====================
    "LeadViewSet": "Account Manager",
    "ClientViewSet": "Account Manager",
    "ClientContactViewSet": "Account Manager",
    "BrandAssetViewSet": "Account Manager",
    "ComplianceDocumentViewSet": "Account Manager",
    "QuoteViewSet": "Account Manager",
    "QuoteLineItemViewSet": "Account Manager",
    
    # ==================== PRODUCTION TEAM ====================
    "JobViewSet": "Production Team",
    "JobVendorStageViewSet": "Production Team",
    "JobNoteViewSet": "Production Team",
    "JobAttachmentViewSet": "Production Team",
    "QCInspectionViewSet": "Production Team",
    "DeliveryViewSet": "Production Team",
    "ProductionUpdateViewSet": "Production Team",
    "CostingEngineViewSet": "Production Team",
    "WorkloadViewSet": "Production Team",
    "ProductionAnalyticsViewSet": "Production Team",
    "VendorQuoteViewSet": "Production Team",
    
    # ==================== FINANCE/PURCHASING ====================
    "VendorViewSet": "Finance & Purchasing",
    "LPOViewSet": "Finance & Purchasing",
    "LPOLineItemViewSet": "Finance & Purchasing",
    "PaymentViewSet": "Finance & Purchasing",
    "RefundViewSet": "Finance & Purchasing",
    "CreditNoteViewSet": "Finance & Purchasing",
    "AdjustmentViewSet": "Finance & Purchasing",
    
    # ==================== PRODUCT CATALOG ====================
    "ProductViewSet": "Product Catalog",
    "StorefrontProductViewSet": "Product Catalog",
    "ProductImageViewSet": "Product Catalog",
    "ProductVideoViewSet": "Product Catalog",
    "ProductDownloadableFileViewSet": "Product Catalog",
    "ProductSEOViewSet": "Product Catalog",
    "ProductReviewSettingsViewSet": "Product Catalog",
    "ProductFAQViewSet": "Product Catalog",
    "ProductShippingViewSet": "Product Catalog",
    "ProductLegalViewSet": "Product Catalog",
    "ProductProductionViewSet": "Product Catalog",
    "ProductChangeHistoryViewSet": "Product Catalog",
    "ProductTemplateViewSet": "Product Catalog",
    "ProductRuleViewSet": "Product Catalog",
    
    # ==================== PRICING & COSTING ====================
    "ProcessViewSet": "Pricing & Costing",
    "ProcessTierViewSet": "Pricing & Costing",
    "ProcessVariableViewSet": "Pricing & Costing",
    "ProductVariableViewSet": "Pricing & Costing",
    "ProductVariableOptionViewSet": "Pricing & Costing",
    "ProcessVendorViewSet": "Pricing & Costing",
    "PricingTierViewSet": "Pricing & Costing",
    "VendorTierPricingViewSet": "Pricing & Costing",
    "ProcessVariableRangeViewSet": "Pricing & Costing",
    "QuantityPricingViewSet": "Pricing & Costing",
    
    # ==================== SYSTEM & CONFIGURATION ====================
    "PropertyTypeViewSet": "System & Configuration",
    "PropertyValueViewSet": "System & Configuration",
    "ProductPropertyViewSet": "System & Configuration",
    "TurnAroundTimeViewSet": "System & Configuration",
    "SystemSettingViewSet": "System & Configuration",
    "SystemAlertViewSet": "System & Configuration",
    "UserViewSet": "System & Configuration",
    "GroupViewSet": "System & Configuration",
    
    # ==================== NOTIFICATIONS & LOGGING ====================
    "NotificationViewSet": "Notifications & Logging",
    "ActivityLogViewSet": "Notifications & Logging",
    
    # ==================== INTEGRATIONS ====================
    "QuickBooksSyncViewSet": "Integrations",
    "WebhookSubscriptionViewSet": "Integrations",
    "WebhookDeliveryViewSet": "Integrations",
    
    # ==================== DASHBOARD & ANALYTICS ====================
    "DashboardViewSet": "Dashboard & Analytics",
    "AnalyticsViewSet": "Dashboard & Analytics",
    "SearchViewSet": "Dashboard & Analytics",
    
    # ==================== TIMELINE & TRACKING ====================
    "TimelineEventViewSet": "Timeline & Tracking",
    "ShipmentViewSet": "Timeline & Tracking",
    
    # ==================== DESIGN & ECOMMERCE ====================
    "DesignTemplateViewSet": "Design & Ecommerce",
    "DesignSessionViewSet": "Design & Ecommerce",
    "DesignVersionViewSet": "Design & Ecommerce",
    "DesignStateViewSet": "Design & Ecommerce",
    "ProofApprovalViewSet": "Design & Ecommerce",
    "CustomerViewSet": "Design & Ecommerce",
    "CustomerAddressViewSet": "Design & Ecommerce",
    "CartViewSet": "Design & Ecommerce",
    "CartItemViewSet": "Design & Ecommerce",
    "OrderViewSet": "Design & Ecommerce",
    "OrderItemViewSet": "Design & Ecommerce",
    "ProductReviewViewSet": "Design & Ecommerce",
    "CouponViewSet": "Design & Ecommerce",
    "PromotionViewSet": "Design & Ecommerce",
    "ShippingMethodViewSet": "Design & Ecommerce",
    "PaymentTransactionViewSet": "Design & Ecommerce",
    "TaxConfigurationViewSet": "Design & Ecommerce",
    
    # ==================== INVENTORY ====================
    "MaterialInventoryViewSet": "Inventory Management",
}

# Define HTTP methods to apply tags to
METHODS_TO_TAG = ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']
