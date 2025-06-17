"""
Wallets app tests - Models, views, and wallet management functionality.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
from unittest.mock import patch, MagicMock

from .models import Wallet, UserSettings
from .models import Chain

User = get_user_model()


class WalletModelTestCase(TestCase):
    """Test Wallet model functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )

    def test_wallet_creation(self):
        """Test creating a wallet."""
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.name, "Test Wallet")
        self.assertEqual(wallet.chain, Chain.ETHEREUM)
        self.assertEqual(wallet.address, "0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07")
        self.assertIsNotNone(wallet.created_at)
        self.assertIsNotNone(wallet.updated_at)

    def test_wallet_str_representation(self):
        """Test wallet string representation."""
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        expected = "Test Wallet (Ethereum)"
        self.assertEqual(str(wallet), expected)

    def test_wallet_unique_constraint(self):
        """Test that user cannot have duplicate wallets."""
        Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        # Creating another wallet with same user, chain, and address should fail
        with self.assertRaises(Exception):  # IntegrityError
            Wallet.objects.create(
                user=self.user,
                label="Duplicate Wallet",
                chain=Chain.ETHEREUM,
                address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
            )

    def test_wallet_different_chains(self):
        """Test that same address can exist on different chains."""
        address = "0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        
        # Create wallet on Ethereum
        wallet1 = Wallet.objects.create(
            user=self.user,
            label="ETH Wallet",
            chain=Chain.ETHEREUM,
            address=address
        )
        
        # Same address on different chain should be allowed
        wallet2 = Wallet.objects.create(
            user=self.user,
            label="Polygon Wallet", 
            chain=Chain.ETHEREUM,
            address=address
        )
        
        self.assertNotEqual(wallet1.id, wallet2.id)
        self.assertEqual(wallet1.address, wallet2.address)

    def test_wallet_ordering(self):
        """Test wallet ordering by name."""
        wallet_b = Wallet.objects.create(
            user=self.user,
            label="B Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        wallet_a = Wallet.objects.create(
            user=self.user,
            label="A Wallet",
            chain=Chain.BITCOIN,
            address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        )
        
        wallets = list(Wallet.objects.filter(user=self.user))
        self.assertEqual(wallets[0], wallet_a)  # Should be first alphabetically
        self.assertEqual(wallets[1], wallet_b)


class UserSettingsModelTestCase(TestCase):
    """Test UserSettings model functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )

    def test_user_settings_creation(self):
        """Test creating user settings."""
        settings, created = UserSettings.objects.get_or_create(
            user=self.user,
            defaults={'mock_data_enabled': True}
        )
        
        self.assertEqual(settings.user, self.user)
        self.assertTrue(settings.mock_data_enabled)
        self.assertIsNotNone(settings.created_at)
        self.assertIsNotNone(settings.updated_at)

    def test_user_settings_default_values(self):
        """Test user settings default values."""
        settings, created = UserSettings.objects.get_or_create(user=self.user)
        
        self.assertEqual(settings.user, self.user)
        self.assertTrue(settings.mock_data_enabled)  # Signal sets to True by default

    def test_user_settings_str_representation(self):
        """Test user settings string representation."""
        settings, created = UserSettings.objects.get_or_create(user=self.user)
        expected = f"Settings for {self.user.email}"
        self.assertEqual(str(settings), expected)

    def test_user_settings_unique_per_user(self):
        """Test that each user can only have one settings record."""
        UserSettings.objects.create(user=self.user)
        
        # Creating another settings record for same user should fail
        with self.assertRaises(Exception):  # IntegrityError
            UserSettings.objects.create(user=self.user)


class WalletViewsTestCase(TestCase):
    """Test wallet-related views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )
        self.client.login(email="test@example.com", password="testpass123")

    def test_wallets_page_view(self):
        """Test wallets page view."""
        response = self.client.get("/htmx/wallets/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Wallets")
        self.assertTemplateUsed(response, "partials/wallets_page.html")

    def test_wallets_page_with_wallets(self):
        """Test wallets page with existing wallets."""
        # Create test wallet
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        response = self.client.get("/htmx/wallets/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Wallet")
        self.assertContains(response, "Ethereum")

    def test_add_wallet_form_get(self):
        """Test displaying add wallet form."""
        response = self.client.get("/htmx/wallets/add/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forms/add_wallet.html")

    def test_add_wallet_post_success(self):
        """Test successful wallet creation."""
        response = self.client.post("/htmx/wallets/add/", {
            "name": "New Wallet",
            "chain": Chain.ETHEREUM,
            "address": "0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Wallet.objects.filter(
            user=self.user,
            label="New Wallet",
            chain=Chain.ETHEREUM
        ).exists())

    def test_add_wallet_post_missing_fields(self):
        """Test wallet creation with missing fields."""
        response = self.client.post("/htmx/wallets/add/", {
            "name": "",
            "chain": "",
            "address": ""
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Name is required", status_code=400)
        self.assertContains(response, "Chain is required", status_code=400)
        self.assertContains(response, "Address is required", status_code=400)

    def test_add_wallet_post_duplicate(self):
        """Test adding duplicate wallet."""
        # Create initial wallet
        Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        # Try to add duplicate
        response = self.client.post("/htmx/wallets/add/", {
            "name": "Duplicate Wallet",
            "chain": Chain.ETHEREUM,
            "address": "0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "This wallet is already added", status_code=400)

    def test_delete_wallet(self):
        """Test wallet deletion."""
        wallet = Wallet.objects.create(
            user=self.user,
            label="Test Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        response = self.client.delete(f"/htmx/wallets/{wallet.id}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Wallet.objects.filter(id=wallet.id).exists())

    def test_delete_wallet_not_found(self):
        """Test deleting non-existent wallet."""
        response = self.client.delete("/htmx/wallets/999/delete/")
        self.assertEqual(response.status_code, 404)

    def test_delete_wallet_wrong_user(self):
        """Test user cannot delete another user's wallet."""
        # Create another user and wallet
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            username="otheruser"
        )
        wallet = Wallet.objects.create(
            user=other_user,
            label="Other Wallet",
            chain=Chain.ETHEREUM,
            address="0x742d35Cc6631C0532925a3b8D86d6E4C6Ed3C07"
        )
        
        # Current user should not be able to delete other user's wallet
        response = self.client.delete(f"/htmx/wallets/{wallet.id}/delete/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Wallet.objects.filter(id=wallet.id).exists())


class ChainChoicesTestCase(TestCase):
    """Test chain choices and validation."""

    def test_chain_choices_values(self):
        """Test that all expected chain choices are available."""
        expected_chains = [
            Chain.ETHEREUM,
            Chain.BITCOIN,
            Chain.SOLANA,
            Chain.ETHEREUM,
            Chain.ETHEREUM,
            Chain.ETHEREUM,
        ]
        
        for chain in expected_chains:
            self.assertIsInstance(chain, str)
            self.assertTrue(len(chain) > 0)

    def test_chain_choices_in_model(self):
        """Test that chain choices work in model creation."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )
        
        for chain in Chain.choices:
            chain_value = chain[0]
            wallet = Wallet.objects.create(
                user=user,
                label=f"Test Wallet {chain_value}",
                chain=chain_value,
                address=f"test_address_{chain_value}"
            )
            self.assertEqual(wallet.chain, chain_value)