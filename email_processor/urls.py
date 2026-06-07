from django.urls import path
from . import views

app_name = 'keywords'

urlpatterns = [
    path('keywords/', views.keyword_list, name='list'),
    path('keywords/add/', views.keyword_add, name='add'),
    path('keywords/<int:pk>/toggle/', views.keyword_toggle, name='toggle'),
    path('keywords/<int:pk>/delete/', views.keyword_delete, name='delete'),
    path('emails/', views.email_list, name='email_list'),
    path('emails/<int:pk>/', views.email_detail, name='email_detail'),
]