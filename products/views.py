from .models import Product, Category
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import  (
    ProductListSerializer, CategoryListSerializer,
    CategoryDetailSerializer, ProductDetailSerializer,
)

# Category views
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """No create/update/delete via API → only admin panel.
Prevents accidental changes from frontend."""
    queryset = Category.objects.filter(is_active=True) #hide inactive categories from public menu
    lookup_field = "slug" #SEO url in frontend
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"] # admin preview or mobile search bar

    def get_serializer_class(self):
        if self.action =="retrieve":
            return CategoryDetailSerializer
        return CategoryListSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "category__slug": ["exact"],
        "price": ["gte", "lte"],
        "is_available": ["exact"],
        "featured": ["exact"],
        "is_coffee_drink": ["exact"],
        "is_merch": ["exact"],
    }
    search_fields = ["name", "short_description"]
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["-featured", "name"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]    
        