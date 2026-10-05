from django.contrib.admin import ModelAdmin, TabularInline, register

from apps.blog.models import (
    Category,
    Comment,
    Post,
    Tag,
)


@register(Category)
class CategoryAdmin(ModelAdmin):
    # admin category conf
    list_display = (
        "id",
        "name",
        "slug",
    )
    prepopulated_fields = {"slug": ("name",)}


@register(Tag)
class TagAdmin(ModelAdmin):
    # tag admin conf
    list_display = (
        "id",
        "name",
        "slug",
    )
    prepopulated_fields = {"slug": ("name",)}


class CommentInline(TabularInline):
    # to show post comments on post page
    model = Comment
    extra = 0


@register(Post)
class PostAdmin(ModelAdmin):
    # post admin class
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
    filter_horizontal = ("tags",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = (CommentInline,)


@register(Comment)
class CommentAdmin(ModelAdmin):
    # comment admin class
    list_display = (
        "id",
        "post",
        "author",
        "created_at",
    )
    search_fields = ("body",)
