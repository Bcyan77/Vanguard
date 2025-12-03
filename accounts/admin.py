from django.contrib import admin
from .models import BungieUser


@admin.register(BungieUser)
class BungieUserAdmin(admin.ModelAdmin):
    """Admin interface for BungieUser model"""
    
    list_display = ('bungie_membership_id', 'display_name', 'get_platform_display', 
                    'bungie_global_display_name', 'is_active', 'date_joined')
    list_filter = ('bungie_membership_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('bungie_membership_id', 'display_name', 'bungie_global_display_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('bungie_membership_id', 'bungie_membership_type', 'display_name')}),
        ('Bungie.net Info', {'fields': ('bungie_global_display_name', 'bungie_global_display_name_code', 'icon_path')}),
        ('OAuth Tokens', {'fields': ('token_expires_at',), 'classes': ('collapse',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ('bungie_membership_id', 'date_joined', 'last_login')
    
    def get_platform_display(self, obj):
        return obj.get_platform_display()
    get_platform_display.short_description = 'Platform'
