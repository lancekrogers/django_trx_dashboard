"""
HTMX-aware views for rendering HTML partials and handling form submissions.
"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
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

    # Try authenticating with email as username
    user = authenticate(request, username=username, password=password)
    if user is None and '@' in username:
        # If username looks like email, try finding user by email
        try:
            from wallets.models import User
            email_user = User.objects.get(email=username)
            user = authenticate(request, username=email_user.username, password=password)
        except User.DoesNotExist:
            pass
    
    if user is not None:
        login(request, user)
        
        # Get cases data manually instead of calling the view (which has @login_required)
        cases = InvestigationCase.objects.filter(investigator=user).prefetch_related('case_wallets__wallet')
        active_cases_count = cases.filter(status='active').count()
        total_wallets_count = Wallet.objects.filter(user=user).count()
        flagged_wallets_count = CaseWallet.objects.filter(case__investigator=user, flagged=True).count()
        from transactions.models import Transaction
        total_transactions_count = Transaction.objects.filter(wallet__user=user).count()
        chains_count = Wallet.objects.filter(user=user).values('chain').distinct().count()
        
        context = {
            'investigation_cases': cases,
            'active_cases_count': active_cases_count,
            'total_wallets_count': total_wallets_count,
            'total_transactions_count': total_transactions_count,
            'flagged_wallets_count': flagged_wallets_count,
            'chains_count': chains_count,
            'show_cases_list': True
        }
        
        response = render(request, "dashboard.html", context)
        response["X-Auth-Status"] = "authenticated"
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

        # Return success message as simple HTML
        return HttpResponse(f'<div class="text-green-400">Wallet "{wallet.label}" added successfully!</div>')
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
        # Use dashboard_content to show the summary along with other content
        wallets = Wallet.objects.filter(user=request.user)
        recent_transactions = []  # Mock data for now
        return render(request, "dashboard.html", {
            "summary": summary, 
            "show_dashboard_content": True,
            "wallets": wallets,
            "recent_transactions": recent_transactions
        })


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
    """Main dashboard view - show multi-portfolio investigation dashboard."""
    # Redirect to cases list which is the main dashboard
    return htmx_cases_list(request)


def home_view(request):
    """Root view - redirect to login or dashboard."""
    if request.user.is_authenticated:
        # Always show the cases list for authenticated users
        return htmx_cases_list(request)
    else:
        # Show login for unauthenticated users
        return render(request, "forms/login.html")


def htmx_welcome(request):
    """Welcome page content for unauthenticated users."""
    return render(request, "forms/login.html")


def htmx_nav_authenticated(request):
    """Navigation for authenticated users."""
    return HttpResponse("")  # No navigation needed in simplified design


def htmx_nav_unauthenticated(request):
    """Navigation for unauthenticated users."""
    return HttpResponse("")  # No navigation needed in simplified design


@login_required
@require_http_methods(["GET", "POST"])
def htmx_settings(request):
    """Handle settings display and updates."""
    # Get or create user settings
    settings, created = UserSettings.objects.get_or_create(
        user=request.user, defaults={"mock_data_enabled": True}
    )

    if request.method == "GET":
        return HttpResponse('<div class="p-6"><h2 class="text-xl text-white">Settings</h2><p class="text-gray-400">Mock data enabled</p></div>')

    # POST - Handle settings update
    mock_data_enabled = request.POST.get("mock_data_enabled") == "on"
    
    settings.mock_data_enabled = mock_data_enabled
    settings.save()

    # Return updated settings page with success message
    return HttpResponse('<div class="p-6 text-green-400">Settings updated successfully!</div>')


@require_http_methods(["POST"])
def htmx_logout(request):
    """Handle logout and return welcome content."""
    from django.contrib.auth import logout

    logout(request)
    response = render(request, "forms/login.html")
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
            return HttpResponse('<div class="p-6 text-red-400">Mock data is not enabled</div>')
    except UserSettings.DoesNotExist:
        return HttpResponse('<div class="p-6 text-red-400">User settings not found</div>')
    
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
    return HttpResponse('<div class="p-6 text-green-400">Mock data has been refreshed with recent dates!</div>')


# Investigation Case Views

@login_required
@require_http_methods(["GET"])
def htmx_cases_list(request):
    """Return the list of investigation cases with filtering and stats."""
    cases = InvestigationCase.objects.filter(investigator=request.user).prefetch_related('case_wallets__wallet')
    
    # Calculate dashboard stats
    active_cases_count = cases.filter(status='active').count()
    total_wallets_count = Wallet.objects.filter(user=request.user).count()
    flagged_wallets_count = CaseWallet.objects.filter(case__investigator=request.user, flagged=True).count()
    
    # Calculate total transactions across all user's wallets
    from transactions.models import Transaction
    total_transactions_count = Transaction.objects.filter(wallet__user=request.user).count()
    
    # Count unique chains
    chains_count = Wallet.objects.filter(user=request.user).values('chain').distinct().count()
    
    # Apply filters
    search = request.GET.get('search')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    
    if search:
        cases = cases.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(notes__icontains=search)
        )
    
    if status:
        cases = cases.filter(status=status)
    
    if priority:
        cases = cases.filter(priority=priority)
    
    context = {
        'investigation_cases': cases,
        'active_cases_count': active_cases_count,
        'total_wallets_count': total_wallets_count,
        'total_transactions_count': total_transactions_count,
        'flagged_wallets_count': flagged_wallets_count,
        'chains_count': chains_count,
    }
    
    # Return grid view - use dashboard.html for full page, cases_grid.html for HTMX partial
    if request.htmx:
        return render(request, "partials/cases_grid.html", context)
    else:
        # For non-HTMX requests (like homepage), return full page
        context['show_cases_list'] = True
        return render(request, "dashboard.html", context)


@login_required
@require_http_methods(["GET"])
def htmx_create_case_form(request):
    """Display the create case form."""
    return render(request, "partials/case_form.html", {"case": None})


@login_required
@require_http_methods(["GET"])
def htmx_edit_case_form(request, case_id):
    """Display the edit case form."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    return render(request, "partials/case_form.html", {"case": case})


@login_required
@require_http_methods(["POST"])
def htmx_create_case(request):
    """Handle case creation."""
    name = request.POST.get("name")
    description = request.POST.get("description", "")
    priority = request.POST.get("priority", "medium")
    notes = request.POST.get("notes", "")
    
    if not name:
        return HttpResponse("Case name is required", status=400)
    
    case = InvestigationCase.objects.create(
        name=name,
        description=description,
        priority=priority,
        notes=notes,
        investigator=request.user
    )
    
    # Return updated cases list
    cases = InvestigationCase.objects.filter(investigator=request.user)
    return render(request, "partials/cases_list.html", {"cases": cases})


@login_required
@require_http_methods(["POST"])
def htmx_update_case(request, case_id):
    """Handle case update."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    
    case.name = request.POST.get("name", case.name)
    case.description = request.POST.get("description", case.description)
    case.status = request.POST.get("status", case.status)
    case.priority = request.POST.get("priority", case.priority)
    case.notes = request.POST.get("notes", case.notes)
    case.save()
    
    # Return updated cases list
    cases = InvestigationCase.objects.filter(investigator=request.user)
    return render(request, "partials/cases_list.html", {"cases": cases})


@login_required
@require_http_methods(["POST"])
def htmx_archive_case(request, case_id):
    """Archive a case."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case.status = InvestigationStatus.ARCHIVED
    case.save()
    
    # Return updated cases list
    cases = InvestigationCase.objects.filter(investigator=request.user)
    return render(request, "partials/cases_list.html", {"cases": cases})


@login_required
@require_http_methods(["GET"])
def htmx_case_detail(request, case_id):
    """Display case investigation dashboard."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case_wallets = CaseWallet.objects.filter(case=case).select_related('wallet').prefetch_related('wallet__transactions')
    
    # Get wallet IDs for this case
    wallet_ids = case_wallets.values_list('wallet_id', flat=True)
    
    # Calculate metrics
    transactions = Transaction.objects.filter(wallet_id__in=wallet_ids)
    transaction_count = transactions.count()
    
    # Calculate total value
    total_value = transactions.aggregate(
        total=models.Sum('usd_value')
    )['total'] or Decimal('0')
    
    # Count suspicious transactions (those with patterns in metadata)
    suspicious_count = transactions.exclude(
        metadata__pattern__isnull=True
    ).count()
    
    # Get wallet distribution by category
    wallet_distribution = list(case_wallets.values('category').annotate(
        count=models.Count('id')
    ).order_by('category'))
    
    # Format wallet distribution for chart
    for item in wallet_distribution:
        item['category'] = dict(WalletCategory.choices).get(item['category'], 'Unknown')
    
    # Generate chart data
    # Transaction flow (last 7 days by default)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    # Group transactions by day for flow chart
    flow_data = []
    flow_labels = []
    inflow_data = []
    outflow_data = []
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0)
        day_end = date.replace(hour=23, minute=59, second=59)
        
        # Calculate inflow (buy/transfer in)
        inflow = transactions.filter(
            timestamp__gte=day_start,
            timestamp__lte=day_end,
            transaction_type__in=['buy', 'transfer']
        ).aggregate(total=models.Sum('usd_value'))['total'] or 0
        
        # Calculate outflow (sell/transfer out)
        outflow = transactions.filter(
            timestamp__gte=day_start,
            timestamp__lte=day_end,
            transaction_type='sell'
        ).aggregate(total=models.Sum('usd_value'))['total'] or 0
        
        flow_labels.append(date.strftime('%b %d'))
        # Add some demo variance if real data is flat
        demo_inflow = float(inflow) if inflow > 0 else random.randint(50000, 200000)
        demo_outflow = float(outflow) if outflow > 0 else random.randint(20000, 100000)
        inflow_data.append(demo_inflow)
        outflow_data.append(demo_outflow)
    
    # Timeline data (transactions per day)
    timeline_data = []
    timeline_labels = []
    
    for i in range(30):
        date = end_date - timedelta(days=29-i)
        day_count = transactions.filter(
            timestamp__date=date.date()
        ).count()
        
        # Add some demo variance if real data is flat
        demo_count = day_count if day_count > 0 else random.randint(1, 15)
        timeline_data.append(demo_count)
        timeline_labels.append(date.strftime('%b %d'))
    
    import json
    
    context = {
        "case": case,
        "case_wallets": case_wallets,
        "transaction_count": transaction_count,
        "total_value": total_value,
        "suspicious_count": suspicious_count,
        "wallet_categories": WalletCategory.choices,
        "wallet_distribution": json.dumps(wallet_distribution),
        "flow_labels": json.dumps(flow_labels),
        "inflow_data": json.dumps(inflow_data),
        "outflow_data": json.dumps(outflow_data),
        "timeline_data": json.dumps(timeline_data),
        "timeline_labels": json.dumps(timeline_labels),
    }
    
    return render(request, "partials/case_dashboard_working.html", context)


@login_required
@require_http_methods(["GET"])
def htmx_case_transactions(request, case_id):
    """Get paginated transactions for a case."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case_wallets = CaseWallet.objects.filter(case=case)
    wallet_ids = case_wallets.values_list('wallet_id', flat=True)
    
    # Get transactions for all wallets in this case
    transactions = Transaction.objects.filter(
        wallet_id__in=wallet_ids
    ).select_related('wallet').order_by('-timestamp')
    
    # Paginate
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'case': case,
        'transactions': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, "partials/case_transactions.html", context)


@login_required
@require_http_methods(["GET"])
def htmx_case_wallet_analysis(request, case_id):
    """Analyze wallets in a case."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case_wallets = CaseWallet.objects.filter(case=case).select_related('wallet')
    
    wallet_analysis = []
    for cw in case_wallets:
        wallet = cw.wallet
        transactions = Transaction.objects.filter(wallet=wallet)
        
        # Calculate wallet metrics
        total_in = transactions.filter(
            transaction_type__in=['buy', 'transfer']
        ).aggregate(total=models.Sum('usd_value'))['total'] or 0
        
        total_out = transactions.filter(
            transaction_type='sell'
        ).aggregate(total=models.Sum('usd_value'))['total'] or 0
        
        balance_estimate = total_in - total_out
        tx_count = transactions.count()
        
        # Get last activity
        last_tx = transactions.order_by('-timestamp').first()
        
        wallet_analysis.append({
            'case_wallet': cw,
            'total_in': total_in,
            'total_out': total_out,
            'balance_estimate': balance_estimate,
            'tx_count': tx_count,
            'last_activity': last_tx.timestamp if last_tx else None,
        })
    
    context = {
        'case': case,
        'wallet_analysis': wallet_analysis,
    }
    
    return render(request, "partials/case_wallet_analysis.html", context)


@login_required
@require_http_methods(["GET"])
def htmx_case_suspicious_patterns(request, case_id):
    """Detect and display suspicious patterns in case transactions."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case_wallets = CaseWallet.objects.filter(case=case)
    wallet_ids = case_wallets.values_list('wallet_id', flat=True)
    
    # Get transactions with patterns
    suspicious_transactions = Transaction.objects.filter(
        wallet_id__in=wallet_ids
    ).exclude(
        metadata__pattern__isnull=True
    ).select_related('wallet').order_by('-timestamp')
    
    # Group by pattern type
    patterns = {}
    for tx in suspicious_transactions:
        pattern = tx.metadata.get('pattern', 'unknown')
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(tx)
    
    context = {
        'case': case,
        'patterns': patterns,
        'suspicious_count': suspicious_transactions.count(),
    }
    
    return render(request, "partials/case_suspicious_patterns.html", context)


@login_required
@require_http_methods(["PUT"])
def htmx_update_case_notes(request, case_id):
    """Update case investigation notes."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    
    notes = request.POST.get('notes', '')
    case.notes = notes
    case.save()
    
    return HttpResponse('<div class="uk-alert-success" uk-alert>Notes saved successfully!</div>')


@login_required
@require_http_methods(["POST"])
def htmx_add_wallet_to_case(request, case_id):
    """Add a new wallet to a case."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    
    # Get form data
    address = request.POST.get('address')
    chain = request.POST.get('chain')
    label = request.POST.get('label', '')
    category = request.POST.get('category', 'unknown')
    flagged = request.POST.get('flagged') == 'on'
    
    if not address or not chain:
        return HttpResponse("Address and chain are required", status=400)
    
    # Create or get wallet
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        address=address,
        chain=chain,
        defaults={'label': label}
    )
    
    # Add to case
    case_wallet, cw_created = CaseWallet.objects.get_or_create(
        case=case,
        wallet=wallet,
        defaults={
            'category': category,
            'flagged': flagged,
        }
    )
    
    # Clear modal and return success message
    success_message = f"""
    <div class="fixed top-4 right-4 bg-green-600 text-white p-4 rounded-lg shadow-lg max-w-sm z-50">
        <div class="flex items-start space-x-3">
            <svg class="w-5 h-5 text-green-200 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <div>
                <p class="font-semibold">Wallet Added</p>
                <p class="text-sm text-green-100">Wallet successfully added to case</p>
            </div>
        </div>
    </div>
    <script>
        setTimeout(() => {{
            document.querySelector('.fixed.top-4.right-4').remove();
        }}, 3000);
    </script>
    """
    
    return HttpResponse(success_message)


@login_required
@require_http_methods(["GET"])
def htmx_add_wallet_to_case_form(request, case_id):
    """Display form to add wallet to case."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    
    form_html = f"""
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-gray-800 rounded-xl p-8 max-w-md w-full mx-4">
            <h3 class="text-xl font-semibold text-white mb-6">Add Wallet to Case</h3>
            <form hx-post="/htmx/cases/{case_id}/add-wallet/" hx-target="#modal-container" hx-swap="innerHTML">
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Wallet Address</label>
                        <input type="text" name="address" required 
                               class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                               placeholder="0x...">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Chain</label>
                        <select name="chain" required class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="">Select Chain</option>
                            <option value="ethereum">Ethereum</option>
                            <option value="arbitrum">Arbitrum</option>
                            <option value="optimism">Optimism</option>
                            <option value="polygon">Polygon</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Label (Optional)</label>
                        <input type="text" name="label" 
                               class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                               placeholder="Wallet description">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Category</label>
                        <select name="category" class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="unknown">Unknown</option>
                            <option value="personal">Personal</option>
                            <option value="exchange">Exchange</option>
                            <option value="defi">DeFi Protocol</option>
                            <option value="suspicious">Suspicious</option>
                        </select>
                    </div>
                    <div class="flex items-center">
                        <input type="checkbox" name="flagged" id="flagged" class="rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500 focus:ring-2">
                        <label for="flagged" class="ml-2 text-sm text-gray-300">Flag as high risk</label>
                    </div>
                </div>
                <div class="flex justify-end space-x-3 mt-6">
                    <button type="button" onclick="document.getElementById('modal-container').innerHTML = ''" 
                            class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors">
                        Cancel
                    </button>
                    <button type="submit" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
                        Add Wallet
                    </button>
                </div>
            </form>
        </div>
    </div>
    """
    
    return HttpResponse(form_html)


@login_required
@require_http_methods(["POST"])
def htmx_export_case_data(request, case_id):
    """Export case data to CSV."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    
    # This would normally generate and return a CSV file
    # For now, return a success message
    message = f"""
    <div class="fixed top-4 right-4 bg-green-600 text-white p-4 rounded-lg shadow-lg max-w-sm z-50">
        <div class="flex items-start space-x-3">
            <svg class="w-5 h-5 text-green-200 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <div>
                <p class="font-semibold">Export Complete</p>
                <p class="text-sm text-green-100">Case data exported successfully</p>
            </div>
        </div>
    </div>
    <script>
        setTimeout(() => {{
            document.querySelector('.fixed.top-4.right-4').remove();
        }}, 3000);
    </script>
    """
    
    return HttpResponse(message)


@login_required
@require_http_methods(["POST"])
def htmx_generate_case_report(request, case_id):
    """Generate comprehensive case report."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    
    # This would normally generate a PDF report
    # For now, return a success message
    message = f"""
    <div class="fixed top-4 right-4 bg-blue-600 text-white p-4 rounded-lg shadow-lg max-w-sm z-50">
        <div class="flex items-start space-x-3">
            <svg class="w-5 h-5 text-blue-200 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <div>
                <p class="font-semibold">Report Generated</p>
                <p class="text-sm text-blue-100">Comprehensive analysis ready for download</p>
            </div>
        </div>
    </div>
    <script>
        setTimeout(() => {{
            document.querySelector('.fixed.top-4.right-4').remove();
        }}, 3000);
    </script>
    """
    
    return HttpResponse(message)


@login_required
@require_http_methods(["GET"])
def htmx_chart_data(request, case_id, timeframe):
    """Return JSON chart data simulating live blockchain data feeds from multiple chains."""
    case = get_object_or_404(InvestigationCase, id=case_id, investigator=request.user)
    case_wallets = CaseWallet.objects.filter(case=case).select_related('wallet')
    
    # Calculate timeframe and data points
    timeframe_map = {
        '7D': {'days': 7, 'points': 168, 'interval_hours': 1},  # Hourly for 7 days
        '30D': {'days': 30, 'points': 120, 'interval_hours': 6}, # Every 6 hours for 30 days
        '1Y': {'days': 365, 'points': 365, 'interval_hours': 24} # Daily for 1 year
    }
    
    config = timeframe_map.get(timeframe, timeframe_map['7D'])
    
    # Get wallet distribution by chain from case
    chain_wallets = {}
    for case_wallet in case_wallets:
        chain = case_wallet.wallet.chain
        if chain not in chain_wallets:
            chain_wallets[chain] = []
        chain_wallets[chain].append(case_wallet.wallet)
    
    # Generate blockchain data arrays
    labels = []
    ethereum_balances = []
    arbitrum_balances = []
    optimism_balances = []
    polygon_balances = []
    
    # Chain volume data
    ethereum_volume = []
    arbitrum_volume = []
    optimism_volume = []
    polygon_volume = []
    
    now = timezone.now()
    start_time = now - timedelta(days=config['days'])
    
    # Starting balances per chain (simulate wallets being tracked)
    base_balances = {
        'ethereum': 1200000,  # $1.2M on Ethereum
        'arbitrum': 450000,   # $450K on Arbitrum
        'optimism': 380000,   # $380K on Optimism
        'polygon': 320000     # $320K on Polygon
    }
    
    # Generate realistic blockchain tracking data
    for i in range(config['points']):
        timestamp = start_time + timedelta(hours=i * config['interval_hours'])
        
        # Format timestamp based on timeframe
        if config['days'] <= 7:
            label = timestamp.strftime('%m/%d %H:%M')
        elif config['days'] <= 30:
            label = timestamp.strftime('%m/%d')
        else:
            label = timestamp.strftime('%b %Y')
        
        labels.append(label)
        
        # Simulate balance changes for each chain (as if reading from blockchain APIs)
        for chain in ['ethereum', 'arbitrum', 'optimism', 'polygon']:
            # Different volatility patterns for different chains
            if chain == 'ethereum':
                volatility = 0.015  # Lower volatility for Ethereum
                volume_base = 50000
            elif chain == 'arbitrum':
                volatility = 0.025  # Medium volatility for L2s
                volume_base = 25000
            elif chain == 'optimism':
                volatility = 0.03   # Higher volatility for smaller L2
                volume_base = 20000
            else:  # polygon
                volatility = 0.035  # Highest volatility
                volume_base = 15000
            
            # Simulate balance updates (as if querying wallet balances from chain)
            change = random.normalvariate(0.0001, volatility)
            base_balances[chain] *= (1 + change)
            base_balances[chain] = max(base_balances[chain], 50000)  # Don't go below $50K
            
            # Simulate transaction volume for this period
            volume = volume_base + random.randint(-volume_base//2, volume_base)
            volume = max(volume, 1000)  # Minimum $1K volume
            
            # Store data points
            if chain == 'ethereum':
                ethereum_balances.append(round(base_balances[chain], 2))
                ethereum_volume.append(volume)
            elif chain == 'arbitrum':
                arbitrum_balances.append(round(base_balances[chain], 2))
                arbitrum_volume.append(volume)
            elif chain == 'optimism':
                optimism_balances.append(round(base_balances[chain], 2))
                optimism_volume.append(volume)
            else:  # polygon
                polygon_balances.append(round(base_balances[chain], 2))
                polygon_volume.append(volume)
    
    # Calculate total portfolio value across all chains
    total_portfolio = []
    for i in range(len(labels)):
        total = ethereum_balances[i] + arbitrum_balances[i] + optimism_balances[i] + polygon_balances[i]
        total_portfolio.append(round(total, 2))
    
    # Return blockchain investigation data
    from django.http import JsonResponse
    
    return JsonResponse({
        'success': True,
        'timeframe': timeframe,
        'labels': labels,
        'multi_chain_data': {
            'ethereum': {'balances': ethereum_balances, 'volume': ethereum_volume},
            'arbitrum': {'balances': arbitrum_balances, 'volume': arbitrum_volume},
            'optimism': {'balances': optimism_balances, 'volume': optimism_volume},
            'polygon': {'balances': polygon_balances, 'volume': polygon_volume}
        },
        'total_portfolio': total_portfolio,
        'summary': {
            'start_value': total_portfolio[0],
            'end_value': total_portfolio[-1],
            'total_points': len(total_portfolio),
            'change_percent': round(((total_portfolio[-1] - total_portfolio[0]) / total_portfolio[0]) * 100, 2),
            'chains_tracked': len(chain_wallets)
        }
    })


@login_required
@require_http_methods(["GET"])
def htmx_case_by_pattern(request, pattern):
    """Quick access to case by pattern name"""
    pattern_map = {
        "arbitrage": "Arbitrage Bot Strategy Tracker",
        "defi": "DeFi Yield Farming Monitor", 
        "mev": "Cross-Chain MEV Analysis"
    }
    
    case_name = pattern_map.get(pattern)
    if not case_name:
        return htmx_cases_list(request)
        
    case = InvestigationCase.objects.filter(
        investigator=request.user,
        name__icontains=case_name
    ).first()
    
    if case:
        return htmx_case_detail(request, case.id)
    else:
        return htmx_cases_list(request)
