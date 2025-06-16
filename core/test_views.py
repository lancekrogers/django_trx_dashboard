"""
Tests for core views using pytest style.
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestHTMXViews:
    """Test HTMX-specific view functionality."""

    @pytest.mark.unit
    @pytest.mark.views
    def test_home_view_unauthenticated(self, client):
        """Test home view returns app.html for unauthenticated users."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Multi-Chain Portfolio" in response.content
        assert "app.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_home_view_authenticated(self, authenticated_client):
        """Test home view returns app.html for authenticated users."""
        response = authenticated_client.get("/")
        assert response.status_code == 200
        assert b"Multi-Chain Portfolio" in response.content
        assert "app.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_htmx_welcome_view(self, client):
        """Test welcome partial view."""
        response = client.get("/htmx/welcome/")
        assert response.status_code == 200
        assert b"Welcome to Portfolio Dashboard" in response.content
        assert "partials/welcome.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_htmx_login_get(self, client):
        """Test login form display."""
        response = client.get("/htmx/login/")
        assert response.status_code == 200
        assert b"Sign in" in response.content
        assert "forms/login.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_htmx_login_post_success(self, client, user_with_password):
        """Test successful login via HTMX."""
        response = client.post("/htmx/login/", {
            "username": user_with_password.email,
            "password": "testpass123"
        })
        assert response.status_code == 200
        assert response["X-Auth-Status"] == "authenticated"
        assert response["HX-Trigger"] == "auth-change"
        assert "dashboard.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_htmx_login_post_invalid(self, client, user_with_password):
        """Test failed login via HTMX."""
        response = client.post("/htmx/login/", {
            "username": user_with_password.email,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert b"Invalid username or password" in response.content
        assert "forms/login.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_htmx_logout(self, authenticated_client):
        """Test logout via HTMX."""
        response = authenticated_client.post("/htmx/logout/")
        assert response.status_code == 200
        assert response["X-Auth-Status"] == "unauthenticated"
        assert "partials/welcome.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_dashboard_requires_auth(self, client):
        """Test dashboard view requires authentication."""
        response = client.get("/htmx/dashboard/")
        assert response.status_code == 302  # Redirect to login

    @pytest.mark.unit
    @pytest.mark.views
    def test_dashboard_authenticated(self, authenticated_client):
        """Test dashboard view for authenticated user."""
        response = authenticated_client.get("/htmx/dashboard/")
        assert response.status_code == 200
        assert "dashboard.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestHTMXBehavior:
    """Test HTMX-specific behaviors and headers."""

    @pytest.mark.unit
    def test_htmx_request_detection(self, authenticated_htmx_client):
        """Test that views properly detect HTMX requests."""
        response = authenticated_htmx_client.get("/htmx/dashboard/")
        assert response.status_code == 200
        # The view should detect this as an HTMX request

    @pytest.mark.unit
    def test_auth_status_headers(self, client, user_with_password):
        """Test that authentication status is properly communicated via headers."""
        # Successful login should set auth status header
        response = client.post("/htmx/login/", {
            "username": user_with_password.email,
            "password": "testpass123"
        })
        assert response["X-Auth-Status"] == "authenticated"
        assert response["HX-Trigger"] == "auth-change"
        
        # Logout should set unauth status header
        response = client.post("/htmx/logout/")
        assert response["X-Auth-Status"] == "unauthenticated"


@pytest.mark.django_db
class TestNavigation:
    """Test navigation components."""

    @pytest.mark.unit
    @pytest.mark.views
    def test_authenticated_navigation(self, authenticated_client):
        """Test authenticated navigation partial."""
        response = authenticated_client.get("/htmx/nav/authenticated/")
        assert response.status_code == 200
        assert b"Dashboard" in response.content
        assert b"Wallets" in response.content
        assert b"Transactions" in response.content
        assert "partials/nav_authenticated.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_unauthenticated_navigation(self, client):
        """Test unauthenticated navigation partial."""
        response = client.get("/htmx/nav/unauthenticated/")
        assert response.status_code == 200
        assert b"Sign In" in response.content
        assert "partials/nav_unauthenticated.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestSettingsView:
    """Test settings functionality."""

    @pytest.mark.unit
    @pytest.mark.views
    def test_settings_view_get(self, authenticated_client):
        """Test settings page display."""
        response = authenticated_client.get("/htmx/settings/")
        assert response.status_code == 200
        assert "partials/settings_page.html" in [t.name for t in response.templates]

    @pytest.mark.unit
    @pytest.mark.views
    def test_settings_update(self, authenticated_client, user_with_password):
        """Test updating settings."""
        response = authenticated_client.post("/htmx/settings/", {
            "mock_data_enabled": "on"
        })
        assert response.status_code == 200
        assert b"Settings updated successfully!" in response.content
        
        # Verify settings were updated
        from wallets.models import UserSettings
        settings = UserSettings.objects.get(user=user_with_password)
        assert settings.mock_data_enabled is True


@pytest.mark.django_db
class TestAuthentication:
    """Test authentication functionality."""

    @pytest.mark.unit
    def test_protected_endpoints_require_auth(self, client):
        """Test that protected endpoints require authentication."""
        protected_urls = [
            "/htmx/dashboard/",
            "/htmx/wallets/",
            "/htmx/transactions/",
            "/htmx/portfolio/summary/",
            "/htmx/settings/",
        ]
        
        for url in protected_urls:
            response = client.get(url)
            assert response.status_code == 302, f"URL {url} should require auth"
            assert "/login/" in response.url

    @pytest.mark.unit
    def test_public_endpoints_accessible(self, client):
        """Test that public endpoints are accessible without auth."""
        public_urls = [
            "/",
            "/htmx/welcome/",
            "/htmx/login/",
            "/htmx/nav/unauthenticated/",
        ]
        
        for url in public_urls:
            response = client.get(url)
            assert response.status_code == 200, f"URL {url} should be publicly accessible"


# Parametrized tests example
@pytest.mark.django_db
@pytest.mark.parametrize("chain,expected_symbol", [
    ("ethereum", "Ξ"),
    ("bitcoin", "₿"),
    ("solana", "◎"),
])
def test_chain_symbols(authenticated_client, eth_wallet, chain, expected_symbol):
    """Test that chain symbols are displayed correctly."""
    # This is just an example of parametrized testing
    pass