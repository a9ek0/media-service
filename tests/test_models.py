from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from news.models import Category, ContentItem
from datetime import timedelta

User = get_user_model()


class ContentItemBusinessLogicTest(TestCase):
    """Тесты кастомной бизнес-логики ContentItem"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(name="Test Category", slug="test-category")

    def test_publish_workflow(self):
        """Тест полного workflow публикации"""
        item = ContentItem.objects.create(title="Test", category=self.category, author=self.user, slug="test")

        self.assertTrue(item.publish())
        item.refresh_from_db()
        self.assertEqual(item.status, ContentItem.Status.PUBLISHED)
        self.assertIsNotNone(item.published_at)

        self.assertFalse(item.publish())

        self.assertTrue(item.hide())
        item.refresh_from_db()
        self.assertEqual(item.status, ContentItem.Status.DRAFT)

    def test_schedule_workflow(self):
        """Тест workflow планирования"""
        item = ContentItem.objects.create(title="Test", category=self.category, author=self.user, slug="test")
        future_time = timezone.now() + timedelta(days=1)

        self.assertTrue(item.schedule(future_time))
        item.refresh_from_db()
        self.assertEqual(item.scheduled_at, future_time)
        self.assertTrue(item.is_scheduled)

        self.assertTrue(item.unschedule())
        item.refresh_from_db()
        self.assertIsNone(item.scheduled_at)

    def test_schedule_past_time_raises_error(self):
        """Тест что планирование на прошлое время вызывает ошибку"""
        item = ContentItem.objects.create(title="Test", category=self.category, author=self.user, slug="test")
        past_time = timezone.now() - timedelta(days=1)

        with self.assertRaises(ValueError):
            item.schedule(past_time)

    def test_publish_scheduled_logic(self):
        """Тест логики публикации запланированных элементов"""
        scheduled_past = ContentItem.objects.create(
            title="Scheduled Past",
            category=self.category,
            author=self.user,
            slug="scheduled-past",
            status=ContentItem.Status.DRAFT,
            scheduled_at=timezone.now() - timedelta(hours=1),
        )
        scheduled_future = ContentItem.objects.create(
            title="Scheduled Future",
            category=self.category,
            author=self.user,
            slug="scheduled-future",
            status=ContentItem.Status.DRAFT,
            scheduled_at=timezone.now() + timedelta(hours=1),
        )

        updated_count = ContentItem.publish_scheduled()

        scheduled_past.refresh_from_db()
        scheduled_future.refresh_from_db()

        self.assertEqual(updated_count, 1)
        self.assertEqual(scheduled_past.status, ContentItem.Status.PUBLISHED)
        self.assertEqual(scheduled_future.status, ContentItem.Status.DRAFT)

    def test_video_url_priority_logic(self):
        """Тест логики приоритета видео URL"""
        item = ContentItem.objects.create(
            title="Test Video",
            category=self.category,
            author=self.user,
            slug="test-video",
            content_type=ContentItem.ContentType.VIDEO,
        )

        item.youtube_id = "yt123"
        item.rutube_id = "rt456"
        self.assertEqual(item.primary_video_url, "https://www.youtube.com/watch?v=yt123")

        item.youtube_id = ""
        self.assertEqual(item.primary_video_url, "https://rutube.ru/video/rt456/")

    def test_should_publish_logic(self):
        """Тест логики определения необходимости публикации"""
        item = ContentItem.objects.create(
            title="Test", category=self.category, author=self.user, slug="test", status=ContentItem.Status.DRAFT
        )

        item.scheduled_at = timezone.now() + timedelta(hours=1)
        self.assertFalse(item.should_publish)

        item.scheduled_at = timezone.now() - timedelta(hours=1)
        self.assertTrue(item.should_publish)
