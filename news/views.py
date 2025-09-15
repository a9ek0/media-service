import hashlib

from django.core.cache import cache
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action, api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .renderers import render_body_from_json
from .models import Category, Tag, Post, MediaAsset, Video
from .serializers import CategorySerializer, TagSerializer, PostSerializer, MediaAssetSerializer, VideoSerializer

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


class MediaAssetViewSet(BaseViewSet):
    lookup_field = "pk"
    queryset = MediaAsset.objects.all()
    serializer_class = MediaAssetSerializer
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["uploaded_at"]
    search_fields = ["original_name", "alt"]
    ordering_fields = ["uploaded_at"]
    ordering = ["-uploaded_at"]


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
    queryset = Post.objects.select_related("category", "cover").prefetch_related("tags")
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ["title", "slug", "excerpt", "body"]
    ordering_fields = ["published_at", "updated_at", "views", "created_at"]
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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['rendered_body'] = render_body_from_json(instance.body_json)
        return Response(data)

class  VideoFilter(django_filters.FilterSet):
    class Meta:
        model = Video
        fields = {
            "status": ["exact"],
            "category__slug": ["exact"],
            "is_featured": ["exact"],
            "tags__slug": ["exact"],
            "created_at": ["date", "date__gte", "date__lte"],
            "published_at": ["date", "date__gte", "date__lte"]
        }

class VideoViewSet(BaseViewSet):
    queryset = Video.objects.select_related("category").prefetch_related("tags")
    serializer_class = VideoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VideoFilter
    search_fields = ["title", "slug", "description"]
    ordering_fields = ["published_at", "updated_at", "views", "created_at"]
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

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
@csrf_exempt
def upload_image(request):
    file = request.FILES.get('image')

    if not file:
        return JsonResponse({'success': 0, 'error': 'No image provided'})

    if not file.content_type.startswith('image/'):
        return JsonResponse({
            'success': 0,
            'error': 'File must be an image'
        })

    media = MediaAsset.objects.create(
        file=file,
        alt='Uploaded image',
        original_name=file.name
    )

    return JsonResponse({
        'success': 1,
        'file': {
            'url': media.file.url,
            'id': media.id
        }
    })

@api_view(['GET'])
def image_list(request):
    media_assets = MediaAsset.objects.all().order_by('-uploaded_at')
    images = []

    for asset in media_assets:
        if asset.file and hasattr(asset.file, 'url'):
            images.append({
                'id': asset.id,
                'url': asset.file.url,
                'name': asset.original_name or 'Untitled',
                'alt': asset.alt,
                'uploaded_at': asset.uploaded_at.isoformat()
            })

    return JsonResponse(images, safe=False)