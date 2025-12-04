from django.contrib import admin
from .models import (
    Fireteam, FireteamMember, FireteamTag, FireteamApplication,
    DestinyActivityType, DestinySpecificActivity,
    DestinyActivityMode, ActivityModeAvailability
)


class FireteamMemberInline(admin.TabularInline):
    """Inline admin for fireteam members"""
    model = FireteamMember
    extra = 0
    readonly_fields = ('joined_at',)


class FireteamTagInline(admin.TabularInline):
    """Inline admin for fireteam tags"""
    model = FireteamTag
    extra = 1


class FireteamApplicationInline(admin.TabularInline):
    """Inline admin for fireteam applications"""
    model = FireteamApplication
    extra = 0
    readonly_fields = ('applied_at', 'reviewed_at')


@admin.register(DestinyActivityType)
class DestinyActivityTypeAdmin(admin.ModelAdmin):
    """Admin interface for DestinyActivityType model (Tier 1)"""

    list_display = ('name', 'hash', 'is_canonical', 'duplicate_group_name', 'has_icon', 'is_active', 'updated_at')
    list_filter = ('is_canonical', 'is_active', 'has_icon', 'redacted')
    search_fields = ('name', 'description', 'hash', 'duplicate_group_name')
    ordering = ('name',)

    fieldsets = (
        ('Bungie API Data', {
            'fields': ('hash', 'index', 'name', 'description')
        }),
        ('Display', {
            'fields': ('icon_path', 'has_icon')
        }),
        ('Deduplication Tracking', {
            'fields': ('is_canonical', 'canonical_entry', 'duplicate_group_name'),
            'description': (
                'Deduplication info. Canonical entries are the primary entries used '
                'in dropdowns. Duplicate entries point to their canonical version and '
                'are marked inactive.'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'redacted')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('hash', 'index', 'canonical_entry', 'duplicate_group_name', 'created_at', 'updated_at')

    actions = ['mark_inactive', 'mark_active', 'mark_as_canonical']

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'Marked {queryset.count()} activity types as inactive')
    mark_inactive.short_description = 'Mark selected activity types as inactive'

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Marked {queryset.count()} activity types as active')
    mark_active.short_description = 'Mark selected activity types as active'

    def mark_as_canonical(self, request, queryset):
        """Manually mark entries as canonical (use with caution)"""
        count = queryset.update(is_canonical=True, canonical_entry=None)
        self.message_user(
            request,
            f'Marked {count} entries as canonical',
            level='WARNING'
        )
    mark_as_canonical.short_description = 'Mark as canonical (WARNING: may create duplicates)'


@admin.register(DestinySpecificActivity)
class DestinySpecificActivityAdmin(admin.ModelAdmin):
    """Admin interface for DestinySpecificActivity model (Tier 2)"""

    list_display = ('name', 'activity_type', 'parsed_difficulty', 'parsed_mode', 'needs_manual_review', 'hash', 'activity_light_level', 'is_active', 'updated_at')
    list_filter = ('needs_manual_review', 'is_active', 'activity_type', 'parsed_difficulty', 'parsed_mode', 'has_icon', 'is_playlist', 'redacted')
    search_fields = ('name', 'original_name', 'parsed_clean_name', 'description', 'hash', 'activity_type__name')
    ordering = ('activity_type__name', 'name')

    fieldsets = (
        ('Bungie API Data', {
            'fields': ('hash', 'index', 'description')
        }),
        ('Name Information', {
            'fields': (
                'name',
                'original_name',
                'parsed_clean_name',
                'parsed_difficulty',
                'parsed_mode',
                'parsing_notes',
                'needs_manual_review'
            ),
            'description': (
                'Name parsing results. The "name" field is the current display name. '
                '"original_name" preserves the Bungie API name. '
                'Parsed fields show extracted difficulty/mode information.'
            )
        }),
        ('Tier 1 Link', {
            'fields': ('activity_type',)
        }),
        ('Display', {
            'fields': ('icon_path', 'has_icon')
        }),
        ('Activity Info', {
            'fields': ('activity_level', 'activity_light_level', 'tier', 'is_playlist')
        }),
        ('Status', {
            'fields': ('is_active', 'redacted')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('hash', 'index', 'original_name', 'created_at', 'updated_at')

    actions = ['mark_inactive', 'mark_active', 'mark_for_review', 'clear_review_flag']

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'Marked {queryset.count()} specific activities as inactive')
    mark_inactive.short_description = 'Mark selected specific activities as inactive'

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Marked {queryset.count()} specific activities as active')
    mark_active.short_description = 'Mark selected specific activities as active'

    def mark_for_review(self, request, queryset):
        count = queryset.update(needs_manual_review=True)
        self.message_user(request, f'Marked {count} activities for manual review')
    mark_for_review.short_description = 'Mark selected for manual review'

    def clear_review_flag(self, request, queryset):
        count = queryset.update(needs_manual_review=False)
        self.message_user(request, f'Cleared review flag for {count} activities')
    clear_review_flag.short_description = 'Clear manual review flag'


@admin.register(DestinyActivityMode)
class DestinyActivityModeAdmin(admin.ModelAdmin):
    """Admin interface for DestinyActivityMode model (Tier 3)"""

    list_display = ('name', 'hash', 'display_order', 'is_team_based', 'is_active', 'updated_at')
    list_filter = ('is_active', 'is_team_based', 'redacted', 'activity_mode_category')
    search_fields = ('name', 'description', 'hash')
    ordering = ('display_order', 'name')

    fieldsets = (
        ('Bungie API Data', {
            'fields': ('hash', 'index', 'name', 'description')
        }),
        ('Display', {
            'fields': ('icon_path', 'has_icon', 'display_order')
        }),
        ('Mode Info', {
            'fields': ('mode_type', 'activity_mode_category', 'is_team_based')
        }),
        ('Status', {
            'fields': ('is_active', 'redacted')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('hash', 'index', 'created_at', 'updated_at')

    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'Marked {queryset.count()} activity modes as inactive')
    mark_inactive.short_description = 'Mark selected activity modes as inactive'

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Marked {queryset.count()} activity modes as active')
    mark_active.short_description = 'Mark selected activity modes as active'


@admin.register(ActivityModeAvailability)
class ActivityModeAvailabilityAdmin(admin.ModelAdmin):
    """Admin interface for ActivityModeAvailability model"""

    list_display = ('specific_activity', 'activity_mode')
    list_filter = ('activity_mode', 'specific_activity__activity_type')
    search_fields = ('specific_activity__name', 'activity_mode__name')
    ordering = ('specific_activity__name', 'activity_mode__display_order')

    fieldsets = (
        ('Activity Mode Link', {
            'fields': ('specific_activity', 'activity_mode')
        }),
    )


@admin.register(Fireteam)
class FireteamAdmin(admin.ModelAdmin):
    """Admin interface for Fireteam model"""

    list_display = ('title', 'get_activity_display', 'creator', 'status',
                    'current_members_count', 'max_members', 'created_at')
    list_filter = ('selected_activity_type', 'status', 'requires_mic', 'created_at')
    search_fields = ('title', 'description', 'creator__display_name',
                     'selected_activity_type__name', 'selected_specific_activity__name')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('3-Tier Activity Selection (NEW)', {
            'fields': ('selected_activity_type', 'selected_specific_activity', 'selected_activity_mode'),
            'description': 'Use the 3-tier system to select activity: Type > Specific Activity > Mode (optional)'
        }),
        ('Legacy Activity Fields (DEPRECATED)', {
            'fields': ('activity', 'activity_type'),
            'classes': ('collapse',),
            'description': 'These fields are deprecated. Use 3-tier selection above.'
        }),
        ('Fireteam Settings', {
            'fields': ('max_members', 'current_members_count', 'status',
                      'requires_mic', 'min_power_level')
        }),
        ('Timing', {
            'fields': ('scheduled_time', 'created_at', 'updated_at')
        }),
        ('Creator', {
            'fields': ('creator',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'current_members_count')

    inlines = [FireteamTagInline, FireteamMemberInline, FireteamApplicationInline]

    def save_model(self, request, obj, form, change):
        """Auto-set creator if creating new fireteam"""
        if not change:
            obj.creator = request.user
        super().save_model(request, obj, form, change)


@admin.register(FireteamMember)
class FireteamMemberAdmin(admin.ModelAdmin):
    """Admin interface for FireteamMember model"""

    list_display = ('user', 'fireteam', 'role', 'status', 'joined_at')
    list_filter = ('role', 'status', 'joined_at')
    search_fields = ('user__display_name', 'fireteam__title')
    ordering = ('-joined_at',)


@admin.register(FireteamTag)
class FireteamTagAdmin(admin.ModelAdmin):
    """Admin interface for FireteamTag model"""

    list_display = ('name', 'fireteam')
    search_fields = ('name', 'fireteam__title')


@admin.register(FireteamApplication)
class FireteamApplicationAdmin(admin.ModelAdmin):
    """Admin interface for FireteamApplication model"""

    list_display = ('applicant', 'fireteam', 'status', 'applied_at', 'reviewed_by')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__display_name', 'fireteam__title')
    ordering = ('-applied_at',)

    readonly_fields = ('applied_at', 'reviewed_at')
