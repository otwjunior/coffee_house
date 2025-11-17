# products/models.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils.text import slugify
from django.db.models import Q


class Category(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="e.g. Drinks, Beans, Pastries, Merch"
    )
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide from menu without deleting"
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        # Removed redundant UniqueConstraint – unique=True already enforces it

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    short_description = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    # Relations
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # ← safer than just null=True
        related_name='products'
    )

    # Pricing
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="e.g. 5.75"
    )

    # Availability
    is_available = models.BooleanField(default=True, help_text="Manually disable if sold out")
    stock_count = models.PositiveIntegerField(default=0, help_text="Physical items only (beans, mugs)")
    low_stock_threshold = models.PositiveIntegerField(default=5)  # ← fixed typo: threashold → threshold

    # Coffee-specific
    is_coffee_drink = models.BooleanField(default=False)
    caffeine_mg = models.PositiveIntegerField(null=True, blank=True)

    # Merch-specific
    is_merch = models.BooleanField(default=False)
    weight_grams = models.PositiveIntegerField(null=True, blank=True)

    # Visual & Operations
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    featured = models.BooleanField(default=False)
    prep_time_minutes = models.PositiveIntegerField(default=3, help_text="Used for kitchen pacing")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-featured', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['slug']),
            models.Index(fields=['price']),
            models.Index(fields=['is_available']),  # extra speed for menu API
        ]

    def save(self, *args, **kwargs):
        # Generate slug only if missing
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # ← FIXED: Was "Products" (typo) → now "Product"
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (${self.price})"

    @property
    def in_stock(self) -> bool:
        """
        Business logic:
        - Drinks/Food → respect is_available flag (barista decides)
        - Merch/Beans → respect actual stock count
        """
        if self.is_merch:
            return self.stock_count > 0
        return self.is_available

    @property
    def is_low_stock(self) -> bool:
        """Used in admin + future inventory alerts"""
        return self.is_merch and self.stock_count <= self.low_stock_threshold