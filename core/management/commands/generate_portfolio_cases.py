import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from portfolio.models import InvestigationCase, CaseWallet, InvestigationStatus, WalletCategory
from transactions.models import Asset, Transaction, TransactionType
from wallets.models import User, UserSettings, Wallet

fake = Faker()


class Command(BaseCommand):
    help = "Generate impressive portfolio case data for demo"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing cases")

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing cases...")
            InvestigationCase.objects.all().delete()
            
        # Get demo user
        user = User.objects.filter(email="lance@blockhead.consulting").first()
        if not user:
            self.stdout.write(self.style.ERROR("Demo user not found"))
            return
            
        # Enable mock data for user
        settings, _ = UserSettings.objects.get_or_create(user=user)
        settings.mock_data_enabled = True
        settings.save()

        self.stdout.write("Creating impressive portfolio cases...")
        
        # Create 3 impressive cases
        cases = [
            {
                "name": "Arbitrage Bot Strategy Tracker",
                "description": "High-frequency arbitrage operations across DEXs and chains",
                "priority": "high",
                "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
                "wallet_count": 8,
                "pattern": "arbitrage"
            },
            {
                "name": "DeFi Yield Farming Monitor", 
                "description": "Yield optimization strategy across multiple protocols",
                "priority": "medium",
                "chains": ["ethereum", "arbitrum", "polygon"],
                "wallet_count": 5,
                "pattern": "defi"
            },
            {
                "name": "Cross-Chain MEV Analysis",
                "description": "MEV extraction opportunities and execution patterns", 
                "priority": "critical",
                "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
                "wallet_count": 12,
                "pattern": "mev"
            }
        ]
        
        for case_data in cases:
            case = self._create_case(user, case_data)
            self._add_wallets(user, case, case_data)
            self._generate_transactions(case, case_data)
            
        self.stdout.write(self.style.SUCCESS("Portfolio cases created successfully!"))

    def _create_case(self, user, data):
        case = InvestigationCase.objects.create(
            name=data["name"],
            description=data["description"],
            investigator=user,
            status=InvestigationStatus.ACTIVE,
            priority=data["priority"],
            notes=f"Tracking {data['pattern']} patterns across {len(data['chains'])} chains",
            created_at=timezone.now() - timedelta(days=random.randint(7, 30))
        )
        self.stdout.write(f"  Created: {case.name}")
        return case
        
    def _add_wallets(self, user, case, data):
        for i in range(data["wallet_count"]):
            chain = random.choice(data["chains"])
            
            # Generate realistic addresses
            if chain == "ethereum":
                address = "0x" + fake.hexify(text="^" * 40)
            elif chain in ["arbitrum", "optimism"]:
                address = "0x" + fake.hexify(text="^" * 40)  # Same format as ETH
            elif chain == "polygon":
                address = "0x" + fake.hexify(text="^" * 40)  # Same format as ETH
            else:
                address = fake.bothify(text="?" * 44)  # Solana-style
                
            wallet = Wallet.objects.create(
                address=address,
                chain=chain,
                user=user,
                label=f"{chain.title()} Wallet {i+1}",
                is_monitored=True
            )
            
            # Add to case with appropriate category
            category = random.choice(["unknown", "exchange"] if i < 3 else ["unknown"])
            
            CaseWallet.objects.create(
                case=case,
                wallet=wallet,
                category=category,
                flagged=False,
                notes=f"Part of {data['pattern']} strategy"
            )
            
    def _generate_transactions(self, case, data):
        """Generate realistic transaction patterns"""
        case_wallets = list(CaseWallet.objects.filter(case=case).select_related('wallet'))
        assets = self._get_assets()
        
        # Transaction counts based on pattern
        tx_counts = {
            "arbitrage": 500,
            "defi": 200, 
            "mev": 800
        }
        
        num_transactions = tx_counts.get(data["pattern"], 300)
        
        for i in range(num_transactions):
            wallet = random.choice(case_wallets).wallet
            asset = random.choice(assets)
            
            # Generate realistic amounts based on pattern
            if data["pattern"] == "arbitrage":
                amount = Decimal(str(random.uniform(0.1, 50)))  # Smaller, frequent trades
                tx_type = random.choice(["swap", "transfer"])
            elif data["pattern"] == "defi":
                amount = Decimal(str(random.uniform(1, 200)))   # Larger positions
                tx_type = random.choice(["transfer", "defi", "swap"])
            else:  # MEV
                amount = Decimal(str(random.uniform(0.05, 25))) # Variable sizes
                tx_type = random.choice(["swap", "transfer", "defi"])
                
            # Create transaction with realistic timing
            timestamp = timezone.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            Transaction.objects.create(
                wallet=wallet,
                tx_hash="0x" + fake.hexify(text="^" * 64),
                block_number=random.randint(18000000, 19000000),
                timestamp=timestamp,
                transaction_type=tx_type,
                amount=amount,
                asset_symbol=asset["symbol"],
                gas_fee=self._calculate_gas_fee(wallet.chain),
                usd_value=amount * Decimal(str(asset["price"])),
                metadata={
                    "pattern": data["pattern"],
                    "chain": wallet.chain,
                    "protocol": random.choice(["uniswap", "sushiswap", "1inch", "paraswap"])
                }
            )
            
    def _get_assets(self):
        """Get common trading assets with prices"""
        return [
            {"symbol": "ETH", "price": 2000},
            {"symbol": "USDC", "price": 1},
            {"symbol": "USDT", "price": 1},
            {"symbol": "ARB", "price": 1.2},
            {"symbol": "OP", "price": 2.1},
            {"symbol": "MATIC", "price": 0.8},
            {"symbol": "WBTC", "price": 42000},
        ]
        
    def _calculate_gas_fee(self, chain):
        """Calculate realistic gas fees by chain"""
        fees = {
            "ethereum": Decimal(str(random.uniform(0.003, 0.02))),
            "arbitrum": Decimal(str(random.uniform(0.0001, 0.001))),
            "optimism": Decimal(str(random.uniform(0.0001, 0.001))), 
            "polygon": Decimal(str(random.uniform(0.0001, 0.001))),
        }
        return fees.get(chain, Decimal("0.001"))