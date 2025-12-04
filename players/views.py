"""
Player search views
"""
import json

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .bungie_api import (
    search_by_bungie_name,
    search_by_prefix,
    get_player_profile,
    get_all_characters_activities,
    get_class_name,
    get_platform_info,
    get_activity_name,
)
from .models import GlobalStatisticsCache
from .services import sync_player_from_api, get_user_statistics_position, refresh_global_statistics, get_raw_player_data


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


def player_statistics(request):
    """
    Display global player statistics including:
    - Total players and characters tracked
    - Average power level, triumph score, play time
    - User's percentile position
    - Class distribution
    - Distribution charts with filtering
    """
    # 통계 데이터 가져오기
    stats_cache = None
    user_position = None

    try:
        stats_cache = GlobalStatisticsCache.objects.get(pk=1)
        # 1시간 초과시 갱신
        if (timezone.now() - stats_cache.last_updated).total_seconds() > 3600:
            stats_cache = refresh_global_statistics()
    except GlobalStatisticsCache.DoesNotExist:
        stats_cache = refresh_global_statistics()

    # 사용자 위치 계산 (로그인한 경우에만)
    if stats_cache and stats_cache.total_players > 0 and request.user.is_authenticated:
        user_position = get_user_statistics_position(request.user)

    # 직업 분포 비율 계산
    class_distribution = None
    if stats_cache and stats_cache.total_characters > 0:
        total_chars = stats_cache.titan_count + stats_cache.hunter_count + stats_cache.warlock_count
        if total_chars > 0:
            class_distribution = {
                'Titan': {
                    'count': stats_cache.titan_count,
                    'percent': round(stats_cache.titan_count / total_chars * 100, 1),
                },
                'Hunter': {
                    'count': stats_cache.hunter_count,
                    'percent': round(stats_cache.hunter_count / total_chars * 100, 1),
                },
                'Warlock': {
                    'count': stats_cache.warlock_count,
                    'percent': round(stats_cache.warlock_count / total_chars * 100, 1),
                },
            }

    # 클라이언트 사이드 필터링용 원본 데이터
    raw_player_data = get_raw_player_data() if stats_cache and stats_cache.total_players > 0 else []

    context = {
        # 통계 데이터
        'stats': stats_cache,
        'user_position': user_position,
        'class_distribution': class_distribution,
        # Chart.js용 JSON 데이터
        'light_distribution_json': json.dumps(stats_cache.light_level_distribution) if stats_cache else '{}',
        'triumph_distribution_json': json.dumps(stats_cache.triumph_score_distribution) if stats_cache else '{}',
        'playtime_distribution_json': json.dumps(stats_cache.play_time_distribution) if stats_cache else '{}',
        # 클라이언트 필터링용 원본 데이터
        'raw_player_data_json': json.dumps(raw_player_data),
        # 개발 모드 플래그
        'debug': settings.DEBUG,
    }
    return render(request, 'players/statistics.html', context)


@login_required
@require_POST
def refresh_stats(request):
    """
    개발용: 통계 캐시 강제 새로고침
    DEBUG 모드에서만 동작
    """
    if settings.DEBUG:
        refresh_global_statistics()
        messages.success(request, 'Statistics refreshed successfully.')
    return redirect('players:statistics')


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

        # Add character class and activity name to activities
        char_class_map = {c['characterId']: c['className'] for c in characters}
        for activity in recent_activities:
            activity['characterClass'] = char_class_map.get(activity.get('characterId'), 'Unknown')
            activity_hash = activity.get('activityDetails', {}).get('referenceId')
            activity['activityName'] = get_activity_name(activity_hash) if activity_hash else 'Unknown Activity'

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
