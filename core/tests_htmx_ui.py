"""
Comprehensive Django tests for HTMX UI flow.

This test suite covers:
- Unauthenticated user flow (welcome page, login form)
- Login flow (successful login, failed login, navigation updates)
- Authenticated navigation (dashboard, wallets, transactions, settings, logout)
- HTMX-specific behaviors (proper headers, targets, swaps)
- Integration tests for the full user journey
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from transactions.models import Asset, Transaction
from wallets.models import UserSettings, Wallet

User = get_user_model()


class HTMXTestMixin:
    """Mixin for common HTMX test utilities."""

    def assertHTMXResponse(self, response, status_code=200):
        """Assert response has expected status and HTMX content."""
        self.assertEqual(response.status_code, status_code)
        self.assertIn("text/html", response.get("Content-Type", ""))

    def make_htmx_request(self, method, url, **kwargs):
        """Make a request with HTMX headers."""
        # Extract HTMX-specific kwargs
        hx_target = kwargs.pop("hx_target", "main-content")
        hx_trigger = kwargs.pop("hx_trigger", "")
        
        # Add HTMX headers directly as kwargs
        kwargs["HTTP_HX_REQUEST"] = "true"
        kwargs["HTTP_HX_TARGET"] = hx_target
        if hx_trigger:
            kwargs["HTTP_HX_TRIGGER"] = hx_trigger
        
        method_func = getattr(self.client, method.lower())
        return method_func(url, **kwargs)


class UnauthenticatedFlowTests(HTMXTestMixin, TestCase):
    """Tests for unauthenticated user flow."""

    def setUp(self):
        self.client = Client()

    def test_root_page_loads_app_container(self):
        """Test that root URL loads the main app container."""
        response = self.client.get("/")
        self.assertHTMXResponse(response)
        self.assertContains(response, 'id="app"')
        self.assertContains(response, 'id="modal-container"')
        self.assertContains(response, 'id="toast-container"')

    def test_app_loads_welcome_content_for_unauthenticated(self):
        """Test that app.html loads welcome content for unauthenticated users."""
        response = self.client.get("/")
        # Check that it loads welcome content for unauthenticated users (the template tag will be rendered)
        self.assertContains(response, 'hx-get="/htmx/welcome/"')
        # Check that it has loading state
        self.assertContains(response, 'Loading...')

    def test_welcome_page_content(self):
        """Test welcome page renders correctly."""
        response = self.make_htmx_request("GET", reverse("htmx:welcome"))
        self.assertHTMXResponse(response)
        self.assertContains(response, "Welcome to Portfolio Dashboard")
        self.assertContains(response, "Sign In")

    def test_unauthenticated_navigation(self):
        """Test navigation bar for unauthenticated users."""
        response = self.make_htmx_request("GET", reverse("htmx:nav_unauthenticated"))
        self.assertHTMXResponse(response)
        self.assertContains(response, "Sign In")
        self.assertNotContains(response, "Sign Out")

    def test_login_form_display(self):
        """Test login form displays correctly."""
        response = self.make_htmx_request("GET", reverse("htmx:login"))
        self.assertHTMXResponse(response)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_dashboard_redirect_when_not_authenticated(self):
        """Test that dashboard access redirects when not authenticated."""
        response = self.client.get(reverse("htmx:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class LoginFlowTests(HTMXTestMixin, TestCase):
    """Tests for login flow and authentication."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )

    def test_successful_login(self):
        """Test successful login flow."""
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:login"),
            data={
                "username": "testuser@example.com",
                "password": "testpass123",
            },
        )
        self.assertHTMXResponse(response)
        # Should return dashboard content
        self.assertContains(response, "Portfolio Dashboard")
        # Check auth status header
        self.assertEqual(response["X-Auth-Status"], "authenticated")
        self.assertEqual(response["HX-Trigger"], '{"auth-change": {}}')

    def test_failed_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:login"),
            data={
                "username": "testuser@example.com",
                "password": "wrongpassword",
            },
        )
        self.assertHTMXResponse(response, status_code=401)
        self.assertContains(
            response, "Invalid username or password", status_code=401
        )
        # Should still show the form
        self.assertContains(response, 'name="username"', status_code=401)
        self.assertContains(response, 'value="testuser@example.com"', status_code=401)

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        # Missing password
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:login"),
            data={"username": "testuser@example.com"},
        )
        self.assertHTMXResponse(response, status_code=400)
        self.assertContains(
            response, "Username and password are required", status_code=400
        )

        # Missing username
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:login"),
            data={"password": "testpass123"},
        )
        self.assertHTMXResponse(response, status_code=400)
        self.assertContains(
            response, "Username and password are required", status_code=400
        )

    def test_login_csrf_protection(self):
        """Test that login requires CSRF token."""
        # Disable CSRF protection for this client
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("htmx:login"),
            data={
                "username": "testuser@example.com",
                "password": "testpass123",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 403)  # CSRF failure


class AuthenticatedNavigationTests(HTMXTestMixin, TestCase):
    """Tests for authenticated user navigation."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )
        self.client.login(username="testuser@example.com", password="testpass123")

    def test_authenticated_navigation(self):
        """Test navigation bar for authenticated users."""
        response = self.make_htmx_request("GET", reverse("htmx:nav_authenticated"))
        self.assertHTMXResponse(response)
        self.assertContains(response, self.user.email)
        self.assertContains(response, "Sign Out")
        self.assertContains(response, "Settings")
        self.assertNotContains(response, "Sign In")

    def test_dashboard_access(self):
        """Test dashboard loads for authenticated users."""
        response = self.make_htmx_request("GET", reverse("htmx:dashboard"))
        self.assertHTMXResponse(response)
        self.assertContains(response, "Portfolio Dashboard")
        self.assertContains(response, "Add Wallet")
        self.assertContains(response, "Your Wallets")
        self.assertContains(response, "Recent Transactions")

    def test_wallets_page(self):
        """Test wallets page loads correctly."""
        # Create test wallet
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain="ethereum",
            address="0x1234567890123456789012345678901234567890",
        )

        response = self.make_htmx_request("GET", reverse("htmx:wallets"))
        self.assertHTMXResponse(response)
        self.assertContains(response, "Test Wallet")
        self.assertContains(response, wallet.address[:6])

    def test_transactions_page_no_mock_data(self):
        """Test transactions page without mock data enabled."""
        # Ensure user has no wallets/transactions
        Wallet.objects.filter(user=self.user).delete()
        
        response = self.make_htmx_request("GET", reverse("htmx:transactions"))
        self.assertHTMXResponse(response)
        self.assertContains(response, "Transaction History")
        # Should show no transactions when mock data is disabled
        self.assertContains(response, "No transactions found")

    def test_transactions_page_with_mock_data(self):
        """Test transactions page with mock data enabled."""
        # Enable mock data (use get_or_create to avoid duplicates)
        UserSettings.objects.get_or_create(user=self.user, defaults={'mock_data_enabled': True})

        # Clear any existing transactions for this user
        Transaction.objects.filter(wallet__user=self.user).delete()

        # Create test data
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain="ethereum",
            address="0x1234567890123456789012345678901234567890",
        )
        asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain="ethereum",
            defaults={"name": "Ethereum"}
        )
        from django.utils import timezone
        transaction = Transaction.objects.create(
            wallet=wallet,
            tx_hash="0xabc123",
            block_number=12345,
            timestamp=timezone.make_aware(timezone.datetime(2025, 1, 1)),
            transaction_type="transfer",
            amount=1.5,
            asset_symbol="ETH",
            gas_fee=0.0042,  # 21000 * 20 gwei
            usd_value=4500.0,  # 1.5 ETH * $3000
        )

        response = self.make_htmx_request("GET", reverse("htmx:transactions"))
        self.assertHTMXResponse(response)
        self.assertContains(response, transaction.tx_hash[:8])
        self.assertContains(response, "ETH")

    def test_settings_page_display(self):
        """Test settings page displays correctly."""
        response = self.make_htmx_request("GET", reverse("htmx:settings"))
        self.assertHTMXResponse(response)
        self.assertContains(response, "Settings")
        self.assertContains(response, "Mock Data")
        self.assertContains(response, 'name="mock_data_enabled"')

    def test_settings_update(self):
        """Test updating settings."""
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:settings"),
            data={"mock_data_enabled": "on"},
        )
        self.assertHTMXResponse(response)
        self.assertContains(response, "Settings updated successfully!")

        # Verify setting was saved
        settings = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings.mock_data_enabled)

    def test_logout_flow(self):
        """Test logout flow."""
        response = self.make_htmx_request("POST", reverse("htmx:logout"))
        self.assertHTMXResponse(response)
        # Should return welcome content
        self.assertContains(response, "Welcome to Portfolio Dashboard")
        # Check auth status header
        self.assertEqual(response["X-Auth-Status"], "unauthenticated")

        # Verify user is logged out
        response = self.client.get(reverse("htmx:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class WalletManagementTests(HTMXTestMixin, TestCase):
    """Tests for wallet management functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )
        self.client.login(username="testuser@example.com", password="testpass123")

    def test_add_wallet_form_display(self):
        """Test add wallet form displays correctly."""
        response = self.make_htmx_request("GET", reverse("htmx:add_wallet"))
        self.assertHTMXResponse(response)
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="chain"')
        self.assertContains(response, 'name="address"')

    def test_add_wallet_success(self):
        """Test successfully adding a wallet."""
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:add_wallet"),
            data={
                "name": "My ETH Wallet",
                "chain": "ethereum",
                "address": "0x1234567890123456789012345678901234567890",
            },
        )
        self.assertHTMXResponse(response)
        # The template uses |title filter which converts "ETH" to "Eth"
        self.assertContains(response, "My Eth Wallet")
        self.assertContains(response, "0x1234567890123456789012345678901234567890")

        # Verify wallet was created
        wallet = Wallet.objects.filter(user=self.user, label="My ETH Wallet").first()
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet.label, "My ETH Wallet")
        self.assertEqual(wallet.chain, "ethereum")

    def test_add_wallet_validation_errors(self):
        """Test wallet form validation."""
        # Missing fields
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:add_wallet"),
            data={"name": "My Wallet"},
        )
        self.assertHTMXResponse(response, status_code=400)
        self.assertContains(response, "Chain is required", status_code=400)
        self.assertContains(response, "Address is required", status_code=400)

    def test_add_duplicate_wallet(self):
        """Test adding duplicate wallet."""
        # Create existing wallet
        Wallet.objects.create(
            user=self.user,
            label="Existing",
            chain="ethereum",
            address="0x1234567890123456789012345678901234567890",
        )

        response = self.make_htmx_request(
            "POST",
            reverse("htmx:add_wallet"),
            data={
                "name": "Duplicate",
                "chain": "ethereum",
                "address": "0x1234567890123456789012345678901234567890",
            },
        )
        self.assertHTMXResponse(response, status_code=400)
        self.assertContains(
            response, "This wallet is already added", status_code=400
        )

    def test_delete_wallet(self):
        """Test deleting a wallet."""
        wallet = Wallet.objects.create(
            user=self.user,
            label="To Delete",
            chain="ethereum",
            address="0x1234567890123456789012345678901234567890",
        )

        response = self.make_htmx_request(
            "DELETE", reverse("htmx:delete_wallet", args=[wallet.id])
        )
        self.assertHTMXResponse(response)
        self.assertEqual(response.content, b"")  # Empty response for deletion

        # Verify wallet was deleted
        self.assertFalse(Wallet.objects.filter(id=wallet.id).exists())

    def test_delete_wallet_unauthorized(self):
        """Test deleting another user's wallet."""
        other_user = User.objects.create_user(
            username="other@example.com", 
            email="other@example.com",
            password="pass"
        )
        wallet = Wallet.objects.create(
            user=other_user,
            label="Other's Wallet",
            chain="ethereum",
            address="0x1234567890123456789012345678901234567890",
        )

        response = self.make_htmx_request(
            "DELETE", reverse("htmx:delete_wallet", args=[wallet.id])
        )
        self.assertEqual(response.status_code, 404)  # Not found for this user


class HTMXBehaviorTests(HTMXTestMixin, TestCase):
    """Tests for HTMX-specific behaviors."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )

    def test_htmx_headers_detection(self):
        """Test that views properly detect HTMX requests."""
        self.client.login(username="testuser@example.com", password="testpass123")

        # Regular request should return full page
        response = self.client.get(reverse("htmx:portfolio_summary"))
        self.assertContains(response, "<!DOCTYPE html>")

        # HTMX request should return partial
        response = self.make_htmx_request("GET", reverse("htmx:portfolio_summary"))
        self.assertNotContains(response, "<!DOCTYPE html>")
        self.assertContains(response, "portfolio-summary")

    def test_transaction_pagination_htmx(self):
        """Test HTMX-specific transaction pagination."""
        self.client.login(username="testuser@example.com", password="testpass123")
        UserSettings.objects.get_or_create(user=self.user, defaults={'mock_data_enabled': True})

        # Clear any existing transactions for this user
        Transaction.objects.filter(wallet__user=self.user).delete()

        # Create test data
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain="ethereum",
            address="0x1234567890123456789012345678901234567890",
        )
        asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain="ethereum",
            defaults={"name": "Ethereum"}
        )

        # Create 25 transactions to test pagination
        for i in range(25):
            from django.utils import timezone
            Transaction.objects.create(
                wallet=wallet,
                tx_hash=f"0xabc{i:03d}",
                block_number=12345 + i,
                timestamp=timezone.make_aware(timezone.datetime(2025, 1, i+1)),
                transaction_type="transfer",
                amount=1.0,
                asset_symbol="ETH",
                gas_fee=0.0042,
                usd_value=3000.0,
            )

        # Test pagination request
        response = self.make_htmx_request(
            "GET", reverse("htmx:transactions") + "?page=2",
            hx_target="transaction-rows"
        )
        self.assertHTMXResponse(response)
        # Should return just rows, not full table
        self.assertNotContains(response, '<table')
        self.assertContains(response, "0xabc")

    def test_transaction_filter_htmx(self):
        """Test HTMX transaction filtering."""
        self.client.login(username="testuser@example.com", password="testpass123")

        # Test filter request with proper target
        response = self.make_htmx_request(
            "GET",
            reverse("htmx:transactions") + "?type=send",
            hx_target="transactions-table",
        )
        self.assertHTMXResponse(response)
        # Should return just the table
        self.assertContains(response, '<table')
        self.assertNotContains(response, "Transaction History")  # Full page title


class IntegrationTests(HTMXTestMixin, TestCase):
    """Integration tests for full user journeys."""

    def setUp(self):
        self.client = Client()

    def test_full_user_journey(self):
        """Test complete user journey from landing to dashboard."""
        # 1. Load home page
        response = self.client.get("/")
        self.assertContains(response, 'id="app"')

        # 2. Load welcome content via HTMX
        response = self.make_htmx_request("GET", reverse("htmx:welcome"))
        self.assertContains(response, "Welcome to Portfolio Dashboard")

        # 3. Navigate to login
        response = self.make_htmx_request("GET", reverse("htmx:login"))
        self.assertContains(response, 'name="username"')

        # 4. Create account (using Django admin)
        user = User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="newpass123",
        )

        # 5. Login
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:login"),
            data={
                "username": "newuser@example.com",
                "password": "newpass123",
            },
        )
        self.assertEqual(response["X-Auth-Status"], "authenticated")
        self.assertContains(response, "Portfolio Dashboard")

        # 6. Add a wallet
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:add_wallet"),
            data={
                "name": "My First Wallet",
                "chain": "ethereum",
                "address": "0x1234567890123456789012345678901234567890",
            },
        )
        self.assertContains(response, "My First Wallet")

        # 7. Navigate to wallets page
        response = self.make_htmx_request("GET", reverse("htmx:wallets"))
        self.assertContains(response, "My First Wallet")

        # 8. Enable mock data in settings
        response = self.make_htmx_request(
            "POST",
            reverse("htmx:settings"),
            data={"mock_data_enabled": "on"},
        )
        self.assertContains(response, "Settings updated successfully!")

        # 9. View transactions
        response = self.make_htmx_request("GET", reverse("htmx:transactions"))
        self.assertContains(response, "Transactions")

        # 10. Logout
        response = self.make_htmx_request("POST", reverse("htmx:logout"))
        self.assertEqual(response["X-Auth-Status"], "unauthenticated")
        self.assertContains(response, "Welcome to Portfolio Dashboard")

    def test_navigation_state_after_auth_change(self):
        """Test that navigation updates correctly after login/logout."""
        # Start unauthenticated
        response = self.make_htmx_request("GET", reverse("htmx:nav_unauthenticated"))
        self.assertContains(response, "Sign In")

        # Create and login user
        User.objects.create_user(
            username="nav@example.com",
            email="nav@example.com",
            password="pass123",
        )

        response = self.make_htmx_request(
            "POST",
            reverse("htmx:login"),
            data={
                "username": "nav@example.com",
                "password": "pass123",
            },
        )
        self.assertEqual(response["HX-Trigger"], '{"auth-change": {}}')

        # Navigation should now show authenticated state
        response = self.make_htmx_request("GET", reverse("htmx:nav_authenticated"))
        self.assertContains(response, "nav@example.com")
        self.assertContains(response, "Sign Out")

        # Logout
        response = self.make_htmx_request("POST", reverse("htmx:logout"))
        self.assertEqual(response["X-Auth-Status"], "unauthenticated")

        # Navigation should revert to unauthenticated
        response = self.make_htmx_request("GET", reverse("htmx:nav_unauthenticated"))
        self.assertContains(response, "Sign In")


class ErrorHandlingTests(HTMXTestMixin, TestCase):
    """Tests for error handling and edge cases."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )

    def test_404_for_invalid_wallet_id(self):
        """Test 404 handling for non-existent wallet."""
        self.client.login(username="testuser@example.com", password="testpass123")

        response = self.make_htmx_request(
            "DELETE", reverse("htmx:delete_wallet", args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_method_not_allowed(self):
        """Test method not allowed errors."""
        self.client.login(username="testuser@example.com", password="testpass123")

        # Try GET on delete endpoint
        response = self.make_htmx_request(
            "GET", reverse("htmx:delete_wallet", args=[1])
        )
        self.assertEqual(response.status_code, 405)

        # Try DELETE on login
        response = self.make_htmx_request("DELETE", reverse("htmx:login"))
        self.assertEqual(response.status_code, 405)

    def test_missing_htmx_headers(self):
        """Test behavior when HTMX headers are missing."""
        self.client.login(username="testuser@example.com", password="testpass123")

        # Portfolio summary without HTMX should return full page
        response = self.client.get(reverse("htmx:portfolio_summary"))
        self.assertContains(response, "<!DOCTYPE html>")
        self.assertContains(response, "Portfolio Dashboard")