from typing import Any

from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.auths.serializers import LoginSerializer, RegisterSerializer, UserSerializer
from apps.common.mixins import ValidationMixin


ACCESS_TOKEN_HEADER = "X-Access-Token"
REFRESH_TOKEN_HEADER = "X-Refresh-Token"


class UserViewSet(ValidationMixin, ViewSet):
    # register, login and the user's own profile

    @action(
        detail=False,
        methods=["post"],
        url_path="register",
        permission_classes=[AllowAny],
        authentication_classes=[],  # an old token in the header must not block registration
    )
    def register(self, request: Request) -> Response:
        serializer = self.get_valid_serializer(RegisterSerializer, request.data)
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["post"],
        url_path="login",
        permission_classes=[AllowAny],
        authentication_classes=[],  # an old token in the header must not block login
    )
    def login(self, request: Request) -> Response:
        serializer = self.get_valid_serializer(LoginSerializer, request.data)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        headers = {
            ACCESS_TOKEN_HEADER: str(refresh.access_token),
            REFRESH_TOKEN_HEADER: str(refresh),
        }
        return Response(UserSerializer(user).data, status=HTTP_200_OK, headers=headers)

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request: Request) -> Response:
        # no permission_classes here: the default IsAuthenticated is used
        if request.method == "GET":
            return Response(UserSerializer(request.user).data, status=HTTP_200_OK)

        serializer = self.get_valid_serializer(
            UserSerializer, request.data, instance=request.user, partial=True
        )
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)


class TokenRefreshHeaderView(TokenRefreshView):
    # Simple JWT's refresh view, but the new token goes into the header, not the body

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().post(request, *args, **kwargs)  # Simple JWT does the real work
        response[ACCESS_TOKEN_HEADER] = response.data.pop("access")  # body -> header
        return response
