from django.db import models

from wallets.models import Chain, User, Wallet


class TransactionType(models.TextChoices):
    """Types of blockchain transactions"""

    BUY = "buy", "Buy"
    SELL = "sell", "Sell"
    TRANSFER = "transfer", "Transfer"
    CONTRACT_CALL = "contract_call", "Contract Call"


class Transaction(models.Model):
    """Blockchain transaction record"""

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    tx_hash = models.CharField(max_length=100, unique=True)
    block_number = models.BigIntegerField()
    timestamp = models.DateTimeField()
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    asset_symbol = models.CharField(max_length=20)
    asset_address = models.CharField(max_length=100, blank=True)
    gas_fee = models.DecimalField(max_digits=36, decimal_places=18)
    usd_value = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    metadata = models.JSONField(default=dict)  # Chain-specific data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["wallet", "-timestamp"]),
            models.Index(fields=["transaction_type", "-timestamp"]),
            models.Index(fields=["asset_symbol", "-timestamp"]),
        ]

    def __str__(self):
        return (
            f"{self.get_transaction_type_display()} {self.amount} {self.asset_symbol}"
        )


class Asset(models.Model):
    """Cryptocurrency/token metadata"""

    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    chain = models.CharField(max_length=20, choices=Chain.choices)
    contract_address = models.CharField(max_length=100, blank=True)
    decimals = models.IntegerField(default=18)
    current_price_usd = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("symbol", "chain")
        indexes = [
            models.Index(fields=["symbol", "chain"]),
        ]

    def __str__(self):
        return f"{self.symbol} ({self.get_chain_display()})"


# Cache models
class PortfolioCache(models.Model):
    """Cache for expensive portfolio calculations"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cache_key = models.CharField(max_length=100)
    data = models.JSONField()
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "cache_key")
        indexes = [
            models.Index(fields=["user", "cache_key"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Cache: {self.cache_key} for {self.user.email}"


class PriceCache(models.Model):
    """Cache for asset prices from external APIs"""

    symbol = models.CharField(max_length=20, unique=True)
    price_data = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["symbol", "-last_updated"])]

    def __str__(self):
        return f"Price: {self.symbol} @ {self.last_updated}"
