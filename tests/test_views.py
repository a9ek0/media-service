import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from news.models import Post, Category, MediaAsset


@pytest.mark.django_db
class TestPostViewSet:
    def test_list_posts(self, api_client):
        """Тест получения списка постов через API"""
        category = Category.objects.create(name='Test Category', slug='test-category')
        Post.objects.create(
            title='Test Post',
            slug='test-post',
            status='published',
            category=category
        )

        url = reverse('post-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_retrieve_post(self, api_client, post):
        """Тест получения конкретного поста"""
        url = reverse('post-detail', args=[post.slug])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == post.title
        assert 'rendered_body' in response.data

    def test_hit_post(self, authenticated_api_client, post):
        """Тест увеличения просмотров"""
        initial_views = post.views
        url = reverse('post-hit', args=[post.slug])
        response = authenticated_api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.views == initial_views + 1


@pytest.mark.django_db
class TestUploadImageView:
    def test_upload_image_authenticated(self, authenticated_api_client):
        """Тест загрузки изображения через API"""
        url = reverse('news:upload_image')

        with open('tests/test_image.jpg', 'rb') as img:
            response = authenticated_api_client.post(url, {'image': img})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['success'] == 1

    def test_upload_image_unauthenticated(self, api_client):
        """Тест загрузки без аутентификации"""
        url = reverse('news:upload_image')
        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMediaAssetViewSet:
    def test_list_media_assets(self, api_client):
        """Тест получения списка медиа-файлов"""
        MediaAsset.objects.create(
            original_name='test.jpg',
            alt='Test image'
        )

        url = reverse('media-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1