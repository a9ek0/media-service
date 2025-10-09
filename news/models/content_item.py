import logging
import requests
import time

from django.utils.text import Truncator
from django.conf import settings
from django.db import models
from django.db.models.functions import Now
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from requests.exceptions import RequestException, Timeout

__all__ = ["ContentItem"]

logger = logging.getLogger(__name__)


class ContentItem(models.Model):

    class Status(models.TextChoices):
        DRAFT = "D", _("Черновик")
        PUBLISHED = "P", _("Опубликован")

    class ContentType(models.TextChoices):
        VIDEO = "V", _("Видео")
        ARTICLE = "A", _("Статья")

    title = models.CharField(
        verbose_name=_("Название"),
        help_text=_("Может автозаполняться из метаданных видео (YouTube/RuTube) если поле пустое"),
    )
    lead = models.TextField(
        blank=True,
        verbose_name=_("Лид/описание"),
        help_text=_("Короткое описание. Автозаполняется из описания видео, только для видео и только если пусто"),
    )
    title_picture = models.CharField(
        null=True,
        blank=True,
        verbose_name=_("Обложка"),
        help_text=_(
            "Код в S3 или полный URL внешней обложки. Может быть автозаполнена из метаданных видео, только для видео"
        ),
    )

    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True, verbose_name=_("Категория"))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_("Автор"))
    tags = models.ManyToManyField("Tag", blank=True, verbose_name=_("Теги"))
    status = models.CharField(choices=Status.choices, default=Status.DRAFT, verbose_name=_("Статус"))  #!

    created_at = models.DateTimeField(
        default=timezone.now,
        db_default=Now(),
        verbose_name=_("Дата создания"),
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Запланированная дата публикации"),
        help_text=_("Дата и время, когда контент должен быть опубликован"),
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Дата публикации"),
        help_text=_("Заполняется автоматически при публикации"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))

    views = models.PositiveIntegerField(default=0, verbose_name=_("Просмотры"))

    content_type = models.CharField(
        choices=ContentType.choices, default=ContentType.ARTICLE, verbose_name=_("Тип контента")
    )

    body = models.TextField(blank=True, verbose_name=_("Текст статьи"), help_text=_("В формате Markdown"))
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Избранный"),
        help_text=_("Отметить для особого отображения в ленте"),
    )
    slug = models.SlugField(unique=True, verbose_name=_("Slug"))

    youtube_id = models.CharField(blank=True, verbose_name=_("ID YouTube видео"))
    rutube_id = models.CharField(blank=True, verbose_name=_("ID Rutube видео"))
    vkvideo_id = models.CharField(blank=True, verbose_name=_("ID VK Видео"))

    class Meta:
        verbose_name = _("Элемент контента")
        verbose_name_plural = _("Элементы контента")
        ordering = ["-published_at", "-updated_at"]
        indexes = [
            models.Index(fields=["published_at"]),
            models.Index(fields=["category", "-published_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def publish(self):
        if self.status == self.Status.PUBLISHED:
            return False

        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])
        return True

    def hide(self):
        if self.status == self.Status.DRAFT:
            return False

        self.status = self.Status.DRAFT
        self.save(update_fields=["status"])
        return True

    def schedule(self, publish_time):
        if publish_time <= timezone.now():
            raise ValueError("Scheduled time must be in the future")

        self.scheduled_at = publish_time
        self.status = self.Status.DRAFT
        self.save(update_fields=["scheduled_at", "status"])
        return True

    def unschedule(self):
        self.scheduled_at = None
        self.save(update_fields=["scheduled_at"])
        return True

    @classmethod
    def publish_scheduled(cls):
        updated = cls.objects.filter(
            status=cls.Status.DRAFT, scheduled_at__isnull=False, scheduled_at__lte=timezone.now()
        ).update(status=cls.Status.PUBLISHED, published_at=timezone.now())
        return updated

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def is_scheduled(self):
        return self.scheduled_at is not None and self.status == self.Status.DRAFT

    @property
    def is_post(self):
        return self.content_type == self.ContentType.ARTICLE

    @property
    def is_video(self):
        return self.content_type == self.ContentType.VIDEO

    @property
    def has_video(self):
        return any([self.youtube_id, self.rutube_id, self.vkvideo_id])

    @property
    def should_publish(self):
        return self.is_scheduled and self.scheduled_at <= timezone.now()

    @property
    def youtube_url(self):
        return f"https://www.youtube.com/watch?v={self.youtube_id}" if self.youtube_id else None

    @property
    def rutube_url(self):
        return f"https://rutube.ru/video/{self.rutube_id}/" if self.rutube_id else None

    @property
    def vkvideo_url(self):
        return f"https://vk.com/video-{self.vkvideo_id}" if self.vkvideo_id else None

    @property
    def primary_video_url(self):
        if self.youtube_id:
            return self.youtube_url
        elif self.rutube_id:
            return self.rutube_url
        elif self.vkvideo_id:
            return self.vkvideo_url
        return None

    def title_picture_url(self):
        if not self.title_picture:
            return None
        if self.title_picture.startswith(("http://", "https://")):
            return self.title_picture
        base_url = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", "")
        if base_url:
            return f"https://{base_url}/{self.title_picture}"
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        if bucket:
            return f"https://{bucket}.s3.amazonaws.com/{self.title_picture}"
        return None

    def fetch_metadata(self):
        if not self.is_video:
            logger.debug("fetch_metadata called for non-video item; skipping")
            return False

        changed_fields = self._fetch_video_metadata()
        if changed_fields:
            self.save(update_fields=changed_fields)
            return True
        return False

    def _fetch_video_metadata(self):
        max_retries = 2
        metadata = None

        for attempt in range(max_retries + 1):
            if self.youtube_id:
                metadata = self._fetch_youtube_metadata()
                if metadata:
                    break

            if not metadata and self.rutube_id:
                metadata = self._fetch_rutube_metadata()
                if metadata:
                    break

            if metadata:
                break

            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))

        changed = []
        if metadata:
            if (not self.title or self.title.strip() == "") and metadata.get("title"):
                self.title = metadata["title"][:255]
                changed.append("title")
            if (not self.lead or self.lead.strip() == "") and metadata.get("lead"):
                self.lead = metadata["lead"]
                changed.append("lead")
            if (not self.title_picture or self.title_picture.strip() == "") and metadata.get("thumbnail_url"):
                self.title_picture = metadata["thumbnail_url"]
                changed.append("title_picture")
        return changed

    def _fetch_youtube_metadata(self):
        try:
            api_key = getattr(settings, "YOUTUBE_API_KEY", None)
            if not api_key:
                logger.warning("YouTube API key not configured")
                return None

            api_url = f"https://www.googleapis.com/youtube/v3/videos?id={self.youtube_id}&part=snippet&key={api_key}"

            response = requests.get(api_url, timeout=(3.05, 10))
            response.raise_for_status()

            data = response.json()

            if not data.get("items"):
                logger.info(f"No YouTube video found with ID: {self.youtube_id}")
                return None

            item = data["items"][0]
            snippet = item["snippet"]

            thumbnails = snippet.get("thumbnails", {}) or {}
            thumb_url = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("standard", {}).get("url")
                or thumbnails.get("default", {}).get("url")
                or ""
            )

            return {
                "title": snippet.get("title", "")[:255],
                "lead": Truncator(snippet.get("description", "") or "").chars(500, truncate="..."),
                "thumbnail_url": thumb_url,
            }

        except Timeout:
            logger.error(f"YouTube API timeout for video {self.youtube_id}")
            return None
        except RequestException as e:
            logger.error(f"YouTube API request failed for video {self.youtube_id}: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching YouTube metadata for {self.youtube_id}")
            return None

    def _fetch_rutube_metadata(self):
        try:
            api_url = f"https://rutube.ru/api/video/{self.rutube_id}/"

            response = requests.get(api_url, timeout=(3.05, 10))

            if response.status_code == 404:
                logger.info(f"RuTube video not found: {self.rutube_id}")
                return None

            response.raise_for_status()
            data = response.json()

            return {
                "title": data.get("title", "")[:200],
                "lead": Truncator(data.get("description", "")).chars(500, truncate="..."),
                "thumbnail_url": data.get("thumbnail_url", ""),
            }

        except Timeout:
            logger.error(f"RuTube API timeout for video {self.rutube_id}")
            return None
        except RequestException as e:
            logger.error(f"RuTube API request failed for video {self.rutube_id}: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching RuTube metadata for {self.rutube_id}")
            return None

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"
