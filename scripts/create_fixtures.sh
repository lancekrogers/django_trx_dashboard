#!/bin/bash
# Export current demo data as Django fixtures for deployment

# Get the project root directory (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate the virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Error: Virtual environment not found. Please run 'uv venv .venv' first."
    exit 1
fi

echo "Creating fixtures directory..."
mkdir -p fixtures

echo "Exporting users and authentication data..."
python manage.py dumpdata auth.User --indent 2 > fixtures/users.json

echo "Exporting core data..."
python manage.py dumpdata core --indent 2 > fixtures/core.json

echo "Exporting wallets data..."
python manage.py dumpdata wallets --indent 2 > fixtures/wallets.json

echo "Exporting portfolio data..."
python manage.py dumpdata portfolio --indent 2 > fixtures/portfolio.json

echo "Exporting transactions data..."
python manage.py dumpdata transactions --indent 2 > fixtures/transactions.json

# Create a combined fixture file for easy loading
echo "Creating combined fixture..."
python manage.py dumpdata auth.User core wallets portfolio transactions --indent 2 > fixtures/all_data.json

echo "Fixtures created successfully in fixtures/ directory"
echo "To load on deployment: python manage.py loaddata fixtures/all_data.json"