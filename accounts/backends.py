from django.contrib.auth.backends import BaseBackend
from accounts.models import BungieUser


class AdminAccountBackend(BaseBackend):
    """
    Custom authentication backend for admin accounts using username/password.
    Regular Bungie OAuth users continue to use the default authentication.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate admin account by username and password
        """
        if not username or not password:
            return None

        try:
            # Only authenticate admin accounts
            user = BungieUser.objects.get(
                username=username,
                is_admin_account=True
            )
        except BungieUser.DoesNotExist:
            # Run default password hasher to prevent timing attacks
            BungieUser().set_password(password)
            return None

        # Check password
        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        """
        Get user by primary key (bungie_membership_id)
        """
        try:
            return BungieUser.objects.get(pk=user_id)
        except BungieUser.DoesNotExist:
            return None
