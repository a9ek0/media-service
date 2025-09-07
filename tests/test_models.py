import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone

from news.models import Category, Tag, Post, MediaAsset


@pytest.mark.django_db
class TestCategoryModel:
    def test_category_creation(self, category):
        """Тест создания категории"""
        assert category.name == 'Test Category'
        assert category.slug == 'test-category'
        assert str(category) == 'Test Category'

    def test_category_with_parent(self, category):
        """Тест категории с родительской категорией"""
        child_category = Category.objects.create(
            name='Child Category',
            slug='child-category',
            parent=category
        )
        assert child_category.parent == category
        assert child_category in category.children.all()

    def test_category_name_empty(self):
        """Тест пустое имя категории"""
        with pytest.raises(ValidationError):
            category = Category(name='', slug='empty')
            category.full_clean()

    def test_category_slug_duplicate(self):
        """Тест дублированный slug"""
        Category.objects.create(name='Test1', slug='duplicate')
        with pytest.raises(IntegrityError):
            Category.objects.create(name='Test2', slug='duplicate')


@pytest.mark.django_db
class TestTagModel:
    def test_tag_creation(self, tag):
        """Тест создания тега"""
        assert tag.name == 'Test Tag'
        assert tag.slug == 'test-tag'
        assert str(tag) == 'Test Tag'


@pytest.mark.django_db
class TestMediaAssetModel:
    def test_media_asset_creation(self, media_asset):
        """Тест создания медиафайла"""
        assert media_asset.original_name == 'test.jpg'
        assert media_asset.uploaded_at is not None

    def test_media_asset_no_file(self):
        """Тест MediaAsset без файла"""
        asset = MediaAsset(original_name='test.jpg')
        with pytest.raises(ValueError):
            asset.file.url


@pytest.mark.django_db
class TestPostModel:
    def test_post_creation(self, post):
        """Тест создания поста"""
        assert post.title == 'Test Post'
        assert post.slug == 'test-post'
        assert post.status == 'published'
        assert post.category.name == 'Test Category'
        assert post.tags.count() == 1
        assert str(post) == 'Test Post'

    def test_post_save_published_at(self, category):
        """Тест автоматической установки published_at при публикации"""
        post = Post(title='Test', slug='test', status='draft', category=category)
        post.save()
        assert post.published_at is None

        post.status = 'published'
        post.save()
        assert post.published_at is not None
        assert post.published_at <= timezone.now()

    def test_post_views_increment(self, post):
        """Тест увеличения счетчика просмотров"""
        initial_views = post.views
        post.views += 1
        post.save()
        assert post.views == initial_views + 1

    def test_post_title_max_length(self, category):
        """Тест заголовок превышает максимальную длину"""
        long_title = 'A' * 201  # Assuming max_length=200
        with pytest.raises(ValidationError):
            post = Post(title=long_title, slug='long', category=category)
            post.full_clean()

    def test_post_without_category(self):
        """Тест пост без категории"""
        with pytest.raises(IntegrityError):
            Post.objects.create(title='No Category', slug='no-cat')