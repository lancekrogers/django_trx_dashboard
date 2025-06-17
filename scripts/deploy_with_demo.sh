#!/bin/bash
# Deployment script that ensures demo data is available

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

echo "Setting up database and demo data for deployment..."

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Check if database has data
USER_COUNT=$(python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.count())")

if [ "$USER_COUNT" -eq "0" ]; then
    echo "No users found. Generating demo data..."
    
    # Generate comprehensive demo data
    python manage.py generate_mock_data \
        --superusers 1 \
        --users 5 \
        --transactions 100
    
    # Generate additional investigation and portfolio cases
    python manage.py generate_investigation_data
    python manage.py generate_portfolio_cases
    
    echo "Demo data generated successfully!"
else
    echo "Database already contains $USER_COUNT users. Skipping demo data generation."
fi

# Collect static files for production
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Deployment setup complete!"
echo ""
echo "Demo credentials:"
echo "  Superuser: admin@example.com / admin123"
echo "  Test users: user1@example.com, user2@example.com, etc. (password: testpass123)"