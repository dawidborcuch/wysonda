from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'user_email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['nickname', 'user__email', 'bio']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('user', 'nickname', 'bio')
        }),
        ('Avatar', {
            'fields': ('avatar',)
        }),
        ('Systemowe', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email użytkownika'
    user_email.admin_order_field = 'user__email'
