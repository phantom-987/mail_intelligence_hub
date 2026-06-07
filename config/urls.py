from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('gmail/', include('gmail_sync.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('emails/', include('email_processor.urls')),
    path('api/', include('api.urls')),
    path('', lambda request: redirect('dashboard:home')),  # root redirect
]