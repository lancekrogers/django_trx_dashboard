/**
 * Dashboard Chart - Visitors chart initialization for dashboard
 * Handles the multi-line chart showing visitors and page views data
 */

class DashboardChart {
    constructor(canvasId = 'visitors-chart') {
        this.canvasId = canvasId;
        this.chart = null;
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initChart());
        } else {
            this.initChart();
        }
    }

    initChart() {
        const ctx = document.getElementById(this.canvasId);
        if (!ctx) {
            console.warn(`Dashboard chart canvas #${this.canvasId} not found`);
            return;
        }

        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'line',
            data: this.getChartData(),
            options: this.getChartOptions()
        });
    }

    getChartData() {
        return {
            labels: ['Apr 7', 'Apr 14', 'Apr 21', 'Apr 29', 'May 6', 'May 13', 'May 21', 'May 29', 'Jun 5', 'Jun 12', 'Jun 20', 'Jun 29'],
            datasets: [{
                label: 'Visitors',
                data: [320, 450, 380, 520, 480, 620, 580, 720, 680, 820, 780, 920],
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                borderWidth: 2,
            }, {
                label: 'Page Views',
                data: [220, 350, 280, 420, 380, 520, 480, 620, 580, 720, 680, 820],
                borderColor: 'rgb(236, 72, 153)',
                backgroundColor: 'rgba(236, 72, 153, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                borderWidth: 2,
            }]
        };
    }

    getChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1a1a',
                    titleColor: '#e5e5e5',
                    bodyColor: '#a0a0a0',
                    borderColor: '#2a2a2a',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    intersect: false,
                    mode: 'index'
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        borderColor: '#2a2a2a'
                    },
                    ticks: {
                        color: '#a0a0a0',
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        color: '#2a2a2a',
                        borderColor: '#2a2a2a'
                    },
                    ticks: {
                        color: '#a0a0a0',
                        font: {
                            size: 11
                        }
                    }
                }
            }
        };
    }

    // Update chart with new data
    updateData(newData) {
        if (this.chart) {
            this.chart.data = newData;
            this.chart.update();
        }
    }

    // Destroy chart instance
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// Initialize dashboard chart when script loads
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if the canvas exists
    if (document.getElementById('visitors-chart')) {
        window.dashboardChart = new DashboardChart('visitors-chart');
    }
});

// Re-initialize after HTMX swaps
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Check if the swapped content contains the chart canvas
    if (evt.target.querySelector && evt.target.querySelector('#visitors-chart')) {
        if (window.dashboardChart) {
            window.dashboardChart.destroy();
        }
        window.dashboardChart = new DashboardChart('visitors-chart');
    }
});

// Make DashboardChart available globally
window.DashboardChart = DashboardChart;