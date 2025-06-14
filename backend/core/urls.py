"""
HTMX URL patterns for server-rendered HTML partials.
"""
from django.urls import path
from . import views

app_name = 'htmx'

urlpatterns = [
    # Authentication
    path('login/', views.htmx_login, name='login'),
    
    # Dashboard
    path('dashboard/', views.htmx_dashboard, name='dashboard'),
    
    # Wallet management
    path('wallets/add/', views.htmx_add_wallet, name='add_wallet'),
    path('wallets/<int:wallet_id>/delete/', views.htmx_delete_wallet, name='delete_wallet'),
    path('wallets/', views.htmx_wallets, name='wallets'),
    
    # Portfolio
    path('portfolio/summary/', views.htmx_portfolio_summary, name='portfolio_summary'),
    
    # Transactions
    path('transactions/', views.htmx_transactions, name='transactions'),
]