/**
 * Analytics Page JavaScript
 * Handles chart rendering, data fetching, and date range filtering
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // STATE
    // ============================================================

    let currentDateRange = '30d'; // Default to last 30 days
    let analyticsData = null;
    let charts = {};

    // ============================================================
    // DATE RANGE FILTER
    // ============================================================

    const dateRangeButtons = document.querySelectorAll('[data-range]');

    dateRangeButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            // Update active button
            dateRangeButtons.forEach(b => {
                b.classList.remove('bg-blue-600', 'text-white');
                b.classList.add('bg-gray-100', 'text-gray-700');
            });
            this.classList.remove('bg-gray-100', 'text-gray-700');
            this.classList.add('bg-blue-600', 'text-white');

            // Load new data
            currentDateRange = this.dataset.range;
            loadAnalyticsData();
        });
    });

    // ============================================================
    // DATA LOADING
    // ============================================================

    loadAnalyticsData();

    async function loadAnalyticsData() {
        showLoading('Loading analytics...');

        try {
            // Calculate date range
            const endDate = new Date();
            let startDate = new Date();

            switch (currentDateRange) {
                case '7d':
                    startDate.setDate(startDate.getDate() - 7);
                    break;
                case '30d':
                    startDate.setDate(startDate.getDate() - 30);
                    break;
                case '90d':
                    startDate.setDate(startDate.getDate() - 90);
                    break;
                case '1y':
                    startDate.setFullYear(startDate.getFullYear() - 1);
                    break;
                case 'all':
                    startDate = new Date(2020, 0, 1); // Far back date
                    break;
            }

            const startStr = startDate.toISOString().split('T')[0];
            const endStr = endDate.toISOString().split('T')[0];

            // Fetch data from multiple endpoints
            const [quotesData, leadsData, clientsData, jobsData] = await Promise.all([
                api.get(`/quotes/?created_at__gte=${startStr}&created_at__lte=${endStr}`),
                api.get(`/leads/?created_at__gte=${startStr}&created_at__lte=${endStr}`),
                api.get(`/clients/?created_at__gte=${startStr}&created_at__lte=${endStr}`),
                api.get(`/jobs/?created_at__gte=${startStr}&created_at__lte=${endStr}`)
            ]);

            analyticsData = {
                quotes: quotesData.results || [],
                leads: leadsData.results || [],
                clients: clientsData.results || [],
                jobs: jobsData.results || [],
                quotesCount: quotesData.count || 0,
                leadsCount: leadsData.count || 0,
                clientsCount: clientsData.count || 0,
                jobsCount: jobsData.count || 0
            };

            hideLoading();
            updateSummaryCards();
            updateCharts();

        } catch (error) {
            hideLoading();
            console.error('Error loading analytics:', error);
            showToast('Error loading analytics data', 'error');
        }
    }

    // ============================================================
    // SUMMARY CARDS
    // ============================================================

    function updateSummaryCards() {
        if (!analyticsData) return;

        // Calculate totals
        const totalQuotesValue = analyticsData.quotes.reduce((sum, q) => sum + (q.total_amount || 0), 0);
        const approvedQuotes = analyticsData.quotes.filter(q => q.status === 'Approved');
        const approvedValue = approvedQuotes.reduce((sum, q) => sum + (q.total_amount || 0), 0);
        const conversionRate = analyticsData.quotesCount > 0
            ? ((approvedQuotes.length / analyticsData.quotesCount) * 100).toFixed(1)
            : 0;

        const newClients = analyticsData.clients.length;
        const convertedLeads = analyticsData.leads.filter(l => l.status === 'Converted').length;
        const leadConversionRate = analyticsData.leadsCount > 0
            ? ((convertedLeads / analyticsData.leadsCount) * 100).toFixed(1)
            : 0;

        // Update UI
        updateCard('total-quotes', analyticsData.quotesCount);
        updateCard('total-quotes-value', formatCurrency(totalQuotesValue));
        updateCard('approved-quotes', approvedQuotes.length);
        updateCard('approved-value', formatCurrency(approvedValue));
        updateCard('conversion-rate', conversionRate + '%');
        updateCard('new-leads', analyticsData.leadsCount);
        updateCard('new-clients', newClients);
        updateCard('lead-conversion-rate', leadConversionRate + '%');
        updateCard('active-jobs', analyticsData.jobs.filter(j => j.status === 'in_progress').length);
        updateCard('completed-jobs', analyticsData.jobs.filter(j => j.status === 'completed').length);
    }

    function updateCard(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    }

    // ============================================================
    // CHARTS
    // ============================================================

    function updateCharts() {
        if (!analyticsData) return;

        renderQuotesTrendChart();
        renderQuotesStatusChart();
        renderLeadSourcesChart();
        renderRevenueChart();
    }

    function renderQuotesTrendChart() {
        const ctx = document.getElementById('quotes-trend-chart');
        if (!ctx) return;

        // Group quotes by date
        const dailyData = {};
        analyticsData.quotes.forEach(quote => {
            const date = quote.created_at.split('T')[0];
            dailyData[date] = (dailyData[date] || 0) + 1;
        });

        // Sort dates and prepare chart data
        const dates = Object.keys(dailyData).sort();
        const counts = dates.map(d => dailyData[d]);

        // Destroy existing chart
        if (charts.quotesTrend) {
            charts.quotesTrend.destroy();
        }

        charts.quotesTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates.map(d => formatDate(d)),
                datasets: [{
                    label: 'Quotes Created',
                    data: counts,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    function renderQuotesStatusChart() {
        const ctx = document.getElementById('quotes-status-chart');
        if (!ctx) return;

        // Count by status
        const statusCounts = {};
        analyticsData.quotes.forEach(quote => {
            statusCounts[quote.status] = (statusCounts[quote.status] || 0) + 1;
        });

        const labels = Object.keys(statusCounts);
        const data = Object.values(statusCounts);
        const colors = {
            'Draft': '#9ca3af',
            'Quoted': '#fbbf24',
            'Approved': '#22c55e',
            'Lost': '#ef4444',
            'Sent to PT': '#3b82f6',
            'Costed': '#8b5cf6'
        };

        if (charts.quotesStatus) {
            charts.quotesStatus.destroy();
        }

        charts.quotesStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: labels.map(l => colors[l] || '#6b7280')
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { usePointStyle: true }
                    }
                }
            }
        });
    }

    function renderLeadSourcesChart() {
        const ctx = document.getElementById('lead-sources-chart');
        if (!ctx) return;

        // Count by source
        const sourceCounts = {};
        analyticsData.leads.forEach(lead => {
            const source = lead.source || 'Unknown';
            sourceCounts[source] = (sourceCounts[source] || 0) + 1;
        });

        const labels = Object.keys(sourceCounts);
        const data = Object.values(sourceCounts);

        if (charts.leadSources) {
            charts.leadSources.destroy();
        }

        charts.leadSources = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Leads',
                    data: data,
                    backgroundColor: '#3b82f6',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
    }

    function renderRevenueChart() {
        const ctx = document.getElementById('revenue-chart');
        if (!ctx) return;

        // Group approved quotes by month
        const monthlyRevenue = {};
        analyticsData.quotes
            .filter(q => q.status === 'Approved')
            .forEach(quote => {
                const month = quote.created_at.substring(0, 7); // YYYY-MM
                monthlyRevenue[month] = (monthlyRevenue[month] || 0) + (quote.total_amount || 0);
            });

        const months = Object.keys(monthlyRevenue).sort();
        const revenue = months.map(m => monthlyRevenue[m]);

        if (charts.revenue) {
            charts.revenue.destroy();
        }

        charts.revenue = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: months.map(m => {
                    const [year, month] = m.split('-');
                    return new Date(year, month - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
                }),
                datasets: [{
                    label: 'Revenue (KES)',
                    data: revenue,
                    backgroundColor: '#22c55e',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => formatCurrency(ctx.raw)
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => 'KES ' + (value / 1000).toFixed(0) + 'K'
                        }
                    }
                }
            }
        });
    }

    // ============================================================
    // EXPORT FUNCTIONALITY
    // ============================================================

    const exportBtn = document.getElementById('export-analytics-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function () {
            if (!analyticsData) {
                showToast('No data to export', 'error');
                return;
            }

            // Create summary report
            const summary = {
                dateRange: currentDateRange,
                generatedAt: new Date().toISOString(),
                totals: {
                    quotes: analyticsData.quotesCount,
                    leads: analyticsData.leadsCount,
                    clients: analyticsData.clientsCount,
                    jobs: analyticsData.jobsCount
                },
                quotesByStatus: {},
                leadsBySource: {}
            };

            // Count quotes by status
            analyticsData.quotes.forEach(q => {
                summary.quotesByStatus[q.status] = (summary.quotesByStatus[q.status] || 0) + 1;
            });

            // Count leads by source
            analyticsData.leads.forEach(l => {
                const source = l.source || 'Unknown';
                summary.leadsBySource[source] = (summary.leadsBySource[source] || 0) + 1;
            });

            // Download as JSON
            const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `analytics_${currentDateRange}_${new Date().toISOString().split('T')[0]}.json`;
            a.click();

            showToast('Analytics exported', 'success');
        });
    }

    // ============================================================
    // REFRESH
    // ============================================================

    // Auto-refresh every 5 minutes
    setInterval(loadAnalyticsData, 300000);

    console.log('Analytics page initialized successfully');
});
