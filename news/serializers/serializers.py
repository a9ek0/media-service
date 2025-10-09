from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import markdown
from rest_framework import serializers

from news.models import Category, Tag, ContentItem

__all__ = ["CategorySerializer", "TagSerializer", "ContentItemSerializer"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class ContentItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True, allow_null=True, required=False
    )

    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), source="tags", write_only=True, required=False
    )

    author_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), source="author", write_only=True, required=False
    )

    body = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.SerializerMethodField(read_only=True)

    primary_video_url = serializers.SerializerMethodField(read_only=True)
    title_picture_url = serializers.SerializerMethodField(read_only=True)

    def get_body_html(self, obj):
        return markdown.markdown(obj.body or "")

    def get_primary_video_url(self, obj):
        return obj.primary_video_url

    def get_title_picture_url(self, obj):
        return obj.title_picture_url

    def validate(self, attrs):
        content_type = attrs.get("content_type", None)

        youtube = attrs.get("youtube_id", None)
        rutube = attrs.get("rutube_id", None)
        vkvideo = attrs.get("vkvideo_id", None)

        inst = getattr(self, "instance", None)
        if inst is not None and content_type is None:
            content_type = inst.content_type

        if content_type == ContentItem.ContentType.VIDEO:
            effective_youtube = youtube if youtube is not None else (inst.youtube_id if inst else None)
            effective_rutube = rutube if rutube is not None else (inst.rutube_id if inst else None)
            effective_vk = vkvideo if vkvideo is not None else (inst.vkvideo_id if inst else None)

            if not any([effective_youtube, effective_rutube, effective_vk]):
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            "Укажите хотя бы один идентификатор видео: youtube_id, rutube_id или vkvideo_id."
                        ]
                    }
                )

        return attrs

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        instance = ContentItem.objects.create(**validated_data)
        if tags:
            instance.tags.set(tags)
        if instance.is_video:
            instance.fetch_metadata()
        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if instance.is_video:
            ids_in_payload = any(k in self.initial_data for k in ("youtube_id", "rutube_id", "vkvideo_id"))
            if ids_in_payload:
                instance.fetch_metadata()
        return instance

    class Meta:
        model = ContentItem
        fields = [
            "id",
            "content_type",
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
            "title_picture_url",
            "is_featured",
            "created_at",
            "scheduled_at",
            "published_at",
            "updated_at",
            "views",
            "tags",
            "tag_ids",
            "youtube_id",
            "rutube_id",
            "vkvideo_id",
            "primary_video_url",
        ]
        read_only_fields = ["views", "created_at", "updated_at", "title_picture_url", "body_html", "primary_video_url"]
