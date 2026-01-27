# home/models.py

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import os
from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)  
    username = None
    fullname = models.CharField(max_length=100, blank=True)

    objects = CustomUserManager()

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.fullname if self.fullname else self.email

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Location(models.Model):
    USER_TYPE_CHOICES = [
        ('Employer', 'Employer'),
        ('Employee', 'Employee'),
    ]
    
    location_id = models.AutoField(primary_key=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    user_id = models.IntegerField()
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_type} - {self.address}"
    
    class Meta:
        db_table = 'location_table'