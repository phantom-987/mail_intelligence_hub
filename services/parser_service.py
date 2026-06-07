import logging
from email_processor.models import Keyword, EmailAnalysis
from services.ai_service import analyze_email

logger = logging.getLogger(__name__)


def check_keyword_matches(email):
    keywords = Keyword.objects.filter(
        user=email.user, enabled=True
    ).values_list('keyword', flat=True)
    body_lower = (email.subject + ' ' + email.body).lower()
    return [kw for kw in keywords if kw.lower() in body_lower]


def process_email(email):
    if EmailAnalysis.objects.filter(email=email).exists():
        return None

    matches = check_keyword_matches(email)
    analysis_data = analyze_email(
        subject=email.subject,
        sender=email.sender,
        body=email.body,
    )

    analysis = EmailAnalysis.objects.create(
        email=email,
        summary=analysis_data['summary'],
        category=analysis_data['category'],
        priority=analysis_data['priority'],
        deadline=analysis_data['deadline'],
        important_points=analysis_data['important_points'],
        links=analysis_data['links'],
        keyword_matches=matches,
    )

    email.is_processed = True
    email.save(update_fields=['is_processed'])
    return analysis