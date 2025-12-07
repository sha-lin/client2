# QUOTE CREATE FORM - REQUIRED CHANGES

## Summary
The `quote_create.html` form currently has hardcoded test data. You need to update it to show real data from the database.

## Changes Required:

### 1. Client/Lead Dropdown (Lines 9-15)

**REPLACE THIS:**
```html
<div>
    <label class="block text-sm font-medium text-gray-700 mb-2">Client Name</label>
    <input type="text" name="client_name"
        value="{% if quote %}{{ quote.client_name }}{% else %}Acme Corporation{% endif %}"
        placeholder="Enter client name"
        class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50">
</div>
```

**WITH THIS:**
```html
<div>
    <label class="block text-sm font-medium text-gray-700 mb-2">Client/Lead Name *</label>
    <select name="client_name" id="client_select" required
        class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        <option value="">Select client or lead...</option>
        <optgroup label="Active Clients">
            {% for client in clients %}
            <option value="{{ client.name }}">{{ client.name }} (Client)</option>
            {% endfor %}
        </optgroup>
        <optgroup label="Active Leads">
            {% for lead in leads %}
            <option value="{{ lead.name }}">{{ lead.name }} (Lead)</option>
            {% endfor %}
        </optgroup>
    </select>
</div>
```

---

### 2. Account Manager Auto-fill (Lines 16-22)

**REPLACE THIS:**
```html
<div>
    <label class="block text-sm font-medium text-gray-700 mb-2">Account Manager</label>
    <input type="text" name="account_manager"
        value="{% if quote %}{{ quote.account_manager }}{% else %}John Doe{% endif %}"
        placeholder="Enter account manager"
        class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50">
</div>
```

**WITH THIS:**
```html
<div>
    <label class="block text-sm font-medium text-gray-700 mb-2">Account Manager</label>
    <input type="text" name="account_manager"
        value="{{ request.user.get_full_name }}"
        readonly
        class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-100">
</div>
```

---

### 3. Product List in Modal (Lines 234-247)

**REPLACE THIS:**
```html
<div id="productList" class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Products will be loaded here -->
    <div class="border border-gray-200 rounded-lg p-4 hover:border-blue-500 cursor-pointer transition-colors product-item">
        <div class="flex gap-4">
            <div class="w-16 h-16 bg-gray-100 rounded flex-shrink-0"></div>
            <div class="flex-1">
                <h4 class="text-sm font-medium text-gray-900 mb-1">Premium Business Cards</h4>
                <p class="text-xs text-gray-500 mb-2">High quality cards with custom options</p>
                <p class="text-sm font-semibold text-blue-600">From KES 15.00</p>
            </div>
        </div>
    </div>
</div>
```

**WITH THIS:**
```html
<div id="productList" class="grid grid-cols-1 md:grid-cols-2 gap-4">
    {% for product in products %}
    <div class="border border-gray-200 rounded-lg p-4 hover:border-blue-500 cursor-pointer transition-colors product-item"
         data-product-id="{{ product.id }}"
         data-product-name="{{ product.name }}"
         data-product-price="{{ product.base_price }}"
         data-product-sku="{{ product.sku }}">
        <div class="flex gap-4">
            <div class="w-16 h-16 bg-gray-100 rounded flex-shrink-0 flex items-center justify-center">
                {% if product.image %}
                <img src="{{ product.image.url }}" alt="{{ product.name }}" class="w-full h-full object-cover rounded">
                {% else %}
                <i data-lucide="package" class="w-8 h-8 text-gray-400"></i>
                {% endif %}
            </div>
            <div class="flex-1">
                <h4 class="text-sm font-medium text-gray-900 mb-1">{{ product.name }}</h4>
                <p class="text-xs text-gray-500 mb-2">{{ product.sku }} - {{ product.description|truncatewords:8 }}</p>
                <p class="text-sm font-semibold text-blue-600">KES {{ product.base_price|floatformat:2 }}</p>
            </div>
        </div>
    </div>
    {% empty %}
    <div class="col-span-2 text-center py-8 text-gray-500">
        <p>No products available. Please add products in the Product Catalog.</p>
    </div>
    {% endfor %}</div>
```

---

## What This Achieves:

✅ **Client/Lead Dropdown** - Shows all registered clients and leads from database  
✅ **Account Manager Auto-fill** - Shows logged-in user's name (readonly)  
✅ **Product List** - Shows products added by production team in catalog  
✅ **No Test Data** - All data comes from database  

## Backend is Ready:

The `quote_create` view (line 1115 in views.py) already passes:
- `clients` - Active clients from database
- `leads` - Active leads from database  
- `products` - Active products from catalog

You just need to update the template to use this data!

## File to Edit:
`clientapp/templates/quote_create.html`

Make these 3 changes and the form will work perfectly with real data!
