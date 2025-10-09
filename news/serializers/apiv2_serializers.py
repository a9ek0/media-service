from rest_framework import serializers
from news.models import Category, ContentItem

__all__ = [
    "CategorySerializer",
    "ContentItemSerializer",
    "NewsFeedQueryParamsSerializer",
    "NewsFeedExcludedRequestSerializer",
]


class CategorySerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    subCategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "type", "subCategories"]

    def get_type(self, obj):
        if obj.type == "V":
            return "video"
        elif obj.type == "A":
            return "article"
        return obj.type

    def get_subCategories(self, obj):
        children = obj.category_set.all()
        return SubCategoryInListSerializer(children, many=True, context=self.context).data


class SubCategoryInListSerializer(serializers.ModelSerializer):
    subCategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "subCategories"]

    def get_subCategories(self, obj):
        children = obj.category_set.all()
        return SubCategoryInListSerializer(children, many=True, context=self.context).data


class ContentItemSerializer(serializers.ModelSerializer):
    datePublished = serializers.SerializerMethodField()
    titlePicture = serializers.SerializerMethodField()
    category = CategorySerializer()
    ytCode = serializers.SerializerMethodField()

    class Meta:
        model = ContentItem
        fields = ["id", "datePublished", "title", "lead", "titlePicture", "ytCode", "category"]

    def get_datePublished(self, obj):
        if obj.published_at:
            return obj.published_at.isoformat()
        return None

    def get_titlePicture(self, obj):
        if hasattr(obj, "title_picture_url") and callable(obj.title_picture_url):
            url = obj.title_picture_url()
        else:
            url = None
        return url or obj.title_picture

    def get_ytCode(self, obj):
        if obj.content_type == ContentItem.ContentType.VIDEO:
            return obj.youtube_id
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
        help_text="Список ID новостей/видео, которые нужно исключить из выдачи",
    )
