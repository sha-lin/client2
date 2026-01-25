/**
 * Client Onboarding Page JavaScript
 * Handles B2B/B2C form switching, validation, and AJAX submission
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // CLIENT TYPE SWITCHING (B2B vs B2C)
    // ============================================================

    const clientTypeRadios = document.querySelectorAll('input[name="client_type"]');
    const b2bSection = document.getElementById('b2b-fields');
    const b2cSection = document.getElementById('b2c-fields');

    clientTypeRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            const isB2B = this.value === 'B2B';

            if (b2bSection) {
                b2bSection.style.display = isB2B ? 'block' : 'none';
                // Toggle required fields
                b2bSection.querySelectorAll('[data-b2b-required]').forEach(input => {
                    input.required = isB2B;
                });
            }

            if (b2cSection) {
                b2cSection.style.display = isB2B ? 'none' : 'block';
                b2cSection.querySelectorAll('[data-b2c-required]').forEach(input => {
                    input.required = !isB2B;
                });
            }

            // Update form labels
            const companyLabel = document.querySelector('label[for="company"]');
            if (companyLabel) {
                companyLabel.textContent = isB2B ? 'Company Name *' : 'Company Name (Optional)';
            }
        });
    });

    // ============================================================
    // TAX PIN VALIDATION (Kenya)
    // ============================================================

    const taxPinInput = document.querySelector('input[name="tax_pin"]');

    if (taxPinInput) {
        taxPinInput.addEventListener('input', function () {
            let value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');

            // Kenya PIN format: A000000000X (letter, 9 digits, letter)
            if (value.length > 11) {
                value = value.substring(0, 11);
            }

            this.value = value;

            // Validate format
            if (value.length === 11) {
                const isValid = /^[A-Z]\d{9}[A-Z]$/.test(value);

                if (isValid) {
                    this.classList.remove('border-red-500');
                    this.classList.add('border-green-500');
                    hideFieldError(this);
                } else {
                    this.classList.remove('border-green-500');
                    this.classList.add('border-red-500');
                    showFieldError(this, 'Invalid PIN format. Expected: A000000000X');
                }
            } else {
                this.classList.remove('border-green-500', 'border-red-500');
            }
        });
    }

    // ============================================================
    // DUPLICATE CHECK ON EMAIL/PHONE
    // ============================================================

    const emailInput = document.querySelector('input[name="email"]');
    const phoneInput = document.querySelector('input[name="phone"]');

    if (emailInput) {
        emailInput.addEventListener('blur', async function () {
            const email = this.value.trim();
            if (email && email.includes('@')) {
                const duplicate = await checkDuplicateClient(email);
                if (duplicate) {
                    showFieldError(this, `A client with this email already exists: ${duplicate.name}`);
                } else {
                    hideFieldError(this);
                }
            }
        });
    }

    if (phoneInput) {
        phoneInput.addEventListener('blur', async function () {
            const phone = this.value.trim();
            if (phone && phone.length >= 10) {
                try {
                    const data = await api.get(`/clients/?phone=${encodeURIComponent(phone)}`);
                    if (data.results && data.results.length > 0) {
                        showFieldError(this, `A client with this phone already exists: ${data.results[0].name}`);
                    } else {
                        hideFieldError(this);
                    }
                } catch (error) {
                    console.log('Error checking phone:', error);
                }
            }
        });
    }

    function showFieldError(input, message) {
        let errorDiv = input.nextElementSibling;
        if (!errorDiv || !errorDiv.classList.contains('field-error')) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-red-500 text-sm mt-1';
            input.parentNode.insertBefore(errorDiv, input.nextSibling);
        }
        errorDiv.textContent = message;
        input.classList.add('border-red-500');
    }

    function hideFieldError(input) {
        const errorDiv = input.nextElementSibling;
        if (errorDiv && errorDiv.classList.contains('field-error')) {
            errorDiv.remove();
        }
        input.classList.remove('border-red-500');
    }

    // ============================================================
    // PHONE NUMBER FORMATTING
    // ============================================================

    if (phoneInput) {
        phoneInput.addEventListener('input', function () {
            // Remove non-numeric except +
            let value = this.value.replace(/[^\d+]/g, '');

            // Ensure starts with + or 0
            if (value && !value.startsWith('+') && !value.startsWith('0')) {
                value = '+' + value;
            }

            this.value = value;
        });
    }

    // ============================================================
    // CREDIT TERMS VALIDATION (B2B)
    // ============================================================

    const creditTermsSelect = document.querySelector('select[name="credit_terms"]');
    const creditLimitInput = document.querySelector('input[name="credit_limit"]');

    if (creditTermsSelect) {
        creditTermsSelect.addEventListener('change', function () {
            const hasCreditTerms = this.value && this.value !== 'COD';

            if (creditLimitInput) {
                creditLimitInput.disabled = !hasCreditTerms;
                creditLimitInput.required = hasCreditTerms;

                if (!hasCreditTerms) {
                    creditLimitInput.value = '';
                }
            }
        });
    }

    // ============================================================
    // FORM SUBMISSION
    // ============================================================

    const onboardingForm = document.getElementById('onboarding-form') || document.querySelector('form');

    if (onboardingForm) {
        onboardingForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            // Client-side validation
            if (!validateForm(this)) {
                return;
            }

            submitBtn.textContent = 'Saving...';
            submitBtn.disabled = true;

            clearFormErrors();
            showLoading('Creating client...');

            try {
                const formData = formToJson(this);

                // Clean up data
                if (formData.client_type === 'B2C') {
                    // Remove B2B-only fields for B2C clients
                    delete formData.tax_pin;
                    delete formData.credit_terms;
                    delete formData.credit_limit;
                    delete formData.business_registration;
                }

                // Handle numeric fields
                if (formData.credit_limit) {
                    formData.credit_limit = parseFloat(formData.credit_limit) || 0;
                }

                // Create client via API
                const response = await api.post('/clients/', formData);

                hideLoading();
                showToast(`Client ${response.client_id} created successfully!`, 'success');

                // Redirect to client profile
                setTimeout(() => {
                    window.location.href = `/clients/${response.id}/`;
                }, 1500);

            } catch (error) {
                hideLoading();
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;

                if (error.data) {
                    showFormErrors(error.data);
                    showToast('Please fix the errors and try again', 'error');
                } else {
                    showToast('Error creating client. Please try again.', 'error');
                }
            }
        });
    }

    function validateForm(form) {
        let isValid = true;
        const clientType = form.querySelector('input[name="client_type"]:checked')?.value || 'B2B';

        // Required fields
        const requiredFields = ['name', 'email', 'phone'];

        if (clientType === 'B2B') {
            requiredFields.push('company');
        }

        requiredFields.forEach(fieldName => {
            const input = form.querySelector(`[name="${fieldName}"]`);
            if (input && !input.value.trim()) {
                showFieldError(input, 'This field is required');
                isValid = false;
            }
        });

        // Email format
        const emailField = form.querySelector('[name="email"]');
        if (emailField && emailField.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailField.value)) {
                showFieldError(emailField, 'Please enter a valid email address');
                isValid = false;
            }
        }

        // TAX PIN format for B2B
        if (clientType === 'B2B' && taxPinInput && taxPinInput.value) {
            const pinRegex = /^[A-Z]\d{9}[A-Z]$/;
            if (!pinRegex.test(taxPinInput.value)) {
                showFieldError(taxPinInput, 'Invalid PIN format. Expected: A000000000X');
                isValid = false;
            }
        }

        if (!isValid) {
            showToast('Please fill in all required fields correctly', 'error');
        }

        return isValid;
    }

    // ============================================================
    // CONTACTS MANAGEMENT (Multiple Contacts)
    // ============================================================

    const addContactBtn = document.getElementById('add-contact-btn');
    const contactsContainer = document.getElementById('contacts-container');
    let contactCounter = 0;

    if (addContactBtn && contactsContainer) {
        addContactBtn.addEventListener('click', function () {
            contactCounter++;

            const contactHtml = `
                <div class="contact-entry border border-gray-200 rounded-lg p-4 mb-3" data-contact-id="${contactCounter}">
                    <div class="flex justify-between items-start mb-3">
                        <h4 class="font-medium text-gray-900">Contact #${contactCounter}</h4>
                        <button type="button" class="text-gray-400 hover:text-red-600" data-action="remove-contact" data-contact-id="${contactCounter}">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
                            <input type="text" name="contact_name_${contactCounter}" class="form-input" placeholder="Contact name">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
                            <input type="text" name="contact_role_${contactCounter}" class="form-input" placeholder="e.g., Procurement Manager">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                            <input type="email" name="contact_email_${contactCounter}" class="form-input" placeholder="contact@example.com">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                            <input type="tel" name="contact_phone_${contactCounter}" class="form-input" placeholder="+254...">
                        </div>
                    </div>
                </div>
            `;

            contactsContainer.insertAdjacentHTML('beforeend', contactHtml);

            // Add remove handler
            const newContact = contactsContainer.querySelector(`[data-contact-id="${contactCounter}"]`);
            newContact.querySelector('[data-action="remove-contact"]').addEventListener('click', function () {
                newContact.remove();
            });
        });
    }

    // ============================================================
    // ADDRESS AUTOCOMPLETE (Optional - with Google Maps)
    // ============================================================

    const addressInput = document.querySelector('input[name="address"]');

    // Only initialize if Google Maps is loaded
    if (addressInput && typeof google !== 'undefined' && google.maps) {
        const autocomplete = new google.maps.places.Autocomplete(addressInput, {
            types: ['address'],
            componentRestrictions: { country: 'ke' } // Kenya
        });

        autocomplete.addListener('place_changed', function () {
            const place = autocomplete.getPlace();

            if (place.address_components) {
                // Auto-fill city if available
                const cityInput = document.querySelector('input[name="city"]');
                const city = place.address_components.find(c => c.types.includes('locality'));
                if (cityInput && city) {
                    cityInput.value = city.long_name;
                }
            }
        });
    }

    // ============================================================
    // BRAND ASSETS UPLOAD
    // ============================================================

    const brandUploadInput = document.getElementById('brand-assets-upload');
    const brandPreviewContainer = document.getElementById('brand-preview');

    if (brandUploadInput) {
        brandUploadInput.addEventListener('change', function () {
            const files = Array.from(this.files);

            if (brandPreviewContainer) {
                brandPreviewContainer.innerHTML = files.map(file => `
                    <div class="flex items-center gap-2 bg-gray-50 rounded px-3 py-2">
                        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                        <span class="text-sm text-gray-700">${file.name}</span>
                        <span class="text-xs text-gray-500">(${(file.size / 1024).toFixed(1)} KB)</span>
                    </div>
                `).join('');
            }
        });
    }

    // ============================================================
    // LEAD CONVERSION AUTO-FILL
    // ============================================================

    // Check if we're converting from a lead
    const urlParams = new URLSearchParams(window.location.search);
    const leadId = urlParams.get('lead_id');

    if (leadId) {
        loadLeadData(leadId);
    }

    async function loadLeadData(leadId) {
        try {
            const lead = await api.get(`/leads/${leadId}/`);

            // Pre-fill form fields
            const fieldMap = {
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'company': lead.company,
                'address': lead.address,
                'notes': lead.notes
            };

            Object.entries(fieldMap).forEach(([name, value]) => {
                const input = document.querySelector(`[name="${name}"]`);
                if (input && value) {
                    input.value = value;
                }
            });

            // Store lead ID for reference
            let leadInput = document.querySelector('input[name="converted_from_lead"]');
            if (!leadInput) {
                leadInput = document.createElement('input');
                leadInput.type = 'hidden';
                leadInput.name = 'converted_from_lead';
                onboardingForm.appendChild(leadInput);
            }
            leadInput.value = leadId;

            showToast('Lead data loaded', 'info');

        } catch (error) {
            console.error('Error loading lead data:', error);
        }
    }

    console.log('Client onboarding page initialized successfully');
});
