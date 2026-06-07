import json
import logging
import os
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from accounts.models import GmailToken, UserProfile

logger = logging.getLogger(__name__)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


def get_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GMAIL_REDIRECT_URI],
            }
        },
        scopes=settings.GMAIL_SCOPES,
        redirect_uri=settings.GMAIL_REDIRECT_URI,
    )


def oauth_start(request):
    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true',
        code_challenge=None,
        code_challenge_method=None,
    )
    request.session['oauth_state'] = state
    request.session.modified = True
    request.session.save()
    return redirect(auth_url)


def oauth_callback(request):
    state = request.session.get('oauth_state')

    if not state:
        state = request.GET.get('state', '')
        if not state:
            messages.error(request, 'OAuth state missing. Please try again.')
            return redirect('accounts:login')

    flow = get_flow()

    try:
        flow.code_verifier = None
        flow.fetch_token(
            authorization_response=request.build_absolute_uri(),
        )
    except Exception as e:
        logger.error(f"OAuth token fetch error: {e}")
        messages.error(request, f'Failed to complete Google login: {str(e)}')
        return redirect('accounts:login')

    creds = flow.credentials

    # Get user info from Google
    gmail_email = ''
    first_name = ''
    last_name = ''

    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials as GoogleCreds
        temp_creds = GoogleCreds(token=creds.token)
        oauth2_service = build('oauth2', 'v2', credentials=temp_creds)
        google_user_info = oauth2_service.userinfo().get().execute()
        gmail_email = google_user_info.get('email', '')
        first_name = google_user_info.get('given_name', '')
        last_name = google_user_info.get('family_name', '')
    except Exception as e:
        logger.error(f"Failed to get Google user info: {e}")

    if not gmail_email:
        messages.error(request, 'Could not retrieve your Gmail address. Please try again.')
        return redirect('accounts:login')

    # Auto-create or get user — safe against duplicates
    if not request.user.is_authenticated:
        user = User.objects.filter(email=gmail_email).first()

        if not user:
            username = gmail_email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=gmail_email,
                first_name=first_name,
                last_name=last_name,
            )

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    else:
        user = request.user

    # Save Gmail token
    GmailToken.objects.update_or_create(
        user=user,
        defaults={
            'access_token': creds.token,
            'refresh_token': creds.refresh_token or '',
            'scopes': json.dumps(list(creds.scopes or [])),
        }
    )

    # Update profile
    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            'gmail_connected': True,
            'gmail_email': gmail_email,
        }
    )

    messages.success(request, f'Welcome, {first_name or user.username}! Gmail connected successfully.')
    return redirect('dashboard:home')


@login_required
def disconnect_gmail(request):
    if request.method == 'POST':
        GmailToken.objects.filter(user=request.user).delete()
        UserProfile.objects.filter(user=request.user).update(gmail_connected=False)
        messages.success(request, 'Gmail disconnected.')
    return redirect('accounts:profile')