/**
 * PT Portal API Client
 * Handles all API calls for Production Team portal
 */

class PTPortalAPI {
    constructor(baseUrl = '/api/v1') {
        this.baseUrl = baseUrl;
        this.token = this.getToken();
    }

    /**
     * Generic API call method with error handling
     */
    async call(endpoint, method = 'GET', data = null, useFormData = false) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            }
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (data) {
            if (useFormData) {
                options.body = data;
            } else {
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify(data);
            }
        }

        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * ============================================================
     * JOBS MANAGEMENT
     * ============================================================
     */

    async getJobs(filters = {}) {
        let url = '/jobs/?';
        
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.search) url += `search=${filters.search}&`;
        if (filters.vendor) url += `vendor=${filters.vendor}&`;
        if (filters.page) url += `page=${filters.page}&`;
        if (filters.ordering) url += `ordering=${filters.ordering}&`;

        return this.call(url);
    }

    async getJobDetail(jobId) {
        return this.call(`/jobs/${jobId}/`);
    }

    async getJobVendorStage(jobId, vendorId) {
        return this.call(`/job-vendor-stages/?job=${jobId}&vendor=${vendorId}`);
    }

    async updateJobStatus(jobId, status, notes = '') {
        return this.call(`/jobs/${jobId}/`, 'PATCH', {
            status,
            notes
        });
    }

    async blockJob(jobId, reason) {
        return this.call(`/jobs/${jobId}/block/`, 'POST', { reason });
    }

    async unblockJob(jobId) {
        return this.call(`/jobs/${jobId}/unblock/`, 'POST');
    }

    async getOverdueJobs() {
        return this.call('/jobs/overdue/');
    }

    async getJobProgressUpdates(jobId) {
        return this.call(`/job-progress-updates/?job=${jobId}`);
    }

    /**
     * ============================================================
     * VENDOR MANAGEMENT
     * ============================================================
     */

    async getVendors(filters = {}) {
        let url = '/vendors/?';
        
        if (filters.search) url += `search=${filters.search}&`;
        if (filters.page) url += `page=${filters.page}&`;

        return this.call(url);
    }

    async getVendorDetail(vendorId) {
        return this.call(`/vendors/${vendorId}/`);
    }

    async getVendorWorkload(vendorId = null) {
        if (vendorId) {
            return this.call(`/vendors/${vendorId}/workload/`);
        }
        return this.call('/vendors/workload/');
    }

    async getVendorPerformance(vendorId) {
        return this.call(`/vendors/${vendorId}/performance/`);
    }

    async getVendorHistory(vendorId) {
        return this.call(`/vendors/${vendorId}/history/`);
    }

    async updateVendorStatus(vendorId, status) {
        return this.call(`/vendors/${vendorId}/`, 'PATCH', { status });
    }

    async getVendorOnTimeRate(vendorId) {
        return this.call(`/vendors/${vendorId}/on-time-rate/`);
    }

    async getVendorQualityScore(vendorId) {
        return this.call(`/vendors/${vendorId}/quality-score/`);
    }

    /**
     * ============================================================
     * PURCHASE ORDERS
     * ============================================================
     */

    async getPurchaseOrders(filters = {}) {
        let url = '/purchase-orders/?';
        
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.vendor) url += `vendor=${filters.vendor}&`;
        if (filters.page) url += `page=${filters.page}&`;

        return this.call(url);
    }

    async getPurchaseOrderDetail(poId) {
        return this.call(`/purchase-orders/${poId}/`);
    }

    async createPurchaseOrder(data) {
        return this.call('/purchase-orders/', 'POST', data);
    }

    async updatePurchaseOrder(poId, data) {
        return this.call(`/purchase-orders/${poId}/`, 'PATCH', data);
    }

    async approvePurchaseOrder(poId) {
        return this.call(`/purchase-orders/${poId}/approve/`, 'POST');
    }

    async rejectPurchaseOrder(poId, reason) {
        return this.call(`/purchase-orders/${poId}/reject/`, 'POST', { reason });
    }

    async completePurchaseOrder(poId) {
        return this.call(`/purchase-orders/${poId}/complete/`, 'POST');
    }

    async blockPurchaseOrder(poId, reason) {
        return this.call(`/purchase-orders/${poId}/block/`, 'POST', { reason });
    }

    /**
     * ============================================================
     * INVOICES
     * ============================================================
     */

    async getInvoices(filters = {}) {
        let url = '/vendor-invoices/?';
        
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.vendor) url += `vendor=${filters.vendor}&`;
        if (filters.page) url += `page=${filters.page}&`;
        if (filters.search) url += `search=${filters.search}&`;

        return this.call(url);
    }

    async getInvoiceDetail(invoiceId) {
        return this.call(`/vendor-invoices/${invoiceId}/`);
    }

    async createInvoice(data) {
        return this.call('/vendor-invoices/', 'POST', data);
    }

    async approveInvoice(invoiceId, notes = '') {
        return this.call(`/vendor-invoices/${invoiceId}/approve/`, 'POST', { notes });
    }

    async rejectInvoice(invoiceId, reason) {
        return this.call(`/vendor-invoices/${invoiceId}/reject/`, 'POST', { reason });
    }

    async markInvoiceAsPaid(invoiceId, paymentDate, notes = '') {
        return this.call(`/vendor-invoices/${invoiceId}/mark-paid/`, 'POST', {
            payment_date: paymentDate,
            notes
        });
    }

    async validateInvoice(invoiceId) {
        return this.call(`/vendor-invoices/${invoiceId}/validate/`, 'POST');
    }

    async getInvoicesByVendor(vendorId) {
        return this.call(`/vendor-invoices/?vendor=${vendorId}`);
    }

    /**
     * ============================================================
     * QC PROOFS
     * ============================================================
     */

    async getProofs(filters = {}) {
        let url = '/purchase-order-proofs/?';
        
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.page) url += `page=${filters.page}&`;

        return this.call(url);
    }

    async getProofDetail(proofId) {
        return this.call(`/purchase-order-proofs/${proofId}/`);
    }

    async approveProof(proofId, notes = '') {
        return this.call(`/purchase-order-proofs/${proofId}/approve/`, 'POST', { notes });
    }

    async rejectProof(proofId, reason) {
        return this.call(`/purchase-order-proofs/${proofId}/reject/`, 'POST', { reason });
    }

    async getProofsByPurchaseOrder(poId) {
        return this.call(`/purchase-order-proofs/?purchase_order=${poId}`);
    }

    async blockProof(proofId, reason) {
        return this.call(`/purchase-order-proofs/${proofId}/block/`, 'POST', { reason });
    }

    /**
     * ============================================================
     * ISSUES & DISPUTES
     * ============================================================
     */

    async getIssues(filters = {}) {
        let url = '/purchase-order-issues/?';
        
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.severity) url += `severity=${filters.severity}&`;
        if (filters.page) url += `page=${filters.page}&`;

        return this.call(url);
    }

    async getIssueDetail(issueId) {
        return this.call(`/purchase-order-issues/${issueId}/`);
    }

    async createIssue(data) {
        return this.call('/purchase-order-issues/', 'POST', data);
    }

    async resolveIssue(issueId, resolutionNotes) {
        return this.call(`/purchase-order-issues/${issueId}/resolve/`, 'POST', {
            resolution_notes: resolutionNotes
        });
    }

    /**
     * ============================================================
     * MESSAGING
     * ============================================================
     */

    async getNotes(filters = {}) {
        let url = '/purchase-order-notes/?';
        
        if (filters.purchase_order) url += `purchase_order=${filters.purchase_order}&`;
        if (filters.page) url += `page=${filters.page}&`;

        return this.call(url);
    }

    async getNoteDetail(noteId) {
        return this.call(`/purchase-order-notes/${noteId}/`);
    }

    async createNote(data) {
        return this.call('/purchase-order-notes/', 'POST', data);
    }

    async markNoteAsRead(noteId) {
        return this.call(`/purchase-order-notes/${noteId}/mark-read/`, 'POST');
    }

    /**
     * ============================================================
     * MATERIAL SUBSTITUTIONS
     * ============================================================
     */

    async getMaterialSubstitutions(filters = {}) {
        let url = '/material-substitutions/?';
        
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.page) url += `page=${filters.page}&`;

        return this.call(url);
    }

    async getMaterialSubstitutionDetail(subId) {
        return this.call(`/material-substitutions/${subId}/`);
    }

    async approveMaterialSubstitution(subId, notes = '') {
        return this.call(`/material-substitutions/${subId}/approve/`, 'POST', { notes });
    }

    async rejectMaterialSubstitution(subId, reason) {
        return this.call(`/material-substitutions/${subId}/reject/`, 'POST', { reason });
    }

    /**
     * ============================================================
     * QC INSPECTIONS
     * ============================================================
     */

    async getQCInspections(filters = {}) {
        let url = '/qc-inspections/?';
        
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.page) url += `page=${filters.page}&`;

        return this.call(url);
    }

    async getQCInspectionDetail(inspectionId) {
        return this.call(`/qc-inspections/${inspectionId}/`);
    }

    async createQCInspection(data) {
        return this.call('/qc-inspections/', 'POST', data);
    }

    async updateQCInspection(inspectionId, data) {
        return this.call(`/qc-inspections/${inspectionId}/`, 'PATCH', data);
    }

    /**
     * ============================================================
     * ANALYTICS & METRICS
     * ============================================================
     */

    async getProductionAnalytics() {
        return this.call('/production-analytics/');
    }

    async getVendorAnalytics() {
        return this.call('/vendor-analytics/');
    }

    async getJobAnalytics(filters = {}) {
        let url = '/job-analytics/?';
        
        if (filters.date_from) url += `date_from=${filters.date_from}&`;
        if (filters.date_to) url += `date_to=${filters.date_to}&`;

        return this.call(url);
    }

    async getInvoiceAnalytics(filters = {}) {
        let url = '/invoice-analytics/?';
        
        if (filters.date_from) url += `date_from=${filters.date_from}&`;
        if (filters.date_to) url += `date_to=${filters.date_to}&`;

        return this.call(url);
    }

    /**
     * ============================================================
     * NOTIFICATIONS
     * ============================================================
     */

    async getNotifications() {
        return this.call('/notifications/');
    }

    async markNotificationAsRead(notificationId) {
        return this.call(`/notifications/${notificationId}/mark-read/`, 'POST');
    }

    async markAllNotificationsAsRead() {
        return this.call('/notifications/mark-all-read/', 'POST');
    }

    /**
     * ============================================================
     * FILE MANAGEMENT
     * ============================================================
     */

    async uploadFile(file, progressCallback = null) {
        const formData = new FormData();
        formData.append('file', file);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            if (progressCallback) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        progressCallback(percentComplete);
                    }
                });
            }

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            });

            xhr.addEventListener('error', () => reject(new Error('Upload failed')));

            xhr.open('POST', `${this.baseUrl}/files/upload/`, true);
            xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
            xhr.setRequestHeader('X-CSRFToken', this.getCsrfToken());
            xhr.send(formData);
        });
    }

    /**
     * ============================================================
     * HELPER METHODS
     * ============================================================
     */

    getToken() {
        return localStorage.getItem('access_token');
    }

    setToken(token) {
        localStorage.setItem('access_token', token);
        this.token = token;
    }

    clearToken() {
        localStorage.removeItem('access_token');
        this.token = null;
    }

    getCsrfToken() {
        const name = 'csrftoken';
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

    /**
     * Batch operations
     */
    async batchApproveInvoices(invoiceIds, notes = '') {
        return Promise.all(
            invoiceIds.map(id => this.approveInvoice(id, notes))
        );
    }

    async batchRejectInvoices(invoiceIds, reason) {
        return Promise.all(
            invoiceIds.map(id => this.rejectInvoice(id, reason))
        );
    }

    async batchApproveProofs(proofIds, notes = '') {
        return Promise.all(
            proofIds.map(id => this.approveProof(id, notes))
        );
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PTPortalAPI;
}
