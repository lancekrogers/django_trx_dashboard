# Portfolio Dashboard Backend

Django REST API for multi-chain cryptocurrency portfolio tracking.

## Features

- JWT Authentication
- Multi-chain wallet support (Ethereum, Bitcoin, Solana)
- Real-time portfolio updates via Server-Sent Events (SSE)
- Transaction history with filtering and pagination
- SQLite with performance optimizations
- Mock data generation for testing

## Quick Start

### Prerequisites

- Python 3.11+
- uv (for fast package management)

### Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Run migrations
python manage.py migrate

# Generate mock data
python manage.py generate_mock_data --users 3 --transactions 20

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/register/` - Register new user

### Wallets
- `GET /api/v1/wallets/` - List user wallets
- `POST /api/v1/wallets/` - Add new wallet
- `GET /api/v1/wallets/{id}/` - Get wallet details
- `PATCH /api/v1/wallets/{id}/` - Update wallet
- `DELETE /api/v1/wallets/{id}/` - Remove wallet

### Portfolio
- `GET /api/v1/portfolio/summary` - Get portfolio summary
- `GET /api/v1/portfolio/history` - Historical portfolio values
- `GET /api/v1/portfolio/wallets` - Individual wallet balances
- `GET /api/v1/portfolio/stream` - SSE portfolio updates

### Transactions
- `GET /api/v1/transactions/` - List transactions (paginated)
- `GET /api/v1/transactions/{id}/` - Transaction details
- `GET /api/v1/transactions/stats` - Transaction statistics

## Testing

Run the API test script:

```bash
# Start the server in one terminal
python manage.py runserver

# In another terminal
python test_api.py
```

## Development

### Project Structure

```
backend/
├── config/          # Django settings and URLs
├── apps/
│   ├── authentication/  # JWT auth
│   ├── wallets/        # Wallet management
│   ├── portfolio/      # Portfolio calculations
│   ├── transactions/   # Transaction history
│   └── core/          # Shared utilities
├── portfolio.db     # SQLite database
└── manage.py
```

### Mock Data

Generate test data:

```bash
python manage.py generate_mock_data --users 5 --transactions 100
```

### API Documentation

Visit http://localhost:8000/api/docs for interactive API documentation.

## Performance Notes

- SSE updates throttled to 10Hz maximum
- Portfolio calculations cached for 1 minute
- SQLite with WAL mode for better concurrency
- Proper indexes on all foreign keys and query fields