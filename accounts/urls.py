from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Linked accounts
    path('linked/', views.linked_accounts_list, name='linked_accounts_list'),
    path('connect/gmail/', views.connect_gmail, name='connect_gmail'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('disconnect/<int:account_id>/', views.disconnect_account, name='disconnect_account'),
    path('nickname/<int:account_id>/', views.update_nickname, name='update_nickname'),
    path('toggle/<int:account_id>/', views.toggle_account, name='toggle_account'),
]