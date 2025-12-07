# Account Manager Functionality Implementation Summary

## Overview
This document outlines the changes needed to implement the account manager functionality for the printshop system. The focus is on improving lead management, quote workflows, and client conversion processes.

## ✅ COMPLETED CHANGES

### 1. Lead Form Validation & Product Interest
**File: `clientapp/forms.py`**
- ✅ Updated `LeadForm` to make all fields required
- ✅ Changed `product_interest` from hardcoded choices to dynamic `ModelChoiceField`
- ✅ Product dropdown now shows products added by production team from the database
- ✅ Added `__init__` method to enforce all fields as required

**Impact:** Account managers can no longer create leads without filling all fields, and product interest shows actual products from the catalog.

---

## 🔄 PENDING CHANGES

### 2. Lead Intake Template Updates
**File: `clientapp/templates/lead_intake.html`**

**Changes Needed:**
1. **Product Interest Field** (Lines 144-154):
   - Replace manual `<select>` dropdown with `{{ form.product_interest }}`
   - Update label to include asterisk: "Product Interest *"

2. **Remove Convert Button** (Lines 90-98):
   - Remove the "Convert" button for Qualified leads
   - Keep only the "Qualify" button for New leads
   - Conversion will now happen through notifications

**Before:**
```html
<div class="space-y-2">
    <label for="id_product_interest" class="text-sm font-medium">Product Interest</label>
    <select name="product_interest" id="id_product_interest" class="form-input">
        <option value="">Select a product...</option>
        {% for product in products %}
        <option value="{{ product.name }}">{{ product.name }} ({{ product.sku }})</option>
        {% endfor %}
    </select>
</div>
```

**After:**
```html
<div class="space-y-2">
    <label for="id_product_interest" class="text-sm font-medium">Product Interest *</label>
    {{ form.product_interest }}
</div>
```

**Actions Column - Before:**
```html
<td>
    <div class="flex gap-2">
        {% if lead.status == 'New' %}
        <a href="{% url 'qualify_lead' lead.lead_id %}" class="btn btn-secondary text-sm py-1 px-3">Qualify</a>
        {% elif lead.status == 'Qualified' %}
        <a href="{% url 'convert_lead' lead.lead_id %}" class="btn btn-primary text-sm py-1 px-3">Convert</a>
        {% endif %}
    </div>
</td>
```

**Actions Column - After:**
```html
<td>
    <div class="flex gap-2">
        {% if lead.status == 'New' %}
        <a href="{% url 'qualify_lead' lead.lead_id %}" class="btn btn-secondary text-sm py-1 px-3">Qualify</a>
        {% endif %}
    </div>
</td>
```

---

### 3. Quote Approval & Lead Conversion Workflow
**File: `clientapp/models.py` - Quote model**

**Current Behavior:**
- Leads are converted to clients immediately when quote is approved (line 723-724)

**Required Behavior:**
- Lead should only convert to client when:
  1. Quote is approved by client
  2. LPO (Local Purchase Order) is received
  3. Account Manager receives notification
  4. Account Manager clicks "Convert" button in notification detail

**Changes Needed:**

1. **Add LPO tracking field to Quote model:**
```python
lpo_received = models.BooleanField(default=False)
lpo_number = models.CharField(max_length=50, blank=True)
lpo_received_date = models.DateTimeField(null=True, blank=True)
```

2. **Update Quote.save() method** (around line 722-726):
```python
# OLD CODE - Remove this:
if self.status == 'Approved' and self.lead and not self.lead.converted_to_client:
    self.convert_lead_to_client()

# NEW CODE - Add this:
if self.status == 'Approved' and self.lpo_received and self.lead and not self.lead.converted_to_client:
    # Create notification for account manager instead of auto-converting
    if self.lead.created_by:  # Account manager who created the lead
        Notification.objects.create(
            recipient=self.lead.created_by,
            title=f"Lead {self.lead.lead_id} Ready for Conversion",
            message=f"Quote {self.quote_id} has been approved and LPO received. Click to convert lead to client.",
            link=reverse('convert_lead_notification', args=[self.lead.lead_id])
        )
```

---

### 4. Notification Detail Page with Convert Button
**New File: `clientapp/templates/notification_detail.html`**

Create a new template to show notification details with a convert button:

```html
{% extends 'base.html' %}

{% block content %}
<div class="max-w-4xl mx-auto p-6">
    <div class="card">
        <div class="p-6">
            <h2 class="text-2xl font-semibold mb-4">{{ notification.title }}</h2>
            <p class="text-gray-700 mb-6">{{ notification.message }}</p>
            
            {% if lead %}
            <div class="bg-gray-50 p-4 rounded-lg mb-6">
                <h3 class="font-semibold mb-2">Lead Details</h3>
                <p><strong>Name:</strong> {{ lead.name }}</p>
                <p><strong>Email:</strong> {{ lead.email }}</p>
                <p><strong>Phone:</strong> {{ lead.phone }}</p>
                <p><strong>Product Interest:</strong> {{ lead.product_interest }}</p>
            </div>
            
            {% if lead.status == 'Qualified' and not lead.converted_to_client %}
            <form method="post" action="{% url 'convert_lead' lead.lead_id %}">
                {% csrf_token %}
                <button type="submit" class="btn btn-primary">
                    Convert to Client
                </button>
            </form>
            {% endif %}
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

---

### 5. Update Notifications Template
**File: `clientapp/templates/notifications.html`**

Update the notification link to go to notification detail page:

**Change line 112:**
```html
<!-- OLD -->
{% if notification.link %}
    <a href="{{ notification.link }}" class="btn-link">View details</a>
{% endif %}

<!-- NEW -->
<a href="{% url 'notification_detail' notification.id %}" class="btn-link">View details</a>
```

---

### 6. Add URL Routes
**File: `clientapp/urls.py`** (or main `urls.py`)

Add these URL patterns:

```python
path('notifications/<int:pk>/', views.notification_detail, view_name='notification_detail'),
path('convert-lead-notification/<str:lead_id>/', views.convert_lead_from_notification, name='convert_lead_notification'),
```

---

### 7. Add Views for Notifications
**File: `clientapp/views.py`**

Add these view functions:

```python
@login_required
@group_required('Account Manager')
def notification_detail(request, pk):
    """View notification details with convert button"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    
    # Mark as read
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    # Try to extract lead_id from notification link
    lead = None
    if 'convert-lead-notification' in notification.link:
        lead_id = notification.link.split('/')[-2]
        lead = Lead.objects.filter(lead_id=lead_id).first()
    
    context = {
        'notification': notification,
        'lead': lead,
        'current_view': 'notifications',
    }
    return render(request, 'notification_detail.html', context)


@login_required
@group_required('Account Manager')
def convert_lead_from_notification(request, lead_id):
    """Redirect to convert lead page from notification"""
    lead = get_object_or_404(Lead, lead_id=lead_id)
    return redirect('convert_lead', lead_id=lead_id)
```

---

### 8. Multi-Product Quote Form (create_quote.html)
**File: `clientapp/templates/create_quote.html`**

**Current State:** Form exists but needs to be made functional

**Changes Needed:**

1. **Client/Lead Dropdown** (Lines 226-260):
   - Already implemented correctly
   - Shows dropdown of clients and leads
   - Auto-fills client details when selected

2. **Account Manager Auto-fill:**
   - Add hidden field or readonly field:
```html
<input type="hidden" name="account_manager" value="{{ request.user.id }}">
<!-- OR for display -->
<div class="form-group">
    <label>Account Manager</label>
    <input type="text" value="{{ request.user.get_full_name }}" class="form-input" readonly>
</div>
```

3. **Product Selection** (Lines 321-327):
   - Update "Add Line Item" to show product dropdown from database
   - Modify JavaScript `addLineItem()` function to include product dropdown:

```javascript
function addLineItem(data = {}) {
    itemCounter++;
    const row = document.createElement('tr');
    row.className = 'item-row border-b border-gray-200';
    row.dataset.itemId = itemCounter;

    row.innerHTML = `
        <td class="py-3 px-2">
            <input type="number" name="quantity_${itemCounter}" 
                class="item-qty w-16 text-right border border-gray-300 rounded px-2 py-1" 
                value="${data.qty || 1}" min="1" required>
        </td>
        <td class="py-3 px-2">
            <select name="product_${itemCounter}" class="item-product w-full border border-gray-300 rounded px-2 py-1 text-sm" required>
                <option value="">Select product...</option>
                {% for product in products %}
                <option value="{{ product.id }}" data-price="{{ product.base_price }}">
                    {{ product.name }} ({{ product.sku }})
                </option>
                {% endfor %}
            </select>
        </td>
        <td class="py-3 px-2 text-right">
            <input type="number" name="unit_price_${itemCounter}" 
                class="item-unitprice w-28 text-right border border-gray-300 rounded px-2 py-1" 
                step="0.01" value="${data.unitPrice || 0}" min="0" required>
        </td>
        <td class="py-3 px-2 text-right">
            <input type="number" name="amount_${itemCounter}" 
                class="item-amount w-28 text-right border border-gray-300 rounded px-2 py-1 bg-gray-50 font-semibold" 
                readonly value="0.00">
        </td>
        <td class="py-3 px-2 text-center">
            <button type="button" class="remove-item text-red-600 hover:text-red-800 text-lg" title="Remove">
                ✖
            </button>
        </td>
    `;

    itemsTableBody.appendChild(row);
    
    // Add event listener for product selection to auto-fill price
    const productSelect = row.querySelector('.item-product');
    productSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const price = selectedOption.dataset.price || 0;
        row.querySelector('.item-unitprice').value = price;
        calculateRowTotal(row);
    });
    
    attachRowListeners(row);
    calculateRowTotal(row);
    updateTotals();
}
```

---

### 9. Quote Creation View Update
**File: `clientapp/views.py`**

Update the `create_quote` view to handle multi-product quotes:

```python
@login_required
@group_required('Account Manager')
def create_quote(request):
    if request.method == 'POST':
        # Get form data
        quote_type = request.POST.get('quote_type')  # 'client' or 'lead'
        client_id = request.POST.get('client_id')
        lead_id = request.POST.get('lead_id')
        item_count = int(request.POST.get('item_count', 0))
        
        # Validate
        if item_count == 0:
            messages.error(request, 'Please add at least one item')
            return redirect('create_quote')
        
        # Create quotes for each item
        for i in range(1, item_count + 1):
            product_id = request.POST.get(f'product_{i}')
            quantity = request.POST.get(f'quantity_{i}')
            unit_price = request.POST.get(f'unit_price_{i}')
            
            if not all([product_id, quantity, unit_price]):
                continue
            
            product = Product.objects.get(id=product_id)
            
            quote = Quote.objects.create(
                client_id=client_id if quote_type == 'client' else None,
                lead_id=lead_id if quote_type == 'lead' else None,
                product_name=product.name,
                quantity=int(quantity),
                unit_price=Decimal(unit_price),
                payment_terms=request.POST.get('payment_terms', 'Prepaid'),
                status=request.POST.get('status', 'Draft'),
                include_vat=request.POST.get('include_vat') == 'on',
                notes=request.POST.get('notes', ''),
                terms=request.POST.get('terms', ''),
                created_by=request.user,
            )
        
        messages.success(request, 'Quote created successfully')
        return redirect('quote_management')
    
    # GET request
    clients = Client.objects.filter(status='Active').order_by('name')
    leads = Lead.objects.exclude(status__in=['Converted', 'Lost']).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'clients': clients,
        'leads': leads,
        'products': products,
        'current_view': 'quote_management',
        'today': timezone.now().date(),
        'default_valid_until': (timezone.now() + timedelta(days=30)).date(),
        'current_year': timezone.now().year,
    }
    return render(request, 'create_quote.html', context)
```

---

## SUMMARY OF KEY WORKFLOW CHANGES

### Old Workflow:
1. Create Lead → Qualify Lead → **Convert Lead** (manual button) → Client

### New Workflow:
1. Create Lead (all fields required, product from catalog)
2. Qualify Lead
3. Create Quote for Lead
4. Send Quote to Client
5. Client Approves Quote
6. **Production Team receives LPO**
7. **System creates notification for Account Manager**
8. **Account Manager clicks notification**
9. **Account Manager clicks "Convert to Client" button in notification detail**
10. Lead becomes Client
11. Client Onboarding Form appears

---

## FILES MODIFIED

1. ✅ `clientapp/forms.py` - LeadForm updated
2. 🔄 `clientapp/templates/lead_intake.html` - Remove convert button, use form field for products
3. 🔄 `clientapp/models.py` - Add LPO fields, update conversion logic
4. 🔄 `clientapp/views.py` - Add notification detail view, update create_quote
5. 🔄 `clientapp/templates/notifications.html` - Update links
6. ➕ `clientapp/templates/notification_detail.html` - New file
7. 🔄 `clientapp/templates/create_quote.html` - Make functional with product dropdown
8. 🔄 `clientapp/urls.py` - Add new URL patterns

---

## TESTING CHECKLIST

- [ ] Lead creation requires all fields
- [ ] Product interest shows products from database
- [ ] Convert button removed from Lead Tracking page
- [ ] Quote approval doesn't auto-convert lead
- [ ] LPO received triggers notification
- [ ] Notification shows convert button
- [ ] Convert button redirects to onboarding form
- [ ] Multi-product quote form shows product dropdown
- [ ] Account manager name auto-fills in quotes
- [ ] Products in quote dropdown match production team's catalog

---

## NOTES

- Do NOT modify any Production Team functionality
- Do NOT change UI/design structure
- Focus on functionality and data flow
- All changes are for Account Manager role only
