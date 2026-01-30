// clientapp/static/js/websocket-client.js

/**
 * WebSocket Client for Real-Time Updates
 * 
 * Usage:
 *   const client = new WebSocketClient();
 *   client.connectToJob(123, (data) => {
 *     console.log('Job update:', data);
 *   });
 */

class WebSocketClient {
    constructor() {
        this.connections = {};
        this.reconnectAttempts = {};
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
    }

    /**
     * Connect to job updates WebSocket
     * @param {number} jobId - Job ID to connect to
     * @param {function} onMessage - Callback when message received
     */
    connectToJob(jobId, onMessage) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsPath = `${protocol}//${window.location.host}/ws/jobs/${jobId}/`;
        
        this.connect(`job_${jobId}`, wsPath, onMessage);
    }

    /**
     * Connect to dashboard updates WebSocket
     * @param {string} dashboardType - Type of dashboard (jobs, substitutions, etc)
     * @param {function} onMessage - Callback when message received
     */
    connectToDashboard(dashboardType, onMessage) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsPath = `${protocol}//${window.location.host}/ws/dashboard/${dashboardType}/`;
        
        this.connect(`dashboard_${dashboardType}`, wsPath, onMessage);
    }

    /**
     * Connect to user notifications WebSocket
     * @param {number} userId - User ID
     * @param {function} onMessage - Callback when message received
     */
    connectToNotifications(userId, onMessage) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsPath = `${protocol}//${window.location.host}/ws/notifications/${userId}/`;
        
        this.connect(`notifications_${userId}`, wsPath, onMessage);
    }

    /**
     * Connect to material substitution updates WebSocket
     * @param {number} substitutionId - Substitution ID to connect to
     * @param {function} onMessage - Callback when message received
     */
    connectToSubstitution(substitutionId, onMessage) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsPath = `${protocol}//${window.location.host}/ws/substitutions/${substitutionId}/`;
        
        this.connect(`substitution_${substitutionId}`, wsPath, onMessage);
    }

    /**
     * Generic WebSocket connection
     * @private
     */
    connect(connectionId, wsPath, onMessage) {
        if (this.connections[connectionId]) {
            console.log(`Already connected to ${connectionId}`);
            return;
        }

        console.log(`Connecting to WebSocket: ${wsPath}`);

        const ws = new WebSocket(wsPath);

        ws.onopen = () => {
            console.log(`✓ WebSocket connected: ${connectionId}`);
            this.reconnectAttempts[connectionId] = 0;
            this.showConnectionStatus(`Connected`, 'connected');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(`📨 Message from ${connectionId}:`, data);
            
            if (onMessage) {
                onMessage(data);
            }
            
            // Handle different message types
            this.handleMessage(data, connectionId);
        };

        ws.onerror = (error) => {
            console.error(`✗ WebSocket error (${connectionId}):`, error);
            this.showConnectionStatus(`Error`, 'error');
        };

        ws.onclose = () => {
            console.log(`✗ WebSocket closed: ${connectionId}`);
            delete this.connections[connectionId];
            this.showConnectionStatus(`Disconnected`, 'disconnected');
            
            // Attempt to reconnect
            this.attemptReconnect(connectionId, wsPath, onMessage);
        };

        this.connections[connectionId] = ws;
    }

    /**
     * Attempt to reconnect to WebSocket
     * @private
     */
    attemptReconnect(connectionId, wsPath, onMessage) {
        if (!this.reconnectAttempts[connectionId]) {
            this.reconnectAttempts[connectionId] = 0;
        }

        if (this.reconnectAttempts[connectionId] >= this.maxReconnectAttempts) {
            console.error(`Max reconnection attempts reached for ${connectionId}`);
            this.showConnectionStatus(`Connection Failed`, 'error');
            return;
        }

        this.reconnectAttempts[connectionId]++;
        const delay = this.reconnectDelay * this.reconnectAttempts[connectionId];
        
        console.log(`Reconnecting to ${connectionId} in ${delay}ms (attempt ${this.reconnectAttempts[connectionId]})`);

        setTimeout(() => {
            this.connect(connectionId, wsPath, onMessage);
        }, delay);
    }

    /**
     * Handle incoming WebSocket message
     * @private
     */
    handleMessage(data, connectionId) {
        const messageType = data.type;

        switch (messageType) {
            case 'job_status_updated':
                this.handleJobStatusUpdate(data);
                break;

            case 'job_progress_updated':
                this.handleJobProgressUpdate(data);
                break;

            case 'job_assigned':
                this.handleJobAssigned(data);
                break;

            case 'substitution_status_changed':
                this.handleSubstitutionStatusChange(data);
                break;

            case 'substitution_approved':
                this.handleSubstitutionApproved(data);
                break;

            case 'substitution_rejected':
                this.handleSubstitutionRejected(data);
                break;

            case 'invoice_status_changed':
                this.handleInvoiceStatusChange(data);
                break;

            case 'deadline_approaching':
                this.handleDeadlineApproaching(data);
                break;

            default:
                console.log('Unhandled message type:', messageType);
        }
    }

    /**
     * Handle job status update
     * @private
     */
    handleJobStatusUpdate(data) {
        console.log(`Job ${data.job_id} status changed to: ${data.status}`);
        
        // Update UI element if exists
        const statusElement = document.querySelector(`[data-job-id="${data.job_id}"] .job-status`);
        if (statusElement) {
            statusElement.textContent = data.status;
            statusElement.className = `job-status status-${data.status.toLowerCase()}`;
        }

        // Dispatch custom event for listeners
        window.dispatchEvent(new CustomEvent('jobStatusUpdated', {
            detail: data
        }));
    }

    /**
     * Handle job progress update
     * @private
     */
    handleJobProgressUpdate(data) {
        console.log(`Job ${data.job_id} progress: ${data.progress}%`);

        // Update progress bar if exists
        const progressElement = document.querySelector(`[data-job-id="${data.job_id}"] .job-progress`);
        if (progressElement) {
            progressElement.style.width = `${data.progress}%`;
            progressElement.textContent = `${data.progress}%`;
        }

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('jobProgressUpdated', {
            detail: data
        }));
    }

    /**
     * Handle job assignment
     * @private
     */
    handleJobAssigned(data) {
        console.log(`Job ${data.job_number} assigned!`);
        this.showNotification(data.title, 'job_assigned');
    }

    /**
     * Handle substitution status change
     * @private
     */
    handleSubstitutionStatusChange(data) {
        console.log(`Substitution ${data.substitution_id} status: ${data.status}`);

        // Update UI element if exists
        const statusElement = document.querySelector(`[data-substitution-id="${data.substitution_id}"] .substitution-status`);
        if (statusElement) {
            statusElement.textContent = data.status;
            statusElement.className = `substitution-status status-${data.status.toLowerCase()}`;
        }

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('substitutionStatusChanged', {
            detail: data
        }));
    }

    /**
     * Handle substitution approved
     * @private
     */
    handleSubstitutionApproved(data) {
        console.log(`Substitution ${data.substitution_id} approved!`);
        this.showNotification(data.title, 'substitution_approved');
    }

    /**
     * Handle substitution rejected
     * @private
     */
    handleSubstitutionRejected(data) {
        console.log(`Substitution ${data.substitution_id} rejected`);
        this.showNotification(`${data.title}: ${data.reason}`, 'substitution_rejected');
    }

    /**
     * Handle invoice status change
     * @private
     */
    handleInvoiceStatusChange(data) {
        console.log(`Invoice ${data.invoice_id} status: ${data.status}`);
        this.showNotification(data.title, 'invoice_status_changed');
    }

    /**
     * Handle deadline approaching
     * @private
     */
    handleDeadlineApproaching(data) {
        console.log(`Deadline approaching for job ${data.job_number}`);
        this.showNotification(
            `${data.title}: ${data.job_number} (${data.days_remaining} days remaining)`,
            `deadline_${data.severity}`
        );
    }

    /**
     * Show in-app notification
     * @private
     */
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // Add to page
        const container = document.querySelector('.notification-container');
        if (container) {
            container.appendChild(notification);
        } else {
            document.body.appendChild(notification);
        }

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    /**
     * Show connection status
     * @private
     */
    showConnectionStatus(status, type) {
        const statusElement = document.querySelector('.websocket-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `websocket-status status-${type}`;
        }
    }

    /**
     * Send message on WebSocket
     */
    send(connectionId, data) {
        const ws = this.connections[connectionId];
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
        } else {
            console.warn(`WebSocket ${connectionId} not ready or not connected`);
        }
    }

    /**
     * Disconnect from WebSocket
     */
    disconnect(connectionId) {
        const ws = this.connections[connectionId];
        if (ws) {
            ws.close();
            delete this.connections[connectionId];
        }
    }

    /**
     * Disconnect all WebSockets
     */
    disconnectAll() {
        Object.keys(this.connections).forEach(connectionId => {
            this.disconnect(connectionId);
        });
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}

// Make available globally
window.WebSocketClient = WebSocketClient;
