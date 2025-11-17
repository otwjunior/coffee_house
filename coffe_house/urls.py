from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ───── Django Admin ─────
    path('admin/', admin.site.urls),

    # ───── API Routes (clean, no namespace conflicts) ─────
    path('api/products/', include('products.urls')),     # Menu + categories
    path('api/orders/', include('orders.urls')),          # Core ordering system
    path('api/auth/', include('users.urls')),             # ← Registration, login, profile

    # ───── Social / Third-party Auth ─────
    path('social-auth/', include('social_django.urls')),  # Google, Apple, etc.

    # ───── DRF browsable API login (only useful in dev) ─────
    path('api-auth/', include('rest_framework.urls')),

    # ───── Optional: Web pages (login page, profile, etc.) ─────
    # If you ever build HTML pages with Django templates
    #path('account/', include('users.urls')),  # ← different path = no conflict!

    # ───── Fallback homepage (optional) ─────
    # path('', some_home_view, name='home'),
]

# Serve media files during development (avatars, product images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)