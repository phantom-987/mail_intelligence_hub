from django.urls import path
from . import views

urlpatterns = [
    path('emails/', views.EmailListAPI.as_view()),
    path('email/<int:pk>/', views.EmailDetailAPI.as_view()),
    path('keywords/', views.KeywordListCreateAPI.as_view()),
    path('keywords/<int:pk>/', views.KeywordDetailAPI.as_view()),
    path('dashboard/', views.DashboardStatsAPI.as_view()),
    path('sync/', views.ManualSyncAPI.as_view()),
]