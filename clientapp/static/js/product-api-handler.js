/**
 * Product API Handler
 * Handles all API communication for product create/edit form
 * Integrates with ProductViewSet endpoints
 */

class ProductAPIHandler {
    constructor(productId = null) {
        this.productId = productId;
        this.apiBaseUrl = '/api/v1/products/';
        this.csrfToken = this.getCsrfToken();
        this.form = document.getElementById('productForm');
        this.isAutoSave = false;
    }

    /**
     * Get CSRF token from cookie or form
     */
    getCsrfToken() {
        // Try to get from cookie first
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

        // If not in cookie, try meta tag
        if (!cookieValue) {
            const token = document.querySelector('[name="csrfmiddlewaretoken"]');
            if (token) {
                cookieValue = token.value;
            }
        }

        return cookieValue;
    }

    /**
     * Get common fetch headers
     */
    getHeaders(includeContentType = true) {
        const headers = {
            'X-CSRFToken': this.csrfToken,
            'Accept': 'application/json',
        };
        
        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }
        
        return headers;
    }

    /**
     * Extract form data and convert to JSON
     */
    getFormDataAsJson() {
        const formData = new FormData(this.form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Skip file inputs and hidden action fields
            if (value instanceof File || key.startsWith('delete_') || key === 'next_tab') {
                continue;
            }

            // Handle checkboxes
            if (key.includes('[]')) {
                const realKey = key.replace('[]', '');
                if (!data[realKey]) {
                    data[realKey] = [];
                }
                data[realKey].push(value);
            } else if (data[key]) {
                // If key already exists, convert to array
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }

        // Handle boolean fields
        ['feature_product', 'bestseller_badge', 'new_arrival'].forEach(field => {
            data[field] = this.form.querySelector(`input[name="${field}"]`)?.checked || false;
        });

        return data;
    }

    /**
     * Create new product via API
     */
    async createProduct(data) {
        try {
            const response = await fetch(this.apiBaseUrl, {
                method: 'POST',
                headers: this.getHeaders(true),
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to create product');
            }

            const result = await response.json();
            this.productId = result.id;
            this.form.dataset.productId = result.id;
            
            return result;
        } catch (error) {
            console.error('Create product error:', error);
            throw error;
        }
    }

    /**
     * Update existing product via API
     */
    async updateProduct(data, isPartial = true) {
        if (!this.productId || this.productId === 'new') {
            throw new Error('Product ID not set');
        }

        try {
            const method = isPartial ? 'PATCH' : 'PUT';
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/`, {
                method: method,
                headers: this.getHeaders(true),
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || `Failed to ${isPartial ? 'update' : 'replace'} product`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Update product error:', error);
            throw error;
        }
    }

    /**
     * Save product draft
     */
    async saveDraft(data = null, isAutoSave = false) {
        // For new products (no productId yet), use createProduct via POST
        if (this.productId === 'new' || !this.productId) {
            try {
                const formData = this.getFormDataAsJson();
                
                // For auto-save from image upload, create minimal product with required fields only
                if (isAutoSave) {
                    // Ensure we have minimum required fields for a draft product
                    // Only include fields that have values or have defaults
                    const minimalData = {
                        name: formData.name || 'New Product (Draft)',
                        short_description: formData.short_description || 'Product description',
                        long_description: formData.long_description || 'Full product description',
                        product_type: formData.product_type || 'physical',
                        customization_level: formData.customization_level || 'fully_customizable',
                        status: 'draft',
                        is_visible: false, // Don't show draft products
                        visibility: formData.visibility || 'hidden',
                    };
                    
                    // Remove base_price for fully customizable drafts
                    if (minimalData.customization_level === 'fully_customizable') {
                        minimalData.base_price = null;
                    }
                    
                    const response = await fetch(this.apiBaseUrl, {
                        method: 'POST',
                        headers: this.getHeaders(true),
                        body: JSON.stringify(minimalData),
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        console.error('Detailed error response:', error);
                        throw new Error(error.detail || JSON.stringify(error) || 'Save failed');
                    }

                    const result = await response.json();
                    
                    // Update product ID if new
                    if (result.id && (this.productId === 'new' || !this.productId)) {
                        this.productId = result.id;
                        this.form.dataset.productId = result.id;
                    }
                    
                    return true; // Silent success for auto-save
                }
                
                // Regular draft save with full form data
                // Ensure base_price is set only if needed
                if (!formData.customization_level) {
                    formData.customization_level = 'fully_customizable';
                }
                
                // For draft, allow null base_price for non-customizable
                // The API will validate on publish
                if (formData.customization_level === 'fully_customizable') {
                    delete formData.base_price; // Remove base_price for fully customizable
                }
                
                // Set product status to draft
                formData.status = 'draft';
                
                const response = await fetch(this.apiBaseUrl, {
                    method: 'POST',
                    headers: this.getHeaders(true),
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || error.base_price?.[0] || error.error || 'Save failed');
                }

                const result = await response.json();
                
                // Update product ID if new
                if (result.id && (this.productId === 'new' || !this.productId)) {
                    this.productId = result.id;
                    this.form.dataset.productId = result.id;
                }
                
                this.showNotification('Draft saved successfully', 'success');
                return true;
            } catch (error) {
                this.showNotification(`Draft save failed: ${error.message}`, 'error');
                console.error('Save draft error:', error);
                return false;
            }
        }
        
        // For existing products, use PATCH to update
        try {
            const formData = data || this.getFormDataAsJson();
            
            // Remove base_price validation for draft saves
            // Only enforce base_price requirement on publish
            
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/`, {
                method: 'PATCH',
                headers: this.getHeaders(true),
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const error = await response.json();
                
                // If it's a base_price error and product is non-customizable draft, ignore it
                if (error.base_price && formData.customization_level !== 'fully_customizable') {
                    console.warn('base_price validation warning (will be enforced on publish):', error.base_price);
                    // Try again without base_price
                    const formDataWithoutPrice = { ...formData };
                    delete formDataWithoutPrice.base_price;
                    
                    const retryResponse = await fetch(`${this.apiBaseUrl}${this.productId}/`, {
                        method: 'PATCH',
                        headers: this.getHeaders(true),
                        body: JSON.stringify(formDataWithoutPrice),
                    });
                    
                    if (retryResponse.ok) {
                        this.showNotification('Draft saved (Note: base price required to publish)', 'info');
                        return true;
                    }
                }
                
                throw new Error(error.detail || error.base_price?.[0] || error.error || 'Save failed');
            }

            const result = await response.json();
            this.showNotification('Draft saved successfully', 'success');
            return true;
        } catch (error) {
            this.showNotification(`Draft save failed: ${error.message}`, 'error');
            console.error('Save draft error:', error);
            return false;
        }
    }

    /**
     * Publish product
     */
    async publishProduct() {
        if (this.productId === 'new' || !this.productId) {
            this.showNotification('Please save the product first', 'warning');
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/publish/`, {
                method: 'POST',
                headers: this.getHeaders(true),
                body: JSON.stringify({}),
            });

            if (!response.ok) {
                const error = await response.json();
                let errorMsg = error.detail || error.error || 'Failed to publish product';
                
                // Provide helpful error message for base_price
                if (error.base_price) {
                    errorMsg = `Base price is required for non-customizable products. ${error.base_price[0] || ''}`;
                }
                
                throw new Error(errorMsg);
            }

            this.showNotification('Product published successfully', 'success');
            return true;
        } catch (error) {
            this.showNotification(`Publish failed: ${error.message}`, 'error');
            console.error('Publish error:', error);
            return false;
        }
    }

    /**
     * Archive product
     */
    async archiveProduct() {
        if (!this.productId || this.productId === 'new') {
            this.showNotification('Please save the product first', 'warning');
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/archive/`, {
                method: 'POST',
                headers: this.getHeaders(true),
                body: JSON.stringify({}),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to archive product');
            }

            this.showNotification('Product archived successfully', 'success');
            return true;
        } catch (error) {
            this.showNotification(`Archive failed: ${error.message}`, 'error');
            console.error('Archive error:', error);
            return false;
        }
    }

    /**
     * Upload primary image
     */
    async uploadPrimaryImage(file) {
        // If product doesn't exist yet, auto-save it first
        if (!this.productId || this.productId === 'new') {
            const data = this.getFormDataAsJson();
            const saveSuccess = await this.saveDraft(data, true); // isAutoSave = true
            if (!saveSuccess) {
                this.showNotification('Could not create product for image. Please fill in basic product details first.', 'warning');
                return false;
            }
            // productId is now updated by saveDraft()
        }

        try {
            const formData = new FormData();
            formData.append('image', file);
            formData.append('alt_text', file.name.replace(/\.[^/.]+$/, ''));

            const response = await fetch(`${this.apiBaseUrl}${this.productId}/upload_primary_image/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                },
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to upload primary image');
            }

            const result = await response.json();
            this.showNotification('Primary image uploaded successfully', 'success');
            return result;
        } catch (error) {
            this.showNotification(`Image upload failed: ${error.message}`, 'error');
            console.error('Upload primary image error:', error);
            return false;
        }
    }

    /**
     * Upload gallery images (bulk)
     */
    async uploadGalleryImages(files) {
        // If product doesn't exist yet, auto-save it first
        if (!this.productId || this.productId === 'new') {
            const data = this.getFormDataAsJson();
            const saveSuccess = await this.saveDraft(data, true); // isAutoSave = true
            if (!saveSuccess) {
                this.showNotification('Could not create product for images. Please fill in basic product details first.', 'warning');
                return false;
            }
            // productId is now updated by saveDraft()
        }

        if (files.length > 10) {
            this.showNotification('Maximum 10 images per batch. Please upload in smaller batches.', 'warning');
            return false;
        }

        try {
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('images', files[i]);
            }

            const response = await fetch(`${this.apiBaseUrl}${this.productId}/upload_gallery_images/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                },
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to upload gallery images');
            }

            const result = await response.json();
            this.showNotification(`${files.length} images uploaded successfully`, 'success');
            return result;
        } catch (error) {
            this.showNotification(`Gallery upload failed: ${error.message}`, 'error');
            console.error('Upload gallery images error:', error);
            return false;
        }
    }

    /**
     * Add video to product
     */
    async addVideo(videoUrl) {
        // If product doesn't exist yet, auto-save it first
        if (!this.productId || this.productId === 'new') {
            const data = this.getFormDataAsJson();
            const saveSuccess = await this.saveDraft(data, true); // isAutoSave = true
            if (!saveSuccess) {
                this.showNotification('Could not create product for video. Please fill in basic product details first.', 'warning');
                return false;
            }
            // productId is now updated by saveDraft()
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/add_video/`, {
                method: 'POST',
                headers: this.getHeaders(true),
                body: JSON.stringify({ video_url: videoUrl }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to add video');
            }

            const result = await response.json();
            this.showNotification('Video added successfully', 'success');
            return result;
        } catch (error) {
            this.showNotification(`Video add failed: ${error.message}`, 'error');
            console.error('Add video error:', error);
            return false;
        }
    }

    /**
     * Calculate price
     */
    async calculatePrice(quantity, includeBreakdown = false) {
        if (!this.productId || this.productId === 'new') {
            this.showNotification('Please save the product first', 'warning');
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/calculate_price/`, {
                method: 'POST',
                headers: this.getHeaders(true),
                body: JSON.stringify({
                    quantity: quantity,
                    include_breakdown: includeBreakdown,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to calculate price');
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Calculate price error:', error);
            throw error;
        }
    }

    /**
     * Delete product video
     */
    async deleteVideo(videoId) {
        if (!this.productId || this.productId === 'new') {
            this.showNotification('Product not saved yet', 'warning');
            return false;
        }

        if (!confirm('Are you sure you want to delete this video?')) {
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/videos/${videoId}/`, {
                method: 'DELETE',
                headers: this.getHeaders(false),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to delete video');
            }

            this.showNotification('Video deleted successfully', 'success');
            return true;
        } catch (error) {
            this.showNotification(`Delete video failed: ${error.message}`, 'error');
            console.error('Delete video error:', error);
            return false;
        }
    }

    /**
     * Delete product image
     */
    async deleteImage(imageId) {
        if (!this.productId || this.productId === 'new') {
            this.showNotification('Product not saved yet', 'warning');
            return false;
        }

        if (!confirm('Are you sure you want to delete this image?')) {
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/images/${imageId}/`, {
                method: 'DELETE',
                headers: this.getHeaders(false),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to delete image');
            }

            this.showNotification('Image deleted successfully', 'success');
            return true;
        } catch (error) {
            this.showNotification(`Delete image failed: ${error.message}`, 'error');
            console.error('Delete image error:', error);
            return false;
        }
    }

    /**
     * Delete downloadable file
     */
    async deleteFile(fileId) {
        if (!this.productId || this.productId === 'new') {
            this.showNotification('Product not saved yet', 'warning');
            return false;
        }

        if (!confirm('Are you sure you want to delete this file?')) {
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/files/${fileId}/`, {
                method: 'DELETE',
                headers: this.getHeaders(false),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || error.error || 'Failed to delete file');
            }

            this.showNotification('File deleted successfully', 'success');
            return true;
        } catch (error) {
            this.showNotification(`Delete file failed: ${error.message}`, 'error');
            console.error('Delete file error:', error);
            return false;
        }
    }
    async getChangeHistory() {
        if (!this.productId || this.productId === 'new') {
            return [];
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${this.productId}/change_history/`, {
                method: 'GET',
                headers: this.getHeaders(false),
            });

            if (!response.ok) {
                console.error('Failed to fetch change history');
                return [];
            }

            const result = await response.json();
            return result.results || result;
        } catch (error) {
            console.error('Get change history error:', error);
            return [];
        }
    }

    /**
     * Show notification/toast
     */
    showNotification(message, type = 'info') {
        // Create toast element if it doesn't exist
        let toast = document.getElementById('apiToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'apiToast';
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 16px 20px;
                border-radius: 8px;
                font-size: 14px;
                z-index: 9999;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                animation: slideIn 0.3s ease-in-out;
            `;
            document.body.appendChild(toast);
        }

        // Set styling based on type
        const colorMap = {
            success: { bg: '#10b981', text: '#fff' },
            error: { bg: '#ef4444', text: '#fff' },
            warning: { bg: '#f59e0b', text: '#fff' },
            info: { bg: '#3b82f6', text: '#fff' },
        };

        const colors = colorMap[type] || colorMap.info;
        toast.style.backgroundColor = colors.bg;
        toast.style.color = colors.text;
        toast.textContent = message;

        // Clear previous timeout
        if (toast.timeout) {
            clearTimeout(toast.timeout);
        }

        // Auto remove after 4 seconds
        toast.timeout = setTimeout(() => {
            toast.remove();
        }, 4000);

        return toast;
    }

    /**
     * Initialize form handlers
     */
    initializeFormHandlers(callbacks = {}) {
        // Save Draft button
        const saveDraftBtns = document.querySelectorAll('button[name="action"][value="save_draft"]');
        saveDraftBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const data = this.getFormDataAsJson();
                const success = await this.saveDraft(data);
                if (success && callbacks.onSaveDraft) {
                    callbacks.onSaveDraft();
                }
            });
        });

        // Publish button - FOR NEW PRODUCTS: save first, then submit form
        // FOR EXISTING PRODUCTS: let form submit naturally with action=publish
        const publishBtns = document.querySelectorAll('button[name="action"][value="publish"]');
        publishBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                // If product is brand new, must save draft first
                if (this.productId === 'new' || !this.productId) {
                    e.preventDefault();
                    const data = this.getFormDataAsJson();
                    const saveSuccess = await this.saveDraft(data);
                    if (!saveSuccess) {
                        this.showNotification('Failed to save product. Please fix errors and try again.', 'error');
                        return;
                    }
                    
                    // After successful save, set action to publish and submit
                    this.form.dataset.productId = this.productId;
                    
                    // Create a hidden input for the publish action
                    let actionInput = this.form.querySelector('input[name="action"]');
                    if (!actionInput) {
                        actionInput = document.createElement('input');
                        actionInput.type = 'hidden';
                        actionInput.name = 'action';
                        this.form.appendChild(actionInput);
                    }
                    actionInput.value = 'publish';
                    
                    // Now submit the form with action=publish
                    this.form.submit();
                } else {
                    // Product exists, let form submit naturally
                    // Don't prevent default - the form submission will handle the publish
                }
            });
        });

        // Primary image upload
        const primaryImageInput = document.getElementById('primary_image_input');
        if (primaryImageInput) {
            const primaryImageContainer = document.getElementById('primary-image-container');
            
            primaryImageContainer?.addEventListener('click', () => {
                primaryImageInput.click();
            });

            primaryImageInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    const success = await this.uploadPrimaryImage(file);
                    if (success && callbacks.onImageUpload) {
                        callbacks.onImageUpload(success);
                    }
                }
            });
        }

        // Gallery images upload
        const galleryImageInput = document.getElementById('gallery_images_input');
        if (galleryImageInput) {
            galleryImageInput.addEventListener('change', async (e) => {
                const files = Array.from(e.target.files);
                if (files.length > 0) {
                    const success = await this.uploadGalleryImages(files);
                    if (success && callbacks.onGalleryUpload) {
                        callbacks.onGalleryUpload(success);
                    }
                }
                // Clear input
                e.target.value = '';
            });
        }

        // Video add button
        const videoUrlInput = document.getElementById('new-video-url');
        const addVideoBtn = document.getElementById('add-video-btn') || (videoUrlInput ? videoUrlInput.nextElementSibling : null);
        
        if (addVideoBtn && videoUrlInput) {
            addVideoBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                const url = videoUrlInput.value.trim();
                if (url) {
                    const success = await this.addVideo(url);
                    if (success && callbacks.onVideoAdd) {
                        callbacks.onVideoAdd(success);
                    }
                    videoUrlInput.value = '';
                }
            });
        }

        // Delete video buttons
        document.querySelectorAll('.delete-video').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const videoId = btn.dataset.videoId;
                const success = await this.deleteVideo(videoId);
                if (success) {
                    btn.closest('div[class*="flex items-center gap-4"]')?.remove();
                }
            });
        });

        // Delete gallery image buttons
        document.querySelectorAll('.delete-gallery-image').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const imageId = btn.dataset.imageId;
                const success = await this.deleteImage(imageId);
                if (success) {
                    btn.closest('.gallery-image-item')?.remove();
                }
            });
        });

        // Delete file buttons
        document.querySelectorAll('.delete-file').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const fileId = btn.dataset.fileId;
                const success = await this.deleteFile(fileId);
                if (success) {
                    btn.closest('div[class*="flex items-center"]')?.remove();
                }
            });
        });
    }

    /**
     * Auto-save with form change detection
     */
    setupAutoSave(autoSaveDelay = 30000) {
        let autoSaveTimeout = null;
        let initialFormState = new FormData(this.form);

        const hasFormChanged = () => {
            const currentFormData = new FormData(this.form);
            const initialKeys = Array.from(initialFormState.keys());
            const currentKeys = Array.from(currentFormData.keys());

            if (initialKeys.length !== currentKeys.length) return true;

            for (let key of initialKeys) {
                const initialValue = initialFormState.get(key);
                const currentValue = currentFormData.get(key);
                if (initialValue !== currentValue) return true;
            }

            return false;
        };

        this.form.querySelectorAll('input, select, textarea').forEach(field => {
            if (field.type === 'hidden' || field.type === 'file') return;

            field.addEventListener('change', () => {
                if (hasFormChanged() && this.productId !== 'new') {
                    // Clear existing timeout
                    if (autoSaveTimeout) clearTimeout(autoSaveTimeout);

                    // Set new timeout
                    autoSaveTimeout = setTimeout(async () => {
                        const data = this.getFormDataAsJson();
                        await this.saveDraft(data);
                        initialFormState = new FormData(this.form);
                    }, autoSaveDelay);
                }
            });
        });
    }
}

// Export for use in templates
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProductAPIHandler;
}
