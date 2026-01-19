import re

# Read the api views file backup
with open('clientapp/api_views.py.backup', 'r') as f:
    content = f.read()

# Mapping of ViewSets to their tags and methods
VIEWSET_CONFIGS = {
    # ACCOUNT MANAGER 
    "LeadViewSet": ("Account Manager", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ClientViewSet": ("Account Manager", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ClientContactViewSet": ("Account Manager", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "BrandAssetViewSet": ("Account Manager", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ComplianceDocumentViewSet": ("Account Manager", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "QuoteViewSet": ("Account Manager", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "QuoteLineItemViewSet": ("Account Manager", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    
    # ==================== PRODUCTION TEAM ====================
    "JobViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "JobVendorStageViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "JobNoteViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "JobAttachmentViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "QCInspectionViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "DeliveryViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductionUpdateViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "VendorQuoteViewSet": ("Production Team", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    
    # ==================== FINANCE/PURCHASING ====================
    "VendorViewSet": ("Finance & Purchasing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "LPOViewSet": ("Finance & Purchasing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "LPOLineItemViewSet": ("Finance & Purchasing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "PaymentViewSet": ("Finance & Purchasing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "RefundViewSet": ("Finance & Purchasing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "CreditNoteViewSet": ("Finance & Purchasing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "AdjustmentViewSet": ("Finance & Purchasing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    
    # ==================== PRODUCT CATALOG ====================
    "ProductViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "StorefrontProductViewSet": ("Product Catalog", ['list', 'retrieve']),  # ReadOnly
    "ProductImageViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductVideoViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductDownloadableFileViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductSEOViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductReviewSettingsViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductFAQViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductShippingViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductLegalViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductProductionViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductChangeHistoryViewSet": ("Product Catalog", ['list', 'retrieve']),  # ReadOnly
    "ProductTemplateViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductRuleViewSet": ("Product Catalog", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    
    # ==================== PRICING & COSTING ====================
    "ProcessViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProcessTierViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProcessVariableViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductVariableViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductVariableOptionViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProcessVendorViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "PricingTierViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "VendorTierPricingViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProcessVariableRangeViewSet": ("Pricing & Costing", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "QuantityPricingViewSet": ("Pricing & Costing", ['list', 'retrieve']),  # ReadOnly
    
    # ==================== SYSTEM & CONFIGURATION ====================
    "PropertyTypeViewSet": ("System & Configuration", ['list', 'retrieve']),  # ReadOnly
    "PropertyValueViewSet": ("System & Configuration", ['list', 'retrieve']),  # ReadOnly
    "ProductPropertyViewSet": ("System & Configuration", ['list', 'retrieve']),  # ReadOnly
    "TurnAroundTimeViewSet": ("System & Configuration", ['list', 'retrieve']),  # ReadOnly
    "SystemSettingViewSet": ("System & Configuration", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "SystemAlertViewSet": ("System & Configuration", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "UserViewSet": ("System & Configuration", ['list', 'retrieve']),  # ReadOnly
    "GroupViewSet": ("System & Configuration", ['list', 'retrieve']),  # ReadOnly
    
    # ==================== NOTIFICATIONS & LOGGING ====================
    "NotificationViewSet": ("Notifications & Logging", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ActivityLogViewSet": ("Notifications & Logging", ['list', 'retrieve']),  # ReadOnly
    
    # ==================== INTEGRATIONS ====================
    "QuickBooksSyncViewSet": ("Integrations", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "WebhookSubscriptionViewSet": ("Integrations", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "WebhookDeliveryViewSet": ("Integrations", ['list', 'retrieve']),  # ReadOnly
    
    # ==================== DASHBOARD & ANALYTICS ====================
    # viewsets
    "DashboardViewSet": ("Dashboard & Analytics", []),
    "AnalyticsViewSet": ("Dashboard & Analytics", []),
    "SearchViewSet": ("Dashboard & Analytics", []),
    
    # ==================== TIMELINE & TRACKING ====================
    "TimelineEventViewSet": ("Timeline & Tracking", ['list', 'retrieve']),  # ReadOnly
    "ShipmentViewSet": ("Timeline & Tracking", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    
    # ==================== DESIGN & ECOMMERCE ====================
    "DesignTemplateViewSet": ("Design & Ecommerce", ['list', 'retrieve']),  # ReadOnly
    "DesignSessionViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "DesignVersionViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "DesignStateViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProofApprovalViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "CustomerViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "CustomerAddressViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "CartViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "CartItemViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "OrderViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "OrderItemViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "ProductReviewViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "CouponViewSet": ("Design & Ecommerce", ['list', 'retrieve']),  # ReadOnly
    "PromotionViewSet": ("Design & Ecommerce", ['list', 'retrieve']),  # ReadOnly
    "ShippingMethodViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "PaymentTransactionViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    "TaxConfigurationViewSet": ("Design & Ecommerce", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    
    # ==================== INVENTORY ====================
    "MaterialInventoryViewSet": ("Inventory Management", ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']),
    
    # ==================== PRODUCTION-SPECIFIC ====================
    "CostingEngineViewSet": ("Production Team", []),  # Custom ViewSet
    "WorkloadViewSet": ("Production Team", []),  # Custom ViewSet
    "ProductionAnalyticsViewSet": ("Production Team", []),  # Custom ViewSet
}

def add_decorators_to_class(match_text, config):
    """Add decorators before a class definition"""
    tag, methods = config
    
    if not methods:  # No methods to decorate
        return match_text
    
    decorators = []
    for method in methods:
        decorators.append(f"@method_decorator(name='{method}', decorator=swagger_auto_schema(tags=['{tag}']))")
    
    decorators_str = '\n'.join(decorators) + '\n'
    return decorators_str + match_text

# Replace class definitions with tagged versions
for viewset_name, config in VIEWSET_CONFIGS.items():
    # Find the class definition
    pattern = rf'^class {viewset_name}\('
    
    def replacer(match):
        return add_decorators_to_class(match.group(0), config)
    
    content = re.sub(pattern, replacer, content, flags=re.MULTILINE)

# Write output
with open('clientapp/api_views.py', 'w') as f:
    f.write(content)

print("✅ Fixed api_views.py with correct Swagger tags!")
print("\nSummary:")
print(f"  Total ViewSets: {len(VIEWSET_CONFIGS)}")
print(f"  ModelViewSet: {sum(1 for c in VIEWSET_CONFIGS.values() if len(c[1]) == 6)}")
print(f"  ReadOnlyModelViewSet: {sum(1 for c in VIEWSET_CONFIGS.values() if len(c[1]) == 2)}")
print(f"  Custom ViewSets: {sum(1 for c in VIEWSET_CONFIGS.values() if len(c[1]) == 0)}")
total_decorators = sum(len(c[1]) for c in VIEWSET_CONFIGS.values())
print(f"  Total decorators: {total_decorators}")
