import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def sync_all_users_emails():
    from accounts.models import GmailToken
    from services.gmail_service import fetch_emails
    from services.parser_service import process_email
    from gmail_sync.models import Email

    logger.info("Scheduler: Starting email sync...")

    for token in GmailToken.objects.select_related('user').all():
        user = token.user
        lock_key = f"sync_lock_{user.id}"
        if cache.get(lock_key):
            continue
        cache.set(lock_key, True, timeout=240)
        try:
            messages_data = fetch_emails(user, max_results=20)
            for msg_data in messages_data:
                email, created = Email.objects.get_or_create(
                    gmail_message_id=msg_data['gmail_message_id'],
                    defaults={**msg_data, 'user': user}
                )
                if created:
                    process_email(email)
            cache.delete(f"dashboard_stats_{user.id}")
        except Exception as e:
            logger.error(f"Sync error for {user.username}: {e}")
        finally:
            cache.delete(lock_key)