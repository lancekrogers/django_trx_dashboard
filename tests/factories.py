"""
Factory classes for generating test data using factory_boy.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from wallets.models import Wallet, UserSettings
from wallets.models import Chain
from transactions.models import Transaction, Asset, TransactionType

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.LazyAttribute(lambda obj: obj.email.split('@')[0])
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False


class UserSettingsFactory(DjangoModelFactory):
    """Factory for creating UserSettings instances."""
    
    class Meta:
        model = UserSettings
    
    user = factory.SubFactory(UserFactory)
    mock_data_enabled = False


class WalletFactory(DjangoModelFactory):
    """Factory for creating Wallet instances."""
    
    class Meta:
        model = Wallet
    
    user = factory.SubFactory(UserFactory)
    label = factory.Sequence(lambda n: f"Wallet {n}")
    chain = factory.Iterator([choice[0] for choice in Chain.choices])
    # Note: address is overridden by the @factory.lazy_attribute method below
    
    @factory.lazy_attribute
    def address(self):
        """Generate chain-appropriate addresses."""
        import random
        import string
        if self.chain == Chain.ETHEREUM:
            return f"0x{''.join(random.choice(string.hexdigits.lower()) for _ in range(40))}"
        elif self.chain == Chain.BITCOIN:
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(34))
        elif self.chain == Chain.SOLANA:
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(44))
        else:
            return f"0x{''.join(random.choice(string.hexdigits.lower()) for _ in range(40))}"


class EthereumWalletFactory(WalletFactory):
    """Factory for creating Ethereum wallet instances."""
    
    chain = Chain.ETHEREUM
    @factory.lazy_attribute
    def address(self):
        import random
        import string
        return f"0x{''.join(random.choice(string.hexdigits.lower()) for _ in range(40))}"


class BitcoinWalletFactory(WalletFactory):
    """Factory for creating Bitcoin wallet instances."""
    
    chain = Chain.BITCOIN
    address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis address


class SolanaWalletFactory(WalletFactory):
    """Factory for creating Solana wallet instances."""
    
    chain = Chain.SOLANA
    @factory.lazy_attribute
    def address(self):
        import random
        import string
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(44))


class AssetFactory(DjangoModelFactory):
    """Factory for creating Asset instances."""
    
    class Meta:
        model = Asset
    
    symbol = factory.Faker('bothify', text='???')
    name = factory.Faker('company')
    chain = factory.Iterator([choice[0] for choice in Chain.choices])
    @factory.lazy_attribute
    def contract_address(self):
        import random
        import string
        return f"0x{''.join(random.choice(string.hexdigits.lower()) for _ in range(40))}"
    decimals = 18


class EthereumAssetFactory(AssetFactory):
    """Factory for creating Ethereum assets."""
    
    chain = Chain.ETHEREUM
    symbol = factory.Iterator(['ETH', 'USDT', 'USDC', 'DAI', 'WETH'])
    decimals = factory.LazyAttribute(lambda obj: 18 if obj.symbol == 'ETH' else 6)


class BitcoinAssetFactory(AssetFactory):
    """Factory for creating Bitcoin assets."""
    
    chain = Chain.BITCOIN
    symbol = 'BTC'
    name = 'Bitcoin'
    decimals = 8
    contract_address = None


class TransactionFactory(DjangoModelFactory):
    """Factory for creating Transaction instances."""
    
    class Meta:
        model = Transaction
    
    wallet = factory.SubFactory(WalletFactory)
    @factory.lazy_attribute
    def tx_hash(self):
        import random
        import string
        return f"0x{''.join(random.choice(string.hexdigits.lower()) for _ in range(64))}"
    block_number = factory.Faker('random_int', min=1000000, max=20000000)
    transaction_type = factory.Iterator([TransactionType.BUY, TransactionType.SELL, TransactionType.TRANSFER])
    amount = factory.LazyAttribute(lambda obj: Decimal('1.234567'))
    asset_symbol = factory.Faker('bothify', text='???')
    gas_fee = factory.LazyAttribute(lambda obj: Decimal('0.001'))
    timestamp = factory.LazyAttribute(lambda obj: timezone.now())


class BuyTransactionFactory(TransactionFactory):
    """Factory for creating buy transactions."""
    
    transaction_type = TransactionType.BUY


class SellTransactionFactory(TransactionFactory):
    """Factory for creating sell transactions."""
    
    transaction_type = TransactionType.SELL


class TransferTransactionFactory(TransactionFactory):
    """Factory for creating transfer transactions."""
    
    transaction_type = TransactionType.TRANSFER


# Utility functions for creating test data scenarios

def create_user_with_wallets(num_wallets=2):
    """Create a user with multiple wallets."""
    user = UserFactory()
    wallets = []
    
    for i in range(num_wallets):
        if i % 3 == 0:
            wallet = EthereumWalletFactory(user=user)
        elif i % 3 == 1:
            wallet = BitcoinWalletFactory(user=user)
        else:
            wallet = SolanaWalletFactory(user=user)
        wallets.append(wallet)
    
    return user, wallets


def create_portfolio_with_transactions(user=None, num_transactions=10):
    """Create a portfolio with transactions for testing."""
    if user is None:
        user, wallets = create_user_with_wallets(3)
    else:
        wallets = [WalletFactory(user=user) for _ in range(3)]
    
    # Create assets using get_or_create to avoid unique constraint issues
    from transactions.models import Asset
    eth_asset, created = Asset.objects.get_or_create(
        symbol='ETH', 
        chain=Chain.ETHEREUM,
        defaults={'name': 'Ethereum', 'decimals': 18}
    )
    btc_asset, created = Asset.objects.get_or_create(
        symbol='BTC',
        chain=Chain.BITCOIN, 
        defaults={'name': 'Bitcoin', 'decimals': 8}
    )
    
    transactions = []
    
    for i in range(num_transactions):
        import random
        wallet = random.choice(wallets)
        asset = eth_asset if wallet.chain == Chain.ETHEREUM else btc_asset
        
        if i % 2 == 0:
            transaction = BuyTransactionFactory(wallet=wallet, asset_symbol=asset.symbol)
        else:
            transaction = SellTransactionFactory(wallet=wallet, asset_symbol=asset.symbol)
        
        transactions.append(transaction)
    
    return user, wallets, transactions


def create_test_superuser():
    """Create a superuser for testing admin functionality."""
    return UserFactory(
        email='admin@example.com',
        username='admin',
        is_staff=True,
        is_superuser=True
    )