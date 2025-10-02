from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import markdown
from rest_framework import serializers

from news.models import Category, Post, Tag, Video

__all__ = [
    "CategorySerializer",
    "TagSerializer",
    "PostSerializer",
    "VideoSerializer"
]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent"]

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]

class PostSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source="tags",
        write_only=True
    )
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        source='author',
        write_only=True
    )

    body = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.SerializerMethodField(read_only=True)

    def get_body_html(self, obj):
        return markdown.markdown(obj.body)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "author_id",
            "category",
            "category_id",
            "lead",
            "body",
            "body_html",
            "status",
            "title_picture",
            "is_featured",
            "created_at",
            "published_at",
            "updated_at",
            "views",
            "tags",
            "tag_ids",
        ]
        read_only_fields = [
            "views",
            "created_at",
            "updated_at",
            "slug"
        ]

class VideoSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True
    )
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source="tags",
        write_only=True
    )
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        source='author',
        write_only=True
    )

    video_url = serializers.SerializerMethodField(read_only=True)

    def get_video_url(self, obj):
        return obj.get_primary_url()

    def validate(self, data):
        urls = [
            data.get('youtube_url'),
            data.get('rutube_url'),
            data.get('vkvideo_url')
        ]

        if not any(urls):
            raise serializers.ValidationError(
                _("Укажите хотя бы одну ссылку на видео (YouTube, RuTube или VK)")
            )

        return data

    class Meta:
        model = Video
        fields = [
            "id", "youtube_url",
            "rutube_url",
            "vkvideo_url",
            "video_url",
            "title",
            "thumbnail_url",
            "author_id",
            "category",
            "category_id",
            "tags",
            "tag_ids",
            "status",
            "created_at",
            "published_at",
            "updated_at",
            "views"
        ]
        read_only_fields = [
            "thumbnail_url",
            "created_at",
            "updated_at",
            "views"
        ]