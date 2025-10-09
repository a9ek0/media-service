from django.urls import path, include
from rest_framework.routers import DefaultRouter
from news.views import CategoryViewSet, TagViewSet, ContentItemViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"contents", ContentItemViewSet, basename="content")

urlpatterns = [
    path("", include(router.urls)),
]
