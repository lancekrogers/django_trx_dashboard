# Portfolio Dashboard Makefile

.PHONY: help setup install migrate collectstatic createsuperuser mock-data run test lint lint-strict format clean shell dbshell status

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
	fi && \
	uv sync || uv pip install -r requirements/development.txt
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

# Development commands
run: ## Run Django development server
	@echo "Starting Django development server..."
	@echo "Application: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"
	@echo "Admin: http://localhost:8000/admin"
	@echo ""
	@uv run --project . python manage.py runserver

# Testing commands
test: ## Run all tests
	@echo "Running Django tests..."
	@uv run --project . python manage.py test
	@echo "Tests complete!"

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
