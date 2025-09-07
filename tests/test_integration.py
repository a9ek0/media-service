import pytest
from django.urls import reverse
from rest_framework import status

from news.models import Post


@pytest.mark.django_db
class TestIntegration:
    def test_full_post_workflow(self, client, user, category):
        """Тест полного рабочего процесса создания и просмотра поста"""
        post = Post.objects.create(title='Integration Test', slug='integration', category=category, status='published')

        url = reverse('news:post_detail', args=[post.slug])
        response = client.get(url)
        assert response.status_code == 200

        api_url = f'/api/posts/{post.slug}/'
        response = client.get(api_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == post.title