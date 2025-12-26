import math
import statistics as py_statistics
from datetime import date

from django.db.models import Avg, Count, StdDev, Sum, Max, Min
from django.utils.dateparse import parse_datetime

try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

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


def calculate_extended_statistics(values):
    """
    확장 기술 통계 계산 (중위값, 사분위수, 왜도, 첨도).

    Args:
        values: 숫자 리스트

    Returns:
        dict with median, q1, q3, skewness, kurtosis, min, max
    """
    if not values or len(values) < 2:
        return {
            'median': None,
            'q1': None,
            'q3': None,
            'min': None,
            'max': None,
            'skewness': None,
            'kurtosis': None,
        }

    sorted_values = sorted(values)
    n = len(sorted_values)

    # 중위값
    median = py_statistics.median(sorted_values)

    # 사분위수 (Q1, Q3)
    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    q1 = sorted_values[q1_idx] if q1_idx < n else sorted_values[0]
    q3 = sorted_values[q3_idx] if q3_idx < n else sorted_values[-1]

    # 최소/최대
    min_val = sorted_values[0]
    max_val = sorted_values[-1]

    # 왜도(skewness)와 첨도(kurtosis) - scipy 사용 가능시
    skewness = None
    kurtosis = None

    if SCIPY_AVAILABLE and len(values) >= 3:
        try:
            skewness = float(scipy_stats.skew(values))
            kurtosis = float(scipy_stats.kurtosis(values))
        except Exception:
            pass

    return {
        'median': median,
        'q1': q1,
        'q3': q3,
        'min': min_val,
        'max': max_val,
        'skewness': skewness,
        'kurtosis': kurtosis,
    }


def calculate_class_statistics():
    """
    클래스별 통계 계산.

    Returns:
        dict: {"titan": {...}, "hunter": {...}, "warlock": {...}}
    """
    class_names = {0: 'titan', 1: 'hunter', 2: 'warlock'}
    class_stats = {}

    for class_type, class_name in class_names.items():
        light_values = list(
            DestinyCharacter.objects.filter(
                class_type=class_type,
                light_level__gt=0
            ).values_list('light_level', flat=True)
        )

        if light_values:
            extended = calculate_extended_statistics(light_values)
            class_stats[class_name] = {
                'count': len(light_values),
                'mean': sum(light_values) / len(light_values),
                'std': py_statistics.stdev(light_values) if len(light_values) > 1 else 0,
                'median': extended['median'],
                'q1': extended['q1'],
                'q3': extended['q3'],
                'min': extended['min'],
                'max': extended['max'],
                'skewness': extended['skewness'],
                'kurtosis': extended['kurtosis'],
            }
        else:
            class_stats[class_name] = {
                'count': 0,
                'mean': 0,
                'std': 0,
                'median': None,
                'q1': None,
                'q3': None,
                'min': None,
                'max': None,
                'skewness': None,
                'kurtosis': None,
            }

    return class_stats


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
    light_extended = calculate_extended_statistics(light_values)

    # Triumph Score 통계 (플레이어 단위)
    triumph_stats = DestinyPlayer.objects.filter(active_triumph_score__gt=0).aggregate(
        avg=Avg('active_triumph_score'),
        stddev=StdDev('active_triumph_score'),
    )

    triumph_values = list(DestinyPlayer.objects.filter(
        active_triumph_score__gt=0
    ).values_list('active_triumph_score', flat=True))
    triumph_distribution = calculate_distribution_buckets(triumph_values, bucket_size=5000)
    triumph_extended = calculate_extended_statistics(triumph_values)

    # Class Distribution
    class_counts = DestinyCharacter.objects.values('class_type').annotate(count=Count('id'))
    class_dist = {0: 0, 1: 0, 2: 0}
    for item in class_counts:
        if item['class_type'] in class_dist:
            class_dist[item['class_type']] = item['count']

    # Class-wise Statistics
    class_statistics = calculate_class_statistics()

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
        playtime_extended = calculate_extended_statistics(playtime_hours)
    else:
        playtime_stats = {'avg': 0, 'stddev': 0}
        playtime_distribution = {}
        playtime_extended = {
            'median': None, 'q1': None, 'q3': None,
            'min': None, 'max': None, 'skewness': None, 'kurtosis': None
        }

    # 캐시 업데이트 또는 생성
    cache, _ = GlobalStatisticsCache.objects.update_or_create(
        pk=1,
        defaults={
            # Light Level
            'avg_light_level': light_stats['avg'] or 0,
            'stddev_light_level': light_stats['stddev'] or 0,
            'median_light_level': light_extended['median'],
            'q1_light_level': light_extended['q1'],
            'q3_light_level': light_extended['q3'],
            'min_light_level': light_extended['min'],
            'max_light_level': light_extended['max'],
            'skewness_light_level': light_extended['skewness'],
            'kurtosis_light_level': light_extended['kurtosis'],
            'light_level_distribution': light_distribution,

            # Triumph Score
            'avg_triumph_score': triumph_stats['avg'] or 0,
            'stddev_triumph_score': triumph_stats['stddev'] or 0,
            'median_triumph_score': triumph_extended['median'],
            'q1_triumph_score': triumph_extended['q1'],
            'q3_triumph_score': triumph_extended['q3'],
            'min_triumph_score': triumph_extended['min'],
            'max_triumph_score': triumph_extended['max'],
            'skewness_triumph_score': triumph_extended['skewness'],
            'kurtosis_triumph_score': triumph_extended['kurtosis'],
            'triumph_score_distribution': triumph_distribution,

            # Class
            'titan_count': class_dist[0],
            'hunter_count': class_dist[1],
            'warlock_count': class_dist[2],
            'class_statistics': class_statistics,

            # Play Time
            'avg_play_time_hours': playtime_stats['avg'],
            'stddev_play_time_hours': playtime_stats['stddev'],
            'median_play_time_hours': playtime_extended['median'],
            'q1_play_time_hours': playtime_extended['q1'],
            'q3_play_time_hours': playtime_extended['q3'],
            'skewness_play_time_hours': playtime_extended['skewness'],
            'kurtosis_play_time_hours': playtime_extended['kurtosis'],
            'play_time_distribution': playtime_distribution,

            # Metadata
            'total_players': DestinyPlayer.objects.count(),
            'total_characters': DestinyCharacter.objects.count(),
        }
    )

    # 파워캡 업데이트 (별도로 처리하여 API 호출 실패 시에도 통계는 저장됨)
    _update_power_cap(cache)

    return cache


def _update_power_cap(cache):
    """
    Bungie API에서 현재 시즌 파워캡을 조회하여 캐시에 저장.
    API 호출 실패 시에도 기존 값 유지.
    """
    from .bungie_api import get_current_power_cap, get_power_cap_from_settings
    import logging

    logger = logging.getLogger(__name__)

    # 방법 1: Settings API에서 직접 조회
    power_cap = get_power_cap_from_settings()

    # 방법 2: Manifest에서 조회 (fallback)
    if not power_cap:
        result = get_current_power_cap()
        if result:
            power_cap = result.get('power_cap')
            season_hash = result.get('season_hash', '')
            if power_cap:
                cache.current_power_cap = power_cap
                cache.power_cap_season_hash = season_hash
                cache.save(update_fields=['current_power_cap', 'power_cap_season_hash'])
                logger.info(f"Updated power cap to {power_cap} (season: {season_hash})")
                return

    if power_cap:
        cache.current_power_cap = power_cap
        cache.save(update_fields=['current_power_cap'])
        logger.info(f"Updated power cap to {power_cap}")


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


# ============================================================
# Gamification 관련 함수
# ============================================================

# 기본 배지 정의 (max_power 제외)
_BASE_BADGES = {
    # 순위 기반 배지
    'brightest': {
        'id': 'brightest',
        'name': 'Brightest',
        'description': 'Light Level Top 10%',
        'icon': '⭐',
        'color': '#FFD700',
        'category': 'rank',
    },
    'veteran': {
        'id': 'veteran',
        'name': 'Veteran',
        'description': 'Light Level Top 25%',
        'icon': '⭐',
        'color': '#4CAF50',
        'category': 'rank',
    },
    'rising_star': {
        'id': 'rising_star',
        'name': 'Rising Star',
        'description': 'Light Level Top 50%',
        'icon': '⭐',
        'color': '#2196F3',
        'category': 'rank',
    },
    'collector': {
        'id': 'collector',
        'name': 'Collector',
        'description': 'Triumph Score Top 10%',
        'icon': '🏆',
        'color': '#FFD700',
        'category': 'rank',
    },
    'dedicated': {
        'id': 'dedicated',
        'name': 'Dedicated',
        'description': 'Play Time Top 10%',
        'icon': '⏱️',
        'color': '#FFD700',
        'category': 'rank',
    },
    # 달성 기반 배지
    'trinity': {
        'id': 'trinity',
        'name': 'Trinity',
        'description': 'Own all 3 classes',
        'icon': '🔺',
        'color': '#9C27B0',
        'category': 'achievement',
    },
    'balanced': {
        'id': 'balanced',
        'name': 'Balanced',
        'description': 'All characters within 50 Light Level',
        'icon': '⚖️',
        'color': '#00BCD4',
        'category': 'achievement',
    },
}


def get_cached_power_cap():
    """캐시된 파워 캡 값 조회. 없으면 기본값 반환."""
    try:
        cache = GlobalStatisticsCache.objects.get(pk=1)
        return cache.current_power_cap
    except GlobalStatisticsCache.DoesNotExist:
        return 2000  # 기본값


def get_badge_definitions(power_cap=None):
    """
    배지 정의를 동적으로 생성.
    max_power 배지의 description이 현재 파워캡에 따라 변경됨.

    Args:
        power_cap: 파워캡 값 (None이면 캐시에서 조회)

    Returns:
        dict: 배지 정의
    """
    if power_cap is None:
        power_cap = get_cached_power_cap()

    return _BASE_BADGES.copy()


# 하위 호환성을 위한 BADGES 변수 (동적으로 생성)
def _get_badges():
    return get_badge_definitions()


# API 등에서 BADGES를 직접 참조할 때를 위한 프로퍼티
class _BadgesProxy:
    """BADGES 상수를 동적으로 조회하는 프록시 클래스."""

    def __getitem__(self, key):
        return get_badge_definitions()[key]

    def __iter__(self):
        return iter(get_badge_definitions())

    def values(self):
        return get_badge_definitions().values()

    def keys(self):
        return get_badge_definitions().keys()

    def items(self):
        return get_badge_definitions().items()

    def get(self, key, default=None):
        return get_badge_definitions().get(key, default)


BADGES = _BadgesProxy()


def get_leaderboard(category='light_level', limit=10):
    """
    리더보드 데이터 조회.

    Args:
        category: 'light_level', 'triumph_score', 'play_time' 중 하나
        limit: 표시할 플레이어 수 (기본 10)

    Returns:
        list of dict: [{rank, player_id, display_name, platform, value}, ...]
    """
    if category == 'light_level':
        # 플레이어별 최고 라이트 레벨
        players = DestinyPlayer.objects.prefetch_related('characters').all()
        player_data = []
        for player in players:
            max_light = player.characters.aggregate(max_light=Max('light_level'))['max_light']
            if max_light and max_light > 0:
                player_data.append({
                    'player_id': player.id,
                    'membership_id': player.membership_id,
                    'membership_type': player.membership_type,
                    'display_name': str(player),
                    'platform': player.get_platform_display(),
                    'value': max_light,
                })
        player_data.sort(key=lambda x: x['value'], reverse=True)

    elif category == 'triumph_score':
        players = DestinyPlayer.objects.filter(
            active_triumph_score__gt=0
        ).order_by('-active_triumph_score')[:limit]

        player_data = [{
            'player_id': p.id,
            'membership_id': p.membership_id,
            'membership_type': p.membership_type,
            'display_name': str(p),
            'platform': p.get_platform_display(),
            'value': p.active_triumph_score,
        } for p in players]

    elif category == 'play_time':
        # 플레이어별 총 플레이 시간
        players = DestinyPlayer.objects.prefetch_related('characters').all()
        player_data = []
        for player in players:
            total_minutes = player.characters.aggregate(total=Sum('minutes_played_total'))['total']
            if total_minutes and total_minutes > 0:
                player_data.append({
                    'player_id': player.id,
                    'membership_id': player.membership_id,
                    'membership_type': player.membership_type,
                    'display_name': str(player),
                    'platform': player.get_platform_display(),
                    'value': round(total_minutes / 60.0, 1),  # 시간 단위
                })
        player_data.sort(key=lambda x: x['value'], reverse=True)

    else:
        return []

    # 순위 추가 및 limit 적용
    result = []
    for idx, data in enumerate(player_data[:limit], 1):
        data['rank'] = idx
        result.append(data)

    return result


def calculate_badges(player):
    """
    플레이어의 배지 계산.

    Args:
        player: DestinyPlayer 인스턴스

    Returns:
        list of dict: 획득한 배지 목록
    """
    earned_badges = []

    # 통계 캐시 가져오기
    try:
        cache = GlobalStatisticsCache.objects.get(pk=1)
    except GlobalStatisticsCache.DoesNotExist:
        cache = refresh_global_statistics()

    # 플레이어 데이터
    characters = player.characters.all()
    if not characters:
        return earned_badges

    max_light = max((c.light_level for c in characters), default=0)
    triumph_score = player.active_triumph_score
    total_minutes = sum(c.minutes_played_total for c in characters)
    play_time_hours = total_minutes / 60.0

    # 백분위 계산
    light_z = calculate_z_score(max_light, cache.avg_light_level, cache.stddev_light_level)
    triumph_z = calculate_z_score(triumph_score, cache.avg_triumph_score, cache.stddev_triumph_score)
    playtime_z = calculate_z_score(play_time_hours, cache.avg_play_time_hours, cache.stddev_play_time_hours)

    light_percentile = calculate_percentile_from_zscore(light_z)
    triumph_percentile = calculate_percentile_from_zscore(triumph_z)
    playtime_percentile = calculate_percentile_from_zscore(playtime_z)

    # 순위 기반 배지
    if light_percentile >= 90:
        earned_badges.append(BADGES['brightest'])
    elif light_percentile >= 75:
        earned_badges.append(BADGES['veteran'])
    elif light_percentile >= 50:
        earned_badges.append(BADGES['rising_star'])

    if triumph_percentile >= 90:
        earned_badges.append(BADGES['collector'])

    if playtime_percentile >= 90:
        earned_badges.append(BADGES['dedicated'])

    # 달성 기반 배지
    class_types = set(c.class_type for c in characters)
    if len(class_types) == 3:
        earned_badges.append(BADGES['trinity'])

    # Balanced 배지: 모든 캐릭터 라이트 레벨 차이 50 이하
    light_levels = [c.light_level for c in characters if c.light_level > 0]
    if len(light_levels) >= 2:
        if max(light_levels) - min(light_levels) <= 50:
            earned_badges.append(BADGES['balanced'])

    return earned_badges


def get_radar_chart_data(player):
    """
    레이더 차트용 정규화 데이터 생성.

    Args:
        player: DestinyPlayer 인스턴스

    Returns:
        dict: {labels, values, max_value}
    """
    # 통계 캐시
    try:
        cache = GlobalStatisticsCache.objects.get(pk=1)
    except GlobalStatisticsCache.DoesNotExist:
        cache = refresh_global_statistics()

    characters = player.characters.all()
    if not characters:
        return {
            'labels': ['Light Level', 'Triumph', 'Play Time', 'Characters', 'Versatility'],
            'values': [0, 0, 0, 0, 0],
            'max_value': 100,
        }

    # 플레이어 데이터
    max_light = max((c.light_level for c in characters), default=0)
    triumph_score = player.active_triumph_score
    total_minutes = sum(c.minutes_played_total for c in characters)
    play_time_hours = total_minutes / 60.0
    char_count = len(characters)
    class_types = set(c.class_type for c in characters)
    versatility = len(class_types)

    # 백분위 계산 (0-100 스케일)
    light_z = calculate_z_score(max_light, cache.avg_light_level, cache.stddev_light_level)
    triumph_z = calculate_z_score(triumph_score, cache.avg_triumph_score, cache.stddev_triumph_score)
    playtime_z = calculate_z_score(play_time_hours, cache.avg_play_time_hours, cache.stddev_play_time_hours)

    light_percentile = min(100, max(0, calculate_percentile_from_zscore(light_z)))
    triumph_percentile = min(100, max(0, calculate_percentile_from_zscore(triumph_z)))
    playtime_percentile = min(100, max(0, calculate_percentile_from_zscore(playtime_z)))

    # 캐릭터 수 (1-3 → 33/66/100)
    char_score = min(100, (char_count / 3) * 100)

    # Versatility (클래스 다양성, 1-3 → 33/66/100)
    versatility_score = min(100, (versatility / 3) * 100)

    return {
        'labels': ['Light Level', 'Triumph', 'Play Time', 'Characters', 'Versatility'],
        'values': [
            round(light_percentile, 1),
            round(triumph_percentile, 1),
            round(playtime_percentile, 1),
            round(char_score, 1),
            round(versatility_score, 1),
        ],
        'max_value': 100,
    }


def get_user_rank_in_leaderboard(user, category='light_level'):
    """
    사용자의 리더보드 내 순위 조회.

    Args:
        user: 현재 로그인한 사용자
        category: 'light_level', 'triumph_score', 'play_time' 중 하나

    Returns:
        dict: {rank, total, value} or None
    """
    try:
        player = DestinyPlayer.objects.get(
            membership_id=user.bungie_membership_id,
            membership_type=user.bungie_membership_type
        )
    except DestinyPlayer.DoesNotExist:
        return None

    # 전체 리더보드 데이터
    full_leaderboard = get_leaderboard(category, limit=9999)

    for entry in full_leaderboard:
        if entry['membership_id'] == player.membership_id:
            return {
                'rank': entry['rank'],
                'total': len(full_leaderboard),
                'value': entry['value'],
            }

    return None


def get_filtered_player_count(min_playtime_hours=0, min_light_level=0):
    """
    필터링된 플레이어 수 반환.

    Args:
        min_playtime_hours: 최소 플레이 시간 (시간)
        min_light_level: 최소 라이트 레벨

    Returns:
        dict: {total_players, filtered_count}
    """
    raw_data = get_raw_player_data()
    filtered = [
        p for p in raw_data
        if p['playTimeHours'] >= min_playtime_hours
        and p['maxLight'] >= min_light_level
    ]
    return {
        'total_players': len(raw_data),
        'filtered_count': len(filtered),
    }
