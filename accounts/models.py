from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gmail_connected = models.BooleanField(default=False)
    gmail_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class GmailToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gmail_token')
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField(null=True, blank=True)
    scopes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token for {self.user.username}"

class LinkedAccount(models.Model):
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook'),  # extendable later
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='linked_accounts')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='gmail')
    email = models.EmailField()
    nickname = models.CharField(max_length=100, blank=True)

    # OAuth tokens
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'email')  # prevent duplicate accounts
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.email} ({self.provider})"
