import random
import re
import time
from typing import Any

from faker import Faker

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.db.models import Model
from django.utils.text import slugify

from apps.blog.models import Category, Comment, Post, Tag


User = get_user_model()


DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500


SEED_PASSWORD = "SeedPass123!"
EMAIL_DOMAIN = "example.com"
INACTIVE_USERS_SHARE = 0.1
STAFF_USERS_SHARE = 0.05


CATEGORY_NAMES = [
    "Python",
    "Java",
    "C++",
    "JavaScript",
    "Django",
    "DevOps",
    "Cyber Security",
    "Career",
    "ML",
    "Databases",
]
TAG_NAMES = [
    "beginner",
    "advanced",
    "tutorial",
    "best-practice",
    "performance",
    "testing",
    "docker",
    "kubernetes",
    "postgresql",
    "rest-api",
    "fullstack",
    "ci/cd",
    "linux",
    "async",
    "orm",
    "security",
    "cloud",
    "debugging",
    "AI",
    "open-source",
    "other stuffffz",
]

POST_TITLE_MIN_WORDS = 3
POST_TITLE_MAX_WORDS = 8
POST_MIN_PARAGRAPHS = 3
POST_MAX_PARAGRAPHS = 6
PARAGRAPH_SEPARATOR = "\n\n"
PUBLISHED_SHARE = 0.7
NO_CATEGORY_SHARE = 0.1
MIN_TAGS_PER_POST = 0
MAX_TAGS_PER_POST = 5
SLUG_MAX_LEN = Post._meta.get_field("slug").max_length

COMMENT_MIN_SENTENCES = 1
COMMENT_MAX_SENTENCES = 3

DUPLICATE_SUFFIX_START = 2

SUMMARY_LABEL_WIDTH = 11
SUMMARY_COUNT_WIDTH = 4
TIME_PRECISION = 2


class Command(BaseCommand):
    # fill the db with fake users, categories, tags, posts and comments

    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users", type=int, default=DEFAULT_USERS, help="Number of users to create"
        )
        parser.add_argument(
            "--posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create"
        )
        parser.add_argument(
            "--comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create"
        )
        parser.add_argument(
            "--clear", action="store_true", help="Delete existing data before seeding"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        self._validate_counts(users=users_count, posts=posts_count, comments=comments_count)

        self.fake = Faker()
        started_at = time.perf_counter()

        # all or nothing: if CommandError is raised, nothing is saved
        with transaction.atomic():
            if clear:
                self._clear()

            created_users = self._create_users(users_count)
            created_categories = self._create_named(Category, CATEGORY_NAMES)
            created_tags = self._create_named(Tag, TAG_NAMES)
            created_posts = self._create_posts(posts_count)
            created_comments = self._create_comments(comments_count)

        elapsed = time.perf_counter() - started_at

        if clear:
            self.stdout.write(self.style.WARNING("Existing data deleted."))
        self._write_line("Users:", created_users)
        self._write_line("Categories:", created_categories)
        self._write_line("Tags:", created_tags)
        self._write_line("Posts:", created_posts)
        self._write_line("Comments:", created_comments)
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed:.{TIME_PRECISION}f} seconds"))

    def _validate_counts(self, **counts: int) -> None:
        # raise CommandError if any count is negative
        for name, value in counts.items():
            if value < 0:
                raise CommandError(f"--{name} must be 0 or greater, got {value}.")

    def _clear(self) -> None:
        # del all seed data, superusers are kept
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def _create_users(self, count: int) -> int:
        # create users with uniq emails and 1 shared hash pwd
        if count == 0:
            return 0

        # hashing is slow on purpose, so do it only once
        hashed_password = make_password(SEED_PASSWORD)
        # emails already in the db, so we don't repeat them
        used_emails = set(User.objects.values_list("email", flat=True))
        users = []

        for _ in range(count):
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            users.append(
                User(
                    email=self._unique_email(first_name, last_name, used_emails),
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    is_active=random.random() >= INACTIVE_USERS_SHARE,
                    is_staff=random.random() < STAFF_USERS_SHARE,
                )
            )

        # one INSERT for all users instead of .save() in a loop
        return len(User.objects.bulk_create(users))

    def _unique_email(self, first_name: str, last_name: str, used: set[str]) -> str:
        # build first.last@domain, add a number if the mail is taken
        local_part = ".".join(
            re.sub(r"[^a-z]", "", name.lower()) for name in (first_name, last_name)
        )
        email = f"{local_part}@{EMAIL_DOMAIN}"
        suffix = DUPLICATE_SUFFIX_START

        while email in used:
            email = f"{local_part}{suffix}@{EMAIL_DOMAIN}"
            suffix += 1

        used.add(email)
        return email

    def _create_named(self, model: type[Model], names: list[str]) -> int:
        # create categories/tags from the names list, skip existing ones
        existing_slugs = set(model.objects.values_list("slug", flat=True))
        new_objects = [
            model(name=name, slug=slugify(name))
            for name in names
            if slugify(name) not in existing_slugs
        ]
        return len(model.objects.bulk_create(new_objects))

    def _author_ids(self) -> list[int]:
        # users that can be authors, superusers are skipped so admin gets no fake data
        return list(User.objects.filter(is_superuser=False).values_list("id", flat=True))

    def _create_posts(self, count: int) -> int:
        # create posts with uniq slugs, random status, category and tags
        if count == 0:
            return 0

        author_ids = self._author_ids()
        if not author_ids:
            raise CommandError("Cannot create posts: there are no users. Use --users.")

        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        used_slugs = set(Post.objects.values_list("slug", flat=True))
        posts = []

        for _ in range(count):
            title = self.fake.sentence(
                nb_words=random.randint(POST_TITLE_MIN_WORDS, POST_TITLE_MAX_WORDS)
            ).rstrip(".")
            paragraphs = self.fake.paragraphs(
                nb=random.randint(POST_MIN_PARAGRAPHS, POST_MAX_PARAGRAPHS)
            )
            is_published = random.random() < PUBLISHED_SHARE
            has_category = categories and random.random() >= NO_CATEGORY_SHARE

            posts.append(
                Post(
                    author_id=random.choice(author_ids),
                    title=title,
                    # bulk_create does not call save(), so we set the slug here
                    slug=self._unique_slug(title, used_slugs),
                    body=PARAGRAPH_SEPARATOR.join(paragraphs),
                    category=random.choice(categories) if has_category else None,
                    status=Post.Status.PUBLISHED if is_published else Post.Status.DRAFT,
                )
            )

        created_posts = Post.objects.bulk_create(posts)

        # after bulk_create posts have ids, so tags can be attached
        max_tags = min(MAX_TAGS_PER_POST, len(tags))
        for post in created_posts:
            post.tags.set(random.sample(tags, random.randint(MIN_TAGS_PER_POST, max_tags)))

        return len(created_posts)

    def _unique_slug(self, title: str, used: set[str]) -> str:
        # slugify the title, add -2, -3, ... if the slug is taken
        base = slugify(title)[:SLUG_MAX_LEN].strip("-")
        slug = base
        suffix = DUPLICATE_SUFFIX_START

        while slug in used:
            ending = f"-{suffix}"
            slug = base[: SLUG_MAX_LEN - len(ending)].strip("-") + ending
            suffix += 1

        used.add(slug)
        return slug

    def _create_comments(self, count: int) -> int:
        # create comments only on published posts
        if count == 0:
            return 0

        author_ids = self._author_ids()
        if not author_ids:
            raise CommandError("Cannot create comments: there are no users. Use --users.")

        post_ids = list(
            Post.objects.filter(status=Post.Status.PUBLISHED).values_list("id", flat=True)
        )
        if not post_ids:
            raise CommandError(
                "Cannot create comments: there are no published posts. Use --posts."
            )

        comments = [
            Comment(
                post_id=random.choice(post_ids),
                author_id=random.choice(author_ids),
                body=" ".join(
                    self.fake.sentences(
                        nb=random.randint(COMMENT_MIN_SENTENCES, COMMENT_MAX_SENTENCES)
                    )
                ),
            )
            for _ in range(count)
        ]
        return len(Comment.objects.bulk_create(comments))

    def _write_line(self, label: str, count: int) -> None:
        # print one summary line, e.g. "Users:       50 created"
        self.stdout.write(
            f"{label:<{SUMMARY_LABEL_WIDTH}}{count:>{SUMMARY_COUNT_WIDTH}} created"
        )
