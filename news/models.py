import re
import requests

from django.db import models
from django_editorjs2.fields import EditorJSField
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Пример: Новости, Технологии")
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL.")
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Родительская категория"),
        help_text = _("Оставьте пустым для корневой категории")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Необязательно. Пояснение к категории.")
    )

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ['name']
        indexes = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Category id={self.id} name='{self.name}'>"


class MediaAsset(models.Model):
    file = models.FileField(
        upload_to="uploads/%Y/%m/%d/",
        verbose_name=_("Файл"),
        help_text=_("Изображение")
    )
    alt = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Описание (alt)"),
        help_text=_("Текст для атрибута alt")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата загрузки")
    )
    original_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Оригинальное имя файла"),
        help_text=_("Имя файла при загрузке")
    )

    class Meta:
        verbose_name = _("Медиафайл")
        verbose_name_plural = _("Медиафайлы")
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=['uploaded_at']),]

    def __str__(self):
        return self.original_name or str(self.file)

    def __repr__(self):
        return f"<MediaAsset id={self.id} file='{self.file.name}'>"


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Название"),
        help_text=_("Пример: Новости, ПДД")
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL")
    )

    class Meta:
        verbose_name = _("Тег")
        verbose_name_plural = _("Теги")
        ordering = ["name"]
        indexes = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Tag id={self.id} name='{self.name}'>"

class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", _("Черновик")),
        ("published", _("Опубликован")),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name=_("Заголовок"),
        help_text=_("Краткий заголовок статьи, до 200 символов")
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
        verbose_name=_("Категория")
    )
    excerpt = models.TextField(
        blank=True,
        verbose_name=_("Краткое описание"),
        help_text=_("Появится в списке постов")
    )
    body = models.TextField(
        blank=True,
        verbose_name=_("Текст (plain)"),
    )
    body_json = EditorJSField(
        blank=True,
        default=dict,
        verbose_name=_("Текст (JSON)")
    )
    cover = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name=_("Обложка")
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
        help_text=_("Пост будет постоянно отображаться в верхней части главной страницы")
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
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="posts",
        verbose_name=_("Теги")
    )

    class Meta:
        verbose_name = _("Пост")
        verbose_name_plural = _("Посты")
        ordering = ["-published_at", "-updated_at"]
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['-published_at', 'status']),
        ]

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == 'draft':
            self.published_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Post id={self.id} title='{self.title}' status={self.status}>"


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
        editable=False,
        verbose_name=_("Заголовок"),
        help_text=_("Краткий заголовок статьи, до 200 символов"))
    slug = models.SlugField(
        max_length=200,
        unique=True,
        editable=False,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL")
    )
    description = models.TextField(
        blank=True,
        editable=False,
        verbose_name=_("Описание"),
        help_text=_("Необязательно. Пояснение к категории.")
    )
    thumbnail_url = models.URLField(
        blank=True,
        editable=False,
        verbose_name=_("Ссылка на обложку")
    )
    external_id = models.CharField(
        max_length=50,
        blank=True,
        editable=False,
        verbose_name=_("ID видео")
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
    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Просмотры")
    )

    class Meta:
        verbose_name=_("Видео")
        verbose_name_plural=_("Видео")
        ordering = ["-published_at", "-updated_at"]
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['-published_at', 'status']),
        ]

    def extract_youtube_id(self, url):
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11})',
            r'(?:embed\/|v\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def fetch_youtube_metadata(self, video_id):
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
                    'external_id': video_id,
                }
        except Exception as e:
            print(f"Error fetching YouTube metadata: {e}")
        return None

    def fetch_rutube_metadata(self, url):
        try:
            video_id = url.rstrip('/').split('/')[-1]
            api_url = f"https://rutube.ru/api/video/{video_id}/"
            response = requests.get(api_url, timeout=5)
            if response.status_code != 200:
                return None
            data = response.json()

            return {
                'title': data['title'],
                'description': data.get('description', ''),
                'thumbnail_url': data['thumbnail_url'],
                'external_id': video_id,
            }
        except Exception as e:
            print(f"Error fetching Rutube meta {e}")
        return None

    def fetch_metadata(self):
        if self.youtube_url:
            video_id = self.extract_youtube_id(self.youtube_url)
            if video_id:
                return self.fetch_youtube_metadata(video_id)

        if self.rutube_url:
            return self.fetch_rutube_metadata(self.rutube_url)

        if self.vkvideo_url:
            pass

    def save(self, *args, **kwargs):
        if not self.pk:
            metadata = self.fetch_metadata()
            if metadata:
                self.title = metadata['title']
                self.description = metadata['description']
                self.thumbnail_url = metadata['thumbnail_url']
                self.external_id = metadata['external_id']

        if not self.slug and self.title:
            self.slug = slugify(self.title)[:200]

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == 'draft':
            self.published_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or _("Без названия")

    def __repr__(self):
        return f"<Video id={self.id} title='{self.title}' status={self.status}>"
