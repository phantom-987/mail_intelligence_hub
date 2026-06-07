from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.core.cache import cache
from gmail_sync.models import Email
from email_processor.models import Keyword, EmailAnalysis
from .serializers import EmailSerializer, EmailDetailSerializer, KeywordSerializer


class EmailListAPI(generics.ListAPIView):
    serializer_class = EmailSerializer

    def get_queryset(self):
        qs = Email.objects.filter(user=self.request.user).select_related('analysis')
        category = self.request.query_params.get('category')
        priority = self.request.query_params.get('priority')
        q = self.request.query_params.get('q')
        if category:
            qs = qs.filter(analysis__category=category)
        if priority:
            qs = qs.filter(analysis__priority=priority)
        if q:
            qs = qs.filter(subject__icontains=q)
        return qs


class EmailDetailAPI(generics.RetrieveAPIView):
    serializer_class = EmailDetailSerializer

    def get_queryset(self):
        return Email.objects.filter(user=self.request.user)


class KeywordListCreateAPI(generics.ListCreateAPIView):
    serializer_class = KeywordSerializer

    def get_queryset(self):
        return Keyword.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class KeywordDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = KeywordSerializer

    def get_queryset(self):
        return Keyword.objects.filter(user=self.request.user)


class DashboardStatsAPI(APIView):
    def get(self, request):
        user = request.user
        cache_key = f"dashboard_stats_{user.id}"
        stats = cache.get(cache_key)
        if not stats:
            today = timezone.now().date()
            stats = {
                'total_emails': Email.objects.filter(user=user).count(),
                'high_priority': EmailAnalysis.objects.filter(
                    email__user=user, priority='High').count(),
                'today_emails': Email.objects.filter(
                    user=user, received_at__date=today).count(),
                'important_emails': EmailAnalysis.objects.filter(
                    email__user=user, priority__in=['High', 'Medium']).count(),
            }
            cache.set(cache_key, stats, 300)
        return Response(stats)


class ManualSyncAPI(APIView):
    def post(self, request):
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
        return Response({'synced': saved}, status=status.HTTP_200_OK)