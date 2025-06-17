"""
HTMX-aware views for rendering HTML partials and handling form submissions.
"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event
from django.utils import timezone
from datetime import timedelta, datetime
import random

from portfolio.services import PortfolioService
from portfolio.models import InvestigationCase, CaseWallet, InvestigationStatus, WalletCategory
from transactions.models import Transaction
from wallets.models import User, UserSettings, Wallet


@require_http_methods(["GET", "POST"])
def htmx_login(request):
    """Handle login form display and submission."""
    if request.method == "GET":
        return render(request, "forms/login.html")

    # POST - Handle login
    username = request.POST.get("username")
    password = request.POST.get("password")

    if not username or not password:
        return render(
            request,
            "forms/login.html",
            {"error": "Username and password are required"},
            status=400,
        )

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # For HTMX requests, return the dashboard partial
        if request.htmx:
            # Get dashboard data for the partial
            wallets = Wallet.objects.filter(user=user)
            recent_transactions = Transaction.objects.filter(
                wallet__user=user
            ).order_by("-timestamp")[:5]
            service = PortfolioService(user)
            summary = service.get_portfolio_summary()
            
            # Get historical data for chart (7 days)
            historical_data = service.get_historical_data("7d")
            
            # Format chart data for the template
            if historical_data:
                chart_labels = []
                chart_values = []
                for point in historical_data:
                    # Format date label
                    dt = datetime.fromisoformat(point["timestamp"].replace('Z', '+00:00'))
                    chart_labels.append(dt.strftime("%b %d"))
                    chart_values.append(point["total_value_usd"])
                summary["chart_labels"] = chart_labels
                summary["chart_values"] = chart_values
                summary["chart_data"] = ",".join(str(v) for v in chart_values)
            else:
                # Default data if no historical data
                summary["chart_labels"] = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
                summary["chart_values"] = [0, 0, 0, 0, 0, 0, 0]
                summary["chart_data"] = "0,0,0,0,0,0,0"
            
            # Format asset distribution for the template
            if summary.get("asset_labels") and summary.get("asset_values"):
                assets = []
                total_value = sum(summary["asset_values"])
                for label, value in zip(summary["asset_labels"], summary["asset_values"]):
                    percentage = (value / total_value * 100) if total_value > 0 else 0
                    assets.append({
                        "symbol": label,
                        "value": value,
                        "percentage": percentage,
                        "color": None  # Will use default colors from template
                    })
                summary["assets"] = assets
            else:
                summary["assets"] = []
            
            # Additional summary fields
            summary["total_value"] = summary.get("total_value_usd", 0)
            summary["percent_change_24h"] = summary.get("change_24h", 0)
            summary["value_change_24h"] = summary["total_value"] * summary["percent_change_24h"] / 100 if summary["percent_change_24h"] else 0
            summary["total_assets"] = summary.get("asset_count", 0)
            summary["volume_24h"] = random.uniform(1000, 5000) if service.mock_data_enabled else 0  # Mock 24h volume
            
            context = {
                "wallets": wallets,
                "recent_transactions": recent_transactions,
                "summary": summary,
            }
            
            response = render(request, "partials/dashboard_content.html", context)
        else:
            # For non-HTMX requests, return full dashboard page
            response = render(request, "dashboard.html")
        response["X-Auth-Status"] = "authenticated"
        # Use django-htmx helper to trigger client event
        trigger_client_event(response, "auth-change")
        return response
    else:
        return render(
            request,
            "forms/login.html",
            {"error": "Invalid username or password", "username": username},
            status=401,
        )


@login_required
@require_http_methods(["GET", "POST"])
def htmx_add_wallet(request):
    """Handle add wallet form display and submission."""
    if request.method == "GET":
        return render(request, "forms/add_wallet.html")

    # POST - Handle wallet creation
    label = request.POST.get("name")  # Form uses 'name' but model uses 'label'
    chain = request.POST.get("chain")
    address = request.POST.get("address")

    # Validate inputs
    errors = {}
    if not label:
        errors["name"] = "Name is required"
    if not chain:
        errors["chain"] = "Chain is required"
    if not address:
        errors["address"] = "Address is required"

    if errors:
        return render(
            request,
            "forms/add_wallet.html",
            {"errors": errors, "name": label, "chain": chain, "address": address},
            status=400,
        )

    # Check if wallet already exists
    if Wallet.objects.filter(user=request.user, address=address, chain=chain).exists():
        return render(
            request,
            "forms/add_wallet.html",
            {
                "error": "This wallet is already added",
                "name": label,
                "chain": chain,
                "address": address,
            },
            status=400,
        )

    try:
        # Create wallet
        wallet = Wallet.objects.create(
            user=request.user, label=label, chain=chain, address=address
        )

        # Return wallet item partial
        return render(
            request, "partials/wallet_item.html", {"wallet": wallet, "success": True}
        )
    except Exception as e:
        return render(
            request,
            "forms/add_wallet.html",
            {
                "error": f"Failed to add wallet: {str(e)}",
                "name": label,
                "chain": chain,
                "address": address,
            },
            status=500,
        )


@login_required
@require_http_methods(["DELETE"])
def htmx_delete_wallet(request, wallet_id):
    """Handle wallet deletion."""
    wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user)
    wallet.delete()

    # Return empty response to remove the element
    return HttpResponse("")


@login_required
@require_http_methods(["GET"])
def htmx_portfolio_summary(request):
    """Render portfolio summary partial."""
    # Get portfolio data
    service = PortfolioService(request.user)
    summary = service.get_portfolio_summary()

    # Check if this is an HTMX request
    if request.htmx:
        return render(request, "partials/portfolio_summary.html", {"summary": summary})
    else:
        # For non-HTMX requests, return a full page with the portfolio summary
        return render(request, "dashboard.html", {"summary": summary})


@login_required
@require_http_methods(["GET"])
def htmx_transactions(request):
    """Render transactions page or table partial."""
    # Get filter parameters
    wallet_id = request.GET.get("wallet")
    tx_type = request.GET.get("type")
    search = request.GET.get("search")
    page = request.GET.get("page", 1)

    # Check user's mock data setting (create if it doesn't exist)
    settings, created = UserSettings.objects.get_or_create(
        user=request.user,
        defaults={'mock_data_enabled': False}
    )
    mock_data_enabled = settings.mock_data_enabled

    # Build query - only show transactions if mock data is enabled
    if mock_data_enabled:
        transactions = Transaction.objects.filter(wallet__user=request.user)
    else:
        # In real mode, show empty transaction list since we don't have real blockchain adapters
        transactions = Transaction.objects.none()

    if wallet_id:
        transactions = transactions.filter(wallet_id=wallet_id)

    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)

    if search:
        transactions = transactions.filter(
            Q(tx_hash__icontains=search)
        )

    # Order by timestamp
    transactions = transactions.order_by("-timestamp")

    # Paginate
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_obj = paginator.get_page(page)

    # Get all user wallets for filter dropdown
    wallets = Wallet.objects.filter(user=request.user)

    # Check if this is an HTMX request using django-htmx
    is_htmx = request.htmx
    hx_target = request.headers.get("HX-Target", "") if is_htmx else ""
    
    # Return table rows only if this is a pagination request targeting the rows
    if (
        is_htmx
        and request.GET.get("page")
        and (hx_target == "transaction-rows" or hx_target == "transactions-table" or hx_target == "")
        and not any([wallet_id, tx_type, search])  # Not a filter request
    ):
        # Just return the rows for pagination
        return render(
            request, "partials/transaction_rows.html", {"transactions": page_obj}
        )

    # Check if this is a filter request (has filter params but not initial page load)
    if (
        is_htmx
        and any([wallet_id, tx_type, search])
        and hx_target == "transactions-table"
    ):
        # Return just the table for filter updates
        return render(
            request,
            "partials/transaction_table.html",
            {"transactions": page_obj, "wallets": wallets},
        )

    # Return full page
    return render(
        request,
        "partials/transactions_page.html",
        {"transactions": page_obj, "wallets": wallets},
    )


@login_required
@require_http_methods(["GET"])
def htmx_wallets(request):
    """Render wallets page."""
    wallets = Wallet.objects.filter(user=request.user)
    
    return render(request, "partials/wallets_page.html", {"wallets": wallets})


@login_required
def htmx_dashboard(request):
    """Main dashboard view - now shows investigation cases."""
    # Get investigation stats
    active_cases = InvestigationCase.objects.filter(
        investigator=request.user, 
        status=InvestigationStatus.ACTIVE
    )
    critical_cases = InvestigationCase.objects.filter(
        investigator=request.user,
        priority="critical"
    )
    
    # Get total wallets across all cases
    total_wallets = Wallet.objects.filter(user=request.user).count()
    
    # Get total transactions
    total_transactions = Transaction.objects.filter(
        wallet__user=request.user
    ).count()
    
    context = {
        "active_cases_count": active_cases.count(),
        "critical_cases_count": critical_cases.count(),
        "total_wallets_count": total_wallets,
        "total_transactions_count": total_transactions,
    }
    
    # Return partial for HTMX requests, full page otherwise
    if request.htmx:
        return render(request, "partials/investigation_cases.html", context)
    
    return render(request, "dashboard.html", context)


def home_view(request):
    """Root view - single page app container."""
    return render(request, "app.html")


def htmx_welcome(request):
    """Welcome page content for unauthenticated users."""
    return render(request, "partials/welcome.html")


def htmx_nav_authenticated(request):
    """Navigation for authenticated users."""
    return render(request, "partials/nav_authenticated.html")


def htmx_nav_unauthenticated(request):
    """Navigation for unauthenticated users."""
    return render(request, "partials/nav_unauthenticated.html")


@login_required
@require_http_methods(["GET", "POST"])
def htmx_settings(request):
    """Handle settings display and updates."""
    # Get or create user settings
    settings, created = UserSettings.objects.get_or_create(
        user=request.user, defaults={"mock_data_enabled": True}
    )

    if request.method == "GET":
        return render(request, "partials/settings_page.html", {"settings": settings})

    # POST - Handle settings update
    mock_data_enabled = request.POST.get("mock_data_enabled") == "on"
    
    settings.mock_data_enabled = mock_data_enabled
    settings.save()

    # Return updated settings page with success message
    return render(
        request,
        "partials/settings_page.html",
        {"settings": settings, "success": "Settings updated successfully!"},
    )


@require_http_methods(["POST"])
def htmx_logout(request):
    """Handle logout and return welcome content."""
    from django.contrib.auth import logout

    logout(request)
    response = render(request, "partials/welcome.html")
    response["X-Auth-Status"] = "unauthenticated"
    # Use django-htmx helper to trigger client event
    trigger_client_event(response, "auth-change")
    return response


@login_required
@require_http_methods(["POST"])
def htmx_refresh_mock_data(request):
    """Refresh mock data by updating all transaction dates to be recent."""
    # Check if user has mock data enabled
    try:
        settings = UserSettings.objects.get(user=request.user)
        if not settings.mock_data_enabled:
            return render(
                request,
                "partials/settings_page.html",
                {"settings": settings, "error": "Mock data is not enabled"},
            )
    except UserSettings.DoesNotExist:
        return render(
            request,
            "partials/settings_page.html",
            {"error": "User settings not found"},
        )
    
    # Get all user's transactions
    transactions = Transaction.objects.filter(wallet__user=request.user)
    
    if not transactions.exists():
        # No transactions to update - create new mock data
        from authentication.signals import create_assets, create_wallets, create_transactions
        
        # Create assets if they don't exist
        assets = create_assets()
        
        # Get or create wallets
        wallets = create_wallets(request.user)
        
        # Create new transactions
        for wallet in wallets:
            create_transactions(wallet, assets[wallet.chain], 50)
    else:
        # Update existing transactions to have recent dates
        # Calculate date range for the last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get all transactions ordered by timestamp
        transactions = transactions.order_by('timestamp')
        total_transactions = transactions.count()
        
        # Calculate time interval between transactions
        if total_transactions > 1:
            time_interval = (end_date - start_date) / (total_transactions - 1)
        else:
            time_interval = timedelta(hours=1)
        
        # Update each transaction with a new timestamp
        for i, transaction in enumerate(transactions):
            new_timestamp = start_date + (time_interval * i)
            transaction.timestamp = new_timestamp
            transaction.save(update_fields=['timestamp'])
    
    # Return updated settings page with success message
    return render(
        request,
        "partials/settings_page.html",
        {"settings": settings, "success": "Mock data has been refreshed with recent dates!"},
    )
