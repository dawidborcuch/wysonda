from rest_framework import serializers
from polls.models import Event, Candidate, Vote, Comment, PollAnalytics


class EventSerializer(serializers.ModelSerializer):
    """Serializer dla wydarzenia"""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_finished = serializers.BooleanField(read_only=True)
    candidate_count = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'event_type_display',
            'event_date', 'status', 'status_display', 'is_private',
            'is_active', 'is_finished', 'candidate_count', 'vote_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_candidate_count(self, obj):
        return obj.candidates.count()
    
    def get_vote_count(self, obj):
        return obj.votes.count()


class CandidateSerializer(serializers.ModelSerializer):
    """Serializer dla kandydata"""
    candidate_type_display = serializers.CharField(source='get_candidate_type_display', read_only=True)
    vote_count = serializers.IntegerField(read_only=True)
    vote_percentage = serializers.FloatField(read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'event', 'event_title', 'name', 'description',
            'candidate_type', 'candidate_type_display', 'main_photo',
            'additional_photos', 'articles', 'extended_description',
            'background_info', 'is_premium', 'vote_count', 'vote_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VoteSerializer(serializers.ModelSerializer):
    """Serializer dla głosu"""
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    
    class Meta:
        model = Vote
        fields = [
            'id', 'event', 'event_title', 'candidate', 'candidate_name',
            'ip_address', 'browser_fingerprint', 'user_agent',
            'location_data', 'created_at'
        ]
        read_only_fields = ['id', 'ip_address', 'browser_fingerprint', 'user_agent', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer dla komentarza"""
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'candidate', 'candidate_name', 'author_name',
            'author_email', 'content', 'is_approved', 'created_at'
        ]
        read_only_fields = ['id', 'is_approved', 'created_at']


class EventResultsSerializer(serializers.Serializer):
    """Serializer dla wyników wydarzenia"""
    event = EventSerializer()
    results = serializers.ListField(child=serializers.DictField())
    total_votes = serializers.IntegerField()
    last_updated = serializers.DateTimeField()


class StatisticsSerializer(serializers.Serializer):
    """Serializer dla statystyk"""
    total_events = serializers.IntegerField()
    active_events = serializers.IntegerField()
    total_votes = serializers.IntegerField()
    total_candidates = serializers.IntegerField()
    popular_events = serializers.ListField(child=serializers.DictField())
    geographic_stats = serializers.DictField()


class PollAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer dla analityki sondaży"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    
    class Meta:
        model = PollAnalytics
        fields = [
            'id', 'event', 'event_title', 'total_votes', 'unique_voters',
            'geographic_data', 'demographic_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
