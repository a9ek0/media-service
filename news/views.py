import json
import os

from django.db.models import F
from django.conf import settings
from django.core.paginator import Paginator
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, requires_csrf_token

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Category, Tag, Post, MediaAsset
from .renderers import render_body_from_json
from .serializers import CategorySerializer, TagSerializer, PostSerializer, MediaAssetSerializer

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
            "created_at": ["date", "date__gte", "date__lte"]
        }

class PostViewSet(BaseViewSet):
    queryset = Post.objects.select_related("category", "cover").prefetch_related("tags")
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ["title", "slug", "excerpt", "body"]
    ordering_fields = ["published_at", "updated_at", "views", "created_at"]
    ordering = ["-published_at"]

    @action(detail=True, methods=["post"])
    def hit(self, request, slug=None):
        post = self.get_object()
        Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
        post.refresh_from_db(fields=['views'])
        return Response({"views": post.views})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['rendered_body'] = render_body_from_json(instance.body_json)
        return Response(data)

def index(request):
    posts_qs = Post.objects.filter(status='published').order_by('-published_at')
    paginator = Paginator(posts_qs, 9)  # 9 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    featured = posts_qs.filter(is_featured=True).first()
    return render(request, 'index.html', {'posts': page_obj, 'featured': featured, 'now': timezone.now()})

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')
    Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
    rendered_body = render_body_from_json(post.body_json)
    return render(request, 'post_detail.html', {'post': post, 'rendered_body': rendered_body, 'now': timezone.now()})


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@requires_csrf_token
def upload_image(request):
    if request.method == 'POST':
        file = request.FILES.get('image')

        if file:
            if not file.content_type.startswith('image/'):
                return JsonResponse({
                    'success': 0,
                    'error': 'Файл должен быть изображением'
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

    return JsonResponse({'success': 0, 'error': 'Ошибка загрузки'})

def image_list(request):
    uploads_path = os.path.join(settings.MEDIA_ROOT, 'uploads')  
    images = []
    if os.path.exists(uploads_path):
        for root, dirs, files in os.walk(uploads_path):  
            for file in files:
                if file.endswith(('.jpg', '.png', '.gif', '.jpeg')):
                    relative_path = os.path.relpath(os.path.join(root, file), settings.MEDIA_ROOT)
                    images.append({
                        'url': f"{settings.MEDIA_URL}{relative_path}",
                        'name': file
                    })
    return JsonResponse(images, safe=False)
