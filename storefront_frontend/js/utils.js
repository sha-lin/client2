/**
 * Frontend Utility Functions
 * Common helpers for UI rendering, formatting, validation, etc.
 */

/**
 * Format currency for display
 */
function formatCurrency(amount, currencyCode = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currencyCode
    }).format(amount);
}

/**
 * Format date for display
 */
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format datetime for display
 */
function formatDateTime(datetime) {
    if (typeof datetime === 'string') {
        datetime = new Date(datetime);
    }
    return datetime.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast alert alert-${mapToastType(type)} alert-dismissible fade show`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
}

/**
 * Map toast type to Bootstrap alert class
 */
function mapToastType(type) {
    const mapping = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return mapping[type] || 'info';
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    document.body.appendChild(container);
    return container;
}

/**
 * Show loading indicator
 */
function showLoading(message = 'Loading...') {
    const loader = document.createElement('div');
    loader.id = 'loading-indicator';
    loader.className = 'loading-indicator';
    loader.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">${message}</p>
    `;
    document.body.appendChild(loader);
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loader = document.getElementById('loading-indicator');
    if (loader) {
        loader.remove();
    }
}

/**
 * Show modal dialog
 */
function showModal(title, content, buttons = null) {
    const modal = new bootstrap.Modal(document.createElement('div'), {});
    const modalElement = document.createElement('div');
    modalElement.className = 'modal fade';
    modalElement.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${buttons || '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>'}
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modalElement);
    const bsModal = new bootstrap.Modal(modalElement);
    bsModal.show();
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate phone number
 */
function isValidPhone(phone) {
    const phoneRegex = /^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

/**
 * Get query parameter from URL
 */
function getQueryParameter(paramName) {
    const params = new URLSearchParams(window.location.search);
    return params.get(paramName);
}

/**
 * Set query parameter in URL without reload
 */
function setQueryParameter(paramName, paramValue) {
    const params = new URLSearchParams(window.location.search);
    params.set(paramName, paramValue);
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
}

/**
 * Debounce function
 */
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Deep clone object
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Merge objects
 */
function mergeObjects(target, source) {
    return { ...target, ...source };
}

/**
 * Is user authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('storefront_access_token');
}

/**
 * Get current user info
 */
function getCurrentUser() {
    const user = localStorage.getItem('storefront_user');
    return user ? JSON.parse(user) : null;
}

/**
 * Store current user info
 */
function setCurrentUser(user) {
    localStorage.setItem('storefront_user', JSON.stringify(user));
}

/**
 * Clear current user info (logout)
 */
function clearCurrentUser() {
    localStorage.removeItem('storefront_user');
    localStorage.removeItem('storefront_access_token');
    localStorage.removeItem('storefront_refresh_token');
}

/**
 * Truncate text
 */
function truncateText(text, length = 100) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

/**
 * Generate unique ID
 */
function generateId(prefix = '') {
    return prefix + Math.random().toString(36).substr(2, 9);
}

/**
 * Status badge class mapping
 */
function getStatusBadgeClass(status) {
    const mapping = {
        'draft': 'badge-secondary',
        'shared_with_am': 'badge-info',
        'converted_to_quote': 'badge-success',
        'pending': 'badge-warning',
        'in_production': 'badge-primary',
        'completed': 'badge-success',
        'unassigned': 'badge-secondary',
        'assigned': 'badge-info',
        'resolved': 'badge-success'
    };
    return mapping[status] || 'badge-secondary';
}

/**
 * Status display name
 */
function getStatusDisplayName(status) {
    const mapping = {
        'draft': 'Draft',
        'shared_with_am': 'Shared with AM',
        'converted_to_quote': 'Converted to Quote',
        'pending': 'Pending',
        'in_production': 'In Production',
        'completed': 'Completed',
        'po_sent': 'PO Sent',
        'qc_check': 'QC Check',
        'unassigned': 'Unassigned',
        'assigned': 'Assigned',
        'resolved': 'Resolved'
    };
    return mapping[status] || status;
}

/**
 * Action dropdown HTML
 */
function createActionDropdown(actions = []) {
    if (actions.length === 0) return '';
    
    return `
        <div class="dropdown">
            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                Actions
            </button>
            <ul class="dropdown-menu">
                ${actions.map(action => `
                    <li><a class="dropdown-item" href="#" data-action="${action.id}">${action.label}</a></li>
                `).join('')}
            </ul>
        </div>
    `;
}

/**
 * Pagination HTML
 */
function createPagination(currentPage, totalPages, onPageChange) {
    if (totalPages <= 1) return '';
    
    let html = '<nav aria-label="Page navigation"><ul class="pagination">';
    
    // Previous button
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage - 1}">Previous</a>
    </li>`;
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
    }
    
    // Next button
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage + 1}">Next</a>
    </li>`;
    
    html += '</ul></nav>';
    return html;
}

/**
 * Export utilities
 */
window.StorefrontUtils = {
    formatCurrency,
    formatDate,
    formatDateTime,
    showToast,
    showLoading,
    hideLoading,
    showModal,
    isValidEmail,
    isValidPhone,
    getQueryParameter,
    setQueryParameter,
    debounce,
    formatFileSize,
    deepClone,
    mergeObjects,
    isAuthenticated,
    getCurrentUser,
    setCurrentUser,
    clearCurrentUser,
    truncateText,
    generateId,
    getStatusBadgeClass,
    getStatusDisplayName,
    createActionDropdown,
    createPagination
};
