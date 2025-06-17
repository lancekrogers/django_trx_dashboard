"""
Core app tests - HTMX views, authentication, and navigation.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse
from unittest.mock import patch, MagicMock

User = get_user_model()


class HTMXViewsTestCase(TestCase):
    """Test HTMX-specific view functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )

    def test_home_view_unauthenticated(self):
        """Test home view returns app.html for unauthenticated users."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Multi-Chain Portfolio")
        self.assertTemplateUsed(response, "app.html")

    def test_home_view_authenticated(self):
        """Test home view returns app.html for authenticated users."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Multi-Chain Portfolio")
        self.assertTemplateUsed(response, "app.html")

    def test_htmx_welcome_view(self):
        """Test welcome partial view."""
        response = self.client.get("/htmx/welcome/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to Portfolio Dashboard")
        self.assertTemplateUsed(response, "partials/welcome.html")

    def test_htmx_login_get(self):
        """Test login form display."""
        response = self.client.get("/htmx/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in")
        self.assertTemplateUsed(response, "forms/login.html")

    def test_htmx_login_post_success(self):
        """Test successful login via HTMX."""
        response = self.client.post("/htmx/login/", {
            "username": "test@example.com",
            "password": "testpass123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Auth-Status"], "authenticated")
        self.assertTemplateUsed(response, "dashboard.html")

    def test_htmx_login_post_invalid(self):
        """Test failed login via HTMX."""
        response = self.client.post("/htmx/login/", {
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertContains(response, "Invalid username or password", status_code=401)
        self.assertTemplateUsed(response, "forms/login.html")

    def test_htmx_login_post_missing_fields(self):
        """Test login with missing fields."""
        response = self.client.post("/htmx/login/", {
            "username": "",
            "password": ""
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Username and password are required", status_code=400)

    def test_htmx_logout(self):
        """Test logout via HTMX."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.post("/htmx/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Auth-Status"], "unauthenticated")
        self.assertTemplateUsed(response, "partials/welcome.html")

    def test_navigation_partials_authenticated(self):
        """Test authenticated navigation partial."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get("/htmx/nav/authenticated/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Wallets")
        self.assertContains(response, "Transactions")
        self.assertTemplateUsed(response, "partials/nav_authenticated.html")

    def test_navigation_partials_unauthenticated(self):
        """Test unauthenticated navigation partial."""
        response = self.client.get("/htmx/nav/unauthenticated/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign In")
        self.assertTemplateUsed(response, "partials/nav_unauthenticated.html")

    def test_dashboard_view_requires_login(self):
        """Test dashboard view requires authentication."""
        response = self.client.get("/htmx/dashboard/")
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated user."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get("/htmx/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")


class HTMXHeaderTestCase(TestCase):
    """Test HTMX-specific HTTP headers and behaviors."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )

    def test_htmx_request_detection(self):
        """Test that views properly detect HTMX requests."""
        self.client.login(email="test@example.com", password="testpass123")
        
        # Regular request
        response = self.client.get("/htmx/dashboard/")
        self.assertEqual(response.status_code, 200)
        
        # HTMX request
        response = self.client.get("/htmx/dashboard/", 
                                 HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)

    def test_auth_status_headers(self):
        """Test that authentication status is properly communicated via headers."""
        # Successful login should set auth status header
        response = self.client.post("/htmx/login/", {
            "username": "test@example.com",
            "password": "testpass123"
        })
        self.assertEqual(response["X-Auth-Status"], "authenticated")
        
        # Logout should set unauth status header
        response = self.client.post("/htmx/logout/")
        self.assertEqual(response["X-Auth-Status"], "unauthenticated")


class AuthenticationTestCase(TestCase):
    """Test authentication functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            username="testuser"
        )

    def test_user_creation(self):
        """Test user can be created successfully."""
        self.assertTrue(User.objects.filter(email="test@example.com").exists())
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpass123"))

    def test_user_login(self):
        """Test user can log in successfully."""
        logged_in = self.client.login(email="test@example.com", password="testpass123")
        self.assertTrue(logged_in)

    def test_user_login_invalid(self):
        """Test user login fails with invalid credentials."""
        logged_in = self.client.login(email="test@example.com", password="wrongpassword")
        self.assertFalse(logged_in)

    def test_protected_views_require_auth(self):
        """Test that protected views require authentication."""
        protected_urls = [
            "/htmx/dashboard/",
            "/htmx/wallets/",
            "/htmx/transactions/",
            "/htmx/portfolio/summary/",
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"URL {url} should require auth")