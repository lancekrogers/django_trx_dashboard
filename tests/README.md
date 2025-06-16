# Testing Guide for Multi-Chain Portfolio Dashboard

This project uses `pytest` with Django for testing, managed through `uv`.

## Running Tests with uv

### Basic Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest core/test_views.py

# Run specific test class
uv run pytest core/test_views.py::TestHTMXViews

# Run specific test method
uv run pytest core/test_views.py::TestHTMXViews::test_home_view_unauthenticated
```

### Test Categories

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run only view tests
uv run pytest -m views

# Run only model tests
uv run pytest -m models

# Exclude slow tests
uv run pytest -m "not slow"
```

### Coverage Reports

```bash
# Run tests with coverage
uv run pytest --cov=.

# Generate HTML coverage report
uv run pytest --cov=. --cov-report=html

# View coverage in terminal with missing lines
uv run pytest --cov=. --cov-report=term-missing
```

### Parallel Testing

```bash
# Run tests in parallel (requires pytest-xdist)
uv run pytest -n auto

# Run with 4 workers
uv run pytest -n 4
```

### Django-Specific Testing

```bash
# Use Django's test runner
uv run python manage.py test

# Run Django tests in parallel
uv run python manage.py test --parallel

# Run specific Django test
uv run python manage.py test core.tests.HTMXViewsTestCase
```

## Test Structure

```
tests/
├── README.md           # This file
├── __init__.py        # Makes tests a package
├── factories.py       # Factory Boy factories for test data
├── test_integration.py # Integration tests
└── fixtures/          # Test fixtures (if needed)

core/
├── tests.py          # Django-style tests
└── test_views.py     # Pytest-style tests

wallets/
├── tests.py          # App-specific tests
└── test_models.py    # Model-specific tests (optional)

portfolio/
└── tests.py          # Portfolio tests

transactions/
└── tests.py          # Transaction tests
```

## Writing Tests

### Pytest Style (Recommended)

```python
import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestMyView:
    @pytest.mark.unit
    def test_something(self, client, user):
        response = client.get(reverse('my-view'))
        assert response.status_code == 200
```

### Django Style (Legacy)

```python
from django.test import TestCase

class MyViewTestCase(TestCase):
    def test_something(self):
        response = self.client.get('/my-url/')
        self.assertEqual(response.status_code, 200)
```

## Available Fixtures

From `conftest.py`:

- `client` - Django test client
- `authenticated_client` - Logged-in client
- `htmx_client` - Client with HTMX headers
- `user` - Test user
- `user_with_password` - User with known password
- `wallet` - Test wallet
- `eth_asset` - Ethereum asset
- `mock_portfolio_api` - Mocked portfolio API

## Testing Best Practices

1. **Use pytest markers** to categorize tests
2. **Keep tests fast** - mock external services
3. **Use factories** for test data generation
4. **Test one thing** per test method
5. **Use descriptive names** for test methods
6. **Mock external dependencies** to avoid flaky tests

## Debugging Tests

```bash
# Drop into debugger on failure
uv run pytest --pdb

# Show local variables on failure
uv run pytest -l

# Show print statements
uv run pytest -s

# Maximum verbosity
uv run pytest -vvv

# Show slowest tests
uv run pytest --durations=10
```

## CI/CD Integration

For CI/CD pipelines:

```bash
# Run with XML output for CI
uv run pytest --junitxml=test-results.xml

# Run with coverage and fail if below threshold
uv run pytest --cov=. --cov-fail-under=80

# Run in quiet mode
uv run pytest -q
```