from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import LinkedAccount


# ─────────────────────────────────────────────
# AUTH FORMS (your existing code — unchanged)
# ─────────────────────────────────────────────

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        """Ensure email is unique across all users."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['autocomplete'] = 'off'


# ─────────────────────────────────────────────
# LINKED ACCOUNT FORMS (new)
# ─────────────────────────────────────────────

class AccountNicknameForm(forms.ModelForm):
    """
    Lets the user assign a friendly label to a linked Gmail account.
    Example: 'Work', 'Personal', 'Freelance'
    """

    class Meta:
        model = LinkedAccount
        fields = ['nickname']
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Work Gmail, Personal, Freelance',
                'maxlength': '100',
                'autofocus': True,
            })
        }
        labels = {
            'nickname': 'Account Nickname',
        }
        help_texts = {
            'nickname': 'Give this account a friendly name to identify it easily.',
        }

    def clean_nickname(self):
        """Strip extra whitespace from nickname."""
        return self.cleaned_data.get('nickname', '').strip()


class LinkedAccountForm(forms.ModelForm):
    """
    Full edit form for a linked account.
    Used in admin or advanced settings — lets user update
    nickname and active status together.
    """

    class Meta:
        model = LinkedAccount
        fields = ['nickname', 'is_active']
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Work Gmail, Personal',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
        }
        labels = {
            'nickname': 'Nickname',
            'is_active': 'Enable syncing for this account',
        }

    def clean_nickname(self):
        return self.cleaned_data.get('nickname', '').strip()


class ProfileUpdateForm(forms.ModelForm):
    """
    Optional: lets user update first name, last name, email
    from the profile page.
    """
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        """Ensure updated email isn't taken by another user."""
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already in use by another account.')
        return email