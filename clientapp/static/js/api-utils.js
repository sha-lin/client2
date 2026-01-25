/**
 * Print Duka API Utilities
 * Global Functions for Frontend-Backend API Integration
 * Version: 1.0.0
 */

const API_BASE = '/api/v1';

// ============================================================
// CSRF TOKEN HANDLING
// ============================================================

/**
 * Get CSRF Token from cookies (required for POST/PUT/DELETE)
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ============================================================
// API CALL FUNCTIONS
// ============================================================

/**
 * Generic API Call Function with error handling
 * @param {string} endpoint - API endpoint (e.g., '/leads/' or '/api/v1/leads/')
 * @param {string} method - HTTP method (GET, POST, PUT, PATCH, DELETE)
 * @param {object} data - Request body data
 * @param {object} options - Additional fetch options
 * @returns {Promise<object>} Response data
 */
async function apiCall(endpoint, method = 'GET', data = null, options = {}) {
    const url = endpoint.startsWith('/api/') ? endpoint : API_BASE + endpoint;

    const fetchOptions = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            ...options.headers
        }
    };

    if (data && method !== 'GET') {
        fetchOptions.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, fetchOptions);

        // Handle 204 No Content
        if (response.status === 204) {
            return { success: true };
        }

        const responseData = await response.json();

        if (!response.ok) {
            throw { status: response.status, data: responseData };
        }

        return responseData;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Shorthand API methods object
 */
const api = {
    get: (endpoint) => apiCall(endpoint, 'GET'),
    post: (endpoint, data) => apiCall(endpoint, 'POST', data),
    put: (endpoint, data) => apiCall(endpoint, 'PUT', data),
    patch: (endpoint, data) => apiCall(endpoint, 'PATCH', data),
    delete: (endpoint) => apiCall(endpoint, 'DELETE')
};

// ============================================================
// UI FEEDBACK FUNCTIONS
// ============================================================

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type: success, error, warning, info
 * @param {number} duration - Duration in ms
 */
function showToast(message, type = 'success', duration = 4000) {
    // Remove existing toasts
    document.querySelectorAll('.toast-notification').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = 'toast-notification fixed top-20 right-4 z-50 px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full';

    const colors = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
    };
    toast.className += ' ' + (colors[type] || colors.success);

    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    toast.innerHTML = '<span class="font-bold mr-2">' + (icons[type] || '✓') + '</span>' + message;

    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => toast.classList.remove('translate-x-full'), 10);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show loading spinner overlay
 * @param {string} message - Loading message
 */
function showLoading(message = 'Loading...') {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        overlay.innerHTML = `
            <div class="bg-white rounded-lg p-6 flex items-center gap-4 shadow-xl">
                <div class="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
                <span class="text-gray-700 font-medium" id="loading-message">${message}</span>
            </div>
        `;
        document.body.appendChild(overlay);
    } else {
        document.getElementById('loading-message').textContent = message;
        overlay.classList.remove('hidden');
    }
}

/**
 * Hide loading spinner overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
}

// ============================================================
// FORM HANDLING FUNCTIONS
// ============================================================

/**
 * Convert form data to JSON object
 * @param {HTMLFormElement} formElement - Form element
 * @returns {object} JSON object of form data
 */
function formToJson(formElement) {
    const formData = new FormData(formElement);
    const data = {};
    formData.forEach((value, key) => {
        // Handle multiple values (like checkboxes)
        if (data[key]) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });
    return data;
}

/**
 * Display validation errors on form fields
 * @param {object} errors - Error object from API
 * @param {string} formId - Optional form ID to scope errors
 */
function showFormErrors(errors, formId = null) {
    // Clear previous errors
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll('.border-red-500').forEach(el => {
        el.classList.remove('border-red-500');
    });

    // Display new errors
    for (const [field, messages] of Object.entries(errors)) {
        const input = document.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('border-red-500');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-red-500 text-sm mt-1';
            errorDiv.textContent = Array.isArray(messages) ? messages.join(', ') : messages;
            input.parentNode.appendChild(errorDiv);
        }
    }

    // Show general errors
    if (errors.detail || errors.non_field_errors) {
        const msg = errors.detail || errors.non_field_errors;
        showToast(Array.isArray(msg) ? msg.join(', ') : msg, 'error');
    }
}

/**
 * Clear all form errors
 */
function clearFormErrors() {
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll('.border-red-500').forEach(el => {
        el.classList.remove('border-red-500');
    });
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

/**
 * Debounce function for search inputs
 * @param {function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format currency (KES)
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount, currency = 'KES') {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Format date
 * @param {string} dateString - Date string to format
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
function formatDate(dateString, options = {}) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        ...options
    });
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {string} dateString - Date string
 * @returns {string} Relative time string
 */
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return formatDate(dateString);
}

/**
 * Confirm action dialog
 * @param {string} message - Confirmation message
 * @param {function} onConfirm - Callback on confirm
 * @param {function} onCancel - Optional callback on cancel
 */
function confirmAction(message, onConfirm, onCancel = null) {
    if (confirm(message)) {
        onConfirm();
    } else if (onCancel) {
        onCancel();
    }
}

// ============================================================
// NOTIFICATION FUNCTIONS
// ============================================================

/**
 * Refresh notification count in UI
 */
async function refreshNotificationCount() {
    try {
        const data = await api.get('/notifications/?is_read=false');
        const count = data.count || 0;
        const badges = document.querySelectorAll('[data-notification-count]');
        badges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        });
    } catch (error) {
        console.log('Could not refresh notification count');
    }
}

// Auto-refresh notifications every 60 seconds
if (typeof window !== 'undefined') {
    setInterval(refreshNotificationCount, 60000);
}

// ============================================================
// QUOTE HELPERS
// ============================================================

/**
 * Calculate quote line item total
 * @param {number} unitPrice - Unit price
 * @param {number} quantity - Quantity
 * @param {number} discountPercent - Optional discount percentage
 * @returns {number} Line total
 */
/**
 * Calculate single line item total
 * Line Total = (unit_price + variable_amount) * quantity - discount
 * Where discount = subtotal * (discount_percent / 100)
 * @param {number} unitPrice - Unit price per item
 * @param {number} quantity - Quantity ordered
 * @param {number} discountPercent - Discount percentage (default 0)
 * @param {number} variableAmount - Variable/additional amount (default 0)
 * @returns {number} Line total after discount
 */
function calculateLineTotal(unitPrice, quantity, discountPercent = 0, variableAmount = 0) {
    const subtotal = (unitPrice + variableAmount) * quantity;
    const discount = subtotal * (discountPercent / 100);
    return subtotal - discount;
}

/**
 * Calculate quote totals - aggregates all line items with tax and shipping
 * @param {Array} lineItems - Array of line item objects {unit_price, quantity, discount_percent, variable_amount}
 * @param {number} taxRate - Tax rate percentage (default 16% VAT)
 * @param {number} shippingCost - Shipping cost (default 0)
 * @param {number} adjustmentAmount - Final adjustment amount (default 0)
 * @returns {object} Totals object {subtotal, discountTotal, taxAmount, shippingCost, adjustmentAmount, total}
 */
function calculateQuoteTotals(lineItems, taxRate = 16, shippingCost = 0, adjustmentAmount = 0) {
    // Calculate subtotal and discount from all line items
    let subtotal = 0;
    let discountTotal = 0;

    lineItems.forEach(item => {
        const itemSubtotal = (item.unit_price + (item.variable_amount || 0)) * (item.quantity || 1);
        const itemDiscount = itemSubtotal * ((item.discount_percent || 0) / 100);
        
        subtotal += itemSubtotal;
        discountTotal += itemDiscount;
    });

    // Apply discount to get after-discount total
    const afterDiscount = subtotal - discountTotal;
    
    // Calculate tax on after-discount amount
    const taxAmount = afterDiscount * (taxRate / 100);
    
    // Final total
    const total = afterDiscount + taxAmount + shippingCost + adjustmentAmount;

    return {
        subtotal: subtotal,
        discountTotal: discountTotal,
        afterDiscount: afterDiscount,
        taxAmount: taxAmount,
        shippingCost: shippingCost,
        adjustmentAmount: adjustmentAmount,
        total: total
    };
}

// ============================================================
// LEAD/CLIENT HELPERS
// ============================================================

/**
 * Check for duplicate lead by email
 * @param {string} email - Email to check
 * @returns {Promise<object|null>} Existing lead or null
 */
async function checkDuplicateLead(email) {
    try {
        const data = await api.get(`/leads/?email=${encodeURIComponent(email)}`);
        if (data.results && data.results.length > 0) {
            return data.results[0];
        }
        return null;
    } catch (error) {
        console.error('Error checking duplicate lead:', error);
        return null;
    }
}

/**
 * Check for duplicate client by email
 * @param {string} email - Email to check
 * @returns {Promise<object|null>} Existing client or null
 */
async function checkDuplicateClient(email) {
    try {
        const data = await api.get(`/clients/?email=${encodeURIComponent(email)}`);
        if (data.results && data.results.length > 0) {
            return data.results[0];
        }
        return null;
    } catch (error) {
        console.error('Error checking duplicate client:', error);
        return null;
    }
}

// ============================================================
// PRODUCT SEARCH HELPERS
// ============================================================

/**
 * Search products by name or SKU
 * @param {string} query - Search query
 * @param {object} filters - Additional filters
 * @returns {Promise<Array>} Array of products
 */
async function searchProducts(query, filters = {}) {
    try {
        let url = `/products/?search=${encodeURIComponent(query)}&status=published`;

        if (filters.category) {
            url += `&category=${filters.category}`;
        }
        if (filters.customization_level) {
            url += `&customization_level=${filters.customization_level}`;
        }

        const data = await api.get(url);
        return data.results || [];
    } catch (error) {
        console.error('Error searching products:', error);
        return [];
    }
}

/**
 * Get product price with options
 * @param {number} productId - Product ID
 * @param {number} quantity - Quantity
 * @param {object} options - Product options/variables
 * @returns {Promise<object>} Pricing info
 */
async function getProductPrice(productId, quantity = 1, options = {}) {
    try {
        const data = await api.post('/pricing/calculate/', {
            product_id: productId,
            quantity: quantity,
            options: options
        });
        return data;
    } catch (error) {
        console.error('Error getting product price:', error);
        return { unit_price: 0, total: 0 };
    }
}

console.log('Print Duka API Utilities loaded successfully');
