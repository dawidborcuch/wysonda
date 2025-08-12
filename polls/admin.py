from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Event, Candidate, Vote, Comment, UserBadge, PollAnalytics


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'event_date', 'status', 'is_private', 'candidate_count', 'vote_count', 'created_at']
    list_filter = ['event_type', 'status', 'is_private', 'created_at', 'event_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'event_date'
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('title', 'description', 'event_type', 'event_date')
        }),
        ('Status', {
            'fields': ('status', 'is_private')
        }),
        ('Systemowe', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def candidate_count(self, obj):
        return obj.candidates.count()
    candidate_count.short_description = 'Liczba kandydatów'
    
    def vote_count(self, obj):
        return obj.votes.count()
    vote_count.short_description = 'Liczba głosów'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('candidates', 'votes')


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_link', 'candidate_type', 'is_premium', 'vote_count', 'vote_percentage', 'created_at']
    list_filter = ['candidate_type', 'is_premium', 'created_at', 'event__event_type']
    search_fields = ['name', 'description', 'event__title']
    readonly_fields = ['id', 'created_at', 'updated_at', 'vote_count', 'vote_percentage']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('event', 'name', 'description', 'candidate_type')
        }),
        ('Zdjęcia', {
            'fields': ('main_photo', 'additional_photos'),
            'classes': ('collapse',)
        }),
        ('Rozszerzone informacje', {
            'fields': ('extended_description', 'background_info', 'articles'),
            'classes': ('collapse',)
        }),
        ('Premium', {
            'fields': ('is_premium',)
        }),
        ('Systemowe', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def event_link(self, obj):
        if obj.event:
            url = reverse('admin:polls_event_change', args=[obj.event.id])
            return format_html('<a href="{}">{}</a>', url, obj.event.title)
        return '-'
    event_link.short_description = 'Wydarzenie'
    event_link.admin_order_field = 'event__title'
    
    def vote_count(self, obj):
        return obj.votes.count()
    vote_count.short_description = 'Liczba głosów'
    
    def vote_percentage(self, obj):
        total_votes = obj.event.votes.count()
        if total_votes == 0:
            return '0%'
        percentage = (obj.votes.count() / total_votes) * 100
        return f'{percentage:.1f}%'
    vote_percentage.short_description = 'Procent głosów'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event').prefetch_related('votes')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['candidate_name', 'event_title', 'ip_address', 'created_at']
    list_filter = ['created_at', 'event__event_type', 'candidate__candidate_type']
    search_fields = ['candidate__name', 'event__title', 'ip_address']
    readonly_fields = ['id', 'created_at', 'ip_address', 'browser_fingerprint', 'user_agent']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Głos', {
            'fields': ('event', 'candidate')
        }),
        ('Informacje techniczne', {
            'fields': ('ip_address', 'browser_fingerprint', 'user_agent', 'location_data'),
            'classes': ('collapse',)
        }),
        ('Systemowe', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def candidate_name(self, obj):
        return obj.candidate.name
    candidate_name.short_description = 'Kandydat'
    candidate_name.admin_order_field = 'candidate__name'
    
    def event_title(self, obj):
        return obj.event.title
    event_title.short_description = 'Wydarzenie'
    event_title.admin_order_field = 'event__title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('candidate', 'event')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'candidate_name', 'is_approved', 'created_at', 'content_preview']
    list_filter = ['is_approved', 'created_at', 'candidate__candidate_type']
    search_fields = ['author_name', 'author_email', 'content', 'candidate__name']
    readonly_fields = ['id', 'created_at', 'ip_address']
    list_editable = ['is_approved']
    actions = ['approve_comments', 'reject_comments']
    
    fieldsets = (
        ('Komentarz', {
            'fields': ('candidate', 'author_name', 'author_email', 'content')
        }),
        ('Moderacja', {
            'fields': ('is_approved',)
        }),
        ('Systemowe', {
            'fields': ('id', 'ip_address', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def candidate_name(self, obj):
        return obj.candidate.name
    candidate_name.short_description = 'Kandydat'
    candidate_name.admin_order_field = 'candidate__name'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Podgląd treści'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'Zatwierdzono {updated} komentarzy.')
    approve_comments.short_description = 'Zatwierdź wybrane komentarze'
    
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'Odrzucono {updated} komentarzy.')
    reject_comments.short_description = 'Odrzuć wybrane komentarze'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('candidate')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'badge_type', 'awarded_at']
    list_filter = ['badge_type', 'awarded_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['id', 'awarded_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Użytkownik'
    user_email.admin_order_field = 'user__email'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PollAnalytics)
class PollAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['event_title', 'total_votes', 'unique_voters', 'participation_rate', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['event__title']
    readonly_fields = ['id', 'created_at', 'updated_at', 'participation_rate']
    
    fieldsets = (
        ('Wydarzenie', {
            'fields': ('event',)
        }),
        ('Statystyki', {
            'fields': ('total_votes', 'unique_voters', 'participation_rate')
        }),
        ('Dane geograficzne', {
            'fields': ('geographic_data',),
            'classes': ('collapse',)
        }),
        ('Dane demograficzne', {
            'fields': ('demographic_data',),
            'classes': ('collapse',)
        }),
        ('Systemowe', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def event_title(self, obj):
        return obj.event.title
    event_title.short_description = 'Wydarzenie'
    event_title.admin_order_field = 'event__title'
    
    def participation_rate(self, obj):
        if obj.total_votes == 0:
            return '0%'
        rate = (obj.unique_voters / obj.total_votes) * 100
        return f'{rate:.1f}%'
    participation_rate.short_description = 'Wskaźnik uczestnictwa'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event')


# Customize admin site
admin.site.site_header = 'Wysonda - Panel Administracyjny'
admin.site.site_title = 'Wysonda Admin'
admin.site.index_title = 'Zarządzanie sondażami politycznymi'
