from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from django.db.models import (
    Avg,
    Case,
    Count,
    DateField,
    F,
    Max,
    Min,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, Round, TruncMonth
from django.utils import timezone

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag


# level 1
NEWEST_POSTS_LIMIT = 5
PAGE_SIZE = 10
FIRST_PAGE = 1

# level 4
EDITED_AFTER = timedelta(hours=1)

# level 5
UNCATEGORIZED = "Uncategorized"

# level 6
AVERAGE_PRECISION = 2
NO_AVERAGE = 0.0

# level 7
TOP_AUTHORS_LIMIT = 5

# level 8
FULL_NAME_SEPARATOR = " "
HOT_MIN_COMMENTS = 10
NORMAL_MIN_COMMENTS = 3
POPULARITY_HOT = "hot"
POPULARITY_NORMAL = "normal"
POPULARITY_QUIET = "quiet"


def _published() -> QuerySet[Post]:
    """Published posts, no sorting (used by other queries)."""
    return Post.objects.filter(status=Post.Status.PUBLISHED)


# level 1 - first queries
def categories_by_name() -> QuerySet[Category]:
    """All categories, A to Z."""
    return Category.objects.order_by("name")


def published_posts() -> QuerySet[Post]:
    """Published posts, newest first."""
    return _published().order_by("-created_at")


def newest_published_posts() -> QuerySet[Post]:
    """5 newest published posts."""
    return published_posts()[:NEWEST_POSTS_LIMIT]


def post_by_slug(slug: str) -> Post | None:
    """Post with this slug, or None if there's no such post."""
    return Post.objects.filter(slug=slug).first()


def active_users_count() -> int:
    """How many active users there are, without staff."""
    return User.objects.filter(is_active=True, is_staff=False).count()


def has_drafts() -> bool:
    """True if there's at least one draft."""
    return Post.objects.filter(status=Post.Status.DRAFT).exists()


def published_posts_page(page: int) -> QuerySet[Post]:
    """One page of published posts (10 per page), pages start at 1."""
    # page 0 or less would be a negative slice, django doesn't support that
    if page < FIRST_PAGE:
        return Post.objects.none()
    start = (page - FIRST_PAGE) * PAGE_SIZE
    return published_posts()[start : start + PAGE_SIZE]


# level 2 - field lookups
def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Posts with this word in the title, any letter case."""
    return Post.objects.filter(title__icontains=word)


def users_with_email_domain(domain: str) -> QuerySet[User]:
    """Users whose email ends with @domain."""
    return User.objects.filter(email__iendswith=f"@{domain}")


def posts_without_category() -> QuerySet[Post]:
    """Posts with no category."""
    return Post.objects.filter(category__isnull=True)


def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Categories whose slug is in the list."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Posts created in this month of this year."""
    return Post.objects.filter(created_at__year=year, created_at__month=month)


def posts_last_days(days: int) -> QuerySet[Post]:
    """Posts created in the last `days` days."""
    return Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=days))


def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Posts created from start to end, both days included."""
    # __date takes only the date part, so the whole end day is included
    return Post.objects.filter(created_at__date__range=(start, end))


# level 3 - across relations
def author_published_posts(email: str) -> QuerySet[Post]:
    """Published posts of the author with this email, any letter case."""
    return _published().filter(author__email__iexact=email)


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Posts that have this tag."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Comments on posts of this category."""
    return Comment.objects.filter(post__category__slug=category_slug)


def users_with_published_posts() -> QuerySet[User]:
    """Users with at least one published post, each user once."""
    # join to posts repeats a user for every post, distinct removes repeats
    return User.objects.filter(posts__status=Post.Status.PUBLISHED).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Posts with no tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments() -> QuerySet[User]:
    """Users who never wrote a comment."""
    return User.objects.filter(comments__isnull=True)


def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    """Posts that have both tags."""
    # two filter() calls = two joins, each one must find its own tag
    return Post.objects.filter(tags__slug=first_slug).filter(tags__slug=second_slug)


# level 4 - Q and F
def search_posts(text: str) -> QuerySet[Post]:
    """Posts with the text in the title or the body, any letter case."""
    return Post.objects.filter(Q(title__icontains=text) | Q(body__icontains=text))


def published_posts_missing_info() -> QuerySet[Post]:
    """Published posts with no category or no tags, each post once."""
    return _published().filter(Q(category__isnull=True) | Q(tags__isnull=True)).distinct()


def edited_posts() -> QuerySet[Post]:
    """Posts edited more than 1 hour after they were created."""
    return Post.objects.filter(updated_at__gt=F("created_at") + EDITED_AFTER)


def comments_by_post_author() -> QuerySet[Comment]:
    """Comments the post author wrote under their own post."""
    return Comment.objects.filter(author=F("post__author"))


def comments_before_post() -> QuerySet[Comment]:
    """Comments created before their post, should be empty."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))


# level 5 - values and values_list
def published_authors_emails() -> list[str]:
    """Emails of authors with published posts, unique, A to Z."""
    # sort only by the selected column, otherwise distinct gives repeats
    return list(
        _published().values_list("author__email", flat=True).distinct().order_by("author__email")
    )


def published_posts_overview() -> list[dict[str, Any]]:
    """Title, author email and category name of each published post."""
    return list(
        published_posts().values(
            "title",
            author_email=F("author__email"),
            category_name=Coalesce(F("category__name"), Value(UNCATEGORIZED)),
        )
    )


# level 6 - aggregate
def posts_stats() -> dict[str, Any]:
    """Post counts and first/last post dates, in one query."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )


def average_comments_per_post() -> float:
    """Average comments on a published post, 2 digits after the point."""
    # first count comments of each post, then average those numbers
    result = (
        _published()
        .annotate(comment_count=Count("comments"))
        .aggregate(
            average=Round(Avg("comment_count", default=NO_AVERAGE), precision=AVERAGE_PRECISION)
        )
    )
    return float(result["average"])


# level 7 - annotate
def categories_with_post_count() -> QuerySet[Category]:
    """Categories with post_count, most posts first."""
    return Category.objects.annotate(post_count=Count("posts")).order_by("-post_count", "name")


def categories_with_published_count() -> QuerySet[Category]:
    """Categories with published_count, 0 is kept too."""
    # filter goes inside Count, otherwise categories with 0 disappear
    return Category.objects.annotate(
        published_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED))
    ).order_by("-published_count", "name")


def top_authors() -> QuerySet[User]:
    """Top 5 users by published posts, with published_count."""
    return User.objects.annotate(
        published_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED))
    ).order_by("-published_count", "email")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Tags used in at least min_posts posts, with post_count."""
    # filter after annotate = HAVING
    return (
        Tag.objects.annotate(post_count=Count("posts"))
        .filter(post_count__gte=min_posts)
        .order_by("-post_count", "name")
    )


def posts_per_status() -> list[dict[str, Any]]:
    """How many posts there are for each status."""
    # values() before annotate() = group by status
    return list(Post.objects.values("status").annotate(count=Count("id")).order_by("status"))


def users_activity() -> QuerySet[User]:
    """Users with post_count and comment_count."""
    # two joins multiply each other, distinct=True counts each row once
    return User.objects.annotate(
        post_count=Count("posts", distinct=True),
        comment_count=Count("comments", distinct=True),
    ).order_by("-post_count", "-comment_count", "email")


# level 8 - db functions and conditions
def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Users whose "First Last" name contains the text, any letter case."""
    return User.objects.annotate(
        full_name=Concat("first_name", Value(FULL_NAME_SEPARATOR), "last_name")
    ).filter(full_name__icontains=text)


def published_posts_per_month() -> list[dict[str, Any]]:
    """Published posts per month, oldest month first."""
    return list(
        _published()
        .annotate(month=TruncMonth("created_at", output_field=DateField()))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Posts with comment_count and popularity: hot, normal or quiet."""
    return (
        Post.objects.annotate(comment_count=Count("comments"))
        .annotate(
            popularity=Case(
                When(comment_count__gte=HOT_MIN_COMMENTS, then=Value(POPULARITY_HOT)),
                When(comment_count__gte=NORMAL_MIN_COMMENTS, then=Value(POPULARITY_NORMAL)),
                default=Value(POPULARITY_QUIET),
            )
        )
        .order_by("-comment_count", "-created_at")
    )


QUERIES: dict[int, Callable[..., Any]] = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
}
