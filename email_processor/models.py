from django.db import models
from django.contrib.auth.models import User
from gmail_sync.models import Email


class Keyword(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='keywords')
    keyword = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'keyword')
        ordering = ['keyword']

    def __str__(self):
        return self.keyword


class EmailAnalysis(models.Model):
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    CATEGORY_CHOICES = [
        ('Job', 'Job'),
        ('Internship', 'Internship'),
        ('Funding', 'Funding'),
        ('AI', 'AI'),
        ('Startup', 'Startup'),
        ('Security', 'Security'),
        ('Event', 'Event'),
        ('Personal', 'Personal'),
        ('Promotion', 'Promotion'),
        ('Other', 'Other'),
    ]

    email = models.OneToOneField(Email, on_delete=models.CASCADE, related_name='analysis')
    summary = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Low')
    deadline = models.CharField(max_length=255, blank=True)
    important_points = models.JSONField(default=list)
    links = models.JSONField(default=list)
    keyword_matches = models.JSONField(default=list)
    sentiment = models.CharField(max_length=20, default='Neutral')
    action_required = models.BooleanField(default=False)
    action_items = models.JSONField(default=list)
    suggested_reply = models.TextField(blank=True)
    reply_subject = models.CharField(max_length=500, blank=True)
    sender_verified = models.BooleanField(default=True)
    sender_verification = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis: {self.email.subject[:40]}"