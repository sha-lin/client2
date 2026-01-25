/**
 * Quote Detail Page JavaScript
 * Handles quote actions, status updates, and PDF generation
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // STATE
    // ============================================================

    const quoteId = document.getElementById('quote-data')?.dataset?.quoteId ||
        window.location.pathname.split('/').filter(Boolean).pop();
    let quoteData = null;

    // ============================================================
    // INITIAL LOAD
    // ============================================================

    loadQuoteDetails();

    async function loadQuoteDetails() {
        try {
            quoteData = await api.get(`/quotes/${quoteId}/`);
            updateActionButtons();
        } catch (error) {
            console.error('Error loading quote details:', error);
        }
    }

    function updateActionButtons() {
        if (!quoteData) return;

        const status = quoteData.status;

        // Show/hide buttons based on status
        const sendToPtBtn = document.getElementById('send-to-pt-btn');
        const sendToClientBtn = document.getElementById('send-to-client-btn');
        const approveBtn = document.getElementById('approve-btn');
        const convertToJobBtn = document.getElementById('convert-to-job-btn');
        const reviseBtn = document.getElementById('revise-btn');

        if (sendToPtBtn) {
            sendToPtBtn.style.display = status === 'Draft' ? 'block' : 'none';
        }

        if (sendToClientBtn) {
            sendToClientBtn.style.display = ['Costed', 'Draft'].includes(status) ? 'block' : 'none';
        }

        if (approveBtn) {
            approveBtn.style.display = ['Quoted', 'Client Review'].includes(status) ? 'block' : 'none';
        }

        if (convertToJobBtn) {
            convertToJobBtn.style.display = status === 'Approved' ? 'block' : 'none';
        }

        if (reviseBtn) {
            reviseBtn.style.display = ['Quoted', 'Client Review', 'Approved'].includes(status) ? 'block' : 'none';
        }
    }

    // ============================================================
    // ACTION HANDLERS
    // ============================================================

    // Send to Production Team for Costing
    const sendToPtBtn = document.getElementById('send-to-pt-btn');
    if (sendToPtBtn) {
        sendToPtBtn.addEventListener('click', async function () {
            if (!confirm('Send this quote to the Production Team for costing?')) return;

            this.textContent = 'Sending...';
            this.disabled = true;

            try {
                await api.post(`/quotes/${quoteId}/send-to-pt/`);

                showToast('Quote sent to Production Team', 'success');

                // Update UI
                updateStatusBadge('Sent to PT');
                this.style.display = 'none';

                // Show next action
                const sendToClientBtn = document.getElementById('send-to-client-btn');
                if (sendToClientBtn) {
                    sendToClientBtn.textContent = 'Waiting for Costing...';
                    sendToClientBtn.disabled = true;
                }

            } catch (error) {
                this.textContent = 'Send to PT';
                this.disabled = false;

                showToast(error.data?.detail || 'Error sending quote to PT', 'error');
            }
        });
    }

    // Send Quote to Client
    const sendToClientBtn = document.getElementById('send-to-client-btn');
    if (sendToClientBtn) {
        sendToClientBtn.addEventListener('click', async function () {
            // Check if quote is costed
            if (quoteData && !quoteData.production_cost && quoteData.status !== 'Costed') {
                if (!confirm('This quote has not been costed by Production. Send anyway?')) {
                    return;
                }
            }

            this.textContent = 'Sending...';
            this.disabled = true;
            showLoading('Sending quote to client...');

            try {
                const response = await api.post(`/quotes/${quoteId}/send-to-client/`);

                hideLoading();
                showToast('Quote sent to client successfully!', 'success');

                // Update UI
                updateStatusBadge('Quoted');
                this.style.display = 'none';

                // Show approval link if returned
                if (response.approval_url) {
                    showApprovalLink(response.approval_url);
                }

                // Enable approve button
                const approveBtn = document.getElementById('approve-btn');
                if (approveBtn) approveBtn.style.display = 'block';

            } catch (error) {
                hideLoading();
                this.textContent = 'Send to Client';
                this.disabled = false;

                showToast(error.data?.detail || 'Error sending quote', 'error');
            }
        });
    }

    // Manual Approve Quote
    const approveBtn = document.getElementById('approve-btn');
    if (approveBtn) {
        approveBtn.addEventListener('click', async function () {
            if (!confirm('Mark this quote as approved? This cannot be undone.')) return;

            this.textContent = 'Approving...';
            this.disabled = true;

            try {
                await api.patch(`/quotes/${quoteId}/`, {
                    status: 'Approved',
                    approved_at: new Date().toISOString()
                });

                showToast('Quote approved!', 'success');

                // Update UI
                updateStatusBadge('Approved');
                this.style.display = 'none';

                // Show convert to job button
                const convertBtn = document.getElementById('convert-to-job-btn');
                if (convertBtn) convertBtn.style.display = 'block';

            } catch (error) {
                this.textContent = 'Approve Quote';
                this.disabled = false;

                showToast(error.data?.detail || 'Error approving quote', 'error');
            }
        });
    }

    // Convert to Job
    const convertToJobBtn = document.getElementById('convert-to-job-btn');
    if (convertToJobBtn) {
        convertToJobBtn.addEventListener('click', async function () {
            if (!confirm('Convert this approved quote to a production job?')) return;

            this.textContent = 'Converting...';
            this.disabled = true;
            showLoading('Creating job from quote...');

            try {
                const response = await api.post(`/quotes/${quoteId}/convert-to-job/`);

                hideLoading();
                showToast(`Job ${response.job_number || 'created'} created successfully!`, 'success');

                // Redirect to job detail
                setTimeout(() => {
                    if (response.job_id) {
                        window.location.href = `/job/${response.job_id}/`;
                    } else if (response.id) {
                        window.location.href = `/job/${response.id}/`;
                    } else {
                        window.location.href = '/account-manager/jobs/';
                    }
                }, 1500);

            } catch (error) {
                hideLoading();
                this.textContent = 'Convert to Job';
                this.disabled = false;

                showToast(error.data?.detail || 'Error converting quote', 'error');
            }
        });
    }

    // Revise Quote (Create New Version)
    const reviseBtn = document.getElementById('revise-btn');
    if (reviseBtn) {
        reviseBtn.addEventListener('click', async function () {
            if (!confirm('Create a revised version of this quote? The current version will be locked.')) return;

            this.textContent = 'Creating revision...';
            this.disabled = true;

            try {
                const response = await api.post(`/quotes/${quoteId}/revise/`);

                showToast('Revision created!', 'success');

                // Redirect to new revision
                setTimeout(() => {
                    window.location.href = `/quotes/${response.quote_id}/`;
                }, 1000);

            } catch (error) {
                this.textContent = 'Revise Quote';
                this.disabled = false;

                showToast(error.data?.detail || 'Error creating revision', 'error');
            }
        });
    }

    // Clone Quote
    const cloneBtn = document.getElementById('clone-btn');
    if (cloneBtn) {
        cloneBtn.addEventListener('click', async function () {
            this.textContent = 'Cloning...';
            this.disabled = true;

            try {
                // Clone is essentially a revise for a different client
                window.location.href = `/quotes/${quoteId}/clone/`;

            } catch (error) {
                this.textContent = 'Clone';
                this.disabled = false;
                showToast('Error cloning quote', 'error');
            }
        });
    }

    // Download PDF
    const downloadPdfBtn = document.getElementById('download-pdf-btn');
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', async function () {
            this.textContent = 'Generating...';
            this.disabled = true;

            try {
                // Open PDF in new tab
                window.open(`/quotes/${quoteId}/download/`, '_blank');

                this.textContent = 'Download PDF';
                this.disabled = false;

            } catch (error) {
                this.textContent = 'Download PDF';
                this.disabled = false;
                showToast('Error generating PDF', 'error');
            }
        });
    }

    // Mark as Lost
    const markLostBtn = document.getElementById('mark-lost-btn');
    if (markLostBtn) {
        markLostBtn.addEventListener('click', async function () {
            const reason = prompt('Why was this quote lost? (Optional)');
            if (reason === null) return; // Cancelled

            this.textContent = 'Updating...';
            this.disabled = true;

            try {
                await api.patch(`/quotes/${quoteId}/`, {
                    status: 'Lost',
                    notes: (quoteData?.notes || '') + `\n\nLost reason: ${reason || 'Not specified'}`
                });

                showToast('Quote marked as lost', 'info');
                updateStatusBadge('Lost');

                // Hide action buttons
                document.querySelectorAll('.quote-action-btn').forEach(btn => {
                    btn.style.display = 'none';
                });

            } catch (error) {
                this.textContent = 'Mark as Lost';
                this.disabled = false;
                showToast('Error updating quote', 'error');
            }
        });
    }

    // Delete Quote (Draft only)
    const deleteBtn = document.getElementById('delete-quote-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', async function () {
            if (quoteData?.status !== 'Draft') {
                showToast('Only draft quotes can be deleted', 'error');
                return;
            }

            if (!confirm('Are you sure you want to delete this quote? This cannot be undone.')) return;

            this.textContent = 'Deleting...';
            this.disabled = true;

            try {
                await api.delete(`/quotes/${quoteId}/`);

                showToast('Quote deleted', 'success');

                setTimeout(() => {
                    window.location.href = '/quotes/';
                }, 1000);

            } catch (error) {
                this.textContent = 'Delete';
                this.disabled = false;
                showToast(error.data?.detail || 'Error deleting quote', 'error');
            }
        });
    }

    // ============================================================
    // HELPER FUNCTIONS
    // ============================================================

    function updateStatusBadge(newStatus) {
        const badge = document.getElementById('quote-status-badge');
        if (badge) {
            badge.textContent = newStatus;

            // Update class
            badge.className = 'px-3 py-1 rounded-full text-sm font-medium ';

            const statusClasses = {
                'Draft': 'bg-gray-100 text-gray-800',
                'Sent to PT': 'bg-blue-100 text-blue-800',
                'Costed': 'bg-purple-100 text-purple-800',
                'Quoted': 'bg-yellow-100 text-yellow-800',
                'Client Review': 'bg-orange-100 text-orange-800',
                'Approved': 'bg-green-100 text-green-800',
                'Lost': 'bg-red-100 text-red-800',
                'Converted': 'bg-teal-100 text-teal-800'
            };

            badge.className += statusClasses[newStatus] || 'bg-gray-100 text-gray-800';
        }
    }

    function showApprovalLink(url) {
        const container = document.getElementById('approval-link-container');
        if (container) {
            container.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
                    <h4 class="font-medium text-green-800 mb-2">Approval Link Generated</h4>
                    <div class="flex items-center gap-2">
                        <input type="text" value="${url}" readonly class="form-input flex-1 text-sm" id="approval-link-input">
                        <button onclick="copyApprovalLink()" class="btn btn-secondary text-sm">Copy</button>
                    </div>
                    <p class="text-xs text-green-600 mt-2">Share this link with the client. It expires in 7 days.</p>
                </div>
            `;
        }
    }

    // Global function for copy
    window.copyApprovalLink = function () {
        const input = document.getElementById('approval-link-input');
        if (input) {
            input.select();
            document.execCommand('copy');
            showToast('Link copied to clipboard', 'success');
        }
    };

    // ============================================================
    // LINE ITEMS EDITING (for Draft quotes)
    // ============================================================

    // Add line item button
    const addLineBtn = document.getElementById('add-line-item-btn');
    if (addLineBtn) {
        addLineBtn.addEventListener('click', function () {
            const modal = document.getElementById('add-line-item-modal');
            if (modal) {
                openModal('add-line-item-modal');
            } else {
                window.location.href = `/quotes/${quoteId}/edit/`;
            }
        });
    }

    // Edit line buttons
    document.querySelectorAll('[data-action="edit-line"]').forEach(btn => {
        btn.addEventListener('click', function () {
            const lineId = this.dataset.lineId;
            // Redirect to edit page or open modal
            showToast('Line item editing coming soon', 'info');
        });
    });

    // Remove line buttons
    document.querySelectorAll('[data-action="remove-line"]').forEach(btn => {
        btn.addEventListener('click', async function () {
            const lineId = this.dataset.lineId;

            if (!confirm('Remove this line item?')) return;

            try {
                await api.delete(`/quote-line-items/${lineId}/`);

                // Remove from DOM
                this.closest('.line-item').remove();
                showToast('Line item removed', 'success');

                // Reload to update totals
                location.reload();

            } catch (error) {
                showToast('Error removing line item', 'error');
            }
        });
    });

    // ============================================================
    // NOTES EDITING
    // ============================================================

    const notesTextarea = document.getElementById('quote-notes');
    const saveNotesBtn = document.getElementById('save-notes-btn');
    let notesChanged = false;

    if (notesTextarea) {
        notesTextarea.addEventListener('input', function () {
            notesChanged = true;
            if (saveNotesBtn) {
                saveNotesBtn.disabled = false;
                saveNotesBtn.classList.remove('opacity-50');
            }
        });
    }

    if (saveNotesBtn) {
        saveNotesBtn.addEventListener('click', async function () {
            if (!notesChanged) return;

            this.textContent = 'Saving...';
            this.disabled = true;

            try {
                await api.patch(`/quotes/${quoteId}/`, {
                    notes: notesTextarea.value
                });

                showToast('Notes saved', 'success');
                notesChanged = false;
                this.textContent = 'Save Notes';
                this.classList.add('opacity-50');

            } catch (error) {
                this.textContent = 'Save Notes';
                this.disabled = false;
                showToast('Error saving notes', 'error');
            }
        });
    }

    console.log('Quote detail page initialized successfully');
});
