from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.enums import ActionVariant
from unfold.sections import TableSection

from django.contrib import messages
from django.contrib.admin import register
from django.db.models import Count, Prefetch, QuerySet, TextField
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import Truncator

from apps.blog.models import Category, Comment, Post, Tag


COMMENT_PREVIEW_LENGTH = 60
COMMENTS_PER_PAGE = 10
SECTION_HEIGHT = 300


class CategoryPostsSection(TableSection):
    # posts of a category, shown when a category row is expanded
    verbose_name = "Posts in this category"
    related_name = "posts"
    fields = ("title", "author", "status", "created_at")
    height = SECTION_HEIGHT


class PostCommentsSection(TableSection):
    # comments of a post, shown when a post row is expanded
    verbose_name = "Comments"
    related_name = "comments"
    fields = ("author", "short_body", "created_at")
    height = SECTION_HEIGHT

    @display(description="Comment")
    def short_body(self, comment: Comment) -> str:
        return Truncator(comment.body).chars(COMMENT_PREVIEW_LENGTH)


@register(Category)
class CategoryAdmin(ModelAdmin):
    # admin category conf
    list_display = ("name", "slug", "posts_count")
    ordering = ("name",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = (CategoryPostsSection,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return (
            super()
            .get_queryset(request)
            .annotate(_posts_count=Count("posts"))
            .prefetch_related(
                Prefetch("posts", queryset=Post.objects.select_related("author"))
            )
        )

    @display(description="Posts", ordering="_posts_count")
    def posts_count(self, obj: Category) -> int:
        return obj._posts_count


@register(Tag)
class TagAdmin(ModelAdmin):
    # tag admin conf
    list_display = ("name", "slug", "posts_count")
    ordering = ("name",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return super().get_queryset(request).annotate(_posts_count=Count("posts"))

    @display(description="Posts", ordering="_posts_count")
    def posts_count(self, obj: Tag) -> int:
        return obj._posts_count


class CommentInline(TabularInline):
    # post comments on the post page, in their own tab, 10 per page
    model = Comment
    extra = 0
    tab = True
    per_page = COMMENTS_PER_PAGE
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Comment]:
        return super().get_queryset(request).select_related("author").order_by("-created_at")


@register(Post)
class PostAdmin(ModelAdmin):
    # post admin: labels, dropdowns, filters, tabs and custom actions

    # list page
    list_display = (
        "post_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comments_count",
        "created_at",
    )
    list_select_related = ("author", "category")
    ordering = ("-created_at",)
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ("title", "body", "author__email")
    list_sections = (PostCommentsSection,)

    # actions
    actions = ("publish_selected", "move_to_drafts")  # bulk, with checkboxes
    actions_row = ("toggle_status",)  # in every row
    actions_list = ("publish_all_drafts",)  # above the list
    actions_detail = ("open_comments",)  # on the post page
    actions_submit_line = ("save_and_publish",)  # next to the Save button

    # edit page
    fieldsets = (
        ("Content", {"classes": ["tab"], "fields": ("title", "slug", "body")}),
        ("Classification", {"classes": ["tab"], "fields": ("category", "tags", "status")}),
        ("Meta", {"classes": ["tab"], "fields": ("author", "created_at", "updated_at")}),
    )
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    readonly_fields = ("created_at", "updated_at")
    formfield_overrides = {TextField: {"widget": WysiwygWidget}}
    warn_unsaved_form = True
    inlines = (CommentInline,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super()
            .get_queryset(request)
            .annotate(_comments_count=Count("comments", distinct=True))
            .prefetch_related(
                "tags",
                # comments (with authors) for the expanded rows
                Prefetch("comments", queryset=Comment.objects.select_related("author")),
            )
        )

    # columns
    @display(description="Post", header=True, ordering="title")
    def post_header(self, obj: Post) -> list[str]:
        return [obj.title, obj.author.email]

    @display(
        description="Status",
        ordering="status",
        label={Post.Status.PUBLISHED: "success", Post.Status.DRAFT: "warning"},
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict:
        # .all() uses prefetch_related("tags"), .count() would query again
        tags = obj.tags.all()
        tags_count = len(tags)
        changelist_url = reverse("admin:blog_post_changelist")
        return {
            "title": f"{tags_count} tag{pluralize(tags_count)}" if tags_count else "No tags",
            "items": [
                {
                    "title": tag.name,
                    "link": f"{changelist_url}?{urlencode({'tags__id__exact': tag.pk})}",
                }
                for tag in tags
            ],
        }

    @display(description="Comments", ordering="_comments_count")
    def comments_count(self, obj: Post) -> int:
        return obj._comments_count

    # bulk actions: get the selected posts as a queryset
    @action(description="Publish selected", icon="publish")
    def publish_selected(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(request, f"{updated} post(s) published.", messages.SUCCESS)

    @action(description="Move to drafts", icon="edit_note")
    def move_to_drafts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f"{updated} post(s) moved to drafts.", messages.WARNING)

    # row action: gets the id of the row, must return a redirect
    @action(
        description="Publish / unpublish",
        icon="swap_horiz",
        url_path="toggle-status",
        permissions=["change"],
    )
    def toggle_status(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=object_id)
        is_draft = post.status == Post.Status.DRAFT
        post.status = Post.Status.PUBLISHED if is_draft else Post.Status.DRAFT
        post.save(update_fields=["status", "updated_at"])
        self.message_user(request, f"“{post}” is now {post.get_status_display().lower()}.")
        # go back to the same page of the list (with filters)
        return redirect(request.headers.get("referer") or "admin:blog_post_changelist")

    # list action: gets only the request, must return a redirect
    @action(
        description="Publish all drafts",
        icon="done_all",
        url_path="publish-all-drafts",
        variant=ActionVariant.PRIMARY,
        permissions=["change"],
    )
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponseRedirect:
        updated = Post.objects.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED
        )
        self.message_user(request, f"{updated} draft(s) published.", messages.SUCCESS)
        return redirect("admin:blog_post_changelist")

    # detail action: gets the id of the post, must return a redirect
    @action(description="Open comments", icon="chat", url_path="open-comments")
    def open_comments(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        changelist_url = reverse("admin:blog_comment_changelist")
        return redirect(f"{changelist_url}?{urlencode({'post__id__exact': object_id})}")

    # submit line action: gets the saved post, runs after the object is saved
    @action(description="Save & publish", permissions=["change"])
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status", "updated_at"])
        self.message_user(request, f"“{obj}” saved and published.", messages.SUCCESS)


@register(Comment)
class CommentAdmin(ModelAdmin):
    # comment admin with autocomplete filters and no N+1 queries
    list_display = ("post_title", "author", "short_body", "created_at")
    # load post and author with a JOIN, not one query per row
    list_select_related = ("post", "author")
    ordering = ("-created_at",)
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    # filters are applied with a button, not on every change
    list_filter_submit = True
    search_fields = ("body", "author__email", "post__title")
    # post and author are picked with a search box in the form
    autocomplete_fields = ("post", "author")

    @display(description="Post", ordering="post__title")
    def post_title(self, obj: Comment) -> str:
        return obj.post.title

    @display(description="Comment")
    def short_body(self, obj: Comment) -> str:
        # body shortened to COMMENT_PREVIEW_LENGTH chars with "…" at the end
        return Truncator(obj.body).chars(COMMENT_PREVIEW_LENGTH)
