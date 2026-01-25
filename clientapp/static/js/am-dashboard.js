/**
 * Account Manager Dashboard - Real-time Data Integration
 * Fetches performance metrics from /api/v1/analytics/am-performance/
 * Features: Auto-refresh every 20 seconds, visual feedback, error recovery
 */

// Configuration
const DASHBOARD_CONFIG = {
    REFRESH_INTERVAL: 20000,  // 20 seconds for more responsive updates
    MAX_RETRIES: 3,
    RETRY_DELAY: 5000,  // 5 seconds initial retry delay
    ERROR_TIMEOUT: 60000  // 1 minute timeout before resuming auto-refresh after error
};

let refreshState = {
    isLoading: false,
    lastUpdate: null,
    failureCount: 0,
    nextRefreshTime: null
};

document.addEventListener('DOMContentLoaded', async function () {
    // Add refresh status indicator to dashboard if it exists
    addRefreshIndicator();
    
    // Load initial dashboard data
    await loadDashboardData();
    
    // Auto-refresh with the configured interval
    setInterval(async () => {
        if (!refreshState.isLoading) {
            await loadDashboardData();
        }
    }, DASHBOARD_CONFIG.REFRESH_INTERVAL);
    
    // Update last-updated timestamp every 5 seconds
    setInterval(updateLastUpdatedTime, 5000);
    
    // Add manual refresh button listener if it exists
    const refreshBtn = document.getElementById('dashboard-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async function () {
            this.classList.add('animate-spin');
            await loadDashboardData();
            this.classList.remove('animate-spin');
        });
    }
});

function addRefreshIndicator() {
    // Check if indicator already exists
    if (document.getElementById('dashboard-refresh-indicator')) return;
    
    const header = document.querySelector('h1, .page-title, [role="heading"]');
    if (!header || !header.parentElement) return;
    
    const indicator = document.createElement('div');
    indicator.id = 'dashboard-refresh-indicator';
    indicator.className = 'inline-flex items-center gap-2 text-xs text-gray-500 ml-4';
    indicator.innerHTML = `
        <span id="refresh-status" class="inline-flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            Live
        </span>
        <span id="last-updated">Last updated: just now</span>
    `;
    
    header.parentElement.appendChild(indicator);
}

function updateLastUpdatedTime() {
    const el = document.getElementById('last-updated');
    if (!el || !refreshState.lastUpdate) return;
    
    const secondsAgo = Math.floor((Date.now() - refreshState.lastUpdate) / 1000);
    
    if (secondsAgo < 60) {
        el.textContent = `Last updated: ${secondsAgo}s ago`;
    } else {
        const minutesAgo = Math.floor(secondsAgo / 60);
        el.textContent = `Last updated: ${minutesAgo}m ago`;
    }
}

async function loadDashboardData() {
    if (refreshState.isLoading) return;
    
    refreshState.isLoading = true;
    updateRefreshIndicator('loading');
    
    try {
        // Fetch AM performance analytics
        const response = await api.get('/analytics/am-performance/');
        
        if (!response || !response.account_manager) {
            console.error('Invalid response format:', response);
            throw new Error('Invalid response format');
        }
        
        // Reset failure count on success
        refreshState.failureCount = 0;
        refreshState.lastUpdate = Date.now();
        
        // Update KPI Cards
        updateDashboardKPIs(response);
        
        // Update performance summary
        updatePerformanceSummary(response.performance_summary);
        
        updateRefreshIndicator('success');
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        refreshState.failureCount++;
        
        updateRefreshIndicator('error');
        
        // Show error message if too many failures
        if (refreshState.failureCount >= DASHBOARD_CONFIG.MAX_RETRIES) {
            showToast('Dashboard data unavailable - will retry in 1 minute', 'warning');
            refreshState.failureCount = 0;  // Reset counter
        }
        
    } finally {
        refreshState.isLoading = false;
    }
}

function updateDashboardKPIs(data) {
    // Total Leads
    updateKPICard('kpi-total-leads', data.leads?.total || 0);
    
    // Converted Leads
    updateKPICard('kpi-converted-leads', data.leads?.converted || 0);
    updateKPICard('kpi-conversion-rate', data.leads?.conversion_rate_percent?.toFixed(1) || '0');
    
    // Total Clients (Account Manager only manages assigned clients)
    updateKPICard('kpi-total-clients', data.clients?.managed || 0);
    
    // Total Quotes
    updateKPICard('kpi-total-quotes', data.quotes?.total || 0);
    
    // Approved Quotes
    updateKPICard('kpi-approved-quotes', data.quotes?.approved || 0);
    
    // Pending Quotes
    updateKPICard('kpi-pending-quotes', data.quotes?.pending || 0);
    
    // Lost Quotes
    updateKPICard('kpi-lost-quotes', data.quotes?.lost || 0);
    
    // Conversion Rate (Quote)
    updateKPICard('kpi-quote-conversion-rate', data.quotes?.conversion_rate_percent?.toFixed(1) || '0');
    
    // Total Revenue
    updateKPICard('kpi-total-revenue', formatCurrency(data.quotes?.total_revenue || 0));
    
    // Average Quote Value
    updateKPICard('kpi-avg-quote-value', formatCurrency(data.quotes?.average_quote_value || 0));
}

function updatePerformanceSummary(summary) {
    if (!summary) return;
    
    const statusElement = document.getElementById('performance-status');
    const metricElement = document.getElementById('performance-metric');
    
    if (statusElement) {
        // Set status badge color
        let badgeClass = 'bg-yellow-100 text-yellow-800';
        if (summary.status === 'strong') {
            badgeClass = 'bg-green-100 text-green-800';
        } else if (summary.status === 'good') {
            badgeClass = 'bg-blue-100 text-blue-800';
        }
        
        statusElement.className = `px-3 py-1 rounded-full text-xs font-medium ${badgeClass}`;
        statusElement.textContent = summary.status?.toUpperCase() || 'PENDING';
    }
    
    if (metricElement) {
        metricElement.textContent = summary.top_metric || 'No data available';
    }
}

function updateKPICard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        // Add animation effect
        element.classList.add('update-pulse');
        setTimeout(() => element.classList.remove('update-pulse'), 500);
    }
}

function updateRefreshIndicator(state) {
    const statusEl = document.getElementById('refresh-status');
    if (!statusEl) return;
    
    const indicator = statusEl.querySelector('span:first-child');
    if (!indicator) return;
    
    switch(state) {
        case 'loading':
            indicator.className = 'w-2 h-2 rounded-full bg-yellow-500 animate-spin';
            break;
        case 'success':
            indicator.className = 'w-2 h-2 rounded-full bg-green-500 animate-pulse';
            break;
        case 'error':
            indicator.className = 'w-2 h-2 rounded-full bg-red-500 animate-pulse';
            break;
        default:
            indicator.className = 'w-2 h-2 rounded-full bg-green-500 animate-pulse';
    }
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 0
    }).format(value);
}

// CSS for update animation and refresh indicator
const style = document.createElement('style');
style.textContent = `
    .update-pulse {
        animation: pulse-update 0.5s ease-in-out;
    }
    
    @keyframes pulse-update {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; background-color: rgba(59, 130, 246, 0.1); }
    }
    
    #dashboard-refresh-indicator {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes spinSlower {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .animate-spin {
        animation: spinSlower 1s linear infinite;
    }
`;
document.head.appendChild(style);
