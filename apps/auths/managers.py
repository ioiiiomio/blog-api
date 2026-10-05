from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

from apps.auths.constants import (
    EMAIL_REQUIRED_ERROR,
    SUPERUSER_STAFF_ERROR,
    SUPERUSER_SUPERUSER_ERROR,
)

if TYPE_CHECKING:
    from apps.auths.models import User


class UserManager(BaseUserManager["User"]):
    """Manager for the custom User model with email as the login field."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra: Any) -> "User":
        if not email:
            raise ValueError(EMAIL_REQUIRED_ERROR)
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)  # hashes; None -> unusable password
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, password: str | None = None, **extra: Any
    ) -> "User":
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str, **extra: Any) -> "User":
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError(SUPERUSER_STAFF_ERROR)
        if extra.get("is_superuser") is not True:
            raise ValueError(SUPERUSER_SUPERUSER_ERROR)
        return self._create_user(email, password, **extra)
