# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode

from .models import Category, Post, MediaAsset, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "children_count")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_per_page = 50

    def children_count(self, obj):
        return obj.children.count()
    children_count.short_description = "Подкатегорий"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_per_page = 100

    def posts_count(self, obj):
        return obj.posts.count()
    posts_count.short_description = "Постов"


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("original_name", "file_link", "uploaded_at", "file_preview")
    readonly_fields = ("uploaded_at",)
    search_fields = ("original_name",)
    ordering = ("-uploaded_at",)
    list_per_page = 50

    def file_link(self, obj):
        if not obj.file:
            return "-"
        url = obj.file.url
        return format_html('<a href="{}" target="_blank">Open</a>', url)
    file_link.short_description = "Файл"

    def file_preview(self, obj):
        if not obj.file:
            return "-"
        url = obj.file.url
        return format_html('<img src="{}" style="max-height:80px; max-width:160px; object-fit:cover;"/>', url)
    file_preview.short_description = "Preview"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "category", "status", "is_featured", "published_at", "views", "cover_preview")
    list_filter = ("status", "is_featured", "category", "tags")
    search_fields = ("title", "slug", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("category", "tags")
    list_select_related = ("category", "cover")
    list_prefetch_related = ("tags",)
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-updated_at")
    readonly_fields = ("views", "updated_at")
    fieldsets = (
        ("Main", {"fields": ("title", "slug", "category", "cover", "tags")}),
        ("Content", {"fields": ("excerpt", "body")}),
        ("Publication", {"fields": ("status", "is_featured", "published_at")}),
        ("Meta", {"fields": ("views", "updated_at")}),
    )
    actions = ("make_published", "make_draft")
    list_per_page = 25
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "cover").prefetch_related("tags")

    def cover_preview(self, obj):
        if obj.cover and obj.cover.file:
            return format_html('<img src="{}" style="max-height:60px; max-width:120px; object-fit:cover;" />', obj.cover.file.url)
        return "-"
    cover_preview.short_description = "Cover"

    @admin.action(description="Mark selected posts as published")
    def make_published(self, request, queryset):
        updated = queryset.update(status="published")
        # set published_at for those without it
        queryset.filter(published_at__isnull=True).update(published_at=__import__("django.utils.timezone").utils.timezone.now())
        self.message_user(request, f"{updated} записей помечено как опубликованные")

    @admin.action(description="Mark selected posts as draft")
    def make_draft(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, f"{updated} записей переведено в черновики")

    # small helper to add direct link to filtered list by tag (optional improvement)
    def tag_link(self, obj):
        if not obj.tags.exists():
            return "-"
        tag = obj.tags.first()
        url = (
            reverse("admin:news_post_changelist")
            + "?"
            + urlencode({"tags__id__exact": str(tag.id)})
        )
        return format_html('<a href="{}">View posts with {}</a>', url, tag.name)
    tag_link.short_description = "Posts by tag"
