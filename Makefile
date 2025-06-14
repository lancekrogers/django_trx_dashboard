# Portfolio Dashboard Makefile
# Handles both frontend and backend operations

.PHONY: help setup setup-backend setup-frontend install install-backend install-frontend \
        migrate createsuperuser mock-data run run-backend run-frontend run-all \
        test test-backend test-frontend lint clean clean-backend clean-frontend \
        shell dbshell logs-backend logs-frontend status

# Default target
help: ## Show this help message
	@echo "Portfolio Dashboard - Make Commands"
	@echo "=================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Setup commands
setup: setup-backend setup-frontend ## Setup both backend and frontend

setup-backend: ## Setup backend (uv sync, migrations)
	@echo "Setting up backend with uv..."
	cd backend && \
	uv sync && \
	source .venv/bin/activate && \
	python manage.py makemigrations && \
	python manage.py migrate
	@echo "Backend setup complete!"

setup-frontend: ## Setup frontend (npm install)
	@echo "Setting up frontend..."
	cd frontend && npm install
	@echo "Frontend setup complete!"

# Install dependencies
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies
	cd backend && \
	uv sync

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# Database commands
migrate: ## Run Django migrations
	cd backend && \
	source .venv/bin/activate && \
	python manage.py makemigrations && \
	python manage.py migrate

createsuperuser: ## Create Django superuser
	cd backend && \
	source .venv/bin/activate && \
	python manage.py createsuperuser

mock-data: ## Generate mock data
	cd backend && \
	source .venv/bin/activate && \
	python manage.py generate_mock_data --users 3 --transactions 20

# Run commands
run: run-all ## Run both frontend and backend (alias for run-all)

run-backend: ## Run Django development server
	cd backend && \
	source .venv/bin/activate && \
	python manage.py runserver

run-frontend: ## Run Vite development server
	cd frontend && npm run dev

run-all: ## Run both servers in parallel (requires GNU parallel or tmux)
	@if command -v tmux >/dev/null 2>&1; then \
		echo "Starting servers in tmux..."; \
		tmux new-session -d -s portfolio || true; \
		tmux send-keys -t portfolio:0 'cd backend && source .venv/bin/activate && python manage.py runserver' Enter; \
		tmux split-window -t portfolio:0 -h; \
		tmux send-keys -t portfolio:0.1 'cd frontend && npm run dev' Enter; \
		tmux attach-session -t portfolio; \
	else \
		echo "tmux not found. Starting servers in background..."; \
		$(MAKE) run-backend & \
		$(MAKE) run-frontend & \
		wait; \
	fi

# Test commands
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	@echo "Note: Django server must be running for API tests"
	@echo "Run 'make run-backend' in another terminal first"
	cd backend && \
	source .venv/bin/activate && \
	python test_api.py

test-frontend: ## Run frontend tests
	cd frontend && npm test

# Lint commands
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Run backend linters (ruff, mypy)
	cd backend && \
	source .venv/bin/activate && \
	ruff check . && \
	mypy .

lint-frontend: ## Run frontend linters
	cd frontend && npm run lint

# Utility commands
shell: ## Open Django shell
	cd backend && \
	source .venv/bin/activate && \
	python manage.py shell

dbshell: ## Open database shell
	cd backend && \
	source .venv/bin/activate && \
	python manage.py dbshell

logs-backend: ## Tail backend logs
	tail -f backend/*.log 2>/dev/null || echo "No log files found"

logs-frontend: ## Tail frontend logs
	cd frontend && npm run dev

status: ## Check status of services
	@echo "Checking service status..."
	@echo ""
	@echo "Backend:"
	@curl -s http://localhost:8000/api/docs >/dev/null 2>&1 && echo "   Django server is running" || echo "  L Django server is not running"
	@echo ""
	@echo "Frontend:"
	@curl -s http://localhost:5173 >/dev/null 2>&1 && echo "   Vite server is running" || echo "  L Vite server is not running"
	@echo ""
	@echo "Database:"
	@if [ -f backend/portfolio.db ]; then echo "   SQLite database exists"; else echo "  L SQLite database not found"; fi

# Clean commands
clean: clean-backend clean-frontend ## Clean all generated files

clean-backend: ## Clean backend generated files
	cd backend && \
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
	find . -type f -name "*.pyc" -delete && \
	rm -rf .pytest_cache .mypy_cache .ruff_cache

clean-frontend: ## Clean frontend generated files
	cd frontend && \
	rm -rf node_modules dist .vite

# Quick commands for common workflows
dev: setup run-all ## Setup and run everything (first time setup)

reset-db: ## Reset database (WARNING: destroys all data)
	cd backend && \
	rm -f portfolio.db portfolio.db-wal portfolio.db-shm && \
	source .venv/bin/activate && \
	python manage.py migrate && \
	echo "Database reset complete!"

# API testing shortcuts
api-test-auth: ## Test authentication endpoints
	@echo "Testing registration..."
	@curl -X POST http://localhost:8000/api/auth/register/ \
		-H "Content-Type: application/json" \
		-d '{"email":"test@example.com","password":"testpass123"}' -s | jq . || echo "Registration response received"
	@echo "\nTesting login..."
	@curl -X POST http://localhost:8000/api/auth/login/ \
		-H "Content-Type: application/json" \
		-d '{"email":"test@example.com","password":"testpass123"}' -s | jq . || echo "Login response received"

api-docs: ## Open API documentation in browser
	@echo "Opening API docs..."
	@python -m webbrowser http://localhost:8000/api/docs || open http://localhost:8000/api/docs || xdg-open http://localhost:8000/api/docs