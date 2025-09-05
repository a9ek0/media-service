from django.db.models import F
from django.core.paginator import Paginator
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response


from .models import Category, Tag, Post, MediaAsset
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
    return render(request, 'post_detail.html', {'post': post, 'now': timezone.now()})
