from django.core.management.base import BaseCommand
from news.models import ContentItem, Category
from django.contrib.auth import get_user_model
from faker import Faker
import random
from django.utils.text import slugify
from django.utils import timezone as dj_timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Generate test data for ContentItem (Articles and Videos)"

    def add_arguments(self, parser):
        parser.add_argument("--articles", type=int, default=5000, help="Number of articles to create")
        parser.add_argument("--videos", type=int, default=5000, help="Number of videos to create")

    def handle(self, *args, **options):
        fake = Faker("ru_RU")  # Лучше использовать русскую локаль для реалистичности
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.WARNING("Нет категорий!"))
            return

        authors = list(User.objects.all())
        if not authors:
            self.stdout.write(self.style.WARNING("Нет пользователей! Создай хотя бы одного пользователя."))
            return

        num_articles = options["articles"]
        num_videos = options["videos"]

        # --- Генерация статей (ARTICLE) ---
        self.stdout.write(f"Генерация {num_articles} статей...")
        articles = []
        for i in range(num_articles):
            title = fake.sentence(nb_words=6).rstrip(".")
            slug = slugify(title) + f"-{i}"
            articles.append(
                ContentItem(
                    title=title,
                    lead=fake.text(max_nb_chars=200),
                    body=fake.text(max_nb_chars=1000),
                    content_type=ContentItem.ContentType.ARTICLE,
                    status=ContentItem.Status.PUBLISHED,
                    published_at=fake.date_time_between(start_date="-1y", end_date="now", tzinfo=dj_timezone.utc),
                    category=random.choice(categories),
                    author=random.choice(authors),
                    slug=slug,
                    is_featured=random.choices([True, False], weights=[1, 3], k=1)[0],
                )
            )
        ContentItem.objects.bulk_create(articles, batch_size=500)

        # --- Генерация видео (VIDEO) ---
        self.stdout.write(f"Генерация {num_videos} видео...")
        videos = []
        fake_yt_ids = ["98_5V4TxDa4", "dQw4w9WgXcQ", "oHg5SJYRHA0", "jNQXAC9IVRw", "M7lc1UVf-VE"]
        fake_rt_ids = ["a1b2c3d4e5f6g7h8i9j0", "k1l2m3n4o5p6q7r8s9t0", "u1v2w3x4y5z6a7b8c9d0"]

        for i in range(num_videos):
            title = fake.sentence(nb_words=6).rstrip(".")
            slug = slugify(title) + f"-{num_articles + i}"
            # Случайно выбираем платформу
            platform = random.choice(["youtube", "rutube", "vk"])
            item = ContentItem(
                title=title,
                lead=fake.text(max_nb_chars=200),
                content_type=ContentItem.ContentType.VIDEO,
                status=ContentItem.Status.PUBLISHED,
                published_at=fake.date_time_between(start_date="-1y", end_date="now", tzinfo=dj_timezone.utc),
                category=random.choice(categories),
                author=random.choice(authors),
                slug=slug,
                is_featured=random.choices([True, False], weights=[1, 4], k=1)[0],
            )
            if platform == "youtube":
                item.youtube_id = random.choice(fake_yt_ids)
            elif platform == "rutube":
                item.rutube_id = random.choice(fake_rt_ids)
            else:
                item.vkvideo_id = f"{random.randint(100000000, 999999999)}_{random.randint(100000000, 999999999)}"

            videos.append(item)

        ContentItem.objects.bulk_create(videos, batch_size=500)

        self.stdout.write(
            self.style.SUCCESS(f"Успешно сгенерировано {num_articles} статей и {num_videos} видео в ContentItem!")
        )
