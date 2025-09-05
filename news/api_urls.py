from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TagViewSet, PostViewSet, MediaAssetViewSet
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'media', MediaAssetViewSet, basename='media')

urlpatterns = [
    path('', include(router.urls)),
]
