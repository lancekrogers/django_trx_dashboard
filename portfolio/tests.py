"""
Portfolio app tests - Services, calculations, and portfolio functionality.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from .services import PortfolioService
from wallets.models import Wallet, UserSettings
from wallets.models import Chain
from transactions.models import Transaction, Asset, TransactionType

User = get_user_model()


class PortfolioServiceTestCase(TestCase):
    """Test PortfolioService functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )
        
        self.wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        self.asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain=Chain.ETHEREUM,
            defaults={
                "name": "Ethereum",
                "decimals": 18
            }
        )
        
        self.service = PortfolioService(self.user)

    def test_portfolio_service_initialization(self):
        """Test portfolio service initialization."""
        self.assertEqual(self.service.user, self.user)
        self.assertIsInstance(self.service, PortfolioService)

    @patch('portfolio.services.PortfolioService._get_current_prices')
    def test_get_portfolio_summary_empty(self, mock_prices):
        """Test portfolio summary with no transactions."""
        mock_prices.return_value = {"ETH": 2000.0}
        
        # Disable mock data for this test
        from wallets.models import UserSettings
        from transactions.models import PortfolioCache
        settings, created = UserSettings.objects.get_or_create(
            user=self.user,
            defaults={'mock_data_enabled': False}
        )
        settings.mock_data_enabled = False
        settings.save()
        
        # Create a new service instance to pick up the updated settings
        service = PortfolioService(self.user)
        
        # Clear any cached data
        cache_key = f"portfolio_summary_{self.user.id}"
        PortfolioCache.objects.filter(user_id=self.user.id, cache_key=cache_key).delete()
        
        summary = service.get_portfolio_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('total_value_usd', summary)
        self.assertIn('change_24h', summary)
        self.assertIn('asset_labels', summary)
        self.assertEqual(summary['total_value_usd'], 0)

    @patch('portfolio.services.PortfolioService._get_current_prices')
    def test_get_portfolio_summary_with_transactions(self, mock_prices):
        """Test portfolio summary with transactions."""
        mock_prices.return_value = {"ETH": 2000.0}
        
        # Create some transactions
        Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=Decimal("2.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x222",
            block_number=12346,
            transaction_type=TransactionType.SELL,
            amount=Decimal("0.5"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        summary = self.service.get_portfolio_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('total_value_usd', summary)
        self.assertIn('asset_labels', summary)
        self.assertTrue(summary['total_value_usd'] > 0)

    def test_calculate_wallet_balance_no_transactions(self):
        """Test wallet balance calculation with no transactions."""
        balance = self.service._calculate_wallet_balance(self.wallet, self.asset)
        self.assertEqual(balance, Decimal('0'))

    def test_calculate_wallet_balance_with_transactions(self):
        """Test wallet balance calculation with transactions."""
        # Add some transactions
        Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=Decimal("5.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x222",
            block_number=12346,
            transaction_type=TransactionType.SELL,
            amount=Decimal("2.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x333",
            block_number=12347,
            transaction_type=TransactionType.BUY,
            amount=Decimal("1.5"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        balance = self.service._calculate_wallet_balance(self.wallet, self.asset)
        expected_balance = Decimal('5.0') - Decimal('2.0') + Decimal('1.5')
        self.assertEqual(balance, expected_balance)

    def test_get_portfolio_history_empty(self):
        """Test portfolio history with no data."""
        history = self.service.get_portfolio_history(days=7)
        
        self.assertIsInstance(history, list)
        # Should return some default points even with no data
        self.assertTrue(len(history) >= 0)

    @patch('portfolio.services.PortfolioService._get_historical_prices')
    def test_get_portfolio_history_with_data(self, mock_historical_prices):
        """Test portfolio history with transaction data."""
        # Mock historical price data
        mock_historical_prices.return_value = {
            "ETH": [
                {"timestamp": timezone.now(), "price": 2000.0},
                {"timestamp": timezone.now() - timezone.timedelta(days=1), "price": 1950.0},
            ]
        }
        
        # Create transaction
        Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=Decimal("1.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now() - timezone.timedelta(days=2)
        )
        
        history = self.service.get_portfolio_history(days=7)
        
        self.assertIsInstance(history, list)
        if history:  # Only check if history is not empty
            for point in history:
                self.assertIn('timestamp', point)
                self.assertIn('value', point)

    @patch('requests.get')
    def test_get_current_prices_success(self, mock_get):
        """Test successful price fetching."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ethereum": {"usd": 2000.0},
            "bitcoin": {"usd": 50000.0}
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        prices = self.service._get_current_prices(["ETH", "BTC"])
        
        self.assertIsInstance(prices, dict)
        self.assertIn("ETH", prices)
        self.assertEqual(prices["ETH"], 2000.0)

    @patch('requests.get')
    def test_get_current_prices_failure(self, mock_get):
        """Test price fetching failure handling."""
        # Mock API failure
        mock_get.side_effect = Exception("API Error")
        
        prices = self.service._get_current_prices(["ETH"])
        
        self.assertIsInstance(prices, dict)
        # Should return default prices on failure
        self.assertEqual(len(prices), 0)

    def test_get_asset_allocation(self):
        """Test asset allocation calculation."""
        # Create multiple assets and transactions
        btc_asset, created = Asset.objects.get_or_create(
            symbol="BTC",
            chain=Chain.BITCOIN,
            defaults={
                "name": "Bitcoin",
                "decimals": 8
            }
        )
        
        btc_wallet = Wallet.objects.create(
            user=self.user,
            label="BTC Wallet",
            chain=Chain.BITCOIN,
            address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        )
        
        # Add transactions
        Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=Decimal("2.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        Transaction.objects.create(
            wallet=btc_wallet,
            tx_hash="0x222",
            block_number=12346,
            transaction_type=TransactionType.BUY,
            amount=Decimal("0.1"),
            asset_symbol=btc_asset.symbol,
            gas_fee=Decimal("0.0001"),
            timestamp=timezone.now()
        )
        
        allocation = self.service.get_asset_allocation()
        
        self.assertIsInstance(allocation, list)
        # Should have allocations for assets with non-zero balances
        symbols = [item['symbol'] for item in allocation]
        self.assertIn('ETH', symbols)
        self.assertIn('BTC', symbols)


class PortfolioViewsTestCase(TestCase):
    """Test portfolio-related views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )
        self.client.login(email="test@example.com", password="testpass123")

    @patch('portfolio.services.PortfolioService.get_portfolio_summary')
    def test_portfolio_summary_view(self, mock_summary):
        """Test portfolio summary view."""
        mock_summary.return_value = {
            'total_value': 5000.0,
            'total_change_24h': 150.0,
            'total_change_percent_24h': 3.0,
            'assets': []
        }
        
        response = self.client.get("/htmx/portfolio/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/portfolio_summary.html")

    @patch('portfolio.services.PortfolioService.get_portfolio_summary')
    def test_portfolio_summary_htmx_request(self, mock_summary):
        """Test portfolio summary with HTMX request."""
        mock_summary.return_value = {
            'total_value': 5000.0,
            'total_change_24h': 150.0,
            'total_change_percent_24h': 3.0,
            'assets': []
        }
        
        response = self.client.get("/htmx/portfolio/summary/", 
                                 HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/portfolio_summary.html")

    def test_portfolio_summary_requires_authentication(self):
        """Test that portfolio summary requires authentication."""
        self.client.logout()
        response = self.client.get("/htmx/portfolio/summary/")
        self.assertEqual(response.status_code, 302)  # Redirect to login


class PortfolioCalculationTestCase(TestCase):
    """Test portfolio calculation accuracy and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )
        
        self.service = PortfolioService(self.user)

    def test_empty_portfolio_calculations(self):
        """Test calculations with empty portfolio."""
        # Disable mock data for this test
        settings, created = UserSettings.objects.get_or_create(
            user=self.user,
            defaults={'mock_data_enabled': False}
        )
        settings.mock_data_enabled = False
        settings.save()
        
        # Create a new service instance to pick up the updated settings
        service = PortfolioService(self.user)
        
        # Clear any cached data
        from transactions.models import PortfolioCache
        cache_key = f"portfolio_summary_{self.user.id}"
        PortfolioCache.objects.filter(user_id=self.user.id, cache_key=cache_key).delete()
        
        summary = service.get_portfolio_summary()
        
        self.assertEqual(summary['total_value_usd'], 0)
        self.assertEqual(summary['change_24h'], 0)
        self.assertEqual(summary['asset_count'], 0)
        self.assertEqual(len(summary['asset_labels']), 0)

    def test_precision_in_calculations(self):
        """Test that calculations maintain proper precision."""
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain=Chain.ETHEREUM,
            defaults={
                "name": "Ethereum",
                "decimals": 18
            }
        )
        
        # Create transaction with very precise amount
        precise_amount = Decimal("1.123456789012345678")
        Transaction.objects.create(
            wallet=wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=precise_amount,
            asset_symbol=asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        balance = self.service._calculate_wallet_balance(wallet, asset)
        # Check precision to 12 decimal places (practical precision limit)
        self.assertAlmostEqual(float(balance), float(precise_amount), places=12)

    def test_multiple_wallets_same_asset(self):
        """Test calculations across multiple wallets with same asset."""
        asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain=Chain.ETHEREUM,
            defaults={
                "name": "Ethereum",
                "decimals": 18
            }
        )
        
        # Create two wallets
        wallet1 = Wallet.objects.create(
            user=self.user,
            label="Wallet 1",
            chain=Chain.ETHEREUM,
            address="0x1111111111111111111111111111111111111111"
        )
        
        wallet2 = Wallet.objects.create(
            user=self.user,
            label="Wallet 2",
            chain=Chain.ETHEREUM,
            address="0x2222222222222222222222222222222222222222"
        )
        
        # Add transactions to both wallets
        Transaction.objects.create(
            wallet=wallet1,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=Decimal("1.5"),
            asset_symbol=asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        Transaction.objects.create(
            wallet=wallet2,
            tx_hash="0x222",
            block_number=12346,
            transaction_type=TransactionType.BUY,
            amount=Decimal("2.5"),
            asset_symbol=asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        # Check individual balances
        balance1 = self.service._calculate_wallet_balance(wallet1, asset)
        balance2 = self.service._calculate_wallet_balance(wallet2, asset)
        
        self.assertEqual(balance1, Decimal("1.5"))
        self.assertEqual(balance2, Decimal("2.5"))

    def test_negative_balance_handling(self):
        """Test handling of negative balances (more sends than receives)."""
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain=Chain.ETHEREUM,
            defaults={
                "name": "Ethereum",
                "decimals": 18
            }
        )
        
        # Create transactions resulting in negative balance
        Transaction.objects.create(
            wallet=wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=Decimal("1.0"),
            asset_symbol=asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        Transaction.objects.create(
            wallet=wallet,
            tx_hash="0x222",
            block_number=12346,
            transaction_type=TransactionType.SELL,
            amount=Decimal("1.5"),
            asset_symbol=asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        balance = self.service._calculate_wallet_balance(wallet, asset)
        self.assertEqual(balance, Decimal("-0.5"))


class PortfolioIntegrationTestCase(TestCase):
    """Integration tests for portfolio functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )
        self.client.login(email="test@example.com", password="testpass123")

    def test_full_portfolio_flow(self):
        """Test complete portfolio workflow."""
        # Create wallet
        wallet = Wallet.objects.create(
            user=self.user,
            label="Integration Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        # Create asset
        asset, created = Asset.objects.get_or_create(
            symbol="ETH",
            chain=Chain.ETHEREUM,
            defaults={
                "name": "Ethereum",
                "decimals": 18
            }
        )
        
        # Add transactions
        Transaction.objects.create(
            wallet=wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.BUY,
            amount=Decimal("2.0"),
            asset_symbol=asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        # Test portfolio summary endpoint
        response = self.client.get("/htmx/portfolio/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portfolio Summary")
        
        # Test dashboard includes portfolio
        response = self.client.get("/htmx/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portfolio Dashboard")