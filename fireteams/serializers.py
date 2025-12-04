from rest_framework import serializers
from .models import (
    Fireteam, FireteamMember, FireteamTag, FireteamApplication,
    DestinyActivityType, DestinySpecificActivity, DestinyActivityMode
)


# ============================================================
# Activity Serializers (Tier 1, 2, 3)
# ============================================================

class ActivityItemSerializer(serializers.Serializer):
    """Serializer for individual activity item"""
    hash = serializers.CharField()
    name = serializers.CharField()


class SpecificActivitiesResponseSerializer(serializers.Serializer):
    """Response serializer for specific activities API endpoint"""
    activities = ActivityItemSerializer(many=True)
    count = serializers.IntegerField()


class ActivityModesResponseSerializer(serializers.Serializer):
    """Response serializer for activity modes API endpoint"""
    modes = ActivityItemSerializer(many=True)
    count = serializers.IntegerField()


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses"""
    error = serializers.CharField()


class DestinyActivityTypeSerializer(serializers.ModelSerializer):
    """Serializer for Tier 1: Activity Types"""
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = DestinyActivityType
        fields = ['hash', 'name', 'description', 'icon_url', 'is_active']

    def get_icon_url(self, obj):
        return obj.get_icon_url()


class DestinySpecificActivitySerializer(serializers.ModelSerializer):
    """Serializer for Tier 2: Specific Activities"""
    icon_url = serializers.SerializerMethodField()
    activity_type_name = serializers.CharField(source='activity_type.name', read_only=True)

    class Meta:
        model = DestinySpecificActivity
        fields = ['hash', 'name', 'description', 'icon_url', 'activity_type', 'activity_type_name', 'is_active']

    def get_icon_url(self, obj):
        return obj.get_icon_url()


class DestinyActivityModeSerializer(serializers.ModelSerializer):
    """Serializer for Tier 3: Activity Modes"""
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = DestinyActivityMode
        fields = ['hash', 'name', 'description', 'icon_url', 'display_order', 'is_active']

    def get_icon_url(self, obj):
        return obj.get_icon_url()


# ============================================================
# User Serializer (간략화된 버전)
# ============================================================

class BungieUserSimpleSerializer(serializers.Serializer):
    """간략화된 사용자 정보 시리얼라이저"""
    bungie_membership_id = serializers.CharField()
    display_name = serializers.CharField()
    bungie_global_display_name = serializers.CharField()
    bungie_global_display_name_code = serializers.IntegerField()
    icon_path = serializers.CharField()

    def get_icon_url(self, obj):
        if obj.icon_path:
            return f"https://www.bungie.net{obj.icon_path}"
        return None


# ============================================================
# Fireteam Serializers
# ============================================================

class FireteamTagSerializer(serializers.ModelSerializer):
    """Serializer for Fireteam Tags"""
    class Meta:
        model = FireteamTag
        fields = ['id', 'name']


class FireteamMemberSerializer(serializers.ModelSerializer):
    """Serializer for Fireteam Members"""
    user = BungieUserSimpleSerializer(read_only=True)

    class Meta:
        model = FireteamMember
        fields = ['id', 'user', 'role', 'status', 'joined_at']


class FireteamApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Fireteam Applications"""
    applicant = BungieUserSimpleSerializer(read_only=True)
    reviewed_by = BungieUserSimpleSerializer(read_only=True)

    class Meta:
        model = FireteamApplication
        fields = ['id', 'applicant', 'message', 'status', 'applied_at', 'reviewed_at', 'reviewed_by']


class FireteamListSerializer(serializers.ModelSerializer):
    """Serializer for Fireteam list view (간략화)"""
    creator = BungieUserSimpleSerializer(read_only=True)
    tags = FireteamTagSerializer(many=True, read_only=True)
    activity_display = serializers.SerializerMethodField()
    selected_activity_type_name = serializers.CharField(source='selected_activity_type.name', read_only=True)
    selected_specific_activity_name = serializers.CharField(source='selected_specific_activity.name', read_only=True)
    selected_activity_mode_name = serializers.CharField(source='selected_activity_mode.name', read_only=True)
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = Fireteam
        fields = [
            'id', 'title', 'description', 'activity_display',
            'selected_activity_type', 'selected_activity_type_name',
            'selected_specific_activity', 'selected_specific_activity_name',
            'selected_activity_mode', 'selected_activity_mode_name',
            'max_members', 'current_members_count', 'available_slots',
            'creator', 'status', 'tags',
            'requires_mic', 'min_power_level', 'scheduled_time',
            'created_at', 'updated_at'
        ]

    def get_activity_display(self, obj):
        return obj.get_activity_display()

    def get_available_slots(self, obj):
        return obj.get_available_slots()


class FireteamDetailSerializer(serializers.ModelSerializer):
    """Serializer for Fireteam detail view (전체 정보)"""
    creator = BungieUserSimpleSerializer(read_only=True)
    tags = FireteamTagSerializer(many=True, read_only=True)
    members = FireteamMemberSerializer(many=True, read_only=True, source='members.all')
    activity_display = serializers.SerializerMethodField()
    selected_activity_type_data = DestinyActivityTypeSerializer(source='selected_activity_type', read_only=True)
    selected_specific_activity_data = DestinySpecificActivitySerializer(source='selected_specific_activity', read_only=True)
    selected_activity_mode_data = DestinyActivityModeSerializer(source='selected_activity_mode', read_only=True)
    available_slots = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()

    class Meta:
        model = Fireteam
        fields = [
            'id', 'title', 'description', 'activity_display',
            'selected_activity_type', 'selected_activity_type_data',
            'selected_specific_activity', 'selected_specific_activity_data',
            'selected_activity_mode', 'selected_activity_mode_data',
            'max_members', 'current_members_count', 'available_slots',
            'creator', 'status', 'tags', 'members',
            'requires_mic', 'min_power_level', 'scheduled_time',
            'created_at', 'updated_at',
            'is_member', 'is_creator'
        ]

    def get_activity_display(self, obj):
        return obj.get_activity_display()

    def get_available_slots(self, obj):
        return obj.get_available_slots()

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_member(request.user)
        return False

    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_creator(request.user)
        return False


class FireteamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Fireteam"""
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True
    )

    class Meta:
        model = Fireteam
        fields = [
            'title', 'description',
            'selected_activity_type', 'selected_specific_activity', 'selected_activity_mode',
            'max_members', 'requires_mic', 'min_power_level', 'scheduled_time',
            'tags'
        ]

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        user = self.context['request'].user

        fireteam = Fireteam.objects.create(creator=user, **validated_data)

        # Create leader membership
        FireteamMember.objects.create(
            fireteam=fireteam,
            user=user,
            role='leader',
            status='active'
        )

        # Create tags
        for tag_name in tags_data:
            FireteamTag.objects.create(fireteam=fireteam, name=tag_name)

        fireteam.update_member_count()
        return fireteam


class FireteamUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a Fireteam"""
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True
    )

    class Meta:
        model = Fireteam
        fields = [
            'title', 'description',
            'selected_activity_type', 'selected_specific_activity', 'selected_activity_mode',
            'max_members', 'requires_mic', 'min_power_level', 'scheduled_time',
            'status', 'tags'
        ]

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags_data is not None:
            instance.tags.all().delete()
            for tag_name in tags_data:
                FireteamTag.objects.create(fireteam=instance, name=tag_name)

        return instance


class FireteamApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Fireteam Application"""
    class Meta:
        model = FireteamApplication
        fields = ['message']
