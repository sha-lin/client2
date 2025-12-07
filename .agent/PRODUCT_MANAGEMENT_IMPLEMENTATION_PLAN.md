# Product Management System - Implementation Plan

## Overview
Replace the current basic product creation form with a comprehensive, multi-tab product management interface for the Production Team.

## Current State
- Simple product detail template (`product_detail.html`) with basic tabs
- Basic Product model with limited fields
- Simple `product_create` view that just renders the template

## Target State (Based on Screenshots)
A comprehensive product management system with 7 main tabs:

### 1. General Info Tab
**Sections:**
- **Basic Product Information**
  - Product Name
  - Internal SKU
  - Short Description (150 chars)
  - Long Description (2000 chars)
  - Technical Specifications

- **Classification**
  - Primary Category
  - Sub-Category
  - Product Type (Physical/Digital/Service/Hybrid)
  - Product Family

- **Tags**
  - Multiple tag support with add/remove functionality

- **Status & Visibility**
  - Product Status (Active/Draft/Archived)
  - Visibility toggle
  - Feature on badge toggle
  - Resellable badge toggle

- **Product Attributes**
  - Unit of Measure
  - Dimensions (L × W × H)
  - Country of Origin
  - Certifications

### 2. Pricing & Variables Tab
**Sections:**
- **Base Pricing Information**
  - Pricing Model dropdown
  - Base Cost (EVP)
  - Price Display options
  - Minimum Margin %
  - Default Margin %
  - Minimum Order Quantity

- **Production & Vendor Information**
  - Standard Lead Time
  - Production Method
  - Primary Vendor
  - Minimum Quantity
  - Bulk Cycle Date

- **Product Variants**
  - Add Variable button
  - Variant list with:
    - Display Order
    - Quantity Options
    - Pricing tiers (50pcs, 100pcs, 500pcs, 1000pcs)
    - Actions (edit, duplicate, delete, reorder)

- **Conditional Logic (Advanced)**
  - Enable Conditional Display Rules checkbox

- **Conflict Detection (Advanced)**
  - Enable Conflict Detection checkbox

- **Set Your Pricing**
  - Quantity input
  - Paper Weight selector
  - Lamination Sides selector
  - Calculation breakdown:
    - Base (KES + %)
    - Premium Paper
    - Labor Costing
    - Bulk Bonus
    - Subtotal EVP
    - Margin (%)
    - Per unit price

### 3. Images & Media Tab
**Sections:**
- **Product Images**
  - Primary Image (Required) - Drag & drop or click to browse
  - Additional Images (Gallery) - up to 10 images
  - Image preview with edit/delete options
  - Image editing dialog:
    - Alt Text (for SEO)
    - Caption
    - Image Type (Product Photo, Detail/Close-up, Mockup/In Use, Size Comparison, Sample/Example)
    - Associated With Variable Option
    - Coating dropdown
    - Save/Replace/Delete/Cancel buttons

- **Product Videos (Optional)**
  - Video URL input
  - Type dropdown (Product Demo, Tutorial, etc.)
  - Thumbnail upload
  - Add Video button
  - Supported: YouTube, Vimeo, Direct MP4 links

- **Downloadable Files (Templates, Specs, etc.)**
  - File upload with:
    - File Name
    - File Type (Adobe Illustrator, PDF, etc.)
    - Description
  - Upload File button (AI, PSD, PDF, ZIP - Max 10MB per file)

### 4. E-commerce & SEO Tab
**Sections:**
- **SEO Optimization**
  - Meta Title (52/60 chars)
  - Meta Description (145/160 chars)
  - URL Slug
  - Auto-generate from product name checkbox
  - Focus Keyword
  - Additional Keywords (tags)
  - Google Search Preview

- **Product Display Settings**
  - Show Price on Product Page toggle
  - Price Display Format (From KES 1,950)
  - How to show price dropdown
  - Show Stock Status toggle
  - Display inventory level checkbox
  - Related Products (Cross-sell products)
  - Upsell Products (Higher tier alternatives)
  - Frequently Bought Together

- **Customer Reviews Settings**
  - Enable customer reviews checkbox
  - Require Purchase checkbox
  - Auto-Approve Reviews toggle
  - Review Reminder (7 days after delivery)
  - Auto email after delivery checkbox

- **Frequently Asked Questions**
  - Add FAQ button
  - FAQ items with:
    - Question
    - Answer
    - Edit/Delete buttons

- **Shipping & Delivery**
  - Weight (for shipping) in kg
  - Shipping Class dropdown
  - Package Dimensions (L × W × H) in cm
  - Free shipping on this product checkbox
  - Free Shipping Threshold (KES)
  - Delivery Restrictions (Nairobi only, Kenya only, No international)
  - Handling Time (business days)
  - Available for pickup at Nairobi CBD checkbox

- **Legal & Compliance**
  - Product Specific Terms
  - Return Policy dropdown
  - Age 18+ required checkbox
  - Certifications (FSC Certified Paper, Eco Friendly, Food Safe)
  - Copyright Notice

### 5. Analytics Tab
**Note:** This tab shows data AFTER product has been published and has activity. For new products, show "No data yet".

**Sections:**
- **Sales Overview** (Last 90 Days dropdown)
  - Revenue (KES 245,000) with % change
  - Orders (18) with % change
  - Margin (28.5%) with % change
  - Avg Order (KES 13,611) with % change
  - Conversion (65%) with % change
  - Repeat Rate (22%) with % change

- **Revenue Trend (Last 6 Months)**
  - Bar chart showing monthly revenue

- **Most Popular Configurations**
  - Top 5 Configuration Ordered list with:
    - Configuration details (e.g., "500pcs, 385gsm, Matte, Both Sides")
    - Percentage and order count

- **Average Margin by Configuration**
  - Highest Margin configuration
  - Lowest Margin configuration

- **Customer Insights**
  - Page Views (Last 30 days)
  - Add to Cart Rate (% added)
  - Cart Abandonment (% abandoned)
  - Purchase Rate (% purchased)
  - Average Time on Page
  - Bounce Rate

- **Traffic Sources**
  - Visual bar chart showing:
    - Direct
    - Google Search
    - Social Media
    - Email Campaign

- **Self Quote Performance**
  - Self Quotes Generated
  - AM Approved (% of AM-approved)
  - Customer Approved (% of AM-approved)
  - Conversion to Order (% overall)
  - Common Rejection Reasons (AM Review)
  - Average Time to Quote
  - Average Quote Value

- **Customer Reviews**
  - Star rating (4.7/5.0)
  - Review count
  - Star distribution (5-star to 1-star with percentages)
  - Recent Reviews with:
    - Star rating
    - Review text
    - Reviewer name
    - Verified Purchase badge
    - Days ago
  - View All Reviews button

### 6. Production Tab
**Sections:**
- **Production Specifications**
  - Production Method
  - Equipment Required
  - Estimated Production Time
  - Setup Time
  - Quality Control Checkpoints

- **Material Requirements**
  - Primary Materials
  - Alternative Materials
  - Material Waste Factor (%)

- **Vendor Management**
  - Preferred Vendor
  - Alternative Vendors
  - Last Price Update
  - Vendor Lead Times

- **Production Notes**
  - Internal production notes
  - Special instructions
  - Common issues/solutions

### 7. History Tab
**Sections:**
- **Change Log**
  - Timestamp
  - User
  - Field Changed
  - Old Value → New Value
  - Reason (if provided)

- **Price History**
  - Date
  - Old Price
  - New Price
  - Changed By
  - Reason

- **Inventory History**
  - Date
  - Stock Change
  - New Stock Level
  - Changed By
  - Reason

## Implementation Phases

### Phase 1: Database Schema Updates
1. **Extend Product Model** with new fields:
   - Internal SKU
   - Technical specifications (TextField)
   - Product family (CharField)
   - Tags (ManyToManyField)
   - Product type extended (Physical/Digital/Service/Hybrid)
   - Dimensions (CharField)
   - Country of origin (CharField)
   - Certifications (JSONField or ManyToManyField)
   - SEO fields (meta_title, meta_description, focus_keyword)
   - Pricing fields (pricing_model, minimum_margin, default_margin, moq)
   - Production fields (production_method, equipment_required, setup_time)
   - E-commerce fields (enable_reviews, auto_approve_reviews, etc.)

2. **Create New Models:**
   - `ProductTag` - For tagging products
   - `ProductVariant` - For product variations with pricing tiers
   - `ProductVideo` - For product videos
   - `ProductDownloadableFile` - For templates/specs
   - `ProductFAQ` - For frequently asked questions
   - `ProductReview` - For customer reviews
   - `ProductAnalytics` - For tracking analytics data
   - `ProductChangeLog` - For history tracking
   - `ProductVendor` - For vendor management

3. **Create Migrations**

### Phase 2: Backend Implementation
1. **Create Forms:**
   - `ProductGeneralInfoForm`
   - `ProductPricingForm`
   - `ProductVariantFormSet`
   - `ProductImageFormSet`
   - `ProductVideoFormSet`
   - `ProductFileFormSet`
   - `ProductSEOForm`
   - `ProductFAQFormSet`
   - `ProductShippingForm`

2. **Update Views:**
   - `product_create` - Handle multi-step form submission
   - `product_edit` - Edit existing products
   - `product_delete` - Soft delete products
   - AJAX endpoints for:
     - Adding/removing variants
     - Uploading images
     - Uploading files
     - Managing FAQs
     - Auto-generating URL slugs

3. **Create API Endpoints** (if needed):
   - Analytics data fetching
   - Review management
   - Change log retrieval

### Phase 3: Frontend Implementation
1. **Create New Template:** `product_create_edit.html`
   - Tab navigation system
   - Form sections for each tab
   - JavaScript for tab switching
   - Form validation
   - AJAX file uploads
   - Dynamic form fields (add/remove variants, FAQs, etc.)

2. **Create Partial Templates:**
   - `_general_info_tab.html`
   - `_pricing_variables_tab.html`
   - `_images_media_tab.html`
   - `_ecommerce_seo_tab.html`
   - `_analytics_tab.html`
   - `_production_tab.html`
   - `_history_tab.html`

3. **JavaScript Components:**
   - Tab manager
   - Form validation
   - Image upload with preview
   - Variant manager (add/remove/reorder)
   - FAQ manager
   - Price calculator
   - Auto-save draft functionality

4. **Styling:**
   - Match the design from screenshots
   - Responsive design
   - Loading states
   - Error states
   - Success messages

### Phase 4: Integration & Testing
1. **Integration:**
   - Connect to existing product catalog
   - Update product listing to show new fields
   - Update quote creation to use new product structure

2. **Testing:**
   - Unit tests for models
   - Integration tests for views
   - Frontend validation testing
   - Cross-browser testing
   - Mobile responsiveness testing

3. **Data Migration:**
   - Migrate existing products to new structure
   - Set default values for new fields

### Phase 5: Documentation & Training
1. **User Documentation:**
   - How to create a product
   - How to manage variants
   - How to upload media
   - How to interpret analytics

2. **Admin Training:**
   - Train production team on new interface
   - Create video tutorials

## Technical Considerations

### File Uploads
- Use Django's FileField/ImageField
- Implement file size validation
- Image optimization (resize, compress)
- Secure file storage

### Performance
- Lazy load analytics data
- Paginate change history
- Optimize database queries (select_related, prefetch_related)
- Cache frequently accessed data

### Security
- CSRF protection
- File upload validation
- Permission checks (only Production Team)
- Sanitize user inputs

### User Experience
- Auto-save drafts
- Unsaved changes warning
- Inline validation
- Clear error messages
- Loading indicators
- Success confirmations

## Priority Order (Recommended)

### High Priority (MVP):
1. General Info Tab
2. Pricing & Variables Tab (basic version without advanced features)
3. Images & Media Tab (images only)
4. Basic form submission and validation

### Medium Priority:
1. E-commerce & SEO Tab
2. Advanced pricing features (conditional logic, conflict detection)
3. Videos and downloadable files
4. Production Tab

### Low Priority (Can be added later):
1. Analytics Tab (requires data collection over time)
2. History Tab
3. Advanced features (auto-save, etc.)

## Estimated Timeline
- **Phase 1 (Database):** 2-3 days
- **Phase 2 (Backend):** 5-7 days
- **Phase 3 (Frontend):** 7-10 days
- **Phase 4 (Integration & Testing):** 3-5 days
- **Phase 5 (Documentation):** 2-3 days

**Total:** 3-4 weeks for full implementation

## Next Steps
1. Review and approve this plan
2. Prioritize which tabs/features to implement first
3. Start with Phase 1 (Database Schema Updates)
4. Implement in iterative sprints (one tab at a time)
