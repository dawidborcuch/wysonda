from django import forms
from django.utils import timezone
from .models import Event, Candidate, Comment


class EventForm(forms.ModelForm):
    """Formularz dla wydarzenia"""
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'event_date', 'status', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_event_date(self):
        """Walidacja daty wydarzenia"""
        event_date = self.cleaned_data.get('event_date')
        if event_date and event_date < timezone.now():
            raise forms.ValidationError('Data wydarzenia nie może być w przeszłości.')
        return event_date


class CandidateForm(forms.ModelForm):
    """Formularz dla kandydata"""
    class Meta:
        model = Candidate
        fields = ['name', 'description', 'candidate_type', 'main_photo', 'extended_description', 'background_info', 'is_premium']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'candidate_type': forms.Select(attrs={'class': 'form-select'}),
            'main_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'extended_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'background_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_premium': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_main_photo(self):
        """Walidacja zdjęcia"""
        photo = self.cleaned_data.get('main_photo')
        if photo:
            # Sprawdź rozmiar pliku (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Rozmiar pliku nie może przekraczać 5MB.')
            
            # Sprawdź typ pliku
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if photo.content_type not in allowed_types:
                raise forms.ValidationError('Dozwolone są tylko pliki JPG, PNG i GIF.')
        
        return photo


class CommentForm(forms.ModelForm):
    """Formularz dla komentarza"""
    class Meta:
        model = Comment
        fields = ['author_name', 'author_email', 'content']
        widgets = {
            'author_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Twoje imię'}),
            'author_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Twój email'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Napisz swój komentarz...'}),
        }
    
    def clean_content(self):
        """Walidacja treści komentarza"""
        content = self.cleaned_data.get('content')
        if content:
            if len(content.strip()) < 10:
                raise forms.ValidationError('Komentarz musi mieć co najmniej 10 znaków.')
            if len(content) > 1000:
                raise forms.ValidationError('Komentarz nie może przekraczać 1000 znaków.')
        return content


class VoteForm(forms.Form):
    """Formularz dla głosowania"""
    candidate_id = forms.UUIDField(widget=forms.HiddenInput())
    fingerprint = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.fields['candidate_id'].choices = [
            (candidate.id, candidate.name) for candidate in event.candidates.all()
        ]
    
    def clean_candidate_id(self):
        """Walidacja kandydata"""
        candidate_id = self.cleaned_data.get('candidate_id')
        try:
            candidate = self.event.candidates.get(id=candidate_id)
            return candidate
        except Candidate.DoesNotExist:
            raise forms.ValidationError('Nieprawidłowy kandydat.')


class SearchForm(forms.Form):
    """Formularz wyszukiwania"""
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Szukaj wydarzeń, kandydatów...'
        })
    )
    event_type = forms.ChoiceField(
        choices=[('', 'Wszystkie typy')] + Event.EVENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Wszystkie statusy')] + Event.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
