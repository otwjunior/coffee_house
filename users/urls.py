# users/urls.py
from django.urls import path
from . import views

app_name = 'users'  # ← Enables reverse('users:me') in templates

urlpatterns = [
    # ───── API ENDPOINTS ─────
    path('me/', views.MeView.as_view(), name='me'),
    path('onboarding/', views.OnboardingAPI.as_view(), name='onboarding'),
    path('register/', views.RegisterAPI.as_view(), name='register'),
    path('login/', views.LoginAPI.as_view(), name='login'),

    # ───── HTML FALLBACK ─────
    path('login-page/', views.login_view, name='login-page'),
    path('logout/', views.logout_view, name='logout'),  # ← Bonus!
]