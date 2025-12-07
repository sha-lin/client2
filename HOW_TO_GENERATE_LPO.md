# How to Generate an LPO (Local Purchase Order)

## 📋 Current Implementation

Based on the codebase analysis, here's how LPO generation **SHOULD** work in your system:

---

## ✅ AUTOMATIC LPO GENERATION (Designed Flow)

### The Automatic Process:

```
1. Create Quote (Account Manager)
   ↓
2. Send Quote to Client (Email/WhatsApp)
   ↓
3. Client Clicks Approval Link
   ↓
4. **LPO AUTO-GENERATED** ← This happens automatically
   ↓
5. View LPO in system
```

### How It Works:

When a client approves a quote via the approval link, the system **automatically**:

1. ✅ Approves the quote
2. ✅ Generates LPO with unique number (LPO-2025-XXX)
3. ✅ Creates line items from quote
4. ✅ Calculates totals (subtotal, VAT, total)
5. ✅ Creates a production Job
6. ✅ Sends notifications to production team
7. ✅ Converts Lead to Client (if quote was for a lead)

**Code Location:** `quote_approval_services.py` - Line 267-303

```python
@staticmethod
def generate_lpo(quote):
    """Generate LPO from approved quote"""
    # Calculates totals
    # Creates LPO record
    # Creates LPO line items
    return lpo
```

---

## ❌ PROBLEM: The Approval System Isn't Connected!

### What's Missing:

The LPO generation code **exists and works**, but the quote approval workflow is **NOT IMPLEMENTED** in views:

1. ❌ **No `send_quote` view** - Account managers can't send quotes to clients
2. ❌ **No `quote_approval` view** - Clients can't approve via link
3. ❌ **No manual LPO creation** - No UI for manual LPO creation

**Result:** You can't actually trigger LPO generation because quotes can't be approved!

---

## 🔧 CURRENT WORKAROUND (What You CAN Do Now)

### Option 1: Django Admin Panel

You can manually create LPOs through Django admin:

1. Go to: `http://your-site/admin/`
2. Navigate to: **clientapp > LPOs**
3. Click: **Add LPO**
4. Fill in:
   - Client
   - Quote (select from dropdown)
   - Status: "approved"
   - Subtotal, VAT, Total
   - Payment terms
5. Save

Then manually create LPO line items for that LPO.

---

### Option 2: Django Shell (For Testing)

```python
python manage.py shell

from clientapp.models import Quote, LPO, LPOLineItem
from clientapp.quote_approval_services import QuoteApprovalService

# Get an approved quote
quote = Quote.objects.get(quote_id='QT-2025-001')

# Change status to approved
quote.status = 'Approved'
quote.save()

# Generate LPO using the service
lpo = QuoteApprovalService.generate_lpo(quote)

print(f"LPO created: {lpo.lpo_number}")
```

---

### Option 3: Create a Simple LPO Creation View (Quick Fix)

Add this to your `views.py`:

```python
@login_required
def create_lpo_from_quote(request, quote_id):
    """Manually create LPO from approved quote"""
    quote = get_object_or_404(Quote, quote_id=quote_id)
    
    # Check if quote is approved
    if quote.status != 'Approved':
        messages.error(request, "Only approved quotes can generate LPOs")
        return redirect('quote_detail', quote_id=quote_id)
    
    # Check if LPO already exists
    if hasattr(quote, 'lpo'):
        messages.warning(request, "LPO already exists for this quote")
        return redirect('lpo_detail', lpo_number=quote.lpo.lpo_number)
    
    # Generate LPO
    from clientapp.quote_approval_services import QuoteApprovalService
    lpo = QuoteApprovalService.generate_lpo(quote)
    
    messages.success(request, f"LPO {lpo.lpo_number} created successfully!")
    return redirect('lpo_detail', lpo_number=lpo.lpo_number)
```

Add to `urls.py`:
```python
path('quotes/<str:quote_id>/generate-lpo/', views.create_lpo_from_quote, name='create_lpo_from_quote'),
```

Then add a button in your quote detail template:
```html
{% if quote.status == 'Approved' and not quote.lpo %}
<a href="{% url 'create_lpo_from_quote' quote.quote_id %}" 
   class="btn btn-primary">
    Generate LPO
</a>
{% endif %}
```

---

## 📊 LPO Features That DO Work

Once an LPO is created (by any method), these features work:

### 1. ✅ View LPO List
- URL: `/lpo/`
- View: `lpo_list` (fully implemented)
- Template: `lpo_list.html`
- Features:
  - Filter by status (pending/approved/in_production/completed)
  - Filter by sync status (synced/not synced to QuickBooks)
  - Search by LPO number, client name, quote ID

### 2. ✅ View LPO Detail
- URL: `/lpo/<lpo_number>/`
- View: `lpo_detail` (fully implemented)
- Template: `lpo_detail.html`
- Shows:
  - LPO information
  - Line items
  - Totals (subtotal, VAT, total)
  - Status tracking
  - QuickBooks sync status
  - Related quote and job links

### 3. ✅ Sync to QuickBooks
- URL: `/lpo/<lpo_number>/sync/`
- View: `sync_to_quickbooks` (fully implemented)
- Features:
  - Creates customer in QuickBooks (if doesn't exist)
  - Creates invoice in QuickBooks
  - Stores QuickBooks invoice ID and number
  - Marks LPO as synced
  - Only works for completed LPOs

---

## 🎯 RECOMMENDED SOLUTION

To get the full flow working properly, you need to implement the missing views:

### Priority 1: Implement Quote Approval Views

**File: `clientapp/views.py`**

```python
@login_required
def send_quote(request, quote_id):
    """Send quote to client via email/WhatsApp"""
    quote = get_object_or_404(Quote, quote_id=quote_id)
    
    if request.method == 'POST':
        method = request.POST.get('method')  # 'email' or 'whatsapp'
        
        from clientapp.quote_approval_services import QuoteApprovalService
        
        if method == 'email':
            result = QuoteApprovalService.send_quote_via_email(quote, request)
        elif method == 'whatsapp':
            result = QuoteApprovalService.send_quote_via_whatsapp(quote)
        else:
            result = {'success': False, 'message': 'Invalid method'}
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
        
        return redirect('quote_detail', quote_id=quote_id)
    
    return render(request, 'send_quote.html', {'quote': quote})


def quote_approval(request, token):
    """Public view for clients to approve quotes"""
    from clientapp.quote_approval_services import QuoteApprovalService
    
    result = QuoteApprovalService.approve_quote(token)
    
    context = {
        'success': result['success'],
        'message': result['message'],
        'quote': result.get('quote'),
        'lpo': result.get('lpo'),
        'job': result.get('job')
    }
    
    return render(request, 'quote_approval.html', context)
```

**Add to `urls.py`:**
```python
# Uncomment these lines:
path('quotes/<str:quote_id>/send/', views.send_quote, name='send_quote'),
path('quotes/approve/<str:token>/', views.quote_approval, name='quote_approval'),
```

---

## 📝 Summary

### What Currently Works:
✅ LPO generation logic (in `QuoteApprovalService`)  
✅ LPO list view  
✅ LPO detail view  
✅ QuickBooks sync  
✅ Auto ID generation (LPO-2025-XXX)  

### What's Broken:
❌ Quote sending to clients  
❌ Quote approval by clients  
❌ Automatic LPO generation trigger  
❌ Manual LPO creation UI  

### Quick Fix to Test:
1. Create a quote in the system
2. Manually set its status to "Approved" in Django admin
3. Use Django shell to run: `QuoteApprovalService.generate_lpo(quote)`
4. View the LPO at `/lpo/<lpo_number>/`
5. Sync to QuickBooks if needed

### Proper Fix:
Implement the two missing views (`send_quote` and `quote_approval`) as shown above, then the full workflow will work end-to-end! 🚀
