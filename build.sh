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

# Load demo data
echo "Loading demo data..."
python load_demo_data.py

# Quick database check
echo "Checking database..."
python check_db.py

