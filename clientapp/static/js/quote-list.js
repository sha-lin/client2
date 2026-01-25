/**
 * Quote List Page JavaScript
 * Handles AJAX filtering, searching, and live status updates
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // STATE
    // ============================================================

    let currentFilters = {
        status: 'all',
        search: '',
        page: 1
    };

    // ============================================================
    // EVENT HANDLERS
    // ============================================================

    const searchInput = document.querySelector('input[name="search"]');
    const statusSelect = document.querySelector('select[name="status"]');
    const filterForm = document.querySelector('form');

    if (filterForm) {
        filterForm.addEventListener('submit', function (e) {
            e.preventDefault();
            updateFilters();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', debounce(function () {
            updateFilters();
        }, 500));
    }

    if (statusSelect) {
        statusSelect.addEventListener('change', function () {
            updateFilters();
        });
    }

    function updateFilters() {
        currentFilters.search = searchInput ? searchInput.value.trim() : '';
        currentFilters.status = statusSelect ? statusSelect.value : 'all';
        currentFilters.page = 1;

        loadQuotes();
    }

    // ============================================================
    // DATA LOADING
    // ============================================================

    async function loadQuotes() {
        const tbody = document.querySelector('tbody');
        if (!tbody) return;

        // Show loading overlay on table
        tbody.style.opacity = '0.5';

        try {
            let url = '/quotes/?';
            if (currentFilters.status !== 'all') {
                url += `status=${currentFilters.status}&`;
            }
            if (currentFilters.search) {
                url += `search=${encodeURIComponent(currentFilters.search)}&`;
            }
            url += `page=${currentFilters.page}&ordering=-created_at`;

            const data = await api.get(url);
            renderQuotes(data.results || []);
            updateSummary(data);

        } catch (error) {
            console.error('Error loading quotes:', error);
            showToast('Error loading quotes', 'error');
        } finally {
            tbody.style.opacity = '1';
        }
    }

    function renderQuotes(quotes) {
        const tbody = document.querySelector('tbody');
        if (!tbody) return;

        if (quotes.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-gray-500 py-8">No quotes found matching your criteria</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = quotes.map(quote => createQuoteRow(quote)).join('');

        // Re-initialize Lucide icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function createQuoteRow(quote) {
        const statusClasses = {
            'Draft': 'bg-gray-100 text-gray-700',
            'Pending PT Costing': 'bg-yellow-100 text-yellow-700',
            'Ready to Send': 'bg-blue-100 text-blue-700',
            'Sent to Client': 'bg-purple-100 text-purple-700',
            'Partially Approved': 'bg-orange-100 text-orange-700',
            'Fully Approved': 'bg-green-100 text-green-700',
            'Rejected': 'bg-red-100 text-red-700',
            'Expired': 'bg-gray-100 text-gray-500'
        };

        const statusClass = statusClasses[quote.status] || 'bg-gray-100 text-gray-500';
        const formattedDate = formatDate(quote.created_at);
        const formattedAmount = quote.total_amount ? formatCurrency(quote.total_amount) : 'Pending';

        return `
            <tr class="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors" onclick="window.location='/quotes/${quote.quote_id}/'">
                <td class="py-4 px-4">
                    <div>
                        <p class="text-sm font-medium text-gray-900">${quote.quote_id}</p>
                        <p class="text-xs text-gray-500">${formattedDate}</p>
                    </div>
                </td>
                <td class="py-4 px-4 text-sm text-gray-900">${quote.client_name || quote.lead_name || 'Unknown'}</td>
                <td class="py-4 px-4 text-sm text-gray-600">${quote.account_manager_name || '-'}</td>
                <td class="py-4 px-4">
                    <div>
                        <p class="text-sm text-gray-900">${quote.line_items_count || 0} products</p>
                    </div>
                </td>
                <td class="py-4 px-4">
                    <p class="text-sm font-medium text-gray-900">${formattedAmount}</p>
                </td>
                <td class="py-4 px-4">
                    <span class="text-sm font-medium ${quote.margin >= 25 ? 'text-green-600' : 'text-gray-900'}">
                        ${quote.margin ? quote.margin.toFixed(1) + '%' : '-'}
                    </span>
                </td>
                <td class="py-4 px-4">
                    <span class="px-2.5 py-1 text-xs font-medium rounded-full inline-flex items-center gap-1 ${statusClass}">
                        ${quote.status}
                    </span>
                </td>
                <td class="py-4 px-4">
                    <p class="text-sm text-gray-900">${quote.valid_until ? formatDate(quote.valid_until) : '-'}</p>
                </td>
                <td class="py-4 px-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                        <a href="/quotes/${quote.quote_id}/" class="p-1.5 text-gray-500 hover:text-gray-700" onclick="event.stopPropagation()">
                            <i data-lucide="eye" class="w-4 h-4"></i>
                        </a>
                        <a href="/quotes/${quote.quote_id}/edit/" class="p-1.5 text-blue-500 hover:text-blue-700" onclick="event.stopPropagation()">
                            <i data-lucide="edit" class="w-4 h-4"></i>
                        </a>
                    </div>
                </td>
            </tr>
        `;
    }

    function updateSummary(data) {
        const summaryText = document.querySelector('.mb-4 p.text-sm.text-gray-600');
        if (summaryText) {
            summaryText.textContent = `Showing ${data.results ? data.results.length : 0} of ${data.count || 0} quotes`;
        }
    }

    console.log('Quote list page initialized');
});
