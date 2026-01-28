/**
 * Storefront Authentication Handler
 * Manages login, registration, and authentication flows
 */

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeAuth();
});

// Initialize API client
let api = null;

function initializeAuth() {
    // Create API client instance
    api = new StorefrontAPIClient('/api/v1');
    
    // Setup form handlers
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterForm);
    }

    // Check if user is already logged in
    const token = localStorage.getItem('storefront_access_token');
    if (token) {
        api.token = token;
        api.headers = api.buildHeaders();
    }

    // Check if redirected from register
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('registered') === 'true') {
        showAlert('success', 'Account created successfully! Please sign in.');
    }

    // Check for next URL to redirect to
    window.nextUrl = urlParams.get('next') || '/storefront/dashboard/';
    
    // Update UI based on auth state
    updateAuthUI();
}

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('email')?.value.trim();
    const password = document.getElementById('password')?.value;

    // Validation
    if (!email || !password) {
        showAlert('error', 'Please fill in all fields');
        return;
    }

    setFormLoading(true);
    hideAlert();

    try {
        const response = await api.login(email, password);

        if (response.access_token) {
            showAlert('success', 'Logged in successfully!');
            
            // Redirect after brief delay
            setTimeout(() => {
                window.location.href = window.nextUrl || '/storefront/dashboard/';
            }, 500);
        } else {
            showAlert('error', response.error || 'Login failed. Please check your credentials.');
        }

    } catch (error) {
        console.error('Login error:', error);
        const message = error.data?.detail || error.data?.error || 'An error occurred. Please try again.';
        showAlert('error', message);
    } finally {
        setFormLoading(false);
    }
}

function clearErrors() {
    document.querySelectorAll('.form-error').forEach(el => {
        el.classList.remove('show');
        el.textContent = '';
    });
    document.querySelectorAll('.form-control').forEach(el => {
        el.classList.remove('error');
    });
}

function showAlert(type, message) {
    const alertEl = document.getElementById('alertMessage');
    if (!alertEl) return;

    const typeMap = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };

    alertEl.className = `alert ${typeMap[type]} alert-dismissible fade show`;
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertEl.style.display = 'block';

    // Auto-hide success alerts after 3 seconds
    if (type === 'success') {
        setTimeout(() => {
            alertEl.style.display = 'none';
        }, 3000);
    }
}

function hideAlert() {
    const alertEl = document.getElementById('alertMessage');
    if (alertEl) {
        alertEl.style.display = 'none';
    }
}

function setFormLoading(isLoading) {
    const form = document.getElementById('loginForm') || document.getElementById('registerForm');
    if (!form) return;

    const btn = form.querySelector('button[type="submit"]');
    if (!btn) return;

    if (isLoading) {
        btn.disabled = true;
        btn.classList.add('loading');
        const originalText = btn.textContent;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        btn.dataset.originalText = originalText;
    } else {
        btn.disabled = false;
        btn.classList.remove('loading');
        btn.textContent = btn.dataset.originalText || 'Submit';
    }
}

async function sendResetEmail() {
    const email = document.getElementById('resetEmail').value.trim();
    const errorEl = document.getElementById('resetError');

    if (!email) {
        if (errorEl) {
            errorEl.textContent = 'Please enter your email address';
            errorEl.classList.add('show');
        }
        return;
    }

    try {
        const response = await fetch('/api/v1/storefront/password-reset/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ email: email })
        });

        const data = await response.json();

        if (!response.ok) {
            if (errorEl) {
                errorEl.textContent = data.detail || 'Failed to send reset email';
                errorEl.classList.add('show');
            }
            return;
        }

        // Show success
        alert('Password reset link sent! Check your email.');
        bootstrap.Modal.getInstance(document.getElementById('forgotPasswordModal')).hide();

    } catch (error) {
        console.error('Reset error:', error);
        if (errorEl) {
            errorEl.textContent = 'An error occurred';
            errorEl.classList.add('show');
        }
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== REGISTRATION PAGE =====

async function handleRegister(event) {
    event.preventDefault();

    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const passwordConfirm = document.getElementById('passwordConfirm').value;
    const phone = document.getElementById('phone').value.trim();
    const company = document.getElementById('company').value.trim();
    const agreeTerms = document.getElementById('agreeTerms').checked;

    // Clear previous errors
    clearErrors();

    // Validation
    if (!firstName || !lastName || !email || !password || !passwordConfirm || !phone) {
        showAlert('error', 'Please fill in all required fields');
        return;
    }

    if (password !== passwordConfirm) {
        showFieldError('passwordConfirm', 'Passwords do not match');
        showAlert('error', 'Passwords do not match');
        return;
    }

    if (password.length < 8) {
        showFieldError('password', 'Password must be at least 8 characters');
        showAlert('error', 'Password must be at least 8 characters');
        return;
    }

    if (!agreeTerms) {
        showAlert('error', 'Please agree to the terms and conditions');
        return;
    }

    // Show loading
    setFormLoading(true);
    hideAlert();

    try {
        // Register user
        const response = await fetch('/api/v1/storefront/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                email: email,
                password: password,
                password_confirm: passwordConfirm,
                phone: phone,
                company: company
            })
        });

        const data = await response.json();

        if (!response.ok) {
            if (data.email) showFieldError('email', data.email[0]);
            if (data.password) showFieldError('password', data.password[0]);
            if (data.phone) showFieldError('phone', data.phone[0]);
            if (data.non_field_errors) {
                showAlert('error', data.non_field_errors[0]);
            } else if (data.detail) {
                showAlert('error', data.detail);
            } else {
                showAlert('error', 'Registration failed. Please try again.');
            }
            return;
        }

        // Show success
        showAlert('success', 'Account created! Redirecting to login...');

        // Redirect after brief delay
        setTimeout(() => {
            window.location.href = '/storefront/login/?registered=true';
        }, 1500);

    } catch (error) {
        console.error('Registration error:', error);
        showAlert('error', 'An error occurred. Please try again.');
    } finally {
        setFormLoading(false);
    }
}

// ===== DASHBOARD PAGE =====

async function loadCustomerProfile() {
    try {
        const token = localStorage.getItem('authToken');
        if (!token) {
            window.location.href = '/storefront/login/';
            return;
        }

        const response = await fetch('/api/v1/storefront/me/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token expired, clear and redirect
                localStorage.removeItem('authToken');
                localStorage.removeItem('currentUser');
                window.location.href = '/storefront/login/';
            }
            throw new Error('Failed to load profile');
        }

        const profile = await response.json();
        window.currentProfile = profile;

        // Populate dashboard
        populateDashboard(profile);

    } catch (error) {
        console.error('Profile load error:', error);
        showDashboardAlert('error', 'Failed to load profile');
    }
}

function populateDashboard(profile) {
    const firstName = profile.user?.first_name || 'Customer';
    const email = profile.user?.email || 'Unknown';
    const phone = profile.phone || 'Not provided';
    const company = profile.company || 'Not provided';

    // Update welcome section
    const welcomeNameEl = document.getElementById('welcomeName');
    if (welcomeNameEl) {
        welcomeNameEl.textContent = firstName;
    }

    // Update profile cards
    const profileEmail = document.getElementById('profileEmail');
    if (profileEmail) profileEmail.textContent = email;

    const profilePhone = document.getElementById('profilePhone');
    if (profilePhone) profilePhone.textContent = phone;

    const profileCompany = document.getElementById('profileCompany');
    if (profileCompany) profileCompany.textContent = company;

    // Load quotes
    loadCustomerQuotes();
}

async function loadCustomerQuotes() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/v1/storefront/my-estimates/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) throw new Error('Failed to load quotes');

        const quotes = await response.json();
        displayCustomerQuotes(quotes);

    } catch (error) {
        console.error('Quotes load error:', error);
        showDashboardAlert('error', 'Failed to load quotes');
    }
}

function displayCustomerQuotes(quotes) {
    const container = document.getElementById('quotesContainer');
    if (!container) return;

    if (!quotes || quotes.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                No quotes yet. <a href="/storefront/quote-builder/">Create one now</a>
            </div>
        `;
        return;
    }

    let html = '<div class="quotes-list">';
    quotes.forEach(quote => {
        html += `
            <div class="quote-card">
                <div class="quote-header">
                    <h5>${quote.estimate_id}</h5>
                    <span class="badge bg-info">${quote.status}</span>
                </div>
                <div class="quote-details">
                    <p><strong>Items:</strong> ${quote.line_items?.length || 0}</p>
                    <p><strong>Total:</strong> KES ${quote.total_amount}</p>
                    <p><strong>Created:</strong> ${new Date(quote.created_at).toLocaleDateString()}</p>
                </div>
                <div class="quote-actions">
                    <button class="btn btn-sm btn-primary" onclick="viewQuote('${quote.estimate_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editQuote('${quote.estimate_id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

function viewQuote(estimateId) {
    window.location.href = `/storefront/quote/${estimateId}/view/`;
}

function editQuote(estimateId) {
    window.location.href = `/storefront/quote-builder/?estimate_id=${estimateId}`;
}

function showDashboardAlert(type, message) {
    const alertEl = document.getElementById('dashboardAlert');
    if (alertEl) {
        alertEl.className = `alert alert-${type}`;
        alertEl.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i> ${message}`;
        alertEl.style.display = 'block';
    }
}

async function handleLogout() {
    if (!confirm('Are you sure you want to log out?')) {
        return;
    }

    try {
        const token = localStorage.getItem('authToken');
        
        // Call logout endpoint
        await fetch('/api/v1/storefront/logout/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        // Clear local storage
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        sessionStorage.removeItem('storefrontCustomer');

        // Redirect to login
        window.location.href = '/storefront/login/';

    } catch (error) {
        console.error('Logout error:', error);
        // Still redirect even if API call fails
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        window.location.href = '/storefront/login/';
    }
}

async function updateProfile(event) {
    event.preventDefault();

    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const company = document.getElementById('company').value.trim();

    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/v1/storefront/me/update/', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                phone: phone,
                company: company
            })
        });

        if (!response.ok) throw new Error('Update failed');

        showDashboardAlert('success', 'Profile updated successfully!');

    } catch (error) {
        console.error('Update error:', error);
        showDashboardAlert('error', 'Failed to update profile');
    }
}
