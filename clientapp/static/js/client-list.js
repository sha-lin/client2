/**
 * Client List Page JavaScript
 * Handles AJAX filtering, searching, and live status updates
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // STATE
    // ============================================================

    let currentFilters = {
        type: 'All',
        status: 'All',
        search: '',
        page: 1
    };

    // ============================================================
    // EVENT HANDLERS
    // ============================================================

    const searchInput = document.querySelector('input[name="search"]');
    const typeSelect = document.querySelector('select[name="type"]');
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

    if (typeSelect) {
        typeSelect.addEventListener('change', updateFilters);
    }

    if (statusSelect) {
        statusSelect.addEventListener('change', updateFilters);
    }

    function updateFilters() {
        currentFilters.search = searchInput ? searchInput.value.trim() : '';
        currentFilters.type = typeSelect ? typeSelect.value : 'All';
        currentFilters.status = statusSelect ? statusSelect.value : 'All';
        currentFilters.page = 1;

        loadClients();
    }

    // ============================================================
    // DATA LOADING
    // ============================================================

    async function loadClients() {
        const tbody = document.querySelector('tbody');
        if (!tbody) return;

        tbody.style.opacity = '0.5';

        try {
            let url = '/clients/?';
            if (currentFilters.type !== 'All') {
                url += `client_type=${currentFilters.type}&`;
            }
            if (currentFilters.status !== 'All') {
                url += `status=${currentFilters.status}&`;
            }
            if (currentFilters.search) {
                url += `search=${encodeURIComponent(currentFilters.search)}&`;
            }
            url += `page=${currentFilters.page}&ordering=-created_at`;

            const data = await api.get(url);
            renderClients(data.results || []);
            updateSummary(data);

        } catch (error) {
            console.error('Error loading clients:', error);
            showToast('Error loading clients', 'error');
        } finally {
            tbody.style.opacity = '1';
        }
    }

    function renderClients(clients) {
        const tbody = document.querySelector('tbody');
        if (!tbody) return;

        if (clients.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-gray-500 py-8">No clients found matching your criteria</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = clients.map(client => createClientRow(client)).join('');
    }

    function createClientRow(client) {
        const statusClass = client.status === 'Active' ? 'badge-success' :
            client.status === 'Dormant' ? 'badge-warning' : 'badge-danger';

        return `
            <tr>
                <td>${client.client_id}</td>
                <td>
                    <div>
                        <div class="font-medium">${client.name}</div>
                        ${client.company ? `<div class="text-sm text-gray-600">${client.company}</div>` : ''}
                    </div>
                </td>
                <td>
                    <span class="badge badge-secondary">
                        ${client.client_type}
                    </span>
                </td>
                <td>
                    <div class="text-sm">
                        <div>${client.email || '-'}</div>
                        <div class="text-gray-600">${client.phone || '-'}</div>
                    </div>
                </td>
                <td>${client.credit_terms || '-'}</td>
                <td>${client.total_jobs || 0}</td>
                <td class="text-sm text-gray-600">${client.last_activity ? formatDate(client.last_activity) : 'Never'}</td>
                <td>
                    <span class="badge ${statusClass}">${client.status}</span>
                </td>
                <td>
                    <div class="flex gap-2">
                        <a href="/clients/${client.id}/" class="btn btn-secondary text-sm py-1 px-2">
                            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        </a>
                        <a href="/clients/${client.id}/edit/" class="btn btn-secondary text-sm py-1 px-2">
                            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                        </a>
                    </div>
                </td>
            </tr>
        `;
    }

    function updateSummary(data) {
        const summaryText = document.querySelector('.px-6.py-4 p.text-sm.text-gray-600');
        if (summaryText) {
            summaryText.textContent = `${data.count || 0} client${data.count === 1 ? '' : 's'} found`;
        }
    }

    console.log('Client list page initialized');
});
