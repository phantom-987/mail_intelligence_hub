import base64
import logging
from email.utils import parsedate_to_datetime
from django.conf import settings
from django.contrib.auth.models import User
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from accounts.models import GmailToken

logger = logging.getLogger(__name__)


def get_credentials(user):
    try:
        token = GmailToken.objects.get(user=user)
        creds = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            scopes=settings.GMAIL_SCOPES,
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token.access_token = creds.token
            token.save()
        return creds
    except GmailToken.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Credentials error for {user}: {e}")
        return None


def get_gmail_service(user):
    creds = get_credentials(user)
    if not creds:
        return None
    return build('gmail', 'v1', credentials=creds)


def decode_body(payload):
    plain = ''
    html = ''

    def extract(part):
        nonlocal plain, html
        mime = part.get('mimeType', '')
        data = part.get('body', {}).get('data', '')
        if data:
            decoded = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='replace')
            if mime == 'text/plain':
                plain += decoded
            elif mime == 'text/html':
                html += decoded
        for sub in part.get('parts', []):
            extract(sub)

    extract(payload)
    return plain, html


def fetch_emails(user, max_results=50):
    service = get_gmail_service(user)
    if not service:
        return []

    from gmail_sync.models import Email
    existing_ids = set(
        Email.objects.filter(user=user).values_list('gmail_message_id', flat=True)
    )

    try:
        result = service.users().messages().list(
            userId='me', maxResults=max_results, labelIds=['INBOX']
        ).execute()
        messages = result.get('messages', [])
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        return []

    fetched = []
    for msg_ref in messages:
        msg_id = msg_ref['id']
        if msg_id in existing_ids:
            continue
        try:
            msg = service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()
            fetched.append(parse_message(msg))
        except HttpError as e:
            logger.error(f"Error fetching message {msg_id}: {e}")

    return fetched


def parse_message(msg):
    headers = {h['name'].lower(): h['value']
               for h in msg['payload'].get('headers', [])}
    plain, html = decode_body(msg['payload'])

    raw_from = headers.get('from', '')
    sender_name = ''
    sender_email = raw_from
    if '<' in raw_from:
        parts = raw_from.split('<')
        sender_name = parts[0].strip().strip('"')
        sender_email = parts[1].rstrip('>')

    try:
        received_at = parsedate_to_datetime(headers.get('date', ''))
    except Exception:
        from django.utils import timezone
        received_at = timezone.now()

    attachments = []
    def find_attachments(payload):
        if payload.get('filename'):
            attachments.append(payload['filename'])
        for part in payload.get('parts', []):
            find_attachments(part)
    find_attachments(msg['payload'])

    return {
        'gmail_message_id': msg['id'],
        'sender': sender_email.strip(),
        'sender_name': sender_name,
        'receiver': headers.get('to', ''),
        'subject': headers.get('subject', '(No Subject)'),
        'body': plain or 'No plain text body.',
        'body_html': html,
        'received_at': received_at,
        'has_attachments': bool(attachments),
        'attachment_names': attachments,
    }