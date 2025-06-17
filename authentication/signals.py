import random
from datetime import timedelta
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from faker import Faker

from transactions.models import Asset, Transaction, TransactionType
from wallets.models import User, UserSettings, Wallet

fake = Faker()


@receiver(post_save, sender=User)
def create_user_mock_data(sender, instance, created, **kwargs):
    """Automatically create mock data for new users"""
    if created:
        # Create user settings with mock data enabled
        UserSettings.objects.create(user=instance, mock_data_enabled=True)
        
        # Create assets
        assets = create_assets()
        
        # Create wallets
        wallets = create_wallets(instance)
        
        # Create transactions
        for wallet in wallets:
            create_transactions(wallet, assets[wallet.chain], 50)


def create_assets():
    """Create mock assets for each chain"""
    assets = {"ethereum": [], "bitcoin": [], "solana": []}
    
    # Ethereum assets
    eth_assets_data = [
        {"symbol": "ETH", "name": "Ethereum", "decimals": 18, "price": 2000},
        {"symbol": "USDC", "name": "USD Coin", "decimals": 6, "price": 1},
        {"symbol": "USDT", "name": "Tether", "decimals": 6, "price": 1},
        {"symbol": "WBTC", "name": "Wrapped Bitcoin", "decimals": 8, "price": 45000},
        {"symbol": "LINK", "name": "Chainlink", "decimals": 18, "price": 15},
    ]
    
    for data in eth_assets_data:
        asset, _ = Asset.objects.get_or_create(
            symbol=data["symbol"],
            chain="ethereum",
            defaults={
                "name": data["name"],
                "decimals": data["decimals"],
                "current_price_usd": Decimal(str(data["price"])),
            },
        )
        assets["ethereum"].append(asset)
    
    # Bitcoin
    btc_asset, _ = Asset.objects.get_or_create(
        symbol="BTC",
        chain="bitcoin",
        defaults={
            "name": "Bitcoin",
            "decimals": 8,
            "current_price_usd": Decimal("45000"),
        },
    )
    assets["bitcoin"].append(btc_asset)
    
    # Solana assets
    sol_assets_data = [
        {"symbol": "SOL", "name": "Solana", "decimals": 9, "price": 100},
        {"symbol": "USDC", "name": "USD Coin", "decimals": 6, "price": 1},
        {"symbol": "RAY", "name": "Raydium", "decimals": 6, "price": 2.5},
    ]
    
    for data in sol_assets_data:
        asset, _ = Asset.objects.get_or_create(
            symbol=data["symbol"],
            chain="solana",
            defaults={
                "name": data["name"],
                "decimals": data["decimals"],
                "current_price_usd": Decimal(str(data["price"])),
            },
        )
        assets["solana"].append(asset)
    
    return assets


def create_wallets(user):
    """Create wallets for a user"""
    wallets = []
    
    # Ethereum wallet
    eth_wallet, _ = Wallet.objects.get_or_create(
        user=user,
        chain="ethereum",
        defaults={
            "address": "0x" + fake.hexify(text="^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"),
            "label": "My ETH Wallet",
        },
    )
    wallets.append(eth_wallet)
    
    # Bitcoin wallet
    btc_wallet, _ = Wallet.objects.get_or_create(
        user=user,
        chain="bitcoin",
        defaults={
            "address": fake.bothify(text="bc1q?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#"),
            "label": "My BTC Wallet",
        },
    )
    wallets.append(btc_wallet)
    
    # Solana wallet
    sol_wallet, _ = Wallet.objects.get_or_create(
        user=user,
        chain="solana",
        defaults={
            "address": fake.bothify(text="?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#"),
            "label": "My SOL Wallet",
        },
    )
    wallets.append(sol_wallet)
    
    return wallets


def create_transactions(wallet, assets, count):
    """Create mock transactions for a wallet"""
    # Start from 30 days ago
    start_date = timezone.now() - timedelta(days=30)
    
    for i in range(count):
        # Random timestamp within the last 30 days
        timestamp = start_date + timedelta(
            hours=random.randint(0, 30 * 24), 
            minutes=random.randint(0, 59)
        )
        
        # Random transaction type
        tx_type = random.choice([t[0] for t in TransactionType.choices])
        
        # Random asset from the chain
        asset = random.choice(assets)
        
        # Generate amount based on asset
        if asset.symbol in ["BTC", "ETH", "SOL"]:
            amount = Decimal(str(random.uniform(0.01, 2)))
        else:
            amount = Decimal(str(random.uniform(10, 1000)))
        
        # Calculate USD value
        usd_value = amount * asset.current_price_usd
        
        # Gas fee
        if wallet.chain == "ethereum":
            gas_fee = Decimal(str(random.uniform(0.001, 0.01)))  # ETH
        elif wallet.chain == "bitcoin":
            gas_fee = Decimal(str(random.uniform(0.00001, 0.0001)))  # BTC
        else:
            gas_fee = Decimal(str(random.uniform(0.00001, 0.001)))  # SOL
        
        # Create transaction
        Transaction.objects.create(
            wallet=wallet,
            tx_hash=fake.hexify(text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"),
            block_number=random.randint(1000000, 9999999),
            timestamp=timestamp,
            transaction_type=tx_type,
            amount=amount,
            asset_symbol=asset.symbol,
            asset_address=fake.hexify(text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"),
            gas_fee=gas_fee,
            usd_value=usd_value,
            metadata={"mock": True, "generated_at": timezone.now().isoformat()},
        )