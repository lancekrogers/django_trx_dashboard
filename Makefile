# Portfolio Dashboard Makefile

.PHONY: help setup install migrate collectstatic createsuperuser mock-data mock-data-full reset-users fresh-start run kill-server server-status test test-django test-help test-pytest test-pytest-coverage test-specific format lint lint-strict clean shell dbshell status

# Default target
help: ## Show this help message
	@echo "Portfolio Dashboard - Make Commands"
	@echo "=================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Setup commands
setup: install migrate collectstatic ## Setup complete Django application

collectstatic: ## Collect static files
	@echo "Collecting static files..."
	@uv run --project . python manage.py collectstatic --noinput
	@echo "Static files collected!"

install: ## Install dependencies with uv
	@echo "Installing dependencies with uv..."
	@if [ ! -d .venv ]; then \
		echo "Creating virtual environment..."; \
		uv venv .venv; \
	fi
	@uv sync --all-extras
	@echo "Dependencies installed!"

migrate: ## Run Django migrations
	@echo "Running Django migrations..."
	@uv run --project . python manage.py makemigrations && uv run --project . python manage.py migrate
	@echo "Migrations complete!"

createsuperuser: ## Create Django superuser
	@uv run --project . python manage.py createsuperuser

mock-data: ## Generate mock portfolio data
	@echo "Generating mock data..."
	@uv run --project . python manage.py generate_mock_data
	@echo "Mock data generated!"

mock-data-full: ## Generate full mock data with superuser and multiple users
	@echo "Generating full mock data set..."
	@uv run --project . python manage.py generate_mock_data --superusers 1 --users 3 --transactions 50
	@echo "Full mock data generated!"

reset-users: ## Delete all users (WARNING: destructive!)
	@echo "WARNING: This will delete ALL users!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "Deleting all users..."
	@uv run --project . python reset_users.py
	@echo "All users deleted!"

fresh-start: reset-users createsuperuser ## Reset users and create new superuser

# Development commands
run: ## Run Django development server
	@echo "Starting Django development server..."
	@echo "Application: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"
	@echo "Admin: http://localhost:8000/admin"
	@echo ""
	@uv run --project . python manage.py runserver

kill-server: ## Kill Django development server
	@echo "Stopping Django development server..."
	@pkill -f "manage.py runserver" || echo "No Django server process found"
	@echo "Server stopped!"

server-status: ## Check if Django server is running
	@if pgrep -f "manage.py runserver" > /dev/null; then \
		echo "✅ Django server is running"; \
		echo "PID(s): $$(pgrep -f 'manage.py runserver')"; \
	else \
		echo "❌ Django server is not running"; \
	fi

# Testing commands - Direct uv usage examples
test: ## Run all tests with pytest (recommended)
	@echo "Running tests with pytest..."
	@echo "Direct uv command: uv run pytest"
	@uv run pytest

test-django: ## Run tests with Django test runner
	@echo "Running Django tests..."
	@echo "Direct uv command: uv run python manage.py test"
	@uv run python manage.py test --verbosity=2

test-help: ## Show testing help and examples
	@echo "Testing with uv - Quick Reference"
	@echo "================================"
	@echo ""
	@echo "Run all tests:"
	@echo "  $$ uv run pytest"
	@echo ""
	@echo "Run specific test file:"
	@echo "  $$ uv run pytest core/test_views.py"
	@echo ""
	@echo "Run with coverage:"
	@echo "  $$ uv run pytest --cov=."
	@echo ""
	@echo "Run by marker:"
	@echo "  $$ uv run pytest -m unit"
	@echo "  $$ uv run pytest -m integration"
	@echo ""
	@echo "Run in parallel:"
	@echo "  $$ uv run pytest -n auto"
	@echo ""
	@echo "For more examples, see tests/README.md"

format: ## Format Python code with Black
	@echo "Formatting Python code with Black..."
	@uv run --project . black .
	@echo "Code formatting complete!"

lint: ## Run code linting for Python and JavaScript
	@echo "Running Python linting..."
	@uv run --project . ruff check .
	@uv run --project . black --check . --diff
	@echo "Running type checking (warnings only)..."
	@uv run --project . mypy . --ignore-missing-imports --warn-return-any --no-error-summary || echo "Note: Some type warnings found (non-blocking)"
	@echo "Running JavaScript linting..."
	@if command -v node >/dev/null 2>&1; then \
		if [ -f package.json ]; then \
			npm run lint 2>/dev/null || echo "Warning: npm lint script not found, checking JS files manually..."; \
		fi; \
		if command -v jshint >/dev/null 2>&1; then \
			jshint static/js/*.js 2>/dev/null || echo "JSHint not available for JS linting"; \
		else \
			echo "Note: Install jshint globally for JS linting: npm install -g jshint"; \
		fi; \
	else \
		echo "Note: Node.js not available for JavaScript linting"; \
	fi
	@echo "Linting complete!"

lint-strict: ## Run strict linting (fails on any errors)
	@echo "Running strict linting..."
	@uv run --project . ruff check .
	@uv run --project . black --check . --diff
	@uv run --project . mypy .
	@echo "Strict linting complete!"

# Database commands
shell: ## Django shell
	@uv run --project . python manage.py shell

dbshell: ## Database shell
	@uv run --project . python manage.py dbshell

# Utility commands
clean: ## Clean up generated files
	@echo "Cleaning up..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + || true
	@rm -rf staticfiles/
	@echo "Cleanup complete!"

status: ## Check service status
	@echo "Checking Django server status..."
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q 200 && echo "✅ Django server is running" || echo "❌ Django server is not running"
	@echo ""
	@echo "Quick Status:"
	@echo "- Django: http://localhost:8000"
	@echo "- Admin: http://localhost:8000/admin"
	@echo "- API: http://localhost:8000/api/docs"
