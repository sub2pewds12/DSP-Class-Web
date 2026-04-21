from django.db import models
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        try:
            # Try to find user by email first (as requested by UI labels) or USERNAME_FIELD
            user = UserModel.objects.get(
                models.Q(email__iexact=username) | 
                models.Q(**{UserModel.USERNAME_FIELD + '__iexact': username})
            )
        except UserModel.DoesNotExist:
            # Run the default password hasher to prevent timing attacks
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
