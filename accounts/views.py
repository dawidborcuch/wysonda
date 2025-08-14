from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile


class SignUpView(CreateView):
    """Widok rejestracji użytkownika"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('polls:home')
    
    def form_valid(self, form):
        """Po pomyślnej rejestracji zaloguj użytkownika"""
        response = super().form_valid(form)
        from django.contrib.auth import authenticate
        user = authenticate(
            username=self.object.username,
            password=form.cleaned_data['password1']
        )
        if user:
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, f'Witaj {form.cleaned_data["nickname"]}! Twoje konto zostało utworzone.')
        return response


class CustomLoginView(LoginView):
    """Własny widok logowania"""
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('polls:home')
    
    def get_success_url(self):
        """Przekieruj do strony głównej po zalogowaniu"""
        messages.success(self.request, f'Witaj ponownie, {self.request.user.username}!')
        return reverse_lazy('polls:home')


@login_required
def profile_view(request):
    """Widok profilu użytkownika"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            # Zaktualizuj username w modelu User
            new_nickname = form.cleaned_data['nickname']
            if new_nickname != request.user.username:
                request.user.username = new_nickname
                request.user.save()
            
            form.save()
            messages.success(request, 'Profil został zaktualizowany.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def logout_view(request):
    """Własny widok wylogowania"""
    logout(request)
    messages.success(request, 'Zostałeś pomyślnie wylogowany.')
    return redirect('polls:home')
