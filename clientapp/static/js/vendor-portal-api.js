/**
 * Vendor Portal API Service Layer
 * Handles all communication with the backend API
 * 
 * This file provides abstracted, reusable methods for all vendor portal operations
 */

class VendorPortalAPI {
    constructor(baseUrl = '/api/v1', tokenKey = 'access_token') {
        this.baseUrl = baseUrl;
        this.tokenKey = tokenKey;
        this.token = localStorage.getItem(tokenKey);
        this.currentVendor = null;
    }

    /**
     * Get authorization headers with JWT token
     */
    getHeaders(includeContentType = true) {
        const headers = {
            'Authorization': `Bearer ${this.token}`
        };

        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }

        return headers;
    }

    /**
     * Generic API call handler
     */
    async call(endpoint, method = 'GET', data = null, useFormData = false) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: useFormData ? { 'Authorization': `Bearer ${this.token}` } : this.getHeaders()
        };

        if (data) {
            if (useFormData) {
                options.body = data; // data should already be FormData
            } else {
                options.body = JSON.stringify(data);
            }
        }

        try {
            const response = await fetch(url, options);

            if (response.status === 401) {
                this.handleUnauthorized();
                return null;
            }

            if (response.status === 403) {
                console.warn('Forbidden: You do not have permission to access this resource');
                return null;
            }

            if (response.status === 404) {
                console.warn(`Resource not found: ${endpoint}`);
                return null;
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                console.error(`API Error (${response.status}):`, error);
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error('API Call Error:', error);
            return null;
        }
    }

    handleUnauthorized() {
        localStorage.removeItem(this.tokenKey);
        window.location.href = '/accounts/login/';
    }

    // ============================================================
    // VENDOR OPERATIONS
    // ============================================================

    /**
     * Get current vendor profile
     */
    async getCurrentVendor() {
        if (this.currentVendor) {
            return this.currentVendor;
        }

        const response = await this.call('/vendors/?is_vendor_portal=true');
        if (response && response.results && response.results.length > 0) {
            this.currentVendor = response.results[0];
            return this.currentVendor;
        }

        return null;
    }

    /**
     * Update vendor profile
     */
    async updateVendorProfile(data) {
        const vendor = await this.getCurrentVendor();
        if (!vendor) return null;

        return await this.call(`/vendors/${vendor.id}/`, 'PATCH', data);
    }

    /**
     * Get vendor statistics (dashboard KPIs)
     */
    async getVendorDashboard() {
        const vendor = await this.getCurrentVendor();
        if (!vendor) return null;

        return await this.call(`/purchase-orders/vendor-dashboard/`);
    }

    // ============================================================
    // PURCHASE ORDERS
    // ============================================================

    /**
     * Get all purchase orders for vendor
     */
    async getPurchaseOrders(filters = {}) {
        let endpoint = '/purchase-orders/';
        const params = new URLSearchParams(filters);

        if (Object.keys(filters).length > 0) {
            endpoint += `?${params.toString()}`;
        }

        return await this.call(endpoint);
    }

    /**
     * Get single purchase order details
     */
    async getPurchaseOrderDetail(poId) {
        return await this.call(`/purchase-orders/${poId}/`);
    }

    /**
     * Accept a purchase order
     */
    async acceptPurchaseOrder(poId) {
        return await this.call(`/purchase-orders/${poId}/accept/`, 'POST', {});
    }

    /**
     * Reject a purchase order
     */
    async rejectPurchaseOrder(poId, reason) {
        return await this.call(`/purchase-orders/${poId}/reject/`, 'POST', { reason });
    }

    /**
     * Update purchase order milestone/progress
     */
    async updatePurchaseOrderMilestone(poId, data) {
        return await this.call(`/purchase-orders/${poId}/update_milestone/`, 'POST', data);
    }

    /**
     * Get purchase orders by status
     */
    async getPurchaseOrdersByStatus(status) {
        return await this.call(`/purchase-orders/?status=${status}`);
    }

    /**
     * Get overdue purchase orders
     */
    async getOverduePurchaseOrders() {
        return await this.call('/purchase-orders/?is_overdue=true');
    }

    /**
     * Search purchase orders
     */
    async searchPurchaseOrders(query) {
        return await this.call(`/purchase-orders/?search=${encodeURIComponent(query)}`);
    }

    // ============================================================
    // PURCHASE ORDER PROOFS
    // ============================================================

    /**
     * Submit a proof
     */
    async submitProof(formData) {
        return await this.call('/purchase-order-proofs/', 'POST', formData, true);
    }

    /**
     * Get all proofs for vendor
     */
    async getProofs(filters = {}) {
        let endpoint = '/purchase-order-proofs/';
        const params = new URLSearchParams(filters);

        if (Object.keys(filters).length > 0) {
            endpoint += `?${params.toString()}`;
        }

        return await this.call(endpoint);
    }

    /**
     * Get specific proof
     */
    async getProofDetail(proofId) {
        return await this.call(`/purchase-order-proofs/${proofId}/`);
    }

    /**
     * Get proofs for specific PO
     */
    async getProofsByPurchaseOrder(poId) {
        return await this.call(`/purchase-order-proofs/?purchase_order=${poId}`);
    }

    /**
     * Download proof file
     */
    async downloadProof(proofId) {
        const proof = await this.getProfDetail(proofId);
        if (proof && proof.files && proof.files.length > 0) {
            // Download files
            proof.files.forEach(file => {
                window.open(file.file, '_blank');
            });
        }
    }

    // ============================================================
    // VENDOR INVOICES
    // ============================================================

    /**
     * Create a new invoice
     */
    async createInvoice(data) {
        return await this.call('/vendor-invoices/', 'POST', data);
    }

    /**
     * Get all invoices
     */
    async getInvoices(filters = {}) {
        let endpoint = '/vendor-invoices/';
        const params = new URLSearchParams(filters);

        if (Object.keys(filters).length > 0) {
            endpoint += `?${params.toString()}`;
        }

        return await this.call(endpoint);
    }

    /**
     * Get specific invoice
     */
    async getInvoiceDetail(invoiceId) {
        return await this.call(`/vendor-invoices/${invoiceId}/`);
    }

    /**
     * Approve invoice (for production team)
     */
    async approveInvoice(invoiceId) {
        return await this.call(`/vendor-invoices/${invoiceId}/approve/`, 'POST', {});
    }

    /**
     * Reject invoice
     */
    async rejectInvoice(invoiceId, reason) {
        return await this.call(`/vendor-invoices/${invoiceId}/reject/`, 'POST', { reason });
    }

    /**
     * Mark invoice as paid
     */
    async markInvoicePaid(invoiceId) {
        return await this.call(`/vendor-invoices/${invoiceId}/mark_paid/`, 'POST', {});
    }

    /**
     * Get invoices by status
     */
    async getInvoicesByStatus(status) {
        return await this.call(`/vendor-invoices/?status=${status}`);
    }

    /**
     * Get overdue invoices
     */
    async getOverdueInvoices() {
        return await this.call('/vendor-invoices/?status=overdue');
    }

    // ============================================================
    // PURCHASE ORDER ISSUES
    // ============================================================

    /**
     * Create an issue/clarification request
     */
    async createIssue(data) {
        return await this.call('/purchase-order-issues/', 'POST', data);
    }

    /**
     * Get all issues
     */
    async getIssues(filters = {}) {
        let endpoint = '/purchase-order-issues/';
        const params = new URLSearchParams(filters);

        if (Object.keys(filters).length > 0) {
            endpoint += `?${params.toString()}`;
        }

        return await this.call(endpoint);
    }

    /**
     * Get issues for specific PO
     */
    async getIssuesByPurchaseOrder(poId) {
        return await this.call(`/purchase-order-issues/?purchase_order=${poId}`);
    }

    /**
     * Update issue status
     */
    async updateIssueStatus(issueId, status) {
        return await this.call(`/purchase-order-issues/${issueId}/`, 'PATCH', { status });
    }

    // ============================================================
    // PURCHASE ORDER NOTES/MESSAGES
    // ============================================================

    /**
     * Add a note/message to a PO
     */
    async addNote(data) {
        return await this.call('/purchase-order-notes/', 'POST', data);
    }

    /**
     * Get all notes
     */
    async getNotes(filters = {}) {
        let endpoint = '/purchase-order-notes/';
        const params = new URLSearchParams(filters);

        if (Object.keys(filters).length > 0) {
            endpoint += `?${params.toString()}`;
        }

        return await this.call(endpoint);
    }

    /**
     * Get notes for specific PO
     */
    async getNotesByPurchaseOrder(poId) {
        return await this.call(`/purchase-order-notes/?purchase_order=${poId}`);
    }

    /**
     * Get vendor's recent messages
     */
    async getRecentMessages(limit = 20) {
        return await this.call(`/purchase-order-notes/?limit=${limit}&ordering=-created_at`);
    }

    // ============================================================
    // MATERIAL SUBSTITUTIONS
    // ============================================================

    /**
     * Request material substitution
     */
    async requestSubstitution(data) {
        return await this.call('/material-substitutions/', 'POST', data);
    }

    /**
     * Get all substitution requests
     */
    async getSubstitutionRequests(filters = {}) {
        let endpoint = '/material-substitutions/';
        const params = new URLSearchParams(filters);

        if (Object.keys(filters).length > 0) {
            endpoint += `?${params.toString()}`;
        }

        return await this.call(endpoint);
    }

    /**
     * Get substitution request by ID
     */
    async getSubstitutionDetail(substitutionId) {
        return await this.call(`/material-substitutions/${substitutionId}/`);
    }

    /**
     * Get pending substitution requests
     */
    async getPendingSubstitutions() {
        return await this.call('/material-substitutions/?status=pending');
    }

    // ============================================================
    // VENDOR PERFORMANCE
    // ============================================================

    /**
     * Get vendor performance metrics
     */
    async getPerformanceMetrics() {
        return await this.call('/vendor-performance/');
    }

    /**
     * Get performance by vendor
     */
    async getPerformanceByVendor() {
        const vendor = await this.getCurrentVendor();
        if (!vendor) return null;

        return await this.call(`/vendor-performance/?vendor=${vendor.id}`);
    }

    /**
     * Get performance trends
     */
    async getPerformanceTrends(days = 30) {
        return await this.call(`/vendor-performance/?days=${days}`);
    }

    /**
     * Get quality metrics
     */
    async getQualityMetrics() {
        const vendor = await this.getCurrentVendor();
        if (!vendor) return null;

        return await this.call(`/purchase-order-proofs/?vendor=${vendor.id}&status=approved`);
    }

    // ============================================================
    // NOTIFICATIONS
    // ============================================================

    /**
     * Get notifications
     */
    async getNotifications(unreadOnly = false) {
        let endpoint = '/notifications/';
        if (unreadOnly) {
            endpoint += '?is_read=false';
        }

        return await this.call(endpoint);
    }

    /**
     * Mark notification as read
     */
    async markNotificationRead(notificationId) {
        return await this.call(`/notifications/${notificationId}/mark_as_read/`, 'POST', {});
    }

    /**
     * Get unread notification count
     */
    async getUnreadNotificationCount() {
        const notifications = await this.getNotifications(true);
        return notifications ? notifications.results?.length || 0 : 0;
    }

    // ============================================================
    // SEARCH & FILTERS
    // ============================================================

    /**
     * Generic search across models
     */
    async search(query, model = 'purchase_orders') {
        return await this.call(`/${model}/?search=${encodeURIComponent(query)}`);
    }

    /**
     * Get data with pagination
     */
    async getPagedData(endpoint, page = 1, pageSize = 20) {
        return await this.call(`${endpoint}?page=${page}&page_size=${pageSize}`);
    }

    /**
     * Get data with filtering
     */
    async getFilteredData(endpoint, filters = {}) {
        const params = new URLSearchParams(filters);
        return await this.call(`${endpoint}?${params.toString()}`);
    }

    // ============================================================
    // ANALYTICS
    // ============================================================

    /**
     * Get revenue analytics
     */
    async getRevenueAnalytics() {
        return await this.call('/analytics/vendor-revenue/');
    }

    /**
     * Get job completion analytics
     */
    async getJobCompletionAnalytics() {
        return await this.call('/analytics/vendor-jobs/');
    }

    /**
     * Get time-to-completion analytics
     */
    async getTimeAnalytics() {
        return await this.call('/analytics/vendor-timing/');
    }

    // ============================================================
    // EXPORT FUNCTIONALITY
    // ============================================================

    /**
     * Export purchase orders to CSV
     */
    async exportPurchaseOrdersCSV() {
        const response = await fetch(`${this.baseUrl}/purchase-orders/export/?format=csv`, {
            headers: this.getHeaders()
        });

        if (response.ok) {
            const blob = await response.blob();
            this.downloadFile(blob, 'purchase_orders.csv');
        }
    }

    /**
     * Export invoices to CSV
     */
    async exportInvoicesCSV() {
        const response = await fetch(`${this.baseUrl}/vendor-invoices/export/?format=csv`, {
            headers: this.getHeaders()
        });

        if (response.ok) {
            const blob = await response.blob();
            this.downloadFile(blob, 'invoices.csv');
        }
    }

    /**
     * Export performance report to PDF
     */
    async exportPerformanceReport() {
        const response = await fetch(`${this.baseUrl}/vendor-performance/export/?format=pdf`, {
            headers: this.getHeaders()
        });

        if (response.ok) {
            const blob = await response.blob();
            this.downloadFile(blob, 'performance_report.pdf');
        }
    }

    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    // ============================================================
    // UTILITY METHODS
    // ============================================================

    /**
     * Format currency for display
     */
    static formatCurrency(amount, currency = 'KES') {
        return `${currency} ${parseFloat(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    /**
     * Format date
     */
    static formatDate(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    /**
     * Calculate days until deadline
     */
    static daysUntilDeadline(deadline) {
        const today = new Date();
        const deadlineDate = new Date(deadline);
        const difference = deadlineDate - today;
        return Math.ceil(difference / (1000 * 60 * 60 * 24));
    }

    /**
     * Check if deadline is overdue
     */
    static isOverdue(deadline) {
        return this.daysUntilDeadline(deadline) < 0;
    }

    /**
     * Get status badge color
     */
    static getStatusColor(status) {
        const colors = {
            'new': 'info',
            'in_production': 'warning',
            'quality_check': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
            'pending': 'warning',
            'approved': 'success',
            'paid': 'success',
            'overdue': 'danger',
            'rejected': 'danger'
        };

        return colors[status] || 'info';
    }

    /**
     * Get status display text
     */
    static getStatusDisplay(status) {
        const displays = {
            'new': 'New Order',
            'in_production': 'In Production',
            'quality_check': 'Quality Check',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'draft': 'Draft',
            'pending': 'Pending Review',
            'approved': 'Approved',
            'paid': 'Paid',
            'overdue': 'Overdue',
            'rejected': 'Rejected'
        };

        return displays[status] || status;
    }
}

// Create global instance
const vendorAPI = new VendorPortalAPI();
