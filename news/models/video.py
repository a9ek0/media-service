import re
import requests

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from . import Category, Tag

class Video(models.Model):
    STATUS_CHOICES = [
        ("draft", _("Черновик")),
        ("published", _("Опубликовано")),
    ]

    youtube_url = models.URLField(
        blank=True,
        verbose_name=_("YouTube ссылка"),
        help_text = _("Ссылка на видео YouTube")
    )
    rutube_url = models.URLField(
        blank=True,
        verbose_name=_("Rutube ссылка"),
        help_text=_("Ссылка на видео RuTube")
    )
    vkvideo_url = models.URLField(
        blank=True,
        verbose_name=_("VK Видео ссылка"),
        help_text=_("Ссылка на видео VK Видео ")
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Заголовок"),
        help_text=_("Автозаполняется. Краткий заголовок статьи, до 200 символов"))
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Автозаполняется. Необязательно. Пояснение к категории.")
    )
    thumbnail_url = models.URLField(
        blank=True,
        verbose_name=_("Автозаполняется. Ссылка на обложку")
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="videos",
        verbose_name=_("Категория")
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="videos",
        verbose_name=_("Теги")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name=_("Статус")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Закрепить на главной"),
        help_text=_("Видео будет постоянно отображаться в верхней части главной страницы")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания")
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Дата публикации")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Обновлено")
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Просмотры")
    )

    class Meta:
        verbose_name=_("Видео")
        verbose_name_plural=_("Видео")
        ordering = ["-published_at", "-updated_at"]
        indexes = [
            models.Index(fields=['published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['-published_at', 'status']),
        ]

    @staticmethod
    def extract_video_id(url, platform):
        patterns = {
            'youtube': [
                r'(?:v=|\/)([0-9A-Za-z_-]{11})',
                r'(?:embed\/|v\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
            ],
            'rutube': [
                r'rutube\.ru\/video\/([a-zA-Z0-9]+)\/',
                r'rutube\.ru\/play\/embed\/([a-zA-Z0-9]+)'
            ],
            'vk': [
                r'vk\.com\/video(-?\d+_\d+)',
                r'vk\.com\/video\?z=video(-?\d+_\d+)'
            ]
        }

        for pattern in patterns.get(platform, []):
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def fetch_youtube_metadata(video_id):
        try:
            from django.conf import settings
            api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
            if not api_key:
                return None

            api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet,contentDetails&key={api_key}"
            response = requests.get(api_url, timeout=5)
            data = response.json()

            if data.get('items'):
                item = data['items'][0]
                snippet = item['snippet']

                return {
                    'title': snippet['title'],
                    'description': snippet.get('description', ''),
                    'thumbnail_url': snippet['thumbnails']['high']['url'],
                }
        except Exception as e:
            print(f"Error fetching YouTube metadata: {e}")
        return None

    @staticmethod
    def fetch_rutube_metadata(video_id):
        try:
            api_url = f"https://rutube.ru/api/video/{video_id}/"
            response = requests.get(api_url, timeout=5)
            if response.status_code != 200:
                return None
            data = response.json()

            return {
                'title': data['title'],
                'description': data.get('description', ''),
                'thumbnail_url': data['thumbnail_url'],
            }
        except Exception as e:
            print(f"Error fetching Rutube meta {e}")
        return None

    def fetch_metadata(self):
        if self.youtube_url:
            video_id = Video.extract_video_id(self.youtube_url, 'youtube')
            if video_id:
                return Video.fetch_youtube_metadata(video_id)

        if self.rutube_url:
            video_id = Video.extract_video_id(self.rutube_url, 'rutube')
            if video_id:
                return Video.fetch_rutube_metadata(video_id)

        if self.vkvideo_url:
            pass

    def save(self, *args, **kwargs):
        if self.pk:
            old = Video.objects.get(pk=self.pk)
            urls_changed = (
                    self.youtube_url != old.youtube_url or
                    self.rutube_url != old.rutube_url or
                    self.vkvideo_url != old.vkvideo_url
            )
        else:
            urls_changed = True

        if urls_changed:
            metadata = self.fetch_metadata()
            if metadata:
                self.title = metadata.get('title', self.title)
                self.description = metadata.get('description', self.description)
                self.thumbnail_url = metadata.get('thumbnail_url', self.thumbnail_url)

        if not self.slug and self.title:
            self.slug = slugify(self.title)[:200]

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == 'draft':
            self.published_at = None

        super().save(*args, **kwargs)

    def get_primary_url(self):
        if self.youtube_url:
            return self.youtube_url
        elif self.rutube_url:
            return self.rutube_url
        elif self.vkvideo_url:
            return self.vkvideo_url
        return None

    def __str__(self):
        return self.title or _("Без названия")

    def __repr__(self):
        return f"<Video id={self.id} title='{self.title}' status={self.status}>"
