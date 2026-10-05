from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.auths.constants import FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH
from apps.auths.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=FIRST_NAME_MAX_LENGTH)
    last_name = models.CharField(max_length=LAST_NAME_MAX_LENGTH)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ("first_name", "last_name")

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ("-date_joined",)

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name
