import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from transactions.models import Asset, Transaction, TransactionType
from wallets.models import User, UserSettings, Wallet

fake = Faker()


class Command(BaseCommand):
    help = "Generate mock data for testing and demo purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=3, help="Number of users to create"
        )
        parser.add_argument(
            "--transactions",
            type=int,
            default=50,
            help="Number of transactions per wallet",
        )
        parser.add_argument(
            "--superusers",
            type=int,
            default=1,
            help="Number of superusers to create",
        )
        parser.add_argument(
            "--email-domain",
            type=str,
            default="example.com",
            help="Email domain for generated users",
        )

    def handle(self, *args, **options):
        self.stdout.write("Generating mock data...")

        # Create assets
        assets = self._create_assets()

        # Create superusers
        for i in range(options["superusers"]):
            user = self._create_superuser(i, options["email_domain"])
            wallets = self._create_wallets(user)

            # Create transactions for each wallet
            for wallet in wallets:
                self._create_transactions(
                    wallet, assets[wallet.chain], options["transactions"]
                )

        # Create regular users with wallets
        for i in range(options["users"]):
            user = self._create_user(i, options["email_domain"])
            wallets = self._create_wallets(user)

            # Create transactions for each wallet
            for wallet in wallets:
                self._create_transactions(
                    wallet, assets[wallet.chain], options["transactions"]
                )

        self.stdout.write(self.style.SUCCESS("Mock data generated successfully!"))
        
        # Also generate investigation cases
        self.stdout.write("\nGenerating investigation cases...")
        from django.core.management import call_command
        call_command('generate_investigation_data', cases=5)

    def _create_assets(self):
        """Create mock assets for each chain"""
        assets = {"ethereum": [], "bitcoin": [], "solana": []}

        # Ethereum assets
        eth_assets_data = [
            {"symbol": "ETH", "name": "Ethereum", "decimals": 18, "price": 2000},
            {"symbol": "USDC", "name": "USD Coin", "decimals": 6, "price": 1},
            {"symbol": "USDT", "name": "Tether", "decimals": 6, "price": 1},
            {
                "symbol": "WBTC",
                "name": "Wrapped Bitcoin",
                "decimals": 8,
                "price": 45000,
            },
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

    def _create_superuser(self, index, domain):
        """Create a mock superuser"""
        email = f"admin{index}@{domain}"
        username = f"admin{index}"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(f"Created superuser: {email}")

        # Create settings with mock data enabled by default
        settings, settings_created = UserSettings.objects.get_or_create(
            user=user, defaults={"mock_data_enabled": True}
        )
        if settings_created:
            self.stdout.write(f"Created settings for superuser: {email}")

        return user

    def _create_user(self, index, domain):
        """Create a mock user"""
        email = f"user{index}@{domain}"
        username = f"user{index}"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
            },
        )

        if created:
            user.set_password("testpass123")
            user.save()
            self.stdout.write(f"Created user: {email}")

        # Create settings with mock data enabled by default
        settings, settings_created = UserSettings.objects.get_or_create(
            user=user, defaults={"mock_data_enabled": True}
        )
        if settings_created:
            self.stdout.write(f"Created settings for user: {email}")

        return user

    def _create_wallets(self, user):
        """Create wallets for a user"""
        wallets = []

        # Ethereum wallet
        eth_wallet, _ = Wallet.objects.get_or_create(
            user=user,
            chain="ethereum",
            defaults={
                "address": "0x"
                + fake.hexify(text="^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"),
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
                "address": fake.bothify(
                    text="?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#"
                ),
                "label": "My SOL Wallet",
            },
        )
        wallets.append(sol_wallet)

        return wallets

    def _create_transactions(self, wallet, assets, count):
        """Create mock transactions for a wallet"""
        # Start from 30 days ago
        start_date = timezone.now() - timedelta(days=30)

        for i in range(count):
            # Random timestamp within the last 30 days
            timestamp = start_date + timedelta(
                hours=random.randint(0, 30 * 24), minutes=random.randint(0, 59)
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
                tx_hash=fake.hexify(
                    text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
                ),
                block_number=random.randint(1000000, 9999999),
                timestamp=timestamp,
                transaction_type=tx_type,
                amount=amount,
                asset_symbol=asset.symbol,
                asset_address=fake.hexify(
                    text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
                ),
                gas_fee=gas_fee,
                usd_value=usd_value,
                metadata={"mock": True, "generated_at": timezone.now().isoformat()},
            )
