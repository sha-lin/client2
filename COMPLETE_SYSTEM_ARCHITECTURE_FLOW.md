#  COMPLETE SYSTEM ARCHITECTURE & FLOW DOCUMENTATION

**System Name:** Print Management & Order Fulfillment Platform  
**Technology Stack:** Django REST Framework + PostgreSQL  
**Last Updated:** January 25, 2026  
**Status:**  Production Ready

---

## TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [User Roles & Permissions](#user-roles--permissions)
4. [Database Schema Overview](#database-schema-overview)
5. [Complete API Endpoint Reference](#complete-api-endpoint-reference)
6. [Workflow Flows](#workflow-flows)
7. [Authentication & Security](#authentication--security)
8. [Data Flow Diagrams](#data-flow-diagrams)
9. [Integration Points](#integration-points)
10. [Error Handling & Notifications](#error-handling--notifications)

---

## SYSTEM OVERVIEW

### Purpose
A comprehensive B2B/B2C print shop management system that handles:
- Lead management and conversion to clients
- Product catalog with configurable options
- Quote generation and approval workflows
- Job creation and production tracking
- Vendor management and purchase orders
- Invoice processing and payment handling
- Quality control and delivery management
- Client portal access
- Production team coordination

### Key Features
- ✅ Multi-tenant capable (B2B and B2C support)
- ✅ Hierarchical approval workflows
- ✅ Vendor management and collaboration
- ✅ Dynamic pricing (tier-based and formula-based)
- ✅ Product customization with variables
- ✅ QC and delivery tracking
- ✅ QuickBooks integration
- ✅ Notification system (Email, SMS, In-App)
- ✅ Real-time activity logging
- ✅ Dashboard analytics

---

## 🏛️ CORE ARCHITECTURE

### Technology Stack
```
Backend:
  - Django 4.2.25
  - Django REST Framework (DRF)
  - PostgreSQL Database
  - Celery (async tasks)
  
Authentication:
  - JWT (JSON Web Tokens) via rest_framework_simplejwt
  - Session-based authentication
  - Role-based access control (RBAC)
  
API Documentation:
  - drf-yasg (Swagger/OpenAPI)
  
Infrastructure:
  - Gunicorn (WSGI server)
  - WhiteNoise (static files)
  - CORS enabled for frontend integration
```

### Application Structure
```
client/                          # Main Django project
├── client/
│   ├── settings.py             # Configuration
│   ├── urls.py                 # Main URL routing
│   ├── wsgi.py                 # WSGI application
│   └── asgi.py                 # ASGI application
└── clientapp/                  # Main application
    ├── models.py               # Database models (5615 lines)
    ├── api_views.py            # API viewsets (5643 lines)
    ├── api_serializers.py      # Serializers for API
    ├── api_urls.py             # API URL routing
    ├── permissions.py          # Custom permission classes
    ├── views.py                # HTML template views
    ├── urls.py                 # Template URL routing
    ├── admin.py                # Django admin configuration
    ├── admin_views.py          # Admin dashboard views
    ├── admin_crud_views.py     # Admin CRUD operations
    ├── vendor_portal_views.py  # Vendor portal views
    ├── vendor_notifications.py # Vendor notification service
    ├── tasks.py                # Celery async tasks
    ├── storefront_services.py  # E-commerce services
    └── templates/              # HTML templates
```

---

## 👥 USER ROLES & PERMISSIONS

### 1. **Admin**
**Group Name:** Admin  
**Access Level:** Full system access

**Capabilities:**
- ✅ CRUD all entities (Leads, Clients, Products, Jobs, Vendors, etc.)
- ✅ System configuration and settings
- ✅ User management
- ✅ Access to all restricted endpoints
- ✅ Override any approval workflow
- ✅ View all analytics and reports

**Key Endpoints:**
- All `/admin/` endpoints
- All API endpoints with `IsAdmin` permission
- User and group management
- System settings configuration

---

### 2. **Account Manager (AM)**
**Group Name:** Account Manager  
**Access Level:** Lead and Client management

**Responsibilities:**
- Lead intake and nurturing
- Lead qualification and conversion
- Client onboarding
- Quote creation and management
- Order follow-up and support
- Client profile management

**Capabilities:**
- ✅ Create and manage leads
- ✅ Convert leads to clients
- ✅ Create multi-product quotes
- ✅ View client profiles and history
- ✅ Assign jobs to Production Team
- ✅ View quote status and approvals
- ✅ Manage client contacts and documents
- ❌ Cannot approve quotes (that's client's role)
- ❌ Cannot manage vendors or processes

**Key Endpoints:**
- `POST /api/v1/leads/` - Create lead
- `POST /api/v1/leads/{id}/qualify/` - Qualify lead
- `GET /api/v1/clients/` - List clients
- `POST /api/v1/clients/` - Onboard client
- `GET /api/v1/quotes/` - List quotes
- `POST /api/v1/quotes/` - Create quote
- `POST /api/v1/jobs/{id}/assign/` - Assign job to PT
- `GET /api/v1/jobs/` - List jobs

**Data Visibility:**
- Own leads only (unless Admin)
- All assigned clients
- Quotes created by them
- Jobs assigned to their clients

---

### 3. **Production Team (PT)**
**Group Name:** Production Team  
**Access Level:** Job management and vendor coordination

**Responsibilities:**
- Job planning and scheduling
- Vendor selection and coordination
- Purchase order creation and tracking
- Quality control and delivery
- Job status monitoring
- Process and product management

**Capabilities:**
- ✅ View job specifications
- ✅ Send jobs to vendors (create PO)
- ✅ Accept/decline vendor proposals
- ✅ Track vendor progress
- ✅ Create and manage processes
- ✅ Create and manage products
- ✅ Create and manage vendors
- ✅ Monitor QC inspections
- ✅ Approve purchase order proofs
- ✅ Mark jobs as complete
- ✅ View cost calculations
- ❌ Cannot modify quotes (read-only)
- ❌ Cannot manage clients directly

**Key Endpoints:**
- `GET /api/v1/jobs/` - View jobs
- `POST /api/v1/jobs/{id}/send_to_vendor/` - Send to vendor
- `GET /api/v1/vendors/` - List vendors
- `POST /api/v1/vendors/` - Create vendor
- `GET /api/v1/processes/` - List processes
- `POST /api/v1/processes/` - Create process
- `POST /api/v1/products/` - Create product
- `POST /api/v1/qc-inspections/` - Create QC record
- `POST /api/v1/purchase-orders/{id}/approve/` - Approve PO
- `GET /api/v1/costing-engine/` - View pricing

**Data Visibility:**
- All jobs and their details
- All vendors and their performance
- All processes and products
- All QC records and deliveries
- Assigned jobs only (for personal workload)

---

### 4. **Vendor**
**Group Name:** Vendor Portal Users (via Vendor model)  
**Access Level:** Purchase order and invoice management

**Responsibilities:**
- Receive job assignments
- Accept/decline work
- Report production progress
- Submit quality proofs
- Request material substitutions
- Submit invoices
- Manage delivery

**Capabilities:**
- ✅ View assigned purchase orders
- ✅ Accept/decline purchase orders
- ✅ Update job progress (milestones)
- ✅ Submit quality proofs
- ✅ Request material substitutions
- ✅ Submit invoices
- ✅ View invoice status
- ❌ Cannot view other vendors' POs
- ❌ Cannot create jobs
- ❌ Cannot modify pricing

**Key Endpoints:**
- `GET /api/v1/purchase-orders/vendor_dashboard/` - Dashboard
- `GET /api/v1/purchase-orders/?vendor={id}` - Vendor's POs
- `POST /api/v1/purchase-orders/{id}/accept/` - Accept PO
- `POST /api/v1/purchase-orders/{id}/decline/` - Decline PO
- `POST /api/v1/purchase-orders/{id}/update_milestone/` - Progress update
- `POST /api/v1/purchase-order-proofs/` - Submit proof
- `POST /api/v1/material-substitutions/` - Request substitution
- `POST /api/v1/vendor-invoices/` - Submit invoice

**Data Visibility:**
- Own purchase orders only
- Own invoices and payments only
- Assigned job details only
- Cannot see other vendors' data

---

### 5. **Client Portal User**
**Group Name:** N/A (via ClientPortalUser model)  
**Access Level:** Order and invoice viewing

**Responsibilities:**
- Place orders/create quotes
- Approve quotes
- Track order status
- Download invoices
- Submit support tickets
- Access brand assets

**Capabilities:**
- ✅ Create order requests
- ✅ Approve/reject quotes
- ✅ View order status
- ✅ Download invoices
- ✅ Submit support tickets
- ✅ Upload brand assets
- ✅ View delivery status
- ❌ Cannot modify quote pricing
- ❌ Cannot create jobs
- ❌ Cannot access other clients' data

**Key Endpoints:**
- `GET /api/v1/client-orders/` - View orders
- `POST /api/v1/quotes/{id}/approve/` - Approve quote
- `GET /api/v1/client-invoices/` - View invoices
- `POST /api/v1/client-support-tickets/` - Create ticket
- `POST /api/v1/deliveries/` - Track delivery

---

## 🗄️ DATABASE SCHEMA OVERVIEW

### Core Entity Groups

#### 1. **Lead & Client Management**
```
Lead
├── lead_id (auto-generated: LD-YYYY-XXX)
├── name, email, phone
├── status (New, Contacted, Qualified, Converted, Lost)
├── source (Website, Referral, Cold Call, Social Media, Event)
├── product_interest
├── preferred_contact (Email, Phone, WhatsApp)
├── preferred_client_type (B2B, B2C)
├── follow_up_date
├── notes
├── converted_to_client (boolean)
├── created_by (ForeignKey: User)
└── timestamps

Client
├── client_id (auto-generated: CL-YYYY-XXX)
├── client_type (B2B, B2C)
├── company, name, email, phone
├── vat_tax_id, kra_pin
├── address, industry
├── payment_terms (Prepaid, Net 7/15/30/60)
├── credit_limit
├── default_markup
├── risk_rating (Low, Medium, High)
├── is_reseller
├── delivery_address, delivery_instructions
├── preferred_channel (Email, Phone, WhatsApp, In-Person)
├── status (Active, Dormant, Inactive)
├── account_manager (ForeignKey: User)
├── converted_from_lead (OneToOne: Lead)
└── tracking fields (created_at, updated_at, last_activity)

ClientContact
├── client (ForeignKey: Client)
├── full_name, email, phone
├── role (None, Approve Quotes, Approve Artwork, Billing Contact)
├── is_primary
└── timestamps

BrandAsset
├── client (ForeignKey: Client)
├── asset_type (Logo, Brand Guide, Color Palette, Font, Other)
├── file
├── description
├── uploaded_by (ForeignKey: User)
└── uploaded_at

ComplianceDocument
├── client (ForeignKey: Client)
├── document_type (COI, KRA, PO Terms, NDA, Other)
├── file, expiry_date, notes
├── uploaded_by (ForeignKey: User)
└── is_expired, expires_soon (properties)
```

#### 2. **Product Management**
```
ProductCategory
├── name, slug, description
└── ordering: name

ProductSubCategory
├── category (ForeignKey: ProductCategory)
├── name, slug, description
└── unique_together: (category, slug)

Product
├── product_id (auto-generated)
├── product_name, sku
├── description, long_description
├── customization_level (non_customizable, semi_customizable, fully_customizable)
├── product_type (physical, digital, service)
├── visibility (catalog-search, catalog-only, search-only, hidden)
├── unit_of_measure (pieces, packs, sets, sqm, other)
├── base_price, cost_price
├── weight, weight_unit
├── dimensions (height, width, depth), dimension_unit
├── status (active, draft, archived)
├── metadata
│   ├── ProductImage
│   ├── ProductVideo
│   ├── ProductDownloadableFile
│   ├── ProductSEO
│   ├── ProductReviewSettings
│   ├── ProductFAQ
│   ├── ProductShipping
│   ├── ProductLegal
│   ├── ProductProduction
│   ├── ProductChangeHistory
│   ├── ProductTemplate
│   └── ProductRule
├── related
│   ├── PropertyTypes (attributes available)
│   ├── QuantityPricing (bulk pricing tiers)
│   ├── TurnAroundTimes (delivery time ranges)
│   └── Variables (configurable options)
└── timestamps

PropertyType
├── property_name (Size, Color, Material, Finish, etc.)
├── description
└── ordering

PropertyValue
├── property_type (ForeignKey: PropertyType)
├── value (e.g., "Red", "A4", "Glossy")
├── display_order
└── is_active

ProductProperty
├── product (ForeignKey: Product)
├── property_type (ForeignKey: PropertyType)
├── property_value (ForeignKey: PropertyValue)
└── is_required

ProductVariable
├── product (ForeignKey: Product)
├── name (Quantity Options, Paper Weight, etc.)
├── variable_type (required, conditional, optional)
├── pricing_type (fixed, increment, percentage, none)
├── source_process_variable (ForeignKey: ProcessVariable)
├── conditional_logic
├── is_active
└── timestamps

ProductVariableOption
├── product_variable (ForeignKey: ProductVariable)
├── option_value (e.g., "100", "500", "1000")
├── display_order
├── price_adjustment
├── cost_adjustment
└── is_default

QuantityPricing
├── product (ForeignKey: Product)
├── quantity_from, quantity_to
├── unit_price, unit_cost
├── margin, margin_percentage
└── discount_percentage

TurnAroundTime
├── product (ForeignKey: Product)
├── quantity_from, quantity_to
├── standard_days, rush_days, expedited_days
└── rush_pricing_adjustment, expedited_pricing_adjustment
```

#### 3. **Quote & Order Management**
```
Quote
├── quote_id (auto-generated: QT-YYYY-XXX)
├── client (ForeignKey: Client)
├── product_name, description
├── quantity, unit_price
├── total_amount
├── markup_percentage
├── status (Draft, Sent, Viewed, Approved, Rejected, Expired, Converted)
├── channel (Email, Phone, In-Person, WhatsApp)
├── valid_until (3 days default)
├── payment_method (Bank Transfer, Card, Cash, Check, Credit)
├── notes
├── created_by (ForeignKey: User - Account Manager)
├── approved_by (ForeignKey: User - Client contact)
├── approval_date, approval_notes
├── converted_to_job (boolean)
└── timestamps

QuoteLineItem
├── quote (ForeignKey: Quote)
├── product (ForeignKey: Product)
├── product_name, description
├── quantity, unit_price
├── line_total
├── properties (JSON: selected attributes)
├── customization_details (JSON)
└── sequence_number

QuoteAttachment
├── quote (ForeignKey: Quote)
├── file, file_type
├── uploaded_by (ForeignKey: User)
└── uploaded_at

Job
├── job_id (auto-generated)
├── job_number (auto-generated: JOB-YYYY-XXX)
├── quote (ForeignKey: Quote)
├── client (ForeignKey: Client)
├── job_name, product, job_type
├── quantity
├── priority (low, normal, high, urgent)
├── status (pending, in_progress, on_hold, completed, cancelled)
├── person_in_charge (ForeignKey: User - PT member)
├── notes
├── expected_delivery
├── actual_delivery
├── created_by (ForeignKey: User)
└── timestamps

JobVendorStage
├── job (ForeignKey: Job)
├── vendor (ForeignKey: Vendor)
├── stage_name (e.g., "Printing", "Design", "Quality Check")
├── stage_order
├── status (sent_to_vendor, in_progress, completed, declined, on_hold)
├── expected_completion
├── actual_completion
├── notes
└── timestamps

JobNote
├── job (ForeignKey: Job)
├── note_type (internal, vendor_communication, status_update)
├── content
├── created_by (ForeignKey: User)
└── created_at

JobAttachment
├── job (ForeignKey: Job)
├── file, file_name, file_size
├── attachment_type (design, specification, proof, other)
├── uploaded_by (ForeignKey: User)
└── uploaded_at
```

#### 4. **Process & Costing Configuration**
```
Process
├── process_id (auto-generated: e.g., PR-PRI-DES)
├── process_name (e.g., "Printing Design")
├── description, category (outsourced, in_house)
├── standard_lead_time (days)
├── pricing_type (tier, formula)
├── unit_of_measure
├── base_cost
├── approval_type, approval_margin_threshold
├── status (draft, active, inactive)
├── created_by (ForeignKey: User - PT)
└── timestamps

ProcessTier
├── process (ForeignKey: Process)
├── tier_number
├── quantity_from, quantity_to
├── price, cost
├── per_unit_price, margin_amount, margin_percentage (calculated)
└── unique_together: (process, tier_number)

ProcessVariable
├── process (ForeignKey: Process)
├── variable_name (e.g., "Thread Color", "Embroidery Stitches")
├── variable_type (number, alphanumeric)
├── unit (e.g., stitches, m, cm)
├── variable_value (single value for this variable)
├── price, rate
├── min_value, max_value, default_value
├── description, order
└── formula-based pricing support

ProcessVariableRange
├── process_variable (ForeignKey: ProcessVariable)
├── range_from, range_to
├── price_per_unit, cost_per_unit
└── is_default

ProcessVendor
├── process (ForeignKey: Process)
├── vendor (ForeignKey: Vendor)
├── vendor_rank (preferred, alternate, backup)
├── lead_time_days
├── cost_per_unit
├── minimum_order_quantity
├── notes
├── is_active
└── timestamps

PricingTier
├── name, description
├── tier_level
└── ordering

VendorTierPricing
├── vendor (ForeignKey: Vendor)
├── pricing_tier (ForeignKey: PricingTier)
├── base_markup_percentage
├── volume_discount
└── is_active
```

#### 5. **Vendor & Purchase Order Management**
```
Vendor
├── vendor_id (auto-generated: VEN-YYYY-XXX)
├── name, slug
├── description, category
├── country, location, address
├── phone, email, website
├── contact_person, contact_email, contact_phone
├── vat_number, tax_id
├── bank_details (JSON)
├── payment_terms
├── lead_time_days
├── minimum_order_value
├── vps_score_value (Vendor Performance Score)
├── rating, review_count
├── documents
│   ├── vps_certificate
│   ├── bank_guarantee
│   ├── compliance_certificate
│   └── agreement_document
├── integration
│   ├── has_api_integration
│   ├── api_key, api_endpoint
│   └── last_sync
├── user (OneToOne: User - for vendor portal)
├── active (boolean)
├── created_by (ForeignKey: User - PT)
└── timestamps

VendorQuote
├── vendor (ForeignKey: Vendor)
├── job (ForeignKey: Job)
├── quote_number (auto-generated)
├── quoted_price, cost_estimate
├── timeline_days
├── notes, terms
├── status (pending, accepted, rejected, expired)
└── timestamps

PurchaseOrder
├── po_number (auto-generated: PO-YYYY-XXXX)
├── job (ForeignKey: Job)
├── vendor (ForeignKey: Vendor)
├── status (NEW, ACCEPTED, DECLINED, IN_PROGRESS, COMPLETED)
├── estimated_cost
├── actual_cost
├── payment_status (unpaid, partial, paid)
├── vendor_accepted (boolean)
├── vendor_accepted_at (timestamp)
├── created_at
├── expected_completion, actual_completion
├── notes
└── attachments (array of file IDs)

PurchaseOrderProof
├── purchase_order (ForeignKey: PurchaseOrder)
├── proof_type (sample, quality_check, photo, certificate)
├── file, file_name
├── description
├── status (pending, approved, rejected)
├── submitted_by (ForeignKey: Vendor.user)
├── submitted_at
├── reviewed_by (ForeignKey: User - PT)
├── reviewed_at, review_notes
└── approved_at

PurchaseOrderIssue
├── purchase_order (ForeignKey: PurchaseOrder)
├── issue_type (quality, delay, incomplete, other)
├── description
├── severity (low, medium, high)
├── status (open, in_progress, resolved)
├── raised_by (ForeignKey: User)
├── resolution_notes
└── timestamps

PurchaseOrderNote
├── purchase_order (ForeignKey: PurchaseOrder)
├── note_type (internal, vendor_communication)
├── content
├── created_by (ForeignKey: User)
└── created_at

MaterialSubstitutionRequest
├── purchase_order (ForeignKey: PurchaseOrder)
├── original_material
├── proposed_material
├── reason
├── status (pending, approved, rejected)
├── requested_by (ForeignKey: Vendor.user)
├── approved_by (ForeignKey: User - PT)
└── timestamps
```

#### 6. **Finance & Invoicing**
```
VendorInvoice
├── invoice_number (auto-generated: INV-YYYY-XXXX)
├── vendor (ForeignKey: Vendor)
├── purchase_order (ForeignKey: PurchaseOrder)
├── invoice_date
├── invoice_amount
├── tax_amount
├── total_amount
├── payment_status (unpaid, partial, paid)
├── status (draft, sent, received, approved, rejected)
├── payment_method
├── notes
├── file (invoice document)
├── submitted_by (ForeignKey: Vendor.user)
├── submitted_date
├── reviewed_by (ForeignKey: User - PT)
├── reviewed_date
├── approval_notes
└── timestamps

Payment
├── payment_number (auto-generated)
├── vendor (ForeignKey: Vendor)
├── invoice (ForeignKey: VendorInvoice)
├── amount, amount_paid
├── payment_date
├── payment_method (bank_transfer, check, cash, card)
├── reference_number
├── notes
├── recorded_by (ForeignKey: User)
└── timestamps

Refund
├── refund_number (auto-generated)
├── payment (ForeignKey: Payment)
├── amount
├── reason
├── status (pending, processed, completed, cancelled)
├── initiated_by (ForeignKey: User)
└── timestamps

CreditNote
├── credit_note_number (auto-generated)
├── vendor (ForeignKey: Vendor)
├── invoice (ForeignKey: VendorInvoice)
├── amount
├── reason
├── status (draft, issued, applied)
└── timestamps

Adjustment
├── purchase_order (ForeignKey: PurchaseOrder)
├── adjustment_type (discount, surcharge, tax_adjustment)
├── amount
├── reason
├── created_by (ForeignKey: User)
└── created_at

LPO (Local Purchase Order)
├── lpo_number (auto-generated)
├── quote (ForeignKey: Quote)
├── job (ForeignKey: Job)
├── vendor (ForeignKey: Vendor)
├── status (draft, issued, accepted, received, completed)
├── total_amount
├── notes
├── synced_to_quickbooks (boolean)
├── quickbooks_id
└── timestamps

LPOLineItem
├── lpo (ForeignKey: LPO)
├── description, quantity
├── unit_price, line_amount
└── sequence_number
```

#### 7. **Quality Control & Delivery**
```
QCInspection
├── qc_inspection_id (auto-generated)
├── job (ForeignKey: Job)
├── purchase_order (ForeignKey: PurchaseOrder)
├── inspection_date
├── inspection_type (incoming, in_process, final)
├── inspector (ForeignKey: User - PT)
├── status (passed, failed, conditional_pass)
├── findings (text)
├── issues_found
│   ├── issue_type (color, dimension, quality, packaging)
│   ├── severity (minor, major, critical)
│   ├── description
│   └── resolution
├── photos (array)
├── approved_by (ForeignKey: User - PT Lead)
├── approval_date, approval_notes
└── timestamps

Delivery
├── delivery_id (auto-generated)
├── job (ForeignKey: Job)
├── delivery_date
├── delivery_location
├── recipient, recipient_contact
├── delivery_method (pickup, courier, custom)
├── tracking_number
├── status (pending, in_transit, delivered, delayed, cancelled)
├── delivery_notes
├── signature_proof (file)
├── delivery_proof (files array)
├── created_by (ForeignKey: User - PT)
└── timestamps

Shipment
├── shipment_id (auto-generated)
├── job (ForeignKey: Job)
├── delivery (ForeignKey: Delivery)
├── shipment_number
├── quantity_shipped
├── weight, dimensions
├── carrier_name
├── tracking_number
├── estimated_arrival
├── status (pending, in_transit, delivered)
└── timestamps
```

#### 8. **Client Portal Models**
```
ClientPortalUser
├── user (OneToOne: User)
├── client (ForeignKey: Client)
├── role (owner, admin, user)
├── is_active
├── last_login
└── created_at

ClientOrder
├── order_id (auto-generated)
├── client (ForeignKey: Client)
├── order_date
├── total_amount
├── status (pending, processing, ready, delivered)
└── timestamps

ClientOrderItem
├── order (ForeignKey: ClientOrder)
├── product (ForeignKey: Product)
├── quantity, unit_price
├── line_total
└── properties (JSON)

ClientInvoice
├── invoice_id (auto-generated)
├── client (ForeignKey: Client)
├── order (ForeignKey: ClientOrder)
├── invoice_date, due_date
├── total_amount, paid_amount
├── status (draft, sent, viewed, paid, overdue)
└── timestamps

ClientPayment
├── payment_id (auto-generated)
├── client (ForeignKey: Client)
├── invoice (ForeignKey: ClientInvoice)
├── payment_date, amount
├── payment_method
└── reference_number

ClientSupportTicket
├── ticket_id (auto-generated: TKT-YYYY-XXXX)
├── client (ForeignKey: Client)
├── subject, description
├── priority (low, medium, high, urgent)
├── status (open, in_progress, resolved, closed)
├── category (technical, billing, delivery, general)
├── assigned_to (ForeignKey: User)
├── created_by (ForeignKey: ClientPortalUser)
└── timestamps

ClientTicketReply
├── ticket (ForeignKey: ClientSupportTicket)
├── reply_text
├── created_by (ForeignKey: User or ClientPortalUser)
└── created_at

ClientDocumentLibrary
├── document_id (auto-generated)
├── client (ForeignKey: Client)
├── document_type (brand_asset, invoice, proof, delivery_note)
├── file, document_name
├── uploaded_by (ForeignKey: User)
└── uploaded_at

ClientPortalNotification
├── notification_id (auto-generated)
├── client (ForeignKey: Client)
├── notification_type (order_status, invoice, delivery, support)
├── title, message
├── is_read
└── created_at

ClientActivityLog
├── log_id (auto-generated)
├── client (ForeignKey: Client)
├── activity_type (order_placed, payment_made, document_viewed)
├── description
├── created_at
└── user_agent (for tracking)
```

#### 9. **System & Operational Models**
```
Notification
├── recipient (ForeignKey: User)
├── notification_type (lead_qualified, job_assigned, quote_approved, etc.)
├── title, message, link
├── is_read
├── created_at

ActivityLog
├── client (ForeignKey: Client, nullable)
├── activity_type (Note, Job, Quote, Invoice, etc.)
├── title, description
├── created_by (ForeignKey: User)
└── created_at

SystemSetting
├── key (e.g., "default_markup", "payment_terms_default")
├── value (JSON)
├── description
├── data_type (string, number, boolean, json)
└── is_active

SystemAlert
├── alert_type (warning, critical, info)
├── title, message
├── is_active
├── created_at
└── dismissible

TimelineEvent
├── event_type (job_created, quote_approved, payment_received)
├── related_object_id
├── title, description
├── event_date
└── created_at

ProductionUpdate
├── job (ForeignKey: Job)
├── update_type (status, milestone, issue)
├── title, description
├── updated_by (ForeignKey: User - PT)
└── created_at

ApprovalThreshold
├── role (e.g., "invoice_approver")
├── user (ForeignKey: User)
├── min_amount, max_amount
├── is_active
└── created_at

InvoiceDispute
├── invoice (ForeignKey: VendorInvoice)
├── dispute_reason
├── amount_disputed
├── status (open, in_review, resolved)
├── created_by (ForeignKey: User)
└── timestamps

JobProgressUpdate
├── job (ForeignKey: Job)
├── update_text
├── milestone_status
├── updated_by (ForeignKey: User - PT or Vendor)
└── created_at

SLAEscalation
├── job (ForeignKey: Job)
├── escalation_type (delay, quality_issue)
├── escalation_level
├── created_at
└── resolved_at

VendorPerformanceMetrics
├── vendor (ForeignKey: Vendor)
├── period_start, period_end
├── on_time_delivery_rate
├── quality_score
├── response_time_average
└── calculated_at

ProfitabilityAnalysis
├── job (ForeignKey: Job)
├── total_revenue
├── total_cost
├── profit_margin
├── calculated_at
└── notes
```

---

## 🔌 COMPLETE API ENDPOINT REFERENCE

### API Base URL
```
http://localhost:8000/api/v1/
```

### Authentication Headers
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

### API Endpoints by Category

#### **1. LEAD MANAGEMENT** (Account Manager)
```
GET    /api/v1/leads/                          # List all leads (filtered by AM)
POST   /api/v1/leads/                          # Create new lead
GET    /api/v1/leads/{id}/                     # Get lead details
PUT    /api/v1/leads/{id}/                     # Update lead
DELETE /api/v1/leads/{id}/                     # Delete lead
POST   /api/v1/leads/{id}/qualify/             # Move to Qualified status
```

**Request Example (Create Lead):**
```json
{
  "name": "John Smith",
  "email": "john@example.com",
  "phone": "+254701234567",
  "source": "Website",
  "product_interest": "Business Cards",
  "preferred_contact": "Email",
  "preferred_client_type": "B2B",
  "follow_up_date": "2026-02-15",
  "notes": "Interested in bulk pricing"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "lead_id": "LD-2026-001",
  "name": "John Smith",
  "email": "john@example.com",
  "phone": "+254701234567",
  "source": "Website",
  "status": "New",
  "created_at": "2026-01-25T10:30:00Z",
  "created_by": 5
}
```

---

#### **2. CLIENT MANAGEMENT** (Account Manager)
```
GET    /api/v1/clients/                        # List clients
POST   /api/v1/clients/                        # Onboard new client
GET    /api/v1/clients/{id}/                   # Get client profile
PUT    /api/v1/clients/{id}/                   # Update client info
DELETE /api/v1/clients/{id}/                   # Delete client

GET    /api/v1/client-contacts/                # List client contacts
POST   /api/v1/client-contacts/                # Add contact to client
GET    /api/v1/client-contacts/{id}/           # Get contact
PUT    /api/v1/client-contacts/{id}/           # Update contact

GET    /api/v1/brand-assets/                   # List brand assets
POST   /api/v1/brand-assets/                   # Upload brand asset
DELETE /api/v1/brand-assets/{id}/              # Delete asset

GET    /api/v1/compliance-documents/           # List compliance docs
POST   /api/v1/compliance-documents/           # Upload document
PUT    /api/v1/compliance-documents/{id}/      # Update document
```

---

#### **3. PRODUCT CATALOG** (Production Team)
```
GET    /api/v1/products/                       # List products
POST   /api/v1/products/                       # Create product
GET    /api/v1/products/{id}/                  # Get product details
PUT    /api/v1/products/{id}/                  # Update product
DELETE /api/v1/products/{id}/                  # Delete product

GET    /api/v1/storefront-products/            # List public products
GET    /api/v1/storefront-products/{id}/       # Get public product

GET    /api/v1/property-types/                 # List attribute types
POST   /api/v1/property-types/                 # Create property type

GET    /api/v1/property-values/                # List property values
POST   /api/v1/property-values/                # Create property value

GET    /api/v1/product-properties/             # List product properties
POST   /api/v1/product-properties/             # Assign property to product

GET    /api/v1/quantity-pricing/               # List quantity price tiers
POST   /api/v1/quantity-pricing/               # Create tier
PUT    /api/v1/quantity-pricing/{id}/          # Update tier

GET    /api/v1/turnaround-times/               # List delivery times
POST   /api/v1/turnaround-times/               # Create turnaround

GET    /api/v1/product-images/                 # List product images
POST   /api/v1/product-images/                 # Upload image

GET    /api/v1/product-seo/                    # Get SEO config
PUT    /api/v1/product-seo/{id}/               # Update SEO

GET    /api/v1/product-templates/              # List templates
POST   /api/v1/product-templates/              # Create template
```

---

#### **4. QUOTE MANAGEMENT** (Account Manager)
```
GET    /api/v1/quotes/                         # List quotes
POST   /api/v1/quotes/                         # Create quote
GET    /api/v1/quotes/{id}/                    # Get quote details
PUT    /api/v1/quotes/{id}/                    # Update quote
DELETE /api/v1/quotes/{id}/                    # Delete quote

POST   /api/v1/quotes/{id}/send/               # Send quote to client
POST   /api/v1/quotes/{id}/resend/             # Resend quote
POST   /api/v1/quotes/{id}/approve/            # Client approves quote
POST   /api/v1/quotes/{id}/reject/             # Client rejects quote
POST   /api/v1/quotes/{id}/convert_to_job/    # Convert to job (if approved)

GET    /api/v1/quote-line-items/               # List line items
POST   /api/v1/quote-line-items/               # Add line item
PUT    /api/v1/quote-line-items/{id}/          # Update line item
DELETE /api/v1/quote-line-items/{id}/          # Delete line item

GET    /api/v1/quote-attachments/              # List attachments
POST   /api/v1/quote-attachments/              # Upload attachment
DELETE /api/v1/quote-attachments/{id}/         # Delete attachment

POST   /api/v1/pricing/calculate/              # Calculate quote price
```

**Request Example (Create Quote):**
```json
{
  "client": 1,
  "product_name": "Business Cards",
  "quantity": 500,
  "unit_price": 2500.00,
  "channel": "Email",
  "notes": "Standard size, full color",
  "line_items": [
    {
      "product": 1,
      "quantity": 500,
      "unit_price": 2500.00,
      "properties": {"size": "A4", "color": "Full Color"}
    }
  ]
}
```

---

#### **5. JOB MANAGEMENT** (Production Team & Account Manager)
```
GET    /api/v1/jobs/                           # List jobs
POST   /api/v1/jobs/                           # Create job from quote
GET    /api/v1/jobs/{id}/                      # Get job details
PUT    /api/v1/jobs/{id}/                      # Update job
PATCH  /api/v1/jobs/{id}/                      # Partial update

POST   /api/v1/jobs/{id}/assign/               # Assign to PT member (AM action)
POST   /api/v1/jobs/{id}/send_to_vendor/      # Send to vendor (PT action)
POST   /api/v1/jobs/{id}/complete/             # Mark as complete

GET    /api/v1/job-vendor-stages/              # List vendor stages
POST   /api/v1/job-vendor-stages/              # Create stage

GET    /api/v1/job-notes/                      # List job notes
POST   /api/v1/job-notes/                      # Add note

GET    /api/v1/job-attachments/                # List job files
POST   /api/v1/job-attachments/                # Upload file

GET    /api/v1/timeline/                       # Get job timeline
```

**Request Example (Send to Vendor):**
```json
{
  "vendor_id": 2,
  "stage_name": "Printing",
  "expected_days": 3,
  "total_cost": 2500.00,
  "notes": "Rush job - customer needs by Friday"
}
```

---

#### **6. VENDOR MANAGEMENT** (Production Team)
```
GET    /api/v1/vendors/                        # List vendors
POST   /api/v1/vendors/                        # Create vendor
GET    /api/v1/vendors/{id}/                   # Get vendor profile
PUT    /api/v1/vendors/{id}/                   # Update vendor
DELETE /api/v1/vendors/{id}/                   # Deactivate vendor

GET    /api/v1/vendor-quotes/                  # List vendor quotes
POST   /api/v1/vendor-quotes/                  # Create vendor quote
```

---

#### **7. PROCESS & COSTING** (Production Team)
```
GET    /api/v1/processes/                      # List processes
POST   /api/v1/processes/                      # Create process
GET    /api/v1/processes/{id}/                 # Get process details
PUT    /api/v1/processes/{id}/                 # Update process

GET    /api/v1/process-tiers/                  # List price tiers
POST   /api/v1/process-tiers/                  # Create tier
PUT    /api/v1/process-tiers/{id}/             # Update tier

GET    /api/v1/process-variables/              # List variables
POST   /api/v1/process-variables/              # Create variable
PUT    /api/v1/process-variables/{id}/         # Update variable

GET    /api/v1/process-variable-ranges/        # List ranges
POST   /api/v1/process-variable-ranges/        # Create range

GET    /api/v1/process-vendors/                # List process vendors
POST   /api/v1/process-vendors/                # Assign vendor to process

GET    /api/v1/costing-engine/                 # Get cost estimate
POST   /api/v1/pricing/calculate/              # Calculate price
```

---

#### **8. PURCHASE ORDER** (Production Team & Vendor)
```
# Production Team Endpoints
GET    /api/v1/purchase-orders/                # List all POs
GET    /api/v1/purchase-orders/{id}/           # Get PO details
PUT    /api/v1/purchase-orders/{id}/           # Update PO
POST   /api/v1/purchase-orders/{id}/complete/  # Mark complete

# Vendor Endpoints
GET    /api/v1/purchase-orders/vendor_dashboard/  # Vendor dashboard
GET    /api/v1/purchase-orders/?vendor={id}   # Vendor's POs only
POST   /api/v1/purchase-orders/{id}/accept/    # Vendor accepts PO
POST   /api/v1/purchase-orders/{id}/decline/   # Vendor declines PO
POST   /api/v1/purchase-orders/{id}/update_milestone/  # Progress update

# Quality Proofs
GET    /api/v1/purchase-order-proofs/          # List proofs
POST   /api/v1/purchase-order-proofs/          # Vendor submits proof
POST   /api/v1/purchase-order-proofs/{id}/approve/  # PT approves proof

# Issues & Notes
GET    /api/v1/purchase-order-issues/          # List issues
POST   /api/v1/purchase-order-issues/          # Create issue

GET    /api/v1/purchase-order-notes/           # List notes
POST   /api/v1/purchase-order-notes/           # Add note

# Material Substitutions
GET    /api/v1/material-substitutions/         # List requests
POST   /api/v1/material-substitutions/         # Request substitution
```

---

#### **9. INVOICE & PAYMENT** (Production Team & Vendor)
```
# Vendor Invoices
GET    /api/v1/vendor-invoices/                # List invoices
POST   /api/v1/vendor-invoices/                # Vendor submits invoice
GET    /api/v1/vendor-invoices/{id}/           # Get invoice details
PUT    /api/v1/vendor-invoices/{id}/           # Update (by vendor)
POST   /api/v1/vendor-invoices/{id}/approve/   # PT approves invoice
POST   /api/v1/vendor-invoices/{id}/reject/    # PT rejects invoice

# Payments
GET    /api/v1/payments/                       # List payments
POST   /api/v1/payments/                       # Record payment
GET    /api/v1/payments/{id}/                  # Get payment details

# Refunds
POST   /api/v1/refunds/                        # Create refund request
GET    /api/v1/refunds/{id}/                   # Get refund status

# Credit Notes
POST   /api/v1/credit-notes/                   # Create credit note
GET    /api/v1/credit-notes/{id}/              # Get credit note

# Adjustments
POST   /api/v1/adjustments/                    # Record adjustment

# LPO (Local Purchase Order)
GET    /api/v1/lpos/                           # List LPOs
POST   /api/v1/lpos/                           # Create LPO
GET    /api/v1/lpos/{id}/                      # Get LPO details
POST   /api/v1/lpos/{id}/sync_quickbooks/      # Sync to QuickBooks

GET    /api/v1/lpo-line-items/                 # List line items
POST   /api/v1/lpo-line-items/                 # Add line item
```

---

#### **10. QUALITY CONTROL** (Production Team)
```
GET    /api/v1/qc-inspections/                 # List QC records
POST   /api/v1/qc-inspections/                 # Create QC inspection
GET    /api/v1/qc-inspections/{id}/            # Get inspection details
PUT    /api/v1/qc-inspections/{id}/            # Update inspection
POST   /api/v1/qc-inspections/{id}/approve/    # Approve inspection
POST   /api/v1/qc-inspections/{id}/reject/     # Reject inspection
```

---

#### **11. DELIVERY** (Production Team)
```
GET    /api/v1/deliveries/                     # List deliveries
POST   /api/v1/deliveries/                     # Create delivery
GET    /api/v1/deliveries/{id}/                # Get delivery details
PUT    /api/v1/deliveries/{id}/                # Update delivery
POST   /api/v1/deliveries/{id}/mark_delivered/ # Mark as delivered

GET    /api/v1/shipments/                      # List shipments
POST   /api/v1/shipments/                      # Create shipment
```

---

#### **12. CLIENT PORTAL** (Client Users)
```
GET    /api/v1/client-portal-users/            # List portal users
POST   /api/v1/client-portal-users/            # Invite user
GET    /api/v1/client-portal-users/{id}/       # Get user details
POST   /api/v1/client-portal-users/{id}/revoke_access/  # Revoke access

GET    /api/v1/client-orders/                  # List client orders
POST   /api/v1/client-orders/                  # Create order
GET    /api/v1/client-orders/{id}/             # Get order details

GET    /api/v1/client-invoices/                # List invoices
GET    /api/v1/client-invoices/{id}/           # Get invoice
GET    /api/v1/client-invoices/{id}/download/  # Download PDF

GET    /api/v1/client-payments/                # List payments
POST   /api/v1/client-payments/                # Record payment

GET    /api/v1/client-support-tickets/         # List tickets
POST   /api/v1/client-support-tickets/         # Create ticket
GET    /api/v1/client-support-tickets/{id}/    # Get ticket details
POST   /api/v1/client-support-tickets/{id}/reply/  # Reply to ticket

GET    /api/v1/client-documents/               # List documents
POST   /api/v1/client-documents/               # Upload document
DELETE /api/v1/client-documents/{id}/          # Delete document

GET    /api/v1/client-notifications/           # List notifications
```

---

#### **13. SYSTEM & CONFIGURATION** (Admin)
```
GET    /api/v1/users/                          # List users
POST   /api/v1/users/                          # Create user
GET    /api/v1/users/{id}/                     # Get user details
PUT    /api/v1/users/{id}/                     # Update user

GET    /api/v1/groups/                         # List groups
POST   /api/v1/groups/                         # Create group
PUT    /api/v1/groups/{id}/                    # Update group

GET    /api/v1/system-settings/                # List settings
POST   /api/v1/system-settings/                # Create setting
PUT    /api/v1/system-settings/{id}/           # Update setting

GET    /api/v1/system-alerts/                  # List alerts
POST   /api/v1/system-alerts/                  # Create alert

GET    /api/v1/notifications/                  # List notifications
POST   /api/v1/notifications/                  # Create notification

GET    /api/v1/activity-log/                   # View activity log
```

---

#### **14. ANALYTICS & REPORTING** (Production Team & Admin)
```
GET    /api/v1/dashboard/                      # Dashboard data
GET    /api/v1/analytics/                      # Analytics data
GET    /api/v1/production-analytics/           # PT-specific analytics
GET    /api/v1/search/                         # Global search
GET    /api/v1/workload/                       # Workload monitoring
GET    /api/v1/vendor-performance-metrics/     # Vendor metrics
GET    /api/v1/profitability-analysis/         # Profit analysis
```

---

#### **15. INTEGRATIONS** (Admin & Production Team)
```
GET    /api/v1/quickbooks/                     # QB sync status
POST   /api/v1/quickbooks/sync/                # Trigger QB sync

GET    /api/v1/webhook-subscriptions/          # List webhooks
POST   /api/v1/webhook-subscriptions/          # Create webhook
PUT    /api/v1/webhook-subscriptions/{id}/     # Update webhook
DELETE /api/v1/webhook-subscriptions/{id}/     # Delete webhook

GET    /api/v1/webhook-deliveries/             # Webhook delivery log
```

---

## 🔄 WORKFLOW FLOWS

### **FLOW 1: LEAD MANAGEMENT TO CLIENT CONVERSION**

```
┌─────────────────────────────────────────────────────────────┐
│  LEAD LIFECYCLE WORKFLOW                                    │
└─────────────────────────────────────────────────────────────┘

1. LEAD CREATION (Account Manager)
   ├─ POST /api/v1/leads/
   ├─ Status: "New"
   ├─ Creates Notification to AM
   └─ Logs ActivityLog entry

2. LEAD QUALIFICATION (Account Manager)
   ├─ POST /api/v1/leads/{id}/qualify/
   ├─ Status: "New" → "Qualified"
   ├─ Ready for quote creation
   ├─ Creates Notification
   └─ Logs ActivityLog entry

3. QUOTE CREATION (Account Manager)
   ├─ POST /api/v1/quotes/
   ├─ Select qualified lead (convert to client)
   ├─ Add quote line items with products
   ├─ System calculates pricing
   ├─ Status: "Draft"
   └─ Generate quote_id: QT-YYYY-XXX

4. SEND QUOTE TO CLIENT (Account Manager)
   ├─ POST /api/v1/quotes/{id}/send/
   ├─ Status: "Draft" → "Sent"
   ├─ Send email to client
   ├─ Create notification
   ├─ Set valid_until (3 days default)
   └─ Logs ActivityLog entry

5. CLIENT REVIEWS QUOTE (Client Portal User)
   ├─ Link in email → Client Portal
   ├─ Status: "Sent" → "Viewed"
   ├─ Notification to AM about view
   └─ 7-day countdown started

6. CLIENT APPROVES QUOTE (Client Portal User)
   ├─ POST /api/v1/quotes/{id}/approve/
   ├─ Status: "Viewed" → "Approved"
   ├─ Recorded approval_by, approval_date
   ├─ Notification to AM
   └─ Logs ActivityLog entry

7. CONVERT TO JOB (Account Manager)
   ├─ POST /api/v1/quotes/{id}/convert_to_job/
   ├─ Check if approved (precondition)
   ├─ Status: "Approved" → "Converted"
   ├─ Create Job from quote:
   │  ├─ job_number: JOB-YYYY-XXX
   │  ├─ Link to quote
   │  ├─ Link to client
   │  ├─ Copy product details
   │  └─ Status: "pending"
   ├─ Assign to PT member (optional)
   ├─ Lead marked as converted_to_client = true
   ├─ Create Client from Lead (if new)
   │  ├─ client_id: CL-YYYY-XXX
   │  ├─ Convert lead details
   │  ├─ Set account_manager
   │  └─ Status: "Active"
   ├─ Create Notification to PT
   └─ Logs ActivityLog entry

8. LEAD REJECTED (Client Portal User)
   ├─ POST /api/v1/quotes/{id}/reject/
   ├─ Status: "Viewed" → "Rejected"
   ├─ Notification to AM
   ├─ Lead remains in funnel
   ├─ Can resend quote or follow up
   └─ Logs ActivityLog entry

9. QUOTE EXPIRATION HANDLER (Automated)
   ├─ Check if valid_until < today
   ├─ Status: "Sent" or "Viewed" → "Expired"
   ├─ Notification to AM
   ├─ Option to resend quote
   └─ Logs ActivityLog entry
```

---

### **FLOW 2: JOB CREATION & VENDOR ASSIGNMENT**

```
┌─────────────────────────────────────────────────────────────┐
│  JOB LIFECYCLE & VENDOR WORKFLOW                            │
└─────────────────────────────────────────────────────────────┘

1. JOB CREATED FROM APPROVED QUOTE (Account Manager)
   ├─ POST /api/v1/quotes/{id}/convert_to_job/
   ├─ Creates Job record
   ├─ job_number: JOB-YYYY-XXX (auto-generated)
   ├─ Status: "pending"
   ├─ Status: "pending"
   ├─ Linked to approved quote
   ├─ Assigned to client from quote
   ├─ Product details copied from quote
   └─ Logs ActivityLog

2. ASSIGN JOB TO PT MEMBER (Account Manager)
   ├─ POST /api/v1/jobs/{id}/assign/
   ├─ Request: { "user_id": 5 }
   ├─ Validate user is in "Production Team" group
   ├─ Set person_in_charge = User(id=5)
   ├─ Create Notification to PT member
   ├─ Create ActivityLog
   └─ PT member can now manage job

3. PT RETRIEVES JOB DETAILS (Production Team)
   ├─ GET /api/v1/jobs/{id}/
   ├─ View full job specification
   ├─ View quote details
   ├─ View client information
   ├─ View file attachments
   ├─ View product specifications
   └─ Ready to assign to vendor(s)

4. PT SELECTS VENDOR (Production Team)
   ├─ GET /api/v1/vendors/
   ├─ List all active vendors
   ├─ Can filter by category, capability
   ├─ Can view vendor performance
   ├─ Can view VPS (Vendor Performance Score)
   └─ Select preferred vendor

5. PT SENDS JOB TO VENDOR (Production Team)
   ├─ POST /api/v1/jobs/{id}/send_to_vendor/
   ├─ Request body:
   │  ├─ vendor_id: 2
   │  ├─ stage_name: "Printing"
   │  ├─ expected_days: 3
   │  ├─ total_cost: 2500.00
   │  └─ notes: "Rush job"
   ├─ Backend creates:
   │  ├─ JobVendorStage record
   │  │  ├─ Links job to vendor
   │  │  ├─ Sets stage_name
   │  │  ├─ Calculates expected_completion
   │  │  ├─ Status: "sent_to_vendor"
   │  │  └─ stage_order auto-incremented
   │  │
   │  ├─ PurchaseOrder record
   │  │  ├─ po_number: PO-YYYY-XXXX
   │  │  ├─ Links job and vendor
   │  │  ├─ Status: "NEW"
   │  │  ├─ Sets estimated_cost
   │  │  ├─ vendor_accepted = false
   │  │  └─ Stores attachments
   │  │
   │  ├─ Copies job attachments to PO
   │  │
   │  └─ Updates Job.status: "pending" → "in_progress"
   │
   ├─ Sends notification to vendor (email/SMS/in-app)
   ├─ Creates ActivityLog
   └─ Response includes PO details

6. VENDOR RECEIVES PO (Vendor Portal)
   ├─ Email notification with job details
   ├─ Logs into vendor portal
   ├─ GET /api/v1/purchase-orders/vendor_dashboard/
   ├─ Views dashboard with new POs
   ├─ Status: "NEW"
   ├─ Can view:
   │  ├─ Job specifications
   │  ├─ Required documents
   │  ├─ Expected completion date
   │  ├─ Cost estimate
   │  └─ Customer contact if allowed
   └─ Decides to accept or decline

7a. VENDOR ACCEPTS PO (Vendor Portal - Option A)
    ├─ POST /api/v1/purchase-orders/{id}/accept/
    ├─ Request: { "vendor_accepted": true }
    ├─ Sets:
    │  ├─ PurchaseOrder.status: "ACCEPTED"
    │  ├─ PurchaseOrder.vendor_accepted: true
    │  ├─ PurchaseOrder.vendor_accepted_at: timestamp
    │  └─ JobVendorStage.status: "in_progress"
    ├─ Create Notification to PT: "Vendor accepted"
    ├─ Create ActivityLog
    └─ Vendor begins production work

7b. VENDOR DECLINES PO (Vendor Portal - Option B)
    ├─ POST /api/v1/purchase-orders/{id}/decline/
    ├─ Request: { "decline_reason": "Capacity unavailable" }
    ├─ Sets:
    │  ├─ PurchaseOrder.status: "DECLINED"
    │  ├─ JobVendorStage.status: "declined"
    │  └─ Stores decline_reason
    ├─ Create Notification to PT: "Vendor declined"
    ├─ Create ActivityLog
    ├─ PT must assign to different vendor
    └─ Returns to Step 4 (Select alternate vendor)

8. VENDOR PROVIDES PROGRESS UPDATES (Vendor Portal)
   ├─ POST /api/v1/purchase-orders/{id}/update_milestone/
   ├─ Request: { "milestone": "in_production", "notes": "50% complete" }
   ├─ Updates PurchaseOrder with milestone
   ├─ Create JobProgressUpdate record
   ├─ Create ActivityLog
   ├─ Notify PT of progress
   └─ Milestones: awaiting_materials, in_production, quality_checking, ready_for_shipment

9. VENDOR SUBMITS QUALITY PROOF (Vendor Portal)
   ├─ POST /api/v1/purchase-order-proofs/
   ├─ Request:
   │  ├─ purchase_order: 456
   │  ├─ proof_type: "sample" or "quality_check"
   │  ├─ file: [uploaded file]
   │  └─ description: "Quality sample for approval"
   ├─ Creates PurchaseOrderProof record
   ├─ Status: "pending"
   ├─ submitted_by: Vendor user
   ├─ submitted_at: timestamp
   ├─ Create Notification to PT
   └─ Create ActivityLog

10. PT REVIEWS QUALITY PROOF (Production Team)
    ├─ GET /api/v1/purchase-order-proofs/
    ├─ View pending proofs
    ├─ Download and review files
    ├─ Assess quality against specs
    └─ Either approve or request revisions

11a. PT APPROVES PROOF (Production Team - Option A)
     ├─ POST /api/v1/purchase-order-proofs/{id}/approve/
     ├─ Request: { "status": "approved", "notes": "Quality meets spec" }
     ├─ Sets:
     │  ├─ PurchaseOrderProof.status: "approved"
     │  ├─ PurchaseOrderProof.reviewed_by: PT user
     │  ├─ PurchaseOrderProof.approved_at: timestamp
     │  └─ PurchaseOrderProof.review_notes
     ├─ Create Notification to vendor: "Proof approved"
     ├─ Create ActivityLog
     ├─ Allow vendor to proceed to delivery/invoicing
     └─ Update JobVendorStage progress

11b. PT REJECTS PROOF (Production Team - Option B)
     ├─ POST /api/v1/purchase-order-proofs/
     ├─ [Vendor resubmits revised proof]
     ├─ Returns to Step 10
     └─ Loop until approved

12. PT MARKS JOB COMPLETE (Production Team)
    ├─ POST /api/v1/jobs/{id}/complete/
    ├─ Update Job.status: "in_progress" → "completed"
    ├─ Update JobVendorStage.status: "completed"
    ├─ Set JobVendorStage.actual_completion: timestamp
    ├─ Calculate job profitability
    ├─ Create Notification to client/AM
    ├─ Create ActivityLog
    └─ Trigger delivery/invoicing workflow
```

---

### **FLOW 3: INVOICE & PAYMENT WORKFLOW**

```
┌─────────────────────────────────────────────────────────────┐
│  VENDOR INVOICE & PAYMENT WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

1. VENDOR SUBMITS INVOICE (Vendor Portal)
   ├─ POST /api/v1/vendor-invoices/
   ├─ Request:
   │  ├─ purchase_order: 456
   │  ├─ invoice_date: "2026-01-25"
   │  ├─ invoice_amount: 2500.00
   │  ├─ tax_amount: 300.00
   │  ├─ total_amount: 2800.00
   │  ├─ payment_method: "bank_transfer"
   │  ├─ file: [invoice PDF]
   │  └─ notes: "Payment to ABC Bank"
   ├─ Creates VendorInvoice record
   ├─ invoice_number: INV-YYYY-XXXX (auto-generated)
   ├─ Status: "received" (from vendor)
   ├─ payment_status: "unpaid"
   ├─ submitted_by: Vendor user
   ├─ submitted_date: timestamp
   ├─ Create Notification to PT: "Invoice received"
   ├─ Create ActivityLog
   └─ Linked to PurchaseOrder

2. PT REVIEWS INVOICE (Production Team)
   ├─ GET /api/v1/vendor-invoices/
   ├─ View pending invoices
   ├─ Download invoice document
   ├─ Verify:
   │  ├─ Amount matches PO estimate
   │  ├─ Line items accurate
   │  ├─ Tax calculation correct
   │  └─ Payment terms compliant
   └─ Either approve or reject

3a. PT APPROVES INVOICE (Production Team - Option A)
    ├─ POST /api/v1/vendor-invoices/{id}/approve/
    ├─ Request: { "status": "approved", "notes": "Approved for payment" }
    ├─ Sets:
    │  ├─ VendorInvoice.status: "approved"
    │  ├─ VendorInvoice.reviewed_by: PT user
    │  ├─ VendorInvoice.reviewed_date: timestamp
    │  ├─ VendorInvoice.approval_notes
    │  └─ payment_status: "unpaid" (ready for payment)
    ├─ Check vendor approval thresholds
    ├─ Create Notification to finance
    ├─ Create ActivityLog
    └─ Ready for payment processing

3b. PT REJECTS INVOICE (Production Team - Option B)
    ├─ POST /api/v1/vendor-invoices/{id}/reject/
    ├─ Request: { "status": "rejected", "rejection_reason": "Amount mismatch" }
    ├─ Sets status: "rejected"
    ├─ Create Notification to vendor: "Invoice rejected"
    ├─ Vendor must resubmit corrected invoice
    ├─ Create ActivityLog
    └─ Returns to Step 1

4. PAYMENT APPROVAL & PROCESSING (Production Team/Finance)
   ├─ Review approval thresholds
   │  ├─ GET /api/v1/approval-thresholds/
   │  ├─ Check if amount requires higher approval
   │  ├─ Can approve if user's authority >= amount
   │  └─ Route to higher authority if needed
   ├─ No direct "approve payment" endpoint
   ├─ Payment initiated by AM/Vendor/Admin manually
   └─ Record payment in system

5. RECORD PAYMENT (Accounts/Finance)
   ├─ POST /api/v1/payments/
   ├─ Request:
   │  ├─ vendor: 2
   │  ├─ invoice: 789
   │  ├─ amount: 2800.00
   │  ├─ payment_date: "2026-01-30"
   │  ├─ payment_method: "bank_transfer"
   │  ├─ reference_number: "TRANSF-123456"
   │  └─ notes: "Payment via Equity Bank"
   ├─ Creates Payment record
   ├─ payment_number: auto-generated
   ├─ Sets recorded_by: User
   ├─ Sets payment_date
   ├─ Update VendorInvoice:
   │  ├─ payment_status: "unpaid" → "paid"
   │  └─ Link to Payment
   ├─ Update PurchaseOrder:
   │  └─ payment_status: "unpaid" → "paid"
   ├─ Create Notification to vendor: "Payment received"
   ├─ Create ActivityLog
   └─ Close out purchase order

6. REFUND REQUEST (Vendor or PT)
   ├─ POST /api/v1/refunds/
   ├─ Request:
   │  ├─ payment: 100
   │  ├─ amount: 500.00
   │  ├─ reason: "Overcharge on materials"
   │  └─ notes: "Quality issue adjustment"
   ├─ Creates Refund record
   ├─ refund_number: auto-generated
   ├─ Status: "pending"
   ├─ Requires PT approval/processing
   ├─ Create Notification to finance
   └─ Create ActivityLog

7. CREDIT NOTE (For partial issues)
   ├─ POST /api/v1/credit-notes/
   ├─ Request:
   │  ├─ vendor: 2
   │  ├─ invoice: 789
   │  ├─ amount: 200.00
   │  ├─ reason: "Damaged goods - 10% discount"
   │  └─ notes: "Item count discrepancy"
   ├─ Creates CreditNote record
   ├─ credit_note_number: auto-generated
   ├─ Status: "issued"
   ├─ Can be applied to future invoices
   └─ Create ActivityLog

8. QUICKBOOKS SYNC (Optional)
   ├─ POST /api/v1/lpos/{id}/sync_quickbooks/
   ├─ LPO record synced to QB
   ├─ Creates QB journal entry
   ├─ Tracks sync status
   └─ Two-way integration for accounting
```

---

### **FLOW 4: QUALITY CONTROL & DELIVERY**

```
┌─────────────────────────────────────────────────────────────┐
│  QC & DELIVERY WORKFLOW                                     │
└─────────────────────────────────────────────────────────────┘

1. PT INITIATES QC INSPECTION (Production Team)
   ├─ POST /api/v1/qc-inspections/
   ├─ Request:
   │  ├─ job: 100
   │  ├─ purchase_order: 456
   │  ├─ inspection_type: "final"
   │  └─ inspector_notes: "Standard quality check"
   ├─ Creates QCInspection record
   ├─ qc_inspection_id: auto-generated
   ├─ inspection_date: today
   ├─ inspector: Current PT user
   ├─ Status: "pending" (awaiting approval)
   ├─ Create Notification
   └─ Create ActivityLog

2. PT CONDUCTS INSPECTION (Production Team)
   ├─ GET /api/v1/qc-inspections/{id}/
   ├─ Review job specifications
   ├─ Physically inspect items
   ├─ Document findings:
   │  ├─ Color matching
   │  ├─ Dimension accuracy
   │  ├─ Quality of finish
   │  ├─ Packaging condition
   │  └─ Completeness
   ├─ Photograph items (if issues)
   └─ Record decisions

3a. QC PASSES (Production Team - Option A)
    ├─ PUT /api/v1/qc-inspections/{id}/
    ├─ Update findings: "All items meet specification"
    ├─ Status: "passed"
    ├─ Set approval_date: today
    ├─ approved_by: Current PT user
    ├─ approval_notes: "Quality approved for delivery"
    ├─ Create Notification to AM/client
    ├─ Create ActivityLog
    └─ Proceed to delivery

3b. QC FAILS (Production Team - Option B)
    ├─ PUT /api/v1/qc-inspections/{id}/
    ├─ Status: "failed"
    ├─ Document issues:
    │  ├─ issue_type (color, dimension, quality, packaging)
    │  ├─ severity (minor, major, critical)
    │  ├─ description
    │  └─ suggested_resolution
    ├─ Upload photo evidence
    ├─ Create Notification to vendor: "QC Failed - rework required"
    ├─ Create ActivityLog
    └─ Return to vendor or halt delivery

3c. QC CONDITIONAL PASS (Production Team - Option C)
    ├─ PUT /api/v1/qc-inspections/{id}/
    ├─ Status: "conditional_pass"
    ├─ Document minor issues acceptable to customer
    ├─ Get client approval for waiver
    ├─ approval_notes: "Client approved for 5% discount"
    ├─ Create Notification to client/vendor
    └─ Create ActivityLog

4. PT CREATES DELIVERY RECORD (Production Team)
   ├─ POST /api/v1/deliveries/
   ├─ Request:
   │  ├─ job: 100
   │  ├─ delivery_date: "2026-02-01"
   │  ├─ delivery_location: "Client warehouse"
   │  ├─ recipient: "John Smith"
   │  ├─ recipient_contact: "0701234567"
   │  ├─ delivery_method: "courier"
   │  └─ notes: "Fragile - handle with care"
   ├─ Creates Delivery record
   ├─ delivery_id: auto-generated
   ├─ Status: "pending"
   ├─ Link to QC inspection
   └─ Create ActivityLog

5. PT ARRANGES CARRIER (Production Team)
   ├─ Select delivery method:
   │  ├─ Pickup: Customer picks up
   │  ├─ Courier: Third-party carrier
   │  ├─ Company delivery: Internal fleet
   │  └─ Custom: Special arrangement
   ├─ Get carrier quote
   ├─ Record tracking number (if applicable)
   └─ Update delivery method

6. DELIVERY IN TRANSIT (Production Team/Carrier)
   ├─ PUT /api/v1/deliveries/{id}/
   ├─ Update status: "pending" → "in_transit"
   ├─ Record tracking number
   ├─ Set estimated_arrival
   ├─ Create Notification to client: "Your order is being delivered"
   ├─ Create Notification to AM
   └─ Create ActivityLog

7. DELIVERY COMPLETED (Production Team/Recipient)
   ├─ POST /api/v1/deliveries/{id}/mark_delivered/
   ├─ Request:
   │  ├─ status: "delivered"
   │  ├─ delivery_date: "2026-02-01"
   │  ├─ recipient_signature: "file_upload" (optional)
   │  ├─ delivery_photos: [file1, file2] (optional)
   │  ├─ notes: "Delivered in good condition"
   │  └─ actual_recipient: "Jane Smith"
   ├─ Update Delivery:
   │  ├─ Status: "in_transit" → "delivered"
   │  └─ actual_delivery: timestamp
   ├─ Update Job:
   │  ├─ Status: "in_progress" → "completed"
   │  └─ actual_delivery: timestamp
   ├─ Create Notification to client: "Your order has arrived!"
   ├─ Create Notification to AM
   ├─ Create ActivityLog
   └─ Send client satisfaction survey

8. DELIVERY DELAYED (If applicable)
   ├─ POST /api/v1/deliveries/{id}/
   ├─ Update status: "delayed"
   ├─ Update estimated_arrival
   ├─ Record delay reason
   ├─ Create Notification to AM/client
   ├─ Create SLAEscalation if critical
   └─ Create ActivityLog

9. SHIPMENT TRACKING (Optional for multi-item)
   ├─ POST /api/v1/shipments/
   ├─ Create Shipment for tracking subdivisions
   ├─ Link to Delivery
   ├─ Track individual shipment status
   ├─ Create Notification on shipment events
   └─ Create ActivityLog
```

---

## 🔐 AUTHENTICATION & SECURITY

### JWT Token Flow

```
1. USER LOGIN
   ├─ POST /api/token/
   ├─ Credentials: { "username": "user", "password": "pass" }
   └─ Response:
      {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
      }

2. API REQUEST WITH TOKEN
   ├─ Include header: Authorization: Bearer {access_token}
   ├─ DRF validates token
   ├─ Extract user info from JWT payload
   └─ Grant access if valid

3. TOKEN REFRESH
   ├─ Access token expires in 30 minutes
   ├─ POST /api/token/refresh/
   ├─ Provide refresh token
   └─ Receive new access token

4. TOKEN BLACKLIST
   ├─ POST /api/token/blacklist/
   ├─ Invalidate token (optional feature)
   └─ User logged out
```

### Permission Layers

```
1. AUTHENTICATION LAYER
   ├─ Token validity check
   ├─ Token expiration check
   └─ User must be authenticated

2. PERMISSION LAYER (Class-level)
   ├─ IsAdmin - User in Admin group
   ├─ IsAccountManager - User in Account Manager group
   ├─ IsProductionTeam - User in Production Team group
   ├─ IsClient - User has ClientPortalUser profile
   ├─ IsVendor - User linked to active Vendor
   └─ Combined permissions with | (OR) operator

3. OBJECT-LEVEL PERMISSIONS
   ├─ IsOwnerOrAdmin - User created object or is admin
   ├─ IsClientOwner - Client data belongs to user's client
   └─ Queryset filtering by user role

4. EXAMPLE PERMISSION CLASS
   ├─ Lead endpoints: IsAuthenticated, IsAccountManager | IsAdmin
   │  ├─ Only AM and Admin can access
   │  ├─ AM can only see leads they created
   │  └─ Admin can see all leads
   │
   ├─ Job endpoints: IsAuthenticated, IsProductionTeam | IsAdmin
   │  ├─ Only PT and Admin can access
   │  └─ They can view and manage jobs
   │
   ├─ Purchase Order endpoints (PT): IsAuthenticated, IsProductionTeam | IsAdmin
   │  ├─ Only PT and Admin can manage
   │  └─ Filter by job ownership
   │
   └─ Purchase Order endpoints (Vendor): IsAuthenticated, IsVendor
       ├─ Only active vendors can access
       └─ Filter by vendor_id ownership
```

### CORS Configuration

```
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://yourdomain.com"
]

CORS_ALLOW_CREDENTIALS = True
```

### Security Middleware

```
1. WhiteNoise - Static file serving with compression
2. CSRF Protection - Token-based CSRF validation
3. HTTPS/SSL - Enforced in production
4. Session Security - Secure, HTTPOnly cookies
5. Rate Limiting - DRF throttling (500 requests/hour per user)
6. Input Validation - Serializer validation on all inputs
7. SQL Injection Prevention - Django ORM parameterized queries
```

---

## 📊 DATA FLOW DIAGRAMS

### **High-Level Request Flow**

```
┌──────────────────┐
│  API Request     │
│  (with JWT)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Authentication   │
│ (Token valid?)   │
└────────┬─────────┘
         │ ✓
         ▼
┌──────────────────┐
│ Permission Check │
│ (User has role?) │
└────────┬─────────┘
         │ ✓
         ▼
┌──────────────────┐
│ Viewset          │
│ (HTTP method)    │
└─┬────────────┬───┘
  │            │
  ▼            ▼
 GET/LIST    POST/UPDATE/DELETE
  │            │
  ▼            ▼
Filter &    Serializer
Order       Validate
  │            │
  ▼            ▼
┌──────────────────┐
│ Database Query   │
│ (SELECT/INSERT) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Response         │
│ Serialization    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ API Response     │
│ (JSON + Status)  │
└──────────────────┘
```

### **Database Relationships (Simplified)**

```
                           ┌─────────────┐
                           │    User     │
                           │  (Django)   │
                           └──────┬──────┘
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
                  ▼               ▼               ▼
           ┌────────────┐  ┌────────────┐  ┌──────────────┐
           │ Lead       │  │ Client     │  │ ClientPortal │
           │            │  │            │  │ User         │
           └────┬───────┘  └────┬───────┘  └──────────────┘
                │                │
                │ converts to    │
                │                │
                └────────────┬───┘
                             │
                             ▼
                      ┌────────────┐
                      │ Quote      │
                      │ (product)  │
                      └────┬───────┘
                           │
                      approved
                           │
                           ▼
                      ┌────────────┐
                      │ Job        │
                      │            │
                      └────┬───────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │ JobVendorStage  │
                    │   & PurchaseOrder
                    └────────┬────────┘
                             │
                 ┌───────────┼───────────┐
                 │           │           │
                 ▼           ▼           ▼
            Vendor    QCInspection   Delivery
```

---

## 🔗 INTEGRATION POINTS

### **QuickBooks Integration**

```
FLOW:
LPO (Local Purchase Order) → QuickBooks Sync → QB Journal Entry

PROCESS:
1. PT creates LPO from approved quote
2. LPO is marked complete
3. PT initiates QB sync
4. System:
   ├─ Validates LPO data
   ├─ Formats as QB journal entry
   ├─ Authenticates with QB API
   ├─ Posts entry to QB
   ├─ Records QB ID in LPO
   └─ Marks synced_to_quickbooks = true

5. Two-way integration:
   ├─ PT system is source of truth
   ├─ QB is accounting system
   └─ Manual reconciliation monthly

ENDPOINTS:
├─ GET /api/v1/quickbooks/
├─ POST /api/v1/quickbooks/sync/
└─ POST /api/v1/lpos/{id}/sync_quickbooks/
```

### **Email Notification Integration**

```
TRIGGERS:
├─ Lead qualified
├─ Quote sent
├─ Quote approved
├─ Job assigned
├─ Job sent to vendor
├─ Vendor accepted PO
├─ Invoice received
├─ Invoice approved
├─ Payment recorded
├─ QC passed/failed
├─ Delivery in transit
├─ Delivery completed
└─ Support ticket reply

IMPLEMENTATION:
1. Event occurs in system
2. Event handler triggers
3. Create Notification record
4. Queue async email task (Celery)
5. Render email template
6. Send via SMTP
7. Record delivery status
```

### **SMS Notification Integration**

```
OPTIONAL:
├─ Vendor prefers SMS
├─ Client prefers SMS
└─ Urgent notifications

TRIGGERS:
├─ Job sent to vendor (SMS)
├─ Delivery in transit (SMS)
├─ Delivery ready for pickup (SMS)
└─ Critical issues (SMS)

IMPLEMENTATION:
1. Check user SMS preference
2. Format message
3. Send via SMS gateway (Twilio, Africastalking, etc.)
4. Record SMS delivery log
```

### **Webhook System**

```
SUBSCRIBE:
├─ POST /api/v1/webhook-subscriptions/
├─ Request: { "event_type": "job_completed", "webhook_url": "..." }
├─ Creates WebhookSubscription record
├─ is_active = true
└─ system_key generated for validation

TRIGGER:
1. Event occurs (e.g., job completed)
2. Find all active webhook subscriptions for event
3. Prepare payload
4. HTTP POST to subscriber URL
5. Record in WebhookDelivery table
6. Include: timestamp, status_code, response_time

SECURITY:
├─ HMAC signing on payload
├─ Webhook URL validation
├─ Retry on failure (exponential backoff)
└─ Delivery logging for debugging

EVENTS:
├─ job_created
├─ job_updated
├─ job_completed
├─ quote_approved
├─ purchase_order_accepted
├─ purchase_order_completed
├─ invoice_received
├─ payment_processed
├─ delivery_completed
└─ qc_inspection_completed
```

---

## ⚠️ ERROR HANDLING & NOTIFICATIONS

### **Error Response Format**

```json
{
  "detail": "Brief error message",
  "status": 400,
  "error_code": "INVALID_INPUT",
  "timestamp": "2026-01-25T10:30:00Z",
  "request_id": "abc-123-def"
}
```

### **HTTP Status Codes**

```
✓ 200 OK              - Request successful
✓ 201 Created         - Resource created
✓ 204 No Content      - Successful delete/update
✗ 400 Bad Request     - Invalid input/validation error
✗ 401 Unauthorized    - Missing/invalid authentication
✗ 403 Forbidden       - Insufficient permissions
✗ 404 Not Found       - Resource doesn't exist
✗ 409 Conflict        - State conflict (e.g., can't approve already approved)
✗ 422 Unprocessable   - Business logic validation failed
✗ 429 Too Many Req    - Rate limit exceeded
✗ 500 Server Error    - Unexpected error
```

### **Notification System**

```
NOTIFICATION TYPES:
├─ lead_qualified
├─ quote_approved
├─ quote_rejected
├─ job_assigned
├─ job_sent_to_vendor
├─ vendor_accepted_po
├─ vendor_declined_po
├─ qc_inspection_failed
├─ qc_inspection_passed
├─ invoice_received
├─ invoice_approved
├─ payment_received
├─ delivery_in_transit
├─ delivery_completed
├─ support_ticket_created
├─ support_ticket_replied
└─ system_alert

DELIVERY CHANNELS:
├─ In-App (database record)
├─ Email (SMTP)
├─ SMS (gateway)
└─ Web Push (optional)

NOTIFICATION RECORD:
├─ recipient (User)
├─ notification_type (string)
├─ title, message, link
├─ is_read (boolean)
└─ created_at

RETRIEVAL:
├─ GET /api/v1/notifications/
├─ Mark as read on view
└─ Delete old notifications
```

### **Activity Logging**

```
LOG RECORD:
├─ activity_type (Job, Quote, Invoice, etc.)
├─ title
├─ description
├─ client (ForeignKey, nullable)
├─ created_by (User)
└─ created_at

EVENTS LOGGED:
├─ Quote created/updated/approved
├─ Job created/assigned/completed
├─ Vendor assigned/declined
├─ Invoice received/approved/rejected
├─ Payment processed
├─ QC inspection completed
├─ Delivery tracked
└─ User actions (create, update, delete)

RETENTION:
├─ Keep all records
├─ Archive after 2 years
└─ Searchable for audits

RETRIEVAL:
├─ GET /api/v1/activity-log/
├─ Filter by client/date/type
└─ Export to CSV for reporting
```

---

## 🎯 KEY BUSINESS LOGIC RULES

### **Quote Validation**

```
Rule: Quotes valid for 3 days
├─ valid_until = created_at + 3 days
├─ Expired quotes cannot be approved
└─ Send reminder email at day 2

Rule: Client must approve before job creation
├─ Status must be "Approved"
├─ approved_by must be set
└─ rejected quotes stay in funnel

Rule: Markup automatically applied
├─ Calculate unit_price × markup_percentage
├─ Total = Sum(line_items)
└─ Client sees final price
```

### **Job Status Transitions**

```
pending → in_progress → completed
   ↑           ↑
   └─────────hold
        ↓
      cancelled

Rules:
├─ Can only assign vendors to in_progress jobs
├─ Cannot revert from completed
├─ Hold requires notes
└─ Cancelled requires approval
```

### **Purchase Order Status Transitions**

```
NEW → ACCEPTED → IN_PROGRESS → COMPLETED
  └→ DECLINED

Rules:
├─ Vendor must accept before work starts
├─ Can't complete without QC approval
├─ Declined POs need reassignment
└─ Payment blocks final completion
```

### **Invoice Approval Authority**

```
Thresholds:
├─ User 1: Can approve up to 50,000 KES
├─ User 2: Can approve up to 200,000 KES
├─ Admin: No limit

Process:
├─ Check invoice amount
├─ Get user's approval threshold
├─ If amount > threshold:
│  ├─ Route to higher authority
│  └─ Email notification for approval
├─ If amount ≤ threshold:
│  ├─ User can approve directly
│  └─ Proceed to payment
└─ Create ApprovalThreshold record for audit
```

### **Vendor Performance Scoring (VPS)**

```
METRICS:
├─ On-time delivery rate (40%)
├─ Quality score from QC (30%)
├─ Response time average (20%)
├─ Invoice accuracy (10%)

CALCULATION:
├─ Monthly average from jobs
├─ Updated after each job completion
├─ Used for vendor ranking
└─ Displayed in vendor dashboard

USAGE:
├─ PT prefers high VPS vendors
├─ Auto-filter low VPS vendors
└─ Alert if VPS drops below threshold
```

### **Pricing Engine**

```
TWO PRICING METHODS:

1. TIER-BASED (Simple)
   ├─ Define quantity ranges
   ├─ Assign price per tier
   ├─ Customer selects quantity
   ├─ System applies matching tier price
   └─ Works for: Business Cards, Flyers, etc.

2. FORMULA-BASED (Complex)
   ├─ Define variables:
   │  ├─ Thread color (stitches)
   │  ├─ Material type
   │  ├─ Embroidery complexity
   │  └─ Custom parameters
   ├─ Calculate cost = base + (var1 * rate1) + (var2 * rate2)
   ├─ Markup applied = cost × (1 + markup%)
   └─ Works for: Customizable apparel, embroidery, etc.

CALCULATION:
├─ AM creates quote
├─ System calculates unit price
├─ Multiplies by quantity
├─ Applies default markup
├─ Shows to customer
└─ PT can adjust before acceptance
```

---

## 🚀 DEPLOYMENT & OPERATIONS

### **Environment Variables**

```
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/printshop

# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# JWT
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# QuickBooks (if using)
QB_CLIENT_ID=your-qb-client-id
QB_CLIENT_SECRET=your-qb-secret
QB_REDIRECT_URI=https://yourdomain.com/auth/callback
QB_ENVIRONMENT=sandbox

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# AWS/Storage (if using S3)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
```

### **Database Migrations**

```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### **Static Files**

```bash
# Collect static files
python manage.py collectstatic --noinput

# Served by WhiteNoise in production
# Gzipped for faster delivery
```

### **Running the Server**

```bash
# Development
python manage.py runserver 0.0.0.0:8000

# Production (Gunicorn)
gunicorn client.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Procfile for Heroku/Render
web: gunicorn client.wsgi:application
```

---

## 📚 APPENDIX: API DOCUMENTATION

### **Swagger/OpenAPI Documentation**

```
URL: http://localhost:8000/api/docs/
Alternative: http://localhost:8000/api/docs/swagger/
ReDoc: http://localhost:8000/api/docs/redoc/

Generated from:
├─ api_views.py viewsets
├─ api_serializers.py fields
├─ @method_decorator(swagger_auto_schema) annotations
└─ Docstrings in viewset classes
```

### **Testing the API**

```bash
# Using cURL
curl -X POST http://localhost:8000/api/v1/leads/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com", "phone": "0701234567"}'

# Using Postman
# Import OpenAPI schema from /api/schema/
# Add Bearer token in Authorization tab
# Set request body as JSON

# Using Python requests
import requests

headers = {"Authorization": f"Bearer {token}"}
data = {"name": "John", "email": "john@example.com"}
response = requests.post("http://localhost:8000/api/v1/leads/", headers=headers, json=data)
print(response.json())
```

---

## 📞 SUPPORT & TROUBLESHOOTING

### **Common Issues**

```
1. 401 Unauthorized
   └─ Token missing or expired
   └─ Solution: Get new token via /api/token/

2. 403 Forbidden
   └─ User doesn't have required group
   └─ Solution: Admin add user to group

3. 404 Not Found
   └─ Resource doesn't exist
   └─ Solution: Verify ID exists

4. 422 Unprocessable Entity
   └─ Business logic validation failed
   └─ Solution: Check error message, update request

5. 429 Too Many Requests
   └─ Rate limit exceeded
   └─ Solution: Wait 1 hour or upgrade tier
```

---

**Document Version:** 1.0  
**Last Updated:** January 25, 2026  
**Next Review:** Q2 2026

