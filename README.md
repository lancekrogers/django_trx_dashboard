# Multi-Chain Portfolio Dashboard

A production-ready cryptocurrency portfolio tracker with real-time updates, supporting Ethereum, Solana, and Bitcoin.

## Features

- 🔐 JWT authentication with email-based login
- 💼 Multi-wallet support across different blockchains
- 📊 Real-time portfolio value tracking with SSE
- 📈 Interactive charts with Chart.js
- 💸 Transaction history with filtering and pagination
- 🎨 Responsive UI with HTMX and Tailwind CSS
- ⚡ Fast development with uv and Vite

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- uv (Python package manager)
- direnv (optional, for automatic environment activation)

### Using Make Commands

The project includes a comprehensive Makefile for easy management:

```bash
# Show all available commands
make help

# First time setup (creates venv, installs deps, runs migrations)
make setup

# Run both frontend and backend servers
make run

# Or run servers individually
make run-backend
make run-frontend
```

### Manual Setup

If you prefer manual setup:

1. **Backend Setup:**
```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements/development.txt
python manage.py migrate
python manage.py createsuperuser  # Optional
```

2. **Frontend Setup:**
```bash
cd frontend
npm install
```

## Common Commands

### Development

```bash
# Run everything (setup + run servers)
make dev

# Check service status
make status

# Generate mock data
make mock-data

# Open Django shell
make shell

# Open API docs in browser
make api-docs
```

### Database

```bash
# Run migrations
make migrate

# Create superuser
make createsuperuser

# Reset database (WARNING: destroys all data)
make reset-db
```

### Testing

```bash
# Run all tests
make test

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Test authentication endpoints
make api-test-auth
```

### Linting

```bash
# Run all linters
make lint

# Backend linting (ruff + mypy)
make lint-backend

# Frontend linting
make lint-frontend
```

### Cleanup

```bash
# Clean all generated files
make clean

# Clean backend only
make clean-backend

# Clean frontend only
make clean-frontend
```

## API Documentation

Once the backend is running, visit http://localhost:8000/api/docs for interactive API documentation.

### Key Endpoints

- **Authentication**: `/api/auth/login/`, `/api/auth/register/`
- **Wallets**: `/api/v1/wallets/`
- **Portfolio**: `/api/v1/portfolio/summary`, `/api/v1/portfolio/stream`
- **Transactions**: `/api/v1/transactions/`

## Architecture

### Backend (Django + Django-Ninja)
- JWT authentication with djangorestframework-simplejwt
- SQLite with performance optimizations (WAL mode)
- Server-Sent Events for real-time updates
- Caching layer for expensive calculations

### Frontend (HTMX + Tailwind)
- Server-driven UI with HTMX
- Real-time updates via SSE
- Chart.js for portfolio visualization
- Responsive design with Tailwind CSS

## Development Tips

1. **Using direnv**: The project supports direnv for automatic environment activation. Run `direnv allow` in the project root.

2. **Mock Data**: Use `make mock-data` to generate sample data for testing.

3. **API Testing**: Use `make api-test-auth` to quickly test authentication endpoints.

4. **Real-time Updates**: The portfolio stream endpoint (`/api/v1/portfolio/stream`) sends updates every 100ms (10Hz).

5. **CORS**: Configured for `http://localhost:5173` (Vite dev server) in development.

## Project Structure

```
multichain_trx_dashboard/
├── Makefile              # Build automation
├── backend/              # Django backend
│   ├── authentication/   # JWT auth
│   ├── wallets/         # Wallet models & API
│   ├── portfolio/       # Portfolio calculations
│   ├── transactions/    # Transaction history
│   └── core/           # Shared utilities
└── frontend/            # HTMX frontend
    ├── src/
    │   ├── css/        # Tailwind styles
    │   ├── js/         # JavaScript modules
    │   └── templates/  # HTMX templates
    └── vite.config.js  # Vite configuration
```

## Troubleshooting

- **Port already in use**: Kill existing processes or change ports in settings
- **Migration errors**: Run `make reset-db` to start fresh
- **CORS errors**: Ensure frontend is running on `http://localhost:5173`
- **SSE not working**: Check browser console for connection errors

## License

MIT