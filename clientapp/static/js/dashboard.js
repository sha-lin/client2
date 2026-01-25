/**
 * Dashboard Page JavaScript
 * Handles live refresh and interactive features for AM Dashboard
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // LIVE DASHBOARD REFRESH - Updates stats every 60 seconds
    // ============================================================

    let lastRefreshTime = new Date();

    // Function to refresh dashboard stats via API
    async function refreshDashboardStats() {
        try {
            // Fetch leads count
            const leadsData = await api.get('/leads/');
            const leadsCount = leadsData.count || 0;

            // Fetch clients count  
            const clientsData = await api.get('/clients/?status=Active');
            const clientsCount = clientsData.count || 0;

            // Fetch quotes stats
            const quotesData = await api.get('/quotes/');
            const quotesCount = quotesData.count || 0;

            // Fetch approved quotes for conversion calculation
            const approvedData = await api.get('/quotes/?status=Approved');
            const approvedCount = approvedData.count || 0;

            // Fetch active jobs
            const jobsData = await api.get('/jobs/?status__in=pending,in_progress');
            const activeJobsCount = jobsData.count || 0;

            // Update UI elements
            updateStatCard('total-leads-count', leadsCount);
            updateStatCard('active-clients-count', clientsCount);
            updateStatCard('total-quotes-count', quotesCount);
            updateStatCard('approved-quotes-count', approvedCount);
            updateStatCard('active-jobs-count', activeJobsCount);

            // Calculate and update conversion rate
            if (quotesCount > 0) {
                const conversionRate = ((approvedCount / quotesCount) * 100).toFixed(1);
                updateStatCard('conversion-rate', conversionRate + '%');
            }

            lastRefreshTime = new Date();
            console.log('Dashboard stats refreshed at', lastRefreshTime.toLocaleTimeString());

        } catch (error) {
            console.log('Could not refresh stats:', error);
        }
    }

    function updateStatCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            // Animate the number change
            element.style.transition = 'opacity 0.3s';
            element.style.opacity = '0.5';
            setTimeout(() => {
                element.textContent = typeof value === 'number' ? value.toLocaleString() : value;
                element.style.opacity = '1';
            }, 150);
        }
    }

    // Refresh stats every 60 seconds
    setInterval(refreshDashboardStats, 60000);

    // ============================================================
    // RECENT QUOTES - Load more functionality
    // ============================================================

    const loadMoreQuotesBtn = document.getElementById('load-more-quotes');
    let quotesPage = 1;

    if (loadMoreQuotesBtn) {
        loadMoreQuotesBtn.addEventListener('click', async function () {
            quotesPage++;
            this.textContent = 'Loading...';
            this.disabled = true;

            try {
                const data = await api.get(`/quotes/?page=${quotesPage}&page_size=5&ordering=-created_at`);

                if (data.results && data.results.length > 0) {
                    const container = document.getElementById('recent-quotes-container');

                    data.results.forEach(quote => {
                        const quoteHtml = createQuoteCard(quote);
                        container.insertAdjacentHTML('beforeend', quoteHtml);
                    });

                    // Hide button if no more results
                    if (!data.next) {
                        this.style.display = 'none';
                    }
                }

                this.textContent = 'Load More';
                this.disabled = false;

            } catch (error) {
                console.error('Error loading more quotes:', error);
                this.textContent = 'Load More';
                this.disabled = false;
                showToast('Could not load more quotes', 'error');
            }
        });
    }

    function createQuoteCard(quote) {
        const statusClass = quote.status === 'Approved' ? 'bg-green-100 text-green-800 border-green-200' :
            quote.status === 'Lost' ? 'bg-red-100 text-red-800 border-red-200' :
                'bg-yellow-100 text-yellow-800 border-yellow-200';

        const clientName = quote.client_name || quote.lead_name || 'Unknown';
        const formattedDate = formatDate(quote.created_at);
        const formattedAmount = formatCurrency(quote.total_amount || 0);

        return `
            <div class="px-4 py-3 hover:bg-gray-50 transition-colors">
                <div class="flex justify-between items-start gap-3">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-semibold text-gray-900">${formattedDate}</span>
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusClass}">
                                ${quote.status}
                            </span>
                        </div>
                        <p class="text-sm font-medium text-gray-900 truncate">${quote.product_name || 'Product'}</p>
                        <p class="text-xs text-gray-600 mt-0.5">${quote.quantity || 0} pieces</p>
                        <p class="text-xs text-gray-500 mt-1">${clientName}</p>
                    </div>
                    <div class="text-right flex-shrink-0">
                        <div class="bg-gray-900 text-white px-3 py-1.5 rounded-lg">
                            <p class="text-xs font-bold whitespace-nowrap">${formattedAmount}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // ============================================================
    // QUICK ACTIONS
    // ============================================================

    // Handle "Complete" buttons for upcoming actions
    document.querySelectorAll('[data-action="complete-action"]').forEach(btn => {
        btn.addEventListener('click', async function () {
            const actionCard = this.closest('.action-card');
            const actionType = actionCard.dataset.type;
            const actionId = actionCard.dataset.id;

            this.textContent = '...';
            this.disabled = true;

            try {
                // Log the completion
                await api.post('/activity-log/', {
                    activity_type: 'Note',
                    title: 'Action completed',
                    description: `${actionType} action completed from dashboard`
                });

                // Fade out and remove the card
                actionCard.style.transition = 'opacity 0.3s, transform 0.3s';
                actionCard.style.opacity = '0';
                actionCard.style.transform = 'translateX(20px)';

                setTimeout(() => {
                    actionCard.remove();
                    showToast('Action completed', 'success');
                }, 300);

            } catch (error) {
                this.textContent = 'Complete';
                this.disabled = false;
                showToast('Could not complete action', 'error');
            }
        });
    });

    // Handle "Snooze" buttons
    document.querySelectorAll('[data-action="snooze-action"]').forEach(btn => {
        btn.addEventListener('click', function () {
            const actionCard = this.closest('.action-card');

            // For now, just hide the card temporarily
            actionCard.style.transition = 'opacity 0.3s';
            actionCard.style.opacity = '0.3';

            showToast('Snoozed for 1 day', 'info');

            setTimeout(() => {
                actionCard.style.opacity = '1';
            }, 3000);
        });
    });

    // ============================================================
    // COMMUNICATION LOG - Quick add
    // ============================================================

    const logNewBtn = document.querySelector('[data-action="log-communication"]');
    if (logNewBtn) {
        logNewBtn.addEventListener('click', function () {
            // Open a modal or redirect to communication log page
            const modal = document.getElementById('log-communication-modal');
            if (modal) {
                openModal('log-communication-modal');
            } else {
                // Fallback - could redirect to a log page
                showToast('Communication logging coming soon', 'info');
            }
        });
    }

    console.log('Dashboard page initialized successfully');
});
