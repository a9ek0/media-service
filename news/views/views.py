import hashlib

from django.core.cache import cache
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from news.models import Category, Tag, ContentItem
from news.serializers.serializers import CategorySerializer, TagSerializer, ContentItemSerializer

__all__ = [
    "CategoryViewSet",
    "TagViewSet",
    "ContentItemViewSet",
]


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"


class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name"]
    ordering = ["name"]


class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name"]
    ordering = ["name"]


class ContentItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"
    serializer_class = ContentItemSerializer

    def get_queryset(self):
        qs = ContentItem.objects.select_related("category", "author").prefetch_related("tags")
        t = self.request.query_params.get("type") or self.request.query_params.get("content_type")
        if t:
            if t.lower() in ("video", "v"):
                qs = qs.filter(content_type=ContentItem.ContentType.VIDEO)
            elif t.lower() in ("article", "post", "a"):
                qs = qs.filter(content_type=ContentItem.ContentType.ARTICLE)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        cat = self.request.query_params.get("category")
        if cat:
            qs = qs.filter(category__slug=cat)
        return qs

    def perform_create(self, serializer):
        ct = serializer.validated_data.get("content_type")
        if not ct:
            t = self.request.query_params.get("type") or self.request.data.get("content_type")
            if t:
                if t.lower() in ("video", "v"):
                    ct = ContentItem.ContentType.VIDEO
                elif t.lower() in ("article", "post", "a"):
                    ct = ContentItem.ContentType.ARTICLE
        save_kwargs = {"author": self.request.user}
        if ct:
            save_kwargs["content_type"] = ct
        serializer.save(**save_kwargs)
        instance = serializer.instance
        if instance and instance.is_video:
            instance.fetch_metadata()

    @action(detail=True, methods=["post"], permission_classes=[])
    def hit(self, request, slug=None):
        item = self.get_object()
        user_ip = request.META.get("REMOTE_ADDR", "") or ""
        cache_key = f"content_view_{item.pk}_{hashlib.md5(user_ip.encode()).hexdigest()}"
        if not cache.get(cache_key):
            ContentItem.objects.filter(pk=item.pk).update(views=F("views") + 1)
            item.refresh_from_db(fields=["views"])
            cache.set(cache_key, True, 86400)
        return Response({"views": item.views})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def refresh_metadata(self, request, slug=None):
        item = self.get_object()
        if not item.is_video:
            return Response({"success": False, "message": _("Not a video item")}, status=400)
        changed = item.fetch_metadata()
        item.refresh_from_db(fields=["title", "lead", "title_picture"])
        if changed:
            return Response({"success": True, "message": _("Metadata updated")})
        return Response({"success": False, "message": _("No metadata applied")}, status=400)
