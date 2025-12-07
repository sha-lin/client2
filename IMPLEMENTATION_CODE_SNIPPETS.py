# IMPLEMENTATION GUIDE: Process-Product Integration
# =================================================
# This file contains all the code changes needed to integrate the Process/Costing system
# with the Product Pricing system. Copy and paste these changes into your files.

## ===========================================
## STEP 1: Database Migration (Already Done!)
## ===========================================
# The models.py file has been updated with:
# - process field in ProductPricing
# - source_process_variable field in ProductVariable

# TO CREATE MIGRATION:
# 1. Stop the runserver ( Ctrl+C in terminal)
# 2. Run: python manage.py makemigrations clientapp --name add_process_integration
# 3. Run: python manage.py migrate
# 4. Restart server: python manage.py runserver


## ===========================================
## STEP 2: UI Changes - product_create_edit.html
## ===========================================

# LOCATION: Insert this HTML after the "Base Pricing Information" section (after line 561)
# FIND THE COMMENT: <!-- Production & Vendor Information -->
# INSERT THIS BEFORE THAT COMMENT:

"""
    <!-- ========== NEW SECTION: Process & Costing Integration ========== -->
    <div class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h3 class="text-base font-semibold text-gray-900 mb-6">
            <i data-lucide="settings" class="w-5 h-5 inline-block mr-2"></i>
            Process & Costing
        </h3>

        <div class="space-y-4">
            <!-- Process Selection Dropdown -->
            <div>
                <label class="block text-sm font-medium text-gray-900 mb-2">
                    Select Costing Process
                    <span class="text-gray-500 font-normal">(Optional)</span>
                </label>
                <select name="process" id="id_process"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="">-- No Process (Manual Pricing) --</option>
                    {% for process in processes %}
                    <option value="{{ process.id }}" 
                        data-pricing-type="{{ process.pricing_type }}"
                        data-category="{{ process.get_category_display }}"
                        data-lead-time="{{ process.standard_lead_time }}"
                        data-process-id="{{ process.process_id }}"
                        {% if product and product.pricing and product.pricing.process_id == process.id %}selected{% endif %}>
                        {{ process.process_id }} - {{ process.process_name }} ({{ process.get_pricing_type_display }})
                    </option>
                    {% endfor %}
                </select>
                <p class="text-xs text-gray-500 mt-1">
                    <i data-lucide="info" class="w-3 h-3 inline"></i>
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
                <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <i data-lucide="file-text" class="w-4 h-4"></i>
                    Process Information
                </h4>
                <div class="grid grid-cols-4 gap-4 text-sm">
                    <div>
                        <span class="text-gray-600">Process ID:</span>
                        <span id="process_id_display" class="font-medium text-gray-900 ml-2 block mt-1">-</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Pricing Type:</span>
                        <span id="process_pricing_type" class="font-medium text-gray-900 ml-2 block mt-1">-</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Lead Time:</span>
                        <span id="process_lead_time" class="font-medium text-gray-900 ml-2 block mt-1">-</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Category:</span>
                        <span id="process_category" class="font-medium text-gray-900 ml-2 block mt-1">-</span>
                    </div>
                </div>
                
                <!-- Process Variables Preview -->
                <div id="process-variables-preview" class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md hidden">
                    <h5 class="text-sm font-semibold text-blue-900 mb-2">Process Variables:</h5>
                    <div id="variables-list" class="text-sm text-blue-800">
                        <!-- Will be populated by JavaScript -->
                    </div>
                </div>

                <!-- Button to View Full Process Details -->
                <div class="mt-3">
                    <a id="view_process_link" href="#" target="_blank" 
                        class="text-sm text-blue-600 hover:text-blue-800 inline-flex items-center gap-2">
                        <i data-lucide="external-link" class="w-3 h-3"></i>
                        View Full Process Details
                    </a>
                </div>
            </div>
        </div>
    </div>
    <!-- ========== END NEW SECTION ========== -->
"""


## ===========================================
## STEP 3: JavaScript for Process Selection
## ===========================================

# LOCATION: Add this script at the bottom of product_create_edit.html
# BEFORE THE CLOSING </div> {% endblock %} tags

"""
<script>
// ========== Process Selection Handler ==========
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
                const processId = selectedOption.getAttribute('data-process-id');
                const leadTime = selectedOption.getAttribute('data-lead-time');
                const category = selectedOption.getAttribute('data-category');
                
                document.getElementById('process_id_display').textContent = processId || '-';
                document.getElementById('process_pricing_type').textContent = 
                    pricingType === 'tier' ? 'Tier-Based' : pricingType === 'formula' ? 'Formula-Based' : '-';
                document.getElementById('process_lead_time').textContent = 
                    leadTime ? leadTime + ' days' : '-';
                document.getElementById('process_category').textContent = category || '-';
                
                // Update view process link
                document.getElementById('view_process_link').href = 
                    `/process/${this.value}/view/`;
                
                // Enable auto-import checkbox
                autoImportCheckbox.disabled = false;
                
                // Fetch process variables
                fetchProcessVariables(this.value);
                
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
                console.log('Auto-import enabled for process:', processSelect.value);
                // Will be handled on form submission
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
                displayProcessVariables(data.variables, data.pricing_type);
            } else {
                console.error('Error fetching process variables:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching process variables:', error);
        });
}

function displayProcessVariables(variables, pricingType) {
    const previewDiv = document.getElementById('process-variables-preview');
    const variablesList = document.getElementById('variables-list');
    
    if (variables && variables.length > 0) {
        previewDiv.classList.remove('hidden');
        
        let html = '<ul class="space-y-1">';
        variables.forEach(v => {
            if (pricingType === 'tier') {
                html += `<li>• Tier ${v.tier_number}: ${v.quantity_from}-${v.quantity_to} pcs (Cost: KES ${v.cost})</li>`;
            } else {
                html += `<li>• ${v.name} ${v.unit ? '(' + v.unit + ')' : ''}</li>`;
            }
        });
        html += '</ul>';
        
        variablesList.innerHTML = html;
    } else {
        previewDiv.classList.add('hidden');
    }
}
</script>
"""


## ===========================================
## STEP 4: Backend Views Changes
## ===========================================

# FILE: clientapp/views.py
# LOCATION: In the product_create function (around line 3042)

# ADD THIS IMPORT AT THE TOP OF THE FILE:
"""
from .models import Process, ProcessVariable, ProcessTier
"""

# MODIFY THE product_create VIEW:
"""
def product_create(request):
    # ... existing code ...
    
    # ADD THIS: Get all active processes
    processes = Process.objects.filter(status='active').order_by('process_name')
    
    if request.method == 'POST':
        # ... existing form handling ...
        
        # ADD THIS: Handle process selection
        process_id = request.POST.get('process')
        auto_import = request.POST.get('auto_import_variables') == 'on'
        
        if process_id:
            try:
                process = Process.objects.get(id=process_id)
                # Link the process to product pricing
                if hasattr(product, 'pricing'):
                    product.pricing.process = process
                    product.pricing.save()
                    messages.success(request, f'Linked to process: {process.process_name}')
                
                # Auto-import variables if requested
                if auto_import:
                    imported_count = import_process_variables_to_product(process, product)
                    if imported_count > 0:
                        messages.success(request, f'Imported {imported_count} variables from process')
                    
            except Process.DoesNotExist:
                messages.warning(request, 'Selected process not found')
    
    context = {
        # ... existing context ...
        'processes': processes,  # ADD THIS LINE
    }
    
    return render(request, 'product_create_edit.html', context)
"""

# ADD THIS NEW HELPER FUNCTION (anywhere in views.py):
"""
def import_process_variables_to_product(process, product):
    \"\"\"
    Import variables from a Process to a Product
    Returns the number of variables imported
    \"\"\"
    imported_count = 0
    
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
                    pricing_type='increment',
                    source_process_variable=pv,
                    display_order=pv.order
                )
                imported_count += 1
                
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
                    name=f"{tier.quantity_from}-{tier.quantity_to} pieces",
                    display_order=i,
                    price_modifier=tier.price
                )
            imported_count += 1
    
    return imported_count
"""

# ADD THIS NEW AJAX VIEW (anywhere in views.py):
"""
from django.http import JsonResponse

def ajax_process_variables(request, process_id):
    \"\"\"
    AJAX endpoint to fetch process variables
    \"\"\"
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
"""


## ===========================================
## STEP 5: URL Configuration
## ===========================================

# FILE: clientapp/urls.py
# ADD THIS LINE TO THE urlpatterns list:

"""
path('ajax/process/<int:process_id>/variables/', ajax_process_variables, name='ajax_process_variables'),
"""


## ===========================================
## SUMMARY OF FILES TO MODIFY
## ===========================================

1. ✅ models.py - ALREADY DONE (process fields added)
2. ⬜ product_create_edit.html - Copy HTML section above
3. ⬜ product_create_edit.html - Copy JavaScript section above  
4. ⬜ views.py - Add imports and modify product_create function
5. ⬜ views.py - Add helper functions
6. ⬜ urls.py - Add AJAX URL pattern


## ===========================================
## MIGRATION INSTRUCTIONS
## ===========================================

After making all changes:

1. Stop the Django server (Ctrl+C in terminal)
2. Run: python manage.py makemigrations clientapp --name add_process_integration
3. Run: python manage.py migrate
4. Restart server: python manage.py runserver
5. Test by creating a new product and selecting a process!


## ===========================================
## TESTING CHECKLIST
## ===========================================

[ ] 1. Create a test process in /processes/create
[ ] 2. Go to product create page
[ ] 3. Navigate to "Pricing & Variables" tab
[ ] 4. See "Process & Costing" section
[ ] 5. Select your test process from dropdown
[ ] 6. See process information display
[ ] 7. Check "Auto-import variables"
[ ] 8. Save product
[ ] 9. Verify variables were imported
[ ] 10. Check product pricing is linked to process


## NEED HELP?
If you encounter any errors, check:
- Migration ran successfully
- All imports are at top of views.py
- URL pattern added to urls.py
- Process dropdown shows processes (check processes exist in database)

