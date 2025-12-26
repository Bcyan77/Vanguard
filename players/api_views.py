from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils import timezone

from .models import GlobalStatisticsCache
from .serializers import (
    DestinyPlayerListSerializer, DestinyPlayerDetailSerializer,
    PlayerSearchResultSerializer
)
from .bungie_api import (
    search_by_bungie_name,
    search_by_prefix,
    get_player_profile,
    get_all_characters_activities,
    get_class_name,
    get_platform_info,
    get_activity_name,
)
from .services import (
    sync_player_from_api,
    refresh_global_statistics,
    get_leaderboard,
    calculate_badges,
    get_radar_chart_data,
    get_user_rank_in_leaderboard,
    BADGES,
)
from .models import DestinyPlayer
from .statistics_service import (
    class_light_level_anova,
    light_triumph_correlation,
    get_class_boxplot_data,
    get_all_hypothesis_tests,
)
from fireteams.serializers import ErrorResponseSerializer


class PlayerSearchAPIView(APIView):
    """
    API endpoint for searching Destiny 2 players.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Search for players",
        description="Search for Destiny 2 players by Bungie Name. Use 'Name#1234' for exact search or partial name for prefix search.",
        parameters=[
            OpenApiParameter(name='q', type=str, required=True, description='Search query (e.g., "PlayerName#1234" for exact or "PlayerName" for prefix)')
        ],
        responses={
            200: PlayerSearchResultSerializer(many=True),
            400: ErrorResponseSerializer,
        },
        tags=['Players']
    )
    def get(self, request):
        query = request.GET.get('q', '').strip()

        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        error = None

        if '#' in query:
            # Exact search: PlayerName#1234
            results, error = search_by_bungie_name(query)
        else:
            # Prefix search: partial name
            results, error = search_by_prefix(query)

        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Add platform info to results
        for result in results:
            platform = get_platform_info(result.get('membershipType'))
            result['platformName'] = platform['name']
            result['platformIcon'] = platform['icon']

        return Response({
            'query': query,
            'search_type': 'exact' if '#' in query else 'prefix',
            'count': len(results),
            'results': results
        })


class PlayerDetailAPIView(APIView):
    """
    API endpoint for getting player details.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get player details",
        description="Get detailed information about a Destiny 2 player including characters, triumph scores, and recent activities.",
        responses={
            200: DestinyPlayerDetailSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Players']
    )
    def get(self, request, membership_type, membership_id):
        # Get profile data from Bungie API
        profile = get_player_profile(membership_type, membership_id)

        if not profile:
            return Response(
                {'error': 'Failed to load player profile. The profile may be private or unavailable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Sync player data to database
        db_player = sync_player_from_api(membership_type, membership_id, profile)

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

        # Get recent activities for all characters
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

        return Response({
            'userInfo': user_info,
            'platform': platform,
            'membershipType': membership_type,
            'membershipId': membership_id,
            'characters': characters,
            'triumphScore': triumph_score,
            'lifetimeScore': lifetime_score,
            'metrics': metrics_data,
            'recentActivities': recent_activities,
            # Database cached data
            'cachedPlayer': DestinyPlayerDetailSerializer(db_player).data if db_player else None
        })


class StatisticsDescriptiveAPIView(APIView):
    """
    기술 통계 API - 전체 공개 (인증 불필요)
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get descriptive statistics",
        description="Get descriptive statistics for player data including mean, median, quartiles, skewness, and kurtosis.",
        responses={200: dict},
        tags=['Statistics']
    )
    def get(self, request):
        # 캐시된 통계 가져오기 또는 새로 계산
        try:
            cache = GlobalStatisticsCache.objects.get(pk=1)
            # 1시간 이상 지났으면 갱신
            if (timezone.now() - cache.last_updated).total_seconds() > 3600:
                cache = refresh_global_statistics()
        except GlobalStatisticsCache.DoesNotExist:
            cache = refresh_global_statistics()

        return Response({
            'metadata': {
                'generated_at': cache.last_updated.isoformat(),
                'total_players': cache.total_players,
                'total_characters': cache.total_characters,
            },
            'light_level': {
                'mean': round(cache.avg_light_level, 2) if cache.avg_light_level else None,
                'std': round(cache.stddev_light_level, 2) if cache.stddev_light_level else None,
                'median': cache.median_light_level,
                'q1': cache.q1_light_level,
                'q3': cache.q3_light_level,
                'min': cache.min_light_level,
                'max': cache.max_light_level,
                'skewness': round(cache.skewness_light_level, 4) if cache.skewness_light_level else None,
                'kurtosis': round(cache.kurtosis_light_level, 4) if cache.kurtosis_light_level else None,
            },
            'triumph_score': {
                'mean': round(cache.avg_triumph_score, 2) if cache.avg_triumph_score else None,
                'std': round(cache.stddev_triumph_score, 2) if cache.stddev_triumph_score else None,
                'median': cache.median_triumph_score,
                'q1': cache.q1_triumph_score,
                'q3': cache.q3_triumph_score,
                'min': cache.min_triumph_score,
                'max': cache.max_triumph_score,
                'skewness': round(cache.skewness_triumph_score, 4) if cache.skewness_triumph_score else None,
                'kurtosis': round(cache.kurtosis_triumph_score, 4) if cache.kurtosis_triumph_score else None,
            },
            'play_time_hours': {
                'mean': round(cache.avg_play_time_hours, 2) if cache.avg_play_time_hours else None,
                'std': round(cache.stddev_play_time_hours, 2) if cache.stddev_play_time_hours else None,
                'median': round(cache.median_play_time_hours, 2) if cache.median_play_time_hours else None,
                'q1': round(cache.q1_play_time_hours, 2) if cache.q1_play_time_hours else None,
                'q3': round(cache.q3_play_time_hours, 2) if cache.q3_play_time_hours else None,
                'skewness': round(cache.skewness_play_time_hours, 4) if cache.skewness_play_time_hours else None,
                'kurtosis': round(cache.kurtosis_play_time_hours, 4) if cache.kurtosis_play_time_hours else None,
            },
            'class_distribution': {
                'titan': cache.titan_count,
                'hunter': cache.hunter_count,
                'warlock': cache.warlock_count,
            },
        })


class StatisticsClassComparisonAPIView(APIView):
    """
    클래스별 비교 통계 API - 전체 공개 (인증 불필요)
    ANOVA 검정 결과 포함
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get class comparison statistics",
        description="Get class-wise statistics and ANOVA test results for light level comparison.",
        responses={200: dict},
        tags=['Statistics']
    )
    def get(self, request):
        # 캐시된 클래스 통계
        try:
            cache = GlobalStatisticsCache.objects.get(pk=1)
            class_stats = cache.class_statistics or {}
        except GlobalStatisticsCache.DoesNotExist:
            cache = refresh_global_statistics()
            class_stats = cache.class_statistics or {}

        # ANOVA 검정 수행
        anova_result = class_light_level_anova()

        # 박스플롯 데이터
        boxplot_data = get_class_boxplot_data()

        return Response({
            'metadata': {
                'generated_at': timezone.now().isoformat(),
            },
            'class_statistics': class_stats,
            'hypothesis_test': anova_result,
            'visualization_data': boxplot_data,
        })


class StatisticsCorrelationAPIView(APIView):
    """
    상관관계 분석 API - 전체 공개 (인증 불필요)
    빛 레벨과 승리 점수 간 Pearson 상관관계
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get correlation analysis",
        description="Get Pearson correlation analysis between light level and triumph score.",
        responses={200: dict},
        tags=['Statistics']
    )
    def get(self, request):
        correlation_result = light_triumph_correlation()

        return Response({
            'metadata': {
                'generated_at': timezone.now().isoformat(),
            },
            'correlation_analysis': correlation_result,
        })


class StatisticsDistributionAPIView(APIView):
    """
    분포 데이터 API - 전체 공개 (인증 불필요)
    시각화용 히스토그램 데이터
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get distribution data",
        description="Get distribution data for visualization (histograms).",
        responses={200: dict},
        tags=['Statistics']
    )
    def get(self, request):
        try:
            cache = GlobalStatisticsCache.objects.get(pk=1)
        except GlobalStatisticsCache.DoesNotExist:
            cache = refresh_global_statistics()

        return Response({
            'metadata': {
                'generated_at': cache.last_updated.isoformat(),
            },
            'light_level_distribution': cache.light_level_distribution,
            'triumph_score_distribution': cache.triumph_score_distribution,
            'play_time_distribution': cache.play_time_distribution,
        })


class StatisticsHypothesisTestsAPIView(APIView):
    """
    전체 가설 검정 결과 API - 전체 공개 (인증 불필요)
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get all hypothesis test results",
        description="Get all hypothesis test results including ANOVA and correlation analysis.",
        responses={200: dict},
        tags=['Statistics']
    )
    def get(self, request):
        all_tests = get_all_hypothesis_tests()

        return Response({
            'metadata': {
                'generated_at': timezone.now().isoformat(),
            },
            'tests': all_tests,
        })


class LeaderboardAPIView(APIView):
    """
    리더보드 API - 전체 공개
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get leaderboard",
        description="Get top players leaderboard by category (light_level, triumph_score, play_time).",
        parameters=[
            OpenApiParameter(
                name='category',
                type=str,
                required=False,
                description='Leaderboard category: light_level (default), triumph_score, play_time'
            ),
            OpenApiParameter(
                name='limit',
                type=int,
                required=False,
                description='Number of players to return (default: 10, max: 100)'
            ),
        ],
        responses={200: dict},
        tags=['Statistics']
    )
    def get(self, request):
        category = request.GET.get('category', 'light_level')
        try:
            limit = min(int(request.GET.get('limit', 10)), 100)
        except ValueError:
            limit = 10

        valid_categories = ['light_level', 'triumph_score', 'play_time']
        if category not in valid_categories:
            return Response(
                {'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        leaderboard = get_leaderboard(category, limit)

        # 로그인한 사용자의 순위 포함
        user_rank = None
        if request.user.is_authenticated:
            user_rank = get_user_rank_in_leaderboard(request.user, category)

        return Response({
            'category': category,
            'leaderboard': leaderboard,
            'user_rank': user_rank,
        })


class BadgesAPIView(APIView):
    """
    배지 정보 API
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get all badge definitions",
        description="Get all available badge definitions.",
        responses={200: dict},
        tags=['Gamification']
    )
    def get(self, request):
        return Response({
            'badges': list(BADGES.values()),
        })
