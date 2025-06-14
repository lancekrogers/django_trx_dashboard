from ninja import Router, Schema
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from typing import Optional

User = get_user_model()
router = Router()


class LoginSchema(Schema):
    email: str
    password: str


class TokenSchema(Schema):
    access: str
    refresh: str


class ErrorSchema(Schema):
    error: str


@router.post("/login/", response={200: TokenSchema, 401: ErrorSchema})
def login(request, data: LoginSchema):
    """Authenticate user and return JWT tokens"""
    # Try to authenticate with email
    user = authenticate(request, username=data.email, password=data.password)
    
    if user:
        refresh = RefreshToken.for_user(user)
        return 200, {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
    
    return 401, {"error": "Invalid credentials"}


class RefreshSchema(Schema):
    refresh: str


@router.post("/refresh/", response={200: TokenSchema, 401: ErrorSchema})
def refresh_token(request, data: RefreshSchema):
    """Refresh JWT access token"""
    try:
        refresh = RefreshToken(data.refresh)
        return 200, {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
    except Exception:
        return 401, {"error": "Invalid refresh token"}


class RegisterSchema(Schema):
    email: str
    password: str
    username: Optional[str] = None


class UserSchema(Schema):
    id: int
    email: str
    username: str


@router.post("/register/", response={201: UserSchema, 400: ErrorSchema})
def register(request, data: RegisterSchema):
    """Register a new user"""
    # Check if user already exists
    if User.objects.filter(email=data.email).exists():
        return 400, {"error": "User with this email already exists"}
    
    # Create username from email if not provided
    username = data.username or data.email.split('@')[0]
    
    # Ensure username is unique
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Create user
    user = User.objects.create_user(
        email=data.email,
        username=username,
        password=data.password
    )
    
    return 201, {
        "id": user.id,
        "email": user.email,
        "username": user.username
    }