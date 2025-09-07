import pytest
from rest_framework import status
from model_bakery import baker


@pytest.mark.django_db
class TestCategoryAPI:
    def test_category_list(self, client):
        """Тест получения списка категорий"""
        baker.make('news.Category', _quantity=4)
        url = '/api/categories/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4

    def test_category_detail(self, client, category):
        """Тест получения деталей категории"""
        url = f'/api/categories/{category.slug}/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == category.name


@pytest.mark.django_db
class TestPostAPI:
    def test_post_list(self, client, post):
        """Тест получения списка постов"""
        url = '/api/posts/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

    def test_post_detail(self, client, post):
        """Тест получения деталей поста"""
        url = f'/api/posts/{post.slug}/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == post.title
        assert 'rendered_body' in response.data

    def test_post_hit_action(self, api_client, post, user):
        """Тест увеличения счетчика просмотров через API"""
        api_client.force_authenticate(user=user)
        initial_views = post.views
        url = f'/api/posts/{post.slug}/hit/'
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['views'] == initial_views + 1

    def test_post_filtering(self, client, category):
        """Тест фильтрации постов по категории"""
        post = baker.make('news.Post', category=category, status="published")

        url = f'/api/posts/?category__slug={category.slug}'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.data
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data

        assert len(results) > 0, f"No posts found. Response data: {response.data}"
        assert any(p.get('category', {}).get('slug') == category.slug for p in results if isinstance(p, dict))

    def test_post_list_empty(self, client):
        """Тест нет постов"""
        url = '/api/posts/'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_post_detail_not_found(self, client):
        """Тест 404 для несуществующего поста"""
        url = '/api/posts/non-existent/'
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_filter_no_results(self, client):
        """Тест фильтрации без совпадений"""
        url = '/api/posts/?category=non-existent'
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestMediaAssetAPI:
    def test_media_list(self, client, media_asset):
        """Тест получения списка медиафайлов"""
        url = '/api/media/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0