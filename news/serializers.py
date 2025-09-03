from rest_framework import serializers
from .models import Category, Post, Tag, MediaAsset


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
            "published_at",
            "updated_at",
            "views",
            "tags",
            "tag_ids",
        ]
