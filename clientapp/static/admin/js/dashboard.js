/**
 * PrintDuka Admin Dashboard JavaScript
 * Handles interactivity, animations, and dynamic features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard features
    initializeSidebar();
    initializeQuickActions();
    initializeNotifications();
});

/**
 * Sidebar Navigation
 */
function initializeSidebar() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
        });
    });
    
    // Set active based on current page
    const currentUrl = window.location.pathname;
    navItems.forEach(item => {
        if (item.href === currentUrl) {
            item.classList.add('active');
        }
    });
}

/**
 * Quick Actions Handler
 */
function initializeQuickActions() {
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // If it's a link, let it navigate naturally
            if (this.tagName === 'A') {
                return;
            }
            
            e.preventDefault();
            const action = this.dataset.action;
            handleQuickAction(action);
        });
    });
}

/**
 * Handle Quick Actions
 */
function handleQuickAction(action) {
    const actions = {
        'new-quote': () => {
            window.location.href = '/admin/clientapp/quote/add/';
        },
        'new-client': () => {
            window.location.href = '/admin/clientapp/client/add/';
        },
        'create-po': () => {
            window.location.href = '/admin/clientapp/lpo/add/';
        },
        'schedule-dispatch': () => {
            alert('Dispatch scheduling feature coming soon!');
        },
        'check-stock': () => {
            window.location.href = '/admin/clientapp/product/';
        },
        'upload-artwork': () => {
            window.location.href = '/admin/clientapp/brandassset/';
        }
    };
    
    if (actions[action]) {
        actions[action]();
    }
}

/**
 * Notifications Handler
 */
function initializeNotifications() {
    const notificationBtn = document.querySelector('#notificationBtn');
    
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleNotificationDropdown();
        });
    }
    
    // Close notification dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const dropdown = document.querySelector('.notification-dropdown');
        if (dropdown && !dropdown.contains(e.target) && !notificationBtn?.contains(e.target)) {
            dropdown?.classList.remove('active');
        }
    });
}

function toggleNotificationDropdown() {
    let dropdown = document.querySelector('.notification-dropdown');
    
    if (!dropdown) {
        dropdown = createNotificationDropdown();
        document.body.appendChild(dropdown);
    }
    
    dropdown.classList.toggle('active');
}

function createNotificationDropdown() {
    const div = document.createElement('div');
    div.className = 'notification-dropdown';
    div.innerHTML = `
        <div class="notification-item">
            <i class="fas fa-check"></i>
            <div>
                <strong>Quote #23847 approved</strong>
                <span>2 minutes ago</span>
            </div>
        </div>
        <div class="notification-item">
            <i class="fas fa-industry"></i>
            <div>
                <strong>New quote created</strong>
                <span>11 minutes ago</span>
            </div>
        </div>
        <div class="notification-item">
            <i class="fas fa-exclamation-triangle"></i>
            <div>
                <strong>QC failure on Job #4523</strong>
                <span>3 hours ago</span>
            </div>
        </div>
    `;
    return div;
}

/**
 * Dismiss Alert Function
 */
function dismissAlert(alertId) {
    if (!confirm('Dismiss this alert?')) return;
    
    fetch(`/admin/dismiss-alert/${alertId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove alert from DOM with animation
            const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
            if (alertElement) {
                alertElement.style.animation = 'slideOutLeft 0.3s ease-out forwards';
                setTimeout(() => {
                    alertElement.remove();
                }, 300);
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

/**
 * Export Report Function
 */
function exportReport(reportType) {
    const url = `/admin/export-report/${reportType}/`;
    window.location.href = url;
}

/**
 * Get CSRF Token from Cookie
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

/**
 * Format Currency
 */
function formatCurrency(value, currency = 'KES') {
    return `${currency} ${parseFloat(value).toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    })}`;
}

/**
 * Format Percentage
 */
function formatPercentage(value) {
    return `${parseFloat(value).toFixed(1)}%`;
}

/**
 * Smooth Scroll to Section
 */
function scrollToSection(sectionId) {
    const section = document.querySelector(`#${sectionId}`);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Add animation to elements on scroll
 */
function observeElements() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    });
    
    document.querySelectorAll('.kpi-card, .chart-card, .alerts-card, .activity-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(10px)';
        el.style.transition = 'opacity 0.5s, transform 0.5s';
        observer.observe(el);
    });
}

// Run observer on page load
window.addEventListener('load', observeElements);

/**
 * Keyboard Shortcuts
 */
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search (if search exists)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        // Implement search functionality
    }
    
    // Escape to close dropdowns
    if (e.key === 'Escape') {
        document.querySelectorAll('.dropdown.active').forEach(el => {
            el.classList.remove('active');
        });
    }
});

/**
 * Auto-refresh dashboard data (optional)
 */
function initializeAutoRefresh(intervalSeconds = 300) {
    // Only refresh if tab is visible
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            refreshDashboardData();
        }
    });
}

function refreshDashboardData() {
    // This would make an AJAX call to refresh dashboard data
    // Implement as needed
    console.log('Refreshing dashboard data...');
}

/**
 * Dark Mode Toggle (Optional)
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

/**
 * Initialize Dark Mode on Load
 */
function initializeDarkMode() {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
}

initializeDarkMode();

/**
 * Export utilities
 */
window.DashboardUtils = {
    formatCurrency,
    formatPercentage,
    dismissAlert,
    exportReport,
    scrollToSection,
    toggleDarkMode
};

console.log('PrintDuka Admin Dashboard initialized');
