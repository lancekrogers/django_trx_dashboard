/**
 * RealTimeManager - Handles SSE connections and real-time data updates
 * Manages connection status, reconnection logic, and UI updates
 * Features: Auto-reconnect, connection indicators, heartbeat monitoring
 */
class RealTimeManager {
    constructor() {
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        
        this.connectionIndicator = document.getElementById('connection-indicator');
        this.disconnectionIndicator = document.getElementById('disconnection-indicator');
        
        // Setup heartbeat
        this.startHeartbeat();
    }

    setConnected(status) {
        this.connected = status;
        
        if (status) {
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this.showConnected();
        } else {
            this.showDisconnected();
            this.attemptReconnect();
        }
    }

    showConnected() {
        if (this.connectionIndicator) {
            this.connectionIndicator.classList.remove('hidden');
        }
        if (this.disconnectionIndicator) {
            this.disconnectionIndicator.classList.add('hidden');
        }
    }

    showDisconnected() {
        if (this.connectionIndicator) {
            this.connectionIndicator.classList.add('hidden');
        }
        if (this.disconnectionIndicator) {
            this.disconnectionIndicator.classList.remove('hidden');
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            // Trigger HTMX to reconnect SSE
            const sseElement = document.querySelector('[hx-ext="sse"]');
            if (sseElement) {
                htmx.trigger(sseElement, 'htmx:sseReconnect');
            }
            
            // Exponential backoff
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds
        }, this.reconnectDelay);
    }

    startHeartbeat() {
        // Update "last updated" times every 10 seconds
        setInterval(() => {
            this.updateRelativeTimes();
        }, 10000);
    }

    updateRelativeTimes() {
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl && lastUpdatedEl.dataset.timestamp) {
            const timestamp = new Date(lastUpdatedEl.dataset.timestamp);
            const now = new Date();
            const diffSeconds = Math.floor((now - timestamp) / 1000);
            
            let text;
            if (diffSeconds < 60) {
                text = 'Just now';
            } else if (diffSeconds < 3600) {
                const minutes = Math.floor(diffSeconds / 60);
                text = `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
            } else {
                const hours = Math.floor(diffSeconds / 3600);
                text = `${hours} hour${hours > 1 ? 's' : ''} ago`;
            }
            
            lastUpdatedEl.textContent = text;
        }
    }
}

// Make class available globally
window.RealTimeManager = RealTimeManager;