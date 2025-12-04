from rest_framework import serializers
from .models import BungieUser


class BungieUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for current user's profile"""
    platform_name = serializers.SerializerMethodField()
    icon_url = serializers.SerializerMethodField()
    full_bungie_name = serializers.SerializerMethodField()

    class Meta:
        model = BungieUser
        fields = [
            'bungie_membership_id', 'bungie_membership_type', 'platform_name',
            'display_name', 'bungie_global_display_name', 'bungie_global_display_name_code',
            'full_bungie_name', 'icon_url',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login'
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
