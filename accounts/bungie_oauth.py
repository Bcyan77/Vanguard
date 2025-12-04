"""
Bungie.net OAuth authentication helper functions
"""

import requests
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
import logging
import base64

logger = logging.getLogger(__name__)


def get_authorization_url(request):
    """
    Generate the Bungie OAuth authorization URL
    
    Args:
        request: Django request object to build absolute URI
    
    Returns:
        str: Full authorization URL to redirect user to
    """
    # Build the callback URL
    callback_url = request.build_absolute_uri(reverse('accounts:oauth_callback'))
    
    logger.info(f"=== AUTHORIZATION URL GENERATION ===")
    logger.info(f"Request host: {request.get_host()}")
    logger.info(f"Request scheme: {request.scheme}")
    logger.info(f"Callback URL: {callback_url}")
    
    # OAuth parameters
    params = {
        'client_id': settings.BUNGIE_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': callback_url,
    }
    
    auth_url = f"{settings.BUNGIE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    logger.info(f"Full auth URL: {auth_url}")
    logger.info(f"====================================")
    
    return auth_url


def exchange_code_for_token(code, request):
    """
    Exchange authorization code for access token
    
    Args:
        code: Authorization code from Bungie
        request: Django request object to build callback URL
    
    Returns:
        dict: Token response containing access_token, refresh_token, etc.
        None: If exchange fails
    """
    callback_url = request.build_absolute_uri(reverse('accounts:oauth_callback'))
    
    # Prepare Basic Auth header with client_id:client_secret
    credentials = f"{settings.BUNGIE_CLIENT_ID}:{settings.BUNGIE_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': callback_url,
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}',
    }
    
    logger.info(f"=== TOKEN EXCHANGE ===")
    logger.info(f"Callback URL (redirect_uri): {callback_url}")
    logger.info(f"Grant type: {data['grant_type']}")
    logger.info(f"Code: {code[:10]}...")
    logger.info(f"======================")
    
    try:
        response = requests.post(
            settings.BUNGIE_OAUTH_TOKEN_URL,
            data=data,
            headers=headers,
            timeout=10
        )
        
        # Log response for debugging
        logger.info(f"Token exchange response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Token exchange failed. Response: {response.text}")
        
        response.raise_for_status()
        
        token_data = response.json()
        logger.info("Successfully exchanged code for token")
        return token_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to exchange code for token: {e}")
        return None


def refresh_access_token(refresh_token):
    """
    Refresh an expired access token
    
    Args:
        refresh_token: The refresh token
    
    Returns:
        dict: New token response
        None: If refresh fails
    """
    # Prepare Basic Auth header with client_id:client_secret
    credentials = f"{settings.BUNGIE_CLIENT_ID}:{settings.BUNGIE_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}',
    }
    
    try:
        response = requests.post(
            settings.BUNGIE_OAUTH_TOKEN_URL,
            data=data,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        token_data = response.json()
        logger.info("Successfully refreshed access token")
        return token_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to refresh token: {e}")
        return None


def get_bungie_user_info(access_token):
    """
    Get current user's Bungie membership information
    
    Args:
        access_token: Valid Bungie access token
    
    Returns:
        dict: User membership data
        None: If request fails
    """
    url = f"{settings.BUNGIE_API_BASE_URL}/User/GetMembershipsForCurrentUser/"
    
    headers = {
        'X-API-Key': settings.BUNGIE_API_KEY,
        'Authorization': f'Bearer {access_token}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ErrorCode') == 1 and 'Response' in data:
            logger.info("Successfully retrieved user info")
            return data['Response']
        else:
            logger.error(f"Bungie API error: {data.get('Message', 'Unknown error')}")
            return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get user info: {e}")
        return None


def get_destiny_profile(membership_type, membership_id, access_token):
    """
    Get Destiny 2 profile information for a user
    
    Args:
        membership_type: Platform membership type (1=Xbox, 2=PSN, 3=Steam, etc.)
        membership_id: User's membership ID
        access_token: Valid Bungie access token
    
    Returns:
        dict: Profile data including characters
        None: If request fails
    """
    # Components: 100=Profiles, 200=Characters
    components = '100,200'
    url = f"{settings.BUNGIE_API_BASE_URL}/Destiny2/{membership_type}/Profile/{membership_id}/"
    
    headers = {
        'X-API-Key': settings.BUNGIE_API_KEY,
        'Authorization': f'Bearer {access_token}',
    }
    
    params = {
        'components': components
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ErrorCode') == 1 and 'Response' in data:
            logger.info(f"Successfully retrieved profile for {membership_id}")
            return data['Response']
        else:
            logger.error(f"Bungie API error: {data.get('Message', 'Unknown error')}")
            return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get profile: {e}")
        return None


def make_bungie_api_request(endpoint, access_token, method='GET', data=None):
    """
    Generic function to make Bungie API requests
    
    Args:
        endpoint: API endpoint (e.g., '/User/GetMembershipsForCurrentUser/')
        access_token: Valid Bungie access token
        method: HTTP method (GET, POST, etc.)
        data: Request data for POST requests
    
    Returns:
        dict: API response
        None: If request fails
    """
    url = f"{settings.BUNGIE_API_BASE_URL}{endpoint}"
    
    headers = {
        'X-API-Key': settings.BUNGIE_API_KEY,
        'Authorization': f'Bearer {access_token}',
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ErrorCode') == 1:
            return data.get('Response')
        else:
            logger.error(f"Bungie API error: {data.get('Message', 'Unknown error')}")
            return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None


def get_manifest_api_request(endpoint, method='GET'):
    """
    Make Bungie API requests that don't require OAuth (manifest endpoints)

    Args:
        endpoint: API endpoint (e.g., '/Destiny2/Manifest/')
        method: HTTP method (GET, POST, etc.)

    Returns:
        dict: API response
        None: If request fails
    """
    url = f"{settings.BUNGIE_API_BASE_URL}{endpoint}"

    headers = {
        'X-API-Key': settings.BUNGIE_API_KEY,
    }

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None

        response.raise_for_status()

        data = response.json()

        if data.get('ErrorCode') == 1:
            return data.get('Response')
        else:
            logger.error(f"Bungie API error: {data.get('Message', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Manifest API request failed: {e}")
        return None
