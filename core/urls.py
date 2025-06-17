"""
HTMX URL patterns for server-rendered HTML partials.
"""

from django.urls import path

from . import views

app_name = "htmx"

urlpatterns = [
    # Authentication
    path("login/", views.htmx_login, name="login"),
    path("logout/", views.htmx_logout, name="logout"),
    path("register/", views.htmx_register_form, name="register_form"),
    # Navigation
    path("nav/authenticated/", views.htmx_nav_authenticated, name="nav_authenticated"),
    path(
        "nav/unauthenticated/",
        views.htmx_nav_unauthenticated,
        name="nav_unauthenticated",
    ),
    # Pages
    path("welcome/", views.htmx_welcome, name="welcome"),
    path("dashboard/", views.htmx_dashboard, name="dashboard"),
    path("settings/", views.htmx_settings, name="settings"),
    path("refresh-mock-data/", views.htmx_refresh_mock_data, name="refresh_mock_data"),
    # Wallet management
    path("wallets/add/", views.htmx_add_wallet, name="add_wallet"),
    path(
        "wallets/<int:wallet_id>/delete/",
        views.htmx_delete_wallet,
        name="delete_wallet",
    ),
    path("wallets/", views.htmx_wallets, name="wallets"),
    # Portfolio
    path("portfolio/summary/", views.htmx_portfolio_summary, name="portfolio_summary"),
    # Transactions
    path("transactions/", views.htmx_transactions, name="transactions"),
    # Investigation Cases
    path("cases/", views.htmx_cases_list, name="cases_list"),
    path("cases/create/form/", views.htmx_create_case_form, name="create_case_form"),
    path("cases/create/", views.htmx_create_case, name="create_case"),
    path("cases/<int:case_id>/edit/form/", views.htmx_edit_case_form, name="edit_case_form"),
    path("cases/<int:case_id>/update/", views.htmx_update_case, name="update_case"),
    path("cases/<int:case_id>/archive/", views.htmx_archive_case, name="archive_case"),
    path("cases/<int:case_id>/", views.htmx_case_detail, name="case_detail"),
    path("cases/<int:case_id>/transactions/", views.htmx_case_transactions, name="case_transactions"),
    path("cases/<int:case_id>/wallet-analysis/", views.htmx_case_wallet_analysis, name="case_wallet_analysis"),
    path("cases/<int:case_id>/suspicious-patterns/", views.htmx_case_suspicious_patterns, name="case_suspicious_patterns"),
    path("cases/<int:case_id>/update-notes/", views.htmx_update_case_notes, name="update_case_notes"),
    path("cases/<int:case_id>/add-wallet/", views.htmx_add_wallet_to_case, name="add_wallet_to_case"),
    path("cases/<int:case_id>/add-wallet/form/", views.htmx_add_wallet_to_case_form, name="add_wallet_to_case_form"),
    path("cases/<int:case_id>/export/", views.htmx_export_case_data, name="export_case_data"),
    path("cases/<int:case_id>/report/", views.htmx_generate_case_report, name="generate_case_report"),
    path("cases/<int:case_id>/chart-data/<str:timeframe>/", views.htmx_chart_data, name="chart_data"),
    path("cases/<int:case_id>/chart-stream/", views.htmx_chart_stream, name="chart_stream"),
    # Quick case access by pattern
    path("case-by-name/<str:pattern>/", views.htmx_case_by_pattern, name="case_by_pattern"),
]
