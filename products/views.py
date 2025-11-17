# products/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch

from django_filters.rest_framework import DjangoFilterBackend

from .models import Product, Category
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    CategoryListSerializer,
    CategoryDetailSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public menu categories – only active ones visible to customers
    Staff can see all in admin panel (we don't expose inactive via API)
    """
    queryset = Category.objects.prefetch_related(
        Prefetch('products', queryset=Product.objects.filter(is_available=True))
    )
    lookup_field = "slug"                      # /categories/drinks/ – beautiful URLs
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        """
        Staff sees all categories (for admin), customers see only active ones
        """
        qs = Category.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs.order_by('name')

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CategoryDetailSerializer
        return CategoryListSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Main menu API – the heart of your coffee shop
    """
    queryset = Product.objects.select_related("category").all()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "category__slug": ["exact"],
        "price": ["gte", "lte"],
        "is_available": ["exact"],
        "featured": ["exact"],
        "is_coffee_drink": ["exact"],
        "is_merch": ["exact"],
    }
    search_fields = ["name", "short_description"]
    ordering_fields = ["price", "name", "created_at", "prep_time_minutes"]
    ordering = ["-featured", "name"]

    def get_permissions(self):
        """
        Customers & guests: can read
        Only staff: can create/update/delete
        """
        if self.action in ["list", "retrieve", "featured", "suggestions"]:
            return [AllowAny()]  # ← guests can browse menu!
        return [IsAdminUser()]

    def get_queryset(self):
        """
        Critical business logic:
        - Customers see only available products in active categories
        - Staff sees everything (for admin panel)
        """
        qs = Product.objects.select_related("category")

        if not self.request.user.is_staff:
            qs = qs.filter(
                category__is_active=True,
                is_available=True
            )
            # For merch: even if is_available=True, hide if stock=0
            qs = qs.filter(
                Q(is_merch=False) | Q(is_merch=True, stock_count__gt=0)
            )

        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

    # BONUS: Homepage carousel
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        """GET /api/products/featured/ → 6 featured items for homepage"""
        products = self.get_queryset().filter(featured=True)[:6]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    # BONUS: Search autocomplete
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def suggestions(self, request):
        """GET /api/products/suggestions/?q=latt → ["Oat Milk Latte", "Iced Latte"]"""
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response([])

        suggestions = self.get_queryset()\
            .filter(name__icontains=q)\
            .values_list('name', flat=True)[:10]

        return Response(list(suggestions))