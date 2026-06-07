
from django.db import models
from django.contrib.auth.models import User


class Email(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails')
    gmail_message_id = models.CharField(max_length=255, unique=True)
    sender = models.CharField(max_length=500)
    sender_name = models.CharField(max_length=255, blank=True)
    receiver = models.CharField(max_length=500, blank=True)
    subject = models.TextField(blank=True)
    body = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    received_at = models.DateTimeField()
    has_attachments = models.BooleanField(default=False)
    attachment_names = models.JSONField(default=list)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['user', 'received_at']),
            models.Index(fields=['user', 'is_processed']),
        ]

    def __str__(self):
        return f"{self.subject[:60]} — {self.sender}"
