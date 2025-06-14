"""
URL Configuration for Portfolio Dashboard
"""
from django.contrib import admin
from django.urls import path, include
from ninja import NinjaAPI

# Import routers
from authentication.api import router as auth_router
from wallets.api import router as wallets_router
from portfolio.api import router as portfolio_router
from transactions.api import router as transactions_router

api = NinjaAPI(
    title="Portfolio Dashboard API",
    version="1.0.0",
    description="Multi-chain cryptocurrency portfolio tracker API"
)

# Add routers
api.add_router("/auth/", auth_router, tags=["Authentication"])
api.add_router("/v1/wallets/", wallets_router, tags=["Wallets"])
api.add_router("/v1/portfolio/", portfolio_router, tags=["Portfolio"])
api.add_router("/v1/transactions/", transactions_router, tags=["Transactions"])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('htmx/', include('core.urls')),
    path('', include('core.urls')),  # For root dashboard access
]