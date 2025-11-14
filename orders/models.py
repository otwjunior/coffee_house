from django.db import models
from django.conf import settings
from django.utils import timezone
from products.models import Product
import uuid
from decimal import Decimal


class Order(models.Model):
    """
    Customer order – can contain drinks, beans, mugs, etc.
    """
    # ------------------------------------------------------------------ #
    # Relations
    # ------------------------------------------------------------------ #
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,                     # allow guest orders
    )

    # ------------------------------------------------------------------ #
    # Core fields
    # ------------------------------------------------------------------ #
    order_number = models.CharField(
        max_length=20, unique=True, editable=False, db_index=True
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, editable=False
    )

    # ------------------------------------------------------------------ #
    # Status & payment
    # ------------------------------------------------------------------ #
    STATUS_CHOICES = [
        ("PENDING", "Pending"),          # created, not paid
        ("CONFIRMED", "Confirmed"),      # paid & accepted
        ("PREPARING", "Preparing"),
        ("READY", "Ready for Pickup"),
        ("COMPLETED", "Picked Up"),
        ("CANCELLED", "Cancelled"),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )
    is_paid = models.BooleanField(default=False)

    # ------------------------------------------------------------------ #
    # Pickup & notes
    # ------------------------------------------------------------------ #
    requested_pickup_time = models.DateTimeField(null=True, blank=True)
    customer_name = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    # ------------------------------------------------------------------ #
    # Timestamps
    # ------------------------------------------------------------------ #
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------ #
    # Model methods
    # ------------------------------------------------------------------ #
    def generate_order_number(self) -> str:
        """
        Format: YYYYMMDD-0001
        """
        today = timezone.now().strftime("%Y%m%d")
        count = (
            Order.objects.filter(
                order_number__startswith=today,
                created_at__date=timezone.now().date(),
            ).count()
            + 1
        )
        return f"{today}-{count:04d}"

    def calculate_total(self) -> Decimal:
        """
        Sum of all OrderItem.subtotal().
        """
        from decimal import Decimal

        total = sum(item.get_subtotal() for item in self.items.all())
        return round(total, 2)

    def save(self, *args, **kwargs):
        """
        - Auto-create order_number on first save
        - Recalculate total_amount every time the Order is saved
        """
        if not self.pk:                     # new object
            self.order_number = self.generate_order_number()

        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------ #
    # Human representation
    # ------------------------------------------------------------------ #
    def __str__(self):
        username = self.user.username if self.user else "Guest"
        return f"Order {self.order_number} – {username}"

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order_number"])]
        verbose_name = "Order"
        verbose_name_plural = "Orders"


class OrderItem(models.Model):
    """
    One line-item inside an Order (e.g. "Large Oat-Milk Latte").
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, editable=False)

    # Example: {"size":"large","milk":"oat","shots":2,"syrup":"vanilla","temperature":80}
    customizations = models.JSONField(default=dict, blank=True)

    # ------------------------------------------------------------------ #
    # Auto-set price on creation
    # ------------------------------------------------------------------ #
    def save(self, *args, **kwargs):
        if not self.pk:                     # new item
            self.unit_price = self.product.price
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------ #
    # Calculations
    # ------------------------------------------------------------------ #
    def get_subtotal(self) -> Decimal:
        from decimal import Decimal

        return round(self.unit_price * self.quantity, 2)

    # ------------------------------------------------------------------ #
    # Human-readable customizations
    # ------------------------------------------------------------------ #
    def get_customization_display(self) -> str:
        if not self.customizations:
            return "Standard"

        mapping = {
            "size": {"small": "S", "medium": "M", "large": "L"},
            "milk": str.capitalize,
            "shots": lambda x: f"{x} shot" if x == 1 else f"{x} shots",
            "syrup": str.capitalize,
            "temperature": lambda x: f"{x}°C",
            "ice_level": str.capitalize,
        }

        parts = []
        for key, value in self.customizations.items():
            transformer = mapping.get(key)
            if transformer:
                if callable(transformer):
                    display = transformer(value)
                else:
                    display = transformer.get(value, value)
                parts.append(display)

        return ", ".join(parts) or "Custom"

    # ------------------------------------------------------------------ #
    # Representation
    # ------------------------------------------------------------------ #
    def __str__(self):
        return f"{self.quantity}× {self.product.name} ({self.get_customization_display()})"

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"