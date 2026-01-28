/**
 * Storefront API Client
 * Central hub for all API communications with the backend
 * Handles authentication, error handling, and request/response interception
 */

class StorefrontAPIClient {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;
        this.token = this.getStoredToken();
        this.refreshToken = this.getStoredRefreshToken();
        this.headers = this.buildHeaders();
    }

    /**
     * Build request headers with authentication
     */
    buildHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    /**
     * Store tokens in localStorage
     */
    storeTokens(accessToken, refreshToken) {
        localStorage.setItem('storefront_access_token', accessToken);
        localStorage.setItem('storefront_refresh_token', refreshToken);
        this.token = accessToken;
        this.refreshToken = refreshToken;
        this.headers = this.buildHeaders();
    }

    /**
     * Get stored access token
     */
    getStoredToken() {
        return localStorage.getItem('storefront_access_token');
    }

    /**
     * Get stored refresh token
     */
    getStoredRefreshToken() {
        return localStorage.getItem('storefront_refresh_token');
    }

    /**
     * Clear stored tokens (logout)
     */
    clearTokens() {
        localStorage.removeItem('storefront_access_token');
        localStorage.removeItem('storefront_refresh_token');
        this.token = null;
        this.refreshToken = null;
        this.headers = this.buildHeaders();
    }

    /**
     * Generic request handler
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.headers,
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // Handle 401 Unauthorized - try to refresh token
            if (response.status === 401 && this.refreshToken) {
                await this.refreshAccessToken();
                config.headers = this.buildHeaders();
                return fetch(url, config);
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new APIError(
                    error.detail || `HTTP ${response.status}`,
                    response.status,
                    error
                );
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * PATCH request
     */
    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
        try {
            const response = await fetch(`${this.baseURL}/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                this.storeTokens(data.access, this.refreshToken);
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.clearTokens();
            window.location.href = '/login.html';
        }
    }

    /**
     * ==================== AUTHENTICATION ====================
     */

    /**
     * Register new customer
     */
    async register(email, password, passwordConfirm, firstName, lastName, phone, company) {
        return this.post('/customers/register/', {
            email,
            password,
            password_confirm: passwordConfirm,
            first_name: firstName,
            last_name: lastName,
            phone,
            company
        });
    }

    /**
     * Verify email with token
     */
    async verifyEmail(email, token) {
        return this.post('/customers/verify-email/', {
            email,
            token
        });
    }

    /**
     * Login customer
     */
    async login(email, password) {
        const response = await this.post('/customers/login/', { email, password });
        if (response.access_token && response.refresh_token) {
            this.storeTokens(response.access_token, response.refresh_token);
        }
        return response;
    }

    /**
     * Get current customer profile
     */
    async getProfile() {
        return this.get('/customers/profile/');
    }

    /**
     * Update customer profile
     */
    async updateProfile(data) {
        return this.put('/customers/profile/', data);
    }

    /**
     * ==================== PRODUCTS ====================
     */

    /**
     * Get all products (public - no auth required)
     */
    async getProducts(params = {}) {
        return this.get('/storefront-products/', params);
    }

    /**
     * Get single product details
     */
    async getProduct(productId) {
        return this.get(`/storefront-products/${productId}/`);
    }

    /**
     * Calculate product price with options
     */
    async calculatePrice(productId, quantity, turnaroundTime = 'standard') {
        return this.post(`/storefront-products/${productId}/calculate_price/`, {
            quantity,
            turnaround_time: turnaroundTime
        });
    }

    /**
     * ==================== ESTIMATES/QUOTES ====================
     */

    /**
     * Get all estimates for current customer
     */
    async getEstimates() {
        return this.get('/v1/storefront-estimates/');
    }

    /**
     * Get single estimate
     */
    async getEstimate(estimateId) {
        return this.get(`/v1/storefront-estimates/${estimateId}/`);
    }

    /**
     * Get estimate by share token (public - no auth required)
     */
    async getEstimateByToken(token) {
        return this.get('/v1/storefront-estimates/by_token/', { token });
    }

    /**
     * Create new estimate
     */
    async createEstimate(customerName, customerEmail, customerPhone, customerCompany, lineItems) {
        return this.post('/v1/storefront-estimates/', {
            customer_name: customerName,
            customer_email: customerEmail,
            customer_phone: customerPhone,
            customer_company: customerCompany,
            line_items: lineItems
        });
    }

    /**
     * Update estimate
     */
    async updateEstimate(estimateId, data) {
        return this.put(`/v1/storefront-estimates/${estimateId}/`, data);
    }

    /**
     * Share estimate via WhatsApp
     */
    async shareEstimateWhatsApp(estimateId, phone) {
        return this.post(`/v1/storefront-estimates/${estimateId}/share-whatsapp/`, {
            phone
        });
    }

    /**
     * Share estimate via Email
     */
    async shareEstimateEmail(estimateId, email) {
        return this.post(`/v1/storefront-estimates/${estimateId}/share-email/`, {
            email
        });
    }

    /**
     * Convert estimate to quote (creates internal Quote in system)
     */
    async convertEstimateToQuote(estimateId) {
        return this.post(`/v1/quotes/save-from-storefront/`, {
            estimate_id: estimateId
        });
    }

    /**
     * Get customer quotes
     */
    async getCustomerQuotes(page = 1, limit = 10) {
        return this.get('/customer/quotes/', { page, limit });
    }

    /**
     * ==================== MESSAGES & CONTACT ====================
     */

    /**
     * Send email inquiry
     */
    async sendEmailInquiry(name, email, subject, message) {
        return this.post('/contact/email/', {
            name,
            email,
            subject,
            message
        });
    }

    /**
     * Send WhatsApp inquiry
     */
    async sendWhatsAppInquiry(phone, message, name = null) {
        return this.post('/contact/whatsapp/', {
            phone,
            message,
            name
        });
    }

    /**
     * Request phone call
     */
    async requestCall(name, phone, preferredTime = null) {
        return this.post('/contact/call/', {
            name,
            phone,
            preferred_time: preferredTime
        });
    }

    /**
     * Send message to chatbot
     */
    async sendChatbotMessage(message, conversationId = null) {
        return this.post('/chatbot/message/', {
            message,
            conversation_id: conversationId
        });
    }

    /**
     * Get chatbot knowledge base
     */
    async getChatbotKnowledge() {
        return this.get('/chatbot/knowledge/');
    }

    /**
     * ==================== PRODUCTION UNITS ====================
     */

    /**
     * Get all production units
     */
    async getProductionUnits(jobId = null, status = null) {
        if (jobId) {
            return this.get(`/jobs/${jobId}/production-units/`);
        }
        const params = {};
        if (status) params.status = status;
        return this.get('/v1/production-units/', params);
    }

    /**
     * Get single production unit
     */
    async getProductionUnit(unitId) {
        return this.get(`/v1/production-units/${unitId}/`);
    }

    /**
     * Create production unit
     */
    async createProductionUnit(jobId, vendorId, estimatedStartDate, estimatedEndDate) {
        return this.post('/v1/production-units/', {
            job: jobId,
            vendor: vendorId,
            expected_start_date: estimatedStartDate,
            expected_end_date: estimatedEndDate
        });
    }

    /**
     * Update production unit
     */
    async updateProductionUnit(unitId, data) {
        return this.put(`/v1/production-units/${unitId}/`, data);
    }

    /**
     * Send purchase order for production unit
     */
    async sendPurchaseOrder(unitId) {
        return this.post(`/v1/production-units/${unitId}/send-po/`, {});
    }

    /**
     * Get production unit progress
     */
    async getProductionProgress(unitId) {
        return this.get(`/v1/production-units/${unitId}/progress/`);
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.status = status;
        this.data = data;
        this.name = 'APIError';
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StorefrontAPIClient;
}
