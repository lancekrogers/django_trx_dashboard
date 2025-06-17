from django.db import models
from wallets.models import User, Wallet


class InvestigationStatus(models.TextChoices):
    """Status options for investigation cases"""
    
    ACTIVE = "active", "Active"
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class InvestigationCase(models.Model):
    """Investigation case for tracking multiple wallets and transactions"""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    investigator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="investigation_cases"
    )
    wallets = models.ManyToManyField(
        Wallet, 
        through="CaseWallet", 
        related_name="investigation_cases"
    )
    status = models.CharField(
        max_length=20, 
        choices=InvestigationStatus.choices, 
        default=InvestigationStatus.ACTIVE
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"), 
            ("high", "High"),
            ("critical", "Critical")
        ],
        default="medium"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["investigator", "status"]),
            models.Index(fields=["status", "-updated_at"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def wallet_count(self):
        """Number of wallets in this case"""
        return self.wallets.count()
    
    @property 
    def transaction_count(self):
        """Total transactions across all wallets in this case"""
        from transactions.models import Transaction
        wallet_ids = self.wallets.values_list('id', flat=True)
        return Transaction.objects.filter(wallet_id__in=wallet_ids).count()


class WalletCategory(models.TextChoices):
    """Categories for wallet roles in investigations"""
    
    SUSPECT = "suspect", "Suspect"
    VICTIM = "victim", "Victim"
    EXCHANGE = "exchange", "Exchange"
    MIXER = "mixer", "Mixer"
    UNKNOWN = "unknown", "Unknown"
    EVIDENCE = "evidence", "Evidence"


class CaseWallet(models.Model):
    """Through model for investigation case to wallet relationship with additional metadata"""
    
    case = models.ForeignKey(InvestigationCase, on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    category = models.CharField(
        max_length=20,
        choices=WalletCategory.choices,
        default=WalletCategory.UNKNOWN
    )
    notes = models.TextField(blank=True)
    flagged = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("case", "wallet")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["case", "category"]),
            models.Index(fields=["flagged", "-added_at"]),
        ]
    
    def __str__(self):
        return f"{self.wallet.short_address} in {self.case.name} ({self.get_category_display()})"