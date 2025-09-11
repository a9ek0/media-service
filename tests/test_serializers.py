import pytest

from news.serializers import PostSerializer, CategorySerializer, TagSerializer


class TestPostSerializer:
    def test_post_serializer(self, post):
        """Тест сериализации поста"""
        serializer = PostSerializer(instance=post)
        data = serializer.data

        assert data['title'] == post.title
        assert data['slug'] == post.slug
        assert 'category' in data
        assert 'tags' in data
        assert 'cover' in data

    def test_post_deserializer(self, category, tag):
        """Тест десериализации поста"""
        data = {
            'title': 'New Post',
            'slug': 'new-post',
            'category_id': category.id,
            'tag_ids': [tag.id],
            'status': 'draft',
            'body_json': [{"type": "paragraph", "data": {"text": "Test text"}}]
        }

        serializer = PostSerializer(data=data)
        assert serializer.is_valid()

        post = serializer.save()
        assert post.title == 'New Post'
        assert post.tags.count() == 1

class TestCategorySerializer:
    def test_category_serializer(self, category):
        """Тест сериализации категории"""
        serializer = CategorySerializer(instance=category)
        data = serializer.data

        assert data['name'] == category.name
        assert data['slug'] == category.slug


class TestTagSerializer:
    def test_tag_serializer(self, tag):
        """Тест сериализации тега"""
        serializer = TagSerializer(instance=tag)
        data = serializer.data

        assert data['name'] == tag.name
        assert data['slug'] == tag.slug