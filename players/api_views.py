from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import DestinyPlayer
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
from .services import sync_player_from_api
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
