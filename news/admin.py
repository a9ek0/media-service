from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Category, Post, MediaAsset, Tag

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "children_count")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_per_page = 50

    @admin.display(description=_("Количество подкатегорий"))
    def children_count(self, obj):
        return obj.children.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_per_page = 100

    @admin.display(description=_("Количество постов"))
    def posts_count(self, obj):
        return obj.posts.count()


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("original_name", "file_link", "uploaded_at", "file_preview")
    readonly_fields = ("uploaded_at",)
    search_fields = ("original_name",)
    ordering = ("-uploaded_at",)
    list_per_page = 50

    @admin.display(description=_("Файл"))
    def file_link(self, obj):
        if not obj.file:
            return format_html("<span style='color:#999;'>—</span>")
        url = obj.file.url
        return format_html(
            '<a href="{}" target="_blank">Open</a>',
            url
        )

    @admin.display(description=_("Предпросмотр"))
    def file_preview(self, obj):
        if not obj.file: 
            return format_html("<span style='color:#999;'>—</span>")
        url = obj.file.url
        return format_html(
            '<img src="{}" style="max-height:80px; max-width:160px; object-fit:cover;"/>',
            url
        )


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
        (_("Main"), {"fields": ("title", "slug", "category", "cover", "tags")}),
        (_("Content"), {"fields": ("excerpt", "body_json")}),
        (_("Publication"), {"fields": ("status", "is_featured", "published_at")}),
        (_("Meta"), {"fields": ("views", "updated_at")}),
    )
    list_per_page = 25
    save_on_top = True

    actions = ("make_published", "make_draft")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "cover").prefetch_related("tags")

    @admin.display(description=_("Обложка"))
    def cover_preview(self, obj):
        if obj.cover and obj.cover.file:
            return format_html(
                '<img src="{}" style="max-height:60px; max-width:120px; object-fit:cover;" />',
                obj.cover.file.url)
        return format_html("<span style='color:#999;'>—</span>")

    @admin.action(description=_("Отметить выбранные посты как опубликованные"))
    def make_published(self, request, queryset):
        updated = queryset.update(status="published")
        queryset.filter(published_at__isnull=True).update(published_at=__import__("django.utils.timezone").utils.timezone.now())
        self.message_user(request, _("%(count)d posts marked as published.") % {"count": updated})

    @admin.action(description=_("Отметить выбранные посты как черновики"))
    def make_draft(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, _("%(count)d posts marked as draft.") % {"count": updated})
