from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    # Publiczne widoki
    path('', views.home, name='home'),
    path('event/<uuid:event_id>/', views.event_detail, name='event_detail'),
    path('event/<uuid:event_id>/vote/', views.vote, name='vote'),
    path('event/<uuid:event_id>/results/', views.get_results, name='get_results'),
    path('candidate/<uuid:candidate_id>/', views.candidate_detail, name='candidate_detail'),
    path('history/', views.event_history, name='event_history'),
    
    # Panel administratora
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/event/create/', views.admin_event_create, name='admin_event_create'),
    path('dashboard/event/<uuid:event_id>/edit/', views.admin_event_edit, name='admin_event_edit'),
    path('dashboard/event/<uuid:event_id>/', views.admin_event_detail, name='admin_event_detail'),
    path('dashboard/event/<uuid:event_id>/candidate/create/', views.admin_candidate_create, name='admin_candidate_create'),
    path('dashboard/candidate/<uuid:candidate_id>/edit/', views.admin_candidate_edit, name='admin_candidate_edit'),
    path('dashboard/event/<uuid:event_id>/export/', views.export_results, name='export_results'),
    path('dashboard/comments/', views.moderate_comments, name='moderate_comments'),
    path('dashboard/comments/<uuid:comment_id>/approve/', views.approve_comment, name='approve_comment'),
    path('dashboard/comments/<uuid:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('dashboard/event/<uuid:event_id>/delete/', views.delete_event, name='delete_event'),
]
