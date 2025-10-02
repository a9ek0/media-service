from numpy.lib.utils import source
from rest_framework import serializers
from news.models import Category, Post, Video

__all__ = [
    "CategorySerializer",
    "PostSerializer",
    "VideoSerializer",
    "NewsItemSerializer",
    "NewsFeedQueryParamsSerializer",
    "NewsFeedExcludedRequestSerializer"
]


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='get_type_display')
    subCategories = SubCategorySerializer(source='children', many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'subCategories']


class BaseContentItemSerializer(serializers.ModelSerializer):
    datePublished = serializers.SerializerMethodField()
    titlePicture = serializers.URLField(source="title_picture")
    category = CategorySerializer()
    ytCode = serializers.SerializerMethodField()

    class Meta:
        fields = ['id', 'datePublished', 'title', 'lead', 'titlePicture', 'ytCode', 'category']

    def get_datePublished(self, obj):
        if obj.published_at:
            return obj.published_at.isoformat()
        return None

    def get_ytCode(self, obj):
        if isinstance(obj, Video):
            return obj.yt_code
        return None


class PostSerializer(BaseContentItemSerializer):
    class Meta(BaseContentItemSerializer.Meta):
        model = Post


class VideoSerializer(BaseContentItemSerializer):
    class Meta(BaseContentItemSerializer.Meta):
        model = Video


class NewsItemSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, Post):
            return PostSerializer(instance).data
        elif isinstance(instance, Video):
            return VideoSerializer(instance).data
        return None


class NewsFeedQueryParamsSerializer(serializers.Serializer):
    pageSize = serializers.IntegerField(default=20, min_value=1, max_value=100)
    pageNumber = serializers.IntegerField(default=1)
    categoryId = serializers.IntegerField(required=False)
    allNews = serializers.BooleanField(default=False)


class NewsFeedExcludedRequestSerializer(serializers.Serializer):
    excluded = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=[],
        help_text="Список ID новостей/видео, которые нужно исключить из выдачи"
    )
