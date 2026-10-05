from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db.models import (
    BooleanField,
    CharField,
    EmailField,
)


class UserManager(BaseUserManager):
    """Custom manager for User, uses email instead of username."""

    EMAIL_REQUIRED_MESSAGE = "Email field is required."

    def __obtain_user_instance(
        self,
        email: str,
        password: str | None,
        **kwargs: Any,
    ) -> "User":
        """Validate email and build (not save) a user instance."""
        if not email:
            raise ValidationError(
                message=self.EMAIL_REQUIRED_MESSAGE, code="email_empty"
            )

        new_user: "User" = self.model(
            email=self.normalize_email(email).lower(),
            **kwargs,
        )
        new_user.set_password(password)
        return new_user

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **kwargs: Any,
    ) -> "User":
        """Create a regular user."""
        new_user: "User" = self.__obtain_user_instance(
            email=email,
            password=password,
            **kwargs,
        )
        new_user.save(using=self._db)
        return new_user

    def create_superuser(
        self,
        email: str,
        password: str,
        **kwargs: Any,
    ) -> "User":
        """Create superuser. Used by manage.py createsuperuser."""
        new_user: "User" = self.__obtain_user_instance(
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
            **kwargs,
        )
        new_user.save(using=self._db)
        return new_user


class User(AbstractBaseUser, PermissionsMixin):
    """Users database table. Login is done by email."""

    FIRST_NAME_MAX_LEN = 50
    LAST_NAME_MAX_LEN = 50

    email = EmailField(
        unique=True,
    )
    first_name = CharField(
        max_length=FIRST_NAME_MAX_LEN,
    )
    last_name = CharField(
        max_length=LAST_NAME_MAX_LEN,
    )
    # True if the user can log in
    is_active = BooleanField(
        default=True,
    )
    # True if the user can open the admin panel
    is_staff = BooleanField(
        default=False,
    )

    REQUIRED_FIELDS = ["first_name", "last_name"]
    USERNAME_FIELD = "email"
    objects = UserManager()

    def __str__(self) -> str:
        return self.email
