/**
 * Client Profile Page JavaScript
 * Handles tab lazy-loading, activity logging, and quick actions
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // STATE
    // ============================================================

    const clientId = document.getElementById('client-data')?.dataset?.clientId ||
        window.location.pathname.split('/').filter(Boolean).pop();

    let loadedTabs = new Set(['overview']); // Overview is always loaded initially

    // ============================================================
    // TAB NAVIGATION & LAZY LOADING
    // ============================================================

    const tabs = document.querySelectorAll('[data-tab]');
    const tabContents = document.querySelectorAll('[data-tab-content]');

    tabs.forEach(tab => {
        tab.addEventListener('click', async function () {
            const tabName = this.dataset.tab;

            // Update active tab styling
            tabs.forEach(t => {
                t.classList.remove('border-blue-500', 'text-blue-600');
                t.classList.add('border-transparent', 'text-gray-500');
            });
            this.classList.remove('border-transparent', 'text-gray-500');
            this.classList.add('border-blue-500', 'text-blue-600');

            // Hide all tab contents
            tabContents.forEach(tc => tc.classList.add('hidden'));

            // Show selected tab content
            const content = document.querySelector(`[data-tab-content="${tabName}"]`);
            if (content) {
                content.classList.remove('hidden');

                // Lazy load if not already loaded
                if (!loadedTabs.has(tabName)) {
                    await loadTabContent(tabName, content);
                    loadedTabs.add(tabName);
                }
            }
        });
    });

    async function loadTabContent(tabName, container) {
        container.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
            </div>
        `;

        try {
            switch (tabName) {
                case 'orders':
                    await loadOrders(container);
                    break;
                case 'quotes':
                    await loadQuotes(container);
                    break;
                case 'jobs':
                    await loadJobs(container);
                    break;
                case 'invoices':
                    await loadInvoices(container);
                    break;
                case 'documents':
                    await loadDocuments(container);
                    break;
                case 'activity':
                    await loadActivity(container);
                    break;
                case 'contacts':
                    await loadContacts(container);
                    break;
                default:
                    container.innerHTML = '<p class="text-gray-500 text-center py-8">Coming soon...</p>';
            }
        } catch (error) {
            console.error(`Error loading ${tabName}:`, error);
            container.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <p>Error loading data</p>
                    <button onclick="location.reload()" class="mt-2 text-sm text-blue-600 hover:underline">Retry</button>
                </div>
            `;
        }
    }

    // ============================================================
    // TAB CONTENT LOADERS
    // ============================================================

    async function loadQuotes(container) {
        const data = await api.get(`/quotes/?client=${clientId}&ordering=-created_at`);
        const quotes = data.results || [];

        if (quotes.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-500">No quotes yet</p>
                    <a href="/quotes/create/?client=${clientId}" class="mt-4 inline-block btn btn-primary">Create Quote</a>
                </div>
            `;
            return;
        }

        const html = `
            <div class="space-y-3">
                ${quotes.map(quote => `
                    <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="font-medium text-gray-900">${quote.quote_id}</span>
                                <span class="px-2 py-0.5 rounded-full text-xs font-medium ${getStatusClass(quote.status)}">
                                    ${quote.status}
                                </span>
                            </div>
                            <p class="text-sm text-gray-600 mt-1">${quote.product_name || 'Multiple products'}</p>
                            <p class="text-xs text-gray-500">${formatDate(quote.created_at)}</p>
                        </div>
                        <div class="text-right">
                            <p class="font-semibold text-gray-900">${formatCurrency(quote.total_amount || 0)}</p>
                            <a href="/quotes/${quote.quote_id}/" class="text-sm text-blue-600 hover:text-blue-800">View →</a>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

    async function loadJobs(container) {
        const data = await api.get(`/jobs/?client=${clientId}&ordering=-created_at`);
        const jobs = data.results || [];

        if (jobs.length === 0) {
            container.innerHTML = `<p class="text-gray-500 text-center py-8">No jobs yet</p>`;
            return;
        }

        const html = `
            <div class="space-y-3">
                ${jobs.map(job => `
                    <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="font-medium text-gray-900">${job.job_number}</span>
                                <span class="px-2 py-0.5 rounded-full text-xs font-medium ${getStatusClass(job.status)}">
                                    ${formatStatus(job.status)}
                                </span>
                            </div>
                            <p class="text-sm text-gray-600 mt-1">${job.job_name || job.product}</p>
                            <div class="flex items-center gap-4 mt-2 text-xs text-gray-500">
                                <span>Progress: ${job.progress_percentage || 0}%</span>
                                <span>${formatDate(job.created_at)}</span>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="font-semibold text-gray-900">${formatCurrency(job.total_amount || 0)}</p>
                            <a href="/job/${job.id}/" class="text-sm text-blue-600 hover:text-blue-800">View →</a>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

    async function loadInvoices(container) {
        const data = await api.get(`/lpos/?client=${clientId}&ordering=-created_at`);
        const lpos = data.results || [];

        if (lpos.length === 0) {
            container.innerHTML = `<p class="text-gray-500 text-center py-8">No invoices yet</p>`;
            return;
        }

        const html = `
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">LPO Number</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                            <th class="px-4 py-3"></th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        ${lpos.map(lpo => `
                            <tr class="hover:bg-gray-50">
                                <td class="px-4 py-3 text-sm font-medium text-gray-900">${lpo.lpo_number}</td>
                                <td class="px-4 py-3 text-sm text-gray-500">${formatDate(lpo.created_at)}</td>
                                <td class="px-4 py-3">
                                    <span class="px-2 py-1 rounded-full text-xs font-medium ${getStatusClass(lpo.status)}">
                                        ${lpo.status}
                                    </span>
                                </td>
                                <td class="px-4 py-3 text-sm text-gray-900 text-right">${formatCurrency(lpo.total_amount || 0)}</td>
                                <td class="px-4 py-3 text-right">
                                    <a href="/lpo/${lpo.lpo_number}/" class="text-blue-600 hover:text-blue-800 text-sm">View</a>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;
    }

    async function loadDocuments(container) {
        const data = await api.get(`/compliance-documents/?client=${clientId}`);
        const docs = data.results || [];

        if (docs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-500">No documents uploaded</p>
                    <button id="upload-doc-btn" class="mt-4 btn btn-secondary">Upload Document</button>
                </div>
            `;
            return;
        }

        const html = `
            <div class="flex justify-end mb-4">
                <button id="upload-doc-btn" class="btn btn-secondary">Upload Document</button>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                ${docs.map(doc => `
                    <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div class="flex items-start justify-between">
                            <div class="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
                                <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                                </svg>
                            </div>
                            <span class="text-xs px-2 py-0.5 rounded ${doc.is_verified ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">
                                ${doc.is_verified ? 'Verified' : 'Pending'}
                            </span>
                        </div>
                        <h4 class="mt-3 font-medium text-sm text-gray-900 truncate">${doc.document_type}</h4>
                        <p class="text-xs text-gray-500 mt-1">${formatDate(doc.uploaded_at)}</p>
                        ${doc.expiry_date ? `<p class="text-xs text-gray-500">Expires: ${formatDate(doc.expiry_date)}</p>` : ''}
                        ${doc.file_url ? `<a href="${doc.file_url}" target="_blank" class="text-xs text-blue-600 hover:text-blue-800 mt-2 inline-block">Download</a>` : ''}
                    </div>
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

    async function loadActivity(container) {
        const data = await api.get(`/activity-log/?client=${clientId}&ordering=-created_at`);
        const activities = data.results || [];

        if (activities.length === 0) {
            container.innerHTML = `<p class="text-gray-500 text-center py-8">No activity recorded</p>`;
            return;
        }

        const html = `
            <div class="space-y-4">
                ${activities.map(activity => `
                    <div class="flex gap-4">
                        <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                            <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div class="flex-1 pb-4 border-b border-gray-100">
                            <p class="text-sm text-gray-900">${activity.title || activity.activity_type}</p>
                            ${activity.description ? `<p class="text-sm text-gray-600 mt-1">${activity.description}</p>` : ''}
                            <p class="text-xs text-gray-500 mt-1">${formatRelativeTime(activity.created_at)} by ${activity.performed_by_name || 'System'}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

    async function loadContacts(container) {
        const data = await api.get(`/client-contacts/?client=${clientId}`);
        const contacts = data.results || [];

        const html = `
            <div class="flex justify-end mb-4">
                <button id="add-contact-btn" class="btn btn-secondary">Add Contact</button>
            </div>
            ${contacts.length === 0 ? `
                <p class="text-gray-500 text-center py-8">No additional contacts</p>
            ` : `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${contacts.map(contact => `
                        <div class="border border-gray-200 rounded-lg p-4">
                            <div class="flex items-start justify-between">
                                <div>
                                    <h4 class="font-medium text-gray-900">${contact.name}</h4>
                                    <p class="text-sm text-gray-600">${contact.role || 'Contact'}</p>
                                </div>
                                ${contact.is_primary ? `<span class="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700">Primary</span>` : ''}
                            </div>
                            <div class="mt-3 space-y-1 text-sm text-gray-600">
                                ${contact.email ? `<p class="flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>${contact.email}</p>` : ''}
                                ${contact.phone ? `<p class="flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path></svg>${contact.phone}</p>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `}
        `;

        container.innerHTML = html;
    }

    // ============================================================
    // HELPER FUNCTIONS
    // ============================================================

    function getStatusClass(status) {
        const classes = {
            'Draft': 'bg-gray-100 text-gray-800',
            'Quoted': 'bg-yellow-100 text-yellow-800',
            'Approved': 'bg-green-100 text-green-800',
            'Lost': 'bg-red-100 text-red-800',
            'pending': 'bg-yellow-100 text-yellow-800',
            'in_progress': 'bg-blue-100 text-blue-800',
            'completed': 'bg-green-100 text-green-800',
            'Active': 'bg-green-100 text-green-800',
            'Inactive': 'bg-gray-100 text-gray-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    }

    function formatStatus(status) {
        const labels = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled'
        };
        return labels[status] || status;
    }

    // ============================================================
    // QUICK ACTIONS
    // ============================================================

    // Create Quote Button
    const createQuoteBtn = document.getElementById('create-quote-btn');
    if (createQuoteBtn) {
        createQuoteBtn.addEventListener('click', function () {
            window.location.href = `/quotes/create/?client=${clientId}`;
        });
    }

    // Edit Client Button
    const editClientBtn = document.getElementById('edit-client-btn');
    if (editClientBtn) {
        editClientBtn.addEventListener('click', function () {
            window.location.href = `/clients/${clientId}/edit/`;
        });
    }

    // Log Activity Button
    const logActivityBtn = document.getElementById('log-activity-btn');
    if (logActivityBtn) {
        logActivityBtn.addEventListener('click', function () {
            const modal = document.getElementById('activity-modal');
            if (modal) {
                openModal('activity-modal');
            } else {
                // Create simple activity logging
                const note = prompt('Enter activity note:');
                if (note) {
                    logActivity(note);
                }
            }
        });
    }

    async function logActivity(note) {
        try {
            await api.post('/activity-log/', {
                client: clientId,
                activity_type: 'Note',
                title: 'Note added',
                description: note
            });

            showToast('Activity logged', 'success');

            // Refresh activity tab if visible
            const activityTab = document.querySelector('[data-tab-content="activity"]');
            if (activityTab && !activityTab.classList.contains('hidden')) {
                await loadActivity(activityTab);
            }

        } catch (error) {
            showToast('Could not log activity', 'error');
        }
    }

    console.log('Client profile page initialized successfully');
});
