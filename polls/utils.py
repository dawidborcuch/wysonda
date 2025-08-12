import hashlib
import json
from django.http import HttpRequest
from django.core.cache import cache
from .models import Vote, Event


def get_client_ip(request: HttpRequest) -> str:
    """Pobiera adres IP klienta"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_browser_fingerprint(request: HttpRequest) -> str:
    """Generuje fingerprint przeglądarki"""
    # Pobierz dane z request
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
    
    # Utwórz fingerprint
    fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}"
    fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    return fingerprint


def check_vote_eligibility(request: HttpRequest, event: Event, client_ip: str) -> bool:
    """Sprawdza czy użytkownik może głosować"""
    # Sprawdź czy sondaż jest aktywny
    if not event.is_active:
        return False
    
    # Sprawdź czy już głosował z tego IP
    if Vote.objects.filter(event=event, ip_address=client_ip).exists():
        return False
    
    # Sprawdź czy głosował z tej przeglądarki (fingerprint)
    browser_fingerprint = get_browser_fingerprint(request)
    if browser_fingerprint and Vote.objects.filter(
        event=event, 
        browser_fingerprint=browser_fingerprint
    ).exists():
        return False
    
    # Sprawdź localStorage/cookie (implementacja po stronie frontendu)
    # Tutaj możemy dodać dodatkowe sprawdzenia
    
    return True


def get_vote_cache_key(event_id: str) -> str:
    """Generuje klucz cache dla wyników głosowania"""
    return f"vote_results_{event_id}"


def cache_vote_results(event_id: str, results: dict, timeout: int = 300):
    """Cache'uje wyniki głosowania"""
    cache_key = get_vote_cache_key(event_id)
    cache.set(cache_key, results, timeout)


def get_cached_vote_results(event_id: str) -> dict:
    """Pobiera wyniki głosowania z cache"""
    cache_key = get_vote_cache_key(event_id)
    return cache.get(cache_key)


def invalidate_vote_cache(event_id: str):
    """Invaliduje cache wyników głosowania"""
    cache_key = get_vote_cache_key(event_id)
    cache.delete(cache_key)


def calculate_vote_statistics(event: Event) -> dict:
    """Oblicza statystyki głosowania"""
    total_votes = event.votes.count()
    unique_voters = event.votes.values('ip_address').distinct().count()
    
    # Statystyki geograficzne (przykład)
    geographic_data = {}
    for vote in event.votes.all():
        # Tutaj można dodać geolokalizację na podstawie IP
        # Na razie używamy prostego podziału
        region = "Nieznany"
        if vote.ip_address:
            # Prosty podział na podstawie IP (przykład)
            if vote.ip_address.startswith('192.168.'):
                region = "Sieć lokalna"
            elif vote.ip_address.startswith('10.'):
                region = "Sieć prywatna"
            else:
                region = "Internet"
        
        geographic_data[region] = geographic_data.get(region, 0) + 1
    
    return {
        'total_votes': total_votes,
        'unique_voters': unique_voters,
        'geographic_data': geographic_data,
        'participation_rate': round((unique_voters / max(total_votes, 1)) * 100, 2)
    }


def generate_vote_report(event: Event) -> dict:
    """Generuje raport z głosowania"""
    candidates = event.candidates.all()
    total_votes = event.votes.count()
    
    report = {
        'event': {
            'title': event.title,
            'event_type': event.get_event_type_display(),
            'event_date': event.event_date.isoformat(),
            'total_votes': total_votes,
        },
        'candidates': [],
        'statistics': calculate_vote_statistics(event)
    }
    
    for candidate in candidates:
        vote_count = candidate.vote_count
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        
        report['candidates'].append({
            'name': candidate.name,
            'candidate_type': candidate.get_candidate_type_display(),
            'vote_count': vote_count,
            'percentage': round(percentage, 2),
            'is_premium': candidate.is_premium
        })
    
    # Sortuj kandydatów malejąco
    report['candidates'].sort(key=lambda x: x['vote_count'], reverse=True)
    
    return report


def check_user_badges(user) -> list:
    """Sprawdza i przyznaje odznaki użytkownikowi"""
    from .models import UserBadge, Vote
    
    badges = []
    
    # Sprawdź liczbę głosów
    vote_count = Vote.objects.filter(ip_address=get_client_ip(user)).count()
    
    if vote_count >= 1:
        badges.append('voter')
    if vote_count >= 5:
        badges.append('regular')
    if vote_count >= 10:
        badges.append('super_voter')
    
    # Sprawdź komentarze
    comment_count = user.comments.filter(is_approved=True).count()
    if comment_count >= 3:
        badges.append('commenter')
    
    return badges


def award_user_badges(user, badges: list):
    """Przyznaje odznaki użytkownikowi"""
    from .models import UserBadge
    
    for badge_type in badges:
        UserBadge.objects.get_or_create(
            user=user,
            badge_type=badge_type,
            defaults={'description': f'Odznaka za {badge_type}'}
        )


def sanitize_filename(filename: str) -> str:
    """Sanityzuje nazwę pliku"""
    import re
    # Usuń niebezpieczne znaki
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Ogranicz długość
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1)
        filename = name[:95] + '.' + ext
    return filename


def validate_image_file(file) -> bool:
    """Waliduje plik obrazu"""
    import imghdr
    
    # Sprawdź rozmiar
    if file.size > 5 * 1024 * 1024:  # 5MB
        return False
    
    # Sprawdź typ pliku
    file_type = imghdr.what(file)
    if file_type not in ['jpeg', 'png', 'gif']:
        return False
    
    return True
