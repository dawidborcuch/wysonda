from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count
from polls.models import Event, Candidate, Vote, PollAnalytics
from polls.utils import get_client_ip, check_vote_eligibility, generate_vote_report
from .serializers import (
    EventSerializer, 
    CandidateSerializer, 
    VoteSerializer,
    EventResultsSerializer,
    StatisticsSerializer
)


class EventListAPIView(generics.ListAPIView):
    """Lista wszystkich wydarzeń"""
    queryset = Event.objects.filter(is_private=False).order_by('event_date')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class EventDetailAPIView(generics.RetrieveAPIView):
    """Szczegóły wydarzenia"""
    queryset = Event.objects.filter(is_private=False)
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class EventResultsAPIView(APIView):
    """Wyniki wydarzenia w czasie rzeczywistym"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, is_private=False)
        candidates = event.candidates.all()
        
        results = []
        total_votes = event.votes.count()
        
        for candidate in candidates:
            vote_count = candidate.vote_count
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            results.append({
                'id': str(candidate.id),
                'name': candidate.name,
                'vote_count': vote_count,
                'percentage': round(percentage, 2)
            })
        
        # Sortuj malejąco
        results.sort(key=lambda x: x['vote_count'], reverse=True)
        
        return Response({
            'event': {
                'id': str(event.id),
                'title': event.title,
                'event_type': event.get_event_type_display(),
                'event_date': event.event_date.isoformat(),
                'status': event.status,
            },
            'results': results,
            'total_votes': total_votes,
            'last_updated': event.updated_at.isoformat()
        })


class CandidateListAPIView(generics.ListAPIView):
    """Lista kandydatów"""
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Candidate.objects.all()
        event_id = self.request.query_params.get('event', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset


class CandidateDetailAPIView(generics.RetrieveAPIView):
    """Szczegóły kandydata"""
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class VoteCreateAPIView(APIView):
    """Tworzenie głosu"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request):
        try:
            event_id = request.data.get('event_id')
            candidate_id = request.data.get('candidate_id')
            browser_fingerprint = request.data.get('fingerprint', '')
            
            event = get_object_or_404(Event, id=event_id)
            candidate = get_object_or_404(Candidate, id=candidate_id, event=event)
            
            client_ip = get_client_ip(request)
            
            # Sprawdź czy można głosować
            if not check_vote_eligibility(request, event, client_ip):
                return Response({
                    'success': False,
                    'message': 'Już oddałeś głos w tym sondażu lub sondaż jest nieaktywny.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Utwórz głos
            vote = Vote.objects.create(
                event=event,
                candidate=candidate,
                ip_address=client_ip,
                browser_fingerprint=browser_fingerprint,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            # Aktualizuj analitykę
            analytics, created = PollAnalytics.objects.get_or_create(event=event)
            analytics.total_votes = event.votes.count()
            analytics.unique_voters = event.votes.values('ip_address').distinct().count()
            analytics.save()
            
            return Response({
                'success': True,
                'message': 'Głos został oddany pomyślnie!',
                'vote_id': str(vote.id)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Wystąpił błąd: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatisticsAPIView(APIView):
    """Statystyki aplikacji"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        total_events = Event.objects.count()
        active_events = Event.objects.filter(status='active').count()
        total_votes = Vote.objects.count()
        total_candidates = Candidate.objects.count()
        
        # Najpopularniejsze wydarzenia
        popular_events = Event.objects.annotate(
            vote_count=Count('votes')
        ).order_by('-vote_count')[:5]
        
        # Statystyki geograficzne (przykład)
        geographic_stats = {}
        for vote in Vote.objects.all()[:1000]:  # Ogranicz do 1000 głosów dla wydajności
            region = "Nieznany"
            if vote.ip_address:
                if vote.ip_address.startswith('192.168.'):
                    region = "Sieć lokalna"
                elif vote.ip_address.startswith('10.'):
                    region = "Sieć prywatna"
                else:
                    region = "Internet"
            
            geographic_stats[region] = geographic_stats.get(region, 0) + 1
        
        return Response({
            'total_events': total_events,
            'active_events': active_events,
            'total_votes': total_votes,
            'total_candidates': total_candidates,
            'popular_events': [
                {
                    'id': str(event.id),
                    'title': event.title,
                    'vote_count': event.vote_count
                } for event in popular_events
            ],
            'geographic_stats': geographic_stats
        })
