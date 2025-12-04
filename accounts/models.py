from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class BungieUserManager(BaseUserManager):
    """Custom manager for BungieUser model"""

    def create_user(self, bungie_membership_id, bungie_membership_type, display_name, **extra_fields):
        """Create and save a BungieUser"""
        if not bungie_membership_id:
            raise ValueError('The Bungie Membership ID must be set')

        user = self.model(
            bungie_membership_id=bungie_membership_id,
            bungie_membership_type=bungie_membership_type,
            display_name=display_name,
            **extra_fields
        )
        user.save(using=self._db)
        return user

    def create_superuser(self, bungie_membership_id, bungie_membership_type, display_name, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(bungie_membership_id, bungie_membership_type, display_name, **extra_fields)

    def create_admin_user(self, username, password, **extra_fields):
        """Create admin account with username/password"""
        if not username:
            raise ValueError('Username is required for admin accounts')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin_account', True)
        extra_fields.setdefault('bungie_membership_type', 254)  # BungieNext

        user = self.model(
            bungie_membership_id=f'admin_{username}',
            username=username,
            display_name=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class BungieUser(AbstractBaseUser):
    """
    Custom user model for Bungie.net authentication
    Uses Bungie membership ID as the primary identifier
    """
    
    MEMBERSHIP_TYPE_CHOICES = [
        (1, 'Xbox'),
        (2, 'PlayStation'),
        (3, 'Steam'),
        (4, 'Blizzard'),
        (5, 'Stadia'),
        (6, 'Epic Games'),
        (254, 'BungieNext'),
    ]
    
    bungie_membership_id = models.CharField(max_length=100, unique=True, primary_key=True)
    bungie_membership_type = models.IntegerField(choices=MEMBERSHIP_TYPE_CHOICES)
    display_name = models.CharField(max_length=255)

    # OAuth tokens (encrypted)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Admin account support (for username/password authentication)
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text='For admin accounts only (not used for Bungie OAuth users)'
    )
    password = models.CharField(max_length=128, blank=True)
    is_admin_account = models.BooleanField(
        default=False,
        help_text='True if this is a username/password admin account (not Bungie OAuth)'
    )

    # User metadata
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Bungie profile data
    icon_path = models.CharField(max_length=500, blank=True, null=True)
    bungie_global_display_name = models.CharField(max_length=255, blank=True, null=True)
    bungie_global_display_name_code = models.CharField(max_length=10, blank=True, null=True)
    
    objects = BungieUserManager()
    
    USERNAME_FIELD = 'bungie_membership_id'
    REQUIRED_FIELDS = ['bungie_membership_type', 'display_name']
    
    class Meta:
        verbose_name = 'Bungie User'
        verbose_name_plural = 'Bungie Users'
    
    def __str__(self):
        if self.bungie_global_display_name and self.bungie_global_display_name_code:
            return f"{self.bungie_global_display_name}#{self.bungie_global_display_name_code}"
        return self.display_name
    
    def get_full_name(self):
        return self.display_name
    
    def get_short_name(self):
        return self.display_name
    
    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        return self.is_superuser
    
    def get_platform_display(self):
        """Get human-readable platform name"""
        return dict(self.MEMBERSHIP_TYPE_CHOICES).get(self.bungie_membership_type, 'Unknown')
    
    def encrypt_token(self, token):
        """Encrypt a token for storage"""
        if not token:
            return None
        # Use Django secret key as encryption key (in production, use a dedicated key)
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token):
        """Decrypt a stored token"""
        if not encrypted_token:
            return None
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.decrypt(encrypted_token.encode()).decode()
    
    def set_access_token(self, token):
        """Set and encrypt access token"""
        self.access_token = self.encrypt_token(token)
    
    def get_access_token(self):
        """Get and decrypt access token"""
        return self.decrypt_token(self.access_token)
    
    def set_refresh_token(self, token):
        """Set and encrypt refresh token"""
        self.refresh_token = self.encrypt_token(token)
    
    def get_refresh_token(self):
        """Get and decrypt refresh token"""
        return self.decrypt_token(self.refresh_token)
