import pytest
import os
import django
import sys
from rest_framework.test import APIClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediaService.settings')
django.setup()

from django.contrib.auth.models import User
from model_bakery import baker

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Автоматически предоставляет доступ к БД для всех тестов"""
    pass

@pytest.fixture
def user():
    """Фикстура для создания пользователя"""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )

@pytest.fixture
def category():
    """Фикстура для создания категории"""
    return baker.make('news.Category', name='Test Category', slug='test-category')

@pytest.fixture
def tag():
    """Фикстура для создания тега"""
    return baker.make('news.Tag', name='Test Tag', slug='test-tag')

@pytest.fixture
def media_asset():
    """Фикстура для создания медиафайла"""
    return baker.make('news.MediaAsset', original_name='test.jpg')

@pytest.fixture
def post(category, tag, media_asset):
    """Фикстура для создания поста"""
    return baker.make('news.Post', title='Test Post', slug='test-post', category=category, status='published', tags=[tag], cover=media_asset)

@pytest.fixture
def authenticated_client(client, user):
    """Фикстура для аутентифицированного клиента"""
    client.login(username=user.username, password='testpass123')
    return client

@pytest.fixture
def api_client():
    return APIClient()