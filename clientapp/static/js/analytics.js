/**
 * Analytics Dashboard - Chart.js Configurations
 * Vendor Performance Metrics & Real-Time Updates
 */

// Global chart instances storage
window.chartInstances = {};

/**
 * Initialize all charts on dashboard load
 */
async function initializeAnalyticsDashboard() {
    try {
        // Load data from API endpoints
        const [deliveryData, qualityData, turnaroundData, completionData] = await Promise.all([
            loadDeliveryRateData(),
            loadQualityScoresData(),
            loadTurnaroundTimeData(),
            loadJobCompletionData()
        ]);
        
        // Initialize Chart.js charts
        initializeDeliveryRateChart(deliveryData);
        initializeQualityScoresChart(qualityData);
        initializeTurnaroundTimeChart(turnaroundData);
        initializeJobCompletionChart(completionData);
        
        // Update stat cards
        updateStatCards(deliveryData, qualityData, turnaroundData, completionData);
        
        // Hide loading spinners
        document.getElementById('deliveryLoading').style.display = 'none';
        document.getElementById('qualityLoading').style.display = 'none';
        document.getElementById('turnaroundLoading').style.display = 'none';
        document.getElementById('completionLoading').style.display = 'none';
        
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showToast('Error loading analytics data', 'error');
    }
}

/**
 * Load delivery rate data from API
 */
async function loadDeliveryRateData() {
    try {
        const months = document.getElementById('dateRangeFilter').value || 12;
        const response = await fetch(`/api/analytics/vendor-delivery-rate/?months=${months}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Delivery rate data:', data);
        return data;
    } catch (error) {
        console.error('Error loading delivery rate:', error);
        return {
            months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            vendors: {
                'Vendor A': [95, 93, 96, 94, 95, 97],
                'Vendor B': [88, 90, 89, 91, 92, 94],
                'Vendor C': [92, 91, 90, 89, 88, 87]
            },
            average: 91.5
        };
    }
}

/**
 * Load quality scores data from API
 */
async function loadQualityScoresData() {
    try {
        const response = await fetch('/api/analytics/vendor-quality-scores/?limit=10');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Quality scores data:', data);
        return data;
    } catch (error) {
        console.error('Error loading quality scores:', error);
        return {
            vendors: [
                { name: 'Vendor A', score: 4.7, jobs: 45 },
                { name: 'Vendor B', score: 4.5, jobs: 38 },
                { name: 'Vendor C', score: 4.2, jobs: 41 },
                { name: 'Vendor D', score: 4.0, jobs: 35 },
                { name: 'Vendor E', score: 3.8, jobs: 28 }
            ],
            total_vendors: 5
        };
    }
}

/**
 * Load turnaround time data from API
 */
async function loadTurnaroundTimeData() {
    try {
        const months = document.getElementById('dateRangeFilter').value || 12;
        const response = await fetch(`/api/analytics/vendor-turnaround-time/?months=${months}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Turnaround time data:', data);
        return data;
    } catch (error) {
        console.error('Error loading turnaround time:', error);
        return {
            vendors: [
                { name: 'Vendor A', avg_days: 3.5, performance: 'excellent' },
                { name: 'Vendor B', avg_days: 4.2, performance: 'excellent' },
                { name: 'Vendor C', avg_days: 5.1, performance: 'good' },
                { name: 'Vendor D', avg_days: 6.3, performance: 'needs_improvement' }
            ],
            target_days: 5.0,
            best_performer: { name: 'Vendor A', avg_days: 3.5 }
        };
    }
}

/**
 * Load job completion stats from API
 */
async function loadJobCompletionData() {
    try {
        const response = await fetch('/api/analytics/job-completion-stats/');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Job completion data:', data);
        return data;
    } catch (error) {
        console.error('Error loading completion stats:', error);
        return {
            completed: 120,
            in_progress: 45,
            pending: 30,
            total: 195,
            completion_rate: 61.5,
            in_progress_rate: 23.1
        };
    }
}

/**
 * Initialize Delivery Rate Line Chart
 */
function initializeDeliveryRateChart(data) {
    const ctx = document.getElementById('deliveryChart')?.getContext('2d');
    if (!ctx) return;
    
    // Prepare datasets for each vendor
    const datasets = [];
    const colors = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'];
    
    let colorIndex = 0;
    for (const [vendorName, rates] of Object.entries(data.vendors || {})) {
        datasets.push({
            label: vendorName,
            data: rates,
            borderColor: colors[colorIndex % colors.length],
            backgroundColor: colors[colorIndex % colors.length] + '15',
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 5,
            pointBackgroundColor: colors[colorIndex % colors.length],
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointHoverRadius: 7
        });
        colorIndex++;
    }
    
    const config = {
        type: 'line',
        data: {
            labels: data.months || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        padding: 15,
                        font: { size: 12, weight: 600 },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 14, weight: 600 },
                    bodyFont: { size: 13 },
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        font: { size: 11 }
                    },
                    grid: {
                        color: '#e2e8f0',
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { size: 11 }
                    }
                }
            }
        }
    };
    
    window.chartInstances['deliveryChart'] = new Chart(ctx, config);
}

/**
 * Initialize Quality Scores Bar Chart
 */
function initializeQualityScoresChart(data) {
    const ctx = document.getElementById('qualityChart')?.getContext('2d');
    if (!ctx) return;
    
    const vendors = data.vendors || [];
    const vendorNames = vendors.map(v => v.name);
    const scores = vendors.map(v => v.score);
    
    // Color based on score
    const colors = scores.map(score => {
        if (score >= 4.5) return '#10b981';  // Green
        if (score >= 4.0) return '#f59e0b';  // Yellow
        return '#ef4444';                     // Red
    });
    
    const config = {
        type: 'bar',
        data: {
            labels: vendorNames,
            datasets: [{
                label: 'Quality Score',
                data: scores,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'x',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return 'Score: ' + context.parsed.y.toFixed(1) + '/5.0';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 5,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(1);
                        },
                        font: { size: 11 }
                    },
                    grid: {
                        color: '#e2e8f0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { size: 10 }
                    }
                }
            }
        }
    };
    
    window.chartInstances['qualityChart'] = new Chart(ctx, config);
}

/**
 * Initialize Turnaround Time Area Chart
 */
function initializeTurnaroundTimeChart(data) {
    const ctx = document.getElementById('turnaroundChart')?.getContext('2d');
    if (!ctx) return;
    
    const vendors = data.vendors || [];
    const vendorNames = vendors.map(v => v.name);
    const days = vendors.map(v => v.avg_days);
    const target = data.target_days || 5;
    
    const config = {
        type: 'bar',
        data: {
            labels: vendorNames,
            datasets: [
                {
                    label: 'Avg Turnaround (days)',
                    data: days,
                    backgroundColor: '#8b5cf6',
                    borderColor: '#7c3aed',
                    borderWidth: 1,
                    borderRadius: 6
                },
                {
                    label: 'Target (5 days)',
                    data: Array(vendorNames.length).fill(target),
                    type: 'line',
                    borderColor: '#ef4444',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(1) + ' days';
                        },
                        font: { size: 11 }
                    },
                    grid: {
                        color: '#e2e8f0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    };
    
    window.chartInstances['turnaroundChart'] = new Chart(ctx, config);
}

/**
 * Initialize Job Completion Doughnut Chart
 */
function initializeJobCompletionChart(data) {
    const ctx = document.getElementById('completionChart')?.getContext('2d');
    if (!ctx) return;
    
    const completed = data.completed || 0;
    const inProgress = data.in_progress || 0;
    const pending = data.pending || 0;
    
    const config = {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'In Progress', 'Pending'],
            datasets: [{
                data: [completed, inProgress, pending],
                backgroundColor: ['#10b981', '#3b82f6', '#f59e0b'],
                borderColor: ['#059669', '#1d4ed8', '#d97706'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: { size: 12, weight: 600 },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const total = completed + inProgress + pending;
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    };
    
    window.chartInstances['completionChart'] = new Chart(ctx, config);
}

/**
 * Update stat cards with current data
 */
function updateStatCards(deliveryData, qualityData, turnaroundData, completionData) {
    // Completion Rate
    const completionRate = completionData.completion_rate || 0;
    document.getElementById('completionRate').textContent = completionRate.toFixed(1) + '%';
    
    // On-Time Delivery Rate
    const onTimeRate = deliveryData.average || 91.5;
    document.getElementById('onTimeRate').textContent = onTimeRate.toFixed(1) + '%';
    
    // Average Quality Score
    const avgQuality = qualityData.vendors?.[0]?.score || 4.2;
    document.getElementById('avgQuality').textContent = avgQuality.toFixed(1) + '/5.0';
    
    // Average Turnaround Time
    const avgTurnaround = turnaroundData.vendors?.[0]?.avg_days || 4.2;
    document.getElementById('avgTurnaround').textContent = avgTurnaround.toFixed(1) + ' days';
}

/**
 * Refresh all charts with new data
 */
async function refreshAllCharts() {
    try {
        // Show loading spinners
        document.getElementById('deliveryLoading').style.display = 'flex';
        document.getElementById('qualityLoading').style.display = 'flex';
        document.getElementById('turnaroundLoading').style.display = 'flex';
        document.getElementById('completionLoading').style.display = 'flex';
        
        // Load new data
        const [deliveryData, qualityData, turnaroundData, completionData] = await Promise.all([
            loadDeliveryRateData(),
            loadQualityScoresData(),
            loadTurnaroundTimeData(),
            loadJobCompletionData()
        ]);
        
        // Destroy old charts
        Object.values(window.chartInstances).forEach(chart => chart.destroy());
        window.chartInstances = {};
        
        // Reinitialize charts
        initializeDeliveryRateChart(deliveryData);
        initializeQualityScoresChart(qualityData);
        initializeTurnaroundTimeChart(turnaroundData);
        initializeJobCompletionChart(completionData);
        
        // Update stats
        updateStatCards(deliveryData, qualityData, turnaroundData, completionData);
        
        // Hide loading spinners
        document.getElementById('deliveryLoading').style.display = 'none';
        document.getElementById('qualityLoading').style.display = 'none';
        document.getElementById('turnaroundLoading').style.display = 'none';
        document.getElementById('completionLoading').style.display = 'none';
        
        return true;
    } catch (error) {
        console.error('Error refreshing charts:', error);
        showToast('Error refreshing data', 'error');
        return false;
    }
}
