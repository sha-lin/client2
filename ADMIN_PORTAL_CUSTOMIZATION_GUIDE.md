# Admin Portal - Code Examples & Customization Guide

## 🎨 COMMON CUSTOMIZATIONS

### 1. Add a New Column to a List

**File:** `clientapp/templates/admin/clients_list.html`

**Current:**
```html
{% block table_header %}
    <tr>
        <th>Client ID</th>
        <th>Name</th>
        <th>Email</th>
        <th>Phone</th>
        <th>Status</th>
        <th>Created</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for client in page_obj %}
        <tr>
            <td>{{ client.client_id }}</td>
            <td>{{ client.name }}</td>
            <td>{{ client.email }}</td>
            <td>{{ client.phone }}</td>
            <td><span class="badge badge-success">{{ client.status }}</span></td>
            <td>{{ client.created_at|date:"M d, Y" }}</td>
            <td><div class="row-actions"><a href="#" class="action-btn">Edit</a></div></td>
        </tr>
    {% endfor %}
{% endblock %}
```

**To Add "Company" Column:**
```html
{% block table_header %}
    <tr>
        <th>Client ID</th>
        <th>Name</th>
        <th>Email</th>
        <th>Company</th>    <!-- ADD THIS -->
        <th>Phone</th>
        <th>Status</th>
        <th>Created</th>
        <th>Actions</th>
    </tr>
{% endblock %}

{% block table_body %}
    {% for client in page_obj %}
        <tr>
            <td>{{ client.client_id }}</td>
            <td>{{ client.name }}</td>
            <td>{{ client.email }}</td>
            <td>{{ client.company }}</td>    <!-- ADD THIS -->
            <td>{{ client.phone }}</td>
            <td><span class="badge badge-success">{{ client.status }}</span></td>
            <td>{{ client.created_at|date:"M d, Y" }}</td>
            <td><div class="row-actions"><a href="#" class="action-btn">Edit</a></div></td>
        </tr>
    {% endfor %}
{% endblock %}
```

---

### 2. Add a New Filter

**File:** `clientapp/templates/admin/clients_list.html`

**Current:**
```html
{% block filter_controls %}
    <select name="status" class="filter-select" onchange="this.form.submit()">
        <option value="">All Status</option>
        <option value="active" {% if status == 'active' %}selected{% endif %}>Active</option>
        <option value="inactive" {% if status == 'inactive' %}selected{% endif %}>Inactive</option>
    </select>
{% endblock %}
```

**To Add "Risk Rating" Filter:**
```html
{% block filter_controls %}
    <select name="status" class="filter-select" onchange="this.form.submit()">
        <option value="">All Status</option>
        <option value="active" {% if status == 'active' %}selected{% endif %}>Active</option>
        <option value="inactive" {% if status == 'inactive' %}selected{% endif %}>Inactive</option>
    </select>
    
    <select name="risk_rating" class="filter-select" onchange="this.form.submit()">
        <option value="">All Risk Ratings</option>
        <option value="low" {% if risk_rating == 'low' %}selected{% endif %}>Low</option>
        <option value="medium" {% if risk_rating == 'medium' %}selected{% endif %}>Medium</option>
        <option value="high" {% if risk_rating == 'high' %}selected{% endif %}>High</option>
    </select>
{% endblock %}
```

**Then Update View:**

**File:** `clientapp/admin_views.py`

**Current:**
```python
@staff_member_required
def clients_list(request):
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = Client.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    context = {
        'title': 'Clients',
        'page_obj': paginator.get_page(page),
        'search': search,
        'status': status,
    }
    return render(request, 'admin/clients_list.html', context)
```

**To Add Risk Rating Filter:**
```python
@staff_member_required
def clients_list(request):
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    risk_rating = request.GET.get('risk_rating', '')  # ADD THIS
    page = request.GET.get('page', 1)
    
    queryset = Client.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    if risk_rating:  # ADD THIS
        queryset = queryset.filter(risk_rating=risk_rating)
    
    context = {
        'title': 'Clients',
        'page_obj': paginator.get_page(page),
        'search': search,
        'status': status,
        'risk_rating': risk_rating,  # ADD THIS
    }
    return render(request, 'admin/clients_list.html', context)
```

---

### 3. Change Items Per Page

**File:** `clientapp/admin_views.py`

**Current:**
```python
paginator = Paginator(queryset, 25)  # 25 items per page
```

**To Change to 50 Items Per Page:**
```python
paginator = Paginator(queryset, 50)  # 50 items per page
```

---

### 4. Add Custom Formatting

**File:** `clientapp/templates/admin/clients_list.html`

**Example: Format Phone as Link**

Before:
```html
<td>{{ client.phone }}</td>
```

After:
```html
<td><a href="tel:{{ client.phone }}">{{ client.phone }}</a></td>
```

**Example: Format Date with Time**

Before:
```html
<td>{{ client.created_at|date:"M d, Y" }}</td>
```

After:
```html
<td>{{ client.created_at|date:"M d, Y H:i" }}</td>
```

**Example: Show First 100 Characters of Description**

Before:
```html
<td>{{ product.description }}</td>
```

After:
```html
<td>{{ product.description|truncatewords:10 }} ...</td>
```

---

### 5. Change Badge Colors

**File:** `clientapp/templates/admin/generic_list.html`

**Current CSS:**
```css
.badge-success {
    background: #d1fae5;
    color: #065f46;
}

.badge-warning {
    background: #fef3c7;
    color: #92400e;
}

.badge-danger {
    background: #fee2e2;
    color: #7f1d1d;
}

.badge-info {
    background: #dbeafe;
    color: #0c4a6e;
}
```

**To Change Success to Purple:**
```css
.badge-success {
    background: #e9d5ff;  /* purple */
    color: #6b21a8;
}
```

**Or Add New Badge Type:**
```css
.badge-custom {
    background: #fde047;  /* yellow */
    color: #713f12;
}
```

Then use in template:
```html
<span class="badge badge-custom">Custom Status</span>
```

---

### 6. Add Modal Field Validation

**File:** Any list template (e.g., `clients_list.html`)

**Current:**
```javascript
const fields = [
    { name: 'name', label: 'Client Name', type: 'text' },
    { name: 'email', label: 'Email', type: 'email' },
];
```

**To Add Validation:**
```javascript
const fields = [
    { 
        name: 'name', 
        label: 'Client Name', 
        type: 'text',
        required: true,
        minlength: 3,
        maxlength: 100
    },
    { 
        name: 'email', 
        label: 'Email', 
        type: 'email',
        required: true
    },
];
```

Then update form field rendering in modal:
```javascript
function renderFormFields(fields) {
    const container = document.getElementById('form-container');
    container.innerHTML = fields.map(field => {
        let html = `<div class="form-group">
            <label>${field.label}</label>
            <input 
                type="${field.type}" 
                name="${field.name}"
                ${field.required ? 'required' : ''}
                ${field.minlength ? `minlength="${field.minlength}"` : ''}
                ${field.maxlength ? `maxlength="${field.maxlength}"` : ''}
            >`;
        if (field.error) {
            html += `<span style="color: red; font-size: 12px;">${field.error}</span>`;
        }
        html += '</div>';
        return html;
    }).join('');
}
```

---

### 7. Add Custom Button Actions

**File:** Any list template

**Current:**
```html
<td>
    <div class="row-actions">
        <a href="#" class="action-btn">Edit</a>
    </div>
</td>
```

**To Add View & Export Buttons:**
```html
<td>
    <div class="row-actions">
        <a href="#" class="action-btn" onclick="viewItem({{ client.id }})">View</a>
        <a href="#" class="action-btn" onclick="editItem({{ client.id }})">Edit</a>
        <a href="#" class="action-btn" onclick="exportItem({{ client.id }})">Export</a>
    </div>
</td>
```

Then add JavaScript:
```javascript
function viewItem(id) {
    fetch(`/api/admin/detail/client/${id}/`)
        .then(r => r.json())
        .then(data => {
            alert(JSON.stringify(data, null, 2));
        });
}

function exportItem(id) {
    window.location.href = `/api/admin/export/client/${id}/`;
}
```

---

### 8. Customize Table Header Styling

**File:** `clientapp/templates/admin/generic_list.html`

**Current:**
```css
th {
    padding: 12px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    color: #64748b;
    background: #f8fafc;
}
```

**To Add Sticky Header:**
```css
th {
    padding: 12px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    color: #64748b;
    background: #f8fafc;
    position: sticky;
    top: 0;
    z-index: 10;
}
```

---

### 9. Change Search Placeholder

**File:** `clientapp/templates/admin/generic_list.html`

**Current:**
```html
<input type="text" name="q" placeholder="Search..." value="{{ search }}">
```

**To Add Custom Placeholder:**
```html
<input type="text" name="q" placeholder="Search by name, email, phone..." value="{{ search }}">
```

---

### 10. Add Row Highlighting on Hover

**File:** `clientapp/templates/admin/generic_list.html`

**Current CSS:**
```css
tbody tr:hover {
    background: #f8fafc;
}
```

**To Add More Prominent Highlight:**
```css
tbody tr:hover {
    background: #eff6ff;
    box-shadow: 0 0 0 1px #bfdbfe;
    transition: all 0.15s ease;
}
```

---

## 🔧 ADVANCED CUSTOMIZATIONS

### Add Inline Editing

**Instead of Opening Modal:**
```html
<td contenteditable="true" onblur="saveInline('client', {{ client.id }}, this)">
    {{ client.name }}
</td>
```

```javascript
function saveInline(model, id, element) {
    fetch(`/api/admin/update/${model}/${id}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({name: element.textContent})
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) {
            element.style.color = 'red';
            element.textContent = 'Error!';
        }
    });
}
```

### Add Bulk Select Checkboxes

**Add to Table Header:**
```html
<th><input type="checkbox" id="select-all" onchange="toggleAll()"></th>
```

**Add to Each Row:**
```html
<td><input type="checkbox" class="row-select" value="{{ client.id }}"></td>
```

**JavaScript:**
```javascript
function toggleAll() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.row-select');
    checkboxes.forEach(cb => cb.checked = selectAll.checked);
}

function deleteSelected() {
    const selected = Array.from(document.querySelectorAll('.row-select:checked'))
        .map(cb => cb.value);
    
    if (selected.length === 0) {
        alert('Select items first');
        return;
    }
    
    if (!confirm(`Delete ${selected.length} items?`)) return;
    
    Promise.all(selected.map(id =>
        fetch(`/api/admin/delete/client/${id}/`, {method: 'POST'})
    ))
    .then(() => location.reload());
}
```

### Add Export to CSV

**View:**
```python
import csv
from django.http import HttpResponse

@staff_member_required
def export_clients(request):
    clients = Client.objects.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clients.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Client ID', 'Name', 'Email', 'Phone', 'Status'])
    for client in clients:
        writer.writerow([
            client.client_id,
            client.name,
            client.email,
            client.phone,
            client.status
        ])
    
    return response
```

**URL:**
```python
path('admin-dashboard/clients/export/', export_clients, name='export_clients'),
```

**Template Button:**
```html
<a href="/admin-dashboard/clients/export/" class="btn btn-primary">Export CSV</a>
```

---

## 📱 RESPONSIVE CUSTOMIZATIONS

### Mobile-Friendly Adjustments

**File:** `clientapp/templates/admin/generic_list.html`

**Add to CSS:**
```css
@media (max-width: 768px) {
    .sidebar {
        width: 200px;
        font-size: 12px;
    }
    
    .main-content {
        margin-left: 200px;
    }
    
    th, td {
        padding: 8px 12px;
        font-size: 12px;
    }
    
    .action-btn {
        padding: 2px 4px;
        font-size: 11px;
    }
    
    .list-controls {
        flex-direction: column;
    }
}

@media (max-width: 480px) {
    .sidebar {
        display: none;
    }
    
    .main-content {
        margin-left: 0;
    }
    
    table {
        font-size: 11px;
    }
}
```

---

## 🎯 COMMON PATTERNS

### Check if Field Exists in Template
```django
{% if client.company %}
    <td>{{ client.company }}</td>
{% else %}
    <td style="color: #ccc;">N/A</td>
{% endif %}
```

### Show Different Badge Based on Value
```django
{% if client.status == 'active' %}
    <span class="badge badge-success">Active</span>
{% elif client.status == 'inactive' %}
    <span class="badge badge-danger">Inactive</span>
{% else %}
    <span class="badge badge-info">{{ client.status }}</span>
{% endif %}
```

### Format Currency
```django
<td>${{ quote.total_amount|floatformat:2 }}</td>
```

### Format DateTime
```django
<td>{{ client.created_at|date:"M d, Y - H:i" }}</td>
```

### Truncate Long Text
```django
<td title="{{ product.description }}">
    {{ product.description|truncatewords:5 }}
</td>
```

---

## ✅ TESTING CUSTOMIZATIONS

After making changes:

1. **Clear Cache**
   ```bash
   Ctrl+Shift+Del in browser
   ```

2. **Reload Page**
   ```
   Ctrl+F5
   ```

3. **Check Console**
   ```
   F12 → Console → Look for red errors
   ```

4. **Test Functionality**
   - Try create/edit/delete
   - Test filters
   - Test search
   - Check styling

5. **Mobile Test**
   - Open DevTools
   - Toggle device toolbar
   - Test on mobile view

---

## 📚 REFERENCE TEMPLATES

### Minimal List Template
```django
{% extends "admin/generic_list.html" %}

{% block table_header %}
<tr><th>ID</th><th>Name</th><th>Status</th><th>Actions</th></tr>
{% endblock %}

{% block table_body %}
{% for item in page_obj %}
<tr>
    <td>{{ item.id }}</td>
    <td>{{ item.name }}</td>
    <td><span class="badge badge-info">{{ item.status }}</span></td>
    <td><a href="#" class="action-btn">Edit</a></td>
</tr>
{% endfor %}
{% endblock %}
```

### Full Featured List Template
```django
{% extends "admin/generic_list.html" %}

{% block filter_controls %}
<select name="status" class="filter-select" onchange="this.form.submit()">
    <option value="">All</option>
    <option value="active" {% if status == 'active' %}selected{% endif %}>Active</option>
</select>
{% endblock %}

{% block table_header %}
<tr>
    <th><input type="checkbox" id="select-all" onchange="toggleAll()"></th>
    <th>ID</th>
    <th>Name</th>
    <th>Email</th>
    <th>Status</th>
    <th>Created</th>
    <th>Actions</th>
</tr>
{% endblock %}

{% block table_body %}
{% for item in page_obj %}
<tr>
    <td><input type="checkbox" class="row-select" value="{{ item.id }}"></td>
    <td>{{ item.id }}</td>
    <td><strong>{{ item.name }}</strong></td>
    <td>{{ item.email }}</td>
    <td><span class="badge {% if item.status == 'active' %}badge-success{% else %}badge-danger{% endif %}">{{ item.status }}</span></td>
    <td>{{ item.created_at|date:"M d, Y" }}</td>
    <td>
        <div class="row-actions">
            <a href="#" class="action-btn" onclick="openEditModal({{ item.id }})">Edit</a>
            <a href="#" class="action-btn danger" onclick="deleteItem({{ item.id }})">Delete</a>
        </div>
    </td>
</tr>
{% endfor %}
{% endblock %}

{% block extra_js %}
<script>
    function deleteItem(id) {
        if (confirm('Sure?')) {
            fetch(`/api/admin/delete/client/${id}/`, {method: 'POST'})
                .then(r => r.json())
                .then(d => d.success && location.reload());
        }
    }
</script>
{% endblock %}
```

---

Happy customizing! 🎉
