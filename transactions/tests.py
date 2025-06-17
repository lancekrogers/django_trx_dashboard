"""
Transactions app tests - Models, views, and transaction management functionality.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock

from .models import Transaction, Asset, TransactionType
from wallets.models import Wallet, UserSettings
from wallets.models import Chain

User = get_user_model()


class AssetModelTestCase(TestCase):
    """Test Asset model functionality."""

    def test_asset_creation(self):
        """Test creating an asset."""
        asset = Asset.objects.create(
            symbol="ETH",
            name="Ethereum",
            chain=Chain.ETHEREUM,
            contract_address="0x0000000000000000000000000000000000000000",
            decimals=18
        )
        
        self.assertEqual(asset.symbol, "ETH")
        self.assertEqual(asset.name, "Ethereum")
        self.assertEqual(asset.chain, Chain.ETHEREUM)
        self.assertEqual(asset.decimals, 18)
        self.assertIsNotNone(asset.last_updated)

    def test_asset_str_representation(self):
        """Test asset string representation."""
        asset = Asset.objects.create(
            symbol="ETH",
            name="Ethereum",
            chain=Chain.ETHEREUM,
            decimals=18
        )
        
        expected = "ETH (Ethereum)"
        self.assertEqual(str(asset), expected)

    def test_asset_unique_constraint(self):
        """Test that assets are unique per chain."""
        Asset.objects.create(
            symbol="ETH",
            name="Ethereum",
            chain=Chain.ETHEREUM,
            decimals=18
        )
        
        # Creating another ETH asset on same chain should fail
        with self.assertRaises(Exception):  # IntegrityError
            Asset.objects.create(
                symbol="ETH",
                name="Ethereum Duplicate",
                chain=Chain.ETHEREUM,
                decimals=18
            )

    def test_asset_different_chains(self):
        """Test that same symbol can exist on different chains."""
        asset1 = Asset.objects.create(
            symbol="USDT",
            name="Tether USD",
            chain=Chain.ETHEREUM,
            decimals=6
        )
        
        asset2 = Asset.objects.create(
            symbol="USDT",
            name="Tether USD",
            chain=Chain.SOLANA,
            decimals=6
        )
        
        self.assertNotEqual(asset1.id, asset2.id)
        self.assertEqual(asset1.symbol, asset2.symbol)


class TransactionModelTestCase(TestCase):
    """Test Transaction model functionality."""

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

    def test_transaction_creation(self):
        """Test creating a transaction."""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x123456789abcdef",
            block_number=12345678,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal("1.5"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.tx_hash, "0x123456789abcdef")
        self.assertEqual(transaction.block_number, 12345678)
        self.assertEqual(transaction.transaction_type, TransactionType.TRANSFER)
        self.assertEqual(transaction.amount, Decimal("1.5"))
        self.assertEqual(transaction.asset_symbol, self.asset.symbol)

    def test_transaction_str_representation(self):
        """Test transaction string representation."""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x123456789abcdef",
            block_number=12345,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal("1.5"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=timezone.now()
        )
        
        expected = "Transfer 1.5 ETH"
        self.assertEqual(str(transaction), expected)

    def test_transaction_ordering(self):
        """Test transaction ordering by timestamp."""
        time1 = timezone.now()
        time2 = time1 + timezone.timedelta(hours=1)
        
        transaction1 = Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x111",
            block_number=12345,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal("1.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=time1
        )
        
        transaction2 = Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x222",
            block_number=12346,
            transaction_type=TransactionType.BUY,
            amount=Decimal("2.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=Decimal("0.001"),
            timestamp=time2
        )
        
        transactions = list(Transaction.objects.all())
        self.assertEqual(transactions[0], transaction2)  # Most recent first
        self.assertEqual(transactions[1], transaction1)

    def test_transaction_gas_fee_calculation(self):
        """Test gas fee calculation."""
        gas_fee = Decimal("0.00042")  # 0.00042 ETH
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            tx_hash="0x123456789abcdef",
            block_number=12345,
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal("1.0"),
            asset_symbol=self.asset.symbol,
            gas_fee=gas_fee,
            timestamp=timezone.now()
        )
        
        # Verify gas fee is stored correctly
        self.assertEqual(transaction.gas_fee, gas_fee)


class TransactionViewsTestCase(TestCase):
    """Test transaction-related views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )
        self.client.login(email="test@example.com", password="testpass123")
        
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

    def test_transactions_page_view(self):
        """Test transactions page view."""
        response = self.client.get("/htmx/transactions/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Transaction History")
        self.assertTemplateUsed(response, "partials/transactions_page.html")

    def test_transactions_page_with_mock_data_disabled(self):
        """Test transactions page with mock data disabled."""
        # Create user settings with mock data disabled
        UserSettings.objects.create(user=self.user, mock_data_enabled=False)
        
        response = self.client.get("/htmx/transactions/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Transaction History")

    def test_transactions_page_with_mock_data_enabled(self):
        """Test transactions page with mock data enabled."""
        # Create user settings with mock data enabled
        UserSettings.objects.create(user=self.user, mock_data_enabled=True)
        
        # Create test transaction
        Transaction.objects.create(
            wallet=self.wallet,
            hash="0x123456789abcdef",
            transaction_type="send",
            amount=Decimal("1.0"),
            asset=self.asset,
            timestamp=timezone.now()
        )
        
        response = self.client.get("/htmx/transactions/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Transaction History")

    def test_transactions_filtering_by_wallet(self):
        """Test filtering transactions by wallet."""
        # Create second wallet
        wallet2 = Wallet.objects.create(
            user=self.user,
            label="Second Wallet",
            chain=Chain.BITCOIN,
            address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        )
        
        # Enable mock data
        UserSettings.objects.create(user=self.user, mock_data_enabled=True)
        
        # Create transactions for both wallets
        Transaction.objects.create(
            wallet=self.wallet,
            hash="0x111",
            transaction_type="send",
            amount=Decimal("1.0"),
            asset=self.asset,
            timestamp=timezone.now()
        )
        
        btc_asset = Asset.objects.create(
            symbol="BTC",
            name="Bitcoin",
            chain=Chain.BITCOIN,
            decimals=8
        )
        
        Transaction.objects.create(
            wallet=wallet2,
            hash="0x222",
            transaction_type="receive",
            amount=Decimal("0.5"),
            asset=btc_asset,
            timestamp=timezone.now()
        )
        
        # Filter by first wallet
        response = self.client.get(f"/htmx/transactions/?wallet={self.wallet.id}")
        self.assertEqual(response.status_code, 200)

    def test_transactions_filtering_by_type(self):
        """Test filtering transactions by type."""
        UserSettings.objects.create(user=self.user, mock_data_enabled=True)
        
        Transaction.objects.create(
            wallet=self.wallet,
            hash="0x111",
            transaction_type="send",
            amount=Decimal("1.0"),
            asset=self.asset,
            timestamp=timezone.now()
        )
        
        Transaction.objects.create(
            wallet=self.wallet,
            hash="0x222",
            transaction_type="receive",
            amount=Decimal("2.0"),
            asset=self.asset,
            timestamp=timezone.now()
        )
        
        # Filter by send transactions
        response = self.client.get("/htmx/transactions/?type=send")
        self.assertEqual(response.status_code, 200)

    def test_transactions_search(self):
        """Test searching transactions."""
        UserSettings.objects.create(user=self.user, mock_data_enabled=True)
        
        Transaction.objects.create(
            wallet=self.wallet,
            hash="0x123456789abcdef",
            transaction_type="send",
            amount=Decimal("1.0"),
            asset=self.asset,
            from_address=self.wallet.address,
            to_address="0x987654321fedcba",
            timestamp=timezone.now()
        )
        
        # Search by hash
        response = self.client.get("/htmx/transactions/?search=0x123456")
        self.assertEqual(response.status_code, 200)
        
        # Search by address
        response = self.client.get("/htmx/transactions/?search=0x987654")
        self.assertEqual(response.status_code, 200)

    def test_transactions_pagination(self):
        """Test transaction pagination."""
        UserSettings.objects.create(user=self.user, mock_data_enabled=True)
        
        # Create multiple transactions
        for i in range(25):  # More than page size (20)
            Transaction.objects.create(
                wallet=self.wallet,
                hash=f"0x{i:064x}",
                transaction_type="send",
                amount=Decimal("1.0"),
                asset=self.asset,
                timestamp=timezone.now()
            )
        
        # First page
        response = self.client.get("/htmx/transactions/")
        self.assertEqual(response.status_code, 200)
        
        # Second page
        response = self.client.get("/htmx/transactions/?page=2")
        self.assertEqual(response.status_code, 200)

    def test_transactions_htmx_pagination(self):
        """Test HTMX-specific pagination behavior."""
        UserSettings.objects.create(user=self.user, mock_data_enabled=True)
        
        # Create multiple transactions
        for i in range(25):
            Transaction.objects.create(
                wallet=self.wallet,
                hash=f"0x{i:064x}",
                transaction_type="send",
                amount=Decimal("1.0"),
                asset=self.asset,
                timestamp=timezone.now()
            )
        
        # HTMX pagination request
        response = self.client.get("/htmx/transactions/?page=2", 
                                 HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)

    def test_transactions_requires_authentication(self):
        """Test that transactions view requires authentication."""
        self.client.logout()
        response = self.client.get("/htmx/transactions/")
        self.assertEqual(response.status_code, 302)  # Redirect to login


class TransactionDataTestCase(TestCase):
    """Test transaction data integrity and validation."""

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

    def test_transaction_amount_precision(self):
        """Test that transaction amounts maintain precision."""
        # Test very small amount
        small_amount = Decimal("0.000000000000000001")  # 1 wei
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            hash="0x123",
            transaction_type="send",
            amount=small_amount,
            asset=self.asset,
            timestamp=timezone.now()
        )
        
        self.assertEqual(transaction.amount, small_amount)
        
        # Test large amount
        large_amount = Decimal("1000000.123456789012345678")
        transaction2 = Transaction.objects.create(
            wallet=self.wallet,
            hash="0x456",
            transaction_type="receive",
            amount=large_amount,
            asset=self.asset,
            timestamp=timezone.now()
        )
        
        self.assertEqual(transaction2.amount, large_amount)

    def test_transaction_status_choices(self):
        """Test transaction status validation."""
        valid_statuses = ["pending", "confirmed", "failed"]
        
        for status in valid_statuses:
            transaction = Transaction.objects.create(
                wallet=self.wallet,
                hash=f"0x{status}",
                transaction_type="send",
                amount=Decimal("1.0"),
                asset=self.asset,
                status=status,
                timestamp=timezone.now()
            )
            self.assertEqual(transaction.status, status)

    def test_transaction_type_choices(self):
        """Test transaction type validation."""
        valid_types = ["send", "receive", "swap", "contract"]
        
        for tx_type in valid_types:
            transaction = Transaction.objects.create(
                wallet=self.wallet,
                hash=f"0x{tx_type}",
                transaction_type=tx_type,
                amount=Decimal("1.0"),
                asset=self.asset,
                timestamp=timezone.now()
            )
            self.assertEqual(transaction.transaction_type, tx_type)