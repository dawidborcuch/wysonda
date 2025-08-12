from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('events/', views.EventListAPIView.as_view(), name='event-list'),
    path('events/<uuid:pk>/', views.EventDetailAPIView.as_view(), name='event-detail'),
    path('events/<uuid:event_id>/results/', views.EventResultsAPIView.as_view(), name='event-results'),
    path('candidates/', views.CandidateListAPIView.as_view(), name='candidate-list'),
    path('candidates/<uuid:pk>/', views.CandidateDetailAPIView.as_view(), name='candidate-detail'),
    path('votes/', views.VoteCreateAPIView.as_view(), name='vote-create'),
    path('statistics/', views.StatisticsAPIView.as_view(), name='statistics'),
]
