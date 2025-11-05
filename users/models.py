from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
#custom user model 
class UserManager(BaseUserManager):
    """BaseUserManager is  tool that allow us to make normalusers and supperusers""" 
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have email address")
        email = self.normalize_email(email)#lowercases the domain part
        user = self.model(email= email, **extra_fields)
        user.set_password(password) #hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email,password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('employee', 'employee'),
        ('admin', 'Administrator'),
        ('partner', 'Partner'),
        ('owner', 'Owner'),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELD = ['full_name'] #create superuser will  ask for fullname

    def __str__(self):
        return f"{self.full_name} ({self.role})"