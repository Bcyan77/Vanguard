from rest_framework import serializers
from .models import DestinyPlayer, DestinyCharacter


class DestinyCharacterSerializer(serializers.ModelSerializer):
    """Serializer for Destiny Character"""
    class_name = serializers.SerializerMethodField()
    race_name = serializers.SerializerMethodField()
    gender_name = serializers.SerializerMethodField()
    emblem_url = serializers.SerializerMethodField()
    emblem_background_url = serializers.SerializerMethodField()

    class Meta:
        model = DestinyCharacter
        fields = [
            'character_id', 'class_type', 'class_name',
            'race_type', 'race_name', 'gender_type', 'gender_name',
            'light_level', 'emblem_url', 'emblem_background_url',
            'date_last_played', 'last_updated'
        ]

    def get_class_name(self, obj):
        return obj.get_class_type_display()

    def get_race_name(self, obj):
        if obj.race_type is not None:
            return dict(DestinyCharacter.RACE_TYPE_CHOICES).get(obj.race_type, 'Unknown')
        return None

    def get_gender_name(self, obj):
        if obj.gender_type is not None:
            return dict(DestinyCharacter.GENDER_TYPE_CHOICES).get(obj.gender_type, 'Unknown')
        return None

    def get_emblem_url(self, obj):
        if obj.emblem_path:
            return f"https://www.bungie.net{obj.emblem_path}"
        return None

    def get_emblem_background_url(self, obj):
        if obj.emblem_background_path:
            return f"https://www.bungie.net{obj.emblem_background_path}"
        return None


class DestinyPlayerListSerializer(serializers.ModelSerializer):
    """Serializer for Destiny Player list view"""
    platform_name = serializers.SerializerMethodField()
    icon_url = serializers.SerializerMethodField()
    full_bungie_name = serializers.SerializerMethodField()

    class Meta:
        model = DestinyPlayer
        fields = [
            'membership_id', 'membership_type', 'platform_name',
            'display_name', 'bungie_global_display_name', 'bungie_global_display_name_code',
            'full_bungie_name', 'icon_url'
        ]

    def get_platform_name(self, obj):
        return obj.get_platform_display()

    def get_icon_url(self, obj):
        if obj.icon_path:
            return f"https://www.bungie.net{obj.icon_path}"
        return None

    def get_full_bungie_name(self, obj):
        if obj.bungie_global_display_name and obj.bungie_global_display_name_code:
            return f"{obj.bungie_global_display_name}#{obj.bungie_global_display_name_code}"
        return obj.display_name


class DestinyPlayerDetailSerializer(serializers.ModelSerializer):
    """Serializer for Destiny Player detail view"""
    platform_name = serializers.SerializerMethodField()
    icon_url = serializers.SerializerMethodField()
    full_bungie_name = serializers.SerializerMethodField()
    characters = DestinyCharacterSerializer(many=True, read_only=True)

    class Meta:
        model = DestinyPlayer
        fields = [
            'membership_id', 'membership_type', 'platform_name',
            'display_name', 'bungie_global_display_name', 'bungie_global_display_name_code',
            'full_bungie_name', 'icon_url',
            'active_triumph_score', 'lifetime_triumph_score',
            'characters',
            'first_seen', 'last_updated'
        ]

    def get_platform_name(self, obj):
        return obj.get_platform_display()

    def get_icon_url(self, obj):
        if obj.icon_path:
            return f"https://www.bungie.net{obj.icon_path}"
        return None

    def get_full_bungie_name(self, obj):
        if obj.bungie_global_display_name and obj.bungie_global_display_name_code:
            return f"{obj.bungie_global_display_name}#{obj.bungie_global_display_name_code}"
        return obj.display_name


class PlayerSearchResultSerializer(serializers.Serializer):
    """Serializer for player search results from Bungie API"""
    membershipId = serializers.CharField()
    membershipType = serializers.IntegerField()
    displayName = serializers.CharField(allow_blank=True, required=False)
    bungieGlobalDisplayName = serializers.CharField(allow_blank=True, required=False)
    bungieGlobalDisplayNameCode = serializers.IntegerField(required=False)
    iconPath = serializers.CharField(allow_blank=True, required=False)
    platformName = serializers.CharField(required=False)
    platformIcon = serializers.CharField(required=False)
