# orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet

# ────────────────────── ROUTER ────────────────────── #
router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')  # → /api/orders/

# ────────────────────── URL PATTERNS ────────────────────── #
urlpatterns = [
    # Main order endpoints
    path('', include(router.urls)),

    # These are automatically added by the router:
    # GET    /api/orders/                  → list + create
    # GET    /api/orders/{number}/         → retrieve
    # PATCH  /api/orders/{number}/status/  → update_status (custom action)
    # GET    /api/orders/active/           → active (custom action)
]

# Final URLs your café will have:
# POST   /api/orders/                     → place order
# GET    /api/orders/                     → your history
# GET    /api/orders/20251117-0001/       → receipt
# PATCH  /api/orders/20251117-0001/status/ → barista changes status
# GET    /api/orders/active/              → barista iPad dashboard