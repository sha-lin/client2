# PrintShop System Implementation Status

## Overview
This document tracks the implementation progress for removing the Finance group and integrating QuickBooks for invoicing.

## ✅ Completed Changes

### Phase 1: Remove Finance Group References

#### 1.1 Updated Views ✅
- **File**: `clientapp/views.py`
  - ✅ Removed Finance group redirect from `dashboard()` function (line 160-162)
  - Finance users will now use the same dashboard as other users

#### 1.2 Updated QuickBooks Integration ✅
- **File**: `quickbooks_integration/views.py`
  - ✅ Changed `@group_required('Finance')` to `@group_required('Production Team')` for:
    - `accounting_dashboard()` - Production Team can access QuickBooks dashboard
    - `get_invoices()` - Production Team can view invoices
    - `get_customers()` - Production Team can view customers
    - `get_balance_sheet()` - Production Team can view balance sheet

## 📋 Current System State

### What's Working
1. **QuickBooks Integration**:
   - Connection to QuickBooks (OAuth flow)
   - Token storage and refresh
   - Invoice creation service (`QuickBooksService.create_invoice_from_quote()`)
   - Customer management (find or create)
   - Item management (find or create)

2. **LPO Model**:
   - LPO auto-generation on quote approval
   - LPO status tracking
   - QuickBooks sync fields (invoice_id, invoice_number, synced status)
   - `sync_to_quickbooks()` method on LPO model

3. **Quote Approval Flow**:
   - Quote sending via email/WhatsApp
   - Quote approval tokens
   - Public approval page
   - Quote approval service

4. **Production Team**:
   - Job management
   - Production updates
   - Product catalog

## 🔧 What Needs to Be Implemented

### Phase 2: Complete Quote → LPO Flow

#### 2.1 Update Quote Approval Service
**File**: `clientapp/quote_approval_services.py`

**Current Status**: Need to verify LPO creation is working

**Required Actions**:
1. Check if `QuoteApprovalService.approve_quote()` creates LPO
2. Ensure LPO line items are created from quote items
3. Verify Job is created automatically
4. Confirm notifications are sent to Production Team

**Code to Add/Verify**:
```python
# In QuoteApprovalService.approve_quote()
# After quote approval:

# 1. Create LPO
from clientapp.models import LPO, LPOLineItem

lpo = LPO.objects.create(
    quote=quote,
    client=quote.client,
    status='approved',
    subtotal=subtotal,
    vat_amount=vat_amount,
    total_amount=total,
    payment_terms=quote.payment_terms,
    notes=quote.notes,
    created_by=quote.created_by
)

# 2. Create LPO line items
for item in quote_items:
    LPOLineItem.objects.create(
        lpo=lpo,
        product_name=item.product_name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        line_total=item.unit_price * item.quantity
    )

# 3. Create Job
job = Job.objects.create(
    client=quote.client,
    quote=quote,
    job_name=f"Job for {quote.product_name}",
    job_type='printing',
    product=quote.product_name,
    quantity=quote.quantity,
    person_in_charge='Production Team',
    status='pending',
    expected_completion=quote.valid_until,
    created_by=quote.created_by
)

# 4. Notify Production Team
# Get all production team users
from django.contrib.auth.models import Group
production_group = Group.objects.get(name='Production Team')
for user in production_group.user_set.all():
    Notification.objects.create(
        recipient=user,
        title=f'New Order - LPO {lpo.lpo_number}',
        message=f'Quote {quote.quote_id} approved. LPO generated for {quote.client.name}',
        link=reverse('lpo_detail', kwargs={'lpo_number': lpo.lpo_number})
    )
```

### Phase 3: Production Team LPO Management

#### 3.1 Create LPO List View ✅ (Already exists)
**File**: `clientapp/views.py`

**Status**: View function exists (`lpo_detail`), but need to add list view

**Required**: Add `lpo_list` view function:
```python
@login_required
@group_required('Production Team')
def lpo_list(request):
    """List all LPOs for production team"""
    from clientapp.models import LPO
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    sync_filter = request.GET.get('sync', 'all')
    
    lpos = LPO.objects.select_related('client', 'quote').order_by('-created_at')
    
    # Apply filters
    if status_filter != 'all':
        lpos = lpos.filter(status=status_filter)
    
    if sync_filter == 'synced':
        lpos = lpos.filter(synced_to_quickbooks=True)
    elif sync_filter == 'not_synced':
        lpos = lpos.filter(synced_to_quickbooks=False)
    
    # Count by status
    status_counts = {
        'pending': LPO.objects.filter(status='pending').count(),
        'approved': LPO.objects.filter(status='approved').count(),
        'in_production': LPO.objects.filter(status='in_production').count(),
        'completed': LPO.objects.filter(status='completed').count(),
        'synced': LPO.objects.filter(synced_to_quickbooks=True).count(),
        'not_synced': LPO.objects.filter(synced_to_quickbooks=False, status='completed').count(),
    }
    
    context = {
        'current_view': 'lpo_list',
        'lpos': lpos,
        'status_filter': status_filter,
        'sync_filter': sync_filter,
        'status_counts': status_counts,
    }
    
    return render(request, 'lpo_list.html', context)
```

#### 3.2 Create LPO List Template
**File**: `clientapp/templates/lpo_list.html`

**Status**: ❌ Needs to be created

**Required**: Create template with:
- Table showing all LPOs
- Columns: LPO#, Client, Quote#, Amount, Status, QB Sync Status, Actions
- Filter by status and sync status
- "Sync to QuickBooks" button for completed, not-synced LPOs
- Link to LPO detail page

#### 3.3 Update URLs
**File**: `clientapp/urls.py`

**Required**: Add URL pattern:
```python
path('lpo/', views.lpo_list, name='lpo_list'),
```

#### 3.4 Update Navigation
**Files**: 
- `clientapp/templates/production2_dashboard.html` (or base template for Production)

**Required**: Add "LPOs" link to sidebar navigation

### Phase 4: Testing & Validation

#### 4.1 Test Complete Flow
1. ✅ Create quote for lead
2. ✅ Send quote to lead
3. ❓ Approve quote (verify LPO created)
4. ❓ Verify lead converted to client
5. ❓ Verify Job created
6. ❓ View LPO in production portal
7. ❓ Mark job as completed
8. ❓ Click "Sync to QuickBooks"
9. ❓ Verify invoice created in QuickBooks
10. ❓ Verify invoice ID stored in LPO

#### 4.2 QuickBooks Connection
**Status**: ❓ Needs testing

**Steps**:
1. Set up QuickBooks sandbox account
2. Configure `.env` with QuickBooks credentials:
   ```
   QB_CLIENT_ID=your_client_id
   QB_CLIENT_SECRET=your_client_secret
   QB_REDIRECT_URI=http://localhost:8000/quickbooks/callback/
   QB_ENVIRONMENT=sandbox
   ```
3. Connect to QuickBooks via `/quickbooks/connect/`
4. Test invoice creation

### Phase 5: Database Cleanup

#### 5.1 Remove Finance Group
**Status**: ❌ Not done

**Required**: Create Django management command or migration:
```python
# In a migration or management command
from django.contrib.auth.models import Group

# Remove Finance group
try:
    finance_group = Group.objects.get(name='Finance')
    # Optionally reassign users to other groups
    for user in finance_group.user_set.all():
        # Decide which group to assign them to
        production_group = Group.objects.get(name='Production Team')
        user.groups.add(production_group)
    finance_group.delete()
except Group.DoesNotExist:
    pass
```

## 📝 Next Steps (Priority Order)

1. **HIGH PRIORITY**: Verify Quote Approval → LPO Flow
   - Check `clientapp/quote_approval_services.py`
   - Ensure LPO is created when quote is approved
   - Test with a sample quote

2. **HIGH PRIORITY**: Create LPO List View
   - Add `lpo_list` view function to `views.py`
   - Create `lpo_list.html` template
   - Add URL pattern
   - Update navigation

3. **MEDIUM PRIORITY**: Test QuickBooks Integration
   - Set up QuickBooks sandbox
   - Configure credentials
   - Test connection
   - Test invoice creation

4. **MEDIUM PRIORITY**: Update LPO Detail Template
   - Ensure "Sync to QuickBooks" button is visible
   - Show QuickBooks invoice details if synced
   - Add proper error handling

5. **LOW PRIORITY**: Remove Finance Group
   - Create migration
   - Reassign users
   - Delete group

6. **LOW PRIORITY**: Update Documentation
   - User guide for Production Team
   - QuickBooks setup guide
   - Troubleshooting guide

## 🔍 Files to Review

### Critical Files
1. `clientapp/quote_approval_services.py` - Quote approval logic
2. `clientapp/quickbooks_services.py` - QuickBooks API integration
3. `clientapp/models.py` - LPO model and sync method
4. `clientapp/views.py` - View functions
5. `clientapp/urls.py` - URL patterns

### Templates to Check/Create
1. `clientapp/templates/lpo_list.html` - ❌ CREATE
2. `clientapp/templates/lpo_detail.html` - ✅ EXISTS (verify sync button)
3. `clientapp/templates/quote_approved.html` - ✅ EXISTS
4. `clientapp/templates/production2_dashboard.html` - UPDATE (add LPO link)

## 💡 Important Notes

1. **No UI Changes**: As requested, no changes to existing UI designs. Only adding new functionality.

2. **QuickBooks Data Mapping**: Only relevant data is sent to QuickBooks:
   - Customer info (name, email, phone, address)
   - Line items (product name, quantity, unit price)
   - Payment terms
   - Due date
   - VAT/Tax (if applicable)

3. **Lead to Client Conversion**: Happens automatically when lead approves quote.

4. **Notifications**: System sends notifications to:
   - Production Team when LPO is created
   - Account Manager when job is completed
   - Account Manager when invoice is synced

5. **Permissions**:
   - Account Manager: Create quotes, send quotes, view LPOs
   - Production Team: View LPOs, manage jobs, sync to QuickBooks
   - No Finance group needed

## 🚀 Ready to Deploy

### What's Ready
- ✅ Finance group removed from views
- ✅ QuickBooks integration permissions updated
- ✅ LPO model with sync functionality
- ✅ Quote approval flow
- ✅ Job management

### What's Not Ready
- ❌ LPO list view and template
- ❌ Quote approval → LPO creation (needs verification)
- ❌ QuickBooks connection testing
- ❌ Finance group removal from database
- ❌ Navigation updates

## 📞 Support

If you encounter issues:
1. Check Django logs for errors
2. Verify QuickBooks credentials in `.env`
3. Ensure all migrations are run: `python manage.py migrate`
4. Check that user groups are set up correctly
5. Test with QuickBooks sandbox before production

---

**Last Updated**: 2025-11-19
**Status**: Phase 1 Complete, Phase 2-5 In Progress
