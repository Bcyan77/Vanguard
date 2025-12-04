"""
Player search views
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .bungie_api import (
    search_by_bungie_name,
    search_by_prefix,
    get_player_profile,
    get_all_characters_activities,
    get_class_name,
    get_platform_info,
)
from .services import sync_player_from_api


@login_required
def player_search(request):
    """
    Search for Destiny 2 players by Bungie Name
    Supports exact search (Name#1234) and prefix search (partial name)
    """
    query = request.GET.get('q', '').strip()
    results = []
    search_type = None
    error = None

    if query:
        if '#' in query:
            # Exact search: PlayerName#1234
            search_type = 'exact'
            results, error = search_by_bungie_name(query)
        else:
            # Prefix search: partial name
            search_type = 'prefix'
            results, error = search_by_prefix(query)

        # Add platform info to results
        for result in results:
            platform = get_platform_info(result.get('membershipType'))
            result['platformName'] = platform['name']
            result['platformIcon'] = platform['icon']

    context = {
        'query': query,
        'results': results,
        'search_type': search_type,
        'error': error,
        'result_count': len(results),
    }
    return render(request, 'players/search.html', context)


@login_required
def player_detail(request, membership_type, membership_id):
    """
    Display detailed player information:
    - Platform
    - Characters (Class, Light Level, Equipment)
    - Triumph Score
    - Metrics
    - Recent Activities (all characters combined)
    """
    # Get profile data with components: 100, 200, 205, 900, 1100 (public API)
    profile = get_player_profile(membership_type, membership_id)

    if not profile:
        messages.error(request, 'Failed to load player profile. The profile may be private or unavailable.')
        return redirect('players:search')

    # Sync player data to database
    sync_player_from_api(membership_type, membership_id, profile)

    # Extract profile info
    profile_data = profile.get('profile', {}).get('data', {})
    user_info = profile_data.get('userInfo', {})

    # Extract characters
    characters_data = profile.get('characters', {}).get('data', {})
    characters = []
    character_ids = list(characters_data.keys())

    # Extract equipment
    equipment_data = profile.get('characterEquipment', {}).get('data', {})

    for char_id, char in characters_data.items():
        char_info = {
            'characterId': char_id,
            'classType': char.get('classType'),
            'className': get_class_name(char.get('classType')),
            'light': char.get('light'),
            'raceType': char.get('raceType'),
            'genderType': char.get('genderType'),
            'emblemPath': char.get('emblemPath', ''),
            'emblemBackgroundPath': char.get('emblemBackgroundPath', ''),
            'dateLastPlayed': char.get('dateLastPlayed', ''),
            'equipment': [],
        }

        # Add equipment for this character
        char_equipment = equipment_data.get(char_id, {}).get('items', [])
        for item in char_equipment:
            char_info['equipment'].append({
                'itemHash': item.get('itemHash'),
                'bucketHash': item.get('bucketHash'),
            })

        characters.append(char_info)

    # Sort characters by last played date
    characters.sort(key=lambda x: x.get('dateLastPlayed', ''), reverse=True)

    # Extract triumph score
    profile_records = profile.get('profileRecords', {}).get('data', {})
    triumph_score = profile_records.get('activeScore', 0)
    lifetime_score = profile_records.get('lifetimeScore', 0)

    # Extract metrics
    metrics_data = profile.get('metrics', {}).get('data', {}).get('metrics', {})

    # Get recent activities for all characters (public API)
    recent_activities = []
    if character_ids:
        recent_activities = get_all_characters_activities(
            membership_type, membership_id, character_ids, count_per_char=5
        )
        # Limit to 15 most recent
        recent_activities = recent_activities[:15]

        # Add character class info to activities
        char_class_map = {c['characterId']: c['className'] for c in characters}
        for activity in recent_activities:
            activity['characterClass'] = char_class_map.get(activity.get('characterId'), 'Unknown')

    # Platform info
    platform = get_platform_info(membership_type)

    context = {
        'user_info': user_info,
        'platform': platform,
        'membership_type': membership_type,
        'membership_id': membership_id,
        'characters': characters,
        'triumph_score': triumph_score,
        'lifetime_score': lifetime_score,
        'metrics': metrics_data,
        'recent_activities': recent_activities,
    }
    return render(request, 'players/detail.html', context)
