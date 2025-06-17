/**
 * Multi-Chain Portfolio Dashboard JavaScript
 * Handles navigation, buttons, charts, and HTMX interactions
 */

// Global state management
window.DashboardApp = {
    currentCase: null,
    charts: {},
    notifications: [],
    eventSource: null,
    simulationEnabled: true
};

// Notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg max-w-sm z-50 ${
        type === 'success' ? 'bg-green-600' : 
        type === 'error' ? 'bg-red-600' : 
        type === 'warning' ? 'bg-yellow-600' : 'bg-blue-600'
    } text-white`;
    
    notification.innerHTML = `
        <div class="flex items-start space-x-3">
            <svg class="w-5 h-5 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${type === 'success' ? 
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>' :
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>'
                }
            </svg>
            <div>
                <p class="font-semibold">${type.charAt(0).toUpperCase() + type.slice(1)}</p>
                <p class="text-sm opacity-90">${message}</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Button functionality
function handleAddWallet() {
    showNotification('Add Wallet modal would open here', 'info');
}

function handleExportData() {
    showNotification('Exporting case data...', 'info');
    // Simulate export process
    setTimeout(() => {
        showNotification('Data exported successfully!', 'success');
    }, 1000);
}

function handleGenerateReport() {
    showNotification('Generating comprehensive report...', 'info');
    // Simulate report generation
    setTimeout(() => {
        showNotification('Report generated successfully!', 'success');
    }, 2000);
}

function handleRefreshData() {
    showNotification('Refreshing portfolio data...', 'info');
    // Simulate data refresh
    setTimeout(() => {
        showNotification('Portfolio data updated!', 'success');
        // Refresh charts if they exist
        Object.values(window.DashboardApp.charts).forEach(chart => {
            if (chart && typeof chart.update === 'function') {
                chart.update();
            }
        });
    }, 1500);
}

// Real-time simulation management
function startRealTimeUpdates(caseId) {
    if (!window.DashboardApp.simulationEnabled || window.DashboardApp.eventSource) {
        return;
    }
    
    try {
        // Use regular polling instead of SSE for better compatibility
        window.DashboardApp.updateInterval = setInterval(() => {
            fetch(`/htmx/cases/${caseId}/chart-data/7D/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateChartData(data);
                        updateSimulationStatus(data);
                    }
                })
                .catch(error => {
                    console.error('Real-time update error:', error);
                });
        }, 3000); // Update every 3 seconds
        
        showNotification('Real-time simulation active', 'success');
        console.log('Real-time updates started for case', caseId);
    } catch (error) {
        console.error('Failed to start real-time updates:', error);
    }
}

function stopRealTimeUpdates() {
    if (window.DashboardApp.updateInterval) {
        clearInterval(window.DashboardApp.updateInterval);
        window.DashboardApp.updateInterval = null;
    }
    
    if (window.DashboardApp.eventSource) {
        window.DashboardApp.eventSource.close();
        window.DashboardApp.eventSource = null;
    }
}

function updateSimulationStatus(data) {
    // Update simulation time display
    const statusElement = document.getElementById('simulation-status');
    if (statusElement && data.simulation_time) {
        statusElement.textContent = `Simulation Time: ${data.simulation_time}`;
    }
    
    // Show fraud alerts if any
    if (data.recent_events && data.recent_events.length > 0) {
        const latestEvent = data.recent_events[data.recent_events.length - 1];
        if (latestEvent && Math.random() < 0.3) { // Occasionally show alerts
            showNotification(`Fraud Alert: ${latestEvent.description}`, 'warning');
        }
    }
}

// Chart timeframe switching
function switchTimeframe(timeframe, caseId, clickedButton) {
    showNotification(`Switching to ${timeframe} view...`, 'info');
    
    // Update button states
    document.querySelectorAll('.timeframe-btn').forEach(btn => {
        btn.classList.remove('bg-blue-600', 'text-white');
        btn.classList.add('bg-gray-700', 'text-gray-300');
    });
    
    // Highlight selected button
    if (clickedButton) {
        clickedButton.classList.remove('bg-gray-700', 'text-gray-300');
        clickedButton.classList.add('bg-blue-600', 'text-white');
    }
    
    // Temporarily stop real-time updates during manual timeframe change
    const wasRealTime = !!window.DashboardApp.updateInterval;
    if (wasRealTime) {
        stopRealTimeUpdates();
    }
    
    // If we have a case ID, fetch new chart data
    if (caseId) {
        fetch(`/htmx/cases/${caseId}/chart-data/${timeframe}/`)
            .then(response => response.json())
            .then(data => {
                console.log('Chart data received:', data);
                if (data.success) {
                    updateChartData(data);
                    // Restart real-time updates for 7D view
                    if (timeframe === '7D' && wasRealTime) {
                        setTimeout(() => startRealTimeUpdates(caseId), 1000);
                    }
                } else {
                    showNotification('Failed to update chart data', 'error');
                }
            })
            .catch(error => {
                console.error('Error fetching chart data:', error);
                showNotification('Failed to update chart data', 'error');
            });
    }
}

// Update chart with new data
function updateChartData(data) {
    const portfolioChart = window.DashboardApp.charts.portfolio;
    const activityChart = window.DashboardApp.charts.activity;
    
    if (portfolioChart && data.multi_chain_data) {
        // Update multi-chain wallet balance tracking chart
        portfolioChart.data.labels = data.labels;
        portfolioChart.data.datasets = [
            {
                label: 'Ethereum',
                data: data.multi_chain_data.ethereum.balances,
                borderColor: '#627EEA',
                backgroundColor: 'rgba(98, 126, 234, 0.1)',
                fill: false,
                tension: 0.4
            },
            {
                label: 'Arbitrum', 
                data: data.multi_chain_data.arbitrum.balances,
                borderColor: '#28A0F0',
                backgroundColor: 'rgba(40, 160, 240, 0.1)', 
                fill: false,
                tension: 0.4
            },
            {
                label: 'Optimism',
                data: data.multi_chain_data.optimism.balances,
                borderColor: '#FF0420',
                backgroundColor: 'rgba(255, 4, 32, 0.1)',
                fill: false,
                tension: 0.4
            },
            {
                label: 'Polygon',
                data: data.multi_chain_data.polygon.balances,
                borderColor: '#8247E5',
                backgroundColor: 'rgba(130, 71, 229, 0.1)',
                fill: false,
                tension: 0.4
            }
        ];
        portfolioChart.update('none');
        
        showNotification(`Updated ${data.timeframe} - tracking ${data.summary.chains_tracked} chains (${data.summary.change_percent}% change)`, 'success');
    }
    
    if (activityChart && data.multi_chain_data) {
        // Update on-chain transaction volume chart
        activityChart.data.labels = data.labels;
        activityChart.data.datasets = [
            {
                label: 'Ethereum Volume',
                data: data.multi_chain_data.ethereum.volume,
                backgroundColor: '#627EEA',
                borderRadius: 4
            },
            {
                label: 'Arbitrum Volume',
                data: data.multi_chain_data.arbitrum.volume,
                backgroundColor: '#28A0F0',
                borderRadius: 4
            },
            {
                label: 'Optimism Volume',
                data: data.multi_chain_data.optimism.volume,
                backgroundColor: '#FF0420',
                borderRadius: 4
            },
            {
                label: 'Polygon Volume',
                data: data.multi_chain_data.polygon.volume,
                backgroundColor: '#8247E5',
                borderRadius: 4
            }
        ];
        activityChart.options.scales.y.ticks.callback = function(value) {
            return '$' + (value / 1000).toFixed(0) + 'K';
        };
        activityChart.update('none');
    }
}

// Initialize charts when DOM is ready
function initializeCharts() {
    // Only initialize if Chart.js is available and we haven't initialized yet
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not available, skipping chart initialization');
        return;
    }

    // Portfolio Chart
    const portfolioCtx = document.getElementById('portfolio-chart');
    if (portfolioCtx && !window.DashboardApp.charts.portfolio) {
        try {
            // Check if we have data from Django context
            let flowLabels, inflowData, outflowData;
            
            try {
                // Try to get data from template variables (will be undefined if not in case detail)
                flowLabels = typeof window.chartData !== 'undefined' ? window.chartData.flowLabels : 
                    ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'];
                inflowData = typeof window.chartData !== 'undefined' ? window.chartData.inflowData : 
                    [120000, 85000, 95000, 110000, 78000, 130000, 102000];
                outflowData = typeof window.chartData !== 'undefined' ? window.chartData.outflowData : 
                    [45000, 62000, 38000, 71000, 56000, 49000, 84000];
            } catch (e) {
                // Fallback to demo data
                flowLabels = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'];
                inflowData = [120000, 85000, 95000, 110000, 78000, 130000, 102000];
                outflowData = [45000, 62000, 38000, 71000, 56000, 49000, 84000];
            }
            
            window.DashboardApp.charts.portfolio = new Chart(portfolioCtx, {
                type: 'line',
                data: {
                    labels: flowLabels,
                    datasets: [{
                        label: 'Inflow',
                        data: inflowData,
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: false,
                        tension: 0.4
                    }, {
                        label: 'Outflow',
                        data: outflowData,
                        borderColor: '#EF4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: false,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true,
                            labels: { color: '#9CA3AF' }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                },
                                color: '#9CA3AF'
                            },
                            grid: { color: '#374151' }
                        },
                        x: {
                            ticks: { color: '#9CA3AF' },
                            grid: { color: '#374151' }
                        }
                    }
                }
            });
            console.log('Portfolio chart initialized successfully');
        } catch (error) {
            console.error('Error initializing portfolio chart:', error);
        }
    }

    // Activity Chart
    const activityCtx = document.getElementById('activity-chart');
    if (activityCtx && !window.DashboardApp.charts.activity) {
        try {
            let timelineLabels, timelineData;
            
            try {
                timelineLabels = typeof window.chartData !== 'undefined' ? window.chartData.timelineLabels : 
                    ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
                timelineData = typeof window.chartData !== 'undefined' ? window.chartData.timelineData : 
                    [45, 62, 38, 71];
            } catch (e) {
                timelineLabels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
                timelineData = [45, 62, 38, 71];
            }
            
            window.DashboardApp.charts.activity = new Chart(activityCtx, {
                type: 'bar',
                data: {
                    labels: timelineLabels,
                    datasets: [{
                        label: 'Transactions',
                        data: timelineData,
                        backgroundColor: '#8B5CF6',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { 
                                color: '#9CA3AF',
                                stepSize: 1
                            },
                            grid: { color: '#374151' }
                        },
                        x: {
                            ticks: { 
                                color: '#9CA3AF',
                                maxTicksLimit: 10
                            },
                            grid: { display: false }
                        }
                    }
                }
            });
            console.log('Activity chart initialized successfully');
        } catch (error) {
            console.error('Error initializing activity chart:', error);
        }
    }
}

// HTMX event handlers
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard app initializing...');
    
    // Initialize charts
    initializeCharts();
    
    // Add global button event listeners
    document.addEventListener('click', function(e) {
        // Handle timeframe buttons
        if (e.target.classList.contains('timeframe-btn')) {
            e.preventDefault();
            const timeframe = e.target.textContent.trim();
            const caseId = e.target.dataset.caseId;
            switchTimeframe(timeframe, caseId, e.target);
        }
        
        // Handle action buttons
        if (e.target.closest('[data-action]')) {
            e.preventDefault();
            const action = e.target.closest('[data-action]').dataset.action;
            
            switch (action) {
                case 'add-wallet':
                    handleAddWallet();
                    break;
                case 'export-data':
                    handleExportData();
                    break;
                case 'generate-report':
                    handleGenerateReport();
                    break;
                case 'refresh-data':
                    handleRefreshData();
                    break;
                default:
                    showNotification(`Action "${action}" triggered`, 'info');
            }
        }
    });
    
    // HTMX after request handler
    document.addEventListener('htmx:afterRequest', function(e) {
        // Re-initialize charts after HTMX content loads
        setTimeout(initializeCharts, 100);
        
        // Start real-time updates if we're on a case detail page
        const path = new URL(e.detail.xhr.responseURL).pathname;
        if (path.includes('/cases/') && path.match(/\/cases\/\d+\//)) {
            const caseId = path.match(/\/cases\/(\d+)\//)[1];
            setTimeout(() => {
                initializeCharts();
                if (window.DashboardApp.simulationEnabled) {
                    startRealTimeUpdates(caseId);
                }
            }, 500);
            showNotification('Investigation loaded - Real-time tracking active', 'success');
        } else {
            // Stop real-time updates when leaving case detail
            stopRealTimeUpdates();
            if (e.detail.xhr.status === 200 && path.includes('/cases')) {
                showNotification('Navigation completed', 'success');
            }
        }
    });
    
    // HTMX error handler
    document.addEventListener('htmx:responseError', function(e) {
        showNotification('Navigation error occurred', 'error');
        console.error('HTMX error:', e.detail);
    });
    
    console.log('Dashboard app initialized successfully');
});

// Global functions for template usage
window.showNotification = showNotification;
window.switchTimeframe = switchTimeframe;
window.handleAddWallet = handleAddWallet;
window.handleExportData = handleExportData;
window.handleGenerateReport = handleGenerateReport;
window.handleRefreshData = handleRefreshData;
window.startRealTimeUpdates = startRealTimeUpdates;
window.stopRealTimeUpdates = stopRealTimeUpdates;

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopRealTimeUpdates();
});