from typing import List

from django.http import StreamingHttpResponse
from ninja import Router, Schema

from authentication.auth import AuthBearer

from .services import PortfolioService
from .sse import portfolio_sse_stream

router = Router()


class PortfolioSummarySchema(Schema):
    total_value_usd: float
    change_24h: float
    wallet_count: int
    last_updated: str


class HistoricalDataPointSchema(Schema):
    timestamp: str
    total_value_usd: float


class WalletBalanceSchema(Schema):
    wallet_id: int
    address: str
    chain: str
    label: str
    value_usd: float
    last_updated: str


class ErrorSchema(Schema):
    error: str


@router.get("/summary", auth=AuthBearer(), response=PortfolioSummarySchema)
def portfolio_summary(request):
    """Get current portfolio summary"""
    service = PortfolioService(request.user)
    return service.get_portfolio_summary()


@router.get("/history", auth=AuthBearer(), response=List[HistoricalDataPointSchema])
def portfolio_history(request, period: str = "24h"):
    """Get historical portfolio values

    Args:
        period: Time period (24h, 7d, 30d)
    """
    if period not in ["24h", "7d", "30d"]:
        period = "24h"

    service = PortfolioService(request.user)
    return service.get_historical_data(period)


@router.get("/wallets", auth=AuthBearer(), response=List[WalletBalanceSchema])
def wallet_balances(request):
    """Get individual wallet balances"""
    service = PortfolioService(request.user)
    return service.get_wallet_balances()


@router.get("/stream", auth=AuthBearer())
def portfolio_stream(request):
    """SSE endpoint for real-time portfolio updates"""

    def event_stream():
        """Generate SSE events"""
        for data in portfolio_sse_stream(request.user):
            yield f"data: {data}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    response["X-Accel-Buffering"] = "no"  # Disable Nginx buffering

    return response


# Mock endpoint for development
@router.get("/mock", response=PortfolioSummarySchema)
def mock_portfolio_summary(request):
    """Mock portfolio summary for frontend development"""
    import random

    from django.utils import timezone

    return {
        "total_value_usd": round(random.uniform(10000, 50000), 2),
        "change_24h": round(random.uniform(-10, 10), 2),
        "wallet_count": 3,
        "last_updated": timezone.now().isoformat(),
    }
