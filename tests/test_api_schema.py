from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from news.models import Category, ContentItem
from datetime import timedelta

User = get_user_model()


class NewsFeedSchemaTest(APITestCase):
    """Тесты соответствия JSON-ответов спецификации для /news/feed"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(
            name="Test Category", slug="test-category", type=Category.CategoryType.ARTICLE
        )

        self.content_item = ContentItem.objects.create(
            title="Test Content",
            lead="Test lead text",
            category=self.category,
            author=self.user,
            status=ContentItem.Status.PUBLISHED,
            content_type=ContentItem.ContentType.ARTICLE,
            slug="test-content",
            published_at=timezone.now(),
            body="Test body content",
        )

    def test_news_feed_get_schema_compliance(self):
        """Тест что GET /news/feed возвращает JSON по спецификации"""
        url = reverse("news-feed")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertIn("data", data)
        self.assertIn("meta", data)

        meta = data["meta"]
        self.assertIn("totalCount", meta)
        self.assertIsInstance(meta["totalCount"], int)

        if data["data"]:
            item = data["data"][0]

            required_fields = ["id", "datePublished", "title", "lead", "titlePicture", "ytCode", "category"]
            for field in required_fields:
                self.assertIn(field, item)

            self.assertIsInstance(item["id"], int)
            self.assertIsInstance(item["title"], str)
            self.assertIsInstance(item["lead"], str)
            self.assertIsInstance(item["titlePicture"], (str, type(None)))
            self.assertIsInstance(item["ytCode"], (str, type(None)))

            self.assertRegex(item["datePublished"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

            category = item["category"]
            self.assertIn("id", category)
            self.assertIn("name", category)
            self.assertIn("type", category)
            self.assertIn("subCategories", category)

            self.assertIsInstance(category["id"], int)
            self.assertIsInstance(category["name"], str)
            self.assertIsInstance(category["type"], str)
            self.assertIsInstance(category["subCategories"], list)

            self.assertIn(category["type"], ["article", "video"])

    def test_news_feed_post_schema_compliance(self):
        """Тест что POST /news/feed возвращает JSON по спецификации"""
        url = reverse("news-feed")
        response = self.client.post(url, {"excluded": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertIn("data", data)
        self.assertIn("meta", data)

        meta = data["meta"]
        self.assertIn("totalCount", meta)
        self.assertIsInstance(meta["totalCount"], int)

        if data["data"]:
            item = data["data"][0]

            required_fields = ["id", "datePublished", "title", "lead", "titlePicture", "ytCode", "category"]
            for field in required_fields:
                self.assertIn(field, item)

    def test_news_feed_with_video_content_schema(self):
        """Тест схемы для видео контента"""
        video_item = ContentItem.objects.create(
            title="Test Video",
            lead="Video lead",
            category=self.category,
            author=self.user,
            status=ContentItem.Status.PUBLISHED,
            content_type=ContentItem.ContentType.VIDEO,
            slug="test-video",
            published_at=timezone.now(),
            youtube_id="test_youtube_id",
        )

        url = reverse("news-feed")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        video_items = [item for item in data["data"] if item["id"] == video_item.id]

        if video_items:
            video_data = video_items[0]
            self.assertEqual(video_data["ytCode"], "test_youtube_id")


class NewsCategoriesSchemaTest(APITestCase):
    """Тесты соответствия JSON-ответов спецификации для /news/categories"""

    def setUp(self):
        self.parent_category = Category.objects.create(
            name="Parent Category", slug="parent-category", type=Category.CategoryType.ARTICLE
        )
        self.child_category = Category.objects.create(
            name="Child Category", slug="child-category", parent=self.parent_category, type=Category.CategoryType.VIDEO
        )

    def test_news_categories_schema_compliance(self):
        """Тест что /news/categories возвращает JSON по спецификации"""
        url = reverse("news-categories")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)

        if data["data"]:
            category = data["data"][0]

            required_fields = ["id", "name", "type", "subCategories"]
            for field in required_fields:
                self.assertIn(field, category)

            self.assertIsInstance(category["id"], int)
            self.assertIsInstance(category["name"], str)
            self.assertIsInstance(category["type"], str)
            self.assertIsInstance(category["subCategories"], list)

            self.assertIn(category["type"], ["article", "video"])

            if category["subCategories"]:
                subcategory = category["subCategories"][0]
                self.assertIn("id", subcategory)
                self.assertIn("name", subcategory)
                self.assertIsInstance(subcategory["id"], int)
                self.assertIsInstance(subcategory["name"], str)

    def test_news_categories_nested_structure(self):
        """Тест вложенной структуры категорий"""
        parent = Category.objects.create(name="Root", slug="root", type=Category.CategoryType.ARTICLE)
        child1 = Category.objects.create(name="Child1", slug="child1", parent=parent, type=Category.CategoryType.VIDEO)
        child2 = Category.objects.create(
            name="Child2", slug="child2", parent=parent, type=Category.CategoryType.ARTICLE
        )
        grandchild = Category.objects.create(
            name="Grandchild", slug="grandchild", parent=child1, type=Category.CategoryType.VIDEO
        )

        url = reverse("news-categories")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        root_categories = [cat for cat in data["data"] if cat["name"] == "Root"]

        if root_categories:
            root = root_categories[0]
            self.assertEqual(len(root["subCategories"]), 2)

            subcategory_names = [sub["name"] for sub in root["subCategories"]]
            self.assertIn("Child1", subcategory_names)
            self.assertIn("Child2", subcategory_names)


class NewsDetailHTMLSchemaTest(APITestCase):
    """Тесты соответствия спецификации для /news/{newsItemId}"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(name="Test Category", slug="test-category")

        self.published_item = ContentItem.objects.create(
            title="Published Item",
            category=self.category,
            author=self.user,
            status=ContentItem.Status.PUBLISHED,
            content_type=ContentItem.ContentType.ARTICLE,
            slug="published-item",
            published_at=timezone.now(),
            body="# Test Header\n\nThis is **bold** text.",
        )

    def test_news_detail_html_content_type(self):
        """Тест что успешный запрос возвращает HTML с правильным Content-Type"""
        url = reverse("news-detail", args=[self.published_item.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

        content = response.content.decode()
        self.assertIn("<h1>Test Header</h1>", content)
        self.assertIn("<strong>bold</strong>", content)

    def test_news_detail_not_found_schema(self):
        """Тест что 404 ошибка возвращает JSON по спецификации"""
        url = reverse("news-detail", args=[999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response["Content-Type"], "application/json")

        error_data = response.json()
        self.assertIn("errors", error_data)
        self.assertIsInstance(error_data["errors"], list)

        if error_data["errors"]:
            error = error_data["errors"][0]
            self.assertIn("code", error)
            self.assertIn("title", error)
            self.assertIn("details", error)

            self.assertIsInstance(error["code"], str)
            self.assertIsInstance(error["title"], str)
            self.assertIsInstance(error["details"], str)

    def test_news_detail_draft_returns_404(self):
        """Тест что черновик возвращает 404"""
        draft_item = ContentItem.objects.create(
            title="Draft Item",
            category=self.category,
            author=self.user,
            status=ContentItem.Status.DRAFT,
            content_type=ContentItem.ContentType.ARTICLE,
            slug="draft-item",
            body="Draft content",
        )

        url = reverse("news-detail", args=[draft_item.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response["Content-Type"], "application/json")


class NewsFeedPaginationSchemaTest(APITestCase):
    """Тесты пагинации в соответствии со спецификацией"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(name="Test Category", slug="test-category")

        for i in range(5):
            ContentItem.objects.create(
                title=f"Item {i}",
                category=self.category,
                author=self.user,
                status=ContentItem.Status.PUBLISHED,
                slug=f"item-{i}",
                published_at=timezone.now() - timedelta(days=i),
            )

    def test_news_feed_pagination_meta(self):
        """Тест что meta.totalCount отражает общее количество"""
        url = reverse("news-feed")
        response = self.client.get(url, {"pageSize": 2, "pageNumber": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["meta"]["totalCount"], 5)
        self.assertEqual(len(data["data"]), 2)

    def test_news_feed_all_news_parameter(self):
        """Тест параметра allNews"""
        url = reverse("news-feed")
        response = self.client.get(url, {"allNews": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data["data"]), 5)


class NewsFeedCategoryFilterSchemaTest(APITestCase):
    """Тесты фильтрации по категориям в соответствии со спецификацией"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

        self.parent_category = Category.objects.create(name="Parent", slug="parent")
        self.child_category = Category.objects.create(name="Child", slug="child", parent=self.parent_category)
        self.other_category = Category.objects.create(name="Other", slug="other")

        ContentItem.objects.create(
            title="Parent Item",
            category=self.parent_category,
            author=self.user,
            status=ContentItem.Status.PUBLISHED,
            slug="parent-item",
        )
        ContentItem.objects.create(
            title="Child Item",
            category=self.child_category,
            author=self.user,
            status=ContentItem.Status.PUBLISHED,
            slug="child-item",
        )
        ContentItem.objects.create(
            title="Other Item",
            category=self.other_category,
            author=self.user,
            status=ContentItem.Status.PUBLISHED,
            slug="other-item",
        )

    def test_category_filter_includes_descendants(self):
        """Тест что фильтр по родительской категории включает потомков"""
        url = reverse("news-feed")
        response = self.client.get(url, {"categoryId": self.parent_category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        item_titles = [item["title"] for item in data["data"]]

        self.assertIn("Parent Item", item_titles)
        self.assertIn("Child Item", item_titles)
        self.assertNotIn("Other Item", item_titles)
