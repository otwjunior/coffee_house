from django.db import models #he orm mapper
from django.core.validators import MinValueValidator#ensure no negtive price
from decimal import Decimal #ensure money is precise
from  django.utils.text import slugify #for SEO friendly urls
from django.db.models import UniqueConstraint #categories have unique name if we forget unique=True

""" this manages all coffee products"""
class Category(models.Model):
    name = models.CharField(max_length=50,unique=True,db_index=True)  #db_index=True → speeds up queries like Product.objects.filter(category__name="Drinks")
    description = models.TextField(blank=True, help_text="Optional detailed description")
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Uncheck to hid from menu") #Frontend can filter: Category.objects.filter(is_active=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_category_name')
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug= slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
class  Product(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug =models.SlugField(max_length=120, unique=True, blank=True)
    short_description = models.CharField(max_length=200, blank= True)
    description =  models.TextField(blank=True)

    #categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True, related_name='products', help_text='set to null if category is deleted') #null=True → allows product without category (rare, but safe)
    #pricing
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))],help_text="Price in dollars like 4.50")
    
    #stock & Availability
    is_available = models.BooleanField(default=True)
    stock_count = models.PositiveIntegerField(default=0,help_text="For beanss/merch")
    low_stock_threashold = models.PositiveIntegerField(default=5)

    # Coffee-specific
    is_coffee_drink = models.BooleanField(default=False)
    caffeine_mg = models.PositiveIntegerField(null=True, blank=True)
    # Merch-specific
    is_merch = models.BooleanField(default=False)
    weight_grams = models.PositiveIntegerField(null=True, blank=True)

    #Visual & Ops
    image = models.ImageField(upload_to='products/', blank=True, null=True) #uload menu photos
    featured = models.BooleanField(default=False) #homepage carousel
    prep_time_minutes = models.PositiveIntegerField(default=3)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True) # every save

    class Meta:
        ordering = ['-featured', 'name'] #featured first then A-Z
        indexes = [
            models.Index(fields=['category','is_available']), # fast api calls
            models.Index(fields=['slug']),
            models.Index(fields=['price']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug =base_slug
            counter = 1
            while Products.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} (${self.price})"

    @property
    def in_stock(self):
        return self.stock_count >0  if self.is_merch else self.is_available
