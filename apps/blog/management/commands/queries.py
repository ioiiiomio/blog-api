from datetime import date, timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.auths.models import User
from apps.blog.management.commands.seed import EMAIL_DOMAIN
from apps.blog.models import Post
from apps.blog.queries import QUERIES

CHANGING_QUERIES = frozenset(range(40, 45))
PREVIEW_ROWS = 5
INDENT = "  "

# slugs are from the seed lists (slugify of CATEGORY_NAMES / TAG_NAMES)
SAMPLE_CATEGORY_SLUG = "python"
SAMPLE_CATEGORY_SLUGS = ["python", "django", "devops"]
SAMPLE_TAG_SLUG = "docker"
SAMPLE_MERGE_SOURCE_SLUG = "java"
SAMPLE_MERGE_TARGET_SLUG = "python"
SAMPLE_TAG_NAME = "Django ORM"
SAMPLE_PAGE = 2
SAMPLE_DAYS = 30
SAMPLE_MIN_POSTS = 10
SAMPLE_OLD_DRAFT_DAYS = 30
FULL_NAME_LAST_NAME_PART = 3
TAGS_IN_PAIR = 2


# values that depend on the db, they run before counting starts
def _sample_post_slug() -> str:
    # slug of the newest published post
    slug = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .order_by("-created_at")
        .values_list("slug", flat=True)
        .first()
    )
    return slug or ""


def _sample_author_email() -> str:
    # email of someone who has published posts
    email = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .values_list("author__email", flat=True)
        .first()
    )
    return email or ""


def _sample_title_word() -> str:
    # longest word from some post title
    title = Post.objects.values_list("title", flat=True).first()
    return max(title.split(), key=len) if title else ""


def _sample_full_name_part() -> str:
    # like "mary jane" for Mary Jane
    names = User.objects.filter(is_superuser=False).values_list("first_name", "last_name").first()
    if names is None:
        return ""
    first_name, last_name = names
    return f"{first_name} {last_name[:FULL_NAME_LAST_NAME_PART]}".lower()


def _shared_tag_slugs() -> list[str]:
    # two tags of the same post, so query 21 finds at least that one
    post = (
        Post.objects.annotate(tag_count=Count("tags"))
        .filter(tag_count__gte=TAGS_IN_PAIR)
        .order_by("pk")
        .first()
    )
    if post is None:
        return [SAMPLE_TAG_SLUG] * TAGS_IN_PAIR
    return list(post.tags.order_by("slug").values_list("slug", flat=True)[:TAGS_IN_PAIR])


def _first_shared_tag() -> str:
    return _shared_tag_slugs()[0]


def _second_shared_tag() -> str:
    return _shared_tag_slugs()[1]


def _current_year() -> int:
    return timezone.localdate().year


def _current_month() -> int:
    return timezone.localdate().month


def _days_ago() -> date:
    return timezone.localdate() - timedelta(days=SAMPLE_DAYS)


def _today() -> date:
    return timezone.localdate()


# if the value is a function, it runs first (not counted)
QUERY_ARGUMENTS: dict[int, dict[str, Any]] = {
    4: {"slug": _sample_post_slug},
    7: {"page": SAMPLE_PAGE},
    8: {"word": _sample_title_word},
    9: {"domain": EMAIL_DOMAIN},
    11: {"slugs": SAMPLE_CATEGORY_SLUGS},
    12: {"year": _current_year, "month": _current_month},
    13: {"days": SAMPLE_DAYS},
    14: {"start": _days_ago, "end": _today},
    15: {"email": _sample_author_email},
    16: {"tag_slug": SAMPLE_TAG_SLUG},
    17: {"category_slug": SAMPLE_CATEGORY_SLUG},
    21: {"first_slug": _first_shared_tag, "second_slug": _second_shared_tag},
    22: {"text": _sample_title_word},
    34: {"min_posts": SAMPLE_MIN_POSTS},
    37: {"text": _sample_full_name_part},
    40: {"name": SAMPLE_TAG_NAME},
    41: {"days": SAMPLE_OLD_DRAFT_DAYS},
    42: {"category_slug": SAMPLE_CATEGORY_SLUG, "tag_slug": SAMPLE_TAG_SLUG},
    43: {"source_slug": SAMPLE_MERGE_SOURCE_SLUG, "target_slug": SAMPLE_MERGE_TARGET_SLUG},
}


class Command(BaseCommand):
    help = "Run the homework queries."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--number", type=int, help="Run one query by its number")
        parser.add_argument("--sql", action="store_true", help="Show the SQL")

    def handle(self, *args: Any, **options: Any) -> None:
        number: int | None = options["number"]
        show_sql: bool = options["sql"]

        # no number = run everything except the ones that change data
        if number is None:
            numbers = [n for n in QUERIES if n not in CHANGING_QUERIES]
        elif number in QUERIES:
            numbers = [number]
        else:
            raise CommandError(f"No query #{number}. Use 1-{max(QUERIES)}.")

        for index, query_number in enumerate(numbers):
            # empty line between queries
            if index:
                self.stdout.write("")
            self._run(query_number, show_sql)

    def _run(self, number: int, show_sql: bool) -> None:
        function = QUERIES[number]
        # functions are called here, before the counting starts
        arguments = {
            name: value() if callable(value) else value
            for name, value in QUERY_ARGUMENTS.get(number, {}).items()
        }

        with CaptureQueriesContext(connection) as context:
            result = function(**arguments)
            # querysets are lazy, so run it here or we count 0 queries
            rows = list(result) if isinstance(result, QuerySet) else None

        sql_count = len(context.captured_queries)
        word = "query" if sql_count == 1 else "queries"
        self.stdout.write(
            self.style.SUCCESS(f"#{number} {function.__name__} — {sql_count} SQL {word}")
        )
        if show_sql:
            for captured in context.captured_queries:
                self.stdout.write(self.style.SQL_KEYWORD(captured["sql"]))

        if rows is not None:
            self._write_rows(rows, list(result.query.annotations))
        elif isinstance(result, list):
            self._write_rows(result, [])
        elif isinstance(result, dict):
            self._write_rows([f"{key}: {value}" for key, value in result.items()], [])
        else:
            self.stdout.write(f"{INDENT}{self._format_row(result, [])}")

    def _write_rows(self, rows: list[Any], annotations: list[str]) -> None:

        for row in rows[:PREVIEW_ROWS]:
            self.stdout.write(f"{INDENT}{self._format_row(row, annotations)}")
        self.stdout.write(f"{INDENT}({len(rows)} {'row' if len(rows) == 1 else 'rows'})")

    def _format_row(self, row: Any, annotations: list[str]) -> str:
        if isinstance(row, Model):
            if not annotations:
                return str(row)
            values = {name: getattr(row, name) for name in annotations}
            return f"{row} {values}"
        if isinstance(row, str):
            return row
        return repr(row)
