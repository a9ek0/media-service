from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from datetime import timezone

from .models import Category, Post, Tag, Video


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
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
class TagAdmin(ModelAdmin):
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


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ("title", "slug", "category", "author", "status", "is_featured", "published_at", "views")
    list_filter = ("status", "is_featured", "category", "tags", "author")
    search_fields = ("title", "slug", "lead", "body", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("category", "tags", "author")
    list_select_related = ("category", "author")
    list_prefetch_related = ("tags",)
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-updated_at")
    readonly_fields = ("views", "updated_at")
    list_per_page = 25
    save_on_top = True

    fieldsets = (
        (_("Основное"), {"fields": ("title", "slug", "category", "tags", "author")}),
        (_("Контент"), {"fields": ("lead", "body")}),
        (_("Публикация"), {"fields": ("status", "is_featured", "published_at")}),
        (_("Метаданные"), {"fields": ("views", "updated_at")}),
    )

    actions = ("make_published", "make_draft")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "author").prefetch_related("tags")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Отметить выбранные посты как опубликованные"))
    def make_published(self, request, queryset):
        updated = queryset.update(status="published")
        queryset.filter(published_at__isnull=True).update(published_at=timezone.now())
        self.message_user(request, _("%(count)d posts marked as published.") % {"count": updated})

    @admin.action(description=_("Отметить выбранные посты как черновики"))
    def make_draft(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, _("%(count)d posts marked as draft.") % {"count": updated})


@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = (
    "title", "lead", "author", "youtube_url", "rutube_url", "vkvideo_url", "views", "created_at", "updated_at",
    "thumbnail_preview")
    list_filter = ("status", "created_at", "updated_at", "category", "author")
    search_fields = ("title", "author__username")
    autocomplete_fields = ("category", "tags", "author")
    list_select_related = ("category", "author")
    ordering = ("-published_at", "-updated_at", "author__username")
    readonly_fields = ("views", "created_at", "updated_at")
    date_hierarchy = "published_at"
    list_per_page = 25
    save_on_top = True

    fieldsets = (
        (_("Основное"), {"fields": ("title", "lead", "category", "tags", "author")}),
        (_("Источники видео"), {"fields": ("youtube_url", "rutube_url", "vkvideo_url")}),
        (_("Публикация"), {"fields": ("status", "published_at")}),
        (_("Служебные"), {"fields": ("views", "created_at", "updated_at")}),
    )

    actions = ("make_published", "make_draft")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "author").prefetch_related("tags")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Отметить выбранные посты как опубликованные"))
    def make_published(self, request, queryset):
        updated = queryset.update(status="published")
        queryset.filter(published_at__isnull=True).update(published_at=timezone.now())
        self.message_user(request, _("%(count)d videos marked as published.") % {"count": updated})

    @admin.action(description=_("Отметить выбранные посты как черновики"))
    def make_draft(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, _("%(count)d videos marked as draft.") % {"count": updated})

    @admin.display(description=_("Превью"))
    def thumbnail_preview(self, obj):
        if obj.title_picture:
            return format_html('<img src="{}" style="height: 100px;" />', obj.title_picture)
        return "-"
