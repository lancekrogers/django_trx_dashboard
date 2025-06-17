/**
 * Main Application JavaScript
 * Initializes all components and handles global HTMX event coordination
 * Dependencies: PortfolioChart, RealTimeManager, TransactionTable classes
 * Note: All JS files must be loaded before this script
 */

// Initialize modules when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize portfolio chart (if PortfolioChart class is available)
    const chartElement = document.getElementById('portfolio-chart');
    if (chartElement && window.PortfolioChart) {
        window.portfolioChart = new window.PortfolioChart(chartElement);
    }

    // Initialize real-time connection manager (if RealTimeManager class is available)
    if (window.RealTimeManager) {
        window.realTimeManager = new window.RealTimeManager();
    }

    // Initialize transaction table enhancements (if TransactionTable class is available)
    const transactionContainer = document.getElementById('transaction-container');
    if (transactionContainer && window.TransactionTable) {
        new window.TransactionTable(transactionContainer);
    }

    // Setup HTMX event handlers
    setupHTMXHandlers();
});

/**
 * Setup global HTMX event handlers
 * Handles error reporting and cross-component event coordination
 */
function setupHTMXHandlers() {
    // Handle AJAX errors
    document.addEventListener('htmx:responseError', (evt) => {
        console.error('HTMX Error:', evt.detail);
        showErrorNotification('An error occurred. Please try again.');
    });
    
    // Note: SSE event handlers are now in portfolio_sse.html
    // to ensure they're properly scoped to the SSE connection
}

/**
 * Show error notification toast
 * @param {string} message - Error message to display
 */
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