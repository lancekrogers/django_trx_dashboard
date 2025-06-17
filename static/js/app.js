/**
 * App-level JavaScript for global functionality
 * Handles authentication changes, toast notifications, and app-wide events
 */

// Handle authentication changes
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.xhr.getResponseHeader('HX-Trigger') === 'auth-change') {
        // Trigger navigation reload
        htmx.trigger('#nav-content', 'auth-change');
    }
});

// Toast notifications system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `p-4 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-indigo-600'
    } transform transition-all duration-300 translate-x-full`;
    toast.innerHTML = message;
    
    const container = document.getElementById('toast-container');
    if (container) {
        container.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
            toast.classList.add('translate-x-0');
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Listen for custom toast events from HTMX responses
document.body.addEventListener('showToast', function(event) {
    showToast(event.detail.message, event.detail.type);
});

// Make showToast available globally for other scripts
window.showToast = showToast;