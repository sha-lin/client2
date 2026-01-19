"""
Script to add Swagger tags to all ViewSets in api_views.py
Improved version that handles existing decorators
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
        content = f.read()
    
    # Split by class definition
    lines = content.split('\n')
    output = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line contains a class definition that's a ViewSet
        match = re.match(r'^class (\w+ViewSet)\(', line)
        
        if match:
            viewset_name = match.group(1)
            tag = VIEWSET_TAGS.get(viewset_name)
            
            if tag:
                # Look backwards to find start of decorators or other code
                j = len(output) - 1
                decorator_start_idx = -1
                
                # Find if decorators already exist for this viewset
                while j >= 0:
                    prev_line = output[j].strip()
                    if prev_line.startswith('@') and 'swagger_auto_schema' in prev_line:
                        # Found existing swagger decorators, don't add duplicates
                        decorator_start_idx = -2  # marker for "has decorators"
                        break
                    elif prev_line.startswith('@'):
                        # Regular decorator, keep going
                        j -= 1
                    elif prev_line == '' or prev_line.startswith('class '):
                        # End of decorators section
                        decorator_start_idx = j + 1
                        break
                    else:
                        # Found code before decorators
                        decorator_start_idx = len(output)
                        break
                
                # Only add decorators if we didn't find existing swagger_auto_schema decorators
                if decorator_start_idx != -2 and decorator_start_idx >= 0:
                    decorator_lines = generate_decorator_lines(tag)
                    for dec in decorator_lines:
                        output.append(dec)
                    output.append('')  # Add blank line
        
        output.append(line)
        i += 1
    
    with open(output_filepath, 'w') as f:
        f.write('\n'.join(output))

if __name__ == '__main__':
    filepath = 'clientapp/api_views.py'
    output_filepath = 'clientapp/api_views_tagged.py'
    add_tags_to_file(filepath, output_filepath)
    print(f"Tagged file written to: {output_filepath}")
    
    # Count tagged viewsets
    with open(output_filepath, 'r') as f:
        content = f.read()
    tags_added = content.count('@method_decorator')
    print(f"Total decorators added: {tags_added}")
    print(f"Total ViewSets tagged: {tags_added // 6}")
