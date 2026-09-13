from django.contrib import admin
from django.utils import timezone

from .models import Category, Comment, Post, Profile, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "is_featured",
        "status",
        "visibility",
        "published_at",
        "updated_at",
    )
    list_filter = ("status", "visibility", "is_featured", "category", "published_at")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("category",)
    actions = ("publish_posts", "make_draft")
    fieldsets = (
        (None, {"fields": ("title", "slug", "summary", "content", "cover")}),
        ("组织", {"fields": ("category", "tags", "is_featured")}),
        ("发布", {"fields": ("status", "visibility", "published_at")}),
        ("时间记录", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.action(description="发布所选文章")
    def publish_posts(self, request, queryset):
        queryset.filter(published_at__isnull=True).update(published_at=timezone.now())
        queryset.update(status=Post.Status.PUBLISHED)

    @admin.action(description="将所选文章改为草稿")
    def make_draft(self, request, queryset):
        queryset.update(status=Post.Status.DRAFT)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "post", "status", "email", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "content", "post__title")
    list_select_related = ("post", "author")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    actions = ("approve_comments", "reject_comments")

    @admin.action(description="通过所选评论")
    def approve_comments(self, request, queryset):
        queryset.update(status=Comment.Status.APPROVED)

    @admin.action(description="拒绝所选评论")
    def reject_comments(self, request, queryset):
        queryset.update(status=Comment.Status.REJECTED)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "created_at", "updated_at")
    search_fields = ("display_name", "user__username")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
