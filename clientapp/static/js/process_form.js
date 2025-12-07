// ============================================
// CREATE NEW FILE: clientapp/static/js/process_form.js
// ============================================

// This JavaScript handles all dynamic interactions on the process create form

document.addEventListener('DOMContentLoaded', function() {
    console.log('Process form script loaded');
    
    // ===== AUTO-GENERATE PROCESS ID =====
    const processNameInput = document.querySelector('input[name="process_name"]');
    const processIdInput = document.querySelector('input[name="process_id"]');
    
    if (processNameInput && processIdInput) {
        processNameInput.addEventListener('blur', function() {
            const name = this.value.trim();
            if (name) {
                // Call AJAX to generate process ID
                fetch(`/ajax/generate-process-id/?name=${encodeURIComponent(name)}`)
                    .then(response => response.json())
                    .then(data => {
                        processIdInput.value = data.process_id;
                    });
            }
        });
    }
    
    
    // ===== PRICING METHOD SELECTION =====
    const pricingMethodButtons = document.querySelectorAll('[data-pricing-method]');
    const tierSection = document.querySelector('[data-section="tier-pricing"]');
    const formulaSection = document.querySelector('[data-section="formula-pricing"]');
    
    pricingMethodButtons.forEach(button => {
        button.addEventListener('click', function() {
            const method = this.getAttribute('data-pricing-method');
            
            // Update button states
            pricingMethodButtons.forEach(btn => {
                btn.classList.remove('border-blue-500', 'bg-blue-50');
                btn.classList.add('border-gray-300', 'bg-white');
            });
            this.classList.remove('border-gray-300', 'bg-white');
            this.classList.add('border-blue-500', 'bg-blue-50');
            
            // Show/hide sections
            if (method === 'tier') {
                if (tierSection) tierSection.style.display = 'block';
                if (formulaSection) formulaSection.style.display = 'none';
            } else if (method === 'formula') {
                if (tierSection) tierSection.style.display = 'none';
                if (formulaSection) formulaSection.style.display = 'block';
            }
        });
    });
    
    
    // ===== TIER MARGIN CALCULATION =====
    // Auto-calculate margin when price or cost changes
    function setupTierCalculations() {
        const tiers = document.querySelectorAll('[data-tier]');
        
        tiers.forEach(tier => {
            const priceInput = tier.querySelector('[name*="_price"]');
            const costInput = tier.querySelector('[name*="_cost"]');
            const marginDisplay = tier.querySelector('[data-margin-display]');
            
            if (priceInput && costInput && marginDisplay) {
                const calculateMargin = () => {
                    const price = parseFloat(priceInput.value) || 0;
                    const cost = parseFloat(costInput.value) || 0;
                    
                    if (price > 0) {
                        // Call AJAX to get calculation
                        fetch(`/ajax/calculate-margin/?price=${price}&cost=${cost}`)
                            .then(response => response.json())
                            .then(data => {
                                if (!data.error) {
                                    marginDisplay.innerHTML = `
                                        <span class="font-semibold text-${data.color}-600">
                                            ${data.margin_amount.toLocaleString()} KES (${data.margin_percentage.toFixed(1)}%)
                                        </span>
                                        <span class="inline-flex items-center gap-1 text-${data.color}-600">
                                            ${data.status === 'above' ? '✅' : data.status === 'below' ? '❌' : '⚠️'}
                                            ${data.message}
                                        </span>
                                    `;
                                }
                            });
                    }
                };
                
                priceInput.addEventListener('input', calculateMargin);
                costInput.addEventListener('input', calculateMargin);
                
                // Calculate on load if values exist
                if (priceInput.value && costInput.value) {
                    calculateMargin();
                }
            }
        });
    }
    
    setupTierCalculations();
    
    
    // ===== ADD/REMOVE TIERS =====
    let tierCount = 3; // Start after the initial 3 tiers
    
    const addTierButton = document.querySelector('[data-action="add-tier"]');
    if (addTierButton) {
        addTierButton.addEventListener('click', function() {
            tierCount++;
            
            // Create new tier card HTML
            const tierHTML = `
                <div class="border border-red-300 rounded-lg p-5 mb-4 bg-red-50 relative" data-tier="${tierCount}">
                    <button type="button" class="absolute top-3 right-3 text-red-500 hover:text-red-700" data-action="remove-tier">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                    
                    <h4 class="font-semibold text-red-700 mb-4">TIER ${tierCount}</h4>
                    
                    <div class="mb-4">
                        <label class="block font-medium mb-2">Quantity Range:</label>
                        <div class="flex items-center gap-2">
                            <span class="text-sm text-gray-600">From:</span>
                            <input type="number" name="tier${tierCount}_from" class="border border-gray-300 rounded px-3 py-2 w-24" value="">
                            <span class="text-sm text-gray-600">To:</span>
                            <input type="number" name="tier${tierCount}_to" class="border border-gray-300 rounded px-3 py-2 w-24" value="">
                            <span class="text-gray-600">pieces</span>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <label class="block font-medium mb-2">Price:</label>
                        <div class="flex items-center gap-2">
                            <input type="number" name="tier${tierCount}_price" class="border border-gray-300 rounded px-3 py-2 w-32" value="">
                            <span class="text-gray-600">KES</span>
                        </div>
                    </div>
                    
                    <div>
                        <label class="block font-medium mb-2">Cost:</label>
                        <div class="flex items-center gap-2 mb-2">
                            <input type="number" name="tier${tierCount}_cost" class="border border-gray-300 rounded px-3 py-2 w-32" value="">
                            <span class="text-gray-600">KES</span>
                        </div>
                        
                        <div class="mb-2">
                            <label class="block font-medium mb-1">Margin:</label>
                            <div class="flex items-center gap-3" data-margin-display>
                                <span class="font-semibold text-gray-600">Enter price and cost above</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Insert before the "Add Another Tier" button
            addTierButton.insertAdjacentHTML('beforebegin', tierHTML);
            
            // Re-setup calculations for new tier
            setupTierCalculations();
            setupRemoveButtons();
        });
    }
    
    
    // ===== REMOVE TIER =====
    function setupRemoveButtons() {
        const removeButtons = document.querySelectorAll('[data-action="remove-tier"]');
        removeButtons.forEach(button => {
            button.addEventListener('click', function() {
                if (confirm('Are you sure you want to remove this tier?')) {
                    this.closest('[data-tier]').remove();
                }
            });
        });
    }
    
    setupRemoveButtons();
    
    
    // ===== FORM VALIDATION BEFORE SUBMIT =====
    const saveActivateButton = document.querySelector('button[name="action"][value="activate"]');
    if (saveActivateButton) {
        saveActivateButton.addEventListener('click', function(e) {
            // Check required fields
            const processName = document.querySelector('input[name="process_name"]').value;
            const category = document.querySelector('input[name="category"]:checked');
            const leadTime = document.querySelector('input[name="standard_lead_time"]').value;
            
            if (!processName || !category || !leadTime) {
                e.preventDefault();
                alert('Please fill in all required fields (marked with *)');
                return false;
            }
            
            // Additional validation can go here
        });
    }
    
    
    // ===== AUTO-SAVE DRAFT (every 30 seconds) =====
    let autoSaveInterval;
    const form = document.querySelector('form');
    
    if (form) {
        autoSaveInterval = setInterval(() => {
            // Implement auto-save logic here
            console.log('Auto-saving draft...');
            // You would submit the form via AJAX with action='draft'
        }, 30000); // 30 seconds
    }
});