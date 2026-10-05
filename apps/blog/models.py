from django.conf import settings
from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    Model,
    SlugField,
    TextChoices,
    TextField,
)


# database tables classes
class Category(Model):
    # categories table
    NAME_MAX_LEN = 100

    name = CharField(
        max_length=NAME_MAX_LEN,
        unique=True,
    )
    slug = SlugField(
        unique=True,
    )

    class Meta:
        # meta data for admin
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Tag(Model):
    # tags table
    NAME_MAX_LEN = 50

    name = CharField(
        max_length=NAME_MAX_LEN,
        unique=True,
    )
    slug = SlugField(
        unique=True,
    )

    def __str__(self) -> str:
        return self.name


class Post(Model):
    # posts table
    TITLE_MAX_LEN = 200
    STATUS_MAX_LEN = 10

    class Status(TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="posts",
    )
    title = CharField(
        max_length=TITLE_MAX_LEN,
    )
    slug = SlugField(
        unique=True,
    )
    body = TextField()
    category = ForeignKey(
        to=Category,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    tags = ManyToManyField(
        to=Tag,
        blank=True,
        related_name="posts",
    )
    status = CharField(
        max_length=STATUS_MAX_LEN,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = DateTimeField(
        auto_now_add=True,
    )
    updated_at = DateTimeField(
        auto_now=True,
    )

    def __str__(self) -> str:
        return self.title


class Comment(Model):
    # comments table
    post = ForeignKey(
        to=Post,
        on_delete=CASCADE,
        related_name="comments",
    )
    author = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="comments",
    )
    body = TextField()
    created_at = DateTimeField(
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return f"Comment #{self.pk} on {self.post}"
