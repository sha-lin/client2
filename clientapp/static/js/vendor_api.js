/**
 * Vendor Portal API Service Layer
 * Centralizes all API calls to backend endpoints
 * Usage: const api = new VendorAPI(vendorId);
 */

class VendorAPI {
  constructor(vendorId, baseUrl = '/api') {
    this.vendorId = vendorId;
    this.baseUrl = baseUrl;
    this.csrfToken = this.getCsrfToken();
  }

  /**
   * Get CSRF token from page or form
   */
  getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
  }

  /**
   * Get common headers for all requests
   */
  getHeaders(includeContent = true) {
    const headers = {};
    if (includeContent) {
      headers['Content-Type'] = 'application/json';
    }
    if (this.csrfToken) {
      headers['X-CSRFToken'] = this.csrfToken;
    }
    return headers;
  }

  /**
   * Handle API errors with user-friendly messages
   */
  handleError(error, defaultMessage = 'API Error') {
    console.error('API Error:', error);
    if (error.response) {
      return error.response.data?.detail || error.response.data?.message || defaultMessage;
    }
    return error.message || defaultMessage;
  }

  /**
   * Generic GET request
   */
  async get(endpoint) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: this.getHeaders()
      });
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.response = await response.json();
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Generic POST request
   */
  async post(endpoint, data = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.response = await response.json();
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Generic PATCH request
   */
  async patch(endpoint, data = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'PATCH',
        headers: this.getHeaders(),
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.response = await response.json();
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * File upload (multipart/form-data)
   */
  async uploadFile(endpoint, formData) {
    try {
      const headers = {};
      if (this.csrfToken) {
        headers['X-CSRFToken'] = this.csrfToken;
      }
      
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers,
        body: formData
      });
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.response = await response.json();
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ================================================================
  // DASHBOARD API CALLS
  // ================================================================

  /**
   * Get vendor dashboard statistics
   * GET /api/purchase-orders/vendor_dashboard/
   */
  async getDashboardStats() {
    return this.get(`/purchase-orders/vendor_dashboard/?vendor_id=${this.vendorId}`);
  }

  // ================================================================
  // PURCHASE ORDER API CALLS
  // ================================================================

  /**
   * Get list of purchase orders
   * GET /api/purchase-orders/?vendor_id={id}&status={status}&search={search}
   */
  async getPurchaseOrders(filters = {}) {
    const params = new URLSearchParams({
      vendor_id: this.vendorId,
      ...filters
    });
    return this.get(`/purchase-orders/?${params.toString()}`);
  }

  /**
   * Get single purchase order details
   * GET /api/purchase-orders/{id}/
   */
  async getPurchaseOrder(poId) {
    return this.get(`/purchase-orders/${poId}/`);
  }

  /**
   * Vendor accepts a purchase order
   * POST /api/purchase-orders/{id}/accept/
   */
  async acceptPO(poId) {
    return this.post(`/purchase-orders/${poId}/accept/`);
  }

  /**
   * Vendor declines a purchase order
   * POST /api/purchase-orders/{id}/decline/
   */
  async declinePO(poId, reason = '') {
    return this.post(`/purchase-orders/${poId}/decline/`, { reason });
  }

  /**
   * Update PO milestone
   * POST /api/purchase-orders/{id}/update_milestone/
   */
  async updateMilestone(poId, milestone, notes = '') {
    return this.post(`/purchase-orders/${poId}/update_milestone/`, {
      milestone,
      notes
    });
  }

  /**
   * Mark PO assets as acknowledged
   * POST /api/purchase-orders/{id}/acknowledge_assets/
   */
  async acknowledgeAssets(poId) {
    return this.post(`/purchase-orders/${poId}/acknowledge_assets/`);
  }

  /**
   * Get coordination jobs (related POs in same coordination group)
   * GET /api/purchase-orders/{id}/coordination_jobs/
   */
  async getCoordinationJobs(poId) {
    return this.get(`/purchase-orders/${poId}/coordination_jobs/`);
  }

  // ================================================================
  // INVOICE API CALLS
  // ================================================================

  /**
   * Get list of invoices
   * GET /api/vendor-invoices/?vendor_id={id}&status={status}
   */
  async getInvoices(filters = {}) {
    const params = new URLSearchParams({
      vendor_id: this.vendorId,
      ...filters
    });
    return this.get(`/vendor-invoices/?${params.toString()}`);
  }

  /**
   * Get single invoice details
   * GET /api/vendor-invoices/{id}/
   */
  async getInvoice(invoiceId) {
    return this.get(`/vendor-invoices/${invoiceId}/`);
  }

  /**
   * Create new invoice (draft)
   * POST /api/vendor-invoices/
   */
  async createInvoice(invoiceData) {
    return this.post('/vendor-invoices/', {
      vendor: this.vendorId,
      ...invoiceData
    });
  }

  /**
   * Update invoice (while in draft status)
   * PATCH /api/vendor-invoices/{id}/
   */
  async updateInvoice(invoiceId, invoiceData) {
    return this.patch(`/vendor-invoices/${invoiceId}/`, invoiceData);
  }

  /**
   * Submit invoice for review
   * POST /api/vendor-invoices/{id}/submit/
   */
  async submitInvoice(invoiceId) {
    return this.post(`/vendor-invoices/${invoiceId}/submit/`);
  }

  /**
   * Approve invoice (PT only)
   * POST /api/vendor-invoices/{id}/approve/
   */
  async approveInvoice(invoiceId) {
    return this.post(`/vendor-invoices/${invoiceId}/approve/`);
  }

  /**
   * Reject invoice with reason
   * POST /api/vendor-invoices/{id}/reject/
   */
  async rejectInvoice(invoiceId, reason = '') {
    return this.post(`/vendor-invoices/${invoiceId}/reject/`, { reason });
  }

  /**
   * Download invoice PDF
   * GET /api/vendor-invoices/{id}/download/
   */
  async downloadInvoice(invoiceId) {
    window.location.href = `${this.baseUrl}/vendor-invoices/${invoiceId}/download/`;
  }

  // ================================================================
  // PURCHASE ORDER PROOF API CALLS
  // ================================================================

  /**
   * Get list of proofs for a PO
   * GET /api/purchase-order-proofs/?purchase_order={id}
   */
  async getProofs(poId) {
    const params = new URLSearchParams({ purchase_order: poId });
    return this.get(`/purchase-order-proofs/?${params.toString()}`);
  }

  /**
   * Upload proof file
   * POST /api/purchase-order-proofs/ (multipart/form-data)
   */
  async uploadProof(poId, file, description = '') {
    const formData = new FormData();
    formData.append('purchase_order', poId);
    formData.append('proof_file', file);
    formData.append('description', description);
    
    return this.uploadFile('/purchase-order-proofs/', formData);
  }

  /**
   * Update proof status
   * PATCH /api/purchase-order-proofs/{id}/
   */
  async updateProof(proofId, status, notes = '') {
    return this.patch(`/purchase-order-proofs/${proofId}/`, {
      status,
      notes
    });
  }

  /**
   * Approve proof
   * POST /api/purchase-order-proofs/{id}/approve/
   */
  async approveProof(proofId) {
    return this.post(`/purchase-order-proofs/${proofId}/approve/`);
  }

  /**
   * Reject proof with reason
   * POST /api/purchase-order-proofs/{id}/reject/
   */
  async rejectProof(proofId, reason = '') {
    return this.post(`/purchase-order-proofs/${proofId}/reject/`, { reason });
  }

  // ================================================================
  // PURCHASE ORDER ISSUE API CALLS
  // ================================================================

  /**
   * Get issues for a PO
   * GET /api/purchase-order-issues/?purchase_order={id}
   */
  async getIssues(poId) {
    const params = new URLSearchParams({ purchase_order: poId });
    return this.get(`/purchase-order-issues/?${params.toString()}`);
  }

  /**
   * Create new issue
   * POST /api/purchase-order-issues/
   */
  async createIssue(poId, issueData) {
    return this.post('/purchase-order-issues/', {
      purchase_order: poId,
      ...issueData
    });
  }

  /**
   * Resolve issue
   * PATCH /api/purchase-order-issues/{id}/
   */
  async resolveIssue(issueId, resolution = '') {
    return this.patch(`/purchase-order-issues/${issueId}/`, {
      status: 'resolved',
      resolution
    });
  }

  // ================================================================
  // PURCHASE ORDER NOTE API CALLS
  // ================================================================

  /**
   * Get notes for a PO
   * GET /api/purchase-order-notes/?purchase_order={id}
   */
  async getNotes(poId) {
    const params = new URLSearchParams({ purchase_order: poId });
    return this.get(`/purchase-order-notes/?${params.toString()}`);
  }

  /**
   * Create new note
   * POST /api/purchase-order-notes/
   */
  async createNote(poId, noteText) {
    return this.post('/purchase-order-notes/', {
      purchase_order: poId,
      note: noteText
    });
  }

  /**
   * Delete note (if user is owner)
   * DELETE /api/purchase-order-notes/{id}/
   */
  async deleteNote(noteId) {
    const response = await fetch(`${this.baseUrl}/purchase-order-notes/${noteId}/`, {
      method: 'DELETE',
      headers: this.getHeaders(false)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete note: HTTP ${response.status}`);
    }
    
    return true;
  }

  // ================================================================
  // MATERIAL SUBSTITUTION REQUEST API CALLS
  // ================================================================

  /**
   * Create material substitution request
   * POST /api/material-substitution-requests/
   */
  async requestMaterialSubstitution(poId, substitutionData) {
    return this.post('/material-substitution-requests/', {
      purchase_order: poId,
      ...substitutionData
    });
  }

  /**
   * Get substitution requests for a PO
   * GET /api/material-substitution-requests/?purchase_order={id}
   */
  async getSubstitutionRequests(poId) {
    const params = new URLSearchParams({ purchase_order: poId });
    return this.get(`/material-substitution-requests/?${params.toString()}`);
  }

  // ================================================================
  // PERFORMANCE API CALLS
  // ================================================================

  /**
   * Get vendor performance scorecard
   * GET /api/vendor-performance/scorecard/
   */
  async getPerformanceScorecard() {
    return this.get(`/vendor-performance/scorecard/?vendor_id=${this.vendorId}`);
  }

  /**
   * Get performance trends (historical data)
   * GET /api/vendor-performance/trends/
   */
  async getPerformanceTrends() {
    return this.get(`/vendor-performance/trends/?vendor_id=${this.vendorId}`);
  }

  /**
   * Get performance insights
   * GET /api/vendor-performance/insights/
   */
  async getPerformanceInsights() {
    return this.get(`/vendor-performance/insights/?vendor_id=${this.vendorId}`);
  }

  // ================================================================
  // UTILITY METHODS
  // ================================================================

  /**
   * Format currency
   */
  static formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  }

  /**
   * Format date
   */
  static formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  /**
   * Format datetime
   */
  static formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Get status badge class
   */
  static getStatusClass(status) {
    const statusMap = {
      'draft': 'badge-info',
      'submitted': 'badge-warning',
      'approved': 'badge-success',
      'rejected': 'badge-danger',
      'paid': 'badge-success',
      'new': 'badge-info',
      'in_production': 'badge-warning',
      'quality_check': 'badge-info',
      'completed': 'badge-success',
      'cancelled': 'badge-danger',
      'open': 'badge-warning',
      'resolved': 'badge-success'
    };
    return statusMap[status] || 'badge-secondary';
  }

  /**
   * Get status display name
   */
  static getStatusDisplay(status) {
    const displayMap = {
      'in_production': 'In Production',
      'quality_check': 'Quality Check',
      'awaiting_acceptance': 'Awaiting Acceptance',
      'delivery_coordination': 'Delivery Coordination',
      'awaiting_approval': 'Awaiting Approval',
      'awaiting_payment': 'Awaiting Payment'
    };
    return displayMap[status] || status;
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = VendorAPI;
}
