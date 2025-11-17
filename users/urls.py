# users/urls.py
from django.urls import path
from . import views

# We keep app_name only if you have Django templates that use {% url 'users:me' %}
# For pure API projects (99 % of coffee shops in 2025), you can remove it — no harm
app_name = 'users'

urlpatterns = [
    # ───── PURE API ENDPOINTS (Mobile App + Barista Tablet) ─────
    path('me/', views.MeView.as_view(), name='me'),
    path('register/', views.RegisterAPI.as_view(), name='register'),
    path('login/', views.LoginAPI.as_view(), name='login'),
    path('logout/', views.LogoutAPI.as_view(), name='logout'),
    path('profile/', views.ProfileUpdateAPI.as_view(), name='profile'),
    path('staff/<int:pk>/', views.StaffManagementAPI.as_view(), name='staff-update'),

    # ───── OPTIONAL: HTML fallback pages (only if you have Django templates) ─────
    # path('login-page/', views.login_view, name='login-page'),   # ← remove if not using
    # path('account-logout/', views.logout_view, name='web-logout'),
]