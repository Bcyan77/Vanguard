from django.contrib import admin

from .models import (
    DestinyPlayer,
    DestinyCharacter,
    PlayerTriumphSnapshot,
    CharacterLightSnapshot,
)


@admin.register(DestinyPlayer)
class DestinyPlayerAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'membership_type',
        'membership_id',
        'active_triumph_score',
        'lifetime_triumph_score',
        'last_updated',
    ]
    list_filter = ['membership_type']
    search_fields = ['display_name', 'bungie_global_display_name', 'membership_id']
    readonly_fields = ['first_seen', 'last_updated']


@admin.register(DestinyCharacter)
class DestinyCharacterAdmin(admin.ModelAdmin):
    list_display = ['player', 'class_type', 'light_level', 'date_last_played']
    list_filter = ['class_type']
    search_fields = ['player__display_name', 'character_id']
    readonly_fields = ['first_seen', 'last_updated']


@admin.register(PlayerTriumphSnapshot)
class PlayerTriumphSnapshotAdmin(admin.ModelAdmin):
    list_display = ['player', 'snapshot_date', 'active_triumph_score', 'lifetime_triumph_score']
    list_filter = ['snapshot_date']
    date_hierarchy = 'snapshot_date'


@admin.register(CharacterLightSnapshot)
class CharacterLightSnapshotAdmin(admin.ModelAdmin):
    list_display = ['character', 'snapshot_date', 'light_level']
    list_filter = ['snapshot_date']
    date_hierarchy = 'snapshot_date'
