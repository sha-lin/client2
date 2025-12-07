# Processes & Product Pricing Integration Plan

## Current Situation Analysis

### What You Have Now

#### 1. **Process/Costing System** (`process_create.html`)
Your production team currently inputs:
- **Process Name & Details**: Name, ID, description, category (outsourced/in-house)
- **Pricing Method**: 
  - **Tier-Based Pricing**: Quantity tiers with fixed costs per tier
  - **Formula-Based Pricing**: Variables and formulas for dynamic cost calculation
- **Vendor Information**: Links to vendors with their costs and rates
- **Pricing Tiers**: Cost ranges based on quantity
- **Variables**: For formula-based pricing (e.g., stitch count, paper weight, etc.)

**Database Models**:
- `Process`: Main process model
- `ProcessTier`: Quantity tiers for tier-based pricing
- `ProcessVariable`: Variables for formula-based pricing
- `ProcessVendor`: Vendor costs associated with processes

#### 2. **Product Pricing System** (`product_create_edit.html` - Pricing & Variables Tab)
Your product catalog has:
- **Base Cost (EVP)**: Lowest possible vendor cost
- **Pricing Model**: Variable, Simple, or Quote-based
- **Margins**: Default margin %, minimum margin %
- **Product Variables**: Customer-facing options (quantity, paper weight, coating, etc.)
- **ProductVariableOption**: Specific option choices with pricing impacts

**Database Models**:
- `Product`: Main product model
- `ProductPricing`: Pricing information for the product
- `ProductVariable`: Customer-facing product options
- `ProductVariableOption`: Specific choices for each variable

### The Problem

**The two systems are currently disconnected:**
- ❌ Product pricing doesn't reference Process costs
- ❌ Variables defined in Processes aren't auto-linked to Product variables
- ❌ Vendor costs from Processes aren't used in Product pricing
- ❌ No way to select a Process when creating a product

---

## Solution: How to Connect the Two Systems

### Phase 1: Database Schema Changes

#### 1.1: Link Product to Process (Most Important)

Add a foreign key relationship in the `ProductPricing` model to link to `Process`:

**File: `clientapp/models.py`**

```python
class ProductPricing(models.Model):
    # ... existing fields ...
    
    # NEW FIELD: Link to Process
    process = models.ForeignKey(
        'Process', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products',
        help_text="Select the costing process for this product"
    )
    
    # Optional: Override process costs with custom values
    use_process_costs = models.BooleanField(
        default=True,
        help_text="Use costs from linked process, or override with custom values"
    )
```

**Migration Command**:
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 1.2: Track Process Variables in Product Variables

Add a field to link `ProductVariable` back to `ProcessVariable`:

**File: `clientapp/models.py`**

```python
class ProductVariable(models.Model):
    # ... existing fields ...
    
    # NEW FIELD: Link to ProcessVariable
    source_process_variable = models.ForeignKey(
        'ProcessVariable',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Source variable from process (if auto-imported)"
    )
```

---

### Phase 2: UI Changes

#### 2.1: Add Process Selection in Product Create/Edit Form

**File: `clientapp/templates/product_create_edit.html`**

Add a new field in the "Pricing & Variables" tab, right after the "Base Pricing Information" section:

```html
<!-- NEW SECTION: Process Selection -->
<div class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
    <h3 class="text-base font-semibold text-gray-900 mb-6">Process & Costing</h3>
    
    <div class="space-y-4">
        <!-- Process Selection Dropdown -->
        <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">
                Select Costing Process
                <span class="text-gray-500">(Optional)</span>
            </label>
            <select name="process" id="id_process"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="">-- No Process (Manual Pricing) --</option>
                {% for process in processes %}
                <option value="{{ process.id }}" 
                    data-pricing-type="{{ process.pricing_type }}"
                    data-base-cost="{{ process.base_cost }}"
                    {% if product and product.pricing and product.pricing.process_id == process.id %}selected{% endif %}>
                    {{ process.process_id }} - {{ process.process_name }} ({{ process.get_pricing_type_display }})
                </option>
                {% endfor %}
            </select>
            <p class="text-xs text-gray-500 mt-1">
                Select a process to auto-populate costs and variables from the costing system
            </p>
        </div>

        <!-- Auto-import Variables Checkbox -->
        <div>
            <label class="flex items-center">
                <input type="checkbox" name="auto_import_variables" id="id_auto_import_variables" 
                    class="mr-2 rounded text-blue-600">
                <span class="text-sm text-gray-700">
                    Auto-import variables from selected process
                </span>
            </label>
            <p class="text-xs text-gray-500 mt-1 ml-6">
                This will create product variables based on the process variables
            </p>
        </div>

        <!-- Process Info Display (shown when process is selected) -->
        <div id="process-info-display" class="hidden border-t border-gray-200 pt-4 mt-4">
            <h4 class="text-sm font-semibold text-gray-900 mb-3">Process Information</h4>
            <div class="grid grid-cols-3 gap-4 text-sm">
                <div>
                    <span class="text-gray-600">Pricing Type:</span>
                    <span id="process_pricing_type" class="font-medium text-gray-900 ml-2">-</span>
                </div>
                <div>
                    <span class="text-gray-600">Lead Time:</span>
                    <span id="process_lead_time" class="font-medium text-gray-900 ml-2">-</span>
                </div>
                <div>
                    <span class="text-gray-600">Category:</span>
                    <span id="process_category" class="font-medium text-gray-900 ml-2">-</span>
                </div>
            </div>
            
            <!-- Button to View Full Process Details -->
            <div class="mt-3">
                <a id="view_process_link" href="#" target="_blank" 
                    class="text-sm text-blue-600 hover:text-blue-800 inline-flex items-center gap-1">
                    <i data-lucide="external-link" class="w-3 h-3"></i>
                    View Full Process Details
                </a>
            </div>
        </div>
    </div>
</div>
```

#### 2.2: Add JavaScript to Handle Process Selection

Add this JavaScript at the bottom of `product_create_edit.html`:

```javascript
<script>
// Handle Process Selection Changes
document.addEventListener('DOMContentLoaded', function() {
    const processSelect = document.getElementById('id_process');
    const processInfoDisplay = document.getElementById('process-info-display');
    const autoImportCheckbox = document.getElementById('id_auto_import_variables');
    const baseCostInput = document.getElementById('id_base_cost');
    
    if (processSelect) {
        processSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            
            if (this.value) {
                // Show process info
                processInfoDisplay.classList.remove('hidden');
                
                // Update process info display
                const pricingType = selectedOption.getAttribute('data-pricing-type');
                document.getElementById('process_pricing_type').textContent = 
                    pricingType === 'tier' ? 'Tier-Based' : 'Formula-Based';
                
                // Update view process link
                document.getElementById('view_process_link').href = 
                    `/processes/${this.value}/view/`;
                
                // Optional: Auto-populate base cost from process
                const baseCost = selectedOption.getAttribute('data-base-cost');
                if (baseCost && confirm('Would you like to use the base cost from this process?')) {
                    baseCostInput.value = baseCost;
                }
                
                // Enable auto-import checkbox
                autoImportCheckbox.disabled = false;
                
                // Optional: Fetch and display process variables
                if (autoImportCheckbox.checked) {
                    fetchProcessVariables(this.value);
                }
            } else {
                // Hide process info
                processInfoDisplay.classList.add('hidden');
                autoImportCheckbox.disabled = true;
                autoImportCheckbox.checked = false;
            }
        });
        
        // Trigger on page load if process is already selected
        if (processSelect.value) {
            processSelect.dispatchEvent(new Event('change'));
        }
    }
    
    // Handle auto-import checkbox change
    if (autoImportCheckbox) {
        autoImportCheckbox.addEventListener('change', function() {
            if (this.checked && processSelect.value) {
                fetchProcessVariables(processSelect.value);
            }
        });
    }
});

// Fetch process variables via AJAX
function fetchProcessVariables(processId) {
    fetch(`/ajax/process/${processId}/variables/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Auto-populate product variables based on process variables
                populateProductVariables(data.variables);
            }
        })
        .catch(error => {
            console.error('Error fetching process variables:', error);
        });
}

function populateProductVariables(processVariables) {
    // This function would create product variables based on process variables
    // Implementation depends on your existing variable management JavaScript
    console.log('Process variables:', processVariables);
    
    // Show confirmation message
    const message = `Found ${processVariables.length} variables from the process. ` +
                   `Click "Add Variable" to review and add them to your product.`;
    alert(message);
}
</script>
```

---

### Phase 3: Backend/View Changes

#### 3.1: Update Product Create View

**File: `clientapp/views.py`**

Modify the `product_create` function to:
1. Pass available processes to the template
2. Handle process selection in POST
3. Auto-import variables if requested

```python
def product_create(request):
    # ... existing code ...
    
    # Get all active processes
    processes = Process.objects.filter(status='active').order_by('process_name')
    
    if request.method == 'POST':
        # ... existing form handling ...
        
        # Handle process selection
        process_id = request.POST.get('process')
        if process_id:
            try:
                process = Process.objects.get(id=process_id)
                # Link the process to product pricing
                if product.pricing:
                    product.pricing.process = process
                    product.pricing.save()
                
                # Auto-import variables if requested
                if request.POST.get('auto_import_variables') == 'on':
                    import_process_variables_to_product(process, product)
                    
            except Process.DoesNotExist:
                messages.warning(request, 'Selected process not found')
    
    context = {
        # ... existing context ...
        'processes': processes,
    }
    
    return render(request, 'product_create_edit.html', context)
```

#### 3.2: Create Helper Function to Import Variables

**File: `clientapp/views.py`**

```python
def import_process_variables_to_product(process, product):
    """
    Import variables from a Process to a Product
    """
    if process.pricing_type == 'formula':
        # For formula-based pricing, import formula variables
        process_variables = process.variables.all()
        
        for pv in process_variables:
            # Check if variable already exists
            existing = ProductVariable.objects.filter(
                product=product,
                name=pv.variable_name
            ).first()
            
            if not existing:
                # Create new product variable
                ProductVariable.objects.create(
                    product=product,
                    name=pv.variable_name,
                    variable_type='required',
                    pricing_type='increment',  # or map from process variable
                    source_process_variable=pv,
                    display_order=pv.order
                )
                
                # Create default options based on variable type
                # (Implementation depends on your needs)
                
    elif process.pricing_type == 'tier':
        # For tier-based pricing, import quantity as a variable
        quantity_var, created = ProductVariable.objects.get_or_create(
            product=product,
            name='Quantity',
            defaults={
                'variable_type': 'required',
                'pricing_type': 'fixed',
                'display_order': 0
            }
        )
        
        if created:
            # Create options from process tiers
            tiers = process.tiers.all().order_by('tier_number')
            for i, tier in enumerate(tiers):
                ProductVariableOption.objects.create(
                    variable=quantity_var,
                    value=f"{tier.quantity_from} - {tier.quantity_to}",
                    display_order=i,
                    base_cost=tier.cost,
                    price_modifier=tier.price,
                    modifier_type='fixed'
                )
```

#### 3.3: Create AJAX Endpoint for Process Variables

**File: `clientapp/views.py`**

```python
from django.http import JsonResponse

def ajax_process_variables(request, process_id):
    """
    AJAX endpoint to fetch process variables
    """
    try:
        process = Process.objects.get(id=process_id)
        
        variables_data = []
        
        if process.pricing_type == 'formula':
            for var in process.variables.all():
                variables_data.append({
                    'id': var.id,
                    'name': var.variable_name,
                    'type': var.variable_type,
                    'unit': var.unit,
                    'min_value': str(var.min_value) if var.min_value else None,
                    'max_value': str(var.max_value) if var.max_value else None,
                    'default_value': str(var.default_value) if var.default_value else None,
                    'description': var.description
                })
        elif process.pricing_type == 'tier':
            # Return tier information
            for tier in process.tiers.all():
                variables_data.append({
                    'tier_number': tier.tier_number,
                    'quantity_from': tier.quantity_from,
                    'quantity_to': tier.quantity_to,
                    'cost': str(tier.cost),
                    'price': str(tier.price)
                })
        
        return JsonResponse({
            'success': True,
            'pricing_type': process.pricing_type,
            'variables': variables_data
        })
        
    except Process.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Process not found'
        }, status=404)
```

**Add URL pattern** in `clientapp/urls.py`:

```python
path('ajax/process/<int:process_id>/variables/', ajax_process_variables, name='ajax_process_variables'),
```

---

### Phase 4: Pricing Calculation Logic

#### 4.1: Update Product Pricing Calculation

When calculating product prices, check if a process is linked and use its costs:

**File: `clientapp/models.py`**

```python
class ProductPricing(models.Model):
    # ... existing fields ...
    
    def calculate_price(self, quantity, selected_options=None):
        """
        Calculate price based on linked process or custom pricing
        """
        if self.process and self.use_process_costs:
            # Use process-based pricing
            if self.process.pricing_type == 'tier':
                return self._calculate_tier_price(quantity)
            elif self.process.pricing_type == 'formula':
                return self._calculate_formula_price(quantity, selected_options)
        else:
            # Use custom pricing logic
            return self._calculate_custom_price(quantity, selected_options)
    
    def _calculate_tier_price(self, quantity):
        """Calculate price using tier-based process"""
        tier = self.process.tiers.filter(
            quantity_from__lte=quantity,
            quantity_to__gte=quantity
        ).first()
        
        if tier:
            cost = tier.cost
            margin_multiplier = 1 + (self.default_margin / 100)
            return cost * margin_multiplier
        return self.base_cost
    
    def _calculate_formula_price(self, quantity, selected_options):
        """Calculate price using formula-based process"""
        # This would evaluate the formula with the selected options
        # Implementation depends on your formula structure
        pass
    
    def _calculate_custom_price(self, quantity, selected_options):
        """Calculate price using custom product pricing"""
        # Your existing custom pricing logic
        pass
```

---

## Implementation Steps (Recommended Order)

### ✅ Step 1: Database Changes (30 minutes)
1. Add `process` field to `ProductPricing` model
2. Add `source_process_variable` field to `ProductVariable` model
3. Run migrations
4. Test in Django admin

### ✅ Step 2: UI Changes (1-2 hours)
1. Add process selection dropdown to product create/edit form
2. Add JavaScript for process selection handling
3. Add process info display section
4. Test UI interactions

### ✅ Step 3: Backend Changes (2-3 hours)
1. Update `product_create` view to pass processes
2. Create `import_process_variables_to_product` helper function
3. Create AJAX endpoint for fetching process variables
4. Update URL patterns

### ✅ Step 4: Testing & Refinement (1-2 hours)
1. Create a test process in the costing system
2. Create a test product and link it to the process
3. Verify variables are imported correctly
4. Test pricing calculations
5. Fix any issues

### ✅ Step 5: Documentation (30 minutes)
1. Document the workflow for production team
2. Create video tutorial if needed
3. Update user guides

---

## Usage Workflow (After Implementation)

### For Production Team:

1. **Create Costing Process** (processes/create)
   - Define process name and details
   - Choose tier-based or formula-based pricing
   - Set up costs and variables
   - Link vendors
   - Save and activate

2. **Create Product** (product/create)
   - Fill out general information
   - Go to "Pricing & Variables" tab
   - **Select the costing process** from dropdown
   - Check "Auto-import variables" if you want to use process variables
   - System auto-populates:
     - Base costs from process
     - Variables from process
     - Vendor information
   - Review and adjust if needed
   - Save and publish

3. **Product Pricing is Now Connected!**
   - Customer selections on the product page will use the costs from the process
   - Changes to the process costs can be reflected in product pricing
   - You have a single source of truth for costs

---

## Benefits of This Approach

✅ **Single Source of Truth**: Process costs drive product pricing
✅ **Consistency**: All products using the same process have consistent costing
✅ **Efficiency**: No need to manually copy costs from processes to products
✅ **Flexibility**: Can still override process costs if needed (via `use_process_costs` flag)
✅ **Traceability**: Can track which process is used for each product

---

## Alternative: Simpler Approach (If You Want to Start Small)

If the above seems too complex, you can start with a simpler approach:

1. **Just add a text field** to link process name to product (no foreign key)
2. **Manually copy** process costs to product pricing
3. **Document the relationship** in internal notes

But this won't give you the automatic linking and cost updates!

---

## Questions to Consider

Before implementing, please answer:

1. **Should product pricing auto-update when process costs change?**
   - Yes → Use foreign key with `use_process_costs=True`
   - No → Just copy costs once during product creation

2. **Should one product be able to use multiple processes?**
   - Yes → Use ManyToMany relationship instead of ForeignKey
   - No → Use ForeignKey as shown above

3. **Should process variables become product variables automatically?**
   - Yes → Implement auto-import function
   - No → Just show process info as reference

4. **Do you want to restrict products to only use processes?**
   - Yes → Make `process` field required
   - No → Keep it optional (as shown above)

---

## Next Steps

**Please review this plan and let me know:**
1. Does this approach make sense for your workflow?
2. Any changes you'd like to the proposed solution?
3. Should I proceed with generating the actual file changes?

I'm ready to implement any of these changes once you approve the approach!
