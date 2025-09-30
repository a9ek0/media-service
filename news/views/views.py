import hashlib

from django.core.cache import cache
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from news.models import Category, Tag, Post, Video
from news.serializers.serializers import CategorySerializer, TagSerializer, PostSerializer, VideoSerializer

__all__ = [
    "CategoryViewSet",
    "TagViewSet",
    "PostViewSet",
    "VideoViewSet",
]


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name"]
    ordering = ["name"]

class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name"]
    ordering = ["name"]

class PostFilter(django_filters.FilterSet):
    class Meta:
        model = Post
        fields = {
            "status": ["exact"],
            "category__slug": ["exact"],
            "is_featured": ["exact"],
            "tags__slug": ["exact"],
            "created_at": ["date", "date__gte", "date__lte"],
            "published_at": ["date", "date__gte", "date__lte"]
        }

class PostViewSet(BaseViewSet):
    queryset = Post.objects.select_related("category", "author").prefetch_related("tags")
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ["title", "slug", "lead", "body", "author__username"]
    ordering_fields = ["published_at", "updated_at", "views", "created_at", "author__username"]
    ordering = ["-published_at"]

    @action(detail=True, methods=["post"], permission_classes=[])
    def hit(self, request, slug=None):
        post = self.get_object()

        user_ip = request.META.get('REMOTE_ADDR', '')
        cache_key = f"post_view_{post.pk}_{hashlib.md5(user_ip.encode()).hexdigest()}"

        if not cache.get(cache_key):
            Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
            post.refresh_from_db(fields=['views'])
            cache.set(cache_key, True, 86400)

        return Response({"views": post.views})

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

class VideoFilter(django_filters.FilterSet):
    class Meta:
        model = Video
        fields = {
            "status": ["exact"],
            "category__slug": ["exact"],
            "created_at": ["date", "date__gte", "date__lte"],
            "published_at": ["date", "date__gte", "date__lte"]
        }

class VideoViewSet(BaseViewSet):
    queryset = Video.objects.select_related("category", "author").prefetch_related("tags")
    serializer_class = VideoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VideoFilter
    search_fields = ["title", "slug", "author__username"]
    ordering_fields = ["published_at", "updated_at", "views", "created_at", "author__username"]
    ordering = ["-published_at"]

    @action(detail=True, methods=["post"], permission_classes=[])
    def hit(self, request, slug=None):
        video = self.get_object()

        user_ip = request.META.get('REMOTE_ADDR', '')
        cache_key = f"video_view_{video.pk}_{hashlib.md5(user_ip.encode()).hexdigest()}"

        if not cache.get(cache_key):
            Video.objects.filter(pk=video.pk).update(views=F('views') + 1)
            video.refresh_from_db(fields=['views'])
            cache.set(cache_key, True, 86400)

        return Response({"views": video.views})

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def refresh_metadata(self, request, slug=None):
        video = self.get_object()
        metadata = video.fetch_metadata()

        if metadata:
            video.title = metadata.get('title', video.title)
            video.description = metadata.get('description', video.description)
            video.thumbnail_url = metadata.get('thumbnail_url', video.thumbnail_url)
            video.save()

            return Response({
                "success": True,
                "message": _("Метаданные обновлены"),
                "title": video.title,
                "thumbnail_url": video.thumbnail_url
            })

        return Response({
            "success": False,
            "message": _("Не удалось получить метаданные")
        }, status=400)
