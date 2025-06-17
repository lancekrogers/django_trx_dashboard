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
    help = "Generate comprehensive mock investigation data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cases", type=int, default=5, help="Number of investigation cases per user"
        )
        parser.add_argument(
            "--clear", action="store_true", help="Clear existing data before generating"
        )

    def handle(self, *args, **options):
        self.stdout.write("Generating investigation mock data...")

        if options["clear"]:
            self.stdout.write("Clearing existing investigation data...")
            InvestigationCase.objects.all().delete()
            
        # Get all users with mock data enabled
        users = User.objects.filter(settings__mock_data_enabled=True)
        
        if not users.exists():
            self.stdout.write(self.style.WARNING("No users with mock data enabled. Run generate_mock_data first."))
            return

        # Predefined investigation case templates
        case_templates = [
            {
                "name": "DeFi Protocol Hack Investigation",
                "description": "Tracking stolen funds from the recent DeFi protocol exploit",
                "priority": "critical",
                "pattern": "hack",
                "wallet_categories": ["victim", "suspect", "mixer", "exchange"],
            },
            {
                "name": "Money Laundering Network",
                "description": "Complex network of wallets involved in layering transactions",
                "priority": "high",
                "pattern": "laundering",
                "wallet_categories": ["suspect", "mixer", "exchange"],
            },
            {
                "name": "Exchange Compliance Check",
                "description": "Regular compliance verification of exchange hot wallets",
                "priority": "medium",
                "pattern": "compliance",
                "wallet_categories": ["exchange", "unknown"],
            },
            {
                "name": "NFT Wash Trading Investigation",
                "description": "Investigating suspicious NFT trading patterns",
                "priority": "medium",
                "pattern": "wash_trading",
                "wallet_categories": ["suspect", "unknown"],
            },
            {
                "name": "Ransomware Payment Tracking",
                "description": "Following ransomware payment through mixing services",
                "priority": "critical",
                "pattern": "ransomware",
                "wallet_categories": ["victim", "suspect", "mixer"],
            },
            {
                "name": "Pump and Dump Scheme",
                "description": "Tracking coordinated token manipulation",
                "priority": "high",
                "pattern": "pump_dump",
                "wallet_categories": ["suspect", "victim", "exchange"],
            },
            {
                "name": "Terrorist Financing Investigation",
                "description": "Tracking suspicious donations to flagged addresses",
                "priority": "critical",
                "pattern": "terrorism",
                "wallet_categories": ["suspect", "unknown", "mixer"],
            },
            {
                "name": "ICO Exit Scam Analysis",
                "description": "Investigating disappearing ICO funds",
                "priority": "high",
                "pattern": "exit_scam",
                "wallet_categories": ["victim", "suspect", "exchange"],
            },
        ]

        for user in users:
            self.stdout.write(f"\nGenerating cases for user: {user.email}")
            
            # Create investigation cases
            num_cases = min(options["cases"], len(case_templates))
            selected_templates = random.sample(case_templates, num_cases)
            
            for template in selected_templates:
                case = self._create_investigation_case(user, template)
                self._populate_case_with_wallets(user, case, template)
                self._generate_pattern_transactions(case, template["pattern"])
                
        self.stdout.write(self.style.SUCCESS("\nInvestigation data generated successfully!"))

    def _create_investigation_case(self, user, template):
        """Create an investigation case from template"""
        # Vary the status based on priority
        if template["priority"] == "critical":
            status = random.choice([InvestigationStatus.ACTIVE, InvestigationStatus.ACTIVE])
        elif template["priority"] == "high":
            status = random.choice([InvestigationStatus.ACTIVE, InvestigationStatus.PENDING])
        else:
            status = random.choice([InvestigationStatus.ACTIVE, InvestigationStatus.PENDING, 
                                   InvestigationStatus.COMPLETED])
        
        # Add case number for realism
        case_number = fake.bothify(text="CASE-####-????").upper()
        
        case = InvestigationCase.objects.create(
            name=f"{case_number}: {template['name']}",
            description=template["description"],
            investigator=user,
            status=status,
            priority=template["priority"],
            notes=self._generate_investigation_notes(template["pattern"]),
            created_at=timezone.now() - timedelta(days=random.randint(1, 90))
        )
        
        self.stdout.write(f"  Created case: {case.name}")
        return case

    def _populate_case_with_wallets(self, user, case, template):
        """Add wallets to the investigation case"""
        # Get or create suspicious wallets
        num_wallets = random.randint(3, 10)
        
        for i in range(num_wallets):
            # Create wallet with suspicious patterns
            chain = random.choice(["ethereum", "bitcoin", "solana"])
            category = random.choice(template["wallet_categories"])
            
            # Generate realistic addresses
            if chain == "ethereum":
                address = "0x" + fake.hexify(text="^" * 40)
            elif chain == "bitcoin":
                address = fake.bothify(text="bc1q" + "?" * 38)
            else:  # solana
                address = fake.bothify(text="?" * 44)
            
            # Create or get wallet
            wallet, created = Wallet.objects.get_or_create(
                address=address,
                chain=chain,
                user=user,
                defaults={
                    "label": f"{category.title()} Wallet {i+1}",
                    "notes": f"Flagged as {category} in {case.name}",
                    "is_monitored": category in ["suspect", "mixer"],
                }
            )
            
            # Add wallet to case
            case_wallet = CaseWallet.objects.create(
                case=case,
                wallet=wallet,
                category=category,
                notes=self._generate_wallet_notes(category, template["pattern"]),
                flagged=category in ["suspect", "mixer"],
            )
            
            if created:
                self.stdout.write(f"    Added {category} wallet: {wallet.short_address}")

    def _generate_pattern_transactions(self, case, pattern):
        """Generate transactions that follow suspicious patterns"""
        case_wallets = CaseWallet.objects.filter(case=case).select_related('wallet')
        
        if not case_wallets.exists():
            return
            
        # Get assets for transaction generation
        assets = self._get_or_create_assets()
        
        # Generate transactions based on pattern
        if pattern == "hack":
            self._generate_hack_pattern(case_wallets, assets)
        elif pattern == "laundering":
            self._generate_laundering_pattern(case_wallets, assets)
        elif pattern == "wash_trading":
            self._generate_wash_trading_pattern(case_wallets, assets)
        elif pattern == "ransomware":
            self._generate_ransomware_pattern(case_wallets, assets)
        elif pattern == "pump_dump":
            self._generate_pump_dump_pattern(case_wallets, assets)
        else:
            # Default pattern
            self._generate_default_pattern(case_wallets, assets)

    def _generate_hack_pattern(self, case_wallets, assets):
        """Generate hack pattern: large withdrawal -> splits -> mixers -> exchanges"""
        victim_wallets = case_wallets.filter(category="victim")
        suspect_wallets = case_wallets.filter(category="suspect")
        mixer_wallets = case_wallets.filter(category="mixer")
        
        if not victim_wallets.exists():
            return
            
        # Initial hack transaction (large amount)
        victim_wallet = victim_wallets.first().wallet
        hack_amount = Decimal(str(random.uniform(100, 1000)))  # Large ETH amount
        hack_time = timezone.now() - timedelta(days=random.randint(5, 30))
        
        # Create the hack transaction
        Transaction.objects.create(
            wallet=victim_wallet,
            tx_hash=fake.hexify(text="0x" + "^" * 64),
            block_number=random.randint(1000000, 9999999),
            timestamp=hack_time,
            transaction_type="transfer",
            amount=hack_amount,
            asset_symbol="ETH",
            gas_fee=Decimal("0.01"),
            usd_value=hack_amount * Decimal("2000"),
            metadata={"pattern": "hack", "role": "initial_theft"}
        )
        
        # Split transactions to suspect wallets
        if suspect_wallets.exists():
            split_amount = hack_amount / len(suspect_wallets)
            for i, cw in enumerate(suspect_wallets):
                Transaction.objects.create(
                    wallet=cw.wallet,
                    tx_hash=fake.hexify(text="0x" + "^" * 64),
                    block_number=random.randint(1000000, 9999999),
                    timestamp=hack_time + timedelta(hours=i+1),
                    transaction_type="transfer",
                    amount=split_amount,
                    asset_symbol="ETH",
                    gas_fee=Decimal("0.005"),
                    usd_value=split_amount * Decimal("2000"),
                    metadata={"pattern": "hack", "role": "split"}
                )

    def _generate_laundering_pattern(self, case_wallets, assets):
        """Generate layering pattern typical of money laundering"""
        wallets = [cw.wallet for cw in case_wallets]
        
        if len(wallets) < 3:
            return
            
        # Create a chain of transactions
        base_amount = Decimal(str(random.uniform(10, 100)))
        current_time = timezone.now() - timedelta(days=20)
        
        for i in range(20):  # 20 layering transactions
            from_wallet = random.choice(wallets)
            to_wallet = random.choice([w for w in wallets if w != from_wallet])
            
            # Vary amounts slightly to avoid detection
            amount = base_amount * Decimal(str(random.uniform(0.9, 1.1)))
            
            Transaction.objects.create(
                wallet=from_wallet,
                tx_hash=fake.hexify(text="0x" + "^" * 64),
                block_number=random.randint(1000000, 9999999),
                timestamp=current_time + timedelta(hours=i*3),
                transaction_type="transfer",
                amount=amount,
                asset_symbol=random.choice(["ETH", "USDC", "USDT"]),
                gas_fee=Decimal("0.002"),
                usd_value=amount * Decimal("1") if "USD" in "USDC" else amount * Decimal("2000"),
                metadata={"pattern": "laundering", "layer": i}
            )

    def _generate_wash_trading_pattern(self, case_wallets, assets):
        """Generate wash trading pattern with circular transactions"""
        wallets = [cw.wallet for cw in case_wallets][:4]  # Use up to 4 wallets
        
        if len(wallets) < 2:
            return
            
        # Create circular trades
        trade_amount = Decimal(str(random.uniform(1, 10)))
        base_time = timezone.now() - timedelta(days=7)
        
        for day in range(7):
            for i in range(len(wallets)):
                from_wallet = wallets[i]
                to_wallet = wallets[(i + 1) % len(wallets)]
                
                # Multiple trades per day
                for trade in range(random.randint(3, 8)):
                    timestamp = base_time + timedelta(days=day, hours=trade*3)
                    
                    Transaction.objects.create(
                        wallet=from_wallet,
                        tx_hash=fake.hexify(text="0x" + "^" * 64),
                        block_number=random.randint(1000000, 9999999),
                        timestamp=timestamp,
                        transaction_type="sell" if trade % 2 == 0 else "buy",
                        amount=trade_amount * Decimal(str(random.uniform(0.95, 1.05))),
                        asset_symbol="SHIB",  # Meme token for wash trading
                        gas_fee=Decimal("0.001"),
                        usd_value=trade_amount * Decimal("0.00001"),  # Low value token
                        metadata={"pattern": "wash_trading", "cycle": f"{day}-{i}-{trade}"}
                    )

    def _generate_ransomware_pattern(self, case_wallets, assets):
        """Generate ransomware payment pattern"""
        victim_wallets = case_wallets.filter(category="victim")
        suspect_wallets = case_wallets.filter(category="suspect")
        
        if not victim_wallets.exists() or not suspect_wallets.exists():
            return
            
        # Ransomware payment (usually in BTC)
        ransom_amount = Decimal(str(random.uniform(0.1, 2)))  # BTC
        payment_time = timezone.now() - timedelta(days=random.randint(3, 15))
        
        # Payment from victim to suspect
        Transaction.objects.create(
            wallet=victim_wallets.first().wallet,
            tx_hash=fake.hexify(text="0x" + "^" * 64),
            block_number=random.randint(1000000, 9999999),
            timestamp=payment_time,
            transaction_type="transfer",
            amount=ransom_amount,
            asset_symbol="BTC",
            gas_fee=Decimal("0.0001"),
            usd_value=ransom_amount * Decimal("45000"),
            metadata={"pattern": "ransomware", "type": "ransom_payment"}
        )
        
        # Quick movement to mixers
        mixer_wallets = case_wallets.filter(category="mixer")
        if mixer_wallets.exists():
            for i, mw in enumerate(mixer_wallets[:3]):
                Transaction.objects.create(
                    wallet=mw.wallet,
                    tx_hash=fake.hexify(text="0x" + "^" * 64),
                    block_number=random.randint(1000000, 9999999),
                    timestamp=payment_time + timedelta(hours=1+i),
                    transaction_type="transfer",
                    amount=ransom_amount / 3,
                    asset_symbol="BTC",
                    gas_fee=Decimal("0.00005"),
                    usd_value=(ransom_amount / 3) * Decimal("45000"),
                    metadata={"pattern": "ransomware", "type": "mixing"}
                )

    def _generate_pump_dump_pattern(self, case_wallets, assets):
        """Generate pump and dump pattern with coordinated buys then mass sell"""
        wallets = [cw.wallet for cw in case_wallets]
        
        if len(wallets) < 3:
            return
            
        # Pump phase - coordinated buys
        pump_start = timezone.now() - timedelta(days=10)
        token_symbol = "MOON"  # Fake token
        
        # Initial accumulation
        for i, wallet in enumerate(wallets):
            for buy in range(5):  # Multiple small buys
                Transaction.objects.create(
                    wallet=wallet,
                    tx_hash=fake.hexify(text="0x" + "^" * 64),
                    block_number=random.randint(1000000, 9999999),
                    timestamp=pump_start + timedelta(hours=i*2 + buy),
                    transaction_type="buy",
                    amount=Decimal(str(random.uniform(1000, 5000))),
                    asset_symbol=token_symbol,
                    gas_fee=Decimal("0.002"),
                    usd_value=Decimal(str(random.uniform(10, 50))),  # Low initial value
                    metadata={"pattern": "pump_dump", "phase": "accumulation"}
                )
        
        # Dump phase - mass selling
        dump_time = pump_start + timedelta(days=3)
        for wallet in wallets:
            Transaction.objects.create(
                wallet=wallet,
                tx_hash=fake.hexify(text="0x" + "^" * 64),
                block_number=random.randint(1000000, 9999999),
                timestamp=dump_time + timedelta(minutes=random.randint(0, 30)),
                transaction_type="sell",
                amount=Decimal(str(random.uniform(10000, 50000))),  # Large sells
                asset_symbol=token_symbol,
                gas_fee=Decimal("0.005"),
                usd_value=Decimal(str(random.uniform(1000, 5000))),  # High value at peak
                metadata={"pattern": "pump_dump", "phase": "dump"}
            )

    def _generate_default_pattern(self, case_wallets, assets):
        """Generate generic suspicious activity"""
        for cw in case_wallets:
            # Random transactions
            for _ in range(random.randint(5, 15)):
                Transaction.objects.create(
                    wallet=cw.wallet,
                    tx_hash=fake.hexify(text="0x" + "^" * 64),
                    block_number=random.randint(1000000, 9999999),
                    timestamp=timezone.now() - timedelta(
                        days=random.randint(1, 30),
                        hours=random.randint(0, 23)
                    ),
                    transaction_type=random.choice(["buy", "sell", "transfer"]),
                    amount=Decimal(str(random.uniform(0.1, 100))),
                    asset_symbol=random.choice(["ETH", "BTC", "USDC"]),
                    gas_fee=Decimal("0.001"),
                    usd_value=Decimal(str(random.uniform(100, 10000))),
                    metadata={"pattern": "default"}
                )

    def _get_or_create_assets(self):
        """Get or create basic assets"""
        assets = []
        
        # Ensure basic assets exist
        eth, _ = Asset.objects.get_or_create(
            symbol="ETH", chain="ethereum",
            defaults={"name": "Ethereum", "decimals": 18, "current_price_usd": Decimal("2000")}
        )
        assets.append(eth)
        
        btc, _ = Asset.objects.get_or_create(
            symbol="BTC", chain="bitcoin",
            defaults={"name": "Bitcoin", "decimals": 8, "current_price_usd": Decimal("45000")}
        )
        assets.append(btc)
        
        usdc, _ = Asset.objects.get_or_create(
            symbol="USDC", chain="ethereum",
            defaults={"name": "USD Coin", "decimals": 6, "current_price_usd": Decimal("1")}
        )
        assets.append(usdc)
        
        return assets

    def _generate_investigation_notes(self, pattern):
        """Generate realistic investigation notes based on pattern"""
        notes_templates = {
            "hack": [
                "Initial breach detected at block 15234567. Funds moved through Tornado Cash.",
                "Smart contract exploit identified. $2.3M drained from liquidity pool.",
                "Attacker used flash loan attack vector. Multiple wallets involved in fund distribution.",
            ],
            "laundering": [
                "Complex layering scheme detected. Over 50 transactions across 15 wallets.",
                "Funds originated from known darknet marketplace. Using DeFi protocols for obfuscation.",
                "Pattern consistent with Hydra market operators. High-frequency small transactions.",
            ],
            "ransomware": [
                "Ransom demand: 2.5 BTC. Payment deadline was 72 hours from initial contact.",
                "Victim organization: Healthcare provider. Critical systems encrypted.",
                "Bitcoin address linked to REvil ransomware group based on blockchain analysis.",
            ],
            "wash_trading": [
                "Circular trading pattern detected between 4 wallets. Volume inflation suspected.",
                "Same wallets trading MOON token repeatedly. No external participants.",
                "Trading bots identified. Coordinated pump scheme across multiple DEXs.",
            ],
            "pump_dump": [
                "Telegram group 'Moon Calls' coordinating buys. 500+ members involved.",
                "Token contract shows mint function still active. Red flag for rug pull.",
                "Coordinated social media campaign detected 24 hours before dump.",
            ],
        }
        
        base_notes = notes_templates.get(pattern, [
            "Suspicious activity flagged by monitoring system.",
            "Multiple red flags identified. Further investigation required.",
            "Pattern analysis indicates potential illicit activity.",
        ])
        
        return random.choice(base_notes) + f"\n\nCase opened: {fake.date_time_this_month()}"

    def _generate_wallet_notes(self, category, pattern):
        """Generate wallet-specific notes"""
        notes_templates = {
            "suspect": [
                "Wallet shows signs of automated trading. Possible bot activity.",
                "Multiple small transactions to avoid detection thresholds.",
                "Connected to known malicious smart contracts.",
            ],
            "victim": [
                "Compromised wallet. Private keys potentially exposed.",
                "Phishing attack victim. Signed malicious transaction.",
                "Hot wallet breach. Security audit recommended.",
            ],
            "mixer": [
                "Tornado Cash deposit detected. 100 ETH mixed in 10 ETH chunks.",
                "CoinJoin participation confirmed. Multiple mixing rounds.",
                "Using privacy protocol for transaction obfuscation.",
            ],
            "exchange": [
                "Binance hot wallet identified. KYC potentially available.",
                "DEX aggregator wallet. No KYC available.",
                "Centralized exchange deposit address. Subpoena possible.",
            ],
            "unknown": [
                "Newly created wallet. No transaction history prior to case.",
                "Wallet purpose unclear. Requires further analysis.",
                "Potentially compromised address. Monitor for activity.",
            ],
        }
        
        return random.choice(notes_templates.get(category, ["Under investigation"]))