from typing import Any

from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from django.db.models import Model


class ValidationMixin:
    # "check the data or answer 400", written once for every ViewSet

    request: Request

    def get_valid_serializer(
        self,
        serializer_class: type[BaseSerializer],
        data: Any,
        instance: Model | None = None,
        partial: bool = False,
    ) -> BaseSerializer:
        serializer = serializer_class(
            instance=instance,
            data=data,
            partial=partial,
            context={"request": self.request},
        )
        serializer.is_valid(raise_exception=True)  # wrong data -> 400 automatically
        return serializer
