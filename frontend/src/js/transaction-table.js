export class TransactionTable {
    constructor(container) {
        this.container = container;
        this.setupFilters();
        this.setupInfiniteScroll();
    }

    setupFilters() {
        // Add filter controls
        const filterHtml = `
            <div class="bg-gray-50 px-6 py-3 border-b border-gray-200">
                <div class="flex items-center space-x-4">
                    <select 
                        id="tx-type-filter"
                        hx-get="/api/v1/transactions/"
                        hx-trigger="change"
                        hx-target="#transaction-container"
                        hx-include="[name='period']"
                        class="text-sm rounded-md border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                    >
                        <option value="">All Types</option>
                        <option value="buy">Buy</option>
                        <option value="sell">Sell</option>
                        <option value="transfer">Transfer</option>
                    </select>
                    
                    <select
                        name="period"
                        hx-get="/api/v1/transactions/"
                        hx-trigger="change"
                        hx-target="#transaction-container"
                        hx-include="[id='tx-type-filter']"
                        class="text-sm rounded-md border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                    >
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="all">All Time</option>
                    </select>
                    
                    <button
                        hx-get="/api/v1/transactions/export"
                        class="ml-auto text-sm text-blue-600 hover:text-blue-700"
                    >
                        Export CSV
                    </button>
                </div>
            </div>
        `;

        // Insert filters if not already present
        if (!this.container.querySelector('#tx-type-filter')) {
            this.container.insertAdjacentHTML('afterbegin', filterHtml);
        }
    }

    setupInfiniteScroll() {
        // Add infinite scroll trigger
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const nextButton = this.container.querySelector('[hx-get*="page="][hx-get*="next"]');
                    if (nextButton) {
                        htmx.trigger(nextButton, 'click');
                    }
                }
            });
        }, {
            rootMargin: '100px'
        });

        // Observe last row
        const lastRow = this.container.querySelector('tbody tr:last-child');
        if (lastRow) {
            observer.observe(lastRow);
        }
    }
}