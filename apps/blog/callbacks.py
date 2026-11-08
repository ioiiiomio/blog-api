import json
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpRequest

from apps.blog.models import Category, Comment, Post


User = get_user_model()

PROD_ENV_ID = "prod"
ENV_LOCAL = ["Local", "warning"]  # orange badge
ENV_PRODUCTION = ["Production", "danger"]  # red badge

TOP_AUTHORS_LIMIT = 5
PERCENT = 100
CHART_LABEL = "Posts"
CHART_BAR_MAX_THICKNESS = 32
NO_CATEGORY_LABEL = "No category"


def environment_callback(request: HttpRequest) -> list[str]:
    # badge in the header, based on BLOG_ENV_ID
    if settings.ENV_ID == PROD_ENV_ID:
        return ENV_PRODUCTION
    return ENV_LOCAL


def drafts_badge(request: HttpRequest) -> int | str:
    # number of drafts next to "Posts" in the sidebar, nothing if 0
    return Post.objects.filter(status=Post.Status.DRAFT).count() or ""


def is_superuser(request: HttpRequest) -> bool:
    # sidebar permission: "Users & Access" is only for superusers
    return request.user.is_superuser


def _percent(part: int, total: int) -> int:
    # share of part in total, in whole percents (0 if total is 0)
    return round(part * PERCENT / total) if total else 0


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    # add data for templates/admin/index.html to the context
    published_count = Post.objects.filter(status=Post.Status.PUBLISHED).count()
    drafts_count = Post.objects.filter(status=Post.Status.DRAFT).count()
    posts_total = published_count + drafts_count
    published_percent = _percent(published_count, posts_total)
    drafts_percent = _percent(drafts_count, posts_total)

    # bar chart: number of posts per category (one query)
    categories = Category.objects.annotate(posts_count=Count("posts")).order_by("name")
    chart_labels = [category.name for category in categories]
    chart_values = [category.posts_count for category in categories]
    uncategorized_count = Post.objects.filter(category__isnull=True).count()
    if uncategorized_count:
        chart_labels.append(NO_CATEGORY_LABEL)
        chart_values.append(uncategorized_count)

    # table: top authors by number of posts (one query)
    top_authors = (
        User.objects.annotate(posts_count=Count("posts"))
        .filter(posts_count__gt=0)
        .order_by("-posts_count", "email")[:TOP_AUTHORS_LIMIT]
    )

    context.update(
        {
            "kpi": [
                {"title": "Total users", "value": User.objects.count(), "icon": "group"},
                {"title": "Published posts", "value": published_count, "icon": "check_circle"},
                {"title": "Drafts", "value": drafts_count, "icon": "edit_note"},
                {"title": "Comments", "value": Comment.objects.count(), "icon": "chat"},
            ],
            # chart data is a JSON string in Chart.js format
            "posts_per_category_chart": json.dumps(
                {
                    "labels": chart_labels,
                    "datasets": [
                        {
                            "label": CHART_LABEL,
                            "data": chart_values,
                            "backgroundColor": "var(--color-primary-600)",
                            "maxBarThickness": CHART_BAR_MAX_THICKNESS,
                        }
                    ],
                }
            ),
            "top_authors_table": {
                "headers": ["#", "Author", "Email", "Posts"],
                "rows": [
                    [
                        position,
                        f"{author.first_name} {author.last_name}",
                        author.email,
                        author.posts_count,
                    ]
                    for position, author in enumerate(top_authors, start=1)
                ],
            },
            "status_progress": [
                {
                    "title": "Published",
                    "value": published_percent,
                    "description": f"{published_percent}% · {published_count}",
                },
                {
                    "title": "Drafts",
                    "value": drafts_percent,
                    "description": f"{drafts_percent}% · {drafts_count}",
                },
            ],
        }
    )
    return context
