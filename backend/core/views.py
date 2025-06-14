"""
HTMX-aware views for rendering HTML partials and handling form submissions.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q

from wallets.models import User, Wallet
from transactions.models import Transaction
from portfolio.services import PortfolioService


@require_http_methods(["GET", "POST"])
def htmx_login(request):
    """Handle login form display and submission."""
    if request.method == "GET":
        return render(request, "forms/login.html")
    
    # POST - Handle login
    username = request.POST.get("username")
    password = request.POST.get("password")
    
    if not username or not password:
        return render(request, "forms/login.html", {
            "error": "Username and password are required"
        }, status=400)
    
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # Return a redirect header for HTMX
        response = HttpResponse()
        response["HX-Redirect"] = "/dashboard"
        return response
    else:
        return render(request, "forms/login.html", {
            "error": "Invalid username or password",
            "username": username
        }, status=401)


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
        return render(request, "forms/add_wallet.html", {
            "errors": errors,
            "name": name,
            "chain": chain,
            "address": address
        }, status=400)
    
    # Check if wallet already exists
    if Wallet.objects.filter(user=request.user, address=address, chain=chain).exists():
        return render(request, "forms/add_wallet.html", {
            "error": "This wallet is already added to your account",
            "name": name,
            "chain": chain,
            "address": address
        }, status=400)
    
    try:
        # Create wallet
        wallet = Wallet.objects.create(
            user=request.user,
            name=name,
            chain=chain,
            address=address
        )
        
        # Return wallet item partial
        return render(request, "partials/wallet_item.html", {
            "wallet": wallet,
            "success": True
        })
    except Exception as e:
        return render(request, "forms/add_wallet.html", {
            "error": f"Failed to add wallet: {str(e)}",
            "name": name,
            "chain": chain,
            "address": address
        }, status=500)


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
        
        return render(request, "partials/portfolio_summary.html", {
            "summary": summary
        })
    else:
        # Full page request
        return render(request, "dashboard.html")


@login_required
@require_http_methods(["GET"])
def htmx_transactions(request):
    """Render paginated transaction table."""
    # Get filter parameters
    wallet_id = request.GET.get("wallet")
    tx_type = request.GET.get("type")
    search = request.GET.get("search")
    page = request.GET.get("page", 1)
    
    # Build query
    transactions = Transaction.objects.filter(wallet__user=request.user)
    
    if wallet_id:
        transactions = transactions.filter(wallet_id=wallet_id)
    
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    
    if search:
        transactions = transactions.filter(
            Q(hash__icontains=search) |
            Q(from_address__icontains=search) |
            Q(to_address__icontains=search)
        )
    
    # Order by timestamp
    transactions = transactions.order_by("-timestamp")
    
    # Paginate
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_obj = paginator.get_page(page)
    
    # Return table rows only if this is an HTMX request
    if request.htmx and request.GET.get("page"):
        # Just return the rows for pagination
        return render(request, "partials/transaction_rows.html", {
            "transactions": page_obj
        })
    
    # Return full table
    return render(request, "partials/transaction_table.html", {
        "transactions": page_obj,
        "wallets": Wallet.objects.filter(user=request.user)
    })


@login_required 
@require_http_methods(["GET"])
def htmx_wallets(request):
    """Render wallet list."""
    wallets = Wallet.objects.filter(user=request.user)
    
    return render(request, "partials/wallet_list.html", {
        "wallets": wallets
    })


@login_required
def htmx_dashboard(request):
    """Main dashboard view that uses HTMX partials."""
    return render(request, "dashboard.html")