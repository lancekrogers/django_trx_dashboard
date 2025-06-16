#!/bin/bash
# Script to run HTMX UI tests

echo "Running HTMX UI Tests..."
echo "========================"

# Run specific test module
echo "Running core.tests_htmx_ui..."
uv run --project . python manage.py test core.tests_htmx_ui -v 2

# Alternative: Run all tests in the core app
# uv run --project . python manage.py test core -v 2

# Alternative: Run specific test classes
# uv run --project . python manage.py test core.tests_htmx_ui.UnauthenticatedFlowTests -v 2
# uv run --project . python manage.py test core.tests_htmx_ui.LoginFlowTests -v 2
# uv run --project . python manage.py test core.tests_htmx_ui.AuthenticatedNavigationTests -v 2
# uv run --project . python manage.py test core.tests_htmx_ui.WalletManagementTests -v 2
# uv run --project . python manage.py test core.tests_htmx_ui.HTMXBehaviorTests -v 2
# uv run --project . python manage.py test core.tests_htmx_ui.IntegrationTests -v 2
# uv run --project . python manage.py test core.tests_htmx_ui.ErrorHandlingTests -v 2