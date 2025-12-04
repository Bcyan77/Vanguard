from datetime import date

from django.utils.dateparse import parse_datetime

from .models import (
    DestinyPlayer,
    DestinyCharacter,
    PlayerTriumphSnapshot,
    CharacterLightSnapshot,
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
