/**
 * Quote Create/Edit Page JavaScript
 * Handles product search, pricing calculation, line items, and form submission
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // STATE MANAGEMENT
    // ============================================================

    let lineItems = [];
    let lineItemCounter = 0;
    let selectedClient = null;
    let selectedLead = null;

    // Tax rate (VAT in Kenya is 16%)
    const TAX_RATE = 16;

    // ============================================================
    // CLIENT/LEAD SELECTION
    // ============================================================

    const clientSelect = document.getElementById('client-select') || document.querySelector('select[name="client"]');
    const leadSelect = document.getElementById('lead-select') || document.querySelector('select[name="lead"]');
    const quoteTypeRadios = document.querySelectorAll('input[name="quote_type"]');

    // Handle quote type toggle (client vs lead)
    quoteTypeRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            const clientSection = document.getElementById('client-section');
            const leadSection = document.getElementById('lead-section');

            if (this.value === 'client') {
                if (clientSection) clientSection.style.display = 'block';
                if (leadSection) leadSection.style.display = 'none';
                selectedLead = null;
            } else {
                if (clientSection) clientSection.style.display = 'none';
                if (leadSection) leadSection.style.display = 'block';
                selectedClient = null;
            }
        });
    });

    // Client selection change handler
    if (clientSelect) {
        clientSelect.addEventListener('change', async function () {
            const clientId = this.value;
            if (clientId) {
                try {
                    const client = await api.get(`/clients/${clientId}/`);
                    selectedClient = client;
                    updateClientInfo(client);
                } catch (error) {
                    console.error('Error fetching client:', error);
                }
            }
        });
    }

    function updateClientInfo(client) {
        const infoDiv = document.getElementById('client-info');
        if (infoDiv) {
            infoDiv.innerHTML = `
                <div class="bg-gray-50 rounded-lg p-3 text-sm">
                    <p class="font-medium">${client.name}</p>
                    <p class="text-gray-600">${client.email || ''}</p>
                    <p class="text-gray-600">${client.phone || ''}</p>
                    <span class="inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium ${client.client_type === 'B2B' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}">
                        ${client.client_type}
                    </span>
                </div>
            `;
        }
    }

    // ============================================================
    // PRODUCT SEARCH
    // ============================================================

    const productSearchInput = document.getElementById('product-search');
    const searchResultsContainer = document.getElementById('product-search-results');

    if (productSearchInput) {
        productSearchInput.addEventListener('input', debounce(async function () {
            const query = this.value.trim();

            if (query.length < 2) {
                hideSearchResults();
                return;
            }

            try {
                const products = await searchProducts(query);
                displaySearchResults(products);
            } catch (error) {
                console.error('Error searching products:', error);
            }
        }, 300));

        // Show all products when focused
        productSearchInput.addEventListener('focus', async function () {
            if (this.value.trim().length < 2) {
                try {
                    const data = await api.get('/products/?status=published&page_size=20');
                    displaySearchResults(data.results || []);
                } catch (error) {
                    console.error('Error loading products:', error);
                }
            }
        });
    }

    function displaySearchResults(products) {
        if (!searchResultsContainer) return;

        if (products.length === 0) {
            searchResultsContainer.innerHTML = `
                <div class="p-4 text-center text-gray-500 text-sm">
                    No products found
                </div>
            `;
            searchResultsContainer.style.display = 'block';
            return;
        }

        const html = products.map(product => `
            <div class="product-result p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-0" 
                 data-product-id="${product.id}"
                 data-product-name="${product.name}"
                 data-product-sku="${product.sku || product.internal_code || ''}"
                 data-product-price="${product.base_price || product.selling_price || 0}"
                 data-customization="${product.customization_level || 'none'}">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="font-medium text-gray-900">${product.name}</p>
                        <p class="text-xs text-gray-500">${product.sku || product.internal_code || 'No SKU'}</p>
                        ${product.customization_level ? `<span class="inline-block mt-1 px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-700">${product.customization_level}</span>` : ''}
                    </div>
                    <div class="text-right">
                        <p class="font-semibold text-gray-900">${formatCurrency(product.base_price || product.selling_price || 0)}</p>
                        <p class="text-xs text-gray-500">per unit</p>
                    </div>
                </div>
            </div>
        `).join('');

        searchResultsContainer.innerHTML = html;
        searchResultsContainer.style.display = 'block';

        // Add click handlers
        searchResultsContainer.querySelectorAll('.product-result').forEach(item => {
            item.addEventListener('click', function () {
                selectProduct({
                    id: this.dataset.productId,
                    name: this.dataset.productName,
                    sku: this.dataset.productSku,
                    price: parseFloat(this.dataset.productPrice) || 0,
                    customization: this.dataset.customization
                });
            });
        });
    }

    function hideSearchResults() {
        if (searchResultsContainer) {
            searchResultsContainer.style.display = 'none';
        }
    }

    // Close search results when clicking outside
    document.addEventListener('click', function (e) {
        if (!e.target.closest('#product-search') && !e.target.closest('#product-search-results')) {
            hideSearchResults();
        }
    });

    // ============================================================
    // LINE ITEM MANAGEMENT
    // ============================================================

    function selectProduct(product) {
        hideSearchResults();
        productSearchInput.value = '';
        addLineItem(product);
    }

    function addLineItem(product) {
        lineItemCounter++;

        const lineItem = {
            id: lineItemCounter,
            product_id: product.id,
            product_name: product.name,
            product_sku: product.sku,
            quantity: 1,
            unit_price: product.price,
            discount_percent: 0,
            variable_amount: 0,  // Additional charges (rush, customization, etc.)
            line_total: product.price,
            specifications: {},
            customization: product.customization
        };

        lineItems.push(lineItem);
        renderLineItems();
        updateTotals();

        showToast(`Added: ${product.name}`, 'success');
    }

    function renderLineItems() {
        const container = document.getElementById('line-items-container');
        if (!container) return;

        if (lineItems.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="w-12 h-12 mx-auto text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <p>No items added yet</p>
                    <p class="text-sm">Search for products above to add them to this quote</p>
                </div>
            `;
            return;
        }

        const html = lineItems.map((item, index) => `
            <div class="line-item bg-white border border-gray-200 rounded-lg p-4 mb-3" data-line-id="${item.id}">
                <div class="flex justify-between items-start gap-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="text-xs font-medium text-gray-400">#${index + 1}</span>
                            <h4 class="font-medium text-gray-900">${item.product_name}</h4>
                            <span class="text-xs text-gray-500">${item.product_sku || ''}</span>
                        </div>
                        
                        <div class="grid grid-cols-5 gap-3 mt-3">
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Quantity</label>
                                <input type="number" 
                                       class="form-input py-2" 
                                       value="${item.quantity}" 
                                       min="1"
                                       data-field="quantity"
                                       data-line-id="${item.id}">
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Unit Price</label>
                                <input type="number" 
                                       class="form-input py-2" 
                                       value="${item.unit_price.toFixed(2)}" 
                                       step="0.01"
                                       data-field="unit_price"
                                       data-line-id="${item.id}">
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Variable Cost</label>
                                <input type="number" 
                                       class="form-input py-2" 
                                       value="${(item.variable_amount || 0).toFixed(2)}" 
                                       step="0.01"
                                       min="0"
                                       data-field="variable_amount"
                                       data-line-id="${item.id}"
                                       title="Additional charges (rush, customization, etc.)">
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Discount %</label>
                                <input type="number" 
                                       class="form-input py-2" 
                                       value="${item.discount_percent}" 
                                       min="0" 
                                       max="100"
                                       data-field="discount_percent"
                                       data-line-id="${item.id}">
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Line Total</label>
                                <div class="form-input py-2 bg-gray-50 font-semibold" data-total-id="${item.id}">
                                    ${formatCurrency(item.line_total)}
                                </div>
                            </div>
                        </div>
                        
                        ${item.customization !== 'none' ? `
                        <div class="mt-3">
                            <button type="button" class="text-sm text-blue-600 hover:text-blue-800" data-action="configure" data-line-id="${item.id}">
                                + Add Specifications
                            </button>
                        </div>
                        ` : ''}
                    </div>
                    
                    <button type="button" 
                            class="text-gray-400 hover:text-red-600 p-1" 
                            data-action="remove" 
                            data-line-id="${item.id}"
                            title="Remove item">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;

        // Attach event handlers
        attachLineItemHandlers();
    }

    function attachLineItemHandlers() {
        // Quantity, price, discount changes
        document.querySelectorAll('[data-field]').forEach(input => {
            input.addEventListener('change', function () {
                const lineId = parseInt(this.dataset.lineId);
                const field = this.dataset.field;
                const value = parseFloat(this.value) || 0;

                updateLineItem(lineId, field, value);
            });
        });

        // Remove button
        document.querySelectorAll('[data-action="remove"]').forEach(btn => {
            btn.addEventListener('click', function () {
                const lineId = parseInt(this.dataset.lineId);
                removeLineItem(lineId);
            });
        });

        // Configure specifications
        document.querySelectorAll('[data-action="configure"]').forEach(btn => {
            btn.addEventListener('click', function () {
                const lineId = parseInt(this.dataset.lineId);
                openSpecificationsModal(lineId);
            });
        });
    }

    function updateLineItem(lineId, field, value) {
        const item = lineItems.find(i => i.id === lineId);
        if (!item) return;

        item[field] = value;

        // Recalculate line total with variable_amount
        item.line_total = calculateLineTotal(
            item.unit_price, 
            item.quantity, 
            item.discount_percent,
            item.variable_amount || 0
        );

        // Update display
        const totalDisplay = document.querySelector(`[data-total-id="${lineId}"]`);
        if (totalDisplay) {
            totalDisplay.textContent = formatCurrency(item.line_total);
        }

        updateTotals();
    }

    function removeLineItem(lineId) {
        const item = lineItems.find(i => i.id === lineId);
        if (item && confirm(`Remove "${item.product_name}" from quote?`)) {
            lineItems = lineItems.filter(i => i.id !== lineId);
            renderLineItems();
            updateTotals();
            showToast('Item removed', 'info');
        }
    }

    // ============================================================
    // TOTALS CALCULATION
    // ============================================================

    function updateTotals() {
        const adjustmentAmount = parseFloat(document.querySelector('input[name="adjustment_amount"]')?.value || 0);
        const totals = calculateQuoteTotals(
            lineItems, 
            TAX_RATE, 
            getShippingCost(),
            adjustmentAmount
        );

        // Update UI - display elements
        const subtotalDisplay = document.getElementById('subtotal-display');
        const discountDisplay = document.getElementById('discount-display');
        const taxDisplay = document.getElementById('tax-display');
        const shippingDisplay = document.getElementById('shipping-display');
        const totalDisplay = document.getElementById('total-display');

        if (subtotalDisplay) subtotalDisplay.textContent = formatCurrency(totals.subtotal);
        if (discountDisplay) discountDisplay.textContent = formatCurrency(totals.discountTotal);
        if (taxDisplay) taxDisplay.textContent = formatCurrency(totals.taxAmount);
        if (shippingDisplay) shippingDisplay.textContent = formatCurrency(totals.shippingCost);
        if (totalDisplay) totalDisplay.textContent = formatCurrency(totals.total);

        // Update hidden fields for form submission
        const subtotalInput = document.querySelector('input[name="subtotal"]');
        const discountInput = document.querySelector('input[name="discount_total"]');
        const taxInput = document.querySelector('input[name="tax_total"]');
        const totalInput = document.querySelector('input[name="total_amount"]');

        if (subtotalInput) subtotalInput.value = totals.subtotal.toFixed(2);
        if (discountInput) discountInput.value = totals.discountTotal.toFixed(2);
        if (taxInput) taxInput.value = totals.taxAmount.toFixed(2);
        if (totalInput) totalInput.value = totals.total.toFixed(2);

        console.log('Quote totals updated:', totals);
    }

    function getShippingCost() {
        const shippingInput = document.querySelector('input[name="shipping_charges"]');
        return shippingInput ? parseFloat(shippingInput.value) || 0 : 0;
    }

    // Shipping and adjustment cost change handlers
    const shippingInput = document.querySelector('input[name="shipping_charges"]');
    if (shippingInput) {
        shippingInput.addEventListener('change', updateTotals);
    }

    const adjustmentInput = document.querySelector('input[name="adjustment_amount"]');
    if (adjustmentInput) {
        adjustmentInput.addEventListener('change', updateTotals);
    }

    const taxRateInput = document.querySelector('input[name="tax_rate"]');
    if (taxRateInput) {
        taxRateInput.addEventListener('change', function () {
            // Update TAX_RATE constant if user modifies it
            window.TAX_RATE = parseFloat(this.value) || 16;
            updateTotals();
        });
    }

    // ============================================================
    // FORM SUBMISSION
    // ============================================================

    const quoteForm = document.getElementById('quote-form');

    if (quoteForm) {
        quoteForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            // Get the action button that was clicked
            const action = e.submitter?.value || 'save_draft';
            
            // Validation
            if (lineItems.length === 0) {
                showToast('Please add at least one product to the quote', 'error');
                return;
            }

            // Get client/lead selection from form
            const clientNameInput = document.querySelector('select[name="client_name"]');
            const clientNameValue = clientNameInput?.value || '';
            let clientId = null;
            let leadId = null;

            // Parse client_name value (format: "client-{id}" or "lead-{id}")
            if (clientNameValue) {
                if (clientNameValue.startsWith('client-')) {
                    clientId = parseInt(clientNameValue.split('-')[1]);
                } else if (clientNameValue.startsWith('lead-')) {
                    leadId = parseInt(clientNameValue.split('-')[1]);
                }
            }

            // Validation: ensure client or lead is selected
            if (!clientId && !leadId) {
                showToast('Please select a customer (Client or Lead)', 'error');
                return;
            }

            const submitBtn = e.submitter;
            const originalText = submitBtn?.textContent || 'Save';
            if (submitBtn) {
                submitBtn.textContent = 'Saving...';
                submitBtn.disabled = true;
            }

            showLoading('Creating quote...');

            try {
                // Build quote data matching backend API expectations
                const quoteData = {
                    client: clientId,                    // Client ID or null
                    lead: leadId,                        // Lead ID or null
                    status: action === 'save_draft' ? 'Draft' : 'Draft',  // API handles status
                    notes: document.querySelector('textarea[name="notes"]')?.value || '',
                    custom_terms: document.querySelector('textarea[name="terms"]')?.value || '',
                    shipping_charges: parseFloat(document.querySelector('input[name="shipping_charges"]')?.value || 0),
                    adjustment_amount: parseFloat(document.querySelector('input[name="adjustment_amount"]')?.value || 0),
                    adjustment_reason: document.querySelector('input[name="adjustment_reason"]')?.value || '',
                    reference_number: document.querySelector('input[name="reference_number"]')?.value || '',
                    payment_terms: document.querySelector('select[name="payment_terms"]')?.value || 'Prepaid',
                    tax_rate: parseFloat(document.querySelector('input[name="tax_rate"]')?.value || 16),
                    
                    // Line items - CRITICAL: must match backend expectations
                    line_items: lineItems.map((item, index) => ({
                        product: parseInt(item.product_id),
                        product_name: item.product_name,
                        quantity: parseInt(item.quantity) || 1,
                        unit_price: parseFloat(item.unit_price) || 0,
                        discount_amount: parseFloat(item.discount_percent) || 0,
                        discount_type: 'percent',  // Frontend currently supports percent only
                        variable_amount: parseFloat(item.variable_amount || 0),
                        customization_level_snapshot: item.customization || 'fixed_price',
                        base_price_snapshot: parseFloat(item.unit_price) || 0,
                        order: index
                    }))
                };

                console.log('Sending quote data to API:', quoteData);

                // Create quote via API
                const response = await api.post('/quotes/', quoteData);

                hideLoading();
                console.log('Quote created successfully:', response);
                showToast(`Quote ${response.quote_id} created successfully!`, 'success');

                // Clear draft from localStorage
                localStorage.removeItem('quote_draft');

                // Handle different actions
                if (action === 'save_draft') {
                    // Redirect to quote detail
                    setTimeout(() => {
                        window.location.href = `/quotes/${response.quote_id}/`;
                    }, 1500);
                } else if (action === 'save_send_pt') {
                    // Send to production team for costing
                    await sendQuoteToPT(response.quote_id);
                } else if (action === 'send_to_customer') {
                    // Send to customer
                    await sendQuoteToCustomer(response.quote_id);
                }

            } catch (error) {
                hideLoading();
                if (submitBtn) {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }

                console.error('Error creating quote:', error);

                // Handle detailed error response
                if (error.data) {
                    let errorMessage = 'Please fix the following errors:\n\n';
                    
                    // Handle both object and array error responses
                    if (typeof error.data === 'object') {
                        Object.keys(error.data).forEach(field => {
                            const fieldErrors = Array.isArray(error.data[field]) 
                                ? error.data[field].join(', ') 
                                : error.data[field];
                            errorMessage += `${field}: ${fieldErrors}\n`;
                        });
                    } else {
                        errorMessage = error.data;
                    }
                    
                    showToast(errorMessage, 'error');
                } else if (error.status === 400) {
                    showToast('Invalid data. Please check all fields and try again.', 'error');
                } else if (error.status === 401) {
                    showToast('Your session has expired. Please log in again.', 'error');
                } else if (error.status === 403) {
                    showToast('You do not have permission to create quotes.', 'error');
                } else {
                    showToast('Error creating quote. Please try again. ' + (error.message || ''), 'error');
                }
            }
        });
    }

    // ============================================================
    // SEND TO PRODUCTION TEAM
    // ============================================================

    async function sendQuoteToPT(quoteId) {
        try {
            // Call API to send quote to production team
            await api.post(`/quotes/${quoteId}/send_to_pt_for_review/`, {});
            showToast('Quote sent to Production Team for costing', 'success');
            
            setTimeout(() => {
                window.location.href = `/quotes/${quoteId}/`;
            }, 1500);
        } catch (error) {
            showToast('Error sending quote to Production Team', 'error');
            console.error('Error:', error);
        }
    }

    // ============================================================
    // SEND TO CUSTOMER
    // ============================================================

    async function sendQuoteToCustomer(quoteId) {
        try {
            // Call API to send quote to customer
            await api.post(`/quotes/${quoteId}/send_to_customer/`, {});
            showToast('Quote sent to customer via email', 'success');
            
            setTimeout(() => {
                window.location.href = `/quotes/${quoteId}/`;
            }, 1500);
        } catch (error) {
            showToast('Error sending quote to customer', 'error');
            console.error('Error:', error);
        }
    }

    // ============================================================
    // SAVE AS DRAFT (Auto-save)
    // ============================================================

    let autoSaveTimeout = null;

    function scheduleAutoSave() {
        if (autoSaveTimeout) clearTimeout(autoSaveTimeout);

        autoSaveTimeout = setTimeout(async () => {
            if (lineItems.length > 0) {
                await saveDraft();
            }
        }, 30000); // Auto-save every 30 seconds
    }

    async function saveDraft() {
        try {
            const formData = formToJson(quoteForm);

            const draftData = {
                client: formData.client || null,
                lead: formData.lead || null,
                notes: formData.notes || '',
                status: 'Draft',
                line_items: lineItems
            };

            // Save to local storage as backup
            localStorage.setItem('quote_draft', JSON.stringify(draftData));

            console.log('Draft saved locally');

        } catch (error) {
            console.error('Error saving draft:', error);
        }
    }

    // Restore draft on page load
    function restoreDraft() {
        const savedDraft = localStorage.getItem('quote_draft');
        if (savedDraft) {
            try {
                const draft = JSON.parse(savedDraft);

                if (draft.line_items && draft.line_items.length > 0) {
                    if (confirm('You have an unsaved quote draft. Would you like to restore it?')) {
                        lineItems = draft.line_items;
                        lineItemCounter = Math.max(...lineItems.map(i => i.id), 0);
                        renderLineItems();
                        updateTotals();
                        showToast('Draft restored', 'info');
                    } else {
                        localStorage.removeItem('quote_draft');
                    }
                }
            } catch (error) {
                console.error('Error restoring draft:', error);
            }
        }
    }

    // Call restore on load
    restoreDraft();

    // ============================================================
    // PRICING CALCULATION (for complex products)
    // ============================================================

    async function calculatePriceWithOptions(productId, quantity, options) {
        try {
            const pricing = await getProductPrice(productId, quantity, options);
            return pricing;
        } catch (error) {
            console.error('Error calculating price:', error);
            return null;
        }
    }

    // ============================================================
    // SPECIFICATIONS MODAL
    // ============================================================

    function openSpecificationsModal(lineId) {
        const item = lineItems.find(i => i.id === lineId);
        if (!item) return;

        const modal = document.getElementById('specifications-modal');
        if (modal) {
            // Populate modal with product-specific options
            const content = modal.querySelector('.modal-content');
            content.innerHTML = `
                <h3 class="text-lg font-semibold mb-4">Specifications for ${item.product_name}</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Size/Dimensions</label>
                        <input type="text" class="form-input" name="size" placeholder="e.g., A4, 210x297mm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Paper/Material</label>
                        <input type="text" class="form-input" name="material" placeholder="e.g., 300gsm Art Card">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Colors</label>
                        <input type="text" class="form-input" name="colors" placeholder="e.g., Full Color, CMYK">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Finish</label>
                        <select class="form-select" name="finish">
                            <option value="">Select finish...</option>
                            <option value="Matte">Matte</option>
                            <option value="Gloss">Gloss</option>
                            <option value="Satin">Satin</option>
                            <option value="Uncoated">Uncoated</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Special Instructions</label>
                        <textarea class="form-textarea" name="instructions" rows="3" placeholder="Any special requirements..."></textarea>
                    </div>
                </div>
                <div class="flex justify-end gap-3 mt-6">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('specifications-modal')">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="saveSpecifications(${lineId})">Save Specifications</button>
                </div>
            `;

            // Pre-fill existing specifications
            if (item.specifications) {
                Object.entries(item.specifications).forEach(([key, value]) => {
                    const input = content.querySelector(`[name="${key}"]`);
                    if (input) input.value = value;
                });
            }

            openModal('specifications-modal');
        } else {
            showToast('Specifications feature coming soon', 'info');
        }
    }

    // Global function for modal
    window.saveSpecifications = function (lineId) {
        const item = lineItems.find(i => i.id === lineId);
        if (!item) return;

        const modal = document.getElementById('specifications-modal');
        const inputs = modal.querySelectorAll('input, select, textarea');

        const specs = {};
        inputs.forEach(input => {
            if (input.name && input.value) {
                specs[input.name] = input.value;
            }
        });

        item.specifications = specs;
        closeModal('specifications-modal');
        showToast('Specifications saved', 'success');
    };

    console.log('Quote create page initialized successfully');
});
