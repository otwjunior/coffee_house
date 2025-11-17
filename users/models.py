# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.core.validators import MinLengthValidator


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'owner')  # ← owner gets full power

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('barista', 'Barista'),          # ← more accurate than "employee"
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
        ('owner', 'Owner'),
    ]

    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(2)],
        help_text="First and last name"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        db_index=True,  # ← fast filtering: User.objects.filter(role='barista')
    )

    # Django auth system
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Custom fields for coffee shop
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    favourite_drink = models.CharField(max_length=100, blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    # Convenience methods for your views/permissions
    @property
    def is_barista(self):
        return self.role == 'barista'

    @property
    def is_manager(self):
        return self.role in ['manager', 'admin', 'owner']

    @property
    def is_owner(self):
        return self.role == 'owner'

    def award_loyalty_points(self, points: int):
        self.loyalty_points += points
        self.save(update_fields=['loyalty_points'])