from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import UserProfile, LinkedAccount
from .forms import RegisterForm, LoginForm, AccountNicknameForm, LinkedAccountForm, ProfileUpdateForm
import google_auth_oauthlib.flow
import google.oauth2.credentials
import googleapiclient.discovery
import os

# ─────────────────────────────────────────────
# Allow HTTP for local dev (remove in production)
# ─────────────────────────────────────────────
os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')

GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid',
]


# ─────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard:home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next', 'dashboard:home'))
        messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')



@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'form': form,
    })


# ─────────────────────────────────────────────
# LINKED ACCOUNTS — LIST
# ─────────────────────────────────────────────

@login_required
def linked_accounts_list(request):
    accounts = LinkedAccount.objects.filter(user=request.user)
    return render(request, 'accounts/linked_accounts.html', {
        'accounts': accounts,
        'total': accounts.count(),
    })


# ─────────────────────────────────────────────
# GMAIL OAUTH — CONNECT
# ─────────────────────────────────────────────

@login_required
def connect_gmail(request):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRETS_FILE,
        scopes=GMAIL_SCOPES
    )
    flow.redirect_uri = request.build_absolute_uri('/accounts/oauth/callback/')

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    request.session['oauth_state'] = state
    return redirect(authorization_url)


# ─────────────────────────────────────────────
# GMAIL OAUTH — CALLBACK
# ─────────────────────────────────────────────

@login_required
def oauth_callback(request):
    state = request.session.get('oauth_state')

    if not state:
        messages.error(request, 'OAuth session expired. Please try again.')
        return redirect('accounts:linked_accounts_list')

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRETS_FILE,
        scopes=GMAIL_SCOPES,
        state=state
    )
    flow.redirect_uri = request.build_absolute_uri('/accounts/oauth/callback/')

    try:
        flow.fetch_token(
            authorization_response=request.build_absolute_uri(request.get_full_path())
        )
    except Exception as e:
        messages.error(request, f'Failed to fetch token: {str(e)}')
        return redirect('accounts:linked_accounts_list')

    credentials = flow.credentials

    try:
        service = googleapiclient.discovery.build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        email = user_info.get('email')
    except Exception as e:
        messages.error(request, f'Failed to retrieve account info: {str(e)}')
        return redirect('accounts:linked_accounts_list')

    if not email:
        messages.error(request, 'Could not retrieve email from Google.')
        return redirect('accounts:linked_accounts_list')

    existing_count = LinkedAccount.objects.filter(user=request.user).count()
    if existing_count >= 5:
        messages.warning(request, 'You can link a maximum of 5 accounts.')
        return redirect('accounts:linked_accounts_list')

    linked, created = LinkedAccount.objects.get_or_create(
        user=request.user,
        email=email,
        defaults={'provider': 'gmail'}
    )
    linked.access_token = credentials.token
    if credentials.refresh_token:
        linked.refresh_token = credentials.refresh_token
    linked.token_expiry = credentials.expiry
    linked.is_active = True
    linked.save()

    if created:
        messages.success(request, f'✅ {email} connected successfully!')
    else:
        messages.info(request, f'🔄 {email} tokens refreshed.')

    return redirect('accounts:linked_accounts_list')  # ← fixed


# ─────────────────────────────────────────────
# DISCONNECT AN ACCOUNT
# ─────────────────────────────────────────────

@login_required
def disconnect_account(request, account_id):
    account = get_object_or_404(LinkedAccount, id=account_id, user=request.user)
    if request.method == 'POST':
        email = account.email
        account.delete()
        messages.success(request, f'🗑️ {email} has been disconnected.')
    else:
        messages.warning(request, 'Invalid request method.')
    return redirect('accounts:linked_accounts_list')


# ─────────────────────────────────────────────
# UPDATE NICKNAME
# ─────────────────────────────────────────────

@login_required
def update_nickname(request, account_id):
    account = get_object_or_404(LinkedAccount, id=account_id, user=request.user)
    if request.method == 'POST':
        form = AccountNicknameForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f'✏️ Nickname updated for {account.email}.')
            return redirect('accounts:linked_accounts_list')
    else:
        form = AccountNicknameForm(instance=account)
    return render(request, 'accounts/update_nickname.html', {
        'form': form,
        'account': account,
    })


# ─────────────────────────────────────────────
# TOGGLE ACTIVE / INACTIVE
# ─────────────────────────────────────────────

@login_required
def toggle_account(request, account_id):
    account = get_object_or_404(LinkedAccount, id=account_id, user=request.user)
    if request.method == 'POST':
        account.is_active = not account.is_active
        account.save()
        status = 'activated' if account.is_active else 'paused'
        icon = '▶️' if account.is_active else '⏸️'
        messages.success(request, f'{icon} {account.email} {status}.')
    return redirect('accounts:linked_accounts_list')
