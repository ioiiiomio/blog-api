from rest_framework.routers import SimpleRouter

from django.urls import path

from apps.auths.views import TokenRefreshHeaderView, UserViewSet


router = SimpleRouter(trailing_slash=False)
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("token/refresh", TokenRefreshHeaderView.as_view(), name="token-refresh"),
    *router.urls,
]
