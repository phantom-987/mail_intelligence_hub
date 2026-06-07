from rest_framework import serializers
from gmail_sync.models import Email
from email_processor.models import Keyword, EmailAnalysis


class EmailAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAnalysis
        fields = ['summary', 'category', 'priority', 'deadline',
                  'important_points', 'links', 'keyword_matches']


class EmailSerializer(serializers.ModelSerializer):
    analysis = EmailAnalysisSerializer(read_only=True)

    class Meta:
        model = Email
        fields = ['id', 'gmail_message_id', 'sender', 'sender_name',
                  'subject', 'received_at', 'has_attachments', 'is_processed', 'analysis']


class EmailDetailSerializer(serializers.ModelSerializer):
    analysis = EmailAnalysisSerializer(read_only=True)

    class Meta:
        model = Email
        fields = '__all__'


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ['id', 'keyword', 'enabled', 'created_at']
        read_only_fields = ['created_at']