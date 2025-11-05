# users/urls.py
from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),               # HTML fallback
    path('api/me/', views.MeView.as_view(), name='api-me'),
    path('signup/', views.OnboardingAPI.as_view(), name='api-onboarding'),
]