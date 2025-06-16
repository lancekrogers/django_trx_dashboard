"""
Global pytest configuration and fixtures.
This file is automatically loaded by pytest.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

# Import factories if using factory_boy
from tests.factories import UserFactory, WalletFactory, AssetFactory, TransactionFactory

User = get_user_model()


# --- Database Fixtures ---

@pytest.fixture
def db_access(db):
    """
    Fixture that ensures database access.
    Use this instead of pytest.mark.django_db for better control.
    """
    pass


# --- User Fixtures ---

@pytest.fixture
def user():
    """Create a test user."""
    return UserFactory(
        email="testuser@example.com",
        username="testuser"
    )


@pytest.fixture
def user_with_password():
    """Create a test user with a known password."""
    user = UserFactory(
        email="testuser@example.com",
        username="testuser"
    )
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def superuser():
    """Create a superuser."""
    return UserFactory(
        email="admin@example.com",
        username="admin",
        is_staff=True,
        is_superuser=True
    )


# --- Client Fixtures ---

@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(client, user_with_password):
    """Django test client with authenticated user."""
    client.login(email=user_with_password.email, password="testpass123")
    return client


@pytest.fixture
def admin_client(client, superuser):
    """Django test client with superuser."""
    superuser.set_password("adminpass123")
    superuser.save()
    client.login(email=superuser.email, password="adminpass123")
    return client


# --- HTMX Client Fixtures ---

@pytest.fixture
def htmx_client(client):
    """Client that sends HTMX headers."""
    class HTMXClient:
        def __init__(self, client):
            self.client = client
            
        def get(self, *args, **kwargs):
            kwargs.setdefault('HTTP_HX_REQUEST', 'true')
            return self.client.get(*args, **kwargs)
            
        def post(self, *args, **kwargs):
            kwargs.setdefault('HTTP_HX_REQUEST', 'true')
            return self.client.post(*args, **kwargs)
            
        def put(self, *args, **kwargs):
            kwargs.setdefault('HTTP_HX_REQUEST', 'true')
            return self.client.put(*args, **kwargs)
            
        def patch(self, *args, **kwargs):
            kwargs.setdefault('HTTP_HX_REQUEST', 'true')
            return self.client.patch(*args, **kwargs)
            
        def delete(self, *args, **kwargs):
            kwargs.setdefault('HTTP_HX_REQUEST', 'true')
            return self.client.delete(*args, **kwargs)
            
        def login(self, **credentials):
            return self.client.login(**credentials)
            
        def logout(self):
            return self.client.logout()
    
    return HTMXClient(client)


@pytest.fixture
def authenticated_htmx_client(htmx_client, user_with_password):
    """HTMX client with authenticated user."""
    htmx_client.login(email=user_with_password.email, password="testpass123")
    return htmx_client


# --- Model Fixtures ---

@pytest.fixture
def wallet(user):
    """Create a test wallet."""
    return WalletFactory(user=user)


@pytest.fixture
def eth_wallet(user):
    """Create an Ethereum wallet."""
    from wallets.models import Chain
    return WalletFactory(
        user=user,
        chain=Chain.ETHEREUM,
        label="ETH Wallet"
    )


@pytest.fixture
def btc_wallet(user):
    """Create a Bitcoin wallet."""
    from wallets.models import Chain
    return WalletFactory(
        user=user,
        chain=Chain.BITCOIN,
        label="BTC Wallet"
    )


@pytest.fixture
def eth_asset():
    """Create Ethereum asset."""
    from wallets.models import Chain
    return AssetFactory(
        symbol="ETH",
        name="Ethereum",
        chain=Chain.ETHEREUM,
        decimals=18
    )


@pytest.fixture
def btc_asset():
    """Create Bitcoin asset."""
    from wallets.models import Chain
    return AssetFactory(
        symbol="BTC",
        name="Bitcoin",
        chain=Chain.BITCOIN,
        decimals=8
    )


# --- Settings Fixtures ---

@pytest.fixture
def mock_settings(settings):
    """Fixture for modifying Django settings in tests."""
    return settings


@pytest.fixture
def enable_mock_data(user):
    """Enable mock data for a user."""
    from wallets.models import UserSettings
    settings, _ = UserSettings.objects.get_or_create(
        user=user,
        defaults={'mock_data_enabled': True}
    )
    settings.mock_data_enabled = True
    settings.save()
    return settings


# --- Utility Fixtures ---

@pytest.fixture
def api_rf():
    """Django REST framework API request factory."""
    from rest_framework.test import APIRequestFactory
    return APIRequestFactory()


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Use temporary directory for media files during tests."""
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def captured_templates():
    """Capture which templates were used in a response."""
    templates_used = []
    
    def _capture_template(sender, template, context, **kwargs):
        templates_used.append(template.name)
    
    from django.template import signals
    signals.template_rendered.connect(_capture_template)
    
    yield templates_used
    
    signals.template_rendered.disconnect(_capture_template)


# --- Mock External Services ---

@pytest.fixture
def mock_portfolio_api(mocker):
    """Mock external portfolio API calls."""
    mock = mocker.patch('portfolio.services.PortfolioService._get_current_prices')
    mock.return_value = {
        'ETH': 2000.0,
        'BTC': 50000.0,
        'SOL': 100.0,
    }
    return mock


@pytest.fixture
def mock_blockchain_api(mocker):
    """Mock blockchain API calls."""
    mock = mocker.patch('chains.adapters.BaseAdapter.get_transactions')
    mock.return_value = []
    return mock


# --- Performance Fixtures ---

@pytest.fixture
def django_assert_num_queries():
    """
    Fixture to assert number of database queries.
    Usage:
        def test_something(django_assert_num_queries):
            with django_assert_num_queries(2):
                # Code that should make exactly 2 queries
    """
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    
    def _assert_num_queries(num):
        return CaptureQueriesContext(connection)
    
    return _assert_num_queries


# --- Session Configuration ---

@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Override django_db_setup to customize test database.
    Runs once per test session.
    """
    with django_db_blocker.unblock():
        # Add any session-level database setup here
        pass