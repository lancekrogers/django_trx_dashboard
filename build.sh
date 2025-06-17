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
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Generate demo data if database is empty
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.count() == 0:
    print('No users found. Generating demo data...')
    from django.core.management import call_command
    call_command('generate_mock_data', '--superusers', '1', '--users', '5', '--transactions', '100')
    call_command('generate_investigation_data')
    call_command('generate_portfolio_cases')
    print('Demo data generated successfully!')
else:
    print(f'Database already has {User.objects.count()} users.')
"