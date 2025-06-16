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
            value = current_value * Decimal(str(variation))

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
