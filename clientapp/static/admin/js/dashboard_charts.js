// Dashboard Charts Initialization
document.addEventListener('DOMContentLoaded', function () {

    // ==================== SALES PERFORMANCE CHART ====================
    const salesCtx = document.getElementById('salesPerformanceChart');
    if (salesCtx && typeof salesPerformanceData !== 'undefined') {
        new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: salesPerformanceData.map(item => {
                    const date = new Date(item.month);
                    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                }),
                datasets: [{
                    label: 'Revenue (KES)',
                    data: salesPerformanceData.map(item => item.revenue || 0),
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3498db',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function (context) {
                                return 'Revenue: KES ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function (value) {
                                return 'KES ' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // ==================== ORDER STATUS DISTRIBUTION CHART ====================
    const orderCtx = document.getElementById('orderStatusChart');
    if (orderCtx && typeof orderStatusData !== 'undefined') {
        // Prepare data
        const labels = orderStatusData.map(item =>
            item.status.charAt(0).toUpperCase() + item.status.slice(1).replace('_', ' ')
        );
        const data = orderStatusData.map(item => item.count);
        const colors = {
            'pending': '#FFA500',
            'approved': '#0066CC',
            'in_production': '#FFD700',
            'in production': '#FFD700',
            'completed': '#28A745',
            'cancelled': '#DC3545'
        };
        const backgroundColors = orderStatusData.map(item =>
            colors[item.status.toLowerCase()] || '#6C757D'
        );

        new Chart(orderCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderWidth: 2,
                    borderColor: '#fff',
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 13
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function (context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }
});
