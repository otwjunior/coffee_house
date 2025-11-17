from .models import Order, OrderItem
from rest_framework  import serializers
from decimal import Decimal # money calculations
from django.utils import timezone #used to validate requested pick up time
from products.serializers import ProductDetailSerializer #validate product exist to get price
from products.models import Product
class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order item"""
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),#validate  the id exit in db
        write_only=True,
    )
    product_details = ProductDetailSerializer(source="product", read_only=True) # nested full product data

    # Human-readable customization
    customizations_display  = serializers.SerializerMethodField() #Dynamic output field: Calls a method to format customizations like "L, Oat, 2 shots".

    class Meta:
        model = OrderItem
        fields = [
            "id", "products", "product_details",
            "quantity", "unit_price", "customizations",
            "customizations_display", "get_subtotal", 
        ]
        read_only_fields = ["unit_price", "get_subtotal"] #read_only_fields: unit_price is set automatically, never from user input.
    
    # Custom fields
    def get_customizations_display(self, obj: OrderItem) -> str:
        """Method field: Called when serializing customizations_display.
            Uses the model methodgG62et_customization_display() to format.
        """
        return obj.get_customization_display()
    
    def get_subtotal(self, obj: OrderItem) -> Decimal:
        return obj.get_subtotal()#Computed field: Returns unit_price × quantity, rounded to 2 decimals.


    # Validation & creation

    def validate(self, data):
        """ Ensure quantity >0 and product is available. """
        
        if data["quantity"] < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        
        product = data["product"]
        if not product.is_available: # check product is in stock
            raise serializers.ValidationError(f"Product '{product.name}' is not available.")
        return data
    
    def create(self, validated_data):
        """unit_price is auto-filled from current product price."""
        product = validated_data["product"]
        item = OrderItem(
            **validated_data,
            unit_price=product.price,
        )
        item.save()
        return item
    

class OrderListRetrieveSerializer(serializers.ModelSerializer):
    """for listing and retrieving orders.
    include nested items and totals.serves GET request
    """
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(source="items.count", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "user",
            "total_amount", "status", 'status_display',
            "is_paid", "requested_pickups_time", 'notes',
            "customer_name", "created_at", "update-at",
            "items", "items_count",
        ]
        read_only_fields =[
            "order_number",
            "total_amount", "created_at", "updated-at",
            "items_count",
        ]
    
class OrderCreateSerializer(serializers.ModelSerializer):
    """ Create an order with nested items in a single POST. """
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            "user", 
            "requested_pickup_time", "customer_name",
            "notes", "items",
        ]
        extra_kwargs = {
            "user": {"required":False}, #allow guest chaeckout
        }


    # Validation
    def validate(self, data):
        if not data.get("items"):
            raise serializers.ValidationError("you submited empty order")
        if data.get("requested_pickup_time") and data["requested_pickup_it"] < timezone.now():
            raise serializers.ValidationError("Pickup time cannot be in the past.")
        return data

    #Atomic creation

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        # allow guest orders - set user later in view if authenticated
        order = Order.objects. create(**validated_data)

        # create items
        for item_data in items_data:
            OrderItemSerializer().create({**item_data, "order": order})
        
        #Recalculate total(trigger Order.save())
        order.save()# save() calls calculate_total() → updates total_amount
        return order

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """ Lightweight serilizer for barista/staff to update status & payment. serve PATCH/status endpoint """
    class Meta:
        model = Order
        fields = ["status", "is_paid"]
        extra_kwargs ={
            "status": {"required": True},
        }
    
    def validate_status(self, value):
        valid_transitions = {
            "PENDING": ["CONFIRMED", "CANCELLED"],
            "CONFIRMED": ["PREPARING", "CANCELLED"],
            "PREPARING": ["READY"],
            "READY": ["COMPLETED"],
        }
        current = self.instance.status if self.instance else None
        if currennt and value not in valid_transitions.get(current, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current} to {value}."
            )
        return value

    def validate(self, data):
        #Only allow  marking as paid if moving to CONFIRMED
        if data.get("is_paid") and self. instance and self.instance.status != "CONFIRMED":
            raise serializers.ValidationError("Can only mark as paid when status is Confirmed")
        return data
