---
description: Complete System Implementation Plan - Remove Finance Group & Implement QuickBooks Integration
---

# PrintShop System Implementation Plan

## Overview
Transform the system to remove Finance group and integrate QuickBooks for invoicing, with seamless flow from quote approval to invoice generation.

## Phase 1: Remove Finance Group References

### 1.1 Update Views
- Remove Finance group checks in `views.py`:
  - Line 161: Remove Finance redirect in dashboard
  - Line 1779: Remove Finance check in login_redirect
- Remove Finance-specific views in `quickbooks_integration/views.py`:
  - Remove `@group_required('Finance')` decorators
  - Update to use Production Team or Account Manager groups

### 1.2 Update URL Patterns
- Remove Finance-related URL comments in `clientapp/urls.py`
- Keep QuickBooks integration URLs but update permissions

### 1.3 Database Cleanup
- Create migration to remove Finance group from database
- Reassign any Finance users to appropriate groups

## Phase 2: Implement Quote Approval → LPO Flow

### 2.1 Update Quote Approval Service
File: `clientapp/quote_approval_services.py`
- Ensure LPO is auto-created when quote is approved
- Create LPO line items from quote items
- Set LPO status to 'approved'
- Create Job automatically
- Notify production team

### 2.2 Update Quote Model
File: `clientapp/models.py`
- Ensure Quote.save() triggers LPO creation on approval
- Add signal to create LPO when status changes to 'Approved'

### 2.3 Lead to Client Conversion
- When quote is approved by lead:
  - Auto-convert lead to client
  - Transfer quote to new client
  - Create LPO with client reference
  - Update all relationships

## Phase 3: Production Team LPO Management

### 3.1 Create LPO List View
- Add new view: `lpo_list` for Production Team
- Show all LPOs with status
- Filter by: pending, in_production, completed
- Show sync status (synced/not synced to QuickBooks)

### 3.2 Create LPO List Template
File: `clientapp/templates/lpo_list.html`
- Table showing: LPO#, Client, Quote#, Amount, Status, QB Sync Status
- "Sync to QuickBooks" button (only for completed, not-synced LPOs)
- Link to LPO detail page

### 3.3 Update Navigation
- Add "LPOs" tab to Production Team sidebar
- Update base template for Production Team

### 3.4 Update LPO Detail Template
File: `clientapp/templates/lpo_detail.html`
- Show complete LPO information
- Show related quote and job
- "Sync to QuickBooks" button (conditional)
- Show QuickBooks invoice details if synced

## Phase 4: QuickBooks Integration Enhancement

### 4.1 Update QuickBooks Service
File: `clientapp/quickbooks_services.py`
- Ensure `create_invoice_from_quote` works correctly
- Handle multi-line quotes properly
- Map only relevant data for invoicing:
  - Customer info
  - Line items (product, quantity, unit price)
  - Payment terms
  - Due date
  - VAT/Tax if applicable

### 4.2 Update LPO Sync Method
File: `clientapp/models.py` - LPO.sync_to_quickbooks()
- Validate LPO is completed
- Call QuickBooks service
- Store invoice ID and number
- Mark as synced with timestamp
- Create notification for AM
- Create activity log

### 4.3 Update Sync View
File: `clientapp/views.py` - sync_to_quickbooks()
- Allow both Production Team and Account Manager
- Add proper error handling
- Return JSON response for AJAX
- Show success/error messages

## Phase 5: Dashboard & Analytics Updates

### 5.1 Account Manager Dashboard
- Show pending quotes
- Show approved quotes (LPOs generated)
- Show quotes sent to clients
- Revenue metrics from approved quotes

### 5.2 Production Team Dashboard
- Show pending LPOs
- Show LPOs in production
- Show completed LPOs (ready for QB sync)
- Show synced LPOs
- Recent production updates

### 5.3 Live Data Updates
- Ensure `get_dashboard_data` API works
- Update dashboards to poll for live data
- Show real-time notifications

## Phase 6: Workflow Automation

### 6.1 Quote Approval Workflow
1. AM creates quote for client/lead
2. AM sends quote via email/WhatsApp
3. Client/lead receives approval link
4. Client/lead clicks "Approve"
5. System:
   - Updates quote status to 'Approved'
   - If lead: converts to client
   - Creates LPO automatically
   - Creates Job automatically
   - Notifies Production Team
   - Notifies Account Manager

### 6.2 Production Workflow
1. Production Team sees new LPO in "LPO" tab
2. Production Team works on order
3. Production Team updates job status
4. When complete:
   - Mark job as 'completed'
   - Mark LPO as 'completed'
   - "Sync to QuickBooks" button appears
5. Click "Sync to QuickBooks":
   - Creates invoice in QuickBooks
   - Stores invoice ID
   - Marks LPO as synced
   - Notifies AM

### 6.3 QuickBooks Sync Workflow
1. Check LPO is completed
2. Check not already synced
3. Get quote data
4. Create/find customer in QuickBooks
5. Create/find items in QuickBooks
6. Create invoice with line items
7. Store invoice reference
8. Update LPO sync status
9. Create activity log
10. Send notifications

## Phase 7: Testing & Validation

### 7.1 Test Quote to LPO Flow
- Create quote for lead
- Send to lead
- Approve quote
- Verify lead converted to client
- Verify LPO created
- Verify job created
- Verify notifications sent

### 7.2 Test Production Flow
- View LPO in production portal
- Update job status
- Mark as completed
- Verify LPO status updated
- Verify sync button appears

### 7.3 Test QuickBooks Sync
- Connect to QuickBooks (sandbox)
- Complete a job
- Click "Sync to QuickBooks"
- Verify invoice created in QuickBooks
- Verify invoice ID stored
- Verify LPO marked as synced

### 7.4 Test Permissions
- Verify Finance group removed
- Verify AM can create quotes
- Verify Production can manage LPOs
- Verify Production can sync to QuickBooks
- Verify proper redirects

## Phase 8: UI/UX Enhancements

### 8.1 Status Badges
- Add color-coded status badges
- Quote status: Draft, Sent, Approved, Lost
- LPO status: Pending, In Production, Completed
- Sync status: Not Synced, Synced

### 8.2 Action Buttons
- "Send to Client" (AM)
- "Approve Quote" (Client)
- "Mark Complete" (Production)
- "Sync to QuickBooks" (Production)

### 8.3 Notifications
- Real-time notification bell
- Toast notifications for actions
- Email notifications for approvals

## Implementation Order

1. **First**: Remove Finance group references (Phase 1)
2. **Second**: Fix Quote Approval → LPO flow (Phase 2)
3. **Third**: Create LPO management for Production (Phase 3)
4. **Fourth**: Enhance QuickBooks integration (Phase 4)
5. **Fifth**: Update dashboards (Phase 5)
6. **Sixth**: Test complete workflow (Phase 7)
7. **Seventh**: UI/UX polish (Phase 8)

## Files to Modify

### Models
- `clientapp/models.py` - Update LPO, Quote models

### Views
- `clientapp/views.py` - Remove Finance checks, add LPO list view
- `quickbooks_integration/views.py` - Update permissions

### URLs
- `clientapp/urls.py` - Add LPO list URL, remove Finance comments
- `quickbooks_integration/urls.py` - Update if needed

### Templates
- `clientapp/templates/lpo_list.html` - NEW
- `clientapp/templates/lpo_detail.html` - UPDATE
- `clientapp/templates/base.html` - Update AM navigation
- `clientapp/templates/production2_dashboard.html` - Update Production navigation
- `clientapp/templates/dashboard.html` - Remove Finance redirect

### Services
- `clientapp/quickbooks_services.py` - Enhance invoice creation
- `clientapp/quote_approval_services.py` - Ensure LPO creation

### Migrations
- Create migration to remove Finance group
- Create migration for any model changes

## Environment Setup

### QuickBooks Credentials
Ensure `.env` has:
```
QB_CLIENT_ID=your_client_id
QB_CLIENT_SECRET=your_client_secret
QB_REDIRECT_URI=http://localhost:8000/quickbooks/callback/
QB_ENVIRONMENT=sandbox
```

### Email Setup
Ensure email settings configured for quote sending:
```
EMAIL_HOST_USER=your_email
EMAIL_APP_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=PrintDuka <noreply@printduka.com>
```

## Success Criteria

✅ Finance group completely removed
✅ Quote approval auto-creates LPO
✅ Lead auto-converts to client on approval
✅ Production Team has LPO management tab
✅ LPO can be synced to QuickBooks
✅ Invoice created in QuickBooks with correct data
✅ All dashboards show live data
✅ Notifications work properly
✅ No UI changes to existing portals (only additions)
✅ Complete workflow tested end-to-end
