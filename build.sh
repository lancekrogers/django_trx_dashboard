#!/usr/bin/env bash
# Render build script

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

# Run migrations (in case of model changes)
python manage.py migrate --run-syncdb

echo "Build complete! Using pre-populated SQLite database."