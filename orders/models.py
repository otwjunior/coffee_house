from django.db import models
from django.conf import settings # access to user model
from products.models  import Product
from  django.utils import timezone
import uuid
# Create your models here.
class Order(models.Model):
    """Customer order can contain drinks, beans, mugs, etc"""
    # link to the  customer who placed the order
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, #work with custom user model
        on_delete=models.CASCADE, #if user deleted then delete  their orders
        related_name='orders' #so user.orders.all() work nicely
    )

    # Human readable order number 
    order_number = models.CharField(max_length=20, unique=True, editable=False)

    #Total price of the entire order (drinks +beans +tip)
    total_amount =  models.DecimalField(max_digits=10, decimal_places=2, default=0)

    #Current status  - barista will change this
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), #  just created, not paid , not registed by staff
        ('CONFIRMED', 'Confirmed'), # paid and accepted
        ('PREPARING', 'Preparing'), # barista in on it 
        ('READY', 'Ready for Pickup'),
        ('COMPLETED', 'Picked Up'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    #PAID OR NOT
    is_paid = models.BooleanField(default=False)
    #when customer should pick it up
    requested_pickup_time = models.DateTimeField(null=True, blank=True)
    #optional; customers's name on the cup (for in-store orders)
    customer_name = models.CharField(max_length=50, blank=True)
    #Notes like "extra hot", "no whipped cream",
    notes = models.TextField(blank=True)
    
    #Auto timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_order_number(self):
        #Format: YYYMMDD-0001 etc
        today = timezone.now().strftime('%Y%m%d')
        #count how many orders today already
        count = Order.objects.filter(
            order_number__startwith=today,
            created_at__date=timezone.now().date()
        ).count() +1
        return f"{today}-{count:04d}" #paddingg tomake it 4 digits
    
    def calculate_total(self):
        #sum all order items
        total = sum(item.get_subtotal() for item in self.items.all())
        return round(total, 2)

    def __str__(self):
        return f"Order {self.order_number} - {self.user.username if self.user else 'Guest'}"
    
    class Meta:
        ordering = ['-created_at'] # New order first

class OrderItem(models.Model):
    """One line item in an order- eg "Large Oat Milk  Latte" or "250g of ethiopia beans"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    ) # cant delete prodct if used in old orde
    quantity  = models.PositiveIntegerField(default=1)

    # price at the time of order(so if you change price later, old order stys correct)
    unit_price =models.DecimalField(max_digits=8, decimal_places=2)

    # store ALL customizations here (size, milk, shots, syrup, temperature, etc.)
    # Example: {"size": "large", "milk": "oat", "shots": 2, "syrup": "vanilla", "temperature": 80}
    customizations = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        #Copy current product price when items is first created
        if not self.pk: #none means its new
            self.unit_price = self.products.price
        super().save(*args, **kwargs)

    
    def get_subtotal(self):
        return self.unit_price * self.quantity
    
    def get_customization_display(self):
        if not self.customizations:
            return "Stardard"

        parts =[]
        #Common customization to show 
        mapping = {
            'size':{'small': 'S', 'medium': 'M', 'large': 'L'},
            'milk': str.capitalize,
            'short': lambda x: f"{x} shot" if x==1 else f'{x} shots',
            'syrup': str.capitalize,
            'temparature': lambda x: f"{x}°C",
            'ice_level': str.capitalize,
        }

        for key, value in self.customizations.items():
            if key in mapping:
                if callable(mapping[key]):
                    display = mapping[key](value)
                else:
                    display = mapping[key].get(value, value)
                parts.append(display)
        return ",".join(parts) or "Custom"
    
    def __strr__(self):
        return f"{self.quantity}x {self.product.name} ({self.get_customization_display()})"


    