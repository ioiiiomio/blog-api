from collections.abc import Callable
from typing import Any

from django.db.models import QuerySet
from apps.blog.models import Category, Post


# level 1
def categories_by_name() -> QuerySet[Category]:
    return Category.objects.order_by("name")


def published_posts() -> QuerySet[Post]:
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")


QUERIES: dict[int, Callable[..., Any]] = {
    1: categories_by_name,
    2: published_posts,
}
