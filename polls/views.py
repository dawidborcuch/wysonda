from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import json
import csv
from datetime import datetime, timedelta

from .models import Event, Candidate, Vote, Comment, UserBadge, PollAnalytics
from .forms import CommentForm, EventForm, CandidateForm
from .utils import get_client_ip, get_browser_fingerprint, check_vote_eligibility


def home(request):
    """Strona główna - lista aktualnych sondaży"""
    now = timezone.now()
    
    # Użyj dynamicznej logiki zamiast statycznych statusów
    events = Event.objects.exclude(is_private=True).order_by('event_date')
    
    # Filtruj na podstawie daty
    active_and_upcoming = []
    active_events = []
    upcoming_events = []
    
    for event in events:
        if event.event_date > now:  # Jeszcze nie minęła data
            if event.status == 'active' or (event.status == 'upcoming' and event.event_date <= now + timezone.timedelta(days=1)):
                active_and_upcoming.append(event)
                active_events.append(event)
            else:
                active_and_upcoming.append(event)
                upcoming_events.append(event)
    
    # Upewnij się, że lista jest posortowana rosnąco po dacie (najbliższa data pierwsza)
    active_and_upcoming.sort(key=lambda x: x.event_date)
    active_events.sort(key=lambda x: x.event_date)
    upcoming_events.sort(key=lambda x: x.event_date)
    
    # Paginacja
    paginator = Paginator(active_and_upcoming, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'active_events': active_events,
        'upcoming_events': upcoming_events,
        'now': now,
    }
    return render(request, 'polls/home.html', context)


def event_detail(request, event_id):
    """Szczegóły wydarzenia z możliwością głosowania"""
    event = get_object_or_404(Event, id=event_id)
    candidates = event.candidates.all()
    
    # Sprawdź czy użytkownik już głosował
    client_ip = get_client_ip(request)
    user_vote = Vote.objects.filter(event=event, ip_address=client_ip).first()
    has_voted = user_vote is not None
    
    # Pobierz wyniki
    results = []
    total_votes = event.votes.count()
    
    for candidate in candidates:
        vote_count = candidate.vote_count
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            'candidate': candidate,
            'vote_count': vote_count,
            'percentage': round(percentage, 2)
        })
    
    # Sortuj wyniki malejąco
    results.sort(key=lambda x: x['vote_count'], reverse=True)
    
    # Sortuj kandydatów według liczby głosów (od największej do najmniejszej)
    sorted_candidates = sorted(candidates, key=lambda c: c.vote_count, reverse=True)
    
    # Oblicz maksymalną liczbę głosów dla proporcjonalnego wypełnienia pasków
    max_votes = max([c.vote_count for c in candidates]) if candidates else 0
    
    # Oblicz proporcjonalne wypełnienie pasków dla każdego kandydata (względem całkowitej liczby głosów)
    for candidate in sorted_candidates:
        if total_votes > 0:
            setattr(candidate, 'proportional_width', (candidate.vote_count / total_votes) * 100)
        else:
            setattr(candidate, 'proportional_width', 0)
        print(f"Candidate {candidate.name}: {candidate.vote_count} votes, total_votes: {total_votes}, proportional_width: {getattr(candidate, 'proportional_width', 'NOT SET')}")  # Debug log
    
    context = {
        'event': event,
        'candidates': sorted_candidates,
        'results': results,
        'total_votes': total_votes,
        'max_votes': max_votes,

        'has_voted': has_voted,
        'user_vote': user_vote,
        'client_ip': client_ip,
        'now': timezone.now(),
    }
    return render(request, 'polls/event_detail.html', context)


@require_POST
@csrf_exempt
def vote(request, event_id):
    """Głosowanie w sondażu"""
    try:
        data = json.loads(request.body)
        candidate_id = data.get('candidate_id')
        browser_fingerprint = data.get('fingerprint', '')
        
        event = get_object_or_404(Event, id=event_id)
        candidate = get_object_or_404(Candidate, id=candidate_id, event=event)
        
        client_ip = get_client_ip(request)
        
        # Sprawdź czy można głosować
        if not check_vote_eligibility(request, event, client_ip):
            return JsonResponse({
                'success': False,
                'message': 'Już oddałeś głos w tym sondażu lub sondaż jest nieaktywny.'
            }, status=400)
        
        # Utwórz głos
        vote = Vote.objects.create(
            event=event,
            candidate=candidate,
            ip_address=client_ip,
            browser_fingerprint=browser_fingerprint,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        print(f"Vote created: {vote.id} for candidate {candidate.name}")  # Debug log
        
        # Aktualizuj analitykę
        analytics, created = PollAnalytics.objects.get_or_create(event=event)
        analytics.total_votes = event.votes.count()
        analytics.unique_voters = event.votes.values('ip_address').distinct().count()
        analytics.save()
        
        # Sprawdź aktualną liczbę głosów
        current_vote_count = candidate.vote_count
        total_votes = event.votes.count()
        print(f"Current vote count for {candidate.name}: {current_vote_count}, Total: {total_votes}")  # Debug log
        
        return JsonResponse({
            'success': True,
            'message': 'Głos został oddany pomyślnie!',
            'vote_id': str(vote.id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Wystąpił błąd: {str(e)}'
        }, status=500)


@require_POST
@csrf_exempt
def change_vote(request, event_id):
    """Zmiana głosu w sondażu"""
    try:
        data = json.loads(request.body)
        candidate_id = data.get('candidate_id')
        browser_fingerprint = data.get('fingerprint', '')
        
        event = get_object_or_404(Event, id=event_id)
        candidate = get_object_or_404(Candidate, id=candidate_id, event=event)
        
        client_ip = get_client_ip(request)
        
        # Sprawdź czy użytkownik już głosował
        existing_vote = Vote.objects.filter(event=event, ip_address=client_ip).first()
        if not existing_vote:
            return JsonResponse({
                'success': False,
                'message': 'Nie oddałeś jeszcze głosu w tym sondażu.'
            }, status=400)
        
        # Sprawdź czy sondaż jest aktywny
        if not event.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Sondaż nie jest już aktywny.'
            }, status=400)
        
        # Usuń poprzedni głos i dodaj nowy
        old_candidate = existing_vote.candidate
        existing_vote.delete()
        
        new_vote = Vote.objects.create(
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
        
        return JsonResponse({
            'success': True,
            'message': f'Głos został zmieniony z {old_candidate.name} na {candidate.name}!',
            'vote_id': str(new_vote.id),
            'old_candidate': old_candidate.name,
            'new_candidate': candidate.name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Wystąpił błąd: {str(e)}'
        }, status=500)


@require_POST
@csrf_exempt
def reset_vote(request, event_id):
    """Resetowanie głosu użytkownika"""
    try:
        event = get_object_or_404(Event, id=event_id)
        client_ip = get_client_ip(request)
        
        # Sprawdź czy użytkownik już głosował
        existing_vote = Vote.objects.filter(event=event, ip_address=client_ip).first()
        if not existing_vote:
            return JsonResponse({
                'success': False,
                'message': 'Nie oddałeś jeszcze głosu w tym sondażu.'
            }, status=400)
        
        # Sprawdź czy sondaż jest aktywny
        if not event.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Sondaż nie jest już aktywny.'
            }, status=400)
        
        # Usuń głos
        existing_vote.delete()
        
        # Aktualizuj analitykę
        analytics, created = PollAnalytics.objects.get_or_create(event=event)
        analytics.total_votes = event.votes.count()
        analytics.unique_voters = event.votes.values('ip_address').distinct().count()
        analytics.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Głos został zresetowany. Możesz oddać głos ponownie.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Wystąpił błąd: {str(e)}'
        }, status=500)


def get_results(request, event_id):
    """Pobieranie wyników w czasie rzeczywistym"""
    event = get_object_or_404(Event, id=event_id)
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
    
    response_data = {
        'results': results,
        'total_votes': total_votes,
        'last_updated': timezone.now().isoformat()
    }
    
    print(f"API Response: {response_data}")  # Debug log
    
    return JsonResponse(response_data)


def candidate_detail(request, candidate_id):
    """Profil kandydata/partii"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    comments = candidate.comments.all()
    

    

    
    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.candidate = candidate
            comment.ip_address = get_client_ip(request)
            comment.is_approved = True  # Automatycznie zatwierdzony
            
            # Ustaw autora jeśli użytkownik jest zalogowany
            if request.user.is_authenticated:
                comment.author = request.user
                comment.author_email = request.user.email
            
            comment.save()
            
            messages.success(request, 'Komentarz został dodany.')
            return redirect('polls:candidate_detail', candidate_id=candidate_id)
    else:
        form = CommentForm(user=request.user)
    
    context = {
        'candidate': candidate,
        'comments': comments,
        'form': form,
    }
    return render(request, 'polls/candidate_detail.html', context)


def event_history(request):
    """Historia zakończonych sondaży"""
    now = timezone.now()
    
    # Pokaż wydarzenia, które już minęły
    finished_events = Event.objects.filter(
        event_date__lt=now
    ).exclude(is_private=True).order_by('-event_date')
    
    paginator = Paginator(finished_events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'polls/event_history.html', context)


# Panel administratora
@staff_member_required
def admin_dashboard(request):
    """Panel administratora"""
    now = timezone.now()
    
    total_events = Event.objects.count()
    # Licz aktywne wydarzenia na podstawie daty
    active_events = Event.objects.filter(
        event_date__gt=now,
        status__in=['active', 'upcoming']
    ).count()
    total_votes = Vote.objects.count()
    total_candidates = Candidate.objects.count()
    
    recent_events = Event.objects.order_by('-created_at')[:5]
    recent_votes = Vote.objects.select_related('event', 'candidate').order_by('-created_at')[:10]
    
    context = {
        'total_events': total_events,
        'active_events': active_events,
        'total_votes': total_votes,
        'total_candidates': total_candidates,
        'recent_events': recent_events,
        'recent_votes': recent_votes,
        'now': now,
    }
    return render(request, 'polls/admin/dashboard.html', context)


@staff_member_required
def admin_event_create(request):
    """Tworzenie nowego wydarzenia"""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Wydarzenie "{event.title}" zostało utworzone.')
            return redirect('polls:admin_event_detail', event_id=event.id)
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'title': 'Utwórz nowe wydarzenie'
    }
    return render(request, 'polls/admin/event_form.html', context)


@staff_member_required
def admin_event_edit(request, event_id):
    """Edycja wydarzenia"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Wydarzenie "{event.title}" zostało zaktualizowane.')
            return redirect('polls:admin_event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'title': f'Edycja wydarzenia: {event.title}'
    }
    return render(request, 'polls/admin/event_form.html', context)


@staff_member_required
def admin_event_detail(request, event_id):
    """Szczegóły wydarzenia w panelu admina"""
    event = get_object_or_404(Event, id=event_id)
    candidates = event.candidates.all()
    
    # Statystyki
    total_votes = event.votes.count()
    unique_voters = event.votes.values('ip_address').distinct().count()
    
    # Wyniki
    results = []
    for candidate in candidates:
        vote_count = candidate.vote_count
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            'candidate': candidate,
            'vote_count': vote_count,
            'percentage': round(percentage, 2)
        })
    
    results.sort(key=lambda x: x['vote_count'], reverse=True)
    
    context = {
        'event': event,
        'candidates': candidates,
        'results': results,
        'total_votes': total_votes,
        'unique_voters': unique_voters,
        'now': timezone.now(),
    }
    return render(request, 'polls/admin/event_detail.html', context)


@staff_member_required
def admin_candidate_create(request, event_id):
    """Dodawanie kandydata do wydarzenia"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.event = event
            candidate.save()
            messages.success(request, f'Kandydat "{candidate.name}" został dodany.')
            return redirect('polls:admin_event_detail', event_id=event.id)
    else:
        form = CandidateForm()
    
    context = {
        'form': form,
        'event': event,
        'title': f'Dodaj kandydata do: {event.title}'
    }
    return render(request, 'polls/admin/candidate_form.html', context)


@staff_member_required
def admin_candidate_edit(request, candidate_id):
    """Edycja kandydata"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, f'Kandydat "{candidate.name}" został zaktualizowany.')
            return redirect('polls:admin_event_detail', event_id=candidate.event.id)
    else:
        form = CandidateForm(instance=candidate)
    
    context = {
        'form': form,
        'candidate': candidate,
        'title': f'Edycja kandydata: {candidate.name}'
    }
    return render(request, 'polls/admin/candidate_form.html', context)


@staff_member_required
def export_results(request, event_id):
    """Eksport wyników do CSV"""
    event = get_object_or_404(Event, id=event_id)
    candidates = event.candidates.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="wyniki_{event.title}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Kandydat', 'Liczba głosów', 'Procent', 'Typ kandydata'])
    
    total_votes = event.votes.count()
    
    for candidate in candidates:
        vote_count = candidate.vote_count
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        writer.writerow([
            candidate.name,
            vote_count,
            f"{percentage:.2f}%",
            candidate.get_candidate_type_display()
        ])
    
    return response





@staff_member_required
@require_POST
def delete_comment(request, comment_id):
    """Usuwanie komentarza"""
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    
    # Sprawdź czy to jest AJAX request
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'success': True, 'message': 'Komentarz został usunięty.'})
    
    messages.success(request, 'Komentarz został usunięty.')
    return redirect('polls:moderate_comments')


@staff_member_required
@require_POST
def delete_event(request, event_id):
    """Usuwanie wydarzenia"""
    event = get_object_or_404(Event, id=event_id)
    event_title = event.title
    
    # Usuń wydarzenie (kaskadowo usunie też kandydatów, głosy, komentarze)
    event.delete()
    
    messages.success(request, f'Wydarzenie "{event_title}" zostało usunięte.')
    return redirect('polls:admin_dashboard')
