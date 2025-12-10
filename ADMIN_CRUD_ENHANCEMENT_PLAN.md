# Admin Portal - CRUD Enhancement Plan

## ✅ CONFIRMED REQUIREMENTS

### Scope
- **Pages to Update:** Clients, Leads, Quotes, Products (BUSINESS tab in admin portal)
- **Changes:** Expand "Add New" forms to be comprehensive matching system functionality
- **Affected Portals:** ADMIN PORTAL ONLY - DO NOT modify Account Manager, Production, or other portals
- **Objective:** Ensure admins can create/manage items with ALL fields, just like AMs can

---

## PHASE 1: CLIENTS MANAGEMENT PAGE ⭐ (NEXT)

### Current State
- Simple modal with just 4 fields: name, email, phone, status
- Doesn't capture B2B vs B2C distinction
- Missing crucial fields

### What's Needed (from Client Model)

**Basic Information:**
- [ ] Client Type (B2B Business / B2C Retail) - RADIO BUTTONS
- [ ] Name (required)
- [ ] Company Name
- [ ] Email (required)
- [ ] Phone (required)

**Business Details:**
- [ ] VAT/Tax ID
- [ ] KRA PIN
- [ ] Industry
- [ ] Address

**Financial Settings:**
- [ ] Payment Terms (Prepaid, Net 7, Net 15, Net 30, Net 60)
- [ ] Credit Limit
- [ ] Default Markup %
- [ ] Risk Rating (Low, Medium, High)
- [ ] Is Reseller (checkbox)

**Delivery Details:**
- [ ] Delivery Address
- [ ] Delivery Instructions

**Account Management:**
- [ ] Preferred Channel (Email, Phone, WhatsApp, In-Person)
- [ ] Lead Source
- [ ] Account Manager (dropdown - assign to AM)
- [ ] Status (Active, Dormant, Inactive)

### Form Structure
Tabs/Sections:
1. **Basic Information** - Client Type, Name, Company, Email, Phone
2. **Business Details** - VAT, KRA PIN, Industry, Address
3. **Financial** - Payment Terms, Credit Limit, Markup, Risk Rating, Reseller
4. **Delivery** - Address, Instructions
5. **Account** - Channel, Lead Source, Account Manager, Status

### Database/API Changes
- Update ClientForm in forms.py to include all fields
- Update api_admin_create_client() in admin_api.py
- Update api_admin_update_client() in admin_api.py
- Update clients_list.html modal form

---

## PHASE 2: LEADS MANAGEMENT PAGE

### Current State
- No create form in admin portal leads page
- Need to check if there's an "Add New Lead" button

### What's Needed (from Lead Model)

**Basic Information:**
- [ ] Name (required)
- [ ] Email (required)
- [ ] Phone (required)
- [ ] Source (Website, Referral, Cold Call, Social Media, Event, Other)

**Business Details:**
- [ ] Product Interest (Product selector)
- [ ] Preferred Contact (Email, Phone, WhatsApp)
- [ ] Follow-up Date

**Management:**
- [ ] Status (New, Contacted, Qualified, Converted, Lost)
- [ ] Notes

### Form Structure
1. **Contact Information** - Name, Email, Phone
2. **Inquiry Details** - Source, Product Interest, Preferred Contact
3. **Follow-up** - Follow-up Date, Notes
4. **Status** - Status, Converted flag

---

## PHASE 3: QUOTES MANAGEMENT PAGE

### Current State
- List view exists
- Need to check for "Add New Quote" button

### What's Needed (from Quote Model)

**Product Info:**
- [ ] Product Name/Selection
- [ ] Quantity
- [ ] Unit Price
- [ ] Total Amount (auto-calculated)

**Client/Lead:**
- [ ] Client (dropdown)
- [ ] Lead (dropdown)

**Quote Details:**
- [ ] Status (Draft, Quoted, Client Review, Approved, Rejected)
- [ ] Production Status
- [ ] Payment Terms
- [ ] Include VAT (checkbox)
- [ ] Quote Date
- [ ] Valid Until (expiry)
- [ ] Due Date

**Production:**
- [ ] Production Cost
- [ ] Production Notes
- [ ] Notes
- [ ] Terms

**Tracking:**
- [ ] Created By (auto - current user)
- [ ] Costed By

### Form Structure
1. **Quote Info** - Quote ID (auto), Product, Quantity, Unit Price, Total
2. **Client/Lead** - Client selector, Lead selector
3. **Details** - Status, Production Status, Payment Terms, VAT
4. **Dates** - Quote Date, Valid Until, Due Date
5. **Production** - Production Cost, Production Notes
6. **Additional** - Notes, Terms

---

## PHASE 4: PRODUCTS MANAGEMENT PAGE

### Current State
- List view exists
- Need to check for "Add New Product" button

### What's Needed (from Product Model)

**Basic Info:**
- [ ] Name
- [ ] SKU (unique)
- [ ] Description
- [ ] Status (published, draft, archived)

**Pricing:**
- [ ] Base Price
- [ ] Category (dropdown)
- [ ] Sub-Category (dropdown)
- [ ] Product Family

**Details:**
- [ ] Tags (multi-select)
- [ ] Visibility (is_visible checkbox)
- [ ] Turn-around times (if needed)

### Form Structure
1. **Basic Information** - Name, SKU, Description, Status
2. **Organization** - Category, Sub-Category, Family, Tags
3. **Pricing** - Base Price, Visibility

---

## TEMPLATE CHANGES NEEDED

### Files to Modify
1. ✅ `clients_list.html` - Expand modal form
2. ⏳ `leads_list.html` - Add/expand create form
3. ⏳ `quotes_list.html` - Add/expand create form
4. ⏳ `products_list.html` - Add/expand create form

### Design Approach
- Keep existing UI/styling (don't change what works)
- Use tab-based forms or collapsible sections for large forms
- Match the professional styling already in place
- Maintain responsive design

---

## CODE CHANGES NEEDED

### Forms (`forms.py`)
- ✅ ClientForm - already has most fields, may need expansion
- ⏳ Verify/Expand LeadForm
- ⏳ Create/Expand QuoteForm
- ⏳ Create/Expand ProductForm

### Views (`views.py`)
- ✅ admin_clients_list() - already exists
- ⏳ admin_leads_list() - verify exists
- ⏳ admin_quotes_list() - verify exists
- ⏳ admin_products_list() - verify exists

### API (`admin_api.py`)
- ⏳ api_admin_create_client() - enhance
- ⏳ api_admin_update_client() - enhance
- ⏳ api_admin_create_lead() - may need new
- ⏳ api_admin_update_lead() - may need new
- ⏳ api_admin_create_quote() - may need new
- ⏳ api_admin_update_quote() - may need new
- ⏳ api_admin_create_product() - may need new
- ⏳ api_admin_update_product() - may need new

### URLs (`urls.py`)
- ⏳ Add any new API routes needed

---

## IMPLEMENTATION ORDER

1. **FIRST:** Clients Page
   - Most important, all businesses have clients
   - Will set template for other pages
   - Affects financials and operations

2. **SECOND:** Leads Page
   - Important for sales pipeline
   - Simpler model than clients

3. **THIRD:** Quotes Page
   - Critical for operations
   - Multiple dependencies (client, lead, product)

4. **FOURTH:** Products Page
   - Simpler model
   - Less dependencies

---

## CONFIRMATION CHECKLIST

Before I start making changes, please confirm:

- [ ] Start with CLIENTS page first
- [ ] Use form sections/tabs for large forms
- [ ] Keep existing UI styling
- [ ] DO NOT modify Account Manager portal
- [ ] DO NOT modify Production portal
- [ ] DO NOT modify any other portals
- [ ] Only enhance ADMIN PORTAL
- [ ] Include all model fields
- [ ] Ensure B2B/B2C distinction for clients
- [ ] Maintain CRUD functionality (Create, Read, Update, Delete)
- [ ] Keep modern styling consistent

---

## ESTIMATED CHANGES

### Per Page
- Template: 300-500 lines (form markup + styling)
- API: 100-200 lines (create/update endpoints)
- Form: 50-100 lines (field definitions)
- View: 20-50 lines (view enhancement)
- URLs: 2-4 lines (route additions)

### Total for 4 Pages
- ~2000 lines of template updates
- ~600 lines of API code
- ~200 lines of form code
- ~150 lines of view code
- ~12 lines of URL code

---

## NEXT STEPS

1. **Review & Confirm** this plan
2. **Start with Clients** page
3. Analyze current ClientForm and clients_list.html
4. Expand form with all Client model fields
5. Create/update API endpoints
6. Test create/edit/delete operations
7. Move to Leads page
8. Move to Quotes page
9. Move to Products page
10. Final testing and validation

**Ready to proceed with Clients page?** ✅

