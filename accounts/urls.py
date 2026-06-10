from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('tracked-accounts/add/', views.add_tracked_account, name='add_tracked_account'),
    path('tracked-accounts/<int:pk>/remove/', views.remove_tracked_account, name='remove_tracked_account'),
]