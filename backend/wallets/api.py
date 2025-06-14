from ninja import Router, Schema
from typing import List, Optional
from datetime import datetime
from django.shortcuts import get_object_or_404
from authentication.auth import AuthBearer
from .models import Wallet, Chain

router = Router()


class WalletCreateSchema(Schema):
    address: str
    chain: str  # ethereum|solana|bitcoin
    label: Optional[str] = None


class WalletSchema(Schema):
    id: int
    address: str
    chain: str
    label: str
    is_active: bool
    created_at: datetime
    
    @staticmethod
    def resolve_label(obj):
        return obj.label or f"{obj.address[:6]}...{obj.address[-4:]}"


class ErrorSchema(Schema):
    error: str


@router.get("/", auth=AuthBearer(), response=List[WalletSchema])
def list_wallets(request):
    """List all wallets for the authenticated user"""
    return request.user.wallets.filter(is_active=True)


@router.post("/", auth=AuthBearer(), response={201: WalletSchema, 400: ErrorSchema})
def create_wallet(request, data: WalletCreateSchema):
    """Add a new wallet address"""
    # Validate chain
    if data.chain not in [choice[0] for choice in Chain.choices]:
        return 400, {"error": f"Invalid chain. Must be one of: {', '.join([c[0] for c in Chain.choices])}"}
    
    # Check if wallet already exists for this user
    if request.user.wallets.filter(address=data.address, chain=data.chain).exists():
        return 400, {"error": "This wallet address is already added"}
    
    # Create wallet
    wallet = Wallet.objects.create(
        user=request.user,
        address=data.address,
        chain=data.chain,
        label=data.label or ""
    )
    
    return 201, wallet


@router.get("/{wallet_id}/", auth=AuthBearer(), response={200: WalletSchema, 404: ErrorSchema})
def get_wallet(request, wallet_id: int):
    """Get wallet details"""
    try:
        wallet = request.user.wallets.get(id=wallet_id, is_active=True)
        return 200, wallet
    except Wallet.DoesNotExist:
        return 404, {"error": "Wallet not found"}


@router.delete("/{wallet_id}/", auth=AuthBearer(), response={204: None, 404: ErrorSchema})
def delete_wallet(request, wallet_id: int):
    """Soft delete a wallet"""
    try:
        wallet = request.user.wallets.get(id=wallet_id, is_active=True)
        wallet.is_active = False
        wallet.save()
        return 204, None
    except Wallet.DoesNotExist:
        return 404, {"error": "Wallet not found"}


class WalletUpdateSchema(Schema):
    label: Optional[str] = None


@router.patch("/{wallet_id}/", auth=AuthBearer(), response={200: WalletSchema, 404: ErrorSchema})
def update_wallet(request, wallet_id: int, data: WalletUpdateSchema):
    """Update wallet label"""
    try:
        wallet = request.user.wallets.get(id=wallet_id, is_active=True)
        if data.label is not None:
            wallet.label = data.label
            wallet.save()
        return 200, wallet
    except Wallet.DoesNotExist:
        return 404, {"error": "Wallet not found"}