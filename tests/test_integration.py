"""
Integration tests for the portfolio dashboard.
Tests the complete user workflow from registration to portfolio management.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

from wallets.models import Wallet, UserSettings
from wallets.models import Chain
from transactions.models import Transaction, Asset
from portfolio.services import PortfolioService
from .factories import (
    UserFactory, 
    WalletFactory, 
    AssetFactory, 
    BuyTransactionFactory,
    SellTransactionFactory,
    create_user_with_wallets,
    create_portfolio_with_transactions
)

User = get_user_model()


class UserWorkflowIntegrationTestCase(TestCase):
    """Test complete user workflow through the application."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = UserFactory(email="integration@example.com")
        self.user.set_password("testpass123")
        self.user.save()

    def test_complete_user_workflow(self):
        """Test complete user journey from login to portfolio management."""
        # Step 1: User accesses home page
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Multi-Chain Portfolio")

        # Step 2: User logs in
        response = self.client.post("/htmx/login/", {
            "username": "integration@example.com",
            "password": "testpass123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Auth-Status"], "authenticated")

        # Step 3: User accesses dashboard
        response = self.client.get("/htmx/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portfolio Dashboard")

        # Step 4: User adds a wallet
        response = self.client.post("/htmx/wallets/add/", {
            "name": "My ETH Wallet",
            "chain": Chain.ETHEREUM,
            "address": "0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        })
        self.assertEqual(response.status_code, 200)

        # Verify wallet was created
        wallet = Wallet.objects.filter(user=self.user, label="My ETH Wallet").first()
        self.assertEqual(wallet.label, "My ETH Wallet")
        self.assertEqual(wallet.chain, Chain.ETHEREUM)

        # Step 5: User views wallets page
        response = self.client.get("/htmx/wallets/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My ETH Wallet")

        # Step 6: User views transactions page
        response = self.client.get("/htmx/transactions/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Transaction History")

        # Step 7: User logs out
        response = self.client.post("/htmx/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Auth-Status"], "unauthenticated")


class PortfolioCalculationIntegrationTestCase(TestCase):
    """Test portfolio calculations with real data scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.user, self.wallets, self.transactions = create_portfolio_with_transactions(
            num_transactions=20
        )
        self.service = PortfolioService(self.user)

    def test_portfolio_with_multiple_assets(self):
        """Test portfolio calculations with multiple assets and wallets."""
        # Create ETH asset and transactions
        from transactions.models import Asset
        eth_asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain=Chain.ETHEREUM,
            defaults={
                "name": "Ethereum",
                "decimals": 18
            }
        )
        
        eth_wallet = WalletFactory(
            user=self.user,
            chain=Chain.ETHEREUM
        )

        # Add some ETH transactions
        BuyTransactionFactory(
            wallet=eth_wallet,
            asset_symbol=eth_asset.symbol,
            amount=Decimal("5.0")
        )
        
        SellTransactionFactory(
            wallet=eth_wallet,
            asset_symbol=eth_asset.symbol,
            amount=Decimal("1.5")
        )

        # Create BTC asset and transactions
        btc_asset, created = Asset.objects.get_or_create(
            symbol="BTC",
            chain=Chain.BITCOIN,
            defaults={
                "name": "Bitcoin",
                "decimals": 8
            }
        )
        
        btc_wallet = WalletFactory(
            user=self.user,
            chain=Chain.BITCOIN
        )

        BuyTransactionFactory(
            wallet=btc_wallet,
            asset_symbol=btc_asset.symbol,
            amount=Decimal("0.25")
        )

        # Test balance calculations
        eth_balance = self.service._calculate_wallet_balance(eth_wallet, eth_asset)
        btc_balance = self.service._calculate_wallet_balance(btc_wallet, btc_asset)

        self.assertEqual(eth_balance, Decimal("3.5"))  # 5.0 - 1.5
        self.assertEqual(btc_balance, Decimal("0.25"))

        # Test portfolio summary
        summary = self.service.get_portfolio_summary()
        self.assertIsInstance(summary, dict)
        self.assertIn('total_value_usd', summary)
        self.assertIn('asset_labels', summary)

    def test_portfolio_with_user_settings(self):
        """Test portfolio behavior with different user settings."""
        # Test with mock data disabled
        # First clear any existing UserSettings that might have been created
        UserSettings.objects.filter(user=self.user).delete()
        settings, created = UserSettings.objects.get_or_create(
            user=self.user,
            defaults={'mock_data_enabled': False}
        )

        # Clear any cached data and create a new service to pick up the updated settings
        from transactions.models import PortfolioCache
        PortfolioCache.objects.filter(user=self.user).delete()
        
        service = PortfolioService(self.user)
        summary = service.get_portfolio_summary()
        self.assertEqual(summary['total_value_usd'], 0)  # Should be 0 with no mock data

        # Enable mock data
        settings.mock_data_enabled = True
        settings.save()

        # Portfolio should now show calculated values
        summary = self.service.get_portfolio_summary()
        self.assertIsInstance(summary['total_value_usd'], (int, float))


class HTMXIntegrationTestCase(TestCase):
    """Test HTMX functionality across the application."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = UserFactory(email="htmx@example.com")
        self.user.set_password("testpass123")
        self.user.save()
        self.client.login(email="htmx@example.com", password="testpass123")

    def test_htmx_navigation_flow(self):
        """Test navigation between pages using HTMX."""
        # Test dashboard (HTMX request returns partial)
        response = self.client.get("/htmx/dashboard/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/dashboard_content.html")

        # Test wallets page
        response = self.client.get("/htmx/wallets/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/wallets_page.html")

        # Test transactions page
        response = self.client.get("/htmx/transactions/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/transactions_page.html")

    def test_htmx_form_submission(self):
        """Test HTMX form submissions."""
        # Test wallet creation form
        response = self.client.get("/htmx/wallets/add/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forms/add_wallet.html")

        # Test form submission
        response = self.client.post("/htmx/wallets/add/", {
            "name": "HTMX Test Wallet",
            "chain": Chain.ETHEREUM,
            "address": "0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        }, HTTP_HX_REQUEST="true")
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Wallet.objects.filter(
            user=self.user,
            label="HTMX Test Wallet"
        ).exists())

    def test_htmx_error_handling(self):
        """Test HTMX error handling."""
        # Test invalid form submission
        response = self.client.post("/htmx/wallets/add/", {
            "name": "",
            "chain": "",
            "address": ""
        }, HTTP_HX_REQUEST="true")
        
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Chain is required", status_code=400)
        self.assertContains(response, "Address is required", status_code=400)


class APIIntegrationTestCase(TestCase):
    """Test API endpoints integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = UserFactory(email="api@example.com")
        self.user.set_password("testpass123")
        self.user.save()
        self.client.login(email="api@example.com", password="testpass123")

    def test_portfolio_summary_api(self):
        """Test portfolio summary API endpoint."""
        response = self.client.get("/htmx/portfolio/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portfolio Summary")

    def test_transactions_api_filtering(self):
        """Test transactions API with filtering."""
        # Create test data
        wallet = WalletFactory(user=self.user)
        asset = AssetFactory()
        UserSettings.objects.get_or_create(user=self.user, defaults={'mock_data_enabled': True})
        
        SellTransactionFactory(
            wallet=wallet,
            asset_symbol=asset.symbol
        )
        
        BuyTransactionFactory(
            wallet=wallet,
            asset_symbol=asset.symbol
        )

        # Test filtering by type
        response = self.client.get("/htmx/transactions/?type=sell")
        self.assertEqual(response.status_code, 200)

        # Test filtering by wallet
        response = self.client.get(f"/htmx/transactions/?wallet={wallet.id}")
        self.assertEqual(response.status_code, 200)


class SecurityIntegrationTestCase(TestCase):
    """Test security aspects of the application."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user1 = UserFactory(email="user1@example.com")
        self.user1.set_password("testpass123")
        self.user1.save()
        
        self.user2 = UserFactory(email="user2@example.com")
        self.user2.set_password("testpass123")
        self.user2.save()

    def test_user_data_isolation(self):
        """Test that users can only access their own data."""
        # Create wallets for both users
        wallet1 = WalletFactory(user=self.user1)
        wallet2 = WalletFactory(user=self.user2)

        # Login as user1
        self.client.login(email="user1@example.com", password="testpass123")

        # User1 should see their own wallet
        response = self.client.get("/htmx/wallets/")
        self.assertContains(response, wallet1.label)
        self.assertNotContains(response, wallet2.label)

        # User1 should not be able to delete user2's wallet
        response = self.client.delete(f"/htmx/wallets/{wallet2.id}/delete/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Wallet.objects.filter(id=wallet2.id).exists())

    def test_authentication_required(self):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/htmx/dashboard/",
            "/htmx/wallets/",
            "/htmx/transactions/",
            "/htmx/portfolio/summary/",
            "/htmx/wallets/add/",
        ]

        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, 
                302, 
                f"Endpoint {endpoint} should require authentication"
            )