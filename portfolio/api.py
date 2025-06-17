from typing import List, Optional

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from authentication.auth import AuthBearer
from wallets.models import Wallet

from .models import InvestigationCase, CaseWallet, InvestigationStatus, WalletCategory
from .services import PortfolioService
from .sse import portfolio_sse_stream

router = Router()


# Investigation Case Schemas
class InvestigationCaseSchema(Schema):
    id: int
    name: str
    description: str
    status: str
    priority: str
    wallet_count: int
    transaction_count: int
    notes: str
    created_at: str
    updated_at: str


class CreateInvestigationCaseSchema(Schema):
    name: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    notes: Optional[str] = ""


class UpdateInvestigationCaseSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class CaseWalletSchema(Schema):
    wallet_id: int
    address: str
    chain: str
    label: str
    category: str
    notes: str
    flagged: bool
    added_at: str


class AddWalletToCaseSchema(Schema):
    wallet_id: int
    category: Optional[str] = "unknown"
    notes: Optional[str] = ""
    flagged: Optional[bool] = False


# Legacy Portfolio Schemas (for backward compatibility)
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


# Investigation Case Management Endpoints

@router.get("/cases", auth=AuthBearer(), response=List[InvestigationCaseSchema])
def list_investigation_cases(request):
    """List all investigation cases for the authenticated user"""
    cases = InvestigationCase.objects.filter(investigator=request.user)
    return [
        {
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "status": case.status,
            "priority": case.priority,
            "wallet_count": case.wallet_count,
            "transaction_count": case.transaction_count,
            "notes": case.notes,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
        }
        for case in cases
    ]


@router.post("/cases", auth=AuthBearer(), response=InvestigationCaseSchema)
def create_investigation_case(request, data: CreateInvestigationCaseSchema):
    """Create a new investigation case"""
    case = InvestigationCase.objects.create(
        name=data.name,
        description=data.description,
        priority=data.priority,
        notes=data.notes,
        investigator=request.user,
    )
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "priority": case.priority,
        "wallet_count": case.wallet_count,
        "transaction_count": case.transaction_count,
        "notes": case.notes,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


@router.get("/cases/{case_id}", auth=AuthBearer(), response=InvestigationCaseSchema)
def get_investigation_case(request, case_id: int):
    """Get a specific investigation case"""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "priority": case.priority,
        "wallet_count": case.wallet_count,
        "transaction_count": case.transaction_count,
        "notes": case.notes,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


@router.put("/cases/{case_id}", auth=AuthBearer(), response=InvestigationCaseSchema)
def update_investigation_case(request, case_id: int, data: UpdateInvestigationCaseSchema):
    """Update an investigation case"""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(case, field, value)
    case.save()
    
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "priority": case.priority,
        "wallet_count": case.wallet_count,
        "transaction_count": case.transaction_count,
        "notes": case.notes,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


@router.delete("/cases/{case_id}", auth=AuthBearer())
def delete_investigation_case(request, case_id: int):
    """Delete an investigation case"""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case.delete()
    return {"success": True}


@router.get("/cases/{case_id}/wallets", auth=AuthBearer(), response=List[CaseWalletSchema])
def list_case_wallets(request, case_id: int):
    """List all wallets in a specific investigation case"""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case_wallets = CaseWallet.objects.filter(case=case).select_related('wallet')
    
    return [
        {
            "wallet_id": cw.wallet.id,
            "address": cw.wallet.address,
            "chain": cw.wallet.chain,
            "label": cw.wallet.label or cw.wallet.short_address,
            "category": cw.category,
            "notes": cw.notes,
            "flagged": cw.flagged,
            "added_at": cw.added_at.isoformat(),
        }
        for cw in case_wallets
    ]


@router.post("/cases/{case_id}/wallets", auth=AuthBearer(), response=CaseWalletSchema)
def add_wallet_to_case(request, case_id: int, data: AddWalletToCaseSchema):
    """Add a wallet to an investigation case"""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    wallet = get_object_or_404(Wallet, id=data.wallet_id, user=request.user)
    
    case_wallet, created = CaseWallet.objects.get_or_create(
        case=case,
        wallet=wallet,
        defaults={
            "category": data.category,
            "notes": data.notes,
            "flagged": data.flagged,
        }
    )
    
    if not created:
        # Update existing relationship
        case_wallet.category = data.category
        case_wallet.notes = data.notes
        case_wallet.flagged = data.flagged
        case_wallet.save()
    
    return {
        "wallet_id": wallet.id,
        "address": wallet.address,
        "chain": wallet.chain,
        "label": wallet.label or wallet.short_address,
        "category": case_wallet.category,
        "notes": case_wallet.notes,
        "flagged": case_wallet.flagged,
        "added_at": case_wallet.added_at.isoformat(),
    }


@router.delete("/cases/{case_id}/wallets/{wallet_id}", auth=AuthBearer())
def remove_wallet_from_case(request, case_id: int, wallet_id: int):
    """Remove a wallet from an investigation case"""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case_wallet = get_object_or_404(CaseWallet, case=case, wallet_id=wallet_id)
    case_wallet.delete()
    return {"success": True}


# Legacy Portfolio Endpoints (for backward compatibility)

@router.get("/summary", auth=AuthBearer(), response=PortfolioSummarySchema)
def portfolio_summary(request):
    """Get current portfolio summary (legacy endpoint)"""
    service = PortfolioService(request.user)
    return service.get_portfolio_summary()


@router.get("/history", auth=AuthBearer(), response=List[HistoricalDataPointSchema])
def portfolio_history(request, period: str = "24h"):
    """Get historical portfolio values (legacy endpoint)"""
    if period not in ["24h", "7d", "30d"]:
        period = "24h"

    service = PortfolioService(request.user)
    return service.get_historical_data(period)


@router.get("/wallets", auth=AuthBearer(), response=List[WalletBalanceSchema])
def wallet_balances(request):
    """Get individual wallet balances (legacy endpoint)"""
    service = PortfolioService(request.user)
    return service.get_wallet_balances()


@router.get("/stream")
def portfolio_stream(request):
    """SSE endpoint for real-time portfolio updates"""
    
    # Check if user is authenticated via Django session
    if not request.user.is_authenticated:
        from django.http import HttpResponse
        return HttpResponse("Unauthorized", status=401)

    def event_stream():
        """Generate SSE events"""
        for data in portfolio_sse_stream(request.user):
            yield f"data: {data}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Disable Nginx buffering

    return response
