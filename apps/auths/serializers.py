from typing import Any

from rest_framework.serializers import (
    CharField,
    EmailField,
    ModelSerializer,
    Serializer,
    ValidationError,
)

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.auths.models import User


EMAIL_TAKEN_MESSAGE = "A user with this email already exists."
INVALID_CREDENTIALS_MESSAGE = "Invalid email or password."


class UserSerializer(ModelSerializer):
    # the user's own profile: login answer, GET and PATCH /users/me

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")
        # PATCH changes only the names, a sent email is ignored
        read_only_fields = ("id", "email")


class RegisterSerializer(ModelSerializer):
    # POST /users/register

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password")
        extra_kwargs = {
            # the password goes in, but never comes out
            "password": {"write_only": True, "trim_whitespace": False},
            # DRF's unique check runs before .lower(), we check it ourselves
            "email": {"validators": []},
        }

    def validate_email(self, value: str) -> str:
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError(EMAIL_TAKEN_MESSAGE)
        return email

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # UserAttributeSimilarityValidator needs the user's attributes
        user = User(
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as error:
            raise ValidationError({"password": list(error.messages)}) from error
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        # create_user() hashes the password, one INSERT
        return User.objects.create_user(**validated_data)


class LoginSerializer(Serializer):
    # POST /users/login, validated_data["user"] is the logged in user

    email = EmailField()
    password = CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # authenticate() checks the password and is_active,
        # one message for every case, so nobody can learn if an email exists
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].lower(),
            password=attrs["password"],
        )
        if user is None:
            raise ValidationError(INVALID_CREDENTIALS_MESSAGE)
        return {"user": user}
