from datetime import timedelta
from typing import Any, Dict, Optional

from django.utils import timezone

from transactions.models import PortfolioCache, PriceCache


class CacheService:
    """SQLite-based caching service for portfolio data"""

    @staticmethod
    def set_portfolio_data(
        user_id: int, key: str, data: Dict[str, Any], ttl_minutes: int = 60
    ) -> None:
        """Cache portfolio data with TTL"""
        expires_at = (
            timezone.now() + timedelta(minutes=ttl_minutes) if ttl_minutes else None
        )

        PortfolioCache.objects.update_or_create(
            user_id=user_id,
            cache_key=key,
            defaults={"data": data, "expires_at": expires_at},
        )

    @staticmethod
    def get_portfolio_data(user_id: int, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached portfolio data"""
        try:
            cache = PortfolioCache.objects.get(user_id=user_id, cache_key=key)

            # Check if expired
            if cache.expires_at and cache.expires_at < timezone.now():
                cache.delete()
                return None

            return cache.data  # type: ignore[return-value]
        except PortfolioCache.DoesNotExist:
            return None

    @staticmethod
    def set_price_data(symbol: str, price_data: Dict[str, Any]) -> None:
        """Cache price data"""
        PriceCache.objects.update_or_create(
            symbol=symbol, defaults={"price_data": price_data}
        )

    @staticmethod
    def get_price_data(symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached price data"""
        try:
            cache = PriceCache.objects.get(symbol=symbol)

            # Check if price data is fresh (30 seconds for crypto prices)
            if cache.last_updated < timezone.now() - timedelta(seconds=30):
                return None

            return cache.price_data  # type: ignore[return-value]
        except PriceCache.DoesNotExist:
            return None

    @staticmethod
    def cleanup_expired():
        """Clean up expired cache entries"""
        expired_count = PortfolioCache.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        return expired_count[0]
