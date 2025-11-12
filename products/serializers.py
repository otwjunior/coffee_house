from rest_framework import serializers
from django.utils.text import slugify #auto generate SEO slugs
from .models import Product, Category

#Category serializer
class CategoryListSerializer(serializers.ModelSerializer):
    """Compact- Used in product listings $ menu."""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', "name", "slug", "description","is_active", "products_count"]
        read_only_fields = ["slug", "products_count"]

    def get_products_count(self,obj) -> int:
        return  obj.products.filters(is_available=True).count()
class CategoryDetailSerializer(CategoryListSerializer):
    """Full detail - admin or deep links."""
    products = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="products-detail",
        lookup_field="slugs",
    )
    class Meta(CategoryListSerializer.Meta):
        fields = CategoryListSerializer.Meta.fields + ["products"]

# Product serilizers
class ProductListSerializer(serializers.ModelSerializer):
    """Optimize for menu/ search result."""
    category = CategoryListSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True), #prevent assigning deleted category
        source="category", #map to product catefgory field
        write_only=True, # client send categoryid when reating or updating
        required=False,
        allow_null=True,
    )
    in_stock = serializers.BooleanField(read_only=True) #stock is available or not
    image_url =serializers.SerializerMethodField() #build the full image url needed by clients
    class Meta :
        model = Product
        fields = [
            "id", "name", 'slug', 'short_description', 'price', 'image', 'image_url', 
            'is_available', 'featured', 'category','categort_id', 'in-stock','prep_time_minutes',
        ] # only send what the menu needs
        read_only_fields = ["slug", "in_stock", "image_url"]
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url) #auto generate image url for clients
            return None # return none if no image

class ProductDetailSerializer(serializers.ModelSerializer):
    """ full product card  -detail page."""
    category = CategoryDetailSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only= True,
        required=False,
        allow_null =True,
    )
    in_stock = serializers.BooleanField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
         "slug", "created_at", 
         "updated_at", "in_stock",
         "image_url",   
        ]
    
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, "url"): #prevent crash if image was deleted but field not cleared
            request = self.context.get("request")
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
    

    #custom validation & slug generation
    def validate(self, data):
        """Business rules that belong  in the serializer."""
        # Merch must have stock > 0 to be  available
        if data.get("is_merch") and data.get("is_available") and data.get("stock_count", 0) <=0:
            raise serializers.ValidationError(
            "Merch items must  have stock_count > 0 to"
            ) # prevent available but 0 stock
        
        # Cofee drinks need caffeine_mg
        if data.get("is_coffee_drink") and data.get("caffeine_mg") is None:
            raise serializers.ValidationError(
                "Coffe drink must specify caffeine_mg."
            )
        #weight only for merch
        if not data.get("is_merch") and data.get("weight_grams") is not None:
            raise serializers.ValidationError(
                "weight_grams is only allowed for merch items."
            )
        return data

    def create(self, validated_data):
        """Auto-generate unique slug."""
        name = validated-data["name"]
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}- {counter}"
            counter += 1
        validated_data["slug"] = slug
        return super().create(validated_data)