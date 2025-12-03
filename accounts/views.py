from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .bungie_oauth import (
    get_authorization_url,
    exchange_code_for_token,
    get_bungie_user_info,
    refresh_access_token
)
from .models import BungieUser
import logging

logger = logging.getLogger(__name__)


def login_view(request):
    """
    Initiate Bungie OAuth flow
    Redirects user to Bungie.net authorization page
    """
    if request.user.is_authenticated:
        return redirect('parties:party_list')
    
    # Generate authorization URL and redirect
    auth_url = get_authorization_url(request)
    return redirect(auth_url)


def oauth_callback(request):
    """
    Handle OAuth callback from Bungie.net
    Exchange code for token and create/update user
    """
    # Get authorization code from query parameters
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f'Authentication failed: {error}')
        return redirect('home')
    
    if not code:
        messages.error(request, 'No authorization code received')
        return redirect('home')
    
    # Exchange code for access token
    token_data = exchange_code_for_token(code, request)
    
    if not token_data:
        messages.error(request, 'Failed to obtain access token')
        return redirect('home')
    
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in', 3600)
    
    # Get user info from Bungie
    user_info = get_bungie_user_info(access_token)
    
    if not user_info:
        messages.error(request, 'Failed to retrieve user information')
        return redirect('home')
    
    # Extract primary membership (Destiny 2)
    destiny_memberships = user_info.get('destinyMemberships', [])
    
    if not destiny_memberships:
        messages.error(request, 'No Destiny 2 account found. Please link a Destiny 2 account to your Bungie.net profile.')
        return redirect('home')
    
    # Use the first (primary) Destiny membership
    primary_membership = destiny_memberships[0]
    
    membership_id = primary_membership.get('membershipId')
    membership_type = primary_membership.get('membershipType')
    display_name = primary_membership.get('displayName')
    icon_path = primary_membership.get('iconPath', '')
    
    # Get Bungie.net display name
    bungie_net_user = user_info.get('bungieNetUser', {})
    bungie_global_display_name = bungie_net_user.get('uniqueName', '')
    bungie_global_display_name_code = bungie_net_user.get('uniqueNameCode', '')
    
    # Calculate token expiration
    token_expires_at = timezone.now() + timedelta(seconds=expires_in)
    
    # Create or update user
    user, created = BungieUser.objects.get_or_create(
        bungie_membership_id=membership_id,
        defaults={
            'bungie_membership_type': membership_type,
            'display_name': display_name,
            'icon_path': icon_path,
            'bungie_global_display_name': bungie_global_display_name,
            'bungie_global_display_name_code': bungie_global_display_name_code,
        }
    )
    
    # Update user data
    user.bungie_membership_type = membership_type
    user.display_name = display_name
    user.icon_path = icon_path
    user.bungie_global_display_name = bungie_global_display_name
    user.bungie_global_display_name_code = bungie_global_display_name_code
    user.set_access_token(access_token)
    user.set_refresh_token(refresh_token)
    user.token_expires_at = token_expires_at
    user.save()
    
    # Log the user in
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    if created:
        messages.success(request, f'Welcome to Vanguard, {user.display_name}!')
    else:
        messages.success(request, f'Welcome back, {user.display_name}!')
    
    logger.info(f"User {user.display_name} logged in successfully")
    
    return redirect('parties:party_list')


@login_required
def logout_view(request):
    """
    Log out the current user
    """
    user_name = request.user.display_name
    logout(request)
    messages.success(request, f'Goodbye, {user_name}!')
    return redirect('home')


@login_required
def profile_view(request):
    """
    Display user profile
    """
    user = request.user
    
    # Get user's created parties
    created_parties = user.created_parties.all()[:5]
    
    # Get user's party memberships
    memberships = user.party_memberships.filter(status='active').select_related('party')[:5]
    
    # Get pending applications
    pending_applications = user.party_applications.filter(status='pending').select_related('party')[:5]
    
    context = {
        'user': user,
        'created_parties': created_parties,
        'memberships': memberships,
        'pending_applications': pending_applications,
    }
    
    return render(request, 'accounts/profile.html', context)


def home_view(request):
    """
    Home page view
    """
    if request.user.is_authenticated:
        return redirect('parties:party_list')
    
    return render(request, 'home.html')
