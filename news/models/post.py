from django.db import models
from django.utils.translation import gettext_lazy as _

from . import BaseContentItem


class Post(BaseContentItem):
    """Cтатья/новость"""

    body = models.TextField(
        blank=True,
        verbose_name=_("Текст статьи")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Закрепить"),
        help_text=_("Пост будет постоянно отображаться в верхней части главной страницы")
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL")
    )
    lead = models.TextField(
        blank=True,
        verbose_name=_("Лид/описание"),
        help_text=_("Описание поста")
    )

    class Meta:
        verbose_name = _("Cтатья")
        verbose_name_plural = _("Cтатьи")
        indexes = [
            models.Index(fields=['is_featured', 'status']),
        ]

    def get_absolute_url(self):
        return f"/news/{self.slug}/"
