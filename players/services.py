import math
import statistics as py_statistics
from datetime import date

from django.db.models import Avg, Count, StdDev, Sum, Max
from django.utils.dateparse import parse_datetime

from .models import (
    DestinyPlayer,
    DestinyCharacter,
    PlayerTriumphSnapshot,
    CharacterLightSnapshot,
    GlobalStatisticsCache,
)


def sync_player_from_api(membership_type, membership_id, profile_data):
    """
    Bungie API 응답 데이터를 DB에 저장/업데이트.

    Args:
        membership_type: 플랫폼 타입 (int)
        membership_id: 플레이어 membership ID (str)
        profile_data: get_player_profile() API 응답

    Returns:
        DestinyPlayer 인스턴스
    """
    profile_info = profile_data.get('profile', {}).get('data', {})
    user_info = profile_info.get('userInfo', {})
    characters_data = profile_data.get('characters', {}).get('data', {})
    profile_records = profile_data.get('profileRecords', {}).get('data', {})

    player, created = DestinyPlayer.objects.update_or_create(
        membership_id=membership_id,
        membership_type=membership_type,
        defaults={
            'display_name': user_info.get('displayName', ''),
            'bungie_global_display_name': user_info.get('bungieGlobalDisplayName'),
            'bungie_global_display_name_code': str(user_info.get('bungieGlobalDisplayNameCode', '') or ''),
            'icon_path': user_info.get('iconPath', ''),
            'active_triumph_score': profile_records.get('activeScore', 0),
            'lifetime_triumph_score': profile_records.get('lifetimeScore', 0),
        }
    )

    today = date.today()
    PlayerTriumphSnapshot.objects.update_or_create(
        player=player,
        snapshot_date=today,
        defaults={
            'active_triumph_score': profile_records.get('activeScore', 0),
            'lifetime_triumph_score': profile_records.get('lifetimeScore', 0),
        }
    )

    sync_characters(player, characters_data)

    return player


def sync_characters(player, characters_data):
    """
    캐릭터 데이터 동기화.

    Args:
        player: DestinyPlayer 인스턴스
        characters_data: 캐릭터 ID -> 캐릭터 데이터 딕셔너리
    """
    today = date.today()

    for char_id, char_data in characters_data.items():
        date_last_played = None
        if char_data.get('dateLastPlayed'):
            try:
                date_last_played = parse_datetime(char_data['dateLastPlayed'])
            except (ValueError, TypeError):
                pass

        character, created = DestinyCharacter.objects.update_or_create(
            player=player,
            character_id=char_id,
            defaults={
                'class_type': char_data.get('classType', 0),
                'race_type': char_data.get('raceType'),
                'gender_type': char_data.get('genderType'),
                'light_level': char_data.get('light', 0),
                'minutes_played_total': int(char_data.get('minutesPlayedTotal', 0)),
                'emblem_path': char_data.get('emblemPath', ''),
                'emblem_background_path': char_data.get('emblemBackgroundPath', ''),
                'date_last_played': date_last_played,
            }
        )

        CharacterLightSnapshot.objects.update_or_create(
            character=character,
            snapshot_date=today,
            defaults={
                'light_level': char_data.get('light', 0),
            }
        )


def get_player_stats(player):
    """
    플레이어 통계 데이터 조회 (향후 활용).

    Returns:
        dict: triumph_trend, light_trends
    """
    triumph_snapshots = player.triumph_snapshots.order_by('snapshot_date')[:30]
    triumph_trend = [
        (s.snapshot_date, s.active_triumph_score)
        for s in triumph_snapshots
    ]

    light_trends = {}
    for character in player.characters.all():
        snapshots = character.light_snapshots.order_by('snapshot_date')[:30]
        light_trends[character.character_id] = [
            (s.snapshot_date, s.light_level)
            for s in snapshots
        ]

    return {
        'triumph_trend': triumph_trend,
        'light_trends': light_trends,
    }


def calculate_z_score(value, mean, stddev):
    """Z-score 계산 (표준편차로부터의 거리)"""
    if stddev == 0 or stddev is None or mean is None:
        return 0
    return (value - mean) / stddev


def calculate_percentile_from_zscore(z_score):
    """Z-score를 백분위로 변환 (정규분포 기반)"""
    return 0.5 * (1 + math.erf(z_score / math.sqrt(2))) * 100


def calculate_distribution_buckets(values, bucket_size):
    """
    값들을 버킷으로 그룹화하여 히스토그램 데이터 생성.
    Returns: dict {bucket_label: count}
    """
    if not values:
        return {}

    buckets = {}
    for value in values:
        bucket_start = int(value // bucket_size) * bucket_size
        bucket_label = f"{bucket_start}"
        buckets[bucket_label] = buckets.get(bucket_label, 0) + 1

    # 정렬하여 반환
    return dict(sorted(buckets.items(), key=lambda x: int(x[0])))


def get_raw_player_data():
    """
    클라이언트 사이드 필터링을 위한 원본 플레이어 데이터 반환.
    Returns: list of player dicts with stats
    """
    players = DestinyPlayer.objects.prefetch_related('characters').all()
    raw_data = []

    for player in players:
        characters = player.characters.all()
        if not characters:
            continue

        max_light = max((c.light_level for c in characters), default=0)
        total_minutes = sum(c.minutes_played_total for c in characters)

        char_data = []
        for c in characters:
            char_data.append({
                'classType': c.class_type,
                'light': c.light_level,
                'minutes': c.minutes_played_total,
            })

        raw_data.append({
            'playerId': player.id,
            'playTimeHours': round(total_minutes / 60.0, 1),
            'maxLight': max_light,
            'triumphScore': player.active_triumph_score,
            'characters': char_data,
        })

    return raw_data


def refresh_global_statistics():
    """
    전역 통계 재계산 및 캐시 저장.
    모든 플레이어 데이터 포함 (필터링은 클라이언트에서 처리).
    Returns: GlobalStatisticsCache 인스턴스
    """
    # Light Level 통계 (모든 캐릭터)
    light_stats = DestinyCharacter.objects.filter(light_level__gt=0).aggregate(
        avg=Avg('light_level'),
        stddev=StdDev('light_level'),
    )

    light_values = list(DestinyCharacter.objects.filter(
        light_level__gt=0
    ).values_list('light_level', flat=True))
    light_distribution = calculate_distribution_buckets(light_values, bucket_size=10)

    # Triumph Score 통계 (플레이어 단위)
    triumph_stats = DestinyPlayer.objects.filter(active_triumph_score__gt=0).aggregate(
        avg=Avg('active_triumph_score'),
        stddev=StdDev('active_triumph_score'),
    )

    triumph_values = list(DestinyPlayer.objects.filter(
        active_triumph_score__gt=0
    ).values_list('active_triumph_score', flat=True))
    triumph_distribution = calculate_distribution_buckets(triumph_values, bucket_size=5000)

    # Class Distribution
    class_counts = DestinyCharacter.objects.values('class_type').annotate(count=Count('id'))
    class_dist = {0: 0, 1: 0, 2: 0}
    for item in class_counts:
        if item['class_type'] in class_dist:
            class_dist[item['class_type']] = item['count']

    # Play Time 통계 (플레이어별 총 시간, 시간 단위)
    player_playtimes = DestinyCharacter.objects.values('player').annotate(
        total_minutes=Sum('minutes_played_total')
    ).filter(total_minutes__gt=0)

    playtime_hours = [p['total_minutes'] / 60.0 for p in player_playtimes]

    if playtime_hours:
        playtime_stats = {
            'avg': sum(playtime_hours) / len(playtime_hours),
            'stddev': py_statistics.stdev(playtime_hours) if len(playtime_hours) > 1 else 0,
        }
        playtime_distribution = calculate_distribution_buckets(playtime_hours, bucket_size=100)
    else:
        playtime_stats = {'avg': 0, 'stddev': 0}
        playtime_distribution = {}

    # 캐시 업데이트 또는 생성
    cache, _ = GlobalStatisticsCache.objects.update_or_create(
        pk=1,
        defaults={
            'avg_light_level': light_stats['avg'] or 0,
            'stddev_light_level': light_stats['stddev'] or 0,
            'light_level_distribution': light_distribution,

            'avg_triumph_score': triumph_stats['avg'] or 0,
            'stddev_triumph_score': triumph_stats['stddev'] or 0,
            'triumph_score_distribution': triumph_distribution,

            'titan_count': class_dist[0],
            'hunter_count': class_dist[1],
            'warlock_count': class_dist[2],

            'avg_play_time_hours': playtime_stats['avg'],
            'stddev_play_time_hours': playtime_stats['stddev'],
            'play_time_distribution': playtime_distribution,

            'total_players': DestinyPlayer.objects.count(),
            'total_characters': DestinyCharacter.objects.count(),
        }
    )

    return cache


def get_user_statistics_position(user):
    """
    로그인한 사용자의 각 통계에서의 위치 계산.
    Returns: dict with z_score and percentile for each stat, or None if user not found
    """
    try:
        cache = GlobalStatisticsCache.objects.get(pk=1)
    except GlobalStatisticsCache.DoesNotExist:
        cache = refresh_global_statistics()

    # 사용자의 플레이어 레코드 찾기
    try:
        player = DestinyPlayer.objects.get(
            membership_id=user.bungie_membership_id,
            membership_type=user.bungie_membership_type
        )
    except DestinyPlayer.DoesNotExist:
        return None

    # 사용자 통계 가져오기
    user_max_light = player.characters.aggregate(
        max_light=Max('light_level')
    )['max_light'] or 0

    user_triumph = player.active_triumph_score

    user_playtime_minutes = player.characters.aggregate(
        total=Sum('minutes_played_total')
    )['total'] or 0
    user_playtime_hours = user_playtime_minutes / 60.0

    # Z-score 및 백분위 계산
    light_z = calculate_z_score(user_max_light, cache.avg_light_level, cache.stddev_light_level)
    triumph_z = calculate_z_score(user_triumph, cache.avg_triumph_score, cache.stddev_triumph_score)
    playtime_z = calculate_z_score(user_playtime_hours, cache.avg_play_time_hours, cache.stddev_play_time_hours)

    light_percentile = calculate_percentile_from_zscore(light_z)
    triumph_percentile = calculate_percentile_from_zscore(triumph_z)
    playtime_percentile = calculate_percentile_from_zscore(playtime_z)

    return {
        'light_level': {
            'value': user_max_light,
            'z_score': round(light_z, 2),
            'percentile': round(light_percentile, 1),
            'top_percent': round(100 - light_percentile, 1),
        },
        'triumph_score': {
            'value': user_triumph,
            'z_score': round(triumph_z, 2),
            'percentile': round(triumph_percentile, 1),
            'top_percent': round(100 - triumph_percentile, 1),
        },
        'play_time': {
            'value': round(user_playtime_hours, 1),
            'z_score': round(playtime_z, 2),
            'percentile': round(playtime_percentile, 1),
            'top_percent': round(100 - playtime_percentile, 1),
        },
    }
