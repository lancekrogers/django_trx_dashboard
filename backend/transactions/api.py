from ninja import Router, Schema, Query
from ninja.pagination import paginate, PageNumberPagination
from typing import List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from authentication.auth import AuthBearer
from .models import Transaction, TransactionType

router = Router()


class TransactionSchema(Schema):
    id: int
    tx_hash: str
    wallet_id: int
    wallet_address: str
    wallet_chain: str
    block_number: int
    timestamp: datetime
    transaction_type: str
    amount: str  # String to preserve decimal precision
    asset_symbol: str
    gas_fee: str
    usd_value: Optional[float] = None
    
    @staticmethod
    def resolve_wallet_address(obj):
        return obj.wallet.address
    
    @staticmethod
    def resolve_wallet_chain(obj):
        return obj.wallet.chain
    
    @staticmethod
    def resolve_amount(obj):
        return str(obj.amount)
    
    @staticmethod
    def resolve_gas_fee(obj):
        return str(obj.gas_fee)


class TransactionFilterSchema(Schema):
    type: Optional[str] = None  # buy|sell|transfer
    period: Optional[str] = "all"  # 24h|7d|30d|all
    wallet_id: Optional[int] = None
    asset_symbol: Optional[str] = None


class ErrorSchema(Schema):
    error: str


@router.get("/", auth=AuthBearer(), response=List[TransactionSchema])
@paginate(PageNumberPagination)
def list_transactions(request, filters: TransactionFilterSchema = Query(...)):
    """List transactions with filtering and pagination"""
    # Base queryset - only transactions for user's wallets
    qs = Transaction.objects.filter(
        wallet__user=request.user,
        wallet__is_active=True
    ).select_related('wallet')
    
    # Apply filters
    if filters.type and filters.type in [t[0] for t in TransactionType.choices]:
        qs = qs.filter(transaction_type=filters.type)
    
    if filters.wallet_id:
        qs = qs.filter(wallet_id=filters.wallet_id)
    
    if filters.asset_symbol:
        qs = qs.filter(asset_symbol__iexact=filters.asset_symbol)
    
    # Period filter
    if filters.period and filters.period != 'all':
        period_map = {
            '24h': timedelta(days=1),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30),
        }
        if filters.period in period_map:
            cutoff_time = timezone.now() - period_map[filters.period]
            qs = qs.filter(timestamp__gte=cutoff_time)
    
    return qs


@router.get("/{transaction_id}/", auth=AuthBearer(), response={200: TransactionSchema, 404: ErrorSchema})
def get_transaction(request, transaction_id: int):
    """Get transaction details"""
    try:
        transaction = Transaction.objects.select_related('wallet').get(
            id=transaction_id,
            wallet__user=request.user
        )
        return 200, transaction
    except Transaction.DoesNotExist:
        return 404, {"error": "Transaction not found"}


class TransactionStatsSchema(Schema):
    total_transactions: int
    total_volume_usd: float
    transactions_24h: int
    most_traded_asset: Optional[str] = None


@router.get("/stats", auth=AuthBearer(), response=TransactionStatsSchema)
def transaction_stats(request):
    """Get transaction statistics for the user"""
    from django.db.models import Count, Sum
    
    user_transactions = Transaction.objects.filter(
        wallet__user=request.user,
        wallet__is_active=True
    )
    
    # Calculate stats
    total = user_transactions.count()
    total_volume = user_transactions.aggregate(
        total=Sum('usd_value')
    )['total'] or 0
    
    # 24h transactions
    cutoff_24h = timezone.now() - timedelta(days=1)
    transactions_24h = user_transactions.filter(
        timestamp__gte=cutoff_24h
    ).count()
    
    # Most traded asset
    asset_counts = user_transactions.values('asset_symbol').annotate(
        count=Count('id')
    ).order_by('-count')
    
    most_traded = asset_counts.first()['asset_symbol'] if asset_counts else None
    
    return {
        'total_transactions': total,
        'total_volume_usd': float(total_volume),
        'transactions_24h': transactions_24h,
        'most_traded_asset': most_traded
    }