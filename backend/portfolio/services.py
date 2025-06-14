from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import timedelta
from typing import Dict, Any, Optional
from wallets.models import Wallet
from transactions.models import Transaction, Asset
from .cache import CacheService
import random  # For mock data until we have real chain adapters


class PortfolioService:
    """Service for portfolio calculations and data aggregation"""
    
    def __init__(self, user):
        self.user = user
        self.cache_service = CacheService()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Calculate current portfolio value across all wallets"""
        # Check cache first
        cache_key = f"portfolio_summary_{self.user.id}"
        cached_data = self.cache_service.get_portfolio_data(self.user.id, cache_key)
        
        if cached_data:
            return cached_data
        
        # Calculate portfolio value
        wallets = Wallet.objects.filter(user=self.user, is_active=True)
        total_value = Decimal('0')
        
        # For MVP, we'll use mock values
        # In production, this would call chain adapters
        for wallet in wallets:
            # Mock balance calculation
            wallet_value = self._get_mock_wallet_value(wallet)
            total_value += wallet_value
        
        # Calculate 24h change
        change_24h = self._calculate_24h_change()
        
        result = {
            'total_value_usd': float(total_value),
            'change_24h': float(change_24h),
            'wallet_count': wallets.count(),
            'last_updated': timezone.now().isoformat()
        }
        
        # Cache for 1 minute
        self.cache_service.set_portfolio_data(self.user.id, cache_key, result, ttl_minutes=1)
        
        return result
    
    def _get_mock_wallet_value(self, wallet: Wallet) -> Decimal:
        """Generate mock wallet value for demo"""
        # Different ranges based on chain
        if wallet.chain == 'ethereum':
            # Mock ETH balance between 0.5 and 10 ETH
            eth_balance = Decimal(str(random.uniform(0.5, 10)))
            eth_price = Decimal('2000')  # Mock ETH price
            return eth_balance * eth_price
        elif wallet.chain == 'bitcoin':
            # Mock BTC balance between 0.01 and 0.5 BTC
            btc_balance = Decimal(str(random.uniform(0.01, 0.5)))
            btc_price = Decimal('45000')  # Mock BTC price
            return btc_balance * btc_price
        else:  # solana
            # Mock SOL balance between 10 and 500 SOL
            sol_balance = Decimal(str(random.uniform(10, 500)))
            sol_price = Decimal('100')  # Mock SOL price
            return sol_balance * sol_price
    
    def _calculate_24h_change(self) -> Decimal:
        """Calculate 24h portfolio change percentage"""
        # For MVP, return a mock change between -10% and +10%
        return Decimal(str(random.uniform(-10, 10)))
    
    def get_historical_data(self, period: str = '24h') -> list:
        """Get historical portfolio values"""
        # Map period to timedelta
        period_map = {
            '24h': timedelta(days=1),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30),
        }
        
        time_delta = period_map.get(period, timedelta(days=1))
        start_time = timezone.now() - time_delta
        
        # For MVP, generate mock historical data
        data_points = []
        current_value = self.get_portfolio_summary()['total_value_usd']
        
        # Generate data points
        num_points = 24 if period == '24h' else 7 if period == '7d' else 30
        for i in range(num_points):
            timestamp = start_time + (time_delta / num_points) * i
            # Add some random variation
            variation = random.uniform(0.95, 1.05)
            value = current_value * Decimal(str(variation))
            
            data_points.append({
                'timestamp': timestamp.isoformat(),
                'total_value_usd': float(value)
            })
        
        return data_points
    
    def get_wallet_balances(self) -> list:
        """Get individual wallet balances"""
        wallets = Wallet.objects.filter(user=self.user, is_active=True)
        balances = []
        
        for wallet in wallets:
            # Mock balance for MVP
            value = self._get_mock_wallet_value(wallet)
            balances.append({
                'wallet_id': wallet.id,
                'address': wallet.address,
                'chain': wallet.chain,
                'label': wallet.label or f"{wallet.address[:6]}...{wallet.address[-4:]}",
                'value_usd': float(value),
                'last_updated': timezone.now().isoformat()
            })
        
        return balances