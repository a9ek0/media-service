from django.core.management.base import BaseCommand
from news.models import Post, Video, Category
from django.contrib.auth import get_user_model
from faker import Faker
import random
from django.utils.text import slugify

from datetime import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Generate test data for Posts and Videos"

    def add_arguments(self, parser):
        parser.add_argument("--posts", type=int, default=5000, help="Number of posts to create")
        parser.add_argument("--videos", type=int, default=5000, help="Number of videos to create")

    def handle(self, *args, **options):
        fake = Faker()
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.WARNING("Нет категорий!"))
            return

        authors = list(User.objects.all())
        if not authors:
            self.stdout.write(self.style.WARNING("Нет пользователей! Создай хотя бы одного пользователя."))
            return

        num_posts = options["posts"]
        num_videos = options["videos"]

        self.stdout.write(f"Генерация {num_posts} постов...")
        posts = []
        for i in range(num_posts):
            title = fake.sentence(nb_words=6)
            slug = slugify(title) + f"-{i}"
            posts.append(Post(
                title=title,
                lead=fake.text(max_nb_chars=200),
                body=fake.text(max_nb_chars=1000),
                status="published",
                published_at=fake.date_time_this_year(tzinfo=timezone.utc).isoformat(),
                category=random.choice(categories),
                author=random.choice(authors),
                slug=slug,
                is_featured=random.choice([True, False, False, False])
            ))
        Post.objects.bulk_create(posts, batch_size=500, ignore_conflicts=True)

        self.stdout.write(f"Генерация {num_videos} видео...")
        videos = []
        for _ in range(num_videos):
            title = fake.sentence(nb_words=6)
            videos.append(Video(
                title=title,
                lead=fake.text(max_nb_chars=200),
                status="published",
                published_at=fake.date_time_this_year(tzinfo=timezone.utc).isoformat(),
                category=random.choice(categories),
                author=random.choice(authors),
                youtube_url="https://www.youtube.com/watch?v=98_5V4TxDa4",
            ))
        Video.objects.bulk_create(videos, batch_size=500, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Успешно сгенерировано {num_posts} постов и {num_videos} видео!"
        ))
