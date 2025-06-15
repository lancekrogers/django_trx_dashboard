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

from portfolio.services import PortfolioService
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
        # Return dashboard content and signal auth status
        response = render(request, "dashboard.html")
        response["X-Auth-Status"] = "authenticated"
        response["HX-Trigger"] = "auth-change"
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
    name = request.POST.get("name")
    chain = request.POST.get("chain")
    address = request.POST.get("address")

    # Validate inputs
    errors = {}
    if not name:
        errors["name"] = "Name is required"
    if not chain:
        errors["chain"] = "Chain is required"
    if not address:
        errors["address"] = "Address is required"

    if errors:
        return render(
            request,
            "forms/add_wallet.html",
            {"errors": errors, "name": name, "chain": chain, "address": address},
            status=400,
        )

    # Check if wallet already exists
    if Wallet.objects.filter(user=request.user, address=address, chain=chain).exists():
        return render(
            request,
            "forms/add_wallet.html",
            {
                "error": "This wallet is already added to your account",
                "name": name,
                "chain": chain,
                "address": address,
            },
            status=400,
        )

    try:
        # Create wallet
        wallet = Wallet.objects.create(
            user=request.user, name=name, chain=chain, address=address
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
                "name": name,
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
    if request.htmx:
        # Get portfolio data
        service = PortfolioService(request.user)
        summary = service.get_portfolio_summary()

        return render(request, "partials/portfolio_summary.html", {"summary": summary})
    else:
        # Full page request
        return render(request, "dashboard.html")


@login_required
@require_http_methods(["GET"])
def htmx_transactions(request):
    """Render transactions page or table partial."""
    # Get filter parameters
    wallet_id = request.GET.get("wallet")
    tx_type = request.GET.get("type")
    search = request.GET.get("search")
    page = request.GET.get("page", 1)

    # Check user's mock data setting
    try:
        settings = UserSettings.objects.get(user=request.user)
        mock_data_enabled = settings.mock_data_enabled
    except UserSettings.DoesNotExist:
        mock_data_enabled = False

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
            Q(hash__icontains=search)
            | Q(from_address__icontains=search)
            | Q(to_address__icontains=search)
        )

    # Order by timestamp
    transactions = transactions.order_by("-timestamp")

    # Paginate
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_obj = paginator.get_page(page)

    # Get all user wallets for filter dropdown
    wallets = Wallet.objects.filter(user=request.user)

    # Return table rows only if this is a pagination request
    if request.htmx and request.GET.get("page") and not request.headers.get("HX-Target") == "main-content":
        # Just return the rows for pagination
        return render(
            request, "partials/transaction_rows.html", {"transactions": page_obj}
        )

    # Check if this is a filter request (has filter params but not initial page load)
    if request.htmx and any([wallet_id, tx_type, search]) and request.headers.get("HX-Target") == "transactions-table":
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


def htmx_dashboard(request):
    """Main dashboard view that uses HTMX partials."""
    return render(request, "dashboard.html")


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
        user=request.user, defaults={"mock_data_enabled": False}
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
    return response
