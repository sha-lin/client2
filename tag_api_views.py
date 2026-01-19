"""
Script to add Swagger tags to all ViewSets in api_views.py
"""
import re

# Mapping of ViewSets to their tags
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

def generate_decorator_lines(tag):
    """Generate @method_decorator lines for a given tag"""
    methods = ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']
    lines = []
    for method in methods:
        lines.append(f"@method_decorator(name='{method}', decorator=swagger_auto_schema(tags=['{tag}']))")
    return lines

def add_tags_to_file(filepath, output_filepath):
    """Add Swagger tags to all ViewSets"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    output = []
    i = 0
    while i < len(lines):
        # Check if this line contains a class definition that's a ViewSet
        match = re.match(r'^class (\w+ViewSet)\(', lines[i])
        
        if match:
            viewset_name = match.group(1)
            tag = VIEWSET_TAGS.get(viewset_name)
            
            if tag:
                # Check if decorators already exist
                # Look backwards from current line to see if there are @method_decorator lines
                j = i - 1
                has_decorators = False
                while j >= 0 and lines[j].strip().startswith('@'):
                    if 'swagger_auto_schema' in lines[j]:
                        has_decorators = True
                        break
                    j -= 1
                
                if not has_decorators:
                    # Add decorators before the class definition
                    decorator_lines = generate_decorator_lines(tag)
                    for dec in decorator_lines:
                        output.append(dec + '\n')
        
        output.append(lines[i])
        i += 1
    
    with open(output_filepath, 'w') as f:
        f.writelines(output)

if __name__ == '__main__':
    filepath = 'clientapp/api_views.py'
    output_filepath = 'clientapp/api_views_tagged.py'
    add_tags_to_file(filepath, output_filepath)
    print(f"Tagged file written to: {output_filepath}")
