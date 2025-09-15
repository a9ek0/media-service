from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Category, Post, Tag, MediaAsset, Video


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "description"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = ["id", "file", "alt", "uploaded_at", "original_name"]


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
    cover = MediaAssetSerializer(read_only=True)
    cover_id = serializers.PrimaryKeyRelatedField(
        queryset=MediaAsset.objects.all(),
        source="cover",
        write_only=True,
        required=False,
        allow_null=True
    )
    body_json = serializers.JSONField(required=False, allow_null=True)
    body = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "category_id",
            "excerpt",
            "body",
            "cover",
            "cover_id",
            "status",
            "is_featured",
            "created_at",
            "published_at",
            "updated_at",
            "views",
            "tags",
            "tag_ids",
            "body_json"
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

    video_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Video
        fields = [
            "id", "youtube_url",
            "rutube_url",
            "vkvideo_url",
            "video_url",
            "title",
            "slug",
            "description",
            "thumbnail_url",
            "category",
            "category_id",
            "tags",
            "tag_ids",
            "status",
            "is_featured",
            "created_at",
            "published_at",
            "updated_at",
            "views"
        ]
        read_only_fields = [
            "title", "slug",
            "description",
            "thumbnail_url",
            "created_at",
            "updated_at",
            "views"
        ]

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
