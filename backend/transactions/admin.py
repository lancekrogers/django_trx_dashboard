from django.contrib import admin
from .models import Transaction, Asset, PortfolioCache, PriceCache


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model"""
    list_display = ('tx_hash_short', 'wallet', 'transaction_type', 'amount', 'asset_symbol', 'usd_value', 'timestamp')
    list_filter = ('transaction_type', 'asset_symbol', 'timestamp', 'wallet__chain')
    search_fields = ('tx_hash', 'asset_symbol', 'wallet__address')
    ordering = ('-timestamp',)
    readonly_fields = ('created_at',)
    
    def tx_hash_short(self, obj):
        """Display shortened transaction hash"""
        return f"{obj.tx_hash[:8]}..."
    tx_hash_short.short_description = 'TX Hash'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Admin configuration for Asset model"""
    list_display = ('symbol', 'name', 'chain', 'current_price_usd', 'last_updated')
    list_filter = ('chain', 'last_updated')
    search_fields = ('symbol', 'name', 'contract_address')
    ordering = ('symbol', 'chain')


@admin.register(PortfolioCache)
class PortfolioCacheAdmin(admin.ModelAdmin):
    """Admin configuration for PortfolioCache model"""
    list_display = ('user', 'cache_key', 'expires_at', 'created_at')
    list_filter = ('expires_at', 'created_at')
    search_fields = ('user__email', 'cache_key')
    ordering = ('-created_at',)


@admin.register(PriceCache)
class PriceCacheAdmin(admin.ModelAdmin):
    """Admin configuration for PriceCache model"""
    list_display = ('symbol', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('symbol',)
    ordering = ('-last_updated',)