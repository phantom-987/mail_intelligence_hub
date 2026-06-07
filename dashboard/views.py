from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from gmail_sync.models import Email
from email_processor.models import EmailAnalysis


@login_required
def home(request):
    user = request.user
    cache_key = f"dashboard_stats_{user.id}"
    stats = cache.get(cache_key)

    if not stats:
        today = timezone.now().date()
        stats = {
            'total': Email.objects.filter(user=user).count(),
            'high_priority': EmailAnalysis.objects.filter(email__user=user, priority='High').count(),
            'today': Email.objects.filter(user=user, received_at__date=today).count(),
            'important': EmailAnalysis.objects.filter(email__user=user, priority__in=['High', 'Medium']).count(),
        }
        cache.set(cache_key, stats, timeout=300)

    recent_emails = (
        Email.objects.filter(user=user)
        .select_related('analysis')
        .order_by('-received_at')[:20]
    )

    return render(request, 'dashboard/home.html', {
        'stats': stats,
        'emails': recent_emails,
    })


@login_required
def manual_sync(request):
    if request.method == 'POST':
        from services.gmail_service import fetch_emails
        from services.parser_service import process_email

        messages_data = fetch_emails(request.user, max_results=20)
        saved = 0
        for msg_data in messages_data:
            email, created = Email.objects.get_or_create(
                gmail_message_id=msg_data['gmail_message_id'],
                defaults={**msg_data, 'user': request.user}
            )
            if created:
                process_email(email)
                saved += 1
        cache.delete(f"dashboard_stats_{request.user.id}")
        messages.success(request, f'Synced {saved} new emails.')
    return redirect('dashboard:home')