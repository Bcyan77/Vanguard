from django.contrib import admin
from .models import Party, PartyMember, PartyTag, PartyApplication


class PartyMemberInline(admin.TabularInline):
    """Inline admin for party members"""
    model = PartyMember
    extra = 0
    readonly_fields = ('joined_at',)


class PartyTagInline(admin.TabularInline):
    """Inline admin for party tags"""
    model = PartyTag
    extra = 1


class PartyApplicationInline(admin.TabularInline):
    """Inline admin for party applications"""
    model = PartyApplication
    extra = 0
    readonly_fields = ('applied_at', 'reviewed_at')


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    """Admin interface for Party model"""
    
    list_display = ('title', 'activity_type', 'creator', 'status', 
                    'current_members_count', 'max_members', 'created_at')
    list_filter = ('activity_type', 'status', 'requires_mic', 'created_at')
    search_fields = ('title', 'description', 'creator__display_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'activity_type')
        }),
        ('Party Settings', {
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
    
    inlines = [PartyTagInline, PartyMemberInline, PartyApplicationInline]
    
    def save_model(self, request, obj, form, change):
        """Auto-set creator if creating new party"""
        if not change:
            obj.creator = request.user
        super().save_model(request, obj, form, change)


@admin.register(PartyMember)
class PartyMemberAdmin(admin.ModelAdmin):
    """Admin interface for PartyMember model"""
    
    list_display = ('user', 'party', 'role', 'status', 'joined_at')
    list_filter = ('role', 'status', 'joined_at')
    search_fields = ('user__display_name', 'party__title')
    ordering = ('-joined_at',)


@admin.register(PartyTag)
class PartyTagAdmin(admin.ModelAdmin):
    """Admin interface for PartyTag model"""
    
    list_display = ('name', 'party')
    search_fields = ('name', 'party__title')


@admin.register(PartyApplication)
class PartyApplicationAdmin(admin.ModelAdmin):
    """Admin interface for PartyApplication model"""
    
    list_display = ('applicant', 'party', 'status', 'applied_at', 'reviewed_by')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__display_name', 'party__title')
    ordering = ('-applied_at',)
    
    readonly_fields = ('applied_at', 'reviewed_at')
