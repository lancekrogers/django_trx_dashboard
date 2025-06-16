# Testing with uv

This project uses Django's built-in test runner, managed through `uv` for fast, reliable testing.

## Quick Start

```bash
# Run all tests
uv run python manage.py test

# Run tests for a specific app
uv run python manage.py test core

# Run a specific test
uv run python manage.py test core.tests.HTMXViewsTestCase.test_home_view_unauthenticated
```

## Using the Test Script

We provide a convenient test script that wraps Django's test runner:

```bash
# Show help
uv run python scripts/test.py --help

# Run all tests
uv run python scripts/test.py

# Run unit tests only
uv run python scripts/test.py --unit

# Run integration tests only
uv run python scripts/test.py --integration

# Run with coverage
uv run python scripts/test.py --coverage

# Run tests in parallel
uv run python scripts/test.py --parallel
```

## Direct uv Commands

### Basic Testing

```bash
# Run all tests with verbose output
uv run python manage.py test -v 2

# Run tests for specific apps
uv run python manage.py test core wallets transactions

# Run tests matching a pattern
uv run python manage.py test -k test_login
```

### Test Filtering

```bash
# Run tests by tag
uv run python manage.py test --tag unit
uv run python manage.py test --tag integration

# Exclude tests by tag
uv run python manage.py test --exclude-tag slow

# Run multiple tags
uv run python manage.py test --tag unit --tag views
```

### Performance Options

```bash
# Run tests in parallel (auto-detect cores)
uv run python manage.py test --parallel auto

# Run with 4 parallel processes
uv run python manage.py test --parallel 4

# Keep test database between runs
uv run python manage.py test --keepdb

# Stop on first failure
uv run python manage.py test --failfast
```

### Debugging Tests

```bash
# Drop into debugger on failure
uv run python manage.py test --pdb

# Show SQL queries
uv run python manage.py test --debug-sql

# Run with debug mode
uv run python manage.py test --debug-mode
```

## Coverage Reports

```bash
# Install coverage if not already installed
uv pip install coverage

# Run tests with coverage
uv run coverage run manage.py test

# Generate coverage report
uv run coverage report

# Generate HTML coverage report
uv run coverage html
# Open htmlcov/index.html in browser
```

## Test Organization

### Test Tags

Mark your tests with tags for easy filtering:

```python
from django.test import TestCase, tag

class MyTestCase(TestCase):
    @tag('unit', 'views')
    def test_something(self):
        pass
    
    @tag('integration')
    def test_integration(self):
        pass
    
    @tag('slow')
    def test_slow_operation(self):
        pass
```

### Test Structure

```
core/
├── tests.py              # Main test file
├── test_views.py         # View-specific tests (optional)
└── test_models.py        # Model-specific tests (optional)

tests/
├── factories.py          # Test data factories
├── test_integration.py   # Integration tests
└── fixtures/            # Test fixtures
```

## Writing Tests

### Django TestCase Style

```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class MyViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_view_requires_auth(self):
        response = self.client.get('/my-url/')
        self.assertEqual(response.status_code, 302)
    
    def test_view_with_auth(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/my-url/')
        self.assertEqual(response.status_code, 200)
```

### HTMX Testing

```python
class HTMXTestCase(TestCase):
    def test_htmx_request(self):
        response = self.client.get(
            '/htmx/endpoint/',
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='main-content'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Auth-Status', response)
```

## Continuous Integration

### GitHub Actions Example

```yaml
- name: Install dependencies
  run: |
    pip install uv
    uv venv
    uv sync --all-extras

- name: Run tests
  run: |
    uv run python manage.py test --parallel

- name: Generate coverage
  run: |
    uv run coverage run manage.py test
    uv run coverage xml
```

## Best Practices

1. **Keep tests fast** - Use in-memory SQLite for tests
2. **Use factories** - Generate test data with Factory Boy
3. **Tag your tests** - Make it easy to run subsets
4. **Mock external services** - Don't make real API calls
5. **Test one thing** - Each test should verify one behavior
6. **Use descriptive names** - Test names should explain what they test

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure your Python path is correct
   ```bash
   uv run python manage.py test --pythonpath .
   ```

2. **Database errors**: Reset the test database
   ```bash
   uv run python manage.py test --keepdb=False
   ```

3. **Slow tests**: Run in parallel
   ```bash
   uv run python manage.py test --parallel auto
   ```

4. **Finding tests**: Check test discovery
   ```bash
   uv run python manage.py test --debug-mode -v 3
   ```

## Advanced Usage

### Custom Test Runner

Create a custom test runner for specialized behavior:

```python
# myapp/test_runner.py
from django.test.runner import DiscoverRunner

class CustomTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        # Custom setup
    
    def teardown_test_environment(self, **kwargs):
        # Custom teardown
        super().teardown_test_environment(**kwargs)
```

Use it:
```bash
uv run python manage.py test --testrunner=myapp.test_runner.CustomTestRunner
```

### Test Settings

Use different settings for tests:

```bash
# Use test-specific settings
uv run python manage.py test --settings=config.test_settings

# Or set environment variable
DJANGO_SETTINGS_MODULE=config.test_settings uv run python manage.py test
```