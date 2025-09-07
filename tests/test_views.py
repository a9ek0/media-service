import pytest
from django.urls import reverse
from unittest.mock import patch

from news.models import Post


@pytest.mark.django_db
class TestIndexView:
    @patch('news.models.MediaAsset.file')
    def test_index_view(self, mock_file, client, post):
        """Тест главной страницы"""
        mock_file.url = '/media/test-image.jpg'

        url = reverse('news:index')
        response = client.get(url)

        assert response.status_code == 200
        assert 'posts' in response.context
        assert 'featured' in response.context

    def test_index_pagination(self, client):
        """Тест пагинации на главной странице"""
        from news.models import Category

        category = Category.objects.create(name='Test Category', slug='test-category')

        for i in range(15):
            Post.objects.create(
                title=f'Post {i}',
                slug=f'post-{i}',
                status='published',
                category=category
            )

        url = reverse('news:index')
        response = client.get(url + '?page=2')

        assert response.status_code == 200
        assert response.context['posts'].number == 2

    def test_index_view_no_posts(self, client):
        """Тест нет постов на главной"""
        url = reverse('news:index')
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.context['posts']) == 0


@pytest.mark.django_db
class TestPostDetailView:
    @patch('news.models.MediaAsset.file')
    def test_post_detail_view(self, mock_file, client, post):
        """Тест страницы поста"""
        mock_file.url = '/media/test-image.jpg'

        url = reverse('news:post_detail', args=[post.slug])
        response = client.get(url)

        assert response.status_code == 200
        assert post.title.encode() in response.content
        assert 'rendered_body' in response.context

    def test_post_detail_404(self, client):
        """Тест 404 для несуществующего поста"""
        url = reverse('news:post_detail', args=['non-existent-slug'])
        response = client.get(url)

        assert response.status_code == 404

    @patch('news.models.MediaAsset.file')
    def test_post_detail_increments_views(self, mock_file, client, post):
        """Тест увеличения счетчика просмотров при посещении"""
        mock_file.url = '/media/test-image.jpg'

        initial_views = post.views
        url = reverse('news:post_detail', args=[post.slug])
        response = client.get(url)

        post.refresh_from_db()
        assert post.views == initial_views + 1

    def test_post_detail_draft_not_visible(self, client, post):
        """Тест черновик поста не видим неаутентифицированным пользователям"""
        post.status = 'draft'
        post.save()
        url = reverse('news:post_detail', args=[post.slug])
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestUploadImageView:
    def test_upload_image_authenticated(self, authenticated_client):
        """Тест загрузки изображения аутентифицированным пользователем"""
        url = reverse('news:upload_image')

        with open('tests/test_image.jpg', 'rb') as img:
            response = authenticated_client.post(url, {'image': img})

        assert response.status_code == 200
        assert response.json()['success'] == 1
        assert 'url' in response.json()['file']

    def test_upload_image_unauthenticated(self, client):
        """Тест загрузки изображения неаутентифицированным пользователем"""
        url = reverse('news:upload_image')
        response = client.post(url)

        assert response.status_code == 200
        assert response.json()['success'] == 0

    def test_upload_invalid_file(self, authenticated_client):
        """Тест загрузки невалидного файла"""
        url = reverse('news:upload_image')
        response = authenticated_client.post(url, {'image': 'invalid'})

        assert response.status_code == 200
        assert response.json()['success'] == 0

    def test_upload_large_file(self, authenticated_client):
        """Тест загрузки слишком большого файла"""
        from django.core.files.base import ContentFile
        url = reverse('news:upload_image')
        large_data = b'X' * (5 * 1024 * 1024) # 5MB
        file = ContentFile(large_data, name='large.jpg')
        response = authenticated_client.post(url, {'image': file})
        assert response.status_code == 200
        assert response.json()['success'] == 1