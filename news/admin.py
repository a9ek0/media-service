from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from django.utils import timezone

from .models import Category, Tag, ContentItem
from core.admin import BaseAdmin


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ("name", "slug", "parent", "children_count")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_per_page = 50

    @admin.display(description=_("Количество подкатегорий"))
    def children_count(self, obj):
        return obj.category_set.count()


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    list_display = ("name", "slug", "contents_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_per_page = 100

    @admin.display(description=_("Количество материалов"))
    def contents_count(self, obj):
        total = 0
        for rel in obj._meta.related_objects:
            rel_name = rel.get_accessor_name()
            if hasattr(obj, rel_name):
                total += getattr(obj, rel_name).count()
        return total


@admin.register(ContentItem)
class ContentItemAdmin(BaseAdmin):
    list_display = (
        "title",
        "slug",
        "content_type",
        "category",
        "author",
        "status",
        "is_featured",
        "published_at",
        "views",
        "thumbnail_preview",
    )
    list_filter = ("content_type", "status", "is_featured", "category", "tags", "author")
    search_fields = ("title", "slug", "lead", "body", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("category", "tags", "author")
    list_select_related = ("category", "author")
    list_prefetch_related = ("tags",)
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-updated_at")
    readonly_fields = ("views", "updated_at", "title_picture_url")
    list_per_page = 25
    save_on_top = True

    fieldsets = (
        (_("Основное"), {"fields": ("title", "slug", "content_type", "category", "tags", "author")}),
        (_("Контент"), {"fields": ("lead", "body")}),
        (_("Источники видео"), {"fields": ("youtube_id", "rutube_id", "vkvideo_id")}),
        (_("Публикация"), {"fields": ("status", "is_featured", "scheduled_at")}),
        (_("Метаданные"), {"fields": ("views", "updated_at", "title_picture_url")}),
    )

    actions = ("make_published", "make_draft")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "author").prefetch_related("tags")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Отметить выбранные элементы как опубликованные"))
    def make_published(self, request, queryset):
        updated = queryset.update(status=ContentItem.Status.PUBLISHED)
        queryset.filter(published_at__isnull=True).update(published_at=timezone.now())
        self.message_user(request, _("%(count)d items marked as published.") % {"count": updated})

    @admin.action(description=_("Отметить выбранные элементы как черновики"))
    def make_draft(self, request, queryset):
        updated = queryset.update(status=ContentItem.Status.DRAFT)
        self.message_user(request, _("%(count)d items marked as draft.") % {"count": updated})

    @admin.display(description=_("Превью"))
    def thumbnail_preview(self, obj):
        url = None
        try:
            url = obj.title_picture_url
        except Exception:
            url = None

        if url:
            return format_html('<img src="{}" style="height: 100px; object-fit: contain;" />', url)
        return "-"

    @admin.display(description=_("Видео"))
    def primary_video_link(self, obj):
        url = None
        try:
            url = obj.primary_video_url
        except Exception:
            url = None
        if url:
            return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>', url, _("Open"))
        return "-"
