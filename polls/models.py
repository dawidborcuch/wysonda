from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Event(models.Model):
    """Model reprezentujący wydarzenie wyborcze"""
    EVENT_TYPES = [
        ('presidential', 'Wybory Prezydenckie'),
        ('parliamentary', 'Wybory Parlamentarne'),
        ('european', 'Wybory do Parlamentu Europejskiego'),
        ('local', 'Wybory Samorządowe'),
        ('other', 'Inne'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Aktywny'),
        ('upcoming', 'Nadchodzący'),
        ('finished', 'Zakończony'),
        ('private', 'Prywatny'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="Nazwa wydarzenia")
    description = models.TextField(verbose_name="Opis")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name="Typ wydarzenia")
    event_date = models.DateTimeField(verbose_name="Data wydarzenia")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming', verbose_name="Status")
    is_private = models.BooleanField(default=False, verbose_name="Sondaż prywatny")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['event_date']
        verbose_name = "Wydarzenie"
        verbose_name_plural = "Wydarzenia"
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        """Sprawdza czy sondaż jest aktywny"""
        now = timezone.now()
        return self.status == 'active' and self.event_date > now
    
    @property
    def is_finished(self):
        """Sprawdza czy sondaż jest zakończony"""
        return self.status == 'finished' or self.event_date < timezone.now()
    
    def update_status(self):
        """Aktualizuje status na podstawie daty"""
        now = timezone.now()
        
        if self.event_date < now:
            if self.status != 'finished':
                self.status = 'finished'
                return True
        elif self.status == 'active':
            # Jeśli jest aktywny i data jeszcze nie minęła, zostaje aktywny
            pass
        elif self.status == 'upcoming' and self.event_date <= now + timezone.timedelta(days=1):
            # Jeśli nadchodzący i data jest w ciągu 24h, staje się aktywny
            self.status = 'active'
            return True
        
        return False
    
    def save(self, *args, **kwargs):
        """Przed zapisem aktualizuje status"""
        self.update_status()
        super().save(*args, **kwargs)


class Candidate(models.Model):
    """Model reprezentujący kandydata lub partię"""
    CANDIDATE_TYPES = [
        ('individual', 'Osoba fizyczna'),
        ('party', 'Partia polityczna'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='candidates', verbose_name="Wydarzenie")
    name = models.CharField(max_length=200, verbose_name="Nazwa")
    description = models.TextField(verbose_name="Opis")
    candidate_type = models.CharField(max_length=20, choices=CANDIDATE_TYPES, verbose_name="Typ kandydata")
    main_photo = models.ImageField(upload_to='candidates/', verbose_name="Główne zdjęcie")
    additional_photos = models.JSONField(default=list, blank=True, verbose_name="Dodatkowe zdjęcia")
    articles = models.JSONField(default=list, blank=True, verbose_name="Artykuły")
    extended_description = models.TextField(blank=True, verbose_name="Rozszerzony opis")
    background_info = models.TextField(blank=True, verbose_name="Informacje tła")
    is_premium = models.BooleanField(default=False, verbose_name="Profil premium")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Kandydat"
        verbose_name_plural = "Kandydaci"
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"
    
    @property
    def vote_count(self):
        """Liczba głosów dla kandydata"""
        return self.votes.count()
    
    @property
    def vote_percentage(self):
        """Procent głosów dla kandydata"""
        total_votes = self.event.votes.count()
        if total_votes == 0:
            return 0
        return round((self.vote_count / total_votes) * 100, 2)


class Vote(models.Model):
    """Model reprezentujący głos użytkownika"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='votes', verbose_name="Wydarzenie")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes', verbose_name="Kandydat")
    ip_address = models.GenericIPAddressField(verbose_name="Adres IP")
    browser_fingerprint = models.CharField(max_length=255, blank=True, verbose_name="Fingerprint przeglądarki")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    location_data = models.JSONField(default=dict, blank=True, verbose_name="Dane lokalizacji")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'ip_address']
        verbose_name = "Głos"
        verbose_name_plural = "Głosy"
    
    def __str__(self):
        return f"Głos na {self.candidate.name} w {self.event.title}"


class Comment(models.Model):
    """Model reprezentujący komentarz pod profilem kandydata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='comments', verbose_name="Kandydat")
    author_name = models.CharField(max_length=100, verbose_name="Nazwa autora")
    author_email = models.EmailField(verbose_name="Email autora")
    content = models.TextField(verbose_name="Treść komentarza")
    is_approved = models.BooleanField(default=False, verbose_name="Zatwierdzony")
    ip_address = models.GenericIPAddressField(verbose_name="Adres IP")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Komentarz"
        verbose_name_plural = "Komentarze"
    
    def __str__(self):
        return f"Komentarz od {self.author_name} na {self.candidate.name}"


class UserBadge(models.Model):
    """Model reprezentujący odznaki użytkowników"""
    BADGE_TYPES = [
        ('voter', 'Głosujący'),
        ('regular', 'Regularny głosujący'),
        ('super_voter', 'Super głosujący'),
        ('commenter', 'Komentujący'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges', verbose_name="Użytkownik")
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, verbose_name="Typ odznaki")
    description = models.TextField(verbose_name="Opis odznaki")
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'badge_type']
        verbose_name = "Odznaka użytkownika"
        verbose_name_plural = "Odznaki użytkowników"
    
    def __str__(self):
        return f"{self.user.email} - {self.get_badge_type_display()}"


class PollAnalytics(models.Model):
    """Model reprezentujący analitykę sondaży"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='analytics', verbose_name="Wydarzenie")
    total_votes = models.IntegerField(default=0, verbose_name="Łączna liczba głosów")
    unique_voters = models.IntegerField(default=0, verbose_name="Unikalni głosujący")
    geographic_data = models.JSONField(default=dict, verbose_name="Dane geograficzne")
    demographic_data = models.JSONField(default=dict, verbose_name="Dane demograficzne")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Analityka sondażu"
        verbose_name_plural = "Analityka sondaży"
    
    def __str__(self):
        return f"Analityka dla {self.event.title}"
