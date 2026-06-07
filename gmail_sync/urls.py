from django.urls import path
from . import views

app_name = 'gmail_sync'

urlpatterns = [
    path('oauth/start/', views.oauth_start, name='oauth_start'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('disconnect/', views.disconnect_gmail, name='disconnect'),
]