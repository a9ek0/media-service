from django.urls import path, include
from rest_framework.routers import DefaultRouter
from news.views import CategoryViewSet, TagViewSet, PostViewSet, VideoViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]
