import random  # For mock data until we have real chain adapters
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict

from django.utils import timezone

from wallets.models import UserSettings, Wallet

from .cache import CacheService


class PortfolioService:
    """Service for portfolio calculations and data aggregation"""

    def __init__(self, user):
        self.user = user
        self.cache_service = CacheService()

        # Check if user has mock data enabled
        try:
            settings = UserSettings.objects.get(user=user)
            self.mock_data_enabled = settings.mock_data_enabled
        except UserSettings.DoesNotExist:
            self.mock_data_enabled = False

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Calculate current portfolio value across all wallets"""
        # Check cache first
        cache_key = f"portfolio_summary_{self.user.id}"
        cached_data = self.cache_service.get_portfolio_data(self.user.id, cache_key)

        if cached_data:
            return cached_data  # type: ignore[return-value]

        # Calculate portfolio value
        wallets = Wallet.objects.filter(user=self.user, is_active=True)
        total_value = Decimal("0")

        if self.mock_data_enabled:
            # Use mock values for demonstration
            for wallet in wallets:
                wallet_value = self._get_mock_wallet_value(wallet)
                total_value += wallet_value
        else:
            # Real data mode - would call chain adapters
            # For now, return zero since we don't have real adapters implemented
            total_value = Decimal("0")

        # Calculate 24h change
        change_24h = (
            self._calculate_24h_change() if self.mock_data_enabled else Decimal("0")
        )

        # Get asset distribution data
        asset_distribution = self._get_asset_distribution() if self.mock_data_enabled else {"labels": [], "values": []}
        
        result = {
            "total_value_usd": float(total_value),
            "change_24h": float(change_24h),
            "wallet_count": wallets.count(),
            "asset_count": len(asset_distribution["labels"]),
            "chain_count": wallets.values("chain").distinct().count(),
            "top_performer": self._get_top_performer() if self.mock_data_enabled else {"symbol": "N/A", "change_24h": 0},
            "asset_labels": asset_distribution["labels"],
            "asset_values": asset_distribution["values"],
            "last_updated": timezone.now().isoformat(),
        }

        # Cache for 1 minute
        self.cache_service.set_portfolio_data(
            self.user.id, cache_key, result, ttl_minutes=1
        )

        return result

    def _get_mock_wallet_value(self, wallet: Wallet) -> Decimal:
        """Generate mock wallet value for demo"""
        # Different ranges based on chain
        if wallet.chain == "ethereum":
            # Mock ETH balance between 0.5 and 10 ETH
            eth_balance = Decimal(str(random.uniform(0.5, 10)))
            eth_price = Decimal("2000")  # Mock ETH price
            return eth_balance * eth_price
        elif wallet.chain == "bitcoin":
            # Mock BTC balance between 0.01 and 0.5 BTC
            btc_balance = Decimal(str(random.uniform(0.01, 0.5)))
            btc_price = Decimal("45000")  # Mock BTC price
            return btc_balance * btc_price
        else:  # solana
            # Mock SOL balance between 10 and 500 SOL
            sol_balance = Decimal(str(random.uniform(10, 500)))
            sol_price = Decimal("100")  # Mock SOL price
            return sol_balance * sol_price

    def _calculate_24h_change(self) -> Decimal:
        """Calculate 24h portfolio change percentage"""
        # For MVP, return a mock change between -10% and +10%
        return Decimal(str(random.uniform(-10, 10)))

    def get_historical_data(self, period: str = "24h") -> list:
        """Get historical portfolio values"""
        if not self.mock_data_enabled:
            # Return empty data in real mode
            return []

        # Map period to timedelta
        period_map = {
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }

        time_delta = period_map.get(period, timedelta(days=1))
        start_time = timezone.now() - time_delta

        # Generate mock historical data
        data_points = []
        current_value = self.get_portfolio_summary()["total_value_usd"]

        # Generate data points
        num_points = 24 if period == "24h" else 7 if period == "7d" else 30
        for i in range(num_points):
            timestamp = start_time + (time_delta / num_points) * i
            # Add some random variation
            variation = random.uniform(0.95, 1.05)
            value = Decimal(str(current_value)) * Decimal(str(variation))

            data_points.append(
                {"timestamp": timestamp.isoformat(), "total_value_usd": float(value)}
            )

        return data_points

    def get_wallet_balances(self) -> list:
        """Get individual wallet balances"""
        wallets = Wallet.objects.filter(user=self.user, is_active=True)
        balances = []

        for wallet in wallets:
            if self.mock_data_enabled:
                # Mock balance for demonstration
                value = self._get_mock_wallet_value(wallet)
            else:
                # Real data mode - would call chain adapters
                value = Decimal("0")

            balances.append(
                {
                    "wallet_id": wallet.id,
                    "address": wallet.address,
                    "chain": wallet.chain,
                    "label": wallet.label
                    or f"{wallet.address[:6]}...{wallet.address[-4:]}",
                    "value_usd": float(value),
                    "last_updated": timezone.now().isoformat(),
                }
            )

        return balances
    
    def _get_asset_distribution(self) -> Dict[str, list]:
        """Get asset distribution for portfolio chart"""
        if not self.mock_data_enabled:
            return {"labels": [], "values": []}
        
        # Mock asset distribution
        assets = [
            {"symbol": "ETH", "value": random.uniform(2000, 10000)},
            {"symbol": "BTC", "value": random.uniform(5000, 20000)},
            {"symbol": "SOL", "value": random.uniform(1000, 5000)},
            {"symbol": "USDC", "value": random.uniform(500, 2000)},
        ]
        
        # Filter out zero values and sort by value
        assets = [a for a in assets if a["value"] > 0]
        assets.sort(key=lambda x: x["value"], reverse=True)
        
        labels = [a["symbol"] for a in assets]
        values = [round(a["value"], 2) for a in assets]
        
        return {"labels": labels, "values": values}
    
    def _get_top_performer(self) -> Dict[str, Any]:
        """Get top performing asset in 24h"""
        if not self.mock_data_enabled:
            return {"symbol": "N/A", "change_24h": 0}
        
        # Mock top performer
        assets = ["ETH", "BTC", "SOL", "MATIC", "LINK"]
        return {
            "symbol": random.choice(assets),
            "change_24h": random.uniform(5, 25)  # Positive change for "top" performer
        }
    
    def _calculate_wallet_balance(self, wallet, asset):
        """Calculate wallet balance for a specific asset"""
        from transactions.models import Transaction
        from decimal import Decimal
        
        # Get all transactions for this wallet and asset
        transactions = Transaction.objects.filter(
            wallet=wallet,
            asset_symbol=asset.symbol
        )
        
        balance = Decimal('0')
        for transaction in transactions:
            # Use the actual TransactionType values
            if transaction.transaction_type in ['buy', 'transfer']:
                balance += transaction.amount
            elif transaction.transaction_type in ['sell']:
                balance -= transaction.amount
        
        return balance
    
    def get_asset_allocation(self):
        """Get asset allocation across all wallets"""
        from transactions.models import Transaction, Asset
        from collections import defaultdict
        
        if not self.mock_data_enabled:
            return []
        
        # Get all user's wallets
        wallets = Wallet.objects.filter(user=self.user, is_active=True)
        
        # Calculate balances per asset
        asset_balances = defaultdict(Decimal)
        for wallet in wallets:
            transactions = Transaction.objects.filter(wallet=wallet)
            for transaction in transactions:
                if transaction.transaction_type in ['buy', 'transfer']:
                    asset_balances[transaction.asset_symbol] += transaction.amount
                elif transaction.transaction_type in ['sell']:
                    asset_balances[transaction.asset_symbol] -= transaction.amount
        
        # Convert to list format with mock prices
        allocation = []
        for symbol, balance in asset_balances.items():
            if balance > 0:  # Only include assets with positive balance
                # Mock price for calculation
                mock_price = Decimal('2000') if symbol == 'ETH' else Decimal('45000') if symbol == 'BTC' else Decimal('100')
                value = balance * mock_price
                allocation.append({
                    'symbol': symbol,
                    'balance': float(balance),
                    'value_usd': float(value),
                    'percentage': 0  # Will be calculated later if needed
                })
        
        return allocation
    
    def _get_current_prices(self, symbols):
        """Get current prices (with mock implementation for testing)"""
        try:
            import requests
            # In a real implementation, this would call an external API
            # For now, simulate the API call for testing
            response = requests.get("https://api.coingecko.com/api/v3/simple/price")
            
            # Mock prices for testing
            mock_prices = {
                'ETH': 2000.0,
                'BTC': 45000.0,
                'SOL': 100.0,
                'USDC': 1.0
            }
            
            return {symbol: mock_prices.get(symbol, 1.0) for symbol in symbols}
        except Exception:
            # Return empty dict on failure
            return {}
    
    def _get_historical_prices(self, symbols):
        """Mock method for getting historical prices"""
        # Return mock historical data
        return {symbol: [] for symbol in symbols}
    
    def get_portfolio_history(self, days=7):
        """Get portfolio history for specified number of days"""
        return self.get_historical_data(f"{days}d")
