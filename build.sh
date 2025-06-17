#!/usr/bin/env bash
# Render build script with demo data

set -o errexit

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Install dependencies with uv sync (uses pyproject.toml)
uv sync --no-dev

# Activate the virtual environment
source .venv/bin/activate

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate

# Generate demo data if database is empty
echo "Checking for existing data..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
print(f"Current user count: {User.objects.count()}")
EOF

# Load demo data from fixtures
echo "Loading demo data from fixtures..."
python manage.py loaddata fixtures/wallets.json || echo "Failed to load wallets data"
python manage.py loaddata fixtures/core.json || echo "Failed to load core data"
python manage.py loaddata fixtures/portfolio.json || echo "Failed to load portfolio data"
python manage.py loaddata fixtures/transactions.json || echo "Failed to load transactions data"

# Create a superuser with known credentials
echo "Creating superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser(
        username='admin@example.com',
        email='admin@example.com',
        password='admin123'
    )
    print("Superuser created: admin@example.com / admin123")
else:
    print("Superuser already exists")
EOF

echo "Demo data setup complete!"

