/**
 * Lead Intake Page JavaScript
 * Handles AJAX form submission, duplicate checking, and qualification
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // STATE
    // ============================================================

    let allProducts = [];
    let selectedProducts = [];

    // ============================================================
    // ELEMENTS
    // ============================================================

    const leadForm = document.getElementById('lead-form');
    const emailInput = document.querySelector('input[name="email"]');
    const phoneInput = document.querySelector('input[name="phone"]');
    const duplicateWarning = document.getElementById('duplicate-warning');

    const productDropdownBtn = document.getElementById('productDropdownBtn');
    const productDropdownMenu = document.getElementById('productDropdownMenu');
    const productSearch = document.getElementById('productSearch');
    const productList = document.getElementById('productList');
    const selectedProductsText = document.getElementById('selectedProductsText');
    const leadProductInterest = document.getElementById('leadProductInterest');

    // ============================================================
    // DUPLICATE LEAD CHECKING
    // ============================================================

    if (emailInput) {
        emailInput.addEventListener('input', debounce(function (e) {
            const email = e.target.value.trim();
            if (email && email.includes('@')) {
                checkForDuplicate('email', email);
            } else {
                hideDuplicateWarning();
            }
        }, 500));
    }

    if (phoneInput) {
        phoneInput.addEventListener('input', debounce(function (e) {
            const phone = e.target.value.trim();
            if (phone && phone.length >= 10) {
                checkForDuplicate('phone', phone);
            } else {
                hideDuplicateWarning();
            }
        }, 500));
    }

    async function checkForDuplicate(field, value) {
        try {
            const response = await api.get(`/leads/?${field}=${encodeURIComponent(value)}`);

            if (response.results && response.results.length > 0) {
                const existingLead = response.results[0];
                showDuplicateWarning(existingLead, field);
            } else {
                const clientResponse = await api.get(`/clients/?${field}=${encodeURIComponent(value)}`);
                if (clientResponse.results && clientResponse.results.length > 0) {
                    showExistingClientWarning(clientResponse.results[0]);
                } else {
                    hideDuplicateWarning();
                }
            }
        } catch (error) {
            console.log('Error checking duplicate:', error);
        }
    }

    function showDuplicateWarning(lead, field) {
        if (!duplicateWarning) return;

        duplicateWarning.className = 'bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4';
        duplicateWarning.innerHTML = `
            <div class="flex items-start gap-3">
                <svg class="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
                <div>
                    <h4 class="font-medium text-yellow-800">Possible Duplicate Found</h4>
                    <p class="text-sm text-yellow-700 mt-1">
                        A lead with this ${field} already exists: <strong>${lead.name}</strong> (${lead.lead_id})
                    </p>
                    <div class="mt-2 flex gap-2">
                        <a href="/leads/${lead.id}/" class="text-sm font-medium text-yellow-800 hover:text-yellow-900 underline">
                            View Existing Lead →
                        </a>
                        <button type="button" onclick="hideDuplicateWarning()" class="text-sm text-gray-600 hover:text-gray-800">
                            Continue Anyway
                        </button>
                    </div>
                </div>
            </div>
        `;
        duplicateWarning.classList.remove('hidden');
    }

    function showExistingClientWarning(client) {
        if (!duplicateWarning) return;

        duplicateWarning.className = 'bg-green-50 border border-green-200 rounded-lg p-4 mb-4';
        duplicateWarning.innerHTML = `
            <div class="flex items-start gap-3">
                <svg class="w-5 h-5 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div>
                    <h4 class="font-medium text-green-800">Existing Client Found</h4>
                    <p class="text-sm text-green-700 mt-1">
                        This contact is already a client: <strong>${client.name}</strong> (${client.client_id})
                    </p>
                    <div class="mt-2">
                        <a href="/clients/${client.id}/" class="text-sm font-medium text-green-800 hover:text-green-900 underline">
                            Go to Client Profile →
                        </a>
                    </div>
                </div>
            </div>
        `;
        duplicateWarning.classList.remove('hidden');
    }

    window.hideDuplicateWarning = function () {
        if (duplicateWarning) duplicateWarning.classList.add('hidden');
    };

    // ============================================================
    // PRODUCT INTEREST DROPDOWN
    // ============================================================

    if (productDropdownBtn) {
        productDropdownBtn.addEventListener('click', function (e) {
            e.preventDefault();
            productDropdownMenu.classList.toggle('hidden');
            if (!productDropdownMenu.classList.contains('hidden')) {
                productSearch.focus();
            }
        });
    }

    if (productSearch) {
        productSearch.addEventListener('input', function () {
            displayProductList();
        });
    }

    async function loadProducts() {
        try {
            console.log('[DEBUG] Calling api.get("/api/product-catalog/")');
            const data = await api.get('/api/product-catalog/');
            console.log('[DEBUG] API Response received:', data);
            allProducts = data.products || data.results || data;
            displayProductList();
        } catch (error) {
            console.error('Error loading products:', error);
            if (productList) {
                productList.innerHTML = '<div class="p-4 text-center text-red-500">Failed to load products</div>';
            }
        }
    }

    function displayProductList() {
        if (!productList) return;

        const searchTerm = productSearch ? productSearch.value.toLowerCase() : '';
        const filteredProducts = allProducts.filter(product =>
            product.name.toLowerCase().includes(searchTerm) ||
            (product.internal_code && product.internal_code.toLowerCase().includes(searchTerm))
        );

        if (filteredProducts.length === 0) {
            productList.innerHTML = '<div class="p-4 text-center text-gray-500">No products found</div>';
            return;
        }

        productList.innerHTML = filteredProducts.map(product => `
            <label class="flex items-center px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0">
                <input type="checkbox" 
                    value="${product.id}" 
                    data-name="${product.name}"
                    class="form-checkbox h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500" 
                    ${selectedProducts.some(p => p.id == product.id) ? 'checked' : ''}>
                <div class="ml-3">
                    <div class="text-sm text-gray-900 font-medium">${product.name}</div>
                    <div class="text-xs text-gray-500">
                        ${product.internal_code ? `Code: ${product.internal_code}` : ''}
                        ${product.base_price ? `| KES ${parseFloat(product.base_price).toLocaleString()}` : ''}
                    </div>
                </div>
            </label>
        `).join('');

        productList.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', updateProductSelection);
        });
    }

    function updateProductSelection() {
        const checkboxes = productList.querySelectorAll('input[type="checkbox"]:checked');
        selectedProducts = Array.from(checkboxes).map(cb => ({
            id: cb.value,
            name: cb.dataset.name
        }));

        if (selectedProducts.length === 0) {
            selectedProductsText.textContent = 'Select products...';
            selectedProductsText.classList.add('text-gray-500');
            selectedProductsText.classList.remove('text-gray-900');
        } else {
            selectedProductsText.textContent = selectedProducts.map(p => p.name).join(', ');
            selectedProductsText.classList.remove('text-gray-500');
            selectedProductsText.classList.add('text-gray-900');
        }

        if (leadProductInterest) {
            leadProductInterest.value = selectedProducts.map(p => p.name).join(', ');
        }
    }

    // ============================================================
    // FORM SUBMISSION
    // ============================================================

    if (leadForm) {
        leadForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Saving...';
            submitBtn.disabled = true;

            clearFormErrors();

            try {
                const formData = formToJson(this);

                if (!formData.name || !formData.phone) {
                    showToast('Please fill in Name and Phone', 'error');
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                    return;
                }

                const response = await api.post('/leads/', formData);
                showToast(`Lead ${response.lead_id} created successfully!`, 'success');

                setTimeout(() => {
                    window.location.reload();
                }, 1000);

            } catch (error) {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;

                if (error.data) {
                    showFormErrors(error.data);
                } else {
                    showToast('Error creating lead', 'error');
                }
            }
        });
    }

    // ============================================================
    // LEADS TABLE & ACTIONS
    // ============================================================

    async function loadLeads() {
        const tbody = document.getElementById('leadsTableBody');
        if (!tbody) return;

        try {
            const searchQuery = document.getElementById('searchInput')?.value || '';
            const data = await api.get(`/leads/?search=${encodeURIComponent(searchQuery)}`);
            const leads = data.results || data;

            const noLeadsMsg = document.getElementById('noLeadsMessage');

            if (!leads.length) {
                tbody.innerHTML = '';
                noLeadsMsg?.classList.remove('hidden');
                return;
            }

            noLeadsMsg?.classList.add('hidden');
            tbody.innerHTML = leads.map(lead => `
                <tr>
                    <td>${lead.lead_id || lead.id}</td>
                    <td>${lead.name}</td>
                    <td>
                        <div class="text-sm">
                            <div>${lead.email || '-'}</div>
                            <div class="text-gray-600">${lead.phone || '-'}</div>
                        </div>
                    </td>
                    <td>${lead.source || '-'}</td>
                    <td>${lead.product_interest || '-'}</td>
                    <td>
                        ${lead.follow_up_date ? formatDate(lead.follow_up_date) : '<span class="text-sm text-gray-500">Not set</span>'}
                    </td>
                    <td>
                        <span class="status-badge badge ${getStatusBadgeClass(lead.status)}">${lead.status}</span>
                    </td>
                    <td>
                        <div class="flex gap-2">
                            ${lead.status === 'Qualified' ? `
                                <a href="/client-onboarding/?lead_id=${lead.id}" class="btn btn-primary text-sm py-1 px-3">Onboard</a>
                            ` : ''}
                            <a href="/leads/${lead.id}/" class="btn btn-secondary text-sm py-1 px-3">View</a>
                        </div>
                    </td>
                </tr>
            `).join('');

            attachQuickActionListeners();

        } catch (error) {
            console.error('Error loading leads:', error);
        }
    }

    function getStatusBadgeClass(status) {
        const classes = {
            'New': 'badge-secondary',
            'Contacted': 'badge-primary',
            'Qualified': 'badge-success',
            'Converted': 'badge-success',
            'Lost': 'badge-danger'
        };
        return classes[status] || 'badge-secondary';
    }

    function attachQuickActionListeners() {
        // No quick actions needed - View button and Onboard link handle all navigation
    }

    // ============================================================
    // INITIALIZATION
    // ============================================================

    loadLeads();
    loadProducts();

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(loadLeads, 300));
    }

    // Close dropdown on outside click
    document.addEventListener('click', function (e) {
        const container = document.getElementById('productSelectContainer');
        if (container && !container.contains(e.target) && productDropdownMenu && !productDropdownMenu.classList.contains('hidden')) {
            productDropdownMenu.classList.add('hidden');
        }
    });

    console.log('Lead intake page initialized successfully');
});
