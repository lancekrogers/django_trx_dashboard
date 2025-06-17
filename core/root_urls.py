"""
Root URL patterns for main pages.
"""

from django.shortcuts import render
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("dashboard/", views.htmx_dashboard, name="dashboard"),
    path("login/", lambda request: render(request, "forms/login.html"), name="login"),
]
