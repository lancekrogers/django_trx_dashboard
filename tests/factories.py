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
from transactions.models import Transaction, Asset

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
    label = factory.Faker('word')
    chain = factory.Iterator([choice[0] for choice in Chain.choices])
    address = factory.LazyAttribute(lambda obj: f"0x{factory.Faker('hex_string', length=40)}")
    
    @factory.lazy_attribute
    def address(self):
        """Generate chain-appropriate addresses."""
        if self.chain == Chain.ETHEREUM:
            return f"0x{factory.Faker('hex_string', length=40).evaluate(None, None, None)}"
        elif self.chain == Chain.BITCOIN:
            return factory.Faker('bothify', text='?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#').evaluate(None, None, None)
        elif self.chain == Chain.SOLANA:
            return factory.Faker('bothify', text='?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#').evaluate(None, None, None)
        else:
            return f"0x{factory.Faker('hex_string', length=40).evaluate(None, None, None)}"


class EthereumWalletFactory(WalletFactory):
    """Factory for creating Ethereum wallet instances."""
    
    chain = Chain.ETHEREUM
    address = factory.LazyAttribute(lambda obj: f"0x{factory.Faker('hex_string', length=40).evaluate(None, None, None)}")


class BitcoinWalletFactory(WalletFactory):
    """Factory for creating Bitcoin wallet instances."""
    
    chain = Chain.BITCOIN
    address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis address


class SolanaWalletFactory(WalletFactory):
    """Factory for creating Solana wallet instances."""
    
    chain = Chain.SOLANA
    address = factory.LazyAttribute(lambda obj: f"{factory.Faker('bothify', text='?#?#?#?#?#?#?#?#?#?#?#?#').evaluate(None, None, None)}")


class AssetFactory(DjangoModelFactory):
    """Factory for creating Asset instances."""
    
    class Meta:
        model = Asset
    
    symbol = factory.Faker('bothify', text='???')
    name = factory.Faker('company')
    chain = factory.Iterator([choice[0] for choice in Chain.choices])
    contract_address = factory.LazyAttribute(lambda obj: f"0x{factory.Faker('hex_string', length=40).evaluate(None, None, None)}")
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
    hash = factory.LazyAttribute(lambda obj: f"0x{factory.Faker('hex_string', length=64).evaluate(None, None, None)}")
    block_number = factory.Faker('random_int', min=1000000, max=20000000)
    transaction_type = factory.Iterator(['send', 'receive', 'swap', 'contract'])
    amount = factory.LazyAttribute(lambda obj: Decimal(factory.Faker('pydecimal', left_digits=4, right_digits=6, positive=True).evaluate(None, None, None)))
    asset = factory.SubFactory(AssetFactory)
    from_address = factory.LazyAttribute(lambda obj: f"0x{factory.Faker('hex_string', length=40).evaluate(None, None, None)}")
    to_address = factory.LazyAttribute(lambda obj: f"0x{factory.Faker('hex_string', length=40).evaluate(None, None, None)}")
    gas_used = factory.Faker('random_int', min=21000, max=500000)
    gas_price = factory.LazyAttribute(lambda obj: Decimal(factory.Faker('random_int', min=10, max=100).evaluate(None, None, None)))
    status = factory.Iterator(['pending', 'confirmed', 'failed'])
    timestamp = factory.LazyAttribute(lambda obj: timezone.now() - timezone.timedelta(
        days=factory.Faker('random_int', min=0, max=365).evaluate(None, None, None)
    ))


class SendTransactionFactory(TransactionFactory):
    """Factory for creating send transactions."""
    
    transaction_type = 'send'
    from_address = factory.SelfAttribute('wallet.address')


class ReceiveTransactionFactory(TransactionFactory):
    """Factory for creating receive transactions."""
    
    transaction_type = 'receive'
    to_address = factory.SelfAttribute('wallet.address')


class SwapTransactionFactory(TransactionFactory):
    """Factory for creating swap transactions."""
    
    transaction_type = 'swap'


class ContractTransactionFactory(TransactionFactory):
    """Factory for creating contract transactions."""
    
    transaction_type = 'contract'
    gas_used = factory.Faker('random_int', min=50000, max=2000000)


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
    
    # Create assets
    eth_asset = EthereumAssetFactory(symbol='ETH', name='Ethereum')
    btc_asset = BitcoinAssetFactory()
    
    transactions = []
    
    for i in range(num_transactions):
        wallet = factory.Faker('random_element', elements=wallets).evaluate(None, None, None)
        asset = eth_asset if wallet.chain == Chain.ETHEREUM else btc_asset
        
        if i % 2 == 0:
            transaction = ReceiveTransactionFactory(wallet=wallet, asset=asset)
        else:
            transaction = SendTransactionFactory(wallet=wallet, asset=asset)
        
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