import { PortfolioChart } from './portfolio-chart.js';
import { RealTimeManager } from './real-time-manager.js';
import { TransactionTable } from './transaction-table.js';

// Initialize modules when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize portfolio chart
    const chartElement = document.getElementById('portfolio-chart');
    if (chartElement) {
        window.portfolioChart = new PortfolioChart(chartElement);
    }

    // Initialize real-time connection manager
    window.realTimeManager = new RealTimeManager();

    // Initialize transaction table enhancements
    const transactionContainer = document.getElementById('transaction-container');
    if (transactionContainer) {
        new TransactionTable(transactionContainer);
    }

    // Setup HTMX event handlers
    setupHTMXHandlers();
});

function setupHTMXHandlers() {
    // Handle SSE messages
    document.addEventListener('htmx:sseMessage', (evt) => {
        if (evt.detail.type === 'portfolio-update' && window.portfolioChart) {
            const data = JSON.parse(evt.detail.data);
            window.portfolioChart.addDataPoint(data);
        }
    });

    // Handle connection status
    document.addEventListener('htmx:sseOpen', () => {
        window.realTimeManager?.setConnected(true);
    });

    document.addEventListener('htmx:sseClose', () => {
        window.realTimeManager?.setConnected(false);
    });

    // Handle AJAX errors
    document.addEventListener('htmx:responseError', (evt) => {
        console.error('HTMX Error:', evt.detail);
        showErrorNotification('An error occurred. Please try again.');
    });
}

function showErrorNotification(message) {
    // Create error toast notification
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg z-50';
    toast.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 text-red-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
            </svg>
            <p class="text-sm text-red-800">${message}</p>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}