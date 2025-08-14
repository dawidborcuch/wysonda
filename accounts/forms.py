from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Formularz rejestracji z walidacją nicku"""
    nickname = forms.CharField(
        max_length=50,
        required=True,
        label='Nazwa użytkownika',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wybierz nazwę użytkownika'
        }),
        help_text='Nazwa użytkownika musi być unikalna i może zawierać litery, cyfry i podkreślenia.'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Twój email'
        })
    )
    
    class Meta:
        model = User
        fields = ('nickname', 'email', 'password1', 'password2')
    
    def clean_nickname(self):
        """Walidacja unikalności nazwy użytkownika"""
        nickname = self.cleaned_data.get('nickname')
        if nickname:
            # Sprawdź czy nazwa użytkownika już istnieje w User
            if User.objects.filter(username=nickname).exists():
                raise ValidationError('Taka nazwa użytkownika już istnieje. Wybierz inną.')
            
            # Sprawdź czy nickname już istnieje w UserProfile
            if UserProfile.objects.filter(nickname=nickname).exists():
                raise ValidationError('Taka nazwa użytkownika już istnieje. Wybierz inną.')
            
            # Sprawdź czy nazwa użytkownika zawiera tylko dozwolone znaki
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$', nickname):
                raise ValidationError('Nazwa użytkownika może zawierać tylko litery, cyfry i podkreślenia.')
            
            # Sprawdź długość
            if len(nickname) < 3:
                raise ValidationError('Nazwa użytkownika musi mieć co najmniej 3 znaki.')
        
        return nickname
    
    def clean_email(self):
        """Walidacja unikalności emaila"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Ten email jest już zajęty.')
        return email
    
    def save(self, commit=True):
        """Zapisanie użytkownika z nickiem jako username"""
        user = super().save(commit=False)
        user.username = self.cleaned_data['nickname']  # Użyj nicku jako username
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Zaktualizuj nickname w profilu
            if hasattr(user, 'profile'):
                user.profile.nickname = self.cleaned_data['nickname']
                user.profile.save()
        
        return user


class UserProfileForm(forms.ModelForm):
    """Formularz edycji profilu użytkownika"""
    class Meta:
        model = UserProfile
        fields = ['nickname', 'bio', 'avatar']
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Twoja nazwa użytkownika'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Napisz coś o sobie...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_nickname(self):
        """Walidacja unikalności nazwy użytkownika przy edycji"""
        nickname = self.cleaned_data.get('nickname')
        if nickname:
            # Sprawdź czy nazwa użytkownika już istnieje w User (ale nie dla tego samego użytkownika)
            existing_user = User.objects.filter(username=nickname).exclude(id=self.instance.user.id).first()
            if existing_user:
                raise ValidationError('Taka nazwa użytkownika już istnieje. Wybierz inną.')
            
            # Sprawdź czy nickname już istnieje w UserProfile (ale nie dla tego samego użytkownika)
            existing_profile = UserProfile.objects.filter(nickname=nickname).exclude(user=self.instance.user).first()
            if existing_profile:
                raise ValidationError('Taka nazwa użytkownika już istnieje. Wybierz inną.')
            
            # Sprawdź czy nazwa użytkownika zawiera tylko dozwolone znaki
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$', nickname):
                raise ValidationError('Nazwa użytkownika może zawierać tylko litery, cyfry i podkreślenia.')
            
            # Sprawdź długość
            if len(nickname) < 3:
                raise ValidationError('Nazwa użytkownika musi mieć co najmniej 3 znaki.')
        
        return nickname
