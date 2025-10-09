from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from news.models import Category, ContentItem

User = get_user_model()


class NewsFeedAPICustomLogicTest(APITestCase):
    """Тесты кастомной логики API"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.parent_category = Category.objects.create(name="Parent", slug="parent")
        self.child_category = Category.objects.create(name="Child", slug="child", parent=self.parent_category)

    def test_category_filter_includes_descendants(self):
        """Тест что фильтр категории включает потомков"""
        parent_item = ContentItem.objects.create(
            title="Parent Item",
            category=self.parent_category,
            author=self.user,
            slug="parent-item",
            status=ContentItem.Status.PUBLISHED,
        )
        child_item = ContentItem.objects.create(
            title="Child Item",
            category=self.child_category,
            author=self.user,
            slug="child-item",
            status=ContentItem.Status.PUBLISHED,
        )

        url = reverse("news-feed")
        response = self.client.get(url, {"categoryId": self.parent_category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item_titles = [item["title"] for item in response.data["data"]]
        self.assertIn("Parent Item", item_titles)
        self.assertIn("Child Item", item_titles)

    def test_exclusion_logic_works(self):
        """Тест логики исключения элементов"""
        item1 = ContentItem.objects.create(
            title="Item 1",
            category=self.parent_category,
            author=self.user,
            slug="item-1",
            status=ContentItem.Status.PUBLISHED,
        )
        item2 = ContentItem.objects.create(
            title="Item 2",
            category=self.parent_category,
            author=self.user,
            slug="item-2",
            status=ContentItem.Status.PUBLISHED,
        )

        url = reverse("news-feed")
        response = self.client.post(url, {"excluded": [item1.id]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in response.data["data"]]

        self.assertNotIn(item1.id, returned_ids)
        self.assertIn(item2.id, returned_ids)
