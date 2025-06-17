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
 * Show error notification toast using the global toast system
 * @param {string} message - Error message to display
 */
function showErrorNotification(message) {
    // Use the global toast system from app.js
    if (window.showToast) {
        window.showToast(message, 'error');
    } else {
        // Fallback if app.js hasn't loaded yet
        console.error('Error:', message);
    }
}