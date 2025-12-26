"""
Bungie API helper functions for player search
"""
import logging
import requests
from django.conf import settings
from accounts.bungie_oauth import make_bungie_api_request

logger = logging.getLogger(__name__)


def make_public_api_request(endpoint, method='GET', data=None):
    """
    Make Bungie API requests that only require API key (no OAuth token)
    Used for public endpoints like player search.

    Args:
        endpoint: API endpoint
        method: HTTP method (GET, POST)
        data: Request data for POST requests

    Returns:
        dict: API response or None
    """
    url = f"{settings.BUNGIE_API_BASE_URL}{endpoint}"

    headers = {
        'X-API-Key': settings.BUNGIE_API_KEY,
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

        resp_data = response.json()

        if resp_data.get('ErrorCode') == 1:
            return resp_data.get('Response')
        else:
            logger.error(f"Bungie API error: {resp_data.get('Message', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

# Destiny 2 class mappings
CLASS_TYPES = {
    0: 'Titan',
    1: 'Hunter',
    2: 'Warlock',
}

# Membership type mappings with Bungie official icon URLs
BUNGIE_NET_URL = 'https://www.bungie.net'
MEMBERSHIP_TYPES = {
    1: {'name': 'Xbox', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/xboxLiveLogo.png'},
    2: {'name': 'PlayStation', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/psnLogo.png'},
    3: {'name': 'Steam', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/steamLogo.png'},
    4: {'name': 'Blizzard', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/blizzardLogo.png'},
    5: {'name': 'Stadia', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/stadiaLogo.png'},
    6: {'name': 'Epic Games', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/epicLogo.png'},
    10: {'name': 'Demon', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/tgrLogo.png'},
    254: {'name': 'BungieNext', 'icon': f'{BUNGIE_NET_URL}/img/theme/bungienet/icons/bunloginLogo.png'},
}


def search_by_bungie_name(full_name):
    """
    Exact search by Bungie Name (PlayerName#1234)

    Args:
        full_name: Full Bungie name with code (e.g., "Guardian#1234")

    Returns:
        tuple: (list of results, error message or None)
    """
    try:
        parts = full_name.rsplit('#', 1)
        if len(parts) != 2:
            return [], 'Invalid format. Use PlayerName#1234'

        display_name = parts[0].strip()
        display_name_code = parts[1].strip()

        if not display_name:
            return [], 'Display name cannot be empty'

        if not display_name_code.isdigit():
            return [], 'Name code must be a number'

        data = {
            'displayName': display_name,
            'displayNameCode': int(display_name_code)
        }

        # membershipType -1 = All platforms (public API, no OAuth needed)
        response = make_public_api_request(
            '/Destiny2/SearchDestinyPlayerByBungieName/-1/',
            method='POST',
            data=data
        )

        if response:
            # Format results consistently
            results = []
            for player in response:
                results.append({
                    'membershipId': player.get('membershipId'),
                    'membershipType': player.get('membershipType'),
                    'displayName': player.get('displayName'),
                    'bungieGlobalDisplayName': player.get('bungieGlobalDisplayName'),
                    'bungieGlobalDisplayNameCode': player.get('bungieGlobalDisplayNameCode'),
                    'iconPath': player.get('iconPath', ''),
                })
            return results, None
        return [], 'No players found'

    except Exception as e:
        logger.error(f"Exact search failed: {e}")
        return [], str(e)


def search_by_prefix(prefix, page=0):
    """
    Prefix search by partial name

    Args:
        prefix: Partial player name
        page: Page number (default 0)

    Returns:
        tuple: (list of results, error message or None)
    """
    try:
        data = {
            'displayNamePrefix': prefix
        }

        # Public API, no OAuth needed
        response = make_public_api_request(
            f'/User/Search/GlobalName/{page}/',
            method='POST',
            data=data
        )

        if response and response.get('searchResults'):
            results = []
            for user in response['searchResults']:
                # Each user may have multiple destiny memberships
                for membership in user.get('destinyMemberships', []):
                    results.append({
                        'membershipId': membership.get('membershipId'),
                        'membershipType': membership.get('membershipType'),
                        'displayName': membership.get('displayName'),
                        'bungieGlobalDisplayName': user.get('bungieGlobalDisplayName'),
                        'bungieGlobalDisplayNameCode': user.get('bungieGlobalDisplayNameCode'),
                        'iconPath': membership.get('iconPath', ''),
                    })
            return results, None
        return [], 'No players found'

    except Exception as e:
        logger.error(f"Prefix search failed: {e}")
        return [], str(e)


def get_player_profile(membership_type, membership_id):
    """
    Get detailed player profile (public API, no OAuth needed)

    Components:
        100 - Profiles (basic info)
        200 - Characters (class, light level)
        205 - CharacterEquipment (equipped items)
        900 - Records (Triumphs)
        1100 - Metrics

    Returns:
        dict: Profile data or None
    """
    try:
        response = make_public_api_request(
            f'/Destiny2/{membership_type}/Profile/{membership_id}/?components=100,200,205,900,1100'
        )
        return response
    except Exception as e:
        logger.error(f"Get profile failed: {e}")
        return None


def get_activity_history(membership_type, membership_id, character_id, count=10):
    """
    Get recent activity history for a character (public API, no OAuth needed)

    Args:
        membership_type: Platform type
        membership_id: Player's membership ID
        character_id: Character ID to get history for
        count: Number of activities to retrieve

    Returns:
        list: Recent activities
    """
    try:
        response = make_public_api_request(
            f'/Destiny2/{membership_type}/Account/{membership_id}/Character/{character_id}/Stats/Activities/?count={count}&mode=0'
        )

        if response and response.get('activities'):
            return response['activities']
        return []
    except Exception as e:
        logger.error(f"Get activity history failed: {e}")
        return []


def get_all_characters_activities(membership_type, membership_id, character_ids, count_per_char=10):
    """
    Get recent activities for all characters, merged and sorted by date

    Args:
        membership_type: Platform type
        membership_id: Player's membership ID
        character_ids: List of character IDs
        count_per_char: Number of activities per character

    Returns:
        list: All activities sorted by date (newest first)
    """
    all_activities = []

    for char_id in character_ids:
        activities = get_activity_history(
            membership_type, membership_id, char_id, count_per_char
        )
        for activity in activities:
            activity['characterId'] = char_id
        all_activities.extend(activities)

    # Sort by period (date) descending
    all_activities.sort(key=lambda x: x.get('period', ''), reverse=True)

    return all_activities


def get_class_name(class_type):
    """Convert class type to class name"""
    return CLASS_TYPES.get(class_type, 'Unknown')


def get_platform_info(membership_type):
    """Get platform name and icon for membership type"""
    return MEMBERSHIP_TYPES.get(membership_type, {'name': 'Unknown', 'icon': 'unknown'})


def get_activity_name(activity_hash):
    """Get activity name from hash using database lookup"""
    from fireteams.models import DestinySpecificActivity
    try:
        activity = DestinySpecificActivity.objects.get(hash=activity_hash)
        return activity.name
    except DestinySpecificActivity.DoesNotExist:
        return "Unknown Activity"


def search_clans(name, page=0):
    """
    Search for clans by name.

    Endpoint: POST /GroupV2/Search/

    Args:
        name: Clan name to search (partial match)
        page: Page number for pagination

    Returns:
        tuple: (list of clan dicts, error message or None)
    """
    try:
        data = {
            'name': name,
            'groupType': 1,  # Clan (Destiny 2)
        }

        response = make_public_api_request(
            f'/GroupV2/Search/?currentpage={page}&itemsPerPage=25',
            method='POST',
            data=data
        )

        if response and response.get('results'):
            results = []
            for clan in response['results']:
                results.append({
                    'groupId': clan.get('groupId'),
                    'name': clan.get('name'),
                    'memberCount': clan.get('memberCount', 0),
                    'motto': clan.get('motto', ''),
                    'about': (clan.get('about', '') or '')[:100],
                })
            return results, None
        return [], 'No clans found'

    except Exception as e:
        logger.error(f"Clan search failed: {e}")
        return [], str(e)


def get_clan_members(group_id, page=1):
    """
    Get members of a clan by group ID.

    Endpoint: GET /GroupV2/{groupId}/Members/

    Args:
        group_id: Bungie clan group ID
        page: Page number (1-indexed, 100 members per page)

    Returns:
        tuple: (list of member dicts, has_more, error message or None)
    """
    try:
        response = make_public_api_request(
            f'/GroupV2/{group_id}/Members/?currentpage={page}'
        )

        if response and response.get('results'):
            members = []
            for member_data in response['results']:
                destiny_info = member_data.get('destinyUserInfo', {})
                if destiny_info.get('membershipId'):
                    members.append({
                        'membershipId': destiny_info.get('membershipId'),
                        'membershipType': destiny_info.get('membershipType'),
                        'displayName': destiny_info.get('displayName'),
                        'bungieGlobalDisplayName': destiny_info.get('bungieGlobalDisplayName'),
                        'bungieGlobalDisplayNameCode': destiny_info.get('bungieGlobalDisplayNameCode'),
                    })

            has_more = response.get('hasMore', False)
            return members, has_more, None

        return [], False, 'Failed to get clan members'

    except Exception as e:
        logger.error(f"Get clan members failed: {e}")
        return [], False, str(e)


def get_current_power_cap():
    """
    Bungie Manifest API에서 현재 시즌의 파워 캡을 조회.

    Settings API를 통해 현재 시즌의 파워 캡 정보를 가져옵니다.

    Returns:
        dict: {'power_cap': int, 'season_hash': str} or None
    """
    try:
        # Destiny2 Settings API에서 현재 시즌 정보 가져오기
        response = make_public_api_request('/Destiny2/Manifest/')

        if not response:
            logger.warning("Failed to get Destiny manifest")
            return None

        # Manifest에서 Settings 정보 가져오기
        settings_response = make_public_api_request('/Settings/')

        if settings_response and settings_response.get('destiny2CoreSettings'):
            core_settings = settings_response['destiny2CoreSettings']
            current_season_hash = core_settings.get('currentSeasonHash')

            if current_season_hash:
                # 시즌 정의에서 파워 캡 정보 조회
                # Manifest의 DestinySeasonDefinition에서 조회
                world_content_paths = response.get('jsonWorldComponentContentPaths', {})
                en_paths = world_content_paths.get('en', {})
                season_path = en_paths.get('DestinySeasonDefinition')

                if season_path:
                    season_url = f"{BUNGIE_NET_URL}{season_path}"
                    try:
                        season_response = requests.get(season_url, timeout=30)
                        season_response.raise_for_status()
                        season_data = season_response.json()

                        # 현재 시즌 해시로 파워 캡 찾기
                        current_season = season_data.get(str(current_season_hash), {})
                        if current_season:
                            # seasonPass에서 prestigeProgressionHash를 통해 파워 캡 확인
                            # 또는 artifact의 powerCap 필드 사용
                            # 시즌마다 구조가 다를 수 있으므로 여러 경로 시도
                            power_cap = None

                            # 방법 1: seasonPass의 power cap
                            season_pass = current_season.get('seasonPass', {})
                            if 'powerCapHash' in current_season:
                                power_cap_hash = current_season.get('powerCapHash')
                                # DestinyPowerCapDefinition에서 조회
                                power_cap_path = en_paths.get('DestinyPowerCapDefinition')
                                if power_cap_path:
                                    cap_url = f"{BUNGIE_NET_URL}{power_cap_path}"
                                    cap_response = requests.get(cap_url, timeout=30)
                                    cap_response.raise_for_status()
                                    cap_data = cap_response.json()
                                    cap_def = cap_data.get(str(power_cap_hash), {})
                                    power_cap = cap_def.get('powerCap')

                            # 방법 2: displayProperties에서 추출 (fallback)
                            if not power_cap:
                                display_props = current_season.get('displayProperties', {})
                                description = display_props.get('description', '')
                                # 설명에서 파워 레벨 숫자 추출 시도
                                import re
                                match = re.search(r'(\d{4})\s*(?:Power|Light)', description)
                                if match:
                                    power_cap = int(match.group(1))

                            if power_cap:
                                logger.info(f"Current season power cap: {power_cap}")
                                return {
                                    'power_cap': power_cap,
                                    'season_hash': str(current_season_hash)
                                }

                    except requests.exceptions.RequestException as e:
                        logger.error(f"Failed to download season definitions: {e}")

        # 실패 시 기본값 반환
        logger.warning("Could not determine current power cap, using fallback")
        return None

    except Exception as e:
        logger.error(f"Get current power cap failed: {e}")
        return None


def get_power_cap_from_settings():
    """
    Bungie Settings API에서 파워 캡 정보를 직접 조회하는 간단한 방법.

    Returns:
        int: 현재 시즌의 소프트 캡/하드 캡 or None
    """
    try:
        # Destiny2 Settings에서 currentSeasonRewardPowerCap 또는 유사 필드 확인
        response = make_public_api_request('/Settings/')

        if response and 'destiny2CoreSettings' in response:
            settings = response['destiny2CoreSettings']

            # 다양한 필드 시도
            power_cap = settings.get('currentSeasonRewardPowerCap')
            if power_cap:
                return power_cap

            # pinnacle cap 확인
            pinnacle_cap = settings.get('currentSeasonPinnaclePowerCap')
            if pinnacle_cap:
                return pinnacle_cap

        return None

    except Exception as e:
        logger.error(f"Get power cap from settings failed: {e}")
        return None
