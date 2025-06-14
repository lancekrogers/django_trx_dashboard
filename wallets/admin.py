from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Wallet


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""

    list_display = ("email", "username", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active", "created_at")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-created_at",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("created_at",)}),
    )
    readonly_fields = ("created_at",)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin configuration for Wallet model"""

    list_display = (
        "user",
        "chain",
        "label",
        "address_short",
        "is_active",
        "created_at",
    )
    list_filter = ("chain", "is_active", "created_at")
    search_fields = ("address", "label", "user__email")
    ordering = ("-created_at",)

    def address_short(self, obj):
        """Display shortened address in admin list"""
        return f"{obj.address[:6]}...{obj.address[-4:]}"

    address_short.short_description = "Address"
