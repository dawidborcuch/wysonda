from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Rozszerzenie modelu użytkownika o nickname"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=50, unique=True, verbose_name="Nazwa użytkownika")
    bio = models.TextField(max_length=500, blank=True, verbose_name="O sobie")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profil użytkownika"
        verbose_name_plural = "Profile użytkowników"
    
    def __str__(self):
        return f"{self.nickname} ({self.user.email})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatyczne tworzenie profilu użytkownika"""
    if created:
        # Utwórz profil z tymczasowym nickiem
        UserProfile.objects.create(user=instance, nickname=f"user_{instance.id}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Automatyczne zapisywanie profilu użytkownika"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
