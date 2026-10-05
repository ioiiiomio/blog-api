from django.contrib.admin import ModelAdmin, TabularInline, register

from apps.blog.models import (
    Category,
    Comment,
    Post,
    Tag,
)


@register(Category)
class CategoryAdmin(ModelAdmin):
    """Category admin class configuration."""

    list_display = (
        "id",
        "name",
        "slug",
    )
    prepopulated_fields = {"slug": ("name",)}


@register(Tag)
class TagAdmin(ModelAdmin):
    """Tag admin class configuration."""

    list_display = (
        "id",
        "name",
        "slug",
    )
    prepopulated_fields = {"slug": ("name",)}


class CommentInline(TabularInline):
    """Shows post comments right on the post page."""

    model = Comment
    extra = 0


@register(Post)
class PostAdmin(ModelAdmin):
    """Post admin class configuration."""

    list_display = (
        "id",
        "title",
        "author",
        "category",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "category",
    )
    search_fields = (
        "title",
        "body",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    filter_horizontal = (
        "tags",
    )
    prepopulated_fields = {"slug": ("title",)}
    inlines = (CommentInline,)


@register(Comment)
class CommentAdmin(ModelAdmin):
    """Comment admin class configuration."""

    list_display = (
        "id",
        "post",
        "author",
        "created_at",
    )
    search_fields = (
        "body",
    )
