# orders/serializers.py
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal

from .models import Order, OrderItem
from products.models import Product
from products.serializers import ProductDetailSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Used when creating orders (write) and displaying them (read)"""
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
    )
    product_details = ProductDetailSerializer(source="product", read_only=True)
    customizations_display = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_details",
            "quantity",
            "unit_price",
            "customizations",
            "customizations_display",
            "subtotal",
        ]
        read_only_fields = ["unit_price", "subtotal"]

    def get_customizations_display(self, obj):
        return obj.get_customization_display()

    def get_subtotal(self, obj):
        return obj.get_subtotal()

    def validate(self, data):
        if data["quantity"] < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")

        product = data["product"]
        if not product.in_stock:  # uses your @property from Product model
            raise serializers.ValidationError(f"'{product.name}' is out of stock or unavailable.")

        return data

    def create(self, validated_data):
        product = validated_data.pop("product")
        item = OrderItem.objects.create(
            product=product,
            unit_price=product.price,  # freeze price at time of order
            **validated_data
        )
        return item


class OrderListRetrieveSerializer(serializers.ModelSerializer):
    """Used for GET /orders/ and /orders/<number>/"""
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(source="items.count", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "total_amount",
            "status",
            "status_display",
            "is_paid",
            "requested_pickup_time",
            "notes",
            "customer_name",
            "created_at",
            "updated_at",
            "items",
            "items_count",
        ]
        read_only_fields = [
            "order_number",
            "total_amount",
            "created_at",
            "updated_at",
            "items_count",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """POST /api/orders/ — accepts nested items"""
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            "user",
            "requested_pickup_time",
            "customer_name",
            "notes",
            "items",
        ]
        extra_kwargs = {
            "user": {"required": False, "allow_null": True},
        }

    def validate(self, data):
        if not data.get("items"):
            raise serializers.ValidationError("Order must contain at least one item.")

        pickup = data.get("requested_pickup_time")
        if pickup and pickup < timezone.now():
            raise serializers.ValidationError("Pickup time cannot be in the past.")

        # Guest checkout: require name
        if not data.get("user") and not data.get("customer_name"):
            raise serializers.ValidationError("customer_name is required for guest orders.")

        return data

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)

        # Create all items
        for item_data in items_data:
            OrderItemSerializer().create({**item_data, "order": order})

        # Triggers calculate_total() + total_amount update
        order.save()
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/orders/<number>/status/ — barista only"""
    class Meta:
        model = Order
        fields = ["status", "is_paid"]

    def validate_status(self, value):
        valid_transitions = {
            "PENDING": ["CONFIRMED", "CANCELLED"],
            "CONFIRMED": ["PREPARING", "CANCELLED"],
            "PREPARING": ["READY"],
            "READY": ["COMPLETED"],
            "COMPLETED": [],
            "CANCELLED": [],
        }

        current = self.instance.status
        if value not in valid_transitions.get(current, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current} to {value}."
            )
        return value

    def validate(self, data):
        # Only allow marking as paid when confirming
        if data.get("is_paid") and self.instance.status != "CONFIRMED":
            raise serializers.ValidationError(
                "Can only mark order as paid when confirming it."
            )
        return data