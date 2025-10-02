import logging
import re
import requests

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import Truncator

from requests.exceptions import RequestException, Timeout

from . import BaseContentItem

logger = logging.getLogger(__name__)


class Video(BaseContentItem):
    """Видео"""

    youtube_url = models.URLField(
        blank=True,
        verbose_name=_("YouTube ссылка"),
        help_text=_("Ссылка на видео YouTube")
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
        verbose_name=_("Название"),
        help_text=_("Автозаполняется. Название видео, до 200 символов")
    )
    title_picture = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Автозаполняется. Ссылка на обложку")
    )
    lead = models.TextField(
        blank=True,
        verbose_name=_("Лид/описание"),
        help_text=_("Автозаполняется. Описание видео")
    )

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
            api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
            if not api_key:
                logger.warning("YouTube API key not configured")
                return None

            api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet&key={api_key}"

            response = requests.get(api_url, timeout=(3.05, 10))
            response.raise_for_status()

            data = response.json()

            if not data.get('items'):
                logger.info(f"No YouTube video found with ID: {video_id}")
                return None

            item = data['items'][0]
            snippet = item['snippet']

            return {
                'title': snippet['title'][:200],
                'lead': Truncator(snippet.get('description', '')).chars(200, truncate='...'),
                'thumbnail_url': snippet['thumbnails']['high']['url'],
            }

        except Timeout:
            logger.error(f"YouTube API timeout for video {video_id}")
            return None
        except RequestException as e:
            logger.error(f"YouTube API request failed for video {video_id}: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching YouTube metadata for {video_id}")
            return None

    @staticmethod
    def fetch_rutube_metadata(video_id):
        try:
            api_url = f"https://rutube.ru/api/video/{video_id}/"

            response = requests.get(api_url, timeout=(3.05, 10))

            if response.status_code == 404:
                logger.info(f"RuTube video not found: {video_id}")
                return None

            response.raise_for_status()
            data = response.json()

            return {
                'title': data.get('title', '')[:200],
                'lead': Truncator(data.get('description', '')).chars(200, truncate='...'),
                'thumbnail_url': data.get('thumbnail_url', ''),
            }

        except Timeout:
            logger.error(f"RuTube API timeout for video {video_id}")
            return None
        except RequestException as e:
            logger.error(f"RuTube API request failed for video {video_id}: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching RuTube metadata for {video_id}")
            return None

    def fetch_metadata(self):
        max_retries = 2
        metadata = None

        for attempt in range(max_retries + 1):
            if self.youtube_url:
                video_id = self.extract_video_id(self.youtube_url, 'youtube')
                if video_id:
                    metadata = self.fetch_youtube_metadata(video_id)
                    if metadata:
                        break

            if self.rutube_url and not metadata:
                video_id = self.extract_video_id(self.rutube_url, 'rutube')
                if video_id:
                    metadata = self.fetch_rutube_metadata(video_id)
                    if metadata:
                        break

            if metadata:
                break

            if attempt < max_retries:
                import time
                time.sleep(1 * (attempt + 1))

        return metadata

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
                if not self.title:
                    self.title = metadata.get('title', self.title)
                if not self.title_picture:
                    self.title_picture = metadata.get('thumbnail_url', self.title_picture)
                if not self.lead:
                    self.lead = metadata.get('lead')

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == 'draft':
            self.published_at = None

        super().save(*args, **kwargs)

    @property
    def yt_code(self):
        return self.extract_video_id(self.youtube_url, "youtube")

    def get_primary_url(self):
        if self.youtube_url:
            return self.youtube_url
        elif self.rutube_url:
            return self.rutube_url
        elif self.vkvideo_url:
            return self.vkvideo_url
        return None

    class Meta:
        verbose_name = _("Видео")
        verbose_name_plural = _("Видео")

    def __str__(self):
        return self.title or _("Без названия")
