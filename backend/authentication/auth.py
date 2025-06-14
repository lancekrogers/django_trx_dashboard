from ninja.security import HttpBearer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


class AuthBearer(HttpBearer):
    """JWT Bearer token authentication for Django-Ninja"""
    
    def authenticate(self, request, token):
        """Validate JWT token and return user"""
        try:
            # Validate the token
            access_token = AccessToken(token)
            
            # Get user from token
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                return None
                
            return user
            
        except (TokenError, User.DoesNotExist):
            return None