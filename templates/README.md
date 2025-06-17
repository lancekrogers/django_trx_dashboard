# Frontend Template Organization

This document explains the template structure and component hierarchy for the Multi-Chain Portfolio Dashboard.

## Overview

The frontend uses Django templates with HTMX for server-driven interactivity. Templates are organized into logical groups for maintainability and clarity.

## Directory Structure

```
templates/
├── README.md                    # This documentation
├── base.html                   # Master layout template
├── app.html                    # SPA container template
├── dashboard.html              # Full dashboard page
├── sse_demo.html              # SSE testing template
├── forms/                     # Form components
│   ├── add_wallet.html        # Wallet creation form
│   └── login.html             # Authentication form
└── partials/                  # Reusable page components
    ├── dashboard_content.html  # Dashboard without base layout
    ├── nav_authenticated.html  # Navigation for logged-in users
    ├── nav_unauthenticated.html # Navigation for guests
    ├── portfolio_sse.html      # SSE connection management
    ├── portfolio_summary.html  # Portfolio overview widget
    ├── settings_page.html      # User settings interface
    ├── transaction_row.html    # Single transaction display
    ├── transaction_rows.html   # Multiple transaction rows
    ├── transaction_table.html  # Complete transaction table
    ├── transactions_page.html  # Full transactions page
    ├── wallet_item.html        # Single wallet display
    ├── wallet_list.html        # Wallet collection display
    ├── wallets_page.html       # Full wallets management page
    └── welcome.html            # Landing page for guests
```

## Template Categories

### 1. Base Templates
- **`base.html`** - Master layout with navigation, scripts, and global structure
- **`app.html`** - SPA wrapper that loads content dynamically based on auth status
- **`dashboard.html`** - Complete dashboard page (can be accessed directly or via SPA)

### 2. Form Components (`forms/`)
Form templates designed for HTMX integration with error handling and validation:
- **`login.html`** - User authentication form with error states
- **`add_wallet.html`** - Wallet creation form with chain selection and validation

### 3. Page Partials (`partials/`)
Reusable components that can be loaded independently via HTMX:

#### Navigation Components
- **`nav_authenticated.html`** - User menu with logout option
- **`nav_unauthenticated.html`** - Sign-in button for guests

#### Page Layouts
- **`welcome.html`** - Landing page with features and demo credentials
- **`dashboard_content.html`** - Dashboard layout for HTMX loading (no base template)
- **`wallets_page.html`** - Wallet management interface
- **`transactions_page.html`** - Transaction history with filtering
- **`settings_page.html`** - User preferences and configuration

#### Portfolio Components
- **`portfolio_summary.html`** - Portfolio value overview with chart
- **`portfolio_sse.html`** - SSE connection for real-time updates

#### Wallet Components
- **`wallet_list.html`** - Collection of wallet items
- **`wallet_item.html`** - Individual wallet display with actions

#### Transaction Components
- **`transaction_table.html`** - Complete transaction table with headers
- **`transaction_rows.html`** - Just the table rows (for pagination)
- **`transaction_row.html`** - Single transaction row

## Template Usage Patterns

### HTMX Integration
All templates are designed to work with HTMX:
- **Form submission** - Forms post to HTMX endpoints and swap responses
- **Navigation** - Page navigation swaps content into `#main-content`
- **Real-time updates** - SSE integration for live data
- **Partial refresh** - Components can refresh independently

### Template Selection Logic
Views choose templates based on request type:
```python
# Full page for direct access
if not request.htmx:
    return render(request, 'dashboard.html', context)
# Partial for SPA loading
return render(request, 'partials/dashboard_content.html', context)
```

### Error Handling
Forms include comprehensive error display:
- Field validation errors
- General form errors
- Loading states with spinners
- Success notifications

## Component Dependencies

### JavaScript Dependencies
Templates that require specific JavaScript components:
- **Portfolio components** → `portfolio-chart.js`
- **SSE components** → `real-time-manager.js`
- **Transaction tables** → `transaction-table.js`
- **All components** → `main.js` (initialization)

### Template Relationships
```
base.html
├── app.html (SPA container)
│   ├── welcome.html (unauthenticated)
│   ├── dashboard_content.html (authenticated)
│   ├── wallets_page.html
│   ├── transactions_page.html
│   └── settings_page.html
├── dashboard.html (direct access)
│   ├── portfolio_summary.html
│   ├── portfolio_sse.html
│   └── wallet_item.html (multiple)
└── forms/
    ├── login.html
    └── add_wallet.html
```

## Styling and Assets

### CSS Framework
- **Tailwind CSS** via CDN for utility-first styling
- **Responsive design** with mobile-first approach
- **Dark/light theme** support via CSS classes

### JavaScript Loading Order
Scripts are loaded in dependency order:
1. External libraries (HTMX, Chart.js, Alpine.js)
2. Component classes (portfolio-chart.js, real-time-manager.js, transaction-table.js)
3. Application initialization (main.js)

## Development Guidelines

### Adding New Templates
1. **Choose appropriate location** (forms/ vs partials/)
2. **Add documentation comment** explaining purpose and usage
3. **Follow naming conventions** (feature_component.html)
4. **Include HTMX attributes** for proper swapping
5. **Add error handling** for forms

### Template Documentation
Every template should start with a documentation comment:
```django
{% comment %}
Template Name - Brief description
Purpose: What this template does
Features: Key functionality list
Usage: How and when it's loaded
Dependencies: Required JS/CSS components (if any)
{% endcomment %}
```

### HTMX Best Practices
- Use semantic `hx-target` selectors
- Include loading indicators with `hx-indicator`
- Handle errors with proper status codes
- Use `hx-swap` strategically (innerHTML, outerHTML, beforeend)
- Include CSRF tokens for forms

## Real-Time Features

### Server-Sent Events (SSE)
- **Connection** managed by `portfolio_sse.html`
- **Updates** processed by JavaScript event handlers
- **Reconnection** handled automatically via `real-time-manager.js`
- **Status indicators** show connection state

### Chart Integration
- **Chart.js** integration via `portfolio-chart.js`
- **Real-time updates** from SSE data
- **Responsive design** adapts to container size
- **Performance optimized** with data point limits

## Testing and Debugging

### Template Testing
- Use Django's template debugging for syntax errors
- Test HTMX interactions with browser dev tools
- Verify responsive design across screen sizes
- Check SSE connections in Network tab

### Common Issues
- **Missing CSRF tokens** in forms
- **Incorrect target selectors** for HTMX swapping  
- **JavaScript dependency order** causing initialization failures
- **SSE connection failures** due to endpoint issues

## Migration Notes

### From Previous Structure
The templates have been cleaned up with:
- ✅ Removed duplicate `login.html` (kept `forms/login.html`)
- ✅ Added comprehensive documentation comments
- ✅ Fixed JavaScript ES6 imports for browser compatibility
- ✅ Organized components with clear hierarchies
- ✅ Improved error handling and loading states

### Future Improvements
Potential enhancements:
- Component-based organization (group related templates)
- Template inheritance for repeated patterns
- CSS component extraction for reusable styles
- Automated testing for HTMX interactions