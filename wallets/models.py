from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager that uses email instead of username"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        # Set username to email if not provided
        extra_fields.setdefault("username", email)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with email as the primary identifier"""

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Chain(models.TextChoices):
    """Supported blockchain networks"""

    ETHEREUM = "ethereum", "Ethereum"
    SOLANA = "solana", "Solana"
    BITCOIN = "bitcoin", "Bitcoin"


class Wallet(models.Model):
    """User wallet for tracking blockchain addresses"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    address = models.CharField(max_length=100)
    chain = models.CharField(max_length=20, choices=Chain.choices)
    label = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "address", "chain")
        indexes = [
            models.Index(fields=["user", "chain"]),
            models.Index(fields=["address", "chain"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.label or self.address[:10]}... ({self.get_chain_display()})"
