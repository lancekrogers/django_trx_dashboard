/**
 * HTMX Configuration and Global Event Handlers
 * Handles CSRF tokens, authentication, error handling, and notifications
 */

// Get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

// HTMX Request Configuration
document.body.addEventListener('htmx:configRequest', (event) => {
    // Add CSRF token to all requests
    const csrfToken = getCSRFToken();
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken;
    }
    
    // Add JWT token if available
    const token = localStorage.getItem('access_token');
    if (token) {
        event.detail.headers['Authorization'] = `Bearer ${token}`;
    }
});

// Global Error Handling
document.body.addEventListener('htmx:responseError', (event) => {
    if (event.detail.xhr.status === 401) {
        // Redirect to login if unauthorized
        window.location.href = '/login';
    }
});

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `pointer-events-auto max-w-sm w-full bg-white shadow-lg rounded-lg overflow-hidden transition-all duration-500 transform translate-x-full`;
    
    const colors = {
        'success': 'bg-green-50 text-green-800',
        'error': 'bg-red-50 text-red-800',
        'warning': 'bg-yellow-50 text-yellow-800',
        'info': 'bg-blue-50 text-blue-800'
    };
    
    notification.innerHTML = `
        <div class="p-4 ${colors[type] || colors.info}">
            <p class="text-sm font-medium">${message}</p>
        </div>
    `;
    
    const container = document.getElementById('notifications');
    if (container) {
        container.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
            notification.classList.add('translate-x-0');
        }, 100);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    }
}

// Make showNotification globally available
window.showNotification = showNotification;